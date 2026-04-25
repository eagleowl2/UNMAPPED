"""Tests for Bayesian confidence scoring."""
import pytest
from app.core.bayesian import compute_confidence, _assign_tier


_DEFAULT_PRIORS = {
    "self_report_alpha": 2.0,
    "self_report_beta": 3.0,
    "peer_endorsement_weight": 0.35,
    "transaction_evidence_weight": 0.45,
}


def test_basic_self_report():
    evidence = [{"evidence_type": "self_report", "weight": 0.7}]
    result = compute_confidence(evidence, _DEFAULT_PRIORS)
    assert 0.0 < result.score < 1.0
    assert result.method == "bayesian_beta"
    assert result.tier in ("emerging", "developing", "established", "expert")


def test_higher_weight_gives_higher_score():
    low = compute_confidence(
        [{"evidence_type": "self_report", "weight": 0.2}], _DEFAULT_PRIORS
    )
    high = compute_confidence(
        [{"evidence_type": "self_report", "weight": 0.9}], _DEFAULT_PRIORS
    )
    assert high.score > low.score


def test_formal_credential_boosts_score():
    base = compute_confidence(
        [{"evidence_type": "self_report", "weight": 0.7}], _DEFAULT_PRIORS
    )
    credentialed = compute_confidence(
        [{"evidence_type": "formal_credential", "weight": 0.7}], _DEFAULT_PRIORS
    )
    assert credentialed.score > base.score


def test_years_experience_boosts_score():
    no_exp = compute_confidence(
        [{"evidence_type": "self_report", "weight": 0.6}], _DEFAULT_PRIORS
    )
    with_exp = compute_confidence(
        [{"evidence_type": "self_report", "weight": 0.6}],
        _DEFAULT_PRIORS,
        extra_signals={"years_experience": 5},
    )
    assert with_exp.score > no_exp.score


def test_credible_interval_bounds():
    evidence = [{"evidence_type": "self_report", "weight": 0.7}]
    result = compute_confidence(evidence, _DEFAULT_PRIORS)
    assert result.lower_95 <= result.score <= result.upper_95
    assert 0.0 <= result.lower_95 <= 1.0
    assert 0.0 <= result.upper_95 <= 1.0


def test_tier_assignment():
    assert _assign_tier(0.80) == "expert"
    assert _assign_tier(0.60) == "established"
    assert _assign_tier(0.40) == "developing"
    assert _assign_tier(0.10) == "emerging"


def test_multiple_evidence_items():
    evidence = [
        {"evidence_type": "self_report", "weight": 0.7},
        {"evidence_type": "peer_endorsement", "weight": 0.8},
        {"evidence_type": "transaction_record", "weight": 0.75},
    ]
    result = compute_confidence(evidence, _DEFAULT_PRIORS)
    assert result.score > 0.5
