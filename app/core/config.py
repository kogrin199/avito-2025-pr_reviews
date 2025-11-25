# Application config, constants, and utilities
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "PR Reviewer Assignment Service"
    PROJECT_VERSION: str = "1.0.0"

    # read postgres creds from env
    _pg_user = os.getenv("POSTGRES_USER", "app_user")
    _pg_password = os.getenv("POSTGRES_PASSWORD", "app_password")
    _pg_db = os.getenv("POSTGRES_DB", "app_db")
    _pg_host = os.getenv("POSTGRES_HOST", "db")
    _pg_port = os.getenv("POSTGRES_PORT", "5432")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{_pg_user}:{_pg_password}@{_pg_host}:{_pg_port}/{_pg_db}",
    )
    API_PREFIX: str = ""


settings = Settings()
