# PR Reviewer Assignment Service

Сервис автоматического назначения ревьюеров на Pull Request'ы.

**Тестовое задание для стажёра Backend (Avito, осень 2025)**

---

## Быстрый старт

* Легче всего запустить с пакетным менеджером [uv](https://docs.astral.sh/uv/)

```shell
uv sync
make migrate
make run
```

* локально, `uv` установлен:

```shell
uv venv # создание .venv/
uv sync # синхронизация зависимостей python
# поднимаем сервис db - для подключения с localhost
docker compose up -d db
# выставление временной переменной окружения
#   для подключения к локальному PostgreSQL 18 (контейнер или нативно)
DATABASE_URL = "postgresql+asyncpg://app_user:app_password@localhost:5432/app_db"
uv run alembic upgrade head # или просто: "make migrate"
# далее можно просто запускать FastAPI через uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080 # или просто "make run"
```

* АЛЬТЕРНАТИВНЫЙ вариант (uv - нет):

```shell
python -m venv .venv
# ВНИМАНИЕ <- сделайте "activate venv" в вашем SHELL = [Bash, Powershell, ZSH]
pip install -r requirements.txt
# alembic upgrade head
```

продолжаем через Docker:

```shell
DATABASE_URL="postgresql+asyncpg://app_user:app_password@localhost:5432/app_db"

# Запуск сервиса (PostgreSQL + приложение)
docker-compose up -d --build

# Сервис доступен на http://localhost:8080
# Swagger UI: http://localhost:8080/docs
```

Миграции применяются автоматически при старте контейнера.

---

## Стек и окружение

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.12 |
| Web-фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| База данных | PostgreSQL 18 |
| Драйвер БД | asyncpg |
| Миграции | Alembic |
| Менеджер зависимостей | uv |
| Линтер/форматтер | Ruff |
| Тестирование | pytest, pytest-asyncio, httpx |
| Контейнеризация | Docker, docker-compose |

### Структура проекта

```
app/
├── api/          # HTTP-эндпойнты (FastAPI роутеры)
├── core/         # Конфигурация
├── db/           # Подключение к БД
├── models/       # SQLAlchemy модели
├── repositories/ # Слой доступа к данным
├── schemas/      # Pydantic схемы
└── services/     # Бизнес-логика
tests/
├── integration/  # Интеграционные тесты API
└── unit/         # Unit-тесты сервисов
```

---

## Makefile команды

```bash
make run          # Запуск локально (uvicorn)
make migrate      # Применить миграции
make test         # Тесты на SQLite (быстрые)
make test-cov     # Тесты с покрытием
make test-pg      # Тесты на PostgreSQL (docker)
make lint         # Проверка линтером
make lint-fix     # Авто-исправление + форматирование
```

---

## Тестирование

### Покрытие: ~85%

* **68 тестов** (32 интеграционных + 36 unit)
* Интеграционные тесты проверяют все эндпойнты через HTTP
* Unit-тесты покрывают бизнес-логику сервисов

### Запуск

```bash
# Быстрые тесты (SQLite in-memory)
make test

# Тесты на PostgreSQL (поднимает тестовый контейнер)
make test-pg

# С отчётом покрытия
make test-cov
```

---

## Ключевые решения

### 1. Алгоритм выбора ревьюеров

При создании PR выбираются до 2 активных участников команды автора с **наименьшим количеством текущих назначений** (load balancing). Это обеспечивает равномерное распределение нагрузки.

### 2. Переназначение ревьюера

При reassign новый ревьюер выбирается из **команды заменяемого** (не автора), также по принципу наименьшей загрузки среди активных участников.

### 3. Идемпотентность merge

Повторный вызов merge для уже смерженного PR возвращает 200 OK с текущим состоянием, а не ошибку.

### 4. Хранение assigned_reviewers

Ревьюеры хранятся в отдельной таблице `pull_request_reviewers` (many-to-many), а не в JSON-поле. Это позволяет эффективно считать статистику и делать выборки.

### 5. DateTime с timezone

Поля `createdAt` и `mergedAt` используют `DateTime(timezone=True)` для корректной работы с asyncpg и PostgreSQL.

---

## Реализованный функционал

### Обязательные требования

| Требование | Статус |
|------------|--------|
| POST /team/add — создание команды | Выполнено |
| GET /team/get — получение команды | Выполнено |
| POST /users/setIsActive — изменение активности | Выполнено |
| POST /pullRequest/create — создание PR с авто-назначением | Выполнено |
| POST /pullRequest/merge — идемпотентный merge | Выполнено |
| POST /pullRequest/reassign — переназначение ревьюера | Выполнено |
| GET /users/getReview — PR'ы пользователя | Выполнено |
| Назначение до 2 ревьюеров из команды автора | Выполнено |
| Исключение неактивных пользователей | Выполнено |
| Запрет изменений после merge | Выполнено |
| docker-compose up на порту 8080 | Выполнено |
| Автоматические миграции | Выполнено |

### Дополнительные задания

| Задание | Статус |
|---------|--------|
| Эндпойнт статистики (GET /stats) | Выполнено |
| Интеграционное тестирование | Выполнено |
| Конфигурация линтера (ruff.toml) | Выполнено |
| Нагрузочное тестирование | Не выполнено |
| Массовая деактивация | Не выполнено |

---

## Конфигурация линтера

Используется **Ruff** с расширенным набором правил:

- `F` — pyflakes (ошибки импортов, неиспользуемые переменные)
- `I` — isort (сортировка импортов)
- `UP` — pyupgrade (современный синтаксис Python 3.12)
- `B` — bugbear (частые ошибки)
- `W` — pycodestyle warnings
- `PIE`, `TID`, `A` — дополнительные проверки

Конфигурация в `ruff.toml`.

---

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| DATABASE_URL | Строка подключения к PostgreSQL | postgresql+asyncpg://... |

* содержимое .env:

```dotenv
POSTGRES_DB=app_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

В docker-compose переменные задаются автоматически.
