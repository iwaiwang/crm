"""报销管理 AI 录入"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.ai_config import AIConfig
from app.models.invoice import Invoice
from app.models.reimbursement import Reimbursement
from app.models.reimbursement_file import ReimbursementFile
from app.models.setting import Setting
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.reimbursement import (
    AiReimbursementDraft,
    AiReimbursementPreviewRequest,
    AiReimbursementPreviewResponse,
    AiReimbursementConfirmRequest,
)
from app.schemas.setting import SettingKeys
from app.api.auth import require_menu_permission
from app.services import ai_service
from app.config import settings
from app.utils.helpers import clean_text, to_decimal, to_date, recommend_expense_category

router = APIRouter()


def _resolve_upload_file(file_id: str) -> tuple:
    """解析上传文件路径"""
    upload_dir = settings.UPLOAD_DIR
    invoices_dir = os.path.join(upload_dir, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    for ext in ["pdf", "jpg", "jpeg", "png", "doc", "docx"]:
        potential_path = os.path.join(invoices_dir, f"{file_id}.{ext}")
        if os.path.exists(potential_path):
            file_url = f"/uploads/invoices/{file_id}.{ext}"
            return potential_path, ext, file_url

    for ext in ["pdf", "jpg", "jpeg", "png", "doc", "docx"]:
        potential_path = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(potential_path):
            file_url = f"/uploads/{file_id}.{ext}"
            return potential_path, ext, file_url

    raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")


async def _load_ai_config(db: AsyncSession) -> None:
    """加载 AI 配置"""
    result = await db.execute(select(AIConfig).limit(1))
    db_config = result.scalar_one_or_none()
    if not db_config or not db_config.enabled:
        raise HTTPException(status_code=503, detail="AI 服务未配置或未启用")

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


async def _get_setting_value(db: AsyncSession, key: str) -> Optional[str]:
    result = await db.execute(select(Setting.value).where(Setting.key == key))
    value = result.scalar_one_or_none()
    return value.strip() if isinstance(value, str) else value


@router.post("/ai-import/preview", response_model=AiReimbursementPreviewResponse)
async def preview_ai_reimbursement_import(
    payload: AiReimbursementPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """AI 预览报销单录入"""
    await _load_ai_config(db)

    file_path, file_ext, file_url = _resolve_upload_file(payload.file_id)

    try:
        ai_result = await ai_service.parse_invoice(file_path, file_ext)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 解析发票失败: {exc}") from exc

    parsed_data = ai_result.get("data") or {}

    invoice_no = clean_text(parsed_data.get("invoice_no") or parsed_data.get("invoice_number"))
    amount = to_decimal(parsed_data.get("amount"))
    total_amount = to_decimal(parsed_data.get("total_amount") or parsed_data.get("amount"))
    tax_amount = to_decimal(parsed_data.get("tax_amount"), "0")

    if total_amount <= 0 and amount > 0:
        total_amount = amount + tax_amount

    reimbursement_draft = AiReimbursementDraft(
        invoice_no=invoice_no,
        invoice_code=clean_text(parsed_data.get("invoice_code")),
        invoice_number=clean_text(parsed_data.get("invoice_number")),
        supplier_name=clean_text(parsed_data.get("seller_name")),
        supplier_tax_id=clean_text(parsed_data.get("seller_tax_id")),
        supplier_bank_name=None,
        supplier_bank_account=None,
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        expense_category=recommend_expense_category(
            clean_text(parsed_data.get("seller_name")),
            clean_text(parsed_data.get("remarks"))
        ),
        issue_date=to_date(parsed_data.get("invoice_date") or parsed_data.get("issue_date")),
        remark=clean_text(parsed_data.get("remarks")),
        file_id=payload.file_id,
        file_url=file_url,
        ai_parsed=True,
        parse_confidence=ai_result.get("confidence"),
    )

    suggested_actions = ["将创建 1 张报销单"]
    if reimbursement_draft.supplier_name:
        suggested_actions.append("可在确认后同时创建收款方")

    return AiReimbursementPreviewResponse(
        reimbursement=reimbursement_draft,
        suggested_actions=suggested_actions,
        raw_ai_result=ai_result,
    )


@router.post("/ai-import/confirm")
async def confirm_ai_reimbursement_import(
    payload: AiReimbursementConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission("reimbursements")),
):
    """AI 确认报销单录入"""
    reimbursement_data = payload.reimbursement

    if not clean_text(reimbursement_data.supplier_name):
        raise HTTPException(status_code=400, detail="供应商/收款方名称不能为空")

    # 创建收款方（如果勾选）
    if payload.create_supplier and reimbursement_data.supplier_name:
        existing_result = await db.execute(
            select(Supplier).where(Supplier.name == reimbursement_data.supplier_name)
        )
        if not existing_result.scalar_one_or_none():
            new_supplier = Supplier(
                name=reimbursement_data.supplier_name,
                tax_id=reimbursement_data.supplier_tax_id,
                bank_name=reimbursement_data.supplier_bank_name,
                bank_branch=reimbursement_data.supplier_bank_branch,
                bank_province=reimbursement_data.supplier_bank_province,
                bank_account=reimbursement_data.supplier_bank_account,
                bank_code=reimbursement_data.supplier_bank_code,
                remark="AI录入报销单自动创建",
            )
            db.add(new_supplier)

    # 创建或复用进项发票记录
    invoice_no = reimbursement_data.invoice_no
    if not invoice_no and reimbursement_data.invoice_code and reimbursement_data.invoice_number:
        invoice_no = f"{reimbursement_data.invoice_code}-{reimbursement_data.invoice_number}"

    db_invoice = None
    invoice_reused = False
    if invoice_no:
        existing_inv = await db.execute(
            select(Invoice).where(Invoice.invoice_no == invoice_no)
        )
        db_invoice = existing_inv.scalar_one_or_none()
        if db_invoice:
            invoice_reused = True
            if reimbursement_data.file_id:
                db_invoice.file_id = reimbursement_data.file_id
                db_invoice.file_url = reimbursement_data.file_url
            if reimbursement_data.remark:
                db_invoice.remark = reimbursement_data.remark

    if not db_invoice:
        company_name = await _get_setting_value(db, SettingKeys.COMPANY_NAME)
        company_tax_id = await _get_setting_value(db, SettingKeys.COMPANY_TAX_ID)
        db_invoice = Invoice(
            invoice_code=reimbursement_data.invoice_code,
            invoice_number=reimbursement_data.invoice_number,
            invoice_no=invoice_no,
            invoice_date=reimbursement_data.issue_date,
            issue_date=reimbursement_data.issue_date,
            amount=reimbursement_data.amount,
            tax_amount=reimbursement_data.tax_amount,
            total_amount=reimbursement_data.total_amount,
            invoice_type="purchase",
            buyer_name=company_name,
            buyer_tax_id=company_tax_id,
            seller_name=reimbursement_data.supplier_name,
            seller_tax_id=reimbursement_data.supplier_tax_id,
            status="normal",
            file_id=reimbursement_data.file_id,
            file_url=reimbursement_data.file_url,
            ai_parsed=True,
            parse_confidence=reimbursement_data.parse_confidence,
            remark=reimbursement_data.remark,
        )
        db.add(db_invoice)
        await db.flush()

    db_reimbursement = Reimbursement(
        invoice_id=db_invoice.id,
        supplier_name=reimbursement_data.supplier_name,
        supplier_tax_id=reimbursement_data.supplier_tax_id,
        supplier_bank_name=reimbursement_data.supplier_bank_name,
        supplier_bank_branch=reimbursement_data.supplier_bank_branch,
        supplier_bank_province=reimbursement_data.supplier_bank_province,
        supplier_bank_city=reimbursement_data.supplier_bank_city,
        supplier_bank_code=reimbursement_data.supplier_bank_code,
        supplier_bank_account=reimbursement_data.supplier_bank_account,
        amount=reimbursement_data.amount,
        tax_amount=reimbursement_data.tax_amount,
        total_amount=reimbursement_data.total_amount,
        expense_category=reimbursement_data.expense_category,
        payer_company=reimbursement_data.payer_company,
        remark=reimbursement_data.remark,
        file_id=reimbursement_data.file_id,
        file_url=reimbursement_data.file_url,
        source_type="invoice",
        status="draft",
        created_by=current_user.id,
    )
    db.add(db_reimbursement)
    await db.flush()

    # 附件：主发票文件 + 额外附件
    order = 0
    seen = set()
    if db_reimbursement.file_id:
        db.add(ReimbursementFile(
            reimbursement_id=db_reimbursement.id,
            file_id=db_reimbursement.file_id,
            file_url=db_reimbursement.file_url,
            file_name=None,
            file_type=None,
            file_size=None,
            sort_order=order,
        ))
        seen.add(db_reimbursement.file_id)
        order += 1
    for f in (payload.files or []):
        if f.file_id and f.file_id not in seen:
            db.add(ReimbursementFile(
                reimbursement_id=db_reimbursement.id,
                file_id=f.file_id,
                file_name=f.file_name,
                file_url=f.file_url,
                file_type=f.file_type,
                file_size=f.file_size,
                sort_order=order,
            ))
            seen.add(f.file_id)
            order += 1

    await db.commit()
    await db.refresh(db_reimbursement)
    await db.refresh(db_invoice)

    return {
        "message": "AI录入报销单成功",
        "reimbursement_id": db_reimbursement.id,
        "invoice_id": db_invoice.id,
        "supplier_created": payload.create_supplier,
        "invoice_reused": invoice_reused,
    }
