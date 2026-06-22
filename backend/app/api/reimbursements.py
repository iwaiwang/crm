"""报销管理 API"""
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import json

from app.database import get_db
from app.models.reimbursement import Reimbursement
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.user import User
from app.models.ai_config import AIConfig
from app.schemas.reimbursement import (
    ReimbursementCreate,
    ReimbursementUpdate,
    ReimbursementResponse,
    ReimbursementListResponse,
    ReimbursementReject,
    ReimbursementApprove,
    ReimbursementStatistics,
    REIMBURSEMENT_CATEGORY_LABELS,
    REIMBURSEMENT_STATUS_LABELS,
    AiReimbursementDraft,
    AiReimbursementPreviewRequest,
    AiReimbursementPreviewResponse,
    AiReimbursementConfirmRequest,
)
from app.api.auth import require_menu_permission, get_current_user
from app.services import ai_service
from app.models.supplier import Supplier
from app.config import settings

router = APIRouter()


def _get_status_label(status: str) -> str:
    return REIMBURSEMENT_STATUS_LABELS.get(status, status)


def _get_category_label(category: str) -> str:
    return REIMBURSEMENT_CATEGORY_LABELS.get(category, category)


async def _enrich_reimbursement_response(db: AsyncSession, reimbursement: Reimbursement) -> ReimbursementResponse:
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

    return ReimbursementResponse(**response_data)


@router.get("", response_model=ReimbursementListResponse)
async def get_reimbursements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    expense_category: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单列表"""
    # 构建基础查询
    query = select(Reimbursement)

    # 非管理员只能看自己创建的
    if current_user.role != "admin":
        query = query.where(Reimbursement.created_by == current_user.id)

    # 状态筛选
    if status:
        query = query.where(Reimbursement.status == status)

    # 分类筛选
    if expense_category:
        query = query.where(Reimbursement.expense_category == expense_category)

    # 年份筛选
    if year:
        query = query.where(extract('year', Reimbursement.created_at) == year)

    # 月份筛选
    if month:
        query = query.where(extract('month', Reimbursement.created_at) == month)

    # 搜索
    if search:
        query = query.where(Reimbursement.supplier_name.contains(search))

    # 获取总数
    count_query = select(func.count()).select_from(Reimbursement)
    if current_user.role != "admin":
        count_query = count_query.where(Reimbursement.created_by == current_user.id)
    if status:
        count_query = count_query.where(Reimbursement.status == status)
    if expense_category:
        count_query = count_query.where(Reimbursement.expense_category == expense_category)
    if year:
        count_query = count_query.where(extract('year', Reimbursement.created_at) == year)
    if month:
        count_query = count_query.where(extract('month', Reimbursement.created_at) == month)
    if search:
        count_query = count_query.where(Reimbursement.supplier_name.contains(search))

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
        items.append(await _enrich_reimbursement_response(db, r))

    return ReimbursementListResponse(total=total, items=items)


@router.get("/statistics", response_model=ReimbursementStatistics)
async def get_reimbursement_statistics(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销统计"""
    # 构建基础查询
    def get_base_query():
        query = select(Reimbursement)
        if current_user.role != "admin":
            query = query.where(Reimbursement.created_by == current_user.id)
        if year:
            query = query.where(extract('year', Reimbursement.created_at) == year)
        return query

    # 待审核金额
    pending_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "pending")
    if current_user.role != "admin":
        pending_query = pending_query.where(Reimbursement.created_by == current_user.id)
    if year:
        pending_query = pending_query.where(extract('year', Reimbursement.created_at) == year)
    pending_result = await db.execute(pending_query)
    pending_amount, pending_count = pending_result.one() or (0, 0)

    # 待支付金额
    approved_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "approved")
    if current_user.role != "admin":
        approved_query = approved_query.where(Reimbursement.created_by == current_user.id)
    if year:
        approved_query = approved_query.where(extract('year', Reimbursement.created_at) == year)
    approved_result = await db.execute(approved_query)
    approved_amount, approved_count = approved_result.one() or (0, 0)

    # 已支付金额
    paid_query = select(func.sum(Reimbursement.total_amount), func.count()).where(Reimbursement.status == "paid")
    if current_user.role != "admin":
        paid_query = paid_query.where(Reimbursement.created_by == current_user.id)
    if year:
        paid_query = paid_query.where(extract('year', Reimbursement.created_at) == year)
    paid_result = await db.execute(paid_query)
    paid_amount, paid_count = paid_result.one() or (0, 0)

    # 按分类统计（已支付）
    category_query = select(Reimbursement.expense_category, func.sum(Reimbursement.total_amount)).where(Reimbursement.status == "paid").group_by(Reimbursement.expense_category)
    if current_user.role != "admin":
        category_query = category_query.where(Reimbursement.created_by == current_user.id)
    if year:
        category_query = category_query.where(extract('year', Reimbursement.created_at) == year)
    category_result = await db.execute(category_query)
    by_category = {}
    for cat, amt in category_result.all():
        label = _get_category_label(cat)
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


