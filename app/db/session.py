"""
Async SQLAlchemy engine + session factory.

Engine is created lazily on first use so importing this module doesn't
touch the filesystem (test isolation). `init_db()` runs at startup; if it
fails we log and disable the DB — the app stays fully functional.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base

logger = logging.getLogger(__name__)

_DEFAULT_URL = "sqlite+aiosqlite:///./unmapped.db"

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_db_enabled: bool = False


def _db_url() -> str:
    return os.getenv("UNMAPPED_DB_URL", _DEFAULT_URL)


def get_engine() -> AsyncEngine:
    """Return the singleton async engine. Creates it on first call."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            _db_url(),
            echo=os.getenv("UNMAPPED_DB_ECHO") == "1",
            future=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def AsyncSessionLocal() -> AsyncSession:  # noqa: N802 — factory-style alias
    """Return a new AsyncSession bound to the engine."""
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory()


def is_db_enabled() -> bool:
    return _db_enabled


async def init_db() -> bool:
    """Create tables if missing. Returns True on success.

    Failures are logged but never raised — the app must keep serving /parse
    even if the database is offline (Master Context §8 Priority 3, step 8).
    """
    global _db_enabled
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _db_enabled = True
        logger.info("UNMAPPED DB ready at %s", _db_url())
        return True
    except Exception as exc:  # noqa: BLE001 — DB is optional
        _db_enabled = False
        logger.warning(
            "UNMAPPED DB init failed (%s) — continuing in stateless mode.", exc
        )
        return False


async def dispose_engine() -> None:
    """Tear the engine down (used by lifespan + tests)."""
    global _engine, _session_factory, _db_enabled
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
    _db_enabled = False