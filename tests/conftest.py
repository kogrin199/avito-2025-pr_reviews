"""
Конфигурация pytest с изолированной тестовой базой данных.

Ключевые принципы:
1. По умолчанию SQLite in-memory для быстрых тестов
2. Поддержка PostgreSQL через переменную TEST_DATABASE_URL
3. Каждый тест получает чистую БД (create_all/drop_all)
4. Корректная работа с asyncpg (NullPool для избежания проблем с event loop)
"""

from collections.abc import AsyncGenerator
import os

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app.db.session import get_db
from app.main import app
from app.models.models import Base

# Определяем URL базы данных
# По умолчанию SQLite, но можно переопределить для PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)

# Определяем тип БД и настройки пула
_is_sqlite = TEST_DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite in-memory — StaticPool чтобы соединение не закрывалось
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
    # PostgreSQL — NullPool для корректной работы с pytest-asyncio
    # NullPool создаёт новое соединение на каждый запрос и сразу закрывает
    # Это избегает проблем с "connection is closed" между тестами
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture для тестовой сессии БД.

    Для каждого теста:
    1. Создаёт все таблицы
    2. Возвращает сессию
    3. После теста — откатывает и дропает таблицы
    """
    # создаём таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # создаём сессию
    async with TestSessionLocal() as session:
        yield session
        # откатываем незакоммиченные изменения
        await session.rollback()

    # дропаем таблицы после теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture для тестового HTTP клиента:
    - Подменяет зависимость get_db на тестовую сессию
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # подменяем зависимость
    app.dependency_overrides[get_db] = override_get_db

    # создаём async клиент для тестирования
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # очищаем override после теста
    app.dependency_overrides.clear()


# =============================================================================
# Fixture-ы для создания тестовых данных
# =============================================================================


@pytest.fixture
def sample_team_data() -> dict:
    """
    Тестовые данные команды с 3 участниками
    """
    return {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
            {"user_id": "u3", "username": "Charlie", "is_active": True},
        ],
    }


@pytest.fixture
def sample_team_with_inactive() -> dict:
    """
    Команда с неактивным участником
    """
    return {
        "team_name": "frontend",
        "members": [
            {"user_id": "f1", "username": "Frank", "is_active": True},
            {"user_id": "f2", "username": "Grace", "is_active": False},
            {"user_id": "f3", "username": "Henry", "is_active": True},
        ],
    }


@pytest.fixture
def sample_small_team() -> dict:
    """
    Маленькая команда — только 1 участник (для тестов edge cases)
    """
    return {
        "team_name": "solo",
        "members": [
            {"user_id": "s1", "username": "Solo", "is_active": True},
        ],
    }


@pytest.fixture
def sample_pr_data() -> dict:
    """
    Тестовые данные для создания PR
    """
    return {
        "pull_request_id": "pr-1001",
        "pull_request_name": "Add search feature",
        "author_id": "u1",
    }
