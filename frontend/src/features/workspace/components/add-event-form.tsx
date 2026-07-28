"use client"

import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { createTimelineEvent } from "../actions"
import type { TimelineEventType, TimelineImportance } from "@/types"

interface AddEventFormProps {
  applicationId: string
}

export function AddEventForm({ applicationId }: AddEventFormProps) {
  const [open, setOpen] = useState(false)
  const [eventType, setEventType] = useState<TimelineEventType>("NOTE")
  const [summary, setSummary] = useState("")
  const [note, setNote] = useState("")
  const [importance, setImportance] = useState<TimelineImportance>("NORMAL")
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsSubmitting(true)

    const formData = new FormData()
    formData.append("application_id", applicationId)
    formData.append("event_type", eventType)
    if (summary) formData.append("summary", summary)
    if (note) formData.append("note", note)
    if (importance) formData.append("importance", importance)

    const result = await createTimelineEvent(formData)

    setIsSubmitting(false)

    if (result.ok) {
      setOpen(false)
      setSummary("")
      setNote("")
      setEventType("NOTE")
      setImportance("NORMAL")
    } else {
      setError(result.error || "Failed to create event")
    }
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!isSubmitting) {
      setOpen(newOpen)
      if (!newOpen) {
        setError("")
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" className="gap-2">
          <Plus className="h-4 w-4" />
          Add Event
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Timeline Event</DialogTitle>
          <DialogDescription>
            Add a custom event to track your application progress
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="event_type">Event Type</Label>
            <Select
              value={eventType}
              onValueChange={(value) => setEventType(value as TimelineEventType)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="APPLIED">Applied</SelectItem>
                <SelectItem value="EMAIL">Email</SelectItem>
                <SelectItem value="CALL">Call</SelectItem>
                <SelectItem value="FOLLOW_UP">Follow-up</SelectItem>
                <SelectItem value="PHONE_SCREEN">Phone Screen</SelectItem>
                <SelectItem value="TECHNICAL">Technical</SelectItem>
                <SelectItem value="SYSTEM_DESIGN">System Design</SelectItem>
                <SelectItem value="ONSITE">Onsite</SelectItem>
                <SelectItem value="TAKE_HOME">Take-Home</SelectItem>
                <SelectItem value="RECRUITER_MESSAGE">Recruiter Message</SelectItem>
                <SelectItem value="OFFER">Offer</SelectItem>
                <SelectItem value="ACCEPTED">Accepted</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="NOTE">Note</SelectItem>
                <SelectItem value="CUSTOM">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="summary">Summary</Label>
            <Input
              id="summary"
              placeholder="Brief description of the event"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="note">Notes</Label>
            <Textarea
              id="note"
              placeholder="Additional details..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="importance">Importance</Label>
            <Select
              value={importance}
              onValueChange={(value) => setImportance(value as TimelineImportance)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NORMAL">Normal</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="CRITICAL">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding..." : "Add Event"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
