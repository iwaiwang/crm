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
    contact = Column(String(100), comment="联系人")
    phone = Column(String(50), comment="联系电话")
    email = Column(String(100), comment="邮箱")
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
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    contracts = relationship("Contract", back_populates="customer", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="customer", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="customer", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="supplier", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.name}>"
