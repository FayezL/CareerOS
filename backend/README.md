# CareerOS API

The canonical FastAPI backend for **CareerOS**, the modern job-application tracker
for software engineers.

* FastAPI application factory (`careeros_api.main:create_app`)
* Async SQLAlchemy 2.0 + Alembic (asyncpg)
* Clerk JWT (RS256) authentication with cached JWKS
* Layered architecture: `routes → services → repositories → models`
* Per-user data scoping
* RFC 7807 `application/problem+json` error responses

## Local development

```bash
cp .env.example .env          # then edit values
uv sync --extra dev           # create .venv and install dev tooling
uv run alembic upgrade head   # apply database migrations
uv run uvicorn careeros_api.main:app --reload
```

## Quality commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

## Project layout

```
src/careeros_api/
  api/            # FastAPI routers + dependency wiring
  core/           # config, logging, security (Clerk)
  db/             # declarative base, async session, mixins
  models/         # SQLAlchemy ORM models
  repositories/   # data-access layer
  schemas/        # Pydantic v2 request/response models
  services/       # business logic
```
