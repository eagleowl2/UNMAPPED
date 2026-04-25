"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AMARA_PAYLOAD = {
    "text": "My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube",
    "country_code": "GH",
    "context_tag": "urban_informal",
}


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "endpoints" in data


def test_parse_amara_success():
    resp = client.post("/api/v1/parse", json=AMARA_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "user" in data
    assert "vss_list" in data
    assert "human_layer" in data
    assert data["meta"]["skills_detected"] >= 1


def test_parse_returns_correct_name():
    resp = client.post("/api/v1/parse", json=AMARA_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["user"]["display_name"] == "Amara"


def test_parse_sms_within_limit():
    resp = client.post("/api/v1/parse", json=AMARA_PAYLOAD)
    assert resp.status_code == 200
    sms = resp.json()["human_layer"]["sms_summary"]
    assert sms["char_count"] <= 160


def test_parse_vss_structure():
    resp = client.post("/api/v1/parse", json=AMARA_PAYLOAD)
    data = resp.json()
    for vss in data["vss_list"]:
        assert vss["vss_id"].startswith("vss_")
        assert "confidence" in vss
        assert "taxonomy_crosswalk" in vss


def test_parse_empty_text_422():
    resp = client.post("/api/v1/parse", json={"text": "", "country_code": "GH"})
    assert resp.status_code == 422


def test_parse_short_text_422():
    resp = client.post("/api/v1/parse", json={"text": "hi", "country_code": "GH"})
    assert resp.status_code == 422


def test_parse_unknown_country_404():
    resp = client.post("/api/v1/parse", json={
        "text": "I fix phones and teach coding",
        "country_code": "ZZ",
        "context_tag": "urban_informal",
    })
    assert resp.status_code == 404


def test_generate_vss_endpoint():
    # First parse
    parse_resp = client.post("/api/v1/parse", json=AMARA_PAYLOAD)
    assert parse_resp.status_code == 200
    parsed = parse_resp.json()

    # Then regenerate VSS
    vss_resp = client.post("/api/v1/generate_vss", json={
        "user": parsed["user"],
        "skills": parsed["skills"],
        "country_code": "GH",
        "context_tag": "urban_informal",
    })
    assert vss_resp.status_code == 200
    data = vss_resp.json()
    assert data["ok"] is True
    assert len(data["vss_list"]) >= 1


def test_parse_lowercase_country_code():
    payload = {**AMARA_PAYLOAD, "country_code": "gh"}
    resp = client.post("/api/v1/parse", json=payload)
    assert resp.status_code == 200


def test_openapi_docs_available():
    resp = client.get("/docs")
    assert resp.status_code == 200
