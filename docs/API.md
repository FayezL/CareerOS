> Living document — kept up to date as CareerOS evolves. Last updated: 2026-07-08.

# CareerOS — API

This document specifies the HTTP API contract for **CareerOS**, the modern Job Application Tracker for software engineers. The API is a versioned, RESTful JSON surface served by the canonical FastAPI backend; every endpoint is per-user and strictly scoped to the authenticated user's data. It is intended as the authoritative contract between the Next.js frontend and the backend services layer (see [ARCHITECTURE.md](./ARCHITECTURE.md) and [DATABASE.md](./DATABASE.md) for the surrounding system and data model).

## Base URL & Versioning

| Environment | Base URL |
| --- | --- |
| Local | `http://localhost:8000/api/v1` |
| Staging | `https://api.staging.careeros.app/api/v1` |
| Production | `https://api.careeros.app/api/v1` |

- All v1 routes are prefixed with `/api/v1`. The environment is selected via the `ENV` variable (`local` | `staging` | `production`).
- **Breaking changes** bump the prefix (e.g. `/api/v2`). Additive, non-breaking changes (new fields, new optional query params, new endpoints) ship under the same `/api/v1` prefix without a version bump.
- All traffic is HTTPS in staging and production. Plain HTTP is permitted only for `local`.

## Authentication

CareerOS uses **Clerk** for identity. Every protected request carries a Clerk-issued JWT in the `Authorization` header:

```
Authorization: Bearer <clerk-jwt>
```

**Verification flow (FastAPI):**

1. The backend reads the `Authorization` header. Missing/malformed → `401`.
2. The JWT's signature is verified against Clerk's JWKS, which are fetched from Clerk and cached. The `sub` claim (`clerk_user_id`) is extracted as the stable principal identifier.
3. The backend **upserts** a local row in `users` keyed by `clerk_user_id` (so the first authenticated request ever made by a user implicitly creates their account), then uses that local `users.id` as the owner scope for all subsequent repository queries.
4. Every repository query is scoped by the resolved user's `id`. There is no way to read or write another user's data through v1 endpoints; cross-user access is structurally impossible rather than enforced per-route.

**Consequences:**

- The "current user" is fully resolved server-side from the JWT; there is no `user_id` path or body parameter on any v1 endpoint.
- A request that references a resource the authenticated user does not own returns `404` (not `403`), to avoid leaking the existence of other users' resources.
- Tokens expire on Clerk's schedule; an expired or revoked token yields `401`.

The two **public** endpoints are `GET /api/v1/health` and `GET /api/v1/health/ready`. Every other v1 endpoint requires a valid Bearer token. See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full auth architecture.

## Conventions

### Request / Response

- Request and response bodies are JSON. Send `Content-Type: application/json` on any request with a body.
- Field names are **snake_case** throughout (e.g. `company_id`, `applied_at`, `next_cursor`).
- IDs in URL paths are **UUIDs** (e.g. `/companies/8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c`).
- `GET` and `DELETE` never accept a request body; parameters come from the path or query string.
- `POST`, `PATCH`, and `PUT` accept a JSON body. `PATCH` performs a partial update; omitted fields are not modified.

### Pagination

List endpoints are **cursor-based**. Pass query params:

| Param | Default | Max | Notes |
| --- | --- | --- | --- |
| `limit` | `20` | `100` | Number of items to return. |
| `cursor` | _(omitted)_ | — | Opaque token returned as `next_cursor` from the previous page. Omit on the first request. |

Response envelope:

```json
{
  "items": [ /* ... */ ],
  "next_cursor": "eyJzb3J0X2tleSI6IjIwMjYtMDctMDhUMTM6MDA6MDBaOjhlNTQ..."
}
```

- `next_cursor` is `null` when the last page has been returned; otherwise pass it verbatim into the next request's `cursor` param.
- The cursor is an opaque, server-signed token encoding the **last row's sort key**. Do not construct or inspect it client-side.
- Stable sort order is `created_at DESC, id ASC`. Pagination is stable under this composite sort key, so concurrent inserts do not cause skips or duplicates while paging.

Example:

```
GET /applications?limit=20&cursor=eyJzb3J0X2tleSI6IjIwMjYtMDctMDhUMTM6MDA6MDBaOjhlNTQ
```

### Filtering & Sorting

- Filters are optional query params, e.g. `GET /applications?status=active&company_id=8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c&stage_id=3a2b1c0d-...&q=staff`.
- Free-text search uses `q=<text>` where supported.
- Sorting uses `sort=<field>` for ascending or `sort=-<field>` for descending, e.g. `sort=-applied_at`. Only documented sort fields are honored; unknown fields fall back to the default order.

