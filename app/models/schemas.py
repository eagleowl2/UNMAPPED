"""
Pydantic v2 request/response models for the SSE API.

Request/response shape matches the frontend contract in docs/api-contract.md
and frontend/src/lib/types.ts exactly.
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    """
    POST /parse — frontend contract.
    Field names mirror frontend/src/lib/types.ts ParseRequest exactly.
    """
    raw_input: str = Field(
        ...,
        min_length=3,
        max_length=8000,
        description="Free-form chaotic input in any language.",
        examples=["My name is Amara, I fix phones in Accra, speak Twi English Ga"],
    )
    country: Literal["GH", "AM"] = Field(
        ...,
        description="Country profile: GH (Ghana) or AM (Armenia).",
    )
    language_hint: Optional[str] = Field(
        default=None,
        description="Optional ISO 639-1 language hint; backend may auto-detect.",
    )

    @field_validator("country", mode="before")
    @classmethod
    def upper_country(cls, v: str) -> str:
        return v.upper()


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------

class Skill(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None


class Signal(BaseModel):
    score: int = Field(ge=0, le=100)
    rationale: str
    display_value: Optional[str] = None


class NetworkEntryPoint(BaseModel):
    channel: str
    lat: float
    lng: float
    label: str


class AutomationRisk(BaseModel):
    """Module 2 — AI Readiness & Displacement Risk Lens (LMIC-calibrated).

    Combines Frey & Osborne (2017) raw automation probability for the top
    occupation with an ILO Future-of-Work LMIC adjustment factor. Rationale
    cites every source used.
    """
    automation_probability: float = Field(ge=0.0, le=1.0)
    raw_probability: float = Field(ge=0.0, le=1.0)
    risk_tier: Literal["low", "medium", "high"]
    trajectory_2035: Literal["growing", "stable", "declining"]
    durable_skills: list[str] = Field(default_factory=list, max_length=6)
    adjacent_skills: list[str] = Field(default_factory=list, max_length=6)
    rationale: str
    sources: list[str] = Field(default_factory=list)


class NeetContext(BaseModel):
    """Data360 / ILOSTAT NEET rate (Signal 4) for the user's country."""
    neet_pct: float = Field(ge=0.0, le=100.0)
    narrative: str
    source: str
    year: int


class BonaSubScore(BaseModel):
    """One of the three BONA sub-audits."""
    score: float = Field(ge=0.0, le=1.0)
    tier: Literal["low", "medium", "high"]


class BonaGhostScore(BonaSubScore):
    """Ghost-listing audit also exposes the number of flagged listings."""
    ghost_count: int = Field(ge=0)


class BonaReport(BaseModel):
    """UNMAPPED Protocol v0.2 §6.7 — Bidirectional Opaque Network Auditor.

    Three deterministic sub-scores plus a flag list, all derived from
    non-PII signals (channels, languages, opportunity metadata). Optional
    on the wire so older SPA versions render unchanged.
    """
    overall_score: float = Field(ge=0.0, le=1.0)
    overall_tier: Literal["low", "medium", "high"]
    network_capture: BonaSubScore
    ghost_listings: BonaGhostScore
    programme_leakage: BonaSubScore
    flags: list[str] = Field(default_factory=list, max_length=8)
    rationale: str
    sources: list[str] = Field(default_factory=list)
class OpportunityEntry(BaseModel):
    title: str
    employer_type: str
    channel: str
    lat: float
    lng: float
    label: str
    wage_range: str
    isco_code: str
    formalization_path: str
    match_score: float = Field(ge=0.0, le=1.0)


class JobMatchSignal(BaseModel):
    score: int = Field(ge=0, le=100)
    rationale: str
    opportunity_count: int
    matched_opportunities: list[OpportunityEntry]


class ProfileCard(BaseModel):
    profile_id: str
    display_name: str
    pseudonym: str
    age: Optional[int] = None
    location: str
    languages: list[str]
    skills: list[Skill] = Field(min_length=1, max_length=8)
    wage_signal: Signal
    growth_signal: Signal
    job_match: Optional[JobMatchSignal] = None
    network_entry: NetworkEntryPoint
    sms_summary: str = Field(max_length=320)
    ussd_menu: list[str] = Field(min_length=4, max_length=8)
    # v0.3.2 — Module 2 (automation risk) and Signal 4 (NEET) — optional so
    # existing SPA versions render unchanged.
    automation_risk: Optional[AutomationRisk] = None
    neet_context: Optional[NeetContext] = None
    # v0.4 — BONA forensic audit (§6.7). Optional for backward compat.
    bona: Optional[BonaReport] = None


class ParseResponse(BaseModel):
    """Successful parse response — mirrors frontend ParseResponse exactly."""
    ok: Literal[True] = True
    profile: ProfileCard
    latency_ms: float
    country: Literal["GH", "AM"]
    parser_version: str


class ParseError(BaseModel):
    """Error response — mirrors frontend ParseError exactly."""
    ok: Literal[False] = False
    error: str
    code: Optional[str] = None


# ---------------------------------------------------------------------------
# System models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    protocol: str
