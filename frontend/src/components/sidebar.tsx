"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Building2, ClipboardList, LayoutDashboard } from "lucide-react"

import { cn } from "@/lib/utils"

type NavItem = {
  label: string
  href: string
  icon: typeof Building2
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/applications", icon: LayoutDashboard },
  { label: "Applications", href: "/applications", icon: ClipboardList },
  { label: "Companies", href: "/companies", icon: Building2 },
]

function isActivePath(pathname: string, href: string): boolean {
  if (href === "/applications") {
    return pathname === "/applications"
  }
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function Sidebar() {
  const pathname = usePathname()

  // When two items share a route (Dashboard + Applications both point at
  // /applications), highlight the most specific label rather than both.
  const activeHref = NAV_ITEMS.map((item) => item.href)
    .filter((href) => isActivePath(pathname, href))
    .at(-1)

  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        const active = item.href === activeHref
        return (
          <Link
            key={item.label}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-secondary text-secondary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
