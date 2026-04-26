"""
Unit tests for EvidenceParser — including Amara (GH) and Ani (AM) canonical vectors.
"""
import pytest
from app.core.parser import EvidenceParser

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


@pytest.fixture(scope="module")
def gh_parser():
    return EvidenceParser(country_code="GH", context_tag="urban_informal")


@pytest.fixture(scope="module")
def am_parser():
    return EvidenceParser(country_code="AM", context_tag="urban_informal")


@pytest.fixture(scope="module")
def amara_internal(gh_parser):
    return gh_parser.parse(AMARA_INPUT)


@pytest.fixture(scope="module")
def amara_profile(gh_parser):
    return gh_parser.parse_for_profile(AMARA_INPUT)


@pytest.fixture(scope="module")
def ani_profile(am_parser):
    return am_parser.parse_for_profile(ANI_INPUT)


# ---------------------------------------------------------------------------
# Internal parse() — USER entity
# ---------------------------------------------------------------------------

class TestUserEntity:
    def test_user_id_format(self, amara_internal):
        assert amara_internal["user"]["user_id"].startswith("usr_")

    def test_name_extracted(self, amara_internal):
        assert amara_internal["user"]["display_name"] == "Amara"

    def test_zero_credential_gh_default(self, amara_internal):
        assert amara_internal["user"]["zero_credential"] is True

    def test_source_text_hash_64_hex(self, amara_internal):
        assert len(amara_internal["user"]["source_text_hash"]) == 64

    def test_languages_non_empty(self, amara_internal):
        assert len(amara_internal["user"]["languages"]) >= 1


# ---------------------------------------------------------------------------
# Internal parse() — SKILL entities
# ---------------------------------------------------------------------------

class TestSkillEntities:
    def test_skills_non_empty(self, amara_internal):
        assert len(amara_internal["skills"]) >= 1

    def test_skill_has_taxonomy_code(self, amara_internal):
        for s in amara_internal["skills"]:
            assert "taxonomy_code" in s
            assert len(s["taxonomy_code"]) >= 3

    def test_fish_or_trading_detected(self, amara_internal):
        labels = [s["label"].lower() for s in amara_internal["skills"]]
        assert any("fish" in l or "trad" in l or "sell" in l or "market" in l for l in labels)

    def test_bookkeeping_detected(self, amara_internal):
        labels = [s["label"].lower() for s in amara_internal["skills"]]
        assert any("book" in l or "ledger" in l or "account" in l for l in labels)

    def test_mobile_money_detected(self, amara_internal):
        labels = [s["label"].lower() for s in amara_internal["skills"]]
        assert any("mobile" in l or "money" in l or "vodafone" in l for l in labels)

    def test_skill_ids_unique(self, amara_internal):
        ids = [s["skill_id"] for s in amara_internal["skills"]]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# parse_for_profile() — ProfileCard shape
# ---------------------------------------------------------------------------

class TestProfileCardShape:
    def test_required_keys(self, amara_profile):
        for key in ["profile_id", "display_name", "pseudonym", "location",
                    "languages", "skills", "wage_signal", "growth_signal",
                    "network_entry", "sms_summary", "ussd_menu"]:
            assert key in amara_profile, f"Missing: {key}"

    def test_pseudonym_is_amara(self, amara_profile):
        assert amara_profile["pseudonym"] == "Amara"

    def test_age_27(self, amara_profile):
        assert amara_profile["age"] == 27

    def test_skills_sorted_desc(self, amara_profile):
        confs = [s["confidence"] for s in amara_profile["skills"]]
        assert confs == sorted(confs, reverse=True)

    def test_skills_max_8(self, amara_profile):
        assert len(amara_profile["skills"]) <= 8

    def test_skill_confidence_0_to_1(self, amara_profile):
        for s in amara_profile["skills"]:
            assert 0.0 <= s["confidence"] <= 1.0

    def test_profile_id_deterministic(self, gh_parser):
        p1 = gh_parser.parse_for_profile(AMARA_INPUT)["profile_id"]
        p2 = gh_parser.parse_for_profile(AMARA_INPUT)["profile_id"]
        assert p1 == p2

    def test_languages_human_readable(self, amara_profile):
        for lang in amara_profile["languages"]:
            assert "-" not in lang or "(" in lang  # no raw BCP-47 like "ak-GH"


# ---------------------------------------------------------------------------
# Wage + Growth signals
# ---------------------------------------------------------------------------

