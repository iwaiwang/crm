"""报销管理 API"""
import io
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import json
from urllib.parse import quote
from openpyxl import Workbook

from app.database import get_db
from app.models.reimbursement import Reimbursement
from app.models.reimbursement_file import ReimbursementFile
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.expense import Expense
from app.models.user import User
from app.models.setting import Setting
from app.schemas.reimbursement import (
    ReimbursementCreate,
    ReimbursementUpdate,
    ReimbursementResponse,
    ReimbursementFileCreate,
    ReimbursementFileResponse,
    ReimbursementListResponse,
    ReimbursementReject,
    ReimbursementApprove,
    ReimbursementStatistics,
    REIMBURSEMENT_CATEGORY_LABELS,
    REIMBURSEMENT_STATUS_LABELS,
    REIMBURSEMENT_KIND_LABELS,
    REIMBURSEMENT_KIND_INVOICE_COMPANY,
    REIMBURSEMENT_KIND_ALLOWANCE_TRAVEL,
    EXPENSE_CATEGORY_OPTIONS,
)
from app.api.auth import require_menu_permission, get_current_user
from app.models.supplier import Supplier
from app.config import settings
from app.schemas.setting import SettingKeys
from app.utils.helpers import clean_text, to_decimal, to_date

router = APIRouter()

# 管理员在「已审核/已支付」状态下可编辑的字段白名单
ADMIN_POST_APPROVAL_EDITABLE_FIELDS = {
    "invoice_id",
    "remark",
    "supplier_bank_name",
    "supplier_bank_branch",
    "supplier_bank_province",
    "supplier_bank_city",
    "supplier_bank_code",
    "supplier_bank_account",
}


async def _get_setting_value(db: AsyncSession, key: str) -> Optional[str]:
    result = await db.execute(select(Setting.value).where(Setting.key == key))
    value = result.scalar_one_or_none()
    return value.strip() if isinstance(value, str) else value


async def _get_payer_companies(db: AsyncSession) -> List[str]:
    """读取支付方公司名称列表"""
    raw = await _get_setting_value(db, SettingKeys.REIMBURSEMENT_PAYER_COMPANIES)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except (json.JSONDecodeError, TypeError):
        return []
    return []


async def _get_expense_categories(db: AsyncSession) -> List[dict]:
    """读取费用分类列表 [{value, label}]"""
    raw = await _get_setting_value(db, SettingKeys.REIMBURSEMENT_EXPENSE_CATEGORIES)
    if not raw:
        return list(EXPENSE_CATEGORY_OPTIONS)
    try:
        data = json.loads(raw)
        if isinstance(data, list) and data:
            normalized = []
            for item in data:
                if isinstance(item, dict) and item.get("value"):
                    value = str(item["value"]).strip()
                    label = str(item.get("label") or value).strip()
                    if value:
                        normalized.append({"value": value, "label": label or value})
                elif isinstance(item, str) and item.strip():
                    normalized.append({"value": item.strip(), "label": item.strip()})
            if normalized:
                return normalized
    except (json.JSONDecodeError, TypeError):
        pass
    return list(DEFAULT_EXPENSE_CATEGORIES)


async def _can_approve_reimbursements(db: AsyncSession, user: User) -> bool:
    if user.role == "admin":
        return True
    approver_id = await _get_setting_value(db, SettingKeys.REIMBURSEMENT_DEFAULT_APPROVER_ID)
    return bool(approver_id and approver_id == user.id)


async def _can_pay_reimbursements(db: AsyncSession, user: User) -> bool:
    if user.role == "admin":
        return True
    payer_id = await _get_setting_value(db, SettingKeys.REIMBURSEMENT_DEFAULT_PAYER_ID)
    return bool(payer_id and payer_id == user.id)


async def _can_view_all_reimbursements(db: AsyncSession, user: User) -> bool:
    return (
        user.role == "admin"
        or await _can_approve_reimbursements(db, user)
        or await _can_pay_reimbursements(db, user)
    )


