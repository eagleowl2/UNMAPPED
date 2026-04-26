"""
Armenian text normalisation for the Skills Signal Engine (v0.3.4).

Why this module exists
----------------------
The previous architecture relied on a multilingual sentence-transformer
(`intfloat/multilingual-e5-small`) to bridge low-resource Armenian inputs to
canonical skill labels. In practice the embedder produced near-zero recall on:

  * heavily abbreviated CV-style Armenian ("թ.-ն. ռ. ու հ." = translator
    from Russian to Armenian) — single-letter tokens carry no semantic
    signal at the embedding layer;
  * mixed Armenian/Russian/Latin script paragraphs;
  * informal punctuation-heavy phrasing.

It also added a hard `torch + transformers` dependency (~700 MB) that
fails to load on most hackathon dev machines, demoting the parser
permanently to alias_registry + regex.

This module replaces the embedding stage with a two-tier, offline-first
normaliser:

    Tier A — Deterministic abbreviation expander (always on, offline).
             Pure regex; expands the small closed set of CV-style Armenian
             abbreviations the parser observes in the demo corpus.

    Tier B — Lightweight LLM fallback over OpenRouter (default) or
             Anthropic direct. Triggered only when (a) Armenian script
             detected, (b) Tier A plus the existing alias/regex pipeline
             returned <2 skills, and (c) an API key is set. Cached by
             text hash. Uses `httpx` (already a project dep) — no new
             SDK dependency required.

Both tiers degrade silently: if the API key is missing or a call times
out, the parser falls back to its existing behaviour. There is no new
hard dependency on the hot path.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


_ARMENIAN_SCRIPT_RE = re.compile(r"[Ա-և]")


def has_armenian_script(text: str) -> bool:
    return bool(_ARMENIAN_SCRIPT_RE.search(text or ""))


# ---------------------------------------------------------------------------
# Tiny .env loader — populates os.environ once at import time.
# Keeps secrets out of source while avoiding a python-dotenv dependency.
# ---------------------------------------------------------------------------


def _load_dotenv_once() -> None:
    if os.environ.get("_UNMAPPED_DOTENV_LOADED"):
        return
    candidates = [
        Path(__file__).resolve().parent.parent.parent / ".env",  # repo root
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                # Don't overwrite values explicitly set in the real env.
                os.environ.setdefault(key, value)
        except OSError:
            continue
    os.environ["_UNMAPPED_DOTENV_LOADED"] = "1"


_load_dotenv_once()


# ---------------------------------------------------------------------------
# Tier A — deterministic abbreviation expander
# ---------------------------------------------------------------------------
#
# Each rule is (compiled_pattern, expansion_phrase). The expansion is a full
# Armenian word (or short phrase) that the existing regex / alias_registry
# already recognises. We APPEND expansions to the original text rather than
# substitute; that keeps original surface-form phrasing intact for the
# context-window snippet the parser stores in `source_phrases`.

_ABBREV_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"թ\.\s*[-–—]?\s*(?:ն\.|ից|ի)?\s*"
            r"(?:ռ\.|հ\.|անգլ\.|ռուս\.)",
            re.UNICODE | re.IGNORECASE,
        ),
        "թարգմանիչ",
    ),
    (re.compile(r"\bթարգ\.", re.UNICODE | re.IGNORECASE), "թարգմանում"),
    (
        re.compile(r"\bծ\.\s*ե\.", re.UNICODE | re.IGNORECASE),
        "ծրագրավորող",
    ),
    (re.compile(r"\bդաս\.", re.UNICODE | re.IGNORECASE), "դասավանդում"),
    (
        re.compile(r"\bկ\.\s*(?:և|ու)\s*ձ\.", re.UNICODE | re.IGNORECASE),
        "դերձակ կարուհի",
    ),
    (re.compile(r"\bԱնգլ\.", re.UNICODE), "Անգլերեն"),
    (
        re.compile(
            r"(?:թարգ|դաս|ուսուց|թ\.|դ\.)[^\n]{0,8}\bռ(?:ուս)?\.",
            re.UNICODE | re.IGNORECASE,
        ),
        "ռուսերեն",
    ),
    (
        re.compile(
            r"(?:թարգ|դաս|ուսուց|թ\.|դ\.)[^\n]{0,12}\bհ\.",
            re.UNICODE | re.IGNORECASE,
        ),
        "հայերեն",
    ),
    (re.compile(r"\bվ\.\s*է\b|\bվ\.\s*եմ\b", re.UNICODE | re.IGNORECASE), "վարորդ"),
    (re.compile(r"\bGym\.", re.IGNORECASE), "Գյումրի"),
]


def expand_armenian_abbreviations(text: str) -> str:
    """Append deterministic abbreviation expansions to Armenian input.

    The original text is preserved verbatim; expansions are concatenated
    after a marker so the existing alias/regex stages can match the
    canonical forms while `source_phrases` still record the original
    abbreviated surface form.
    """
    if not has_armenian_script(text):
        return text
    expansions: list[str] = []
    seen: set[str] = set()
    for pattern, replacement in _ABBREV_RULES:
        if pattern.search(text) and replacement not in seen:
            expansions.append(replacement)
            seen.add(replacement)
    if not expansions:
        return text
    return f"{text}\n[hy-expansions] {' '.join(expansions)}"


# ---------------------------------------------------------------------------
# Tier B — OpenRouter / Anthropic chat completion
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LLMNormalisation:
    english_phrases: str        # space-separated canonical English skill phrases
    source: str                 # "openrouter" | "anthropic" | "cache" | "disabled" | "error"


# Backend selector: "openrouter" (default) or "anthropic".
_LLM_BACKEND = os.environ.get("UNMAPPED_LLM_BACKEND", "openrouter").lower()
_LLM_MODEL = os.environ.get(
    "UNMAPPED_LLM_MODEL",
    "anthropic/claude-haiku-4.5"
    if _LLM_BACKEND == "openrouter"
    else "claude-haiku-4-5-20251001",
)
_LLM_TIMEOUT_S = float(os.environ.get("UNMAPPED_LLM_TIMEOUT_S", "8.0"))
_LLM_MAX_TOKENS = int(os.environ.get("UNMAPPED_LLM_MAX_TOKENS", "200"))
_LLM_DISABLED = os.environ.get("UNMAPPED_LLM_DISABLE", "").lower() in {
    "1",
    "true",
    "yes",
}

_OPENROUTER_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).rstrip("/") + "/chat/completions"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

_SYSTEM_PROMPT = (
    "You normalise short Armenian / Russian / mixed-script worker "
    "self-descriptions into a flat list of canonical ENGLISH skill phrases "
    "for a job-skills extraction pipeline. The input is informal, often "
    "heavily abbreviated (e.g. 'թ.-ն. ռ. ու հ.' = 'translator from Russian "
    "to Armenian'; 'ծ. ե.' = 'programmer'; 'կ. և ձ.' = 'sewing and "
    "tailoring'). Output ONLY a comma-separated list of 1-6 short English "
    "skill phrases. No commentary, no Armenian text, no quotation marks, "
    "no numbering. Use the canonical labels: teacher, tutor, translator, "
    "interpreter, software developer, programmer, web developer, driver, "
    "taxi driver, tailor, seamstress, accountant, bookkeeper, hairdresser, "
    "cook, shopkeeper, trader, mobile money agent, graphic designer, "
    "construction worker, farmer. If the input describes none of these, "
    "output exactly: NONE."
)


def _resolve_api_key() -> Optional[str]:
    """Return the API key for the active backend, or None."""
    if _LLM_BACKEND == "openrouter":
        return os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
            "OPEN_ROUTER_API_KEY"
        )
    return os.environ.get("ANTHROPIC_API_KEY")


class ArmenianLLMNormaliser:
    """Singleton wrapper around the OpenRouter / Anthropic chat endpoint.

    Uses `httpx` (already a project dep). If no API key is available, the
    normaliser self-disables and every `normalise` call returns
    `LLMNormalisation('', 'disabled')`.

    Successful normalisations are cached in-process by SHA-256 of the input
    text so repeat calls (test re-runs, idempotent SPA reloads) don't burn
    tokens.
    """

    _instance: Optional["ArmenianLLMNormaliser"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._client_failed = False
        self._init_lock = threading.Lock()
        self._cache: dict[str, str] = {}

    @classmethod
    def get(cls) -> "ArmenianLLMNormaliser":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def available(self) -> bool:
        if _LLM_DISABLED:
            return False
        if self._client_failed:
            return False
        if self._api_key is not None:
            return True
        return self._try_init()

    def normalise(self, text: str) -> LLMNormalisation:
        if not text or not text.strip():
            return LLMNormalisation("", "disabled")
        if not self.available:
            return LLMNormalisation("", "disabled")

        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cached = self._cache.get(key)
        if cached is not None:
            return LLMNormalisation(cached, "cache")

        try:
            if _LLM_BACKEND == "openrouter":
                cleaned, source = self._call_openrouter(text)
            else:
                cleaned, source = self._call_anthropic(text)
            if cleaned:
                self._cache[key] = cleaned
            return LLMNormalisation(cleaned, source)
        except Exception as exc:  # noqa: BLE001 — must never crash parser
            logger.warning("Armenian LLM normalisation failed: %s", exc)
            self._client_failed = True
            return LLMNormalisation("", "error")

    # ------------------------------------------------------------------
    # Backend calls
    # ------------------------------------------------------------------

    def _call_openrouter(self, text: str) -> tuple[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/eagleowl2/UNMAPPED",
            "X-Title": "UNMAPPED Skills Signal Engine",
        }
        payload = {
            "model": _LLM_MODEL,
            "max_tokens": _LLM_MAX_TOKENS,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }
        with httpx.Client(timeout=_LLM_TIMEOUT_S) as client:
            response = client.post(_OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return "", "openrouter"
        content = choices[0].get("message", {}).get("content", "") or ""
        return _clean_llm_output(content), "openrouter"

    def _call_anthropic(self, text: str) -> tuple[str, str]:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": _LLM_MODEL,
            "max_tokens": _LLM_MAX_TOKENS,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": text}],
        }
        with httpx.Client(timeout=_LLM_TIMEOUT_S) as client:
            response = client.post(_ANTHROPIC_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        blocks = data.get("content") or []
        if not blocks:
            return "", "anthropic"
        content = blocks[0].get("text", "") or ""
        return _clean_llm_output(content), "anthropic"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _try_init(self) -> bool:
        with self._init_lock:
            if self._api_key is not None:
                return True
            if self._client_failed:
                return False
            api_key = _resolve_api_key()
            if not api_key:
                logger.info(
                    "%s API key not set — Armenian LLM stage disabled "
                    "(deterministic abbreviation expander still active).",
                    _LLM_BACKEND.title(),
                )
                self._client_failed = True
                return False
            self._api_key = api_key
            logger.info(
                "Armenian LLM normaliser ready (backend=%s, model=%s).",
                _LLM_BACKEND,
                _LLM_MODEL,
            )
            return True


def _clean_llm_output(raw: str) -> str:
    """Strip stray quoting / explanation lines from LLM output."""
    if not raw:
        return ""
    text = raw.strip()
    if text.upper().startswith("NONE"):
        return ""
    text = text.splitlines()[0].strip()
    text = text.strip("\"'`")
    return text.replace(",", " ").strip()


# ---------------------------------------------------------------------------
# Public entry point used by the parser
# ---------------------------------------------------------------------------


def normalise_for_skills(
    text: str,
    *,
    skills_already_found: int = 0,
    skill_threshold: int = 2,
) -> tuple[str, str]:
    """Return `(normalised_text, source)`.

    * Always runs the Tier-A abbreviation expander on Armenian input.
    * Runs Tier-B (LLM) only when Armenian script is present, fewer than
      `skill_threshold` skills have been extracted upstream, and the LLM
      is available.
    """
    if not has_armenian_script(text):
        return text, "noop"

    expanded = expand_armenian_abbreviations(text)
    if skills_already_found >= skill_threshold:
        return expanded, "tier-a"

    llm = ArmenianLLMNormaliser.get()
    if not llm.available:
        return expanded, "tier-a"

    result = llm.normalise(text)
    if not result.english_phrases:
        return expanded, f"tier-a+{result.source}"

    augmented = f"{expanded}\n[hy-llm] {result.english_phrases}"
    return augmented, f"tier-a+{result.source}"


__all__ = [
    "ArmenianLLMNormaliser",
    "LLMNormalisation",
    "expand_armenian_abbreviations",
    "has_armenian_script",
    "normalise_for_skills",
]
