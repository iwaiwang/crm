"""Contract file model."""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ContractFile(Base):
    __tablename__ = "contract_files"
    __table_args__ = (
        Index("ix_contract_files_contract_id", "contract_id"),
        Index(
            "ux_contract_files_primary_per_contract",
            "contract_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
        ),
        UniqueConstraint("file_id", name="uq_contract_files_file_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(
        String(36),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        comment="Related contract ID",
    )
    file_id = Column(String(36), nullable=False, comment="Uploaded file ID")
    file_name = Column(String(255), nullable=False, comment="Original file name")
    file_path = Column(String(500), nullable=False, comment="Stored file path")
    file_url = Column(String(500), nullable=False, comment="Public file URL")
    file_type = Column(String(50), comment="File extension")
    file_size = Column(Integer, comment="File size in bytes")
    source = Column(String(32), default="manual", nullable=False, comment="manual or ai_import")
    is_primary = Column(Boolean, default=False, nullable=False, comment="Primary contract file")
    sort_order = Column(Integer, default=0, nullable=False, comment="Display order")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contract = relationship("Contract", back_populates="files")

    def __repr__(self):
        return f"<ContractFile {self.file_name}>"
