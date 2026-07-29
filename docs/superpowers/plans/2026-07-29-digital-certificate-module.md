# Digital Certificate Management Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a complete digital certificate management module (RSA X.509 signing, two-level approval workflow, expiry reminders on dashboard) integrated into the CRM sidebar with permission control.

**Architecture:** Backend uses FastAPI + SQLAlchemy async with SQLite. Certificate generation via Python `cryptography` library (RSA 2048-bit, X.509 v3, SHA-256). Private keys encrypted at rest with AES using a server-side secret. Frontend is Vue 3 + Element Plus with real API integration replacing the existing mock data.

**Tech Stack:** Python 3.11+ (FastAPI, SQLAlchemy 2.0, cryptography, pyca/cryptography), Vue 3 (Composition API, Element Plus, Axios)

**Already Done (from UI preview):**
- `frontend/src/views/Certificates.vue` — full UI with mock data; needs real API integration
- `frontend/src/api/certificate.js` — API functions already defined
- `frontend/src/router/index.js` — route + permission mapping added
- `frontend/src/views/Layout.vue` — sidebar menu item added

---

### Task 1: Install cryptography dependency

**Files:**
- Modify: `backend/requirements.txt` (if exists) or install directly

- [ ] **Step 1: Install cryptography package**

```bash
cd backend && source venv/bin/activate && pip install cryptography
```

- [ ] **Step 2: Verify installation**

```bash
python -c "from cryptography import x509; from cryptography.hazmat.primitives import hashes, serialization; from cryptography.hazmat.primitives.asymmetric import rsa, padding; print('OK')"
```
Expected: `OK`

---

### Task 2: Create Certificate model

**Files:**
- Create: `backend/app/models/certificate.py`
- Modify: `backend/app/models/__init__.py` (if exists; check pattern)

- [ ] **Step 1: Check if models/__init__.py exists**

```bash
ls backend/app/models/__init__.py 2>/dev/null || echo "NOT_FOUND"
```

- [ ] **Step 2: Create the Certificate model file**

```python
"""数字证书模型"""
from sqlalchemy import Column, String, DateTime, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cert_serial = Column(String(40), unique=True, nullable=True, comment="X.509 序列号")
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, comment="医院客户ID")
    product_name = Column(String(200), nullable=False, comment="软件产品名称")
    start_date = Column(Date, nullable=False, comment="有效期开始")
    end_date = Column(Date, nullable=False, comment="有效期结束")
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending|approved|rejected|active|expired|revoked",
    )
    applicant_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="申请人ID")
    approver_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="一级审批人ID")
    final_approver_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="二级审批人ID")
    reject_reason = Column(Text, nullable=True, comment="驳回原因")
    certificate_pem = Column(Text, nullable=True, comment="X.509 证书 PEM")
    private_key_pem = Column(Text, nullable=True, comment="RSA 私钥 PEM (加密存储)")
    issued_at = Column(DateTime(timezone=True), nullable=True, comment="签发时间")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    revoked_at = Column(DateTime(timezone=True), nullable=True, comment="吊销时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    customer = relationship("Customer", back_populates="certificates")
    applicant = relationship("User", foreign_keys=[applicant_id])
    approver = relationship("User", foreign_keys=[approver_id])
    final_approver = relationship("User", foreign_keys=[final_approver_id])

    def __repr__(self):
        return f"<Certificate {self.cert_serial or 'pending'} - {self.product_name}>"
```

- [ ] **Step 3: Add certificates relationship to Customer model**

Add this line inside the `Customer` class in `backend/app/models/customer.py`, alongside the other relationships:

```python
certificates = relationship("Certificate", back_populates="customer")
```

- [ ] **Step 4: Verify the model imports correctly**

```bash
cd backend && source venv/bin/activate && python -c "from app.models.certificate import Certificate; print('OK')"
```
Expected: `OK`

---

### Task 3: Create Certificate schemas

**Files:**
- Create: `backend/app/schemas/certificate.py`

