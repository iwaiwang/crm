"""支出 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ExpenseCategory(str, Enum):
    CATERING = "catering"           # 餐饮
    TRAVEL = "travel"               # 差旅
    PROCUREMENT = "procurement"     # 采购
    OFFICE = "office"               # 办公
    RENT = "rent"                   # 房租
    UTILITIES = "utilities"         # 水电
    SALARY = "salary"               # 工资
    MARKETING = "marketing"         # 市场推广
    SOFTWARE = "software"           # 软件服务
    MAINTENANCE = "maintenance"     # 维修维护
    TRAINING = "training"           # 培训
    ENTERTAINMENT = "entertainment" # 业务招待
    LOGISTICS = "logistics"         # 物流快递
    OTHER = "other"                 # 其他


# 支出分类中文映射
EXPENSE_CATEGORY_LABELS = {
    "catering": "餐饮",
    "travel": "差旅",
    "procurement": "采购",
    "office": "办公",
    "rent": "房租",
    "utilities": "水电",
    "salary": "工资",
    "marketing": "市场推广",
    "software": "软件服务",
    "maintenance": "维修维护",
    "training": "培训",
    "entertainment": "业务招待",
    "logistics": "物流快递",
    "other": "其他",
}


class ExpenseBase(BaseModel):
    supplier_id: Optional[str] = Field(None, description="供应商 ID")
    supplier_name: Optional[str] = Field(None, description="供应商/收款方名称")
    invoice_id: Optional[str] = Field(None, description="关联的进项发票 ID")
    contract_id: Optional[str] = Field(None, description="关联合同 ID")
    amount: Decimal = Field(default=0, description="支出金额（不含税）")
    tax_amount: Optional[Decimal] = Field(None, description="税额")
    total_amount: Decimal = Field(default=0, description="价税合计")
    expense_date: date = Field(..., description="支出日期")
    expense_year: str = Field(..., description="支出年份")
    expense_category: Optional[ExpenseCategory] = Field(ExpenseCategory.OTHER, description="支出分类")
    payment_method: Optional[str] = Field(None, description="支付方式")
    remark: Optional[str] = Field(None, description="备注")
    file_id: Optional[str] = Field(None, description="发票/凭证文件 ID")
    file_url: Optional[str] = Field(None, description="发票/凭证文件 URL")
    ai_parsed: Optional[bool] = Field(False, description="是否 AI 解析")
    parsed_at: Optional[datetime] = Field(None, description="AI 解析时间")
    parse_confidence: Optional[float] = Field(None, description="AI 解析置信度")


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_id: Optional[str] = None
    contract_id: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    expense_year: Optional[str] = None
    expense_category: Optional[ExpenseCategory] = None
    payment_method: Optional[str] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: Optional[bool] = None
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None


class ExpenseResponse(ExpenseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    total: int
    items: List[ExpenseResponse]


class ExpenseStats(BaseModel):
    total_amount: Decimal = Decimal(0)
    total_count: int = 0
    by_category: dict = Field(default_factory=dict, description="按分类统计")
    by_month: list = Field(default_factory=list, description="按月度统计")
    by_year: dict = Field(default_factory=dict, description="按年份统计")
