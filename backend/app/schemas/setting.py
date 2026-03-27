"""系统设置 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SettingBase(BaseModel):
    value: str = Field(..., description="设置值")
    value_type: str = Field(default="string", description="值类型：string, number, boolean, json")
    description: Optional[str] = Field(None, description="设置描述", max_length=500)
    is_public: bool = Field(default=False, description="是否公开（前端可访问）")


class SettingCreate(SettingBase):
    key: str = Field(..., description="设置键", max_length=100)


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class SettingResponse(SettingBase):
    key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingListResponse(BaseModel):
    total: int
    items: List[SettingResponse]


# 预定义设置键
class SettingKeys:
    # 公司信息
    COMPANY_NAME = "company_name"
    COMPANY_TAX_ID = "company_tax_id"
    COMPANY_BANK_ACCOUNT = "company_bank_account"
    COMPANY_ADDRESS = "company_address"
    COMPANY_PHONE = "company_phone"
    COMPANY_EMAIL = "company_email"

    # 数据库配置
    DATABASE_DIRECTORY = "database_directory"

    # 其他设置
    OCR_ENABLED = "ocr_enabled"
    AI_ENABLED = "ai_enabled"
