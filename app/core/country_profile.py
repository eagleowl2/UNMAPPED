"""
Country profile loader and validator.
Loads JSON configs from config/ and validates against schemas/country_profile.json.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import ValidationError

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).parent.parent.parent
_SCHEMA_PATH = _ROOT / "schemas" / "country_profile.json"
_CONFIG_DIR = _ROOT / "config"

# Registry of known context configs: (country_code, context_tag) -> filename
_PROFILE_REGISTRY: dict[tuple[str, str], str] = {
    ("GH", "urban_informal"): "ghana_urban_informal.json",
    ("AM", "urban_informal"): "armenia_urban_informal.json",
}


@lru_cache(maxsize=32)
def _load_schema() -> dict[str, Any]:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_country_profile(
    country_code: str,
    context_tag: str = "urban_informal",
) -> dict[str, Any]:
    """Load and validate a country profile config.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g. "GH").
        context_tag: Context identifier (e.g. "urban_informal").

    Returns:
        Validated country profile dict.

    Raises:
        FileNotFoundError: No config found for this country/context.
        ValidationError: Config violates the JSON schema.
    """
    key = (country_code.upper(), context_tag)
    filename = _PROFILE_REGISTRY.get(key)
    if filename is None:
        available = [f"{cc}/{ctx}" for cc, ctx in _PROFILE_REGISTRY]
        raise FileNotFoundError(
            f"No country profile for '{country_code}/{context_tag}'. "
            f"Available: {available}"
        )

    config_path = _CONFIG_DIR / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file missing: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        profile = json.load(f)

    schema = _load_schema()
    try:
        jsonschema.validate(instance=profile, schema=schema)
    except ValidationError as exc:
        raise ValidationError(
            f"Country profile '{filename}' failed schema validation: {exc.message}"
        ) from exc

    logger.debug("Loaded country profile: %s/%s", country_code, context_tag)
    return profile


def load_profile_from_path(path: Path) -> dict[str, Any]:
    """Load and validate a country profile from an explicit file path."""
    with path.open(encoding="utf-8") as f:
        profile = json.load(f)
    schema = _load_schema()
    jsonschema.validate(instance=profile, schema=schema)
    return profile


def get_language_list(profile: dict[str, Any]) -> list[str]:
    return profile["languages"]["supported"]


def get_sector_tags(profile: dict[str, Any]) -> list[str]:
    return profile["informal_economy"].get("sector_tags", [])


def get_local_skill_overrides(profile: dict[str, Any]) -> list[dict[str, str]]:
    return profile["taxonomy_config"].get("local_skill_overrides", [])


def get_skill_alias_registry(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Locale-specific multilingual alias registry (v0.3.1 §4.6.1).

    Each entry: {canonical_label, aliases[], isco_code, category, base_weight?, language?}.
    Consumed by the parser BEFORE regex / embedding fallbacks.
    """
    return profile.get("taxonomy_config", {}).get("skill_alias_registry", [])


def get_confidence_priors(profile: dict[str, Any]) -> dict[str, float]:
    return profile.get("confidence_priors", {
        "self_report_alpha": 2.0,
        "self_report_beta": 3.0,
        "peer_endorsement_weight": 0.35,
        "transaction_evidence_weight": 0.45,
    })


def is_zero_credential_context(profile: dict[str, Any]) -> bool:
    return profile["informal_economy"].get("zero_credential_default", False)


def get_opportunity_catalog(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the opportunity catalog for BONA-style job-match scoring (v0.4.0)."""
    return profile.get("opportunity_catalog", [])
