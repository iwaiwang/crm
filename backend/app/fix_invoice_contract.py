"""修复 invoice 表 contract_id 字段的 NOT NULL 约束"""
import sqlite3

db_path = 'd:/工作/007-project/claude-code-test/crm-system/data/crm.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 启用外键
cursor.execute("PRAGMA foreign_keys = ON;")

# 1. 重命名旧表
cursor.execute("ALTER TABLE invoices RENAME TO invoices_old")

# 2. 创建新表（contract_id 允许 NULL）
cursor.execute("""
CREATE TABLE invoices (
    id VARCHAR(36) PRIMARY KEY,
    invoice_code VARCHAR(20),
    invoice_number VARCHAR(20),
    check_code VARCHAR(20),
    invoice_date DATE,
    invoice_no VARCHAR(50) UNIQUE,
    contract_id VARCHAR(36) REFERENCES contracts(id) ON DELETE SET NULL,
    amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2),
    total_amount DECIMAL(15, 2),
    type VARCHAR(7) DEFAULT 'normal',
    issue_date DATE,
    due_date DATE,
    status VARCHAR(8) DEFAULT 'pending',
    file_id VARCHAR(36),
    file_url TEXT,
    ai_parsed INTEGER DEFAULT 0,
    parsed_at DATETIME,
    parse_confidence REAL,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 3. 复制数据（不包括 contract_id 为 NULL 的行，如果有的话）
cursor.execute("""
INSERT INTO invoices SELECT * FROM invoices_old
""")

# 4. 删除旧表
cursor.execute("DROP TABLE invoices_old")

conn.commit()
conn.close()

print("迁移完成！contract_id 现在允许 NULL 值")
