"use client"

import Link from "next/link"
import { ClipboardList, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

/**
 * The global create menu. New Application is the dominant action — it owns a
 * dedicated, always-enabled button (companies are auto-created inline, so there
 * is no longer a "create a company first" prerequisite). Secondary, rarer
 * records live behind the dropdown.
 */
export function NewMenu() {
  return (
    <div className="flex items-center gap-2">
      <Button size="sm" asChild>
        <Link href="/applications">
          <Plus className="mr-1 h-4 w-4" />
          New application
        </Link>
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline" aria-label="Add something else">
            <Plus className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-52">
          <DropdownMenuLabel>Add…</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/companies">
              <ClipboardList className="mr-2 h-4 w-4" />
              Company
              <span className="ml-auto text-xs text-muted-foreground">optional</span>
            </Link>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
