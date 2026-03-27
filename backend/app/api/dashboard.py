"""数据分析仪表盘 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional
from decimal import Decimal

from app.database import get_db
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.receivable import Receivable
from app.models.product import Product
from app.models.project import Project
from app.models.income import Income
from app.models.expense import Expense
from app.schemas.dashboard import (
    DashboardStats, CustomerStats, ContractStats, ReceivableStats,
    InvoiceStats, InventoryStats, ProjectStats
)
from app.schemas.income import IncomeStats
from app.schemas.expense import ExpenseStats

router = APIRouter()


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取仪表盘统计数据"""
    return DashboardStats(
        customers=await get_customer_stats(db),
        contracts=await get_contract_stats(db, year),
        receivables=await get_receivable_stats(db),
        invoices=await get_invoice_stats(db),
        inventory=await get_inventory_stats(db),
        projects=await get_project_stats(db),
        cashflow=await get_cashflow_stats(db, year),
    )


async def get_customer_stats(db: AsyncSession) -> CustomerStats:
    """客户统计"""
    total_result = await db.execute(select(func.count()).select_from(Customer))
    total = total_result.scalar() or 0

    category_result = await db.execute(
        select(Customer.category, func.count()).group_by(Customer.category)
    )
    categories = dict(category_result.all())

    status_result = await db.execute(
        select(Customer.status, func.count()).group_by(Customer.status)
    )
    statuses = dict(status_result.all())

    first_day = date.today().replace(day=1)
    new_result = await db.execute(
        select(func.count()).where(Customer.created_at >= func.datetime(first_day))
    )
    new_this_month = new_result.scalar() or 0

    trend = []
    for i in range(5, -1, -1):
        month_start = (date.today().replace(day=1) - relativedelta(months=i))
        month_end = month_start + relativedelta(months=1)
        count_result = await db.execute(
            select(func.count()).where(
                Customer.created_at >= func.datetime(month_start),
                Customer.created_at < func.datetime(month_end)
            )
        )
        count = count_result.scalar() or 0
        trend.append({"month": month_start.strftime("%Y-%m"), "count": count})

    return CustomerStats(
        total=total,
        potential=categories.get("potential", 0),
        normal=categories.get("normal", 0),
        vip=categories.get("vip", 0),
        active=statuses.get("active", 0),
        lost=statuses.get("lost", 0),
        new_this_month=new_this_month,
        trend=trend,
    )


async def get_contract_stats(db: AsyncSession, year: Optional[int] = None) -> ContractStats:
    """合同统计"""
    # 如果没有传 year，默认使用当前年份
    if year is None:
        year = date.today().year

    # 当年的合同统计
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)

    result = await db.execute(
        select(func.count(), func.sum(Contract.amount)).where(
            Contract.start_date >= year_start,
            Contract.start_date < year_end
        )
    )
    row = result.first()
    total_count = row[0] or 0
    total_amount = row[1] or 0

    status_result = await db.execute(
        select(Contract.status, func.count()).where(
            Contract.start_date >= year_start,
            Contract.start_date < year_end
        ).group_by(Contract.status)
    )
    statuses = dict(status_result.all())

    first_day = date.today().replace(day=1)
    new_result = await db.execute(
        select(func.count()).where(
            Contract.start_date >= year_start,
            Contract.start_date < year_end,
            Contract.created_at >= func.datetime(first_day)
        )
    )
    new_this_month = new_result.scalar() or 0

    return ContractStats(
        total_count=total_count,
        total_amount=total_amount,
        draft=statuses.get("draft", 0),
        pending_review=statuses.get("pending_review", 0),
        in_progress=statuses.get("in_progress", 0),
        completed=statuses.get("completed", 0),
        terminated=statuses.get("terminated", 0),
        new_this_month=new_this_month,
    )


async def get_receivable_stats(db: AsyncSession) -> ReceivableStats:
    """应收款统计"""
    result = await db.execute(
        select(
            func.sum(Receivable.amount),
            func.sum(Receivable.received_amount),
            func.sum(Receivable.amount - Receivable.received_amount)
        )
    )
    row = result.first()
    total_amount = row[0] or 0
    received_amount = row[1] or 0
    unpaid_amount = row[2] or 0

    status_result = await db.execute(
        select(Receivable.status, func.count()).group_by(Receivable.status)
    )
    statuses = dict(status_result.all())

    overdue_result = await db.execute(
        select(func.count()).where(
            Receivable.status != "paid",
            Receivable.due_date < date.today()
        )
    )
    overdue_count = overdue_result.scalar() or 0

    overdue_amount_result = await db.execute(
        select(func.sum(Receivable.amount - Receivable.received_amount)).where(
            Receivable.status != "paid",
            Receivable.due_date < date.today()
        )
    )
    overdue_amount = overdue_amount_result.scalar() or 0

    return ReceivableStats(
        total_amount=total_amount,
        received_amount=received_amount,
        unpaid_amount=unpaid_amount,
        overdue_amount=overdue_amount,
        paid_count=statuses.get("paid", 0),
        unpaid_count=statuses.get("unpaid", 0),
        overdue_count=overdue_count,
    )


