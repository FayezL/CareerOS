import type { ReactNode } from "react"
import Link from "next/link"
import { BarChart3, Briefcase, Sparkles, Workflow } from "lucide-react"

const FEATURES = [
  {
    icon: Workflow,
    title: "Visual pipeline",
    body: "Drag-and-drop every application from applied to offer.",
  },
  {
    icon: BarChart3,
    title: "Real analytics",
    body: "Funnel, response rate, and trends — not just a list.",
  },
  {
    icon: Sparkles,
    title: "AI assist",
    body: "Tailor resumes, draft cover letters, prep for interviews.",
  },
]

/**
 * Two-column auth shell: a dark branded panel on the left (logo, value prop,
 * feature highlights) and a clean, centered form area on the right. On mobile
 * the branded panel collapses away and only a compact logo + the form remain.
 *
 * Inspried by the split-screen sign-in pattern used by Linear / Stripe / Notion.
 */
export function AuthLayout({
  children,
  title,
  subtitle,
}: {
  children: ReactNode
  title: string
  subtitle: string
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      {/* Branded panel */}
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-zinc-950 p-10 text-zinc-100 lg:flex xl:p-14">
        {/* ambient glow — one subtle radial, kept restrained */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-70 [background:radial-gradient(60%_50%_at_15%_0%,rgba(99,102,241,0.18),transparent_60%),radial-gradient(50%_40%_at_100%_100%,rgba(168,85,247,0.12),transparent_55%)]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.04] [background-image:linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] [background-size:44px_44px]"
        />

        {/* Brand */}
        <Link href="/" className="relative flex items-center gap-2.5">
          <span className="flex size-9 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15 backdrop-blur">
            <Briefcase className="size-5" />
          </span>
          <span className="text-lg font-semibold tracking-tight">CareerOS</span>
        </Link>

        {/* Value proposition */}
        <div className="relative max-w-md space-y-6">
          <h1 className="text-balance text-3xl font-semibold leading-tight tracking-tight xl:text-4xl">
            Your operating system for the job search.
          </h1>
          <p className="text-pretty text-[15px] leading-relaxed text-zinc-400">
            Track applications, organize your network, and surface the opportunities that actually
            move you forward — all in one place.
          </p>
          <ul className="space-y-4 pt-2">
            {FEATURES.map((f) => (
              <li key={f.title} className="flex items-start gap-3">
                <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-white/[0.06] text-zinc-200 ring-1 ring-white/10">
                  <f.icon className="size-4" />
                </span>
                <div>
                  <p className="text-sm font-medium text-zinc-100">{f.title}</p>
                  <p className="text-sm text-zinc-400">{f.body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <p className="relative text-xs text-zinc-500">
          &ldquo;It feels like how a modern job search should work.&rdquo;
        </p>
      </aside>

      {/* Form panel */}
      <main className="flex flex-col bg-background">
        {/* compact brand on mobile/tablet */}
        <Link href="/" className="flex items-center gap-2.5 px-6 pt-8 lg:hidden">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Briefcase className="size-5" />
          </span>
          <span className="text-lg font-semibold tracking-tight">CareerOS</span>
        </Link>

        <div className="flex flex-1 items-center justify-center px-6 py-10">
          <div className="w-full max-w-sm space-y-6">
            <div className="space-y-1.5">
              <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
              <p className="text-sm text-muted-foreground">{subtitle}</p>
            </div>
            <div className="[&_.cl-form-button-primary]:w-full">{children}</div>
          </div>
        </div>
      </main>
    </div>
  )
}
