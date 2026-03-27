"""支出模型"""
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ExpenseCategory(str, Enum):
    CATERING = "catering"           # 餐饮
    TRAVEL = "travel"               # 差旅
    PROCUREMENT = "procurement"     # 采购
    OFFICE = "office"               # 办公
    RENT = "rent"                   # 房租
    UTILITIES = "utilities"         # 水电
    SALARY = "salary"               # 工资
    MARKETING = "marketing"         # 市场推广
    SOFTWARE = "software"           # 软件服务
    MAINTENANCE = "maintenance"     # 维修维护
    TRAINING = "training"           # 培训
    ENTERTAINMENT = "entertainment" # 业务招待
    LOGISTICS = "logistics"         # 物流快递
    OTHER = "other"                 # 其他


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String(36), ForeignKey("customers.id"), comment="供应商 ID")
    supplier_name = Column(String(100), comment="供应商/收款方名称")
    invoice_id = Column(String(36), ForeignKey("invoices.id"), comment="关联的进项发票 ID（可选）")
    contract_id = Column(String(36), ForeignKey("contracts.id"), comment="关联合同 ID（可选）")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="支出金额（不含税）")
    tax_amount = Column(DECIMAL(15, 2), default=0, comment="税额")
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="价税合计")
    expense_date = Column(Date, nullable=False, comment="支出日期")
    expense_year = Column(String(4), nullable=False, comment="支出年份")
    expense_category = Column(
        SQLEnum(
            "catering", "travel", "procurement", "office", "rent",
            "utilities", "salary", "marketing", "software", "maintenance",
            "training", "entertainment", "logistics", "other",
            name="expense_category"
        ),
        default="other",
        comment="支出分类"
    )
    payment_method = Column(String(50), comment="支付方式")
    file_id = Column(String(36), comment="发票/凭证文件 ID")
    file_url = Column(String(500), comment="发票/凭证文件 URL")
    ai_parsed = Column(Boolean, default=False, comment="是否 AI 解析")
    parsed_at = Column(DateTime(timezone=True), comment="AI 解析时间")
    parse_confidence = Column(Float, comment="AI 解析置信度 (0-1)")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    supplier = relationship("Customer", back_populates="expenses")
    invoice = relationship("Invoice", back_populates="expense")
    contract = relationship("Contract", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.id} - {self.total_amount}>"