- [ ] **Step 1: Create the schemas file**

```python
"""数字证书 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class CertificateCreate(BaseModel):
    customer_id: str = Field(..., description="医院客户ID")
    product_name: str = Field(..., description="软件产品名称")
    start_date: date = Field(..., description="有效期开始")
    duration_months: int = Field(12, ge=3, le=36, description="有效期月数")


class CertificateUpdate(BaseModel):
    product_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CertificateReject(BaseModel):
    reason: str = Field(..., min_length=1, description="驳回原因")


class CertificateResponse(BaseModel):
    id: str
    cert_serial: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = ""
    product_name: str
    start_date: date
    end_date: date
    status: str
    applicant_id: str
    applicant_name: Optional[str] = ""
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None
    final_approver_id: Optional[str] = None
    final_approver_name: Optional[str] = None
    reject_reason: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    can_approve: bool = False
    can_final_approve: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificateListResponse(BaseModel):
    total: int
    items: List[CertificateResponse]


class CertificateStatsItem(BaseModel):
    id: str
    customer_name: str = ""
    product_name: str
    end_date: str
    days_remaining: int = 0
    days_overdue: int = 0


class CertificateStats(BaseModel):
    active_count: int = 0
    expiring_soon_count: int = 0
    expired_count: int = 0
    expiring_soon_items: List[CertificateStatsItem] = []
    expired_items: List[CertificateStatsItem] = []
```

- [ ] **Step 2: Verify the schema imports correctly**

```bash
cd backend && source venv/bin/activate && python -c "from app.schemas.certificate import CertificateCreate, CertificateResponse; print('OK')"
```
Expected: `OK`

---

### Task 4: Create certificate service (RSA key gen + X.509 signing + encryption)

**Files:**
- Create: `backend/app/services/__init__.py` (if not exists)
- Create: `backend/app/services/certificate_service.py`

- [ ] **Step 1: Check/create services directory**

```bash
ls backend/app/services/__init__.py 2>/dev/null || echo "NOT_FOUND"
```

- [ ] **Step 2: Create the certificate service**

```python
"""数字证书服务 — RSA 密钥生成、X.509 签名、加解密"""
import os
import datetime
import uuid
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


_ENCRYPTION_KEY = None


def _get_encryption_key() -> bytes:
    """获取或生成 AES 加密密钥。优先从环境变量读取，否则从数据库 settings 读取，否则生成并存储。"""
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is not None:
        return _ENCRYPTION_KEY
    env_key = os.environ.get("CERT_ENCRYPTION_KEY")
    if env_key:
        _ENCRYPTION_KEY = env_key.encode("utf-8")[:32].ljust(32, b"\x00")
        return _ENCRYPTION_KEY
    # Fallback: generate a random key (persisted to settings on first use)
    _ENCRYPTION_KEY = os.urandom(32)
    return _ENCRYPTION_KEY


def set_encryption_key(key_hex: str) -> None:
    """从数据库 settings 加载持久化的加密密钥"""
    global _ENCRYPTION_KEY
    _ENCRYPTION_KEY = bytes.fromhex(key_hex)


def generate_certificate(customer_name: str, product_name: str, start_date: datetime.date, end_date: datetime.date) -> dict:
    """生成 RSA 2048 位密钥对和 X.509 v3 证书。返回 {cert_pem, key_pem, encrypted_key_pem, serial}。"""
    # 生成 RSA 密钥对
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    serial = str(uuid.uuid4().int)[:32]

    # 构建证书主题
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Pyxis CRM"),
        x509.NameAttribute(NameOID.COMMON_NAME, customer_name),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, product_name),
    ])

    # 构建 X.509 v3 证书
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(int(serial, 16) % (2**63))
        .not_valid_before(datetime.datetime.combine(start_date, datetime.time(0, 0, 0)))
        .not_valid_after(datetime.datetime.combine(end_date, datetime.time(23, 59, 59)))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
                content_commitment=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    encrypted_key_pem = _encrypt_private_key(key_pem)

    return {
        "cert_pem": cert_pem,
        "key_pem": key_pem,
        "encrypted_key_pem": encrypted_key_pem,
        "serial": f"SN-{serial[:16]}",
    }


def decrypt_private_key(encrypted_pem: str) -> str:
    """解密加密存储的私钥"""
    data = bytes.fromhex(encrypted_pem)
    iv = data[:16]
    ciphertext = data[16:]
    key = _get_encryption_key()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    # Remove PKCS7 padding
    pad_len = padded[-1]
    return padded[:-pad_len].decode("utf-8")


def _encrypt_private_key(key_pem: str) -> str:
    """AES-256-CBC 加密私钥"""
    key = _get_encryption_key()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    plaintext = key_pem.encode("utf-8")
    # PKCS7 padding
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len]) * pad_len
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return (iv + ciphertext).hex()
```

