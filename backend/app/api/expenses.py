"""支出管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.expense import Expense
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse, ExpenseStats, EXPENSE_CATEGORY_LABELS
from app.api.auth import require_menu_permission

router = APIRouter()


@router.get("", response_model=ExpenseListResponse)
async def get_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    year: Optional[str] = None,
    expense_category: Optional[str] = None,
    supplier_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('cashflow')),
):
    """获取支出列表"""
    # 构建基础查询
    query = select(Expense)

    if search:
        query = query.where(Expense.supplier_name.contains(search))
    if year:
        query = query.where(Expense.expense_year == year)
    if expense_category:
        query = query.where(Expense.expense_category == expense_category)
    if supplier_id:
        query = query.where(Expense.supplier_id == supplier_id)

    # 获取总数
    count_query = select(func.count()).select_from(Expense)
    if search:
        count_query = count_query.where(Expense.supplier_name.contains(search))
    if year:
        count_query = count_query.where(Expense.expense_year == year)
    if expense_category:
        count_query = count_query.where(Expense.expense_category == expense_category)
    if supplier_id:
        count_query = count_query.where(Expense.supplier_id == supplier_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 获取分页数据
    query = query.order_by(Expense.expense_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    expenses = result.scalars().all()

    return ExpenseListResponse(
        total=total,
        items=[ExpenseResponse.model_validate(i) for i in expenses]
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """获取支出详情"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")

    return ExpenseResponse.model_validate(expense)


@router.post("", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """创建支出"""
    # 验证供应商是否存在
    if expense.supplier_id:
        result = await db.execute(select(Customer).where(Customer.id == expense.supplier_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="供应商不存在")

    # 验证发票是否存在
    if expense.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == expense.invoice_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="发票不存在")

    # 验证合同是否存在
    if expense.contract_id:
        result = await db.execute(select(Contract).where(Contract.id == expense.contract_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="合同不存在")

    # 自动设置年份
    if not expense.expense_year:
        expense.expense_year = str(expense.expense_date.year)

    db_expense = Expense(**expense.model_dump())
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)

    return ExpenseResponse.model_validate(db_expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: str, expense: ExpenseUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """更新支出"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    db_expense = result.scalar_one_or_none()

    if not db_expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")

    update_data = expense.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_expense, field, value)

    await db.commit()
    await db.refresh(db_expense)

    return ExpenseResponse.model_validate(db_expense)


@router.delete("/{expense_id}")
async def delete_expense(expense_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('cashflow'))):
    """删除支出"""
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    db_expense = result.scalar_one_or_none()

    if not db_expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")

    await db.delete(db_expense)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/stats/overview", response_model=ExpenseStats)
async def get_expense_stats(
    year: str = Query(..., description="统计年份"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('cashflow')),
):
    """获取支出统计"""
    # 总支出
    total_query = select(func.sum(Expense.total_amount)).where(Expense.expense_year == year)
    total_result = await db.execute(total_query)
    total_amount = total_result.scalar() or 0

    # 总笔数
    count_query = select(func.count()).where(Expense.expense_year == year)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # 按分类统计
    category_query = select(
        Expense.expense_category,
        func.sum(Expense.total_amount),
        func.count()
    ).where(Expense.expense_year == year).group_by(Expense.expense_category)
    category_result = await db.execute(category_query)
    by_category = {
        EXPENSE_CATEGORY_LABELS.get(cat, cat): {"amount": float(amt), "count": cnt, "category_code": cat}
        for cat, amt, cnt in category_result.all()
    }

    # 按月度统计
    month_query = select(
        extract('month', Expense.expense_date),
        func.sum(Expense.total_amount)
    ).where(Expense.expense_year == year).group_by(extract('month', Expense.expense_date))
    month_result = await db.execute(month_query)
    by_month = [{"month": int(m), "amount": float(amt)} for m, amt in month_result.all()]

    return ExpenseStats(
        total_amount=total_amount,
        total_count=total_count,
        by_category=by_category,
        by_month=by_month,
        by_year={year: float(total_amount)}
    )
