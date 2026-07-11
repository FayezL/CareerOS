# CareerOS — Architecture Guide

> Feature-based frontend + Clean-architecture backend. Living document.
> This describes **structure and conventions only** — business features live inside it.

---

## Part 1 — Frontend (Feature-Based Architecture)

### Principles
- **Feature modules are self-contained.** Everything one feature needs (UI, hooks, server actions, types) lives under `src/features/<name>/`. Features depend on shared layers, never on each other.
- **Shared code is layered by kind** (`components`, `hooks`, `services`, `schemas`, `utils`, `types`, `providers`). Anything used by 2+ features goes here.
- **App Router is for routing only.** `src/app/` holds routes/layouts/global providers — no business logic.

### Folder map

| Folder | Purpose | Depends on |
|---|---|---|
| `src/app/` | **Routing & layouts.** Route segments, page templates, `layout.tsx`, `loading.tsx`, `not-found.tsx`, global `globals.css`, `middleware.ts`. Server Components fetch data; mutations are Server Actions. | providers, components |
| `src/providers/` | **React context/providers.** `ClerkProvider`, `ThemeProvider` (next-themes), `QueryProvider`, composed once in the root layout. Keeps the app shell clean. | libraries |
| `src/components/` | **Shared presentational components.** `ui/` = shadcn primitives (Button, Dialog, …); `layout/` = `AppShell`, `Sidebar`, `Header`; `ThemeToggle`. Dumb, reusable, no feature knowledge. | utils, ui |
| `src/features/` | **Feature modules.** One folder per domain (`companies`, `applications`, `pipeline`, …). Each contains its `actions.ts` (server actions), client components, forms, tables, and feature-local types. The only place feature logic lives. | services, components, schemas, types |
| `src/hooks/` | **Reusable cross-feature hooks** (e.g. `useDebounce`, `useMediaQuery`). Feature-specific hooks stay in the feature. | utils |
| `src/services/` | **API layer.** `api-client.ts` (the `apiFetch` wrapper that injects the Clerk Bearer token), plus typed resource clients (`companies.ts`, etc.). The *only* place that knows the backend URL. | schemas, types |
| `src/schemas/` | **Validation schemas (zod).** `env.ts` (validated process.env), and form/DTO schemas shared across features. | — |
| `src/types/` | **Shared TypeScript types.** API entity types (`Company`, `Application`, `PageOut<T>`), branded primitives. Feature-local types stay in the feature. | — |
| `src/utils/` | **Pure helpers.** `cn()` (classnames), formatters (dates, numbers), id generators. No I/O, no React. | — |
| `src/styles/` | Global stylesheets beyond `globals.css` (rare). | — |

### Dependency rule (enforced by review)
```
app → providers, components, features
features → services, schemas, types, components, hooks, utils
services → schemas, types
components → utils
providers → (composes libraries)
utils, types, schemas → (leaf; depend on nothing internal)
```
Features **never import from each other.** `services` never imports from `features`.

### Example code

`src/providers/index.tsx` — compose all providers in one place:
```tsx
import { ClerkProvider } from "@clerk/nextjs"
import { ThemeProvider } from "@/components/theme-provider"
import type { ReactNode } from "react"

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        {children}
      </ThemeProvider>
    </ClerkProvider>
  )
}
```

