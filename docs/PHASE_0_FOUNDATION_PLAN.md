# Phase 0 — Foundation Implementation Plan

> **Living document.** Last updated: 2026-07-08.
> **Scope:** Foundation scaffold ONLY. No product features. Output = a deployable,
> authenticated, CI-green monorepo with an empty-but-real schema and a health check.
> **Reference:** PRODUCT.md · ARCHITECTURE.md · DATABASE.md · API.md · UI_GUIDELINES.md · ROADMAP.md

**Goal:** Stand up the CareerOS monorepo (Next.js + FastAPI + Postgres) with Docker,
env validation, path aliases, lint/format, GitHub Actions CI, Clerk auth wiring,
async SQLAlchemy 2 + Alembic, and a health check — nothing more.

**Architecture:** FastAPI is the canonical API; Next.js forwards the Clerk session JWT
as `Authorization: Bearer`; FastAPI verifies via Clerk JWKS and scopes every query by
`user_id`. Monorepo under `/backend`, `/frontend`, root `docker-compose.yml`.

**Tech Stack:** Next.js 15 (App Router) · TypeScript (strict) · Tailwind · shadcn/ui ·
FastAPI · SQLAlchemy 2 async (asyncpg) · Alembic · PostgreSQL 16 · Clerk · Firebase Storage.
Package managers: **pnpm** (frontend), **uv** (backend).

---

## Canonical ENV contract (all areas must agree)

### Postgres / compose root (`.env`)
```
POSTGRES_USER=careeros
POSTGRES_PASSWORD=careeros
POSTGRES_DB=careeros
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://careeros:careeros@db:5432/careeros   # backend in compose
DATABASE_URL_LOCAL=postgresql+asyncpg://careeros:careeros@localhost:5432/careeros
```

### `backend/.env.example`
```
ENV=local                       # local | staging | production
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5432/careeros
CLERK_ISSUER=https://example.clerk.accounts.dev
CLERK_JWKS_URL=https://example.clerk.accounts.dev/.well-known/jwks.json
CORS_ORIGINS=http://localhost:3000
FIREBASE_STORAGE_BUCKET=         # reserved (Phase 4)
LLM_API_KEY=                     # reserved (Phase 7)
```

