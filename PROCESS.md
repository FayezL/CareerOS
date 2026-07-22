# Engineering Case Study — CareerOS

> How CareerOS was architected, debugged, and shipped. Written as an engineering
> record for portfolio review — this documents the *process and judgment*, not
> the feature list (see [README.md](README.md) for that).

---

## The thesis

Most "job tracker" portfolio projects are CRUD apps: a forms-over-tables UI
glued to an ORM. I set out to build the opposite — a **production-shaped SaaS**
where every layer (schema, API, auth, frontend, infra) is engineered the way a
real startup team would ship it: strongly typed, tested, indexed, paginated,
isolated per tenant, and verifiable.

The bar wasn't "it works" — it was **"can I prove it works, and can I prove
*why* the design is sound."**

---

## Architecture decisions (and the trade-offs)

### 1. A separate FastAPI backend instead of Next.js Route Handlers

**Decision:** Next.js for the frontend only; a standalone async FastAPI service
for the API.

**Why:** Route Handlers couple the API to the Node process and to JavaScript.
A Python backend gives clean async SQLAlchemy 2, first-class Pydantic v2
validation, OpenAPI for free, and a language ecosystem (uv, mypy, pytest)
that I wanted for the data layer. It also forces a **real network boundary**
between client and server — which is where production auth actually lives.

**Trade-off acknowledged:** two deploy targets (Vercel + Railway) and a
network hop the frontend must cross. Worth it for the separation of concerns
and the typing story.

### 2. SQLAlchemy 2 + Alembic, not Prisma

**Decision:** Hand-written ORM models + hand-written, numbered migrations.

**Why:** Prisma's generator hides SQL. For a project where **indexes are the
performance story**, I needed to reason about (and verify) exactly what hits
the database — composite indexes, keyset pagination cursors, FK indexing gaps
in Postgres, `ondelete` cascades. You can't `EXPLAIN ANALYZE` what you can't
see.

**Trade-off:** more code than Prisma. Accepted because the whole point was to
demonstrate database engineering competence.

### 3. Clerk JWT forwarded as a Bearer token, verified by hand

**Decision:** Clerk issues the JWT from the frontend; the FastAPI backend
verifies the RS256 signature against Clerk's published JWKS (cached with a
TTL), checks the `iss` claim, requires `exp`/`iss`/`sub`, and resolves the
local `User` row — **no magic SDK on the backend.**

**Why:** I wanted to actually understand the auth flow, not call
`@clerk/express` and hope. The verification is ~130 lines and readable. It
also means the backend is provider-agnostic — swapping Clerk for Auth0 or
Cognito is a JWKS-URL change.

**Trade-off:** more code than a middleware import. Accepted because "I can
debug auth" is a claim this project backs up (see the debugging section).

### 4. Per-user multi-tenancy, hard-scoped

**Decision:** every tenant-scoped table carries `user_id`; every repository
query filters by it; cross-user isolation is tested explicitly.

**Why:** v1 has no orgs/teams, so the isolation primitive is the user. Getting
this right at the repository layer means a route can't accidentally leak data
even if it tries — the scope is structural, not a convention someone remembers.

### 5. Clean architecture on the backend, feature-based on the frontend

**Decision:** `routes → services → repositories → models` (dependencies point
inward only). Frontend modules under `features/<feature>/` with shared
primitives in `components/`.

**Why:** each layer is independently testable and replaceable. Routes are thin
(parse, call service, return typed DTO). Services own transactions + auth
context. Repositories own data access + pagination. Nothing reaches across.

---

## Debugging case studies

These are the bugs that taught the most. Each was solved by **finding the root
cause before touching a fix** — never by guess-and-check.

### Case 1: "fetch failed" on every page after login

**Symptom:** the user signed in successfully (Clerk session created, 1 user +
1 company in the DB), but every authenticated page showed "Couldn't load
applications." Backend logs showed **zero requests arriving**.

**Investigation:** I instrumented both sides — a `console.log` in the frontend
`apiFetch` and a structured log on the backend's auth-failure handler. The
frontend log proved `getToken()` returned a token (`hasToken: true`), but the
backend still saw nothing. The response time on the failed calls was ~0ms.

**Root cause:** Server Components run **inside the frontend Docker container**.
The api-client fetched `http://localhost:8000` — but inside that container,
`localhost:8000` is the container itself (connection refused), not the host's
backend. The fetch never left the container.

