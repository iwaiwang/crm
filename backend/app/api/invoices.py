"""发票管理 API"""
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.database import get_db
from app.models.ai_config import AIConfig
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.income import Income
from app.models.invoice import Invoice
from app.models.receivable import Receivable, PaymentRecord, invoice_payment_record
from app.models.setting import Setting
from app.models.user import User
from app.schemas.invoice import (
    AiInvoiceContractMatch,
    AiInvoiceDraft,
    AiInvoiceExpenseDraft,
    AiInvoiceIncomeDraft,
    AiInvoicePaymentDraft,
    AiInvoiceReceivableMatch,
    InvoiceAiConfirmRequest,
    InvoiceAiPreviewRequest,
    InvoiceAiPreviewResponse,
    InvoiceCreate,
    InvoiceDirectionType,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceType,
    InvoiceUpdate,
)
from app.schemas.receivable import PaymentRecordCreate, PaymentRecordResponse, ReceivableResponse, ReceivableListResponse
from app.api.auth import require_menu_permission
from app.schemas.setting import SettingKeys
from app.services.ai_parser import ai_service

router = APIRouter()
SUPPORTED_INVOICE_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
PAYMENT_METHOD_OPTIONS = {"bank_transfer", "check", "cash", "alipay", "wechat"}


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _to_decimal(value, default: str = "0") -> Decimal:
    if value in (None, ""):
        return Decimal(default)
    cleaned = str(value).replace(",", "").replace("¥", "").replace("楼", "").replace("%", "").strip()
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


def _normalize_party_name(value: Optional[str]) -> str:
    normalized = _clean_text(value) or ""
    for token in ["（", "）", "(", ")", "有限责任公司", "有限公司", "股份有限公司", "公司", " ", "\u3000"]:
        normalized = normalized.replace(token, "")
    return normalized.lower()


def _normalize_tax_rate(value) -> Decimal:
    rate = _to_decimal(value)
    if rate > 1:
        rate = (rate / Decimal("100")).quantize(Decimal("0.0001"))
    return rate


def _normalize_invoice_kind(value: Optional[str]) -> InvoiceType:
    text = (_clean_text(value) or "").lower()
    if "special" in text or "专" in text:
        return InvoiceType.SPECIAL
    return InvoiceType.NORMAL


def _recommend_expense_category(*texts: Optional[str]) -> str:
    combined = " ".join(filter(None, [_clean_text(item) for item in texts])).lower()
    rules = {
        "software": ["云", "软件", "订阅", "license", "saas", "系统", "平台", "技术服务"],
        "procurement": ["采购", "设备", "材料", "耗材", "货物", "器材"],
        "travel": ["机票", "酒店", "差旅", "出行", "车票"],
        "logistics": ["物流", "快递", "运费", "货运", "运输"],
        "marketing": ["推广", "广告", "宣传", "投放"],
        "office": ["办公", "文具", "打印", "耗材"],
        "maintenance": ["维护", "维修", "保养"],
        "training": ["培训", "课程"],
        "rent": ["房租", "租赁", "租金"],
        "utilities": ["水费", "电费", "燃气", "物业"],
        "entertainment": ["招待", "宴请", "餐饮", "接待"],
    }
    for category, keywords in rules.items():
        if any(keyword in combined for keyword in keywords):
            return category
    return "other"


async def _load_ai_config(db: AsyncSession) -> None:
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


async def _load_company_info(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Setting).where(Setting.key.in_([SettingKeys.COMPANY_NAME, SettingKeys.COMPANY_TAX_ID]))
    )
    company_info = {setting.key: setting.value for setting in result.scalars().all()}
    return {
        "company_name": _clean_text(company_info.get(SettingKeys.COMPANY_NAME)),
        "company_tax_id": _clean_text(company_info.get(SettingKeys.COMPANY_TAX_ID)),
    }


def _resolve_invoice_upload(file_id: str) -> tuple[str, str, str, str]:
    upload_dir = os.path.join("uploads", "invoices")
    for ext in SUPPORTED_INVOICE_EXTENSIONS:
        filename = f"{file_id}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        if os.path.exists(filepath):
            return filepath, ext, f"/uploads/invoices/{filename}", filename
    raise HTTPException(status_code=404, detail="发票文件不存在")