### Errors

Errors use **RFC 7807 Problem Details** with `Content-Type: application/problem+json`:

```json
{
  "type": "https://api.careeros.app/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "One or more fields were invalid.",
  "instance": "/api/v1/applications",
  "errors": [
    { "field": "company_id", "code": "required", "message": "company_id is required." },
    { "field": "applied_at", "code": "invalid_date", "message": "Must be an ISO 8601 date (YYYY-MM-DD)." }
  ]
}
```

- `type` is a stable, documented error category URI (human-readable documentation pointer).
- `title` is a short, stable summary. `detail` is a human-readable explanation of this occurrence.
- `instance` is the request path.
- `errors` is an optional array of field-level problems, present on `422` responses and on multi-field validation failures.
- All problem details are documented to be stable across v1.

### Status Codes

| Code | Meaning | When |
| --- | --- | --- |
| `200 OK` | Success | Successful `GET`, `PATCH`, or action responses. |
| `201 Created` | Resource created | Successful `POST` that creates a resource. |
| `204 No Content` | No body | Successful `DELETE`, or an action returning nothing. |
| `400 Bad Request` | Malformed request | Unparseable JSON, unknown enum, malformed UUID in body. |
| `401 Unauthorized` | No/invalid token | Missing, expired, or unverifiable Clerk JWT. |
| `403 Forbidden` | Authenticated but forbidden | Rare in v1 (per-user isolation); e.g. attempting an action on a soft-deleted resource. |
| `404 Not Found` | Resource not found | Unknown ID, or an ID owned by another user. |
| `409 Conflict` | State conflict | Duplicate unique value (e.g. duplicate stage position). |
| `422 Unprocessable Entity` | Validation error | Valid JSON but field validation failed; `errors` array present. |
| `429 Too Many Requests` | Rate limited | See Rate Limiting. |
| `500 Internal Server Error` | Server fault | Unexpected error; safe to retry. |

### Idempotency

Creating endpoints (`POST`) accept an optional `Idempotency-Key` header:

```
Idempotency-Key: 7e3c1a4b-9d2e-4f8a-8b1c-0e6f2a5d7c3a
```

- When supplied with the same key within the key's TTL, the server returns the original response rather than creating a duplicate.
- **Note:** In v1, idempotency is **stubbed** (header accepted and echoed but not yet deduplicating). Full idempotency caching lands in a later phase. Clients should still send the header so behavior activates transparently when implemented.

### Rate Limiting

- **Phase 0:** simple fixed-window limiter, applied per authenticated user.
- Limits are returned on every protected response via headers:

| Header | Meaning |
| --- | --- |
| `X-RateLimit-Limit` | Maximum requests allowed in the current window. |
| `X-RateLimit-Remaining` | Requests remaining in the current window. |
| `X-RateLimit-Reset` | Epoch seconds at which the window resets. |

- When exceeded: `429 Too Many Requests` with a `Retry-After` header (seconds until reset) and an `application/problem+json` body.
- The long-term design is a per-user token bucket; the v1 fixed window is a stand-in.

### CORS

- Only origins on the allow-list (the CareerOS Next.js frontends for staging and production, plus `http://localhost:3000` for local development) may make credentialed cross-origin requests.
- Preflight `OPTIONS` is handled at the edge. Unauthorized origins are rejected by the browser, not by a 4xx from the API.

### Dates

- Timestamps with time are **ISO 8601 in UTC**: `2026-07-08T13:00:00Z`.
- Calendar dates without time are `YYYY-MM-DD`: `2026-07-08`.
- All date and timestamp fields are returned as strings; the API does not accept or return bare Unix epoch numbers.

## Common Response Shapes

**List envelope** (every list endpoint):

```json
{
  "items": [
    {
      "id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "name": "Stripe",
      "website": "https://stripe.com",
      "industry": "Financial Services",
      "size": "5001-10000",
      "location": "San Francisco, CA",
      "created_at": "2026-07-08T13:00:00Z",
      "updated_at": "2026-07-08T13:00:00Z"
    }
  ],
  "next_cursor": "eyJzb3J0X2tleSI6IjIwMjYtMDctMDhUMTM6MDA6MDBaOjhlNTQ..."
}
```

**Single resource** (every create/get returns the raw object, no wrapper):

