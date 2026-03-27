"""合同管理 API"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import os
import uuid
from datetime import date

from app.database import get_db
from app.config import settings
from app.models.contract import Contract
from app.models.contract_attachment import ContractAttachment
from app.models.customer import Customer
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse, ContractListResponse, AttachmentResponse

router = APIRouter()


@router.get("", response_model=ContractListResponse)
async def get_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取合同列表"""
    query = select(Contract)

    if search:
        query = query.where(
            (Contract.name.contains(search)) |
            (Contract.contract_no.contains(search))
        )

    if year:
        query = query.where(func.extract('year', Contract.start_date) == year)

    if status:
        query = query.where(Contract.status == status)
    if customer_id:
        query = query.where(Contract.customer_id == customer_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Contract.created_at.desc())
    query = query.options(selectinload(Contract.attachments))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    contracts = result.scalars().all()

    return ContractListResponse(
        total=total,
        items=[ContractResponse.model_validate(c) for c in contracts]
    )


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    """获取合同详情"""
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.attachments))
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    return ContractResponse.model_validate(contract)


@router.post("", response_model=ContractResponse)
async def create_contract(contract: ContractCreate, db: AsyncSession = Depends(get_db)):
    """创建合同"""
    customer_result = await db.execute(select(Customer).where(Customer.id == contract.customer_id))
    if not customer_result.scalar():
        raise HTTPException(status_code=400, detail="客户不存在")

    db_contract = Contract(**contract.model_dump())
    db.add(db_contract)
    await db.commit()

    # 重新加载并预加载附件
    result = await db.execute(
        select(Contract)
        .where(Contract.id == db_contract.id)
        .options(selectinload(Contract.attachments))
    )
    db_contract = result.scalar_one()

    return ContractResponse.model_validate(db_contract)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(contract_id: str, contract: ContractUpdate, db: AsyncSession = Depends(get_db)):
    """更新合同"""
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.attachments))
    )
    db_contract = result.scalar_one_or_none()

    if not db_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    update_data = contract.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contract, field, value)

    await db.commit()

    # 重新加载并预加载附件
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.attachments))
    )
    db_contract = result.scalar_one()

    return ContractResponse.model_validate(db_contract)


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    """删除合同"""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    db_contract = result.scalar_one_or_none()

    if not db_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    await db.delete(db_contract)
    await db.commit()

    return {"message": "删除成功"}


@router.post("/{contract_id}/files")
async def upload_contract_file(
    contract_id: str,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """上传合同附件（支持多文件）"""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    db_contract = result.scalar_one_or_none()

    if not db_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    upload_dir = os.path.join(settings.UPLOAD_DIR, "contracts")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 创建附件记录
    attachment = ContractAttachment(
        contract_id=contract_id,
        file_name=file.filename or filename,
        file_path=filepath,
        file_url=f"/uploads/contracts/{filename}",
        file_type=ext[1:] if ext else "",
        file_size=str(len(content)),
        is_primary=is_primary,
    )
    db.add(attachment)

    # 如果是主文件，同时更新合同的主文件字段
    if is_primary:
        db_contract.file_path = filepath
        db_contract.file_id = file_id
        db_contract.file_url = f"/uploads/contracts/{filename}"

    await db.commit()
    await db.refresh(attachment)

    return {
        "id": attachment.id,
        "file_name": attachment.file_name,
        "file_url": attachment.file_url,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,
        "is_primary": attachment.is_primary,
    }


@router.get("/{contract_id}/files")
async def get_contract_files(contract_id: str, db: AsyncSession = Depends(get_db)):
    """获取合同附件列表"""
    result = await db.execute(
        select(ContractAttachment)
        .where(ContractAttachment.contract_id == contract_id)
        .order_by(ContractAttachment.is_primary.desc(), ContractAttachment.created_at.desc())
    )
    attachments = result.scalars().all()

    return {
        "total": len(attachments),
        "items": [
            {
                "id": att.id,
                "file_name": att.file_name,
                "file_path": att.file_path,
                "file_url": att.file_url,
                "file_type": att.file_type,
                "file_size": att.file_size,
                "is_primary": att.is_primary,
                "created_at": att.created_at.isoformat(),
            }
            for att in attachments
        ],
    }


@router.delete("/{contract_id}/files/{file_id}")
async def delete_contract_file(contract_id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    """删除合同附件"""
    # 验证合同存在
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    db_contract = result.scalar_one_or_none()
    if not db_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 查找附件
    result = await db.execute(select(ContractAttachment).where(ContractAttachment.id == file_id))
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="文件不存在")

    if attachment.contract_id != contract_id:
        raise HTTPException(status_code=400, detail="文件不属于该合同")

    # 删除文件记录（cascade 会处理关联关系）
    await db.delete(attachment)
    await db.commit()

    return {"message": "删除成功"}
