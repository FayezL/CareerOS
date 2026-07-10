import type { Metadata } from "next"

import { getAnalyticsFunnel, getAnalyticsOverTime, getAnalyticsSummary } from "@/lib/api-client"
import type { AnalyticsFunnel, AnalyticsOverTime, AnalyticsSummary } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ErrorState } from "@/components/error-state"
import { FunnelChart } from "@/features/analytics/funnel-chart"
import { OverTimeChart } from "@/features/analytics/over-time-chart"
import { SummaryCards } from "@/features/analytics/summary-cards"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Analytics",
  description: "Funnel, response rate, and application trends for your job search.",
}

/** Inclusive trailing 90-day window as `YYYY-MM-DD`. */
function defaultRange(): { from: string; to: string } {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 89)
  return { from: toISODate(from), to: toISODate(to) }
}

function toISODate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

export default async function AnalyticsPage() {
  const { from, to } = defaultRange()

  let summary: AnalyticsSummary | null = null
  let funnel: AnalyticsFunnel | null = null
  let overTime: AnalyticsOverTime | null = null
  let errorMessage: string | null = null

  try {
    const [summaryData, funnelData, overTimeData] = await Promise.all([
      getAnalyticsSummary(),
      getAnalyticsFunnel(),
      getAnalyticsOverTime({ from, to }),
    ])
    summary = summaryData
    funnel = funnelData
    overTime = overTimeData
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load analytics right now."
  }

  if (errorMessage || !summary || !funnel || !overTime) {
    return (
      <ErrorState
        title="Couldn't load analytics"
        description={errorMessage ?? "Unable to load analytics right now."}
      />
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Funnel, response rate, and application trends.
        </p>
      </div>

      <SummaryCards summary={summary} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Stage funnel</CardTitle>
            <CardDescription>Unique applications reaching each pipeline stage.</CardDescription>
          </CardHeader>
          <CardContent>
            <FunnelChart data={funnel.stages} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Applications over time</CardTitle>
            <CardDescription>New applications per day, last 90 days.</CardDescription>
          </CardHeader>
          <CardContent>
            <OverTimeChart data={overTime.buckets} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
