"""添加发票 tax_amount 和 total_amount 字段"""
import sqlite3
from pathlib import Path

# 找到数据库文件
db_path = Path(__file__).parent.parent / "data" / "crm.db"
print(f"数据库路径：{db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 检查列是否存在
cursor.execute("PRAGMA table_info(invoices)")
columns = [col[1] for col in cursor.fetchall()]

print(f"当前 invoices 表的列：{columns}")

# 添加 tax_amount 列
if "tax_amount" not in columns:
    cursor.execute("ALTER TABLE invoices ADD COLUMN tax_amount DECIMAL(15, 2)")
    print("已添加 tax_amount 列")
else:
    print("tax_amount 列已存在")

# 添加 total_amount 列
if "total_amount" not in columns:
    cursor.execute("ALTER TABLE invoices ADD COLUMN total_amount DECIMAL(15, 2)")
    print("已添加 total_amount 列")
else:
    print("total_amount 列已存在")

conn.commit()
conn.close()

print("迁移完成！")
