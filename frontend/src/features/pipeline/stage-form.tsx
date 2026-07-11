"use client"

import { useActionState, useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import { toast } from "sonner"

import type { PipelineStage } from "@/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import { createStage, updateStage, type ActionResult } from "./actions"

const STAGE_COLORS = [
  "#94a3b8",
  "#60a5fa",
  "#a78bfa",
  "#34d399",
  "#fbbf24",
  "#f87171",
  "#22c55e",
  "#f59e0b",
]

type StageFormProps = {
  stage?: PipelineStage
  trigger?: ReactNode
  /** Controlled open state (used when launched from a menu item). */
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

/**
 * Create/rename dialog for a pipeline stage. When `trigger` is provided the
 * dialog opens from that element; otherwise it is controlled via `open` /
 * `onOpenChange` (e.g. launched from a dropdown menu item). The inner form
 * (with its `useActionState`) lives inside `DialogContent`, which Radix only
 * mounts while open — so each open begins with a fresh action state and
 * prefilled defaults.
 */
export function StageForm({ stage, trigger, open, onOpenChange }: StageFormProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen
  const noop = useCallback(() => {}, [])
  const setOpen = useMemo(
    () => (isControlled ? (onOpenChange ?? noop) : setInternalOpen),
    [isControlled, onOpenChange, noop],
  )
  const close = useCallback(() => setOpen(false), [setOpen])

  return (
    <Dialog open={isOpen} onOpenChange={setOpen}>
      {trigger ? <DialogTrigger asChild>{trigger}</DialogTrigger> : null}
      <DialogContent>
        <StageFormFields stage={stage} onClose={close} />
      </DialogContent>
    </Dialog>
  )
}

type StageFormFieldsProps = {
  stage?: PipelineStage
  onClose: () => void
}

function StageFormFields({ stage, onClose }: StageFormFieldsProps) {
  const [state, formAction, isPending] = useActionState<ActionResult, FormData>(
    async (_prevState, formData) => {
      const fn = stage ? updateStage.bind(null, stage.id) : createStage
      return fn(formData)
    },
    { ok: false },
  )

  useEffect(() => {
    if (state.ok) {
      toast.success(stage ? "Stage updated" : "Stage created")
      onClose()
    } else if (state.error) {
      toast.error(state.error)
    }
  }, [state, stage, onClose])

  const defaultColor = stage?.color ?? STAGE_COLORS[0]

  return (
    <>
      <DialogHeader>
        <DialogTitle>{stage ? "Rename stage" : "New stage"}</DialogTitle>
        <DialogDescription>
          {stage ? "Update this pipeline stage." : "Add a column to your pipeline."}
        </DialogDescription>
      </DialogHeader>

      <form action={formAction} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            name="name"
            required
            placeholder="e.g. Phone screen"
            defaultValue={stage?.name ?? ""}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="color">Color</Label>
          <div className="flex flex-wrap items-center gap-2">
            {STAGE_COLORS.map((color) => (
              <label key={color} className="cursor-pointer">
                <input
                  type="radio"
                  name="color"
                  value={color}
                  defaultChecked={color === defaultColor}
                  className="peer sr-only"
                />
                <span
                  className="block h-7 w-7 rounded-full ring-offset-2 ring-offset-background peer-checked:ring-2 peer-checked:ring-ring"
                  style={{ backgroundColor: color }}
                />
              </label>
            ))}
            <Input
              id="color"
              name="color"
              type="color"
              defaultValue={defaultColor}
              className="h-7 w-12 cursor-pointer border-0 bg-transparent p-0"
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving…" : "Save stage"}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}
