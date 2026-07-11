import type { Metadata } from "next"

import { listCompanies, listContacts } from "@/services/api-client"
import type { Company, Contact } from "@/types"
import { ErrorState } from "@/components/error-state"
import { ContactsTable } from "@/features/contacts/contacts-table"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Contacts",
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
    return <ErrorState title="Couldn't load contacts" description={errorMessage} />
  }

  return <ContactsTable contacts={contacts} companies={companies} />
}
