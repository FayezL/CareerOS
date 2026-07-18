"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Briefcase, ClipboardList, Search, User } from "lucide-react"

import { globalSearch, type SearchResults } from "@/services/search-actions"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { cn } from "@/utils/cn"

type ResultItem = {
  id: string
  label: string
  sub: string | null
  href: string
  icon: typeof Briefcase
  group: string
}

const EMPTY: SearchResults = { applications: [], companies: [], contacts: [], total: 0 }

/**
 * Global Cmd/Ctrl+K command palette. Searches applications, companies, and
 * contacts in parallel and navigates to the chosen record. Mounted once in the
 * authenticated layout so it's available on every page.
 */
export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResults>(EMPTY)
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState(0)
  const router = useRouter()
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null)

  // Global hotkey: Cmd/Ctrl+K to open, Esc handled by Dialog.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [])

  // Debounced search whenever the palette is open.
  useEffect(() => {
    if (!open) {
      setQuery("")
      setResults(EMPTY)
      setActive(0)
      return
    }
    const q = query.trim()
    if (!q) {
      setResults(EMPTY)
      return
    }
    setLoading(true)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        setResults(await globalSearch(q))
        setActive(0)
      } catch {
        setResults(EMPTY)
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, open])

  const items = useMemo<ResultItem[]>(() => {
    const out: ResultItem[] = []
    for (const a of results.applications) {
      out.push({
        id: `app:${a.id}`,
        label: a.role_title,
        sub: a.company?.name ?? null,
        href: `/applications/${a.id}`,
        icon: ClipboardList,
        group: "Applications",
      })
    }
    for (const c of results.companies) {
      out.push({
        id: `co:${c.id}`,
        label: c.name,
        sub: [c.industry, c.location].filter(Boolean).join(" · ") || null,
        href: `/companies/${c.id}`,
        icon: Briefcase,
        group: "Companies",
      })
    }
    for (const c of results.contacts) {
      out.push({
        id: `contact:${c.id}`,
        label: c.name,
        sub: c.role ?? c.email ?? null,
        href: `/contacts`,
        icon: User,
        group: "Contacts",
      })
    }
    return out
  }, [results])

  function choose(item: ResultItem) {
    setOpen(false)
    router.push(item.href)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (items.length === 0) return
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActive((i) => (i + 1) % items.length)
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActive((i) => (i - 1 + items.length) % items.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      const item = items[active]
      if (item) choose(item)
    }
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="w-60 justify-start px-3 text-muted-foreground"
        onClick={() => setOpen(true)}
      >
        <Search className="mr-2 size-4" />
        <span className="flex-1 text-left">Search…</span>
        <kbd className="ml-2 rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium">⌘K</kbd>
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-[560px]">
          <DialogHeader className="sr-only">
            <DialogTitle>Search</DialogTitle>
            <DialogDescription>Find applications, companies, and contacts.</DialogDescription>
          </DialogHeader>
          <div className="flex items-center border-b px-3">
            <Search className="size-4 shrink-0 text-muted-foreground" />
            <Input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Search applications, companies, contacts…"
              className="border-0 focus-visible:ring-0"
            />
          </div>
          <div className="max-h-80 overflow-y-auto p-2">
            {loading ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">Searching…</p>
            ) : items.length === 0 ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                {query.trim() ? "No matches." : "Start typing to search across everything."}
              </p>
            ) : (
              items.map((item, i) => {
                const Icon = item.icon
                const showGroupHeader = i === 0 || items[i - 1].group !== item.group
                return (
                  <div key={item.id}>
                    {showGroupHeader && (
                      <p className="px-2 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                        {item.group}
                      </p>
                    )}
                    <button
                      type="button"
                      onMouseEnter={() => setActive(i)}
                      onClick={() => choose(item)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-left text-sm outline-none transition-colors",
                        i === active ? "bg-accent text-accent-foreground" : "",
                      )}
                    >
                      <Icon className="size-4 shrink-0 text-muted-foreground" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{item.label}</span>
                        {item.sub && (
                          <span className="block truncate text-xs text-muted-foreground">
                            {item.sub}
                          </span>
                        )}
                      </span>
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
