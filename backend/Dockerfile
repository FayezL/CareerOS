# syntax=docker/dockerfile:1.7

# ===== Builder stage =====
FROM python:3.12-slim AS builder

# Install uv (fast Python package manager) from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install the project into a contained virtualenv at /app/.venv.
COPY pyproject.toml uv.lock* /app/
RUN uv sync --frozen=false --no-install-project --no-dev

COPY src /app/src
COPY README.md /app/README.md
RUN uv sync --frozen=false --no-dev

# ===== Runtime stage =====
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the project and its virtualenv from the builder.
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "careeros_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
