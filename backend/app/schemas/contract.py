"""Contract schemas."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ContractStatus(str, Enum):
    SIGNED = "signed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ContractBase(BaseModel):
    contract_no: str = Field(..., description="Contract number", max_length=50)
    name: str = Field(..., description="Contract name", max_length=200)
    customer_id: str = Field(..., description="Customer ID")
    amount: Decimal = Field(default=0, description="Contract amount")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    status: ContractStatus = Field(default=ContractStatus.SIGNED, description="Contract status")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    remark: Optional[str] = Field(None, description="Remark")


class ContractCreate(ContractBase):
    file_id: Optional[str] = Field(None, description="Uploaded file ID for the primary file")
    file_url: Optional[str] = Field(None, description="Uploaded file URL")
    ai_parsed: Optional[bool] = Field(False, description="Parsed by AI")
    parsed_at: Optional[datetime] = Field(None, description="AI parse time")
    parse_confidence: Optional[float] = Field(None, description="AI parse confidence")


class ContractUpdate(BaseModel):
    contract_no: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    customer_id: Optional[str] = None
    amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ContractStatus] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None
    ai_parsed: Optional[bool] = None
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None


class ContractFileResponse(BaseModel):
    id: str
    file_id: str
    file_name: str
    file_path: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    source: str
    is_primary: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractResponse(ContractBase):
    id: str
    ai_parsed: Optional[bool] = False
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    files: List[ContractFileResponse] = Field(default_factory=list)
    primary_file: Optional[ContractFileResponse] = None

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    total: int
    items: List[ContractResponse]


class AiReceivableDraft(BaseModel):
    amount: Decimal = Field(default=0, description="Receivable amount")
    percent: Optional[float] = Field(default=None, description="Payment percent")
    due_date: Optional[date] = Field(default=None, description="Due date")
    remark: Optional[str] = Field(default=None, description="Remark")


class AiContractDraft(BaseModel):
    contract_no: Optional[str] = Field(default=None, description="Contract number")
    name: Optional[str] = Field(default=None, description="Contract name")
    customer_id: Optional[str] = Field(default=None, description="Matched customer ID")
    customer_name: Optional[str] = Field(default=None, description="Customer name from AI")
    amount: Decimal = Field(default=0, description="Contract amount")
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")
    status: ContractStatus = Field(default=ContractStatus.SIGNED, description="Contract status")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    remark: Optional[str] = Field(default=None, description="Remark")
    file_id: Optional[str] = Field(default=None, description="Uploaded file ID")
    file_url: Optional[str] = Field(default=None, description="Uploaded file URL")
    ai_parsed: Optional[bool] = Field(default=True, description="Parsed by AI")
    parse_confidence: Optional[float] = Field(default=None, description="AI parse confidence")


class ContractAiPreviewRequest(BaseModel):
    file_id: str = Field(..., description="Uploaded file ID")


class ContractAiPreviewResponse(BaseModel):
    contract: AiContractDraft
    receivables: List[AiReceivableDraft]
    raw_ai_result: Optional[dict] = Field(default=None, description="Raw AI result")
    matching_customer_names: List[str] = Field(default_factory=list, description="Matched customer names")


class ContractAiConfirmRequest(BaseModel):
    contract: AiContractDraft
    receivables: List[AiReceivableDraft] = Field(default_factory=list)
