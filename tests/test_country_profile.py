"""Tests for country profile loader and validator."""
import pytest
from pathlib import Path

from app.core.country_profile import (
    get_confidence_priors,
    get_local_skill_overrides,
    get_sector_tags,
    is_zero_credential_context,
    load_country_profile,
)


def test_load_ghana_urban_informal():
    profile = load_country_profile("GH", "urban_informal")
    assert profile["country_code"] == "GH"
    assert profile["context_tag"] == "urban_informal"
    assert "languages" in profile
    assert "informal_economy" in profile


def test_schema_validation_passes():
    profile = load_country_profile("GH", "urban_informal")
    assert profile is not None  # no ValidationError raised


def test_unknown_country_raises():
    with pytest.raises(FileNotFoundError, match="No country profile"):
        load_country_profile("ZZ", "urban_informal")


def test_get_sector_tags():
    profile = load_country_profile("GH", "urban_informal")
    tags = get_sector_tags(profile)
    assert "mobile_repair" in tags
    assert isinstance(tags, list)


def test_is_zero_credential_context():
    profile = load_country_profile("GH", "urban_informal")
    assert is_zero_credential_context(profile) is True


def test_confidence_priors_keys():
    profile = load_country_profile("GH", "urban_informal")
    priors = get_confidence_priors(profile)
    assert "self_report_alpha" in priors
    assert "self_report_beta" in priors
    assert priors["self_report_alpha"] > 0


def test_local_skill_overrides_include_phone_repair():
    profile = load_country_profile("GH", "urban_informal")
    overrides = get_local_skill_overrides(profile)
    labels = [o["local_label"] for o in overrides]
    assert "fix phone" in labels or "fixing phones" in labels


def test_case_insensitive_country_code():
    profile = load_country_profile("gh", "urban_informal")
    assert profile["country_code"] == "GH"
