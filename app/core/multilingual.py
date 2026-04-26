"""
Multilingual semantic similarity layer (v0.3.1 §4.6.2).

Provides:
  AliasMatcher       — exact/case-insensitive/Unicode-NFC alias lookup
                       sourced from country_profile.skill_alias_registry
  MultilingualEmbedder — lazy-loaded Hugging Face encoder for paraphrase
                         scoring in 100+ languages

Design goals
------------
* Pure-CPU inference so the container stays small.
* `intfloat/multilingual-e5-small` (~118 MB) is the default — covers
  English, Russian, Armenian, French, Arabic, Hausa, Swahili, etc.
* `BAAI/bge-m3` is a drop-in upgrade if `UNMAPPED_EMBED_MODEL=BAAI/bge-m3`
  is set in the env (production / GPU deployments).
* The module degrades gracefully: if `transformers`/`torch` are missing,
  the embedder simply reports `available = False` and the parser
  falls back to alias_registry → regex → noun-phrase taxonomy.
* Twi / Ga / Ewe / Hausa low-resource coverage is delivered via
  the alias_registry, NOT via embeddings (no production-grade encoder
  has high recall on those scripts as of v0.3.1).
"""
from __future__ import annotations

import logging
import os
import re
import threading
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AliasHit:
    """Result of an alias-registry lookup."""

    canonical_label: str
    isco_code: str
    category: str
    base_weight: float
    matched_alias: str
    surface_form: str          # the substring in the source text
    language_hint: Optional[str]


@dataclass(frozen=True)
class SemanticHit:
    """Result of an embedding-based paraphrase match."""

    canonical_label: str
    isco_code: str
    category: str
    base_weight: float
    score: float               # cosine similarity 0..1
    surface_form: str


# ---------------------------------------------------------------------------
# Alias matcher — primary low-resource path
# ---------------------------------------------------------------------------


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


class AliasMatcher:
    """Locale-specific alias matcher.

    Looks up multilingual surface forms (Twi / Ga / Armenian / Russian /
    English) against the `skill_alias_registry` block from a country
    profile. Matching is case-insensitive over Unicode-NFC text using
    word-bounded substring search (regex with `re.UNICODE`).

    A single alias entry can match multiple times in the same input;
    `find_all` returns one hit per distinct canonical_label, keyed by
    the longest matched alias (most specific surface form wins).
    """

    _WORD_LEFT = r"(?<![\w])"
    _WORD_RIGHT = r"(?![\w])"

    def __init__(self, registry: list[dict[str, Any]]) -> None:
        self._entries: list[dict[str, Any]] = []
        for entry in registry:
            aliases = entry.get("aliases") or []
            patterns: list[tuple[str, re.Pattern[str]]] = []
            for alias in aliases:
                if not alias:
                    continue
                surf = _nfc(alias).strip()
                if not surf:
                    continue
                pat = re.compile(
                    self._WORD_LEFT + re.escape(surf) + self._WORD_RIGHT,
                    re.IGNORECASE | re.UNICODE,
                )
                patterns.append((surf, pat))
            if not patterns:
                continue
            patterns.sort(key=lambda p: len(p[0]), reverse=True)
            self._entries.append({
                "canonical_label": entry["canonical_label"],
                "isco_code": entry["isco_code"],
                "category": entry["category"],
                "base_weight": float(entry.get("base_weight", 0.78)),
                "language": entry.get("language"),
                "patterns": patterns,
            })

    def __len__(self) -> int:
        return len(self._entries)

    def find_all(self, text: str) -> list[AliasHit]:
        """Return one AliasHit per distinct canonical_label found in text."""
        if not text or not self._entries:
            return []
        haystack = _nfc(text)
        hits: dict[str, AliasHit] = {}
        for entry in self._entries:
            for alias_surf, pattern in entry["patterns"]:
                m = pattern.search(haystack)
                if m is None:
                    continue
                key = entry["canonical_label"]
                if key in hits:
                    continue
                hits[key] = AliasHit(
                    canonical_label=entry["canonical_label"],
                    isco_code=entry["isco_code"],
                    category=entry["category"],
                    base_weight=entry["base_weight"],
                    matched_alias=alias_surf,
                    surface_form=m.group(0),
                    language_hint=entry["language"],
                )
                break
        return list(hits.values())


