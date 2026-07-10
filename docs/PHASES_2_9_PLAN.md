# Phases 2–9 — Implementation Plan (bulk)

> **Living document.** Last updated: 2026-07-08.
> Builds on Phase 0 (foundation) + Phase 1 (companies/applications CRUD).
> **Reference:** DATABASE.md · API.md · UI_GUIDELINES.md · ROADMAP.md.

**Cross-cutting rule:** every new content table carries `user_id` and is scoped by the
authenticated user. Migrations are sequential: 0003 (pipeline), 0004 (contacts/interviews/notes),
0005 (documents), 0006 (reminders), 0007 (subscriptions). Credential-dependent integrations
(Firebase, Stripe, LLM, email) are behind provider interfaces with **mock/noop implementations**
selected when env vars are absent — so the app compiles, tests pass, and builds are green with
zero real keys; runtime just needs the keys to use the real provider.

## Phase 2 — Pipeline & Kanban
- B: `pipeline_stages`, `application_stage_history`; add `applications.current_stage_id` (FK RESTRICT, nullable). Endpoints: `GET/POST/PATCH/DELETE /pipeline-stages`, `POST /pipeline-stages/reorder`, `POST /applications/{id}/move`, `GET /applications/{id}/history`. Seed default stages lazily per user.
- F: `/pipeline` board with `@dnd-kit` (columns=stages, cards=applications), move on drop, stage CRUD.

## Phase 3 — Contacts, Interviews, Notes
- B: `contacts`, `interviews` (+ `interview_type` enum), `notes`. Full CRUD, user-scoped.
- F: `/contacts`, `/interviews` lists + forms; notes on application detail.

## Phase 4 — Documents & Storage
- B: `documents` (+ `document_type` enum); `StorageClient` interface → `LocalStorageClient` (FS) or `FirebaseStorageClient` (firebase-admin) by env. `POST /documents` (returns upload target), `GET/DELETE`.
- F: upload + document list on application detail.

## Phase 5 — Analytics
- B: `GET /analytics/{summary,funnel,over-time}` (read-only, from applications + stage history).
- F: `/analytics` dashboard with `recharts` (funnel bar, over-time area, summary cards).

## Phase 6 — Reminders
- B: `reminders`; CRUD + `POST /reminders/{id}/{complete,snooze}`. `Notifier` interface → log/email. A `POST /reminders/dispatch-due` (dev/worker) dry-run.
- F: reminders list on dashboard.

## Phase 7 — AI
- B: `POST /ai/{tailor-resume,cover-letter,interview-prep}`; `LLMClient` → `MockLLMClient` (deterministic) or `OpenAICompatibleClient` by `LLM_API_KEY`. Feature-flagged.
- F: `/ai` tools (server-action calls); gated by flag.

## Phase 8 — Billing
- B: `subscriptions`; `POST /billing/{checkout,portal}`, `POST /webhooks/stripe` (sig verify). `require_plan` dependency. `BillingProvider` → noop or Stripe by `STRIPE_*`.
- F: `/settings/billing` (mock upgrade).

## Phase 9 — Polish
- A11y pass, consistent loading/empty/error states, metadata/SEO, rate-limit middleware, structured request logging, onboarding empty states, global 404.

## Verification per round
- Backend: `ruff check` · `ruff format --check` · `mypy src` · `pytest -q` (DB tests skip locally) · `alembic history`.
- Frontend: `pnpm lint` · `pnpm typecheck` · `pnpm build`.
- Controller in-process smoke: every new route returns 401 problem+json without a token.
