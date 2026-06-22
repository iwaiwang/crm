"""收款方 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SupplierType(str, Enum):
    """收款方类型"""
    COMPANY = "company"
    INDIVIDUAL = "individual"


class AccountType(str, Enum):
    """账户类型"""
    CORPORATE = "corporate"
    PERSONAL = "personal"


class SupplierStatus(str, Enum):
    """合作状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class PaymentMethod(str, Enum):
    """付款方式"""
    TRANSFER = "transfer"
    CHECK = "check"
    CASH = "cash"
    OTHER = "other"


# 类型中文映射
SUPPLIER_TYPE_LABELS = {
    "company": "企业",
    "individual": "个人",
}

ACCOUNT_TYPE_LABELS = {
    "corporate": "对公账户",
    "personal": "个人账户",
}

SUPPLIER_STATUS_LABELS = {
    "active": "活跃",
    "inactive": "暂停合作",
}

PAYMENT_METHOD_LABELS = {
    "transfer": "电汇",
    "check": "支票",
    "cash": "现金",
    "other": "其他",
}


class SupplierBase(BaseModel):
    name: str = Field(..., description="收款方名称")
    supplier_type: Optional[SupplierType] = Field(SupplierType.COMPANY, description="收款方类型")
    tax_id: Optional[str] = Field(None, description="税号/统一社会信用代码")
    id_card: Optional[str] = Field(None, description="身份证号（个人收款方）")

    # 银行账户信息
    bank_name: Optional[str] = Field(None, description="开户行名称")
    bank_province: Optional[str] = Field(None, description="开户行省份")
    bank_branch: Optional[str] = Field(None, description="支行名称")
    bank_account: Optional[str] = Field(None, description="银行账号")
    bank_code: Optional[str] = Field(None, description="联行号")
    account_type: Optional[AccountType] = Field(AccountType.CORPORATE, description="账户类型")

    # 地址信息
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    address: Optional[str] = Field(None, description="详细地址")

    # 联系信息
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")

    # 业务信息
    status: Optional[SupplierStatus] = Field(SupplierStatus.ACTIVE, description="合作状态")
    payment_term: Optional[int] = Field(30, description="付款账期（天）")
    payment_method: Optional[PaymentMethod] = Field(PaymentMethod.TRANSFER, description="付款方式")

    remark: Optional[str] = Field(None, description="备注")


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    supplier_type: Optional[SupplierType] = None
    tax_id: Optional[str] = None
    id_card: Optional[str] = None

    bank_name: Optional[str] = None
    bank_province: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None
    account_type: Optional[AccountType] = None

    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None

    status: Optional[SupplierStatus] = None
    payment_term: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None

    remark: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    total: int
    items: List[SupplierResponse]