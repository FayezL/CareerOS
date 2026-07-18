"use server"

/**
 * Server actions callable from Client Components that need to read from the
 * backend. The shared `api-client` is server-only (it uses Clerk's server
 * `auth()` to forward the session JWT), so Client Components cannot import it
 * directly — they go through these actions instead.
 */

import { searchCompanies as searchCompaniesApi } from "@/services/api-client"
import type { CompanyOption } from "@/types"

/** Prefix-match company autocomplete for the company combobox. */
export async function searchCompaniesAction(query: string): Promise<CompanyOption[]> {
  return searchCompaniesApi(query)
}