def _infer_invoice_direction(
    *,
    buyer_name: Optional[str],
    buyer_tax_id: Optional[str],
    seller_name: Optional[str],
    seller_tax_id: Optional[str],
    company_name: Optional[str],
    company_tax_id: Optional[str],
) -> InvoiceDirectionType:
    normalized_company_name = _normalize_party_name(company_name)
    normalized_buyer = _normalize_party_name(buyer_name)
    normalized_seller = _normalize_party_name(seller_name)
    cleaned_company_tax_id = _clean_text(company_tax_id)
    cleaned_buyer_tax_id = _clean_text(buyer_tax_id)
    cleaned_seller_tax_id = _clean_text(seller_tax_id)

    if cleaned_company_tax_id and cleaned_seller_tax_id and cleaned_company_tax_id == cleaned_seller_tax_id:
        return InvoiceDirectionType.SALES
    if cleaned_company_tax_id and cleaned_buyer_tax_id and cleaned_company_tax_id == cleaned_buyer_tax_id:
        return InvoiceDirectionType.PURCHASE
    if normalized_company_name and normalized_seller and normalized_company_name == normalized_seller:
        return InvoiceDirectionType.SALES
    if normalized_company_name and normalized_buyer and normalized_company_name == normalized_buyer:
        return InvoiceDirectionType.PURCHASE
    return InvoiceDirectionType.SALES


async def _match_contracts_for_invoice(*, invoice: AiInvoiceDraft, db: AsyncSession) -> List[AiInvoiceContractMatch]:
    if invoice.invoice_type != InvoiceDirectionType.SALES:
        return []

    target_customer_name = _clean_text(invoice.buyer_name)
    if not target_customer_name:
        return []

    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.customer), selectinload(Contract.receivables))
        .order_by(Contract.created_at.desc())
    )
    contracts = result.scalars().all()
    normalized_target = _normalize_party_name(target_customer_name)
    total_amount = _to_decimal(invoice.total_amount or invoice.amount)
    matches: List[AiInvoiceContractMatch] = []

    for contract in contracts:
        customer_name = contract.customer.name if contract.customer else None
        if not customer_name:
            continue

        score = 0.0
        reasons: List[str] = []
        normalized_customer = _normalize_party_name(customer_name)
        if normalized_customer and normalized_customer == normalized_target:
            score += 70
            reasons.append("客户名称精确匹配")
        elif normalized_customer and (normalized_customer in normalized_target or normalized_target in normalized_customer):
            score += 45
            reasons.append("客户名称近似匹配")
        else:
            continue

        if total_amount > 0:
            contract_amount = _to_decimal(contract.amount)
            amount_diff = abs(contract_amount - total_amount)
            if amount_diff == 0:
                score += 20
                reasons.append("合同金额一致")
            elif contract_amount > 0:
                ratio = amount_diff / contract_amount
                if ratio <= Decimal("0.1"):
                    score += 15
                    reasons.append("合同金额接近")
                elif ratio <= Decimal("0.3"):
                    score += 8
                    reasons.append("合同金额较接近")

            unpaid_candidates = []
            for receivable in contract.receivables:
                unpaid_amount = _to_decimal(receivable.amount) - _to_decimal(receivable.received_amount)
                if unpaid_amount > 0:
                    unpaid_candidates.append(unpaid_amount)
            if unpaid_candidates:
                nearest_unpaid = min(unpaid_candidates, key=lambda item: abs(item - total_amount))
                diff = abs(nearest_unpaid - total_amount)
                if diff == 0:
                    score += 15
                    reasons.append("存在金额一致的未收应收")
                elif total_amount > 0 and diff / total_amount <= Decimal("0.15"):
                    score += 10
                    reasons.append("存在金额接近的未收应收")

        matches.append(
            AiInvoiceContractMatch(
                contract_id=contract.id,
                contract_no=contract.contract_no,
                contract_name=contract.name,
                customer_id=contract.customer_id,
                customer_name=customer_name,
                amount=_to_decimal(contract.amount),
                score=round(score, 2),
                reason="，".join(reasons) if reasons else None,
            )
        )

    return sorted(matches, key=lambda item: item.score, reverse=True)[:5]


