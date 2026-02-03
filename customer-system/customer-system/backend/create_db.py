"""
创建数据库表
"""
import asyncio
from app.database import engine, Base
from app import models, models_config, models_messaging


async def create_tables():
    """创建所有数据库表"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建完成！")


if __name__ == "__main__":
    asyncio.run(create_tables())
