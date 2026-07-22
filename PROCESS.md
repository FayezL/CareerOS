# CareerOS — Project Status & Vision

> A full-stack **Job Application Tracker & Career Management platform** I'm
> building as a portfolio flagship. This document tracks what's shipped, what's
> planned, and where the project is headed.
>
> ⚠️ **This is a work in progress.** The roadmap below reflects my current
> thinking — features, priorities, and scope **will change** as the project
> evolves. Nothing here is a final commitment; it's a direction.

---

## What this project is

CareerOS is a single place to run an entire job search: track applications from
bookmark to signed offer, manage companies and contacts, log every interaction
on a timeline, and surface analytics that actually help you adjust course.
It's built to **production SaaS standards** — strongly typed, tested, indexed,
paginated, per-user isolated, and containerised — not a CRUD demo.

**Stack:** Next.js 15 (App Router, React, TypeScript) · FastAPI (Python, async,
SQLAlchemy 2, Alembic) · PostgreSQL 16 · Clerk auth · Docker Compose.

---

## ✅ What's done so far

### Core platform (v1)
- **Auth** — Clerk JWT issued by the frontend, verified against Clerk's JWKS on
  the FastAPI backend (hand-written RS256 verification, not an SDK). Per-user
  data isolation on every query.
- **Clean-architecture backend** — `routes → services → repositories → models`,
  Pydantic v2 validation, 9 hand-written Alembic migrations, 14 tables, 36+
  indexes, keyset (cursor) pagination on every list endpoint.
- **Feature-based frontend** — Server Components for data, Server Actions for
  mutations, shadcn/ui, dark-mode-first, feature modules under `features/`.
- **Quality bar** — 122 backend tests (0 failing), `mypy --strict` clean,
  `tsc --strict` + eslint clean, Conventional Commits throughout.
- **Docker Compose** one-command dev environment (db + backend + frontend).

### Workflow redesign (in progress)
- **Application-centric create** — type a company name → it auto-creates or
  reuses the company. No "create a company first" prerequisite.
- **Application workspace** — a detail page with a narrative **timeline**
  (Applied → stage transitions → offer/rejection), a details sidebar, and
  documents.
- **Company dashboards** — `/companies/[id]` answers "what's my history with
  this company?" (applications, stats, contacts).
- **Home dashboard** — `/dashboard` with headline metrics, follow-up banner,
  and recent activity.
- **⌘K command palette** — global search across applications, companies, and
  contacts.
- **Application tags** — Remote, Visa Sponsorship, Python, Europe… inline
  multi-select with auto-create; the filtering + analytics axis.
- **Split-screen branded auth** — custom-styled Clerk sign-in/sign-up.
- **New 8-stage pipeline** — Saved → Preparing → Applied → Recruiter Contacted
  → Interview → Offer → Accepted → Rejected.

---

## 🔨 What I'm building next (current focus)

These are the features I'm actively working on. **Order and scope may shift.**

- **Custom timeline events** — beyond stage changes: Email Sent, Follow-up,
  Phone Screen, Take-home, System Design, Recruiter Viewed, and user-defined
  custom events. The workspace timeline becomes the full story of an
  application.
- **Rejection reasons** — structured capture (Visa, Salary, Experience, Culture
  Fit, Position Filled, No Feedback, Other) when an application is rejected,
  fed into analytics.
- **Document Manager** — replaces the basic documents section with categorised
  files: resumes, cover letters, certificates, references, visa documents.
- **Resume & Cover-Letter versioning** — link each application to the resume
  and cover letter version used, then track interview rate / offer rate /
  response rate **per version**.
- **Dream Companies** — save and prioritise companies you want to work for
  before applying (careers page, priority, applied-or-not).

---

## 🗺 Future roadmap (longer-term vision)

These are the bigger features I want to explore once the core workflow is
complete. **All of this is provisional — I expect the plan to change as I learn
what's most valuable.**

- **Expanded analytics** — applications by country and source, response rate
  by source/country, resume & cover-letter performance, most common rejection
  reasons, most successful technologies, average response time.
- **Career goals** — set targets ("apply to 150 jobs", "reach 200 recruiters",
  "get 15 interviews") and track progress on the dashboard.
- **Weekly review** — an auto-generated summary of the past 7 days:
  applications sent, interviews, rejections, offers, follow-ups needed, goal
  progress.
- **AI insights** — *deferred until enough real data exists.* The AI should
  analyse the user's actual history and surface patterns ("Resume V3 performs
  27% better", "most interview requests arrive within 8 days"), never generate
  placeholder copy.
- **LinkedIn networking module** — track connections, recruiters by country,
  pending/accepted invitations, messages sent vs replies. A flagship feature,
  but depends on deciding the data-source approach (manual logging vs import).
- **Browser extension** — one-click job import from LinkedIn, Greenhouse,
  Lever, and Workday (company, role, URL, description, salary, location).

---

## 📌 A note on scope

This is a **personal portfolio project**, not a funded startup. I'm building
it to demonstrate end-to-end engineering competence — architecture decisions,
database design, auth, testing, debugging, and product thinking. The feature
list above is ambitious on purpose: it reflects what a complete product *would*
be, and I'll ship as much of it as the learning (and the portfolio story)
justifies.

The most honest single sentence about the state of things: **the foundation is
production-quality and tested; the product surface is growing steadily; the
roadmap is a direction, not a contract.**

---

*Built by [FayezL](https://github.com/FayezL). See the
[main README](README.md) for the product overview and quickstart, and
[docs/REDESIGN_ROADMAP.md](docs/REDESIGN_ROADMAP.md) for the detailed phased
plan.*
