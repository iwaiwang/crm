from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "小微企业 CRM 系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/crm.db"

    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 小时

    # 文件上传配置
    # 使用绝对路径，确保静态文件挂载正确
    UPLOAD_DIR: str = r"D:\工作\007-project\claude-code-test\crm-system\backend\data\uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Webhook API Key (OpenClaw 调用时使用)
    WEBHOOK_API_KEY: Optional[str] = None

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", ""}:
                return False
        return value

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
