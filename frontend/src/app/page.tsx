import Link from "next/link"
import { redirect } from "next/navigation"
import { ArrowRight, Sparkles } from "lucide-react"

import { auth } from "@/lib/clerk"
import { Button } from "@/components/ui/button"

export const dynamic = "force-dynamic"

export default async function Home() {
  const { userId } = await auth()
  if (userId) {
    redirect("/applications")
  }

  return (
    <main className="min-h-screen">
      <section className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-4 py-1.5 text-sm text-secondary-foreground">
          <Sparkles className="size-4" />
          Your operating system for career growth
        </div>
        <h1 className="text-balance text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
          Build the career you deserve.
        </h1>
        <p className="mt-6 max-w-xl text-pretty text-lg text-muted-foreground">
          Track applications, organize your network, and surface the opportunities that actually
          move you forward — all in one place.
        </p>
        <div className="mt-10 flex items-center gap-4">
          <Button asChild size="lg">
            <Link href="/sign-up">
              Get started
              <ArrowRight className="ml-2 size-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/sign-in">Sign in</Link>
          </Button>
        </div>
      </section>
    </main>
  )
}
