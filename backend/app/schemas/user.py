"""用户认证 Schema"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import json


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    menu_permissions: Optional[List[str]] = None


class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: str
    role: str
    is_active: bool
    avatar: Optional[str] = None
    menu_permissions: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator('menu_permissions', mode='before')
    @classmethod
    def parse_menu_permissions(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return value if value else []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