```json
{
  "id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "name": "Stripe",
  "website": "https://stripe.com",
  "industry": "Financial Services",
  "size": "5001-10000",
  "location": "San Francisco, CA",
  "created_at": "2026-07-08T13:00:00Z",
  "updated_at": "2026-07-08T13:00:00Z"
}
```

## Endpoints

All endpoints below are under `/api/v1`. All are **protected** (require `Authorization: Bearer <clerk-jwt>`) except the two Health endpoints.

### Health

#### GET /health

**Purpose:** Liveness probe. Returns `200` as long as the process is serving requests. Does not touch the database.

**Auth:** None.

**Response `200`:**

```json
{ "status": "ok", "service": "careeros-api", "version": "v1" }
```

#### GET /health/ready

**Purpose:** Readiness probe. Returns `200` only when the process can reach its primary database; otherwise `503`. Used by load balancers and deploy checks.

**Auth:** None.

**Response `200`:**

```json
{ "status": "ready", "checks": { "database": "ok" } }
```

**Response `503`:**

```json
{ "status": "unavailable", "checks": { "database": "fail" } }
```

### Users / Me

The current user is created implicitly on their first authenticated request (upsert on `clerk_user_id`). There is no `POST /me`.

#### GET /me

**Purpose:** Return the authenticated user's profile.

**Response `200`:**

```json
{
  "id": "6b9a0f3a-1c2b-4d3e-9a01-2b3c4d5e6f70",
  "clerk_user_id": "user_2ABCDEFGHIJKLMNOPQRSTUVWX",
  "email": "andrei@example.com",
  "full_name": "Andrei Popescu",
  "avatar_url": "https://images.clerk.dev/user_2ABC/avatar.png",
  "timezone": "America/Los_Angeles",
  "created_at": "2026-07-08T13:00:00Z",
  "updated_at": "2026-07-08T13:05:42Z"
}
```

#### PATCH /me

**Purpose:** Update the current user's editable profile fields.

**Request:**

```json
{
  "full_name": "Andrei P.",
  "timezone": "America/Los_Angeles"
}
```

**Response `200`:** the updated user object (same shape as `GET /me`).

### Companies

A company is a deduplicated record referenced by many applications over time.

#### GET /companies

**Purpose:** List companies, newest first, with optional search.

**Query params:** `limit`, `cursor`, `q` (name/website substring).

**Response `200`:** list envelope of company objects.

