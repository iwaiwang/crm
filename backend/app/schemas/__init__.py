"""Pydantic Schemas 初始化"""
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse, ContractListResponse
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse
from app.schemas.receivable import ReceivableCreate, ReceivableUpdate, ReceivableResponse, ReceivableListResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, StockMoveCreate
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse, FollowupCreate, PhaseCreate, TaskCreate
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.schemas.dashboard import DashboardStats, CustomerStats, ContractStats, ReceivableStats, InventoryStats, ProjectStats
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeResponse, IncomeListResponse, IncomeStats
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse, ExpenseStats, EXPENSE_CATEGORY_LABELS

__all__ = [
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    "ContractCreate",
    "ContractUpdate",
    "ContractResponse",
    "ContractListResponse",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "ReceivableCreate",
    "ReceivableUpdate",
    "ReceivableResponse",
    "ReceivableListResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "StockMoveCreate",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "FollowupCreate",
    "PhaseCreate",
    "TaskCreate",
    "UserCreate",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    "DashboardStats",
    "CustomerStats",
    "ContractStats",
    "ReceivableStats",
    "InventoryStats",
    "ProjectStats",
    "IncomeCreate",
    "IncomeUpdate",
    "IncomeResponse",
    "IncomeListResponse",
    "IncomeStats",
    "ExpenseCreate",
    "ExpenseUpdate",
    "ExpenseResponse",
    "ExpenseListResponse",
    "ExpenseStats",
    "EXPENSE_CATEGORY_LABELS",
]
