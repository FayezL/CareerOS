"use server"

/**
 * Global search server action. Queries applications, companies, and contacts in
 * parallel through their existing `?q=` filters and returns grouped results.
 * Lives behind a "use server" boundary because the shared api-client is
 * server-only (Clerk auth).
 */

import { apiFetch } from "@/services/api-client"
import type { Application, Company, Contact, PageOut } from "@/types"

export type SearchResults = {
  applications: Application[]
  companies: Company[]
  contacts: Contact[]
  total: number
}

function unwrap<T>(data: PageOut<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.items
}

export async function globalSearch(query: string): Promise<SearchResults> {
  const q = query.trim()
  if (q.length < 1) {
    return { applications: [], companies: [], contacts: [], total: 0 }
  }
  const qs = `?q=${encodeURIComponent(q)}&limit=5`
  const settled = await Promise.allSettled([
    apiFetch<PageOut<Application> | Application[]>(`/applications${qs}`),
    apiFetch<PageOut<Company> | Company[]>(`/companies${qs}`),
    apiFetch<PageOut<Contact> | Contact[]>(`/contacts${qs}`),
  ])
  const applications = settled[0].status === "fulfilled" ? unwrap(settled[0].value) : []
  const companies = settled[1].status === "fulfilled" ? unwrap(settled[1].value) : []
  const contacts = settled[2].status === "fulfilled" ? unwrap(settled[2].value) : []
  return {
    applications,
    companies,
    contacts,
    total: applications.length + companies.length + contacts.length,
  }
}
