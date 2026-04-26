"""
BONA — Bidirectional Opaque Network Auditor (v0.1, hackathon scope).

Cross-cutting forensic layer specified by UNMAPPED Protocol v0.2 §6.7. Until
v0.4 the only BONA surface area was the youth-side `network_entry` map stub.
This module adds a deterministic, heuristic implementation of the three
auditor scores so the protocol promise is met end-to-end:

    network_capture_risk   — does ONE intermediary dominate the entry path?
    ghost_listing_risk     — do the matched opportunities look real?
    programme_leakage_score — gap between formal eligibility and reach
                              (zero-credential reach + language coverage).

Output is intentionally cheap to compute (rule-based, no external calls) so
it can run inline inside /parse without breaking the latency budget. Every
flag carries a short plain-language string so the policymaker view can show
it verbatim.

Inputs all come pre-extracted from EvidenceParser.parse_for_profile().
Output shape mirrors the BonaReport Pydantic model in app/models/schemas.py.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Optional


_ZERO_CRED_KEYWORDS = (
    "zero-credential",
    "zero_credential",
    "no credentials",
    "informal",
    "community navigator",
    "peer attestation",
    "mobile money",
    "MoMo",
    "Idram",
)


def _tier_for(score: float) -> str:
    """3-tier label used for every BONA sub-score."""
    if score < 0.34:
        return "low"
    if score < 0.66:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Sub-score 1 — Network capture risk
# ---------------------------------------------------------------------------

def _score_network_capture(
    matched_opportunities: list[dict[str, Any]],
    network_entry: Optional[dict[str, Any]],
) -> tuple[float, list[str]]:
    """How concentrated is the youth's path into the formal economy?

    A single-channel funnel ('every match routes through MTN MoMo') is a
    capture warning even if the channel itself is benign — it means the
    youth has zero exit options if that gatekeeper changes terms.
    """
    flags: list[str] = []
    if not matched_opportunities:
        return 0.5, ["No matched opportunities to audit — network entry is the only signal."]

    # Channel concentration (Herfindahl-style: 0..1, higher = more captured)
    channels = [str(opp.get("channel", "")).strip() for opp in matched_opportunities]
    counts = Counter(c for c in channels if c)
    n = sum(counts.values())
    if n == 0:
        return 0.5, ["Opportunities have no channel labels — cannot audit network capture."]

    # Top-channel share is the strongest single signal.
    top_share = max(counts.values()) / n
    distinct_channels = len(counts)

    # Employer-type diversity dampens capture risk.
    employer_types = {str(o.get("employer_type", "")) for o in matched_opportunities}
    employer_diversity = len(employer_types - {""})

    raw = top_share
    if distinct_channels == 1:
        raw = max(raw, 0.85)
        flags.append(f"Single channel handles {n}/{n} opportunities — high capture risk.")
    elif distinct_channels == 2 and top_share > 0.7:
        raw = max(raw, 0.7)
        flags.append("Two channels but one dominates >70% of matches.")

    if employer_diversity <= 1:
        raw = min(1.0, raw + 0.1)
        flags.append("All matches share a single employer type.")
    elif employer_diversity >= 3:
        raw = max(0.0, raw - 0.1)

    # Network entry pin same as the dominant channel? That's expected,
    # but worth surfacing transparently.
    if network_entry and counts:
        ne_channel = str(network_entry.get("channel", ""))
        top_channel, top_n = counts.most_common(1)[0]
        if ne_channel == top_channel and top_n >= n * 0.5:
            flags.append(
                f"Primary network entry '{top_channel[:48]}…' overlaps the dominant match channel — "
                f"diversify before formal registration."
            )

    return min(1.0, max(0.0, raw)), flags


# ---------------------------------------------------------------------------
# Sub-score 2 — Ghost listing risk
# ---------------------------------------------------------------------------

def _score_ghost_listings(
    matched_opportunities: list[dict[str, Any]],
) -> tuple[float, list[str], int]:
    """Per-opportunity sanity check.

    A 'ghost listing' is one that *looks* like a real opening but lacks the
    minimum signature of a verifiable opportunity: wage range, formalization
    path, employer type. Each missing field bumps the listing's ghost
    probability. The aggregate is a count-weighted mean.
    """
    if not matched_opportunities:
        return 0.0, [], 0

    flags: list[str] = []
    ghost_count = 0
    per_opp_scores: list[float] = []

    for opp in matched_opportunities:
        score = 0.0
        missing: list[str] = []

        wage = str(opp.get("wage_range", "")).strip()
        if not wage:
            score += 0.35
            missing.append("wage_range")
        elif not any(ch.isdigit() for ch in wage):
            score += 0.20
            missing.append("wage_range[no digits]")

        path = str(opp.get("formalization_path", "")).strip()
        if not path:
            score += 0.30
            missing.append("formalization_path")
        elif len(path) < 20:
            score += 0.15
            missing.append("formalization_path[too short]")

        if not str(opp.get("employer_type", "")).strip():
            score += 0.15
            missing.append("employer_type")

        if not str(opp.get("isco_code", "")).strip():
            score += 0.10
            missing.append("isco_code")

        # Coordinate sanity — (0,0) is suspicious but acceptable as 'unknown'.
        lat = float(opp.get("lat", 0.0) or 0.0)
        lng = float(opp.get("lng", 0.0) or 0.0)
        if lat == 0.0 and lng == 0.0:
            score += 0.10
            missing.append("coordinates")

        score = min(1.0, score)
        per_opp_scores.append(score)
        if score >= 0.5:
            ghost_count += 1
            title = str(opp.get("title", "untitled"))[:40]
            flags.append(f"Listing '{title}' lacks {', '.join(missing[:3])}.")

    aggregate = sum(per_opp_scores) / len(per_opp_scores) if per_opp_scores else 0.0
    return aggregate, flags, ghost_count


# ---------------------------------------------------------------------------
# Sub-score 3 — Programme leakage
# ---------------------------------------------------------------------------

def _score_programme_leakage(
    profile_languages: list[str],
    country_profile: dict[str, Any],
    zero_credential: bool,
    matched_opportunities: list[dict[str, Any]],
) -> tuple[float, list[str]]:
    """How much of the programme's stated reach actually lands on this user?

    Heuristic: leakage is high when the user's languages are NOT in the
    config-listed supported set, OR when zero-credential users have nowhere
    to go in the matched opportunities. Both are visible failure modes the
    brief explicitly calls out.
    """
    flags: list[str] = []
    leakage = 0.0

    # 1. Language coverage
    languages_cfg = country_profile.get("languages", {}) or {}
    supported = {str(l).lower() for l in languages_cfg.get("supported", [])}
    if profile_languages:
        prof = {str(l).lower() for l in profile_languages}
        # Any language match? (compare ISO root, e.g. 'en' against 'en-GH')
        prof_roots = {p.split("-")[0] for p in prof}
        sup_roots = {s.split("-")[0] for s in supported}
        if not (prof_roots & sup_roots):
            leakage += 0.5
            flags.append(
                f"User languages {sorted(prof_roots)} not in supported set {sorted(sup_roots)} — "
                f"programme delivery channels may not reach this profile."
            )
    else:
        leakage += 0.15
        flags.append("No languages detected — assume programme delivery is monolingual default.")

    # 2. Zero-credential reach
    if zero_credential:
        accepting = [o for o in matched_opportunities if o.get("accepts_zero_credential", True)]
        if not matched_opportunities:
            leakage += 0.25
            flags.append("Zero-credential profile but zero matched opportunities — full leakage.")
        else:
            share = len(accepting) / len(matched_opportunities)
            if share < 0.5:
                leakage += 0.30
                flags.append(
                    f"Only {len(accepting)}/{len(matched_opportunities)} matched opportunities "
                    f"accept zero-credential entrants."
                )
            elif share < 1.0:
                leakage += 0.10

    # 3. Informal-economy share signal — high informal share + few opportunities
    #    in the catalog means a large unreached cohort.
    informal = country_profile.get("informal_economy", {}) or {}
    gdp_share = float(informal.get("gdp_share_pct") or 0.0)
    if gdp_share >= 50 and len(matched_opportunities) < 3:
        leakage += 0.15
        flags.append(
            f"Informal economy is {gdp_share:.0f}% of GDP but only "
            f"{len(matched_opportunities)} opportunities surfaced for this profile."
        )

    return min(1.0, max(0.0, leakage)), flags


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_bona(
    country_code: str,
    country_profile: dict[str, Any],
    profile_languages: list[str],
    zero_credential: bool,
    matched_opportunities: list[dict[str, Any]],
    network_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compute the full BONA report for a single profile.

    All inputs are already non-PII (channel names, flags, language codes).
    No raw_input is referenced — BONA never sees the user's free-text story.
    """
    capture_score, capture_flags = _score_network_capture(matched_opportunities, network_entry)
    ghost_score, ghost_flags, ghost_count = _score_ghost_listings(matched_opportunities)
    leakage_score, leakage_flags = _score_programme_leakage(
        profile_languages, country_profile, zero_credential, matched_opportunities
    )

    # Overall = mean of three sub-scores. Higher = more concerning.
    overall = (capture_score + ghost_score + leakage_score) / 3.0

    flags: list[str] = []
    flags.extend(capture_flags)
    flags.extend(ghost_flags)
    flags.extend(leakage_flags)

    # Cap displayed flags to keep the panel scannable.
    flags = flags[:8]

    return {
        "overall_score": round(overall, 3),
        "overall_tier": _tier_for(overall),
        "network_capture": {
            "score": round(capture_score, 3),
            "tier": _tier_for(capture_score),
        },
        "ghost_listings": {
            "score": round(ghost_score, 3),
            "tier": _tier_for(ghost_score),
            "ghost_count": ghost_count,
        },
        "programme_leakage": {
            "score": round(leakage_score, 3),
            "tier": _tier_for(leakage_score),
        },
        "flags": flags,
        "rationale": _build_rationale(
            country_code, capture_score, ghost_score, leakage_score, ghost_count
        ),
        "sources": [
            "UNMAPPED Protocol v0.2 §6.7 (BONA spec)",
            f"Country profile: {country_code}",
            "Matched opportunity catalog",
        ],
    }


def _build_rationale(
    country_code: str,
    capture: float,
    ghost: float,
    leakage: float,
    ghost_count: int,
) -> str:
    parts = [
        f"BONA audit for {country_code}:",
        f"capture {int(capture * 100)}%,",
        f"ghost-listing {int(ghost * 100)}% ({ghost_count} flagged),",
        f"leakage {int(leakage * 100)}%.",
    ]
    return " ".join(parts)