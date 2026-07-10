"use client"

import { useTransition } from "react"
import { Building2, Pencil, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import type { Company } from "@/lib/types"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { CompanyForm } from "./company-form"
import { deleteCompany } from "./actions"

type CompaniesTableProps = {
  companies: Company[]
}

export function CompaniesTable({ companies }: CompaniesTableProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Companies</h1>
          <p className="text-sm text-muted-foreground">
            Track the organizations you&apos;re engaging with.
          </p>
        </div>
        <CompanyForm
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New company
            </Button>
          }
        />
      </div>

      {companies.length === 0 ? (
        <EmptyCompanies />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Location</TableHead>
                <TableHead className="w-[96px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <CompanyRow key={company.id} company={company} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}

function EmptyCompanies() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-12 text-center">
      <div className="rounded-full bg-muted p-3">
        <Building2 className="h-6 w-6 text-muted-foreground" />
      </div>
      <div>
        <p className="font-medium">No companies yet</p>
        <p className="text-sm text-muted-foreground">Add your first company to get started.</p>
      </div>
      <CompanyForm
        trigger={
          <Button variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            New company
          </Button>
        }
      />
    </div>
  )
}

function CompanyRow({ company }: { company: Company }) {
  const [isPending, startTransition] = useTransition()

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteCompany(company.id)
      if (result.ok) {
        toast.success("Company deleted")
      } else {
        toast.error(result.error ?? "Failed to delete company")
      }
    })
  }

  return (
    <TableRow>
      <TableCell className="font-medium">{company.name}</TableCell>
      <TableCell>{company.industry ?? "—"}</TableCell>
      <TableCell>{company.size ?? "—"}</TableCell>
      <TableCell>{company.location ?? "—"}</TableCell>
      <TableCell>
        <div className="flex items-center justify-end gap-1">
          <CompanyForm
            company={company}
            trigger={
              <Button variant="ghost" size="icon">
                <Pencil className="h-4 w-4" />
                <span className="sr-only">Edit {company.name}</span>
              </Button>
            }
          />
          <Button variant="ghost" size="icon" onClick={handleDelete} disabled={isPending}>
            <Trash2 className="h-4 w-4" />
            <span className="sr-only">Delete {company.name}</span>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}
