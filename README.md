# Testing System

[English](#english) | [Русский](#русский)

---

<a id="english"></a>

## English

Production-ready base architecture for FastAPI projects
with JWT auth, refresh tokens, roles, Alembic, SQLAdmin, and clean layer separation.

Designed as a **template** that scales into a monolith or microservices.

---

### Features

- JWT authentication (access + refresh tokens)
- Logout with refresh token revocation
- User roles (ADMIN / STAFF / USER)
- User registration
- SQLAlchemy 2.0 (async) + Alembic migrations
- SQLAdmin panel with real auth
- CORS middleware (configurable)
- Health check endpoint
- Global exception handlers
- Pre-commit hooks (ruff + mypy)
- APScheduler support (optional)
- S3/MinIO storage (optional)
- Docker-ready

---

### Project Structure

```text
.
├── core/
│   ├── db/
│   │   ├── base.py           # SQLAlchemy Base + naming convention
│   │   ├── mixins.py         # ID, Timestamp, TableName, Repr mixins
│   │   ├── engine.py         # Async engine instance
│   │   ├── session.py        # SessionLocal
│   │   ├── deps.py           # get_db dependency
│   │   └── factory/          # Engine / session factories
│   ├── repository/
│   │   └── base.py           # Generic async repository
│   ├── settings/             # Pydantic settings
│   └── logging/              # Logging setup
│
├── apps/
│   └── auth/
│       ├── api/
│       │   ├── router.py     # Auth endpoints
│       │   ├── deps.py       # get_current_user
│       │   └── permissions.py # require_role dependency
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── service/          # Business logic
│       ├── domain/           # Roles enum
│       ├── admin/            # SQLAdmin views
│       ├── utils/            # JWT, password hashing
│       └── cli/              # CLI commands (createsuperuser)
│
├── infrastructure/
│   ├── scheduler/            # APScheduler base (optional)
│   └── storage/              # S3 adapter (optional)
│
├── bootstrap/
│   ├── routers.py            # Router registration
│   ├── admin.py              # Admin panel setup
│   ├── scheduler.py          # Scheduler lifecycle
│   └── events.py             # Domain events
│
├── migrations/               # Alembic
├── main.py                   # Application entrypoint
├── pyproject.toml
├── Makefile
├── Dockerfile
├── compose.yaml
└── .pre-commit-config.yaml
```

---

### Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd testing-system
poetry install

# 2. Setup pre-commit hooks
make install

# 3. Copy env and fill in values
cp .env.example .env

# 4. Start database
docker compose up -d db

# 5. Run migrations
poetry run alembic upgrade head

# 6. Create superuser
make createsuperuser

# 7. Run the app
poetry run uvicorn main:app --reload
```

---

### API Endpoints

| Method | URL               | Description            | Auth     |
|--------|-------------------|------------------------|----------|
| POST   | `/auth/register`  | Register new user      | No       |
| POST   | `/auth/token`     | Login (get tokens)     | No       |
| POST   | `/auth/refresh`   | Refresh access token   | No       |
| POST   | `/auth/logout`    | Revoke refresh token   | No       |
| GET    | `/auth/me`        | Current user info      | Bearer   |
| GET    | `/health`         | Health check           | No       |
| GET    | `/admin`          | Admin panel            | Session  |

---

### Roles

| Role    | Created via          |
|---------|----------------------|
| `ADMIN` | `make createsuperuser` |
| `STAFF` | Admin panel          |
| `USER`  | `/auth/register`     |

Access control: `Depends(require_role(Role.ADMIN))`.

---

### Code Quality

Pre-commit hooks run automatically on every `git commit`:

| Tool   | Purpose                                    |
|--------|--------------------------------------------|
| ruff   | Linting + formatting (replaces black/flake8/isort) |
| mypy   | Static type checking                       |

```bash
make lint        # Run linter
make format      # Auto-format code
make typecheck   # Run type checker
make check       # All checks at once
```

---

### Migrations (Alembic)

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one step
poetry run alembic downgrade -1
```

---

### Docker

```bash
# Full stack (app + db)
docker compose up -d

# With optional extras (scheduler, s3)
POETRY_EXTRAS="scheduler s3" docker compose up -d --build
```

---

### Environment Variables (.env)

```env
# App
APP_PORT=8000

# Postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=secret
DB_NAME=mydb
DB_PATH=/mnt/data/psql-data

# Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Logging
LOG_DIR=logs
LOG_FILE=app.log
LOG_LEVEL=INFO

# Optional extras for Docker
POETRY_EXTRAS="scheduler s3"
```

---

### Adding a New App

1. Create `apps/your_app/` with `api/`, `models/`, `schemas/`, `service/`
2. Register router in [bootstrap/routers.py](bootstrap/routers.py)
3. Import models in `apps/your_app/models/__init__.py`
4. Import models in [migrations/env.py](migrations/env.py)
5. Generate migration: `poetry run alembic revision --autogenerate -m "add your_app"`

---

---

<a id="русский"></a>

## Русский

Готовая базовая архитектура для проектов на FastAPI
с JWT-авторизацией, refresh-токенами, ролями, Alembic, SQLAdmin и чистым разделением слоёв.

Проект задуман как **шаблон**, который легко масштабируется в монолит или микросервисы.

---

### Возможности

- JWT-аутентификация (access + refresh токены)
- Logout с отзывом refresh-токена
- Роли пользователей (ADMIN / STAFF / USER)
- Регистрация пользователей
- SQLAlchemy 2.0 (async) + миграции Alembic
- Админ-панель SQLAdmin с реальной аутентификацией
- CORS middleware (настраиваемый)
- Health check эндпоинт
- Глобальные обработчики ошибок
- Pre-commit хуки (ruff + mypy)
- Поддержка APScheduler (опционально)
- S3/MinIO хранилище (опционально)
- Docker-ready

---

### Быстрый старт

```bash
# 1. Клонировать и установить
git clone <repo-url> && cd testing-system
poetry install

# 2. Установить pre-commit хуки
make install

# 3. Скопировать .env и заполнить значения
cp .env.example .env

# 4. Поднять базу данных
docker compose up -d db

# 5. Применить миграции
poetry run alembic upgrade head

# 6. Создать суперпользователя
make createsuperuser

# 7. Запустить приложение
poetry run uvicorn main:app --reload
```

---

### API-эндпоинты

| Метод  | URL               | Описание                | Авторизация |
|--------|-------------------|-------------------------|-------------|
| POST   | `/auth/register`  | Регистрация             | Нет         |
| POST   | `/auth/token`     | Логин (получить токены) | Нет         |
| POST   | `/auth/refresh`   | Обновить access-токен   | Нет         |
| POST   | `/auth/logout`    | Отозвать refresh-токен  | Нет         |
| GET    | `/auth/me`        | Информация о текущем юзере | Bearer   |
| GET    | `/health`         | Проверка здоровья       | Нет         |
| GET    | `/admin`          | Админ-панель            | Session     |

---

### Роли

| Роль    | Создаётся через        |
|---------|------------------------|
| `ADMIN` | `make createsuperuser` |
| `STAFF` | Админ-панель           |
| `USER`  | `/auth/register`       |

Контроль доступа: `Depends(require_role(Role.ADMIN))`.

---

### Качество кода

Pre-commit хуки запускаются автоматически при каждом `git commit`:

| Инструмент | Назначение                                         |
|------------|----------------------------------------------------|
| ruff       | Линтинг + форматирование (заменяет black/flake8/isort) |
| mypy       | Статическая проверка типов                         |

```bash
make lint        # Запустить линтер
make format      # Автоформатирование
make typecheck   # Проверка типов
make check       # Все проверки сразу
```

---

### Миграции (Alembic)

```bash
# Создать миграцию
poetry run alembic revision --autogenerate -m "описание"

# Применить миграции
poetry run alembic upgrade head

# Откатить на шаг назад
poetry run alembic downgrade -1
```

---

### Docker

```bash
# Полный стек (приложение + БД)
docker compose up -d

# С опциональными модулями (scheduler, s3)
POETRY_EXTRAS="scheduler s3" docker compose up -d --build
```

---

### Переменные окружения (.env)

```env
# Приложение
APP_PORT=8000

# Postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=secret
DB_NAME=mydb
DB_PATH=/mnt/data/psql-data

# Авторизация
SECRET_KEY=ваш-секретный-ключ
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Логирование
LOG_DIR=logs
LOG_FILE=app.log
LOG_LEVEL=INFO

# Опциональные модули для Docker
POETRY_EXTRAS="scheduler s3"
```

---

### Добавление нового приложения

1. Создать `apps/your_app/` с папками `api/`, `models/`, `schemas/`, `service/`
2. Зарегистрировать роутер в [bootstrap/routers.py](bootstrap/routers.py)
3. Импортировать модели в `apps/your_app/models/__init__.py`
4. Импортировать модели в [migrations/env.py](migrations/env.py)
5. Сгенерировать миграцию: `poetry run alembic revision --autogenerate -m "add your_app"`
