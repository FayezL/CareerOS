// Frontend fake data generators for development and testing
// Provides realistic sample data for UI mock data and development

// --- Company Types ---
export type CompanyType = "Tech" | "Finance" | "Healthcare" | "Retail" | "Startup" | "Enterprise"

export interface Company {
  id: string
  user_id: string
  name: string
  website: string
  description?: string
  created_at: string
}

// --- Application Types ---
export type ApplicationStatus =
  "SAVED" | "APPLIED" | "INTERVIEW" | "OFFER" | "ACCEPTED" | "REJECTED"
export type Source = "LinkedIn" | "Wellfound" | "Referral" | "Company Website" | "Indeed"

export interface Application {
  id: string
  user_id: string
  company: Company
  role: string
  salary_min?: number
  salary_max?: number
  status: ApplicationStatus
  source: Source
  description?: string
  created_at: string
  updated_at: string
  rejection_reason_category?: string
  archived: boolean
}

// --- Timeline Event Types ---
export type TimelineEventType =
  | "APPLIED"
  | "EMAIL"
  | "CALL"
  | "FOLLOW_UP"
  | "PHONE_SCREEN"
  | "TECHNICAL"
  | "SYSTEM_DESIGN"
  | "ONSITE"
  | "TAKE_HOME"
  | "RECRUITER_MESSAGE"
  | "OFFER"
  | "ACCEPTED"
  | "REJECTED"
  | "NOTE"
  | "CUSTOM"
export type TimelineImportance = "NORMAL" | "IMPORTANT" | "MILESTONE"

export interface TimelineEvent {
  id: string
  user_id: string
  application_id: string
  event_type: TimelineEventType
  summary?: string
  note?: string
  occurred_at: string
  importance: TimelineImportance
  follow_up_date?: string
  source: string
}

// --- Contact Types ---
export interface Contact {
  id: string
  user_id: string
  name: string
  email: string
  role?: string
  company_name?: string
  phone?: string
  created_at: string
}

// --- Helper Functions ---
function generateRandomId(): string {
  return `id-${Math.random().toString(36).substring(2, 15)}-${Math.random().toString(36).substring(2, 15)}`
}

function generateRandomDate(daysAgo: number = 30, future: boolean = false): string {
  const baseDate = new Date()
  const days = Math.floor(Math.random() * daysAgo)
  const date = future
    ? baseDate.getTime() + days * 24 * 60 * 60 * 1000
    : baseDate.getTime() - days * 24 * 60 * 60 * 1000
  return new Date(date).toISOString()
}

// --- Company Generators ---
export const COMPANIES: Company[] = [
  {
    id: generateRandomId(),
    user_id: "mock-user-1",
    name: "TechCorp Solutions",
    website: "https://techcorp.example.com",
    description: "Leading cloud infrastructure provider",
    created_at: generateRandomDate(45),
  },
  {
    id: generateRandomId(),
    user_id: "mock-user-1",
    name: "FinServe Global",
    website: "https://finserve.example.com",
    description: "Global financial services platform",
    created_at: generateRandomDate(30),
  },
  {
    id: generateRandomId(),
    user_id: "mock-user-1",
    name: "HealthTech Innovations",
    website: "https://healthtech.example.com",
    description: "AI-powered healthcare solutions",
    created_at: generateRandomDate(20),
  },
  {
    id: generateRandomId(),
    user_id: "mock-user-1",
    name: "RetailFlow Inc",
    website: "https://retailflow.example.com",
    description: "E-commerce optimization platform",
    created_at: generateRandomDate(15),
  },
  {
    id: generateRandomId(),
    user_id: "mock-user-1",
    name: "DataSpark Labs",
    website: "https://dataspark.example.com",
    description: "Data analytics startup for SMBs",
    created_at: generateRandomDate(10),
  },
]

// --- Application Templates ---
const APPLICATION_TEMPLATES = [
  {
    role: "Senior Software Engineer",
    salaryMin: 180000,
    salaryMax: 220000,
    status: "INTERVIEW" as ApplicationStatus,
    source: "LinkedIn" as Source,
  },
  {
    role: "Staff Backend Engineer",
    salaryMin: 200000,
    salaryMax: 250000,
    status: "APPLIED" as ApplicationStatus,
    source: "Wellfound" as Source,
  },
  {
    role: "Engineering Manager",
    salaryMin: 240000,
    salaryMax: 300000,
    status: "SAVED" as ApplicationStatus,
    source: "Referral" as Source,
  },
  {
    role: "Full Stack Developer",
    salaryMin: 150000,
    salaryMax: 190000,
    status: "REJECTED" as ApplicationStatus,
    source: "Company Website" as Source,
  },
  {
    role: "DevOps Engineer",
    salaryMin: 170000,
    salaryMax: 210000,
    status: "OFFER" as ApplicationStatus,
    source: "Indeed" as Source,
  },
]

// --- Timeline Event Data ---
const TIMELINE_EVENT_TYPES: TimelineEventType[] = [
  "EMAIL",
  "CALL",
  "FOLLOW_UP",
  "PHONE_SCREEN",
  "TECHNICAL",
  "SYSTEM_DESIGN",
  "ONSITE",
  "TAKE_HOME",
  "RECRUITER_MESSAGE",
  "OFFER",
  "ACCEPTED",
  "REJECTED",
  "NOTE",
  "CUSTOM",
]

const TIMELINE_EVENT_SUMMARIES = [
  "Initial phone screen with HR",
  "Technical interview with engineering team",
  "Follow-up call about next steps",
  "Recruiter reached out about opportunity",
  "Take-home assignment received",
  "System design interview scheduled",
  "On-site interview completed",
  "Offer discussion and negotiation",
  "Application submitted online",
  "Company reached out via LinkedIn",
]

