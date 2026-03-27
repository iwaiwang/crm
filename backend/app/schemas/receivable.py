"""应收款 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ReceivableStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentRecordBase(BaseModel):
    amount: Decimal = Field(default=0, description="收款金额")
    payment_date: date = Field(..., description="收款日期")
    payment_method: Optional[str] = Field(None, description="收款方式")
    remark: Optional[str] = Field(None, description="备注")


class PaymentRecordCreate(PaymentRecordBase):
    receivable_id: Optional[str] = Field(None, description="关联应收款")
    invoice_ids: Optional[List[str]] = Field(None, description="关联发票 ID 列表")


class PaymentRecordResponse(PaymentRecordBase):
    id: str
    receivable_id: str
    created_at: datetime
    invoice_ids: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ReceivableBase(BaseModel):
    contract_id: str = Field(..., description="关联合同")
    amount: Decimal = Field(default=0, description="应收金额")
    due_date: Optional[date] = Field(None, description="应收日期")
    status: ReceivableStatus = Field(default=ReceivableStatus.UNPAID, description="状态")
    remark: Optional[str] = Field(None, description="备注")


class ReceivableCreate(ReceivableBase):
    pass


class ReceivableUpdate(BaseModel):
    amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    received_amount: Optional[Decimal] = None
    status: Optional[ReceivableStatus] = None
    remark: Optional[str] = None


class ReceivableResponse(ReceivableBase):
    id: str
    received_amount: Decimal = Field(default=0)
    created_at: datetime
    updated_at: datetime
    payment_records: Optional[List[PaymentRecordResponse]] = None
    contract_no: Optional[str] = None  # 关联合同编号

    class Config:
        from_attributes = True


class ReceivableListResponse(BaseModel):
    total: int
    items: List[ReceivableResponse]
