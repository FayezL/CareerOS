"use server"

import { revalidatePath } from "next/cache"

import { apiFetch } from "@/lib/api-client"
import type {
  CoverLetterRequest,
  GenerationResponse,
  InterviewPrepRequest,
  TailorResumeRequest,
} from "@/lib/types"

/** Result of an AI generation action — `result` holds the generated text. */
export type AIActionResult = { ok: boolean; result?: string; error?: string }

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

/** POST to an AI generation endpoint and unwrap the returned `text` field. */
async function generate(
  path: string,
  payload: TailorResumeRequest | CoverLetterRequest | InterviewPrepRequest,
): Promise<AIActionResult> {
  try {
    const data = await apiFetch<GenerationResponse>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return { ok: true, result: data.text }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

/** Tailor a resume to a job description (`POST /ai/tailor-resume`). */
export async function tailorResume(input: TailorResumeRequest): Promise<AIActionResult> {
  const result = await generate("/ai/tailor-resume", input)
  revalidatePath("/ai")
  return result
}

/** Draft a cover letter for a company and role (`POST /ai/cover-letter`). */
export async function generateCoverLetter(input: CoverLetterRequest): Promise<AIActionResult> {
  const result = await generate("/ai/cover-letter", input)
  revalidatePath("/ai")
  return result
}

/** Generate interview-prep questions for a role (`POST /ai/interview-prep`). */
export async function interviewPrep(input: InterviewPrepRequest): Promise<AIActionResult> {
  const result = await generate("/ai/interview-prep", input)
  revalidatePath("/ai")
  return result
}
