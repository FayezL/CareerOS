"use client"

import { useTransition } from "react"
import { Pencil, Plus, Trash2, Users } from "lucide-react"
import { toast } from "sonner"

import type { Company, Contact, ContactRole } from "@/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/empty-state"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { ContactForm } from "./contact-form"
import { deleteContact } from "./actions"

type ContactsTableProps = {
  contacts: Contact[]
  companies: Company[]
}

export function ContactsTable({ contacts, companies }: ContactsTableProps) {
  const companyName = buildCompanyNameMap(companies)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Contacts</h1>
          <p className="text-sm text-muted-foreground">
            Recruiters, hiring managers, and referrals in your network.
          </p>
        </div>
        <ContactForm
          companies={companies}
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New contact
            </Button>
          }
        />
      </div>

      {contacts.length === 0 ? (
        <EmptyContacts companies={companies} />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Email</TableHead>
                <TableHead className="w-[96px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {contacts.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  companies={companies}
                  companyName={
                    contact.company_id ? (companyName.get(contact.company_id) ?? "—") : "—"
                  }
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function EmptyContacts({ companies }: { companies: Company[] }) {
  return (
    <EmptyState
      icon={Users}
      title="No contacts yet"
      description="Add the people you meet during your search."
      action={
        <ContactForm
          companies={companies}
          trigger={
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              New contact
            </Button>
          }
        />
      }
    />
  )
}

function ContactRow({
  contact,
  companies,
  companyName,
}: {
  contact: Contact
  companies: Company[]
  companyName: string
}) {
  const [isPending, startTransition] = useTransition()

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteContact(contact.id)
      if (result.ok) {
        toast.success("Contact deleted")
      } else {
        toast.error(result.error ?? "Failed to delete contact")
      }
    })
  }

  return (
    <TableRow>
      <TableCell className="font-medium">{contact.name}</TableCell>
      <TableCell>{companyName}</TableCell>
      <TableCell>
        <RoleBadge role={contact.role} />
      </TableCell>
      <TableCell>{contact.email ?? "—"}</TableCell>
      <TableCell>
        <div className="flex items-center justify-end gap-1">
          <ContactForm
            companies={companies}
            contact={contact}
            trigger={
              <Button variant="ghost" size="icon">
                <Pencil className="h-4 w-4" />
                <span className="sr-only">Edit {contact.name}</span>
              </Button>
            }
          />
          <Button variant="ghost" size="icon" onClick={handleDelete} disabled={isPending}>
            <Trash2 className="h-4 w-4" />
            <span className="sr-only">Delete {contact.name}</span>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

function RoleBadge({ role }: { role: ContactRole | null }) {
  if (!role) return <Badge variant="outline">—</Badge>
  const label = role
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
  return <Badge variant="secondary">{label}</Badge>
}

function buildCompanyNameMap(companies: Company[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const company of companies) {
    map.set(company.id, company.name)
  }
  return map
}
