"""Async database engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from careeros_api.core.config import settings

# NullPool outside production: every connection is opened/closed per use, which
# avoids the "Event loop is closed" errors when pytest-asyncio spins a fresh loop
# per test. Production keeps the default QueuePool for throughput.
_poolclass = None if settings.ENV == "production" else NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    poolclass=_poolclass,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an ``AsyncSession``, committing on success and rolling back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
