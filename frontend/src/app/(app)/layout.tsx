import { Briefcase } from "lucide-react"

import { NewMenu } from "@/components/new-menu"
import { Sidebar } from "@/components/sidebar"
import { UserButton } from "@/lib/clerk"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <Briefcase className="h-5 w-5" />
          <span className="font-semibold">CareerOS</span>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <Sidebar />
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between gap-4 border-b px-4 sm:px-6">
          <span className="font-semibold md:hidden">CareerOS</span>
          <div className="ml-auto flex items-center gap-3">
            <NewMenu />
            <UserButton afterSignOutUrl="/" />
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6">
          <div className="mx-auto w-full max-w-5xl">{children}</div>
        </main>
      </div>
    </div>
  )
}
