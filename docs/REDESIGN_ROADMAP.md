# CareerOS Redesign Roadmap (v2)

> Living plan, synthesizing the 15 architectural directives into a dependency-
> ordered sequence. Every feature integrates into existing surfaces (the
> application form, the workspace, the dashboard, analytics) — **no isolated
> CRUD pages**. The Application stays at the centre; companies, contacts,
> documents, tags, and timelines grow from it.

---

## Operating principles

1. **Application-centric.** Never make the user manage an entity before they
   can do the thing they actually want to do.
2. **Integrate, don't isolate.** New capability lands inside the surfaces the
   user already visits (form, workspace, dashboard, analytics) — not a new
   sidebar entry that becomes a CRUD page.
3. **No AI until there is data.** AI insights are deferred until enough real
   user data exists for analysis. AI must analyse, not generate placeholders.
4. **Finish the core workflow first.** The core job-search loop (saved →
   applied → interview → offer) is complete before expanding into networking.
5. **Real keys only when the feature ships.** The mock LLM/storage/billing
   providers stay mocked until the matching feature is genuinely being used.

---

## Status legend
- ✅ shipped
- 🔨 next (in priority order)
- ⏳ queued
- ⏸ deferred (data- or decision-dependent)

---

## What's shipped (the v1 redesign)

| # | Capability | Integration point |
|---|---|---|
| 1 | Application-centric create (company combobox + auto-create) | New Application form, NewMenu |
| 2 | Application workspace + narrative timeline | `/applications/[id]` |
| 3 | Company dashboards | `/companies/[id]` |
| 4 | Home dashboard | `/dashboard` (auth landing) |
| 7 | Global command palette | ⌘K / Ctrl+K from any authed page |

---

## The revised sequence

### Phase F — Foundation: enriching the Application
> Unblocks everything in analytics, versioning, and pipeline work. Pure
> additive schema, no UX churn.

