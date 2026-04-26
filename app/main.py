"""
UNMAPPED Protocol v0.2 — Skills Signal Engine
FastAPI application entry point.

Endpoints:
  POST /parse              — primary SPA endpoint (frontend contract v0.3)
  POST /api/v1/parse       — legacy alias
  POST /api/v1/generate_profile_card — explicit card regeneration
  GET  /health
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.employer import router as employer_router
from app.api.routes import public_router, v1_router
from app.db.session import dispose_engine, init_db
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("UNMAPPED SSE v0.4 starting — GH + AM profiles loaded")
    # DB is best-effort. init_db() logs and returns False on failure;
    # the app keeps serving /parse in stateless mode.
    await init_db()
    yield
    await dispose_engine()
    logger.info("UNMAPPED SSE shutting down")


app = FastAPI(
    title="UNMAPPED Skills Signal Engine",
    description=(
        "UNMAPPED Protocol v0.2 — Module 1: Skills Signal Engine.\n\n"
        "POST /parse accepts any chaotic free-form text (any language) and returns "
        "a complete ProfileCard: skills, wage signal, growth signal, network entry, "
        "SMS summary, and USSD menu. Supports GH (Ghana) and AM (Armenia)."
    ),
    version="0.3.2",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — SPA (http://localhost:5173 Vite dev) + production origins
_CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Primary public endpoint — SPA calls POST /parse
app.include_router(public_router, tags=["Skills Signal Engine"])

# Legacy / internal v1 prefix
app.include_router(v1_router, prefix="/api/v1", tags=["v1 (legacy)"])

# Employer + policymaker read API (bearer-token gated, DB-backed)
app.include_router(employer_router, prefix="/api/v1", tags=["Employer API"])


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.3.2",
        "protocol": "UNMAPPED v0.2",
    }


@app.get("/", tags=["System"])
async def root() -> JSONResponse:
    return JSONResponse({
        "name": "UNMAPPED Skills Signal Engine",
        "version": "0.3.2",
        "protocol": "UNMAPPED v0.2",
        "docs": "/docs",
        "endpoints": {
            "parse": "POST /parse",
            "parse_legacy": "POST /api/v1/parse",
            "generate_profile_card": "POST /api/v1/generate_profile_card",
            "health": "GET /health",
        },
    })
