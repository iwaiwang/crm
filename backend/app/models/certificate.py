"""数字证书模型"""
from sqlalchemy import Column, String, DateTime, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cert_serial = Column(String(40), unique=True, nullable=True, comment="X.509 序列号")
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, comment="医院客户ID")
    product_name = Column(String(200), nullable=False, comment="软件产品名称")
    start_date = Column(Date, nullable=False, comment="有效期开始")
    end_date = Column(Date, nullable=False, comment="有效期结束")
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending|approved|rejected|active|expired|revoked",
    )
    applicant_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="申请人ID")
    approver_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="一级审批人ID")
    final_approver_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="二级审批人ID")
    reject_reason = Column(Text, nullable=True, comment="驳回原因")
    certificate_pem = Column(Text, nullable=True, comment="X.509 证书 PEM")
    private_key_pem = Column(Text, nullable=True, comment="RSA 私钥 PEM (加密存储)")
    issued_at = Column(DateTime(timezone=True), nullable=True, comment="签发时间")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    revoked_at = Column(DateTime(timezone=True), nullable=True, comment="吊销时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    customer = relationship("Customer", back_populates="certificates")
    applicant = relationship("User", foreign_keys=[applicant_id])
    approver = relationship("User", foreign_keys=[approver_id])
    final_approver = relationship("User", foreign_keys=[final_approver_id])

    def __repr__(self):
        return f"<Certificate {self.cert_serial or 'pending'} - {self.product_name}>"