class TestSignals:
    def test_wage_score_range(self, amara_profile):
        assert 0 <= amara_profile["wage_signal"]["score"] <= 100

    def test_wage_has_ghs(self, amara_profile):
        assert "GHS" in amara_profile["wage_signal"].get("display_value", "")

    def test_wage_has_rationale(self, amara_profile):
        assert len(amara_profile["wage_signal"]["rationale"]) > 10

    def test_growth_score_range(self, amara_profile):
        assert 0 <= amara_profile["growth_signal"]["score"] <= 100

    def test_growth_has_rationale(self, amara_profile):
        assert len(amara_profile["growth_signal"]["rationale"]) > 10

    def test_ambition_boosts_growth(self, gh_parser):
        low = gh_parser.parse_for_profile("I sell things")["growth_signal"]["score"]
        high = gh_parser.parse_for_profile(
            "I sell things, I want to expand my business online and register formally"
        )["growth_signal"]["score"]
        assert high > low


# ---------------------------------------------------------------------------
# SMS + USSD constraints
# ---------------------------------------------------------------------------

class TestSmsUssd:
    def test_sms_max_160(self, amara_profile):
        assert len(amara_profile["sms_summary"]) <= 160

    def test_ussd_4_to_8_lines(self, amara_profile):
        assert 4 <= len(amara_profile["ussd_menu"]) <= 8

    def test_ussd_line_max_40(self, amara_profile):
        for line in amara_profile["ussd_menu"]:
            assert len(line) <= 40

    def test_ussd_shortcode_gh(self, amara_profile):
        assert any("*789#" in l for l in amara_profile["ussd_menu"])


# ---------------------------------------------------------------------------
# Network entry
# ---------------------------------------------------------------------------

class TestNetworkEntry:
    def test_has_channel(self, amara_profile):
        assert len(amara_profile["network_entry"]["channel"]) > 5

    def test_has_coords(self, amara_profile):
        ne = amara_profile["network_entry"]
        assert isinstance(ne["lat"], float)
        assert isinstance(ne["lng"], float)

    def test_gh_coords_in_ghana(self, amara_profile):
        ne = amara_profile["network_entry"]
        assert 4.0 < ne["lat"] < 12.0  # Ghana latitude range
        assert -4.0 < ne["lng"] < 2.0  # Ghana longitude range


# ---------------------------------------------------------------------------
# Armenia (Ani) canonical story
# ---------------------------------------------------------------------------

class TestAniArmenia:
    def test_parse_succeeds(self, ani_profile):
        assert "skills" in ani_profile

    def test_age_31(self, ani_profile):
        assert ani_profile.get("age") == 31

    def test_teaching_or_tutoring_detected(self, ani_profile):
        labels = [s["name"].lower() for s in ani_profile["skills"]]
        assert any("teach" in l or "tutor" in l or "lesson" in l for l in labels)

    def test_translation_detected(self, ani_profile):
        labels = [s["name"].lower() for s in ani_profile["skills"]]
        assert any("transl" in l or "interpr" in l for l in labels)

    def test_mobile_money_idram_detected(self, ani_profile):
        labels = [s["name"].lower() for s in ani_profile["skills"]]
        assert any("idram" in l or "mobile" in l or "money" in l for l in labels)

    def test_amd_wage(self, ani_profile):
        assert "AMD" in ani_profile["wage_signal"].get("display_value", "")

    def test_ussd_shortcode_am(self, ani_profile):
        assert any("*404#" in l for l in ani_profile["ussd_menu"])

    def test_network_entry_armenia(self, ani_profile):
        channel = ani_profile["network_entry"]["channel"].lower()
        assert "e-gov" in channel or "idram" in channel or "ata" in channel

    def test_am_coords_in_armenia(self, ani_profile):
        ne = ani_profile["network_entry"]
        assert 38.0 < ne["lat"] < 42.0
        assert 43.0 < ne["lng"] < 47.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_minimal_english(self, gh_parser):
        r = gh_parser.parse_for_profile("I sew clothes")
        assert len(r["skills"]) >= 1

    def test_phone_repair_story(self, gh_parser):
        r = gh_parser.parse_for_profile(
            "My name is Kwame, I fix phones in Accra, learned on YouTube, 3 years"
        )
        labels = [s["name"].lower() for s in r["skills"]]
        assert any("phone" in l or "repair" in l for l in labels)

    def test_multiple_skills_max_8(self, gh_parser):
        r = gh_parser.parse_for_profile(
            "I teach, translate, code, design, photograph, braid hair, "
            "sell cloth, and do bookkeeping in Accra"
        )
        assert len(r["skills"]) <= 8

    def test_no_name_fallback(self, gh_parser):
        r = gh_parser.parse_for_profile("fixing phones for 2 years in Kumasi")
        assert r["pseudonym"] in ("Anonymous", "Worker") or isinstance(r["pseudonym"], str)

    def test_experience_boosts_confidence(self, gh_parser):
        low = gh_parser.parse_for_profile("I fix phones")
        hi = gh_parser.parse_for_profile("I fix phones, 5 years experience, 50 customers per week")
        low_conf = max((s["confidence"] for s in low["skills"]), default=0)
        hi_conf = max((s["confidence"] for s in hi["skills"]), default=0)
        assert hi_conf >= low_conf
