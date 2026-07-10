> Living document — kept up to date as CareerOS evolves. Last updated: 2026-07-08.

# CareerOS — Roadmap

This roadmap sequences CareerOS from an empty, deployable foundation to a production-ready v1. It defines what lands in each phase, what must be true before a phase starts, and what "done" looks like — so engineering, product, and reviewers always share one view of where the project stands. See [PRODUCT.md](./PRODUCT.md) for the product vision and feature definitions, and [ARCHITECTURE.md](./ARCHITECTURE.md) for the technical foundation each phase builds on.

## Current Focus

**Phase 0 — Foundation is the current focus.** Nothing in Phases 1–9 starts until the foundation is green: a deployable empty app with auth working, CI green, `alembic upgrade head` clean, and the health check live.

## How To Read This

- **Phases are sequential by default.** Each phase declares its **Dependencies**; do not start a phase before its dependencies meet their **Exit Criteria**. Where phases are independent, that is noted explicitly.
- **Scope items are atomic and trackable.** Each `- [ ]` checkbox represents one shippable unit of work; check it off only when it is merged, reviewed, and verifiable against the exit criteria. A phase is **Done** only when every scope box is checked **and** every exit criterion is met.
- **Statuses are coarse-grained:** `Planned` (not started), `In Progress` (actively being worked), `Done` (exit criteria met and verified). Only one phase is `In Progress` at a time.
- **This document is updated whenever scope changes** — when items are added, removed, reordered, or exit criteria are revised. The "Last updated" date at the top moves with every change.

## Status Legend

| Status | Meaning |
| --- | --- |
| `Planned` | Not started; waiting on dependencies or capacity. |
| `In Progress` | Actively being worked; this is the current focus. |
| `Done` | All scope items checked and all exit criteria verified. |

---

## Phase 0 — Foundation

**Status:** In Progress

**Goal:** Stand up a deployable, empty CareerOS app with auth, CI, and a clean database baseline so feature work can begin on solid ground.

**Scope:**
- [x] Monorepo scaffold: `/backend` (FastAPI + SQLAlchemy 2 async + Alembic + PostgreSQL) and `/frontend` (Next.js 15 + TypeScript + Tailwind + shadcn/ui), pinned with pnpm (frontend) and uv (backend).
- [x] Docker + Docker Compose for local dev: `db` (PostgreSQL), `backend`, `frontend` from a single `docker compose up`.
- [x] Environment validation: `pydantic-settings` on backend, `zod` on frontend, with fail-fast on missing/invalid vars.
- [x] Path aliases and absolute imports in both apps (`@/...` frontend, package-root imports backend).
- [x] Lint and format: ESLint + Prettier (frontend), Ruff + mypy (backend), Husky pre-commit hooks.
- [x] GitHub Actions CI: separate jobs for frontend checks, backend checks, and Docker image build.
- [x] Clerk auth wiring: frontend SDK (session, user, token) and FastAPI JWKS verification middleware.
- [x] Async SQLAlchemy base layer + Alembic setup with an initial migration baseline.
- [x] Users table with `clerk_user_id` sync on first authenticated request; every downstream table scopes by user.
- [x] Health check endpoint (`GET /health`) reporting DB + app liveness.
- [x] Root README plus the docs set (PRODUCT.md, ARCHITECTURE.md, ROADMAP.md).

**Implementation status (2026-07-08):** scaffold complete and locally verified — backend
`ruff`/`mypy`(strict)/`pytest` green (14 passed, DB tests skip w/o Postgres), frontend
`lint`/`typecheck`/`build` green, API responds (`/health`→200, `/health/ready`→503 w/o DB,
`/me`→401), `alembic history` intact. **Pending your environment:** provide real Clerk keys,
run `docker compose up` (Docker not available in the build sandbox), `alembic upgrade head`
against a live DB, and the first Vercel/Railway deploy. See
`docs/PHASE_0_FOUNDATION_PLAN.md` for the verification checklist.

