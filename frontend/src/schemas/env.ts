import { z } from "zod"

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url("NEXT_PUBLIC_API_URL must be a valid URL."),
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: z
    .string()
    .min(1, "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required."),
  CLERK_SECRET_KEY: z.string().min(1, "CLERK_SECRET_KEY is required.").optional(),
})

export type Env = z.infer<typeof envSchema>

let cached: Env | null = null

/**
 * Lazily parse and validate environment variables.
 *
 * Validation runs on first call (not at module import time), so that
 * `next build` can succeed without any environment variables set. This is
 * only invoked from async server functions.
 */
export function getEnv(): Env {
  if (cached) {
    return cached
  }
  const parsed = envSchema.parse(process.env)
  cached = parsed
  return cached
}