async def get_invoice_stats(db: AsyncSession) -> InvoiceStats:
    """发票统计"""
    result = await db.execute(
        select(func.count(), func.sum(Invoice.amount))
    )
    row = result.first()
    total_count = row[0] or 0
    total_amount = row[1] or 0

    status_result = await db.execute(
        select(Invoice.status, func.count()).group_by(Invoice.status)
    )
    statuses = dict(status_result.all())

    return InvoiceStats(
        total_count=total_count,
        total_amount=total_amount,
        pending=statuses.get("pending", 0),
        issued=statuses.get("issued", 0),
        sent=statuses.get("sent", 0),
        received=statuses.get("received", 0),
    )


async def get_inventory_stats(db: AsyncSession) -> InventoryStats:
    """库存统计"""
    result = await db.execute(
        select(func.count(), func.sum(Product.price * Product.stock_qty))
        .where(Product.is_active == True)
    )
    row = result.first()
    total_products = row[0] or 0
    total_value = row[1] or 0

    low_stock_result = await db.execute(
        select(Product).where(
            Product.is_active == True,
            Product.stock_qty <= Product.min_stock
        )
    )
    low_stock_products = low_stock_result.scalars().all()

    low_stock_list = [
        {"id": p.id, "name": p.name, "stock_qty": p.stock_qty, "min_stock": p.min_stock}
        for p in low_stock_products
    ]

    return InventoryStats(
        total_products=total_products,
        total_value=total_value,
        low_stock_count=len(low_stock_products),
        low_stock_products=low_stock_list,
    )


async def get_project_stats(db: AsyncSession) -> ProjectStats:
    """项目统计"""
    total_result = await db.execute(select(func.count()).select_from(Project))
    total = total_result.scalar() or 0

    status_result = await db.execute(
        select(Project.status, func.count()).group_by(Project.status)
    )
    statuses = dict(status_result.all())

    return ProjectStats(
        total=total,
        contact=statuses.get("contact", 0),
        bidding=statuses.get("bidding", 0),
        signing=statuses.get("signing", 0),
        implementation=statuses.get("implementation", 0),
        acceptance=statuses.get("acceptance", 0),
        after_sales=statuses.get("after_sales", 0),
        completed=statuses.get("after_sales", 0),
        overdue=0,
    )


async def get_cashflow_stats(db: AsyncSession, year: Optional[int] = None) -> "CashflowStats":
    """现金流统计"""
    from app.schemas.dashboard import CashflowStats

    if year is None:
        year = date.today().year

    year_str = str(year)
    year_start = date(year, 1, 1)
    year_end = date(year + 1, 1, 1)

    # 收入统计
    income_result = await db.execute(
        select(func.sum(Income.amount), func.count()).where(
            Income.income_year == year_str
        )
    )
    income_row = income_result.first()
    total_income = income_row[0] or 0
    income_count = income_row[1] or 0

    # 支出统计
    expense_result = await db.execute(
        select(func.sum(Expense.total_amount), func.count()).where(
            Expense.expense_year == year_str
        )
    )
    expense_row = expense_result.first()
    total_expense = expense_row[0] or 0
    expense_count = expense_row[1] or 0

    # 净现金流
    net_cashflow = Decimal(total_income) - Decimal(total_expense)

    # 按月度统计收入
    income_month_result = await db.execute(
        select(
            extract('month', Income.income_date),
            func.sum(Income.amount)
        ).where(
            Income.income_year == year_str
        ).group_by(extract('month', Income.income_date))
    )
    income_by_month = [{"month": int(m), "amount": float(amt)} for m, amt in income_month_result.all()]

    # 按月度统计支出
    expense_month_result = await db.execute(
        select(
            extract('month', Expense.expense_date),
            func.sum(Expense.total_amount)
        ).where(
            Expense.expense_year == year_str
        ).group_by(extract('month', Expense.expense_date))
    )
    expense_by_month = [{"month": int(m), "amount": float(amt)} for m, amt in expense_month_result.all()]

    # 按分类统计支出
    expense_category_result = await db.execute(
        select(
            Expense.expense_category,
            func.sum(Expense.total_amount)
        ).where(
            Expense.expense_year == year_str
        ).group_by(Expense.expense_category)
    )
    from app.schemas.expense import EXPENSE_CATEGORY_LABELS
    expense_by_category = {
        EXPENSE_CATEGORY_LABELS.get(cat, cat): {"amount": float(amt), "category_code": cat}
        for cat, amt in expense_category_result.all()
    }

    # 按分类统计收入
    income_category_result = await db.execute(
        select(
            Income.income_category,
            func.sum(Income.amount)
        ).where(
            Income.income_year == year_str
        ).group_by(Income.income_category)
    )
    income_by_category = {
        cat: {"amount": float(amt)}
        for cat, amt in income_category_result.all()
    }

    return CashflowStats(
        year=year_str,
        total_income=total_income,
        total_expense=total_expense,
        net_cashflow=net_cashflow,
        income_count=income_count,
        expense_count=expense_count,
        income_by_month=income_by_month,
        expense_by_month=expense_by_month,
        expense_by_category=expense_by_category,
        income_by_category=income_by_category,
    )
