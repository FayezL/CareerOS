"""Fake data generators for development and testing.

Provides realistic sample data for applications, companies, timeline events,
and related entities. Used across frontend (UI mock data) and backend (seeds,
test fixtures).
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from enum import StrEnum

# --- Company Types ---


class CompanyType(StrEnum):
    TECH = "Tech"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    RETAIL = "Retail"
    STARTUP = "Startup"
    ENTERPRISE = "Enterprise"


# --- Sample Companies ---
COMPANIES = [
    {
        "name": "TechCorp Solutions",
        "website": "https://techcorp.example.com",
        "type": CompanyType.TECH,
        "description": "Leading cloud infrastructure provider",
    },
    {
        "name": "FinServe Global",
        "website": "https://finserve.example.com",
        "type": CompanyType.FINANCE,
        "description": "Global financial services platform",
    },
    {
        "name": "HealthTech Innovations",
        "website": "https://healthtech.example.com",
        "type": CompanyType.HEALTHCARE,
        "description": "AI-powered healthcare solutions",
    },
    {
        "name": "RetailFlow Inc",
        "website": "https://retailflow.example.com",
        "type": CompanyType.RETAIL,
        "description": "E-commerce optimization platform",
    },
    {
        "name": "DataSpark Labs",
        "website": "https://dataspark.example.com",
        "type": CompanyType.STARTUP,
        "description": "Data analytics startup for SMBs",
    },
]


# --- Application Templates ---
APPLICATION_TEMPLATES = [
    {
        "role": "Senior Software Engineer",
        "salary_min": 180000,
        "salary_max": 220000,
        "status": "INTERVIEW",
        "source": "LinkedIn",
    },
    {
        "role": "Staff Backend Engineer",
        "salary_min": 200000,
        "salary_max": 250000,
        "status": "APPLIED",
        "source": "Wellfound",
    },
    {
        "role": "Engineering Manager",
        "salary_min": 240000,
        "salary_max": 300000,
        "status": "SAVED",
        "source": "Referral",
    },
    {
        "role": "Full Stack Developer",
        "salary_min": 150000,
        "salary_max": 190000,
        "status": "REJECTED",
        "source": "Company Website",
    },
    {
        "role": "DevOps Engineer",
        "salary_min": 170000,
        "salary_max": 210000,
        "status": "OFFER",
        "source": "Indeed",
    },
]


# --- Timeline Event Types ---
TIMELINE_EVENT_TYPES = [
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


TIMELINE_EVENT_SUMMARIES = [
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


TIMELINE_EVENT_NOTES = [
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


# --- Interview Templates ---
INTERVIEW_TEMPLATES = [
    {
        "interview_type": "PHONE_SCREEN",
        "duration": 30,
        "status": "COMPLETED",
        "notes": "Good first impression, discussed background",
    },
    {
        "interview_type": "TECHNICAL",
        "duration": 60,
        "status": "SCHEDULED",
        "notes": "Algorithm and data structures focus",
    },
    {
        "interview_type": "SYSTEM_DESIGN",
        "duration": 60,
        "status": "PENDING",
        "notes": "Scalable system design case study",
    },
    {
        "interview_type": "ONSITE",
        "duration": 240,
        "status": "COMPLETED",
        "notes": "Full day of interviews, positive experience",
    },
]


# --- Rejection Reason Categories ---
REJECTION_REASONS = [
    "EXPERIENCE",
    "SKILLS",
    "CULTURE",
    "SALARY",
    "LOCATION",
    "TIMING",
    "OTHER",
]


# --- Helper Functions ---


def generate_random_id() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def generate_random_date(
    days_ago: int = 30,
    future: bool = False,
) -> datetime:
    """Generate a random datetime within the specified range."""
    base_date = datetime.now()
    if future:
        delta = timedelta(days=random.randint(1, days_ago))
        return base_date + delta
    else:
        delta = timedelta(days=random.randint(0, days_ago))
        return base_date - delta


def generate_random_timeline_events(
    application_id: str,
    user_id: str,
    count: int = 3,
) -> list[dict]:
    """Generate realistic timeline events for an application."""
    events = []
    base_date = generate_random_date(days_ago=14)

    for i in range(count):
        event_date = base_date + timedelta(days=i * 2)
        event_type = random.choice(TIMELINE_EVENT_TYPES)
        importance = random.choice(["NORMAL", "IMPORTANT", "MILESTONE"])

        events.append(
            {
                "id": generate_random_id(),
                "user_id": user_id,
                "application_id": application_id,
                "event_type": event_type,
                "summary": random.choice(TIMELINE_EVENT_SUMMARIES),
                "note": random.choice(TIMELINE_EVENT_NOTES),
                "occurred_at": event_date.isoformat(),
                "importance": importance,
                "follow_up_date": (event_date + timedelta(days=7)).isoformat()
                if random.random() > 0.5
                else None,
                "source": "user",
            }
        )

    return events


def generate_complete_application_set(
    user_id: str,
    companies: list[dict[str, str]] | None = None,
) -> list[dict]:
    """Generate a complete set of applications with timeline events."""
    if companies is None:
        companies = COMPANIES

    applications = []

    for company in companies[:3]:  # Limit to 3 companies for small scale
        application_template = random.choice(APPLICATION_TEMPLATES)
        application_id = generate_random_id()

        application = {
            "id": application_id,
            "user_id": user_id,
            "company": company,
            "role": application_template["role"],
            "salary_min": application_template["salary_min"],
            "salary_max": application_template["salary_max"],
            "status": application_template["status"],
            "source": application_template["source"],
            "created_at": generate_random_date(days_ago=20).isoformat(),
            "updated_at": generate_random_date(days_ago=5).isoformat(),
            "description": (
                f"Exciting opportunity at {company['name']} as a {application_template['role']}"
            ),
            "rejection_reason_category": random.choice(REJECTION_REASONS)
            if application_template["status"] == "REJECTED"
            else None,
            "archived": False,
            "timeline_events": generate_random_timeline_events(
                application_id, user_id, count=random.randint(2, 4)
            ),
        }

        applications.append(application)

    return applications


def generate_sample_contacts(
    user_id: str,
    company_name: str,
    count: int = 2,
) -> list[dict]:
    """Generate sample contacts for a company."""
    contacts = []
    roles = ["Recruiter", "Engineering Manager", "Technical Lead"]

    for i in range(count):
        contacts.append(
            {
                "id": generate_random_id(),
                "user_id": user_id,
                "name": f"Contact {company_name} {i + 1}",
                "email": f"contact{i + 1}@{company_name.lower().replace(' ', '')}.com",
                "role": random.choice(roles),
                "company_name": company_name,
                "phone": (
                    f"+1-{random.randint(100, 999)}-"
                    f"{random.randint(100, 999)}-"
                    f"{random.randint(1000, 9999)}"
                ),
                "created_at": generate_random_date(days_ago=15).isoformat(),
            }
        )

    return contacts


# --- Main Data Generation Function ---


def generate_all_fake_data(user_id: str) -> dict:
    """Generate complete fake data set for development/testing."""
    applications = generate_complete_application_set(user_id)
    contacts = [
        contact
        for company in COMPANIES
        for contact in generate_sample_contacts(user_id, company["name"])
    ]

    return {
        "user_id": user_id,
        "companies": COMPANIES,
        "applications": applications,
        "contacts": contacts,
        "stats": {
            "total_applications": len(applications),
            "total_companies": len(COMPANIES),
            "total_contacts": len(contacts),
            "total_timeline_events": sum(len(app["timeline_events"]) for app in applications),
        },
    }


if __name__ == "__main__":
    # Generate and print sample data for verification
    sample_data = generate_all_fake_data(user_id="test-user-123")
    import json

    print(json.dumps(sample_data, indent=2, default=str))
