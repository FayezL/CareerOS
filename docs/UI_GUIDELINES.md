> Living document — kept up to date as CareerOS evolves. Last updated: 2026-07-08.

# CareerOS — UI Guidelines

CareerOS is a modern job-application tracker for software engineers, and its interface must feel like a premium, developer-focused tool — in the lineage of Linear and Vercel. These guidelines define the visual language, interaction patterns, and component conventions that keep the product fast, dense, calm, and consistent. They are the single source of truth for anyone building UI in CareerOS, and they work hand-in-hand with `PRODUCT.md` (what we build) and `ARCHITECTURE.md` (how the system is built). Frontend is Next.js 15 (App Router) + TypeScript + TailwindCSS + shadcn/ui, packaged with pnpm.

## Design Principles

### Calm & Dense
CareerOS surfaces a lot of data — dozens of applications, contacts, interviews — but must never feel cluttered. We achieve density through tight, rhythmic spacing, restrained color, and quiet typography, not by shrinking everything. Whitespace is a deliberate tool, not leftover room.

### Speed First
Every interaction must feel instant. We prefer skeletons over spinners, optimistic updates for board moves and edits, and route-level code splitting so navigation never blocks. Perceived performance matters as much as measured performance.

### Keyboard-First
Engineers live on the keyboard. Every primary action has a shortcut, `Cmd/Ctrl+K` opens the command palette, the board is navigable by arrow keys, and dialogs close on `Esc`. The mouse is always optional, never required.

### Dark Mode Native
Dark mode is a first-class default, not a coat of paint. Every color token is designed dark-first and light-second, surfaces layer predictably, and we never ship a component that hasn't been reviewed in both themes.

### Accessible by Default
Accessibility is a baseline requirement, not a retrofit. We target WCAG 2.1 AA, lean on Radix UI for semantics and focus management, and never use color alone to convey meaning. See `PRODUCT.md` target users — our engineers expect inclusive, professional tooling.

### Consistent Spacing
A 4px base grid governs every margin, padding, and gap. Tailwind's spacing scale maps cleanly to it, and components snap to it. Consistent spacing is the single biggest contributor to a "designed" feel.

### Content Hierarchy
Hierarchy is established through type scale, weight, and color contrast — not through boxes and borders. One clear primary action per surface; secondary actions recede. The eye should always know where to land first.

### Progressive Disclosure
Default views show the essential; detail is one click away. The board shows a card; the card opens a detail drawer with tabs; tabs reveal history, notes, documents. We never front-load everything at once.

## Design Language

CareerOS aims for a restrained, developer-tool aesthetic — the polish of Linear, the clarity of Vercel, the calm of a well-made settings page. The palette is dominated by neutral grays; a single accent color carries emphasis and interactivity. Borders are subtle and low-contrast, shadows are soft and short, and corners are gently rounded (typically 6–10px) rather than pill-soft or razor-sharp. Type is set in Inter for UI and JetBrains Mono for codes, IDs, and counts. Motion is minimal and fast. This is exactly the aesthetic shadcn/ui ships by default, and we treat that default as our baseline, customizing tokens rather than fighting the primitives. The result should feel native to a developer's existing toolchain — not a generic admin panel.

## Color System

Colors are defined as CSS custom properties in `src/styles/globals.css` and surfaced as Tailwind theme keys (`bg-background`, `text-foreground`, `border-border`, etc.). Tokens are semantic — they describe *role*, not raw color — so a single swap in `:root` and `.dark` re-themes the entire app. Light and dark are both fully specified; default behavior follows the system preference, with a manual override persisted to `localStorage` (see Dark Mode). All values avoid pure `#000` / `#fff` to keep contrast perceptually balanced.

### Core Tokens

