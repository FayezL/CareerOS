import { Tag as TagIcon } from "lucide-react"

import type { TagRef } from "@/types"
import { cn } from "@/utils/cn"

type TagBadgesProps = {
  tags: TagRef[]
  className?: string
  /** Render size: compact for table rows, default for workspace/cards. */
  size?: "default" | "compact"
}

/**
 * Read-only tag chip row used in the application workspace, table rows, and
 * (later) analytics group-by labels. Colours are taken from the tag if set,
 * otherwise fall back to the muted secondary style.
 */
export function TagBadges({ tags, className, size = "default" }: TagBadgesProps) {
  if (tags.length === 0) return null
  return (
    <div className={cn("flex flex-wrap gap-1", className)}>
      {tags.map((tag) => {
        const style = tag.color ? { backgroundColor: hexToRgba(tag.color, 0.12) } : undefined
        return (
          <span
            key={tag.id}
            style={style}
            className={cn(
              "inline-flex items-center gap-1 rounded-md font-medium",
              size === "compact" ? "px-1.5 py-0 text-[11px]" : "bg-secondary px-2 py-0.5 text-xs",
              !tag.color && "bg-secondary text-secondary-foreground",
              tag.color && "text-foreground",
            )}
          >
            <TagIcon className={size === "compact" ? "size-2.5" : "size-3"} />
            {tag.name}
          </span>
        )
      })}
    </div>
  )
}

/** Hex (#rrggbb) → rgba string with the given alpha. Falls back gracefully. */
function hexToRgba(hex: string, alpha: number): string {
  const m = /^#([0-9a-f]{6})$/i.exec(hex.trim())
  if (!m) return ""
  const n = parseInt(m[1], 16)
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`
}
