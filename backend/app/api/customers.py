"""客户管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional

from app.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse

router = APIRouter()


@router.get("", response_model=CustomerListResponse)
async def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取客户列表（支持搜索、筛选、分页）"""
    query = select(Customer)

    # 搜索
    if search:
        query = query.where(
            (Customer.name.contains(search)) |
            (Customer.contact.contains(search)) |
            (Customer.phone.contains(search))
        )

    # 筛选
    if category:
        query = query.where(Customer.category == category)
    if status:
        query = query.where(Customer.status == status)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    customers = result.scalars().all()

    return CustomerListResponse(
        total=total,
        items=[CustomerResponse.model_validate(c) for c in customers]
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """获取客户详情"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    return CustomerResponse.model_validate(customer)


@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """创建客户"""
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)

    return CustomerResponse.model_validate(db_customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, customer: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    """更新客户"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    db_customer = result.scalar_one_or_none()

    if not db_customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = customer.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    await db.commit()
    await db.refresh(db_customer)

    return CustomerResponse.model_validate(db_customer)


@router.post("/batch-delete")
async def batch_delete_customers(ids: list[str], db: AsyncSession = Depends(get_db)):
    """批量删除客户"""
    from sqlalchemy import text

    # 检查是否有关联的合同或项目
    from app.models.contract import Contract
    from app.models.project import Project

    for customer_id in ids:
        contract_result = await db.execute(select(Contract).where(Contract.customer_id == customer_id))
        contracts = contract_result.scalars().all()
        if contracts:
            raise HTTPException(status_code=400, detail=f"客户 {customer_id} 下存在合同，无法批量删除")

        project_result = await db.execute(select(Project).where(Project.customer_id == customer_id))
        projects = project_result.scalars().all()
        if projects:
            raise HTTPException(status_code=400, detail=f"客户 {customer_id} 下存在项目，无法批量删除")

    # 删除关联记录和 customers
    for customer_id in ids:
        await db.execute(text("DELETE FROM incomes WHERE customer_id = :cid"), {"cid": customer_id})
        await db.execute(text("DELETE FROM expenses WHERE supplier_id = :sid"), {"sid": customer_id})
        await db.execute(text("DELETE FROM contracts WHERE customer_id = :cid"), {"cid": customer_id})
        await db.execute(text("DELETE FROM projects WHERE customer_id = :cid"), {"cid": customer_id})

    await db.commit()
    await db.close()

    # 批量删除 customers
    result = await db.execute(select(Customer).where(Customer.id.in_(ids)))
    customers = result.scalars().all()
    for customer in customers:
        await db.delete(customer)

    await db.commit()

    return {"message": f"成功删除 {len(ids)} 个客户"}


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """删除客户"""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    # 检查是否有关联的合同
    from app.models.contract import Contract
    from app.models.project import Project

    # 先检查合同和项目（这些不能删除）
    contract_result = await db.execute(select(Contract).where(Contract.customer_id == customer_id))
    contracts = contract_result.scalars().all()
    if contracts:
        raise HTTPException(status_code=400, detail=f"客户下存在 {len(contracts)} 个合同，无法删除")

    project_result = await db.execute(select(Project).where(Project.customer_id == customer_id))
    projects = project_result.scalars().all()
    if projects:
        raise HTTPException(status_code=400, detail=f"客户下存在 {len(projects)} 个项目，无法删除")

    # 使用原始 SQL 删除关联的记录（避免 SQLAlchemy 级联问题）
    await db.execute(text("DELETE FROM incomes WHERE customer_id = :cid"), {"cid": customer_id})
    await db.execute(text("DELETE FROM expenses WHERE supplier_id = :sid"), {"sid": customer_id})
    await db.execute(text("DELETE FROM contracts WHERE customer_id = :cid"), {"cid": customer_id})
    await db.execute(text("DELETE FROM projects WHERE customer_id = :cid"), {"cid": customer_id})
    await db.commit()

    # 关闭并重新创建 session（清除所有缓存的对象）
    await db.close()

    # 重新获取客户并删除（使用新的 session）
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    db_customer = result.scalar_one_or_none()
    if db_customer:
        await db.delete(db_customer)
        await db.commit()

    return {"message": "删除成功"}
