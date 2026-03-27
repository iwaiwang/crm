"""API 路由初始化"""
from app.api import customers, contracts, invoices, receivables, products, projects, auth, dashboard, webhooks, incomes, expenses, settings

__all__ = [
    "customers",
    "contracts",
    "invoices",
    "receivables",
    "products",
    "projects",
    "auth",
    "dashboard",
    "webhooks",
    "incomes",
    "expenses",
    "settings",
]
