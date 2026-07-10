> Living document — kept up to date as CareerOS evolves. Last updated: 2026-07-08.

# CareerOS — Product

CareerOS is a modern Job Application Tracker built for software engineers — a single, fast, intelligent workspace to manage every application, contact, interview, and document from first click to signed offer. It turns a chaotic, spreadsheet-driven job search into a structured pipeline with AI-assisted drafting and real analytics on what actually works. v1 is a focused, per-user product: every engineer owns a private, isolated view of their search.

## Vision

Become the default operating system for a software engineer's career search — the place where applications, relationships, interviews, documents, and decisions live together. Long-term, CareerOS helps engineers not just track their search, but understand it: surfacing patterns, suggesting the next best action, and removing the busywork that stands between a strong candidate and the right offer. Today that means a best-in-class tracker with AI drafting and analytics; tomorrow it means a system that learns each engineer's strengths and market position and actively improves their outcomes.

## Target Users

CareerOS is designed for **software engineers running an active job search**, with a secondary audience of passive candidates.

- **Primary persona — "Active Engineer Seeker" (Andrei, 3–8 yrs experience)**
  Andei is a mid-to-senior engineer in an active, often multi-month search. He applies to 20–80 roles, talks to a dozen recruiters, juggles 4–8 active interview loops, and keeps separate cover letters and resume variants. He currently lives in a sprawling Google Sheet plus a notes app, loses track of who said what, and forgets to follow up. He wants order, momentum, and signal — not more busywork.

- **Secondary persona — "Passive Explorer" (Maya, open to the right role)**
  Maya is selectively exploring, taking 1–2 conversations a month. She wants a quiet, low-overhead place to log inbound opportunities and recruiters so that when the right one appears, she has full context in one place.

- **Tertiary persona — "New-Grad Systematizer" (Rohan, early career)**
  Rohan is graduating and applying at high volume with little experience managing a search. He benefits most from structure, reminders, and AI-assisted resume tailoring per role.

## Problem Statement

The modern software-engineering job search is high-volume, multi-channel, and long-running — and the tools to manage it are broken:

- **Spreadsheets don't model the search.** A sheet can hold a list of companies, but it collapses under the weight of contacts per company, multiple interviews per application, per-role resume variants, follow-up reminders, and stage transitions.
- **Context lives everywhere.** Recruiters ping on LinkedIn, interviews arrive by email, notes get typed into Notion, resumes live in Drive, and the offer ends up buried in Slack. Nothing connects.
- **Follow-ups die.** The single highest-leverage action in a search — following up — is the one candidates forget most, because nothing reminds them.
- **No signal on what works.** Engineers apply to dozens of roles blindly, with no visibility into response rate, funnel drop-off, or which sources convert. They optimize for volume instead of effectiveness.
- **Starting materials are painful to tailor.** Every role wants a slightly different resume and cover letter. Rewriting them by hand for 40 applications is exhausting and inconsistent.

## Value Proposition

CareerOS replaces the spreadsheet-and-sticky-notes workflow with a purpose-built system that models how a search actually works — and makes it smarter over time.

| Pain | Spreadsheet | CareerOS |
| --- | --- | --- |
| Application lifecycle | One flat row | Pipeline with configurable stages, drag-and-drop board |
| Multiple contacts per company | Cramped cells | Dedicated contacts tied to companies and applications |
| Interview scheduling | Calendar + memory | Typed interview events with reminders and links |
| Notes & prep | Scattered docs | Rich-text notes attached to applications or contacts |
| Resume variants per role | Filenames everywhere | Versioned resumes stored and attached to applications |
| Follow-ups | Forgotten | In-app and email reminders, never miss a window |
| Knowing what works | Guesswork | Funnel, response rate, and applications-over-time analytics |
| Tailoring materials | Manual, hours per role | AI-generated resume tailoring, cover-letter drafts, and prep questions |

**The differentiators:** AI-assisted drafting, real analytics on the funnel, and a data model built around software-engineer job hunts — not a generic CRM or a generic board.

## Core Features (v1)

### 1. Applications

**Purpose:** The atomic record of the job search — one application = one candidate × one role at one company.

