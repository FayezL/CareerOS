"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  BarChart3,
  Bell,
  Building2,
  CalendarClock,
  ClipboardList,
  Home,
  KanbanSquare,
  Settings,
  Sparkles,
  Users,
} from "lucide-react"

import { cn } from "@/utils/cn"

type NavItem = {
  label: string
  href: string
  icon: typeof Building2
}

type NavSection = {
  label: string
  items: NavItem[]
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: "Main",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: Home },
      { label: "Applications", href: "/applications", icon: ClipboardList },
      { label: "Pipeline", href: "/pipeline", icon: KanbanSquare },
      { label: "Companies", href: "/companies", icon: Building2 },
      { label: "Contacts", href: "/contacts", icon: Users },
      { label: "Interviews", href: "/interviews", icon: CalendarClock },
    ],
  },
  {
    label: "Insights",
    items: [
      { label: "Analytics", href: "/analytics", icon: BarChart3 },
      { label: "Reminders", href: "/reminders", icon: Bell },
      { label: "AI Tools", href: "/ai", icon: Sparkles },
    ],
  },
]

const SETTINGS_ITEM: NavItem = {
  label: "Settings",
  href: "/settings/billing",
  icon: Settings,
}

function isActivePath(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function Sidebar() {
  const pathname = usePathname()

  return (
    <nav aria-label="Primary" className="flex flex-col gap-1">
      {NAV_SECTIONS.map((section) => (
        <div key={section.label} className="space-y-1">
          <p className="px-3 pb-1 pt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {section.label}
          </p>
          {section.items.map((item) => (
            <NavLink key={item.href} item={item} active={isActivePath(pathname, item.href)} />
          ))}
        </div>
      ))}

      <div className="mt-4 border-t pt-2">
        <NavLink item={SETTINGS_ITEM} active={isActivePath(pathname, SETTINGS_ITEM.href)} />
      </div>
    </nav>
  )
}

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon
  return (
    <Link
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
}
