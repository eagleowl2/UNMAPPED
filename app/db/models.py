"""
ORM models — single Profile table + an optional API-key registry.

Schema choices (per Master Context §8 Priority 3):
  • `profile_json` is the canonical store — full ProfileCard JSON.
  • Flat indexed columns (wage_score, growth_score, …) are derived at insert
    time so the dashboard can aggregate without scanning every blob.
  • `raw_input` is NEVER persisted (PII rule, §5.4 of the protocol).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    """One ProfileCard returned by /parse, snapshotted for analytics.

    The PK is the `profile_id` from the parser (deterministic from the text
    hash) so calling /parse twice with the same input upserts a single row
    instead of accumulating duplicates.
    """

    __tablename__ = "profiles"

    profile_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    pseudonym: Mapped[str] = mapped_column(String(64))
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(128))

    # Flat indexed signals — derived from profile_json at insert time.
    wage_score: Mapped[int] = mapped_column(Integer, index=True)
    growth_score: Mapped[int] = mapped_column(Integer, index=True)
    job_match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    automation_risk_tier: Mapped[Optional[str]] = mapped_column(
        String(8), index=True, nullable=True
    )
    bona_overall_tier: Mapped[Optional[str]] = mapped_column(
        String(8), index=True, nullable=True
    )
    bona_overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    zero_credential: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    skill_count: Mapped[int] = mapped_column(Integer, default=0)

    # Full ProfileCard payload — source of truth for the GET endpoints.
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class ApiKey(Base):
    """Bcrypt-hashed API key for employer/policymaker endpoints.

    Hackathon scope: a single environment-variable token (UNMAPPED_ADMIN_TOKEN)
    also works without populating this table. The table exists so the
    upgrade path to per-employer keys is one migration away.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(64), unique=True)
    key_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )