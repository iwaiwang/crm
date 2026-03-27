"""应收款模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


# 发票与收款记录关联表
invoice_payment_record = Table(
    "invoice_payment_record",
    Base.metadata,
    Column("invoice_id", String(36), ForeignKey("invoices.id"), primary_key=True),
    Column("payment_record_id", String(36), ForeignKey("payment_records.id"), primary_key=True),
)


class PaymentRecord(Base):
    """收款记录"""
    __tablename__ = "payment_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receivable_id = Column(String(36), ForeignKey("receivables.id"), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="收款金额")
    payment_date = Column(Date, nullable=False, comment="收款日期")
    payment_method = Column(String(50), comment="收款方式")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    receivable = relationship("Receivable", back_populates="payment_records")
    invoice = relationship("Invoice", back_populates="payment_records", secondary="invoice_payment_record")


class Receivable(Base):
    __tablename__ = "receivables"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False, comment="关联合同")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="应收金额")
    due_date = Column(Date, nullable=False, comment="应收日期")
    received_amount = Column(DECIMAL(15, 2), default=0, comment="已收金额")
    status = Column(
        SQLEnum("unpaid", "partial", "paid", "overdue", name="receivable_status"),
        default="unpaid",
        comment="状态",
    )
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    contract = relationship("Contract", back_populates="receivables")
    payment_records = relationship("PaymentRecord", back_populates="receivable", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Receivable {self.id}>"