def _get_status_label(status: str) -> str:
    return REIMBURSEMENT_STATUS_LABELS.get(status, status)


def _get_category_label(category: str, categories: Optional[List[dict]] = None) -> str:
    if categories:
        for item in categories:
            if item.get("value") == category:
                return item.get("label") or category
    return REIMBURSEMENT_CATEGORY_LABELS.get(category, category)


def _collect_file_entries(primary_file_id, primary_file_url, files):
    """合并主文件(file_id)与附件列表(files)，按 file_id 去重，主文件在前"""
    file_map = {f.file_id: f for f in (files or []) if f.file_id}
    entries = []
    seen = set()

    def add(entry):
        entries.append(entry)
        seen.add(entry["file_id"])

    if primary_file_id:
        match = file_map.get(primary_file_id)
        add({
            "file_id": primary_file_id,
            "file_url": primary_file_url or (match.file_url if match else None),
            "file_name": match.file_name if match else None,
            "file_type": match.file_type if match else None,
            "file_size": match.file_size if match else None,
        })
    for f in (files or []):
        if f.file_id and f.file_id not in seen:
            add(f.model_dump())
    return entries


async def _persist_files(db, reimbursement, entries):
    """重建报销单附件"""
    await db.execute(
        delete(ReimbursementFile).where(ReimbursementFile.reimbursement_id == reimbursement.id)
    )
    for idx, entry in enumerate(entries):
        db.add(ReimbursementFile(reimbursement_id=reimbursement.id, sort_order=idx, **entry))


async def _get_reimbursement_with_files(db, reimbursement_id):
    result = await db.execute(
        select(Reimbursement)
        .options(selectinload(Reimbursement.files))
        .where(Reimbursement.id == reimbursement_id)
    )
    return result.scalar_one_or_none()


async def _enrich_reimbursement_response(
    db: AsyncSession,
    reimbursement: Reimbursement,
    current_user: Optional[User] = None,
) -> ReimbursementResponse:
    """为报销单响应添加用户名称"""
    response_data = ReimbursementResponse.model_validate(reimbursement).model_dump()

    # 获取录入人名称
    if reimbursement.created_by:
        creator_result = await db.execute(select(User).where(User.id == reimbursement.created_by))
        creator = creator_result.scalar_one_or_none()
        response_data["creator_name"] = creator.username if creator else None

    # 获取审核人名称
    if reimbursement.approved_by:
        approver_result = await db.execute(select(User).where(User.id == reimbursement.approved_by))
        approver = approver_result.scalar_one_or_none()
        response_data["approver_name"] = approver.username if approver else None

    # 获取支付人名称
    if reimbursement.paid_by:
        payer_result = await db.execute(select(User).where(User.id == reimbursement.paid_by))
        payer = payer_result.scalar_one_or_none()
        response_data["payer_name"] = payer.username if payer else None

    # 获取关联发票号
    if reimbursement.invoice_id:
        invoice_result = await db.execute(select(Invoice).where(Invoice.id == reimbursement.invoice_id))
        invoice = invoice_result.scalar_one_or_none()
        if invoice:
            response_data["invoice_no"] = invoice.invoice_no
            response_data["invoice_code"] = invoice.invoice_code

    # 兼容旧数据：无附件记录但有主文件时，合成一条附件
    if not response_data.get("files") and reimbursement.file_id:
        response_data["files"] = [{
            "id": None,
            "file_id": reimbursement.file_id,
            "file_name": None,
            "file_url": reimbursement.file_url,
            "file_type": None,
            "file_size": None,
            "sort_order": 0,
        }]

    if current_user:
        can_approve = await _can_approve_reimbursements(db, current_user)
        can_pay = await _can_pay_reimbursements(db, current_user)
        response_data["can_approve"] = bool(can_approve and reimbursement.status == "pending")
        response_data["can_pay"] = bool(can_pay and reimbursement.status == "approved")

    return ReimbursementResponse(**response_data)


