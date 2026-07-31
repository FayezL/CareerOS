"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"

/**
 * Light/dark toggle for the app header.
 *
 * `mounted` guards against a hydration mismatch: next-themes resolves the theme
 * on the client, so the icon is kept stable until after mount. The `<html>`
 * element's `suppressHydrationWarning` (set in the root layout) covers the
 * class attribute.
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  const isDark = resolvedTheme === "dark"

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        aria-label="Toggle theme"
        title="Toggle theme"
        onClick={() => setTheme(isDark ? "light" : "dark")}
      >
        <Moon className="h-5 w-5" />
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  )
}
