"""发票模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_code = Column(String(20), comment="发票代码 (10-12 位)")
    invoice_number = Column(String(20), comment="发票号码 (8 位)")
    check_code = Column(String(20), comment="校验码后 6 位")
    invoice_date = Column(Date, comment="开票日期")
    invoice_no = Column(String(50), unique=True, comment="发票号码")
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True, comment="关联合同（可选）")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="发票金额")
    tax_rate = Column(DECIMAL(5, 2), default=0, comment="税率")
    tax_amount = Column(DECIMAL(15, 2), comment="税额")
    total_amount = Column(DECIMAL(15, 2), comment="价税合计")
    type = Column(
        SQLEnum("normal", "special", name="invoice_type"),
        default="normal",
        comment="发票类型",
    )
    invoice_type = Column(
        SQLEnum("sales", "purchase", name="invoice_direction_type"),
        default="sales",
        comment="发票方向：sales=销项发票，purchase=进项发票",
    )
    buyer_name = Column(String(200), comment="购买方名称")
    buyer_tax_id = Column(String(50), comment="购买方税号")
    seller_name = Column(String(200), comment="销售方名称")
    seller_tax_id = Column(String(50), comment="销售方税号")
    issue_date = Column(Date, comment="应开票日期")
    due_date = Column(Date, comment="应开票日期")
    status = Column(
        SQLEnum("pending", "issued", "sent", "received", "normal", "void", name="invoice_status"),
        default="pending",
        comment="发票状态",
    )
    file_id = Column(String(36), comment="上传文件 ID")
    file_url = Column(String(500), comment="文件访问 URL")
    ai_parsed = Column(Boolean, default=False, comment="是否 AI 解析")
    parsed_at = Column(DateTime(timezone=True), comment="AI 解析时间")
    parse_confidence = Column(Float, comment="AI 解析置信度 (0-1)")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    contract = relationship("Contract", back_populates="invoices")
    income = relationship("Income", back_populates="invoice", uselist=False)
    expense = relationship("Expense", back_populates="invoice", uselist=False)
    # 与收款记录的关联（本公司开具发票时关联应收计划的收款登记）
    payment_records = relationship("PaymentRecord", back_populates="invoice", secondary="invoice_payment_record")

    def __repr__(self):
        return f"<Invoice {self.invoice_no}>"