@router.get("/{reimbursement_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单详情"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    reimbursement = result.scalar_one_or_none()

    if not reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")

    # 权限检查：非管理员只能看自己的
    if current_user.role != "admin" and reimbursement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此报销单")

    return await _enrich_reimbursement_response(db, reimbursement)


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

    # 创建报销单
    db_reimbursement = Reimbursement(
        **reimbursement.model_dump(),
        created_by=current_user.id,
        status="draft",
    )
    db.add(db_reimbursement)
    await db.commit()
    await db.refresh(db_reimbursement)

    return await _enrich_reimbursement_response(db, db_reimbursement)


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
    if current_user.role != "admin":
        # 普通用户只能编辑自己的草稿或驳回状态
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限编辑此报销单")
        if db_reimbursement.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="只能编辑草稿或驳回状态的报销单")
    else:
        # 管理员可以编辑草稿和驳回状态
        if db_reimbursement.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="只能编辑草稿或驳回状态的报销单")

    # 更新字段
    update_data = reimbursement.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reimbursement, field, value)

    # 驳回状态编辑后自动重置为草稿
    if db_reimbursement.status == "rejected":
        db_reimbursement.status = "draft"
        db_reimbursement.reject_reason = None

    await db.commit()
    await db.refresh(db_reimbursement)

    return await _enrich_reimbursement_response(db, db_reimbursement)


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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

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

    await db.commit()
    await db.refresh(db_reimbursement)

    return {"message": "已支付", "status": "paid"}


# ===== AI 录入报销单相关 =====

async def _load_ai_config(db: AsyncSession) -> None:
    """加载 AI 配置"""
    result = await db.execute(select(AIConfig).limit(1))
    db_config = result.scalar_one_or_none()
    if not db_config or not db_config.enabled:
        raise HTTPException(status_code=503, detail="AI 服务未配置或未启用")

    ai_service.load_config_from_db(
        {
            "service_type": db_config.service_type,
            "api_base_url": db_config.api_base_url,
            "api_key": db_config.api_key,
            "model": db_config.model,
            "ollama_base_url": db_config.ollama_base_url,
            "ollama_model": db_config.ollama_model,
            "timeout": db_config.timeout,
            "enabled": db_config.enabled,
        }
    )


def _clean_text(value) -> Optional[str]:
    """清理文本"""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _to_decimal(value, default="0") -> Decimal:
    """转换为 Decimal"""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except:
        return Decimal(default)


