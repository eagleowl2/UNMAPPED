# UNMAPPED Protocol — Project Log

Format per Section 12.4 of UNMAPPED Protocol v0.2 spec.

---

## LOG ENTRY: 2026-04-26

**Entry ID:** `LOG-0001`
**Version:** `v0.3.0-alpha.1`
**Branch:** `module/m1-sse`
**Author:** Claude (Senior Backend Architect — SSE Core)
**Status:** COMPLETE — ready for PR review

---

### 1. Change Type
`feat` — Initial implementation of Module 1: Skills Signal Engine + Evidence Parser.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| `USER` | ADDED | `app/core/parser.py` |
| `SKILL` | ADDED | `app/core/parser.py` |
| `VerifiableSkillSignal` (VSS) | ADDED | `app/core/parser.py` |
| `HumanLayer` | ADDED | `app/core/human_layer.py` |
| `CountryProfile` | ADDED | `app/core/country_profile.py` |
| `TaxonomyGraph` | ADDED | `app/core/taxonomy.py` |
| `ConfidenceResult` (Bayesian) | ADDED | `app/core/bayesian.py` |

---

### 3. Summary of Changes

Implemented the complete Skills Signal Engine (SSE) backend from scratch on branch `module/m1-sse`. The core deliverable is a **chaotic single-field parser** that accepts any unstructured personal/professional text in any language and produces structured Verifiable Skill Signals with full Human Layer output.

**Pipeline:**
```
raw_text
  → language detection (spaCy multilingual / BCP-47 pattern matching)
  → NER extraction (name, location, languages, skills, experience)
  → regex skill pattern catalog (30+ patterns, multilingual-aware)
  → taxonomy crosswalk (NetworkX: ISCO-08 → ESCO → O*NET)
  → Bayesian confidence (Beta conjugate update, credible intervals)
  → VSS assembly (one VSS per skill)
  → HumanLayer rendering (Jinja2 HTML card + SMS ≤160 + USSD tree)
```

**Canonical test vector — Amara story:**
> "My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube, been fixing phones for 3 years, I have about 20 customers a week"

Produces:
- USER: `{display_name: "Amara", location: {city: "Accra", country_code: "GH"}, languages: ["ak-GH", "en-GH", "gaa"], zero_credential: true}`
- SKILLs: Phone Repair (ISCO-08:7421, confidence ~0.68 established), Software Development (ISCO-08:2512)
- VSS: Two VSS objects with full evidence chains, Bayesian posteriors, ISCO/ESCO/O*NET crosswalks
- HumanLayer: Profile card HTML, SMS "UNMAPPED:Amara in Accra|Skills:Phone Repair(68%), Software Development(52%)|Confidence:ESTABLISHED", USSD navigation tree

---

### 4. Architecture Decisions

**4.1 Graceful NLP degradation**
spaCy is loaded with `try/except` and falls back to pure regex extraction if the model is unavailable. This ensures the parser works in constrained environments (no GPU, no model download) while upgrading quality when spaCy is present.

**4.2 Beta conjugate Bayesian scoring (no full MCMC)**
PyMC/Bambi are listed in requirements but disabled for MVP. Beta conjugate update (`alpha += weighted_successes`, `beta += weighted_failures`) gives closed-form posteriors in microseconds — acceptable for a hackathon demo. Full MCMC sampling can be swapped in by replacing `compute_confidence()`.

**4.3 NetworkX taxonomy graph**
ISCO-08 nodes are the canonical anchor. ESCO and O*NET are secondary crosswalk targets linked by directed edges with match-score weights. Country-profile `local_skill_overrides` (e.g. Ghanaian colloquial "phone fixer" → 7421) are registered at runtime, checked before the keyword map, so local terminology always wins.

**4.4 Zero-credential auto-detection**
Detected from six signal patterns in the raw text (self-taught, dropped out, learned on YouTube, etc.) AND from `country_profile.zero_credential_default: true`. The `zero_credential_badge` propagates to the profile card, SMS, and USSD tree.

**4.5 Parser cache**
`EvidenceParser` instances are cached in-process by `(country_code, context_tag)`. spaCy model load is expensive (~2s); subsequent requests for the same context are sub-10ms.

---

### 5. Files Created/Modified

