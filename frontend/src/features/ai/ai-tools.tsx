"use client"

import { type ReactNode, useActionState, useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/utils/cn"

import { generateCoverLetter, interviewPrep, tailorResume, type AIActionResult } from "./actions"

type Tool = "tailor" | "cover" | "interview"

const TABS: { id: Tool; label: string }[] = [
  { id: "tailor", label: "Resume Tailor" },
  { id: "cover", label: "Cover Letter" },
  { id: "interview", label: "Interview Prep" },
]

export function AiTools() {
  const [active, setActive] = useState<Tool>("tailor")

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Tools</CardTitle>
        <CardDescription>
          Generate tailored resumes, cover letters, and interview prep. AI runs in demo mode until
          an API key is configured.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div role="tablist" className="flex flex-wrap gap-1 rounded-lg bg-muted p-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active === tab.id}
              onClick={() => setActive(tab.id)}
              className={cn(
                "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                active === tab.id
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {active === "tailor" && <TailorResumeForm />}
        {active === "cover" && <CoverLetterForm />}
        {active === "interview" && <InterviewPrepForm />}
      </CardContent>
    </Card>
  )
}

function FieldShell({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  )
}

function ResultPanel({ state }: { state: AIActionResult }) {
  if (!state.ok || !state.result) return null
  return (
    <div className="space-y-2">
      <Label htmlFor="result">Result</Label>
      <Textarea id="result" readOnly value={state.result} rows={12} className="resize-y" />
    </div>
  )
}

function useErrorToast(state: AIActionResult) {
  useEffect(() => {
    if (!state.ok && state.error) toast.error(state.error)
  }, [state])
}

function TailorResumeForm() {
  const [state, formAction, isPending] = useActionState<AIActionResult, FormData>(
    async (_prev, formData) =>
      tailorResume({
        resume_text: String(formData.get("resume_text") ?? ""),
        job_description: String(formData.get("job_description") ?? ""),
      }),
    { ok: false },
  )
  useErrorToast(state)

  return (
    <form action={formAction} className="space-y-4">
      <FieldShell label="Your resume" htmlFor="resume_text">
        <Textarea
          id="resume_text"
          name="resume_text"
          required
          rows={8}
          placeholder="Paste your current resume here."
        />
      </FieldShell>
      <FieldShell label="Job description" htmlFor="job_description">
        <Textarea
          id="job_description"
          name="job_description"
          required
          rows={8}
          placeholder="Paste the target job description here."
        />
      </FieldShell>
      <Button type="submit" disabled={isPending}>
        {isPending ? "Tailoring…" : "Tailor resume"}
      </Button>
      <ResultPanel state={state} />
    </form>
  )
}

function CoverLetterForm() {
  const [state, formAction, isPending] = useActionState<AIActionResult, FormData>(
    async (_prev, formData) =>
      generateCoverLetter({
        company: String(formData.get("company") ?? ""),
        role: String(formData.get("role") ?? ""),
        resume_text: String(formData.get("resume_text") ?? ""),
      }),
    { ok: false },
  )
  useErrorToast(state)

  return (
    <form action={formAction} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FieldShell label="Company" htmlFor="company">
          <Input id="company" name="company" required placeholder="Acme Corp" />
        </FieldShell>
        <FieldShell label="Role" htmlFor="role">
          <Input id="role" name="role" required placeholder="Senior Engineer" />
        </FieldShell>
      </div>
      <FieldShell label="Your resume" htmlFor="cover_resume_text">
        <Textarea
          id="cover_resume_text"
          name="resume_text"
          required
          rows={8}
          placeholder="Paste your current resume here."
        />
      </FieldShell>
      <Button type="submit" disabled={isPending}>
        {isPending ? "Drafting…" : "Generate cover letter"}
      </Button>
      <ResultPanel state={state} />
    </form>
  )
}

function InterviewPrepForm() {
  const [state, formAction, isPending] = useActionState<AIActionResult, FormData>(
    async (_prev, formData) =>
      interviewPrep({
        role: String(formData.get("role") ?? ""),
        job_description: String(formData.get("job_description") ?? ""),
      }),
    { ok: false },
  )
  useErrorToast(state)

  return (
    <form action={formAction} className="space-y-4">
      <FieldShell label="Role" htmlFor="prep_role">
        <Input id="prep_role" name="role" required placeholder="Senior Engineer" />
      </FieldShell>
      <FieldShell label="Job description" htmlFor="prep_job_description">
        <Textarea
          id="prep_job_description"
          name="job_description"
          required
          rows={8}
          placeholder="Paste the target job description here."
        />
      </FieldShell>
      <Button type="submit" disabled={isPending}>
        {isPending ? "Generating…" : "Generate prep questions"}
      </Button>
      <ResultPanel state={state} />
    </form>
  )
}