def _build_receivable_match(receivable: Receivable, invoice_total: Decimal) -> AiInvoiceReceivableMatch:
    amount = _to_decimal(receivable.amount)
    received_amount = _to_decimal(receivable.received_amount)
    unpaid_amount = amount - received_amount
    score = 0.0
    reasons: List[str] = []

    if unpaid_amount > 0:
        diff = abs(unpaid_amount - invoice_total)
        if diff == 0:
            score += 50
            reasons.append("未收金额一致")
        elif invoice_total > 0 and diff / invoice_total <= Decimal("0.15"):
            score += 35
            reasons.append("未收金额接近")
        elif invoice_total > 0 and diff / invoice_total <= Decimal("0.3"):
            score += 20
            reasons.append("未收金额较接近")
    if receivable.status in {"unpaid", "partial"}:
        score += 20
        reasons.append("应收未结清")
    if receivable.due_date:
        day_gap = abs((receivable.due_date - date.today()).days)
        if day_gap <= 30:
            score += 10
            reasons.append("应收日期接近")

    return AiInvoiceReceivableMatch(
        receivable_id=receivable.id,
        contract_id=receivable.contract_id,
        due_date=receivable.due_date,
        amount=amount,
        received_amount=received_amount,
        unpaid_amount=unpaid_amount if unpaid_amount > 0 else Decimal("0"),
        status=receivable.status,
        remark=_clean_text(receivable.remark),
        score=round(score, 2),
        reason="，".join(reasons) if reasons else None,
    )


async def _match_receivables_for_invoice(
    *,
    contract_id: Optional[str],
    invoice_total: Decimal,
    db: AsyncSession,
) -> List[AiInvoiceReceivableMatch]:
    if not contract_id:
        return []
    result = await db.execute(
        select(Receivable)
        .where(Receivable.contract_id == contract_id)
        .order_by(Receivable.due_date.asc(), Receivable.created_at.asc())
    )
    receivables = result.scalars().all()
    matches = [
        _build_receivable_match(receivable, invoice_total)
        for receivable in receivables
        if (_to_decimal(receivable.amount) - _to_decimal(receivable.received_amount)) > 0
    ]
    return sorted(matches, key=lambda item: item.score, reverse=True)[:5]


def _build_invoice_remark(invoice_no: Optional[str], prefix: str) -> str:
    if invoice_no:
        return f"{prefix}，发票号：{invoice_no}"
    return prefix


