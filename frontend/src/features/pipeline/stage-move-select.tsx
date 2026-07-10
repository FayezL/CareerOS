"use client"

import { useTransition } from "react"
import { toast } from "sonner"

import type { PipelineStage } from "@/lib/types"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { moveApplication } from "./actions"

type StageMoveSelectProps = {
  applicationId: string
  stages: PipelineStage[]
  currentStageId: string | null | undefined
}

/** Select control that moves an application between pipeline stages. */
export function StageMoveSelect({ applicationId, stages, currentStageId }: StageMoveSelectProps) {
  const [isPending, startTransition] = useTransition()

  function handleChange(toStageId: string) {
    if (toStageId === currentStageId) return
    startTransition(async () => {
      const result = await moveApplication(applicationId, toStageId)
      if (result.ok) {
        toast.success("Application moved")
      } else {
        toast.error(result.error ?? "Failed to move application")
      }
    })
  }

  if (stages.length === 0) {
    return (
      <Select disabled>
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="No stages" />
        </SelectTrigger>
      </Select>
    )
  }

  return (
    <Select
      defaultValue={currentStageId ?? undefined}
      onValueChange={handleChange}
      disabled={isPending}
    >
      <SelectTrigger className="w-[220px]">
        <SelectValue placeholder="Select a stage" />
      </SelectTrigger>
      <SelectContent>
        {stages.map((stage) => (
          <SelectItem key={stage.id} value={stage.id}>
            <span className="flex items-center gap-2">
              <span
                aria-hidden
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: stage.color ?? "#94a3b8" }}
              />
              {stage.name}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
