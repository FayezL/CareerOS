# D1 — Document Manager: Design Specification

- **Date:** 2026-08-24
- **Status:** Approved (pending implementation)
- **Depends on:** none (replaces/extends the v1 Documents feature)
- **Blocks:** D2 (resume versioning), D3 (cover letter versioning), A2 (per-version analytics)
- **Roadmap:** `docs/REDESIGN_ROADMAP.md` → Phase D, item D1

---

## 1. Problem & Goal

The current Documents feature (`documents` table + `/documents` panel on the
application workspace) treats every upload as a standalone file with only three
types (`resume`, `cover_letter`, `other`) and an unused per-row integer
`version`. Job seekers accumulate **revisions** of the same logical document
("my Python-backend resume v3") and documents of more kinds (certificates,
references, visa documents). D1 turns documents into **grouped, versioned,
categorised** resources without changing the upload flow.

**Goals**

1. Six document types: `resume, cover_letter, certificate, reference, visa, other`.
2. Explicit revision grouping: a logical document (root) with N file revisions.
3. A dedicated **Document Manager** page (`/documents`), reachable from the
   sidebar and linked from each application workspace.
4. DB-enforced invariants: exactly one "latest" per group; no version-counter
   collisions — even under concurrency or crashed transactions.

**Non-goals (deferred)**

- `resume_version_id` / `cover_letter_version_id` on `applications` (D2/D3).
- Per-version performance analytics (A2).
- The "Resume used" / "Cover letter used" picker in the Application form (D2/D3).
- Cross-device sync, sharing, or document editing.

---

## 2. Data Model

### 2.1 Columns (all additive)

| Column | Type | Default | Notes |
|---|---|---|---|
| `parent_document_id` | `UUID NULL` | — | FK → `documents.id ON DELETE CASCADE`. NULL = root document. |
| `version_label` | `VARCHAR(255) NULL` | — | User's friendly name, e.g. `"v3 — Python backend"`. |
| `is_latest_version` | `BOOLEAN NOT NULL` | `true` | Exactly one per group (DB-enforced, §2.3). |

### 2.2 Type enum expansion

`document_type` gains `certificate`, `reference`, `visa` via
`ALTER TYPE … ADD VALUE IF NOT EXISTS`. Existing rows are untouched.

### 2.3 Indexes

```sql
-- Group key = COALESCE(parent_document_id, id): root id for every row.
CREATE UNIQUE INDEX ix_documents_one_latest_per_group
  ON documents (COALESCE(parent_document_id, id))
  WHERE is_latest_version = true;

CREATE UNIQUE INDEX ix_documents_group_version
  ON documents (COALESCE(parent_document_id, id), version);

CREATE INDEX ix_documents_user_type_created_at
  ON documents (user_id, type, created_at DESC, id DESC);

CREATE INDEX ix_documents_parent_document_id
  ON documents (parent_document_id);

DROP INDEX ix_documents_user_id_type;  -- subsumed by the composite above
```

The two **partial unique** indexes are the invariants:

- `ix_documents_one_latest_per_group` — makes "zero or two latests in one
  group" impossible at the storage layer, regardless of application bugs.
- `ix_documents_group_version` — makes the `max(version)+1` counter
  race-free: two concurrent revision inserts for the same group compute the
  same next version; the loser violates the index and surfaces as `409`.

`ix_documents_user_type_created_at` backs the Document Manager list
(user scope + type filter + keyset pagination on `(created_at DESC, id DESC)`).

`ix_documents_parent_document_id` backs `GET /documents/{id}/revisions` and
the `revisions_count` correlated subquery — both filter directly on
`parent_document_id`, which the expression indexes cannot serve (their
leading column is `COALESCE(...)`).

The ORM `Document.__table_args__` is updated in the same change so the model
and migration never drift (AGENTS.md rule). Note the two expression/partial
indexes must be declared with `sa.text("COALESCE(parent_document_id, id)")`
key expressions and `postgresql_where=`/`sqlite_where=` predicates — plain
column lists are not enough for these.

### 2.4 Grouping semantics

- **Root:** `parent_document_id IS NULL`, `version = 1`,
  `is_latest_version = true` (until a revision exists).
- **Revision:** `parent_document_id = <root id>`. Insert transaction:
  1. Load parent **via `repo.get(user.id, parent_id)`** → cross-user parent
     yields `None` → `404` (no existence leak).
  2. Reject if the parent is itself a revision (`parent.parent_document_id
     IS NOT NULL`) → `409`. Depth-1 trees only.
  3. `version = max(version in group) + 1`.
  4. Set previous latest `is_latest_version = false`; insert new row with
     `is_latest_version = true`.
