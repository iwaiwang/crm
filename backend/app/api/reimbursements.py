"""报销管理 API"""
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
)
from app.api.auth import require_menu_permission, get_current_user

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
    # 构建基础条件
    base_condition = True
    if current_user.role != "admin":
        base_condition = (Reimbursement.created_by == current_user.id)
    if year:
        base_condition = base_condition & (extract('year', Reimbursement.created_at) == year)

    # 待审核金额
    pending_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "pending")
        .where(base_condition if current_user.role != "admin" else True)
    )
    pending_amount, pending_count = pending_result.one() or (0, 0)

    # 待支付金额
    approved_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "approved")
        .where(base_condition if current_user.role != "admin" else True)
    )
    approved_amount, approved_count = approved_result.one() or (0, 0)

    # 已支付金额
    paid_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "paid")
        .where(base_condition if current_user.role != "admin" else True)
    )
    paid_amount, paid_count = paid_result.one() or (0, 0)

    # 按分类统计（已支付）
    category_result = await db.execute(
        select(Reimbursement.expense_category, func.sum(Reimbursement.total_amount))
        .where(Reimbursement.status == "paid")
        .where(base_condition if current_user.role != "admin" else True)
        .group_by(Reimbursement.expense_category)
    )
    by_category = {}
    for cat, amt in category_result.all():
        label = _get_category_label(cat)
        by_category[label] = {"amount": float(amt or 0), "category_code": cat}

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