"""数据库模型初始化"""
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.receivable import Receivable
from app.models.product import Product, StockMove
from app.models.project import Project, ProjectFollowup, ProjectTask
from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense
from app.models.setting import Setting

__all__ = [
    "Customer",
    "Contract",
    "Invoice",
    "Receivable",
    "Product",
    "StockMove",
    "Project",
    "ProjectFollowup",
    "ProjectTask",
    "User",
    "Income",
    "Expense",
    "Setting",
]
