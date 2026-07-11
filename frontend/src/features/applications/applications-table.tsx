"use client"

import { useTransition } from "react"
import { ClipboardList, Pencil, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import type { Application, ApplicationStatus, Company } from "@/types"
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

import { ApplicationForm } from "./application-form"
import { deleteApplication } from "./actions"

type ApplicationsTableProps = {
  applications: Application[]
  companies: Company[]
}

export function ApplicationsTable({ applications, companies }: ApplicationsTableProps) {
  const companyName = buildCompanyNameMap(companies)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Applications</h1>
          <p className="text-sm text-muted-foreground">
            Every role you&apos;re pursuing, in one place.
          </p>
        </div>
        <ApplicationForm
          companies={companies}
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New application
            </Button>
          }
        />
      </div>

      {applications.length === 0 ? (
        <EmptyApplications companies={companies} />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Role</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Applied</TableHead>
                <TableHead className="w-[96px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {applications.map((application) => (
                <ApplicationRow
                  key={application.id}
                  application={application}
                  companies={companies}
                  companyName={companyName.get(application.company_id) ?? "Unknown"}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function EmptyApplications({ companies }: { companies: Company[] }) {
  return (
    <EmptyState
      icon={ClipboardList}
      title="No applications yet"
      description="Track your first role to start building your pipeline."
      action={
        <ApplicationForm
          companies={companies}
          trigger={
            <Button variant="outline" disabled={companies.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              New application
            </Button>
          }
        />
      }
    />
  )
}

function ApplicationRow({
  application,
  companies,
  companyName,
}: {
  application: Application
  companies: Company[]
  companyName: string
}) {
  const [isPending, startTransition] = useTransition()

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteApplication(application.id)
      if (result.ok) {
        toast.success("Application deleted")
      } else {
        toast.error(result.error ?? "Failed to delete application")
      }
    })
  }

  return (
    <TableRow>
      <TableCell className="font-medium">{application.role_title}</TableCell>
      <TableCell>{companyName}</TableCell>
      <TableCell>
        <StatusBadge status={application.status} />
      </TableCell>
      <TableCell>{formatDate(application.applied_at)}</TableCell>
      <TableCell>
        <div className="flex items-center justify-end gap-1">
          <ApplicationForm
            companies={companies}
            application={application}
            trigger={
              <Button variant="ghost" size="icon">
                <Pencil className="h-4 w-4" />
                <span className="sr-only">Edit {application.role_title}</span>
              </Button>
            }
          />
          <Button variant="ghost" size="icon" onClick={handleDelete} disabled={isPending}>
            <Trash2 className="h-4 w-4" />
            <span className="sr-only">Delete {application.role_title}</span>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

function StatusBadge({ status }: { status: ApplicationStatus }) {
  switch (status) {
    case "active":
      return <Badge>Active</Badge>
    case "accepted":
      return (
        <Badge className="border-green-500/30 bg-green-500/10 text-green-700 dark:border-green-400/30 dark:text-green-400">
          Accepted
        </Badge>
      )
    case "rejected":
      return <Badge variant="destructive">Rejected</Badge>
    case "archived":
      return <Badge variant="outline">Archived</Badge>
  }
}

function buildCompanyNameMap(companies: Company[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const company of companies) {
    map.set(company.id, company.name)
  }
  return map
}

function formatDate(value: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}
