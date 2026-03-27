"""用户管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import json
import os
import uuid

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.utils.auth import get_password_hash, verify_password
from app.config import settings
from jose import jwt

router = APIRouter()


async def get_current_user_id(
    authorization: str = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="无效的令牌")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user_id),
) -> User:
    """验证是否为管理员"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("", response_model=List[UserResponse])
async def get_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有用户列表（管理员）"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse)
async def create_user(
    username: str = Body(...),
    password: str = Body(...),
    email: Optional[str] = Body(None),
    role: Optional[str] = Body("user"),
    is_active: Optional[bool] = Body(True),
    menu_permissions: Optional[List[str]] = Body(None),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建用户（管理员）"""
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    db_user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        is_active=is_active,
        menu_permissions=json.dumps(menu_permissions or []),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    username: Optional[str] = None,
    email: Optional[str] = None,
    avatar: Optional[str] = None,
    authorization: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """更新个人信息"""
    # 更新字段
    if username and username != current_user.username:
        exist_result = await db.execute(select(User).where(User.username == username))
        if exist_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        current_user.username = username

    if email and email != current_user.email:
        current_user.email = email

    if avatar is not None:
        current_user.avatar = avatar

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """上传头像"""
    # 创建上传目录
    upload_dir = os.path.join(os.getcwd(), "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    # 保存文件
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    # 更新用户头像
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar = avatar_url
    await db.commit()

    return {"avatar": avatar_url}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    authorization: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    # 更新密码
    current_user.password_hash = get_password_hash(new_password)
    await db.commit()

    return {"message": "密码修改成功"}


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user_data.username and user_data.username != user.username:
        exist_result = await db.execute(select(User).where(User.username == user_data.username))
        if exist_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = user_data.username

    if user_data.email and user_data.email != user.email:
        user.email = user_data.email

    if user_data.role:
        user.role = user_data.role

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    if user_data.menu_permissions is not None:
        user.menu_permissions = json.dumps(user_data.menu_permissions)

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除用户（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")

    await db.delete(user)
    await db.commit()

    return {"message": "删除成功"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    new_password: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = get_password_hash(new_password)
    await db.commit()

    return {"message": "密码重置成功"}
