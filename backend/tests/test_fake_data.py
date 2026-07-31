"""Test that fake data generators work correctly."""

from __future__ import annotations

from careeros_api.fake_data import (
    COMPANIES,
    generate_all_fake_data,
    generate_complete_application_set,
    generate_random_date,
    generate_random_id,
    generate_random_timeline_events,
    generate_sample_contacts,
)


def test_fake_companies_structure():
    """Verify fake companies have expected structure."""
    assert len(COMPANIES) > 0

    for company in COMPANIES:
        assert "name" in company
        assert "website" in company
        assert "type" in company
        assert "description" in company
        assert company["name"]
        assert company["website"].startswith("https://")


def test_generate_random_id_is_unique():
    """Verify random ID generation produces unique IDs."""
    ids = [generate_random_id() for _ in range(100)]
    assert len(set(ids)) == 100  # All unique


def test_generate_random_date_is_in_range():
    """Verify random dates fall within expected range."""
    dates = [generate_random_date(days_ago=30) for _ in range(50)]

    now = generate_random_date(0)
    for date in dates:
        assert date <= now  # Should be in the past
        age = (now - date).days
        assert 0 <= age <= 30  # Should be within 30 days


def test_generate_complete_application_set():
    """Verify application set generation."""
    user_id = "test-user"
    applications = generate_complete_application_set(user_id)

    assert len(applications) > 0

    for app in applications:
        assert app["user_id"] == user_id
        assert "id" in app
        assert "company" in app
        assert "role" in app
        assert "status" in app
        assert "timeline_events" in app


def test_generate_random_timeline_events():
    """Verify timeline event generation."""
    user_id = "test-user"
    application_id = "app-123"

    events = generate_random_timeline_events(application_id, user_id, count=5)

    assert len(events) == 5

    for event in events:
        assert event["user_id"] == user_id
        assert event["application_id"] == application_id
        assert "event_type" in event
        assert "summary" in event
        assert "occurred_at" in event
        assert "importance" in event


def test_generate_sample_contacts():
    """Verify contact generation."""
    user_id = "test-user"
    company_name = "Test Company"

    contacts = generate_sample_contacts(user_id, company_name, count=3)

    assert len(contacts) == 3

    for contact in contacts:
        assert contact["user_id"] == user_id
        assert "name" in contact
        assert "email" in contact
        assert "@" in contact["email"]  # Verify it's a valid email format


def test_generate_all_fake_data():
    """Verify complete fake data set generation."""
    user_id = "comprehensive-test-user"
    data = generate_all_fake_data(user_id)

    assert "user_id" in data
    assert "companies" in data
    assert "applications" in data
    assert "contacts" in data
    assert "stats" in data

    assert data["user_id"] == user_id
    assert len(data["companies"]) > 0
    assert len(data["applications"]) > 0
    assert len(data["contacts"]) > 0

    # Verify stats are accurate
    assert data["stats"]["total_companies"] == len(data["companies"])
    assert data["stats"]["total_applications"] == len(data["applications"])
    assert data["stats"]["total_contacts"] == len(data["contacts"])


def test_timeline_events_chronological_order():
    """Verify timeline events are generated in chronological order."""
    user_id = "test-user"
    application_id = "app-123"

    events = generate_random_timeline_events(application_id, user_id, count=10)

    # Check dates are in ascending order
    dates = [event["occurred_at"] for event in events]
    assert dates == sorted(dates)


def test_fake_data_realistic_content():
    """Verify fake data contains realistic content."""
    user_id = "test-user"
    data = generate_all_fake_data(user_id)

    # Check company names are realistic
    for company in data["companies"]:
        assert len(company["name"]) > 3
        assert len(company["name"]) < 100

    # Check application roles are realistic
    for app in data["applications"]:
        assert len(app["role"]) > 5
        assert any(
            keyword in app["role"].lower()
            for keyword in ["engineer", "developer", "manager", "lead"]
        )

    # Check timeline events have meaningful summaries
    for app in data["applications"]:
        for event in app["timeline_events"]:
            if event.get("summary"):
                assert len(event["summary"]) > 5
                assert len(event["summary"]) < 200
