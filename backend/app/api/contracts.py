"""Contract management API."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import os
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user, require_menu_permission, require_any_menu_permission
from app.config import settings
from app.database import get_db
from app.models.ai_config import AIConfig
from app.models.contract import Contract
from app.models.contract_file import ContractFile
from app.models.customer import Customer
from app.models.receivable import Receivable
from app.models.user import User
from app.schemas.contract import (
    AiContractDraft,
    AiReceivableDraft,
    ContractAiConfirmRequest,
    ContractAiPreviewRequest,
    ContractAiPreviewResponse,
    ContractCreate,
    ContractListResponse,
    ContractResponse,
    ContractUpdate,
)
from app.services.ai_parser import ai_service

router = APIRouter()

SUPPORTED_CONTRACT_EXTENSIONS = ["pdf", "doc", "docx", "jpg", "jpeg", "png"]


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _to_decimal(value, default: str = "0") -> Decimal:
    if value in (None, ""):
        return Decimal(default)
    cleaned = str(value).replace(",", "").replace("￥", "").replace("¥", "").strip()
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _to_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    cleaned = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _generate_contract_no() -> str:
    return f"AI-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _resolve_receivable_due_date(raw_due_date, contract_start_date: Optional[date]) -> date:
    parsed_due_date = _to_date(raw_due_date)
    if parsed_due_date:
        return parsed_due_date
    if contract_start_date:
        return contract_start_date
    return date.today()


def _resolve_contract_upload(file_id: str) -> tuple[str, str, str, str]:
    upload_dir = os.path.join(settings.UPLOAD_DIR, "contracts")
    for ext in SUPPORTED_CONTRACT_EXTENSIONS:
        filename = f"{file_id}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        if os.path.exists(filepath):
            return filepath, ext, f"/uploads/contracts/{filename}", filename
    raise HTTPException(status_code=404, detail="合同文件不存在")


async def _load_ai_config(db: AsyncSession) -> None:
    result = await db.execute(select(AIConfig).limit(1))
    db_config = result.scalar_one_or_none()
    if not db_config or not db_config.enabled:
        raise HTTPException(status_code=503, detail="AI 服务未启用")

    ai_service.load_config_from_db(
        {
            "service_type": db_config.service_type,
            "api_base_url": db_config.api_base_url,
            "api_key": db_config.api_key,
            "model": db_config.model,
            "ollama_base_url": db_config.ollama_base_url,
            "ollama_model": db_config.ollama_model,
            "timeout": db_config.timeout,
            "enabled": db_config.enabled,
        }
    )


async def _match_customer(customer_name: Optional[str], db: AsyncSession) -> tuple[Optional[Customer], List[str]]:
    cleaned_name = _clean_text(customer_name)
    if not cleaned_name:
        return None, []

    result = await db.execute(select(Customer).order_by(Customer.name.asc()))
    customers = result.scalars().all()

    exact_match = next((customer for customer in customers if customer.name == cleaned_name), None)
    if exact_match:
        return exact_match, [exact_match.name]

    fuzzy_matches = [
        customer
        for customer in customers
        if cleaned_name in customer.name or customer.name in cleaned_name
    ]
    if fuzzy_matches:
        return fuzzy_matches[0], [customer.name for customer in fuzzy_matches[:5]]

    return None, []


def _can_auto_create_customer(customer_name: Optional[str]) -> bool:
    cleaned_name = _clean_text(customer_name)
    if not cleaned_name or len(cleaned_name) < 4:
        return False

    generic_names = {
        "甲方",
        "乙方",
        "客户",
        "客户单位",
        "采购方",
        "采购单位",
        "供应商",
        "医院",
        "公司",
        "项目",
        "单位",
    }
    return cleaned_name not in generic_names


async def _get_or_create_customer(
    customer_id: Optional[str],
    customer_name: Optional[str],
    db: AsyncSession,
) -> Customer:
    if customer_id:
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if customer:
            return customer
        raise HTTPException(status_code=400, detail="客户不存在")

    matched_customer, _ = await _match_customer(customer_name, db)
    if matched_customer:
        return matched_customer

    cleaned_name = _clean_text(customer_name)
    if not _can_auto_create_customer(cleaned_name):
        raise HTTPException(status_code=400, detail="未匹配到客户，请补充明确的客户名称或手动选择")

    customer = Customer(
        name=cleaned_name,
        category="normal",
        status="active",
        remark="AI录入合同时自动创建",
    )
    db.add(customer)
    await db.flush()
    return customer


async def _ensure_contract_file(
    *,
    db: AsyncSession,
    contract_id: str,
    uploaded_file_id: str,
    preferred_name: Optional[str],
    source: str,
    is_primary: bool,
) -> ContractFile:
    existing_result = await db.execute(
        select(ContractFile).where(ContractFile.file_id == uploaded_file_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.contract_id != contract_id:
            raise HTTPException(status_code=400, detail="该文件已绑定到其他合同")
        if is_primary:
            await _set_primary_contract_file(db=db, contract_id=contract_id, contract_file_id=existing.id)
            existing.is_primary = True
        return existing

    file_path, file_type, file_url, filename = _resolve_contract_upload(uploaded_file_id)
    order_result = await db.execute(
        select(func.max(ContractFile.sort_order)).where(ContractFile.contract_id == contract_id)
    )
    current_max_sort = order_result.scalar_one()
    next_sort = 0 if current_max_sort is None else int(current_max_sort) + 1

    if is_primary:
        await db.execute(
            text("UPDATE contract_files SET is_primary = 0 WHERE contract_id = :cid"),
            {"cid": contract_id},
        )

    contract_file = ContractFile(
        contract_id=contract_id,
        file_id=uploaded_file_id,
        file_name=_clean_text(preferred_name) or filename,
        file_path=file_path,
        file_url=file_url,
        file_type=file_type,
        file_size=os.path.getsize(file_path),
        source=source,
        is_primary=is_primary,
        sort_order=next_sort,
    )
    db.add(contract_file)
    await db.flush()
    return contract_file


async def _set_primary_contract_file(*, db: AsyncSession, contract_id: str, contract_file_id: str) -> None:
    await db.execute(
        text("UPDATE contract_files SET is_primary = 0 WHERE contract_id = :cid"),
        {"cid": contract_id},
    )
    await db.execute(
        text("UPDATE contract_files SET is_primary = 1 WHERE id = :fid AND contract_id = :cid"),
        {"fid": contract_file_id, "cid": contract_id},
    )


async def _promote_next_primary_file(*, db: AsyncSession, contract_id: str) -> None:
    next_file_result = await db.execute(
        select(ContractFile)
        .where(ContractFile.contract_id == contract_id)
        .order_by(ContractFile.sort_order.asc(), ContractFile.created_at.asc())
        .limit(1)
    )
    next_file = next_file_result.scalar_one_or_none()
    if next_file:
        next_file.is_primary = True


def _build_receivable_plan(payment_terms: Optional[str], total_amount: Decimal) -> List[AiReceivableDraft]:
    normalized_amount = total_amount if total_amount > 0 else Decimal("0")
    cleaned_terms = _clean_text(payment_terms)
    if normalized_amount <= 0:
        return []

    if not cleaned_terms:
        return [
            AiReceivableDraft(
                amount=normalized_amount,
                percent=100.0,
                due_date=None,
                remark="未识别付款条款，按合同总金额生成",
            )
        ]

    percentages = [
        max(min(float(match), 100.0), 0.0)
        for match in re.findall(r"(\d+(?:\.\d+)?)\s*%", cleaned_terms)
    ]
    receivables: List[AiReceivableDraft] = []

    if percentages:
        segments = [segment.strip() for segment in re.split(r"[，。,；;\n]+", cleaned_terms) if segment.strip()]
        segment_index = 0
        total_percent = 0.0
        for percent in percentages:
            total_percent += percent
            amount = (normalized_amount * Decimal(str(percent)) / Decimal("100")).quantize(Decimal("0.01"))
            remark = None
            while segment_index < len(segments):
                segment = segments[segment_index]
                segment_index += 1
                if f"{percent:g}%" in segment:
                    remark = segment
                    break
            receivables.append(
                AiReceivableDraft(
                    amount=amount,
                    percent=round(percent, 2),
                    due_date=None,
                    remark=remark or f"付款节点 {len(receivables) + 1}",
                )
            )

        if total_percent < 99.99:
            remainder_amount = normalized_amount - sum(item.amount for item in receivables)
            if remainder_amount > 0:
                receivables.append(
                    AiReceivableDraft(
                        amount=remainder_amount.quantize(Decimal("0.01")),
                        percent=round(100 - total_percent, 2),
                        due_date=None,
                        remark="剩余尾款",
                    )
                )

        if receivables:
            return receivables

    return [
        AiReceivableDraft(
            amount=normalized_amount,
            percent=100.0,
            due_date=None,
            remark="未识别清晰付款比例，按合同总金额生成",
        )
    ]


async def _load_contract_with_files(contract_id: str, db: AsyncSession) -> Contract:
    result = await db.execute(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(selectinload(Contract.files))
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.get("", response_model=ContractListResponse)
async def get_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_menu_permission(['contracts', 'reimbursements'])),
):
    query = select(Contract)

    if search:
        query = query.where((Contract.name.contains(search)) | (Contract.contract_no.contains(search)))
    if year:
        query = query.where(func.extract("year", Contract.start_date) == year)
    if status:
        query = query.where(Contract.status == status)
    if customer_id:
        query = query.where(Contract.customer_id == customer_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    result = await db.execute(
        query.order_by(Contract.created_at.desc())
        .options(selectinload(Contract.files))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    contracts = result.scalars().all()

    return ContractListResponse(total=total, items=[ContractResponse.model_validate(item) for item in contracts])


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    contract = await _load_contract_with_files(contract_id, db)
    return ContractResponse.model_validate(contract)


@router.post("", response_model=ContractResponse)
async def create_contract(contract: ContractCreate, db: AsyncSession = Depends(get_db)):
    customer_result = await db.execute(select(Customer).where(Customer.id == contract.customer_id))
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="客户不存在")

    payload = contract.model_dump(exclude={"file_id", "file_url"})
    db_contract = Contract(**payload)
    db.add(db_contract)

    try:
        await db.flush()
        if contract.file_id:
            await _ensure_contract_file(
                db=db,
                contract_id=db_contract.id,
                uploaded_file_id=contract.file_id,
                preferred_name=contract.name,
                source="manual",
                is_primary=True,
            )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="合同编号已存在，请修改后重试") from exc

    saved_contract = await _load_contract_with_files(db_contract.id, db)
    return ContractResponse.model_validate(saved_contract)


@router.post("/ai-import/preview", response_model=ContractAiPreviewResponse)
async def preview_ai_contract_import(
    payload: ContractAiPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    await _load_ai_config(db)

    file_path, file_ext, file_url, _ = _resolve_contract_upload(payload.file_id)
    try:
        ai_result = await ai_service.parse_contract(file_path, file_ext)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 解析合同失败: {exc}") from exc

    parsed_data = ai_result.get("data") or {}
    confidence = ai_result.get("confidence")
    customer_name = _clean_text(parsed_data.get("customer_name"))
    matched_customer, matching_names = await _match_customer(customer_name, db)

    amount = _to_decimal(parsed_data.get("amount"))
    contract_draft = AiContractDraft(
        contract_no=_clean_text(parsed_data.get("contract_no")) or _generate_contract_no(),
        name=_clean_text(parsed_data.get("contract_name")) or "AI 导入合同",
        customer_id=matched_customer.id if matched_customer else None,
        customer_name=customer_name,
        amount=amount,
        start_date=_to_date(parsed_data.get("start_date") or parsed_data.get("sign_date")),
        end_date=_to_date(parsed_data.get("end_date")),
        status="signed",
        payment_terms=_clean_text(parsed_data.get("payment_terms")),
        remark=_clean_text(parsed_data.get("remarks")),
        file_id=payload.file_id,
        file_url=file_url,
        ai_parsed=True,
        parse_confidence=confidence,
    )
    receivables = _build_receivable_plan(contract_draft.payment_terms, amount)

    return ContractAiPreviewResponse(
        contract=contract_draft,
        receivables=receivables,
        raw_ai_result=ai_result,
        matching_customer_names=matching_names,
    )


@router.post("/ai-import/confirm")
async def confirm_ai_contract_import(
    payload: ContractAiConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    contract_data = payload.contract
    customer = await _get_or_create_customer(contract_data.customer_id, contract_data.customer_name, db)

    if not _clean_text(contract_data.contract_no):
        raise HTTPException(status_code=400, detail="合同编号不能为空")
    if not _clean_text(contract_data.name):
        raise HTTPException(status_code=400, detail="合同名称不能为空")

    contract_payload = ContractCreate(
        contract_no=contract_data.contract_no.strip(),
        name=contract_data.name.strip(),
        customer_id=customer.id,
        amount=_to_decimal(contract_data.amount),
        start_date=_to_date(contract_data.start_date),
        end_date=_to_date(contract_data.end_date),
        status=contract_data.status or "signed",
        payment_terms=_clean_text(contract_data.payment_terms),
        remark=_clean_text(contract_data.remark),
        file_id=contract_data.file_id,
        file_url=contract_data.file_url,
        ai_parsed=bool(contract_data.ai_parsed),
        parsed_at=datetime.now() if contract_data.ai_parsed else None,
        parse_confidence=contract_data.parse_confidence,
    )
    contract_start_date = _to_date(contract_data.start_date)

    db_contract = Contract(**contract_payload.model_dump(exclude={"file_id", "file_url"}))
    db.add(db_contract)

    try:
        await db.flush()
        if contract_data.file_id:
            await _ensure_contract_file(
                db=db,
                contract_id=db_contract.id,
                uploaded_file_id=contract_data.file_id,
                preferred_name=contract_data.name,
                source="ai_import",
                is_primary=True,
            )

        receivable_payloads = payload.receivables or _build_receivable_plan(contract_payload.payment_terms, contract_payload.amount)
        created_receivables: List[Receivable] = []
        for receivable in receivable_payloads:
            amount = _to_decimal(receivable.amount)
            if amount <= 0:
                continue
            db_receivable = Receivable(
                contract_id=db_contract.id,
                amount=amount,
                due_date=_resolve_receivable_due_date(receivable.due_date, contract_start_date),
                status="unpaid",
                remark=_clean_text(receivable.remark),
            )
            db.add(db_receivable)
            created_receivables.append(db_receivable)

        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="合同编号已存在，请修改后重试") from exc

    saved_contract = await _load_contract_with_files(db_contract.id, db)
    return {
        "contract": ContractResponse.model_validate(saved_contract),
        "receivables": [
            {
                "id": receivable.id,
                "amount": str(receivable.amount),
                "due_date": receivable.due_date.isoformat() if receivable.due_date else None,
                "status": receivable.status,
                "remark": receivable.remark,
            }
            for receivable in created_receivables
        ],
    }


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(contract_id: str, contract: ContractUpdate, db: AsyncSession = Depends(get_db)):
    db_contract = await _load_contract_with_files(contract_id, db)

    update_data = contract.model_dump(exclude_unset=True)
    if "customer_id" in update_data and update_data["customer_id"]:
        customer_result = await db.execute(select(Customer).where(Customer.id == update_data["customer_id"]))
        if not customer_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="客户不存在")

    for field, value in update_data.items():
        setattr(db_contract, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="合同更新失败，请检查合同编号是否重复") from exc

    saved_contract = await _load_contract_with_files(contract_id, db)
    return ContractResponse.model_validate(saved_contract)


@router.post("/batch-delete")
async def batch_delete_contracts(
    ids: List[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """批量删除合同"""
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的合同")

    deleted_count = 0
    for contract_id in ids:
        # 删除相关记录
        await db.execute(
            text("DELETE FROM payment_records WHERE receivable_id IN (SELECT id FROM receivables WHERE contract_id = :cid)"),
            {"cid": contract_id},
        )
        await db.execute(text("DELETE FROM receivables WHERE contract_id = :cid"), {"cid": contract_id})
        await db.execute(
            text("DELETE FROM incomes WHERE invoice_id IN (SELECT id FROM invoices WHERE contract_id = :cid)"),
            {"cid": contract_id},
        )
        await db.execute(text("DELETE FROM expenses WHERE contract_id = :cid"), {"cid": contract_id})
        await db.execute(text("DELETE FROM invoices WHERE contract_id = :cid"), {"cid": contract_id})
        await db.execute(text("DELETE FROM projects WHERE contract_id = :cid"), {"cid": contract_id})
        await db.execute(text("DELETE FROM contract_files WHERE contract_id = :cid"), {"cid": contract_id})
        await db.execute(text("DELETE FROM contracts WHERE id = :cid"), {"cid": contract_id})
        deleted_count += 1

    await db.commit()
    return {"message": "批量删除成功", "deleted_count": deleted_count}


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("DELETE FROM payment_records WHERE receivable_id IN (SELECT id FROM receivables WHERE contract_id = :cid)"),
        {"cid": contract_id},
    )
    await db.execute(text("DELETE FROM receivables WHERE contract_id = :cid"), {"cid": contract_id})
    await db.execute(
        text("DELETE FROM incomes WHERE invoice_id IN (SELECT id FROM invoices WHERE contract_id = :cid)"),
        {"cid": contract_id},
    )
    await db.execute(text("DELETE FROM expenses WHERE contract_id = :cid"), {"cid": contract_id})
    await db.execute(text("DELETE FROM invoices WHERE contract_id = :cid"), {"cid": contract_id})
    await db.execute(text("DELETE FROM projects WHERE contract_id = :cid"), {"cid": contract_id})
    await db.execute(text("DELETE FROM contract_files WHERE contract_id = :cid"), {"cid": contract_id})
    await db.execute(text("DELETE FROM contracts WHERE id = :cid"), {"cid": contract_id})
    await db.commit()
    return {"message": "删除成功"}


@router.post("/{contract_id}/files")
async def upload_contract_file(
    contract_id: str,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: AsyncSession = Depends(get_db),
):
    contract_result = await db.execute(select(Contract).where(Contract.id == contract_id))
    db_contract = contract_result.scalar_one_or_none()
    if not db_contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    upload_dir = os.path.join(settings.UPLOAD_DIR, "contracts")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower()
    normalized_ext = ext.lstrip(".")
    if normalized_ext not in SUPPORTED_CONTRACT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的合同文件类型")

    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    filepath = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(filepath, "wb") as output:
        output.write(content)

    existing_count = (
        await db.execute(select(func.count()).select_from(ContractFile).where(ContractFile.contract_id == contract_id))
    ).scalar_one()
    should_be_primary = bool(is_primary or existing_count == 0)

    contract_file = await _ensure_contract_file(
        db=db,
        contract_id=contract_id,
        uploaded_file_id=file_id,
        preferred_name=file.filename,
        source="manual",
        is_primary=should_be_primary,
    )
    await db.commit()
    await db.refresh(contract_file)

    return {
        "id": contract_file.id,
        "file_id": contract_file.file_id,
        "file_name": contract_file.file_name,
        "file_url": contract_file.file_url,
        "file_type": contract_file.file_type,
        "file_size": contract_file.file_size,
        "source": contract_file.source,
        "is_primary": contract_file.is_primary,
        "sort_order": contract_file.sort_order,
    }


@router.get("/{contract_id}/files")
async def get_contract_files(contract_id: str, db: AsyncSession = Depends(get_db)):
    contract_result = await db.execute(select(Contract.id).where(Contract.id == contract_id))
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="合同不存在")

    result = await db.execute(
        select(ContractFile)
        .where(ContractFile.contract_id == contract_id)
        .order_by(ContractFile.is_primary.desc(), ContractFile.sort_order.asc(), ContractFile.created_at.desc())
    )
    files = result.scalars().all()

    return {
        "total": len(files),
        "items": [
            {
                "id": item.id,
                "file_id": item.file_id,
                "file_name": item.file_name,
                "file_path": item.file_path,
                "file_url": item.file_url,
                "file_type": item.file_type,
                "file_size": item.file_size,
                "source": item.source,
                "is_primary": item.is_primary,
                "sort_order": item.sort_order,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in files
        ],
    }


@router.delete("/{contract_id}/files/{file_id}")
async def delete_contract_file(contract_id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    contract_result = await db.execute(select(Contract.id).where(Contract.id == contract_id))
    if not contract_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="合同不存在")

    result = await db.execute(select(ContractFile).where(ContractFile.id == file_id))
    contract_file = result.scalar_one_or_none()
    if not contract_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    if contract_file.contract_id != contract_id:
        raise HTTPException(status_code=400, detail="文件不属于该合同")

    was_primary = contract_file.is_primary
    await db.delete(contract_file)
    await db.flush()

    if was_primary:
        await _promote_next_primary_file(db=db, contract_id=contract_id)

    await db.commit()
    return {"message": "删除成功"}
