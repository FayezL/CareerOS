"use server"

/**
 * Server actions callable from Client Components that need to read tags.
 * Mirrors the company-actions.ts pattern: the shared api-client is server-only
 * (Clerk auth), so Client Components go through these actions instead.
 */

import { listTags as listTagsApi } from "@/services/api-client"
import type { Tag } from "@/types"

/** Fetch the caller's tag library (seeds curated defaults on first access). */
export async function listTagsAction(): Promise<Tag[]> {
  return listTagsApi()
}