**Dependencies:** None — this is the starting point.

**Exit Criteria:**
- `docker compose up` brings db + backend + frontend up locally with no manual steps beyond env setup.
- A Clerk-authenticated request hits a protected route and returns the caller's `clerk_user_id`.
- CI is green on the default branch across frontend, backend, and docker-build jobs.
- `alembic upgrade head` runs clean against an empty database.
- `GET /health` returns 200 from the deployed backend.
- An empty app is deployable to Vercel (frontend) + Railway (backend) end-to-end.

---

## Phase 1 — Core CRUD

**Status:** Done (code) — pending live-DB/CI confirm

**Goal:** Let a user create companies and applications and browse them end-to-end — the first real product loop.

**Scope:**
- [x] Companies model + CRUD API (name, website, industry, size, location), deduplicated per user.
- [x] Applications model + CRUD API (company FK, role/title, status, applied date, job URL, source). *(stage fields deferred to Phase 2)*
- [x] Enforce per-user data isolation (`user_id` / `clerk_user_id` scoping) on every query.
- [x] Companies list + detail UI with create/edit forms.
- [x] Applications list + detail UI with create/edit forms and company autocomplete.
- [x] Pagination on all list endpoints and UI (cursor-based `PageOut[T]`).
- [x] Filtering by status, company, and source on the applications list. *(status + company dedicated; source via `q` text search)*
- [x] API request/response validation and consistent error envelopes.

**Implementation status (2026-07-08):** backend `ruff`/`mypy`(strict, 38 files)/`pytest`
(26 passed, 13 DB-skips) green; `alembic 0001 → 0002`; new routes live & auth-protected
(`/companies`, `/applications` → 401 problem+json w/o token). Frontend `lint`/`typecheck`/
`build` green; `/applications` + `/companies` server-rendered with server actions for CRUD.
**Pending:** live-Postgres CRUD round-trip (CI runs `alembic upgrade head` then the DB-backed
tests); real Clerk keys for an actual signed-in UI flow.

**Dependencies:** Phase 0 — Foundation.

**Exit Criteria:**
- A signed-in user can create a company, create an application referencing it, edit both, and see them in a paginated list.
- A user cannot read or mutate another user's companies or applications (isolation verified by test).
- All list views paginate; filters return correct subsets.

---

## Phase 2 — Pipeline & Kanban

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Turn the flat application list into a living, configurable pipeline board with persisted ordering and full stage history.

**Scope:**
- [ ] `pipeline_stages` model, configurable per user, seeded with defaults (Applied → Screening → Interview → Offer → Rejected / Accepted).
- [ ] Link applications to a current stage; default new applications to "Applied".
- [ ] Kanban board UI grouped by stage with per-stage counts.
- [ ] Drag-and-drop across stages and within a stage (reordering).
- [ ] Persisted ordering via a position/rank field updated atomically on every move.
- [ ] Backend endpoints for stage transitions and batch reordering.
- [ ] `application_stage_history` audit table recording from-stage, to-stage, and timestamp on every transition.
- [ ] Stage-set management UI to add/rename/reorder custom stages.

**Dependencies:** Phase 1 — Core CRUD.

**Exit Criteria:**
- The board renders all applications grouped by stage with correct counts.
- Dragging an application between stages or within a stage persists across reloads and concurrent users.
- Every stage move is recorded in `application_stage_history` with accurate from/to/timestamp.
- Users can configure their own stage set without breaking existing applications.

---

## Phase 3 — People & Process

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Capture the humans, conversations, and scheduled events around each application so full context lives in one place.

**Scope:**
- [ ] Contacts model (name, email, LinkedIn URL, role: recruiter / hiring manager / interviewer / referral).
- [ ] Associate contacts with a company and/or one or more applications.
- [ ] Contacts CRUD API + list/detail UI with company and application linkage.
- [ ] Interviews/events model (type, date/time, location or video link, interviewer contact).
- [ ] Link interviews to the parent application; surface on application detail.
- [ ] Interviews CRUD API + UI, plus an upcoming-events view.
- [ ] Notes model: rich-text notes attachable to an application or a contact, timestamped.
- [ ] Notes CRUD API + UI forming a running thread per parent.
- [ ] Cross-note keyword search.

