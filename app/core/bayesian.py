"""
Bayesian confidence scoring for skill signals.
Uses Beta distribution conjugate update: Beta(alpha, beta) posterior.
PyMC/scipy used for credible interval computation.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Confidence tier thresholds (posterior mean)
_TIERS = [
    (0.75, "expert"),
    (0.55, "established"),
    (0.35, "developing"),
    (0.0,  "emerging"),
]


@dataclass
class ConfidenceResult:
    score: float          # posterior mean
    lower_95: float       # 2.5th percentile
    upper_95: float       # 97.5th percentile
    alpha: float
    beta: float
    method: str
    tier: str


def _beta_mean(alpha: float, beta: float) -> float:
    return alpha / (alpha + beta)


def _beta_variance(alpha: float, beta: float) -> float:
    s = alpha + beta
    return (alpha * beta) / (s * s * (s + 1))


def _beta_quantile_approx(alpha: float, beta: float, p: float) -> float:
    """Wilson-Hilferty approximation for Beta quantiles (avoids scipy dependency)."""
    # Use incomplete beta via normal approximation when scipy unavailable
    try:
        from scipy.stats import beta as sp_beta  # type: ignore
        return float(sp_beta.ppf(p, alpha, beta))
    except ImportError:
        pass

    # Fallback: simple normal approximation
    mean = _beta_mean(alpha, beta)
    std = math.sqrt(_beta_variance(alpha, beta))
    # z-score for p
    z = {0.025: -1.96, 0.975: 1.96}.get(p, 0.0)
    val = mean + z * std
    return max(0.0, min(1.0, val))


def _assign_tier(score: float) -> str:
    for threshold, tier in _TIERS:
        if score >= threshold:
            return tier
    return "emerging"


def compute_confidence(
    evidence_list: list[dict[str, Any]],
    priors: dict[str, float],
    extra_signals: dict[str, Any] | None = None,
) -> ConfidenceResult:
    """Compute Bayesian Beta confidence from evidence chain.

    Conjugate update rule:
        alpha += sum(successes weighted by evidence weight)
        beta  += sum(failures weighted by (1 - evidence weight))

    Args:
        evidence_list: List of evidence dicts with 'weight' and 'evidence_type'.
        priors: Country profile priors (alpha, beta, peer/txn weights).
        extra_signals: Optional additional signals (years_exp, client_count, etc.)

    Returns:
        ConfidenceResult with posterior distribution parameters.
    """
    alpha = priors.get("self_report_alpha", 2.0)
    beta_param = priors.get("self_report_beta", 3.0)

    peer_w = priors.get("peer_endorsement_weight", 0.35)
    txn_w = priors.get("transaction_evidence_weight", 0.45)

    for ev in evidence_list:
        ev_type = ev.get("evidence_type", "self_report")
        weight = float(ev.get("weight", 0.3))

        # Scale weight by evidence type quality
        if ev_type == "self_report":
            effective_weight = weight * 1.0
        elif ev_type == "peer_endorsement":
            effective_weight = weight * (1.0 + peer_w)
        elif ev_type == "transaction_record":
            effective_weight = weight * (1.0 + txn_w)
        elif ev_type == "formal_credential":
            effective_weight = weight * 1.6
        elif ev_type == "digital_footprint":
            effective_weight = weight * 1.2
        elif ev_type == "community_attestation":
            effective_weight = weight * 1.1
        else:
            effective_weight = weight * 0.8

        effective_weight = min(effective_weight, 1.0)
        alpha += effective_weight
        beta_param += (1.0 - effective_weight) * 0.5

    # Boost for extra signals (years of experience, client count, etc.)
    if extra_signals:
        years = extra_signals.get("years_experience", 0)
        if years and isinstance(years, (int, float)) and years > 0:
            boost = min(years * 0.08, 0.5)
            alpha += boost

        clients = extra_signals.get("client_count", 0)
        if clients and isinstance(clients, (int, float)) and clients > 0:
            boost = min(math.log1p(clients) * 0.05, 0.3)
            alpha += boost

    score = _beta_mean(alpha, beta_param)
    lower = _beta_quantile_approx(alpha, beta_param, 0.025)
    upper = _beta_quantile_approx(alpha, beta_param, 0.975)
    tier = _assign_tier(score)

    return ConfidenceResult(
        score=round(score, 4),
        lower_95=round(lower, 4),
        upper_95=round(upper, 4),
        alpha=round(alpha, 4),
        beta=round(beta_param, 4),
        method="bayesian_beta",
        tier=tier,
    )
