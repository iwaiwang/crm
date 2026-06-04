"""收款方/供应商模型"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="收款方名称")
    tax_id = Column(String(50), comment="税号")
    bank_name = Column(String(100), comment="开户行")
    bank_account = Column(String(50), comment="银行账号")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    address = Column(String(200), comment="地址")
    remark = Column(Text, comment="备注")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Supplier {self.name}>"