# CareerOS

CareerOS is a job application tracker that helps you manage every stage of your search — from saved opportunities and tailored résumés to interviews and offers — in a single, fast, and organized workspace.

## Tech Stack

- **Frontend:** Next.js 15 (App Router, React, TypeScript, Tailwind)
- **Backend:** FastAPI (Python, async, SQLAlchemy 2.0, Alembic)
- **Database:** PostgreSQL 16
- **Auth:** Clerk
- **File Storage:** Firebase Storage
- **Hosting:** Vercel (frontend) + Railway (backend / database)

## Quickstart

> The Docker Compose path requires Docker Desktop (or the Docker Engine with the Compose plugin) to be installed.

### 1. Copy environment files

```bash
cp .env.example .env
# plus any per-app .env.example files under /backend and /frontend once they exist
```

### 2. Run everything (Docker Compose)

```bash
docker compose up -d
# frontend -> http://localhost:3000
# backend  -> http://localhost:8000
# db       -> localhost:5432
```

### 3. Per-app local development (no Docker)

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn careeros_api.main:app --reload
```

## Documentation

- [Product](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Database](docs/DATABASE.md)
- [API](docs/API.md)
- [UI Guidelines](docs/UI_GUIDELINES.md)
- [Phase 0 Foundation Plan](docs/PHASE_0_FOUNDATION_PLAN.md)
