"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Plus, Tag as TagIcon, X } from "lucide-react"

import { listTagsAction } from "@/services/tag-actions"
import type { Tag } from "@/types"
import { cn } from "@/utils/cn"
import { Input } from "@/components/ui/input"

type TagInputProps = {
  /** Initial tag names (edit mode — pre-fills the chips). */
  defaultTags?: string[]
}

/**
 * Multi-select tag picker for the application form.
 *
 * - Loads the user's tag library on mount so the picker has useful defaults.
 * - Type → filters the library by case-insensitive substring.
 * - Enter / comma / click adds the typed tag (reusing an existing name
 *   case-insensitively, or creating a new one).
 * - Each chip is removable.
 * - Emits one ``<input type="hidden" name="tags">`` per selected tag, so the
 *   FormData-based server action picks them up without any prop threading.
 */
export function TagInput({ defaultTags = [] }: TagInputProps) {
  const [library, setLibrary] = useState<Tag[]>([])
  const [selected, setSelected] = useState<string[]>(defaultTags)
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listTagsAction()
      .then(setLibrary)
      .catch(() => {
        /* empty picker is fine */
      })
  }, [])

  // Close on outside click.
  useEffect(() => {
    function onPointerDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onPointerDown)
    return () => document.removeEventListener("mousedown", onPointerDown)
  }, [])

  const queryClean = query.trim()
  const lowerSelected = useMemo(() => selected.map((s) => s.toLowerCase()), [selected])

  // Suggestions: from the library, not already picked, matching the query.
  const suggestions = useMemo(() => {
    const filtered = library.filter(
      (t) =>
        !lowerSelected.includes(t.name.toLowerCase()) &&
        (!queryClean || t.name.toLowerCase().includes(queryClean.toLowerCase())),
    )
    // If the typed text isn't an exact match (case-insensitive) in the library,
    // offer a "create" row at the end.
    const exactExists = library.some((t) => t.name.toLowerCase() === queryClean.toLowerCase())
    return { filtered, createOption: queryClean && !exactExists ? queryClean : null }
  }, [library, lowerSelected, queryClean])

  const options = useMemo(
    () => [
      ...suggestions.filtered.map((t) => ({ kind: "existing" as const, name: t.name })),
      ...(suggestions.createOption
        ? [{ kind: "new" as const, name: suggestions.createOption }]
        : []),
    ],
    [suggestions],
  )

  function add(name: string) {
    const cleaned = name.trim()
    if (!cleaned) return
    if (lowerSelected.includes(cleaned.toLowerCase())) {
      setQuery("")
      setOpen(false)
      return
    }
    // Reuse the library's casing if a case-insensitive match exists.
    const match = library.find((t) => t.name.toLowerCase() === cleaned.toLowerCase())
    setSelected((s) => [...s, match?.name ?? cleaned])
    setQuery("")
    setOpen(false)
  }

  function remove(name: string) {
    setSelected((s) => s.filter((t) => t !== name))
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && query === "" && selected.length > 0) {
      remove(selected[selected.length - 1])
    } else if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      const target = queryClean ? options[Math.min(active, options.length - 1)] : undefined
      if (target) add(target.name)
      else if (queryClean) add(queryClean)
    } else if (open && options.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setActive((i) => (i + 1) % options.length)
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setActive((i) => (i - 1 + options.length) % options.length)
      } else if (e.key === "Escape") {
        e.preventDefault()
        setOpen(false)
      }
    }
  }

  return (
    <div ref={containerRef} className="space-y-2">
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((name) => (
            <span
              key={name}
              className="inline-flex items-center gap-1 rounded-md bg-secondary pl-2 pr-1 py-0.5 text-xs font-medium text-secondary-foreground"
            >
              <TagIcon className="size-3" />
              {name}
              <button
                type="button"
                onClick={() => remove(name)}
                className="ml-0.5 rounded-sm p-0.5 hover:bg-background/60"
                aria-label={`Remove ${name}`}
              >
                <X className="size-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="relative">
        <Input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
            setActive(0)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={selected.length === 0 ? "Add tags (Remote, Visa, Python…)" : "Add another…"}
        />
        {open && (options.length > 0 || queryClean) && (
          <div className="absolute left-0 right-0 top-full z-50 mt-1 max-h-60 overflow-y-auto rounded-md border bg-popover p-1 shadow-md">
            {options.length === 0 ? (
              <p className="px-3 py-2 text-sm text-muted-foreground">
                Press Enter to create &ldquo;{queryClean}&rdquo;.
              </p>
            ) : (
              options.map((opt, i) => (
                <button
                  key={`${opt.kind}:${opt.name}`}
                  type="button"
                  onMouseEnter={() => setActive(i)}
                  onClick={() => add(opt.name)}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-sm px-3 py-1.5 text-left text-sm outline-none transition-colors",
                    i === active ? "bg-accent text-accent-foreground" : "",
                  )}
                >
                  {opt.kind === "new" ? (
                    <>
                      <Plus className="size-3.5 text-primary" />
                      Create <span className="font-medium">&ldquo;{opt.name}&rdquo;</span>
                    </>
                  ) : (
                    <>
                      <TagIcon className="size-3.5 text-muted-foreground" />
                      {opt.name}
                    </>
                  )}
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Hidden inputs — one per selected tag (FormData collects them as an array). */}
      {selected.map((name) => (
        <input key={name} type="hidden" name="tags" value={name} readOnly />
      ))}
    </div>
  )
}
