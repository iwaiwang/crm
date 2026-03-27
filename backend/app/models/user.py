"""用户模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean, Text
from sqlalchemy.sql import func
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(500), comment="头像 URL")
    role = Column(
        SQLEnum("admin", "user", name="user_role"),
        default="user",
        comment="角色",
    )
    is_active = Column(Boolean, default=True, comment="是否启用")
    menu_permissions = Column(Text, default="[]", comment="菜单权限 JSON 数组")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.username}>"
