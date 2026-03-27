"""收入管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.income import Income
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeResponse, IncomeListResponse, IncomeStats
from app.api.auth import require_menu_permission

router = APIRouter()


@router.get("", response_model=IncomeListResponse)
async def get_incomes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    year: Optional[str] = None,
    income_category: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('cashflow')),
):
    """获取收入列表"""
    # 构建基础查询
    query = select(Income)

    if search:
        query = query.where(Income.customer_name.contains(search))
    if year:
        query = query.where(Income.income_year == year)
    if income_category:
        query = query.where(Income.income_category == income_category)
    if customer_id:
        query = query.where(Income.customer_id == customer_id)

    # 获取总数
    count_query = select(func.count()).select_from(Income)
    if search:
        count_query = count_query.where(Income.customer_name.contains(search))
    if year:
        count_query = count_query.where(Income.income_year == year)
    if income_category:
        count_query = count_query.where(Income.income_category == income_category)
    if customer_id:
        count_query = count_query.where(Income.customer_id == customer_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 获取分页数据
    query = query.order_by(Income.income_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    incomes = result.scalars().all()

    return IncomeListResponse(
        total=total,
        items=[IncomeResponse.model_validate(i) for i in incomes]
    )


@router.get("/{income_id}", response_model=IncomeResponse)
async def get_income(income_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """获取收入详情"""
    result = await db.execute(select(Income).where(Income.id == income_id))
    income = result.scalar_one_or_none()

    if not income:
        raise HTTPException(status_code=404, detail="收入记录不存在")

    return IncomeResponse.model_validate(income)


@router.post("", response_model=IncomeResponse)
async def create_income(income: IncomeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """创建收入"""
    # 验证客户是否存在
    if income.customer_id:
        result = await db.execute(select(Customer).where(Customer.id == income.customer_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="客户不存在")

    # 验证发票是否存在
    if income.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == income.invoice_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="发票不存在")

    # 自动设置年份
    if not income.income_year:
        income.income_year = str(income.income_date.year)

    db_income = Income(**income.model_dump())
    db.add(db_income)
    await db.commit()
    await db.refresh(db_income)

    return IncomeResponse.model_validate(db_income)


@router.put("/{income_id}", response_model=IncomeResponse)
async def update_income(income_id: str, income: IncomeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """更新收入"""
    result = await db.execute(select(Income).where(Income.id == income_id))
    db_income = result.scalar_one_or_none()

    if not db_income:
        raise HTTPException(status_code=404, detail="收入记录不存在")

    update_data = income.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_income, field, value)

    await db.commit()
    await db.refresh(db_income)

    return IncomeResponse.model_validate(db_income)


@router.delete("/{income_id}")
async def delete_income(income_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """删除收入"""
    result = await db.execute(select(Income).where(Income.id == income_id))
    db_income = result.scalar_one_or_none()

    if not db_income:
        raise HTTPException(status_code=404, detail="收入记录不存在")

    await db.delete(db_income)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/stats/overview", response_model=IncomeStats)
async def get_income_stats(
    year: str = Query(..., description="统计年份"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('cashflow')),
):
    """获取收入统计"""
    # 总收入
    total_query = select(func.sum(Income.amount)).where(Income.income_year == year)
    total_result = await db.execute(total_query)
    total_amount = total_result.scalar() or 0

    # 总笔数
    count_query = select(func.count()).where(Income.income_year == year)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # 按分类统计
    category_query = select(
        Income.income_category,
        func.sum(Income.amount),
        func.count()
    ).where(Income.income_year == year).group_by(Income.income_category)
    category_result = await db.execute(category_query)
    by_category = {
        cat: {"amount": float(amt), "count": cnt}
        for cat, amt, cnt in category_result.all()
    }

    # 按月度统计
    month_query = select(
        extract('month', Income.income_date),
        func.sum(Income.amount)
    ).where(Income.income_year == year).group_by(extract('month', Income.income_date))
    month_result = await db.execute(month_query)
    by_month = [{"month": int(m), "amount": float(amt)} for m, amt in month_result.all()]

    return IncomeStats(
        total_amount=total_amount,
        total_count=total_count,
        by_category=by_category,
        by_month=by_month,
        by_year={year: float(total_amount)}
    )
