import asyncio
from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from app.core.config import settings
import app.models.models as data_models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = data_models.Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def do_run_migrations_async(connectable):
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    if isinstance(connectable, AsyncEngine):
        asyncio.run(do_run_migrations_async(connectable))
    else:
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
