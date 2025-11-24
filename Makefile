# Makefile
.PHONY: run migrate test

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080

migrate:
	alembic upgrade head

test:
	pytest

lint:
	ruff check .

lint-fix:
	ruff check . --fix
	ruff format .
