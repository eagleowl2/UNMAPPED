"""
Unit tests for Module 2 — Job-Match Signal Engine (app/core/jobmatch.py).
"""
import pytest

from app.core.jobmatch import (
    _isco_group,
    _score_opportunity,
    _skill_boost,
    compute_job_match,
)
from app.core.country_profile import get_opportunity_catalog, load_country_profile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gh_catalog():
    profile = load_country_profile("GH", "urban_informal")
    return get_opportunity_catalog(profile)


@pytest.fixture(scope="module")
def am_catalog():
    profile = load_country_profile("AM", "urban_informal")
    return get_opportunity_catalog(profile)


_PHONE_REPAIR_SKILL = {"name": "Phone Repair", "confidence": 0.80, "taxonomy_code": "7421", "category": "technical"}
_CODING_SKILL = {"name": "Software Development", "confidence": 0.65, "taxonomy_code": "2512", "category": "digital"}
_MOMO_SKILL = {"name": "Mobile money", "confidence": 0.70, "taxonomy_code": "4211", "category": "financial"}

_TEACHER_SKILL = {"name": "Teacher", "confidence": 0.80, "taxonomy_code": "2320", "category": "care"}
_TRANSLATOR_SKILL = {"name": "Translator", "confidence": 0.65, "taxonomy_code": "2643", "category": "creative"}


# ---------------------------------------------------------------------------
# _isco_group
# ---------------------------------------------------------------------------

class TestIscoGroup:
    def test_standard_4digit(self):
        assert _isco_group("7421") == "7"

    def test_standard_3digit(self):
        assert _isco_group("532") == "5"

    def test_empty_returns_9(self):
        assert _isco_group("") == "9"

    def test_non_digit_returns_9(self):
        assert _isco_group("ABCD") == "9"


# ---------------------------------------------------------------------------
# _skill_boost
# ---------------------------------------------------------------------------

class TestSkillBoost:
    def test_exact_match_returns_confidence(self):
        skills = [_PHONE_REPAIR_SKILL]
        boost = _skill_boost(skills, "7421")
        assert boost == pytest.approx(0.80)

    def test_same_major_group_returns_partial(self):
        skills = [_PHONE_REPAIR_SKILL]
        boost = _skill_boost(skills, "7112")  # same major group 7
        assert boost == pytest.approx(0.80 * 0.6)

    def test_no_match_returns_zero(self):
        skills = [_PHONE_REPAIR_SKILL]
        boost = _skill_boost(skills, "2512")
        assert boost == 0.0

    def test_multiple_skills_returns_max(self):
        skills = [_PHONE_REPAIR_SKILL, {"name": "S2", "confidence": 0.95, "taxonomy_code": "7421"}]
        boost = _skill_boost(skills, "7421")
        assert boost == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# _score_opportunity
# ---------------------------------------------------------------------------

class TestScoreOpportunity:
    def _make_opp(self, isco_code, zero_cred=True, langs=None):
        return {
            "isco_code": isco_code,
            "accepts_zero_credential": zero_cred,
            "required_languages": langs or ["en"],
        }

    def test_exact_isco_match_high_score(self):
        opp = self._make_opp("7421")
        score = _score_opportunity(opp, [_PHONE_REPAIR_SKILL], zero_credential=True, profile_languages=["en"])
        assert score >= 0.8

    def test_score_clamped_to_1(self):
        opp = self._make_opp("7421")
        score = _score_opportunity(opp, [_PHONE_REPAIR_SKILL], zero_credential=True, profile_languages=["en"])
        assert score <= 1.0

    def test_zero_credential_bonus_applied(self):
        opp_zc = self._make_opp("9999", zero_cred=True)
        opp_no_zc = self._make_opp("9999", zero_cred=False)
        score_zc = _score_opportunity(opp_zc, [_PHONE_REPAIR_SKILL], zero_credential=True, profile_languages=["en"])
        score_no_zc = _score_opportunity(opp_no_zc, [_PHONE_REPAIR_SKILL], zero_credential=True, profile_languages=["en"])
        assert score_zc > score_no_zc

    def test_language_match_bonus_applied(self):
        opp = self._make_opp("9999", langs=["en"])
        score_match = _score_opportunity(opp, [_PHONE_REPAIR_SKILL], zero_credential=False, profile_languages=["en"])
        score_no_match = _score_opportunity(opp, [_PHONE_REPAIR_SKILL], zero_credential=False, profile_languages=["fr"])
        assert score_match > score_no_match

    def test_multi_skill_diversification(self):
        opp = self._make_opp("7421")
        score_one = _score_opportunity(opp, [_PHONE_REPAIR_SKILL], zero_credential=False, profile_languages=["en"])
        score_two = _score_opportunity(opp, [_PHONE_REPAIR_SKILL, _CODING_SKILL], zero_credential=False, profile_languages=["en"])
        assert score_two > score_one


