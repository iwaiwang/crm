"""系统设置模型"""
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.database import Base


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True, comment="设置键")
    value = Column(Text, comment="设置值")
    value_type = Column(String(20), default="string", comment="值类型：string, number, boolean, json")
    description = Column(String(500), comment="设置描述")
    is_public = Column(Boolean, default=False, comment="是否公开（前端可访问）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"
