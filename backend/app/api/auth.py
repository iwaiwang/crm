"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import json

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse, LoginResponse, UserResponse,
    TwoFactorSetupResponse, TwoFactorVerifyRequest, TwoFactorDisableRequest,
)
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token,
    generate_totp_secret, verify_totp_code, generate_qr_code_uri, generate_qr_code_base64,
)
from app.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前登录用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
        )

    try:
        from jose import jwt
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的令牌")
    except Exception:
        raise HTTPException(status_code=401, detail="令牌验证失败")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    return user


def require_menu_permission(required_permission: str):
    """创建需要菜单权限的依赖"""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 管理员可以访问所有页面
        if current_user.role == 'admin':
            return current_user

        # 检查用户的菜单权限
        menu_permissions = []
        if current_user.menu_permissions:
            try:
                menu_permissions = json.loads(current_user.menu_permissions)
            except (json.JSONDecodeError, TypeError):
                menu_permissions = []

        if required_permission not in menu_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限访问该资源",
            )

        return current_user
    return permission_checker


def require_any_menu_permission(required_permissions: list):
    """创建需要任意一个菜单权限的依赖"""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 管理员可以访问所有页面
        if current_user.role == 'admin':
            return current_user

        # 检查用户的菜单权限
        menu_permissions = []
        if current_user.menu_permissions:
            try:
                menu_permissions = json.loads(current_user.menu_permissions)
            except (json.JSONDecodeError, TypeError):
                menu_permissions = []

        # 检查是否有任意一个所需权限
        for perm in required_permissions:
            if perm in menu_permissions:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问该资源",
        )

    return permission_checker


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=get_password_hash(user.password),
        role="user",
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 管理员且开启了 2FA：返回临时 token，要求验证
    if user.role == "admin" and user.totp_enabled:
        temp_token = _create_temp_token(user.id, "2fa")
        return LoginResponse(
            require_2fa=True,
            temp_token=temp_token,
        )

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}


# ---- 2FA 辅助函数 ----

def _create_temp_token(user_id: str, scope: str) -> str:
    return create_access_token(
        data={"sub": user_id, "scope": scope},
        expires_delta=timedelta(minutes=5),
    )


def _verify_temp_token(token_str: str, expected_scope: str) -> str:
    """验证临时 token，返回 user_id"""
    from jose import jwt as jose_jwt
    try:
        payload = jose_jwt.decode(
            token_str, settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except Exception:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    if payload.get("scope") != expected_scope:
        raise HTTPException(status_code=401, detail="无效的临时令牌")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的令牌")
    return user_id


# ---- 2FA 端点 ----

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成 TOTP 密钥和二维码"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可设置两步验证")

    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="两步验证已开启，请先关闭后再重新设置")

    secret = generate_totp_secret()
    current_user.totp_secret = secret
    await db.commit()

    qr_uri = generate_qr_code_uri(current_user.username, secret)
    qr_base64 = generate_qr_code_base64(qr_uri)

    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_base64=qr_base64,
        qr_uri=qr_uri,
    )


@router.post("/2fa/verify-setup", response_model=TokenResponse)
async def verify_2fa_setup(
    data: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """验证动态码并启用 2FA"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可设置两步验证")

    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="两步验证已开启")

    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="请先获取两步验证密钥")

    if not verify_totp_code(current_user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="验证码错误，请检查验证器 App 时间是否同步")

    current_user.totp_enabled = True
    await db.commit()

    access_token = create_access_token(
        data={"sub": current_user.id, "username": current_user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(current_user),
    )


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(
    data: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """登录第二步：验证动态码，返回正式 JWT"""
    user_id = _verify_temp_token(data.token, "2fa")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="未设置两步验证")

    if not verify_totp_code(user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="验证码错误")

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/2fa/disable")
async def disable_2fa(
    data: TwoFactorDisableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """关闭两步验证"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="两步验证未开启")

    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="无两步验证密钥")

    if not verify_totp_code(current_user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="验证码错误")

    current_user.totp_secret = None
    current_user.totp_enabled = False
    await db.commit()
    return {"message": "两步验证已关闭"}
