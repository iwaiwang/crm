"""Contract model."""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_no = Column(String(50), unique=True, nullable=False, comment="Contract number")
    name = Column(String(200), nullable=False, comment="Contract name")
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, comment="Customer ID")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="Contract amount")
    start_date = Column(Date, comment="Start date")
    end_date = Column(Date, comment="End date")
    status = Column(
        SQLEnum("signed", "in_progress", "completed", "terminated", name="contract_status"),
        default="signed",
        comment="Contract status",
    )
    ai_parsed = Column(Boolean, default=False, comment="Parsed by AI")
    parsed_at = Column(DateTime(timezone=True), comment="AI parse time")
    parse_confidence = Column(Float, comment="AI parse confidence")
    payment_terms = Column(Text, comment="Payment terms")
    remark = Column(Text, comment="Remark")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="contracts")
    invoices = relationship("Invoice", back_populates="contract", cascade="all, delete-orphan", passive_deletes=True)
    receivables = relationship("Receivable", back_populates="contract", cascade="all, delete-orphan", passive_deletes=True)
    project = relationship("Project", back_populates="contract", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    expenses = relationship("Expense", back_populates="contract", cascade="all, delete-orphan", passive_deletes=True)
    files = relationship("ContractFile", back_populates="contract", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def primary_file(self):
        if not self.files:
            return None

        for contract_file in self.files:
            if contract_file.is_primary:
                return contract_file

        return sorted(
            self.files,
            key=lambda item: (
                item.sort_order if item.sort_order is not None else 0,
                item.created_at.isoformat() if item.created_at else "",
            ),
        )[0]

    def __repr__(self):
        return f"<Contract {self.contract_no}>"
