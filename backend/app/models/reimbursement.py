"""报销单模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 来源信息
    source_type = Column(
        SQLEnum("invoice", "manual", name="reimbursement_source_type"),
        default="manual",
        comment="来源类型"
    )
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True, comment="关联进项发票ID")
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True, comment="关联合同ID")

    # 基本信息
    supplier_name = Column(String(100), nullable=False, comment="供应商/收款方名称")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="报销金额不含税")
    tax_amount = Column(DECIMAL(15, 2), default=0, comment="税额")
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="价税合计")
    expense_category = Column(
        SQLEnum(
            "catering", "travel", "procurement", "office", "rent",
            "utilities", "salary", "marketing", "software", "maintenance",
            "training", "entertainment", "logistics", "other",
            name="reimbursement_category"
        ),
        default="other",
        comment="费用分类"
    )
    remark = Column(Text, comment="备注说明")

    # 附件
    file_id = Column(String(36), comment="附件文件ID")
    file_url = Column(String(500), comment="附件文件URL")

    # 流程状态
    status = Column(
        SQLEnum("draft", "pending", "approved", "rejected", "paid", name="reimbursement_status"),
        default="draft",
        comment="状态"
    )

    # 操作记录
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False, comment="录入人ID")
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="审核人ID")
    approved_at = Column(DateTime(timezone=True), comment="审核时间")
    reject_reason = Column(Text, comment="驳回原因")
    paid_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="支付确认人ID")
    paid_at = Column(DateTime(timezone=True), comment="支付确认时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    invoice = relationship("Invoice", back_populates="reimbursements")
    contract = relationship("Contract", back_populates="reimbursements")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    payer = relationship("User", foreign_keys=[paid_by])

    def __repr__(self):
        return f"<Reimbursement {self.id} - {self.total_amount}>"