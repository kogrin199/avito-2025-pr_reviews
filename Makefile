# Makefile
.PHONY: run migrate test test-cov test-html test-pg test-pg-cov lint lint-fix

# PostgreSQL test connection string
TEST_PG_URL = postgresql+asyncpg://test_user:test_password@localhost:5433/test_db

run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8080

migrate:
	uv run alembic upgrade head

# тесты на SQLite (быстрые, для разработки)
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ --cov=app --cov-report=term-missing

test-html:
	uv run pytest tests/ --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# тесты на PostgreSQL (для CI / pre-release)
test-pg-up:
	docker-compose -f docker-compose.test.yml up -d --wait

test-pg-down:
	docker-compose -f docker-compose.test.yml down

# запуск тестов на PostgreSQL через хак `python -c` чтобы поддержать make на Windows
test-pg: test-pg-up
	uv run python -c "import os; os.environ['TEST_DATABASE_URL']='$(TEST_PG_URL)'; import pytest; pytest.main(['-v', 'tests/'])"
	$(MAKE) test-pg-down

# запуск тестов с покрытием кода на PostgreSQL через хак `python -c` чтобы поддержать make на Windows 
test-pg-cov: test-pg-up
	uv run python -c "import os; os.environ['TEST_DATABASE_URL']='$(TEST_PG_URL)'; import pytest; pytest.main(['--cov=app', '--cov-report=term-missing', 'tests/'])"
	$(MAKE) test-pg-down

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix
	uv run ruff format .
