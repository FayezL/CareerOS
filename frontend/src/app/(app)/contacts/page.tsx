import type { Metadata } from "next"
import { AlertCircle } from "lucide-react"

import { listCompanies, listContacts } from "@/lib/api-client"
import type { Company, Contact } from "@/lib/types"
import { ContactsTable } from "@/features/contacts/contacts-table"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Contacts · CareerOS",
}

export default async function ContactsPage() {
  let contacts: Contact[] = []
  let companies: Company[] = []
  let errorMessage: string | null = null

  try {
    contacts = await listContacts()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Unable to load contacts right now."
  }

  try {
    companies = await listCompanies()
  } catch {
    // Non-fatal: the table still renders; the create/edit form shows an empty
    // company list.
  }

  if (errorMessage) {
    return (
      <div className="mx-auto mt-12 w-full max-w-md rounded-lg border border-border bg-card p-6 text-card-foreground shadow-sm">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <h2 className="text-lg font-semibold">Couldn&apos;t load contacts</h2>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
      </div>
    )
  }

  return <ContactsTable contacts={contacts} companies={companies} />
}
