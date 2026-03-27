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


class CustomerBase(BaseModel):
    name: str = Field(..., description="客户名称", max_length=200)
    contact: Optional[str] = Field(None, description="联系人", max_length=100)
    phone: Optional[str] = Field(None, description="联系电话", max_length=50)
    email: Optional[str] = Field(None, description="邮箱", max_length=100)
    address: Optional[str] = Field(None, description="地址")
    category: CustomerCategory = Field(default=CustomerCategory.NORMAL, description="客户分类")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="客户状态")
    remark: Optional[str] = Field(None, description="备注")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    contact: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    category: Optional[CustomerCategory] = None
    status: Optional[CustomerStatus] = None
    remark: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    total: int
    items: List[CustomerResponse]
