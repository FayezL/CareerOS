import type { Metadata } from "next"

import { AiTools } from "@/features/ai/ai-tools"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "AI Tools",
  description:
    "Tailor your resume, draft cover letters, and prepare for interviews with AI-assisted tools.",
}

export default function AiPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI Tools</h1>
        <p className="text-sm text-muted-foreground">
          Tailor resumes, draft cover letters, and prep for interviews.
        </p>
      </div>

      <AiTools />
    </div>
  )
}