def _to_date(value) -> Optional[date]:
    """转换为日期"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except:
            return None
    return None


def _recommend_expense_category(seller_name: Optional[str], remark: Optional[str]) -> str:
    """根据供应商名称和备注推荐费用分类"""
    text = f"{seller_name or ''} {remark or ''}".lower()

    # 关键词匹配
    if any(kw in text for kw in ["餐", "饭", "酒店", "住宿", "机票", "车票", "火车", "打车", "滴滴", "出行", "差旅", "旅行"]):
        return "travel"
    if any(kw in text for kw in ["采购", "进货", "原料", "材料", "设备", "物资"]):
        return "procurement"
    if any(kw in text for kw in ["办公", "文具", "纸张", "打印机", "电脑", "IT", "软件", "系统", "服务", "云", "服务器", "域名", "阿里云", "腾讯云"]):
        return "software" if any(kw in text for kw in ["软件", "系统", "云", "服务器", "域名"]) else "office"
    if any(kw in text for kw in ["房租", "租金", "物业", "租赁"]):
        return "rent"
    if any(kw in text for kw in ["水电", "电费", "水费", "燃气", "宽带", "网络"]):
        return "utilities"
    if any(kw in text for kw in ["工资", "薪资", "薪酬", "奖金", "提成"]):
        return "salary"
    if any(kw in text for kw in ["推广", "广告", "营销", "市场", "宣传", "投放", "百度", "抖音", "快手", "小红书"]):
        return "marketing"
    if any(kw in text for kw in ["维修", "维护", "修理", "保养", "配件"]):
        return "maintenance"
    if any(kw in text for kw in ["培训", "学习", "课程", "教育", "会议"]):
        return "training"
    if any(kw in text for kw in ["招待", "宴请", "礼品", "送礼"]):
        return "entertainment"
    if any(kw in text for kw in ["快递", "物流", "运输", "配送", "发货", "邮寄"]):
        return "logistics"

    return "other"


def _resolve_upload_file(file_id: str) -> tuple:
    """解析上传文件路径"""
    upload_dir = settings.UPLOAD_DIR
    invoices_dir = os.path.join(upload_dir, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    # 查找文件
    for ext in ["pdf", "jpg", "jpeg", "png", "doc", "docx"]:
        potential_path = os.path.join(invoices_dir, f"{file_id}.{ext}")
        if os.path.exists(potential_path):
            file_url = f"/uploads/invoices/{file_id}.{ext}"
            return potential_path, ext, file_url

    # 也可能在根目录
    for ext in ["pdf", "jpg", "jpeg", "png", "doc", "docx"]:
        potential_path = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(potential_path):
            file_url = f"/uploads/{file_id}.{ext}"
            return potential_path, ext, file_url

    raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")


@router.post("/ai-import/preview", response_model=AiReimbursementPreviewResponse)
async def preview_ai_reimbursement_import(
    payload: AiReimbursementPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """AI 预览报销单录入"""
    # 先加载 AI 配置
    await _load_ai_config(db)

    file_path, file_ext, file_url = _resolve_upload_file(payload.file_id)

    try:
        ai_result = await ai_service.parse_invoice(file_path, file_ext)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 解析发票失败: {exc}") from exc

    parsed_data = ai_result.get("data") or {}

    # 从发票解析结果构建报销单草稿
    # 报销单主要处理进项发票，所以供应商是销售方
    invoice_no = _clean_text(parsed_data.get("invoice_no") or parsed_data.get("invoice_number"))
    amount = _to_decimal(parsed_data.get("amount"))
    total_amount = _to_decimal(parsed_data.get("total_amount") or parsed_data.get("amount"))
    tax_amount = _to_decimal(parsed_data.get("tax_amount"), "0")

    if total_amount <= 0 and amount > 0:
        total_amount = amount + tax_amount

    reimbursement_draft = AiReimbursementDraft(
        invoice_no=invoice_no,
        invoice_code=_clean_text(parsed_data.get("invoice_code")),
        invoice_number=_clean_text(parsed_data.get("invoice_number")),
        supplier_name=_clean_text(parsed_data.get("seller_name")),  # 销售方是供应商
        supplier_tax_id=_clean_text(parsed_data.get("seller_tax_id")),
        supplier_bank_name=None,  # AI 通常不解析银行信息
        supplier_bank_account=None,
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        expense_category=_recommend_expense_category(
            _clean_text(parsed_data.get("seller_name")),
            _clean_text(parsed_data.get("remarks"))
        ),
        issue_date=_to_date(parsed_data.get("invoice_date") or parsed_data.get("issue_date")),
        remark=_clean_text(parsed_data.get("remarks")),
        file_id=payload.file_id,
        file_url=file_url,
        ai_parsed=True,
        parse_confidence=ai_result.get("confidence"),
    )

    suggested_actions = ["将创建 1 张报销单"]
    if reimbursement_draft.supplier_name:
        suggested_actions.append("可在确认后同时创建收款方")

    return AiReimbursementPreviewResponse(
        reimbursement=reimbursement_draft,
        suggested_actions=suggested_actions,
        raw_ai_result=ai_result,
    )


@router.post("/ai-import/confirm")
async def confirm_ai_reimbursement_import(
    payload: AiReimbursementConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """AI 确认报销单录入"""
    reimbursement_data = payload.reimbursement

    if not _clean_text(reimbursement_data.supplier_name):
        raise HTTPException(status_code=400, detail="供应商/收款方名称不能为空")

    # 创建收款方（如果勾选）
    if payload.create_supplier and reimbursement_data.supplier_name:
        existing_result = await db.execute(
            select(Supplier).where(Supplier.name == reimbursement_data.supplier_name)
        )
        if not existing_result.scalar_one_or_none():
            new_supplier = Supplier(
                name=reimbursement_data.supplier_name,
                tax_id=reimbursement_data.supplier_tax_id,
                bank_name=reimbursement_data.supplier_bank_name,
                bank_account=reimbursement_data.supplier_bank_account,
                remark=f"AI录入报销单自动创建",
            )
            db.add(new_supplier)

    # 创建进项发票记录
    invoice_no = reimbursement_data.invoice_no
    if not invoice_no and reimbursement_data.invoice_code and reimbursement_data.invoice_number:
        invoice_no = f"{reimbursement_data.invoice_code}-{reimbursement_data.invoice_number}"

    db_invoice = Invoice(
        invoice_code=reimbursement_data.invoice_code,
        invoice_number=reimbursement_data.invoice_number,
        invoice_no=invoice_no,
        invoice_date=reimbursement_data.issue_date,
        issue_date=reimbursement_data.issue_date,
        amount=reimbursement_data.amount,
        tax_amount=reimbursement_data.tax_amount,
        total_amount=reimbursement_data.total_amount,
        invoice_type="purchase",  # 进项发票
        seller_name=reimbursement_data.supplier_name,  # 销售方是供应商
        seller_tax_id=reimbursement_data.supplier_tax_id,
        status="normal",  # 已收到发票
        file_id=reimbursement_data.file_id,
        file_url=reimbursement_data.file_url,
        ai_parsed=True,
        parse_confidence=reimbursement_data.parse_confidence,
        remark=reimbursement_data.remark,
    )
    db.add(db_invoice)
    await db.flush()  # 获取发票ID

    # 创建报销单，关联发票
    db_reimbursement = Reimbursement(
        invoice_id=db_invoice.id,  # 关联发票
        supplier_name=reimbursement_data.supplier_name,
        supplier_tax_id=reimbursement_data.supplier_tax_id,
        supplier_bank_name=reimbursement_data.supplier_bank_name,
        supplier_bank_account=reimbursement_data.supplier_bank_account,
        amount=reimbursement_data.amount,
        tax_amount=reimbursement_data.tax_amount,
        total_amount=reimbursement_data.total_amount,
        expense_category=reimbursement_data.expense_category,
        remark=reimbursement_data.remark,
        file_id=reimbursement_data.file_id,
        file_url=reimbursement_data.file_url,
        source_type="invoice",
        status="draft",
        created_by=current_user.id,
    )
    db.add(db_reimbursement)

    await db.commit()
    await db.refresh(db_reimbursement)
    await db.refresh(db_invoice)

    return {
        "message": "AI录入报销单成功",
        "reimbursement_id": db_reimbursement.id,
        "invoice_id": db_invoice.id,
        "supplier_created": payload.create_supplier,
    }