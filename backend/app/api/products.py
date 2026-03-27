"""产品库存 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.product import Product, StockMove
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    StockMoveCreate, StockMoveResponse
)

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    low_stock: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取产品列表"""
    query = select(Product).where(Product.is_active == True)

    if search:
        query = query.where(
            (Product.name.contains(search)) |
            (Product.spec.contains(search))
        )
    if category:
        query = query.where(Product.category == category)
    if low_stock:
        query = query.where(Product.stock_qty <= Product.min_stock)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Product.name.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        total=total,
        items=[ProductResponse.model_validate(p) for p in products]
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """获取产品详情"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """创建产品"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return ProductResponse.model_validate(db_product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductUpdate, db: AsyncSession = Depends(get_db)):
    """更新产品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    await db.commit()
    await db.refresh(db_product)

    return ProductResponse.model_validate(db_product)


@router.delete("/{product_id}")
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """删除产品（软删除）"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    db_product.is_active = False
    await db.commit()

    return {"message": "删除成功"}


@router.post("/stock-move", response_model=StockMoveResponse)
async def create_stock_move(move: StockMoveCreate, db: AsyncSession = Depends(get_db)):
    """出入库操作"""
    result = await db.execute(select(Product).where(Product.id == move.product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    db_move = StockMove(**move.model_dump())
    db.add(db_move)

    if move.type == "in":
        db_product.stock_qty += move.qty
    else:
        if db_product.stock_qty < move.qty:
            raise HTTPException(status_code=400, detail="库存不足")
        db_product.stock_qty -= move.qty

    await db.commit()
    await db.refresh(db_move)

    return StockMoveResponse.model_validate(db_move)


@router.get("/{product_id}/stock-moves", response_model=list[StockMoveResponse])
async def get_product_stock_moves(product_id: str, db: AsyncSession = Depends(get_db)):
    """获取产品出入库记录"""
    result = await db.execute(
        select(StockMove)
        .where(StockMove.product_id == product_id)
        .order_by(StockMove.created_at.desc())
    )
    moves = result.scalars().all()

    return [StockMoveResponse.model_validate(m) for m in moves]