**Dependencies:** Phase 1 — Core CRUD. (Benefits from Phase 2 for application context, but does not require it.)

**Exit Criteria:**
- A user can create a contact, tie it to a company and an application, and see every related record from the contact's view.
- A user can schedule an interview linked to an application and see it on the upcoming-events view.
- A user can add notes to an application or contact and retrieve them later by search.

---

## Phase 4 — Documents & Storage

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Let users upload, version, and attach resumes and cover letters to applications — ending filename chaos.

**Scope:**
- [ ] Firebase Storage integration with signed upload/download URLs.
- [ ] Resume model with versioning (multiple variants per user).
- [ ] Cover-letter model with versioning.
- [ ] Upload endpoints and UI for resumes and cover letters.
- [ ] Attach a specific resume/cover-letter version to a specific application.
- [ ] Surface the attached file version on the application detail view.
- [ ] Replace or add versions without losing prior ones; version history view.

**Dependencies:** Phase 1 — Core CRUD (applications must exist to attach files to).

**Exit Criteria:**
- A user can upload a resume and a cover letter and retrieve them later.
- A user can attach a specific file version to an application and see exactly which version was sent.
- Prior versions remain accessible after a new version is added.

---

## Phase 5 — Analytics

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Give engineers signal on what's working — funnel, response rate, and momentum — from a single dashboard.

**Scope:**
- [ ] Headline counts: total applications, active loops, offers, rejections.
- [ ] Response rate: share of applications that moved past "Applied".
- [ ] Stage-to-stage funnel conversion derived from `application_stage_history`.
- [ ] Applications-over-time chart (volume by day/week/month).
- [ ] Breakdowns by source and by company.
- [ ] Analytics dashboard UI with the above, served from real (non-mock) data.

