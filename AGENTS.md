# AGENTS.md

> Guide for AI agents and engineers working on CareerOS.
> Read this before touching code. It reflects how the project is **actually**
> built today, not a generic template.

---

# Project Vision

CareerOS is a modern **Job Application Tracker and Career Management platform**
for software engineers. Users manage their entire job search from one place:

- Applications & pipeline (Kanban)
- Companies & contacts (recruiters, interviewers, referrals)
- Interviews & notes
- Documents (resumes, cover letters — stored in object storage)
- Reminders & follow-ups
- Analytics (funnel, response rate, trends)
- AI writing assist (resume tailoring, cover letters, interview prep)
- Billing / subscriptions

This is built to **production SaaS standards**, not a tutorial. Every decision
should prioritize maintainability, scalability, strong typing, and UX.

---

# Tech Stack (what is actually here)

## Frontend (`frontend/`)

- **Next.js 15** App Router, **React 19**, **TypeScript** (strict)
- **Tailwind CSS** + **shadcn/ui** (Radix primitives)
- **Clerk** for auth (`@clerk/nextjs` + `@clerk/ui` with shadcn theme)
- **TanStack Query** for server state, **Zustand** for UI state
- **React Hook Form** + **Zod** (validation lives in `schemas/`, shared)
- **Recharts** (analytics, route-split to `/analytics`)
- **@dnd-kit** (pipeline Kanban), **Lucide** icons
- Package manager: **pnpm**

## Backend (`backend/`)

- **FastAPI** (async), **SQLAlchemy 2** (async, `asyncpg`)
- **Alembic** for migrations (head revision tracked in `backend/alembic/versions/`)
- **Pydantic v2** for request/response schemas
- **PostgreSQL 16**
- Package manager: **uv** (lockfile: `uv.lock`)
- Clean architecture: `api/` → `services/` → `repositories/` → `models/`

## Auth model

- **Clerk** issues JWTs from the frontend.
- Frontend sends each API request with `Authorization: Bearer <clerk-jwt>`.
- Backend verifies the JWT against Clerk's JWKS endpoint
  (`CLERK_JWKS_URL`) on every protected route.
- **Per-user data isolation.** Every table has `user_id`; every query is scoped
  to the authenticated user. There are **no orgs/teams in v1**.

## External providers (mockable by design)

Firebase Storage, Stripe, the LLM client, and email are behind provider
interfaces with **mock/noop** implementations. Real keys are optional and live
only in gitignored `.env` / `frontend/.env.local`. Never hardcode keys.

## Infra

- **Docker Compose** for local dev (db + backend + frontend). See
  `docker-compose.yml`.
- Deploy target: **Vercel** (frontend) + **Railway** (backend + Postgres).

