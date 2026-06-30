# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* .python-version ./
RUN uv sync --frozen --no-dev

FROM base AS final

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "src/main.py"]