- **F1 — Application Tags** 🔨
  New `tags` table (user-scoped, name + colour) and `application_tags` join.
  Surfaced as a multi-select in the New/Edit Application form, displayed as
  badges in the workspace + table rows, used as a filter on every list, and
  available as a `group_by` in analytics. **No standalone Tags page** — manage
  inline (rename/colour via the form's tag popover).
  *Predefined seed*: Remote, Hybrid, Onsite, Visa Sponsorship, Senior, Junior,
  Backend, Frontend, Fullstack, Python, Go, React, Startup, Europe, Germany,
  Netherlands, USA, UK.

- **F2 — Custom timeline events** 🔨
  New `timeline_events` table (type, title, note, occurred_at) **alongside**
  the existing `application_stage_history`. The workspace timeline merges both,
  ordered by time. Predefined `event_type` enum: `applied, recruiter_viewed,
  email_sent, follow_up, phone_screen, technical, take_home, system_design,
  offer, accepted, rejected, custom`. Added inline from the workspace
  ("Log activity"). **No separate Events page.**

- **F3 — Rejection reasons** 🔨
  Nullable `rejection_reason` (free text) + `rejection_reason_category` (enum)
  columns on `applications`. Set when moving an application to the Rejected
  stage (the stage-move dialog gains a "reason" select). Used in the timeline
  ("Rejected — Visa Sponsorship") and in analytics.
  *Predefined categories*: visa_sponsorship, lack_of_experience, salary,
  culture_fit, position_filled, no_feedback, other.

- **F4 — New default pipeline** 🔨
  New users are seeded with: **Saved → Preparing → Applied → Recruiter
  Contacted → Interview → Offer → Accepted → Rejected**. Existing users keep
  their stages; a one-time "adopt new defaults" affordance is offered in
  settings. "Saved" is the entry point that replaces the need for a separate
  wishlist for roles (Dream Companies, F7, is company-level, not role-level).

### Phase D — Documents, Resumes, Cover Letters
> Replaces the current Documents section with versioned, analytics-aware
> documents. The Application form gains a "Resume used" + "Cover letter used"
> picker; analytics reads these to compute per-version performance.

- **D1 — Document Manager** ⏳
  Expand `documents.type` enum: `resume, cover_letter, certificate, reference,
  visa, other`. Add `version_label` (e.g. "v3 — Python backend") and
  `is_latest_version`. The current `/documents` panel becomes a categorised
  Document Manager reachable from the sidebar and from each application
  workspace.

- **D2 — Resume version management** ⏳
  Documents of type `resume` are grouped into "versions" (a version = one
  logical resume, with optional file revisions). The Application model gains
  `resume_version_id`. Analytics computes interview rate / offer rate / response
  rate per resume version. **No separate "Resumes" page** — the Document
  Manager filtered to `type=resume` is the resume list.

- **D3 — Cover letter version management** ⏳
  Mirror of D2 for `type=cover_letter`. Application gains
  `cover_letter_version_id`. Same performance analytics.

### Phase C — Dream Companies
- **C1 — Dream Companies** ⏳
  A company can be starred as a "Dream Company" with `priority` (1–5),
  `careers_page_url`, and free-text notes. The Companies page gains a
  "Dream list" filter; the company dashboard surfaces the dream badge + priority
  + "Not applied yet / N applications". **Not a new entity** — a flag on
  `companies`, so it integrates with the existing company dashboard built in v1
  redesign Phase 3.

### Phase A — Expanded Analytics
> Needs F1 (tags), F3 (rejection reasons), and D2/D3 (resume/CL links) to be
> populated before the analytics are meaningful.

- **A1 — Tracking enrichment** ⏳
  Add `country` (derived from location), `first_responded_at` (timestamp set
  when an application first moves past "Applied" — enables response-time
  analytics), and ensure `source` is captured consistently.

- **A2 — Expanded analytics page** ⏳
  Add: Applications by Country, Applications by Source, Response Rate by Source,
  Response Rate by Country, Resume Performance, Cover Letter Performance, Most
  Common Rejection Reasons, Most Successful Technologies (derived from tags),
  Average Response Time. All filterable by date range (already supported).

### Phase G — Goals + Weekly Review
- **G1 — Career Goals** ⏳
  New `goals` table (metric, target, period, deadline). Seeded templates: "Apply
  to N jobs", "Reach N recruiters", "Get N interviews", "Receive N offers". The
  dashboard shows a progress card per active goal.

- **G2 — Weekly Review** ⏳
  A `/review` page (and optional email) summarising the past 7 days:
  applications sent, interviews, rejections (with reasons), offers, follow-ups
  needed, recruiters contacted, and goal progress. Generated on demand from
  existing data — no new schema.

---

## Deferred (explicitly per directive #1 and #2)

- **AI Insights** ⏸ — deferred until enough real user data exists. When built:
  analyse the data the user has already entered; surface patterns ("Resume V3
  performs 27% better", "most interview requests happen within 8 days"); never
  generate placeholder copy.
- **LinkedIn Networking** ⏸ — after Analytics + AI. The core job-search
  workflow must be complete first. Needs its own brainstorm: there is no public
  LinkedIn API, so this is manual weekly logging + CSV import. New `network`
  module with its own schema.

## Future (not in active scope)
- **Browser Extension** — one-click import from LinkedIn / Greenhouse / Lever /
  Workday. Captures company, role, URL, description, salary, location. Tracked
  here as a future roadmap item; not started.
- **Smart Job Import** (paste-URL → auto-extract) — deferred until LLM keys are
  in scope or a scraper is justified; the extension (above) is the better UX
  when it ships.
- **Smart Reminders** — backend rules engine (no-activity-14-days, etc.).
- **Contacts auto-link** — recruiter creation inline in the application flow.
  Small; will slot in alongside F1.

---

## Follow-ups (technical debt from the v1 redesign)
1. **Test-DB isolation** — the backend test suite currently runs against the
   Docker dev DB and truncates real data. Fix: dedicated `careeros_test`
   database (recommended) or embedded `pgserver`.
2. **Contacts detail page** (`/contacts/[id]`) — the command palette links
   contacts to the list today.
3. **WSL → Windows filesystem** makes `next build` slow/flaky; documented in
   AGENTS.md but unresolved.

---

## Integration map (where each feature lands)

| Capability | Form | Workspace | Dashboard | Analytics | Command palette |
|---|---|---|---|---|---|
| Tags | multi-select | badges | top-N | group_by | searchable |
| Timeline events | — | add + display | recent activity | — | — |
| Rejection reason | on reject | timeline entry | — | breakdown | — |
| Resume version | picker | chip + link | — | performance | searchable |
| Cover letter version | picker | chip + link | — | performance | searchable |
| Dream company | star toggle | badge | count | — | searchable |
| Goals | — | — | progress cards | — | — |
| Pipeline stages | status select | timeline | distribution | funnel | — |

---

## Build order (what to do next)

1. **F1–F4** (foundation migration: tags + timeline events + rejection reasons +
   new default pipeline). One migration, additive only.
2. F1 endpoints + UI (tag multi-select in the form; tag filter on lists).
3. F2 endpoints + UI (inline "Log activity" in the workspace).
4. F3 + F4 (rejection-reason select on stage move; pipeline seeding change).
5. D1–D3 (Document Manager + resume/CL versioning + application links).
6. C1 (Dream companies flag + dashboard integration).
7. A1–A2 (tracking fields + expanded analytics).
8. G1–G2 (goals + weekly review).
9. Then: AI Insights (when data exists), LinkedIn (after that).
