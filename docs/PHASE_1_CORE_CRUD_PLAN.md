# Phase 1 — Core CRUD Implementation Plan

> **Living document.** Last updated: 2026-07-08.
> **Scope:** Companies + Applications CRUD, end-to-end (backend + frontend). Pipeline/Kanban
> is Phase 2, so `applications.current_stage_id` + `pipeline_stages` + stage history are
> intentionally DEFERRED. **Reference:** DATABASE.md · API.md · UI_GUIDELINES.md · ROADMAP.md.

**Goal:** A signed-in user can create, list, view, edit, and soft-delete companies and
applications through the UI, backed by a tested FastAPI layer.

**Architecture:** Same as Phase 0 — FastAPI canonical API, Clerk JWT, async SQLAlchemy,
`routes → services → repositories → models`. Frontend reads in Server Components, mutates
via Server Actions (server-side `auth().getToken()` → Bearer → api-client).

**Key deviation from DATABASE.md (intentional):** `applications` is created in Phase 1
**without** `current_stage_id` and without the `pipeline_stages` / `application_stage_history`
tables. Those land in Phase 2. Phase 1 `application_status` enum =
`active | archived | rejected | accepted`.

---

## Backend tasks (`/backend`)

New/modified files:
- `models/company.py`, `models/application.py` (+ `application_status` enum via `sa.Enum`)
- `schemas/company.py` (CompanyCreate/Read/Update), `schemas/application.py` (ApplicationCreate/Read/Update), `schemas/common.py` (+ `PageOut[T]` cursor envelope)
- `repositories/base.py` extend with `list_paginated(user_id, cursor, limit, filters)` returning `(items, next_cursor)`; `repositories/company.py`, `repositories/application.py`
- `services/company.py`, `services/application.py`
- `api/v1/routes/companies.py`, `api/v1/routes/applications.py`
- `api/v1/routes/__init__.py` aggregate router
- `main.py` register new routers
- `alembic/versions/0002_companies_applications.py` (create both tables, indexes, `application_status` enum, `updated_at` trigger reuse)
- tests: `test_companies.py`, `test_applications.py` (CRUD + 404 + isolation between users + pagination), DB-backed via `require_db`; unit tests for cursor encoding.

### Endpoint contract (matches API.md)
- `GET /api/v1/companies?limit=&cursor=&q=` → `{items, next_cursor}`
- `POST /api/v1/companies`, `GET /api/v1/companies/{id}`, `PATCH .../{id}`, `DELETE .../{id}` (soft)
- `GET /api/v1/applications?limit=&cursor=&status=&company_id=&q=&sort=`
- `POST /api/v1/applications`, `GET /api/v1/applications/{id}` (embed company), `PATCH`, `DELETE` (soft)

Schema (Phase 1):
- `companies`: id, user_id, name, website, industry, size, location, linkedin_url, notes, created_at, updated_at, deleted_at. Unique (user_id, lower(name)).
- `applications`: id, user_id, company_id (FK RESTRICT), role_title, status (enum), job_url, job_description, source, salary_min, salary_max, salary_currency, applied_at, created_at, updated_at, deleted_at. Indexes (user_id), (user_id,status), (user_id,applied_at), company_id.

## Frontend tasks (`/frontend`)

New/modified:
- `src/app/(app)/layout.tsx` — authenticated app shell (sidebar per UI_GUIDELINES: Dashboard, Applications, Companies; UserButton).
- `src/app/(app)/companies/page.tsx` (list, server) + `src/features/companies/{actions.ts, company-form.tsx, columns.tsx}`
- `src/app/(app)/applications/page.tsx` (list, server) + `src/features/applications/{actions.ts, application-form.tsx, columns.tsx}`
- `src/app/page.tsx` redirect signed-in users to `/applications`
- shadcn primitives added via CLI: `table dialog input label select textarea badge card dropdown-menu form`
- `src/lib/api-client.ts` already supports server-side Bearer calls; add typed helpers per resource.
- Server Actions: `createCompany`, `updateCompany`, `deleteCompany`, `createApplication`, `updateApplication`, `deleteApplication` — each `use server`, calls api-client, `revalidatePath` on success.

## Verification checklist
- Backend: `uv run ruff check .` · `ruff format --check .` · `mypy src` · `pytest -q` (DB tests pass in CI with `alembic upgrade head`)
- Frontend: `pnpm lint` · `pnpm typecheck` · `pnpm build` (must pass with no real Clerk keys)
- New migration applies (verified in CI; locally `alembic history` shows `0001 -> 0002`)
- In-process smoke (controller): `/api/v1/companies` →401 w/o auth; create company via mocked-JWT → 200; list returns it.

## Out of scope (Phase 2+)
pipeline_stages, kanban, stage moves/history, contacts, interviews, notes, documents, analytics.