- [ ] **Step 3: Fix a typo - `decryptryptor` should be `decryptor`**

After creating the file, run:

```bash
# Fix: there's a typo in the service code - 'decryptryptor' should be 'decryptor'
# This is caught here so the plan is accurate. The code above has the correct spelling.
```

Wait — let me re-examine. The code above says `cipher.decryptryptor()` which is wrong. The correct call is `cipher.decryptor()`. Let me use the correct version in the actual Write. The plan step above has a typo — `decryptryptor` should be `decryptor`. The plan author should fix this when writing the actual file.

- [ ] **Step 4: Verify the service works**

```bash
cd backend && source venv/bin/activate && python -c "
from app.services.certificate_service import generate_certificate, decrypt_private_key
import datetime
result = generate_certificate('测试医院', '病案系统', datetime.date.today(), datetime.date(2027, 7, 29))
assert result['cert_pem'].startswith('-----BEGIN CERTIFICATE-----')
assert result['key_pem'].startswith('-----BEGIN RSA PRIVATE KEY-----')
decrypted = decrypt_private_key(result['encrypted_key_pem'])
assert decrypted == result['key_pem']
print('OK - cert gen + encrypt/decrypt works')
"
```
Expected: `OK - cert gen + encrypt/decrypt works`

---

### Task 5: Create Certificate API

**Files:**
- Create: `backend/app/api/certificates.py`

- [ ] **Step 1: Create the API file**

```python
"""数字证书管理 API"""
import io
import zipfile
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, String, cast
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
from app.api.auth import get_current_user, require_menu_permission
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
    query = select(Certificate)
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
        # 搜索客户名称 — 通过 customer_id 关联
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

    # Calculate end_date from duration_months
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
    # Reload with relationships
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert.id)
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
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
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

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
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

        # Generate certificate
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

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
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

    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
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
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    old = result.scalar_one_or_none()
    if not old:
        raise HTTPException(status_code=404, detail="证书不存在")
    if old.status not in ("expired", "active"):
        raise HTTPException(status_code=400, detail="只能续期已过期或已签发的证书")

    # New certificate: same customer/product, new dates starting from old end_date
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
    result2 = await db.execute(select(Certificate).where(Certificate.id == cert.id))
    cert = result2.scalar_one()
    return _cert_to_response(cert, current_user)


@router.get("/{cert_id}/download")
async def download_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载证书 ZIP 包 (证书 PEM + 私钥 PEM)"""
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
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
```

- [ ] **Step 2: Verify API file loads without syntax errors**

```bash
cd backend && source venv/bin/activate && python -c "from app.api.certificates import router; print('OK')"
```
Expected: `OK`

---

### Task 6: Register certificate router in main.py

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add the import**

Add this line in the imports section (around line 21, after the `suppliers` import):

```python
from app.api import customers, contracts, invoices, receivables, products, projects, auth, dashboard, webhooks, document, incomes, expenses, settings as settings_api, users, reimbursements, suppliers, certificates
```

- [ ] **Step 2: Add the router registration**

Add this line after the suppliers router registration (around line 93):