| Token | Light | Dark | Usage |
| --- | --- | --- | --- |
| `background` | `#ffffff` | `#0a0a0a` | App canvas behind everything |
| `foreground` | `#0a0a0a` | `#fafafa` | Primary text on background |
| `card` | `#ffffff` | `#111111` | Cards, list rows, surface containers |
| `card-foreground` | `#0a0a0a` | `#fafafa` | Text on card surfaces |
| `popover` | `#ffffff` | `#161616` | Dropdowns, command palette, tooltips |
| `popover-foreground` | `#0a0a0a` | `#fafafa` | Text on popovers |
| `primary` | `#3b82f6` | `#3b82f6` | Brand accent — primary buttons, focus rings, active nav |
| `primary-foreground` | `#ffffff` | `#0a0a0a` | Text/icon on primary surfaces |
| `secondary` | `#f4f4f5` | `#1c1c1c` | Secondary buttons, subtle fills |
| `secondary-foreground` | `#18181b` | `#fafafa` | Text on secondary surfaces |
| `muted` | `#f4f4f5` | `#1c1c1c` | Inactive backgrounds, table zebra |
| `muted-foreground` | `#71717a` | `#a1a1aa` | Captions, secondary text, placeholders |
| `accent` | `#eff6ff` | `#1e293b` | Hover fills, selected row highlight |
| `accent-foreground` | `#1d4ed8` | `#fafafa` | Text on accent surfaces |
| `destructive` | `#dc2626` | `#ef4444` | Delete, reject, error actions |
| `destructive-foreground` | `#ffffff` | `#0a0a0a` | Text on destructive surfaces |
| `border` | `#e4e4e7` | `#262626` | Hairline borders, dividers |
| `input` | `#e4e4e7` | `#262626` | Form field borders |
| `ring` | `#3b82f6` | `#3b82f6` | Focus-visible outline on all interactive elements |

The accent (`primary`) is the only intentionally colorful brand element. Every other emphasis comes from neutral contrast, type weight, or status semantics below.

### Status / Semantic Palette

Status colors are used for application stages, badges, toasts, and analytics. Each has a soft tinted background variant (for badges) and a saturated foreground (for icons/text). Never rely on color alone — always pair with a text label or icon.

| Status | Foreground (Light / Dark) | Background (Light / Dark) | Usage in CareerOS |
| --- | --- | --- | --- |
| **Success** (green) | `#16a34a` / `#22c55e` | `#f0fdf4` / `#052e16` | "Accepted", positive funnel movement, saved-toaster |
| **Warning** (amber) | `#d97706` / `#f59e0b` | `#fffbeb` / `#3a2a06` | Stale application, overdue reminder, follow-up due |
| **Danger** (red) | `#dc2626` / `#ef4444` | `#fef2f2` / `#3a0a0a` | "Rejected", destructive confirm, validation error |
| **Info** (blue) | `#2563eb` / `#3b82f6` | `#eff6ff` / `#0c1f3d` | Scheduled interview, neutral informational toast |
| **Neutral** (slate) | `#71717a` / `#a1a1aa` | `#f4f4f5` / `#1c1c1c` | "Applied", default/quiet stage, draft state |

These map onto pipeline stages in `PRODUCT.md`: Applied = Neutral, Screening/Interview = Info, Offer = Success, Rejected = Danger.

## Typography

UI text uses **Inter**, loaded via `next/font` and set as the default Tailwind `font-sans`. Counts, application IDs, codes, and keyboard hints use **JetBrains Mono** as `font-mono`. Base font size is 14px (Tailwind `text-sm`) for density; line-heights are tight. Type scale is intentionally compressed — a developer tool rewards information per viewport.

| Token | Size / Line-height | Weight | Usage |
| --- | --- | --- | --- |
| `text-3xl` | 30 / 36 | 600 (semibold) | Landing/empty-state hero headings only |
| `text-2xl` | 24 / 32 | 600 | Page titles (rare, top-level analytics) |
| `text-xl` | 20 / 28 | 600 | `h1` — page heading (e.g. "Pipeline") |
| `text-lg` | 18 / 28 | 600 | `h2` — section heading, dialog title |
| `text-base` | 16 / 24 | 500–600 | `h3`, dialog titles on desktop |
| `text-sm` | 14 / 20 | 400–500 | Body — default for all UI text |
| `text-sm` (mono) | 14 / 20 | 500 | IDs, counts, shortcuts, metadata |
| `text-xs` | 12 / 16 | 500 | Caption, table headers, badges, helper text |
| `text-xs` (uppercase) | 12 / 16 | 600 | Overline labels, eyebrow text |