@router.get("", response_model=ReimbursementListResponse)
async def get_reimbursements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    expense_category: Optional[str] = None,
    payer_company: Optional[str] = None,
    reimbursement_kind: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单列表"""
    can_view_all = await _can_view_all_reimbursements(db, current_user)

    # 构建基础查询
    query = select(Reimbursement).options(selectinload(Reimbursement.files))

    # 普通用户只能看自己创建的；指定审核/支付人可看全部
    if not can_view_all:
        query = query.where(Reimbursement.created_by == current_user.id)

    # 状态筛选
    if status:
        query = query.where(Reimbursement.status == status)

    # 分类筛选
    if expense_category:
        query = query.where(Reimbursement.expense_category == expense_category)

    # 支付方筛选
    if payer_company:
        query = query.where(Reimbursement.payer_company == payer_company)

    # 报销种类筛选
    if reimbursement_kind:
        query = query.where(Reimbursement.reimbursement_kind == reimbursement_kind)

    # 年份筛选
    if year:
        query = query.where(extract('year', Reimbursement.created_at) == year)

    # 月份筛选
    if month:
        query = query.where(extract('month', Reimbursement.created_at) == month)

    # 搜索（供应商名称或支付方）
    if search:
        query = query.where(
            Reimbursement.supplier_name.contains(search)
            | Reimbursement.payer_company.contains(search)
        )

    # 获取总数
    count_query = select(func.count()).select_from(Reimbursement)
    if not can_view_all:
        count_query = count_query.where(Reimbursement.created_by == current_user.id)
    if status:
        count_query = count_query.where(Reimbursement.status == status)
    if expense_category:
        count_query = count_query.where(Reimbursement.expense_category == expense_category)
    if payer_company:
        count_query = count_query.where(Reimbursement.payer_company == payer_company)
    if reimbursement_kind:
        count_query = count_query.where(Reimbursement.reimbursement_kind == reimbursement_kind)
    if year:
        count_query = count_query.where(extract('year', Reimbursement.created_at) == year)
    if month:
        count_query = count_query.where(extract('month', Reimbursement.created_at) == month)
    if search:
        count_query = count_query.where(
            Reimbursement.supplier_name.contains(search)
            | Reimbursement.payer_company.contains(search)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    query = query.order_by(Reimbursement.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reimbursements = result.scalars().all()

    # 响应
    items = []
    for r in reimbursements:
        items.append(await _enrich_reimbursement_response(db, r, current_user))

    return ReimbursementListResponse(total=total, items=items)


@router.get("/statistics", response_model=ReimbursementStatistics)
async def get_reimbursement_statistics(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销统计"""
    can_view_all = await _can_view_all_reimbursements(db, current_user)

    # 构建基础查询
    def get_base_query():
        query = select(Reimbursement)
        if not can_view_all:
            query = query.where(Reimbursement.created_by == current_user.id)
        if year:
            query = query.where(extract('year', Reimbursement.created_at) == year)
        return query

    # 待审核金额
    pending_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "pending")
    if not can_view_all:
        pending_query = pending_query.where(Reimbursement.created_by == current_user.id)
    if year:
        pending_query = pending_query.where(extract('year', Reimbursement.created_at) == year)
    pending_result = await db.execute(pending_query)
    pending_amount, pending_count = pending_result.one() or (0, 0)

    # 待支付金额
    approved_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "approved")
    if not can_view_all:
        approved_query = approved_query.where(Reimbursement.created_by == current_user.id)
    if year:
        approved_query = approved_query.where(extract('year', Reimbursement.created_at) == year)
    approved_result = await db.execute(approved_query)
    approved_amount, approved_count = approved_result.one() or (0, 0)

    # 已支付金额
    paid_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "paid")
    if not can_view_all:
        paid_query = paid_query.where(Reimbursement.created_by == current_user.id)
    if year:
        paid_query = paid_query.where(extract('year', Reimbursement.created_at) == year)
    paid_result = await db.execute(paid_query)
    paid_amount, paid_count = paid_result.one() or (0, 0)

    # 按分类统计（已支付）
    category_query = select(Reimbursement.expense_category, func.sum(Reimbursement.total_amount)).where(Reimbursement.status == "paid").group_by(Reimbursement.expense_category)
    if not can_view_all:
        category_query = category_query.where(Reimbursement.created_by == current_user.id)
    if year:
        category_query = category_query.where(extract('year', Reimbursement.created_at) == year)
    category_result = await db.execute(category_query)
    categories = await _get_expense_categories(db)
    by_category = {}
    for cat, amt in category_result.all():
        label = _get_category_label(cat, categories)
        by_category[label] = {"amount": Decimal(str(amt or 0))}

    return ReimbursementStatistics(
        total_pending_amount=Decimal(str(pending_amount or 0)),
        total_approved_amount=Decimal(str(approved_amount or 0)),
        total_paid_amount=Decimal(str(paid_amount or 0)),
        pending_count=pending_count or 0,
        approved_count=approved_count or 0,
        paid_count=paid_count or 0,
        by_category=by_category,
    )


