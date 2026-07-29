"""项目进度 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.project import Project, ProjectFollowup, ProjectPhase, ProjectTask
from app.models.customer import Customer
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse, ProjectListItem,
    FollowupCreate, FollowupResponse, PhaseCreate, PhaseResponse, TaskCreate, TaskResponse,
    FunnelStage, FunnelResponse
)

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    manager: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表"""
    query = select(Project)

    if search:
        query = query.where(Project.name.contains(search))
    if status:
        query = query.where(Project.status == status)
    if manager:
        query = query.where(Project.manager == manager)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Project.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    # 获取所有项目的客户名称
    customer_ids = list(set(p.customer_id for p in projects))
    customer_map = {}
    if customer_ids:
        cust_result = await db.execute(
            select(Customer.id, Customer.name).where(Customer.id.in_(customer_ids))
        )
        for row in cust_result:
            customer_map[row[0]] = row[1]

    items = []
    for p in projects:
        item = ProjectListItem.model_validate(p)
        item.customer_name = customer_map.get(p.customer_id, "")
        items.append(item)

    return ProjectListResponse(
        total=total,
        items=items
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取项目详情"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.followups))
        .options(selectinload(Project.phases))
        .options(selectinload(Project.tasks))
    )
    project = result.unique().scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """创建项目"""
    result = await db.execute(select(Customer).where(Customer.id == project.customer_id))
    if not result.scalar():
        raise HTTPException(status_code=400, detail="客户不存在")

    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return ProjectResponse.model_validate(db_project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    """更新项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()

    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    await db.commit()
    await db.refresh(db_project)
    return ProjectResponse.model_validate(db_project)


@router.post("/batch-delete")
async def batch_delete_projects(ids: list[str], db: AsyncSession = Depends(get_db)):
    """批量删除项目"""
    from sqlalchemy import text

    for project_id in ids:
        # 删除子表记录
        await db.execute(text("DELETE FROM project_tasks WHERE project_id = :pid"), {"pid": project_id})
        await db.execute(text("DELETE FROM project_phases WHERE project_id = :pid"), {"pid": project_id})
        await db.execute(text("DELETE FROM project_followups WHERE project_id = :pid"), {"pid": project_id})

    await db.commit()
    await db.close()

    # 批量删除项目
    result = await db.execute(select(Project).where(Project.id.in_(ids)))
    projects = result.scalars().all()

    for project in projects:
        await db.delete(project)

    await db.commit()

    return {"message": f"成功删除 {len(projects)} 个项目"}


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """删除项目"""
    from sqlalchemy import text

    # 先删除子表记录
    await db.execute(text("DELETE FROM project_tasks WHERE project_id = :pid"), {"pid": project_id})
    await db.execute(text("DELETE FROM project_phases WHERE project_id = :pid"), {"pid": project_id})
    await db.execute(text("DELETE FROM project_followups WHERE project_id = :pid"), {"pid": project_id})
    await db.commit()

    # 关闭 session 清除缓存对象
    await db.close()

    # 重新获取并删除项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()

    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(db_project)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/stats/funnel", response_model=FunnelResponse)
async def get_funnel_stats(db: AsyncSession = Depends(get_db)):
    """获取销售漏斗统计数据"""
    from sqlalchemy import text

    result = await db.execute(
        select(Project.status, func.count(Project.id), func.coalesce(func.sum(Project.budget_amount), 0))
        .group_by(Project.status)
    )
    rows = result.all()

    status_map = {
        "contact": "接触洽谈",
        "bidding": "投标",
        "signing": "签约",
        "implementation": "实施",
        "acceptance": "验收",
        "after_sales": "售后",
        "lost": "流失",
    }

    status_order = ["contact", "bidding", "signing", "implementation", "acceptance", "after_sales", "lost"]
    row_map = {r[0]: r for r in rows}

    stages = []
    for status in status_order:
        r = row_map.get(status, (status, 0, 0))
        stages.append(FunnelStage(
            status=status,
            label=status_map.get(status, status),
            count=r[1],
            total_amount=float(r[2] or 0)
        ))

    return FunnelResponse(stages=stages)


@router.post("/{project_id}/followups", response_model=FollowupResponse)
async def create_followup(project_id: str, followup: FollowupCreate, db: AsyncSession = Depends(get_db)):
    """添加销售跟进记录"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db_followup = ProjectFollowup(**followup.model_dump(exclude={'project_id'}), project_id=project_id)
    db.add(db_followup)

    # 更新项目的最后跟进时间
    from datetime import datetime
    project.last_followup_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_followup)

    return FollowupResponse.model_validate(db_followup)