Number-heavy figures (counts in board columns, analytics stats) use tabular-nums via `font-variant-numeric: tabular-nums` so digits align in columns.

## Spacing & Layout

All spacing is on a **4px base grid**. Tailwind's default scale (`1` = 4px, `2` = 8px, `3` = 12px, `4` = 16px, `6` = 24px, `8` = 32px, `12` = 48px) maps directly to it — use these tokens and never hard-coded pixel values. Typical rhythm: 8px between related fields, 12–16px between groups in a card, 24px between top-level sections, 32px page padding on desktop.

### App Shell

- **Max content width:** 1280px for the app shell (sidebar + main); reading-heavy surfaces (notes editor, onboarding) center at **768px**.
- **App shell pattern:** a persistent left sidebar (collapsible to icon-rail) + a top bar + a scrollable main content area. See the wireframe under App Shell & Navigation.
- **Main content padding:** 24px (`p-6`) on desktop, 16px (`p-4`) on mobile.

### Responsive Breakpoints

| Breakpoint | Min width | Target |
| --- | --- | --- |
| `sm` | 640px | Large phones in portrait |
| `md` | 768px | Tablets; sidebar collapses to rail |
| `lg` | 1024px | Small laptops; board shows all columns with horizontal scroll |
| `xl` | 1280px | Desktop; full app shell, comfortable density |
| `2xl` | 1536px | Large monitors; multi-column analytics grids |

CareerOS is desktop-first — the board and dense tables are the primary surfaces — but every route must remain usable down to `sm` by collapsing the sidebar into a Sheet and stacking content. Mobile is supported but not optimized for heavy data entry.

## Component Conventions

We build on **shadcn/ui** primitives (Radix UI + Tailwind). Primitives live in `src/components/ui` and are treated as *owned* code — copy them in, then customize freely; never patch `node_modules`. Composed, app-agnostic components (e.g. `AppShell`, `PageHeader`, `EmptyState`) live in `src/components`. Feature-specific, stateful components live in `src/features/<feature>` alongside their hooks, types, and API calls. If a component is reused across two or more features, promote it to `src/components`; if it wraps a single primitive with no app logic, keep it in `src/components/ui`.

Forms always pair **react-hook-form** with **zod** schemas (schemas in `src/lib`), wired via shadcn's `Form` + `FormField`/`FormItem`/`FormControl`/`FormMessage`. Never hand-roll form state.

### Key Components

**Button** — the primary action primitive. Variants communicate hierarchy; sizes control density. One `default` primary per surface.

| Variant | Size `sm` | Size `default` | Size `lg` | Size `icon` | When to use |
| --- | --- | --- | --- | --- | --- |
| `default` (primary) | 32px | 36px | 40px | — | The single primary action on a surface ("New application") |
| `secondary` | 32px | 36px | 40px | — | Secondary, cancel, alternative actions |
| `outline` | 32px | 36px | 40px | — | Tertiary actions, filters, toolbars |
| `ghost` | 32px | 36px | 40px | 36px | Inline actions, row actions, nav items |
| `destructive` | 32px | 36px | 40px | — | Delete, reject confirmations |
| `link` | — | — | — | — | Inline text links inside paragraphs |

Loading state renders a small spinner inside the button and disables it; never swap the label.

**Card** — the universal surface for list rows, dashboard tiles, and detail sections. `rounded-lg`, `border`, `bg-card`, `p-4`/`p-6`. No drop shadow by default; reserve shadow for floating layers (popovers, dialogs).

**Dialog / Sheet** — use `Dialog` for focused actions (confirm, quick-edit), `Sheet` for the application detail panel sliding from the right on desktop. All have `Esc` to close, focus trap, and restore focus on close — provided by Radix.

**Form** — react-hook-form + zod; inline error text below each field via `FormMessage`; submit button shows loading state; disable submit until valid where appropriate.

