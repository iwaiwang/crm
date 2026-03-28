"""系统设置 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
import json
import os

from app.database import DATA_DIR, get_db
from app.models.setting import Setting
from app.models.user import User
from app.schemas.setting import (
    SettingCreate,
    SettingUpdate,
    SettingResponse,
    SettingListResponse,
    SettingKeys,
)
from app.api.auth import require_menu_permission
from app.config import settings

router = APIRouter()


def _get_database_directory() -> str:
    return os.path.abspath(DATA_DIR)


def _get_upload_directory() -> str:
    return os.path.abspath(settings.UPLOAD_DIR)


# 预定义设置项的默认值
DEFAULT_SETTINGS = {
    SettingKeys.COMPANY_NAME: {"value": "", "value_type": "string", "description": "公司名称", "is_public": True},
    SettingKeys.COMPANY_TAX_ID: {"value": "", "value_type": "string", "description": "公司税号", "is_public": True},
    SettingKeys.COMPANY_BANK_ACCOUNT: {"value": "", "value_type": "string", "description": "公司银行账号", "is_public": True},
    SettingKeys.COMPANY_ADDRESS: {"value": "", "value_type": "string", "description": "公司地址", "is_public": True},
    SettingKeys.COMPANY_PHONE: {"value": "", "value_type": "string", "description": "公司电话", "is_public": True},
    SettingKeys.COMPANY_EMAIL: {"value": "", "value_type": "string", "description": "公司邮箱", "is_public": True},
    SettingKeys.DATABASE_DIRECTORY: {"value": _get_database_directory(), "value_type": "string", "description": "数据库目录", "is_public": False},
    SettingKeys.UPLOAD_DIRECTORY: {"value": _get_upload_directory(), "value_type": "string", "description": "文件上传目录", "is_public": False},
    SettingKeys.OCR_ENABLED: {"value": "true", "value_type": "boolean", "description": "是否启用 OCR 功能", "is_public": False},
    SettingKeys.AI_ENABLED: {"value": "true", "value_type": "boolean", "description": "是否启用 AI 功能", "is_public": False},
}


async def init_default_settings(db: AsyncSession):
    """初始化默认设置项"""
    for key, config in DEFAULT_SETTINGS.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        db_setting = result.scalar_one_or_none()
        if not db_setting:
            db_setting = Setting(key=key, **config)
            db.add(db_setting)
        elif key in {SettingKeys.DATABASE_DIRECTORY, SettingKeys.UPLOAD_DIRECTORY} and not (db_setting.value or "").strip():
            db_setting.value = config["value"]
    await db.commit()


@router.get("", response_model=SettingListResponse)
async def get_settings(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('settings')),
):
    """获取设置列表"""
    # 构建基础查询
    query = select(Setting)

    if search:
        query = query.where(
            (Setting.key.contains(search)) | (Setting.description.contains(search))
        )

    if is_public is not None:
        query = query.where(Setting.is_public == is_public)

    # 获取总数
    count_query = select(func.count()).select_from(Setting)
    if search:
        count_query = count_query.where(
            (Setting.key.contains(search)) | (Setting.description.contains(search))
        )
    if is_public is not None:
        count_query = count_query.where(Setting.is_public == is_public)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 获取分页数据
    query = query.order_by(Setting.key)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    settings = result.scalars().all()

    return SettingListResponse(
        total=total,
        items=[SettingResponse.model_validate(s) for s in settings]
    )


@router.get("/public", response_model=SettingListResponse)
async def get_public_settings(
    db: AsyncSession = Depends(get_db),
):
    """获取公开设置（无需认证）"""
    result = await db.execute(select(Setting).where(Setting.is_public == True))
    settings = result.scalars().all()

    return SettingListResponse(
        total=len(settings),
        items=[SettingResponse.model_validate(s) for s in settings]
    )


@router.get("/{setting_key}", response_model=SettingResponse)
async def get_setting(setting_key: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('settings'))):
    """获取单个设置详情"""
    result = await db.execute(select(Setting).where(Setting.key == setting_key))
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail="设置项不存在")

    return SettingResponse.model_validate(setting)


@router.post("", response_model=SettingResponse)
async def create_setting(setting: SettingCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('settings'))):
    """创建设置项"""
    # 检查设置项是否已存在
    result = await db.execute(select(Setting).where(Setting.key == setting.key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="设置项已存在")

    db_setting = Setting(**setting.model_dump())
    db.add(db_setting)
    await db.commit()
    await db.refresh(db_setting)

    return SettingResponse.model_validate(db_setting)


@router.put("/{setting_key}", response_model=SettingResponse)
async def update_setting(setting_key: str, setting: SettingUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('settings'))):
    """更新设置项"""
    result = await db.execute(select(Setting).where(Setting.key == setting_key))
    db_setting = result.scalar_one_or_none()

    if not db_setting:
        raise HTTPException(status_code=404, detail="设置项不存在")

    update_data = setting.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_setting, field, value)

    await db.commit()
    await db.refresh(db_setting)

    return SettingResponse.model_validate(db_setting)


@router.delete("/{setting_key}")
async def delete_setting(setting_key: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('settings'))):
    """删除设置项"""
    result = await db.execute(select(Setting).where(Setting.key == setting_key))
    db_setting = result.scalar_one_or_none()

    if not db_setting:
        raise HTTPException(status_code=404, detail="设置项不存在")

    # 禁止删除预定义设置项
    if setting_key in DEFAULT_SETTINGS:
        raise HTTPException(status_code=400, detail="预定义设置项不可删除")

    await db.delete(db_setting)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/company/info", response_model=dict)
async def get_company_info(db: AsyncSession = Depends(get_db)):
    """获取公司信息（公开接口，无需认证）"""
    result = await db.execute(
        select(Setting).where(
            Setting.key.in_(
                [
                    SettingKeys.COMPANY_NAME,
                    SettingKeys.COMPANY_TAX_ID,
                    SettingKeys.COMPANY_BANK_ACCOUNT,
                    SettingKeys.COMPANY_ADDRESS,
                    SettingKeys.COMPANY_PHONE,
                    SettingKeys.COMPANY_EMAIL,
                ]
            )
        )
    )
    settings = result.scalars().all()

    company_info = {}
    for setting in settings:
        company_info[setting.key] = setting.value

    return company_info


@router.post("/init", response_model=dict)
async def init_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_menu_permission('settings'))):
    """初始化默认设置项"""
    await init_default_settings(db)
    return {"message": "设置项初始化成功"}


@router.get("/system/upload-dir", response_model=dict)
@router.get("/meta/upload-dir", response_model=dict)
async def get_upload_directory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('settings')),
):
    """获取实际的文件上传目录"""
    return {
        "database_directory": _get_database_directory(),
        "upload_directory": _get_upload_directory(),
        "avatars_directory": os.path.join(_get_upload_directory(), "avatars"),
        "contracts_directory": os.path.join(_get_upload_directory(), "contracts"),
        "invoices_directory": os.path.join(_get_upload_directory(), "invoices"),
    }


@router.post("/cleanup-files", response_model=dict)
async def cleanup_unused_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_menu_permission('settings')),
):
    """清理未使用的上传文件"""
    from app.models.contract_file import ContractFile

    upload_dir = settings.UPLOAD_DIR
    avatars_dir = os.path.join(upload_dir, "avatars")
    contracts_dir = os.path.join(upload_dir, "contracts")

    deleted_count = 0
    deleted_size = 0

    # 清理头像文件
    if os.path.exists(avatars_dir):
        # 获取所有用户头像
        result = await db.execute(select(User.avatar).where(User.avatar.isnot(None)))
        user_avatars = [r[0] for r in result.all() if r[0]]
        used_avatar_files = set()
        for avatar in user_avatars:
            if avatar.startswith("/uploads/avatars/"):
                used_avatar_files.add(avatar.replace("/uploads/avatars/", ""))

        # 删除未使用的头像
        for filename in os.listdir(avatars_dir):
            if filename not in used_avatar_files:
                filepath = os.path.join(avatars_dir, filename)
                if os.path.isfile(filepath):
                    deleted_size += os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1

    # 清理合同文件
    if os.path.exists(contracts_dir):
        result = await db.execute(select(ContractFile.file_url).where(ContractFile.file_url.isnot(None)))
        contract_urls = [r[0] for r in result.all() if r[0]]
        used_contract_files = set()
        for url in contract_urls:
            if url.startswith("/uploads/contracts/"):
                used_contract_files.add(url.replace("/uploads/contracts/", ""))

        for filename in os.listdir(contracts_dir):
            if filename not in used_contract_files:
                filepath = os.path.join(contracts_dir, filename)
                if os.path.isfile(filepath):
                    deleted_size += os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1

    # 注意：不清理发票文件，因为发票可以不关联合同独立存在

    return {
        "message": "清理完成",
        "deleted_count": deleted_count,
        "deleted_size": deleted_size,
    }
