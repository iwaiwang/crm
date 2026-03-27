"""项目进度 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ProjectStatus(str, Enum):
    CONTACT = "contact"
    BIDDING = "bidding"
    SIGNING = "signing"
    IMPLEMENTATION = "implementation"
    ACCEPTANCE = "acceptance"
    AFTER_SALES = "after_sales"


class ProjectPhaseStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class ProjectBase(BaseModel):
    name: str = Field(..., description="项目名称", max_length=200)
    customer_id: str = Field(..., description="关联客户")
    contract_id: Optional[str] = Field(None, description="关联合同")
    manager: Optional[str] = Field(None, description="负责人", max_length=100)
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="预计结束日期")
    progress: int = Field(default=0, description="进度百分比 0-100", ge=0, le=100)
    status: ProjectStatus = Field(default=ProjectStatus.CONTACT, description="项目状态")

    # 投标信息
    budget_amount: Optional[Decimal] = Field(None, description="预算金额")
    bid_amount: Optional[Decimal] = Field(None, description="中标金额")
    bid_date: Optional[date] = Field(None, description="投标日期")
    bid_result: Optional[str] = Field(None, description="中标结果")
    competitor: Optional[str] = Field(None, description="竞争对手", max_length=200)

    remark: Optional[str] = Field(None, description="备注")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    customer_id: Optional[str] = None
    contract_id: Optional[str] = None
    manager: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[ProjectStatus] = None
    budget_amount: Optional[Decimal] = None
    bid_amount: Optional[Decimal] = None
    bid_date: Optional[date] = None
    bid_result: Optional[str] = None
    competitor: Optional[str] = Field(None, max_length=200)
    remark: Optional[str] = None


class FollowupBase(BaseModel):
    followup_by: str = Field(..., description="跟进人", max_length=100)
    followup_date: date = Field(..., description="跟进日期")
    followup_method: Optional[str] = Field(None, description="跟进方式")
    content: Optional[str] = Field(None, description="跟进内容")
    result: Optional[str] = Field(None, description="跟进结果")
    next_plan: Optional[str] = Field(None, description="下一步计划")


class FollowupCreate(FollowupBase):
    project_id: str


class PhaseBase(BaseModel):
    name: str = Field(..., description="阶段名称", max_length=100)
    plan_start: Optional[date] = Field(None, description="计划开始日期")
    plan_end: Optional[date] = Field(None, description="计划结束日期")
    progress: int = Field(default=0, description="进度百分比")
    status: ProjectPhaseStatus = Field(default=ProjectPhaseStatus.NOT_STARTED)
    remark: Optional[str] = None


class PhaseCreate(PhaseBase):
    project_id: str


class TaskBase(BaseModel):
    name: str = Field(..., description="任务名称", max_length=200)
    assignee: Optional[str] = Field(None, description="负责人")
    due_date: Optional[date] = Field(None, description="截止日期")
    progress: int = Field(default=0, description="进度百分比")
    status: str = Field(default="pending", description="状态")


class TaskCreate(TaskBase):
    project_id: str


class FollowupResponse(FollowupBase):
    id: str
    project_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PhaseResponse(PhaseBase):
    id: str
    project_id: str
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    id: str
    project_id: str
    completed_at: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    # 关联关系字段，默认不加载，需要单独查询
    followups: Optional[List[FollowupResponse]] = Field(default_factory=list)
    phases: Optional[List[PhaseResponse]] = Field(default_factory=list)
    tasks: Optional[List[TaskResponse]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    total: int
    items: List[ProjectResponse]