**Table / DataTable** — for the applications list, companies, contacts. Sticky header, `text-xs` uppercase column headers, `hover:bg-accent/50` rows, optional zebra via `muted/50`. Sort indicators on columns that support it.

**Badge** — small, uppercase or sentence-case label for stage/status. Uses the status palette. Always pairs text with optional leading dot or icon.

**Toast / Sonner** — Sonner for transient feedback (saved, copied, error). Auto-dismiss ~4s, stacked bottom-right; destructive toasts persist until dismissed.

**Dropdown** — `DropdownMenu` for row actions and the user menu. Group related actions; separate destructive items with a divider and tint them `text-destructive`.

**Command (cmdk)** — the `Cmd/Ctrl+K` palette for navigation, quick search, and quick actions. Fuzzy-matched, grouped (Pages, Applications, Actions), keyboard-driven.

**Skeleton** — `bg-muted` shimmering placeholder, same dimensions as the real content. Used everywhere content loads (see Loading States). Never a spinner for content.

**EmptyState** — center-aligned block: icon (lucide, 24px), `h3` title, `text-sm muted` description, and a primary CTA. Used on first-run and after filters return nothing.

**Tabs** — `underline` variant for in-page section switching (application detail); `pill` variant is not used. Keyboard arrows move between tabs.

## Interaction States

Every interactive element must define and visibly support all six states. Test each in both light and dark.

| State | Treatment |
| --- | --- |
| **Default** | Resting styles per variant |
| **Hover** | Subtle background/foreground shift toward `accent` or `muted`; never layout shift |
| **Focus-visible** | 2px `ring` color (`--ring`) with 2px offset — visible on every keyboard-focusable element |
| **Active** | Slightly darker fill than hover; provides tactile feedback on click |
| **Disabled** | `opacity-50`, `cursor-not-allowed`, removed from tab order; never just greyed text |
| **Loading** | Buttons: inline spinner + disabled. Content: skeletons (never spinners) |

Hover and focus states must never cause layout reflow (no border-width or size changes) — use box-shadow or color shifts only.

## Loading / Empty / Error States

Consistent placeholder states keep the app feeling stable under any network condition.

**Loading — Skeletons first.** Replace the expected content shape with shimmering `Skeleton` blocks of matching dimensions: list rows become 3–6 skeleton rows, cards become skeleton cards, dashboard tiles become skeleton rectangles. Route transitions show a skeleton of the route shell. Buttons and inline actions may use a small spinner *inside* the control. Never use a full-page spinner for content areas.

```
┌───────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓                 │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     │
└───────────────────────────────────────┘
```

**EmptyState — guide the next action.** Used on first run and whenever a list/filter returns nothing. Centered, with an icon, a short title, one-line description, and a primary CTA. Example: empty Pipeline shows a `Kanban` icon, "No applications yet", "Add your first application to start tracking your search.", and a "New application" button.

```
                  ┌─────┐
                  │  ◇  │
                  └─────┘
            No applications yet
   Add your first application to start
          tracking your search.
           [ + New application ]
```

**ErrorState — message + retry.** Replaces the failed region with an icon, a plain-language message (never a raw stack trace), and a "Try again" button that re-triggers the query. Form errors render inline below each field in `text-destructive` `text-xs`. Network-level errors surface a Sonner toast with a retry action.

## Dark Mode

Dark mode is the **default** and a first-class theme — designed dark-first, then light. Strategy:

- **Class-based toggle.** A `.dark` class on `<html>` enables dark tokens; absence defaults to light. State is persisted to `localStorage` under `careeros.theme`.
- **Default to system.** On first visit, resolve `prefers-color-scheme` and follow it until the user explicitly chooses. The toggle in Settings/User menu cycles System → Light → Dark.
- **Contrast targets.** Body text meets WCAG AA (≥ 4.5:1) in both themes; large text and UI components meet ≥ 3:1. Verify every token pair.
- **Surface layering.** Layer from dark to darker as elevation increases: `background` (canvas) → `card` (raised) → `popover` (floating). Higher layers are *lighter* in dark mode (counter-intuitively) so they read as elevated; in light mode they're near-white.
- **No pure black/white.** Darkest surface is `#0a0a0a`, not `#000`; lightest is `#ffffff` only for the canvas. Borders stay low-contrast to avoid a "drawn-on" look.

