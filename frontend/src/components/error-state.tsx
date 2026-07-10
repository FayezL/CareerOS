"use client"

import { AlertCircle } from "lucide-react"

import { Button } from "@/components/ui/button"

type ErrorStateProps = {
  title?: string
  description?: string
  /** Optional retry handler; renders a "Try again" button when provided. */
  retry?: () => void
}

/**
 * Replaces a failed region with a plain-language message and an optional retry
 * action — never a raw stack trace. See `docs/UI_GUIDELINES.md` (ErrorState).
 */
export function ErrorState({
  title = "Something went wrong",
  description,
  retry,
}: ErrorStateProps) {
  return (
    <div className="mx-auto mt-12 flex w-full max-w-md flex-col items-center gap-3 rounded-lg border border-border bg-card p-6 text-center text-card-foreground shadow-sm">
      <div className="rounded-full bg-destructive/10 p-3">
        <AlertCircle className="h-6 w-6 text-destructive" />
      </div>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {retry ? (
        <Button variant="outline" onClick={retry}>
          Try again
        </Button>
      ) : null}
    </div>
  )
}
