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


# 报销种类
REIMBURSEMENT_KIND_INVOICE_COMPANY = "invoice_company"
REIMBURSEMENT_KIND_INVOICE_PERSONAL = "invoice_personal"
REIMBURSEMENT_KIND_ALLOWANCE_TRAVEL = "allowance_travel"

REIMBURSEMENT_KIND_LABELS = {
    "invoice_company": "发票·公司直付",
    "invoice_personal": "发票·个人垫付",
    "allowance_travel": "出差津贴",
}


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
    supplier_tax_id: Optional[str] = Field(None, description="收款方税号")
    supplier_bank_name: Optional[str] = Field(None, description="开户行")
    supplier_bank_account: Optional[str] = Field(None, description="银行账号")
    amount: Decimal = Field(..., ge=0, description="报销金额不含税")
    tax_amount: Optional[Decimal] = Field(Decimal("0"), description="税额")
    total_amount: Decimal = Field(..., ge=0, description="价税合计")
    expense_category: Optional[str] = Field("other", description="费用分类")
    payer_company: Optional[str] = Field(None, description="支付方公司名称")
    remark: Optional[str] = Field(None, description="备注说明")
    file_id: Optional[str] = Field(None, description="附件文件ID")
    file_url: Optional[str] = Field(None, description="附件文件URL")
    reimbursement_kind: Optional[str] = Field(REIMBURSEMENT_KIND_INVOICE_COMPANY, description="报销种类")
    travel_start_date: Optional[date] = Field(None, description="出差开始日期(津贴)")
    travel_end_date: Optional[date] = Field(None, description="出差结束日期(津贴)")
    travel_destination: Optional[str] = Field(None, description="出差地点(津贴)")


class ReimbursementCreate(ReimbursementBase):
    pass


class ReimbursementUpdate(BaseModel):
    supplier_name: Optional[str] = None
    supplier_tax_id: Optional[str] = None
    supplier_bank_name: Optional[str] = None
    supplier_bank_account: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    expense_category: Optional[str] = None
    payer_company: Optional[str] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    reimbursement_kind: Optional[str] = None
    travel_start_date: Optional[date] = None
    travel_end_date: Optional[date] = None
    travel_destination: Optional[str] = None


class ReimbursementReject(BaseModel):
    reason: str = Field(..., description="驳回原因")


class ReimbursementApprove(BaseModel):
    amount: Optional[Decimal] = Field(None, description="修改后的金额")
    expense_category: Optional[str] = Field(None, description="修改后的分类")


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
    can_approve: bool = False
    can_pay: bool = False
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


# AI 录入报销单相关 Schema
class AiReimbursementDraft(BaseModel):
    """AI 解析后的报销单草稿"""
    invoice_no: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_tax_id: Optional[str] = None
    supplier_bank_name: Optional[str] = None
    supplier_bank_account: Optional[str] = None
    amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    expense_category: str = "other"
    payer_company: Optional[str] = None
    issue_date: Optional[date] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: bool = True
    parse_confidence: Optional[float] = None


class AiReimbursementPreviewRequest(BaseModel):
    """AI 报销单预览请求"""
    file_id: str = Field(..., description="上传文件ID")


class AiReimbursementPreviewResponse(BaseModel):
    """AI 报销单预览响应"""
    reimbursement: AiReimbursementDraft
    suggested_actions: List[str] = Field(default_factory=list)
    raw_ai_result: Optional[Dict] = None


class AiReimbursementConfirmRequest(BaseModel):
    """AI 报销单确认请求"""
    reimbursement: AiReimbursementDraft
    create_supplier: bool = Field(False, description="是否同时创建收款方")