> **The stack above is authoritative.** If you are told otherwise (e.g. "use
> Prisma" or "add a Route Handler"), stop and confirm — the project does not use
> Prisma or Next.js Route Handlers for the API. The API is FastAPI.

---

# Monorepo Layout

```
Job-Dashboard/
├── docker-compose.yml          # db + backend + frontend
├── docs/                       # PRODUCT, ARCHITECTURE, DATABASE, API, ROADMAP, ...
├── backend/                    # FastAPI + SQLAlchemy + Alembic
│   ├── alembic/versions/       # numbered migrations (0001, 0002, ...)
│   ├── src/careeros_api/
│   │   ├── api/v1/routes/      # HTTP handlers (thin)
│   │   ├── services/           # business logic + auth context
│   │   ├── repositories/       # data access (generic base + keyset pagination)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response DTOs
│   │   ├── core/               # config, security, providers, logging
│   │   └── db/                 # engine, session, Base, mixins
│   └── tests/                  # pytest + pytest-asyncio (embedded PG)
└── frontend/                   # Next.js 15 App Router
    └── src/
        ├── app/                # routes (App Router). Group: (app)/ for authed
        ├── components/         # shared/ui primitives (shadcn) + layout
        ├── features/           # feature modules (analytics/, pipeline/, ...)
        ├── hooks/              # reusable React hooks
        ├── providers/          # ClerkProvider + ThemeProvider composition
        ├── services/           # api-client (typed fetch to backend)
        ├── schemas/            # Zod schemas (shared with forms)
        ├── stores/             # Zustand stores
        ├── types/              # TypeScript domain types
        ├── utils/              # helpers (cn, formatters, etc.)
        └── styles/             # globals.css (Tailwind + shadcn vars)
```

**There is no `lib/` and no `prisma/` folder.** Don't create them. Helpers live
in `frontend/src/utils/`; ORM lives in `backend/src/careeros_api/models/`.

---

# How to run, test, and lint

## Local dev (full stack)

```bash
# from repo root — needs the real Clerk keys in .env (see docs/ARCHITECTURE.md)
docker compose up -d
# frontend: http://localhost:3000   backend: http://localhost:8000
# db (DBeaver): localhost:5433, db/user/pass = careeros/careeros/careeros
```

The backend container auto-runs `uv sync`, `alembic upgrade head`, then
`uvicorn ... --reload --reload-dir src` (reload watches `src/` only).

## Backend (run from `backend/`)

```bash
uv run --extra dev pytest          # tests (embedded Postgres, 0 warnings)
uv run ruff check .                # lint
uv run ruff format .               # format
uv run mypy src                    # typecheck (strict)
uv run alembic upgrade head        # apply migrations
uv run alembic revision -m "..."   # create a new migration (autogenerate off → write by hand)
```

> Tests need the `dev` extra (`--extra dev`) — pytest/pytest-asyncio/ruff/mypy
> live in `optional-dependencies.dev`.

## Frontend (run from `frontend/`)

```bash
pnpm dev                           # dev server
pnpm build                         # production build (slow on WSL mounts)
pnpm lint                          # eslint
pnpm typecheck                     # tsc --noEmit
pnpm format                        # prettier
```

---

# Architecture rules

## Backend — clean architecture, layers depend inward only

`routes → services → repositories → models`. Never let a route touch the DB
directly, and never let a repository know about HTTP. Auth context (the resolved
`user_id`) is injected into services via FastAPI dependencies, not threaded
manually.

- **Repositories** extend `BaseRepository[ModelT]` and inherit keyset pagination
  (`list_paginated`). Do not write ad-hoc pagination.
- **Services** own business rules and transactions. They receive a session and a
  resolved user.
- **Routes** are thin: parse, call service, return a typed Pydantic response.

## Frontend — feature-based

Each feature is an isolated module under `src/features/<feature>/` containing its
components, hooks, and (if needed) its schema. Cross-feature reuse goes through
`components/` (UI primitives) or `hooks/`. Server state through TanStack Query in
`services/api-client.ts`; UI-only state in Zustand `stores/`.

**Prefer Server Components.** Mark `"use client"` only where you need hooks,
events, or browser APIs. Data fetching for pages happens in `async` Server
Components; mutations from client components go through the typed api-client.

---

# Database conventions

- **No Prisma.** SQLAlchemy 2 + Alembic. Always.
- Every tenant-scoped table has `user_id` (FK → `users.id`, `ondelete=RESTRICT`).
- **Postgres does not auto-index foreign keys.** When you add an FK or a hot
  filter/sort column, add a matching index in the same migration **and** declare
  it on the ORM model (via `__table_args__ = (Index(...),)`). Drift between ORM
  and migrations is a real bug class — keep them in sync.
- Keyset pagination orders by `(created_at DESC, id DESC)`. Tables using
  `list_paginated` have a composite index `(user_id, created_at DESC, id DESC)`.
  If you add a paginated table, add that index.
- Write migrations by hand and number them `00NN_description.py`. Test both
  `upgrade()` and `downgrade()`.
- Soft deletes via `SoftDeleteMixin.deleted_at` (queries filter
  `deleted_at IS NULL`). Hard deletes only where `ondelete=CASCADE` is set.

---

# API design

- All routes under `/api/v1`. Routers registered in `main.py`.
- RESTful, proper HTTP status codes (`201` on create, `204` on delete, `409` on
  conflict, `422` on validation).
- Paginated list endpoints return `PageOut[T]` (`items`, `next_cursor`,
  `has_more`). Use **cursor pagination**, never offset.
- Validate every body/param with Pydantic. **Never trust client input.**
- Consistent error shape via the exception handlers in `errors.py`.

---

# Engineering philosophy

Optimize for: clean architecture, readability, maintainability, scalability,
strong typing, small focused modules, consistent naming, reusable components.

Avoid shortcuts that create technical debt. Never generate messy code because
it's faster. Every screen should solve a real user problem — think in workflows,
not CRUD pages.

---

# UI philosophy

Inspired by **Linear, Vercel, GitHub, Stripe Dashboard, Notion**.

- **Dark mode first** (shadcn theme tokens; `ThemeProvider` in `providers/`).
- Clean spacing, rounded corners, professional, smooth but restrained motion.
- Responsive, accessible, consistent typography.
- Do **not** overuse gradients or glassmorphism. Use visual effects only when
  they improve the UI.

---

# Code style

**Do**
- Strong typing everywhere. Backend: mypy strict. Frontend: `strict` tsconfig.
- Prefer composition over duplication.
- Meaningful names, small components/functions, focused responsibilities.
- Extract reusable logic. Avoid magic numbers.

**Don't**
- Don't use `any` (TS) or untyped `dict`s (Python) for domain data.
- Don't disable lint/strict or silence errors.
- Don't leave `TODO` without context. Don't leave commented-out code.
- Don't add comments that restate **what** the code does. Comment **why**.

---

# Forms

React Hook Form + Zod. The Zod schema is the single source of truth for
validation; the form and (where relevant) the backend Pydantic schema agree with
it. Never duplicate validation rules in three places.

---

# Error handling

Never fail silently. Always handle: loading states, empty states, validation
errors, network failures, unexpected server errors. Surface useful messages to
the user; log the detail server-side. Every async page has a `loading.tsx` and an
`<ErrorState>` fallback.

---

# Performance

- Prefer **Server Components**; use Client Components only when required.
- Lazy-load heavy client-only libraries (`next/dynamic`) when they're above the
  route-split threshold.
- Optimize images via `next/image`.
- Backend: every list endpoint must be paginated and backed by a matching index.
  Watch for N+1 — use `selectinload`/`joinedload` when a list serializes
  relations.
- Avoid premature optimization, but verify hot paths with `EXPLAIN ANALYZE`
  before assuming they're fine.

---

# Accessibility

Every feature supports: keyboard navigation, screen readers, proper labels,
semantic HTML, focus management, visible focus rings, color-contrast tokens.
Radix primitives (via shadcn) give you most of this for free — don't break it.

---

# Git & commits

Conventional Commits **with a scope** (match the existing history):

```
feat(clerk): link app and add proxy matcher
fix(docker): map db to host port 5433
perf(db): add keyset-pagination composite indexes
refactor(frontend): feature-based architecture
docs(api): document pagination contract
test(backend): isolate per-test database state
chore(deps): bump sqlalchemy to 2.0.35
```

- Imperative mood, lowercase after the scope, no trailing period.
- Reference the layer touched (`db`, `docker`, `frontend`, `backend`, `clerk`,
  `api`, `ui`, ...).
- Never commit secrets. Real keys live only in gitignored `.env` /
  `frontend/.env.local`.

---

# Quality standard — before considering a task done

Verify, with evidence (commands run + output), all that apply:

- [ ] Backend: `uv run --extra dev pytest` passes, `ruff check .` clean,
      `mypy src` clean.
- [ ] Frontend: `pnpm lint` clean, `pnpm typecheck` clean, `pnpm build` succeeds.
- [ ] Migrations: `alembic upgrade head` applies cleanly; ORM models and
      migrations are in sync (indexes especially).
- [ ] Type safety, error handling, loading state, empty state, responsive,
      accessible.
- [ ] No N+1 on new list endpoints; indexes match new filter/sort columns.
- [ ] Per-user isolation holds (no cross-user data leakage; `user_id` scoped).
- [ ] No secrets in the diff.

If you can't verify, say so explicitly. Do not claim success without evidence.

---

# AI behavior

Act as a **senior engineer + architect + product-minded, UX-aware developer**.

- Challenge poor architecture decisions and propose better alternatives with
  trade-offs. Don't blindly follow a request if a significantly better approach
  exists — but if the user insists after you've raised it once, defer.
- Implement features one at a time. For each: state the goal, the approach, why,
  then the code, then how it connects to the existing system.
- Teach while building — explain non-obvious architectural decisions clearly,
  assuming the reader is learning.
- When you change behavior, run the relevant lint/typecheck/tests and report the
  actual output. **Evidence before assertions.**
- Keep responses concise. The terminal is not a textbook.