@router.get("/{project_id}/followups", response_model=list[FollowupResponse])
async def get_project_followups(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取项目跟进记录"""
    result = await db.execute(
        select(ProjectFollowup)
        .where(ProjectFollowup.project_id == project_id)
        .order_by(ProjectFollowup.followup_date.desc())
    )
    followups = result.scalars().all()

    return [FollowupResponse.model_validate(f) for f in followups]


@router.post("/{project_id}/phases", response_model=PhaseResponse)
async def create_phase(project_id: str, phase: PhaseCreate, db: AsyncSession = Depends(get_db)):
    """添加项目阶段"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar():
        raise HTTPException(status_code=404, detail="项目不存在")

    db_phase = ProjectPhase(**phase.model_dump(exclude={'project_id'}), project_id=project_id)
    db.add(db_phase)
    await db.commit()
    await db.refresh(db_phase)

    return PhaseResponse.model_validate(db_phase)


@router.get("/{project_id}/phases", response_model=list[PhaseResponse])
async def get_project_phases(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取项目阶段"""
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.project_id == project_id)
        .order_by(ProjectPhase.created_at.asc())
    )
    phases = result.scalars().all()

    return [PhaseResponse.model_validate(p) for p in phases]


@router.put("/{project_id}/phases/{phase_id}", response_model=PhaseResponse)
async def update_phase(project_id: str, phase_id: str, phase_data: dict, db: AsyncSession = Depends(get_db)):
    """更新项目阶段"""
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.id == phase_id)
        .where(ProjectPhase.project_id == project_id)
    )
    db_phase = result.scalar_one_or_none()

    if not db_phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    for field, value in phase_data.items():
        if hasattr(db_phase, field) and value is not None:
            setattr(db_phase, field, value)

    await db.commit()
    await db.refresh(db_phase)

    return PhaseResponse.model_validate(db_phase)


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: str, task: TaskCreate, db: AsyncSession = Depends(get_db)):
    """添加项目任务"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar():
        raise HTTPException(status_code=404, detail="项目不存在")

    db_task = ProjectTask(**task.model_dump(exclude={'project_id'}), project_id=project_id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return TaskResponse.model_validate(db_task)


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def get_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取项目任务"""
    result = await db.execute(
        select(ProjectTask)
        .where(ProjectTask.project_id == project_id)
        .order_by(ProjectTask.due_date.asc())
    )
    tasks = result.scalars().all()

    return [TaskResponse.model_validate(t) for t in tasks]


@router.put("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(project_id: str, task_id: str, task_data: dict, db: AsyncSession = Depends(get_db)):
    """更新项目任务"""
    result = await db.execute(
        select(ProjectTask)
        .where(ProjectTask.id == task_id)
        .where(ProjectTask.project_id == project_id)
    )
    db_task = result.scalar_one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail="任务不存在")

    for field, value in task_data.items():
        if hasattr(db_task, field) and value is not None:
            setattr(db_task, field, value)

    if task_data.get("status") == "completed" and not db_task.completed_at:
        db_task.completed_at = date.today()

    await db.commit()
    await db.refresh(db_task)

    return TaskResponse.model_validate(db_task)