**Key capabilities:**
- Create and edit applications with company, role/title, status, applied date, job URL, and source (e.g. LinkedIn, referral, company site).
- Reference a deduplicated company record so company data is edited once and reused.
- Move applications across pipeline stages via the board or a detail view.
- Full-text search and filtering by status, company, source, and date.
- Per-application history of stage transitions and timestamps.

**Done looks like:** An engineer can capture a new application in under 30 seconds, see it appear on the pipeline board, and reopen it weeks later with every related interview, note, contact, and resume version in one place.

### 2. Pipeline / Kanban Stages

**Purpose:** Visualize the entire search as a moving board so the engineer always knows what needs attention next.

**Key capabilities:**
- Default stages: Applied → Screening → Interview → Offer → Rejected / Accepted.
- Drag-and-drop reordering of applications across and within stages.
- Per-stage counts and quick visual cues for stale or high-priority items.
- Configurable stage set so engineers can model their own process (e.g. adding "Technical Screen" or "Team Match").

**Done looks like:** At a glance, the engineer can see how many applications sit at each stage and drag an application forward (or to Rejected) the moment a recruiter responds — the board is the search's heartbeat.

### 3. Companies Directory

**Purpose:** A single source of truth for company information, decoupled from individual applications.

**Key capabilities:**
- Deduplicated company records: name, website, industry, size, and location.
- One company can be referenced by many applications over time.
- Company view aggregates every application, contact, and note tied to that company.
- Edit once; every referencing application stays in sync.

**Done looks like:** The engineer never types "Google's website" twice — applying to a second role at the same company reuses the existing record and shows prior history instantly.

### 4. Contacts / Recruiters

**Purpose:** Capture and remember the humans behind each opportunity.

**Key capabilities:**
- People records with name, email, LinkedIn URL, and role (recruiter, hiring manager, interviewer, referral).
- Associate a contact with a company and/or one or more applications.
- See, per contact, the full thread of applications and notes they're tied to.

**Done looks like:** When a recruiter emails back three weeks after first contact, the engineer finds them in one search and sees exactly what was said and when — no scrolling through LinkedIn DMs.

### 5. Interviews & Events

**Purpose:** Never miss, mistime, or under-prepare for an interview again.

**Key capabilities:**
- Scheduled events with type: phone screen, video call, onsite, take-home, technical, final.
- Date/time, location or video link, and the interviewer contact.
- Linked to the parent application so context is one click away.
- Reminder generation that feeds the reminders engine.

**Done looks like:** Every confirmed interview lands on a single upcoming-events view with the join link, the interviewer, the prep notes, and a reminder — all without the engineer copy-pasting into a personal calendar.

### 6. Notes

**Purpose:** Capture the unstructured context — recruiter scripts, salary hints, behavioral answers, prep — in the place it belongs.

**Key capabilities:**
- Rich-text notes attachable to an application or a contact.
- Timestamped entries form a running conversation and prep log.
- Searchable across all notes so anything can be found by keyword.

**Done looks like:** The engineer can reconstruct the exact state of any conversation months later, and prep notes sit one click from the interview they were written for.

### 7. Resumes & Files

**Purpose:** Manage the inevitable reality of multiple resume and cover-letter variants without filename chaos.

**Key capabilities:**
- Upload and store multiple resumes and cover letters.
- Attach a specific resume version to a specific application so the engineer always knows which one was sent.
- Replace or add versions without losing prior ones.

**Done looks like:** The engineer opens an application, sees precisely which resume variant was submitted, and can pull it back to tailor for a similar role in seconds.

### 8. Analytics & Insights

**Purpose:** Turn the search from guesswork into signal — show what's working and what's stalling.

**Key capabilities:**
- Headline counts: total applications, active loops, offers, rejections.
- Response rate (applications that moved past "Applied") and stage-to-stage funnel conversion.
- Applications-over-time chart to see momentum and consistency.
- Breakdowns by source and company where relevant.

**Done looks like:** An engineer can answer "where is my search stalling, and which sources convert?" from a single dashboard — and adjust strategy the same week, not the next month.

### 9. Reminders & Follow-ups

**Purpose:** Make sure the highest-leverage action — following up — actually happens.

**Key capabilities:**
- In-app and email reminders for follow-ups (e.g. "no reply in 7 days") and upcoming interviews.
- Reminders generated automatically from application state, interviews, and configurable rules.
- A consolidated "due today / overdue" view.

