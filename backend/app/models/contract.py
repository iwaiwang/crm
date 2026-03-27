"""合同模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_no = Column(String(50), unique=True, nullable=False, comment="合同编号")
    name = Column(String(200), nullable=False, comment="合同名称")
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, comment="关联客户")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="合同金额")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    status = Column(
        SQLEnum("signed", "in_progress", "completed", "terminated", name="contract_status"),
        default="signed",
        comment="合同状态",
    )
    file_path = Column(String(500), comment="合同文件路径")
    file_id = Column(String(36), comment="上传文件 ID")
    file_url = Column(String(500), comment="文件访问 URL")
    ai_parsed = Column(Boolean, default=False, comment="是否 AI 解析")
    parsed_at = Column(DateTime(timezone=True), comment="AI 解析时间")
    parse_confidence = Column(Float, comment="AI 解析置信度 (0-1)")
    payment_terms = Column(Text, comment="付款条款")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    customer = relationship("Customer", back_populates="contracts")
    invoices = relationship("Invoice", back_populates="contract", cascade="all, delete-orphan")
    receivables = relationship("Receivable", back_populates="contract", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="contract", cascade="all, delete-orphan")
    # 使用字符串引用，lazy='select' 避免在初始化时立即解析
    attachments = relationship("ContractAttachment", back_populates="contract", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Contract {self.contract_no}>"
