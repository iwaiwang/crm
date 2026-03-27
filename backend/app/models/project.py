"""项目进度模型（销售/实施）"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, Integer, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, comment="项目名称")
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, comment="关联客户")
    contract_id = Column(String(36), ForeignKey("contracts.id"), comment="关联合同")
    manager = Column(String(100), comment="负责人")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="预计结束日期")
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    status = Column(
        SQLEnum("contact", "bidding", "signing", "implementation", "acceptance", "after_sales", name="project_status"),
        default="contact",
        comment="项目状态",
    )

    # 投标信息
    budget_amount = Column(DECIMAL(15, 2), comment="预算金额")
    bid_amount = Column(DECIMAL(15, 2), comment="中标金额")
    bid_date = Column(Date, comment="投标日期")
    bid_result = Column(String(50), comment="中标结果")
    competitor = Column(String(200), comment="竞争对手")

    # 其他
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    customer = relationship("Customer", back_populates="projects")
    contract = relationship("Contract", back_populates="project")
    followups = relationship("ProjectFollowup", back_populates="project", cascade="all, delete-orphan")
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectFollowup(Base):
    """销售跟进记录"""
    __tablename__ = "project_followups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    followup_by = Column(String(100), comment="跟进人")
    followup_date = Column(Date, nullable=False, comment="跟进日期")
    followup_method = Column(String(50), comment="跟进方式 (上门/电话/微信/邮件)")
    content = Column(Text, comment="跟进内容")
    result = Column(String(100), comment="跟进结果")
    next_plan = Column(Text, comment="下一步计划")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="followups")


class ProjectPhase(Base):
    """项目实施阶段"""
    __tablename__ = "project_phases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="阶段名称")
    plan_start = Column(Date, comment="计划开始日期")
    plan_end = Column(Date, comment="计划结束日期")
    actual_start = Column(Date, comment="实际开始日期")
    actual_end = Column(Date, comment="实际结束日期")
    progress = Column(Integer, default=0, comment="进度百分比")
    status = Column(
        SQLEnum("not_started", "in_progress", "completed", "suspended", name="project_phase_status"),
        default="not_started",
        comment="阶段状态",
    )
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="phases")


class ProjectTask(Base):
    """项目任务"""
    __tablename__ = "project_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="任务名称")
    assignee = Column(String(100), comment="负责人")
    due_date = Column(Date, comment="截止日期")
    progress = Column(Integer, default=0, comment="进度百分比")
    status = Column(String(20), default="pending", comment="状态")
    completed_at = Column(Date, comment="完成日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="tasks")