- **Immutable inheritance:** revisions copy `user_id`, `type`,
  `application_id` from the root at creation. Per-revision fields: file bytes
  (`firebase_path` etc.), `name`, `version_label`, timestamps.
- **`version` (existing int column):** repurposed from an unused per-row
  default-1 number to the within-group counter. Existing rows are all roots
  with `version = 1` — consistent, no data migration needed.

### 2.5 Deletion rules

- Deleting a **root** cascades to all revisions (FK `ON DELETE CASCADE`).
- Deleting the **latest revision** promotes the previous latest (by highest
  `version`). **Order matters:** the transaction must DELETE the row first
  and then set `is_latest_version = true` on the predecessor. Promoting
  before the delete would transiently create two latest rows in one group
  and violate `ix_documents_one_latest_per_group` (Postgres unique indexes
  cannot be deferred). The post-delete zero-latest state is permitted by the
  partial index (it only constrains rows where the flag is true) and is
  invisible outside the transaction. Deleting a non-latest revision is a
  plain delete.
- Deleting the *only* (root) row of a group is a plain delete.

### 2.6 Migration & rollback

Migration `0011_document_versioning.py`:

1. Enum expansion inside `with op.get_context().autocommit_block():`
   (`ALTER TYPE … ADD VALUE` cannot run inside a regular transaction on some
   setups; the autocommit block makes it deterministic).
2. `op.add_column` × 3 (nullable / `server_default='true'` for the flag).
3. Create the four indexes (two partial unique, the user/type/created_at
   composite, and the plain `parent_document_id` index); drop
   `ix_documents_user_id_type`.
