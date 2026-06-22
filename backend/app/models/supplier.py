"""收款方/供应商模型"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
import uuid
from enum import Enum

from app.database import Base


class SupplierType(str, Enum):
    """收款方类型"""
    company = "company"  # 企业
    individual = "individual"  # 个人


class AccountType(str, Enum):
    """账户类型"""
    corporate = "corporate"  # 对公账户
    personal = "personal"  # 个人账户


class SupplierStatus(str, Enum):
    """合作状态"""
    active = "active"  # 活跃
    inactive = "inactive"  # 暂停合作


class PaymentMethod(str, Enum):
    """付款方式"""
    transfer = "transfer"  # 电汇
    check = "check"  # 支票
    cash = "cash"  # 现金
    other = "other"  # 其他


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="收款方名称")
    supplier_type = Column(
        SQLEnum(SupplierType),
        default=SupplierType.company,
        comment="收款方类型：企业/个人"
    )
    tax_id = Column(String(50), comment="税号/统一社会信用代码")
    id_card = Column(String(20), comment="身份证号（个人收款方）")

    # 银行账户信息
    bank_name = Column(String(100), comment="开户行名称")
    bank_province = Column(String(50), comment="开户行省份")
    bank_branch = Column(String(100), comment="支行名称")
    bank_account = Column(String(50), comment="银行账号")
    bank_code = Column(String(20), comment="联行号（12位）")
    account_type = Column(
        SQLEnum(AccountType),
        default=AccountType.corporate,
        comment="账户类型：对公/个人"
    )

    # 地址信息
    province = Column(String(50), comment="省份")
    city = Column(String(50), comment="城市")
    address = Column(String(200), comment="详细地址")

    # 联系信息
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    email = Column(String(100), comment="邮箱")

    # 业务信息
    status = Column(
        SQLEnum(SupplierStatus),
        default=SupplierStatus.active,
        comment="合作状态"
    )
    payment_term = Column(Integer, default=30, comment="付款账期（天）")
    payment_method = Column(
        SQLEnum(PaymentMethod),
        default=PaymentMethod.transfer,
        comment="付款方式"
    )

    # 备注
    remark = Column(Text, comment="备注")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Supplier {self.name}>"