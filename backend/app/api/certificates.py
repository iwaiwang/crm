"""数字证书管理 API"""
import io
import zipfile
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.models.certificate import Certificate
from app.models.customer import Customer
from app.models.user import User
from app.schemas.certificate import (
    CertificateCreate,
    CertificateReject,
    CertificateResponse,
    CertificateListResponse,
)
from app.api.auth import get_current_user
from app.services.certificate_service import generate_certificate, decrypt_private_key

router = APIRouter()


def _cert_to_response(cert: Certificate, current_user: User) -> CertificateResponse:
    """将模型转换为响应，计算 can_approve / can_final_approve"""
    customer_name = ""
    applicant_name = ""
    approver_name = ""
    final_approver_name = ""
    if cert.customer:
        customer_name = cert.customer.name
    if cert.applicant:
        applicant_name = cert.applicant.username
    if cert.approver:
        approver_name = cert.approver.username
    if cert.final_approver:
        final_approver_name = cert.final_approver.username

    is_admin = current_user.role == "admin"
    return CertificateResponse(
        id=cert.id,
        cert_serial=cert.cert_serial,
        customer_id=cert.customer_id,
        customer_name=customer_name,
        product_name=cert.product_name,
        start_date=cert.start_date,
        end_date=cert.end_date,
        status=cert.status,
        applicant_id=cert.applicant_id,
        applicant_name=applicant_name,
        approver_id=cert.approver_id,
        approver_name=approver_name,
        final_approver_id=cert.final_approver_id,
        final_approver_name=final_approver_name,
        reject_reason=cert.reject_reason,
        issued_at=cert.issued_at,
        expires_at=cert.expires_at,
        revoked_at=cert.revoked_at,
        can_approve=is_admin and cert.status == "pending" and cert.applicant_id != current_user.id,
        can_final_approve=is_admin and cert.status == "approved" and cert.approver_id != current_user.id and cert.applicant_id != current_user.id,
        created_at=cert.created_at,
        updated_at=cert.updated_at,
    )


@router.get("", response_model=CertificateListResponse)
async def get_certificates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取证书列表"""
    query = select(Certificate).options(
        selectinload(Certificate.customer),
        selectinload(Certificate.applicant),
        selectinload(Certificate.approver),
        selectinload(Certificate.final_approver),
    )
    count_q = select(func.count()).select_from(Certificate)

    if status:
        if status == "expiring_soon":
            thirty_days = date.today().replace(day=min(date.today().day + 30, 28))
            query = query.where(
                and_(Certificate.status == "active", Certificate.end_date <= thirty_days, Certificate.end_date >= date.today())
            )
            count_q = count_q.where(
                and_(Certificate.status == "active", Certificate.end_date <= thirty_days, Certificate.end_date >= date.today())
            )
        else:
            query = query.where(Certificate.status == status)
            count_q = count_q.where(Certificate.status == status)

    if search:
        subq = select(Customer.id).where(Customer.name.contains(search))
        result = await db.execute(subq)
        customer_ids = [r[0] for r in result.all()]
        if customer_ids:
            query = query.where(Certificate.customer_id.in_(customer_ids))
            count_q = count_q.where(Certificate.customer_id.in_(customer_ids))
        else:
            query = query.where(Certificate.customer_id == None)
            count_q = count_q.where(Certificate.customer_id == None)

    total_result = await db.execute(count_q)
    total = total_result.scalar()

    query = query.order_by(Certificate.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    certificates = result.scalars().all()

    items = [_cert_to_response(c, current_user) for c in certificates]
    return CertificateListResponse(total=total, items=items)


@router.post("", response_model=CertificateResponse)
async def create_certificate(
    data: CertificateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """申请证书 (status=pending)"""
    from datetime import timedelta

    start = data.start_date
    end_month = start.month + data.duration_months
    end_year = start.year + (end_month - 1) // 12
    end_month = ((end_month - 1) % 12) + 1
    end_day = min(start.day, 28)
    end_date = date(end_year, end_month, end_day)

    cert = Certificate(
        customer_id=data.customer_id,
        product_name=data.product_name,
        start_date=data.start_date,
        end_date=end_date,
        status="pending",
        applicant_id=current_user.id,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert.id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one()
    return _cert_to_response(cert, current_user)


@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取证书详情"""
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    return _cert_to_response(cert, current_user)


