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

    # 特殊迁移：将 customers 表的旧联系人字段迁移到 customer_contacts 表
    _migrate_customer_contacts(db_path)

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


def _migrate_customer_contacts(db_path):
    """将 customers 表上的旧 contact/phone/email 列迁移到 customer_contacts 表"""
    import sqlite3
    import uuid

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查旧列是否存在
    cursor.execute("PRAGMA table_info(customers)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    conn.close()

    if "contact" not in existing_cols:
        return  # 已迁移过，跳过

    print("[MIGRATE] Moving customer contact fields to customer_contacts table...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建 customer_contacts 表（如果不存在）
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_contacts'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE customer_contacts (
                id VARCHAR(36) PRIMARY KEY,
                customer_id VARCHAR(36) NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(100),
                position VARCHAR(100),
                is_primary BOOLEAN DEFAULT 0,
                remark TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # 迁移数据
    cursor.execute("SELECT id, name, contact, phone, email FROM customers WHERE contact IS NOT NULL AND contact != ''")
    rows = cursor.fetchall()
    for row in rows:
        customer_id, customer_name, contact, phone, email = row
        contact_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO customer_contacts (id, customer_id, name, phone, email, is_primary) VALUES (?, ?, ?, ?, ?, 1)",
            (contact_id, customer_id, contact, phone, email)
        )
    migrated = len(rows)

    # 为没有联系人的客户自动创建默认联系人
    cursor.execute("""
        SELECT c.id, c.name, c.phone, c.email FROM customers c
        WHERE NOT EXISTS (SELECT 1 FROM customer_contacts cc WHERE cc.customer_id = c.id)
    """)
    no_contact_rows = cursor.fetchall()
    auto_created = 0
    for row in no_contact_rows:
        customer_id, customer_name, phone, email = row
        contact_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO customer_contacts (id, customer_id, name, phone, email, is_primary) VALUES (?, ?, ?, ?, ?, 1)",
            (contact_id, customer_id, customer_name, phone or '', email or '')
        )
        auto_created += 1

    conn.commit()

    # 删除旧列（SQLite 需要重建表）
    cursor.execute("PRAGMA table_info(customers)")
    all_cols = cursor.fetchall()
    keep_cols = [(c[1], c[2], c[3], c[4]) for c in all_cols if c[1] not in ("contact", "phone", "email")]
    col_names = [c[0] for c in keep_cols]
    col_defs = ", ".join(
        f"{c[0]} {c[1]}" + (" NOT NULL" if c[2] else "") + (f" DEFAULT {c[3]}" if c[3] is not None else "")
        for c in keep_cols
    )

    cursor.execute("ALTER TABLE customers RENAME TO customers_old")
    cursor.execute(f"CREATE TABLE customers ({col_defs})")
    cursor.execute(f"INSERT INTO customers ({', '.join(col_names)}) SELECT {', '.join(col_names)} FROM customers_old")
    cursor.execute("DROP TABLE customers_old")
    conn.commit()
    conn.close()

    print(f"[MIGRATE] Migrated {migrated} contacts, auto-created {auto_created} defaults")


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
