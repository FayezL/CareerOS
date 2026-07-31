"""Enhanced pytest fixtures using fake data generators.

Provides realistic test data that can be reused across test suites.
"""

from __future__ import annotations

import random
from datetime import datetime

import pytest
import pytest_asyncio

from careeros_api.fake_data import (
    COMPANIES,
    generate_complete_application_set,
    generate_random_date,
    generate_random_id,
    generate_random_timeline_events,
    generate_sample_contacts,
)
from careeros_api.models.application import Application, ApplicationStage
from careeros_api.models.company import Company
from careeros_api.models.contact import Contact
from careeros_api.models.timeline_event import (
    TimelineEvent,
    TimelineEventType,
    TimelineImportance,
)


@pytest.fixture
def test_user_id() -> str:
    """Generate a consistent test user ID."""
    return "test-user-fixture"


@pytest.fixture
def fake_companies() -> list[dict]:
    """Provide fake company data."""
    return COMPANIES


@pytest_asyncio.fixture
async def seeded_companies(
    async_session: any,
    test_user_id: str,
) -> list[Company]:
    """Create seeded companies in the database."""
    companies = []

    for company_data in COMPANIES:
        company = Company(
            id=generate_random_id(),
            user_id=test_user_id,
            name=company_data["name"],
            website=company_data["website"],
            description=company_data.get("description"),
            created_at=generate_random_date(days_ago=45),
        )
        async_session.add(company)
        companies.append(company)

    await async_session.commit()
    return companies


@pytest_asyncio.fixture
async def seeded_applications(
    async_session: any,
    test_user_id: str,
    seeded_companies: list[Company],
) -> list[Application]:
    """Create seeded applications with companies."""
    applications_data = generate_complete_application_set(test_user_id, seeded_companies)
    applications = []

    for app_data in applications_data:
        company = next(
            (c for c in seeded_companies if c.name == app_data["company"]["name"]),
            None,
        )
        if not company:
            continue

        application = Application(
            id=app_data["id"],
            user_id=test_user_id,
            company_id=company.id,
            role=app_data["role"],
            salary_min=app_data["salary_min"],
            salary_max=app_data["salary_max"],
            status=ApplicationStage[app_data["status"]],
            source=app_data["source"],
            description=app_data["description"],
            rejection_reason_category=app_data.get("rejection_reason_category"),
            archived=False,
            created_at=datetime.fromisoformat(app_data["created_at"]),
            updated_at=datetime.fromisoformat(app_data["updated_at"]),
        )
        async_session.add(application)
        applications.append(application)

    await async_session.commit()
    return applications


@pytest_asyncio.fixture
async def seeded_timeline_events(
    async_session: any,
    test_user_id: str,
    seeded_applications: list[Application],
) -> list[TimelineEvent]:
    """Create seeded timeline events for applications."""
    all_events = []

    for application in seeded_applications:
        events_data = generate_random_timeline_events(
            application.id, test_user_id, count=random.randint(2, 4)
        )

        for event_data in events_data:
            event = TimelineEvent(
                id=event_data["id"],
                user_id=test_user_id,
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
            async_session.add(event)
            all_events.append(event)

    await async_session.commit()
    return all_events


@pytest_asyncio.fixture
async def seeded_contacts(
    async_session: any,
    test_user_id: str,
    seeded_companies: list[Company],
) -> list[Contact]:
    """Create seeded contacts for companies."""
    all_contacts = []

    for company in seeded_companies:
        contacts_data = generate_sample_contacts(test_user_id, company.name, count=2)

        for contact_data in contacts_data:
            contact = Contact(
                id=contact_data["id"],
                user_id=test_user_id,
                name=contact_data["name"],
                email=contact_data["email"],
                role=contact_data.get("role"),
                company_name=contact_data.get("company_name"),
                phone=contact_data.get("phone"),
                created_at=datetime.fromisoformat(contact_data["created_at"]),
            )
            async_session.add(contact)
            all_contacts.append(contact)

    await async_session.commit()
    return all_contacts


@pytest_asyncio.fixture
async def fully_seeded_test_data(
    async_session: any,
    test_user_id: str,
) -> dict[str, list]:
    """Complete test dataset with companies, applications, events, and contacts."""
    # Companies
    companies = []
    for company_data in COMPANIES:
        company = Company(
            id=generate_random_id(),
            user_id=test_user_id,
            name=company_data["name"],
            website=company_data["website"],
            description=company_data.get("description"),
            created_at=generate_random_date(days_ago=45),
        )
        async_session.add(company)
        companies.append(company)

    await async_session.commit()

    # Applications
    applications_data = generate_complete_application_set(test_user_id, companies)
    applications = []

    for app_data in applications_data:
        company = next(
            (c for c in companies if c.name == app_data["company"]["name"]),
            None,
        )
        if not company:
            continue

        application = Application(
            id=app_data["id"],
            user_id=test_user_id,
            company_id=company.id,
            role=app_data["role"],
            salary_min=app_data["salary_min"],
            salary_max=app_data["salary_max"],
            status=ApplicationStage[app_data["status"]],
            source=app_data["source"],
            description=app_data["description"],
            rejection_reason_category=app_data.get("rejection_reason_category"),
            archived=False,
            created_at=datetime.fromisoformat(app_data["created_at"]),
            updated_at=datetime.fromisoformat(app_data["updated_at"]),
        )
        async_session.add(application)
        applications.append(application)

    await async_session.commit()

    # Timeline Events
    all_events = []
    for application in applications:
        events_data = generate_random_timeline_events(
            application.id, test_user_id, count=random.randint(2, 4)
        )

        for event_data in events_data:
            event = TimelineEvent(
                id=event_data["id"],
                user_id=test_user_id,
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
            async_session.add(event)
            all_events.append(event)

    await async_session.commit()

    # Contacts
    all_contacts = []
    for company in companies:
        contacts_data = generate_sample_contacts(test_user_id, company.name, count=2)

        for contact_data in contacts_data:
            contact = Contact(
                id=contact_data["id"],
                user_id=test_user_id,
                name=contact_data["name"],
                email=contact_data["email"],
                role=contact_data.get("role"),
                company_name=contact_data.get("company_name"),
                phone=contact_data.get("phone"),
                created_at=datetime.fromisoformat(contact_data["created_at"]),
            )
            async_session.add(contact)
            all_contacts.append(contact)

    await async_session.commit()

    return {
        "user_id": test_user_id,
        "companies": companies,
        "applications": applications,
        "timeline_events": all_events,
        "contacts": all_contacts,
    }
