"""
FastAPI routes for the Skills Signal Engine.

Primary endpoint: POST /parse  (matches frontend contract docs/api-contract.md)
Legacy endpoint:  POST /api/v1/parse (retained for backward compat, same logic)
"""
from __future__ import annotations

import logging
import os
import time
import traceback
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.parser import EvidenceParser
from app.models.schemas import (
    ParseError,
    ParseRequest,
    ParseResponse,
    ProfileCard,
    HealthResponse,
)

logger = logging.getLogger(__name__)

# When set (default in dev), the /parse error response includes the actual
# exception class + message so the SPA shows it directly instead of the
# generic "Internal parser error". Disable in production by setting to "0".
_VERBOSE_ERRORS = os.getenv("UNMAPPED_VERBOSE_ERRORS", "1") != "0"

# ---------------------------------------------------------------------------
# Two routers:
#   public_router  — mounted at "/" for the /parse endpoint the SPA calls
#   v1_router      — mounted at "/api/v1" for legacy / internal use
# ---------------------------------------------------------------------------
public_router = APIRouter()
v1_router = APIRouter()

# Parser cache: country_code → EvidenceParser instance
_parser_cache: dict[str, EvidenceParser] = {}


def _get_parser(country: str) -> EvidenceParser:
    key = country.upper()
    if key not in _parser_cache:
        _parser_cache[key] = EvidenceParser(
            country_code=key,
            context_tag="urban_informal",
        )
    return _parser_cache[key]


# ---------------------------------------------------------------------------
# Shared parse logic
# ---------------------------------------------------------------------------

def _do_parse(req: ParseRequest, t0: float) -> dict[str, Any]:
    """Execute parse and return the full response dict."""
    parser = _get_parser(req.country)
    profile_dict = parser.parse_for_profile(req.raw_input)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "profile": profile_dict,
        "latency_ms": latency_ms,
        "country": req.country.upper(),
        "parser_version": "sse-0.3.2",
    }


# ---------------------------------------------------------------------------
# Primary public endpoint — POST /parse
# SPA calls: ${API_URL}/parse where API_URL = http://localhost:8000
# ---------------------------------------------------------------------------

_PARSE_DESCRIPTION = """
Accept any free-form personal/professional text in any language and return
a complete ProfileCard with skills, wage signal, growth signal, network entry,
SMS summary, and USSD menu.

Supports `country: "GH"` (Ghana, English/Twi/Ga) and `country: "AM"` (Armenia, Armenian/Russian).

On any parser error returns `{"ok": false, "error": "...", "code": "..."}` per
the frontend contract — the SPA falls back to its bundled mock automatically.
"""


@public_router.post(
    "/parse",
    summary="Parse chaotic input → ProfileCard",
    description=_PARSE_DESCRIPTION,
    responses={
        200: {"description": "ProfileCard produced"},
        422: {"model": ParseError},
    },
)
async def parse_public(body: ParseRequest) -> JSONResponse:
    t0 = time.perf_counter()
    # Log inputs at DEBUG so we can correlate failures with the exact text
    # that triggered them. raw_input is truncated to 200 chars to avoid
    # blowing out the log on large payloads.
    snippet = (body.raw_input[:200] + "…") if len(body.raw_input) > 200 else body.raw_input
    logger.info(
        "[/parse] country=%s len=%d input=%r",
        body.country, len(body.raw_input), snippet,
    )
    try:
        result = _do_parse(body, t0)
        return JSONResponse(content=result)
    except FileNotFoundError as exc:
        logger.warning("Country profile not found: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_200_OK,  # frontend expects 200 on errors too
            content={"ok": False, "error": str(exc), "code": "UNSUPPORTED_LOCALE"},
        )
    except ValueError as exc:
        logger.warning(
            "[/parse] ValueError for country=%s input=%r: %s",
            body.country, snippet, exc,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"ok": False, "error": str(exc), "code": "PARSER_FAILURE"},
        )
    except Exception as exc:
        # Always log the full traceback to backend stderr.
        logger.exception(
            "[/parse] UNEXPECTED parser error for country=%s input=%r",
            body.country, snippet,
        )
        # In dev (default), surface the actual exception in the SPA so the
        # user can copy-paste it back. Set UNMAPPED_VERBOSE_ERRORS=0 in prod.
        if _VERBOSE_ERRORS:
            error_msg = f"{type(exc).__name__}: {exc}"
            tb_tail = traceback.format_exc().splitlines()[-6:]
        else:
            error_msg = "Internal parser error"
            tb_tail = []
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "ok": False,
                "error": error_msg,
                "code": "PARSER_FAILURE",
                **({"traceback_tail": tb_tail} if tb_tail else {}),
            },
        )


# ---------------------------------------------------------------------------
# Legacy V1 endpoint — POST /api/v1/parse (same logic, kept for backward compat)
# ---------------------------------------------------------------------------

@v1_router.post(
    "/parse",
    summary="[v1] Parse chaotic input → ProfileCard (legacy path)",
    include_in_schema=True,
)
async def parse_v1(body: ParseRequest) -> JSONResponse:
    return await parse_public(body)


# ---------------------------------------------------------------------------
# /generate_profile_card — explicit card regeneration from parsed entities
# (optional, exposes same logic as /parse for SPA override scenarios)
# ---------------------------------------------------------------------------

@v1_router.post(
    "/generate_profile_card",
    summary="Regenerate ProfileCard from pre-parsed data",
    description=(
        "Pass `raw_input` + `country` to force a fresh profile card build. "
        "Identical to /parse — exists for SPA components that call it separately."
    ),
)
async def generate_profile_card(body: ParseRequest) -> JSONResponse:
    return await parse_public(body)
