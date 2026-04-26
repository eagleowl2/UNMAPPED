"""
Lazy loaders for the bundled econometric data fixtures in /data.

Each fixture cites its source + year. Loaders are cached so the JSON parse
runs once per process. Missing files return safe defaults — the parse
endpoint must never crash because a fixture is unavailable.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(filename: str) -> dict[str, Any]:
    path = _DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("data fixture missing: %s", path)
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("data fixture unreadable: %s — %s", path, exc)
        return {}


@lru_cache(maxsize=8)
def load_ilostat(country: str) -> dict[str, Any]:
    """Wage bands + 5yr sector growth from ILOSTAT, per country."""
    return _load_json(f"ilostat_{country.upper()}.json")


@lru_cache(maxsize=1)
def load_frey_osborne() -> dict[str, Any]:
    return _load_json("frey_osborne_isco.json")


@lru_cache(maxsize=1)
def load_lmic_adjustment() -> dict[str, Any]:
    return _load_json("ilo_lmic_adjustment.json")


@lru_cache(maxsize=1)
def load_wittgenstein() -> dict[str, Any]:
    return _load_json("wittgenstein_2035.json")


@lru_cache(maxsize=1)
def load_neet() -> dict[str, Any]:
    return _load_json("data360_neet.json")


def get_wage_band(country: str, isco_code: str) -> dict[str, Any] | None:
    data = load_ilostat(country)
    bands = data.get("wage_bands", {})
    return bands.get(isco_code) or bands.get("DEFAULT")


def get_growth_for_isco(country: str, isco_code: str) -> dict[str, Any] | None:
    """Return {growth_pct, sector} for a given ISCO code via the country map."""
    data = load_ilostat(country)
    sectors = data.get("growth_5yr", {})
    for sector_name, sector in sectors.items():
        if not isinstance(sector, dict):
            continue
        if isco_code in sector.get("isco_codes", []):
            return {"growth_pct": sector["growth_pct"], "sector": sector_name}
    default = sectors.get("DEFAULT")
    if isinstance(default, dict):
        return {"growth_pct": default.get("growth_pct", 4), "sector": "DEFAULT"}
    return None


def get_data_citation(country: str) -> dict[str, str]:
    data = load_ilostat(country)
    return {
        "source": data.get("source", "ILO ILOSTAT"),
        "year": str(data.get("year", "")),
    }
