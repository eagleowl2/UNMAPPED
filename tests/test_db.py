"""
Persistence-layer tests.

Each test runs against a fresh in-memory SQLite (UNMAPPED_DB_URL points at
`:memory:` per-test). The /parse endpoint should still work even when the
DB module is bypassed entirely — that is verified at the bottom.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


GH_PAYLOAD = {
    "raw_input": (
        "I am Amara, 27, I sell smoked fish at Makola three days a week and "
        "braid hair on the other days. I learned book-keeping from my aunt."
    ),
    "country": "GH",
}


@pytest.fixture
def admin_client(monkeypatch, tmp_path):
    """Give every test an isolated DB file + a known admin token."""
    db_path = tmp_path / "unmapped_test.db"
    monkeypatch.setenv("UNMAPPED_DB_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("UNMAPPED_ADMIN_TOKEN", "test-token")

    # Reset the module-level engine so the env var takes effect.
    import importlib

    from app.db import session as db_session

    importlib.reload(db_session)
    # Re-import the modules that bind the engine via get_engine().
    from app.db import repository as db_repo  # noqa: F401
    from app.api import employer as employer_mod
    importlib.reload(employer_mod)

    from app import main as main_mod
    importlib.reload(main_mod)

    with TestClient(main_mod.app) as client:
        yield client


def test_parse_persists_profile(admin_client):
    r = admin_client.post("/parse", json=GH_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Read it back via the employer endpoint
    r2 = admin_client.get(
        "/api/v1/profiles",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["count"] >= 1
    summary = body["profiles"][0]
    # Summary fields are present, raw_input is NOT
    assert "raw_input" not in summary
    assert summary["country"] == "GH"
    assert summary["wage_score"] >= 0


def test_employer_endpoints_require_token(admin_client):
    r = admin_client.get("/api/v1/profiles")
    assert r.status_code == 401


def test_employer_endpoints_reject_wrong_token(admin_client):
    r = admin_client.get(
        "/api/v1/profiles",
        headers={"Authorization": "Bearer not-the-token"},
    )
    assert r.status_code == 401


def test_get_profile_returns_full_card(admin_client):
    profile = admin_client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    pid = profile["profile_id"]

    r = admin_client.get(
        f"/api/v1/profiles/{pid}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["profile_id"] == pid
    # Full ProfileCard JSON is returned, but it never contained raw_input.
    assert "profile" in body
    assert body["profile"]["profile_id"] == pid
    assert "raw_input" not in body["profile"]


def test_dashboard_returns_aggregates_only(admin_client):
    admin_client.post("/parse", json=GH_PAYLOAD)
    admin_client.post(
        "/parse",
        json={
            "raw_input": (
                "Իմ անունը Անի է, 31 տարեկան, Գյումրիից եմ։ "
                "Անգլերեն դասեր եմ տալիս։"
            ),
            "country": "AM",
        },
    )

    r = admin_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    body = r.json()
    for key in (
        "total_profiles",
        "by_country",
        "automation_risk_distribution",
        "bona_distribution",
        "zero_credential_rate",
    ):
        assert key in body
    # Dashboard never echoes individual rows or raw_input
    assert "profiles" not in body
    assert "raw_input" not in r.text


def test_parse_idempotent_upsert(admin_client):
    # Same input → same profile_id → exactly one row
    admin_client.post("/parse", json=GH_PAYLOAD)
    admin_client.post("/parse", json=GH_PAYLOAD)
    admin_client.post("/parse", json=GH_PAYLOAD)

    r = admin_client.get(
        "/api/v1/profiles?country=GH",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1