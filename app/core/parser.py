"""
Skills Signal Engine — Evidence Parser.

Accepts one chaotic unstructured text input (any language, any format) and
produces: USER entity + N SKILL entities + VSS objects + HumanLayer.

Pipeline:
  raw_text
    → language detection
    → NER / pattern extraction (name, location, languages, skills, experience)
    → taxonomy crosswalk (NetworkX)
    → Bayesian confidence scoring (Beta conjugate)
    → VSS assembly
    → HumanLayer rendering (Jinja2)
"""
from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.bayesian import compute_confidence
from app.core.country_profile import (
    get_confidence_priors,
    get_local_skill_overrides,
    is_zero_credential_context,
    load_country_profile,
)
from app.core.taxonomy import TaxonomyGraph

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill pattern catalog (regex + weight) — language-agnostic heuristics
# These fire BEFORE spaCy NER and act as lightweight keyword extractors.
# ---------------------------------------------------------------------------

_SKILL_PATTERNS: list[tuple[re.Pattern[str], str, str, float]] = [
    # (pattern, canonical_label, category, base_evidence_weight)
    (re.compile(r"\b(fix(?:ing)?|repair(?:ing)?)\s+(?:mobile\s+)?phone[s]?\b", re.I), "Phone Repair", "technical", 0.75),
    (re.compile(r"\bphone\s+(?:repair(?:er|ing)?|technician|fixer)\b", re.I), "Phone Repair", "technical", 0.78),
    (re.compile(r"\bmobile\s+(?:repair|technician)\b", re.I), "Phone Repair", "technical", 0.76),
    (re.compile(r"\belectronics?\s+repair\b", re.I), "Electronics Repair", "technical", 0.70),
    (re.compile(r"\bscreen\s+(?:replacement|repair|fix)\b", re.I), "Screen Repair", "technical", 0.68),
    (re.compile(r"\bcod(?:e|ing|er)\b", re.I), "Software Development", "digital", 0.65),
    (re.compile(r"\bprogramm(?:ing|er)\b", re.I), "Software Development", "digital", 0.70),
    (re.compile(r"\bweb\s+dev(?:elop(?:ment|er))?\b", re.I), "Web Development", "digital", 0.72),
    (re.compile(r"\bpython\b", re.I), "Python Programming", "digital", 0.60),
    (re.compile(r"\bjavascript\b", re.I), "JavaScript Programming", "digital", 0.60),
    (re.compile(r"\bhtml\b", re.I), "HTML/CSS", "digital", 0.55),
    (re.compile(r"\bteach(?:ing|er)?\b", re.I), "Teaching", "other", 0.65),
    (re.compile(r"\btutor(?:ing)?\b", re.I), "Tutoring", "other", 0.65),
    (re.compile(r"\btailoring\b", re.I), "Tailoring", "trade", 0.75),
    (re.compile(r"\bsewing\b", re.I), "Sewing", "trade", 0.70),
    (re.compile(r"\bdriv(?:ing|er)\b", re.I), "Driving", "trade", 0.60),
    (re.compile(r"\bdeliver(?:y|ies|ing)\b", re.I), "Delivery Services", "trade", 0.55),
    (re.compile(r"\bfarming\b", re.I), "Farming", "agricultural", 0.70),
    (re.compile(r"\bagriculture\b", re.I), "Agriculture", "agricultural", 0.70),
    (re.compile(r"\bchildcare\b", re.I), "Childcare", "care", 0.72),
    (re.compile(r"\bnurse\b|\bnursing\b", re.I), "Nursing/Care", "care", 0.68),
    (re.compile(r"\baccounting\b|\baccountant\b", re.I), "Accounting", "financial", 0.72),
    (re.compile(r"\bbook(?:keeping|keeper)\b", re.I), "Bookkeeping", "financial", 0.70),
    (re.compile(r"\bdesign(?:er|ing)?\b", re.I), "Design", "creative", 0.60),
    (re.compile(r"\bphotograph(?:y|er|ing)\b", re.I), "Photography", "creative", 0.68),
    (re.compile(r"\bvideo\s+editing\b", re.I), "Video Editing", "creative", 0.65),
    (re.compile(r"\bsocial\s+media\b", re.I), "Social Media Management", "digital", 0.58),
    (re.compile(r"\bdata\s+entry\b", re.I), "Data Entry", "digital", 0.60),
]