## Accessibility

CareerOS targets **WCAG 2.1 AA** and treats accessibility as a baseline, not a feature. Radix UI primitives handle much of the heavy lifting (focus management, ARIA, keyboard interaction), but app code must follow:

- **Semantic HTML first.** Use `<nav>`, `<main>`, `<button>`, `<a>`, real `<table>` semantics — not divs with click handlers.
- **Visible focus.** Every interactive element shows the 2px focus ring on `:focus-visible`. Never remove outlines without a replacement.
- **Keyboard navigation.** The board, lists, and tables are fully operable by keyboard (arrows, Enter, Esc). Custom widgets publish an ARIA pattern.
- **Labeled icon buttons.** Every icon-only button has an `aria-label` (e.g. a trash button → `aria-label="Delete application"`).
- **Color contrast.** All text meets ≥ 4.5:1; large text and UI components ≥ 3:1.
- **No color-only signaling.** Stage and status always pair color with a text label or icon — a red badge says "Rejected", it isn't just red.
- **Reduced motion.** Respect `prefers-reduced-motion`: disable shimmer, shorten/disable transitions, replace slide with fade.
- **Skip links.** A "Skip to content" link is the first focusable element in the DOM, visible on focus, jumping past the sidebar to `#main`.

## Iconography

Icons come exclusively from **lucide-react**, matching shadcn/ui defaults. Rules:

- **Stroke width:** 1.75px default (set on the icon or via CSS), never below 1.5 or above 2.
- **Sizes:** 16px (`size-4`) for inline/badges, 20px (`size-5`) for buttons/menus, 24px (`size-6`) for empty states and feature tiles. Stay on these three.
- **Always labeled for a11y.** Decorative icons are `aria-hidden`; functional icon-only buttons get an `aria-label`.
- **Consistency.** Don't mix outline and filled icons. CareerOS uses outline (stroke) icons throughout.

## Motion

Motion is subtle, fast, and purposeful — it clarifies state changes, never decorates.

- **Duration:** 150–250ms for most transitions (hover, focus, open/close). Avoid anything over 300ms except large panel slides.
- **Easing:** `ease-out` for entrances, `ease-in` for exits; or a single `cubic-bezier(0.32, 0.72, 0, 1)` for the Linear-style feel.
- **Reduced motion.** `@media (prefers-reduced-motion: reduce)` disables shimmer and reduces transitions to opacity-only or removes them entirely.
- **No gratuitous animation.** No parallax, no auto-rotating carousels, no bounce on mount.
- **Board drag.** DnD with `@dnd-kit` uses transform-based movement with no spring physics — items snap, they don't wobble. Drop feedback is a clean placeholder, not a flourish.

## App Shell & Navigation

CareerOS uses a persistent **left sidebar + top bar + main content** shell, shared across all authenticated routes. The sidebar carries primary navigation; the top bar carries global search, the primary creation action, and the user menu; the main area renders the active route with breadcrumbs above the page title.

**Sidebar navigation** (top to bottom), mirroring the features in `PRODUCT.md`:

1. **Dashboard** — upcoming interviews, due reminders, funnel snapshot
2. **Pipeline** — the Kanban board (default landing)
3. **Applications** — filterable list/table
4. **Companies** — companies directory
5. **Contacts** — recruiters and people
6. **Interviews** — calendar + list of events
7. **Documents** — resumes and files
8. **Analytics** — funnel and response-rate dashboard
9. **Settings** — profile, stages config, reminders rules, theme

**Top bar:** a `Cmd/Ctrl+K` search field (opens the command palette), a primary `+ New application` button, a notifications bell for reminders, and the user menu (avatar dropdown → Settings, theme toggle, Sign out).

