"use client"

import { useActionState, useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"

import type { Company } from "@/types"
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
import { Textarea } from "@/components/ui/textarea"

import { createCompany, updateCompany, type ActionResult } from "./actions"

type CompanyFormProps = {
  company?: Company
  trigger: ReactNode
}

/**
 * Create/edit dialog for a company. The outer component owns the dialog's open
 * state and trigger; the inner form (with its `useActionState`) lives inside
 * `DialogContent`, which Radix only mounts while open — so each open starts with
 * a fresh action state and prefilled defaults.
 */
export function CompanyForm({ company, trigger }: CompanyFormProps) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <CompanyFormFields company={company} onClose={close} />
      </DialogContent>
    </Dialog>
  )
}

type CompanyFormFieldsProps = {
  company?: Company
  onClose: () => void
}

function CompanyFormFields({ company, onClose }: CompanyFormFieldsProps) {
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    async (_prevState, formData) => {
      const fn = company ? updateCompany.bind(null, company.id) : createCompany
      return fn(formData)
    },
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success(company ? "Company updated" : "Company created")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, company, onClose])

  return (
    <>
      <DialogHeader>
        <DialogTitle>{company ? "Edit company" : "New company"}</DialogTitle>
        <DialogDescription>
          {company ? "Update this company's details." : "Add a company you're engaging with."}
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" name="name" required defaultValue={company?.name ?? ""} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              name="website"
              type="url"
              inputMode="url"
              placeholder="https://example.com"
              defaultValue={company?.website ?? ""}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="industry">Industry</Label>
            <Input id="industry" name="industry" defaultValue={company?.industry ?? ""} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="size">Size</Label>
            <Input id="size" name="size" placeholder="1-50" defaultValue={company?.size ?? ""} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              name="location"
              placeholder="Remote / San Francisco"
              defaultValue={company?.location ?? ""}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="linkedin_url">LinkedIn URL</Label>
          <Input
            id="linkedin_url"
            name="linkedin_url"
            type="url"
            inputMode="url"
            placeholder="https://linkedin.com/company/example"
            defaultValue={company?.linkedin_url ?? ""}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            name="notes"
            rows={3}
            placeholder="Anything worth remembering about this company."
            defaultValue={company?.notes ?? ""}
          />
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save company"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
