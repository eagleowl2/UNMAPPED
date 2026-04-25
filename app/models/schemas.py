"""
Pydantic v2 request/response models for the SSE API.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ParseRequest(BaseModel):
    """POST /parse — single chaotic text input."""
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Any unstructured personal/professional text in any language.",
        examples=["My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube"],
    )
    country_code: str = Field(
        default="GH",
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code for context.",
    )
    context_tag: str = Field(
        default="urban_informal",
        description="Context tag matching a loaded country profile.",
    )

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        return v.upper()


class GenerateVSSRequest(BaseModel):
    """POST /generate_vss — generate VSS from already-parsed output."""
    user: dict[str, Any] = Field(..., description="USER entity dict from /parse response.")
    skills: list[dict[str, Any]] = Field(..., min_length=1, description="SKILL entities from /parse response.")
    country_code: str = Field(default="GH")
    context_tag: str = Field(default="urban_informal")

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        return v.upper()


class HealthResponse(BaseModel):
    status: str
    version: str
    protocol: str


class ParseResponse(BaseModel):
    """Full response from POST /parse."""
    ok: bool
    user: dict[str, Any]
    skills: list[dict[str, Any]]
    vss_list: list[dict[str, Any]]
    human_layer: dict[str, Any]
    meta: dict[str, Any]


class VSSResponse(BaseModel):
    ok: bool
    vss_list: list[dict[str, Any]]
    human_layer: dict[str, Any]
    meta: dict[str, Any]


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    detail: Optional[str] = None
