"""迁移脚本：更新发票状态枚举值

恢复完整的发票状态：pending, issued, sent, received, normal, void
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "crm.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查旧表是否已存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices_old'")
    if cursor.fetchone():
        print("发现备份表 invoices_old，先删除...")
        cursor.execute("DROP TABLE invoices_old")

    # 1. 重命名旧表
    cursor.execute("ALTER TABLE invoices RENAME TO invoices_old")
    print("已重命名旧表为 invoices_old")

    # 2. 创建新表（使用完整的 ENUM 值）
    cursor.execute("""
    CREATE TABLE invoices (
        id VARCHAR(36) PRIMARY KEY,
        invoice_code VARCHAR(20),
        invoice_number VARCHAR(20),
        check_code VARCHAR(20),
        invoice_date DATE,
        invoice_no VARCHAR(50) UNIQUE,
        contract_id VARCHAR(36) REFERENCES contracts(id),
        amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        tax_amount DECIMAL(15, 2),
        total_amount DECIMAL(15, 2),
        type VARCHAR(20) DEFAULT 'normal',
        buyer_name VARCHAR(200),
        buyer_tax_id VARCHAR(50),
        seller_name VARCHAR(200),
        seller_tax_id VARCHAR(50),
        issue_date DATE,
        due_date DATE,
        status VARCHAR(20) DEFAULT 'pending',
        file_id VARCHAR(36),
        file_url VARCHAR(500),
        ai_parsed BOOLEAN DEFAULT 0,
        parsed_at DATETIME,
        parse_confidence FLOAT,
        remark TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("已创建新表 invoices")

    # 3. 复制数据（保留原有状态值）
    cursor.execute("""
    INSERT INTO invoices (
        id, invoice_code, invoice_number, check_code, invoice_date, invoice_no,
        contract_id, amount, tax_rate, tax_amount, total_amount, type,
        buyer_name, buyer_tax_id, seller_name, seller_tax_id, issue_date, due_date,
        status, file_id, file_url, ai_parsed, parsed_at, parse_confidence, remark,
        created_at, updated_at
    )
    SELECT
        id, invoice_code, invoice_number, check_code, invoice_date, invoice_no,
        contract_id, amount, tax_rate, tax_amount, total_amount, type,
        buyer_name, buyer_tax_id, seller_name, seller_tax_id, issue_date, due_date,
        status, file_id, file_url, ai_parsed, parsed_at, parse_confidence, remark,
        created_at, updated_at
    FROM invoices_old
    """)
    print("已复制数据")

    # 4. 删除旧表
    cursor.execute("DROP TABLE invoices_old")
    print("已删除旧表")

    conn.commit()
    conn.close()
    print("\n迁移完成！发票状态：pending, issued, sent, received, normal, void")

if __name__ == "__main__":
    migrate()
