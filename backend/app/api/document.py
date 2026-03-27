"""通用文档服务 API"""
import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.ai_config import AIConfig
from app.api.auth import get_current_user
from app.services.ai_parser import ai_service
from app.services.invoice_qr import recognize_invoice_from_qr
from app.services.invoice_ocr import InvoiceOCR
from app.config import settings

router = APIRouter(prefix="/document", tags=["文档服务"])

# 配置 - 使用与 StaticFiles 相同的目录
UPLOAD_BASE_DIR = settings.UPLOAD_DIR
UPLOAD_CONTRACT_DIR = os.path.join(UPLOAD_BASE_DIR, "contracts")
UPLOAD_INVOICE_DIR = os.path.join(UPLOAD_BASE_DIR, "invoices")

ALLOWED_CONTRACT_TYPES = [".pdf", ".doc", ".docx"]
ALLOWED_INVOICE_TYPES = [".pdf", ".jpg", ".jpeg", ".png"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def ensure_upload_dirs():
    """确保上传目录存在"""
    os.makedirs(UPLOAD_CONTRACT_DIR, exist_ok=True)
    os.makedirs(UPLOAD_INVOICE_DIR, exist_ok=True)


def get_upload_dir(doc_type: str) -> str:
    """根据类型获取上传目录"""
    if doc_type == "contract":
        return UPLOAD_CONTRACT_DIR
    elif doc_type == "invoice":
        return UPLOAD_INVOICE_DIR
    else:
        raise ValueError(f"不支持的文档类型：{doc_type}")


def get_allowed_types(doc_type: str) -> list:
    """根据类型获取允许的文件扩展名"""
    if doc_type == "contract":
        return ALLOWED_CONTRACT_TYPES
    elif doc_type == "invoice":
        return ALLOWED_INVOICE_TYPES
    else:
        raise ValueError(f"不支持的文档类型：{doc_type}")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    type: str = Body("contract", description="文档类型：contract|invoice"),
    current_user: User = Depends(get_current_user),
):
    """
    上传文档
    - file: 文件
    - type: 文档类型 (contract/invoice)
    """
    ensure_upload_dirs()

    # 验证类型
    if type not in ["contract", "invoice"]:
        raise HTTPException(status_code=400, detail="不支持的文档类型")

    # 验证文件扩展名
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    allowed_types = get_allowed_types(type)
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，允许：{', '.join(allowed_types)}"
        )

    # 验证文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")

    # 生成文件名
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    upload_dir = get_upload_dir(type)
    filepath = os.path.join(upload_dir, filename)

    # 调试输出
    print(f"[DEBUG] upload_dir={upload_dir}")
    print(f"[DEBUG] filepath={filepath}")

    # 保存文件
    with open(filepath, "wb") as f:
        f.write(content)

    # 返回文件信息
    file_url = f"/uploads/{type}s/{filename}"

    return {
        "file_id": file_id,
        "file_name": file.filename or filename,
        "file_url": file_url,
        "file_size": len(content),
        "file_type": ext[1:] if ext else "",
    }


