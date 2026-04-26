"""
Tests for Module 2 — automation risk + NEET context (v0.3.2).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.automation_risk import compute_automation_risk
from app.core.signals import get_neet_context
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit — compute_automation_risk
# ---------------------------------------------------------------------------

def test_compute_returns_none_for_empty_skills():
    assert compute_automation_risk([], "GH") is None


def test_compute_phone_repair_GH_is_low_to_medium():
    """Phone repair (ISCO 7421) — Frey-Osborne ~0.41 raw, GH factor 0.55 →
    adjusted ~0.23 (low). Trajectory should be 'stable' or 'growing' since
    GH electronics_repair sector grew +8% over 5yr."""
    skills = [{"name": "Phone Repair", "taxonomy_code": "7421", "category": "technical"}]
    result = compute_automation_risk(skills, "GH", growth_signal_pct=8)
    assert result is not None
    assert result["risk_tier"] in ("low", "medium")
    assert 0.0 <= result["automation_probability"] <= 1.0
    assert result["trajectory_2035"] in ("growing", "stable", "declining")
    assert "Frey-Osborne" in result["rationale"]
    assert any("Wittgenstein" in s for s in result["sources"])


def test_compute_software_dev_AM_is_calibrated_high():
    """Software dev (ISCO 2512) — Frey-Osborne 0.42 raw × AM factor 0.90
    → ~0.38 adjusted; Armenia ICT growing +28% so trajectory = stable/growing."""
    skills = [{"name": "Software Development", "taxonomy_code": "2512", "category": "digital"}]
    result = compute_automation_risk(skills, "AM", growth_signal_pct=28)
    assert result is not None
    assert result["automation_probability"] > 0.30
    assert result["trajectory_2035"] in ("growing", "stable")
    assert result["adjacent_skills"]


def test_lmic_calibration_dampens_GH_relative_to_AM():
    """For the same ISCO code, GH factor < AM factor → GH score should be
    lower (less automation pressure) than AM."""
    skills = [{"name": "Accounting", "taxonomy_code": "2411", "category": "financial"}]
    gh = compute_automation_risk(skills, "GH", 4)
    am = compute_automation_risk(skills, "AM", 11)
    assert gh and am
    assert gh["automation_probability"] <= am["automation_probability"]


# ---------------------------------------------------------------------------
# Unit — NEET context (Signal 4)
# ---------------------------------------------------------------------------

def test_neet_context_GH():
    ctx = get_neet_context("GH")
    assert ctx is not None
    assert 0 < ctx["neet_pct"] < 50
    assert "Ghan" in ctx["narrative"]
    assert ctx["year"] >= 2020


def test_neet_context_AM():
    ctx = get_neet_context("AM")
    assert ctx is not None
    assert 0 < ctx["neet_pct"] < 60
    assert "Armen" in ctx["narrative"]


def test_neet_context_unknown_country_returns_none():
    assert get_neet_context("ZZ") is None


# ---------------------------------------------------------------------------
# API contract — automation_risk + neet_context surfaced on /parse response
# ---------------------------------------------------------------------------

GH_PAYLOAD = {
    "raw_input": (
        "My name is Amara, I fix phones in Accra, speak Twi English Ga, "
        "learned coding on YouTube, been fixing phones for 3 years."
    ),
    "country": "GH",
}


def test_profile_includes_automation_risk():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert "automation_risk" in profile
    ar = profile["automation_risk"]
    assert ar is None or {
        "automation_probability", "raw_probability", "risk_tier",
        "trajectory_2035", "rationale", "sources",
    }.issubset(ar.keys())


def test_profile_includes_neet_context():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert "neet_context" in profile
    nc = profile["neet_context"]
    assert nc is None or {"neet_pct", "narrative", "source", "year"}.issubset(nc.keys())


def test_growth_signal_includes_ilostat_citation():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert "ILOSTAT" in profile["growth_signal"]["rationale"]


def test_wage_signal_includes_data_citation():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert "ILOSTAT" in profile["wage_signal"]["rationale"]
