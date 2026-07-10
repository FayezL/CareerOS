import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { ClerkProvider } from "@clerk/nextjs"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

// ClerkProvider runs at build time (e.g. when prerendering the not-found page),
// so it must never receive a malformed key during `next build`. The publishable
// key is a public env var inlined at build; we fall back to a format-valid
// placeholder whenever it is missing OR malformed (CI/Docker builds). Strict
// runtime validation of the API base URL lives in the data-fetch path
// (see src/lib/env.ts).
const FALLBACK_CLERK_PUBLISHABLE_KEY = "pk_test_Zm9vLWJhci0xMy5jbGVyay5hY2NvdW50cy5kZXYk"

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

export const metadata: Metadata = {
  title: "CareerOS",
  description: "Your operating system for career growth.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ClerkProvider publishableKey={clerkPublishableKey}>
      <html lang="en" suppressHydrationWarning>
        <body className={`${inter.variable} font-sans antialiased`}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <Toaster />
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  )
}