```json
{
  "items": [
    {
      "id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "name": "Stripe",
      "website": "https://stripe.com",
      "industry": "Financial Services",
      "size": "5001-10000",
      "location": "San Francisco, CA",
      "created_at": "2026-07-08T13:00:00Z",
      "updated_at": "2026-07-08T13:00:00Z"
    },
    {
      "id": "2b1a0c9d-3e4f-5a6b-7c8d-9e0f1a2b3c4d",
      "name": "Vercel",
      "website": "https://vercel.com",
      "industry": "Software",
      "size": "501-1000",
      "location": "Remote",
      "created_at": "2026-07-08T12:30:00Z",
      "updated_at": "2026-07-08T12:30:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /companies

**Purpose:** Create a company.

**Request:**

```json
{
  "name": "Linear",
  "website": "https://linear.app",
  "industry": "Software",
  "size": "101-500",
  "location": "Remote"
}
```

**Response `201`:** the created company.

```json
{
  "id": "4d5e6f7a-8b9c-0d1e-2f3a4b5c6d7e8f9a",
  "name": "Linear",
  "website": "https://linear.app",
  "industry": "Software",
  "size": "101-500",
  "location": "Remote",
  "created_at": "2026-07-08T14:00:00Z",
  "updated_at": "2026-07-08T14:00:00Z"
}
```

#### GET /companies/{id}

**Purpose:** Fetch a single company.

**Response `200`:** the company object (same shape as items above).

#### PATCH /companies/{id}

**Purpose:** Partial update of a company.

**Request:**

```json
{ "size": "501-1000" }
```

**Response `200`:** the updated company object.

#### DELETE /companies/{id}

**Purpose:** Soft-delete a company. Subsequent reads return `404`; the row is retained for audit and undo.

**Response:** `204 No Content`.

### Pipeline Stages

Stages are ordered by `position` and are owned by the user. Defaults are seeded on signup; the user may rename, add, or remove stages.

#### GET /pipeline-stages

**Purpose:** Return all stages for the current user, ordered by `position` ascending. Not paginated (small set).

**Response `200`:**

```json
{
  "items": [
    { "id": "10a1b2c3-d4e5-6789-0123-456789abcdef", "name": "Applied",    "position": 0, "color": "#94a3b8", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" },
    { "id": "11b2c3d4-e5f6-7890-1234-56789abcdef0", "name": "Screening",  "position": 1, "color": "#60a5fa", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" },
    { "id": "12c3d4e5-f6a7-8901-2345-6789abcdef01", "name": "Interview",  "position": 2, "color": "#a78bfa", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" },
    { "id": "13d4e5f6-a7b8-9012-3456-789abcdef012", "name": "Offer",      "position": 3, "color": "#34d399", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" },
    { "id": "14e5f6a7-b8c9-0123-4567-89abcdef0123", "name": "Rejected",   "position": 4, "color": "#f87171", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" },
    { "id": "15f6a7b8-c9d0-1234-5678-9abcdef01234", "name": "Accepted",   "position": 5, "color": "#22c55e", "created_at": "2026-07-08T13:00:00Z", "updated_at": "2026-07-08T13:00:00Z" }
  ],
  "next_cursor": null
}
```

#### POST /pipeline-stages

**Purpose:** Create a stage. `position` may be omitted (appends to the end).

**Request:**

```json
{ "name": "Team Match", "color": "#fbbf24" }
```

**Response `201`:**

```json
{
  "id": "20a1b2c3-d4e5-6789-0123-456789abcde0",
  "name": "Team Match",
  "position": 6,
  "color": "#fbbf24",
  "created_at": "2026-07-08T14:30:00Z",
  "updated_at": "2026-07-08T14:30:00Z"
}
```

#### PATCH /pipeline-stages/{id}

**Purpose:** Update a stage's name or color. Changing `position` via this route is allowed but discouraged — use `reorder` for atomic reordering.

**Request:**

```json
{ "name": "Technical Screen", "color": "#f59e0b" }
```

**Response `200`:** the updated stage.

#### DELETE /pipeline-stages/{id}

**Purpose:** Delete a stage. Applications referencing the stage must be moved first; otherwise `409`.

**Response:** `204 No Content`.

#### POST /pipeline-stages/reorder

**Purpose:** Atomically reorder all stages. The body is the complete, ordered list of stage IDs belonging to the current user.

**Request:**

```json
{
  "ordered_ids": [
    "10a1b2c3-d4e5-6789-0123-456789abcdef",
    "11b2c3d4-e5f6-7890-1234-56789abcdef0",
    "20a1b2c3-d4e5-6789-0123-456789abcde0",
    "12c3d4e5-f6a7-8901-2345-6789abcdef01",
    "13d4e5f6-a7b8-9012-3456-789abcdef012",
    "14e5f6a7-b8c9-0123-4567-89abcdef0123",
    "15f6a7b8-c9d0-1234-5678-9abcdef01234"
  ]
}
```

**Response `200`:** the full reordered list (same shape as `GET /pipeline-stages`).

### Applications

An application = one candidate × one role at one company. Each has a status, a current pipeline stage, an applied date, an optional source, and a job URL.

#### GET /applications

**Purpose:** List applications, paginated, filterable and sortable.

**Query params:** `limit`, `cursor`, `status` (`active` | `paused` | `closed`), `company_id`, `stage_id`, `q` (title/role text), `sort` (default `-applied_at`; allowed: `applied_at`, `-applied_at`, `created_at`, `-created_at`, `title`, `-title`).

**Response `200`:**

```json
{
  "items": [
    {
      "id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "company_id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "company": { "id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c", "name": "Stripe" },
      "title": "Senior Software Engineer, Payments",
      "status": "active",
      "stage_id": "12c3d4e5-f6a7-8901-2345-6789abcdef01",
      "stage": { "id": "12c3d4e5-f6a7-8901-2345-6789abcdef01", "name": "Interview" },
      "job_url": "https://stripe.com/jobs/listing/senior-engineer-payments",
      "source": "linkedin",
      "applied_at": "2026-07-01",
      "created_at": "2026-07-01T09:00:00Z",
      "updated_at": "2026-07-08T16:00:00Z"
    }
  ],
  "next_cursor": "eyJzb3J0X2tleSI6IjIwMjYtMDctMDFUMDk6MDA6MDBaOjdmNmU1ZDQj..."
}
```

#### POST /applications

**Purpose:** Create an application.

**Request:**

```json
{
  "company_id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "title": "Senior Software Engineer, Payments",
  "status": "active",
  "stage_id": "10a1b2c3-d4e5-6789-0123-456789abcdef",
  "job_url": "https://stripe.com/jobs/listing/senior-engineer-payments",
  "source": "linkedin",
  "applied_at": "2026-07-08"
}
```

**Response `201`:** the created application (same shape as items above, with expanded `company` and `stage`).

#### GET /applications/{id}

**Purpose:** Fetch a single application, including expanded `company` and current `stage`.

**Response `200`:** a single application object (same shape as items above).

#### PATCH /applications/{id}

**Purpose:** Partial update of an application (e.g. edit title, set status to `paused`).

**Request:**

```json
{ "title": "Staff Software Engineer, Payments", "status": "paused" }
```

**Response `200`:** the updated application.

#### DELETE /applications/{id}

**Purpose:** Soft-delete an application. Related stage history is retained.

**Response:** `204 No Content`.

#### POST /applications/{id}/move

**Purpose:** Move an application to a different pipeline stage. Appends a row to `application_stage_history` and updates `stage_id` / `updated_at`. Optional `note` is stored on the history entry.

**Request:**

```json
{
  "to_stage_id": "11b2c3d4-e5f6-7890-1234-56789abcdef0",
  "note": "Recruiter call scheduled for Friday."
}
```

**Response `200`:**

```json
{
  "id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "stage_id": "11b2c3d4-e5f6-7890-1234-56789abcdef0",
  "stage": { "id": "11b2c3d4-e5f6-7890-1234-56789abcdef0", "name": "Screening" },
  "updated_at": "2026-07-08T16:15:00Z"
}
```

#### GET /applications/{id}/history

**Purpose:** Return the stage-change timeline for an application, oldest first. Not paginated.

**Response `200`:**

```json
{
  "items": [
    {
      "id": "30a1b2c3-d4e5-6789-0123-456789abcd01",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "to_stage_id": "10a1b2c3-d4e5-6789-0123-456789abcdef",
      "to_stage": { "id": "10a1b2c3-d4e5-6789-0123-456789abcdef", "name": "Applied" },
      "note": null,
      "occurred_at": "2026-07-01T09:00:00Z"
    },
    {
      "id": "31b2c3d4-e5f6-7890-1234-56789abcd02",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "to_stage_id": "12c3d4e5-f6a7-8901-2345-6789abcdef01",
      "to_stage": { "id": "12c3d4e5-f6a7-8901-2345-6789abcdef01", "name": "Interview" },
      "note": "Passed recruiter screen.",
      "occurred_at": "2026-07-05T18:00:00Z"
    },
    {
      "id": "32c3d4e5-f6a7-8901-2345-6789abcd03",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "to_stage_id": "11b2c3d4-e5f6-7890-1234-56789abcdef0",
      "to_stage": { "id": "11b2c3d4-e5f6-7890-1234-56789abcdef0", "name": "Screening" },
      "note": "Recruiter call scheduled for Friday.",
      "occurred_at": "2026-07-08T16:15:00Z"
    }
  ],
  "next_cursor": null
}
```

### Contacts

A contact is a person (recruiter, hiring manager, interviewer, referral), optionally tied to a company and/or applications.

#### GET /contacts

**Purpose:** List contacts.

**Query params:** `limit`, `cursor`, `company_id`.

**Response `200`:**

```json
{
  "items": [
    {
      "id": "40a1b2c3-d4e5-6789-0123-456789abcd10",
      "company_id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "company": { "id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c", "name": "Stripe" },
      "name": "Priya Nair",
      "email": "priya.nair@stripe.com",
      "linkedin_url": "https://www.linkedin.com/in/priyanair",
      "role": "recruiter",
      "created_at": "2026-07-02T10:00:00Z",
      "updated_at": "2026-07-02T10:00:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /contacts

**Request:**

```json
{
  "company_id": "8c2f1a3b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "name": "Priya Nair",
  "email": "priya.nair@stripe.com",
  "linkedin_url": "https://www.linkedin.com/in/priyanair",
  "role": "recruiter"
}
```

**Response `201`:** the created contact (same shape as items above).

#### GET /contacts/{id}

**Response `200`:** a single contact object.

#### PATCH /contacts/{id}

**Request:**

```json
{ "role": "hiring_manager" }
```

**Response `200`:** the updated contact.

#### DELETE /contacts/{id}

**Purpose:** Soft-delete a contact.

**Response:** `204 No Content`.

### Interviews

A scheduled interview/event tied to a parent application, with an interviewer contact, type, time, and location/link.

#### GET /interviews

**Purpose:** List interviews.

**Query params:** `limit`, `cursor`, `application_id`, `from` (ISO 8601 timestamp), `to` (ISO 8601 timestamp), `sort` (default `scheduled_at`; allowed: `scheduled_at`, `-scheduled_at`). Results are filtered by `scheduled_at` between `from` and `to` inclusive.

**Response `200`:**

```json
{
  "items": [
    {
      "id": "50a1b2c3-d4e5-6789-0123-456789abcd20",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "type": "technical",
      "scheduled_at": "2026-07-10T16:00:00Z",
      "duration_minutes": 60,
      "location": "https://meet.google.com/abc-defg-hij",
      "interviewer_contact_id": "40a1b2c3-d4e5-6789-0123-456789abcd10",
      "notes": "Systems design — focus on idempotency and payments.",
      "created_at": "2026-07-06T12:00:00Z",
      "updated_at": "2026-07-06T12:00:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /interviews

**Request:**

```json
{
  "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "type": "technical",
  "scheduled_at": "2026-07-10T16:00:00Z",
  "duration_minutes": 60,
  "location": "https://meet.google.com/abc-defg-hij",
  "interviewer_contact_id": "40a1b2c3-d4e5-6789-0123-456789abcd10",
  "notes": "Systems design — focus on idempotency and payments."
}
```

**Response `201`:** the created interview (same shape as items above).

#### GET /interviews/{id}

**Response `200`:** a single interview object.

#### PATCH /interviews/{id}

**Request:**

```json
{ "scheduled_at": "2026-07-11T16:00:00Z", "duration_minutes": 90 }
```

**Response `200`:** the updated interview.

#### DELETE /interviews/{id}

**Purpose:** Soft-delete an interview.

**Response:** `204 No Content`.

### Notes

Free-form rich-text notes attachable to an application or a contact (at least one of `application_id` / `contact_id` is required on create).

#### GET /notes

**Purpose:** List notes.

**Query params:** `limit`, `cursor`, `application_id`, `contact_id`.

**Response `200`:**

```json
{
  "items": [
    {
      "id": "60a1b2c3-d4e5-6789-0123-456789abcd30",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "contact_id": null,
      "title": "Recruiter screen recap",
      "body": "Priya mentioned the team is hiring for both Payments and Issuing. Comp band: $220k–$260k base. Next step: technical on 2026-07-10.",
      "created_at": "2026-07-05T18:30:00Z",
      "updated_at": "2026-07-05T18:30:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /notes

**Request:**

```json
{
  "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "title": "Recruiter screen recap",
  "body": "Priya mentioned the team is hiring for both Payments and Issuing. Comp band: $220k–$260k base. Next step: technical on 2026-07-10."
}
```

**Response `201`:** the created note (same shape as items above).

#### GET /notes/{id}

**Response `200`:** a single note object.

#### PATCH /notes/{id}

**Request:**

```json
{ "body": "Updated: comp band confirmed at $220k–$260k base + equity." }
```

**Response `200`:** the updated note.

#### DELETE /notes/{id}

**Purpose:** Soft-delete a note.

**Response:** `204 No Content`.

### Documents

Documents store **metadata only** in the CareerOS database; the file bytes live in **Firebase Storage**. Creating a document returns a **signed upload URL**; the client `PUT`s the bytes to Firebase directly. Deleting a document removes the metadata row and the Firebase object.

Documents support **versioning**: a root document may have revisions (`parent_document_id` points at the root). Each group has exactly one row with `is_latest_version = true`. Deleting the latest revision promotes its predecessor; deleting a root cascades to its revisions.

#### GET /documents

**Purpose:** List documents. Grouped by default: one row per logical document (the newest row of each group) with `revisions_count` populated.

**Query params:** `limit`, `cursor`, `application_id`, `type` (see `document_type` enum), `include_revisions` (`true` returns every row flat, no counts).

**Response `200`:**

```json
{
  "items": [
    {
      "id": "70a1b2c3-d4e5-6789-0123-456789abcd40",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "type": "resume",
      "name": "resume_stripe_payments_v2.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 184320,
      "firebase_path": "gs://careeros-docs/users/6b9a0f3a-.../70a1b2c3-...pdf",
      "version": 2,
      "parent_document_id": "60a1b2c3-d4e5-6789-0123-456789abcd30",
      "version_label": "v2 — Stripe focus",
      "is_latest_version": true,
      "revisions_count": 2,
      "created_at": "2026-07-03T11:00:00Z",
      "updated_at": "2026-07-03T11:00:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /documents

**Purpose:** Request a signed upload URL and create the metadata row.

**Request:**

```json
{
  "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "type": "resume",
  "name": "resume_stripe_payments_v2.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 184320,
  "version_label": "v2 — Stripe focus"
}
```

**Response `201`:**

```json
{
  "id": "70a1b2c3-d4e5-6789-0123-456789abcd40",
  "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "type": "resume",
  "name": "resume_stripe_payments_v2.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 184320,
  "firebase_path": "gs://careeros-docs/users/6b9a0f3a-.../70a1b2c3-...pdf",
  "upload_url": "https://storage.googleapis.com/careeros-docs/users/6b9a0f3a-.../70a1b2c3-...pdf?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=...&X-Goog-Date=20260708T130000Z&X-Goog-Expires=900&X-Goog-Signature=...",
  "upload_method": "PUT",
  "upload_headers": { "Content-Type": "application/pdf" },
  "expires_at": "2026-07-08T13:15:00Z",
  "created_at": "2026-07-08T13:00:00Z",
  "updated_at": "2026-07-08T13:00:00Z"
}
```

The client uploads the bytes by `PUT`ing them to `upload_url` with `upload_headers` before `expires_at` (15-minute TTL).

#### POST /documents/{id}/revisions

**Purpose:** Create a revision of a caller-owned **root** document and return an upload target. `type` and `application_id` are inherited from the root; `version` is assigned automatically.

**Errors:** `404` if `{id}` is not found (or belongs to another user); `409` if `{id}` is itself a revision.

**Request:**

```json
{
  "name": "resume_stripe_payments_v3.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 190204,
  "version_label": "v3 — quantified impact"
}
```

**Response `201`:** same shape as `POST /documents` (includes `upload_url`).

#### GET /documents/{id}/revisions

**Purpose:** List a document group's revision history (root + revisions, oldest first).

**Errors:** `404` if `{id}` is not found; `409` if `{id}` is not a root document.

**Response `200`:** array of document objects ordered by `version` ascending.

#### GET /documents/{id}

**Response `200`:** a single document object (same shape as items above; no `upload_url`, since the upload is complete).

#### DELETE /documents/{id}

**Purpose:** Delete a document row **and** its underlying storage object. Deleting the latest revision promotes the previous one to latest. Deleting a root cascades to its revisions (storage objects included).

**Response:** `204 No Content`.

### Reminders

Reminders drive follow-ups and interview prep nudges. They may be tied to an application, contact, or interview.

#### GET /reminders

**Purpose:** List reminders.

**Query params:** `limit`, `cursor`, `due_before` (ISO 8601 timestamp — returns reminders due at or before this time), `completed` (`true` | `false`).

**Response `200`:**

```json
{
  "items": [
    {
      "id": "80a1b2c3-d4e5-6789-0123-456789abcd50",
      "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
      "contact_id": null,
      "title": "Follow up with Priya on Stripe loop",
      "due_at": "2026-07-09T16:00:00Z",
      "completed": false,
      "completed_at": null,
      "created_at": "2026-07-05T18:30:00Z",
      "updated_at": "2026-07-05T18:30:00Z"
    }
  ],
  "next_cursor": null
}
```

#### POST /reminders

**Request:**

```json
{
  "application_id": "7f6e5d4c-3b2a-1900-8abc-def012345678",
  "title": "Send thank-you note after technical",
  "due_at": "2026-07-10T17:30:00Z"
}
```

**Response `201`:** the created reminder (same shape as items above).

#### PATCH /reminders/{id}

**Request:**

```json
{ "title": "Send thank-you note + reference the payments design", "due_at": "2026-07-10T18:00:00Z" }
```

**Response `200`:** the updated reminder.

#### DELETE /reminders/{id}

**Response:** `204 No Content`.

#### POST /reminders/{id}/complete

**Purpose:** Mark a reminder complete.

**Response `200`:**

```json
{
  "id": "80a1b2c3-d4e5-6789-0123-456789abcd50",
  "completed": true,
  "completed_at": "2026-07-09T15:48:00Z",
  "updated_at": "2026-07-09T15:48:00Z"
}
```

#### POST /reminders/{id}/snooze

**Purpose:** Push a reminder's `due_at` into the future.

**Request:**

```json
{ "due_at": "2026-07-12T16:00:00Z" }
```

**Response `200`:**

```json
{
  "id": "80a1b2c3-d4e5-6789-0123-456789abcd50",
  "due_at": "2026-07-12T16:00:00Z",
  "completed": false,
  "updated_at": "2026-07-09T15:50:00Z"
}
```

### Analytics

Read-only analytics computed from the user's own data.

#### GET /analytics/summary

**Purpose:** Headline totals and rates.

**Response `200`:**

```json
{
  "generated_at": "2026-07-08T13:00:00Z",
  "totals": {
    "applications": 42,
    "active": 11,
    "offers": 1,
    "rejections": 18
  },
  "response_rate": 0.452,
  "active_companies": 9
}
```

- `response_rate` is the share of applications that have ever moved past the initial "Applied" stage.

#### GET /analytics/funnel

**Purpose:** Stage-by-stage conversion counts derived from `application_stage_history`.

**Response `200`:**

```json
{
  "generated_at": "2026-07-08T13:00:00Z",
  "stages": [
    { "stage_id": "10a1b2c3-d4e5-6789-0123-456789abcdef", "name": "Applied",   "position": 0, "entered": 42, "distinct_applications": 42 },
    { "stage_id": "11b2c3d4-e5f6-7890-1234-56789abcdef0", "name": "Screening", "position": 1, "entered": 19, "distinct_applications": 19 },
    { "stage_id": "12c3d4e5-f6a7-8901-2345-6789abcdef01", "name": "Interview", "position": 2, "entered": 11, "distinct_applications": 11 },
    { "stage_id": "13d4e5f6-a7b8-9012-3456-789abcdef012", "name": "Offer",     "position": 3, "entered": 1,  "distinct_applications": 1 },
    { "stage_id": "14e5f6a7-b8c9-0123-4567-89abcdef0123", "name": "Rejected",  "position": 4, "entered": 18, "distinct_applications": 18 },
    { "stage_id": "15f6a7b8-c9d0-1234-5678-9abcdef01234", "name": "Accepted",  "position": 5, "entered": 0,  "distinct_applications": 0 }
  ]
}
```

- `entered` is the total number of times any application entered that stage (an application may re-enter).
- `distinct_applications` is the number of unique applications that have ever entered that stage.

#### GET /analytics/over-time

**Purpose:** Applications created per time bucket within a window.

**Query params:** `granularity` (`day` | `week`, default `day`), `from` (ISO 8601 date or timestamp), `to` (ISO 8601 date or timestamp).

**Response `200`:**

```json
{
  "generated_at": "2026-07-08T13:00:00Z",
  "granularity": "day",
  "from": "2026-07-01",
  "to": "2026-07-08",
  "buckets": [
    { "bucket": "2026-07-01", "applications": 6 },
    { "bucket": "2026-07-02", "applications": 4 },
    { "bucket": "2026-07-03", "applications": 9 },
    { "bucket": "2026-07-04", "applications": 0 },
    { "bucket": "2026-07-05", "applications": 5 },
    { "bucket": "2026-07-06", "applications": 7 },
    { "bucket": "2026-07-07", "applications": 3 },
    { "bucket": "2026-07-08", "applications": 8 }
  ]
}
```

## Enumerations

| Enum | Values | Used by |
| --- | --- | --- |
| `application_status` | `active`, `paused`, `closed` | `applications.status` |
| `application_source` | `linkedin`, `referral`, `company_site`, `agency`, `other` | `applications.source` |
| `contact_role` | `recruiter`, `hiring_manager`, `interviewer`, `referral`, `other` | `contacts.role` |
| `interview_type` | `phone_screen`, `video_call`, `onsite`, `take_home`, `technical`, `final` | `interviews.type` |
| `document_type` | `resume`, `cover_letter`, `certificate`, `reference`, `visa`, `other` | `documents.type` |
| `company_size` | `1-10`, `11-50`, `51-100`, `101-500`, `501-1000`, `1001-5000`, `5001-10000`, `10000+` | `companies.size` |
| `analytics_granularity` | `day`, `week` | `GET /analytics/over-time` `granularity` param |

Sending an unknown enum value yields `400 Bad Request` (or `422` when part of a JSON body validated with the schema). See [DATABASE.md](./DATABASE.md) for the canonical enum definitions on each entity.

## Future Endpoints

The following are **not** part of v1 and will be added in later phases:

- **AI generation.** Endpoints to tailor a resume to a job description, draft a cover letter grounded in an application and company, and generate interview-prep questions for a role. Likely surfaced under `/api/v1/ai/...` as async, job-style resources (submit → poll or stream).
- **Billing.** Stripe-backed subscription, customer portal, and webhook endpoints (`/api/v1/billing/...`, `/api/v1/webhooks/stripe`). Billing is explicitly deferred in v1 (see [PRODUCT.md](./PRODUCT.md) Non-Goals); no subscription or payment endpoints exist in this version.
