"use client"

import { useActionState, useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"

import type { Company, Contact, ContactRole } from "@/lib/types"
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

import { createContact, updateContact, type ActionResult } from "./actions"

const ROLE_OPTIONS: { value: ContactRole; label: string }[] = [
  { value: "recruiter", label: "Recruiter" },
  { value: "hiring_manager", label: "Hiring manager" },
  { value: "interviewer", label: "Interviewer" },
  { value: "referral", label: "Referral" },
  { value: "other", label: "Other" },
]

type ContactFormProps = {
  companies: Company[]
  contact?: Contact
  trigger: ReactNode
}

/**
 * Create/edit dialog for a contact. The outer component owns the dialog's open
 * state and trigger; the inner form (with its `useActionState`) lives inside
 * `DialogContent`, which Radix only mounts while open — so each open begins
 * with a fresh action state and prefilled defaults.
 */
export function ContactForm({ companies, contact, trigger }: ContactFormProps) {
  const [open, setOpen] = useState(false)
  const close = useCallback(() => setOpen(false), [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <ContactFormFields companies={companies} contact={contact} onClose={close} />
      </DialogContent>
    </Dialog>
  )
}

type ContactFormFieldsProps = {
  companies: Company[]
  contact?: Contact
  onClose: () => void
}

function ContactFormFields({ companies, contact, onClose }: ContactFormFieldsProps) {
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    async (_prevState, formData) => {
      const fn = contact ? updateContact.bind(null, contact.id) : createContact
      return fn(formData)
    },
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success(contact ? "Contact updated" : "Contact created")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, contact, onClose])

  const defaultRole = contact?.role ?? "recruiter"

  return (
    <>
      <DialogHeader>
        <DialogTitle>{contact ? "Edit contact" : "New contact"}</DialogTitle>
        <DialogDescription>
          {contact
            ? "Update this person's details."
            : "Track a recruiter, hiring manager, or referral."}
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" name="name" required defaultValue={contact?.name ?? ""} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              inputMode="email"
              placeholder="name@company.com"
              defaultValue={contact?.email ?? ""}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Select name="role" defaultValue={defaultRole}>
              <SelectTrigger id="role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROLE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="company_id">Company</Label>
            <Select name="company_id" defaultValue={contact?.company_id ?? undefined}>
              <SelectTrigger id="company_id">
                <SelectValue placeholder="No company" />
              </SelectTrigger>
              <SelectContent>
                {companies.map((company) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="linkedin_url">LinkedIn URL</Label>
            <Input
              id="linkedin_url"
              name="linkedin_url"
              type="url"
              inputMode="url"
              placeholder="https://linkedin.com/in/name"
              defaultValue={contact?.linkedin_url ?? ""}
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save contact"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