const TIMELINE_EVENT_NOTES = [
  "Good conversation, discussed project experience",
  "Challenging technical questions about database design",
  "Team seems well-organized and collaborative",
  "Strong interest in my background with distributed systems",
  "Assignment focuses on API design and performance",
  "Need to prepare for system design round",
  "Positive feedback from all interviewers",
  "Competitive compensation package discussed",
  "Role aligns well with career goals",
  "Recruiter mentioned potential for rapid growth",
]

const TIMELINE_IMPORTANCE: TimelineImportance[] = ["NORMAL", "IMPORTANT", "MILESTONE"]

const REJECTION_REASONS = [
  "EXPERIENCE",
  "SKILLS",
  "CULTURE",
  "SALARY",
  "LOCATION",
  "TIMING",
  "OTHER",
]

// --- Generator Functions ---
function generateRandomTimelineEvents(
  applicationId: string,
  userId: string,
  count: number = 3,
): TimelineEvent[] {
  const events: TimelineEvent[] = []
  const baseDate = new Date(generateRandomDate(14))

  for (let i = 0; i < count; i++) {
    const eventDate = new Date(baseDate.getTime() + i * 2 * 24 * 60 * 60 * 1000)
    const eventType = TIMELINE_EVENT_TYPES[Math.floor(Math.random() * TIMELINE_EVENT_TYPES.length)]
    const importance = TIMELINE_IMPORTANCE[Math.floor(Math.random() * TIMELINE_IMPORTANCE.length)]

    events.push({
      id: generateRandomId(),
      user_id: userId,
      application_id: applicationId,
      event_type: eventType,
      summary:
        TIMELINE_EVENT_SUMMARIES[Math.floor(Math.random() * TIMELINE_EVENT_SUMMARIES.length)],
      note: TIMELINE_EVENT_NOTES[Math.floor(Math.random() * TIMELINE_EVENT_NOTES.length)],
      occurred_at: eventDate.toISOString(),
      importance,
      follow_up_date:
        Math.random() > 0.5
          ? new Date(eventDate.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString()
          : undefined,
      source: "user",
    })
  }

  return events
}

export function generateApplications(userId: string, count: number = 5): Application[] {
  const applications: Application[] = []

  for (let i = 0; i < count; i++) {
    const template = APPLICATION_TEMPLATES[Math.floor(Math.random() * APPLICATION_TEMPLATES.length)]
    const company = COMPANIES[Math.floor(Math.random() * COMPANIES.length)]
    const applicationId = generateRandomId()

    applications.push({
      id: applicationId,
      user_id: userId,
      company,
      role: template.role,
      salary_min: template.salaryMin,
      salary_max: template.salaryMax,
      status: template.status,
      source: template.source,
      created_at: generateRandomDate(20),
      updated_at: generateRandomDate(5),
      description: `Exciting opportunity at ${company.name} as a ${template.role}`,
      rejection_reason_category:
        template.status === "REJECTED"
          ? REJECTION_REASONS[Math.floor(Math.random() * REJECTION_REASONS.length)]
          : undefined,
      archived: false,
    })
  }

  return applications
}

export function generateTimelineEvents(
  applications: Application[],
  userId: string,
): TimelineEvent[] {
  const events: TimelineEvent[] = []

  for (const application of applications) {
    const appEvents = generateRandomTimelineEvents(
      application.id,
      userId,
      Math.floor(Math.random() * 3) + 2,
    )
    events.push(...appEvents)
  }

  return events.sort(
    (a, b) => new Date(a.occurred_at).getTime() - new Date(b.occurred_at).getTime(),
  )
}

export function generateContacts(userId: string, count: number = 4): Contact[] {
  const contacts: Contact[] = []
  const roles = ["Recruiter", "Engineering Manager", "Technical Lead", "HR"]

  for (let i = 0; i < count; i++) {
    const company = COMPANIES[Math.floor(Math.random() * COMPANIES.length)]
    contacts.push({
      id: generateRandomId(),
      user_id: userId,
      name: `Contact ${company.name.split(" ")[0]} ${i + 1}`,
      email: `contact${i + 1}@${company.name.toLowerCase().replace(/\s+/g, "")}.example.com`,
      role: roles[Math.floor(Math.random() * roles.length)],
      company_name: company.name,
      phone: `+1-${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 9000) + 1000}`,
      created_at: generateRandomDate(15),
    })
  }

  return contacts
}

// --- Complete Data Set Generator ---
export interface MockDataSet {
  user_id: string
  companies: Company[]
  applications: Application[]
  timeline_events: TimelineEvent[]
  contacts: Contact[]
  stats: {
    total_applications: number
    total_companies: number
    total_contacts: number
    total_timeline_events: number
  }
}

export function generateMockDataSet(userId: string = "mock-user-1"): MockDataSet {
  const applications = generateApplications(userId, 5)
  const timeline_events = generateTimelineEvents(applications, userId)
  const contacts = generateContacts(userId, 4)

  return {
    user_id: userId,
    companies: COMPANIES,
    applications,
    timeline_events,
    contacts,
    stats: {
      total_applications: applications.length,
      total_companies: COMPANIES.length,
      total_contacts: contacts.length,
      total_timeline_events: timeline_events.length,
    },
  }
}

// --- Export for use in components ---
export const mockData = generateMockDataSet()
export const mockApplications = mockData.applications
export const mockCompanies = mockData.companies
export const mockTimelineEvents = mockData.timeline_events
export const mockContacts = mockData.contacts
