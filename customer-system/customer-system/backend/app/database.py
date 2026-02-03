from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
import redis

# 默认使用 SQLite，生产环境使用 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./customer_system.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Initialize Redis client (optional, for caching and message tracking)
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    print("Redis connection successful")
except Exception as e:
    print(f"Redis connection failed, caching unavailable: {e}")
    redis_client = None

async def get_db():
    async with async_session_maker() as session:
        yield session
