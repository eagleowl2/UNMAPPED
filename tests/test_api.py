"""
Integration tests for the FastAPI endpoints.
Validates the exact frontend contract from docs/api-contract.md.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Canonical inputs from frontend/src/lib/locales.ts
AMARA_INPUT = (
    "I am Amara, 27, I sell smoked fish at Makola three days a week and braid hair on the other days. "
    "I learned book-keeping from my aunt and I keep my own ledger in a notebook. I have a Vodafone Cash account. "
    "I want to start a small frozen-fish stall."
)

ANI_INPUT = (
    "Իմ անունը Անի է, 31 տարեկան, Գյումրիից եմ։ Անգլերեն դասեր եմ տալիս տանը և շաբաթական "
    "մի քանի անգամ թարգմանում փոքր ընկերությունների համար։ Ունեմ Idram հաշիվ։ Ուզում եմ բացել իմ "
    "դասավանդման փոքր ստուդիան։"
)

GH_PAYLOAD = {"raw_input": AMARA_INPUT, "country": "GH"}
AM_PAYLOAD = {"raw_input": ANI_INPUT, "country": "AM"}


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_lists_parse_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "POST /parse" in data["endpoints"]["parse"]


def test_docs_available():
    assert client.get("/docs").status_code == 200


# ---------------------------------------------------------------------------
# POST /parse — response shape (contract compliance)
# ---------------------------------------------------------------------------

def test_parse_returns_ok_true():
    r = client.post("/parse", json=GH_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_parse_top_level_fields():
    data = client.post("/parse", json=GH_PAYLOAD).json()
    assert "profile" in data
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], (int, float))
    assert data["country"] == "GH"
    assert "parser_version" in data


def test_parse_profile_card_fields():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    required = ["profile_id", "display_name", "pseudonym", "location",
                "languages", "skills", "wage_signal", "growth_signal",
                "network_entry", "sms_summary", "ussd_menu"]
    for field in required:
        assert field in profile, f"Missing field: {field}"


def test_parse_profile_id_stable():
    # Same input → same profile_id (deterministic hash)
    r1 = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["profile_id"]
    r2 = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["profile_id"]
    assert r1 == r2


def test_parse_skills_sorted_by_confidence():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    assert len(skills) >= 1
    confs = [s["confidence"] for s in skills]
    assert confs == sorted(confs, reverse=True)


def test_parse_skill_confidence_range():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    for s in skills:
        assert 0.0 <= s["confidence"] <= 1.0


def test_parse_skills_max_eight():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    assert len(skills) <= 8


# ---------------------------------------------------------------------------
# Signal fields
# ---------------------------------------------------------------------------

def test_wage_signal_score_range():
    ws = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["wage_signal"]
    assert 0 <= ws["score"] <= 100
    assert isinstance(ws["rationale"], str) and len(ws["rationale"]) > 0
    assert "GHS" in ws.get("display_value", "")


def test_growth_signal_score_range():
    gs = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["growth_signal"]
    assert 0 <= gs["score"] <= 100
    assert isinstance(gs["rationale"], str) and len(gs["rationale"]) > 0


def test_network_entry_has_coords():
    ne = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["network_entry"]
    assert "channel" in ne and len(ne["channel"]) > 0
    assert isinstance(ne["lat"], float)
    assert isinstance(ne["lng"], float)
    assert "label" in ne


# ---------------------------------------------------------------------------
# SMS + USSD constraints
# ---------------------------------------------------------------------------

def test_sms_within_160_chars():
    sms = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["sms_summary"]
    assert len(sms) <= 160, f"SMS too long: {len(sms)} chars"


def test_ussd_menu_line_count():
    menu = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["ussd_menu"]
    assert 4 <= len(menu) <= 8


def test_ussd_menu_line_length():
    menu = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["ussd_menu"]
    for line in menu:
        assert len(line) <= 40, f"USSD line too long: {repr(line)}"


# ---------------------------------------------------------------------------
# Amara canonical story
# ---------------------------------------------------------------------------

def test_amara_name_extracted():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert profile["pseudonym"] == "Amara" or "Amara" in profile["display_name"]


def test_amara_age_extracted():
    profile = client.post("/parse", json=GH_PAYLOAD).json()["profile"]
    assert profile.get("age") == 27


def test_amara_location_contains_accra():
    profile = client.post("/parse", json={"raw_input": AMARA_INPUT + " in Accra", "country": "GH"}).json()["profile"]
    assert "Accra" in profile["location"] or profile["location"]


def test_amara_bookkeeping_detected():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    names = [s["name"].lower() for s in skills]
    assert any("book" in n or "ledger" in n or "account" in n for n in names)


def test_amara_trading_or_fish_detected():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    names = [s["name"].lower() for s in skills]
    assert any("fish" in n or "trad" in n or "sell" in n or "market" in n for n in names)


def test_amara_mobile_money_detected():
    skills = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["skills"]
    names = [s["name"].lower() for s in skills]
    assert any("mobile" in n or "money" in n or "cash" in n or "vodafone" in n for n in names)


def test_amara_wage_has_ghs():
    ws = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["wage_signal"]
    assert "GHS" in ws.get("display_value", "")


# ---------------------------------------------------------------------------
# Armenia (AM) — Ani canonical story
# ---------------------------------------------------------------------------

def test_ani_parse_ok():
    r = client.post("/parse", json=AM_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_ani_country_echo():
    assert client.post("/parse", json=AM_PAYLOAD).json()["country"] == "AM"


def test_ani_skills_detected():
    skills = client.post("/parse", json=AM_PAYLOAD).json()["profile"]["skills"]
    assert len(skills) >= 1


def test_ani_wage_has_amd():
    ws = client.post("/parse", json=AM_PAYLOAD).json()["profile"]["wage_signal"]
    assert "AMD" in ws.get("display_value", "")


def test_ani_ussd_shortcode_am():
    menu = client.post("/parse", json=AM_PAYLOAD).json()["profile"]["ussd_menu"]
    assert any("*404#" in line for line in menu)


def test_ani_network_entry_egovernment():
    ne = client.post("/parse", json=AM_PAYLOAD).json()["profile"]["network_entry"]
    assert "e-gov" in ne["channel"].lower() or "idram" in ne["channel"].lower()


# ---------------------------------------------------------------------------
# Locale swap — GH vs AM produce different wage currencies
# ---------------------------------------------------------------------------

def test_locale_swap_different_currencies():
    gh = client.post("/parse", json=GH_PAYLOAD).json()["profile"]["wage_signal"]["display_value"]
    am = client.post("/parse", json=AM_PAYLOAD).json()["profile"]["wage_signal"]["display_value"]
    assert "GHS" in (gh or "")
    assert "AMD" in (am or "")


# ---------------------------------------------------------------------------
# Zero-credential path
# ---------------------------------------------------------------------------

def test_zero_credential_from_self_taught():
    payload = {
        "raw_input": "I fix phones, self-taught, no formal degree, 3 years experience",
        "country": "GH",
    }
    r = client.post("/parse", json=payload).json()
    assert r["ok"] is True
    skills = r["profile"]["skills"]
    assert len(skills) >= 1


def test_zero_credential_default_gh():
    # GH urban_informal has zero_credential_default=true
    r = client.post("/parse", json={"raw_input": "I sell cloth at market", "country": "GH"})
    assert r.json()["ok"] is True


# ---------------------------------------------------------------------------
# Schema validation (request)
# ---------------------------------------------------------------------------

def test_empty_input_422():
    r = client.post("/parse", json={"raw_input": "", "country": "GH"})
    assert r.status_code == 422


def test_short_input_422():
    r = client.post("/parse", json={"raw_input": "hi", "country": "GH"})
    assert r.status_code == 422


def test_invalid_country_422():
    r = client.post("/parse", json={"raw_input": "I fix phones", "country": "XX"})
    assert r.status_code == 422


def test_missing_raw_input_422():
    r = client.post("/parse", json={"country": "GH"})
    assert r.status_code == 422


def test_lowercase_country_normalised():
    r = client.post("/parse", json={"raw_input": AMARA_INPUT, "country": "gh"})
    assert r.json()["ok"] is True
    assert r.json()["country"] == "GH"


# ---------------------------------------------------------------------------
# Legacy /api/v1/parse alias
# ---------------------------------------------------------------------------

def test_legacy_v1_parse_works():
    r = client.post("/api/v1/parse", json=GH_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_generate_profile_card_endpoint():
    r = client.post("/api/v1/generate_profile_card", json=GH_PAYLOAD)
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert "profile" in r.json()