4. **Downgrade:** drops the new columns and indexes and restores
   `ix_documents_user_id_type`. It does **not** shrink the `document_type`
   enum — Postgres cannot remove enum values without recreating the type, and
   extra unused values are harmless. This is deliberate (pre-launch; the
   elaborate type-recreation dance isn't worth the risk) and is documented in
   the migration header.

---

## 3. Backend API

All routes remain under `/api/v1`, Clerk-authenticated, per-user scoped.

### 3.1 Unchanged in shape

- `GET /documents/{id}` — now simply also resolves for revisions (ownership
  scoped as before).
- `DELETE /documents/{id}` — gains the promote-previous-latest behaviour
  (§2.5) internally.
- Two-step upload flow (`POST /documents` → upload bytes to target) — reused
  verbatim by the new revision endpoint.

### 3.2 Changed

**`GET /documents`** — returns **one row per group** (the latest revision,
falling back to the root when a group has no revisions) by default, with a
new computed field `revisions_count`. Filters (`application_id`, `type`) and
keyset pagination (`(created_at DESC, id DESC)` of the representative row)
are preserved. New optional query param:

- `include_revisions=false` (default) — grouped view (page of groups).
- `include_revisions=true` — flat view of every row, same filters (used by
  the workspace panel to render full revision lists per application).

Implementation note: grouped keyset pagination is a **two-step query**, not a
variant of `BaseRepository.list_paginated` — `DISTINCT ON (group_key)`
requires its ORDER BY to lead with the group key, which conflicts with the
`(created_at DESC, id DESC)` pagination order. The purpose-built repository
method therefore runs an inner `DISTINCT ON (COALESCE(parent_document_id, id))
… ORDER BY group_key, created_at DESC, id DESC` subquery (selecting each
group's representative — the latest revision, falling back to the root), and
an outer query that applies the keyset cursor + `LIMIT` over those
representatives. `revisions_count` comes from a correlated subquery, not an
N+1 loop.

### 3.3 New

**`POST /documents/{id}/revisions`** — create a revision of root `id`.

- Body: `{ name, mime_type?, size_bytes?, version_label? }` (file metadata
  only; `type`, `application_id` are inherited, not accepted).
- `404` if `id` is not found or not owned by the caller. **`409`** if `id` is
  found and owned but is itself a revision (a revision id is not a valid
  group handle — see §7 errata for the rationale).
- Returns `201` with `DocumentUploadTarget` (same shape as `POST /documents`)
  → client uploads bytes to the target exactly as today.
- `409` on version-race `IntegrityError` (client may retry).

**`GET /documents/{id}/revisions`** — revision history of group `id`
(root + revisions, oldest first). `404` if `id` isn't a caller-owned root.

### 3.4 Schemas

- `DocumentType = Literal["resume","cover_letter","certificate","reference","visa","other"]`.
- `DocumentCreate` += optional `version_label` (max 255) — labels the new root.
- `DocumentRead` += `parent_document_id`, `version_label`, `is_latest_version`,
  and `revisions_count: int | None` (present only on grouped reads; `None` on
  flat/single reads).
- `DocumentRevisionCreate(BaseModel)` = `name`, `mime_type?`, `size_bytes?`,
  `version_label?` (max 255).

---

## 4. Frontend

### 4.1 Navigation

- Sidebar "Main" section gains **Documents** (`/documents`, `FileText` icon),
  placed after Applications.

### 4.2 `/documents` — the Document Manager

- **Filter chips:** All · Resumes · Cover Letters · Certificates · References ·
  Visa · Other (single-select, keyboard navigable, `aria-pressed`).
- **Grouped list:** one card per group — latest revision's name, type badge,
  `version_label` (when set), `v{version}` counter, `revisions_count`,
  `updated_at`, open/download actions, and an **Add version** button.
  Expanding a card (Radix Collapsible) fetches and shows the revision history.
- **Upload document** button → upload dialog with the 6-type selector and an
  optional `version_label` field. The same field appears in the "Add version"
  flow (it labels the revision there); both flows post it to the matching
  endpoint.
- Loading skeleton, empty state ("No documents yet — upload your first
  resume"), `<ErrorState>` fallback, keyset **Load more** pagination.
- Server Component page fetches the first page; client components handle
  chips, expansion, and pagination (TanStack Query via api-client where
  pagination is interactive).

### 4.3 Workspace `DocumentsPanel` (updated)

- Lists **groups** for the current application (`application_id` filter,
  grouped view).
- Each group is expandable (revisions fetched lazily) with per-revision
  download/delete and **Add version**.
- "Upload new document" action unchanged except the expanded type selector.

### 4.4 Shared grouping helper

`features/documents/document-groups.ts` — pure functions that merge flat
revision lists into grouped view models (`GroupSummary`, `RevisionRow`).
Single source of truth for both the page and the workspace panel; unit-tested.

### 4.5 Types

`frontend/src/types` — `DocumentType` widens to the 6 values; `Document` +=

```ts
parent_document_id?: string | null
version_label?: string | null
is_latest_version?: boolean
revisions_count?: number | null
```

---

## 5. Testing

### 5.1 Backend (pytest, embedded PG)

1. Create revision on own root → 201; `version=2`; previous latest flipped to
   `false`; `revisions_count` increments; bytes upload flow works on the
   returned target.
2. Revision on **another user's** root → **404**.
3. Revision on a **non-root** (a revision id) → **409**.
4. Version-counter race protection is verified **deterministically**: insert
   a revision, then attempt a second row with the same `(group, version)`
   directly at the repository layer and assert `IntegrityError` from
   `ix_documents_group_version` (a true concurrent-race test would be
   timing-dependent and flaky).
5. Delete latest revision → previous promoted (`is_latest_version=true`).
6. Delete root → all revisions cascade-deleted.
7. `GET /documents` default → one row per group, `revisions_count` correct;
   `include_revisions=true` → flat.
8. Invalid `type` value → **422** (Literal validation, same pattern as F3).
9. Legacy rows (pre-migration) → behave as roots (`version=1`,
   `is_latest_version=true`).
10. `GET /documents/{id}/revisions` oldest-first ordering + 404 for non-roots.

### 5.2 Frontend

- Unit tests for `document-groups.ts` (merge, ordering, latest
  representative selection, empty input).
- Typecheck/lint/build gates as usual; manual E2E smoke of upload → add
  version → expand → delete latest.

---

## 6. Verification checklist (definition of done)

- [ ] `uv run --extra dev pytest` green (incl. the 10 new backend tests).
- [ ] `ruff check`, `ruff format --check`, `mypy src` clean.
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm build` clean.
- [ ] `alembic upgrade head` applies; `downgrade -1` documented behaviour
      verified (or explicitly best-effort with a clean error).
- [ ] ORM `__table_args__` matches the migration's indexes exactly.
- [ ] `docs/API.md` documents the new endpoints (`POST /documents/{id}/revisions`,
      `GET /documents/{id}/revisions`) and the grouped-list contract change
      (`revisions_count`, `include_revisions`).
- [ ] No N+1 in the grouped list (verified by query count in a test).
- [ ] Per-user isolation holds on every new endpoint (test 2).
- [ ] No secrets in the diff.

---

## 7. Errata / decisions log

- **Revision-on-non-root → 409 vs 404:** a revision id *is* an owned document,
  so returning 404 would be misleading. Final rule: **404** only for
  "not found or not yours"; **409** for "found, yours, but not a root".
  (Supersedes the ambiguity in §3.3.)
- **`revisions_count` on `DocumentRead` as nullable** keeps one read schema
  for both grouped and flat contexts instead of two nearly-identical models.
- **`version` semantics change** (unused per-row int → group counter) is
  safe: every existing row is a root with `version=1`.
- F4 ("adopt new defaults" migration affordance) was **skipped as YAGNI** —
  pre-launch, no users hold the old 6-stage pipeline. New-user seeding of the
  8-stage pipeline already shipped.
