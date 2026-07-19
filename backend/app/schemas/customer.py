"""客户 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CustomerCategory(str, Enum):
    POTENTIAL = "potential"
    NORMAL = "normal"
    VIP = "vip"


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOST = "lost"


# ── 联系人 Schema ──────────────────────────────────────────────

class ContactBase(BaseModel):
    name: str = Field(..., description="联系人姓名", max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: bool = Field(default=False)
    remark: Optional[str] = Field(None)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    remark: Optional[str] = None


class ContactResponse(ContactBase):
    id: str
    customer_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 客户 Schema ────────────────────────────────────────────────

class CustomerBase(BaseModel):
    name: str = Field(..., description="客户名称", max_length=200)
    address: Optional[str] = Field(None, description="地址")
    category: CustomerCategory = Field(default=CustomerCategory.NORMAL, description="客户分类")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="客户状态")
    remark: Optional[str] = Field(None, description="备注")


class CustomerCreate(CustomerBase):
    contacts: List[ContactCreate] = Field(default_factory=list, description="联系人列表")


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    category: Optional[CustomerCategory] = None
    status: Optional[CustomerStatus] = None
    remark: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: str
    contacts: List[ContactResponse] = Field(default_factory=list, description="联系人列表")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    total: int
    items: List[CustomerResponse]
