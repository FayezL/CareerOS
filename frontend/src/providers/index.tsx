import type { ReactNode } from "react"
import { ClerkProvider } from "@clerk/nextjs"
import { shadcn } from "@clerk/ui/themes"

import { ThemeProvider } from "@/components/theme-provider"

// ClerkProvider runs at build time (e.g. when prerendering the not-found page),
// so it must never receive a malformed key during `next build`. The publishable
// key is a public env var inlined at build; we fall back to a format-valid
// placeholder whenever it is missing OR malformed (CI/Docker builds). Strict
// runtime validation of the API base URL lives in the data-fetch path
// (see src/schemas/env.ts).
const FALLBACK_CLERK_PUBLISHABLE_KEY = "pk_test_Zm9vLWJhci0xMy5jbGVray5hY2NvdW50cy5kZXYk"

function resolveClerkPublishableKey(): string {
  const raw = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  if (!raw) return FALLBACK_CLERK_PUBLISHABLE_KEY
  // Clerk publishable keys are `pk_(test|live)_<base64>` where the base64
  // payload decodes to `<frontend-api>.clerk.accounts.dev$`.
  const match = /^pk_(?:test|live)_(.+)$/.exec(raw)
  if (!match) return FALLBACK_CLERK_PUBLISHABLE_KEY
  try {
    const decoded = Buffer.from(match[1], "base64").toString("utf-8")
    if (!decoded.endsWith("$")) return FALLBACK_CLERK_PUBLISHABLE_KEY
    return raw
  } catch {
    return FALLBACK_CLERK_PUBLISHABLE_KEY
  }
}

const clerkPublishableKey = resolveClerkPublishableKey()

/**
 * Compose every app-wide provider in one place so the root layout stays thin.
 *
 * Kept as a Server Component (no `"use client"`) so the build-time Clerk
 * publishable-key resolution above runs server-side only.
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider publishableKey={clerkPublishableKey} appearance={{ theme: shadcn }}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        {children}
      </ThemeProvider>
    </ClerkProvider>
  )
}
