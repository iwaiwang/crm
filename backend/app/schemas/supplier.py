"""收款方 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SupplierBase(BaseModel):
    name: str = Field(..., description="收款方名称")
    tax_id: Optional[str] = Field(None, description="税号")
    bank_name: Optional[str] = Field(None, description="开户行")
    bank_account: Optional[str] = Field(None, description="银行账号")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    address: Optional[str] = Field(None, description="地址")
    remark: Optional[str] = Field(None, description="备注")


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
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