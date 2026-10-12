# D2 + D3: Resume & Cover-Letter Version Links — Design

**Status:** Approved
**Date:** 2026-10-13
**Depends on:** D1 Document Manager (shipped — grouped documents, revisions, `version_label`, `is_latest_version`)
**Roadmap:** `docs/REDESIGN_ROADMAP.md` Phase D, items D2 + D3

---

## 1. Scope

Link each application to the resume and cover-letter **versions** used for it,
and compute per-version performance analytics.

In scope:
- `applications.resume_version_id` / `cover_letter_version_id` FKs → root
  `documents.id` (`SET NULL` on delete)
- Pickers in the application create/edit form ("Resume used", "Cover letter used")
- Embedded refs on `ApplicationRead` so the UI shows names without extra fetches
- One analytics endpoint: per-version application/interview/offer/response-rate
  rows

Out of scope (deferred to A2, per decision):
- Analytics-page charts for resume/cover-letter performance
- Quick re-link actions in the workspace documents panel (form-only editing,
  per decision)
- Any linking UI on `/documents` itself

Semantics (from roadmap): **a version = one logical document group** (D1's
`parent_document_id` grouping). The FK always references a group **root**;
file revisions under it do not change the link.

---

## 2. Data model

Migration `0012_application_document_links.py` (additive):

| Column | Type | Constraints |
|---|---|---|
| `resume_version_id` | UUID, NULL | FK → `documents.id`, `ON DELETE SET NULL` |
| `cover_letter_version_id` | UUID, NULL | FK → `documents.id`, `ON DELETE SET NULL` |

Indexes (Postgres does not auto-index FKs; the analytics endpoint groups by
these columns):

- `ix_applications_resume_version_id` on `applications(resume_version_id)`
  where not null (partial index — only linked rows matter)
- `ix_applications_cover_letter_version_id` likewise

ORM (`models/application.py`): both columns + relationships
`resume_version` / `cover_letter_version` → `Document`
(`foreign_keys=` must be explicit — two FKs to the same table).

Downgrade: drop indexes, drop columns.

DB cannot express "root of type=resume" in a FK constraint — that is
service-level validation (§4.2).

---

## 3. Backend API

### 3.1 Schemas (`schemas/application.py`)

- `ApplicationCreate` + `ApplicationUpdate` gain:
  `resume_version_id: uuid.UUID | None = None`,
  `cover_letter_version_id: uuid.UUID | None = None`.
  In `ApplicationUpdate` these use `exclude_unset` semantics like every other
  field: absent = untouched, explicit `null` = clear the link.
- `ApplicationRead` gains the two ids plus embedded refs:

```python
class DocumentVersionRef(BaseModel):
    """Minimal document-group reference embedded on application reads."""
    id: uuid.UUID
    name: str
    version_label: str | None = None
```

### 3.2 Service validation (`services/application.py`)

Applied on create and on update, per non-null field (shared helper):

1. Load the document through the user-scoped `DocumentRepository`.
   Missing or foreign → `NotFoundError` (404), identical to `company_id`
   handling — existence is never leaked across users.
2. `document.parent_document_id is not None` → 422
   ("must be a root document").
3. `resume_version_id` requires `type == "resume"`; `cover_letter_version_id`
   requires `type == "cover_letter"` → 422 otherwise.

The repository's create/update pass the validated ids through; list/get
eager-load both refs (`selectinload`), consistent with company/stage/tags.

### 3.3 Analytics (`services/analytics.py`, `routes/analytics.py`)

`GET /api/v1/analytics/document-performance?type=resume|cover_letter`
(default `resume`; Literal-validated → 422 on anything else).

Response rows, one per linked document group, ordered by `applications` DESC:

```json
{
  "generated_at": "…",
  "type": "resume",
  "items": [
    {
      "document_id": "…",
      "name": "resume_stripe_payments.pdf",
      "version_label": "v2 — Stripe focus",
      "applications": 12,
      "interviews": 3,
      "offers": 1,
      "response_rate": 0.333
    }
  ]
}
```

- interview/offer counts use the same semantics as `summary`: distinct
  applications that ever **entered** a stage named `Interview` / `Offer`
  (case-insensitive), from stage history — grouped by the FK.
- `response_rate = (interviews + offers) / applications` rounded to 3 dp.
- Only groups referenced by ≥ 1 application appear (unused documents would be
  zero-noise). Unattributed applications are excluded from this view.

Implementation: one repository query joining applications (not deleted) →
documents (root, matching type) grouped by document id for the application
counts; stage-history distinct-application counts joined per document group
(reuses the `stage_entered_counts` pattern, partitioned by the FK).

---

## 4. Frontend

### 4.1 Types (`types/index.ts`)

```ts
export interface DocumentVersionRef {
  id: string
  name: string
  version_label: string | null
}
```

`Application` gains `resume_version_id`, `cover_letter_version_id`
(`string | null`) and `resume_version`, `cover_letter_version`
(`DocumentVersionRef | null`).

### 4.2 API client

- `getDocumentPerformance(type: "resume" | "cover_letter")` fetcher (no UI yet;
  A2 consumes it).
- Create/update payloads pass the two ids through unchanged.

### 4.3 Application form (`features/applications`)

- Two Select fields: "Resume used" and "Cover letter used", options =
  the user's document groups of the matching type (labelled
  `name — version_label`), with a "None" option; default None.
- Options are fetched **server-side** (page-level `listDocuments({ type })`,
  grouped; first N=100 groups) and passed into the form as props — no client
  fetch on mount.
- Editing sends the selected root id (or `null` to clear).
- The workspace detail view shows the linked names via the embedded refs
  (read-only display next to existing metadata).

---

## 5. Error handling

| Case | Result |
|---|---|
| Link id unknown or owned by another user | 404 problem+json |
| Link id is a revision (non-root) | 422 |
| `resume_version_id` → non-resume document (or CL mirror) | 422 |
| `type` query param invalid on analytics | 422 (Literal) |
| Linked document later deleted | FK `SET NULL`; refs read as `null` |

---

## 6. Testing

Backend (`tests/test_applications.py`, `test_analytics.py`):
1. Create with both links → persisted, read back with embedded refs.
2. Link to foreign document → 404.
3. Link to revision → 422; link to wrong type → 422 (both fields).
4. Update: change link; clear link with explicit `null`; absent = untouched.
5. Delete linked document → application read shows `null` refs (SET NULL).
6. Analytics: two linked resumes; one has apps that entered "Interview"/
   "Offer" stages, one only "Applied" → counts and rate per group correct;
   unlinked apps excluded; `type=cover_letter` mirror; invalid type → 422.

Frontend: typecheck / lint / build gates (form wiring verified by types).

---

## 7. Verification checklist

- `uv run --extra dev pytest`, `ruff check`, `mypy src` clean (pre-existing
  `fake_data.py` errors aside)
- Migration up/down both apply; ORM ↔ migration index parity
- `pnpm typecheck`, `pnpm lint`, `pnpm build`
- No N+1 on application lists (refs eager-loaded)
- Per-user isolation on the analytics endpoint
