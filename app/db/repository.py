"""
Profile read/write helpers.

The write side is invoked via FastAPI BackgroundTasks from /parse — it runs
after the response is sent so the SPA never waits on the DB. Errors are
swallowed (logged) — the parse response is the source of truth, the DB is
best-effort.

The read side never returns raw_input — only the indexed summary fields
plus the profile JSON we built ourselves (which already has no raw_input).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Integer, desc, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.db.session import AsyncSessionLocal, is_db_enabled

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Write side
# ---------------------------------------------------------------------------

def _flat_columns(profile_dict: dict[str, Any]) -> dict[str, Any]:
    """Project a ProfileCard dict to the flat indexed columns."""
    wage = profile_dict.get("wage_signal") or {}
    growth = profile_dict.get("growth_signal") or {}
    job_match = profile_dict.get("job_match") or {}
    automation = profile_dict.get("automation_risk") or {}
    bona = profile_dict.get("bona") or {}

    # Zero-credential isn't on the wire ProfileCard but show up indirectly via
    # the rationale. Look for a stable signal — the parser sets a clean flag
    # when it persists; we infer here as a fallback.
    rationale = (job_match.get("rationale") or "").lower()
    zero_cred = "zero-credential" in rationale or "zero_credential" in rationale

    return {
        "country": (profile_dict.get("country") or "").upper()[:2],
        "pseudonym": (profile_dict.get("pseudonym") or "")[:64],
        "age": profile_dict.get("age"),
        "location": (profile_dict.get("location") or "")[:128],
        "wage_score": int(wage.get("score") or 0),
        "growth_score": int(growth.get("score") or 0),
        "job_match_score": int(job_match["score"]) if job_match.get("score") is not None else None,
        "automation_risk_tier": automation.get("risk_tier"),
        "bona_overall_tier": bona.get("overall_tier"),
        "bona_overall_score": (
            float(bona["overall_score"]) if bona.get("overall_score") is not None else None
        ),
        "zero_credential": bool(zero_cred),
        "skill_count": len(profile_dict.get("skills") or []),
    }


async def upsert_profile(profile_dict: dict[str, Any], country: str) -> None:
    """Persist or refresh one Profile row. Called via fire-and-forget."""
    if not is_db_enabled():
        return
    profile_id = profile_dict.get("profile_id")
    if not profile_id:
        return

    flat = _flat_columns({**profile_dict, "country": country})
    payload = {
        "profile_id": profile_id,
        **flat,
        "profile_json": profile_dict,
        "updated_at": datetime.now(timezone.utc),
    }

    try:
        async with AsyncSessionLocal() as session:
            stmt = sqlite_insert(Profile).values(**payload)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Profile.profile_id],
                set_={k: stmt.excluded[k] for k in payload if k != "profile_id"},
            )
            await session.execute(stmt)
            await session.commit()
    except Exception as exc:  # noqa: BLE001 — DB is best-effort
        logger.warning("profile upsert failed for %s: %s", profile_id, exc)


# ---------------------------------------------------------------------------
# Read side — used by the employer/policymaker endpoints
# ---------------------------------------------------------------------------

async def list_profiles(
    session: AsyncSession,
    *,
    country: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Profile]:
    stmt = select(Profile).order_by(desc(Profile.updated_at)).limit(limit).offset(offset)
    if country:
        stmt = stmt.where(Profile.country == country.upper())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_profile(session: AsyncSession, profile_id: str) -> Optional[Profile]:
    stmt = select(Profile).where(Profile.profile_id == profile_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def aggregate_dashboard(session: AsyncSession) -> dict[str, Any]:
    """Aggregate stats for the policymaker dashboard.

    Returns ONLY non-PII aggregates. Per Master Context §6.3, this view
    never exposes individual rows.
    """
    total_q = select(func.count()).select_from(Profile)
    total = (await session.execute(total_q)).scalar_one()

    by_country_q = select(
        Profile.country,
        func.count().label("n"),
        func.avg(Profile.wage_score).label("avg_wage"),
        func.avg(Profile.growth_score).label("avg_growth"),
    ).group_by(Profile.country)
    by_country_rows = (await session.execute(by_country_q)).all()

    risk_q = select(
        Profile.country,
        Profile.automation_risk_tier,
        func.count().label("n"),
    ).group_by(Profile.country, Profile.automation_risk_tier)
    risk_rows = (await session.execute(risk_q)).all()

    bona_q = select(
        Profile.country,
        Profile.bona_overall_tier,
        func.count().label("n"),
    ).group_by(Profile.country, Profile.bona_overall_tier)
    bona_rows = (await session.execute(bona_q)).all()

    zero_cred_q = select(
        Profile.country,
        func.sum(func.cast(Profile.zero_credential, Integer)).label("n_zero"),
        func.count().label("n_total"),
    ).group_by(Profile.country)
    zero_rows = (await session.execute(zero_cred_q)).all()

    return {
        "total_profiles": int(total or 0),
        "by_country": [
            {
                "country": row.country,
                "count": int(row.n),
                "avg_wage_score": round(float(row.avg_wage or 0), 1),
                "avg_growth_score": round(float(row.avg_growth or 0), 1),
            }
            for row in by_country_rows
        ],
        "automation_risk_distribution": [
            {
                "country": row.country,
                "tier": row.automation_risk_tier or "unknown",
                "count": int(row.n),
            }
            for row in risk_rows
        ],
        "bona_distribution": [
            {
                "country": row.country,
                "tier": row.bona_overall_tier or "unknown",
                "count": int(row.n),
            }
            for row in bona_rows
        ],
        "zero_credential_rate": [
            {
                "country": row.country,
                "zero_credential": int(row.n_zero or 0),
                "total": int(row.n_total or 0),
                "share": round(
                    float(row.n_zero or 0) / float(row.n_total) if row.n_total else 0.0,
                    3,
                ),
            }
            for row in zero_rows
        ],
    }