# 报销管理模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现报销管理模块，支持报销单的录入、审核、支付三步流程，提供应付/已付/待付统计分析。

**Architecture:** 新增独立的报销管理模块，与现有发票管理和支出管理并行。使用 SQLAlchemy 模型存储报销单数据，FastAPI 提供 REST API，Vue 3 + Element Plus 构建前端界面。

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (后端), Vue 3 + Element Plus + Pinia (前端)

---

## 文件结构

**后端新增文件：**
- `backend/app/models/reimbursement.py` - 报销单数据模型
- `backend/app/schemas/reimbursement.py` - Pydantic Schema 定义
- `backend/app/api/reimbursements.py` - REST API 端点

**后端修改文件：**
- `backend/app/models/__init__.py` - 导出 Reimbursement 模型
- `backend/app/models/invoice.py` - 添加 reimbursements relationship
- `backend/app/models/contract.py` - 添加 reimbursements relationship
- `backend/app/main.py` - 注册报销管理路由

**前端新增文件：**
- `frontend/src/api/reimbursement.js` - API 调用封装
- `frontend/src/views/Reimbursements.vue` - 报销管理页面

**前端修改文件：**
- `frontend/src/router/index.js` - 添加路由配置
- `frontend/src/views/Layout.vue` - 添加菜单项

---

## Task 1: 创建报销单数据模型

**Files:**
- Create: `backend/app/models/reimbursement.py`

- [ ] **Step 1: 创建报销单模型文件**

```python
"""报销单模型"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, DECIMAL, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 来源信息
    source_type = Column(
        SQLEnum("invoice", "manual", name="reimbursement_source_type"),
        default="manual",
        comment="来源类型"
    )
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True, comment="关联进项发票ID")
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True, comment="关联合同ID")

    # 基本信息
    supplier_name = Column(String(100), nullable=False, comment="供应商/收款方名称")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="报销金额不含税")
    tax_amount = Column(DECIMAL(15, 2), default=0, comment="税额")
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="价税合计")
    expense_category = Column(
        SQLEnum(
            "catering", "travel", "procurement", "office", "rent",
            "utilities", "salary", "marketing", "software", "maintenance",
            "training", "entertainment", "logistics", "other",
            name="reimbursement_category"
        ),
        default="other",
        comment="费用分类"
    )
    remark = Column(Text, comment="备注说明")

    # 附件
    file_id = Column(String(36), comment="附件文件ID")
    file_url = Column(String(500), comment="附件文件URL")

    # 流程状态
    status = Column(
        SQLEnum("draft", "pending", "approved", "rejected", "paid", name="reimbursement_status"),
        default="draft",
        comment="状态"
    )

    # 操作记录
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False, comment="录入人ID")
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="审核人ID")
    approved_at = Column(DateTime(timezone=True), comment="审核时间")
    reject_reason = Column(Text, comment="驳回原因")
    paid_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="支付确认人ID")
    paid_at = Column(DateTime(timezone=True), comment="支付确认时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    invoice = relationship("Invoice", back_populates="reimbursements")
    contract = relationship("Contract", back_populates="reimbursements")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    payer = relationship("User", foreign_keys=[paid_by])

    def __repr__(self):
        return f"<Reimbursement {self.id} - {self.total_amount}>"
```

- [ ] **Step 2: 在模型 __init__.py 中导出 Reimbursement**

修改 `backend/app/models/__init__.py`，添加导入和导出：

```python
"""Database models."""
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.contract_file import ContractFile
from app.models.invoice import Invoice
from app.models.receivable import Receivable
from app.models.product import Product, StockMove
from app.models.project import Project, ProjectFollowup, ProjectTask, ProjectPhase
from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense
from app.models.setting import Setting
from app.models.reimbursement import Reimbursement

__all__ = [
    "Customer",
    "Contract",
    "ContractFile",
    "Invoice",
    "Receivable",
    "Product",
    "StockMove",
    "Project",
    "ProjectFollowup",
    "ProjectTask",
    "ProjectPhase",
    "User",
    "Income",
    "Expense",
    "Setting",
    "Reimbursement",
]
```

- [ ] **Step 3: 在 Invoice 模型添加 reimbursements relationship**

修改 `backend/app/models/invoice.py`，在现有 relationships 后添加：

```python
# 在 Invoice 类中添加以下 relationship（约第 59 行附近）
reimbursements = relationship("Reimbursement", back_populates="invoice")
```

- [ ] **Step 4: 在 Contract 模型添加 reimbursements relationship**

修改 `backend/app/models/contract.py`，在现有 relationships 后添加：

```python
# 在 Contract 类中添加以下 relationship
reimbursements = relationship("Reimbursement", back_populates="contract")
```

- [ ] **Step 5: 重启后端服务验证数据库初始化**

Run: `curl -s http://localhost:8002/health`
Expected: `{"status":"ok"}`

检查后端日志，确认数据库表创建成功。

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/reimbursement.py backend/app/models/__init__.py backend/app/models/invoice.py backend/app/models/contract.py
git commit -m "feat: add Reimbursement model for expense reimbursement workflow

- Create reimbursement table with status workflow (draft/pending/approved/rejected/paid)
- Add relationships to Invoice and Contract models
- Support invoice import and manual entry sources

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 2: 创建报销单 Schema

**Files:**
- Create: `backend/app/schemas/reimbursement.py`

- [ ] **Step 1: 创建 Schema 文件**

```python
"""报销单 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ReimbursementSourceType(str, Enum):
    INVOICE = "invoice"
    MANUAL = "manual"


class ReimbursementStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ReimbursementCategory(str, Enum):
    CATERING = "catering"
    TRAVEL = "travel"
    PROCUREMENT = "procurement"
    OFFICE = "office"
    RENT = "rent"
    UTILITIES = "utilities"
    SALARY = "salary"
    MARKETING = "marketing"
    SOFTWARE = "software"
    MAINTENANCE = "maintenance"
    TRAINING = "training"
    ENTERTAINMENT = "entertainment"
    LOGISTICS = "logistics"
    OTHER = "other"


# 费用分类中文映射
REIMBURSEMENT_CATEGORY_LABELS = {
    "catering": "餐饮",
    "travel": "差旅",
    "procurement": "采购",
    "office": "办公",
    "rent": "房租",
    "utilities": "水电",
    "salary": "工资",
    "marketing": "市场推广",
    "software": "软件服务",
    "maintenance": "维修维护",
    "training": "培训",
    "entertainment": "业务招待",
    "logistics": "物流快递",
    "other": "其他",
}


# 状态中文映射
REIMBURSEMENT_STATUS_LABELS = {
    "draft": "草稿",
    "pending": "待审核",
    "approved": "已审核",
    "rejected": "已驳回",
    "paid": "已支付",
}


class ReimbursementBase(BaseModel):
    source_type: Optional[ReimbursementSourceType] = Field(ReimbursementSourceType.MANUAL, description="来源类型")
    invoice_id: Optional[str] = Field(None, description="关联进项发票ID")
    contract_id: Optional[str] = Field(None, description="关联合同ID")
    supplier_name: str = Field(..., description="供应商/收款方名称")
    amount: Decimal = Field(..., ge=0, description="报销金额不含税")
    tax_amount: Optional[Decimal] = Field(Decimal("0"), description="税额")
    total_amount: Decimal = Field(..., ge=0, description="价税合计")
    expense_category: Optional[ReimbursementCategory] = Field(ReimbursementCategory.OTHER, description="费用分类")
    remark: Optional[str] = Field(None, description="备注说明")
    file_id: Optional[str] = Field(None, description="附件文件ID")
    file_url: Optional[str] = Field(None, description="附件文件URL")


class ReimbursementCreate(ReimbursementBase):
    pass


class ReimbursementUpdate(BaseModel):
    supplier_name: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    expense_category: Optional[ReimbursementCategory] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None


class ReimbursementReject(BaseModel):
    reason: str = Field(..., description="驳回原因")


class ReimbursementApprove(BaseModel):
    amount: Optional[Decimal] = Field(None, description="修改后的金额")
    expense_category: Optional[ReimbursementCategory] = Field(None, description="修改后的分类")


class ReimbursementResponse(ReimbursementBase):
    id: str
    status: ReimbursementStatus
    created_by: str
    creator_name: Optional[str] = None
    approved_by: Optional[str] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    paid_by: Optional[str] = None
    payer_name: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReimbursementListResponse(BaseModel):
    total: int
    items: List[ReimbursementResponse]


class ReimbursementStatistics(BaseModel):
    total_pending_amount: Decimal = Decimal("0")
    total_approved_amount: Decimal = Decimal("0")
    total_paid_amount: Decimal = Decimal("0")
    pending_count: int = 0
    approved_count: int = 0
    paid_count: int = 0
    by_category: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/reimbursement.py
git commit -m "feat: add Reimbursement schemas for API validation

- Define create/update/response schemas
- Add reject and approve request schemas
- Include statistics response schema

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 3: 创建报销单 API

**Files:**
- Create: `backend/app/api/reimbursements.py`

- [ ] **Step 1: 创建 API 文件（基础 CRUD）**

```python
"""报销管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import json

from app.database import get_db
from app.models.reimbursement import Reimbursement
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.user import User
from app.schemas.reimbursement import (
    ReimbursementCreate,
    ReimbursementUpdate,
    ReimbursementResponse,
    ReimbursementListResponse,
    ReimbursementReject,
    ReimbursementApprove,
    ReimbursementStatistics,
    REIMBURSEMENT_CATEGORY_LABELS,
    REIMBURSEMENT_STATUS_LABELS,
)
from app.api.auth import require_menu_permission, get_current_user

router = APIRouter()


def _get_status_label(status: str) -> str:
    return REIMBURSEMENT_STATUS_LABELS.get(status, status)


def _get_category_label(category: str) -> str:
    return REIMBURSEMENT_CATEGORY_LABELS.get(category, category)


async def _enrich_reimbursement_response(db: AsyncSession, reimbursement: Reimbursement) -> ReimbursementResponse:
    """为报销单响应添加用户名称"""
    response_data = ReimbursementResponse.model_validate(reimbursement).model_dump()
    
    # 获取录入人名称
    if reimbursement.created_by:
        creator_result = await db.execute(select(User).where(User.id == reimbursement.created_by))
        creator = creator_result.scalar_one_or_none()
        response_data["creator_name"] = creator.username if creator else None
    
    # 获取审核人名称
    if reimbursement.approved_by:
        approver_result = await db.execute(select(User).where(User.id == reimbursement.approved_by))
        approver = approver_result.scalar_one_or_none()
        response_data["approver_name"] = approver.username if approver else None
    
    # 获取支付人名称
    if reimbursement.paid_by:
        payer_result = await db.execute(select(User).where(User.id == reimbursement.paid_by))
        payer = payer_result.scalar_one_or_none()
        response_data["payer_name"] = payer.username if payer else None
    
    return ReimbursementResponse(**response_data)


@router.get("", response_model=ReimbursementListResponse)
async def get_reimbursements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    expense_category: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单列表"""
    # 构建基础查询
    query = select(Reimbursement)
    
    # 非管理员只能看自己创建的
    if current_user.role != "admin":
        query = query.where(Reimbursement.created_by == current_user.id)
    
    # 状态筛选
    if status:
        query = query.where(Reimbursement.status == status)
    
    # 分类筛选
    if expense_category:
        query = query.where(Reimbursement.expense_category == expense_category)
    
    # 年份筛选
    if year:
        query = query.where(extract('year', Reimbursement.created_at) == year)
    
    # 月份筛选
    if month:
        query = query.where(extract('month', Reimbursement.created_at) == month)
    
    # 搜索
    if search:
        query = query.where(Reimbursement.supplier_name.contains(search))
    
    # 获取总数
    count_query = select(func.count()).select_from(Reimbursement)
    if current_user.role != "admin":
        count_query = count_query.where(Reimbursement.created_by == current_user.id)
    if status:
        count_query = count_query.where(Reimbursement.status == status)
    if expense_category:
        count_query = count_query.where(Reimbursement.expense_category == expense_category)
    if year:
        count_query = count_query.where(extract('year', Reimbursement.created_at) == year)
    if month:
        count_query = count_query.where(extract('month', Reimbursement.created_at) == month)
    if search:
        count_query = count_query.where(Reimbursement.supplier_name.contains(search))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.order_by(Reimbursement.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    reimbursements = result.scalars().all()
    
    # 响应
    items = []
    for r in reimbursements:
        items.append(await _enrich_reimbursement_response(db, r))
    
    return ReimbursementListResponse(total=total, items=items)


@router.get("/statistics", response_model=ReimbursementStatistics)
async def get_reimbursement_statistics(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销统计"""
    # 构建基础条件
    base_condition = True
    if current_user.role != "admin":
        base_condition = (Reimbursement.created_by == current_user.id)
    if year:
        base_condition = base_condition & (extract('year', Reimbursement.created_at) == year)
    
    # 待审核金额
    pending_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "pending")
        .where(base_condition if current_user.role != "admin" else True)
    )
    pending_amount, pending_count = pending_result.one() or (0, 0)
    
    # 待支付金额
    approved_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "approved")
        .where(base_condition if current_user.role != "admin" else True)
    )
    approved_amount, approved_count = approved_result.one() or (0, 0)
    
    # 已支付金额
    paid_result = await db.execute(
        select(func.sum(Reimbursement.total_amount), func.count())
        .where(Reimbursement.status == "paid")
        .where(base_condition if current_user.role != "admin" else True)
    )
    paid_amount, paid_count = paid_result.one() or (0, 0)
    
    # 按分类统计（已支付）
    category_result = await db.execute(
        select(Reimbursement.expense_category, func.sum(Reimbursement.total_amount))
        .where(Reimbursement.status == "paid")
        .where(base_condition if current_user.role != "admin" else True)
        .group_by(Reimbursement.expense_category)
    )
    by_category = {}
    for cat, amt in category_result.all():
        label = _get_category_label(cat)
        by_category[label] = {"amount": float(amt or 0), "category_code": cat}
    
    return ReimbursementStatistics(
        total_pending_amount=Decimal(str(pending_amount or 0)),
        total_approved_amount=Decimal(str(approved_amount or 0)),
        total_paid_amount=Decimal(str(paid_amount or 0)),
        pending_count=pending_count or 0,
        approved_count=approved_count or 0,
        paid_count=paid_count or 0,
        by_category=by_category,
    )


@router.get("/{reimbursement_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报销单详情"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    reimbursement = result.scalar_one_or_none()
    
    if not reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    # 权限检查：非管理员只能看自己的
    if current_user.role != "admin" and reimbursement.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此报销单")
    
    return await _enrich_reimbursement_response(db, reimbursement)


@router.post("", response_model=ReimbursementResponse)
async def create_reimbursement(
    reimbursement: ReimbursementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建报销单"""
    # 验证发票是否存在
    if reimbursement.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == reimbursement.invoice_id))
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=400, detail="发票不存在")
        # 只能关联进项发票
        if invoice.invoice_type != "purchase":
            raise HTTPException(status_code=400, detail="只能关联进项发票")
    
    # 验证合同是否存在
    if reimbursement.contract_id:
        result = await db.execute(select(Contract).where(Contract.id == reimbursement.contract_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="合同不存在")
    
    # 创建报销单
    db_reimbursement = Reimbursement(
        **reimbursement.model_dump(),
        created_by=current_user.id,
        status="draft",
    )
    db.add(db_reimbursement)
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return await _enrich_reimbursement_response(db, db_reimbursement)


@router.put("/{reimbursement_id}", response_model=ReimbursementResponse)
async def update_reimbursement(
    reimbursement_id: str,
    reimbursement: ReimbursementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新报销单"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    # 权限和状态检查
    if current_user.role != "admin":
        # 普通用户只能编辑自己的草稿或驳回状态
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限编辑此报销单")
        if db_reimbursement.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="只能编辑草稿或驳回状态的报销单")
    else:
        # 管理员可以编辑草稿和驳回状态
        if db_reimbursement.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="只能编辑草稿或驳回状态的报销单")
    
    # 更新字段
    update_data = reimbursement.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reimbursement, field, value)
    
    # 驳回状态编辑后自动重置为草稿
    if db_reimbursement.status == "rejected":
        db_reimbursement.status = "draft"
        db_reimbursement.reject_reason = None
    
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return await _enrich_reimbursement_response(db, db_reimbursement)