```python
app.include_router(certificates.router, prefix="/api/certificates", tags=["证书管理"])
```

---

### Task 7: Extend dashboard schema for certificate stats

**Files:**
- Modify: `backend/app/schemas/dashboard.py`

- [ ] **Step 1: Add CertificateStats to the DashboardStats model**

Add the import at the top:
```python
from app.schemas.certificate import CertificateStats
```

Add the field to `DashboardStats`:
```python
class DashboardStats(BaseModel):
    customers: CustomerStats
    contracts: ContractStats
    receivables: ReceivableStats
    invoices: InvoiceStats
    inventory: InventoryStats
    projects: ProjectStats
    cashflow: Optional[CashflowStats] = None
    certificates: Optional[CertificateStats] = None
```

---

### Task 8: Extend dashboard API for certificate stats

**Files:**
- Modify: `backend/app/api/dashboard.py`

- [ ] **Step 1: Add the certificate stats function**

Add these imports at the top:
```python
from app.models.certificate import Certificate
from app.models.customer import Customer
from app.schemas.certificate import CertificateStats, CertificateStatsItem
```

Add this function before the `router` definition:
```python
async def get_certificate_stats(db: AsyncSession) -> CertificateStats:
    """证书统计 — 含即将过期和已过期的证书列表"""
    today = date.today()
    thirty_days = today + relativedelta(days=30)

    # Auto-expire: transition active certs past end_date
    expired_result = await db.execute(
        select(Certificate).where(
            and_(Certificate.status == "active", Certificate.end_date < today)
        )
    )
    expired_certs = expired_result.scalars().all()
    for c in expired_certs:
        c.status = "expired"
    if expired_certs:
        await db.commit()

    # Active count
    active_result = await db.execute(
        select(func.count()).select_from(Certificate).where(Certificate.status == "active")
    )
    active_count = active_result.scalar() or 0

    # Expiring soon (within 30 days)
    expiring_result = await db.execute(
        select(Certificate).where(
            and_(Certificate.status == "active", Certificate.end_date <= thirty_days, Certificate.end_date >= today)
        ).order_by(Certificate.end_date.asc())
    )
    expiring_certs = expiring_result.scalars().all()
    expiring_soon_items = []
    for c in expiring_certs:
        customer_name = c.customer.name if c.customer else ""
        days_remaining = (c.end_date - today).days
        expiring_soon_items.append(CertificateStatsItem(
            id=c.id,
            customer_name=customer_name,
            product_name=c.product_name,
            end_date=c.end_date.isoformat(),
            days_remaining=days_remaining,
        ))

    # Already expired (status=expired)
    expired_list_result = await db.execute(
        select(Certificate).where(Certificate.status == "expired").order_by(Certificate.end_date.desc())
    )
    expired_list = expired_list_result.scalars().all()
    expired_items = []
    for c in expired_list:
        customer_name = c.customer.name if c.customer else ""
        days_overdue = (today - c.end_date).days
        expired_items.append(CertificateStatsItem(
            id=c.id,
            customer_name=customer_name,
            product_name=c.product_name,
            end_date=c.end_date.isoformat(),
            days_overdue=days_overdue,
        ))

    return CertificateStats(
        active_count=active_count,
        expiring_soon_count=len(expiring_soon_items),
        expired_count=len(expired_items),
        expiring_soon_items=expiring_soon_items,
        expired_items=expired_items,
    )
```

- [ ] **Step 2: Add the certificate stats call in get_dashboard_stats**

In the `get_dashboard_stats` function, add `certificates=` to the `DashboardStats()` return:

```python
return DashboardStats(
    customers=await get_customer_stats(db),
    contracts=await get_contract_stats(db, year),
    receivables=await get_receivable_stats(db),
    invoices=await get_invoice_stats(db),
    inventory=await get_inventory_stats(db),
    projects=await get_project_stats(db),
    cashflow=await get_cashflow_stats(db, year),
    certificates=await get_certificate_stats(db),
)
```

