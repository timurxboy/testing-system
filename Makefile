.PHONY: install pre-commit-install lint format typecheck check \
       migrate migration upgrade downgrade migrate-history \
       createsuperuser run

# ---- Setup ----
install:
	poetry install
	poetry run pre-commit install

pre-commit-install:
	poetry run pre-commit install

# ---- Code quality ----
lint:
	poetry run ruff check .

format:
	poetry run ruff format .
	poetry run ruff check --fix .

typecheck:
	poetry run mypy .

check: lint typecheck
	@echo "All checks passed"

# ---- Migrations ----
# make migration m="add users table"
migration:
	poetry run alembic revision --autogenerate -m "$(m)"

upgrade:
	poetry run alembic upgrade head

# make downgrade r=-1
downgrade:
	poetry run alembic downgrade $(or $(r),-1)

migrate-history:
	poetry run alembic history --verbose

# Shortcut: create migration + apply
migrate:
	poetry run alembic revision --autogenerate -m "$(m)"
	poetry run alembic upgrade head

# ---- App ----
createsuperuser:
	@poetry run python -m apps.auth.cli.create_admin

run:
	poetry run uvicorn main:app --reload
