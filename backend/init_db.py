"""
数据库初始化脚本
创建默认管理员账号：admin / admin123
"""
import asyncio
import sys
import os

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 确保 data 目录存在
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'crm.db')}"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.utils.auth import get_password_hash


async def init():
    # 创建数据库引擎
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 创建表
    from app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建默认管理员
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            print("[OK] 默认管理员账号已创建：admin / admin123")
        else:
            print("[INFO] 管理员账号已存在")

    await engine.dispose()
    print("[OK] 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init())