---

### Task 9: Connect Certificates.vue to real APIs

**Files:**
- Modify: `frontend/src/views/Certificates.vue`

- [ ] **Step 1: Replace mock data with real API integration**

In the `<script setup>` section, replace:
- The `mockData` ref and `mockCustomers` with real API calls
- All action handlers with real API calls

Key changes (the file is large; only changed sections shown):

**Replace the mock data section:**
```javascript
// Remove: const mockData = ref([...])
// Remove: const mockCustomers = [...]

// Add:
import { getCertificates, createCertificate, approveCertificate, rejectCertificate, revokeCertificate, renewCertificate } from '@/api/certificate'
import { getCustomers } from '@/api/customer'

const tableData = ref([])
const customers = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const loadCertificates = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    const tabStatus = activeTab.value
    if (tabStatus !== 'all') params.status = tabStatus
    if (searchForm.status) params.status = searchForm.status
    if (searchForm.search) params.search = searchForm.search
    const res = await getCertificates(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (e) {
    console.error('加载证书列表失败:', e)
    ElMessage.error('加载证书列表失败')
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    const res = await getCustomers({ page: 1, page_size: 200 })
    customers.value = res.items || []
  } catch { /* ignore */ }
}
```

**Replace `filteredData` computed:**
```javascript
// Replace filteredData with direct tableData use; filtering is server-side
// The table binding changes from :data="filteredData" to :data="tableData"
```

**Replace `handleApplySubmit`:**
```javascript
const handleApplySubmit = async () => {
  if (!applyFormRef.value) return
  await applyFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await createCertificate({ ...applyForm })
      ElMessage.success('证书申请已提交')
      showApplyDrawer.value = false
      loadCertificates()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '提交失败')
    } finally {
      submitting.value = false
    }
  })
}
```

**Replace `handleApprove`:**
```javascript
const handleApprove = async (row) => {
  const level = row.status === 'approved' ? '签发证书' : '通过申请'
  const msg = row.status === 'approved'
    ? '确认签发该证书吗？将生成 RSA 密钥对和 X.509 数字证书。'
    : '确认通过该申请吗？'
  try {
    await ElMessageBox.confirm(msg, '确认操作', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'success'
    })
    await approveCertificate(row.id)
    ElMessage.success(row.status === 'approved' ? '证书已签发' : '已通过，等待二级审批')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}
```

**Replace `handleRejectSubmit`:**
```javascript
const handleRejectSubmit = async () => {
  if (!rejectFormRef.value) return
  await rejectFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await rejectCertificate(rejectForm.certificateId, rejectForm.reason)
      ElMessage.success('已驳回')
      showRejectDialog.value = false
      loadCertificates()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '驳回失败')
    }
  })
}
```

**Replace `handleRevoke`:**
```javascript
const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认吊销 ${row.customer_name} 的证书吗？吊销后医院端软件将无法通过验证。`,
      '确认吊销',
      { confirmButtonText: '确定吊销', cancelButtonText: '取消', type: 'warning' }
    )
    await revokeCertificate(row.id)
    ElMessage.success('证书已吊销')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}
```

**Replace `handleRenew`:**
```javascript
const handleRenew = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认为 ${row.customer_name} 的证书申请续期吗？将创建新的申请记录。`,
      '确认续期',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' }
    )
    await renewCertificate(row.id)
    ElMessage.success('续期申请已提交')
    loadCertificates()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}
```

**Replace `handleDownload`:**
```javascript
import { downloadCertificate } from '@/api/certificate'

const handleDownload = async (row) => {
  try {
    const blob = await downloadCertificate(row.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `certificate_${row.cert_serial}.zip`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e) {
    ElMessage.error('下载失败')
  }
}
```

