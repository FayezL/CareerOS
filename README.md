# CareerOS

A full-stack job application tracker. Track every application from bookmark to
signed offer, manage companies and contacts, log every interaction on a
timeline, and see how your search is going at a glance.

> ⚠️ **Work in progress.** This is a personal project I'm actively building.
> What's described below reflects the current state, but features, scope, and
> priorities will change as it evolves. Nothing here is a final commitment.

---

## Why I built this

My job search was scattered across spreadsheets, browser bookmarks, sticky
notes, and DMs with recruiters. I'd forget to follow up, lose track of which
resume version I sent where, and have no real sense of how the search was
trending. The existing tools were either too shallow (a kanban board) or too
manual (a spreadsheet I had to maintain).

I wanted **one workspace** for the whole search — where every application
tells its full story, companies remember my history with them, and the
numbers I actually care about (response rate, interview rate, where I get
stuck) are visible without a spreadsheet.

I also wanted to build something end-to-end that exercises the full stack the
way real software does: a typed API, a real database with proper indexes and
migrations, real auth, tested code, and a UI that doesn't feel like a tutorial.

---

## What it does today

- **Track applications** end-to-end with a company, role, salary, source, job
  description, and status.
- **Type a company name** → it auto-creates or reuses the company. No separate
  "create a company first" step.
- **Application workspace** — each application has a narrative **timeline**
  (Applied → stage moves → offer/rejection) with custom events, importance
  levels, rejection reasons, and details.
- **Company pages** — see your full history with a company: how many
  applications, how many offers/rejections, who your contacts there are.
- **Dashboard** — "how is my search going?" with key numbers and recent activity.
- **⌘K command palette** — search across applications, companies, and contacts.
- **Tags** — Remote, Visa Sponsorship, Python, Europe… for filtering later.
- **Pipeline** — Saved → Preparing → Applied → Recruiter Contacted → Interview
  → Offer → Accepted → Rejected.

---

## Recently completed

- **Custom Timeline Events (F2)** — Full implementation of custom activity events
  including:
  - Native enum event types (Email, Call, Take-home, Recruiter Message, etc.)
  - Importance levels (Normal, Important, Milestone)
  - Follow-up date tracking for next actions
  - Rejection reason sync when events are marked "Rejected"
  - Chronological merge with stage history, interviews, and notes
  - Server-side validation and user isolation

---

## What I'm working on next

These are the features I'm currently building. **Order and scope may shift.**

- **Custom timeline events** — Email, Call, Follow-up, Take-home, Recruiter
  Viewed, and user-defined events with importance levels (not just stage changes).
- **Rejection reasons** — structured capture (Visa, Salary, Experience, etc.)
  for analytics.
- **Document Manager** — resumes, cover letters, certificates, references.
- **Resume & Cover-Letter versioning** — link each application to the version
  used, then compare performance per version.
- **Dream Companies** — save and prioritise companies before applying.

---

## Longer-term ideas (provisional)

These are directions I'm considering once the core workflow is solid. **All of
this may change.**

- Expanded analytics (by country, source, resume performance, rejection reasons)
- Career goals with dashboard progress
- Weekly review summaries
- AI insights — only once there's enough real data to analyse
- LinkedIn networking tracking
- Browser extension for one-click job import

---

## Tech stack

| Layer | What |
|---|---|
| Frontend | Next.js 15 (App Router) · React · TypeScript · Tailwind · shadcn/ui |
| Backend | FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | Clerk (JWT verified against Clerk's JWKS on the backend) |
| Dev | Docker Compose · pnpm · uv |

External providers (file storage, payments, AI, email) are **currently mocked** —
the interfaces exist but no live service is integrated.

---

## Run it locally

> Requires Docker Desktop (or the Docker Engine + Compose plugin).

```bash
git clone https://github.com/FayezL/Job-Dashboard.git
cd Job-Dashboard
cp .env.example .env   # add your Clerk keys — see docs/ARCHITECTURE.md
docker compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend (OpenAPI docs) | http://localhost:8000/docs |
| Postgres | `localhost:5433` · db/user/pass = `careeros` |

Without real Clerk keys the app runs but API requests return 401 — sign-in
needs a valid Clerk instance.

---

## Project structure

```
backend/    FastAPI + SQLAlchemy + Alembic (routes → services → repositories → models)
frontend/   Next.js App Router (Server Components + Server Actions + shadcn/ui)
docs/       Product, architecture, database, API, and redesign-roadmap docs
```

---

## More

- [Engineering case study (PROCESS.md)](PROCESS.md) — the how and why behind the build
- [Architecture](docs/ARCHITECTURE.md)
- [Redesign roadmap](docs/REDESIGN_ROADMAP.md)
- [Engineering guide (AGENTS.md)](AGENTS.md)

---

*Built by [FayezL](https://github.com/FayezL).*
