"""Custom seed script for your personal CareerOS account.

Replace YOUR_CLERK_USER_ID with your actual Clerk user ID to seed
fake data specifically for your account.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import seeds.seed_db as seed_module

# --- REPLACE WITH YOUR ACTUAL CLERK USER ID ---
YOUR_CLERK_USER_ID = "YOUR_CLERK_USER_ID_HERE"
YOUR_EMAIL = "your.email@example.com"
YOUR_NAME = "Your Name"

# Override default test user with your credentials
seed_module.TEST_USER_ID = YOUR_CLERK_USER_ID
seed_module.TEST_USER_EMAIL = YOUR_EMAIL
seed_module.TEST_USER_NAME = YOUR_NAME


def main() -> None:
    """Main seeding function."""
    print(f"🌱 Seeding fake data for user: {YOUR_EMAIL}")
    print(f"👤 User ID: {YOUR_CLERK_USER_ID}")
    print()

    if YOUR_CLERK_USER_ID == "YOUR_CLERK_USER_ID_HERE":
        print("❌ ERROR: Please update YOUR_CLERK_USER_ID with your actual Clerk user ID")
        print("   You can find it in your browser console: window.Clerk?.user?.id")
        sys.exit(1)

    asyncio.run(seed_module.main())

    print()
    print("✅ Fake data seeded successfully!")
    print(f"📊 Data created for: {YOUR_EMAIL}")
    print("🔍 Refresh your CareerOS dashboard to see the new data")


if __name__ == "__main__":
    main()
