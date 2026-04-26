"""
Employer / policymaker read endpoints.

Auth: bearer token from `UNMAPPED_ADMIN_TOKEN`. If unset, endpoints respond
with HTTP 503 — the brief requires explicit consent on the operator side
before any non-aggregated data leaves the server.

The /dashboard endpoint is the policymaker view (§6.3). It aggregates only;
no row-level PII ever leaves through it.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import (
    aggregate_dashboard,
    get_profile,
    list_profiles,
)
from app.db.session import AsyncSessionLocal, is_db_enabled

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Auth dependency — single token, env-driven (hackathon scope)
# ---------------------------------------------------------------------------

def _require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    expected = os.getenv("UNMAPPED_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Employer API disabled — UNMAPPED_ADMIN_TOKEN is not set.",
        )
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token.",
        )


def _require_db() -> None:
    if not is_db_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistence layer not available.",
        )


async def _get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _summary(row: Any) -> dict[str, Any]:
    """Project a Profile row to its non-PII summary shape."""
    return {
        "profile_id": row.profile_id,
        "country": row.country,
        "pseudonym": row.pseudonym,
        "age": row.age,
        "location": row.location,
        "wage_score": row.wage_score,
        "growth_score": row.growth_score,
        "job_match_score": row.job_match_score,
        "automation_risk_tier": row.automation_risk_tier,
        "bona_overall_tier": row.bona_overall_tier,
        "bona_overall_score": row.bona_overall_score,
        "zero_credential": row.zero_credential,
        "skill_count": row.skill_count,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get(
    "/profiles",
    summary="List persisted profiles (non-PII summary).",
    dependencies=[Depends(_require_admin), Depends(_require_db)],
)
async def list_profiles_endpoint(
    country: Optional[str] = Query(default=None, pattern="^[A-Za-z]{2}$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(_get_session),
) -> dict[str, Any]:
    rows = await list_profiles(session, country=country, limit=limit, offset=offset)
    return {
        "ok": True,
        "count": len(rows),
        "profiles": [_summary(r) for r in rows],
    }


@router.get(
    "/profiles/{profile_id}",
    summary="Fetch one persisted ProfileCard.",
    dependencies=[Depends(_require_admin), Depends(_require_db)],
)
async def get_profile_endpoint(
    profile_id: str,
    session: AsyncSession = Depends(_get_session),
) -> dict[str, Any]:
    row = await get_profile(session, profile_id)
    if row is None:
        raise HTTPException(status_code=404, detail="profile_id not found")
    return {
        "ok": True,
        "summary": _summary(row),
        "profile": row.profile_json,
    }


@router.get(
    "/dashboard",
    summary="Aggregate stats for the policymaker view (no PII, no row data).",
    dependencies=[Depends(_require_admin), Depends(_require_db)],
)
async def dashboard_endpoint(
    session: AsyncSession = Depends(_get_session),
) -> dict[str, Any]:
    return {"ok": True, **await aggregate_dashboard(session)}