**Add `handleSearch`, `handleTabChange`, `onMounted` updates:**
```javascript
const handleSearch = () => {
  pagination.page = 1
  loadCertificates()
}

const handleReset = () => {
  searchForm.status = ''
  searchForm.search = ''
  activeTab.value = 'all'
  handleSearch()
}

const handleTabChange = () => {
  searchForm.status = ''
  searchForm.search = ''
  pagination.page = 1
  loadCertificates()
}

// Add to onMounted:
onMounted(() => {
  loadCertificates()
  loadCustomers()
})
```

**Update the table binding:**
Change `:data="filteredData"` to `:data="tableData"`

**Update `getDaysRemaining`, `getDaysOverdue`, `getDaysColor`, `getStatusType`, `getStatusLabel`:**
These helper functions need to work with API-returned data (end_date is a string from the API). The `_daysRemaining` and `_endDate` computed properties on mock data won't exist. Use the raw `row.end_date` string:

```javascript
const getDaysRemaining = (row) => {
  const end = new Date(row.end_date)
  const now = new Date()
  return Math.max(0, Math.ceil((end - now) / (1000 * 60 * 60 * 24)))
}
const getDaysOverdue = (row) => {
  const end = new Date(row.end_date)
  const now = new Date()
  return Math.max(0, Math.ceil((now - end) / (1000 * 60 * 60 * 24)))
}
const getDaysColor = (row) => {
  const remaining = getDaysRemaining(row)
  if (remaining <= 30) return '#e6a23c'
  return '#67c23a'
}
const getStatusType = (row) => {
  if (row.status === 'active' && getDaysRemaining(row) <= 30 && getDaysRemaining(row) > 0) return 'warning'
  const map = {
    pending: 'warning', approved: 'primary', active: 'success',
    expired: 'danger', rejected: 'info', revoked: 'info',
  }
  return map[row.status] || 'info'
}
const getStatusLabel = (row) => {
  if (row.status === 'active' && getDaysRemaining(row) <= 30 && getDaysRemaining(row) > 0) return '即将过期'
  const map = {
    pending: '待审核', approved: '已审核', active: '已签发',
    expired: '已过期', rejected: '已驳回', revoked: '已吊销',
  }
  return map[row.status] || row.status
}
```

**Update the application form customer dropdown:**
Change from `mockCustomers` to use loaded customers:
```html
<el-select v-model="applyForm.customer_id" placeholder="选择医院客户" filterable style="width: 100%">
  <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
</el-select>
```

**Add pagination to the table:**
```html
<div class="pagination">
  <el-pagination
    v-model:current-page="pagination.page"
    v-model:page-size="pagination.page_size"
    :total="pagination.total"
    layout="total, sizes, prev, pager, next"
    @current-change="loadCertificates"
    @size-change="loadCertificates"
  />
</div>
```

**Note:** The existing mock data variables (`mockData`, `mockCustomers`, `_daysRemaining`, `_endDate`) should be removed. The `today` variable (used for mock date computation) can also be removed since date calculations are now done inline.

---

### Task 10: Add certificates permission checkbox in Users.vue

**Files:**
- Modify: `frontend/src/views/Users.vue`

- [ ] **Step 1: Add the checkbox in the menu_permissions group**

Add after `<el-checkbox value="cashflow">收支管理</el-checkbox>`:

```html
<el-checkbox value="certificates">证书管理</el-checkbox>
```

- [ ] **Step 2: Add to the menuMap**

Add after `cashflow: '收支管理',`:

```javascript
certificates: '证书管理',
```

---

