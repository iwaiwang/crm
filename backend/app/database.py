import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# 确保 data 目录存在
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 使用绝对路径的数据库 URL
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'crm.db')}"

# 创建异步数据库引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话依赖"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 自动迁移：添加缺失的列
    await auto_migrate_columns()


async def auto_migrate_columns():
    """自动检测并添加缺失的数据库列"""
    import sqlite3
    from sqlalchemy import inspect

    db_path = os.path.join(DATA_DIR, 'crm.db')

    # 获取所有模型类
    models = Base.registry._class_registry.values()

    for model in models:
        if not hasattr(model, '__tablename__'):
            continue

        table_name = model.__tablename__

        # 获取模型中定义的所有列
        model_columns = {}
        for column in model.__table__.columns:
            model_columns[column.name] = column

        # 获取数据库中现有的列
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        # 添加缺失的列
        for col_name, column in model_columns.items():
            if col_name not in existing_columns:
                col_type = _get_sqlite_type(column.type)
                print(f"[MIGRATE] Adding column {col_name} to {table_name}")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                conn.commit()
                conn.close()


def _get_sqlite_type(col_type):
    """将 SQLAlchemy 类型转换为 SQLite 类型"""
    type_name = str(col_type)
    if 'VARCHAR' in type_name or 'STRING' in type_name:
        size = type_name.split('(')[-1].split(')')[0] if '(' in type_name else '255'
        return f'VARCHAR({size})'
    elif 'INTEGER' in type_name:
        return 'INTEGER'
    elif 'DECIMAL' in type_name or 'FLOAT' in type_name or 'NUMERIC' in type_name:
        return 'DECIMAL(15, 2)'
    elif 'DATE' in type_name:
        return 'DATE'
    elif 'DATETIME' in type_name or 'TIMESTAMP' in type_name:
        return 'DATETIME'
    elif 'TEXT' in type_name:
        return 'TEXT'
    elif 'BOOLEAN' in type_name or 'BOOL' in type_name:
        return 'BOOLEAN'
    elif 'ENUM' in type_name:
        return 'VARCHAR(20)'
    else:
        return 'VARCHAR(255)'