@router.post("/{cert_id}/approve", response_model=CertificateResponse)
async def approve_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批证书 (两级审批: pending→approved→active+cert gen)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可审批")

    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    if cert.status == "pending":
        if cert.applicant_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能审核自己提交的申请")
        cert.status = "approved"
        cert.approver_id = current_user.id
        await db.commit()
        await db.refresh(cert)
        return _cert_to_response(cert, current_user)

    elif cert.status == "approved":
        if cert.approver_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能由同一人完成两级审批")
        if cert.applicant_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能审核自己提交的申请")

        customer_name = cert.customer.name if cert.customer else "Unknown"
        gen_result = generate_certificate(
            customer_name=customer_name,
            product_name=cert.product_name,
            start_date=cert.start_date,
            end_date=cert.end_date,
        )
        cert.cert_serial = gen_result["serial"]
        cert.certificate_pem = gen_result["cert_pem"]
        cert.private_key_pem = gen_result["encrypted_key_pem"]
        cert.status = "active"
        cert.final_approver_id = current_user.id
        cert.issued_at = datetime.utcnow()
        cert.expires_at = datetime.combine(cert.end_date, datetime.max.time())
        await db.commit()
        await db.refresh(cert)
        return _cert_to_response(cert, current_user)

    else:
        raise HTTPException(status_code=400, detail=f"当前状态 {cert.status} 不允许审批")


@router.post("/{cert_id}/reject", response_model=CertificateResponse)
async def reject_certificate(
    cert_id: str,
    data: CertificateReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """驳回证书申请"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可驳回")

    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    if cert.status not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail=f"当前状态 {cert.status} 不允许驳回")

    cert.status = "rejected"
    cert.reject_reason = data.reason
    await db.commit()
    await db.refresh(cert)
    return _cert_to_response(cert, current_user)


@router.post("/{cert_id}/revoke", response_model=CertificateResponse)
async def revoke_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """吊销证书"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可吊销")

    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    if cert.status != "active":
        raise HTTPException(status_code=400, detail="只能吊销已签发的证书")

    cert.status = "revoked"
    cert.revoked_at = datetime.utcnow()
    await db.commit()
    await db.refresh(cert)
    return _cert_to_response(cert, current_user)


@router.post("/{cert_id}/renew", response_model=CertificateResponse)
async def renew_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """续期证书 (创建新的 pending 记录)"""
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    old = result.scalar_one_or_none()
    if not old:
        raise HTTPException(status_code=404, detail="证书不存在")
    if old.status not in ("expired", "active"):
        raise HTTPException(status_code=400, detail="只能续期已过期或已签发的证书")

    delta = old.end_date - old.start_date
    new_start = old.end_date
    new_end = new_start + delta
    cert = Certificate(
        customer_id=old.customer_id,
        product_name=old.product_name,
        start_date=new_start,
        end_date=new_end,
        status="pending",
        applicant_id=current_user.id,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    result2 = await db.execute(
        select(Certificate).where(Certificate.id == cert.id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result2.scalar_one()
    return _cert_to_response(cert, current_user)


@router.get("/{cert_id}/download")
async def download_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载证书 ZIP 包 (证书 PEM + 私钥 PEM)"""
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id).options(
            selectinload(Certificate.customer),
            selectinload(Certificate.applicant),
            selectinload(Certificate.approver),
            selectinload(Certificate.final_approver),
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    if cert.status != "active":
        raise HTTPException(status_code=400, detail="只能下载已签发的证书")
    if not cert.private_key_pem or not cert.certificate_pem:
        raise HTTPException(status_code=400, detail="证书文件不完整")

    try:
        key_pem = decrypt_private_key(cert.private_key_pem)
    except Exception:
        raise HTTPException(status_code=500, detail="私钥解密失败")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        safe_name = cert.customer.name if cert.customer else "certificate"
        safe_product = cert.product_name.replace("/", "_")
        zf.writestr(f"{safe_name}_{safe_product}_certificate.pem", cert.certificate_pem)
        zf.writestr(f"{safe_name}_{safe_product}_private_key.pem", key_pem)

    zip_buffer.seek(0)
    filename = f"certificate_{cert.cert_serial}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
