"""发票管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.receivable import Receivable, PaymentRecord, invoice_payment_record
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse
from app.schemas.receivable import PaymentRecordCreate, PaymentRecordResponse, ReceivableResponse, ReceivableListResponse
from app.api.auth import require_menu_permission

router = APIRouter()


# 注意：check-duplicate 必须放在 /{invoice_id} 之前，否则会被当作 invoice_id 匹配
# 使用 /actions/check-duplicate 避免与 /{invoice_id} 冲突
@router.get("/actions/check-duplicate")
async def check_invoice_duplicate(
    invoice_no: str = Query(...),
    exclude_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """检查发票号码是否重复"""
    query = select(Invoice).where(Invoice.invoice_no == invoice_no)
    if exclude_id:
        query = query.where(Invoice.id != exclude_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return {"duplicate": True, "message": f"发票号码 {invoice_no} 已存在"}
    return {"duplicate": False}


@router.get("", response_model=InvoiceListResponse)
async def get_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    contract_id: Optional[str] = None,
    invoice_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """获取发票列表"""
    from sqlalchemy import select, func
    import traceback

    print(f"[DEBUG] get_invoices 收到参数：page={page}, page_size={page_size}, search={search}, status={status}, invoice_type={invoice_type}")
    try:
        # 构建基础查询
        query = select(Invoice)

        if search:
            query = query.where(Invoice.invoice_no.contains(search))
        if status:
            query = query.where(Invoice.status == status)
        if contract_id:
            query = query.where(Invoice.contract_id == contract_id)
        if invoice_type and invoice_type != 'all':
            query = query.where(Invoice.invoice_type == invoice_type)

        # 获取总数
        count_query = select(func.count()).select_from(Invoice)
        if search:
            count_query = count_query.where(Invoice.invoice_no.contains(search))
        if status:
            count_query = count_query.where(Invoice.status == status)
        if contract_id:
            count_query = count_query.where(Invoice.contract_id == contract_id)
        if invoice_type and invoice_type != 'all':
            count_query = count_query.where(Invoice.invoice_type == invoice_type)

        print(f"[DEBUG] 执行 count_query...")
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        print(f"[DEBUG] total={total}")

        # 获取分页数据
        query = query.order_by(Invoice.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        print(f"[DEBUG] 执行查询 invoices...")
        result = await db.execute(query)
        invoices = result.scalars().all()
        print(f"[DEBUG] 查询到 {len(invoices)} 条记录")

        return InvoiceListResponse(
            total=total,
            items=[InvoiceResponse.model_validate(i) for i in invoices]
        )
    except Exception as e:
        print(f"[ERROR] get_invoices 异常：{type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """获取发票详情"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    return InvoiceResponse.model_validate(invoice)


