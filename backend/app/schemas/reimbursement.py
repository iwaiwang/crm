"""报销单 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ReimbursementSourceType(str, Enum):
    INVOICE = "invoice"
    MANUAL = "manual"


class ReimbursementStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ReimbursementCategory(str, Enum):
    CATERING = "catering"
    TRAVEL = "travel"
    PROCUREMENT = "procurement"
    OFFICE = "office"
    RENT = "rent"
    UTILITIES = "utilities"
    SALARY = "salary"
    MARKETING = "marketing"
    SOFTWARE = "software"
    MAINTENANCE = "maintenance"
    TRAINING = "training"
    ENTERTAINMENT = "entertainment"
    LOGISTICS = "logistics"
    OTHER = "other"


# 费用分类中文映射
REIMBURSEMENT_CATEGORY_LABELS = {
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


# 状态中文映射
REIMBURSEMENT_STATUS_LABELS = {
    "draft": "草稿",
    "pending": "待审核",
    "approved": "已审核",
    "rejected": "已驳回",
    "paid": "已支付",
}


class ReimbursementBase(BaseModel):
    source_type: Optional[ReimbursementSourceType] = Field(ReimbursementSourceType.MANUAL, description="来源类型")
    invoice_id: Optional[str] = Field(None, description="关联进项发票ID")
    contract_id: Optional[str] = Field(None, description="关联合同ID")
    supplier_name: str = Field(..., description="供应商/收款方名称")
    amount: Decimal = Field(..., ge=0, description="报销金额不含税")
    tax_amount: Optional[Decimal] = Field(Decimal("0"), description="税额")
    total_amount: Decimal = Field(..., ge=0, description="价税合计")
    expense_category: Optional[ReimbursementCategory] = Field(ReimbursementCategory.OTHER, description="费用分类")
    remark: Optional[str] = Field(None, description="备注说明")
    file_id: Optional[str] = Field(None, description="附件文件ID")
    file_url: Optional[str] = Field(None, description="附件文件URL")


class ReimbursementCreate(ReimbursementBase):
    pass


class ReimbursementUpdate(BaseModel):
    supplier_name: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    expense_category: Optional[ReimbursementCategory] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class ReimbursementReject(BaseModel):
    reason: str = Field(..., description="驳回原因")


class ReimbursementApprove(BaseModel):
    amount: Optional[Decimal] = Field(None, description="修改后的金额")
    expense_category: Optional[ReimbursementCategory] = Field(None, description="修改后的分类")


class ReimbursementResponse(ReimbursementBase):
    id: str
    status: ReimbursementStatus
    created_by: str
    creator_name: Optional[str] = None
    approved_by: Optional[str] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    paid_by: Optional[str] = None
    payer_name: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReimbursementListResponse(BaseModel):
    total: int
    items: List[ReimbursementResponse]


class ReimbursementStatistics(BaseModel):
    total_pending_amount: Decimal = Decimal("0")
    total_approved_amount: Decimal = Decimal("0")
    total_paid_amount: Decimal = Decimal("0")
    pending_count: int = 0
    approved_count: int = 0
    paid_count: int = 0
    by_category: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict)