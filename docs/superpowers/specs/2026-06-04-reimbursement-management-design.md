# 报销管理模块设计文档

## 1. 概述

### 1.1 背景

现有系统的发票管理支持进项发票录入，但缺乏审批和支付流程。支出管理直接记录已完成的支出，无法区分"待审批"和"已支付"状态。需要新增报销管理模块，实现完整的费用报销审批流程。

### 1.2 目标

- 实现报销单的录入、审核、支付三步流程
- 支持从进项发票生成报销单，也支持无发票的费用报销
- 提供应付/已付/待付的统计分析

### 1.3 范围

- 新增报销管理模块（后端模型、API、前端页面）
- 不修改现有的发票管理和支出管理模块

## 2. 业务流程

### 2.1 状态流转

```
草稿(draft) → 待审核(pending) → 已审核(approved) → 已支付(paid)
                  ↓
               已驳回(rejected) → (录入人修改后) → 待审核(pending)
```

### 2.2 角色权限

| 操作 | 普通用户 | 管理员 |
|------|----------|--------|
| 创建报销单 | 可 | 可 |
| 编辑/删除 | 仅自己的草稿 | 所有草稿和驳回状态 |
| 提交审核 | 仅自己的草稿 | 所有 |
| 审核/驳回 | 无 | 可 |
| 确认支付 | 无 | 可 |
| 查看列表 | 仅自己创建的 | 所有 |

### 2.3 操作说明

1. **录入**：用户创建报销单，可从进项发票导入或手动录入
2. **提交**：录入人提交报销单进入待审核状态
3. **审核**：管理员审核通过，或修改金额/分类后通过，或填写驳回原因退回
4. **支付**：管理员点击"已支付"按钮确认支付

## 3. 数据模型

### 3.1 Reimbursement 报销单表

```python
class Reimbursement(Base):
    __tablename__ = "reimbursements"

    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 来源信息
    source_type = Column(
        SQLEnum("invoice", "manual", name="reimbursement_source_type"),
        default="manual",
        comment="来源类型：invoice=从发票导入，manual=手动录入"
    )
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True, comment="关联进项发票ID")
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True, comment="关联合同ID")

    # 基本信息
    supplier_name = Column(String(100), nullable=False, comment="供应商/收款方名称")
    amount = Column(DECIMAL(15, 2), nullable=False, default=0, comment="报销金额（不含税）")
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
```

### 3.2 字段约束

- `supplier_name`：必填
- `amount`：必填，大于 0
- `total_amount`：必填，等于 amount + tax_amount
- `created_by`：必填，关联用户表

### 3.3 状态定义

| 状态值 | 中文名 | 说明 |
|--------|--------|------|
| draft | 草稿 | 新建未提交，可编辑删除 |
| pending | 待审核 | 已提交，等待管理员审核 |
| approved | 已审核 | 审核通过，等待支付确认 |
| rejected | 已驳回 | 管理员驳回，录入人可修改重提 |
| paid | 已支付 | 支付确认完成，流程结束 |

## 4. API 设计

### 4.1 API 端点列表

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/reimbursements` | 创建报销单 | 所有用户 |
| GET | `/api/reimbursements` | 获取报销单列表 | 普通用户看自己的，管理员看全部 |
| GET | `/api/reimbursements/{id}` | 获取报销单详情 | 有查看权限的用户 |
| PUT | `/api/reimbursements/{id}` | 更新报销单 | 仅草稿/驳回状态可编辑 |
| DELETE | `/api/reimbursements/{id}` | 删除报销单 | 仅草稿状态可删除 |
| POST | `/api/reimbursements/{id}/submit` | 提交审核 | 录入人操作 |
| POST | `/api/reimbursements/{id}/approve` | 审核通过 | 管理员操作 |
| POST | `/api/reimbursements/{id}/reject` | 驳回报销单 | 管理员操作 |
| POST | `/api/reimbursements/{id}/pay` | 确认支付 | 管理员操作 |
| GET | `/api/reimbursements/statistics` | 统计报表 | 所有用户 |

### 4.2 请求/响应 Schema

#### 创建报销单请求

```python
class ReimbursementCreate(BaseModel):
    source_type: Optional[str] = "manual"
    invoice_id: Optional[str] = None
    contract_id: Optional[str] = None
    supplier_name: str
    amount: Decimal
    tax_amount: Optional[Decimal] = 0
    total_amount: Decimal
    expense_category: str = "other"
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
```

#### 更新报销单请求

```python
class ReimbursementUpdate(BaseModel):
    supplier_name: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    expense_category: Optional[str] = None
    remark: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
```

#### 驳回请求

```python
class ReimbursementReject(BaseModel):
    reason: str  # 驳回原因，必填
```

#### 列表响应

```python
class ReimbursementListResponse(BaseModel):
    total: int
    items: List[ReimbursementResponse]
```

#### 统计响应

```python
class ReimbursementStatistics(BaseModel):
    total_pending_amount: Decimal  # 待审核金额
    total_approved_amount: Decimal  # 待支付金额
    total_paid_amount: Decimal  # 已支付金额
    by_category: Dict[str, Decimal]  # 按分类统计
```

### 4.3 查询参数

**列表查询 GET `/api/reimbursements`：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| page_size | int | 每页数量，默认 20 |
| status | str | 状态筛选 |
| expense_category | str | 分类筛选 |
| year | int | 年份筛选 |
| month | int | 月份筛选 |
| search | str | 供应商名称搜索 |

## 5. 前端设计

### 5.1 页面结构

新增页面 `frontend/src/views/Reimbursements.vue`，路由 `/reimbursements`。

### 5.2 页面布局

```
┌─────────────────────────────────────────────────────┐
│ 报销管理                    [新增报销单] [AI导入]    │
├─────────────────────────────────────────────────────┤
│ [统计卡片]                                          │
│ 待审核 ¥0  |  待支付 ¥0  |  已支付 ¥0              │
├─────────────────────────────────────────────────────┤
│ 状态: [全部▼] 分类: [全部▼] 年份: [2026▼] 搜索... │
├─────────────────────────────────────────────────────┤
│ 报销单列表                                          │
│ ┌─────┬────────┬──────┬──────┬──────┬──────┬─────┐ │
│ │ 选择│供应商  │金额  │分类  │状态  │录入人│操作 │ │
│ ├─────┼────────┼──────┼──────┼──────┼──────┼─────┤ │
│ │ ☐   │XX公司  │¥1000 │采购  │待审核│张三  │审核 │ │
│ └─────┴────────┴──────┴──────┴──────┴──────┴─────┘ │
│ [分页]                                              │
└─────────────────────────────────────────────────────┘
```

### 5.3 状态标签颜色

| 状态 | 颜色 | Element Plus Tag type |
|------|------|----------------------|
| draft | 灰色 | info |
| pending | 橙色 | warning |
| approved | 蓝色 | primary |
| rejected | 红色 | danger |
| paid | 绿色 | success |

### 5.4 新建/编辑报销单 Drawer

```
┌───────────────────────────────────┐
│ 新增报销单                        │
├───────────────────────────────────┤
│ 来源类型: ○ 从发票导入 ● 手动录入 │
│ ──────────────────────────────── │
│ 供应商/收款方: [____________]     │
│ 报销金额(不含税): [_______]       │
│ 税额: [_______]                   │
│ 价税合计: [_______] (自动计算)    │
│ 费用分类: [采购▼]                 │
│ 关联发票: [可选▼]                 │
│ 关联合同: [可选▼]                 │
│ 备注: [___________________]       │
│ 附件: [上传文件]                  │
├───────────────────────────────────┤
│           [取消] [保存]           │
└───────────────────────────────────┘
```

### 5.5 统计图表

在列表上方显示统计卡片：
- 待审核金额（pending 状态 total_amount 合计）
- 待支付金额（approved 状态 total_amount 合计）
- 已支付金额（paid 状态 total_amount 合计）

可选：按分类的饼图/柱状图展示各分类支出占比。

## 6. 实现计划

### 6.1 后端实现

1. 创建 `backend/app/models/reimbursement.py`
2. 创建 `backend/app/schemas/reimbursement.py`
3. 创建 `backend/app/api/reimbursements.py`
4. 在 `backend/app/main.py` 注册路由
5. 在 Invoice 和 Contract 模型添加 `reimbursements` relationship

### 6.2 前端实现

1. 创建 `frontend/src/api/reimbursement.js`
2. 创建 `frontend/src/views/Reimbursements.vue`
3. 在 `frontend/src/router/index.js` 添加路由
4. 在 Layout 菜单中添加导航项
5. 在用户权限配置中添加 `reimbursements` 权限项

### 6.3 数据库迁移

新增 `reimbursements` 表，执行数据库初始化自动创建。

## 7. 测试要点

### 7.1 功能测试

- 创建报销单（手动录入）
- 创建报销单（从发票导入）
- 编辑草稿报销单
- 提交审核
- 审核通过
- 驳回并填写原因
- 驳回后修改重提
- 确认支付
- 删除草稿报销单

### 7.2 权限测试

- 普通用户只能看到自己创建的报销单
- 管理员可以看到所有报销单
- 普通用户无法审核/驳回/支付
- 管理员可以审核/驳回/支付

### 7.3 统计测试

- 统计数据准确反映各状态金额合计
- 按分类统计准确

## 8. 兼容性说明

- 本模块为新增模块，不影响现有发票管理、支出管理功能
- 可选择性地将已支付的报销单同步到支出管理（未来扩展）
- 费用分类与现有支出管理的分类保持一致