@router.post("", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """创建发票"""
    print(f"[DEBUG] create_invoice 收到数据：{invoice}")

    # 检查发票号码是否重复
    if invoice.invoice_no:
        result = await db.execute(select(Invoice).where(Invoice.invoice_no == invoice.invoice_no))
        existing = result.scalar()
        print(f"[DEBUG] 检查发票号码 {invoice.invoice_no} 是否重复，existing={existing}")
        if existing:
            raise HTTPException(status_code=400, detail=f"发票号码 {invoice.invoice_no} 已存在，请勿重复添加")

    # 只有当 contract_id 有值时才检查合同是否存在
    if invoice.contract_id:
        result = await db.execute(select(Contract).where(Contract.id == invoice.contract_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="合同不存在")

    try:
        db_invoice = Invoice(**invoice.model_dump())
        print(f"[DEBUG] 创建发票对象：{db_invoice}")
        db.add(db_invoice)
        await db.commit()
        await db.refresh(db_invoice)
        print(f"[DEBUG] 发票创建成功：{db_invoice.id}")
    except IntegrityError as e:
        await db.rollback()
        print(f"[DEBUG] IntegrityError: {e}, orig={e.orig}")
        # 检查是否是唯一约束冲突
        if 'invoice_no' in str(e.orig) or 'UNIQUE constraint failed' in str(e):
            raise HTTPException(status_code=400, detail=f"发票号码已存在，请勿重复添加")
        raise HTTPException(status_code=400, detail=f"创建失败：{str(e)}")
    except Exception as e:
        await db.rollback()
        print(f"[DEBUG] 其他异常：{type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")

    return InvoiceResponse.model_validate(db_invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, invoice: InvoiceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """更新发票"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查发票号码是否重复（排除自己）
    update_data = invoice.model_dump(exclude_unset=True)
    if 'invoice_no' in update_data and update_data['invoice_no']:
        duplicate_result = await db.execute(
            select(Invoice).where(
                Invoice.invoice_no == update_data['invoice_no'],
                Invoice.id != invoice_id
            )
        )
        if duplicate_result.scalar():
            raise HTTPException(status_code=400, detail=f"发票号码 {update_data['invoice_no']} 已存在，请勿重复添加")

    for field, value in update_data.items():
        setattr(db_invoice, field, value)

    await db.commit()
    await db.refresh(db_invoice)

    return InvoiceResponse.model_validate(db_invoice)


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """删除发票"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    await db.delete(db_invoice)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/{invoice_id}/receivables", response_model=ReceivableListResponse)
async def get_invoice_receivables(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """获取发票可关联的应收款列表（用于收款登记）"""
    import traceback

    print(f"[DEBUG] get_invoice_receivables 开始，invoice_id={invoice_id}")
    try:
        # 先获取发票信息
        invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        db_invoice = invoice_result.scalar_one_or_none()
        print(f"[DEBUG] db_invoice={db_invoice}, contract_id={db_invoice.contract_id if db_invoice else None}")

        if not db_invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        # 获取所有未付清的应收款（可关联）
        query = select(Receivable).options(selectinload(Receivable.payment_records)).where(
            (Receivable.status != "paid")
        )

        # 如果发票有合同，优先返回该合同的应收款
        if db_invoice.contract_id:
            # 先获取该合同的应收款
            contract_receivables = await db.execute(
                select(Receivable)
                .options(selectinload(Receivable.payment_records))
                .where(
                    (Receivable.contract_id == db_invoice.contract_id) &
                    (Receivable.status != "paid")
                )
            )
            receivables = contract_receivables.scalars().all()
            print(f"[DEBUG] 合同应收款数量={len(receivables)}")
        else:
            result = await db.execute(query.order_by(Receivable.due_date.asc()))
            receivables = result.scalars().all()
            print(f"[DEBUG] 所有应收款数量={len(receivables)}")

        # 验证 Pydantic 转换
        items = []
        for r in receivables:
            try:
                item = ReceivableResponse.model_validate(r)
                items.append(item)
                print(f"[DEBUG] 转换成功：id={r.id}")
            except Exception as e:
                print(f"[ERROR] 转换失败：id={r.id}, error={e}")
                traceback.print_exc()
                raise

        print(f"[DEBUG] 返回 total={len(items)}")
        return ReceivableListResponse(
            total=len(items),
            items=items
        )
    except Exception as e:
        print(f"[ERROR] get_invoice_receivables 异常：{type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.post("/{invoice_id}/register-payment", response_model=PaymentRecordResponse)
async def register_payment_from_invoice(
    invoice_id: str,
    payment_data: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """从发票创建收款记录（本公司开具发票时的收款登记）"""
    # 验证发票是否存在
    invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = invoice_result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 验证应收款是否存在
    receivable_result = await db.execute(select(Receivable).where(Receivable.id == payment_data.receivable_id))
    db_receivable = receivable_result.scalar_one_or_none()

    if not db_receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    # 创建收款记录
    db_payment = PaymentRecord(
        receivable_id=payment_data.receivable_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method,
        remark=payment_data.remark,
    )
    db.add(db_payment)

    # 关联发票
    db_payment.invoice.append(db_invoice)

    # 更新应收款
    db_receivable.received_amount = float(db_receivable.received_amount) + float(payment_data.amount)
    if db_receivable.received_amount >= db_receivable.amount:
        db_receivable.status = "paid"
    elif db_receivable.received_amount > 0:
        db_receivable.status = "partial"

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
        invoice_ids=[invoice_id],
    )
