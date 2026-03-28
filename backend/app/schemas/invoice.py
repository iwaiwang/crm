"""发票 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class InvoiceType(str, Enum):
    NORMAL = "normal"
    SPECIAL = "special"


class InvoiceDirectionType(str, Enum):
    SALES = "sales"        # 销项发票（本公司开具给客户的发票）
    PURCHASE = "purchase"  # 进项发票（客户开具给本公司的发票）


class InvoiceStatus(str, Enum):
    PENDING = "pending"      # 待开票
    ISSUED = "issued"        # 已开具
    SENT = "sent"            # 已寄送
    RECEIVED = "received"    # 已收到
    NORMAL = "normal"        # 正常
    VOID = "void"            # 作废


class InvoiceBase(BaseModel):
    invoice_code: Optional[str] = Field(None, description="发票代码", max_length=20)
    invoice_number: Optional[str] = Field(None, description="发票号码", max_length=20)
    check_code: Optional[str] = Field(None, description="校验码", max_length=20)
    invoice_date: Optional[date] = Field(None, description="开票日期")
    invoice_no: Optional[str] = Field(None, description="发票号码", max_length=50)
    contract_id: Optional[str] = Field(None, description="关联合同（可选）")
    amount: Decimal = Field(default=0, description="发票金额")
    tax_rate: Decimal = Field(default=0, description="税率")
    tax_amount: Optional[Decimal] = Field(None, description="税额")
    total_amount: Optional[Decimal] = Field(None, description="价税合计")
    type: InvoiceType = Field(default=InvoiceType.NORMAL, description="发票类型")
    invoice_type: InvoiceDirectionType = Field(default=InvoiceDirectionType.SALES, description="发票方向：销项/进项")
    buyer_name: Optional[str] = Field(None, description="购买方名称", max_length=200)
    buyer_tax_id: Optional[str] = Field(None, description="购买方税号", max_length=50)
    seller_name: Optional[str] = Field(None, description="销售方名称", max_length=200)
    seller_tax_id: Optional[str] = Field(None, description="销售方税号", max_length=50)
    issue_date: Optional[date] = Field(None, description="开票日期")
    due_date: Optional[date] = Field(None, description="应开票日期")
    status: InvoiceStatus = Field(default=InvoiceStatus.NORMAL, description="发票状态")
    remark: Optional[str] = Field(None, description="备注")


class InvoiceCreate(InvoiceBase):
    file_id: Optional[str] = Field(None, description="上传文件 ID")
    file_url: Optional[str] = Field(None, description="文件访问 URL")
    ai_parsed: Optional[bool] = Field(False, description="是否 AI 解析")
    parsed_at: Optional[datetime] = Field(None, description="AI 解析时间")
    parse_confidence: Optional[float] = Field(None, description="AI 解析置信度")


class InvoiceUpdate(BaseModel):
    invoice_code: Optional[str] = Field(None, max_length=20)
    invoice_number: Optional[str] = Field(None, max_length=20)
    check_code: Optional[str] = Field(None, max_length=20)
    invoice_date: Optional[date] = None
    invoice_no: Optional[str] = Field(None, max_length=50)
    contract_id: Optional[str] = Field(None, description="关联合同（可选）")
    amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    type: Optional[InvoiceType] = None
    buyer_name: Optional[str] = Field(None, max_length=200)
    buyer_tax_id: Optional[str] = Field(None, max_length=50)
    seller_name: Optional[str] = Field(None, max_length=200)
    seller_tax_id: Optional[str] = Field(None, max_length=50)
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: Optional[bool] = None
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None


class InvoiceResponse(InvoiceBase):
    id: str
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: Optional[bool] = False
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    total: int
    items: List[InvoiceResponse]


class AiInvoiceDraft(BaseModel):
    invoice_code: Optional[str] = Field(default=None, description="发票代码")
    invoice_number: Optional[str] = Field(default=None, description="发票号码")
    check_code: Optional[str] = Field(default=None, description="校验码")
    invoice_date: Optional[date] = Field(default=None, description="原始开票日期")
    invoice_no: Optional[str] = Field(default=None, description="发票号")
    contract_id: Optional[str] = Field(default=None, description="推荐合同 ID")
    amount: Decimal = Field(default=0, description="不含税金额")
    tax_rate: Decimal = Field(default=0, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="价税合计")
    type: InvoiceType = Field(default=InvoiceType.NORMAL, description="发票种类：专票/普票")
    invoice_type: InvoiceDirectionType = Field(default=InvoiceDirectionType.SALES, description="发票方向：销项/进项")
    buyer_name: Optional[str] = Field(default=None, description="购买方名称")
    buyer_tax_id: Optional[str] = Field(default=None, description="购买方税号")
    seller_name: Optional[str] = Field(default=None, description="销售方名称")
    seller_tax_id: Optional[str] = Field(default=None, description="销售方税号")
    issue_date: Optional[date] = Field(default=None, description="开票日期")
    due_date: Optional[date] = Field(default=None, description="应开票日期")
    status: InvoiceStatus = Field(default=InvoiceStatus.NORMAL, description="发票状态")
    remark: Optional[str] = Field(default=None, description="备注")
    file_id: Optional[str] = Field(default=None, description="上传文件 ID")
    file_url: Optional[str] = Field(default=None, description="文件 URL")
    ai_parsed: Optional[bool] = Field(default=True, description="是否 AI 解析")
    parse_confidence: Optional[float] = Field(default=None, description="AI 解析置信度")


class AiInvoiceContractMatch(BaseModel):
    contract_id: str
    contract_no: str
    contract_name: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    amount: Decimal = Field(default=0, description="合同金额")
    score: float = Field(default=0, description="匹配分")
    reason: Optional[str] = Field(default=None, description="匹配说明")


class AiInvoiceReceivableMatch(BaseModel):
    receivable_id: str
    contract_id: str
    due_date: Optional[date] = None
    amount: Decimal = Field(default=0, description="应收金额")
    received_amount: Decimal = Field(default=0, description="已收金额")
    unpaid_amount: Decimal = Field(default=0, description="未收金额")
    status: Optional[str] = Field(default=None, description="状态")
    remark: Optional[str] = Field(default=None, description="备注")
    score: float = Field(default=0, description="匹配分")
    reason: Optional[str] = Field(default=None, description="匹配说明")


class AiInvoicePaymentDraft(BaseModel):
    receivable_id: Optional[str] = Field(default=None, description="关联应收 ID")
    amount: Decimal = Field(default=0, description="收款金额")
    payment_date: Optional[date] = Field(default=None, description="收款日期")
    payment_method: Optional[str] = Field(default=None, description="收款方式")
    remark: Optional[str] = Field(default=None, description="备注")


class AiInvoiceIncomeDraft(BaseModel):
    amount: Decimal = Field(default=0, description="收入金额")
    income_date: Optional[date] = Field(default=None, description="收入日期")
    income_category: Optional[str] = Field(default="sales", description="收入分类")
    payment_method: Optional[str] = Field(default=None, description="收款方式")
    remark: Optional[str] = Field(default=None, description="备注")


class AiInvoiceExpenseDraft(BaseModel):
    supplier_id: Optional[str] = Field(default=None, description="供应商 ID")
    supplier_name: Optional[str] = Field(default=None, description="供应商名称")
    contract_id: Optional[str] = Field(default=None, description="关联合同 ID")
    amount: Decimal = Field(default=0, description="不含税金额")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Decimal = Field(default=0, description="价税合计")
    expense_date: Optional[date] = Field(default=None, description="支出日期")
    expense_category: Optional[str] = Field(default="other", description="支出分类")
    payment_method: Optional[str] = Field(default=None, description="支付方式")
    remark: Optional[str] = Field(default=None, description="备注")


class InvoiceAiPreviewRequest(BaseModel):
    file_id: str = Field(..., description="上传文件 ID")


class InvoiceAiPreviewResponse(BaseModel):
    invoice: AiInvoiceDraft
    matching_contracts: List[AiInvoiceContractMatch] = Field(default_factory=list)
    matching_receivables: List[AiInvoiceReceivableMatch] = Field(default_factory=list)
    payment: Optional[AiInvoicePaymentDraft] = Field(default=None, description="建议收款草稿")
    income: Optional[AiInvoiceIncomeDraft] = Field(default=None, description="收入草稿")
    expense: Optional[AiInvoiceExpenseDraft] = Field(default=None, description="支出草稿")
    suggested_actions: List[str] = Field(default_factory=list, description="建议执行摘要")
    raw_ai_result: Optional[dict] = Field(default=None, description="原始 AI 输出")


class InvoiceAiConfirmRequest(BaseModel):
    invoice: AiInvoiceDraft
    create_payment: bool = Field(default=False, description="是否同步登记收款")
    payment: Optional[AiInvoicePaymentDraft] = Field(default=None, description="收款草稿")
    create_income: bool = Field(default=False, description="是否创建收入")
    income: Optional[AiInvoiceIncomeDraft] = Field(default=None, description="收入草稿")
    create_expense: bool = Field(default=False, description="是否创建支出")
    expense: Optional[AiInvoiceExpenseDraft] = Field(default=None, description="支出草稿")