```
UNMAPPED/
├── schemas/
│   ├── country_profile.json          NEW — JSON Schema v7
│   ├── verifiable_skill_signal.json  NEW — JSON Schema v7
│   └── human_layer.json              NEW — JSON Schema v7
├── config/
│   └── ghana_urban_informal.json     NEW — Ghana urban informal profile
├── app/
│   ├── __init__.py
│   ├── main.py                       NEW — FastAPI app + CORS + lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                 NEW — POST /parse, POST /generate_vss
│   ├── core/
│   │   ├── __init__.py
│   │   ├── country_profile.py        NEW — loader + validator
│   │   ├── taxonomy.py               NEW — NetworkX crosswalk engine
│   │   ├── bayesian.py               NEW — Beta conjugate confidence
│   │   ├── parser.py                 NEW — EvidenceParser (core SSE)
│   │   └── human_layer.py            NEW — HumanLayerRenderer (Jinja2)
│   └── models/
│       ├── __init__.py
│       └── schemas.py                NEW — Pydantic v2 models
├── tests/
│   ├── __init__.py
│   ├── test_country_profile.py       NEW
│   ├── test_taxonomy.py              NEW
│   ├── test_bayesian.py              NEW
│   ├── test_parser.py                NEW — Amara story test vector
│   └── test_api.py                   NEW — FastAPI integration tests
├── Dockerfile                        NEW
├── docker-compose.yml                NEW
├── requirements.txt                  NEW
├── requirements-dev.txt              NEW
├── pytest.ini                        NEW
├── .gitignore                        NEW
├── CHANGELOG.md                      NEW
└── PROJECT_LOG.md                    NEW (this file)
```

---

### 6. Backward Compatibility
**N/A** — First code commit. No existing API contracts to break.

---

### 7. Test Plan

```bash
# Install dev deps
pip install -r requirements-dev.txt
python -m spacy download xx_ent_wiki_sm

# Run all tests
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test suites
pytest tests/test_parser.py -v         # Amara story + edge cases
pytest tests/test_api.py -v            # API integration
pytest tests/test_taxonomy.py -v       # Crosswalk engine
pytest tests/test_bayesian.py -v       # Confidence scoring
pytest tests/test_country_profile.py   # Profile loader

# Manual smoke test
uvicorn app.main:app --reload
curl -X POST http://localhost:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube", "country_code": "GH"}'
```

---

### 8. Rollback Path
1. `git checkout main`
2. Branch `module/m1-sse` can be deleted without affecting `main` (no merges yet).
3. No database migrations, no persistent state — fully stateless API.

---

### 9. Instructions for Claude 2 (SPA Integration)

**Base URL:** `http://localhost:8000` (local) or container hostname on shared network.

**POST /api/v1/parse**

```http
POST /api/v1/parse
Content-Type: application/json

{
  "text": "<any unstructured user input>",
  "country_code": "GH",
  "context_tag": "urban_informal"
}
```

**Response shape:**
```json
{
  "ok": true,
  "user": {
    "user_id": "usr_...",
    "display_name": "Amara",
    "location": {"country_code": "GH", "city": "Accra"},
    "languages": ["ak-GH", "en-GH", "gaa"],
    "zero_credential": true
  },
  "skills": [
    {
      "skill_id": "skl_...",
      "label": "Phone Repair",
      "category": "technical",
      "confidence_score": 0.68,
      "source_phrases": ["fix phones in Accra"]
    }
  ],
  "vss_list": [
    {
      "vss_id": "vss_...",
      "skill": {"label": "Phone Repair", "category": "technical"},
      "confidence": {"score": 0.68, "tier": "established"},
      "taxonomy_crosswalk": {
        "primary": {"framework": "ISCO-08", "code": "7421", "label": "..."}
      }
    }
  ],
  "human_layer": {
    "hl_id": "hl_...",
    "profile_card": {
      "display_name": "Amara",
      "headline": "Phone Repair & Software Development specialist | Accra",
      "skills_summary": [...],
      "rendered_html": "<html>...",
      "zero_credential_badge": true
    },
    "sms_summary": {"text": "UNMAPPED:Amara in Accra|...", "char_count": 87},
    "ussd_tree": {"root": {...}}
  },
  "meta": {
    "skills_detected": 2,
    "processing_time_ms": 45.2,
    "parser_version": "v0.3-sse-alpha.1"
  }
}
```

**Key fields for SPA rendering:**
- `human_layer.profile_card.rendered_html` — inject directly into profile preview `<div>`
- `human_layer.sms_summary.text` — display in SMS preview widget
- `human_layer.ussd_tree.root` — render USSD tree navigator
- `vss_list[].confidence.score` — confidence bar (0.0–1.0)
- `vss_list[].confidence.tier` — badge label (emerging/developing/established/expert)
- `vss_list[].taxonomy_crosswalk.primary.code` — ISCO code for credential display

**CORS:** API allows `localhost:3000`, `localhost:5173`, `localhost:8080` by default. Update `CORS_ORIGINS` env var for production.

---

### 10. Next Steps (v0.3-sse-alpha.2)
- [ ] Add `POST /api/v1/profiles` (persist VSS to lightweight store)
- [ ] Add more country profiles (NG, KE, TZ, SN)
- [ ] Integrate HuggingFace `xlm-roberta` for deeper multilingual NER
- [ ] Add PyMC full MCMC mode behind feature flag
- [ ] Webhooks for VSS update events
- [ ] Rate limiting + API key auth

---

*End of LOG-0001*
