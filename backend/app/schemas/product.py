"""产品库存 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class StockMoveType(str, Enum):
    IN = "in"
    OUT = "out"


class StockMoveReason(str, Enum):
    PURCHASE = "purchase"
    SALES = "sales"
    RETURN_IN = "return_in"
    RETURN_OUT = "return_out"
    ADJUSTMENT = "adjustment"


class ProductBase(BaseModel):
    name: str = Field(..., description="产品名称", max_length=200)
    spec: Optional[str] = Field(None, description="规格型号", max_length=100)
    unit: str = Field(default="件", description="单位", max_length=20)
    price: Decimal = Field(default=0, description="单价")
    min_stock: int = Field(default=0, description="安全库存")
    category: Optional[str] = Field(None, description="分类", max_length=50)
    is_active: bool = Field(default=True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    spec: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=20)
    price: Optional[Decimal] = None
    min_stock: Optional[int] = None
    category: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class StockMoveCreate(BaseModel):
    product_id: str = Field(..., description="关联产品")
    type: StockMoveType = Field(..., description="出入库类型")
    qty: int = Field(..., description="数量", ge=1)
    reason: Optional[StockMoveReason] = Field(None, description="原因")
    ref_type: Optional[str] = Field(None, description="关联类型")
    ref_id: Optional[str] = Field(None, description="关联单据 ID")
    remark: Optional[str] = Field(None, description="备注")


class StockMoveResponse(BaseModel):
    id: str
    product_id: str
    type: StockMoveType
    qty: int
    reason: Optional[StockMoveReason]
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: str
    stock_qty: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    total: int
    items: List[ProductResponse]
