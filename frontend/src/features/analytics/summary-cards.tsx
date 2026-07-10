"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { AnalyticsSummary } from "@/lib/types"

type SummaryCardsProps = {
  summary: AnalyticsSummary
}

/**
 * Headline analytics tiles. Figures render with `tabular-nums` so digits stay
 * aligned across the responsive grid (per the UI guidelines).
 */
export function SummaryCards({ summary }: SummaryCardsProps) {
  const responseRate = Math.round(summary.response_rate * 1000) / 10

  const tiles: { label: string; value: string }[] = [
    { label: "Applications", value: String(summary.totals.applications) },
    { label: "Active", value: String(summary.totals.active) },
    { label: "Interviews", value: String(summary.totals.interviews) },
    { label: "Offers", value: String(summary.totals.offers) },
    { label: "Response rate", value: `${responseRate}%` },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {tiles.map((tile) => (
        <Card key={tile.label}>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {tile.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold tabular-nums">{tile.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
