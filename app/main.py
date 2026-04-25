"""
UNMAPPED Protocol v0.2 — Skills Signal Engine
FastAPI application entry point.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("UNMAPPED SSE v0.3-sse-alpha.1 starting up")
    yield
    logger.info("UNMAPPED SSE shutting down")


app = FastAPI(
    title="UNMAPPED Skills Signal Engine",
    description=(
        "UNMAPPED Protocol v0.2 — Module 1: Skills Signal Engine + Evidence Parser.\n\n"
        "Accepts any unstructured single-field text input and produces Verifiable Skill Signals (VSS) "
        "with Human Layer output (profile card, SMS, USSD) for LMIC informal economy workers."
    ),
    version="0.3.0-alpha.1",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow SPA (Claude 2 frontend) to call the API
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

app.include_router(router, prefix="/api/v1", tags=["Skills Signal Engine"])


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.3.0-alpha.1",
        "protocol": "UNMAPPED v0.2",
    }


@app.get("/", tags=["System"])
async def root() -> JSONResponse:
    return JSONResponse({
        "name": "UNMAPPED Skills Signal Engine",
        "version": "0.3.0-alpha.1",
        "protocol": "UNMAPPED v0.2",
        "docs": "/docs",
        "endpoints": {
            "parse": "POST /api/v1/parse",
            "generate_vss": "POST /api/v1/generate_vss",
            "health": "GET /health",
        },
    })