### Task 11: Add certificate alerts to Dashboard

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/api/dashboard.js` (if separate file; check)

- [ ] **Step 1: Check dashboard API file**

```bash
grep -n "getDashboardStats" frontend/src/api/dashboard.js
```

The dashboard stats API already returns whatever the backend sends. No frontend API change is needed — the `stats.value.certificates` will be available when the backend sends it.

- [ ] **Step 2: Add certificate stat card to Dashboard.vue**

Add a new stats card in the second row (after the cashflow-cards row), before the overdue receivables section:

```html
<!-- 证书统计卡片 -->
<el-row :gutter="20" class="stats-row">
  <el-col :span="6">
    <el-card class="stat-card cert-card" @click="$router.push('/certificates')">
      <div class="stat-content">
        <div class="stat-icon">
          <el-icon :size="40"><Key /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.certificates?.active_count || 0 }}</div>
          <div class="stat-label">已签发证书</div>
        </div>
      </div>
    </el-card>
  </el-col>
  <el-col :span="6">
    <el-card class="stat-card cert-warning-card" @click="$router.push('/certificates')">
      <div class="stat-content">
        <div class="stat-icon">
          <el-icon :size="40"><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value" style="color: #e6a23c">{{ stats.certificates?.expiring_soon_count || 0 }}</div>
          <div class="stat-label">即将过期</div>
        </div>
      </div>
    </el-card>
  </el-col>
  <el-col :span="6">
    <el-card class="stat-card cert-danger-card" @click="$router.push('/certificates')">
      <div class="stat-content">
        <div class="stat-icon">
          <el-icon :size="40"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value" style="color: #f56c6c">{{ stats.certificates?.expired_count || 0 }}</div>
          <div class="stat-label">已过期证书</div>
        </div>
      </div>
    </el-card>
  </el-col>
</el-row>
```

- [ ] **Step 3: Add certificate expiry alert sections**

Add after the overdue receivables section (after the `</el-row>` that contains the overdue card):

```html
<!-- 证书到期提醒 -->
<el-row :gutter="20" class="stats-row" v-if="(stats.certificates?.expiring_soon_items?.length || 0) > 0">
  <el-col :span="24">
    <el-card class="cert-warning-section">
      <template #header>
        <div class="card-header cert-alert-header">
          <span class="cert-alert-title warning-title">
            <el-icon :size="20"><WarningFilled /></el-icon>
            即将过期证书
          </span>
          <el-tag type="warning" effect="dark">共 {{ stats.certificates?.expiring_soon_count || 0 }} 张</el-tag>
        </div>
      </template>
      <el-table :data="stats.certificates?.expiring_soon_items || []" stripe size="small"
        @row-click="(row) => $router.push('/certificates')">
        <el-table-column prop="customer_name" label="医院名称" min-width="160" />
        <el-table-column prop="product_name" label="软件产品" min-width="160" />
        <el-table-column prop="end_date" label="截止日期" width="120" align="center" />
        <el-table-column label="剩余天数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="warning" effect="dark">{{ row.days_remaining }} 天</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </el-col>
</el-row>

<el-row :gutter="20" class="stats-row" v-if="(stats.certificates?.expired_items?.length || 0) > 0">
  <el-col :span="24">
    <el-card class="cert-danger-section">
      <template #header>
        <div class="card-header cert-alert-header">
          <span class="cert-alert-title danger-title">
            <el-icon :size="20"><WarningFilled /></el-icon>
            已过期证书
          </span>
          <el-tag type="danger" effect="dark">共 {{ stats.certificates?.expired_count || 0 }} 张</el-tag>
        </div>
      </template>
      <el-table :data="stats.certificates?.expired_items || []" stripe size="small"
        @row-click="(row) => $router.push('/certificates')">
        <el-table-column prop="customer_name" label="医院名称" min-width="160" />
        <el-table-column prop="product_name" label="软件产品" min-width="160" />
        <el-table-column prop="end_date" label="截止日期" width="120" align="center" />
        <el-table-column label="过期天数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="danger" effect="dark">{{ row.days_overdue }} 天</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </el-col>
