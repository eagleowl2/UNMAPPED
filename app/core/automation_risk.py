"""
Module 2 — AI Readiness & Displacement Risk Lens (minimum-viable).

Combines:
  - Frey & Osborne (2017) raw automation probability per ISCO-08 occupation
  - ILO Future-of-Work LMIC adjustment factor per country × occupation
  - Wittgenstein Centre SSP2 post-secondary projection 2025→2035

Output shape mirrors the AutomationRisk Pydantic model in app/models/schemas.py.
Inputs come pre-extracted from EvidenceParser.parse_for_profile().
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.data_sources import (
    load_frey_osborne,
    load_lmic_adjustment,
    load_wittgenstein,
)


_TIER_THRESHOLDS = {
    "low": 0.34,
    "medium": 0.66,
}


def _tier_for(p: float) -> str:
    if p < _TIER_THRESHOLDS["low"]:
        return "low"
    if p < _TIER_THRESHOLDS["medium"]:
        return "medium"
    return "high"


def _trajectory_for(p: float, sector_growth: float) -> str:
    """Rough qualitative direction by 2035.

    sector_growth is the ILOSTAT 5yr CAGR percentage (-100..+100). High
    automation pressure on a contracting sector → declining; low automation
    pressure on an expanding sector → growing; everything else → stable.
    """
    if p >= 0.66 and sector_growth <= 2:
        return "declining"
    if p <= 0.34 and sector_growth >= 6:
        return "growing"
    return "stable"


def _adjusted_probability(country: str, isco: str) -> tuple[float, float, str]:
    """Return (raw, adjusted, soc_match) for an ISCO code.

    Falls back to the DEFAULT entry if a code is missing — never raises.
    """
    fo = load_frey_osborne().get("probabilities", {})
    raw_entry = fo.get(isco) or fo.get("DEFAULT", {"p_raw": 0.5, "soc_match": None})
    p_raw = float(raw_entry.get("p_raw", 0.5))
    soc = raw_entry.get("soc_match")

    adj_root = load_lmic_adjustment().get("country_factors", {})
    adj_country = adj_root.get(country.upper()) or adj_root.get("DEFAULT", {})
    factor = (
        adj_country.get("by_isco", {}).get(isco)
        or adj_country.get("default", 0.6)
    )
    p_adj = max(0.0, min(1.0, p_raw * float(factor)))
    return p_raw, p_adj, soc


def _adjacent_skills(isco: str) -> list[str]:
    """Suggest two adjacent / complementary skills less exposed to automation."""
    suggestions = {
        "2512": ["AI tooling for non-coders", "Product / UX design"],
        "2166": ["Brand storytelling", "Motion design / video"],
        "2320": ["Education-coach mentorship", "Digital-literacy training"],
        "2411": ["FP&A / advisory", "Compliance & audit"],
        "2643": ["Localization / cultural mediation", "Subtitling & accessibility"],
        "3312": ["Financial advisory", "Climate-risk underwriting"],
        "3431": ["Multimedia direction", "Brand photography"],
        "4131": ["Data quality QA", "RPA orchestration"],
        "4211": ["SME advisory / micro-loan officer", "Customer-success"],
        "5120": ["Catering / events", "Food-safety supervision"],
        "5141": ["Beauty entrepreneurship", "Aesthetic technician"],
        "5221": ["E-commerce micro-store", "Wholesale aggregation"],
        "5322": ["Nursing assistant", "Community health work"],
        "6110": ["Agronomy advisory", "Climate-smart agriculture"],
        "7112": ["Site supervision / QA", "Sustainable retrofit"],
        "7421": ["IoT diagnostics", "Right-to-repair instruction"],
        "7436": ["Fashion design", "Pattern making for ethical brands"],
        "7531": ["Fashion design", "Bespoke / heritage tailoring"],
        "8322": ["Logistics dispatch", "Fleet maintenance"],
        "9211": ["Agronomy advisory", "Cooperative aggregation"],
        "9621": ["Logistics dispatch", "Last-mile coordination"],
    }
    return suggestions.get(isco, ["Customer-facing services", "Skilled trades / supervision"])


def _durable_skills(isco: str) -> list[str]:
    """Return 'human-edge' skills durable against automation for this occupation."""
    durable = {
        "2512": ["systems thinking", "pair-programming with non-coders"],
        "2166": ["client storytelling", "creative direction"],
        "2320": ["mentorship", "youth motivation"],
        "2411": ["judgement", "client relationships"],
        "2643": ["cultural nuance", "domain specialization"],
        "3312": ["customer trust", "informal-economy underwriting"],
        "5120": ["hospitality", "improvisation"],
        "5141": ["bespoke service", "customer rapport"],
        "5221": ["network trust", "informal credit relationships"],
        "5322": ["empathy", "cultural fluency"],
        "7112": ["site coordination", "skilled judgement"],
        "7421": ["right-to-repair diagnostics", "customer trust"],
        "7531": ["bespoke fit", "design taste"],
        "8322": ["local-route knowledge", "passenger trust"],
        "9621": ["physical-task coordination", "informal-network access"],
    }
    return durable.get(isco, ["interpersonal trust", "context judgement"])


def compute_automation_risk(
    skills: list[dict[str, Any]],
    country: str,
    growth_signal_pct: Optional[float] = None,
) -> Optional[dict[str, Any]]:
    """Compute automation risk for the top skill on the profile.

    Returns None if the skill list is empty or fixtures unavailable.
    The shape mirrors `AutomationRisk` in app/models/schemas.py.
    """
    if not skills:
        return None
    top = skills[0]
    isco = top.get("taxonomy_code", "DEFAULT")
    skill_name = top.get("name", "this occupation")

    fo = load_frey_osborne()
    if not fo:
        return None

    p_raw, p_adj, soc = _adjusted_probability(country, isco)
    risk_tier = _tier_for(p_adj)
    sector_growth = float(growth_signal_pct or 0)
    trajectory = _trajectory_for(p_adj, sector_growth)

    wittgenstein = load_wittgenstein().get("projections", {})
    wit = wittgenstein.get(country.upper()) or wittgenstein.get("DEFAULT", {})
    wit_narrative = wit.get("narrative", "")

    rationale = (
        f"{skill_name}: Frey-Osborne raw exposure {round(p_raw * 100)}% "
        f"(SOC {soc or 'n/a'}); ILO LMIC calibration → {round(p_adj * 100)}% "
        f"in {country.upper()}. Trajectory to 2035: {trajectory}. "
        + (wit_narrative if wit_narrative else "")
    ).strip()

    return {
        "automation_probability": round(p_adj, 2),
        "raw_probability": round(p_raw, 2),
        "risk_tier": risk_tier,
        "trajectory_2035": trajectory,
        "durable_skills": _durable_skills(isco),
        "adjacent_skills": _adjacent_skills(isco),
        "rationale": rationale,
        "sources": [
            "Frey & Osborne (2017), Oxford Martin School",
            "ILO Future of Work — LMIC task indices (2018, 2021)",
            "Wittgenstein Centre Human Capital, SSP2 (2024)",
        ],
    }
