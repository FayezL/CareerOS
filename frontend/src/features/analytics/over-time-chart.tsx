"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { OverTimePoint } from "@/lib/types"

type OverTimeChartProps = {
  data: OverTimePoint[]
}

const tooltipStyle: React.CSSProperties = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.5rem",
  color: "hsl(var(--popover-foreground))",
  fontSize: "12px",
}

type BucketDatum = { date: string; count: number }

/** Applications created per day, rendered as a soft area chart. */
export function OverTimeChart({ data }: OverTimeChartProps) {
  const chartData: BucketDatum[] = data.map((point) => ({
    date: point.bucket,
    count: point.applications,
  }))

  if (chartData.length === 0) {
    return <EmptyChart label="No applications in this window yet." />
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <defs>
            <linearGradient id="overTimeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--chart-2))" stopOpacity={0.35} />
              <stop offset="100%" stopColor="hsl(var(--chart-2))" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={{ stroke: "hsl(var(--border))" }}
            minTickGap={24}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            labelFormatter={(label) => formatDate(String(label))}
            formatter={(value) => [value, "Applications"]}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="hsl(var(--chart-2))"
            strokeWidth={2}
            fill="url(#overTimeFill)"
          />
        </AreaChart>
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

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}
