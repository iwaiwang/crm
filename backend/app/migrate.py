"""数据库迁移脚本 - 添加用户新字段"""
import asyncio
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR.parent / "data" / "crm.db"

async def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查并添加 avatar 字段
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT ''")
        print("[OK] 添加 avatar 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] avatar 字段已存在")
        else:
            raise

    # 检查并添加 menu_permissions 字段
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN menu_permissions TEXT DEFAULT '[]'")
        print("[OK] 添加 menu_permissions 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] menu_permissions 字段已存在")
        else:
            raise

    # 检查并添加 updated_at 字段
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
        print("[OK] 添加 updated_at 字段")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[SKIP] updated_at 字段已存在")
        else:
            raise

    # 更新 admin 用户的 menu_permissions 为所有菜单
    cursor.execute("""
        UPDATE users
        SET menu_permissions = '["dashboard","customers","contracts","invoices","receivables","products","projects"]'
        WHERE username = 'admin' AND (menu_permissions IS NULL OR menu_permissions = '[]')
    """)
    if cursor.rowcount > 0:
        print(f"[OK] 更新 admin 用户菜单权限：{cursor.rowcount} 行")

    conn.commit()
    conn.close()
    print("迁移完成!")

if __name__ == "__main__":
    asyncio.run(migrate())
