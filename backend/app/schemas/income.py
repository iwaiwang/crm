"""收入 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class IncomeSource(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    OTHER = "other"


class IncomeCategory(str, Enum):
    SALES = "sales"
    SERVICE = "service"
    REFUND = "refund"
    OTHER = "other"


class IncomeBase(BaseModel):
    source_type: Optional[IncomeSource] = Field(None, description="收入来源类型")
    source_id: Optional[str] = Field(None, description="关联源 ID")
    invoice_id: Optional[str] = Field(None, description="关联的发票 ID")
    customer_id: Optional[str] = Field(None, description="付款方 ID")
    customer_name: Optional[str] = Field(None, description="付款方名称")
    amount: Decimal = Field(default=0, description="收入金额")
    income_date: date = Field(..., description="收入日期")
    income_year: str = Field(..., description="收入年份")
    income_category: Optional[IncomeCategory] = Field(IncomeCategory.SALES, description="收入分类")
    payment_method: Optional[str] = Field(None, description="收款方式")
    remark: Optional[str] = Field(None, description="备注")
    file_id: Optional[str] = Field(None, description="凭证文件 ID")
    file_url: Optional[str] = Field(None, description="凭证文件 URL")


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    source_type: Optional[IncomeSource] = None
    source_id: Optional[str] = None
    invoice_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    amount: Optional[Decimal] = None
    income_date: Optional[date] = None
    income_year: Optional[str] = None
    income_category: Optional[IncomeCategory] = None
    payment_method: Optional[str] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class IncomeResponse(IncomeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncomeListResponse(BaseModel):
    total: int
    items: List[IncomeResponse]


class IncomeStats(BaseModel):
    total_amount: Decimal = Decimal(0)
    total_count: int = 0
    by_category: dict = Field(default_factory=dict, description="按分类统计")
    by_month: list = Field(default_factory=list, description="按月度统计")
    by_year: dict = Field(default_factory=dict, description="按年份统计")
