"""
Skills Signal Engine — Evidence Parser (v0.3.1).

Accepts one chaotic unstructured text input (any language) and produces:
  USER entity + N SKILL entities + VSS list + HumanLayer (profile card format).

Also exposes parse_for_profile() which returns the exact ProfileCard dict
shape expected by the frontend contract in docs/api-contract.md.
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
    get_skill_alias_registry,
    is_zero_credential_context,
    load_country_profile,
)
from app.core.multilingual import (
    AliasHit,
    AliasMatcher,
    MultilingualEmbedder,
    SemanticHit,
    candidate_phrases,
    semantic_match,
)
from app.core.taxonomy import TaxonomyGraph

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill pattern catalog — English + Armenian transliteration
# (pattern, canonical_label, category, base_evidence_weight, isco_code)
# ---------------------------------------------------------------------------

_SKILL_PATTERNS: list[tuple[re.Pattern[str], str, str, float, str]] = [
    # Phone / electronics repair
    (re.compile(r"\b(fix(?:ing)?|repair(?:ing)?)\s+(?:mobile\s+)?phone[s]?\b", re.I), "Phone Repair", "technical", 0.75, "7421"),
    (re.compile(r"\bphone\s+(?:repair(?:er|ing)?|technician|fixer)\b", re.I), "Phone Repair", "technical", 0.78, "7421"),
    (re.compile(r"\bmobile\s+(?:repair|technician)\b", re.I), "Phone Repair", "technical", 0.76, "7421"),
    (re.compile(r"\belectronics?\s+repair\b", re.I), "Electronics Repair", "technical", 0.70, "7421"),
    (re.compile(r"\bscreen\s+(?:replacement|repair|fix)\b", re.I), "Screen Repair", "technical", 0.68, "7421"),
    # Software / digital
    (re.compile(r"\bcod(?:e|ing|er)\b", re.I), "Software Development", "digital", 0.65, "2512"),
    (re.compile(r"\bprogramm(?:ing|er)\b", re.I), "Software Development", "digital", 0.70, "2512"),
    (re.compile(r"\bweb\s+dev(?:elop(?:ment|er))?\b", re.I), "Web Development", "digital", 0.72, "2512"),
    (re.compile(r"\bpython\b", re.I), "Python Programming", "digital", 0.60, "2512"),
    (re.compile(r"\bjavascript\b", re.I), "JavaScript Programming", "digital", 0.60, "2512"),
    (re.compile(r"\bhtml\b", re.I), "HTML/CSS", "digital", 0.55, "2512"),
    # Teaching / tutoring
    (re.compile(r"\bteach(?:ing|er)?\b", re.I), "Teaching", "other", 0.65, "2320"),
    (re.compile(r"\btutor(?:ing)?\b", re.I), "Tutoring", "other", 0.65, "2320"),
    (re.compile(r"\benglish\s+(?:tutor|lesson|teach|class)\b", re.I), "English Tutoring", "other", 0.80, "2320"),
    (re.compile(r"\blessons?\b", re.I), "Teaching", "other", 0.60, "2320"),
    # Translation
    (re.compile(r"\btranslat(?:e|ing|ion|or)\b", re.I), "Translation", "other", 0.78, "2643"),
    (re.compile(r"\binterpret(?:ing|er)?\b", re.I), "Interpretation", "other", 0.72, "2643"),
    # Trade / retail
    (re.compile(r"\bsell(?:ing)?\b|\bsales?\b|\btrader\b|\btrading\b", re.I), "Trading/Sales", "trade", 0.68, "5221"),
    (re.compile(r"\bmarket\s+(?:trader|vendor|stall)\b", re.I), "Market Trading", "trade", 0.75, "5221"),
    (re.compile(r"\bvendor\b|\bkiosk\b|\bstall\b", re.I), "Market Trading", "trade", 0.65, "5221"),
    # Tailoring / textiles
    (re.compile(r"\btailoring\b|\bdressmaking\b", re.I), "Tailoring", "trade", 0.75, "7436"),
    (re.compile(r"\bsew(?:ing)?\b", re.I), "Sewing", "trade", 0.70, "7436"),
    (re.compile(r"\bbraiding\b|\bhair\s+braid\b", re.I), "Hair Braiding", "trade", 0.73, "5141"),
    (re.compile(r"\bhair\s+(?:salon|dress|style|cut)\b", re.I), "Hair Styling", "trade", 0.70, "5141"),
    # Transport / delivery
    (re.compile(r"\bdriv(?:ing|er)\b", re.I), "Driving", "trade", 0.60, "8322"),
    (re.compile(r"\bdeliver(?:y|ies|ing)\b", re.I), "Delivery Services", "trade", 0.55, "8322"),
    # Farming
    (re.compile(r"\bfarming\b|\bagriculture\b|\bcrop[s]?\b", re.I), "Farming", "agricultural", 0.70, "6110"),
    (re.compile(r"\bfish(?:ing|erman|monger|trader)\b|\bsmoked\s+fish\b", re.I), "Fish Trading", "trade", 0.72, "5221"),
    # Care work
    (re.compile(r"\bchildcare\b|\bnanny\b", re.I), "Childcare", "care", 0.72, "5322"),
    (re.compile(r"\bnurs(?:e|ing)\b", re.I), "Nursing/Care", "care", 0.68, "5322"),
    # Finance
    (re.compile(r"\baccounting\b|\baccountant\b", re.I), "Accounting", "financial", 0.72, "3312"),
    (re.compile(r"\bbook(?:keeping|keeper)\b|\bledger\b", re.I), "Bookkeeping", "financial", 0.70, "3312"),
    (re.compile(r"\bmobile\s+money\b|\bvodafone\s+cash\b|\bmtn\s+momo\b|\bidram\b", re.I), "Mobile Money", "financial", 0.68, "3312"),
    # Creative
    (re.compile(r"\bphotograph(?:y|er|ing)\b", re.I), "Photography", "creative", 0.68, "3431"),
    (re.compile(r"\bvideo\s+editing\b", re.I), "Video Editing", "creative", 0.65, "3431"),
    (re.compile(r"\bdesign(?:er|ing)?\b", re.I), "Design", "creative", 0.60, "3431"),
    # Social media / digital marketing
    (re.compile(r"\bsocial\s+media\b", re.I), "Social Media Management", "digital", 0.58, "2512"),
    (re.compile(r"\bdata\s+entry\b", re.I), "Data Entry", "digital", 0.60, "4131"),
]

# Armenian skill patterns (transliteration + Unicode script)
_ARMENIAN_SKILL_PATTERNS: list[tuple[re.Pattern[str], str, str, float, str]] = [
    # "դաս" = lesson, "դասավ" = teach, "դասատու" = teacher
    (re.compile(r"\bդաս(?:ավ|եր|ատու)?\b", re.I), "Teaching", "other", 0.75, "2320"),
    # "թարգման" root = translate (թարգմանում = translating, թարգմանիչ = translator)
    (re.compile(r"թարգման", re.UNICODE), "Translation", "other", 0.78, "2643"),
    # "Idram" digital payment
    (re.compile(r"\bIdram\b|\bիդ(?:րամ)?\b", re.I), "Mobile Money", "financial", 0.68, "3312"),
    # "ստուդ" = studio
    (re.compile(r"\bստուդ(?:իա|ո)?\b", re.I), "Teaching", "other", 0.65, "2320"),
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

_NAME_PATTERNS = [
    re.compile(r"(?:my\s+name\s+is|i(?:'m|\s+am)|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.I),
    re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*(?:i\s+am|i'm|is\s+a|\d{2})", re.I),
    # Armenian: "Իմ անունը X է"
    re.compile(r"Իմ\s+անունը\s+([Ա-Ֆա-ֆA-Za-z]+)\s+է", re.UNICODE),
]

_LOCATION_PATTERNS = [
    re.compile(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\blive[s]?\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    re.compile(r"\bbased\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"),
    # Armenian "Գյ" = Gyumri prefix, "Երևան" = Yerevan
    re.compile(r"\b(Երևան|Գյ(?:ումրի)?|Վ(?:անաձոր)?)\b", re.UNICODE),
]

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
    "armenian": "hy-AM",
    "russian": "ru",
    "հայ": "hy-AM",          # "Armenian" in Armenian
    "ռուս": "ru",             # "Russian" in Armenian
    "անգլ": "en",            # "English" in Armenian
}

_LANGUAGE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _LANGUAGE_MAP) + r")\b",
    re.I | re.UNICODE,
)

# Armenian script range
_ARMENIAN_SCRIPT_RE = re.compile(r"[\u0531-\u0587]")


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
    taxonomy_code: str = "9999"     # ISCO-08 code, for signals computation


class EvidenceParser:
    """
    Core SSE parser: raw text (any language) → USER entity + SKILL entities.

    Two public entry points:
      parse()              → full internal dict (VSS list, HumanLayer)
      parse_for_profile()  → ProfileCard dict matching the frontend contract
    """

    def __init__(
        self,
        country_code: str = "GH",
        context_tag: str = "urban_informal",
        spacy_model: str = "xx_ent_wiki_sm",
        enable_embedder: bool = True,
    ) -> None:
        self.country_code = country_code.upper()
        self.context_tag = context_tag
        self.profile = load_country_profile(country_code, context_tag)
        self.priors = get_confidence_priors(self.profile)
        self.zero_credential_default = is_zero_credential_context(self.profile)
        self._taxonomy = TaxonomyGraph()
        self._taxonomy.register_local_overrides(get_local_skill_overrides(self.profile))
        self._nlp = self._load_spacy(spacy_model)
        self._alias_registry = get_skill_alias_registry(self.profile)
        self._alias_matcher = AliasMatcher(self._alias_registry)
        self._enable_embedder = enable_embedder

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, raw_text: str) -> dict[str, Any]:
        """Full parse pipeline → internal dict (VSS list + HumanLayer)."""
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

    def parse_for_profile(self, raw_text: str) -> dict[str, Any]:
        """Parse and return the ProfileCard dict matching the frontend API contract.

        Returns a dict matching ProfileCard in frontend/src/lib/types.ts.
        """
        from app.core.signals import (
            compute_wage_signal,
            compute_growth_signal,
            get_network_entry,
            bcp47_to_human,
            detect_age,
        )

        t_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()

        user = self._extract_user(raw_text, t_hash)
        skills = self._extract_skills(raw_text)
        vss_list = self._build_vss_list(user, skills, now)

        # --- Build skill list for profile (name, confidence, evidence)
        skill_items: list[dict[str, Any]] = []
        for i, skill in enumerate(skills[:8]):
            vss = vss_list[i] if i < len(vss_list) else {}
            confidence = vss.get("confidence", {}).get("score", skill.evidence_weight)
            evidence = skill.source_phrases[0] if skill.source_phrases else None
            skill_items.append({
                "name": skill.label,
                "confidence": round(confidence, 2),
                "evidence": evidence,
                # pass-through for signals
                "category": skill.category,
                "taxonomy_code": skill.taxonomy_code,
            })

        # Sort by confidence descending, cap at 8
        skill_items.sort(key=lambda x: x["confidence"], reverse=True)

        # Collect extra signals from all skills (merge)
        extra: dict[str, Any] = {}
        for sk in skills:
            for k, v in sk.extra_signals.items():
                if k not in extra:
                    extra[k] = v

        # Wage signal
        wage = compute_wage_signal(skill_items, self.country_code, extra)
        # Growth signal
        growth = compute_growth_signal(
            raw_text, skill_items,
            user.zero_credential, extra, self.country_code,
        )
        # Network entry
        city = user.location.get("city", "")
        net_entry = get_network_entry(skill_items, self.country_code, city)

        # Location string
        loc_parts = [p for p in [city, _country_region(self.country_code)] if p]
        location_str = ", ".join(loc_parts) or self.country_code

        # Languages — human-readable names
        lang_names = bcp47_to_human(user.languages)

        # Pseudonym = first name only; display_name = first + last initial
        name = user.display_name or "Anonymous"
        pseudonym = name.split()[0] if name else "Worker"
        display_name = _safe_display_name(name)

        # Age
        age = detect_age(raw_text)

        # Profile ID — deterministic from text hash
        profile_id = f"prf-{t_hash[:12]}"

        # SMS summary (≤ 160 chars, target)
        sms = _build_sms(
            pseudonym=pseudonym,
            age=age,
            location=location_str,
            skills=skill_items[:3],
            wage_score=wage["score"],
            growth_score=growth["score"],
            country=self.country_code,
        )

        # USSD menu (4-8 lines, ≤ 40 chars each)
        ussd_code = self.profile.get("delivery_channels", {}).get("ussd", {})
        shortcode = _ussd_shortcode(self.country_code)
        ussd_menu = _build_ussd_menu(
            shortcode=shortcode,
            pseudonym=pseudonym,
            skills=skill_items[:5],
            wage_score=wage["score"],
            growth_score=growth["score"],
        )

        # Strip pass-through keys before returning
        for s in skill_items:
            s.pop("category", None)
            s.pop("taxonomy_code", None)

        return {
            "profile_id": profile_id,
            "display_name": display_name,
            "pseudonym": pseudonym,
            "age": age,
            "location": location_str,
            "languages": lang_names,
            "skills": skill_items,
            "wage_signal": wage,
            "growth_signal": growth,
            "network_entry": net_entry,
            "sms_summary": sms,
            "ussd_menu": ussd_menu,
        }

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_user(self, text: str, text_hash: str) -> ExtractedUser:
        display_name = self._extract_name(text)
        location = self._extract_location(text)
        languages = self._extract_languages(text)
        zero_cred = self._detect_zero_credential(text)

        uid = f"usr_{uuid.uuid4()}"
        return ExtractedUser(
            user_id=uid,
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
                city = m.group(1).strip()
                # Exclude obvious non-cities
                if city.lower() not in ("a", "the", "my", "our", "any", "your"):
                    location["city"] = city
                    break
        if "city" not in location and self._nlp:
            doc = self._nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    location["city"] = ent.text.strip()
                    break
        return location

    def _extract_languages(self, text: str) -> list[str]:
        found = []
        # Armenian script detection
        if _ARMENIAN_SCRIPT_RE.search(text) and "hy-AM" not in found:
            found.append("hy-AM")
        for m in _LANGUAGE_PATTERN.finditer(text):
            bcp47 = _LANGUAGE_MAP.get(m.group(1).lower())
            if bcp47 and bcp47 not in found:
                found.append(bcp47)
        if not found:
            found.append(self.profile["languages"]["primary"])
        return found

    def _extract_skills(self, text: str) -> list[ExtractedSkill]:
        """Multi-stage extraction:

        1. Locale alias_registry (Twi / Ga / Armenian / Russian / English) —
           highest precision, primary path for low-resource languages.
        2. English + Armenian regex patterns — broad coverage of common
           informal-economy verbs/nouns.
        3. Multilingual embedder (E5-small / BGE-M3) — semantic
           paraphrase fallback against canonical skill labels.
        4. Noun-phrase taxonomy crosswalk — final structural fallback.

        Earlier stages "lock in" canonical_label → skill mapping so later
        stages cannot duplicate the same skill under a different name.
        """
        found: dict[str, ExtractedSkill] = {}
        experience_signals_text, extra_text = self._extract_experience(text)

        # Stage 1 — locale alias registry
        for hit in self._alias_matcher.find_all(text):
            label = hit.canonical_label
            if label in found:
                continue
            phrase = self._surrounding_phrase(text, hit.surface_form)
            found[label] = ExtractedSkill(
                skill_id=f"skl_{uuid.uuid4()}",
                label=label,
                category=hit.category,
                source_phrases=[phrase or hit.surface_form],
                experience_signals=list(set(experience_signals_text)),
                evidence_weight=hit.base_weight,
                extra_signals={
                    **extra_text,
                    "alias_match": hit.matched_alias,
                    "alias_lang": hit.language_hint,
                },
                taxonomy_code=hit.isco_code,
            )

        # Stage 2 — English + Armenian regex
        all_patterns = list(_SKILL_PATTERNS)
        if _ARMENIAN_SCRIPT_RE.search(text):
            all_patterns += _ARMENIAN_SKILL_PATTERNS

        for pattern, label, category, base_weight, isco_code in all_patterns:
            if not pattern.search(text):
                continue

            source_phrases = [
                self._get_context_window(text, m.start(), m.end())
                for m in pattern.finditer(text)
            ]

            if label in found:
                existing = found[label]
                existing.source_phrases.extend(source_phrases)
                existing.experience_signals.extend(experience_signals_text)
                existing.evidence_weight = min(existing.evidence_weight + 0.03, 1.0)
            else:
                found[label] = ExtractedSkill(
                    skill_id=f"skl_{uuid.uuid4()}",
                    label=label,
                    category=category,
                    source_phrases=source_phrases,
                    experience_signals=list(set(experience_signals_text)),
                    evidence_weight=base_weight,
                    extra_signals=dict(extra_text),
                    taxonomy_code=isco_code,
                )

        # Stage 3 — multilingual embedder (semantic paraphrase)
        if self._enable_embedder and self._alias_registry:
            self._apply_semantic_stage(text, found, experience_signals_text, extra_text)

        # Stage 4 — noun-phrase taxonomy crosswalk
        for phrase in self._extract_noun_phrases(text):
            result = self._taxonomy.crosswalk(phrase)
            if result and result.primary.label not in found:
                found[result.primary.label] = ExtractedSkill(
                    skill_id=f"skl_{uuid.uuid4()}",
                    label=result.primary.label,
                    category="other",
                    source_phrases=[phrase],
                    experience_signals=[],
                    evidence_weight=result.primary.match_score * 0.8,
                    extra_signals={},
                    taxonomy_code=result.primary.code,
                )

        return list(found.values())

    def _apply_semantic_stage(
        self,
        text: str,
        found: dict[str, "ExtractedSkill"],
        experience_signals_text: list[str],
        extra_text: dict[str, Any],
    ) -> None:
        """Run the multilingual embedder against candidate phrases."""
        embedder = MultilingualEmbedder.get()
        if not embedder.available:
            return
        phrases = candidate_phrases(text, max_words=4)
        if not phrases:
            return
        # Cap to keep CPU inference snappy on small inputs.
        phrases = phrases[:64]
        hits: list[SemanticHit] = semantic_match(
            phrases, self._alias_registry,
        )
        for hit in hits:
            label = hit.canonical_label
            if label in found:
                continue
            found[label] = ExtractedSkill(
                skill_id=f"skl_{uuid.uuid4()}",
                label=label,
                category=hit.category,
                source_phrases=[hit.surface_form],
                experience_signals=list(set(experience_signals_text)),
                evidence_weight=min(hit.base_weight, 0.75) * hit.score,
                extra_signals={
                    **extra_text,
                    "semantic_score": hit.score,
                    "semantic_phrase": hit.surface_form,
                },
                taxonomy_code=hit.isco_code,
            )

    @staticmethod
    def _surrounding_phrase(text: str, surface: str, window: int = 40) -> str:
        if not surface:
            return ""
        idx = text.lower().find(surface.lower())
        if idx < 0:
            return surface
        return EvidenceParser._get_context_window(text, idx, idx + len(surface), window)

    def _extract_experience(self, text: str) -> tuple[list[str], dict[str, Any]]:
        signals: list[str] = []
        extra: dict[str, Any] = {}
        for pattern, signal_type in _EXPERIENCE_PATTERNS:
            m = pattern.search(text)
            if not m:
                continue
            signals.append(m.group(0))
            if signal_type == "years_experience":
                try:
                    extra["years_experience"] = int(m.group(1))
                except (IndexError, ValueError):
                    pass
            elif signal_type == "since_year":
                try:
                    yr = int(m.group(1))
                    full_yr = (2000 + yr) if yr < 50 else (1900 + yr)
                    extra["years_experience"] = max(0, 2025 - full_yr)
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
        patterns = [
            r"no\s+(?:formal\s+)?(?:degree|diploma|certificate|qualification)",
            r"didn'?t\s+(?:finish|complete|go\s+to)\s+school",
            r"dropped\s+out",
            r"self[\s-]?taught",
            r"learned\s+(?:on\s+the\s+job|from\s+youtube|online)",
            r"no\s+credentials?",
        ]
        return any(re.search(p, text, re.I) for p in patterns)

    def _extract_noun_phrases(self, text: str) -> list[str]:
        if self._nlp:
            doc = self._nlp(text)
            return [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 4]
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
                    "taxonomy_code": skill.taxonomy_code,
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
                "taxonomy_crosswalk": _crosswalk_to_dict(crosswalk_result),
                "country_code": self.country_code,
                "processing_meta": {
                    "parser_version": "v0.3.1",
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

    # ------------------------------------------------------------------
    # HumanLayer builder (internal format)
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
            "taxonomy_code": skill.taxonomy_code,
            "source_phrases": skill.source_phrases,
            "experience_signals": skill.experience_signals,
            "evidence_weight": skill.evidence_weight,
        }

    @staticmethod
    def _load_spacy(model: str) -> Any:
        try:
            import spacy  # type: ignore
            return spacy.load(model)
        except ImportError:
            logger.warning("spaCy not installed — NLP fallback active")
            return None
        except OSError:
            logger.warning("spaCy model '%s' not found — running regex-only", model)
            return None


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _crosswalk_to_dict(result: Any) -> dict[str, Any]:
    if result is None:
        return {"primary": {"framework": "ISCO-08", "code": "9999", "label": "Unclassified", "match_score": 0.0}}
    return {
        "primary": {
            "framework": result.primary.framework,
            "code": result.primary.code,
            "label": result.primary.label,
            "match_score": result.primary.match_score,
        },
        "secondary": [
            {"framework": s.framework, "code": s.code, "label": s.label, "match_score": s.match_score}
            for s in (result.secondary or [])
        ],
    }


def _safe_display_name(name: str) -> str:
    """Privacy-safe display name: first name + last initial if available."""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][0]}."
    return parts[0] if parts else "Anonymous"


def _country_region(country: str) -> str:
    return {
        "GH": "Greater Accra",
        "AM": "",
    }.get(country.upper(), "")


def _ussd_shortcode(country: str) -> str:
    return {"GH": "*789#", "AM": "*404#"}.get(country.upper(), "*789#")


def _build_sms(
    pseudonym: str,
    age: Optional[int],
    location: str,
    skills: list[dict[str, Any]],
    wage_score: int,
    growth_score: int,
    country: str,
) -> str:
    """Build SMS summary ≤ 160 characters."""
    age_part = f", {age}" if age else ""
    loc_part = f", {location}" if location else ""
    skill_labels = "+".join(s["name"] for s in skills[:2])
    sender = "UNMAPPED"
    # target format matching mock.ts sample style
    text = (
        f"{sender}: {pseudonym}{age_part}{loc_part}. "
        f"{skill_labels}. "
        f"Wage {wage_score}/100 Growth {growth_score}/100. "
        f"Reply 1 for plan."
    )
    if len(text) > 160:
        text = (
            f"{sender}: {pseudonym}{loc_part}. "
            f"{skill_labels}. W:{wage_score} G:{growth_score}"
        )[:160]
    return text[:160]


def _build_ussd_menu(
    shortcode: str,
    pseudonym: str,
    skills: list[dict[str, Any]],
    wage_score: int,
    growth_score: int,
) -> list[str]:
    """Build USSD menu — 4-8 lines, ≤ 40 chars each."""
    lines = [
        f"UNMAPPED {shortcode}"[:40],
        f"1. View my profile"[:40],
        f"2. Wage signal: {wage_score}/100"[:40],
        f"3. Growth signal: {growth_score}/100"[:40],
    ]
    for i, skill in enumerate(skills[:3], start=4):
        lines.append(f"{i}. {skill['name']}"[:40])
    lines.append("0. Exit"[:40])
    return lines[:8]
