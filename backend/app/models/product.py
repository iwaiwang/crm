"""产品库存模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, comment="产品名称")
    spec = Column(String(100), comment="规格型号")
    unit = Column(String(20), default="件", comment="单位")
    price = Column(DECIMAL(15, 2), default=0, comment="单价")
    stock_qty = Column(Integer, default=0, comment="库存数量")
    min_stock = Column(Integer, default=0, comment="安全库存")
    category = Column(String(50), comment="分类")
    is_active = Column(Boolean, default=True, comment="是否启用")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    stock_moves = relationship("StockMove", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name}>"


class StockMove(Base):
    """出入库记录"""
    __tablename__ = "stock_moves"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    type = Column(
        SQLEnum("in", "out", name="stock_move_type"),
        nullable=False,
        comment="出入库类型",
    )
    qty = Column(Integer, nullable=False, default=0, comment="数量")
    reason = Column(
        SQLEnum("purchase", "sales", "return_in", "return_out", "adjustment", name="stock_move_reason"),
        comment="原因",
    )
    ref_type = Column(String(50), comment="关联类型 (contract/order)")
    ref_id = Column(String(36), comment="关联单据 ID")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    product = relationship("Product", back_populates="stock_moves")

    def __repr__(self):
        return f"<StockMove {self.type} {self.qty}>"