### `frontend/.env.example`
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
```

---

## File structure to create

```
.
├── .github/workflows/{frontend-ci,backend-ci,docker-build}.yml
├── .husky/pre-commit
├── package.json                  # root: husky + lint-staged only
├── .editorconfig
├── .gitignore
├── .env.example                  # compose vars
├── docker-compose.yml
├── README.md
├── backend/
│   ├── pyproject.toml            # uv, ruff, mypy(strict), pytest
│   ├── uv.lock                   # generated
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                # async, import models, naming convention
│   │   ├── script.py.mako
│   │   └── versions/<initial_users>.py
│   ├── src/careeros_api/
│   │   ├── __init__.py
│   │   ├── main.py               # app factory: lifespan, CORS, exception handlers, routers
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py         # pydantic-settings Settings (fail-fast)
│   │   │   ├── logging.py        # structlog/JSON-ish logging setup
│   │   │   └── security/
│   │   │       ├── __init__.py
│   │   │       ├── clerk.py      # JWKS fetch+cache, verify, CurrentUser
│   │   │       └── errors.py     # AuthError
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # DeclarativeBase + naming convention
│   │   │   ├── session.py        # async engine + sessionmaker + get_session
│   │   │   └── mixins.py         # TimestampMixin, SoftDeleteMixin, UUIDPrimaryKey
│   │   ├── models/
│   │   │   ├── __init__.py       # re-export all models (for Alembic autogenerate)
│   │   │   └── user.py           # User(clerk_user_id, email, full_name, avatar_url)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py         # Paginated envelope, cursors
│   │   │   └── user.py           # UserRead, UserUpdate
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── base.py           # BaseRepository (user_id scoping) + UserRepository
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py           # get_session, get_current_user
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── routes/
│   │   │           ├── __init__.py
│   │   │           ├── health.py     # GET /health, GET /health/ready
│   │   │           └── me.py         # GET /me, PATCH /me  (auth-required)
│   │   └── errors.py             # RFC 7807 problem+json handlers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py           # fixture app/client, settings override, mock JWKS
│       ├── test_health.py
│       ├── test_config.py
│       ├── test_clerk_verification.py
│       └── test_me.py            # auth-required path (skipped w/o DB)
├── frontend/
│   ├── package.json              # pnpm, Next 15, React 19, TS, Tailwind, shadcn, clerk, zod
│   ├── pnpm-lock.yaml            # generated
│   ├── next.config.ts
│   ├── tsconfig.json             # @/* -> ./src/*
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── components.json           # shadcn config
│   ├── eslint.config.mjs         # flat, next + TS + prettier
│   ├── .prettierrc
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile                # multi-stage, standalone
│   └── src/
│       ├── app/
│       │   ├── layout.tsx        # <ClerkProvider>, fonts, Tailwind globals
│       │   ├── page.tsx          # landing (signed-out) / dashboard stub (signed-in)
│       │   ├── globals.css       # Tailwind + shadcn CSS variables (light/dark)
│       │   └── (auth)/{sign-in,sign-up}/[[...index]]/page.tsx  # Clerk routes
│       ├── middleware.ts         # clerk middleware + public routes
│       ├── components/
│       │   ├── ui/{button.tsx}   # shadcn primitives (button minimal)
│       │   └── theme-provider.tsx
│       ├── lib/
│       │   ├── env.ts            # zod-validated process.env (fail-fast)
│       │   ├── api-client.ts     # fetch wrapper w/ Bearer token
│       │   ├── clerk.ts          # token getter
│       │   └── utils.ts          # cn()
│       ├── hooks/
│       ├── stores/
│       ├── types/
│       └── styles/
└── docs/                         # already created
```

---

## Tasks (area-grouped)

### Task A — Root / infra (independent)
Create: `.gitignore`, `.editorconfig`, `.env.example`, `README.md`, `docker-compose.yml`
(db: postgres:16 healthcheck; backend: uvicorn --reload, mount `backend/src`; frontend:
`next dev`, mount `frontend/src`), `.github/workflows/{frontend-ci,backend-ci,docker-build}.yml`,
root `package.json` (husky + lint-staged, `prepare` script), `.husky/pre-commit`.
CI path filters: `frontend/**`, `backend/**`. backend-ci uses `services: postgres:16`.
docker-build builds both Dockerfiles.

### Task B — Backend scaffold (FastAPI + SQLAlchemy async + Alembic + Clerk)
Per file structure above. Key behaviors:
- `Settings` (pydantic-settings) with `ENV`, `DATABASE_URL`, `CLERK_ISSUER`,
  `CLERK_JWKS_URL`, `CORS_ORIGINS` (list), `LOG_LEVEL`; fail-fast on missing required.
- `DeclarativeBase` with `naming_convention` (ix/uq/ck/fk/pk). Mixins: `UUIDPrimaryKey`
  (`UUID` pk `gen_random_uuid()`), `TimestampMixin` (created_at/updated_at TIMESTAMPTZ
  default now(), updated_at onupdate), `SoftDeleteMixin` (deleted_at).
- async engine `create_async_engine`, `async_sessionmaker`, `get_session` dependency.
- `core/security/clerk.py`: fetch JWKS with `httpx`, cache with TTL + `kid`-miss refetch,
  verify RS256 JWT (`PyJWT`) checking `iss`/`exp`/`azp`, return `CurrentUser(clerk_user_id,
  email, full_name, avatar_url)`. Raise `AuthError` → 401.
- `api/deps.py`: `get_current_user` (verify JWT, upsert local User, return ORM `User`).
  Upsert uses `INSERT ... ON CONFLICT (clerk_user_id) DO UPDATE`.
- `models/user.py`: `users` table (id UUID pk, clerk_user_id TEXT unique not null, email
  not null, full_name, avatar_url, timestamps).
- `api/v1/routes/health.py`: `GET /api/v1/health` (liveness, no DB), `GET /api/v1/health/ready`
  (readiness, `SELECT 1`). `api/v1/routes/me.py`: `GET /api/v1/me`, `PATCH /api/v1/me`
  (auth-required). Wire routers in `main.py`.
- `errors.py`: RFC 7807 `application/problem+json` for 400/401/404/422/500 and
  `RequestValidationError`.
- Alembic `env.py` (async, `run_sync`), initial migration creating `users` + the
  `updated_at` trigger function. `alembic.ini` with `sqlalchemy.url` from env override.
- Tests: `test_health.py` (200 on liveness; readiness skipped w/o DB), `test_config.py`
  (Settings parsing, CORS split), `test_clerk_verification.py` (verify happy path with a
  generated RS256 key + JWKS mock; reject bad iss/exp). Use `pytest-asyncio`. DB tests skip
  if `DATABASE_URL` unset.

### Task C — Frontend scaffold (Next.js 15 + shadcn + Clerk + zod)
Per file structure above. Key behaviors:
- `package.json`: Next 15, React 19, TS 5, Tailwind 3, `@clerk/nextjs`, `zod`,
  `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, `next-themes`.
  devDeps: eslint (flat), eslint-config-next, eslint-config-prettier, prettier,
  `@types/*`, typescript. Scripts: dev/build/start/lint/typecheck(format).
- `tsconfig.json` strict, `paths: { "@/*": ["./src/*"] }`.
- `lib/env.ts`: zod schema validating `NEXT_PUBLIC_API_URL`,
  `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`; export typed object; throw on missing.
- `lib/api-client.ts`: fetch wrapper that injects `Authorization: Bearer <token>` from Clerk.
- `app/layout.tsx`: `<ClerkProvider>`, `<ThemeProvider>`, Inter font, globals.
- `middleware.ts`: `clerkMiddleware` with public routes `/sign-in`, `/sign-up`.
- `app/page.tsx`: signed-out → CTA; signed-in → minimal dashboard stub calling `/api/v1/health`.
- shadcn `components/ui/button.tsx` + `components.json` + `globals.css` with CSS variables
  (light/dark) + `tailwind.config.ts` with `darkMode: "class"`, container, shadcn tokens.
- Dockerfile: node:20-alpine, `standalone` output, multi-stage.

---

## Verification checklist (must pass before handoff)

**Backend (local, no Docker):**
- [ ] `cd backend && uv sync` succeeds (lockfile generated)
- [ ] `uv run ruff check .` clean
- [ ] `uv run ruff format --check .` clean
- [ ] `uv run mypy src` clean
- [ ] `uv run pytest -q` green (DB tests skipped)

**Frontend (local):**
- [ ] `cd frontend && pnpm install` succeeds
- [ ] `pnpm lint` clean
- [ ] `pnpm typecheck` (`tsc --noEmit`) clean
- [ ] `pnpm build` succeeds

**Docker (requires Docker — run on host if unavailable here):**
- [ ] `docker compose build` builds db/backend/frontend
- [ ] `docker compose up -d db` healthy
- [ ] `docker compose run --rm backend alembic upgrade head` creates `users` table
- [ ] `curl localhost:8000/api/v1/health` → 200

**CI:** workflows validate on PR; `docker-build.yml` builds both images.

**Out of scope (explicit):** any feature CRUD, pipeline stages, analytics, AI, billing,
real Clerk dashboard keys, real Firebase creds. Only `users` table + health + `/me`.
