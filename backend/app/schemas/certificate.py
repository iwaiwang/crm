"""数字证书 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class CertificateCreate(BaseModel):
    customer_id: str = Field(..., description="医院客户ID")
    product_name: str = Field(..., description="软件产品名称")
    start_date: date = Field(..., description="有效期开始")
    duration_months: int = Field(12, ge=3, le=36, description="有效期月数")


class CertificateUpdate(BaseModel):
    product_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CertificateReject(BaseModel):
    reason: str = Field(..., min_length=1, description="驳回原因")


class CertificateResponse(BaseModel):
    id: str
    cert_serial: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = ""
    product_name: str
    start_date: date
    end_date: date
    status: str
    applicant_id: str
    applicant_name: Optional[str] = ""
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None
    final_approver_id: Optional[str] = None
    final_approver_name: Optional[str] = None
    reject_reason: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    can_approve: bool = False
    can_final_approve: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificateListResponse(BaseModel):
    total: int
    items: List[CertificateResponse]


class CertificateStatsItem(BaseModel):
    id: str
    customer_name: str = ""
    product_name: str
    end_date: str
    days_remaining: int = 0
    days_overdue: int = 0


class CertificateStats(BaseModel):
    active_count: int = 0
    expiring_soon_count: int = 0
    expired_count: int = 0
    expiring_soon_items: List[CertificateStatsItem] = []
    expired_items: List[CertificateStatsItem] = []