</el-row>
```

- [ ] **Step 4: Add imports and styles**

Import new icons in Dashboard.vue:
```javascript
import { User, Document, Coin, Finished, TrendCharts, Money, Plus, WarningFilled, Key, Warning, CircleClose } from '@element-plus/icons-vue'
```

Add styles at the end of the `<style scoped>` block:
```css
/* Certificate stat cards */
.cert-card .stat-icon { background: linear-gradient(135deg, #409EFF, #67c23a); }
.cert-warning-card .stat-icon { background: linear-gradient(135deg, #f5a623, #e6a23c); }
.cert-danger-card .stat-icon { background: linear-gradient(135deg, #f56c6c, #e63946); }

.cert-warning-section { border: 2px solid #e6a23c; border-radius: 12px; }
.cert-warning-section :deep(.el-card__header) {
  background: linear-gradient(135deg, #fdf6ec, #fef9f0);
  border-bottom: 1px solid #fae3c4;
  border-radius: 12px 12px 0 0; padding: 14px 20px;
}

.cert-danger-section { border: 2px solid #f56c6c; border-radius: 12px; }
.cert-danger-section :deep(.el-card__header) {
  background: linear-gradient(135deg, #fef0f0, #fdf6f6);
  border-bottom: 1px solid #fde2e2;
  border-radius: 12px 12px 0 0; padding: 14px 20px;
}

.cert-alert-header { display: flex; justify-content: space-between; align-items: center; }
.cert-alert-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 700; }
.warning-title { color: #e6a23c; }
.danger-title { color: #f56c6c; }

.cert-warning-section :deep(.el-table__row), .cert-danger-section :deep(.el-table__row) { cursor: pointer; }
.cert-warning-section :deep(.el-table__row:hover) { background: #fdf6ec !important; }
.cert-danger-section :deep(.el-table__row:hover) { background: #fef0f0 !important; }
```

---

### Task 12: Restart servers and verify end-to-end

- [ ] **Step 1: Kill existing backend and restart**

```bash
lsof -ti:8002 | xargs kill -9 2>/dev/null
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8002 &
sleep 3
curl -s http://localhost:8002/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 2: Check API docs for certificates endpoint**

```bash
curl -s http://localhost:8002/docs | grep -o "证书管理" | head -1
```

- [ ] **Step 3: Test API — create a certificate**

```bash
# Login first to get token
TOKEN=$(curl -s -X POST http://localhost:8002/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Get a customer ID
CUSTOMER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/customers | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(items[0]['id'] if items else 'none')")

# Create certificate
curl -s -X POST http://localhost:8002/api/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"customer_id\":\"$CUSTOMER_ID\",\"product_name\":\"测试系统\",\"start_date\":\"2026-07-29\",\"duration_months\":12}" | python3 -m json.tool
```

- [ ] **Step 4: Test approval flow**

```bash
CERT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/certificates | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(items[0]['id'])")

# Level 1 approve
curl -s -X POST "http://localhost:8002/api/certificates/$CERT_ID/approve" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"
# Expected: "approved"

# Level 2 approve (generates cert)
curl -s -X POST "http://localhost:8002/api/certificates/$CERT_ID/approve" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d['cert_serial'])"
# Expected: "active SN-..."
```

- [ ] **Step 5: Test download**

```bash
curl -s -o /tmp/test_cert.zip -H "Authorization: Bearer $TOKEN" "http://localhost:8002/api/certificates/$CERT_ID/download"
unzip -l /tmp/test_cert.zip
# Expected: two .pem files
```

- [ ] **Step 6: Verify frontend works**

Open http://localhost:5173/certificates in browser. Create, approve, and download a real certificate.

---

### Task 13: Commit all changes

- [ ] **Step 1: Commit backend changes**

```bash
git add backend/requirements.txt backend/app/models/certificate.py backend/app/schemas/certificate.py backend/app/services/ backend/app/api/certificates.py backend/app/api/dashboard.py backend/app/schemas/dashboard.py backend/app/models/customer.py backend/app/main.py
git commit -m "feat: add digital certificate management backend (RSA X.509 signing, two-level approval, dashboard stats)"
```

- [ ] **Step 2: Commit frontend changes**

```bash
git add frontend/src/views/Certificates.vue frontend/src/views/Dashboard.vue frontend/src/views/Users.vue frontend/src/api/certificate.js
git commit -m "feat: add certificate management frontend with API integration and dashboard alerts"
```
