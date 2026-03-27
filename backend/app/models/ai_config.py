"""AI 服务配置模型"""
from sqlalchemy import Column, String, Boolean, Float, DateTime
from datetime import datetime
from app.database import Base


class AIConfig(Base):
    """AI 服务配置"""
    __tablename__ = "ai_configs"

    id = Column(String(36), primary_key=True)
    service_type = Column(String(50), default="openai_compatible", comment="服务类型：openai_compatible | ollama")
    api_base_url = Column(String(500), comment="API 基础 URL")
    api_key = Column(String(500), comment="API Key")
    model = Column(String(100), comment="模型名称")
    ollama_base_url = Column(String(500), default="http://localhost:11434", comment="Ollama 基础 URL")
    ollama_model = Column(String(100), comment="Ollama 模型名称")
    timeout = Column(Float, default=120, comment="请求超时（秒）")
    enabled = Column(Boolean, default=True, comment="是否启用")
    health_status = Column(String(20), default="unknown", comment="健康状态：unknown | healthy | unhealthy")
    last_health_check = Column(DateTime, comment="最后健康检查时间")
