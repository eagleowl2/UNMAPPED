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
