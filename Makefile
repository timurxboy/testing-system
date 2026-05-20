.PHONY: install pre-commit-install lint format typecheck check \
       migrate migration upgrade downgrade migrate-history \
       createsuperuser run bot seed seed-reset

# Все make-команды ниже рассчитаны на локальный запуск через Poetry.
# На Windows (или там, где нет Poetry) выполняйте эквивалент внутри
# запущенного контейнера `backend` (см. комментарий перед каждой целью).
# Контейнеры поднимаются командой: docker compose up -d

# ---- Setup ----
# Docker: docker compose build
install:
	poetry install
	poetry run pre-commit install

# Docker: не нужен (хуки ставятся на хосте для git-коммитов)
pre-commit-install:
	poetry run pre-commit install

# ---- Code quality ----
# Docker: docker compose exec backend poetry run ruff check .
lint:
	poetry run ruff check .

# Docker: docker compose exec backend poetry run ruff format .
#         docker compose exec backend poetry run ruff check --fix .
format:
	poetry run ruff format .
	poetry run ruff check --fix .

# Docker: docker compose exec backend poetry run mypy .
typecheck:
	poetry run mypy .

check: lint typecheck
	@echo "All checks passed"

# ---- Migrations ----
# make migration m="add users table"
# Docker: docker compose exec backend poetry run alembic revision --autogenerate -m "add users table"
migration:
	poetry run alembic revision --autogenerate -m "$(m)"

# Docker: docker compose exec backend poetry run alembic upgrade head
upgrade:
	poetry run alembic upgrade head

# make downgrade r=-1
# Docker: docker compose exec backend poetry run alembic downgrade -1
downgrade:
	poetry run alembic downgrade $(or $(r),-1)

# Docker: docker compose exec backend poetry run alembic history --verbose
migrate-history:
	poetry run alembic history --verbose

# Shortcut: create migration + apply
# Docker: docker compose exec backend poetry run alembic revision --autogenerate -m "msg"
#         docker compose exec backend poetry run alembic upgrade head
migrate:
	poetry run alembic revision --autogenerate -m "$(m)"
	poetry run alembic upgrade head

# ---- App ----
# Docker: docker compose exec backend poetry run python -m apps.auth.cli.create_admin
createsuperuser:
	@poetry run python -m apps.auth.cli.create_admin

# Docker: бэкенд уже запущен сервисом `backend` (docker compose up -d).
#        Для ручного запуска: docker compose exec backend poetry run uvicorn main:app --reload
run:
	poetry run uvicorn main:app --reload

# ---- Bot ----
# Docker: бот уже запущен сервисом `bot` (docker compose up -d).
#        Для ручного запуска: docker compose exec bot poetry run python -m apps.bot.cli.run_bot
bot:
	poetry run python -m apps.bot.cli.run_bot

# ---- Seed ----
# Заливает демо-предметы/вопросы/варианты (идемпотентно).
# Docker: docker compose exec backend poetry run python -m apps.testing.cli.seed
seed:
	poetry run python -m apps.testing.cli.seed

# Полная перезаливка: дропает ВСЕ предметы (каскадом — вопросы, варианты,
# попытки, сессии) и заливает заново. DESTRUCTIVE.
# Docker: docker compose exec backend poetry run python -m apps.testing.cli.seed --reset
seed-reset:
	poetry run python -m apps.testing.cli.seed --reset
