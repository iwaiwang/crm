"""项目进度 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.project import Project, ProjectFollowup, ProjectPhase, ProjectTask
from app.models.customer import Customer
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    FollowupCreate, FollowupResponse, PhaseCreate, PhaseResponse, TaskCreate, TaskResponse
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

    return ProjectListResponse(
        total=total,
        items=[ProjectResponse.model_validate(p) for p in projects]
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 预加载关联关系，避免 model_validate 时触发异步查询
    await db.refresh(project, attribute_names=['followups', 'phases', 'tasks'])
    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """创建项目"""
    try:
        result = await db.execute(select(Customer).where(Customer.id == project.customer_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="客户不存在")

        db_project = Project(**project.model_dump())
        db.add(db_project)
        await db.commit()
        # 预加载关联关系，避免 model_validate 时触发异步查询
        await db.refresh(db_project, attribute_names=['followups', 'phases', 'tasks'])

        return ProjectResponse.model_validate(db_project)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in create_project: {e}")
        print(traceback.format_exc())
        raise


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
    # 预加载关联关系，避免 model_validate 时触发异步查询
    await db.refresh(db_project, attribute_names=['followups', 'phases', 'tasks'])
    return ProjectResponse.model_validate(db_project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """删除项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()

    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(db_project)
    await db.commit()

    return {"message": "删除成功"}


@router.post("/{project_id}/followups", response_model=FollowupResponse)
async def create_followup(project_id: str, followup: FollowupCreate, db: AsyncSession = Depends(get_db)):
    """添加销售跟进记录"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar():
        raise HTTPException(status_code=404, detail="项目不存在")

    db_followup = ProjectFollowup(**followup.model_dump(), project_id=project_id)
    db.add(db_followup)
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

    db_phase = ProjectPhase(**phase.model_dump(), project_id=project_id)
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

    db_task = ProjectTask(**task.model_dump(), project_id=project_id)
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
