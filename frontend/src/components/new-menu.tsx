"use client"

import Link from "next/link"
import { Building2, ClipboardList, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function NewMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="sm">
          <Plus className="mr-1 h-4 w-4" />
          New
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link href="/applications">
            <ClipboardList className="mr-2 h-4 w-4" />
            Application
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/companies">
            <Building2 className="mr-2 h-4 w-4" />
            Company
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
