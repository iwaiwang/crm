"""收入模型"""
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class IncomeSource(str, Enum):
    INVOICE = "invoice"       # 发票收入
    CONTRACT = "contract"     # 合同收入
    OTHER = "other"           # 其他收入


class IncomeCategory(str, Enum):
    SALES = "sales"           # 销售收入
    SERVICE = "service"       # 服务收入
    REFUND = "refund"         # 退税/返还
    OTHER = "other"           # 其他收入


class Income(Base):
    __tablename__ = "incomes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(
        SQLEnum("invoice", "contract", "other", name="income_source"),
        default="invoice",
        comment="收入来源类型"
    )
    source_id = Column(String(36), comment="关联源 ID（发票或合同 ID）")
    invoice_id = Column(String(36), ForeignKey("invoices.id"), comment="关联的发票 ID")
    payment_record_id = Column(String(36), ForeignKey("payment_records.id"), comment="关联的收款记录 ID")
    customer_id = Column(String(36), ForeignKey("customers.id"), comment="付款方 ID")
    customer_name = Column(String(100), comment="付款方名称")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="收入金额")
    income_date = Column(Date, nullable=False, comment="收入日期")
    income_year = Column(String(4), nullable=False, comment="收入年份")
    income_category = Column(
        SQLEnum("sales", "service", "refund", "other", name="income_category"),
        default="sales",
        comment="收入分类"
    )
    payment_method = Column(String(50), comment="收款方式")
    remark = Column(Text, comment="备注")
    file_id = Column(String(36), comment="凭证文件 ID")
    file_url = Column(String(500), comment="凭证文件 URL")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    customer = relationship("Customer", back_populates="incomes")
    invoice = relationship("Invoice", back_populates="income")
    payment_record = relationship("PaymentRecord", backref="incomes")

    def __repr__(self):
        return f"<Income {self.id} - {self.amount}>"
