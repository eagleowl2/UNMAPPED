"""
Tests for Evidence Parser — the core SSE pipeline.
Uses Amara story as canonical test vector.
"""
import pytest
from app.core.parser import EvidenceParser

AMARA_INPUT = (
    "My name is Amara, I fix phones in Accra, speak Twi English Ga, "
    "learned coding on YouTube, been fixing phones for 3 years, "
    "I have about 20 customers a week"
)


@pytest.fixture(scope="module")
def parser():
    return EvidenceParser(country_code="GH", context_tag="urban_informal")


@pytest.fixture(scope="module")
def amara_result(parser):
    return parser.parse(AMARA_INPUT)


class TestUserExtraction:
    def test_user_entity_present(self, amara_result):
        assert "user" in amara_result
        user = amara_result["user"]
        assert user["user_id"].startswith("usr_")

    def test_name_extracted(self, amara_result):
        assert amara_result["user"]["display_name"] == "Amara"

    def test_location_extracted(self, amara_result):
        loc = amara_result["user"]["location"]
        assert loc["country_code"] == "GH"
        assert loc.get("city", "").lower() in ("accra", "")

    def test_languages_detected(self, amara_result):
        langs = amara_result["user"]["languages"]
        assert len(langs) >= 1
        # Twi should be detected
        assert any("ak" in l or "GH" in l or l == "ak-GH" for l in langs)

    def test_zero_credential_flagged(self, amara_result):
        # "learned coding on YouTube" triggers zero-credential
        assert amara_result["user"]["zero_credential"] is True

    def test_source_text_hash(self, amara_result):
        h = amara_result["user"]["source_text_hash"]
        assert len(h) == 64  # SHA-256 hex


class TestSkillExtraction:
    def test_skills_list_present(self, amara_result):
        assert "skills" in amara_result
        assert len(amara_result["skills"]) >= 1

    def test_phone_repair_detected(self, amara_result):
        labels = [s["label"] for s in amara_result["skills"]]
        assert any("phone" in l.lower() or "repair" in l.lower() for l in labels)

    def test_coding_detected(self, amara_result):
        labels = [s["label"] for s in amara_result["skills"]]
        assert any("software" in l.lower() or "coding" in l.lower() or "develop" in l.lower() for l in labels)

    def test_skill_ids_unique(self, amara_result):
        ids = [s["skill_id"] for s in amara_result["skills"]]
        assert len(ids) == len(set(ids))

    def test_source_phrases_populated(self, amara_result):
        for skill in amara_result["skills"]:
            assert len(skill["source_phrases"]) >= 1


class TestVSSList:
    def test_vss_list_present(self, amara_result):
        assert "vss_list" in amara_result
        assert len(amara_result["vss_list"]) >= 1

    def test_vss_ids_unique(self, amara_result):
        ids = [v["vss_id"] for v in amara_result["vss_list"]]
        assert len(ids) == len(set(ids))

    def test_vss_structure(self, amara_result):
        for vss in amara_result["vss_list"]:
            assert vss["vss_id"].startswith("vss_")
            assert "user" in vss
            assert "skill" in vss
            assert "evidence_chain" in vss
            assert "confidence" in vss
            assert "taxonomy_crosswalk" in vss

    def test_confidence_score_in_range(self, amara_result):
        for vss in amara_result["vss_list"]:
            score = vss["confidence"]["score"]
            assert 0.0 <= score <= 1.0

    def test_confidence_has_tier(self, amara_result):
        valid_tiers = {"emerging", "developing", "established", "expert"}
        for vss in amara_result["vss_list"]:
            assert vss["confidence"]["tier"] in valid_tiers

    def test_phone_repair_taxonomy_isco(self, amara_result):
        phone_vss = [
            v for v in amara_result["vss_list"]
            if "phone" in v["skill"]["label"].lower() or "repair" in v["skill"]["label"].lower()
        ]
        assert len(phone_vss) >= 1
        assert phone_vss[0]["taxonomy_crosswalk"]["primary"]["framework"] == "ISCO-08"
        assert phone_vss[0]["taxonomy_crosswalk"]["primary"]["code"] == "7421"

    def test_evidence_chain_non_empty(self, amara_result):
        for vss in amara_result["vss_list"]:
            assert len(vss["evidence_chain"]) >= 1

    def test_experience_boosts_confidence(self, parser):
        no_exp = parser.parse("I fix phones")
        with_exp = parser.parse("I fix phones, 5 years experience, 50 customers per week")
        phone_no = next((v for v in no_exp["vss_list"] if "7421" in str(v["taxonomy_crosswalk"])), None)
        phone_yes = next((v for v in with_exp["vss_list"] if "7421" in str(v["taxonomy_crosswalk"])), None)
        if phone_no and phone_yes:
            assert phone_yes["confidence"]["score"] >= phone_no["confidence"]["score"]


class TestHumanLayer:
    def test_human_layer_present(self, amara_result):
        assert "human_layer" in amara_result
        hl = amara_result["human_layer"]
        assert hl["hl_id"].startswith("hl_")

    def test_profile_card_present(self, amara_result):
        card = amara_result["human_layer"]["profile_card"]
        assert card["display_name"] == "Amara"
        assert len(card["skills_summary"]) >= 1
        assert "headline" in card

    def test_sms_summary_max_160(self, amara_result):
        sms = amara_result["human_layer"]["sms_summary"]
        assert sms["char_count"] <= 160
        assert len(sms["text"]) <= 160

    def test_ussd_tree_has_root(self, amara_result):
        ussd = amara_result["human_layer"]["ussd_tree"]
        assert "root" in ussd
        assert "text" in ussd["root"]
        assert len(ussd["root"]["text"]) <= 182

    def test_zero_credential_badge(self, amara_result):
        card = amara_result["human_layer"]["profile_card"]
        assert card["zero_credential_badge"] is True

    def test_rendered_html_contains_name(self, amara_result):
        html = amara_result["human_layer"]["profile_card"].get("rendered_html", "")
        assert "Amara" in html


class TestEdgeCases:
    def test_minimal_input(self, parser):
        result = parser.parse("I sew clothes")
        assert len(result["skills"]) >= 1

    def test_no_name_input(self, parser):
        result = parser.parse("fixing phones for 2 years in Kumasi")
        assert result["user"]["display_name"] is None or isinstance(result["user"]["display_name"], str)

    def test_multilingual_hint(self, parser):
        result = parser.parse("Mena din de Kofi, mede phone repair na Accra, Twi ne English na kasa")
        # Should not crash even for non-English text
        assert "user" in result

    def test_multiple_skills(self, parser):
        result = parser.parse(
            "I am a teacher and I also do tailoring and phone repair in Lagos"
        )
        assert len(result["skills"]) >= 2