@router.post("/parse-with-ai")
async def parse_document_with_ai(
    file_id: str = Body(..., description="文件 ID"),
    type: str = Body("contract", description="文档类型：contract|invoice"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    使用 AI 解析文档
    - file_id: 文件 ID
    - type: 文档类型 (contract/invoice)
    """
    # 从数据库加载最新配置
    result = await db.execute(select(AIConfig).limit(1))
    db_config = result.scalar_one_or_none()

    if not db_config:
        raise HTTPException(status_code=503, detail="AI 服务未配置")

    if not db_config.enabled:
        raise HTTPException(status_code=503, detail="AI 服务未启用")

    # 加载配置到内存
    ai_service.load_config_from_db({
        "service_type": db_config.service_type,
        "api_base_url": db_config.api_base_url,
        "api_key": db_config.api_key,
        "model": db_config.model,
        "ollama_base_url": db_config.ollama_base_url,
        "ollama_model": db_config.ollama_model,
        "timeout": db_config.timeout,
        "enabled": db_config.enabled,
    })

    upload_dir = get_upload_dir(type)

    # 查找文件并确定类型
    file_path = None
    file_ext = None
    for ext in ["pdf", "doc", "docx", "jpg", "jpeg", "png"]:
        filepath = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(filepath):
            file_path = filepath
            file_ext = ext
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        # 根据类型调用不同的解析方法
        if type == "contract":
            result = await ai_service.parse_contract(file_path, file_ext)
        elif type == "invoice":
            result = await ai_service.parse_invoice(file_path, file_ext)
        else:
            raise HTTPException(status_code=400, detail="不支持的文档类型")

        # 打印 AI 返回的原始结果（用于调试）
        print(f"[DEBUG] AI 解析结果：{result}")

        return result

    except Exception as e:
        print(f"[DEBUG] AI 解析失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"AI 解析失败：{str(e)}")


@router.post("/parse-invoice-qr")
async def parse_invoice_by_qr(
    request_data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    通过识别二维码解析发票信息
    - file_id: 文件 ID
    支持图片格式（jpg, jpeg, png）和 PDF 格式

    说明：二维码本身不包含税率信息，如需税率请同时调用 OCR API
    """
    file_id = request_data.get("file_id")
    if not file_id:
        raise HTTPException(status_code=400, detail="file_id 是必需的")

    upload_dir = get_upload_dir("invoice")

    # 查找文件（支持图片和 PDF）
    file_path = None
    file_ext = None
    for ext in ["jpg", "jpeg", "png", "pdf"]:
        filepath = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(filepath):
            file_path = filepath
            file_ext = ext
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        print(f"[QR API] 开始识别二维码，file_id={file_id}, ext={file_ext}")

        # 使用二维码识别（自动处理 PDF 转换）
        qr_result = recognize_invoice_from_qr(file_path, file_ext)

        print(f"[QR API] === 二维码识别结果 ===")
        print(f"[QR API] success: {qr_result.get('success')}")
        if qr_result.get('data'):
            for key, value in qr_result['data'].items():
                print(f"[QR API]   {key}: {value}")
        print(f"[QR API] ==========================")

        if qr_result['success']:
            # 如果 QR 识别返回了税率，直接返回
            if qr_result.get('data', {}).get('tax_rate'):
                print(f"[QR API] QR 已返回税率，直接返回")
                return qr_result

            # QR 没有税率信息，尝试用 OCR 补充
            print(f"[QR API] QR 未返回税率，尝试用 OCR 补充...")
            try:
                from app.services.invoice_ocr import InvoiceOCR
                ocr = InvoiceOCR()

                if ocr.is_available():
                    # PDF 转图片（如果需要）
                    image_path = None
                    temp_created = False
                    if file_ext == "pdf":
                        import pypdfium2 as pdfium
                        import tempfile
                        pdf = pdfium.PdfDocument(file_path)
                        page = pdf[0]
                        bitmap = page.render(scale=200/72)
                        temp_dir = tempfile.mkdtemp()
                        image_path = os.path.join(temp_dir, 'page_1.png')
                        bitmap.to_pil().save(image_path, 'PNG')
                        pdf.close()
                        temp_created = True
                    else:
                        image_path = file_path

                    # OCR 识别税率
                    ocr_result = ocr.extract_invoice_fields(image_path)
                    print(f"[QR API] OCR 识别结果：tax_rate={ocr_result.get('data', {}).get('tax_rate')}")

                    # 如果 OCR 识别到税率，合并到 QR 结果
                    if ocr_result.get('success') and ocr_result.get('data', {}).get('tax_rate'):
                        tax_rate = ocr_result['data']['tax_rate']
                        # 将税率从百分比转换为小数（如 13 -> 0.13）
                        if tax_rate > 1:
                            tax_rate = tax_rate / 100

                        # 计算不含税金额和税额
                        total_amount = qr_result['data'].get('total_amount')
                        if total_amount:
                            # total_amount = amount * (1 + tax_rate)
                            # amount = total_amount / (1 + tax_rate)
                            amount = round(total_amount / (1 + tax_rate), 2)
                            tax_amount = round(total_amount - amount, 2)

                            qr_result['data']['tax_rate'] = tax_rate
                            qr_result['data']['amount'] = amount
                            qr_result['data']['tax_amount'] = tax_amount
                            print(f"[QR API] 合并 OCR 税率：tax_rate={tax_rate}, amount={amount}, tax_amount={tax_amount}")

                    # 清理临时文件
                    if temp_created and image_path:
                        import shutil
                        shutil.rmtree(os.path.dirname(image_path), ignore_errors=True)

            except Exception as e:
                print(f"[QR API] OCR 补充失败：{e}")
                # 不影响 QR 结果，继续返回

            print(f"[QR API] 识别成功")
            return qr_result
        else:
            print(f"[QR API] 识别失败：{qr_result.get('error')}")
            raise HTTPException(status_code=400, detail=qr_result['error'])

    except HTTPException:
        raise
    except Exception as e:
        print(f"[QR API] 识别异常：{str(e)}")
        raise HTTPException(status_code=500, detail=f"二维码识别失败：{str(e)}")


@router.post("/parse-invoice-ocr")
async def parse_invoice_by_ocr(
    request_data: dict,
    current_user: User = Depends(get_current_user),
):
    """
    通过 OCR 识别发票购买方/销售方信息
    - file_id: 文件 ID
    支持图片格式（jpg, jpeg, png）和 PDF 格式
    """
    file_id = request_data.get("file_id")
    if not file_id:
        raise HTTPException(status_code=400, detail="file_id 是必需的")

    upload_dir = get_upload_dir("invoice")

    # 查找文件（支持图片和 PDF）
    file_path = None
    file_ext = None
    for ext in ["jpg", "jpeg", "png", "pdf"]:
        filepath = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(filepath):
            file_path = filepath
            file_ext = ext
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        print(f"[OCR API] 开始 OCR 识别，file_id={file_id}, ext={file_ext}")

        # OCR 识别
        ocr = InvoiceOCR()

        if not ocr.is_available():
            print(f"[OCR API] OCR 服务未启用")
            raise HTTPException(status_code=503, detail="OCR 服务未启用，请先安装：pip install rapidocr_onnxruntime")

        # PDF 转图片
        image_path = None
        if file_ext == "pdf":
            try:
                import pypdfium2 as pdfium
                import tempfile

                pdf = pdfium.PdfDocument(file_path)
                page = pdf[0]
                bitmap = page.render(scale=200/72)

                # 保存到临时文件
                temp_dir = tempfile.mkdtemp()
                image_path = os.path.join(temp_dir, 'page_1.png')
                bitmap.to_pil().save(image_path, 'PNG')
                pdf.close()
                print(f"[OCR API] PDF 转换完成：{image_path}")
            except Exception as e:
                print(f"[OCR API] PDF 转换失败：{str(e)}")
                raise HTTPException(status_code=500, detail=f"PDF 转换失败：{str(e)}")
        else:
            image_path = file_path
            print(f"[OCR API] 直接使用图片：{image_path}")

        try:
            # OCR 识别 - 先提取原始文本
            print(f"[OCR API] === 开始 OCR 识别 ===")
            ocr_result = ocr.extract_text_with_position(image_path)

            if ocr_result:
                print(f"[OCR API] 识别到 {len(ocr_result)} 个文本块：")
                for i, (box, text, conf) in enumerate(ocr_result[:30]):  # 只打印前 30 个
                    print(f"[OCR API]   [{i+1}] {text} (置信度：{conf:.2f})")
                if len(ocr_result) > 30:
                    print(f"[OCR API]   ... 还有 {len(ocr_result) - 30} 个文本块")

            # 提取发票字段
            result = ocr.extract_invoice_fields(image_path)

            print(f"[OCR API] === OCR 识别结果 ===")
            print(f"[OCR API] success: {result.get('success')}")
            print(f"[OCR API] error: {result.get('error')}")
            print(f"[OCR API] data 内容:")
            data = result.get('data', {})
            for key, value in data.items():
                print(f"[OCR API]   {key}: {value}")
            print(f"[OCR API] ========================")

            if result['success']:
                print(f"[OCR API] 识别成功")
                # 添加置信度字段
                result['confidence'] = 0.85  # OCR 默认置信度
                return result
            else:
                print(f"[OCR API] 识别失败：{result.get('error')}")
                raise HTTPException(status_code=400, detail=result['error'])

        finally:
            # 清理临时文件
            if image_path and file_ext == "pdf":
                import shutil
                shutil.rmtree(os.path.dirname(image_path), ignore_errors=True)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[OCR API] 识别异常：{str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR 识别失败：{str(e)}")


@router.get("/{file_id}/info")
async def get_document_info(
    file_id: str,
    type: str = "contract",
    current_user: User = Depends(get_current_user),
):
    """获取文档信息"""
    upload_dir = get_upload_dir(type)

    # 查找文件
    for ext in ["pdf", "doc", "docx", "jpg", "jpeg", "png"]:
        filepath = os.path.join(upload_dir, f"{file_id}.{ext}")
        if os.path.exists(filepath):
            return {
                "file_id": file_id,
                "file_url": f"/uploads/{type}s/{file_id}.{ext}",
                "exists": True,
            }

    return {
        "file_id": file_id,
        "exists": False,
    }


@router.get("/ai-service/status")
async def get_ai_service_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 AI 服务状态（从数据库读取，不实时检查）"""
    # 从数据库加载配置
    result = await db.execute(select(AIConfig).limit(1))
    db_config = result.scalar_one_or_none()

    if not db_config:
        return {
            "enabled": False,
            "available": False,
            "health_status": "unknown",
            "last_health_check": None,
        }

    # 从数据库加载配置到内存
    ai_service.load_config_from_db({
        "service_type": db_config.service_type,
        "api_base_url": db_config.api_base_url,
        "api_key": db_config.api_key,
        "model": db_config.model,
        "ollama_base_url": db_config.ollama_base_url,
        "ollama_model": db_config.ollama_model,
        "timeout": db_config.timeout,
        "enabled": db_config.enabled,
    })

    config = ai_service.get_config()
    return {
        "enabled": db_config.enabled,
        "health_status": db_config.health_status or "unknown",
        "last_health_check": db_config.last_health_check.isoformat() if db_config.last_health_check else None,
        "service_type": config["service_type"],
        "api_base_url": config["api_base_url"],
        "model": config["model"],
        "has_api_key": bool(config.get("api_key")),
    }


@router.post("/ai-service/config")
async def save_ai_config(
    config: dict = Body(..., description="AI 配置"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    保存 AI 服务配置
    - service_type: 服务类型 (openai_compatible | ollama)
    - api_base_url: API 基础 URL
    - api_key: API Key（如果传空字符串且已有配置，则保留原值）
    - model: 模型名称
    - enabled: 是否启用
    """
    try:
        # 查找现有配置
        result = await db.execute(select(AIConfig).limit(1))
        db_config = result.scalar_one_or_none()

        # 获取配置值
        api_key = config.get("api_key", "")
        api_base_url = config.get("api_base_url", "")

        # 如果有现有配置，允许空 API Key 和空 API Base URL（表示保留原值）
        if db_config:
            # 保留原值
            if not api_key:
                api_key = db_config.api_key
            if not api_base_url:
                api_base_url = db_config.api_base_url
        else:
            # 新配置，必须填写
            if config.get("service_type") == "openai_compatible":
                if not api_base_url or not api_key:
                    raise HTTPException(status_code=400, detail="API 地址和 API Key 不能为空")

        if db_config:
            # 更新现有配置
            db_config.service_type = config.get("service_type", "openai_compatible")
            db_config.api_base_url = api_base_url
            db_config.api_key = api_key
            db_config.model = config.get("model", "qwen-vl-plus")
            db_config.enabled = config.get("enabled", True)
        else:
            # 创建新配置
            db_config = AIConfig(
                id=str(uuid.uuid4()),
                service_type=config.get("service_type", "openai_compatible"),
                api_base_url=api_base_url,
                api_key=api_key,
                model=config.get("model", "qwen-vl-plus"),
                enabled=config.get("enabled", True),
            )
            db.add(db_config)

        # 加载配置到内存
        ai_service.load_config_from_db({
            "service_type": db_config.service_type,
            "api_base_url": db_config.api_base_url,
            "api_key": db_config.api_key,
            "model": db_config.model,
            "ollama_base_url": db_config.ollama_base_url,
            "ollama_model": db_config.ollama_model,
            "timeout": db_config.timeout,
            "enabled": db_config.enabled,
        })

        # 检查新配置是否可用
        is_available = await ai_service.check_health()

        # 更新健康状态到数据库
        db_config.health_status = "healthy" if is_available else "unhealthy"
        db_config.last_health_check = datetime.now()

        # 显式提交
        await db.commit()
        await db.refresh(db_config)

        return {
            "success": True,
            "config": ai_service.get_config(),
            "health_status": db_config.health_status,
            "last_health_check": db_config.last_health_check.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"配置保存失败：{str(e)}")
