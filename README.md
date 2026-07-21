# CareerOS

> A production-grade, full-stack **Job Application Tracker & Career Management
> platform** for software engineers. Track every application from bookmark to
> signed offer, organise your network, and surface the opportunities that
> actually move you forward — all in one fast, dark-mode-first workspace.

CareerOS is built to **production SaaS standards**, not as a tutorial or CRUD
demo. Every layer — schema, API, auth, frontend — is engineered the way a real
startup team would ship it: strongly typed, tested, indexed, paginated, and
containerised.

---

## ✨ Highlights

- **Application-centric workflow** — companies, contacts, and tags grow *from*
  the application. Type a company name → it's auto-created. No "create a
  company first" prerequisite.
- **Workspace + narrative timeline** — every application has a visual timeline
  (Applied → stage transitions → offer/rejection) alongside details, documents,
  and tags.
- **Company dashboards** — `/companies/[id]` answers *"what is my history with
  this company?"* with stats (applications / active / offers / rejected),
  embedded applications, and contacts.
- **Home dashboard** — `/dashboard` surfaces "how is my job search going?" with
  headline metrics, follow-up banner, and recent activity.
- **⌘K command palette** — Raycast/Linear-style global search across
  applications, companies, and contacts.
- **Split-screen auth** — branded Clerk sign-in / sign-up with a custom-styled
  component that reads as native shadcn.
- **Application tags** — Remote, Visa Sponsorship, Python, Europe… filter and
  analyse by any axis. Tags auto-create inline.
- **Clerk JWT → FastAPI** — the frontend forwards the Clerk session JWT as a
  Bearer token; the backend verifies against Clerk's JWKS on every request.
  Per-user data isolation throughout.

---

## 🧱 Tech Stack

| Layer | Choice |
|---|---|
| **Frontend** | Next.js 15 (App Router) · React 19 · TypeScript (strict) · Tailwind · shadcn/ui · TanStack Query · React Hook Form + Zod · Recharts · @dnd-kit |
| **Backend** | FastAPI (async) · SQLAlchemy 2 (async, asyncpg) · Alembic · Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **Auth** | Clerk (`@clerk/nextjs` + `@clerk/ui` with a shadcn theme) |
| **Dev infra** | Docker Compose (db + backend + frontend) · pnpm · uv |
| **Deploy target** | Vercel (frontend) + Railway (backend + Postgres) |

External providers (Firebase Storage, Stripe, LLM, email) live behind provider
interfaces with **mock/noop** implementations — real keys are optional and
gitignored.

---

## 🏛 Architecture

**Clean, layered, dependency-directional.**

```
frontend (Next.js App Router)
  Server Components ──► services/api-client.ts ──► FastAPI
  (data fetching)         (typed fetch + Clerk JWT)   │
  Client Components ──► Server Actions ───────────────┤
  (mutations, ⌘K)         ("use server" boundary)      │
                                                       ▼
backend (FastAPI)                                 routes (thin)
                                                     │
              ┌──────────────────────────────────────┘
              ▼
          services (business logic, auth context, transactions)
              │
              ▼
          repositories (data access, keyset pagination, eager loading)
              │
              ▼
          models (SQLAlchemy 2 ORM)  ──►  PostgreSQL 16
```

- **Backend**: `routes → services → repositories → models`. Routes never touch
  the DB; repositories never know about HTTP. Auth context (resolved `user_id`)
  is injected via FastAPI dependencies.
- **Frontend**: feature-based modules under `src/features/<feature>/`. Server
  Components fetch data; mutations flow through typed Server Actions. UI state
  in Zustand, server state through the typed api-client.
- **Auth**: Clerk issues JWTs from the frontend; every API request carries
  `Authorization: Bearer <clerk-jwt>`; the backend verifies the signature
  against Clerk's JWKS, checks the issuer, and resolves the local `User` row.
  **Every query is scoped by `user_id`** — no orgs/teams in v1, just hard
  per-user isolation.

---

## 🚀 Quickstart

> Requires Docker Desktop (or the Docker Engine + Compose plugin).

### 1. Clone & configure

```bash
git clone https://github.com/FayezL/Job-Dashboard.git
cd Job-Dashboard
cp .env.example .env
# add your Clerk keys (CLERK_ISSUER, CLERK_JWKS_URL, publishable + secret keys)
# — see docs/ARCHITECTURE.md
```

### 2. Run the full stack

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000 (`/docs` for OpenAPI) |
| Postgres | `localhost:5433` · db/user/pass = `careeros` (DBeaver-friendly) |

The backend container auto-runs `uv sync`, `alembic upgrade head`, then
`uvicorn ... --reload --reload-dir src`.

### 3. Local dev (without Docker)

```bash
# backend
cd backend && uv sync && uv run uvicorn careeros_api.main:app --reload

# frontend (separate terminal)
cd frontend && pnpm install && pnpm dev
```

---

## 🧪 Quality bar

