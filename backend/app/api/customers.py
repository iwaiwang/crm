"""客户管理 API"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.customer import Customer
from app.models.customer_contact import CustomerContact
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse,
    ContactCreate, ContactUpdate, ContactResponse,
)

router = APIRouter()


# ── 辅助函数 ──────────────────────────────────────────────────

async def _build_customer_response(customer: Customer) -> CustomerResponse:
    """将 Customer ORM 对象转为 CustomerResponse，含联系人列表"""
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        address=customer.address,
        category=customer.category,
        status=customer.status,
        remark=customer.remark,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        contacts=[
            ContactResponse.model_validate(c) for c in (customer.contacts or [])
        ],
    )


# ── 客户 CRUD ─────────────────────────────────────────────────

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

    # 搜索 - 同时搜索客户名称和联系人姓名/电话
    if search:
        query = query.outerjoin(Customer.contacts).where(
            (Customer.name.contains(search)) |
            (CustomerContact.name.contains(search)) |
            (CustomerContact.phone.contains(search))
        ).distinct()

    # 筛选
    if category:
        query = query.where(Customer.category == category)
    if status:
        query = query.where(Customer.status == status)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页 - eager load contacts
    query = query.options(selectinload(Customer.contacts))
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    customers = result.unique().scalars().all()

    return CustomerListResponse(
        total=total,
        items=[await _build_customer_response(c) for c in customers]
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """获取客户详情"""
    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    return await _build_customer_response(customer)


@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """创建客户"""
    contact_data = customer.contacts
    customer_data = customer.model_dump(exclude={"contacts"})

    customer_id = str(uuid.uuid4())
    db_customer = Customer(id=customer_id, **customer_data)
    db.add(db_customer)

    for c in contact_data:
        db_contact = CustomerContact(id=str(uuid.uuid4()), customer_id=customer_id, **c.model_dump())
        db.add(db_contact)

    await db.commit()
    await db.refresh(db_customer)

    # 重新加载带 contacts 的完整对象
    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(Customer.id == db_customer.id)
    )
    db_customer = result.scalar_one()

    return await _build_customer_response(db_customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, customer: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    """更新客户"""
    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(Customer.id == customer_id)
    )
    db_customer = result.scalar_one_or_none()

    if not db_customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = customer.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    await db.commit()
    await db.refresh(db_customer)

    return await _build_customer_response(db_customer)


@router.post("/batch-delete")
async def batch_delete_customers(ids: list[str], db: AsyncSession = Depends(get_db)):
    """批量删除客户"""
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

    # cascade 会自动删除 contacts，手动清理其他关联
    for customer_id in ids:
        await db.execute(text("DELETE FROM incomes WHERE customer_id = :cid"), {"cid": customer_id})
        await db.execute(text("DELETE FROM expenses WHERE supplier_id = :sid"), {"sid": customer_id})
        await db.execute(text("DELETE FROM contracts WHERE customer_id = :cid"), {"cid": customer_id})
        await db.execute(text("DELETE FROM projects WHERE customer_id = :cid"), {"cid": customer_id})

    await db.commit()

    result = await db.execute(select(Customer).where(Customer.id.in_(ids)))
    customers = result.scalars().all()
    for customer in customers:
        await db.delete(customer)

    await db.commit()

    return {"message": f"成功删除 {len(ids)} 个客户"}


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """删除客户"""
    from app.models.contract import Contract
    from app.models.project import Project

    contract_result = await db.execute(select(Contract).where(Contract.customer_id == customer_id))
    contracts = contract_result.scalars().all()
    if contracts:
        raise HTTPException(status_code=400, detail=f"客户下存在 {len(contracts)} 个合同，无法删除")

    project_result = await db.execute(select(Project).where(Project.customer_id == customer_id))
    projects = project_result.scalars().all()
    if projects:
        raise HTTPException(status_code=400, detail=f"客户下存在 {len(projects)} 个项目，无法删除")

    await db.execute(text("DELETE FROM incomes WHERE customer_id = :cid"), {"cid": customer_id})
    await db.execute(text("DELETE FROM expenses WHERE supplier_id = :sid"), {"sid": customer_id})
    await db.execute(text("DELETE FROM contracts WHERE customer_id = :cid"), {"cid": customer_id})
    await db.execute(text("DELETE FROM projects WHERE customer_id = :cid"), {"cid": customer_id})
    await db.commit()

    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    db_customer = result.scalar_one_or_none()
    if db_customer:
        await db.delete(db_customer)
        await db.commit()

    return {"message": "删除成功"}


# ── 联系人 CRUD（嵌套路由）────────────────────────────────────

@router.get("/{customer_id}/contacts", response_model=list[ContactResponse])
async def get_contacts(customer_id: str, db: AsyncSession = Depends(get_db)):
    """获取客户的所有联系人"""
    result = await db.execute(
        select(CustomerContact).where(CustomerContact.customer_id == customer_id)
    )
    contacts = result.scalars().all()
    return [ContactResponse.model_validate(c) for c in contacts]


@router.post("/{customer_id}/contacts", response_model=ContactResponse)
async def create_contact(customer_id: str, contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """为客户添加联系人"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="客户不存在")

    db_contact = CustomerContact(id=str(uuid.uuid4()), customer_id=customer_id, **contact.model_dump())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)

    return ContactResponse.model_validate(db_contact)


@router.put("/{customer_id}/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    customer_id: str, contact_id: str, contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新联系人"""
    result = await db.execute(
        select(CustomerContact).where(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id,
        )
    )
    db_contact = result.scalar_one_or_none()
    if not db_contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    update_data = contact.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contact, field, value)

    await db.commit()
    await db.refresh(db_contact)

    return ContactResponse.model_validate(db_contact)


@router.delete("/{customer_id}/contacts/{contact_id}")
async def delete_contact(customer_id: str, contact_id: str, db: AsyncSession = Depends(get_db)):
    """删除联系人"""
    result = await db.execute(
        select(CustomerContact).where(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id,
        )
    )
    db_contact = result.scalar_one_or_none()
    if not db_contact:
        raise HTTPException(status_code=404, detail="联系人不存在")

    await db.delete(db_contact)
    await db.commit()

    return {"message": "删除成功"}
