"""合同 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ContractStatus(str, Enum):
    SIGNED = "signed"  # 签约
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 完毕
    TERMINATED = "terminated"  # 终止


class ContractBase(BaseModel):
    contract_no: str = Field(..., description="合同编号", max_length=50)
    name: str = Field(..., description="合同名称", max_length=200)
    customer_id: str = Field(..., description="关联客户")
    amount: Decimal = Field(default=0, description="合同金额")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    status: ContractStatus = Field(default=ContractStatus.SIGNED, description="合同状态")
    payment_terms: Optional[str] = Field(None, description="付款条款")
    remark: Optional[str] = Field(None, description="备注")


class ContractCreate(ContractBase):
    file_id: Optional[str] = Field(None, description="上传文件 ID")
    file_url: Optional[str] = Field(None, description="文件访问 URL")
    ai_parsed: Optional[bool] = Field(False, description="是否 AI 解析")
    parsed_at: Optional[datetime] = Field(None, description="AI 解析时间")
    parse_confidence: Optional[float] = Field(None, description="AI 解析置信度")


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
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: Optional[bool] = None
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None


class ContractResponse(ContractBase):
    id: str
    file_path: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    ai_parsed: Optional[bool] = False
    parsed_at: Optional[datetime] = None
    parse_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    attachments: Optional[List["AttachmentResponse"]] = None

    class Config:
        from_attributes = True


class AttachmentResponse(BaseModel):
    """合同附件响应"""
    id: str
    file_name: str
    file_path: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[str] = None
    is_primary: Optional[bool] = False
    created_at: datetime

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    total: int
    items: List[ContractResponse]
