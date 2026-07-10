"use client"

import { useActionState, useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"

import type { Application, ApplicationStatus, Company } from "@/lib/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

import { createApplication, updateApplication, type ActionResult } from "./actions"

const STATUS_OPTIONS: { value: ApplicationStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
  { value: "rejected", label: "Rejected" },
  { value: "accepted", label: "Accepted" },
]

type ApplicationFormProps = {
  companies: Company[]
  application?: Application
  trigger: ReactNode
}

/**
 * Create/edit dialog for an application. The outer component owns the dialog's
 * open state and trigger; the inner form (with its `useActionState`) lives in
 * `DialogContent`, which Radix only mounts while open, so each open begins with
 * a fresh action state and prefilled defaults.
 */
export function ApplicationForm({ companies, application, trigger }: ApplicationFormProps) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[560px]">
        <ApplicationFormFields companies={companies} application={application} onClose={close} />
      </DialogContent>
    </Dialog>
  )
}

type ApplicationFormFieldsProps = {
  companies: Company[]
  application?: Application
  onClose: () => void
}

function ApplicationFormFields({ companies, application, onClose }: ApplicationFormFieldsProps) {
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    async (_prevState, formData) => {
      const fn = application ? updateApplication.bind(null, application.id) : createApplication
      return fn(formData)
    },
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success(application ? "Application updated" : "Application created")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, application, onClose])

  const defaultCompanyId = application?.company_id ?? companies[0]?.id
  const defaultStatus = application?.status ?? "active"
  const appliedDate = application?.applied_at ? application.applied_at.slice(0, 10) : ""

  return (
    <>
      <DialogHeader>
        <DialogTitle>{application ? "Edit application" : "New application"}</DialogTitle>
        <DialogDescription>
          {application ? "Update this application's details." : "Track a role you're pursuing."}
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="company_id">Company</Label>
            {companies.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Add a company first, then create an application.
              </p>
            ) : (
              <Select name="company_id" defaultValue={defaultCompanyId} required>
                <SelectTrigger id="company_id">
                  <SelectValue placeholder="Select a company" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="role_title">Role title</Label>
            <Input
              id="role_title"
              name="role_title"
              required
              placeholder="Senior Software Engineer"
              defaultValue={application?.role_title ?? ""}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select name="status" defaultValue={defaultStatus}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="applied_at">Applied on</Label>
            <Input id="applied_at" name="applied_at" type="date" defaultValue={appliedDate} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="job_url">Job URL</Label>
            <Input
              id="job_url"
              name="job_url"
              type="url"
              inputMode="url"
              placeholder="https://jobs.example.com/123"
              defaultValue={application?.job_url ?? ""}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="source">Source</Label>
            <Input
              id="source"
              name="source"
              placeholder="LinkedIn, referral, careers page…"
              defaultValue={application?.source ?? ""}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="salary_min">Salary min</Label>
            <Input
              id="salary_min"
              name="salary_min"
              type="number"
              min="0"
              step="any"
              inputMode="numeric"
              placeholder="80000"
              defaultValue={application?.salary_min ?? ""}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="salary_max">Salary max</Label>
            <Input
              id="salary_max"
              name="salary_max"
              type="number"
              min="0"
              step="any"
              inputMode="numeric"
              placeholder="120000"
              defaultValue={application?.salary_max ?? ""}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="salary_currency">Currency</Label>
            <Input
              id="salary_currency"
              name="salary_currency"
              placeholder="USD"
              defaultValue={application?.salary_currency ?? ""}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="job_description">Job description</Label>
          <Textarea
            id="job_description"
            name="job_description"
            rows={4}
            placeholder="Paste the role description for quick reference."
            defaultValue={application?.job_description ?? ""}
          />
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save application"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