**Wireframe:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  CareerOS        ⌘K  Search applications, companies, people…    [ + New ] │
├────────────┬─────────────────────────────────────────────────────────────┤
│            │  Pipeline / Active                                          │
│  Dashboard │ ┌─────────────────────────────────────────────────────────┐  │
│  Pipeline ●│ │  Page title + filters + view toggle                     │  │
│  Applicat. │ ├─────────────────────────────────────────────────────────┤  │
│  Companies │ │                                                         │  │
│  Contacts  │ │                  Main content area                      │  │
│  Interview │ │                  (board / list / detail / charts)       │  │
│  Documents │ │                                                         │  │
│  Analytics │ │                                                         │  │
│            │ │                                                         │  │
│ ─────────  │ │                                                         │  │
│  Settings  │ │                                                         │  │
│  ◐ Theme   │ │                                                         │  │
│  □ Avatar  │ │                                                         │  │
└────────────┴─────────────────────────────────────────────────────────────┘
   Sidebar (240px)        Main content (max 1280px, p-6, scrollable)
```

On `< lg`, the sidebar collapses into an icon rail (56px); on `< md`, it hides entirely behind a hamburger that opens it as a Sheet. Breadcrumbs above the page title reflect the route hierarchy (e.g. `Pipeline / Active`, `Applications / Stripe — Senior Engineer`).

## Patterns for Core Surfaces

**Kanban board (Pipeline).** Columns map 1:1 to pipeline stages (Applied, Screening, Interview, Offer, Rejected, Accepted by default — configurable per `PRODUCT.md`). Each column header shows the stage name and a tabular-num count. Cards are compact: company, role title, source badge, last-updated timestamp, and an optional stale/priority dot. Drag-and-drop is powered by `@dnd-kit` with transform-based movement (no spring); cross-column moves fire an optimistic stage update with rollback on failure. The board scrolls horizontally when column count exceeds viewport width — never let columns shrink below a readable card width. Each card is keyboard-focusable; Enter opens the detail Sheet.

**Application detail.** Opens as a right-side **Sheet** on desktop (full-screen on mobile) with a header (company, role, stage badge, primary actions) and an `underline` Tabs row: **Overview** (key fields, source, dates, linked company/contact), **Notes** (timestamped rich-text thread), **Interviews** (events tied to this application), **Documents** (attached resume versions and files), and **History** (auditable stage-transition log). Tabs lazy-load their content with per-tab skeletons so the Sheet opens instantly.

**Analytics dashboard.** A responsive grid of `Card` tiles: headline stat cards (total applications, active loops, response rate, offers) with large tabular-num figures and delta indicators, followed by charts built with **recharts** — a stage-to-stage funnel bar chart, an applications-over-time area chart, and a source-breakdown donut. Charts use semantic status colors for stage series, muted neutrals for axes and gridlines, and render with skeleton placeholders while data loads. All figures update from the same data model described in `PRODUCT.md`.

## Performance & Perceived Speed

Speed is a design principle (`Speed First`), enforced through concrete techniques:

- **Prefetch on hover.** Navigation links and command-palette results prefetch their route data on hover/focus so the click lands instantly.
- **Optimistic updates.** Board moves, stage changes, and quick edits apply to the UI immediately and roll back on server error, surfaced via Sonner.
- **Skeleton-first loading.** Every async surface renders skeletons matching its content shape before data arrives (see Loading States).
- **Route-level code splitting.** App Router handles per-route splitting; heavy views (Analytics charts, the rich-text editor) are dynamic imports with their own skeletons.
- **Image optimization.** All images go through `next/image` with explicit dimensions; avatars and logos use appropriately sized `srcset` variants.
- **Virtualize long lists.** Applications, contacts, and notes threads longer than ~50 rows use `@tanstack/react-virtual` to avoid rendering the full DOM.

---

*These guidelines govern every screen in CareerOS. For what we build, see `PRODUCT.md`; for how the system is structured behind the UI, see `ARCHITECTURE.md`. When a pattern isn't covered here, default to the shadcn/ui convention and document the decision here.*
