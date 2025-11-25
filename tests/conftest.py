import os

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text

from app.db.session import DATABASE_URL  # подстрой под свой код
from app.main import app
from app.models.models import Base

# 1) Синхронный engine только для тестов/очистки БД
# Если у тебя URL вида "postgresql+asyncpg://user:pass@host/db":
TEST_DB_URL = DATABASE_URL.replace("+asyncpg", "+psycopg")  # или "+psycopg2"

sync_engine = create_engine(TEST_DB_URL, future=True)


# 2) Один раз создаём таблицы перед всеми тестами
@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)


# 3) Перед КАЖДЫМ тестом чистим все таблицы
@pytest.fixture(autouse=True)
def clear_db():
    """
    Синхронная очистка всех таблиц перед каждым тестом.
    Никаких async/await — значит, нет проблем с event loop.
    """
    with sync_engine.begin() as conn:
        # Вариант A: через DELETE
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

        # Вариант B (быстрее, если много строк) — TRUNCATE:
        # table_names = [table.name for table in Base.metadata.sorted_tables]
        # if table_names:
        #     conn.execute(
        #         text(
        #             "TRUNCATE " +
        #             ", ".join(f'"{name}"' for name in table_names) +
        #             " RESTART IDENTITY CASCADE"
        #         )
        #     )


# 4) Асинхронный httpx-клиент как раньше
@pytest_asyncio.fixture(scope="function")
async def async_client():
    _host = os.getenv("API_HOST", "localhost")
    _port = os.getenv("API_PORT", "8080")
    _api_url = f"http://{_host}:{_port}"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=_api_url,
    ) as client:
        yield client
