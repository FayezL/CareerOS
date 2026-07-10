"use client"

import { useEffect, useMemo, useState, useTransition } from "react"
import Link from "next/link"
import {
  closestCorners,
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core"
import { KanbanSquare, MoreVertical, Pencil, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import type { Application, Company, PipelineStage } from "@/lib/types"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

import { StageForm } from "./stage-form"
import { deleteStage, moveApplication } from "./actions"

type KanbanBoardProps = {
  stages: PipelineStage[]
  applications: Application[]
  companies: Company[]
}

export function KanbanBoard({ stages, applications, companies }: KanbanBoardProps) {
  const companyName = useMemo(() => buildCompanyNameMap(companies), [companies])

  if (stages.length === 0) {
    return <EmptyStages />
  }

  if (applications.length === 0) {
    return <EmptyApplications />
  }

  return <Board stages={stages} applications={applications} companyName={companyName} />
}

function Board({
  stages,
  applications,
  companyName,
}: {
  stages: PipelineStage[]
  applications: Application[]
  companyName: Map<string, string>
}) {
  const [apps, setApps] = useState<Application[]>(applications)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [, startTransition] = useTransition()

  // Re-sync from server data whenever the parent re-renders with fresh props
  // (e.g. after a server action revalidates the route).
  useEffect(() => {
    setApps(applications)
  }, [applications])

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const grouped = useMemo(() => groupByStage(apps), [apps])
  const activeCard = activeId ? (apps.find((a) => a.id === activeId) ?? null) : null

  function handleDragStart(event: DragStartEvent) {
    setActiveId(String(event.active.id))
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveId(null)
    const { active, over } = event
    if (!over) return

    const applicationId = String(active.id)
    const toStageId = String(over.id)
    const app = apps.find((a) => a.id === applicationId)
    if (!app) return

    const fromStageId = app.stage_id ?? null
    if (toStageId === fromStageId) return

    // Optimistic: move the card immediately, revert on failure.
    setApps((prev) => prev.map((a) => (a.id === applicationId ? { ...a, stage_id: toStageId } : a)))
    startTransition(async () => {
      const result = await moveApplication(applicationId, toStageId)
      if (!result.ok) {
        setApps((prev) =>
          prev.map((a) => (a.id === applicationId ? { ...a, stage_id: fromStageId } : a)),
        )
        toast.error(result.error ?? "Failed to move application")
      }
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
          <p className="text-sm text-muted-foreground">
            Drag cards across stages to update your funnel.
          </p>
        </div>
        <StageForm
          trigger={
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              Add stage
            </Button>
          }
        />
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={() => setActiveId(null)}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => (
            <KanbanColumn
              key={stage.id}
              stage={stage}
              applications={grouped.get(stage.id) ?? []}
              companyName={companyName}
            />
          ))}
        </div>

        <DragOverlay>
          {activeCard ? (
            <CardPreview
              application={activeCard}
              companyName={companyName.get(activeCard.company_id) ?? "Unknown"}
            />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}

function KanbanColumn({
  stage,
  applications,
  companyName,
}: {
  stage: PipelineStage
  applications: Application[]
  companyName: Map<string, string>
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id })

  return (
    <div className="flex w-72 shrink-0 flex-col">
      <div className="mb-2 flex items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: stage.color ?? "#94a3b8" }}
          />
          <h2 className="text-sm font-semibold">{stage.name}</h2>
          <span className="font-mono text-xs tabular-nums text-muted-foreground">
            {applications.length}
          </span>
        </div>
        <ColumnMenu stage={stage} />
      </div>

      <div
        ref={setNodeRef}
        className={cn(
          "flex min-h-[120px] flex-1 flex-col gap-2 rounded-lg border bg-muted/30 p-2 transition-colors",
          isOver && "border-primary/50 bg-accent/40",
        )}
      >
        {applications.length === 0 ? (
          <p className="px-1 py-2 text-xs text-muted-foreground">No applications</p>
        ) : (
          applications.map((application) => (
            <KanbanCard
              key={application.id}
              application={application}
              companyName={companyName.get(application.company_id) ?? "Unknown"}
            />
          ))
        )}
      </div>
    </div>
  )
}

function KanbanCard({
  application,
  companyName,
}: {
  application: Application
  companyName: string
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: application.id,
  })

  return (
    <Link
      ref={setNodeRef}
      href={`/applications/${application.id}`}
      {...attributes}
      {...listeners}
      className={cn(
        "block cursor-grab rounded-md border bg-card p-3 text-card-foreground shadow-sm transition-colors hover:border-primary/40 active:cursor-grabbing",
        isDragging && "opacity-40",
      )}
    >
      <p className="text-sm font-medium leading-tight">{application.role_title}</p>
      <p className="mt-1 text-xs text-muted-foreground">{companyName}</p>
      <div className="mt-2">
        <StatusBadge status={application.status} />
      </div>
    </Link>
  )
}

function CardPreview({
  application,
  companyName,
}: {
  application: Application
  companyName: string
}) {
  return (
    <div className="w-64 cursor-grabbing rounded-md border bg-card p-3 text-card-foreground shadow-lg">
      <p className="text-sm font-medium leading-tight">{application.role_title}</p>
      <p className="mt-1 text-xs text-muted-foreground">{companyName}</p>
      <div className="mt-2">
        <StatusBadge status={application.status} />
      </div>
    </div>
  )
}

function ColumnMenu({ stage }: { stage: PipelineStage }) {
  const [isPending, startTransition] = useTransition()
  const [renameOpen, setRenameOpen] = useState(false)

  function handleDelete() {
    startTransition(async () => {
      const result = await deleteStage(stage.id)
      if (result.ok) {
        toast.success("Stage deleted")
      } else {
        toast.error(result.error ?? "Couldn't delete this stage — move its applications first.")
      }
    })
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            disabled={isPending}
            aria-label={`Stage ${stage.name} options`}
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => setRenameOpen(true)}>
            <Pencil className="h-4 w-4" />
            Rename
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={handleDelete}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <StageForm stage={stage} open={renameOpen} onOpenChange={setRenameOpen} />
    </>
  )
}

function EmptyStages() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
        <p className="text-sm text-muted-foreground">
          Drag cards across stages to update your funnel.
        </p>
      </div>
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-12 text-center">
        <div className="rounded-full bg-muted p-3">
          <KanbanSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="font-medium">No pipeline stages yet</p>
          <p className="text-sm text-muted-foreground">
            Add your first stage to start building your board.
          </p>
        </div>
        <StageForm
          trigger={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add stage
            </Button>
          }
        />
      </div>
    </div>
  )
}

function EmptyApplications() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pipeline</h1>
          <p className="text-sm text-muted-foreground">
            Drag cards across stages to update your funnel.
          </p>
        </div>
        <StageForm
          trigger={
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              Add stage
            </Button>
          }
        />
      </div>
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-12 text-center">
        <div className="rounded-full bg-muted p-3">
          <KanbanSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <p className="font-medium">No applications yet</p>
          <p className="text-sm text-muted-foreground">
            Add your first application to start tracking your search.
          </p>
        </div>
        <Button asChild>
          <Link href="/applications">
            <Plus className="mr-2 h-4 w-4" />
            New application
          </Link>
        </Button>
      </div>
    </div>
  )
}

function buildCompanyNameMap(companies: Company[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const company of companies) {
    map.set(company.id, company.name)
  }
  return map
}

function groupByStage(applications: Application[]): Map<string, Application[]> {
  const map = new Map<string, Application[]>()
  for (const application of applications) {
    const stageId = application.stage_id
    if (!stageId) continue
    const list = map.get(stageId)
    if (list) {
      list.push(application)
    } else {
      map.set(stageId, [application])
    }
  }
  return map
}
