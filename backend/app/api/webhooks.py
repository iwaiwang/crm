"""Webhook API - 接收 OpenClaw 等外部系统推送的数据"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from decimal import Decimal
import logging

from app.database import get_db
from app.config import settings
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.receivable import Receivable

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """验证 API Key"""
    if not settings.WEBHOOK_API_KEY:
        return True
    return x_api_key == settings.WEBHOOK_API_KEY


@router.post("/contract")
async def webhook_contract(
    data: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
):
    """
    接收 OpenClaw 推送的合同数据
    """
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        contract_data = data.get("data", {})

        customer_name = contract_data.get("customer_name")
        if not customer_name:
            raise HTTPException(status_code=400, detail="缺少客户名称")

        result = await db.execute(
            select(Customer).where(Customer.name == customer_name)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(
                name=customer_name,
                contact=contract_data.get("customer_contact"),
                phone=contract_data.get("customer_phone"),
                email=contract_data.get("customer_email"),
            )
            db.add(customer)
            await db.commit()
            await db.refresh(customer)
            logger.info(f"创建新客户：{customer_name}")

        contract_amount = Decimal(str(contract_data.get("contract_amount", 0)))
        contract_date = contract_data.get("contract_date")

        contract = Contract(
            contract_no=f"WEBHOOK-{date.today().strftime('%Y%m%d')}-{customer.id[:8]}",
            name=contract_data.get("contract_name", f"{customer_name}合同"),
            customer_id=customer.id,
            amount=contract_amount,
            status="in_progress",
            payment_terms=contract_data.get("payment_terms"),
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        logger.info(f"创建合同：{contract.contract_no}")

        if contract_data.get("invoice_needed"):
            invoice = Invoice(
                contract_id=contract.id,
                amount=Decimal(str(contract_data.get("invoice_amount", contract_amount))),
                due_date=contract_data.get("invoice_due_date"),
                status="pending",
            )
            db.add(invoice)
            await db.commit()
            logger.info(f"创建发票记录：{contract.id}")

        receivable = Receivable(
            contract_id=contract.id,
            amount=contract_amount,
            due_date=contract_data.get("payment_date", contract_date),
            status="unpaid",
        )
        db.add(receivable)
        await db.commit()

        return {
            "status": "success",
            "customer_id": customer.id,
            "contract_id": contract.id,
            "invoice_id": invoice.id if contract_data.get("invoice_needed") else None,
        }

    except Exception as e:
        logger.error(f"Webhook 处理失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoice")
async def webhook_invoice(
    data: dict,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
):
    """
    接收 OpenClaw 推送的发票数据
    """
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        invoice_data = data.get("data", {})
        contract_id = invoice_data.get("contract_id")

        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=400, detail="合同不存在")

        invoice = Invoice(
            invoice_no=invoice_data.get("invoice_no"),
            contract_id=contract_id,
            amount=Decimal(str(invoice_data.get("invoice_amount", 0))),
            tax_rate=Decimal(str(invoice_data.get("tax_rate", 0))),
            issue_date=invoice_data.get("issue_date"),
            status="issued",
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)

        return {
            "status": "success",
            "invoice_id": invoice.id,
        }

    except Exception as e:
        logger.error(f"发票 Webhook 处理失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