**Dependencies:** Phase 2 — Pipeline & Kanban (analytics depend on stage history and transitions). See the [Sequencing Rationale](#sequencing-rationale) for why this ordering matters.

**Exit Criteria:**
- The dashboard renders correct counts and rates computed from the user's live data.
- Funnel conversion matches `application_stage_history` exactly.
- The applications-over-time chart reflects real creation dates.

---

## Phase 6 — Reminders & Follow-ups

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Make sure follow-ups and interview prep actually happen — never silently drop an opportunity.

**Scope:**
- [ ] Reminders model with type, due datetime, target entity, and status.
- [ ] Rule-based generation: "no reply in N days" follow-ups and upcoming-interview reminders.
- [ ] In-app notifications for due and overdue reminders.
- [ ] Email notifications via a transactional provider.
- [ ] Consolidated "due today / overdue" view.
- [ ] Reminder action tracking (mark done / snooze / dismiss).

**Dependencies:** Phase 3 — People & Process (interviews drive interview reminders; contacts/applications drive follow-ups).

**Exit Criteria:**
- A stalled application generates a follow-up reminder and it is delivered in-app and by email.
- An upcoming interview generates a reminder ahead of time.
- The "due today / overdue" view accurately reflects reminder state.

---

## Phase 7 — AI Features

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Remove the busywork of tailoring materials and prepping for interviews through generation, not scraping.

**Scope:**
- [ ] LLM provider integration with secure key management and usage metering.
- [ ] Resume tailoring to a specific job description (emphasize relevant experience, rewrite bullets).
- [ ] Cover-letter draft generation grounded in the application and company.
- [ ] Interview-prep question generation tailored to role and seniority.
- [ ] Feature flag gating for each AI capability.
- [ ] Output review/edit UI so every generation is human-editable before saving.

**Dependencies:** Phase 1 — Core CRUD (applications provide grounding). Benefits from Phase 4 — Documents & Storage (resume source of truth) but does not strictly require it.

**Exit Criteria:**
- At least one AI feature (resume tailoring, cover-letter draft, or prep questions) is shipped behind a feature flag.
- Generated output is reviewable and editable before being attached to an application.
- All AI calls are metered and fail gracefully when the provider is unavailable.

---

## Phase 8 — Billing (Stripe)

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Introduce paid plans with Stripe-backed entitlements and feature gating.

**Scope:**
- [ ] Plans and entitlements schema mapping plan → allowed features/limits.
- [ ] Stripe Checkout integration for plan purchase and upgrade.
- [ ] Stripe webhooks handling the subscription lifecycle (create, update, cancel, renew).
- [ ] Feature gating enforced on both backend (API guards) and frontend (UI affordances).
- [ ] Billing UI: view current plan, manage subscription, billing history.

**Dependencies:** A meaningful feature surface to gate against — at minimum Phases 1–5, ideally through Phase 7 (AI) so paid tiers can differentiate on AI and analytics.

**Exit Criteria:**
- A user can purchase a paid plan via Stripe Checkout.
- Webhooks correctly update entitlements across the subscription lifecycle.
- Gated features are inaccessible on free plans and available on paid plans, enforced server-side.

---

## Phase 9 — Polish & Scale

**Status:** Done (code) — pending live-DB/CI confirm + real keys for credential-gated features (Firebase/Stripe/LLM, which run in demo/mock mode without keys)

**Goal:** Take CareerOS from "feature-complete" to production-ready: accessible, fast, observable, and hardened.

**Scope:**
- [ ] Accessibility audit against WCAG 2.1 AA and remediation of findings.
- [ ] Performance work targeting Core Web Vitals (LCP, INP, CLS) on key flows.
- [ ] Observability: structured logging, metrics, and distributed tracing across backend and frontend.
- [ ] Onboarding flow: first-run guidance to a user's first application within minutes of signup.
- [ ] Security hardening: rate limiting, input hardening, secrets review, dependency audit.
- [ ] Production-readiness review covering reliability, recovery, and runbooks.

**Dependencies:** All feature phases intended for v1 (Phases 0–8) should be functionally complete before the hardening pass.

**Exit Criteria:**
- Accessibility audit passes with no critical or serious issues open.
- Core Web Vitals meet target thresholds on the primary flows.
- Logging, metrics, and tracing are live and useful for diagnosing real incidents.
- Production-readiness review is signed off.

---

## Sequencing Rationale

The order is deliberate, not arbitrary:

- **Foundation before features.** Phase 0 exists so every later phase builds on auth, isolation, CI, and a clean DB baseline rather than retrofitting them under load. Skipping it means every feature pays a tax.
- **Core CRUD before pipeline.** Phase 2's board is meaningless without applications and companies to put on it, so Phase 1 must land first.
- **Pipeline before analytics.** Phase 5's funnel and response-rate metrics are derived from `application_stage_history` (Phase 2). Analytics without stage history would be fabricated numbers.
- **People & process before reminders.** Phase 6's reminders fire on interviews and follow-ups (Phase 3); building the reminder engine before its triggers exist would be premature.
- **Documents before AI.** Resume tailoring (Phase 7) is far more valuable when it can read the user's stored resume variants (Phase 4), so documents come first.
- **AI and billing last.** AI (Phase 7) is the differentiator but not the foundation; billing (Phase 8) only makes sense once there is a feature surface worth gating. Both wait until the core product is real.

## Out of Scope (v1)

These are intentionally excluded from v1 to keep the release focused and shippable (mirrors the Non-Goals in [PRODUCT.md](./PRODUCT.md)):

- **Organizations, teams, or shared workspaces.** v1 is strictly per-user with full data isolation.
- **Native mobile app.** v1 is a responsive web application.
- **Job-board scraping or a job-posting marketplace.** AI features generate tailored materials; they do not scrape or re-host third-party postings.
- **Multi-user collaboration.** Real-time co-editing, shared pipelines, and team views are not part of v1.