`src/app/layout.tsx` — root layout stays thin:
```tsx
import { Inter } from "next/font/google"
import { Providers } from "@/providers"
import "./globals.css"
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })
export const metadata = { title: { default: "CareerOS", template: "%s · CareerOS" } }
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

`src/services/api-client.ts` — the only place that talks to FastAPI:
```ts
import { auth } from "@clerk/nextjs/server"
import { getEnv } from "@/schemas/env"

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { getToken } = await auth()
  const token = await getToken()
  const res = await fetch(`${getEnv().NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: { Authorization: token ? `Bearer ${token}` : "", Accept: "application/json", ...init?.headers },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}
```

`src/schemas/env.ts` — fail-fast, lazy (runtime only, never at build):
```ts
import { z } from "zod"
const schema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: z.string().min(1),
})
let cached: z.infer<typeof schema> | null = null
export function getEnv() {
  if (!cached) cached = schema.parse(process.env)
  return cached
}
```

`src/utils/cn.ts`:
```ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
```

A **feature module** shape (`src/features/<name>/`):
```
features/companies/
├── actions.ts          # "use server" — create/update/delete (calls services)
├── company-form.tsx    # "use client" dialog form
├── companies-table.tsx # "use client" table + row actions
└── types.ts            # feature-local types (if any)
```

### Layouts, navigation, theme, dark mode
- **Root layout** (`src/app/layout.tsx`): fonts + `<Providers>`.
- **Authenticated layout** (`src/app/(app)/layout.tsx`): the `AppShell` (sidebar + header) for signed-in routes; the route group is auto-protected by `middleware.ts`.
- **Navigation** = the `Sidebar` in `components/layout/` driven by a `NAV_ITEMS` array (grouped: Main / Insights / Settings), active state via `usePathname`.
- **Theme & dark mode**: `next-themes` with `attribute="class"` (Tailwind `darkMode: "class"`); CSS variables in `globals.css` for `:root` and `.dark`; a `<ThemeToggle>` (sun/moon) in the header.

---

## Part 2 — Backend (Clean Architecture)

### Layer map

| Layer (`src/careeros_api/`) | Why it exists |
|---|---|
| `api/` | **Delivery layer.** FastAPI routers + route-level dependencies. Parses HTTP into calls, returns DTOs. Holds **no business rules** — just wiring. |
| `api/deps.py` | **Dependencies.** `SessionDep`, `CurrentUserDep`, `require_plan`. The composition point where routes receive their authenticated session/user. |
| `services/` | **Use-case / business logic.** Orchestrates repos, enforces rules (e.g. "default stages seeded on first access", "move appends history"), raises domain errors (`NotFoundError`, `ConflictError`). The only layer that defines a "transaction of work". |
| `repositories/` | **Data access.** Owns SQLAlchemy queries. **Every query is scoped by `user_id`** (tenant isolation). Returns ORM models. No HTTP, no business decisions. |
| `schemas/` | **DTOs & validation** (Pydantic v2). `Create`/`Update`/`Read` shapes, the `PageOut[T]` envelope. The boundary shape between layers and the wire. |
| `models/` | **ORM models** (SQLAlchemy 2). Tables, columns, constraints, relationships. Pure persistence shape — re-exported from `models/__init__.py` so Alembic sees them. |
| `core/` | **Cross-cutting concerns.** `config` (pydantic-settings), `logging`, `security/clerk` (JWKS verify), `storage`, `llm`, `billing`, `notifier`, `ratelimit`, `middleware`. Infrastructure adapters the app swaps via env. |
| `db/` | **Database plumbing.** `base` (DeclarativeBase + naming convention), `session` (async engine + `get_session`), `mixins` (`UUIDPrimaryKey`, `TimestampMixin`, `SoftDeleteMixin`). |

### Dependency rule (strict, inward-pointing)
```
api → services → repositories → models
        │             │
        └── schemas ──┘
api/services/repositories → core, db
core → config            (core never imports services/api)
db → (nothing internal except config)
```
- `api` never touches `repositories` or `models` directly.
- `repositories` never imports `services` or `api`.
- `core` never imports from `api/services/repositories` (it's the innermost infrastructure).

### Why each layer exists (one-liners)
- **api** — keep HTTP concerns out of logic so logic is testable without a server.
- **services** — one home for rules; prevents logic leaking into routes or queries.
- **repositories** — centralizes **user_id scoping** (security) and query details (swappable).
- **schemas** — explicit wire contract; validation happens once at the edge.
- **models** — persistence shape isolated from the API shape (they can evolve independently).
- **core** — infra adapters behind interfaces, so swapping Clerk/Stripe/Firebase is config, not a rewrite.
- **db** — engine/session lifecycle separated from business code.

### Example skeleton (non-business)

Model (`models/example.py`):
```python
from sqlalchemy.orm import Mapped, mapped_column
from careeros_api.db.base import Base
from careeros_api.db.mixins import UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin

class Example(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "examples"
    user_id: Mapped[int] = mapped_column(index=True)  # FK users in real code
    name: Mapped[str]
```

Repository (`repositories/example.py`):
```python
class ExampleRepository(BaseRepository[Example]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Example)
    # all reads take user_id and filter by it
```

Service (`services/example.py`):
```python
async def create_example(session: AsyncSession, user: User, data: ExampleCreate) -> ExampleRead:
    repo = ExampleRepository(session)
    example = await repo.create(user.id, data)
    return ExampleRead.model_validate(example)
```

Route (`api/v1/routes/example.py`):
```python
@router.post("", response_model=ExampleRead, status_code=201)
async def create(data: ExampleCreate, session: SessionDep, user: CurrentUserDep) -> ExampleRead:
    return await example_service.create_example(session, user, data)
```

Dependency (`api/deps.py`):
```python
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
```

---

## Verification
- Frontend: `pnpm lint && pnpm typecheck && pnpm build` green.
- Backend: `ruff check && mypy src && pytest` green; dependency rule enforced by review.
