"""客户模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, comment="客户名称")
    address = Column(Text, comment="地址")
    category = Column(
        SQLEnum("potential", "normal", "vip", name="customer_category"),
        default="normal",
        comment="客户分类",
    )
    status = Column(
        SQLEnum("active", "suspended", "lost", name="customer_status"),
        default="active",
        comment="客户状态",
    )
    province = Column(String(50), nullable=True, comment="所属省份")
    customer_type = Column(
        SQLEnum("hospital", "agent", name="customer_type"),
        nullable=True,
        comment="客户类型: hospital=医院(终端用户), agent=代理商",
    )
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    # 注意：incomes 和 expenses 不使用级联删除，由 API 手动处理
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    contracts = relationship("Contract", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    projects = relationship("Project", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    incomes = relationship("Income", back_populates="customer", passive_deletes=True)
    expenses = relationship("Expense", back_populates="supplier", passive_deletes=True)
    certificates = relationship("Certificate", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name}>"
