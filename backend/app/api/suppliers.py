"""收款方管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models.supplier import Supplier, SupplierType, SupplierStatus
from app.models.user import User
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
)
from app.api.auth import get_current_user, require_menu_permission

router = APIRouter()


@router.get("", response_model=SupplierListResponse)
async def get_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    supplier_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取收款方列表"""
    query = select(Supplier)

    if search:
        query = query.where(Supplier.name.contains(search))

    if supplier_type:
        query = query.where(Supplier.supplier_type == supplier_type)

    if status:
        query = query.where(Supplier.status == status)

    # 获取总数
    count_query = select(func.count()).select_from(Supplier)
    if search:
        count_query = count_query.where(Supplier.name.contains(search))
    if supplier_type:
        count_query = count_query.where(Supplier.supplier_type == supplier_type)
    if status:
        count_query = count_query.where(Supplier.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    query = query.order_by(Supplier.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    suppliers = result.scalars().all()

    return SupplierListResponse(
        total=total,
        items=[SupplierResponse.model_validate(s) for s in suppliers]
    )


@router.get("/search")
async def search_suppliers(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜索收款方（用于自动补全）"""
    query = select(Supplier).where(Supplier.name.contains(keyword)).limit(limit)
    result = await db.execute(query)
    suppliers = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "supplier_type": s.supplier_type,
            "tax_id": s.tax_id,
            "id_card": s.id_card,
            "bank_name": s.bank_name,
            "bank_province": s.bank_province,
            "bank_branch": s.bank_branch,
            "bank_account": s.bank_account,
            "bank_code": s.bank_code,
            "account_type": s.account_type,
        }
        for s in suppliers
    ]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取收款方详情"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="收款方不存在")

    return SupplierResponse.model_validate(supplier)


@router.post("", response_model=SupplierResponse)
async def create_supplier(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("suppliers")),
):
    """创建收款方"""
    # 检查名称是否重复
    result = await db.execute(select(Supplier).where(Supplier.name == supplier.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="收款方名称已存在")

    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    await db.commit()
    await db.refresh(db_supplier)

    return SupplierResponse.model_validate(db_supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("suppliers")),
):
    """更新收款方"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    db_supplier = result.scalar_one_or_none()

    if not db_supplier:
        raise HTTPException(status_code=404, detail="收款方不存在")

    # 检查名称是否重复（如果修改了名称）
    if supplier.name and supplier.name != db_supplier.name:
        exist_result = await db.execute(select(Supplier).where(Supplier.name == supplier.name))
        if exist_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="收款方名称已存在")

    update_data = supplier.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_supplier, field, value)

    await db.commit()
    await db.refresh(db_supplier)

    return SupplierResponse.model_validate(db_supplier)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("suppliers")),
):
    """删除收款方"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(status_code=404, detail="收款方不存在")

    await db.delete(supplier)
    await db.commit()

    return {"message": "删除成功"}