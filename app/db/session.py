# Database config and session management
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# read postgres creds from env
_pg_user = os.getenv("POSTGRES_USER", "app_user")
_pg_password = os.getenv("POSTGRES_PASSWORD", "app_password")
_pg_db = os.getenv("POSTGRES_DB", "app_db")
_pg_host = os.getenv("POSTGRES_HOST", "db")
_pg_port = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{_pg_user}:{_pg_password}@{_pg_host}:{_pg_port}/{_pg_db}",
)

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