This isn't a "works on my machine" project. Verification is built in:

| Check | Command | Result |
|---|---|---|
| Backend tests (embedded PG, 0 warnings) | `uv run --extra dev pytest` | **122 pass / 0 fail** |
| Backend lint | `uv run ruff check .` | clean |
| Backend types (strict) | `uv run --extra dev mypy src` | clean (93 files) |
| Frontend lint | `pnpm lint` | clean |
| Frontend types (strict) | `pnpm typecheck` | clean |

**Engineering rigour:**

- **Keyset (cursor) pagination** on every list endpoint, backed by composite
  indexes `(user_id, created_at DESC, id DESC)`. Verified with `EXPLAIN
  ANALYZE` against 5,000 rows — index scan stops at LIMIT (~0.08ms).
- **Postgres FKs are explicitly indexed** (Postgres doesn't auto-index them) —
  the schema ships 36+ indexes including hot-path composites.
- **Hand-written Alembic migrations** (`00NN_description.py`), tested both
  upgrade and downgrade. ORM models declare every index/constraint to prevent
  ORM↔migration drift.
- **Strict typing end-to-end**: `mypy --strict` on the backend, `strict`
  tsconfig on the frontend. No `any`, no untyped dicts for domain data.
- **Per-user isolation**: every tenant-scoped table carries `user_id`; every
  query is user-scoped. Tested with cross-user isolation cases.
- **Provider-interface pattern**: Firebase/Stripe/LLM/email are mockable by
  design — real keys never hardcoded, never committed.

---

## 📁 Project structure

```
Job-Dashboard/
├── docker-compose.yml          # db + backend + frontend
├── docs/                       # PRODUCT, ARCHITECTURE, DATABASE, API, REDESIGN_ROADMAP, ...
├── AGENTS.md                   # engineering guide for AI agents + humans
├── backend/                    # FastAPI + SQLAlchemy + Alembic
│   ├── alembic/versions/       # 0001 → 0009 migrations
│   ├── src/careeros_api/
│   │   ├── api/v1/routes/      # thin HTTP handlers
│   │   ├── services/           # business logic + auth context
│   │   ├── repositories/       # data access + keyset pagination
│   │   ├── models/             # SQLAlchemy 2 ORM
│   │   ├── schemas/            # Pydantic v2 DTOs
│   │   ├── core/               # config, security (Clerk JWKS), providers
│   │   └── db/                 # engine, session, Base, mixins
│   └── tests/                  # pytest + pytest-asyncio
└── frontend/                   # Next.js 15 App Router
    └── src/
        ├── app/                # routes; (app)/ group for authenticated
        ├── features/           # feature modules (applications/, companies/, ...)
        ├── components/         # shared UI (shadcn primitives, combobox, command palette)
        ├── services/           # typed api-client + server actions
        ├── schemas/            # Zod schemas (shared with forms)
        └── types/              # TypeScript domain types mirroring the API
```

---

## 🗺 Roadmap

CareerOS ships a complete v1 core and is mid-redesign toward a workflow-first
v2. The full plan lives in [`docs/REDESIGN_ROADMAP.md`](docs/REDESIGN_ROADMAP.md).

**Shipped:**
- ✅ Application-centric create (company combobox + auto-create)
- ✅ Application workspace + narrative timeline
- ✅ Company dashboards
- ✅ Home dashboard (`/dashboard`)
- ✅ ⌘K global command palette
- ✅ Application tags (filtering + analytics axis)
- ✅ Split-screen branded auth
- ✅ 8-stage default pipeline (Saved → Preparing → Applied → … → Rejected)

**In progress / next:**
- 🔨 Custom timeline events (Email, Call, Follow-up, custom types)
- 🔨 Rejection reasons (structured capture for analytics)
- 🔨 Document Manager + Resume / Cover-Letter versioning with per-version
  performance analytics
- 🔨 Dream Companies (save & prioritise before applying)
- 🔨 Expanded analytics (by country, source, resume/CL performance, rejection
  reasons, response time)

**Deferred (until real data exists):**
- ⏸ AI Insights — analyse the user's data; never generate placeholder copy
- ⏸ LinkedIn networking module
- ⏸ Browser extension (one-click import from LinkedIn / Greenhouse / Lever / Workday)

---

## 📚 Documentation

- [Product spec](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database design](docs/DATABASE.md)
- [API contract](docs/API.md)
- [UI guidelines](docs/UI_GUIDELINES.md)
- [Redesign roadmap (v2)](docs/REDESIGN_ROADMAP.md)
- [Engineering guide (AGENTS.md)](AGENTS.md)

---

## 📝 Notes

- The frontend dev server compiles routes on first request — the initial page
  load can take ~10–25s on WSL2/Windows mounts. Subsequent loads are fast.
- Real Clerk keys are required for sign-in to work end-to-end; without them the
  app runs but API requests return 401. See `.env.example`.
- Built by [FayezL](https://github.com/FayezL) as a portfolio flagship.
