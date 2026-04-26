"""
Module 2 — Job-Match Signal Engine (v0.4.0).

Takes a parsed skill profile (list of ExtractedSkill-like dicts + country context)
and produces:
  - job_match_signal  : Signal (score 0-100, rationale, opportunity_count)
  - matched_opportunities : list[OpportunityEntry] — top-5 ranked concrete openings
  - updated network_entry  : NetworkEntryPoint from the #1 matched opportunity

Matching algorithm (BONA-style, no external API):
  1. Load opportunity_catalog from the country profile JSON.
  2. For each opportunity, compute a match_score:
        isco_score   = 1.0 if exact ISCO match else
                       0.6 if same major ISCO group else 0.1
        skill_boost  = max(confidence) of skills matching the opportunity ISCO
        zero_cred    = +0.15 if opportunity accepts zero-credential & profile is zero-cred
        language     = +0.10 if profile speaks a language the opp explicitly requires
        multi_skill  = +0.05 * min(len(skills)-1, 2)  (diversification bonus)
        match_score  = clamp(isco_score * 0.55 + skill_boost * 0.35 + bonuses, 0, 1)
  3. Filter: keep match_score >= 0.35.
  4. Rank descending; take top 5.
  5. job_match score = weighted mean of top-3 scores * 100 (floor 10, ceil 100).
"""
from __future__ import annotations

import math
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Public data-classes (plain dicts for JSON serialisation; Pydantic models
# in schemas.py wrap these on the way out).
# ---------------------------------------------------------------------------

def make_opportunity(
    title: str,
    employer_type: str,
    channel: str,
    lat: float,
    lng: float,
    label: str,
    wage_range: str,
    isco_code: str,
    formalization_path: str,
    match_score: float,
    accepts_zero_credential: bool = True,
    required_languages: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "employer_type": employer_type,
        "channel": channel,
        "lat": lat,
        "lng": lng,
        "label": label,
        "wage_range": wage_range,
        "isco_code": isco_code,
        "formalization_path": formalization_path,
        "match_score": round(match_score, 3),
        "accepts_zero_credential": accepts_zero_credential,
        "required_languages": required_languages or [],
    }


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def _isco_group(code: str) -> str:
    """Return the 1-digit ISCO major group."""
    return code[0] if code and code[0].isdigit() else "9"


def _skill_boost(skills: list[dict[str, Any]], isco_code: str) -> float:
    """Max confidence of skills that match this opportunity's ISCO code."""
    best = 0.0
    for sk in skills:
        tc = str(sk.get("taxonomy_code", ""))
        conf = float(sk.get("confidence", sk.get("evidence_weight", 0.5)))
        if tc == isco_code:
            best = max(best, conf)
        elif tc and tc[0] == isco_code[0]:
            best = max(best, conf * 0.6)
    return best


def _score_opportunity(
    opp: dict[str, Any],
    skills: list[dict[str, Any]],
    zero_credential: bool,
    profile_languages: list[str],
) -> float:
    isco = str(opp.get("isco_code", "9999"))

    # Base ISCO match against ALL skills
    best_isco_score = 0.0
    for sk in skills:
        tc = str(sk.get("taxonomy_code", ""))
        if tc == isco:
            best_isco_score = 1.0
            break
        elif tc and tc[0] == isco[0]:
            best_isco_score = max(best_isco_score, 0.6)
        else:
            best_isco_score = max(best_isco_score, 0.1)

    boost = _skill_boost(skills, isco)
    score = best_isco_score * 0.55 + boost * 0.35

    # Zero-credential bonus
    if zero_credential and opp.get("accepts_zero_credential", True):
        score += 0.15

    # Language match bonus
    req_langs = [l.lower() for l in opp.get("required_languages", [])]
    prof_langs = [l.lower() for l in profile_languages]
    if req_langs and any(l in prof_langs for l in req_langs):
        score += 0.10

    # Multi-skill diversification
    score += 0.05 * min(len(skills) - 1, 2)

    return min(score, 1.0)


def compute_job_match(
    skills: list[dict[str, Any]],
    country_code: str,
    zero_credential: bool,
    profile_languages: list[str],
    opportunity_catalog: list[dict[str, Any]],
    city: str = "",
) -> dict[str, Any]:
    """
    Core M2 function. Returns a dict matching JobMatchSignal shape:
        {
          score: int,
          rationale: str,
          opportunity_count: int,
          matched_opportunities: list[dict],  # max 5
        }
    Plus a separate network_entry dict (top-1 opportunity).
    """
    if not opportunity_catalog or not skills:
        return _empty_match(country_code)

    scored: list[tuple[float, dict[str, Any]]] = []
    for opp in opportunity_catalog:
        s = _score_opportunity(opp, skills, zero_credential, profile_languages)
        scored.append((s, opp))

    # Filter and rank
    scored = [(s, o) for s, o in scored if s >= 0.35]
    scored.sort(key=lambda x: -x[0])
    top5 = scored[:5]

    if not top5:
        return _empty_match(country_code)

    # Build matched_opportunities list
    matched: list[dict[str, Any]] = []
    for s, opp in top5:
        entry = dict(opp)
        entry["match_score"] = round(s, 3)
        # Remove internal scoring keys
        entry.pop("accepts_zero_credential", None)
        entry.pop("required_languages", None)
        matched.append(entry)

    # Overall score: weighted mean of top-3
    top3_scores = [s for s, _ in top5[:3]]
    weights = [0.5, 0.3, 0.2][: len(top3_scores)]
    total_w = sum(weights)
    weighted_score = sum(s * w for s, w in zip(top3_scores, weights)) / total_w
    score_int = max(10, min(100, int(weighted_score * 100)))

    rationale = _build_rationale(matched, skills, score_int, country_code)

    # network_entry = top-1 opportunity coords
    top_opp = matched[0]
    network_entry = {
        "channel": top_opp["channel"],
        "lat": top_opp["lat"],
        "lng": top_opp["lng"],
        "label": top_opp["label"],
    }

    return {
        "job_match": {
            "score": score_int,
            "rationale": rationale,
            "opportunity_count": len(matched),
            "matched_opportunities": matched,
        },
        "network_entry": network_entry,
    }


def _build_rationale(
    matched: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    score: int,
    country_code: str,
) -> str:
    top = matched[0]["title"] if matched else "local opportunities"
    n = len(matched)
    skill_names = [sk.get("name", sk.get("label", "")) for sk in skills[:2]]
    skill_str = " + ".join(filter(None, skill_names))
    tier = (
        "high" if score >= 70
        else "moderate" if score >= 45
        else "early-stage"
    )
    return (
        f"{skill_str} profile matches {n} opportunit{'y' if n == 1 else 'ies'} "
        f"in the {country_code} labor market — best fit: {top}. "
        f"{tier.capitalize()} job-market alignment."
    )


def _empty_match(country_code: str) -> dict[str, Any]:
    defaults = {
        "GH": {"channel": "NBSSI informal-sector SME onboarding", "lat": 5.5502, "lng": -0.2174, "label": "Accra"},
        "AM": {"channel": "Sole-proprietor e-registration via e-gov.am", "lat": 40.1872, "lng": 44.5152, "label": "Yerevan"},
    }
    ne = defaults.get(country_code.upper(), defaults["GH"])
    return {
        "job_match": {
            "score": 15,
            "rationale": "Insufficient skill signals for precise job matching — complete your profile for better matches.",
            "opportunity_count": 0,
            "matched_opportunities": [],
        },
        "network_entry": ne,
    }
