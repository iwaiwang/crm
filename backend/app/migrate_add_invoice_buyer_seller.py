"""添加发票购买方和销售方字段的迁移脚本"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.database import async_session_maker


async def migrate():
    async with async_session_maker() as session:
        # 添加购买方和销售方字段 (SQLite 不支持 COMMENT)
        await session.execute(text("""
            ALTER TABLE invoices ADD COLUMN buyer_name VARCHAR(200)
        """))
        await session.execute(text("""
            ALTER TABLE invoices ADD COLUMN buyer_tax_id VARCHAR(50)
        """))
        await session.execute(text("""
            ALTER TABLE invoices ADD COLUMN seller_name VARCHAR(200)
        """))
        await session.execute(text("""
            ALTER TABLE invoices ADD COLUMN seller_tax_id VARCHAR(50)
        """))

        await session.commit()
        print("迁移完成：已添加 buyer_name, buyer_tax_id, seller_name, seller_tax_id 字段")


if __name__ == "__main__":
    asyncio.run(migrate())
