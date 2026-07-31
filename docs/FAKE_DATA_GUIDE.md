"""Guide for using fake data with your CareerOS account.

This document explains how to populate your development database with
realistic fake data for testing and demonstration.
"""

# Using Fake Data with Your Account

## Quick Start (Default Test User)

The seed script creates data for a default test user:

```bash
cd backend
uv run alembic upgrade head  # Ensure DB is current
uv run python -m seeds.seed_db
```

This creates data for user ID: `00000000-0000-0000-0000-000000000001`

## Using Fake Data with Your Clerk Account

### Method 1: Get Your Clerk User ID

1. Sign into your CareerOS app
2. Open browser DevTools (F12)
3. Go to Console and run:
   ```javascript
   // If using Clerk
   window.Clerk?.user?.id
   ```
4. Copy your user ID (should be a UUID format)

### Method 2: Custom Seed Script

Create a custom seed script for your user ID:

```python
# backend/seeds/seed_my_account.py
from seeds.seed_db import main
import asyncio
import uuid

# Override the test user ID
import seeds.seed_db as seed_module
seed_module.TEST_USER_ID = "YOUR_CLERK_USER_ID_HERE"
seed_module.TEST_USER_EMAIL = "your.email@example.com"
seed_module.TEST_USER_NAME = "Your Name"

asyncio.run(main())
```

Run it:
```bash
cd backend
uv run python seeds/seed_my_account.py
```

### Method 3: Direct Python API

Use the fake data generators directly in Python scripts:

```python
# backend/examples/use_fake_data.py
from careeros_api.fake_data import generate_all_fake_data
from careeros_api.models.company import Company
from careeros_api.models.application import Application
from careeros_api.models.timeline_event import TimelineEvent
from careeros_api.db.session import async_session_maker
import asyncio

YOUR_USER_ID = "your-clerk-user-id-here"

async def seed_my_data():
    data = generate_all_fake_data(YOUR_USER_ID)

    async with async_session_maker() as session:
        # Create companies
        for company_data in data["companies"]:
            company = Company(
                user_id=YOUR_USER_ID,
                name=company_data["name"],
                website=company_data["website"],
                description=company_data["description"],
            )
            session.add(company)
        await session.commit()

        # Create applications with timeline events
        for app_data in data["applications"]:
            application = Application(
                user_id=YOUR_USER_ID,
                company_id=app_data["company_id"],
                role=app_data["role"],
                status=app_data["status"],
                # ... other fields
            )
            session.add(application)

            # Add timeline events
            for event_data in app_data["timeline_events"]:
                event = TimelineEvent(
                    user_id=YOUR_USER_ID,
                    application_id=application.id,
                    event_type=event_data["event_type"],
                    summary=event_data["summary"],
                    # ... other fields
                )
                session.add(event)

        await session.commit()

asyncio.run(seed_my_data())
```

## Frontend Mock Data Usage

For UI development without backend, use the TypeScript generators:

```typescript
// app/(app)/dashboard/page.tsx
import { mockData, generateMockDataSet } from '@/lib/mock-data'

export default function DashboardPage() {
  // Use pre-generated mock data
  const applications = mockData.applications
  const timelineEvents = mockData.timeline_events

  // Or generate fresh data
  const customData = generateMockDataSet('your-user-id')

  return (
    <div>
      <h1>Dashboard</h1>
      <div>
        {applications.map(app => (
          <div key={app.id}>
            {app.role} at {app.company.name}
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Testing with Fake Data

Use the enhanced pytest fixtures:

```python
# tests/test_my_feature.py
from tests.fixtures.fake_data import fully_seeded_test_data

async def test_with_fake_data(fully_seeded_test_data):
    data = fully_seeded_test_data

    # Access seeded data
    applications = data["applications"]
    timeline_events = data["timeline_events"]

    # Your test logic here
    assert len(applications) > 0
    assert len(timeline_events) > 0
```

## Environment Setup

Ensure your `.env` file is configured:

```bash
# .env
ENV=local
DATABASE_URL=postgresql+asyncpg://careeros:careeros@localhost:5433/careeros
CLERK_ISSUER=https://your-app.clerk.accounts.dev
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key
CLERK_SECRET_KEY=sk_test_your_secret
```

## Docker Development

When using Docker Compose:

```bash
# Start the full stack
docker compose up -d

# Wait for services to be ready, then seed data
docker compose exec backend uv run python -m seeds.seed_db
```

## Troubleshooting

### Data doesn't appear in UI
- Ensure you're using the correct user ID
- Check database connection: `docker compose exec backend uv run python -c "from careeros_api.db.session import engine; print('DB OK')"`
- Verify data exists: `docker compose exec backend psql -U careeros -d careeros -c "SELECT COUNT(*) FROM applications;"`

### Timeline events not showing
- Check the application ID matches
- Ensure events have correct `user_id`
- Verify `occurred_at` dates are valid ISO format

### Import errors
```bash
cd backend
uv run python -c "from careeros_api.fake_data import generate_all_fake_data; print('OK')"
```

## Next Steps

1. **For UI Development**: Use `frontend/src/lib/mock-data.ts` directly
2. **For Backend Development**: Run the seed script for your user ID
3. **For Testing**: Use the pytest fixtures in `tests/fixtures/fake_data.py`
4. **For Production**: Never use fake data in production environments

The fake data system is designed to make development and testing easier while maintaining realistic scenarios for job application tracking.