# ---------------------------------------------------------------------------
# compute_job_match — Ghana
# ---------------------------------------------------------------------------

class TestComputeJobMatchGhana:
    def test_returns_expected_keys(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        assert "job_match" in result
        assert "network_entry" in result

    def test_job_match_shape(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        jm = result["job_match"]
        assert isinstance(jm["score"], int)
        assert 0 <= jm["score"] <= 100
        assert isinstance(jm["rationale"], str)
        assert isinstance(jm["opportunity_count"], int)
        assert isinstance(jm["matched_opportunities"], list)

    def test_phone_repair_matches_isco_7421(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        opps = result["job_match"]["matched_opportunities"]
        assert any(o["isco_code"] == "7421" for o in opps)

    def test_score_above_threshold(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL, _CODING_SKILL, _MOMO_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        assert result["job_match"]["score"] >= 50

    def test_max_5_opportunities(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL, _CODING_SKILL, _MOMO_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        assert len(result["job_match"]["matched_opportunities"]) <= 5

    def test_network_entry_from_top_opportunity(self, gh_catalog):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        ne = result["network_entry"]
        assert "channel" in ne and "lat" in ne and "lng" in ne and "label" in ne

    def test_empty_skills_returns_empty_match(self, gh_catalog):
        result = compute_job_match(
            skills=[],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=gh_catalog,
        )
        assert result["job_match"]["score"] == 15
        assert result["job_match"]["opportunity_count"] == 0

    def test_empty_catalog_returns_empty_match(self):
        result = compute_job_match(
            skills=[_PHONE_REPAIR_SKILL],
            country_code="GH",
            zero_credential=True,
            profile_languages=["en"],
            opportunity_catalog=[],
        )
        assert result["job_match"]["score"] == 15


# ---------------------------------------------------------------------------
# compute_job_match — Armenia
# ---------------------------------------------------------------------------

class TestComputeJobMatchArmenia:
    def test_teacher_matches_isco_2320(self, am_catalog):
        result = compute_job_match(
            skills=[_TEACHER_SKILL, _TRANSLATOR_SKILL],
            country_code="AM",
            zero_credential=False,
            profile_languages=["hy-AM"],
            opportunity_catalog=am_catalog,
        )
        opps = result["job_match"]["matched_opportunities"]
        assert any(o["isco_code"] == "2320" for o in opps)

    def test_translator_matches_isco_2643(self, am_catalog):
        result = compute_job_match(
            skills=[_TRANSLATOR_SKILL],
            country_code="AM",
            zero_credential=False,
            profile_languages=["hy-AM", "en"],
            opportunity_catalog=am_catalog,
        )
        opps = result["job_match"]["matched_opportunities"]
        assert any(o["isco_code"] == "2643" for o in opps)

    def test_rationale_mentions_country(self, am_catalog):
        result = compute_job_match(
            skills=[_TEACHER_SKILL],
            country_code="AM",
            zero_credential=False,
            profile_languages=["hy-AM"],
            opportunity_catalog=am_catalog,
        )
        assert "AM" in result["job_match"]["rationale"]


# ---------------------------------------------------------------------------
# opportunity_catalog in country profile (integration)
# ---------------------------------------------------------------------------

class TestOpportunityCatalogIntegration:
    def test_gh_catalog_not_empty(self, gh_catalog):
        assert len(gh_catalog) >= 8

    def test_am_catalog_not_empty(self, am_catalog):
        assert len(am_catalog) >= 8

    def test_gh_catalog_has_required_fields(self, gh_catalog):
        for entry in gh_catalog:
            assert "isco_code" in entry
            assert "title" in entry
            assert "formalization_path" in entry
            assert "lat" in entry and "lng" in entry

    def test_gh_catalog_schema_valid(self):
        profile = load_country_profile("GH", "urban_informal")
        assert "opportunity_catalog" in profile

    def test_am_catalog_schema_valid(self):
        profile = load_country_profile("AM", "urban_informal")
        assert "opportunity_catalog" in profile
