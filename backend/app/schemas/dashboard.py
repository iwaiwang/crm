"""数据分析 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from decimal import Decimal


class CustomerStats(BaseModel):
    total: int = 0
    potential: int = 0
    normal: int = 0
    vip: int = 0
    active: int = 0
    lost: int = 0
    new_this_month: int = 0
    trend: List[Dict] = []  # [{date, count}]


class ContractStats(BaseModel):
    total_count: int = 0
    total_amount: Decimal = Decimal(0)
    draft: int = 0
    in_progress: int = 0
    completed: int = 0
    pending_review: int = 0
    terminated: int = 0
    new_this_month: int = 0


class ReceivableStats(BaseModel):
    total_amount: Decimal = Decimal(0)
    received_amount: Decimal = Decimal(0)
    unpaid_amount: Decimal = Decimal(0)
    overdue_amount: Decimal = Decimal(0)
    paid_count: int = 0
    unpaid_count: int = 0
    overdue_count: int = 0


class InvoiceStats(BaseModel):
    total_count: int = 0
    total_amount: Decimal = Decimal(0)
    pending: int = 0
    issued: int = 0
    sent: int = 0
    received: int = 0


class InventoryStats(BaseModel):
    total_products: int = 0
    total_value: Decimal = Decimal(0)
    low_stock_count: int = 0
    low_stock_products: List[Dict] = []  # [{id, name, stock_qty, min_stock}]


class ProjectStats(BaseModel):
    total: int = 0
    contact: int = 0
    bidding: int = 0
    signing: int = 0
    implementation: int = 0
    acceptance: int = 0
    after_sales: int = 0
    completed: int = 0
    overdue: int = 0


class CashflowStats(BaseModel):
    """现金流统计"""
    year: str
    total_income: Decimal = Decimal(0)
    total_expense: Decimal = Decimal(0)
    net_cashflow: Decimal = Decimal(0)  # 净现金流 = 收入 - 支出
    income_count: int = 0
    expense_count: int = 0
    income_by_month: List[Dict] = Field(default_factory=list, description="月度收入")
    expense_by_month: List[Dict] = Field(default_factory=list, description="月度支出")
    expense_by_category: Dict = Field(default_factory=dict, description="支出分类统计")
    income_by_category: Dict = Field(default_factory=dict, description="收入分类统计")


class DashboardStats(BaseModel):
    customers: CustomerStats
    contracts: ContractStats
    receivables: ReceivableStats
    invoices: InvoiceStats
    inventory: InventoryStats
    projects: ProjectStats
    cashflow: Optional[CashflowStats] = None
