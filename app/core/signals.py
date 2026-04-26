"""
Wage signal, growth signal, and network entry computation.
These are the three new Human Layer fields required by the frontend contract (v0.3).

Wage signal  : 0-100 score + currency-formatted display_value + rationale
Growth signal: 0-100 score + rationale (cited 5yr CAGR from ILOSTAT)
Network entry: formal-economy channel + WGS84 pin + label

v0.3.2 — wage_bands and growth_5yr now load from data/ilostat_<CC>.json with
explicit source citations. The hardcoded WageBand maps below remain as a
last-resort fallback if the fixtures are missing.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Optional

from app.core.data_sources import (
    get_data_citation,
    get_growth_for_isco,
    get_wage_band,
    load_neet,
)


# ---------------------------------------------------------------------------
# Wage bands per country (ISCO-08 code → (low, mid, high) daily/hourly)
# Values are approximate median informal-sector wages for MVP.
# ---------------------------------------------------------------------------

@dataclass
class WageBand:
    low: int
    mid: int
    high: int
    unit: str            # "day", "hr", "week"
    currency: str


_GH_WAGE_BANDS: dict[str, WageBand] = {
    "7421": WageBand(25,  38,  60,  "day", "GHS"),   # electronics repair
    "2512": WageBand(40,  80, 150,  "day", "GHS"),   # software dev
    "2166": WageBand(35,  65, 110,  "day", "GHS"),   # graphic / digital design
    "5221": WageBand(20,  35,  55,  "day", "GHS"),   # retail/trading
    "7436": WageBand(18,  30,  50,  "day", "GHS"),   # tailoring (legacy)
    "7531": WageBand(18,  30,  50,  "day", "GHS"),   # tailor / dressmaker
    "8322": WageBand(22,  34,  48,  "day", "GHS"),   # transport/delivery
    "6110": WageBand(15,  25,  40,  "day", "GHS"),   # farming
    "9211": WageBand(15,  25,  40,  "day", "GHS"),   # smallholder farmer
    "5141": WageBand(20,  32,  55,  "day", "GHS"),   # hairdressing
    "5322": WageBand(16,  28,  44,  "day", "GHS"),   # care work
    "2320": WageBand(25,  45,  70,  "day", "GHS"),   # teaching
    "3312": WageBand(30,  55,  90,  "day", "GHS"),   # financial services
    "4211": WageBand(25,  42,  65,  "day", "GHS"),   # mobile-money agent
    "5120": WageBand(18,  30,  50,  "day", "GHS"),   # cook / food vendor
    "7112": WageBand(28,  45,  75,  "day", "GHS"),   # construction artisan
    "9621": WageBand(15,  22,  35,  "day", "GHS"),   # head-load porter (kayayei)
    "DEFAULT": WageBand(18, 30, 50, "day", "GHS"),
}

_AM_WAGE_BANDS: dict[str, WageBand] = {
    "2320": WageBand(2500, 4500, 8000, "hr", "AMD"),  # tutoring
    "2643": WageBand(3000, 5500, 9000, "hr", "AMD"),  # translation
    "2512": WageBand(3500, 7000,15000, "hr", "AMD"),  # software dev
    "2166": WageBand(2500, 5000, 9000, "hr", "AMD"),  # graphic / digital design
    "2411": WageBand(2500, 4500, 7500, "hr", "AMD"),  # accountant
    "5221": WageBand(1200, 2500, 4500, "hr", "AMD"),  # retail
    "7436": WageBand(1000, 2000, 3500, "hr", "AMD"),  # tailoring (legacy)
    "7531": WageBand(1000, 2000, 3500, "hr", "AMD"),  # tailor / seamstress
    "8322": WageBand(1500, 2800, 5000, "hr", "AMD"),  # driver / taxi
    "5141": WageBand(1200, 2400, 4500, "hr", "AMD"),  # hairdressing
    "5120": WageBand(1100, 2200, 4000, "hr", "AMD"),  # cook
    "3312": WageBand(2000, 4000, 7000, "hr", "AMD"),  # financial
    "4211": WageBand(1500, 3000, 5500, "hr", "AMD"),  # mobile-money / Idram agent
    "6110": WageBand( 800, 1500, 3000, "hr", "AMD"),  # farming
    "9211": WageBand( 800, 1500, 3000, "hr", "AMD"),  # smallholder farmer
    "7112": WageBand(1800, 3500, 6000, "hr", "AMD"),  # construction artisan
    "DEFAULT": WageBand(1500, 3000, 5500, "hr", "AMD"),
}

_WAGE_BANDS: dict[str, dict[str, WageBand]] = {
    "GH": _GH_WAGE_BANDS,
    "AM": _AM_WAGE_BANDS,
}

# Network entry channels: (country, ISCO code) → (channel description, lat, lng, label)
_NETWORK_ENTRIES: dict[tuple[str, str], tuple[str, float, float, str]] = {
    # Ghana
    ("GH", "7421"): (
        "Mobile-device repair SME registry via NBSSI + MTN MoMo SME account",
        5.5502, -0.2174, "Accra Central"
    ),
    ("GH", "2512"): (
        "Ghana Tech Lab / iSpace digital entrepreneur onboarding",
        5.6037, -0.1870, "Accra Tech Hub"
    ),
    ("GH", "5221"): (
        "Mobile-money cooperative onboarding (Vodafone Cash → MTN MoMo SME)",
        5.5502, -0.2174, "Makola Market"
    ),
    ("GH", "7436"): (
        "NBSSI textile & garment SME incubator — Accra Fashion District",
        5.5721, -0.2079, "Kantamanto"
    ),
    ("GH", "8322"): (
        "Ghana Private Road Transport Union (GPRTU) cooperative membership",
        5.5480, -0.2059, "Circle Interchange"
    ),
    ("GH", "6110"): (
        "Farmer registration via MoFA (Ghana Ministry of Food & Agriculture)",
        5.5600, -0.2000, "Accra"
    ),
    ("GH", "2320"): (
        "GES community-teaching assistant programme + GhanaLearn platform",
        5.5600, -0.2000, "Accra"
    ),
    ("GH", "4211"): (
        "MTN MoMo / Vodafone Cash agent registration + GhIPSS",
        5.5502, -0.2174, "Accra Mobile-Money Hub"
    ),
    ("GH", "5120"): (
        "Ghana Tourism Authority chop-bar registry + FDA food licence",
        5.5502, -0.2174, "Accra Food Vendors"
    ),
    ("GH", "7112"): (
        "Construction Industry Development Authority (CIDA) artisan certification",
        5.5500, -0.2050, "Accra Construction Hub"
    ),
    ("GH", "7531"): (
        "NBSSI textile & garment SME incubator — Accra Fashion District",
        5.5721, -0.2079, "Kantamanto"
    ),
    ("GH", "9211"): (
        "Farmer registration via MoFA (Ghana Ministry of Food & Agriculture)",
        5.5600, -0.2000, "Accra"
    ),
    ("GH", "9621"): (
        "Kayayei Youth Association onboarding → MoMo savings group",
        5.5530, -0.2080, "Agbogbloshie"
    ),
    ("GH", "5141"): (
        "Ghana Hairdressers & Beauticians Association cooperative",
        5.5600, -0.2000, "Accra Beauty District"
    ),
    ("GH", "2166"): (
        "Ghana Tech Lab + Creative Industries Hub (designer fast-track)",
        5.6037, -0.1870, "Accra Creative Hub"
    ),
    ("GH", "DEFAULT"): (
        "NBSSI informal-sector SME onboarding → MTN MoMo business account",
        5.5502, -0.2174, "Accra"
    ),
    # Armenia
    ("AM", "2320"): (
        "Sole-proprietor e-registration via e-gov.am + Idram for-business",
        40.7894, 43.8475, "Gyumri"
    ),
    ("AM", "2643"): (
        "Armenia Translators Association + Idram invoice gateway",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "2512"): (
        "TUMO Centre for Creative Technologies + EIF SME tech grant",
        40.1909, 44.5209, "Yerevan Tech Hub"
    ),
    ("AM", "5221"): (
        "Small-business e-registration (taxservice.am) + Idram merchant terminal",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "7531"): (
        "Craft cooperative (ArtBridge / Norategh) + Idram merchant account",
        40.7894, 43.8475, "Gyumri Craft Hub"
    ),
    ("AM", "8322"): (
        "Inasxarh taxi cooperative + sole-proprietor e-reg via taxservice.am",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "5141"): (
        "Beauty Workers Association Armenia + Idram merchant terminal",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "5120"): (
        "Small-business food-service e-reg (taxservice.am) + Idram PoS",
        40.7894, 43.8475, "Gyumri"
    ),
    ("AM", "4211"): (
        "Idram / Telcell agent registration + ABA Bank SME programme",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "2411"): (
        "Sole-proprietor e-registration via e-gov.am + ACBA accounting track",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "2166"): (
        "TUMO Centre for Creative Technologies + EIF digital creator grant",
        40.1909, 44.5209, "Yerevan Tech Hub"
    ),
    ("AM", "7112"): (
        "Armenia Construction Workers Union + Idram payroll account",
        40.7894, 43.8475, "Gyumri"
    ),
    ("AM", "9211"): (
        "Agricultural cooperative registration via MoA Armenia + loan programme",
        40.1872, 44.5152, "Yerevan"
    ),
    ("AM", "DEFAULT"): (
        "Sole-proprietor e-registration via e-gov.am + Idram for-business",
        40.1872, 44.5152, "Yerevan"
    ),
}

# Ambition / growth signal keywords
_AMBITION_PATTERNS = [
    (re.compile(r"\bwant\s+to\b|\bwould\s+like\s+to\b|\bplan\s+to\b|\bgoing\s+to\b", re.I), 8),
    (re.compile(r"\bstudio\b|\bbusiness\b|\bstart(?:up)?\b|\bexpand\b|\bgrow\b", re.I), 10),
    (re.compile(r"\bformal(?:ize|isation)?\b|\bregister\b|\blicense\b", re.I), 12),
    (re.compile(r"\bsave\b|\bsavings?\b|\bbudget\b|\bplan(?:ning)?\b", re.I), 7),
    (re.compile(r"\bonline\b|\bdigital\b|\bapp\b|\bwebsite\b|\binternet\b", re.I), 9),
    (re.compile(r"\bmobile\s+money\b|\bidram\b|\bvodafone\s+cash\b|\bmtn\s+momo\b", re.I), 11),
    (re.compile(r"\bledger\b|\baccounts?\b|\bbooks?\b|\bbookkeeping\b", re.I), 10),
    (re.compile(r"\bclient[s]?\b|\bcustomer[s]?\b", re.I), 6),
    (re.compile(r"\bmulti(?:lingual|language)?\b|\btranslat\b", re.I), 7),
    (re.compile(r"\byoutube\b|\bcourse\b|\bself[\s-]?taught\b", re.I), 5),
]

_BCP47_TO_HUMAN: dict[str, str] = {
    "en": "English",
    "en-GH": "English",
    "ak-GH": "Twi",
    "gaa": "Ga",
    "ee-GH": "Ewe",
    "ha-GH": "Hausa",
    "ha": "Hausa",
    "fr": "French",
    "ar": "Arabic",
    "sw": "Swahili",
    "hy-AM": "Armenian",
    "hy": "Armenian",
    "ru": "Russian",
    "yo": "Yoruba",
    "ig": "Igbo",
    "am": "Amharic",
    "so": "Somali",
    "wo": "Wolof",
}

# Armenian keyword patterns for language detection
_ARMENIAN_PATTERN = re.compile(r"[\u0531-\u0587]")  # Armenian Unicode block


def _band_from_fixture(country: str, isco_code: str) -> Optional[WageBand]:
    """Translate the JSON fixture row → WageBand dataclass for downstream use."""
    cc = country.upper()
    row = get_wage_band(cc, isco_code)
    if not row:
        return None
    currency = "GHS" if cc == "GH" else ("AMD" if cc == "AM" else "USD")
    unit = "day" if cc == "GH" else "hr"
    try:
        return WageBand(
            low=int(row["low"]), mid=int(row["mid"]), high=int(row["high"]),
            unit=unit, currency=currency,
        )
    except (KeyError, TypeError, ValueError):
        return None


def compute_wage_signal(
    skills: list[dict[str, Any]],
    country: str,
    extra_signals: dict[str, Any],
) -> dict[str, Any]:
    """Compute wage signal (0-100) with display_value and rationale.

    Wage values come from data/ilostat_<CC>.json (ILO ILOSTAT, cited).
    The hardcoded _WAGE_BANDS map remains as fallback if the fixture is
    missing in a given deploy.
    """
    cc = country.upper()
    fallback_bands = _WAGE_BANDS.get(cc, _WAGE_BANDS["GH"])

    # Find highest-wage skill among top 3 — try fixture first, fallback second
    best_band: Optional[WageBand] = None
    best_skill_name = ""
    for skill in skills[:3]:
        isco_code = skill.get("taxonomy_code", "DEFAULT")
        band = _band_from_fixture(cc, isco_code)
        if band is None:
            band = fallback_bands.get(isco_code) or fallback_bands.get("DEFAULT")
        if band and (best_band is None or band.mid > best_band.mid):
            best_band = band
            best_skill_name = skill.get("name", "")

    if best_band is None:
        best_band = fallback_bands.get("DEFAULT") or WageBand(20, 35, 55, "day", "GHS")

    # Base score: normalise mid wage to 0-100 using country-specific range
    max_wage = 200 if cc == "GH" else 20000
    base_score = int(min(100, (best_band.mid / max_wage) * 100))

    # Boost for experience
    years = extra_signals.get("years_experience", 0)
    if isinstance(years, (int, float)):
        base_score = min(100, base_score + int(years * 1.5))

    # Boost for multiple skills (diversification)
    if len(skills) >= 3:
        base_score = min(100, base_score + 8)
    elif len(skills) == 2:
        base_score = min(100, base_score + 4)

    score = max(10, base_score)

    display_value = (
        f"{best_band.currency} {best_band.mid:,} / {best_band.unit}"
    )

    citation = get_data_citation(cc)
    rationale = _wage_rationale(
        best_skill_name, best_band, skills, years, cc, citation,
    )

    return {"score": score, "display_value": display_value, "rationale": rationale}


def _wage_rationale(
    top_skill: str,
    band: WageBand,
    skills: list[dict[str, Any]],
    years: Any,
    country: str,
    citation: Optional[dict[str, str]] = None,
) -> str:
    parts = []
    if top_skill:
        parts.append(f"{top_skill} in the {country} informal sector")
    parts.append(
        f"{band.currency} {band.low:,}–{band.high:,}/{band.unit} typical range"
    )
    if isinstance(years, (int, float)) and years > 0:
        parts.append(f"{int(years)} yr experience adds wage floor")
    if len(skills) >= 2:
        skill_labels = [s["name"] for s in skills[:2]]
        parts.append(f"multi-skill portfolio ({', '.join(skill_labels)}) reduces income volatility")
    base = ". ".join(parts) + "."
    if citation and citation.get("source"):
        cit_year = citation.get("year")
        suffix = f" Source: {citation['source']}" + (f" ({cit_year})." if cit_year else ".")
        base = base + suffix
    return base


def compute_growth_signal(
    raw_text: str,
    skills: list[dict[str, Any]],
    zero_credential: bool,
    extra_signals: dict[str, Any],
    country: str,
) -> dict[str, Any]:
    """Compute growth / formalization potential signal (0-100) with rationale.

    Anchored to the cited 5-year sector employment growth (ILOSTAT) for the
    top skill's ISCO code. The score blends: sector growth, ambition signals
    in raw text, portfolio depth, experience, and zero-credential boost.
    Returns score, rationale, and a `display_value` string when sector data
    is available.
    """
    cc = country.upper()
    sector_pct: Optional[float] = None
    sector_name: Optional[str] = None
    if skills:
        top_isco = skills[0].get("taxonomy_code", "DEFAULT")
        sector = get_growth_for_isco(cc, top_isco)
        if sector:
            sector_pct = float(sector.get("growth_pct", 0))
            sector_name = sector.get("sector")

    rationale_parts: list[str] = []

    # Sector growth anchor: map -5..+30 pp into 0..40 score points
    if sector_pct is not None:
        sector_component = max(0, min(40, int((sector_pct + 5) * 1.6)))
    else:
        sector_component = 12
    score = 25 + sector_component

    # Ambition keywords in raw text
    ambition_total = 0
    for pattern, pts in _AMBITION_PATTERNS:
        if pattern.search(raw_text):
            ambition_total += pts
    score += min(20, ambition_total)

    # Digital skill presence
    digital_skills = [s for s in skills if s.get("category") == "digital"]
    if digital_skills:
        score += 8
        rationale_parts.append("digital skill stack")

    # Financial/bookkeeping skills
    fin_skills = [s for s in skills if s.get("category") == "financial"]
    if fin_skills:
        score += 6
        rationale_parts.append("financial literacy signal")

    # Multiple skills = portfolio depth
    if len(skills) >= 3:
        score += 8
        rationale_parts.append(f"{len(skills)}-skill portfolio")
    elif len(skills) == 2:
        score += 4
        rationale_parts.append("2-skill portfolio")

    # Experience boosts formalization potential
    years = extra_signals.get("years_experience", 0)
    if isinstance(years, (int, float)) and years >= 3:
        score += 6
        rationale_parts.append(f"{int(years)} yr track record")

    # Zero-credential path users often have informal networks → cap higher
    if zero_credential and score > 40:
        score += 4
        rationale_parts.append("zero-credential community network")

    score = max(10, min(100, score))

    # Build rationale
    channel = _country_growth_channel(cc, skills)
    if channel:
        rationale_parts.insert(0, channel)
    if sector_pct is not None:
        sign = "+" if sector_pct >= 0 else ""
        sector_label = sector_name.replace("_", " ") if sector_name else "sector"
        rationale_parts.insert(
            0,
            f"{sector_label} jobs grew {sign}{sector_pct:g}% over the last 5 years (ILO ILOSTAT, {cc}, 2018→2023)",
        )

    rationale = (
        " · ".join(rationale_parts) + "."
        if rationale_parts
        else "Self-reported skills with growth potential through formal registration."
    )

    out: dict[str, Any] = {"score": score, "rationale": rationale}
    if sector_pct is not None:
        sign = "+" if sector_pct >= 0 else ""
        out["display_value"] = f"{sign}{sector_pct:g}% / 5yr"
    return out


def get_neet_context(country: str) -> Optional[dict[str, Any]]:
    """Return Data360/ILOSTAT NEET context for the user's country, or None.

    Shape mirrors `NeetContext` in app/models/schemas.py.
    """
    cc = country.upper()
    rates = (load_neet().get("rates") or {}).get(cc)
    if not rates:
        return None
    return {
        "neet_pct": float(rates.get("neet_pct", 0.0)),
        "narrative": rates.get("narrative", ""),
        "source": "World Bank Data360 / ILO ILOSTAT (SDG 8.6.1)",
        "year": int(rates.get("year", 2022)),
    }


def _country_growth_channel(country: str, skills: list[dict[str, Any]]) -> str:
    if not skills:
        return ""
    top_code = skills[0].get("taxonomy_code", "")
    channels = {
        "GH": {
            "7421": "mobile-repair SME registry (NBSSI)",
            "2512": "GhanaTechLab digital entrepreneur track",
            "2166": "Ghana Creative Industries Hub designer fast-track",
            "5221": "MoMo SME rails",
            "2320": "GhanaLearn educator platform",
            "4211": "MTN MoMo / GhIPSS agent registration",
            "7531": "NBSSI textile & garment SME incubator",
            "9621": "Kayayei Youth Association savings cooperative",
            "7112": "CIDA artisan certification track",
        },
        "AM": {
            "2320": "studio business via e-gov.am",
            "2643": "ATA translation cooperative",
            "2512": "EIF SME tech grant",
            "2166": "TUMO Creative Technologies grant",
            "2411": "ACBA accountant SME track",
            "4211": "Idram agent + ABA Bank SME programme",
            "7531": "ArtBridge craft cooperative",
            "8322": "Inasxarh taxi cooperative",
        },
    }
    return channels.get(country.upper(), {}).get(top_code, "")


def get_network_entry(
    skills: list[dict[str, Any]],
    country: str,
    location_city: str,
) -> dict[str, Any]:
    """Return the most appropriate formal-economy network entry point."""
    top_code = skills[0].get("taxonomy_code", "DEFAULT") if skills else "DEFAULT"
    key = (country.upper(), top_code)
    entry = _NETWORK_ENTRIES.get(key)
    if entry is None:
        entry = _NETWORK_ENTRIES.get((country.upper(), "DEFAULT"))
    if entry is None:
        # Hard fallback
        if country.upper() == "AM":
            entry = ("Sole-proprietor e-registration via e-gov.am", 40.1872, 44.5152, "Yerevan")
        else:
            entry = ("NBSSI informal-sector SME onboarding → MTN MoMo", 5.5502, -0.2174, "Accra")

    channel, lat, lng, label = entry
    # Refine label with detected city if available
    if location_city and location_city.lower() not in label.lower():
        label = f"{label} ({location_city})"

    return {"channel": channel, "lat": lat, "lng": lng, "label": label}


def detect_age(text: str) -> Optional[int]:
    """Extract age from raw text (English + Armenian patterns)."""
    patterns = [
        re.compile(r"\b(\d{1,2})\s*(?:years?\s+old|yr[s]?\s+old)\b", re.I),
        re.compile(r"\bage[d]?\s+(\d{1,2})\b", re.I),
        re.compile(r",\s*(\d{2})\s*,", re.I),           # "Amara, 27, Accra"
        re.compile(r"\bi['\s]?m\s+(\d{2})\b", re.I),
        # Armenian: "31 տարեկան" (years old in Armenian)
        re.compile(r"\b(\d{1,2})\s+տ(?:արեկան)?\b", re.UNICODE),
        # Armenian age-first: "31  տ." abbreviation
        re.compile(r"\b(\d{2})\s*տ\.", re.UNICODE),
    ]
    for p in patterns:
        m = p.search(text)
        if m:
            age = int(m.group(1))
            if 14 <= age <= 80:
                return age
    return None


def bcp47_to_human(tags: list[str]) -> list[str]:
    """Convert BCP-47 language tags to human-readable names."""
    result = []
    for t in tags:
        label = _BCP47_TO_HUMAN.get(t, t.split("-")[0].capitalize())
        if label not in result:
            result.append(label)
    return result


def detect_armenian_in_text(text: str) -> bool:
    """Return True if the text contains Armenian script characters."""
    return bool(_ARMENIAN_PATTERN.search(text))
