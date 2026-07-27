import type { Application, Interview, Note, StageHistory, TimelineEvent } from "@/types"
import {
  Calendar,
  CheckCircle2,
  FileText,
  MessageSquare,
  Phone,
  Send,
  User,
  XCircle,
} from "lucide-react"

export interface EventMetadata {
  icon: React.ComponentType<{ className?: string }>
  label: string
  color: string
  description: string
}

export interface TimelineItem {
  id: string
  type: "stage" | "interview" | "note" | "custom"
  occurred_at: string
  metadata: EventMetadata
  title: string
  body: string | null
  importance?: "NORMAL" | "HIGH" | "CRITICAL"
  source?: string
  isReview: boolean
  borderColor: string
}

const EVENT_METADATA: Record<string, EventMetadata> = {
  APPLIED: {
    icon: Send,
    label: "Applied",
    color: "text-blue-600",
    description: "Submitted application",
  },
  EMAIL: {
    icon: MessageSquare,
    label: "Email",
    color: "text-slate-600",
    description: "Email correspondence",
  },
  CALL: {
    icon: Phone,
    label: "Call",
    color: "text-purple-600",
    description: "Phone call",
  },
  FOLLOW_UP: {
    icon: Calendar,
    label: "Follow-up",
    color: "text-orange-600",
    description: "Follow-up scheduled",
  },
  PHONE_SCREEN: {
    icon: Phone,
    label: "Phone Screen",
    color: "text-indigo-600",
    description: "Initial phone screen",
  },
  TECHNICAL: {
    icon: FileText,
    label: "Technical",
    color: "text-cyan-600",
    description: "Technical interview",
  },
  SYSTEM_DESIGN: {
    icon: FileText,
    label: "System Design",
    color: "text-emerald-600",
    description: "System design interview",
  },
  ONSITE: {
    icon: User,
    label: "Onsite",
    color: "text-violet-600",
    description: "Onsite interviews",
  },
  TAKE_HOME: {
    icon: FileText,
    label: "Take-Home",
    color: "text-amber-600",
    description: "Take-home assignment",
  },
  RECRUITER_MESSAGE: {
    icon: MessageSquare,
    label: "Recruiter Message",
    color: "text-rose-600",
    description: "Message from recruiter",
  },
  OFFER: {
    icon: CheckCircle2,
    label: "Offer",
    color: "text-green-600",
    description: "Received offer",
  },
  ACCEPTED: {
    icon: CheckCircle2,
    label: "Accepted",
    color: "text-green-600",
    description: "Accepted offer",
  },
  REJECTED: {
    icon: XCircle,
    label: "Rejected",
    color: "text-red-600",
    description: "Application rejected",
  },
  NOTE: {
    icon: FileText,
    label: "Note",
    color: "text-slate-500",
    description: "Personal note",
  },
  CUSTOM: {
    icon: FileText,
    label: "Event",
    color: "text-slate-600",
    description: "Custom event",
  },
}

function getEventMetadata(eventType: string): EventMetadata {
  return EVENT_METADATA[eventType] || EVENT_METADATA.CUSTOM
}

export function buildTimeline(
  application: Application,
  stageHistory: StageHistory[],
  interviews: Interview[],
  notes: Note[],
  timelineEvents: TimelineEvent[],
): TimelineItem[] {
  const items: TimelineItem[] = []

  for (const stage of stageHistory) {
    items.push({
      id: `stage-${stage.id}`,
      type: "stage",
      occurred_at: stage.changed_at,
      metadata: {
        icon: Calendar,
        label: "Stage Change",
        color: "text-blue-600",
        description: `Moved to ${stage.to_stage.name}`,
      },
      title: `Moved to ${stage.to_stage.name}`,
      body: stage.note,
      isReview: false,
      borderColor: "border-l-blue-500",
    })
  }

  for (const interview of interviews) {
    const metadata = getEventMetadata(interview.type.toUpperCase())
    items.push({
      id: `interview-${interview.id}`,
      type: "interview",
      occurred_at: interview.scheduled_at,
      metadata,
      title: metadata.label,
      body: interview.notes,
      isReview: false,
      borderColor: "border-l-slate-200",
    })
  }

  for (const note of notes) {
    items.push({
      id: `note-${note.id}`,
      type: "note",
      occurred_at: note.created_at,
      metadata: {
        icon: FileText,
        label: note.title || "Note",
        color: "text-slate-500",
        description: "Personal note",
      },
      title: note.title || "Note",
      body: note.body,
      isReview: true,
      borderColor: "border-l-slate-200",
    })
  }

  for (const event of timelineEvents) {
    const metadata = getEventMetadata(event.event_type)
    const importanceColor =
      event.importance === "HIGH"
        ? "border-l-amber-500"
        : event.importance === "CRITICAL"
          ? "border-l-red-500"
          : "border-l-slate-200"
    items.push({
      id: `event-${event.id}`,
      type: "custom",
      occurred_at: event.occurred_at,
      metadata,
      title: event.summary || metadata.label,
      body: event.note,
      importance: event.importance,
      source: event.source,
      isReview: event.event_type === "NOTE",
      borderColor: importanceColor,
    })
  }

  return items.sort((a, b) => new Date(a.occurred_at).getTime() - new Date(b.occurred_at).getTime())
}

export const EVENT_METADATA_MAP = EVENT_METADATA