**Done looks like:** The engineer never silently drops an opportunity because they forgot to nudge a recruiter or prep for a scheduled call.

### 10. AI Features

**Purpose:** Remove the busywork of tailoring materials and prepping for interviews — generation, not scraping.

**Key capabilities:**
- Resume tailoring to a specific job description (emphasize relevant experience, rewrite bullets to match).
- Cover-letter draft generation grounded in the application and company.
- Interview-prep question generation tailored to the role and seniority.

**Done looks like:** The engineer goes from "just saw a JD" to a tailored resume, a draft cover letter, and a set of likely interview questions in a few minutes — all reviewable and editable, none of it scraped from any marketplace.

## Non-Goals (v1)

To keep v1 sharp and shippable, the following are **explicitly out of scope** for this release:

- **No organizations, teams, or shared workspaces.** CareerOS v1 is strictly per-user with full data isolation. Each user owns only their own data.
- **No billing or subscriptions yet.** Stripe integration is deferred to a later phase; v1 is not gated by payment.
- **No native mobile app.** v1 is a responsive web application.
- **No job-board scraping marketplace.** AI features are about *generating* tailored materials, not scraping or re-hosting job postings from third-party boards.
- **No multi-user collaboration.** Real-time co-editing, shared pipelines, or team views are not part of v1.

## Jobs To Be Done

1. **When** I find a role I want to pursue, **I want to** log it in under a minute with all the context I'll need later, **so that** I don't lose track of it among dozens of others.
2. **When** a recruiter responds, **I want to** instantly move that application forward and see every prior interaction, **so that** I reply with full context instead of scrambling through my inbox.
3. **When** I have several active loops, **I want to** see them as a single pipeline with clear next steps, **so that** nothing stalls silently because I forgot about it.
4. **When** I haven't heard back on a strong application, **I want to** be reminded to follow up at the right moment, **so that** I don't lose an opportunity to a missed nudge.
5. **When** I land an interview, **I want to** see the date, join link, interviewer, and my prep notes in one place, **so that** I show up prepared and on time.
6. **When** I'm writing a resume for a specific role, **I want to** get a tailored draft and a cover letter, **so that** I spend minutes, not hours, per application.
7. **When** I'm deep into a search, **I want to** see my response rate and funnel, **so that** I can stop wasting effort on sources that aren't converting.
8. **When** I finally get an offer, **I want to** look back at the full history of that application, **so that** I can decide with complete context — and replicate what worked next time.

## Success Metrics

**North-star metric: Weekly Active Applications Touched** — the number of applications an active user creates, edits, or advances in a given week. It captures the core loop: the search is alive and moving, not abandoned.

**Supporting metrics:**

| Metric | Type | What it tells us |
| --- | --- | --- |
| Activation rate | Activation | % of new signups who log their first application within 24 hours of signup. |
| Pipeline advancement rate | Engagement | % of applications that move past "Applied" — a healthy search is in motion. |
| Reminder action rate | Engagement | % of reminders that lead to a follow-up or interview action within 48 hours. |
| AI feature adoption | Engagement | % of active users who generate at least one tailored resume, cover letter, or prep set per week. |
| Weekly retention (W4) | Retention | % of signed-up users still active in their fourth week — the search is long, we must hold attention. |
| Offer capture rate | Outcome | % of active users who record at least one Accepted offer within 90 days of their first application. |

## Competitive Landscape

CareerOS occupies a narrow, underserved intersection: a tracker built specifically for software engineers, with first-class analytics and AI generation layered on top.

| | Spreadsheet | Generic trackers (Teal, Huntr) | **CareerOS** |
| --- | --- | --- | --- |
| Built for software engineers | ✗ | Partial | ✓ |
| Models contacts, interviews, notes, files together | ✗ | Partial | ✓ |
| Pipeline / Kanban with configurable stages | Manual | ✓ | ✓ |
| Funnel & response-rate analytics | ✗ | Minimal | ✓ |
| AI resume tailoring, cover letters, prep questions | ✗ | ✗ | ✓ |
| Zero-setup, per-user, fast | ✗ | ✓ | ✓ |

**Positioning statement:** For software engineers running an active, multi-month search, CareerOS is the job-application tracker that turns chaos into a structured, data-driven pipeline — with AI-assisted drafting and real analytics that spreadsheets and generic trackers can't match.
