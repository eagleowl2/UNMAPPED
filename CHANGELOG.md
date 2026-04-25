# Changelog

All notable changes to UNMAPPED follow [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

---

## [0.3.0-alpha.1] — 2026-04-26 — v0.3-sse-alpha.1

### Branch: `module/m1-sse`

### Added
- **Skills Signal Engine (Module 1) — full implementation**
  - `app/core/parser.py` — `EvidenceParser` class: chaotic single-field text input → USER entity + N SKILL entities → VSS list + HumanLayer. Supports any language via pattern matching + spaCy multilingual NLP.
  - `app/core/taxonomy.py` — `TaxonomyGraph` (NetworkX): ISCO-08 primary taxonomy with ESCO and O*NET crosswalk bridges. Local override registry for LMIC skill aliases (e.g. "phone fixer" → ISCO-08:7421).
  - `app/core/bayesian.py` — `compute_confidence()`: Beta distribution conjugate update (Bayesian). Computes posterior mean, 95% credible interval, confidence tier (emerging/developing/established/expert).
  - `app/core/human_layer.py` — `HumanLayerRenderer`: Jinja2 HTML profile card, SMS digest (≤160 chars), USSD tree (≤182 chars/node, max depth 3).
  - `app/core/country_profile.py` — `load_country_profile()`: JSON schema–validated country/context config loader with `lru_cache`.
- **JSON Schemas** (Section 4, 6.1, 7 of UNMAPPED v0.2 spec)
  - `schemas/country_profile.json`
  - `schemas/verifiable_skill_signal.json`
  - `schemas/human_layer.json`
- **Country Config**: `config/ghana_urban_informal.json` — Ghana urban informal economy profile (ISCO-08, zero-credential default, Twi/Ga/Ewe language support).
- **FastAPI Application**
  - `app/main.py` — FastAPI app with CORS, lifespan, `/health`, `/` root.
  - `app/api/routes.py` — `POST /api/v1/parse` and `POST /api/v1/generate_vss` endpoints.
  - `app/models/schemas.py` — Pydantic v2 request/response models.
- **Tests** (pytest, 100% core coverage target)
  - `tests/test_country_profile.py`
  - `tests/test_taxonomy.py`
  - `tests/test_bayesian.py`
  - `tests/test_parser.py` — Amara story canonical test vector
  - `tests/test_api.py` — FastAPI integration tests
- **Docker**: `Dockerfile`, `docker-compose.yml` (health-checked, spaCy model pre-baked)
- **Project infrastructure**: `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `.gitignore`

### Primitives Affected
- NEW: `USER` entity extraction
- NEW: `SKILL` entity extraction (multiple per input)
- NEW: `VerifiableSkillSignal` (VSS) assembly
- NEW: `HumanLayer` (profile card, SMS, USSD)
- NEW: `CountryProfile` loader

### Backward Compatibility
- First implementation — no breaking changes to prior versions (v0.2.0-full had no code).

### Zero-Credential Path
- Fully supported: auto-detected from input signals ("self-taught", "learned on YouTube", "no credentials") and country profile `zero_credential_default: true`.

---

## [0.2.0-full] — Pre-existing

- Protocol specification (UNMAPPED_Protocol_v0.2_Complete.docx)
- Repository initialised with LICENSE only.
