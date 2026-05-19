FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установим Poetry
RUN apt-get update && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN mkdir -p /logs

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false 
RUN if [ -n "$POETRY_EXTRAS" ]; then \
        poetry install $(echo $POETRY_EXTRAS | sed 's/[^ ]\+/ -E &/g'); \
    else \
        poetry install; \
    fi