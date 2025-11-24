# Database config and session management
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/postgres")

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session
