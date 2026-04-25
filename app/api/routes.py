"""
FastAPI route definitions for the Skills Signal Engine.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.parser import EvidenceParser
from app.models.schemas import (
    ErrorResponse,
    GenerateVSSRequest,
    ParseRequest,
    ParseResponse,
    VSSResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Parser cache: (country_code, context_tag) → EvidenceParser instance
_parser_cache: dict[tuple[str, str], EvidenceParser] = {}


def _get_parser(country_code: str, context_tag: str) -> EvidenceParser:
    key = (country_code, context_tag)
    if key not in _parser_cache:
        _parser_cache[key] = EvidenceParser(
            country_code=country_code,
            context_tag=context_tag,
        )
    return _parser_cache[key]


@router.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse chaotic single-field input",
    description=(
        "Accepts one unstructured text input (any language, any format) and returns:\n"
        "- One USER entity\n"
        "- One or more SKILL entities\n"
        "- Full VSS list (one per skill)\n"
        "- HumanLayer (profile card, SMS ≤160 chars, USSD tree)\n\n"
        "Zero-credential path is automatically applied for LMIC informal economy contexts."
    ),
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Parser error"},
    },
)
async def parse_input(body: ParseRequest) -> dict[str, Any]:
    """Parse chaotic single-field input → USER + SKILL entities → VSS + HumanLayer."""
    t0 = time.perf_counter()
    try:
        parser = _get_parser(body.country_code, body.context_tag)
        result = parser.parse(body.text)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Parser error for input: %s...", body.text[:80])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parser error: {exc}",
        ) from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "user": result["user"],
        "skills": result["skills"],
        "vss_list": result["vss_list"],
        "human_layer": result["human_layer"],
        "meta": {
            "country_code": body.country_code,
            "context_tag": body.context_tag,
            "skills_detected": len(result["skills"]),
            "processing_time_ms": elapsed_ms,
            "parser_version": "v0.3-sse-alpha.1",
        },
    }


@router.post(
    "/generate_vss",
    response_model=VSSResponse,
    summary="Generate VSS from pre-parsed entities",
    description=(
        "Takes USER and SKILL entities (from /parse) and regenerates "
        "VSS list + HumanLayer. Useful for re-scoring or channel-specific rendering."
    ),
)
async def generate_vss(body: GenerateVSSRequest) -> dict[str, Any]:
    """Regenerate VSS + HumanLayer from existing parsed entities."""
    t0 = time.perf_counter()
    try:
        parser = _get_parser(body.country_code, body.context_tag)

        from app.core.parser import ExtractedUser, ExtractedSkill
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        # Reconstruct ExtractedUser from dict
        u = body.user
        user_obj = ExtractedUser(
            user_id=u.get("user_id", "usr_unknown"),
            display_name=u.get("display_name"),
            location=u.get("location", {}),
            languages=u.get("languages", []),
            source_text_hash=u.get("source_text_hash", ""),
            zero_credential=u.get("zero_credential", True),
            raw_text=u.get("raw_text", ""),
        )

        # Reconstruct ExtractedSkill list
        skill_objs = []
        for s in body.skills:
            skill_objs.append(ExtractedSkill(
                skill_id=s.get("skill_id", "skl_unknown"),
                label=s.get("label", ""),
                category=s.get("category", "other"),
                source_phrases=s.get("source_phrases", [s.get("label", "")]),
                experience_signals=s.get("experience_signals", []),
                evidence_weight=s.get("evidence_weight", 0.5),
                extra_signals=s.get("extra_signals", {}),
            ))

        vss_list = parser._build_vss_list(user_obj, skill_objs, now)
        human_layer = parser._build_human_layer(user_obj, vss_list, now)

    except Exception as exc:
        logger.exception("generate_vss error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"VSS generation error: {exc}",
        ) from exc

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "vss_list": vss_list,
        "human_layer": human_layer,
        "meta": {
            "country_code": body.country_code,
            "context_tag": body.context_tag,
            "vss_generated": len(vss_list),
            "processing_time_ms": elapsed_ms,
        },
    }