# ---------------------------------------------------------------------------
# Multilingual embedder — semantic fallback
# ---------------------------------------------------------------------------


_DEFAULT_MODEL = os.environ.get(
    "UNMAPPED_EMBED_MODEL", "intfloat/multilingual-e5-small"
)
_EMBED_DISABLED = os.environ.get("UNMAPPED_EMBED_DISABLE", "").lower() in {
    "1",
    "true",
    "yes",
}
_DEFAULT_THRESHOLD = float(os.environ.get("UNMAPPED_EMBED_THRESHOLD", "0.74"))


class MultilingualEmbedder:
    """Lazy multilingual sentence encoder with mean-pooling.

    Uses the Hugging Face `transformers` AutoModel directly (no
    `sentence_transformers` dependency). Models are downloaded on first
    use and cached under HF_HOME. If the libraries are not available
    (or network access is blocked), `available` becomes False and all
    `encode()` calls return None — the parser then skips the semantic
    stage and falls through to the noun-phrase taxonomy crosswalk.
    """

    _instance: Optional["MultilingualEmbedder"] = None
    _instance_lock = threading.Lock()

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._loaded = False
        self._load_failed = False
        self._init_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def get(cls) -> "MultilingualEmbedder":
        """Process-wide singleton (one model load per worker)."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def available(self) -> bool:
        if _EMBED_DISABLED:
            return False
        if self._load_failed:
            return False
        if self._loaded:
            return True
        return self._try_load()

    def encode(self, texts: list[str], is_query: bool = False) -> Optional[Any]:
        """Encode a batch of texts → L2-normalised numpy matrix (or None).

        E5-family models expect "query: ..." / "passage: ..." prefixes;
        we follow that convention when the configured model name starts
        with ``intfloat/``.
        """
        if not texts:
            return None
        if not self.available:
            return None
        try:
            import numpy as np

            tokens = self._format(texts, is_query=is_query)
            with self._torch.no_grad():
                batch = self._tokenizer(
                    tokens,
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors="pt",
                )
                output = self._model(**batch)
                hidden = output.last_hidden_state
                mask = batch["attention_mask"].unsqueeze(-1).float()
                summed = (hidden * mask).sum(dim=1)
                counts = mask.sum(dim=1).clamp(min=1e-9)
                pooled = summed / counts
                norms = pooled.norm(dim=1, keepdim=True).clamp(min=1e-9)
                normalised = pooled / norms
                return normalised.cpu().numpy().astype(np.float32)
        except Exception as exc:  # noqa: BLE001 — embedder must never crash parser
            logger.warning("MultilingualEmbedder.encode failed: %s", exc)
            self._load_failed = True
            return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _format(self, texts: list[str], is_query: bool) -> list[str]:
        if self.model_name.startswith("intfloat/"):
            prefix = "query: " if is_query else "passage: "
            return [prefix + (t or "") for t in texts]
        return [t or "" for t in texts]

    def _try_load(self) -> bool:
        with self._init_lock:
            if self._loaded:
                return True
            if self._load_failed:
                return False
            try:
                import torch  # type: ignore
                from transformers import AutoModel, AutoTokenizer  # type: ignore

                logger.info("Loading multilingual embedder: %s", self.model_name)
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModel.from_pretrained(self.model_name)
                self._model.eval()
                self._torch = torch
                self._loaded = True
                logger.info("Embedder loaded.")
                return True
            except Exception as exc:  # noqa: BLE001 — degrade quietly
                logger.warning(
                    "Multilingual embedder unavailable (%s) — falling back "
                    "to alias_registry + regex.",
                    exc,
                )
                self._load_failed = True
                return False


# ---------------------------------------------------------------------------
# Cached canonical-label index
# ---------------------------------------------------------------------------


def _registry_signature(registry: list[dict[str, Any]]) -> str:
    parts = []
    for e in registry:
        parts.append(f"{e.get('canonical_label')}|{e.get('isco_code')}")
    return "::".join(parts)


@lru_cache(maxsize=8)
def _encode_canonical_index(
    signature: str,
    labels: tuple[str, ...],
    model_name: str,
) -> Optional[Any]:
    embedder = MultilingualEmbedder.get()
    if embedder.model_name != model_name:
        return None
    return embedder.encode(list(labels), is_query=False)


def semantic_match(
    candidate_phrases: list[str],
    registry: list[dict[str, Any]],
    threshold: float = _DEFAULT_THRESHOLD,
    top_k: int = 5,
) -> list[SemanticHit]:
    """Score each candidate noun-phrase against the canonical labels and
    expanded aliases in the alias_registry. Returns hits whose cosine
    similarity ≥ `threshold`, deduplicated by canonical_label (highest
    score wins).
    """
    if not candidate_phrases or not registry:
        return []
    embedder = MultilingualEmbedder.get()
    if not embedder.available:
        return []

    expanded_labels: list[str] = []
    label_to_entry: dict[str, dict[str, Any]] = {}
    for entry in registry:
        canonical = entry["canonical_label"]
        label_to_entry[canonical] = entry
        expanded_labels.append(canonical)
        for alias in entry.get("aliases", [])[:3]:
            expanded_labels.append(f"{canonical} :: {alias}")
            label_to_entry[f"{canonical} :: {alias}"] = entry

    sig = _registry_signature(registry)
    label_vecs = _encode_canonical_index(
        sig, tuple(expanded_labels), embedder.model_name
    )
    if label_vecs is None:
        return []

    candidate_vecs = embedder.encode(candidate_phrases, is_query=True)
    if candidate_vecs is None:
        return []

    import numpy as np

    sims = candidate_vecs @ label_vecs.T   # shape: (n_cand, n_labels)
    hits: dict[str, SemanticHit] = {}
    for i, phrase in enumerate(candidate_phrases):
        order = np.argsort(-sims[i])[:top_k]
        for j in order:
            score = float(sims[i, j])
            if score < threshold:
                break
            entry = label_to_entry[expanded_labels[j]]
            label = entry["canonical_label"]
            existing = hits.get(label)
            if existing is None or score > existing.score:
                hits[label] = SemanticHit(
                    canonical_label=label,
                    isco_code=entry["isco_code"],
                    category=entry["category"],
                    base_weight=float(entry.get("base_weight", 0.78)),
                    score=round(score, 4),
                    surface_form=phrase.strip(),
                )
    return sorted(hits.values(), key=lambda h: -h.score)


# ---------------------------------------------------------------------------
# Lightweight multilingual phrase extractor
# ---------------------------------------------------------------------------


_SENT_SPLIT = re.compile(r"[.!?\n;]+")
_WORD_PATTERN = re.compile(r"[\w][\w\u0531-\u0587\u0400-\u04FF\u0300-\u036F-]*")


def candidate_phrases(text: str, max_words: int = 4) -> list[str]:
    """Extract candidate noun-phrases for semantic matching.

    Uses lightweight tokenisation that preserves Armenian (U+0530–U+058F)
    and Cyrillic (U+0400–U+04FF) word characters. Sliding-window phrases
    of length 1..max_words; deduplicated; lower-cased.
    """
    if not text:
        return []
    norm = _nfc(text)
    phrases: list[str] = []
    seen: set[str] = set()
    for sentence in _SENT_SPLIT.split(norm):
        words = _WORD_PATTERN.findall(sentence)
        n = len(words)
        for size in range(1, max_words + 1):
            for i in range(0, n - size + 1):
                window = " ".join(words[i:i + size]).lower()
                if len(window) < 3:
                    continue
                if window in seen:
                    continue
                seen.add(window)
                phrases.append(window)
    return phrases


__all__ = [
    "AliasHit",
    "AliasMatcher",
    "MultilingualEmbedder",
    "SemanticHit",
    "candidate_phrases",
    "semantic_match",
]