@router.get("/payer-companies/list", response_model=dict)
async def get_payer_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取支付方公司名称列表（来源：系统设置 → 报销设置）"""
    companies = await _get_payer_companies(db)
    return {"items": companies}


@router.get("/expense-categories/list", response_model=dict)
async def get_expense_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取费用分类列表（来源：系统设置 → 报销设置）"""
    categories = await _get_expense_categories(db)
    return {"items": categories}


@router.post("/expense-categories/migrate", response_model=dict)
async def migrate_expense_category(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """把已有报销单的 expense_category 从旧值改成新值（用于分类标识变更后修复历史数据）"""
    old_value = (payload.get("old_value") or "").strip()
    new_value = (payload.get("new_value") or "").strip()
    if not old_value or not new_value:
        raise HTTPException(status_code=400, detail="old_value 和 new_value 都不能为空")
    if old_value == new_value:
        return {"message": "新旧值相同，无需迁移", "updated": 0}

    result = await db.execute(
        select(Reimbursement).where(Reimbursement.expense_category == old_value)
    )
    reimbursements = result.scalars().all()
    for r in reimbursements:
        r.expense_category = new_value
    await db.commit()
    return {"message": "迁移成功", "updated": len(reimbursements)}


@router.post("/export-batch-payment")
async def export_batch_payment(
    ids: List[str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出选中报销单为银行批量支付 Excel 格式"""
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要导出的报销单")

    result = await db.execute(
        select(Reimbursement).where(Reimbursement.id.in_(ids))
    )
    reimbursements = result.scalars().all()

    if not reimbursements:
        raise HTTPException(status_code=404, detail="未找到选中的报销单")

    company_name = await _get_setting_value(db, SettingKeys.COMPANY_NAME) or ""
    company_bank_name = await _get_setting_value(db, SettingKeys.COMPANY_BANK_NAME) or ""
    company_bank_account = await _get_setting_value(db, SettingKeys.COMPANY_BANK_ACCOUNT) or ""

    # 预加载收款方信息：收集所有涉及的供应商名称 + 公司自身（作为付款方也查一下）
    supplier_names = list({r.supplier_name for r in reimbursements if r.supplier_name})
    if company_name:
        supplier_names.append(company_name)
    supplier_map = {}
    if supplier_names:
        result = await db.execute(
            select(Supplier).where(Supplier.name.in_(supplier_names))
        )
        for s in result.scalars().all():
            supplier_map[s.name] = s

    # 付款方信息：优先从收款方表（公司自身）获取，其次用设置
    payer = supplier_map.get(company_name)
    payer_bank_name = (payer.bank_name if payer else "") or company_bank_name
    payer_bank_account = (payer.bank_account if payer else "") or company_bank_account
    payer_name = company_name

    wb = Workbook()
    ws = wb.active
    ws.title = "批量支付"

    headers = [
        "币种", "日期", "明细标志", "顺序号",
        "付款账号开户行", "付款账号/卡号", "付款账号名称/卡名称",
        "收款账号开户行", "收款账号省份", "收款账号地市", "收款账号地区码",
        "收款账号", "收款账号名称", "金额",
        "汇款用途", "备注信息", "汇款方式",
        "收款账户短信通知手机号码", "自定义序号",
    ]
    ws.append(headers)

    today_str = date.today().strftime("%Y%m%d")

    for idx, r in enumerate(reimbursements, 1):
        s = supplier_map.get(r.supplier_name) if r.supplier_name else None

        bank_name = r.supplier_bank_name or (s.bank_name if s else "") or ""
        bank_branch = r.supplier_bank_branch or (s.bank_branch if s else "") or ""
        bank_province = r.supplier_bank_province or (s.bank_province if s else "") or ""
        bank_city = r.supplier_bank_city or (s.city if s else "") or ""
        bank_account = r.supplier_bank_account or (s.bank_account if s else "") or ""

        supplier_bank_full = " ".join(filter(None, [bank_name, bank_branch]))
        expense_label = REIMBURSEMENT_CATEGORY_LABELS.get(r.expense_category, r.expense_category or "")
        ws.append([
            "RMB",
            today_str,
            "",
            idx,
            payer_bank_name,
            payer_bank_account,
            payer_name,
            supplier_bank_full,
            bank_province,
            bank_city,
            bank_account[:4],
            bank_account,
            r.supplier_name or "",
            float(r.total_amount or 0),
            expense_label,
            r.remark or "",
            "0",
            "",
            idx,
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"批量支付_{today_str}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{reimbursement_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单详情"""
    result = await db.execute(
        select(Reimbursement)
        .options(selectinload(Reimbursement.files))
        .where(Reimbursement.id == reimbursement_id)
    )
    reimbursement = result.scalar_one_or_none()

    if not reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    # 权限检查：非管理员只能看自己的
    if not await _can_view_all_reimbursements(db, current_user) and reimbursement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此报销单")

    return await _enrich_reimbursement_response(db, reimbursement, current_user)


@router.post("", response_model=ReimbursementResponse)
async def create_reimbursement(
    reimbursement: ReimbursementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建报销单"""
    # 验证发票是否存在
    if reimbursement.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == reimbursement.invoice_id))
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=400, detail="发票不存在")
        # 只能关联进项发票
        if invoice.invoice_type != "purchase":
            raise HTTPException(status_code=400, detail="只能关联进项发票")

    # 验证合同是否存在
    if reimbursement.contract_id:
        result = await db.execute(select(Contract).where(Contract.id == reimbursement.contract_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同不存在")

    # 报销种类业务规则
    kind = reimbursement.reimbursement_kind or REIMBURSEMENT_KIND_INVOICE_COMPANY
    if kind == REIMBURSEMENT_KIND_ALLOWANCE_TRAVEL:
        # 出差津贴：无税，分类强制差旅
        reimbursement.tax_amount = Decimal("0")
        reimbursement.total_amount = reimbursement.amount
        reimbursement.expense_category = "travel"
        # 津贴无需税号
        reimbursement.supplier_tax_id = None

    # 创建报销单
    data = reimbursement.model_dump(exclude={"files"})
    db_reimbursement = Reimbursement(
        **data,
        created_by=current_user.id,
        status="draft",
    )
    db.add(db_reimbursement)
    await db.flush()

    # 附件：主文件 + 附件列表
    entries = _collect_file_entries(reimbursement.file_id, reimbursement.file_url, reimbursement.files)
    if entries:
        await _persist_files(db, db_reimbursement, entries)
        db_reimbursement.file_id = entries[0]["file_id"]
        db_reimbursement.file_url = entries[0]["file_url"]

    await db.commit()
    db_reimbursement = await _get_reimbursement_with_files(db, db_reimbursement.id)

    return await _enrich_reimbursement_response(db, db_reimbursement, current_user)


@router.put("/{reimbursement_id}", response_model=ReimbursementResponse)
async def update_reimbursement(
    reimbursement_id: str,
    reimbursement: ReimbursementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新报销单"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    # 权限和状态检查
    is_post_approval = db_reimbursement.status in ("approved", "paid")
    if current_user.role != "admin":
        # 普通用户只能编辑自己的草稿或驳回状态
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限编辑此报销单")
        if db_reimbursement.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="只能编辑草稿或驳回状态的报销单")
    else:
        # 管理员：草稿/驳回可全量编辑；已审核/已支付仅部分字段
        if db_reimbursement.status not in ("draft", "rejected", "approved", "paid"):
            raise HTTPException(status_code=400, detail="当前状态不允许编辑")

    # 更新字段（files 是关系，单独处理）
    files_payload = reimbursement.files
    update_data = reimbursement.model_dump(exclude_unset=True, exclude={"files"})

    # 已审核/已支付状态下，管理员只能修改白名单字段
    if is_post_approval:
        update_data = {k: v for k, v in update_data.items() if k in ADMIN_POST_APPROVAL_EDITABLE_FIELDS}

    for field, value in update_data.items():
        setattr(db_reimbursement, field, value)

    # 附件：客户端显式传入 files 时重建
    if files_payload is not None:
        primary_file_id = update_data.get("file_id") if "file_id" in update_data else None
        primary_file_url = update_data.get("file_url") if "file_url" in update_data else None
        entries = _collect_file_entries(primary_file_id, primary_file_url, files_payload)
        await _persist_files(db, db_reimbursement, entries)
        if entries:
            db_reimbursement.file_id = entries[0]["file_id"]
            db_reimbursement.file_url = entries[0]["file_url"]
        else:
            db_reimbursement.file_id = None
            db_reimbursement.file_url = None

    # 报销种类业务规则：津贴场景强制非税、分类为差旅、税号清空
    effective_kind = update_data.get("reimbursement_kind", None) or db_reimbursement.reimbursement_kind
    if effective_kind == REIMBURSEMENT_KIND_ALLOWANCE_TRAVEL:
        if "amount" in update_data or "tax_amount" in update_data or "total_amount" in update_data:
            db_reimbursement.tax_amount = Decimal("0")
            db_reimbursement.total_amount = db_reimbursement.amount or Decimal("0")
        if "expense_category" not in update_data:
            db_reimbursement.expense_category = "travel"
        if "supplier_tax_id" not in update_data:
            db_reimbursement.supplier_tax_id = None

    # 驳回状态编辑后自动重置为草稿
    if db_reimbursement.status == "rejected":
        db_reimbursement.status = "draft"
        db_reimbursement.reject_reason = None

    await db.commit()
    db_reimbursement = await _get_reimbursement_with_files(db, db_reimbursement.id)

    return await _enrich_reimbursement_response(db, db_reimbursement, current_user)


@router.delete("/{reimbursement_id}")
async def delete_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除报销单"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    # 权限和状态检查
    if current_user.role != "admin":
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此报销单")
        if db_reimbursement.status != "draft":
            raise HTTPException(status_code=400, detail="只能删除草稿状态的报销单")
    else:
        if db_reimbursement.status != "draft":
            raise HTTPException(status_code=400, detail="只能删除草稿状态的报销单")

    await db.execute(
        delete(ReimbursementFile).where(ReimbursementFile.reimbursement_id == reimbursement_id)
    )
    await db.delete(db_reimbursement)
    await db.commit()

    return {"message": "删除成功"}


@router.post("/{reimbursement_id}/submit")
async def submit_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交报销单审核"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    # 权限检查
    if current_user.role != "admin":
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限提交此报销单")

    # 状态检查
    if db_reimbursement.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的报销单")

    # 提交审核
    db_reimbursement.status = "pending"
    await db.commit()
    await db.refresh(db_reimbursement)

    return {"message": "提交成功", "status": "pending"}


@router.post("/{reimbursement_id}/approve")
async def approve_reimbursement(
    reimbursement_id: str,
    approve_data: Optional[ReimbursementApprove] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """审核通过报销单"""
    if not await _can_approve_reimbursements(db, current_user):
        raise HTTPException(status_code=403, detail="需要管理员或默认审核人权限")

    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    if db_reimbursement.status != "pending":
        raise HTTPException(status_code=400, detail="只能审核待审核状态的报销单")

    # 管理员可修改金额和分类
    if approve_data:
        if approve_data.amount is not None:
            db_reimbursement.amount = approve_data.amount
            db_reimbursement.total_amount = approve_data.amount + (db_reimbursement.tax_amount or Decimal("0"))
        if approve_data.expense_category is not None:
            db_reimbursement.expense_category = approve_data.expense_category

    # 审核通过
    db_reimbursement.status = "approved"
    db_reimbursement.approved_by = current_user.id
    db_reimbursement.approved_at = datetime.now()

    await db.commit()
    await db.refresh(db_reimbursement)

    return {"message": "审核通过", "status": "approved"}


@router.post("/{reimbursement_id}/reject")
async def reject_reimbursement(
    reimbursement_id: str,
    reject_data: ReimbursementReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """驳回报销单"""
    if not await _can_approve_reimbursements(db, current_user):
        raise HTTPException(status_code=403, detail="需要管理员或默认审核人权限")

    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    if db_reimbursement.status != "pending":
        raise HTTPException(status_code=400, detail="只能驳回待审核状态的报销单")

    # 驳回
    db_reimbursement.status = "rejected"
    db_reimbursement.approved_by = current_user.id
    db_reimbursement.approved_at = datetime.now()
    db_reimbursement.reject_reason = reject_data.reason

    await db.commit()
    await db.refresh(db_reimbursement)

    return {"message": "已驳回", "status": "rejected", "reason": reject_data.reason}


@router.post("/{reimbursement_id}/pay")
async def pay_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """确认支付"""
    if not await _can_pay_reimbursements(db, current_user):
        raise HTTPException(status_code=403, detail="需要管理员或默认支付确认人权限")

    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()

    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    if db_reimbursement.status != "approved":
        raise HTTPException(status_code=400, detail="只能支付已审核状态的报销单")

    # 确认支付
    db_reimbursement.status = "paid"
    db_reimbursement.paid_by = current_user.id
    db_reimbursement.paid_at = datetime.now()

    # 自动创建支出记录（避免重复）
    existing = await db.execute(
        select(Expense).where(Expense.reimbursement_id == reimbursement_id)
    )
    if not existing.scalar_one_or_none():
        paid_date = db_reimbursement.paid_at.date()
        expense = Expense(
            reimbursement_id=reimbursement_id,
            source_type="reimbursement",
            supplier_name=db_reimbursement.supplier_name,
            invoice_id=db_reimbursement.invoice_id,
            contract_id=db_reimbursement.contract_id,
            amount=db_reimbursement.amount,
            tax_amount=db_reimbursement.tax_amount,
            total_amount=db_reimbursement.total_amount,
            expense_date=paid_date,
            expense_year=str(paid_date.year),
            expense_category=db_reimbursement.expense_category,
            file_id=db_reimbursement.file_id,
            file_url=db_reimbursement.file_url,
            remark=db_reimbursement.remark,
        )
        db.add(expense)

    await db.commit()
    await db.refresh(db_reimbursement)

    return {"message": "已支付", "status": "paid"}


from app.api.reimbursements_ai import router as ai_router
router.include_router(ai_router)