# 注意：check-duplicate 必须放在 /{invoice_id} 之前，否则会被当作 invoice_id 匹配
# 使用 /actions/check-duplicate 避免与 /{invoice_id} 冲突
@router.get("/actions/check-duplicate")
async def check_invoice_duplicate(
    invoice_no: str = Query(...),
    exclude_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """检查发票号码是否重复"""
    query = select(Invoice).where(Invoice.invoice_no == invoice_no)
    if exclude_id:
        query = query.where(Invoice.id != exclude_id)

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return {"duplicate": True, "message": f"发票号码 {invoice_no} 已存在"}
    return {"duplicate": False}


@router.get("", response_model=InvoiceListResponse)
async def get_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    contract_id: Optional[str] = None,
    invoice_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """获取发票列表"""
    from sqlalchemy import select, func
    import traceback

    print(f"[DEBUG] get_invoices 收到参数：page={page}, page_size={page_size}, search={search}, status={status}, invoice_type={invoice_type}")
    try:
        # 构建基础查询
        query = select(Invoice)

        if search:
            query = query.where(Invoice.invoice_no.contains(search))
        if status:
            query = query.where(Invoice.status == status)
        if contract_id:
            query = query.where(Invoice.contract_id == contract_id)
        if invoice_type and invoice_type != 'all':
            query = query.where(Invoice.invoice_type == invoice_type)

        # 获取总数
        count_query = select(func.count()).select_from(Invoice)
        if search:
            count_query = count_query.where(Invoice.invoice_no.contains(search))
        if status:
            count_query = count_query.where(Invoice.status == status)
        if contract_id:
            count_query = count_query.where(Invoice.contract_id == contract_id)
        if invoice_type and invoice_type != 'all':
            count_query = count_query.where(Invoice.invoice_type == invoice_type)

        print(f"[DEBUG] 执行 count_query...")
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        print(f"[DEBUG] total={total}")

        # 获取分页数据
        query = query.order_by(Invoice.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        print(f"[DEBUG] 执行查询 invoices...")
        result = await db.execute(query)
        invoices = result.scalars().all()
        print(f"[DEBUG] 查询到 {len(invoices)} 条记录")

        return InvoiceListResponse(
            total=total,
            items=[InvoiceResponse.model_validate(i) for i in invoices]
        )
    except Exception as e:
        print(f"[ERROR] get_invoices 异常：{type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.post("/ai-import/preview", response_model=InvoiceAiPreviewResponse)
async def preview_ai_invoice_import(
    payload: InvoiceAiPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    del current_user
    await _load_ai_config(db)
    company_info = await _load_company_info(db)

    file_path, file_ext, file_url, _ = _resolve_invoice_upload(payload.file_id)
    try:
        ai_result = await ai_service.parse_invoice(file_path, file_ext)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 解析发票失败: {exc}") from exc

    parsed_data = ai_result.get("data") or {}
    invoice_no = _clean_text(parsed_data.get("invoice_no") or parsed_data.get("invoice_number"))
    issue_date = _to_date(parsed_data.get("issue_date") or parsed_data.get("invoice_date"))
    amount = _to_decimal(parsed_data.get("amount"))
    total_amount = _to_decimal(parsed_data.get("total_amount") or parsed_data.get("amount"))
    tax_amount = _to_decimal(parsed_data.get("tax_amount"), "0")
    if total_amount <= 0 and amount > 0:
        total_amount = amount + tax_amount

    invoice_draft = AiInvoiceDraft(
        invoice_code=_clean_text(parsed_data.get("invoice_code")),
        invoice_number=_clean_text(parsed_data.get("invoice_number")),
        check_code=_clean_text(parsed_data.get("check_code")),
        invoice_date=_to_date(parsed_data.get("invoice_date")),
        invoice_no=invoice_no,
        amount=amount,
        tax_rate=_normalize_tax_rate(parsed_data.get("tax_rate")),
        tax_amount=tax_amount,
        total_amount=total_amount,
        type=_normalize_invoice_kind(parsed_data.get("invoice_type")),
        buyer_name=_clean_text(parsed_data.get("buyer_name")),
        buyer_tax_id=_clean_text(parsed_data.get("buyer_tax_id")),
        seller_name=_clean_text(parsed_data.get("seller_name")),
        seller_tax_id=_clean_text(parsed_data.get("seller_tax_id")),
        issue_date=issue_date,
        due_date=issue_date,
        status="normal",
        remark=_clean_text(parsed_data.get("remarks")),
        file_id=payload.file_id,
        file_url=file_url,
        ai_parsed=True,
        parse_confidence=ai_result.get("confidence"),
    )
    invoice_draft.invoice_type = _infer_invoice_direction(
        buyer_name=invoice_draft.buyer_name,
        buyer_tax_id=invoice_draft.buyer_tax_id,
        seller_name=invoice_draft.seller_name,
        seller_tax_id=invoice_draft.seller_tax_id,
        company_name=company_info.get("company_name"),
        company_tax_id=company_info.get("company_tax_id"),
    )

    contract_matches = await _match_contracts_for_invoice(invoice=invoice_draft, db=db)
    if contract_matches:
        invoice_draft.contract_id = contract_matches[0].contract_id

    receivable_matches = await _match_receivables_for_invoice(
        contract_id=invoice_draft.contract_id,
        invoice_total=_to_decimal(invoice_draft.total_amount or invoice_draft.amount),
        db=db,
    )

    recommended_payment = None
    recommended_income = None
    recommended_expense = None
    suggested_actions = ["将创建 1 张发票"]

    if invoice_draft.invoice_type == InvoiceDirectionType.SALES:
        payment_amount = (
            receivable_matches[0].unpaid_amount
            if receivable_matches and receivable_matches[0].unpaid_amount > 0
            else _to_decimal(invoice_draft.total_amount or invoice_draft.amount)
        )
        recommended_payment = AiInvoicePaymentDraft(
            receivable_id=receivable_matches[0].receivable_id if receivable_matches else None,
            amount=payment_amount,
            payment_date=invoice_draft.issue_date or date.today(),
            payment_method="bank_transfer",
            remark=_build_invoice_remark(invoice_draft.invoice_no, "AI录入销项发票同步登记收款"),
        )
        recommended_income = AiInvoiceIncomeDraft(
            amount=payment_amount if payment_amount > 0 else _to_decimal(invoice_draft.total_amount or invoice_draft.amount),
            income_date=invoice_draft.issue_date or date.today(),
            income_category="sales",
            payment_method="bank_transfer",
            remark=_build_invoice_remark(invoice_draft.invoice_no, "AI录入销项发票自动创建收入"),
        )
        suggested_actions.append("将创建 1 条收入")
        if recommended_payment.receivable_id:
            suggested_actions.append("可同步登记 1 条收款并更新应收状态")
    else:
        supplier_name = invoice_draft.seller_name
        supplier_id = None
        if supplier_name:
            customer_result = await db.execute(select(Customer).where(Customer.name == supplier_name).limit(1))
            supplier = customer_result.scalar_one_or_none()
            supplier_id = supplier.id if supplier else None
        recommended_expense = AiInvoiceExpenseDraft(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            contract_id=None,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=_to_decimal(invoice_draft.total_amount or invoice_draft.amount),
            expense_date=invoice_draft.issue_date or date.today(),
            expense_category=_recommend_expense_category(invoice_draft.seller_name, invoice_draft.remark),
            payment_method="bank_transfer",
            remark=_build_invoice_remark(invoice_draft.invoice_no, "AI录入进项发票自动创建支出"),
        )
        suggested_actions.append("将创建 1 条支出")

    return InvoiceAiPreviewResponse(
        invoice=invoice_draft,
        matching_contracts=contract_matches,
        matching_receivables=receivable_matches,
        payment=recommended_payment,
        income=recommended_income,
        expense=recommended_expense,
        suggested_actions=suggested_actions,
        raw_ai_result=ai_result,
    )


@router.post("/ai-import/confirm")
async def confirm_ai_invoice_import(
    payload: InvoiceAiConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    del current_user
    invoice_data = payload.invoice

    if not _clean_text(invoice_data.invoice_no):
        raise HTTPException(status_code=400, detail="发票号码不能为空")

    duplicate_result = await db.execute(select(Invoice).where(Invoice.invoice_no == invoice_data.invoice_no))
    if duplicate_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"发票号码 {invoice_data.invoice_no} 已存在，请勿重复录入")

    if invoice_data.contract_id:
        contract_result = await db.execute(select(Contract).where(Contract.id == invoice_data.contract_id))
        if not contract_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="关联合同不存在")

    invoice_payload = InvoiceCreate(
        invoice_code=_clean_text(invoice_data.invoice_code),
        invoice_number=_clean_text(invoice_data.invoice_number),
        check_code=_clean_text(invoice_data.check_code),
        invoice_date=_to_date(invoice_data.invoice_date),
        invoice_no=invoice_data.invoice_no.strip(),
        contract_id=invoice_data.contract_id,
        amount=_to_decimal(invoice_data.amount),
        tax_rate=_normalize_tax_rate(invoice_data.tax_rate),
        tax_amount=_to_decimal(invoice_data.tax_amount, "0"),
        total_amount=_to_decimal(invoice_data.total_amount or invoice_data.amount),
        type=invoice_data.type or InvoiceType.NORMAL,
        invoice_type=invoice_data.invoice_type or InvoiceDirectionType.SALES,
        buyer_name=_clean_text(invoice_data.buyer_name),
        buyer_tax_id=_clean_text(invoice_data.buyer_tax_id),
        seller_name=_clean_text(invoice_data.seller_name),
        seller_tax_id=_clean_text(invoice_data.seller_tax_id),
        issue_date=_to_date(invoice_data.issue_date),
        due_date=_to_date(invoice_data.due_date or invoice_data.issue_date),
        status=invoice_data.status or "normal",
        remark=_clean_text(invoice_data.remark),
        file_id=invoice_data.file_id,
        file_url=invoice_data.file_url,
        ai_parsed=bool(invoice_data.ai_parsed),
        parsed_at=datetime.now() if invoice_data.ai_parsed else None,
        parse_confidence=invoice_data.parse_confidence,
    )

    created_payment = None
    created_income = None
    created_expense = None
    db_invoice = Invoice(**invoice_payload.model_dump())
    db.add(db_invoice)

    try:
        await db.flush()

        if payload.create_payment:
            payment_data = payload.payment
            if not payment_data or not payment_data.receivable_id:
                raise HTTPException(status_code=400, detail="已勾选登记收款，请选择关联合同应收")
            receivable_result = await db.execute(select(Receivable).where(Receivable.id == payment_data.receivable_id))
            db_receivable = receivable_result.scalar_one_or_none()
            if not db_receivable:
                raise HTTPException(status_code=404, detail="关联应收不存在")

            payment_amount = _to_decimal(payment_data.amount)
            unpaid_amount = _to_decimal(db_receivable.amount) - _to_decimal(db_receivable.received_amount)
            if payment_amount <= 0:
                raise HTTPException(status_code=400, detail="收款金额必须大于 0")
            if unpaid_amount > 0 and payment_amount > unpaid_amount:
                payment_amount = unpaid_amount

            created_payment = PaymentRecord(
                receivable_id=db_receivable.id,
                amount=payment_amount,
                payment_date=_to_date(payment_data.payment_date) or date.today(),
                payment_method=payment_data.payment_method if payment_data.payment_method in PAYMENT_METHOD_OPTIONS else "bank_transfer",
                remark=_clean_text(payment_data.remark),
            )
            db.add(created_payment)
            await db.flush()
            created_payment.invoice.append(db_invoice)

            db_receivable.received_amount = _to_decimal(db_receivable.received_amount) + payment_amount
            if _to_decimal(db_receivable.received_amount) >= _to_decimal(db_receivable.amount):
                db_receivable.status = "paid"
            elif _to_decimal(db_receivable.received_amount) > 0:
                db_receivable.status = "partial"

        if payload.create_income and invoice_payload.invoice_type == InvoiceDirectionType.SALES:
            income_data = payload.income or AiInvoiceIncomeDraft()
            income_amount = _to_decimal(income_data.amount)
            if income_amount <= 0:
                income_amount = _to_decimal(created_payment.amount if created_payment else invoice_payload.total_amount)
            resolved_income_date = _to_date(income_data.income_date) or invoice_payload.issue_date or date.today()
            created_income = Income(
                source_type="invoice",
                source_id=db_invoice.id,
                invoice_id=db_invoice.id,
                payment_record_id=created_payment.id if created_payment else None,
                customer_id=None,
                customer_name=_clean_text(invoice_payload.buyer_name),
                amount=income_amount,
                income_date=resolved_income_date,
                income_year=str(resolved_income_date.year),
                income_category=income_data.income_category or "sales",
                payment_method=income_data.payment_method if income_data.payment_method in PAYMENT_METHOD_OPTIONS else (created_payment.payment_method if created_payment else None),
                remark=_clean_text(income_data.remark) or _build_invoice_remark(invoice_payload.invoice_no, "AI录入销项发票自动创建收入"),
                file_id=invoice_payload.file_id,
                file_url=invoice_payload.file_url,
            )
            db.add(created_income)

        if payload.create_expense and invoice_payload.invoice_type == InvoiceDirectionType.PURCHASE:
            expense_data = payload.expense or AiInvoiceExpenseDraft()
            resolved_expense_date = _to_date(expense_data.expense_date) or invoice_payload.issue_date or date.today()
            created_expense = Expense(
                supplier_id=expense_data.supplier_id,
                supplier_name=_clean_text(expense_data.supplier_name) or _clean_text(invoice_payload.seller_name),
                invoice_id=db_invoice.id,
                contract_id=expense_data.contract_id,
                amount=_to_decimal(expense_data.amount or invoice_payload.amount),
                tax_amount=_to_decimal(expense_data.tax_amount or invoice_payload.tax_amount, "0"),
                total_amount=_to_decimal(expense_data.total_amount or invoice_payload.total_amount),
                expense_date=resolved_expense_date,
                expense_year=str(resolved_expense_date.year),
                expense_category=expense_data.expense_category or "other",
                payment_method=expense_data.payment_method if expense_data.payment_method in PAYMENT_METHOD_OPTIONS else None,
                file_id=invoice_payload.file_id,
                file_url=invoice_payload.file_url,
                ai_parsed=bool(invoice_payload.ai_parsed),
                parsed_at=invoice_payload.parsed_at,
                parse_confidence=invoice_payload.parse_confidence,
                remark=_clean_text(expense_data.remark) or _build_invoice_remark(invoice_payload.invoice_no, "AI录入进项发票自动创建支出"),
            )
            db.add(created_expense)

        await db.commit()
        await db.refresh(db_invoice)
        if created_payment:
            await db.refresh(created_payment)
        if created_income:
            await db.refresh(created_income)
        if created_expense:
            await db.refresh(created_expense)
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="发票号已存在，请修改后重试") from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"确认录入失败: {exc}") from exc

    return {
        "invoice": InvoiceResponse.model_validate(db_invoice),
        "payment_record": (
            PaymentRecordResponse(
                id=created_payment.id,
                receivable_id=created_payment.receivable_id,
                amount=created_payment.amount,
                payment_date=created_payment.payment_date,
                payment_method=created_payment.payment_method,
                remark=created_payment.remark,
                created_at=created_payment.created_at,
                invoice_ids=[db_invoice.id],
            )
            if created_payment
            else None
        ),
        "income_id": created_income.id if created_income else None,
        "expense_id": created_expense.id if created_expense else None,
    }


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """获取发票详情"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    return InvoiceResponse.model_validate(invoice)


@router.post("", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """创建发票"""
    print(f"[DEBUG] create_invoice 收到数据：{invoice}")

    # 检查发票号码是否重复
    if invoice.invoice_no:
        result = await db.execute(select(Invoice).where(Invoice.invoice_no == invoice.invoice_no))
        existing = result.scalar()
        print(f"[DEBUG] 检查发票号码 {invoice.invoice_no} 是否重复，existing={existing}")
        if existing:
            raise HTTPException(status_code=400, detail=f"发票号码 {invoice.invoice_no} 已存在，请勿重复添加")

    # 只有当 contract_id 有值时才检查合同是否存在
    if invoice.contract_id:
        result = await db.execute(select(Contract).where(Contract.id == invoice.contract_id))
        if not result.scalar():
            raise HTTPException(status_code=400, detail="合同不存在")

    try:
        db_invoice = Invoice(**invoice.model_dump())
        print(f"[DEBUG] 创建发票对象：{db_invoice}")
        db.add(db_invoice)
        await db.commit()
        await db.refresh(db_invoice)
        print(f"[DEBUG] 发票创建成功：{db_invoice.id}")
    except IntegrityError as e:
        await db.rollback()
        print(f"[DEBUG] IntegrityError: {e}, orig={e.orig}")
        # 检查是否是唯一约束冲突
        if 'invoice_no' in str(e.orig) or 'UNIQUE constraint failed' in str(e):
            raise HTTPException(status_code=400, detail=f"发票号码已存在，请勿重复添加")
        raise HTTPException(status_code=400, detail=f"创建失败：{str(e)}")
    except Exception as e:
        await db.rollback()
        print(f"[DEBUG] 其他异常：{type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")

    return InvoiceResponse.model_validate(db_invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, invoice: InvoiceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """更新发票"""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查发票号码是否重复（排除自己）
    update_data = invoice.model_dump(exclude_unset=True)
    if 'invoice_no' in update_data and update_data['invoice_no']:
        duplicate_result = await db.execute(
            select(Invoice).where(
                Invoice.invoice_no == update_data['invoice_no'],
                Invoice.id != invoice_id
            )
        )
        if duplicate_result.scalar():
            raise HTTPException(status_code=400, detail=f"发票号码 {update_data['invoice_no']} 已存在，请勿重复添加")

    for field, value in update_data.items():
        setattr(db_invoice, field, value)

    await db.commit()
    await db.refresh(db_invoice)

    return InvoiceResponse.model_validate(db_invoice)


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('invoices'))):
    """删除发票"""
    from sqlalchemy import text

    # 先删除相关的 income/expense 记录（使用原始 SQL 避免 SQLAlchemy 级联问题）
    await db.execute(text("DELETE FROM incomes WHERE invoice_id = :iid"), {"iid": invoice_id})
    await db.execute(text("DELETE FROM expenses WHERE invoice_id = :iid"), {"iid": invoice_id})
    await db.commit()

    # 关闭 session 清除缓存对象
    await db.close()

    # 重新获取并删除发票
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    await db.delete(db_invoice)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/{invoice_id}/receivables", response_model=ReceivableListResponse)
async def get_invoice_receivables(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """获取发票可关联的应收款列表（用于收款登记）"""
    import traceback

    print(f"[DEBUG] get_invoice_receivables 开始，invoice_id={invoice_id}")
    try:
        # 先获取发票信息
        invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        db_invoice = invoice_result.scalar_one_or_none()
        print(f"[DEBUG] db_invoice={db_invoice}, contract_id={db_invoice.contract_id if db_invoice else None}")

        if not db_invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        # 获取所有未付清的应收款（可关联）
        query = select(Receivable).options(selectinload(Receivable.payment_records)).where(
            (Receivable.status != "paid")
        )

        # 如果发票有合同，优先返回该合同的应收款
        if db_invoice.contract_id:
            # 先获取该合同的应收款
            contract_receivables = await db.execute(
                select(Receivable)
                .options(selectinload(Receivable.payment_records))
                .where(
                    (Receivable.contract_id == db_invoice.contract_id) &
                    (Receivable.status != "paid")
                )
            )
            receivables = contract_receivables.scalars().all()
            print(f"[DEBUG] 合同应收款数量={len(receivables)}")
        else:
            result = await db.execute(query.order_by(Receivable.due_date.asc()))
            receivables = result.scalars().all()
            print(f"[DEBUG] 所有应收款数量={len(receivables)}")

        # 验证 Pydantic 转换
        items = []
        for r in receivables:
            try:
                item = ReceivableResponse.model_validate(r)
                items.append(item)
                print(f"[DEBUG] 转换成功：id={r.id}")
            except Exception as e:
                print(f"[ERROR] 转换失败：id={r.id}, error={e}")
                traceback.print_exc()
                raise

        print(f"[DEBUG] 返回 total={len(items)}")
        return ReceivableListResponse(
            total=len(items),
            items=items
        )
    except Exception as e:
        print(f"[ERROR] get_invoice_receivables 异常：{type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.post("/{invoice_id}/register-payment", response_model=PaymentRecordResponse)
async def register_payment_from_invoice(
    invoice_id: str,
    payment_data: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('invoices')),
):
    """从发票创建收款记录（本公司开具发票时的收款登记）"""
    # 验证发票是否存在
    invoice_result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    db_invoice = invoice_result.scalar_one_or_none()

    if not db_invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 验证应收款是否存在
    receivable_result = await db.execute(select(Receivable).where(Receivable.id == payment_data.receivable_id))
    db_receivable = receivable_result.scalar_one_or_none()

    if not db_receivable:
        raise HTTPException(status_code=404, detail="应收款不存在")

    # 创建收款记录
    db_payment = PaymentRecord(
        receivable_id=payment_data.receivable_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        payment_method=payment_data.payment_method,
        remark=payment_data.remark,
    )
    db.add(db_payment)

    # 关联发票
    db_payment.invoice.append(db_invoice)

    # 更新应收款
    db_receivable.received_amount = float(db_receivable.received_amount) + float(payment_data.amount)
    if db_receivable.received_amount >= db_receivable.amount:
        db_receivable.status = "paid"
    elif db_receivable.received_amount > 0:
        db_receivable.status = "partial"

    await db.commit()
    await db.refresh(db_payment)

    return PaymentRecordResponse(
        id=db_payment.id,
        receivable_id=db_payment.receivable_id,
        amount=db_payment.amount,
        payment_date=db_payment.payment_date,
        payment_method=db_payment.payment_method,
        remark=db_payment.remark,
        created_at=db_payment.created_at,
        invoice_ids=[invoice_id],
    )
