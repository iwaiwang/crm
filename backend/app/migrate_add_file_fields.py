"""
迁移脚本：添加文件上传和 AI 解析相关字段
- contracts 表：file_id, file_url, ai_parsed, parsed_at, parse_confidence
- invoices 表：file_id, file_url, ai_parsed, parsed_at, parse_confidence, invoice_code, invoice_number, check_code
"""
import sqlite3
import os

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "crm.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在：{DB_PATH}")
        print("请先启动应用初始化数据库")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("开始迁移 contracts 表...")

    # contracts 表新增字段
    try:
        cursor.execute("ALTER TABLE contracts ADD COLUMN file_id TEXT")
        cursor.execute("ALTER TABLE contracts ADD COLUMN file_url TEXT")
        cursor.execute("ALTER TABLE contracts ADD COLUMN ai_parsed INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE contracts ADD COLUMN parsed_at DATETIME")
        cursor.execute("ALTER TABLE contracts ADD COLUMN parse_confidence REAL")
        print("contracts 表迁移完成")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("contracts 表字段已存在，跳过")
        else:
            raise

    print("开始迁移 invoices 表...")

    # invoices 表新增字段
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_code TEXT")
        cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_number TEXT")
        cursor.execute("ALTER TABLE invoices ADD COLUMN check_code TEXT")
        cursor.execute("ALTER TABLE invoices ADD COLUMN file_id TEXT")
        cursor.execute("ALTER TABLE invoices ADD COLUMN file_url TEXT")
        cursor.execute("ALTER TABLE invoices ADD COLUMN ai_parsed INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE invoices ADD COLUMN parsed_at DATETIME")
        cursor.execute("ALTER TABLE invoices ADD COLUMN parse_confidence REAL")
        print("invoices 表迁移完成")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("invoices 表字段已存在，跳过")
        else:
            raise

    conn.commit()
    conn.close()

    print("所有迁移完成！")


if __name__ == "__main__":
    migrate()
