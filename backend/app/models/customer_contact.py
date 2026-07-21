"""客户联系人模型"""
import uuid

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CustomerContact(Base):
    __tablename__ = "customer_contacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, comment="所属客户ID")
    name = Column(String(100), nullable=False, comment="联系人姓名")
    phone = Column(String(50), comment="联系电话")
    email = Column(String(100), comment="邮箱")
    position = Column(String(100), comment="职位")
    is_primary = Column(Boolean, default=False, comment="是否为主要联系人")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="contacts")

    def __repr__(self):
        return f"<CustomerContact {self.name}>"
