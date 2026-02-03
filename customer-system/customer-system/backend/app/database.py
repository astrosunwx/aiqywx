from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
import redis

# 默认使用 SQLite，生产环境使用 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./customer_system.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# 初始化 Redis 客户端（可选，用于缓存和消息追踪）
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    print("✅ Redis 连接成功")
except Exception as e:
    print(f"⚠️  Redis连接失败，缓存功能不可用: {e}")
    redis_client = None

async def get_db():
    async with async_session_maker() as session:
        yield session