**Fix:** introduced `API_INTERNAL_URL` (`http://backend:8000/api/v1`, the
Docker-network hostname) for server-side fetches, keeping `NEXT_PUBLIC_API_URL`
(`localhost:8000`) for the browser. One env var, documented in the compose
file. ([commit `f2e0ebc`](https://github.com/FayezL/Job-Dashboard/commit/f2e0ebc))

**Lesson:** in SSR + containers, the server and the browser live in different
network namespaces. The URL that's correct for one is wrong for the other.

### Case 2: every list endpoint was doing an in-memory sort

**Symptom:** pagination worked, but I noticed no index matched the keyset
query's `ORDER BY created_at DESC, id DESC`.

**Investigation:** I ran `EXPLAIN ANALYZE` against 5,000 seeded rows. The plan
showed `Seq Scan → Sort (quickstore, 25kB)` — Postgres materialised every row
the user owned, sorted them in memory, then applied LIMIT. O(n log n) per
page, growing with the user's history.

**Fix:** a migration adding `(user_id, created_at DESC, id DESC)` composite
indexes to the 6 paginated tables that lacked them. Re-ran `EXPLAIN ANALYZE`:
now an `Index Scan` that walks the index in order and **stops at LIMIT** — 21
rows touched, 3 buffer hits, **0.077ms** execution. ([commit `a58d933`](https://github.com/FayezL/Job-Dashboard/commit/a58d933))

**Lesson:** "it works" and "it scales" are different claims. The first is
obvious; the second needs `EXPLAIN`.

### Case 3: the test suite was silently destroying real data

**Symptom:** after running the backend tests, the user's signed-in session
vanished — 0 users in the DB.

**Investigation:** the test `conftest.py` truncated every table before each
test for isolation. It connected to the same Postgres the app used
(`localhost:5432`, later `5433`). So "run the tests" meant "wipe the dev
database." The skip-when-unreachable guard meant this failed *silently* — DB
tests just showed as skipped, masking the problem.

**Fix (in flight):** a dedicated test database (or embedded Postgres) so the
truncate-for-isolation can never touch real data. The immediate mitigation is
operational: never run the host test suite against the Docker dev DB; run it
inside the backend container instead (where it hits `db:5432` cleanly).

**Lesson:** test isolation and test-target selection are security concerns, not
just convenience. A fixture that truncates is a footgun aimed at your data.

### Case 4: the landing page 404'd for anonymous visitors

**Symptom:** `GET /` returned a 404 instead of the marketing landing page —
but only for logged-out users, and only after Clerk was wired up.

**Root cause:** the Clerk middleware protected **every** route except
`/sign-in` and `/sign-up`. The root page (`app/page.tsx`) is a public landing
page that does its own `auth()` check + redirect, but the middleware blocked
anonymous visitors before the page ran. `auth.protect()` then rendered the
not-found boundary instead of redirecting.

**Fix:** added `/` to the public-route matcher — one line. Verified `GET /`
returns 200 with the landing content for anonymous visitors. ([commit `31e9e96`](https://github.com/FayezL/Job-Dashboard/commit/31e9e96))

**Lesson:** middleware runs before your page. A route can be "public-by-design"
in code and "protected-by-accident" in middleware.

---

## Performance engineering

| Concern | Approach | Evidence |
|---|---|---|
| List endpoints scale | Keyset (cursor) pagination, not offset | `BaseRepository.list_paginated` — `(created_at DESC, id DESC)` cursor, `LIMIT n+1` to detect `has_more` |
| Pagination is index-backed | Composite index on the keyset per table | `EXPLAIN ANALYZE`: Index Scan, 3 buffers, 0.077ms @ 5k rows |
| Foreign keys don't seq-scan | Postgres doesn't auto-index FKs — I added them | 36+ indexes across 14 tables, declared on both ORM + migration |
| N+1 on serialised relations | `selectinload` where a list embeds relations | `Application.company`, `.current_stage`, `.tags` eager-loaded |
| Backend connection churn | `NullPool` in tests (fresh loop per test); `QueuePool` in prod | env-aware pool in `db/session.py` |

---

## Quality methodology

**Evidence before assertions.** I never claim a task is done without running
the verification and pasting the output. The standard before closing any task:

- Backend: `uv run --extra dev pytest` passes, `ruff check .` clean,
  `mypy src` (strict) clean.
- Frontend: `pnpm lint` clean, `pnpm typecheck` clean.
- Migrations: `alembic upgrade head` applies; ORM models and migrations agree
  on indexes/constraints.
- Per-user isolation holds (no cross-user leak; `user_id` scoped + tested).

**Strict typing everywhere.** `mypy --strict` on 93 backend files; `strict`
tsconfig on the frontend. No `any`, no untyped dicts for domain data.

**Conventional Commits with scopes** (`fix(docker):`, `perf(db):`,
`feat(frontend):`, `feat(api):`) — the history reads as a changelog.

---

## By the numbers

| Metric | Value |
|---|---|
| Commits | 27 |
| Alembic migrations | 9 (hand-written, upgrade + downgrade tested) |
| Database tables / indexes | 14 / 36+ |
| Backend source files (Python) | 93 |
| Frontend source files (TS/TSX) | 97 |
| Backend tests | 122 passing, 0 failing |
| Lint / type coverage | ruff clean · mypy strict clean · eslint clean · tsc strict clean |
| API surface | 14 routers, all cursor-paginated, all auth-gated |
| Redesign phases shipped | 6 of 10 (v1 core complete; v2 workflow redesign in progress) |

---

## What I'd do differently

- **Test-database isolation from day one.** The truncate-against-dev-DB footgun
  should have been designed out early (dedicated `careeros_test` DB or embedded
  Postgres), not discovered when it wiped real data.
- **The WSL2 ↔ Windows filesystem** makes Next.js production builds slow/flaky
  on this dev machine. A native-Linux dev box or devcontainer would have saved
  real time across the project.
- **Screenshot the UI as I ship each phase.** I built five redesign phases
  before pausing for visual verification — fine for velocity, but a
  screenshot-per-phase gallery would strengthen the portfolio.

---

## How to read the engineering trail

The commit history is the most honest record. Notable entries, newest first:

- `db6e015` F1 application tags (auto-resolve + seeding + 122 tests)
- `0ef7381` v2 foundation migration (tags, timeline events, rejection reasons)
- `f2bbdeb` ⌘K command palette (global search across entities)
- `a58d933` **keyset-pagination composite indexes** (the EXPLAIN ANALYZE win)
- `f2e0ebc` **API_INTERNAL_URL** (the Docker SSR networking fix)
- `31e9e96` Clerk public-route fix (landing-page 404)
- `7d47898` DB test isolation + 3 runtime bugs found via real-PG verification
- `b418633` feature-based frontend refactor + dark-mode theming

Full context for each lives in the commit messages.

---

*Built and documented by [FayezL](https://github.com/FayezL). The product
README is [here](README.md); the full v2 redesign plan is in
[docs/REDESIGN_ROADMAP.md](docs/REDESIGN_ROADMAP.md).*
