"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Building2, Check, Plus, Search } from "lucide-react"

import { searchCompaniesAction } from "@/services/company-actions"
import type { CompanyOption } from "@/types"
import { cn } from "@/utils/cn"
import { Input } from "@/components/ui/input"

/**
 * The resolved company selection — either an existing company id or a free-text
 * name to be auto-created on submit. Matches the backend's ApplicationCreate
 * contract (company_id XOR company_name).
 */
export type CompanySelection =
  { mode: "existing"; id: string; name: string } | { mode: "new"; name: string }

export function CompanyCombobox({
  defaultCompany,
  required = true,
}: {
  defaultCompany?: { id: string; name: string }
  required?: boolean
}) {
  const [query, setQuery] = useState(defaultCompany?.name ?? "")
  const [results, setResults] = useState<CompanyOption[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState(0)
  const [selection, setSelection] = useState<CompanySelection | null>(
    defaultCompany ? { mode: "existing", id: defaultCompany.id, name: defaultCompany.name } : null,
  )

  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null)

  // Close on outside click.
  useEffect(() => {
    function onPointerDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onPointerDown)
    return () => document.removeEventListener("mousedown", onPointerDown)
  }, [])

  // Debounced autocomplete search.
  useEffect(() => {
    const q = query.trim()
    // Keep the existing selection if the input still matches it exactly.
    if (selection && selection.name.toLowerCase() === q.toLowerCase()) {
      setResults([])
      setOpen(false)
      return
    }
    if (q.length === 0) {
      setResults([])
      setOpen(false)
      return
    }
    setLoading(true)
    setOpen(true)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const rows = await searchCompaniesAction(q)
        setResults(rows)
        setActive(0)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, selection])

  const exactMatchExists = useMemo(
    () => results.some((r) => r.name.toLowerCase() === query.trim().toLowerCase()),
    [results, query],
  )

  // Build the option list: existing results, plus a "create" row when the typed
  // text isn't an exact match (so the user can always create a new company).
  const options: Array<
    { kind: "existing"; company: CompanyOption } | { kind: "new"; name: string }
  > = useMemo(() => {
    const list: Array<
      { kind: "existing"; company: CompanyOption } | { kind: "new"; name: string }
    > = results.map((company) => ({ kind: "existing" as const, company }))
    if (query.trim() && !exactMatchExists) {
      list.push({ kind: "new", name: query.trim() })
    }
    return list
  }, [results, query, exactMatchExists])

  function choose(option: (typeof options)[number]) {
    if (option.kind === "existing") {
      setSelection({ mode: "existing", id: option.company.id, name: option.company.name })
      setQuery(option.company.name)
    } else {
      setSelection({ mode: "new", name: option.name })
      setQuery(option.name)
    }
    setOpen(false)
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || options.length === 0) {
      if (e.key === "ArrowDown" && query.trim()) setOpen(true)
      return
    }
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActive((i) => (i + 1) % options.length)
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActive((i) => (i - 1 + options.length) % options.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      const opt = options[active]
      if (opt) choose(opt)
    } else if (e.key === "Escape") {
      e.preventDefault()
      setOpen(false)
    }
  }

  const inputValid = selection !== null

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls="company-listbox"
          aria-autocomplete="list"
          autoComplete="off"
          value={query}
          required={required}
          onChange={(e) => {
            setQuery(e.target.value)
            // Typing invalidates the prior selection until a new pick is made.
            if (selection && selection.name !== e.target.value) setSelection(null)
          }}
          onFocus={() => query.trim() && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search or type a company name…"
          className={cn("pl-9", !inputValid && query.trim() && "border-amber-500/60")}
        />
      </div>

      {/* Hidden form fields — emits either company_id or company_name for FormData. */}
      {selection?.mode === "existing" ? (
        <input type="hidden" name="company_id" value={selection.id} />
      ) : selection?.mode === "new" ? (
        <input type="hidden" name="company_name" value={selection.name} />
      ) : null}

      {open && (query.trim() || loading) && (
        <div
          id="company-listbox"
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
        >
          {loading ? (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">Searching…</div>
          ) : options.length === 0 ? (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">No matches.</div>
          ) : (
            options.map((option, i) => {
              const isSelected =
                option.kind === "existing"
                  ? selection?.mode === "existing" && selection.id === option.company.id
                  : selection?.mode === "new" && selection.name === option.name
              return (
                <button
                  key={option.kind === "existing" ? option.company.id : `new:${option.name}`}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => choose(option)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-sm px-3 py-2 text-left text-sm outline-none transition-colors",
                    i === active ? "bg-accent text-accent-foreground" : "",
                  )}
                >
                  {option.kind === "existing" ? (
                    <>
                      <Building2 className="size-4 shrink-0 text-muted-foreground" />
                      <span className="flex-1">
                        <span className="font-medium">{option.company.name}</span>
                        {(option.company.industry || option.company.location) && (
                          <span className="ml-2 text-xs text-muted-foreground">
                            {[option.company.industry, option.company.location]
                              .filter(Boolean)
                              .join(" · ")}
                          </span>
                        )}
                      </span>
                    </>
                  ) : (
                    <>
                      <Plus className="size-4 shrink-0 text-primary" />
                      <span className="flex-1">
                        Create <span className="font-medium">“{option.name}”</span>
                      </span>
                    </>
                  )}
                  {isSelected && <Check className="size-4 shrink-0 text-primary" />}
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
