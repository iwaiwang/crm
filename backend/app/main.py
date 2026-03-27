"""
小微企业 CRM 系统
"""
import os
import sys

# 设置 Python 默认编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import init_db, async_session_maker
from app.models import contract_attachment  # 在导入其他 API 之前先导入附件模型
from app.api import customers, contracts, invoices, receivables, products, projects, auth, dashboard, webhooks, document, incomes, expenses, settings as settings_api, users
from app.api.settings import init_default_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    print("[OK] Database initialized")

    # 初始化默认设置项
    async with async_session_maker() as db:
        try:
            await init_default_settings(db)
            print("[OK] Default settings initialized")
        except Exception as e:
            print(f"[WARN] Failed to initialize settings: {e}")
        finally:
            await db.close()

    # 创建上传目录 - 使用与 StaticFiles 挂载相同的目录
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(os.path.join(upload_dir, "contracts"), exist_ok=True)
    os.makedirs(os.path.join(upload_dir, "invoices"), exist_ok=True)
    os.makedirs(os.path.join(upload_dir, "avatars"), exist_ok=True)

    yield
    # 关闭时清理
    print("[STOP] Application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="面向小微企业的客户管理系统 - 客户、合同、发票、应收款、产品库存、项目进度管理",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（头像、合同附件等）- 在 routes 之前
upload_dir = settings.UPLOAD_DIR
print(f"[DEBUG] UPLOAD_DIR: {upload_dir}")
print(f"[DEBUG] UPLOAD_DIR exists: {os.path.exists(upload_dir)}")
if os.path.exists(upload_dir):
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
    print(f"[DEBUG] Mounted /uploads at {upload_dir}")
else:
    print(f"[WARN] UPLOAD_DIR does not exist: {upload_dir}")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(document.router, prefix="/api", tags=["文档服务"])
app.include_router(customers.router, prefix="/api/customers", tags=["客户管理"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["合同管理"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["发票管理"])
app.include_router(receivables.router, prefix="/api/receivables", tags=["应收款管理"])
app.include_router(products.router, prefix="/api/products", tags=["产品库存"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目进度"])
app.include_router(incomes.router, prefix="/api/incomes", tags=["收入管理"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["支出管理"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["系统设置"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["数据分析"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhook"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "面向小微企业的客户管理系统",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