@router.delete("/{reimbursement_id}")
async def delete_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除报销单"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    # 权限和状态检查
    if current_user.role != "admin":
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此报销单")
        if db_reimbursement.status != "draft":
            raise HTTPException(status_code=400, detail="只能删除草稿状态的报销单")
    else:
        if db_reimbursement.status != "draft":
            raise HTTPException(status_code=400, detail="只能删除草稿状态的报销单")
    
    await db.delete(db_reimbursement)
    await db.commit()
    
    return {"message": "删除成功"}
```

- [ ] **Step 2: 添加流程操作 API（提交、审核、驳回、支付）**

在 `backend/app/api/reimbursements.py` 文件末尾添加：

```python
@router.post("/{reimbursement_id}/submit")
async def submit_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交报销单审核"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    # 权限检查
    if current_user.role != "admin":
        if db_reimbursement.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权限提交此报销单")
    
    # 状态检查
    if db_reimbursement.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的报销单")
    
    # 提交审核
    db_reimbursement.status = "pending"
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return {"message": "提交成功", "status": "pending"}


@router.post("/{reimbursement_id}/approve")
async def approve_reimbursement(
    reimbursement_id: str,
    approve_data: Optional[ReimbursementApprove] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """审核通过报销单"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    if db_reimbursement.status != "pending":
        raise HTTPException(status_code=400, detail="只能审核待审核状态的报销单")
    
    # 管理员可修改金额和分类
    if approve_data:
        if approve_data.amount is not None:
            db_reimbursement.amount = approve_data.amount
            db_reimbursement.total_amount = approve_data.amount + (db_reimbursement.tax_amount or Decimal("0"))
        if approve_data.expense_category is not None:
            db_reimbursement.expense_category = approve_data.expense_category
    
    # 审核通过
    db_reimbursement.status = "approved"
    db_reimbursement.approved_by = current_user.id
    db_reimbursement.approved_at = datetime.now()
    
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return {"message": "审核通过", "status": "approved"}


@router.post("/{reimbursement_id}/reject")
async def reject_reimbursement(
    reimbursement_id: str,
    reject_data: ReimbursementReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """驳回报销单"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    if db_reimbursement.status != "pending":
        raise HTTPException(status_code=400, detail="只能驳回待审核状态的报销单")
    
    # 驳回
    db_reimbursement.status = "rejected"
    db_reimbursement.approved_by = current_user.id
    db_reimbursement.approved_at = datetime.now()
    db_reimbursement.reject_reason = reject_data.reason
    
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return {"message": "已驳回", "status": "rejected", "reason": reject_data.reason}


@router.post("/{reimbursement_id}/pay")
async def pay_reimbursement(
    reimbursement_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """确认支付"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    db_reimbursement = result.scalar_one_or_none()
    
    if not db_reimbursement:
        raise HTTPException(status_code=404, detail="报销单不存在")
    
    if db_reimbursement.status != "approved":
        raise HTTPException(status_code=400, detail="只能支付已审核状态的报销单")
    
    # 确认支付
    db_reimbursement.status = "paid"
    db_reimbursement.paid_by = current_user.id
    db_reimbursement.paid_at = datetime.now()
    
    await db.commit()
    await db.refresh(db_reimbursement)
    
    return {"message": "已支付", "status": "paid"}
```

- [ ] **Step 3: 在 main.py 注册路由**

修改 `backend/app/main.py`，在路由注册部分添加：

```python
# 在第 20 行附近添加导入
from app.api import customers, contracts, invoices, receivables, products, projects, auth, dashboard, webhooks, document, incomes, expenses, settings as settings_api, users, reimbursements

# 在第 91 行附近添加路由注册（expenses 后面）
app.include_router(reimbursements.router, prefix="/api/reimbursements", tags=["报销管理"])
```

- [ ] **Step 4: 重启后端验证 API 注册**

Run: `curl -s http://localhost:8002/docs | grep -o 'reimbursements' | head -1`
Expected: `reimbursements`

或直接访问 http://localhost:8002/docs 查看 API 文档中是否有报销管理模块。

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/reimbursements.py backend/app/main.py
git commit -m "feat: add reimbursement management API

- CRUD operations with role-based permissions
- Workflow actions: submit, approve, reject, pay
- Statistics endpoint for pending/approved/paid amounts
- Non-admin users can only see their own reimbursements

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 4: 创建前端 API 封装

**Files:**
- Create: `frontend/src/api/reimbursement.js`

- [ ] **Step 1: 创建 API 封装文件**

```javascript
import request from './request'

// 获取报销单列表
export function getReimbursements(params) {
  return request.get('/reimbursements', { params })
}

// 获取报销单详情
export function getReimbursement(id) {
  return request.get(`/reimbursements/${id}`)
}

// 创建报销单
export function createReimbursement(data) {
  return request.post('/reimbursements', data)
}

// 更新报销单
export function updateReimbursement(id, data) {
  return request.put(`/reimbursements/${id}`, data)
}

// 删除报销单
export function deleteReimbursement(id) {
  return request.delete(`/reimbursements/${id}`)
}

// 提交审核
export function submitReimbursement(id) {
  return request.post(`/reimbursements/${id}/submit`)
}

// 审核通过
export function approveReimbursement(id, data) {
  return request.post(`/reimbursements/${id}/approve`, data)
}

// 驳回报销单
export function rejectReimbursement(id, reason) {
  return request.post(`/reimbursements/${id}/reject`, { reason })
}

// 确认支付
export function payReimbursement(id) {
  return request.post(`/reimbursements/${id}/pay`)
}

// 获取报销统计
export function getReimbursementStatistics(params) {
  return request.get('/reimbursements/statistics', { params })
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/reimbursement.js
git commit -m "feat: add reimbursement API wrapper for frontend

- CRUD operations and workflow actions
- Statistics endpoint wrapper

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 5: 创建报销管理页面

**Files:**
- Create: `frontend/src/views/Reimbursements.vue`

- [ ] **Step 1: 创建报销管理页面**

```vue
<template>
  <div class="reimbursements-page">
    <div class="page-header">
      <h2>报销管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> 新增报销单
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="statistics-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">待审核</div>
            <div class="stat-value warning">¥{{ Number(statistics.total_pending_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.pending_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">待支付</div>
            <div class="stat-value primary">¥{{ Number(statistics.total_approved_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.approved_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">已支付</div>
            <div class="stat-value success">¥{{ Number(statistics.total_paid_amount || 0).toLocaleString() }}</div>
            <div class="stat-count">{{ statistics.paid_count || 0 }} 笔</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable @change="handleSearch">
            <el-option label="草稿" value="draft" />
            <el-option label="待审核" value="pending" />
            <el-option label="已审核" value="approved" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已支付" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用分类">
          <el-select v-model="searchForm.expense_category" placeholder="全部分类" clearable @change="handleSearch">
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="房租" value="rent" />
            <el-option label="水电" value="utilities" />
            <el-option label="工资" value="salary" />
            <el-option label="市场推广" value="marketing" />
            <el-option label="软件服务" value="software" />
            <el-option label="维修维护" value="maintenance" />
            <el-option label="培训" value="training" />
            <el-option label="业务招待" value="entertainment" />
            <el-option label="物流快递" value="logistics" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="searchForm.year" placeholder="全部年份" clearable @change="handleSearch">
            <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="searchForm.search" placeholder="供应商名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报销单列表 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="supplier_name" label="供应商/收款方" width="150" />
        <el-table-column prop="total_amount" label="报销金额" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="费用分类" width="100">
          <template #default="{ row }">
            <el-tag>{{ getCategoryLabel(row.expense_category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="录入人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'draft'">
              <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="success" @click="handleSubmit(row)">提交</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
            <template v-else-if="row.status === 'pending' && isAdmin">
              <el-button link type="success" @click="openApproveDialog(row)">审核通过</el-button>
              <el-button link type="danger" @click="openRejectDialog(row)">驳回</el-button>
            </template>
            <template v-else-if="row.status === 'approved' && isAdmin">
              <el-button link type="success" @click="handlePay(row)">确认支付</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button link type="primary" @click="handleEdit(row)">修改重提</el-button>
              <el-button link type="info" @click="showRejectReason(row)">查看原因</el-button>
            </template>
            <template v-else-if="row.status === 'paid'">
              <el-button link type="info" @click="handleView(row)">查看</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="loadReimbursements"
          @size-change="loadReimbursements"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-drawer
      v-model="showDialog"
      :title="formData.id ? '编辑报销单' : '新增报销单'"
      size="620px"
      direction="rtl"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="供应商/收款方" prop="supplier_name">
          <el-input v-model="formData.supplier_name" placeholder="供应商/收款方名称" />
        </el-form-item>
        <el-form-item label="报销金额(不含税)" prop="amount">
          <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="税额" prop="tax_amount">
          <el-input-number v-model="formData.tax_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="价税合计" prop="total_amount">
          <el-input-number v-model="formData.total_amount" :min="0" :precision="2" style="width: 100%" disabled />
        </el-form-item>
        <el-form-item label="费用分类" prop="expense_category">
          <el-select v-model="formData.expense_category" style="width: 100%">
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="房租" value="rent" />
            <el-option label="水电" value="utilities" />
            <el-option label="工资" value="salary" />
            <el-option label="市场推广" value="marketing" />
            <el-option label="软件服务" value="software" />
            <el-option label="维修维护" value="maintenance" />
            <el-option label="培训" value="training" />
            <el-option label="业务招待" value="entertainment" />
            <el-option label="物流快递" value="logistics" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联发票">
          <el-select v-model="formData.invoice_id" placeholder="选择进项发票（可选）" clearable style="width: 100%">
            <el-option v-for="inv in purchaseInvoices" :key="inv.id" :label="inv.invoice_no" :value="inv.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联合同">
          <el-select v-model="formData.contract_id" placeholder="选择合同（可选）" clearable style="width: 100%">
            <el-option v-for="c in contracts" :key="c.id" :label="c.contract_no" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>

    <!-- 审核通过对话框（可修改金额） -->
    <el-dialog v-model="showApproveDialog" title="审核通过" width="400px">
      <el-form :model="approveForm" label-width="100px">
        <el-form-item label="修改金额">
          <el-input-number v-model="approveForm.amount" :min="0" :precision="2" style="width: 100%" placeholder="不修改则保持原金额" />
        </el-form-item>
        <el-form-item label="修改分类">
          <el-select v-model="approveForm.expense_category" style="width: 100%" placeholder="不修改则保持原分类" clearable>
            <el-option label="餐饮" value="catering" />
            <el-option label="差旅" value="travel" />
            <el-option label="采购" value="procurement" />
            <el-option label="办公" value="office" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleApprove">确认通过</el-button>
      </template>
    </el-dialog>

    <!-- 驳回对话框 -->
    <el-dialog v-model="showRejectDialog" title="驳回报销单" width="400px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="驳回原因" prop="reason">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请填写驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import {
  getReimbursements,
  createReimbursement,
  updateReimbursement,
  deleteReimbursement,
  submitReimbursement,
  approveReimbursement,
  rejectReimbursement,
  payReimbursement,
  getReimbursementStatistics,
} from '@/api/reimbursement'
import { getInvoices } from '@/api/invoice'
import { getContracts } from '@/api/contract'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const showApproveDialog = ref(false)
const showRejectDialog = ref(false)
const formRef = ref(null)
const rejectFormRef = ref(null)
const tableData = ref([])
const purchaseInvoices = ref([])
const contracts = ref([])
const statistics = ref({
  total_pending_amount: 0,
  total_approved_amount: 0,
  total_paid_amount: 0,
  pending_count: 0,
  approved_count: 0,
  paid_count: 0,
})

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i)

const searchForm = reactive({
  status: '',
  expense_category: '',
  year: null,
  search: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const formData = reactive({
  id: '',
  supplier_name: '',
  amount: 0,
  tax_amount: 0,
  total_amount: 0,
  expense_category: 'other',
  invoice_id: '',
  contract_id: '',
  remark: '',
})

const approveForm = reactive({
  id: '',
  amount: null,
  expense_category: '',
})

const rejectForm = reactive({
  id: '',
  reason: '',
})

const rules = {
  supplier_name: [{ required: true, message: '请输入供应商/收款方名称', trigger: 'blur' }],
  amount: [{ required: true, message: '请输入报销金额', trigger: 'blur' }],
}

const rejectRules = {
  reason: [{ required: true, message: '请填写驳回原因', trigger: 'blur' }],
}

// 分类标签映射
const categoryLabels = {
  catering: '餐饮',
  travel: '差旅',
  procurement: '采购',
  office: '办公',
  rent: '房租',
  utilities: '水电',
  salary: '工资',
  marketing: '市场推广',
  software: '软件服务',
  maintenance: '维修维护',
  training: '培训',
  entertainment: '业务招待',
  logistics: '物流快递',
  other: '其他',
}

// 状态标签映射
const statusLabels = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  rejected: '已驳回',
  paid: '已支付',
}

// 状态颜色映射
const statusTypes = {
  draft: 'info',
  pending: 'warning',
  approved: 'primary',
  rejected: 'danger',
  paid: 'success',
}

const getCategoryLabel = (category) => categoryLabels[category] || category
const getStatusLabel = (status) => statusLabels[status] || status
const getStatusType = (status) => statusTypes[status] || 'info'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

// 监听金额变化自动计算合计
watch([() => formData.amount, () => formData.tax_amount], ([amount, tax]) => {
  formData.total_amount = Number(amount || 0) + Number(tax || 0)
}, { immediate: true })

const loadReimbursements = async () => {
  loading.value = true
  try {
    const res = await getReimbursements({
      page: pagination.page,
      page_size: pagination.page_size,
      status: searchForm.status,
      expense_category: searchForm.expense_category,
      year: searchForm.year,
      search: searchForm.search,
    })
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error('加载报销单列表失败')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const res = await getReimbursementStatistics({ year: searchForm.year })
    statistics.value = res
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadPurchaseInvoices = async () => {
  try {
    const res = await getInvoices({ page_size: 100, invoice_type: 'purchase' })
    purchaseInvoices.value = res.items || []
  } catch (error) {
    console.error('加载发票失败:', error)
  }
}

const loadContracts = async () => {
  try {
    const res = await getContracts({ page_size: 100 })
    contracts.value = res.items || []
  } catch (error) {
    console.error('加载合同失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadReimbursements()
  loadStatistics()
}

const handleReset = () => {
  searchForm.status = ''
  searchForm.expense_category = ''
  searchForm.year = null
  searchForm.search = ''
  handleSearch()
}

const openAddDialog = () => {
  showDialog.value = true
  Object.assign(formData, {
    id: '',
    supplier_name: '',
    amount: 0,
    tax_amount: 0,
    total_amount: 0,
    expense_category: 'other',
    invoice_id: '',
    contract_id: '',
    remark: '',
  })
}

const handleEdit = (row) => {
  showDialog.value = true
  Object.assign(formData, {
    id: row.id,
    supplier_name: row.supplier_name,
    amount: Number(row.amount),
    tax_amount: Number(row.tax_amount || 0),
    total_amount: Number(row.total_amount),
    expense_category: row.expense_category,
    invoice_id: row.invoice_id || '',
    contract_id: row.contract_id || '',
    remark: row.remark || '',
  })
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          ...formData,
          total_amount: Number(formData.amount) + Number(formData.tax_amount),
        }
        if (formData.id) {
          await updateReimbursement(formData.id, data)
          ElMessage.success('更新成功')
        } else {
          await createReimbursement(data)
          ElMessage.success('创建成功')
        }
        showDialog.value = false
        loadReimbursements()
        loadStatistics()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleSubmit = async (row) => {
  try {
    await ElMessageBox.confirm('确认提交此报销单进行审核？', '提示', { type: 'info' })
    await submitReimbursement(row.id)
    ElMessage.success('提交成功')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '提交失败')
    }
  }
}

const openApproveDialog = (row) => {
  approveForm.id = row.id
  approveForm.amount = null
  approveForm.expense_category = ''
  showApproveDialog.value = true
}

const handleApprove = async () => {
  try {
    const data = {}
    if (approveForm.amount !== null) data.amount = approveForm.amount
    if (approveForm.expense_category) data.expense_category = approveForm.expense_category
    await approveReimbursement(approveForm.id, data)
    ElMessage.success('审核通过')
    showApproveDialog.value = false
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '审核失败')
  }
}

const openRejectDialog = (row) => {
  rejectForm.id = row.id
  rejectForm.reason = ''
  showRejectDialog.value = true
}

const handleReject = async () => {
  if (!rejectFormRef.value) return
  await rejectFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await rejectReimbursement(rejectForm.id, rejectForm.reason)
        ElMessage.success('已驳回')
        showRejectDialog.value = false
        loadReimbursements()
        loadStatistics()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '驳回失败')
      }
    }
  })
}

const handlePay = async (row) => {
  try {
    await ElMessageBox.confirm('确认支付此报销单？', '提示', { type: 'success' })
    await payReimbursement(row.id)
    ElMessage.success('已确认支付')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '支付确认失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除此报销单？', '提示', { type: 'warning' })
    await deleteReimbursement(row.id)
    ElMessage.success('删除成功')
    loadReimbursements()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleView = (row) => {
  ElMessage.info(`报销单详情：供应商 ${row.supplier_name}，金额 ¥${row.total_amount}`)
}

const showRejectReason = (row) => {
  ElMessageBox.alert(row.reject_reason || '无驳回原因', '驳回原因', { type: 'warning' })
}

onMounted(() => {
  loadReimbursements()
  loadStatistics()
  loadPurchaseInvoices()
  loadContracts()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.statistics-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-value.primary {
  color: #409eff;
}

.stat-value.success {
  color: #67c23a;
}

.stat-count {
  font-size: 12px;
  color: #909399;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Reimbursements.vue
git commit -m "feat: add reimbursement management page

- Statistics cards for pending/approved/paid amounts
- List with status/category/year filtering
- CRUD operations with role-based action buttons
- Workflow dialogs: approve (with edit), reject (with reason)
- Auto-calculate total amount from base + tax

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 6: 配置路由和菜单

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/views/Layout.vue`

- [ ] **Step 1: 在路由配置添加报销管理路由**

修改 `frontend/src/router/index.js`，在 `children` 数组中添加路由配置：

```javascript
// 在 receivables 路由后添加（约第 58 行附近）
{
  path: 'reimbursements',
  name: 'Reimbursements',
  component: () => import('@/views/Reimbursements.vue'),
  meta: { title: '报销管理' },
},
```

同时在路由守卫的 `menuMap` 中添加映射：

```javascript
// 在 menuMap 对象中添加（约第 150 行附近）
'Reimbursements': 'reimbursements',
```

- [ ] **Step 2: 在 Layout 菜单添加报销管理入口**

修改 `frontend/src/views/Layout.vue`：

1. 在 script setup 中添加图标导入：

```javascript
// 在图标导入行添加（约第 99 行）
import { ..., Receipt } from '@element-plus/icons-vue'
```

2. 在菜单中添加报销管理入口（在应收款管理后添加）：

```vue
<!-- 在应收款管理菜单项后添加（约第 34 行附近） -->
<el-menu-item index="/reimbursements" v-if="hasPermission('reimbursements')">
  <el-icon><Receipt /></el-icon>
  <span>报销管理</span>
</el-menu-item>
```

- [ ] **Step 3: 验证前端页面可访问**

启动前端后访问 http://localhost:5174/reimbursements，确认页面正常显示。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.js frontend/src/views/Layout.vue
git commit -m "feat: add reimbursement route and menu entry

- Add /reimbursements route with permission mapping
- Add menu item in Layout sidebar

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 7: 验收测试

- [ ] **Step 1: 测试后端 API**

```bash
# 测试创建报销单
curl -X POST http://localhost:8002/api/reimbursements \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"supplier_name":"测试供应商","amount":1000,"tax_amount":0,"total_amount":1000}'
```

Expected: 返回创建的报销单数据，状态为 draft

- [ ] **Step 2: 测试前端页面功能**

1. 创建报销单（手动录入）
2. 编辑草稿报销单
3. 提交审核
4. 管理员审核通过
5. 管理员确认支付
6. 验证统计卡片数据正确

- [ ] **Step 3: 测试权限控制**

1. 普通用户登录，验证只能看到自己创建的报销单
2. 管理员登录，验证可以看到所有报销单
3. 普通用户验证无法审核/驳回/支付

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git status
# 确认所有文件已提交，无遗漏
git log --oneline -5
```

---

## 自审检查

**1. Spec 覆盖检查：**
- ✅ 数据模型定义 → Task 1
- ✅ Schema 定义 → Task 2
- ✅ API 端点 → Task 3
- ✅ 前端 API 封装 → Task 4
- ✅ 前端页面 → Task 5
- ✅ 路由和菜单 → Task 6
- ✅ 状态流转 → Task 3 (submit/approve/reject/pay)
- ✅ 权限控制 → Task 3 (角色判断逻辑)
- ✅ 统计报表 → Task 3 (statistics API) + Task 5 (统计卡片)

**2. Placeholder 检查：**
- ✅ 无 TBD/TODO
- ✅ 所有代码步骤包含完整代码
- ✅ 所有命令步骤包含具体命令

**3. 类型一致性检查：**
- ✅ ReimbursementCreate → ReimbursementResponse 字段匹配
- ✅ 前端 formData 与后端 Schema 字段名一致
- ✅ 状态枚举值 draft/pending/approved/rejected/paid 一致