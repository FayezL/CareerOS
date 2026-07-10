"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import type { FunnelPoint } from "@/lib/types"

type FunnelChartProps = {
  data: FunnelPoint[]
}

const tooltipStyle: React.CSSProperties = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.5rem",
  color: "hsl(var(--popover-foreground))",
  fontSize: "12px",
}

type StageDatum = { name: string; count: number }

/**
 * Stage-to-stage funnel. Bars are ordered by stage `position` and sized by the
 * number of unique applications that have ever entered each stage.
 */
export function FunnelChart({ data }: FunnelChartProps) {
  const chartData: StageDatum[] = [...data]
    .sort((a, b) => a.position - b.position)
    .map((point) => ({ name: point.name, count: point.distinct_applications }))

  if (chartData.length === 0) {
    return <EmptyChart label="No stage data yet." />
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            interval={0}
            angle={-15}
            textAnchor="end"
            height={48}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          <Tooltip
            cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }}
            contentStyle={tooltipStyle}
            formatter={(value) => [value, "Applications"]}
          />
          <Bar dataKey="count" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} maxBarSize={64} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex h-72 w-full items-center justify-center text-sm text-muted-foreground">
      {label}
    </div>
  )
}
