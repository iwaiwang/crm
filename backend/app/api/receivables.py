"""应收款管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models.receivable import Receivable, PaymentRecord, invoice_payment_record
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.income import Income
from app.models.customer import Customer
from app.models.user import User
from app.schemas.receivable import (
    ReceivableCreate, ReceivableUpdate, ReceivableResponse, ReceivableListResponse,
    PaymentRecordCreate, PaymentRecordResponse
)
from app.api.auth import require_menu_permission

router = APIRouter()


@router.get("", response_model=ReceivableListResponse)
async def get_receivables(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    contract_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('receivables')),
):
    """获取应收款列表"""
    query = select(Receivable).options(selectinload(Receivable.payment_records), selectinload(Receivable.contract))

    if status:
        query = query.where(Receivable.status == status)
    if contract_id:
        query = query.where(Receivable.contract_id == contract_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Receivable.due_date.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    receivables = result.scalars().all()

    # 构建返回数据，添加 contract_no 字段
    items = []
    for r in receivables:
        r_dict = ReceivableResponse.model_validate(r)
        if r.contract:
            r_dict.contract_no = r.contract.contract_no
        items.append(r_dict)

    return ReceivableListResponse(
        total=total,
        items=items
    )


@router.get("/{receivable_id}", response_model=ReceivableResponse)
async def get_receivable(receivable_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('receivables'))):
    """获取应收款详情"""
    result = await db.execute(
        select(Receivable)
        .where(Receivable.id == receivable_id)
        .options(selectinload(Receivable.payment_records), selectinload(Receivable.contract))
    )
    receivable = result.scalar_one_or_none()

    if not receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    return ReceivableResponse.model_validate(receivable)


@router.post("", response_model=ReceivableResponse)
async def create_receivable(receivable: ReceivableCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('receivables'))):
    """创建应收款"""
    result = await db.execute(select(Contract).where(Contract.id == receivable.contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=400, detail="合同不存在")

    db_receivable = Receivable(**receivable.model_dump())
    db.add(db_receivable)
    await db.commit()
    await db.refresh(db_receivable)

    # 重新加载关联关系
    result = await db.execute(
        select(Receivable)
        .where(Receivable.id == db_receivable.id)
        .options(selectinload(Receivable.payment_records), selectinload(Receivable.contract))
    )
    db_receivable = result.scalar_one()

    # 构建响应数据，包含 contract_no
    response_data = ReceivableResponse(
        id=db_receivable.id,
        contract_id=db_receivable.contract_id,
        amount=db_receivable.amount,
        due_date=db_receivable.due_date,
        status=db_receivable.status,
        remark=db_receivable.remark,
        received_amount=db_receivable.received_amount,
        created_at=db_receivable.created_at,
        updated_at=db_receivable.updated_at,
        payment_records=[],
        contract_no=contract.contract_no,
    )

    return response_data


@router.put("/{receivable_id}", response_model=ReceivableResponse)
async def update_receivable(receivable_id: str, receivable: ReceivableUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('receivables'))):
    """更新应收款"""
    result = await db.execute(select(Receivable).where(Receivable.id == receivable_id).options(selectinload(Receivable.contract)))
    db_receivable = result.scalar_one_or_none()

    if not db_receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    update_data = receivable.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_receivable, field, value)

    await db.commit()
    await db.refresh(db_receivable)

    # 构建响应数据，包含 contract_no
    response_data = ReceivableResponse.model_validate(db_receivable)
    if db_receivable.contract:
        response_data.contract_no = db_receivable.contract.contract_no

    return response_data


@router.post("/{receivable_id}/payment", response_model=PaymentRecordResponse)
async def add_payment(
    receivable_id: str,
    payment: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('receivables')),
):
    """登记收款"""
    result = await db.execute(select(Receivable).where(Receivable.id == receivable_id))
    db_receivable = result.scalar_one_or_none()

    if not db_receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    # 创建收款记录
    db_payment = PaymentRecord(
        receivable_id=receivable_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        remark=payment.remark,
    )
    db.add(db_payment)

    # 更新应收款已收金额和状态
    db_receivable.received_amount = float(db_receivable.received_amount) + float(payment.amount)

    if db_receivable.received_amount >= db_receivable.amount:
        db_receivable.status = "paid"
    elif db_receivable.received_amount > 0:
        db_receivable.status = "partial"

    # 关联发票（如果有）
    invoice_ids = []
    if payment.invoice_ids:
        for invoice_id in payment.invoice_ids:
            invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
            db_invoice = invoice_result.scalar_one_or_none()
            if not db_invoice:
                raise HTTPException(status_code=400, detail=f"发票 {invoice_id} 不存在")
            # 添加到关联表
            db_payment.invoice.append(db_invoice)
            invoice_ids.append(db_invoice.id)

    # 自动创建收入记录
    if payment.amount > 0:
        # 获取合同信息
        contract_result = await db.execute(select(Contract).where(Contract.id == db_receivable.contract_id))
        contract = contract_result.scalar_one_or_none()

        # 确定客户信息
        customer_id = contract.customer_id if contract else None
        customer_name = ""
        if customer_id:
            customer_result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = customer_result.scalar_one_or_none()
            if customer:
                customer_name = customer.name

        # 构建收入记录数据
        income_data = {
            "source_type": "contract",
            "source_id": db_receivable.contract_id,
            "customer_id": customer_id,
            "customer_name": customer_name or (contract.customer_name if contract and hasattr(contract, 'customer_name') else ""),
            "amount": payment.amount,
            "income_date": payment.payment_date,
            "income_year": str(payment.payment_date.year),
            "income_category": "sales",
            "payment_method": payment.payment_method,
            "remark": f"收款登记自动创建 - 应收款{db_receivable.id[:8]}",
        }

        # 如果关联了发票，更新为发票来源
        if invoice_ids:
            income_data["source_type"] = "invoice"
            income_data["invoice_id"] = invoice_ids[0]
            income_data["source_id"] = invoice_ids[0]

        # 先 flush 获取收款记录 ID
        await db.flush()
        income_data["payment_record_id"] = db_payment.id

        # 创建收入记录
        db_income = Income(**income_data)
        db.add(db_income)

    await db.commit()
    await db.refresh(db_payment)

    return PaymentRecordResponse(
        id=db_payment.id,
        receivable_id=db_payment.receivable_id,
        amount=db_payment.amount,
        payment_date=db_payment.payment_date,
        payment_method=db_payment.payment_method,
        remark=db_payment.remark,
        created_at=db_payment.created_at,
        invoice_ids=invoice_ids,
    )


@router.delete("/{receivable_id}")
async def delete_receivable(receivable_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('receivables'))):
    """删除应收款"""
    result = await db.execute(select(Receivable).where(Receivable.id == receivable_id))
    db_receivable = result.scalar_one_or_none()

    if not db_receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    await db.delete(db_receivable)
    await db.commit()

    return {"message": "删除成功"}


@router.delete("/payment/{payment_record_id}")
async def delete_payment_record(
    payment_record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('receivables')),
):
    """删除收款记录（同步删除关联的收入记录）"""
    result = await db.execute(
        select(PaymentRecord).where(PaymentRecord.id == payment_record_id)
    )
    db_payment = result.scalar_one_or_none()

    if not db_payment:
        raise HTTPException(status_code=404, detail="收款记录不存在")

    # 查找关联的收入记录并删除
    income_result = await db.execute(
        select(Income).where(Income.payment_record_id == payment_record_id)
    )
    db_income = income_result.scalar_one_or_none()
    if db_income:
        await db.delete(db_income)

    # 更新应收款的已收金额和状态
    receivable_result = await db.execute(
        select(Receivable).where(Receivable.id == db_payment.receivable_id)
    )
    db_receivable = receivable_result.scalar_one_or_none()
    if db_receivable:
        # 重新计算已收金额
        db_receivable.received_amount = float(db_receivable.received_amount) - float(db_payment.amount)
        if db_receivable.received_amount <= 0:
            db_receivable.received_amount = 0
            db_receivable.status = "unpaid"
        elif db_receivable.received_amount < db_receivable.amount:
            db_receivable.status = "partial"
        else:
            db_receivable.status = "paid"

    await db.delete(db_payment)
    await db.commit()

    return {"message": "删除成功"}
