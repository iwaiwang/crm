"""合同附件模型"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ContractAttachment(Base):
    __tablename__ = "contract_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, comment="关联合同 ID")
    file_name = Column(String(255), nullable=False, comment="文件名称")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_url = Column(String(500), nullable=False, comment="文件访问 URL")
    file_type = Column(String(50), comment="文件类型 (pdf, jpg, png, doc, docx)")
    file_size = Column(String(50), comment="文件大小 (字节)")
    is_primary = Column(Boolean, default=False, comment="是否主合同文件")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    contract = relationship("Contract", back_populates="attachments")

    def __repr__(self):
        return f"<ContractAttachment {self.file_name}>"