# Experience signal patterns
_EXPERIENCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(\d+)\s*(?:year|yr)s?\s*(?:of\s+)?(?:experience|exp|doing)", re.I), "years_experience"),
    (re.compile(r"(\d+)\s*(?:year|yr)s?\s*(?:in|working)", re.I), "years_experience"),
    (re.compile(r"(?:since|from)\s+(?:20|19)(\d{2})", re.I), "since_year"),
    (re.compile(r"(\d+)\s*clients?\b", re.I), "client_count"),
    (re.compile(r"(\d+)\s*customers?\b", re.I), "client_count"),
    (re.compile(r"(\d+)\s*(?:phone|device)s?\s+(?:per|a)\s+(?:week|month|day)", re.I), "volume_per_period"),
    (re.compile(r"learned\s+(?:on|from|via|through)\s+youtube\b", re.I), "self_taught_digital"),
    (re.compile(r"self[\s-]?taught\b", re.I), "self_taught"),
    (re.compile(r"taught\s+(?:my)?self\b", re.I), "self_taught"),
    (re.compile(r"online\s+course[s]?\b", re.I), "online_learning"),
]

# Name extraction patterns
_NAME_PATTERNS = [
    re.compile(r"(?:my\s+name\s+is|i(?:'m|\s+am)|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.I),
    re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*(?:i\s+am|i'm|is\s+a)", re.I),
]

# Location patterns
_LOCATION_PATTERNS = [
    re.compile(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\blive[s]?\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\bbased\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
]

# Language mention patterns (maps detected language words to BCP-47)
_LANGUAGE_MAP: dict[str, str] = {
    "english": "en",
    "twi": "ak-GH",
    "akan": "ak-GH",
    "ga": "gaa",
    "ewe": "ee-GH",
    "hausa": "ha",
    "french": "fr",
    "arabic": "ar",
    "swahili": "sw",
    "yoruba": "yo",
    "igbo": "ig",
    "amharic": "am",
    "somali": "so",
    "wolof": "wo",
}

_LANGUAGE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _LANGUAGE_MAP) + r")\b",
    re.I,
)


@dataclass
class ExtractedUser:
    user_id: str
    display_name: Optional[str]
    location: dict[str, str]
    languages: list[str]
    source_text_hash: str
    zero_credential: bool
    raw_text: str


@dataclass
class ExtractedSkill:
    skill_id: str
    label: str
    category: str
    source_phrases: list[str]
    experience_signals: list[str]
    evidence_weight: float
    extra_signals: dict[str, Any]


class EvidenceParser:
    """
    Core parser: raw text → USER + SKILL entities → VSS + HumanLayer.

    Usage:
        parser = EvidenceParser(country_code="GH", context_tag="urban_informal")
        result = parser.parse("My name is Amara, I fix phones in Accra...")
    """

    def __init__(
        self,
        country_code: str = "GH",
        context_tag: str = "urban_informal",
        spacy_model: str = "xx_ent_wiki_sm",
    ) -> None:
        self.country_code = country_code
        self.context_tag = context_tag
        self.profile = load_country_profile(country_code, context_tag)
        self.priors = get_confidence_priors(self.profile)
        self.zero_credential_default = is_zero_credential_context(self.profile)
        self._taxonomy = TaxonomyGraph()
        self._taxonomy.register_local_overrides(get_local_skill_overrides(self.profile))
        self._nlp = self._load_spacy(spacy_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, raw_text: str) -> dict[str, Any]:
        """Full parse pipeline: raw_text → VSS list + HumanLayer.

        Returns a dict with keys: user, skills (list), vss_list (list), human_layer.
        """
        text_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()

        user = self._extract_user(raw_text, text_hash)
        skills = self._extract_skills(raw_text)
        vss_list = self._build_vss_list(user, skills, now)
        human_layer = self._build_human_layer(user, vss_list, now)

        return {
            "user": self._user_to_dict(user),
            "skills": [self._skill_to_dict(s) for s in skills],
            "vss_list": vss_list,
            "human_layer": human_layer,
        }

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_user(self, text: str, text_hash: str) -> ExtractedUser:
        display_name = self._extract_name(text)
        location = self._extract_location(text)
        languages = self._extract_languages(text)
        zero_cred = self._detect_zero_credential(text)

        return ExtractedUser(
            user_id=f"usr_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}",
            display_name=display_name,
            location=location,
            languages=languages,
            source_text_hash=text_hash,
            zero_credential=zero_cred or self.zero_credential_default,
            raw_text=text,
        )

    def _extract_name(self, text: str) -> Optional[str]:
        for pattern in _NAME_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group(1).strip().title()
        # spaCy PERSON entity fallback
        if self._nlp:
            doc = self._nlp(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text.strip().title()
        return None

    def _extract_location(self, text: str) -> dict[str, str]:
        location: dict[str, str] = {
            "country_code": self.country_code,
            "context_tag": self.context_tag,
        }
        for pattern in _LOCATION_PATTERNS:
            m = pattern.search(text)
            if m:
                location["city"] = m.group(1).strip()
                break
        # spaCy GPE fallback
        if "city" not in location and self._nlp:
            doc = self._nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    location["city"] = ent.text.strip()
                    break
        return location

    def _extract_languages(self, text: str) -> list[str]:
        found = []
        for m in _LANGUAGE_PATTERN.finditer(text):
            bcp47 = _LANGUAGE_MAP.get(m.group(1).lower())
            if bcp47 and bcp47 not in found:
                found.append(bcp47)
        if not found:
            found.append(self.profile["languages"]["primary"])
        return found

    def _extract_skills(self, text: str) -> list[ExtractedSkill]:
        """Extract all skill signals from text using pattern matching."""
        found: dict[str, ExtractedSkill] = {}  # label → skill (dedup)

        for pattern, label, category, base_weight in _SKILL_PATTERNS:
            matches = pattern.findall(text)
            if not matches:
                continue

            source_phrases = []
            for m in pattern.finditer(text):
                phrase = self._get_context_window(text, m.start(), m.end())
                source_phrases.append(phrase)

            experience_signals, extra = self._extract_experience(text)

            if label in found:
                # Merge evidence
                existing = found[label]
                existing.source_phrases.extend(source_phrases)
                existing.experience_signals.extend(experience_signals)
                existing.evidence_weight = min(existing.evidence_weight + 0.05, 1.0)
            else:
                skill_id = f"skl_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
                found[label] = ExtractedSkill(
                    skill_id=skill_id,
                    label=label,
                    category=category,
                    source_phrases=source_phrases,
                    experience_signals=list(set(experience_signals)),
                    evidence_weight=base_weight,
                    extra_signals=extra,
                )

        # NLP-based skill fallback via taxonomy crosswalk
        noun_phrases = self._extract_noun_phrases(text)
        for phrase in noun_phrases:
            result = self._taxonomy.crosswalk(phrase)
            if result and result.primary.label not in found:
                skill_id = f"skl_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
                found[result.primary.label] = ExtractedSkill(
                    skill_id=skill_id,
                    label=result.primary.label,
                    category="other",
                    source_phrases=[phrase],
                    experience_signals=[],
                    evidence_weight=result.primary.match_score * 0.8,
                    extra_signals={},
                )

        return list(found.values())

    def _extract_experience(self, text: str) -> tuple[list[str], dict[str, Any]]:
        signals: list[str] = []
        extra: dict[str, Any] = {}

        for pattern, signal_type in _EXPERIENCE_PATTERNS:
            m = pattern.search(text)
            if m:
                raw_signal = m.group(0)
                signals.append(raw_signal)
                if signal_type == "years_experience":
                    try:
                        extra["years_experience"] = int(m.group(1))
                    except (IndexError, ValueError):
                        pass
                elif signal_type == "since_year":
                    try:
                        year = int("20" + m.group(1)) if int(m.group(1)) < 50 else int("19" + m.group(1))
                        extra["years_experience"] = max(0, 2024 - year)
                    except (IndexError, ValueError):
                        pass
                elif signal_type in ("client_count", "volume_per_period"):
                    try:
                        extra[signal_type] = int(m.group(1))
                    except (IndexError, ValueError):
                        pass
                elif signal_type in ("self_taught", "self_taught_digital"):
                    extra["self_taught"] = True

        return signals, extra

    def _detect_zero_credential(self, text: str) -> bool:
        zero_cred_signals = [
            r"no\s+(?:formal\s+)?(?:degree|diploma|certificate|qualification)",
            r"didn'?t\s+(?:finish|complete|go\s+to)\s+school",
            r"dropped\s+out",
            r"self[\s-]?taught",
            r"learned\s+(?:on\s+the\s+job|from\s+youtube|online)",
            r"no\s+credentials?",
        ]
        for sig in zero_cred_signals:
            if re.search(sig, text, re.I):
                return True
        return False

    def _extract_noun_phrases(self, text: str) -> list[str]:
        """Extract candidate skill phrases via spaCy or simple NP regex fallback."""
        if self._nlp:
            doc = self._nlp(text)
            return [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 4]
        # Fallback: extract 1-3 word noun-like tokens
        return re.findall(r"\b[A-Za-z]+(?:\s+[A-Za-z]+){0,2}\b", text)

    @staticmethod
    def _get_context_window(text: str, start: int, end: int, window: int = 40) -> str:
        left = max(0, start - window)
        right = min(len(text), end + window)
        return text[left:right].strip()

    # ------------------------------------------------------------------
    # VSS builder
    # ------------------------------------------------------------------

    def _build_vss_list(
        self,
        user: ExtractedUser,
        skills: list[ExtractedSkill],
        now: str,
    ) -> list[dict[str, Any]]:
        vss_list = []
        for skill in skills:
            evidence_chain = self._build_evidence_chain(skill)
            confidence = compute_confidence(
                evidence_list=evidence_chain,
                priors=self.priors,
                extra_signals=skill.extra_signals,
            )
            crosswalk_result = self._taxonomy.crosswalk(
                " ".join([skill.label] + skill.source_phrases[:2])
            )

            vss = {
                "vss_id": f"vss_{uuid.uuid4()}",
                "schema_version": "v0.2",
                "created_at": now,
                "updated_at": now,
                "user": {
                    "user_id": user.user_id,
                    "display_name": user.display_name,
                    "location": user.location,
                    "languages": user.languages,
                    "source_text_hash": user.source_text_hash,
                    "zero_credential": user.zero_credential,
                },
                "skill": {
                    "skill_id": skill.skill_id,
                    "label": skill.label,
                    "category": skill.category,
                    "source_phrases": skill.source_phrases[:5],
                    "experience_signals": skill.experience_signals[:5],
                },
                "evidence_chain": evidence_chain,
                "confidence": {
                    "score": confidence.score,
                    "lower_95": confidence.lower_95,
                    "upper_95": confidence.upper_95,
                    "alpha": confidence.alpha,
                    "beta": confidence.beta,
                    "method": confidence.method,
                    "tier": confidence.tier,
                },
                "taxonomy_crosswalk": self._crosswalk_to_dict(crosswalk_result),
                "country_code": self.country_code,
                "processing_meta": {
                    "parser_version": "v0.3-sse-alpha.1",
                    "model_id": "unmapped-sse-parser",
                    "detected_language": user.languages[0] if user.languages else "en",
                },
            }
            vss_list.append(vss)
        return vss_list

    def _build_evidence_chain(self, skill: ExtractedSkill) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        chain = [
            {
                "evidence_type": "self_report",
                "raw_signal": phrase,
                "normalized_signal": phrase.lower().strip(),
                "weight": round(skill.evidence_weight, 3),
                "source": "chaotic_input_parser",
                "timestamp": now,
            }
            for phrase in skill.source_phrases[:3]
        ]
        if skill.experience_signals:
            for sig in skill.experience_signals[:2]:
                chain.append({
                    "evidence_type": "self_report",
                    "raw_signal": sig,
                    "normalized_signal": sig.lower().strip(),
                    "weight": round(min(skill.evidence_weight + 0.1, 1.0), 3),
                    "source": "experience_signal_extractor",
                    "timestamp": now,
                })
        if not chain:
            chain.append({
                "evidence_type": "self_report",
                "raw_signal": skill.label,
                "normalized_signal": skill.label.lower(),
                "weight": 0.3,
                "source": "pattern_match_fallback",
                "timestamp": now,
            })
        return chain

    @staticmethod
    def _crosswalk_to_dict(result: Any) -> dict[str, Any]:
        if result is None:
            return {
                "primary": {
                    "framework": "ISCO-08",
                    "code": "9999",
                    "label": "Unclassified",
                    "match_score": 0.0,
                }
            }
        return {
            "primary": {
                "framework": result.primary.framework,
                "code": result.primary.code,
                "label": result.primary.label,
                "match_score": result.primary.match_score,
            },
            "secondary": [
                {
                    "framework": s.framework,
                    "code": s.code,
                    "label": s.label,
                    "match_score": s.match_score,
                }
                for s in (result.secondary or [])
            ],
        }

    # ------------------------------------------------------------------
    # HumanLayer builder
    # ------------------------------------------------------------------

    def _build_human_layer(
        self,
        user: ExtractedUser,
        vss_list: list[dict[str, Any]],
        now: str,
    ) -> dict[str, Any]:
        from app.core.human_layer import HumanLayerRenderer
        renderer = HumanLayerRenderer(self.profile)
        return renderer.render(user, vss_list, now)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _user_to_dict(user: ExtractedUser) -> dict[str, Any]:
        return {
            "user_id": user.user_id,
            "display_name": user.display_name,
            "location": user.location,
            "languages": user.languages,
            "source_text_hash": user.source_text_hash,
            "zero_credential": user.zero_credential,
        }

    @staticmethod
    def _skill_to_dict(skill: ExtractedSkill) -> dict[str, Any]:
        return {
            "skill_id": skill.skill_id,
            "label": skill.label,
            "category": skill.category,
            "source_phrases": skill.source_phrases,
            "experience_signals": skill.experience_signals,
            "evidence_weight": skill.evidence_weight,
        }

    # ------------------------------------------------------------------
    # spaCy loader (graceful degradation if model not installed)
    # ------------------------------------------------------------------

    @staticmethod
    def _load_spacy(model: str) -> Any:
        try:
            import spacy  # type: ignore
            return spacy.load(model)
        except ImportError:
            logger.warning("spaCy not installed — NLP fallback active")
            return None
        except OSError:
            logger.warning("spaCy model '%s' not found — NLP fallback active", model)
            # Try downloading automatically
            try:
                import spacy  # type: ignore
                spacy.cli.download(model)
                return spacy.load(model)
            except Exception:
                return None
