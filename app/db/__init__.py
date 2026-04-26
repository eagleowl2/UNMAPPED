"""
UNMAPPED persistence layer.

Lightweight, file-backed SQLite via SQLAlchemy 2.0 async + aiosqlite. Zero
infra: one file at $UNMAPPED_DB_URL (default `sqlite+aiosqlite:///./unmapped.db`).

Per Master Context §5 Phase 1 the DB is *additive* — the parse endpoint must
keep working if the DB is missing or unreachable. `init_db()` logs a warning
on failure and the app continues stateless.
"""
from app.db.session import (
    AsyncSessionLocal,
    get_engine,
    init_db,
    is_db_enabled,
)

__all__ = [
    "AsyncSessionLocal",
    "get_engine",
    "init_db",
    "is_db_enabled",
]