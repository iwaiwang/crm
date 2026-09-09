"""报销单附件模型"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ReimbursementFile(Base):
    __tablename__ = "reimbursement_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reimbursement_id = Column(
        String(36),
        ForeignKey("reimbursements.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联报销单ID",
    )
    file_id = Column(String(36), nullable=False, comment="上传文件ID")
    file_name = Column(String(255), comment="原始文件名")
    file_url = Column(String(500), comment="文件访问URL")
    file_type = Column(String(50), comment="文件扩展名")
    file_size = Column(Integer, comment="文件大小(字节)")
    sort_order = Column(Integer, default=0, nullable=False, comment="显示顺序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reimbursement = relationship("Reimbursement", back_populates="files")

    def __repr__(self):
        return f"<ReimbursementFile {self.file_name}>"
