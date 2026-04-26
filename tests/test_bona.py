"""
BONA forensic-audit tests.

Two layers:
  • Direct compute_bona() unit tests with hand-rolled inputs.
  • Contract tests through /parse — the canonical Amara/Ani vectors must
    surface a bona block with the documented shape.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.bona import compute_bona
from app.main import app

client = TestClient(app)


GH_PAYLOAD = {
    "raw_input": (
        "I am Amara, 27, I sell smoked fish at Makola three days a week and "
        "braid hair on the other days. I learned book-keeping from my aunt "
        "and I keep my own ledger in a notebook."
    ),
    "country": "GH",
}


# ---------------------------------------------------------------------------
# Pure compute_bona() unit tests
# ---------------------------------------------------------------------------

def _opp(**overrides):
    base = {
        "title": "Mobile Repair SME — NBSSI",
        "employer_type": "government",
        "channel": "NBSSI mobile-device repair SME registry",
        "lat": 5.55,
        "lng": -0.21,
        "label": "Accra Central",
        "wage_range": "GHS 35–60 / day",
        "isco_code": "7421",
        "formalization_path": "1. Register at nbssi.gov.gh  2. Open MoMo SME",
        "accepts_zero_credential": True,
        "required_languages": ["en"],
    }
    base.update(overrides)
    return base


GH_PROFILE = {
    "country_code": "GH",
    "languages": {"primary": "en-GH", "supported": ["en-GH", "ak-GH", "gaa"]},
    "informal_economy": {"gdp_share_pct": 68.7},
}


def test_bona_shape_is_complete():
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["en-GH"],
        zero_credential=False,
        matched_opportunities=[_opp(), _opp(channel="MTN MoMo agent")],
    )
    for key in (
        "overall_score",
        "overall_tier",
        "network_capture",
        "ghost_listings",
        "programme_leakage",
        "flags",
        "rationale",
        "sources",
    ):
        assert key in out, f"missing {key} in BONA report"
    assert 0.0 <= out["overall_score"] <= 1.0
    assert out["overall_tier"] in {"low", "medium", "high"}


def test_bona_high_capture_when_single_channel():
    """All matches share one channel → capture risk should be high."""
    same = "MTN MoMo agent registry"
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["en-GH"],
        zero_credential=False,
        matched_opportunities=[_opp(channel=same), _opp(channel=same), _opp(channel=same)],
    )
    assert out["network_capture"]["tier"] == "high"
    assert any("Single channel" in f for f in out["flags"])


def test_bona_ghost_listing_flagged_when_critical_fields_missing():
    """An opportunity without wage_range + formalization_path is a ghost."""
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["en-GH"],
        zero_credential=False,
        matched_opportunities=[
            _opp(),  # healthy
            _opp(wage_range="", formalization_path="", lat=0.0, lng=0.0),  # ghost
        ],
    )
    assert out["ghost_listings"]["ghost_count"] >= 1
    assert any("lacks" in f for f in out["flags"])


def test_bona_leakage_high_when_language_mismatch():
    """User speaks French; programme supports en/ak/gaa → leakage flag."""
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["fr-FR"],
        zero_credential=False,
        matched_opportunities=[_opp()],
    )
    assert out["programme_leakage"]["score"] >= 0.5
    assert any("not in supported set" in f for f in out["flags"])


def test_bona_no_opportunities_falls_back_gracefully():
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["en-GH"],
        zero_credential=False,
        matched_opportunities=[],
    )
    assert out["ghost_listings"]["score"] == 0.0
    # No opportunities → no ghost_count, but capture should still report something
    assert 0.0 <= out["overall_score"] <= 1.0


def test_bona_zero_credential_leakage_when_few_accept():
    out = compute_bona(
        country_code="GH",
        country_profile=GH_PROFILE,
        profile_languages=["en-GH"],
        zero_credential=True,
        matched_opportunities=[
            _opp(accepts_zero_credential=False, channel="formal-only-1"),
            _opp(accepts_zero_credential=False, channel="formal-only-2"),
        ],
    )
    assert out["programme_leakage"]["score"] >= 0.3
    assert any("zero-credential" in f.lower() for f in out["flags"])


# ---------------------------------------------------------------------------
# Contract test through /parse
# ---------------------------------------------------------------------------

def test_parse_includes_bona_block():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert "bona" in profile, "v0.4 ProfileCard must include bona"
    bona = profile["bona"]
    assert bona["overall_tier"] in {"low", "medium", "high"}
    assert isinstance(bona["flags"], list)
    assert "Protocol §6.7" in " ".join(bona.get("sources", [])) or any(
        "BONA" in s for s in bona.get("sources", [])
    )


def test_parse_bona_subscores_in_range():
    bona = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["bona"]
    for sub in ("network_capture", "ghost_listings", "programme_leakage"):
        s = bona[sub]
        assert 0.0 <= s["score"] <= 1.0
        assert s["tier"] in {"low", "medium", "high"}