"""Alembic seed script for populating development database with fake data.

This script loads JSON seed files and creates realistic test data for
development, testing, and demonstration purposes.

Usage:
    uv run alembic upgrade head  # Ensure DB is at latest migration
    uv run python -m backend.seeds.seed_db
"""

from __future__ import annotations

import json

# Add src to path for imports
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from careeros_api.db.session import async_session_maker
from careeros_api.models.application import Application, ApplicationStage
from careeros_api.models.company import Company
from careeros_api.models.contact import Contact
from careeros_api.models.timeline_event import (
    TimelineEvent,
    TimelineEventType,
    TimelineImportance,
)
from careeros_api.models.user import User

# --- Constants ---
SEED_DIR = Path(__file__).parent
COMPANIES_FILE = SEED_DIR / "companies.json"
APPLICATIONS_FILE = SEED_DIR / "applications.json"
TIMELINE_EVENTS_FILE = SEED_DIR / "timeline_events.json"
CONTACTS_FILE = SEED_DIR / "contacts.json"

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_NAME = "Test User"


async def create_test_user() -> User:
    """Create or retrieve the test user."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == TEST_USER_ID))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✓ Test user already exists: {TEST_USER_EMAIL}")
            return existing_user

        user = User(
            id=TEST_USER_ID,
            email=TEST_USER_EMAIL,
            name=TEST_USER_NAME,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✓ Created test user: {TEST_USER_EMAIL}")
        return user


async def seed_companies(user_id: str) -> list[Company]:
    """Seed companies from JSON file."""
    if not COMPANIES_FILE.exists():
        print(f"✗ Companies seed file not found: {COMPANIES_FILE}")
        return []

    async with async_session_maker() as session:
        with open(COMPANIES_FILE) as f:
            companies_data = json.load(f)

        companies = []
        for company_data in companies_data:
            # Check if company already exists
            result = await session.execute(
                select(Company).where(
                    Company.user_id == user_id,
                    Company.name == company_data["name"],
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                companies.append(existing)
                continue

            company = Company(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=company_data["name"],
                website=company_data["website"],
                description=company_data.get("description"),
                created_at=datetime.now() - timedelta(days=random.randint(1, 45)),
            )
            session.add(company)
            companies.append(company)

        await session.commit()
        print(f"✓ Seeded {len(companies)} companies")
        return companies


async def seed_applications(user_id: str, companies: list[Company]) -> list[Application]:
    """Seed applications from JSON file."""
    if not APPLICATIONS_FILE.exists():
        print(f"✗ Applications seed file not found: {APPLICATIONS_FILE}")
        return []

    async with async_session_maker() as session:
        with open(APPLICATIONS_FILE) as f:
            applications_data = json.load(f)

        applications = []
        for app_data in applications_data:
            # Find matching company
            company = next(
                (c for c in companies if c.name == app_data["company_name"]),
                None,
            )
            if not company:
                print(f"✗ Company not found for application: {app_data['company_name']}")
                continue

            application = Application(
                id=str(uuid.uuid4()),
                user_id=user_id,
                company_id=company.id,
                role=app_data["role"],
                salary_min=app_data.get("salary_min"),
                salary_max=app_data.get("salary_max"),
                status=ApplicationStage[app_data["status"]],
                source=app_data["source"],
                description=app_data.get("description"),
                rejection_reason_category=app_data.get("rejection_reason_category"),
                archived=False,
                created_at=datetime.now() - timedelta(days=random.randint(10, 30)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 10)),
            )
            session.add(application)
            applications.append(application)

        await session.commit()
        print(f"✓ Seeded {len(applications)} applications")
        return applications


async def seed_timeline_events(
    user_id: str,
    applications: list[Application],
) -> list[TimelineEvent]:
    """Seed timeline events from JSON file."""
    if not TIMELINE_EVENTS_FILE.exists():
        print(f"✗ Timeline events seed file not found: {TIMELINE_EVENTS_FILE}")
        return []

    async with async_session_maker() as session:
        with open(TIMELINE_EVENTS_FILE) as f:
            events_data = json.load(f)

        events = []
        for event_data in events_data:
            # Assign to a random application
            application = applications[random.randint(0, len(applications) - 1)]

            event = TimelineEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                application_id=application.id,
                event_type=TimelineEventType[event_data["event_type"]],
                summary=event_data.get("summary"),
                note=event_data.get("note"),
                occurred_at=datetime.fromisoformat(event_data["occurred_at"]),
                importance=TimelineImportance[event_data["importance"]],
                follow_up_date=datetime.fromisoformat(event_data["follow_up_date"])
                if event_data.get("follow_up_date")
                else None,
                source=event_data["source"],
            )
            session.add(event)
            events.append(event)

        await session.commit()
        print(f"✓ Seeded {len(events)} timeline events")
        return events


async def seed_contacts(user_id: str) -> list[Contact]:
    """Seed contacts from JSON file."""
    if not CONTACTS_FILE.exists():
        print(f"✗ Contacts seed file not found: {CONTACTS_FILE}")
        return []

    async with async_session_maker() as session:
        with open(CONTACTS_FILE) as f:
            contacts_data = json.load(f)

        contacts = []
        for contact_data in contacts_data:
            contact = Contact(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=contact_data["name"],
                email=contact_data["email"],
                role=contact_data.get("role"),
                company_name=contact_data.get("company_name"),
                phone=contact_data.get("phone"),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            )
            session.add(contact)
            contacts.append(contact)

        await session.commit()
        print(f"✓ Seeded {len(contacts)} contacts")
        return contacts


async def seed_additional_timeline_events(
    user_id: str,
    applications: list[Application],
) -> None:
    """Generate additional timeline events for each application."""
    async with async_session_maker() as session:
        event_types = [
            TimelineEventType.EMAIL,
            TimelineEventType.CALL,
            TimelineEventType.FOLLOW_UP,
            TimelineEventType.TECHNICAL,
            TimelineEventType.NOTE,
        ]

        for application in applications:
            # Add 2-3 additional events per application
            num_events = random.randint(2, 3)
            base_date = application.created_at + timedelta(days=random.randint(1, 7))

            for i in range(num_events):
                event_date = base_date + timedelta(days=i * 2)
                event_type = event_types[random.randint(0, len(event_types) - 1)]
                importance = TimelineImportance.NORMAL

                if event_type in [TimelineEventType.TECHNICAL, TimelineEventType.ONSITE]:
                    importance = TimelineImportance.IMPORTANT

                event = TimelineEvent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    application_id=application.id,
                    event_type=event_type,
                    summary=f"Additional event {i + 1}",
                    note=f"Generated event for {application.role} at {application.company.name}",
                    occurred_at=event_date,
                    importance=importance,
                    follow_up_date=event_date + timedelta(days=7)
                    if random.random() > 0.5
                    else None,
                    source="user",
                )
                session.add(event)

        await session.commit()
        print(f"✓ Seeded additional timeline events for {len(applications)} applications")


async def main() -> None:
    """Main seeding function."""
    print("\n=== Seeding CareerOS Database ===\n")

    # Create test user
    user = await create_test_user()

    # Seed companies
    companies = await seed_companies(user.id)

    # Seed applications
    applications = await seed_applications(user.id, companies)

    # Seed timeline events from file
    await seed_timeline_events(user.id, applications)

    # Seed additional timeline events
    await seed_additional_timeline_events(user.id, applications)

    # Seed contacts
    await seed_contacts(user.id)

    print("\n=== Seeding Complete ===")
    print(f"✓ User: {user.email}")
    print(f"✓ Companies: {len(companies)}")
    print(f"✓ Applications: {len(applications)}")
    print(f"✓ Contacts: {len(await seed_contacts(user.id))}")
    print()


if __name__ == "__main__":
    import asyncio
    import random

    asyncio.run(main())
