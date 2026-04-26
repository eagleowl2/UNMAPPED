# UNMAPPED Protocol — Project Log

Format per Section 12.4 of UNMAPPED Protocol v0.2 spec.

> Per anti-conflict rule: new entries are added at the top of this file.
> Older entries below are preserved verbatim (append-only).

---

## LOG ENTRY: 2026-04-26 (v0.4 — SQLite Persistence + BONA Forensic Layer)

**Entry ID:** `LOG-0006`
**Version:** `v0.4`
**Branch:** `main` (working tree)
**Author:** Claude (Senior Data & Product Analyst, working from `UNMAPPED_Master_Context.docx`)
**Status:** COMPLETE — 226/226 backend tests passing (212 prior + 8 BONA + 6 DB).

### 1. Change Type
`feature` — Closes two outstanding gaps from §6 of the Master Context: the
absent persistence/employer-API layer (§6 Phase 1) and the BONA forensic
audit (§6.7), which up to now existed only as a `network_entry` stub.

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| BONA module — three deterministic sub-scores + flags | ADDED | `app/core/bona.py` |
| `BonaReport` / `BonaSubScore` / `BonaGhostScore` Pydantic models | ADDED | `app/models/schemas.py` |
| Parser pipeline — invokes `compute_bona()` after job_match | MODIFIED | `app/core/parser.py` |
| SQLite persistence layer (async SQLAlchemy 2.0 + aiosqlite) | ADDED | `app/db/__init__.py`, `app/db/session.py`, `app/db/models.py`, `app/db/repository.py` |
| Employer / policymaker read API (`GET /api/v1/profiles`, `/profiles/{id}`, `/dashboard`) | ADDED | `app/api/employer.py` |
| `parser_version` bump to `sse-0.4`; lifespan calls `init_db()`; BackgroundTasks upsert | MODIFIED | `app/main.py`, `app/api/routes.py` |
| `BonaPanel` component + `BonaReport`/`JobMatchSignal`/`OpportunityEntry` types | ADDED | `frontend/src/components/BonaPanel.tsx`, `frontend/src/lib/types.ts` |
| ProfileCard wires `<BonaPanel>` between AutomationRisk and NEET context | MODIFIED | `frontend/src/components/ProfileCard.tsx` |
| Tests — BONA unit + contract; DB persistence + RBAC + dashboard aggregation | ADDED | `tests/test_bona.py`, `tests/test_db.py` |
| `sqlalchemy>=2.0.30` + `aiosqlite>=0.19.0` | ADDED | `requirements.txt` |

### 3. Summary of Changes

**3.1 BONA — `app/core/bona.py`**
Three sub-scores, all derived from non-PII signals already on the
ProfileCard, so BONA never sees `raw_input`:
* `network_capture` — Herfindahl-style channel concentration over
  matched opportunities, plus an employer-type diversity bump.
* `ghost_listings` — per-opportunity sanity audit (wage_range,
  formalization_path, employer_type, isco_code, coordinates). Each
  missing field bumps a per-listing ghost probability; aggregate is
  the count-weighted mean. Flagged listings counted explicitly.
* `programme_leakage` — language coverage + zero-credential reach +
  informal-economy share gap.

Output is the `BonaReport` Pydantic model, attached to ProfileCard as
an optional field. Flag list is capped at 8 for SPA scannability.

**3.2 SQLite persistence — `app/db/`**
* Async SQLAlchemy 2.0 + `aiosqlite` (no external infra; `unmapped.db`
  in the cwd by default; override via `UNMAPPED_DB_URL`).
* `Profile` table: PK = `profile_id` (deterministic from text hash) so
  duplicate `/parse` calls upsert one row. Flat indexed columns
  (wage_score, growth_score, automation_risk_tier, bona_overall_tier,
  zero_credential, skill_count) derived at insert time; `profile_json`
  holds the full ProfileCard.
* `ApiKey` table — bcrypt-ready upgrade path, unused in MVP.
* `init_db()` runs in the lifespan and **never raises** — failure is
  logged, `is_db_enabled()` flips to False, app keeps serving `/parse`
  in stateless mode (per Master Context §8 Priority 3 step 8).
* Write side uses FastAPI **`BackgroundTasks`**, not raw
  `asyncio.create_task`. Reason: `create_task` inside a TestClient
  request can be cancelled before the SQLite commit lands, producing
  flaky persistence. BackgroundTasks runs after the response ships but
  inside the request scope, so it's both non-blocking and reliable.

**3.3 Employer / policymaker API — `app/api/employer.py`**
Mounted under `/api/v1`:
* `GET /api/v1/profiles?country=&limit=&offset=` — non-PII summary list
* `GET /api/v1/profiles/{profile_id}` — full ProfileCard (no raw_input)
* `GET /api/v1/dashboard` — aggregates only: counts by country, avg
  wage/growth, automation-risk distribution, BONA distribution, zero-
  credential rate. Implements the policymaker view promised in §6.3.

Auth: bearer token via `UNMAPPED_ADMIN_TOKEN`. If unset, all three
endpoints return HTTP 503 (operator must explicitly enable). Wrong
token → 401. The bcrypt-hashed `ApiKey` table exists for the eventual
multi-tenant path but is not wired into auth yet — single-token
hackathon scope.

**3.4 Frontend — `BonaPanel`**
Three sub-score bars + flag list + sources line, slotted between
`AutomationRisk` and `NeetContext` in `ProfileCard.tsx`. Reuses the
same low/medium/high vocabulary as automation risk so the user only
learns one scale.

### 4. Compatibility / Risk
* `bona`, `automation_risk`, `neet_context`, `job_match` are all
  optional on the wire — older SPA versions render unchanged.
* DB is best-effort everywhere. The /parse contract is unchanged on
  failure; tests confirm 226/226 with and without a DB file present.
* `raw_input` is never persisted (PII rule §5.4) — verified by
  `tests/test_db.py::test_get_profile_returns_full_card`.
* Frontend `tsc --noEmit` cleared all errors caused by these changes;
  one pre-existing `TIER_LABEL` unused-var warning in
  `JobMatchPanel.tsx` is unrelated. The pre-existing
  `ProfileCard.test.tsx` failure (expects an outdated
  "Mobile-money cooperative" channel string that the mock fixture
  removed in commit `c875894`) is also unrelated and unchanged.

### 5. Follow-ups
* Wire the `ApiKey` table into the bearer dependency for per-employer
  keys (replace `UNMAPPED_ADMIN_TOKEN` lookup with bcrypt verify).
* Build the policymaker SPA route (Master Context §8 Priority 4) on
  top of `GET /api/v1/dashboard`.
* Consider adding BONA distribution to the Profile flat columns so the
  dashboard can paginate over hundreds of profiles without scanning
  every JSON blob (already in place — `bona_overall_tier` is indexed).

---

## LOG ENTRY: 2026-04-26 (v0.3.3 — Armenian NLP Re-architecture)

**Entry ID:** `LOG-0005`
**Version:** `v0.3.3`
**Branch:** `module/m1-armenian-nlp`
**Author:** Claude 1 (Senior Data & Product Analyst — backend NLP)
**Status:** COMPLETE — 212/212 tests passing locally (189 prior + 23 new); previously failing abbreviated-Armenian translator test now green offline.

### 1. Change Type
`refactor` — Replaces the multilingual-embedder stage (E5-small via `transformers`/`torch`) with a two-tier Armenian normaliser. Drops a ~700 MB hard dependency that was failing to load on every dev machine, and recovers recall on heavily abbreviated Armenian inputs that embeddings could not reach.

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| Armenian normaliser (Tier A: regex abbreviation expander; Tier B: Anthropic Haiku 4.5) | ADDED | `app/core/armenian_llm.py` |
| Parser pipeline | MODIFIED — replaces `_apply_semantic_stage` with `_run_alias_and_regex` helper + Stage 0 normaliser + Stage 3 LLM second pass | `app/core/parser.py` |
| `parser_version` | BUMPED to `v0.3.3` (internal VSS); routes-side unchanged | `app/core/parser.py` |
| Tests for Armenian normaliser | ADDED — 23 cases covering script detection, abbreviation expansion, LLM graceful-degradation contract, and parser integration | `tests/test_armenian_llm.py` |
| Requirements | torch + transformers downgraded to OPTIONAL (commented); `anthropic>=0.40.0` added | `requirements.txt` |

### 3. Summary of Changes

**3.1 Why E5 was failing**
Local containers don't have `torch`, so `MultilingualEmbedder.available` was permanently `False` and the parser silently fell back to alias_registry + regex. Even when E5 *did* load, it had near-zero recall on CV-style abbreviated Armenian (`թ.-ն. ռ. ու հ.` = "translator from Russian to Armenian"; `ծ. ե.` = "I am a programmer"). Single-letter Unicode tokens carry no usable embedding signal.

**3.2 Tier A — deterministic abbreviation expander (offline-first)**
A short, context-anchored regex catalogue in `armenian_llm.py` expands the closed set of abbreviations seen in the demo corpus into canonical Armenian roots that the existing `_SKILL_PATTERNS` / `_ARMENIAN_SKILL_PATTERNS` already match (`թ.-ն. ռ.` → `թարգմանիչ`; `ծ. ե.` → `ծրագրավորող`; `կ. և ձ.` → `դերձակ կարուհի`; `վ. է` → `վարորդ`; `Gym.` → `Գյումրի`). Expansions are appended to the input rather than substituted, so `source_phrases` retain the original abbreviated surface form for the evidence chain.

**3.3 Tier B — Anthropic Haiku 4.5 normaliser**
When (a) Armenian script is present, (b) Tier A + alias + regex still produced fewer than 2 skills, and (c) `ANTHROPIC_API_KEY` is set, the parser asks Haiku 4.5 (`claude-haiku-4-5-20251001`) for a comma-separated list of canonical English skill phrases, appends them to the text, and re-runs the alias + regex stages. Calls are cached by SHA-256 of the input, system prompt is `cache_control: ephemeral` for prompt-cache reuse, max-tokens capped at 200, timeout 5 s. Any failure (no key, network error, missing SDK) is swallowed — the parser falls through to its existing path without raising.

**3.4 Justification — LLM over Xenova/ONNX**

| Criterion | Anthropic Haiku 4.5 | Xenova / ONNX (e.g. `paraphrase-multilingual-MiniLM`, `LaBSE`) |
|---|---|---|
| Recall on abbreviated Armenian (`թ.-ն.`, `ծ. ե.`) | High — LLM resolves contextually | Near-zero — same root failure as E5 |
| Local install footprint | ~5 MB (`anthropic` SDK only) | ~50–200 MB ONNX runtime + model weights |
| Cold-start latency | None (HTTP call only) | 1–4 s model load on first request |
| Demo robustness on bad wifi | LLM optional → falls back to Tier A offline | No fallback once model is required |
| Per-request cost | ~$0.0008 / call, cached after first hit | Free but adds CPU cost per call |
| Maintenance | Closed prompt + tiny code surface | Model versioning, ONNX export, tokenizer drift |

The deciding factor: Xenova would replicate the original failure mode (embeddings can't read single-letter abbreviations) while keeping a heavy dependency. The LLM path solves the actual recall problem, the offline Tier-A path keeps the demo working without a key, and the implementation is one new file ~250 LoC.

### 4. Compatibility / Risk
- All 189 pre-existing tests still pass; the previously failing `TestArmenianAliasDetection::test_translator_in_armenian_script` is now green via Tier A only (no API key required).
- `MultilingualEmbedder` and `semantic_match` remain in `app/core/multilingual.py` for backwards import compatibility, but are no longer wired into the parser.
- API contract unchanged. Frontend mock fallback path is unaffected.

### 5. Follow-ups
- Frontend: no changes required.
- Ops: when deploying with a key, set `ANTHROPIC_API_KEY` and (optionally) `UNMAPPED_LLM_MODEL`, `UNMAPPED_LLM_TIMEOUT_S`. Set `UNMAPPED_LLM_DISABLE=1` for fully-offline runs.
- Future: extend Tier-A catalogue as more demo corpora surface; consider pushing the abbreviation table into `country_profile.json` once the schema is touched.

---

## LOG ENTRY: 2026-04-26 (v0.3.2 — Module 2 + Real Data + PII Fix)

**Entry ID:** `LOG-0004`
**Version:** `v0.3.2`
**Branch:** `fixes`
**Author:** Claude (Senior Data & Product Analyst, working from `UNMAPPED_Master_Context.docx`)
**Status:** COMPLETE — 117/117 tests passing locally (106 backend non-embedder + 11 new automation-risk + 27 frontend incl. AutomationRisk)
## LOG ENTRY: 2026-04-26 (v0.4.0 — Module 2: Dynamic Job-Match Signal)

**Entry ID:** `LOG-0004`
**Version:** `v0.4.0`
**Branch:** `module/m2`
**Author:** Claude (Senior Full-Stack Engineer — M2 Job-Match)
**Status:** COMPLETE — 178/178 tests passing (29 new M2 tests), ready for merge to `dev`

---

### 1. Change Type
`feat` — Implements the highest-impact gaps from the Master Context document:
(a) Module 2 — AI Readiness & Displacement Risk Lens (LMIC-calibrated);
(b) Bundled real ILOSTAT/WDI/Wittgenstein/Data360 data with cited rationale;
(c) NEET context (Signal 4 from §2.3) surfaced on the ProfileCard;
(d) Removes localStorage PII violation per Protocol §5.4 / Master Context §6.5.
`feat` — Module 2: BONA-style dynamic job-match signal engine. Replaces static `network_entry` lookup with a full opportunity-scoring pipeline using VSS `taxonomy_code` (ISCO-08) against a per-country `opportunity_catalog`. Adds `job_match` field to `ProfileCard`. Adds `JobMatchPanel` to the SPA. Zero breaking changes to M1 contract.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| ILOSTAT GH wage bands + 5yr CAGR | ADDED — cited fixture | `data/ilostat_GH.json` |
| ILOSTAT AM wage bands + 5yr CAGR | ADDED — cited fixture | `data/ilostat_AM.json` |
| Frey-Osborne automation probabilities | ADDED — ISCO-08 mapped | `data/frey_osborne_isco.json` |
| ILO Future of Work LMIC adjustment | ADDED — country × ISCO factors | `data/ilo_lmic_adjustment.json` |
| Wittgenstein SSP2 2025–2035 | ADDED — post-sec attainment | `data/wittgenstein_2035.json` |
| Data360 NEET rates | ADDED — SDG 8.6.1 | `data/data360_neet.json` |
| `data_sources.py` | ADDED — lazy lru_cache loaders | `app/core/data_sources.py` |
| `automation_risk.py` | ADDED — Module 2 minimum-viable | `app/core/automation_risk.py` |
| `signals.py` | MODIFIED — wage/growth load from fixtures, cite source in rationale; `get_neet_context` added | `app/core/signals.py` |
| `parser.py` | MODIFIED — `parse_for_profile` returns `automation_risk` + `neet_context` | `app/core/parser.py` |
| `schemas.py` | MODIFIED — `AutomationRisk`, `NeetContext` Pydantic models added (optional on `ProfileCard`) | `app/models/schemas.py` |
| `parser_version` | BUMPED to `sse-0.3.2` | `app/api/routes.py` |
| `types.ts` | MODIFIED — TS twins of new models | `frontend/src/lib/types.ts` |
| `mock.ts` | MODIFIED — Amara + Ani fixtures include automation_risk + neet_context | `frontend/src/lib/mock.ts` |
| `AutomationRisk.tsx` | ADDED — risk tier, probability bar, durable + adjacent skills, sources line | `frontend/src/components/AutomationRisk.tsx` |
| `ProfileCard.tsx` | MODIFIED — renders AutomationRisk + NEET context block when present | `frontend/src/components/ProfileCard.tsx` |
| `storage.ts` | REWRITTEN — drops `saveInput` / `saveResult`, purges legacy v3 PII keys, keeps only locale preference | `frontend/src/lib/storage.ts` |
| `App.tsx` | MODIFIED — input + result no longer persisted | `frontend/src/App.tsx` |
| `api-contract.md` | UPDATED — v0.3.2 contract; new optional fields; data-sources table; PII rule documented | `docs/api-contract.md` |
| Tests | ADDED — `tests/test_automation_risk.py` (11 tests) + `AutomationRisk.test.tsx` (2 tests) | `tests/`, `frontend/src/components/__tests__/` |

---

### 3. Summary of Changes

**3.1 Module 2 — AI Readiness (Master Context §2.2 / §6.2 / Priority 2)**

`compute_automation_risk()` takes the top extracted skill's ISCO-08 code,
looks up the raw Frey-Osborne probability, multiplies by the
country × ISCO ILO LMIC adjustment factor, classifies into
`low / medium / high` risk tiers (thresholds 0.34 / 0.66), and infers
trajectory (`growing / stable / declining`) from the 5yr ILOSTAT sector
growth. Output also includes `durable_skills` (human-edge retention) and
`adjacent_skills` (growth pathway), plus the Wittgenstein 2035
post-secondary narrative for the user's country. All three sources are
cited verbatim in the `sources[]` array.

**3.2 Real ILOSTAT data (Master Context §6.1 / Priority 1)**

`signals.py` now reads `wage_bands` and `growth_5yr` from
`data/ilostat_<CC>.json` via `app/core/data_sources.py`. The hardcoded
`_WAGE_BANDS` and `_NETWORK_ENTRIES` dicts remain as a fallback if
fixtures are unavailable in a deploy. Every `wage_signal.rationale` and
`growth_signal.rationale` now ends with a `Source: …` citation. Brief
requirement BR-05 moves from PARTIAL to MET.

**3.3 NEET context — Signal 4 (Master Context §2.3 / Priority 4)**

`get_neet_context()` returns the country's youth (15–24) NEET rate from
Data360 as a one-sentence narrative with year-cited source. The
ProfileCard surfaces it as a "Local context" footer.

**3.4 PII / localStorage fix (Master Context §6.5 / Protocol §5.4)**

`raw_input` and the `ParseResponse` carry PII (name, age, location,
free-text narrative). The SPA used to cache both under `unmapped:*_v3`
keys. The new `storage.ts` removes both entirely, keeps only the locale
preference (non-PII configuration), and proactively purges any leftover
v2/v3 PII keys on first read so existing installs become compliant
immediately.

**3.5 API contract additions (Master Context §6.8)**

`automation_risk` and `neet_context` are added as **optional** fields on
`ProfileCard`. Older SPA versions render unchanged. The contract doc
explicitly states the stability rule.

---

### 4. Tests

- **Backend regression:** 106 / 106 non-embedder tests pass unchanged
  (test_api 39, test_parser 46, test_bayesian 7, test_taxonomy 6,
  test_country_profile 8). The pre-existing
  `test_translator_in_armenian_script` failure is environmental
  (requires spaCy `xx_ent_wiki_sm` + torch); unrelated to this entry.
- **Backend new:** 11 / 11 in `tests/test_automation_risk.py`. Covers
  empty-input None, Phone Repair GH (low/medium tier), Software AM
  (calibrated higher than raw), GH ≤ AM dampening invariant for the same
  ISCO, NEET GH/AM presence, NEET unknown-country None, automation_risk
  + neet_context surfaced on /parse, ILOSTAT citation in both wage and
  growth rationale.
- **Frontend regression:** 25 / 25 existing tests pass.
- **Frontend new:** 2 / 2 in `AutomationRisk.test.tsx`. Asserts heading,
  low-risk chip, 23% adjusted probability, raw FO probability, and the
  three required source citations.
- **Total locally green:** 117.

---

### 5. Breaking Changes
None. `automation_risk` and `neet_context` are optional. SPA tolerates
their absence. `parser_version` bumped to `sse-0.3.2` (informational
only). `storage.ts` drops `saveInput` / `loadInput` / `saveResult` /
`loadResult`; any caller relying on those would have failed compilation
— there were none in `App.tsx` after the diff.

---

### 6. Brief Compliance Delta (Master Context §11)

| Brief Requirement | Before | After |
|---|---|---|
| BR-02: Module 2 | ❌ NOT BUILT | ✅ minimum-viable shipped |
| BR-04: ≥ 2 modules | M1 only | ✅ M1 + minimum M2 |
| BR-05: ≥ 2 real econometric signals | ⚠️ PARTIAL | ✅ ILOSTAT-cited |
| BR-12: Automation risk LMIC-calibrated | ❌ NOT BUILT | ✅ ILO Future-of-Work factor applied |
| BR-13: Wittgenstein 2025–2035 used | ❌ NOT BUILT | ✅ surfaced in rationale |
| BR-14: ≥ 1 real automation exposure dataset | ❌ NOT BUILT | ✅ Frey-Osborne (2017) bundled |
| Protocol §5.4 / §6.5 PII | ❌ violated | ✅ enforced |

Compliance count: **8 → 13 / 16** (matches the §8 forecast).

---

### 7. Out of Scope (next phases — explicit, per §5)

These remain queued and require infrastructure / external service decisions:

- Phase 1 — Database + Employer API (asyncpg, Alembic, `/api/employer/*`).
- Phase 2 — Employer SPA at `:5174`.
- Phase 3 — Railway deployment (`railway.toml`, Postgres plugin,
  `entrypoint.sh` running `alembic upgrade head` before uvicorn).
- Module 3 full opportunity-matching engine + Kwame's policymaker dashboard.
- Country expansion (NG, KE, TZ, SN). NG is the recommended next.

Per Master Context §6.4, Railway free-tier (512 MB RAM) will require
`UNMAPPED_EMBED_DISABLE=1`.

---

### 8. Next Steps
- [ ] Module 3 — opportunity matching + dual interface (Kwame view).
- [ ] Phase 1 of the implementation plan — DB + Employer API (8 steps).
- [ ] Wire ILOSTAT fixtures into a build-time fetcher (today they're
      hand-curated; see §6.1 of Master Context for the option-(b) path).
- [ ] BONA forensic layer (currently a design concept only).
| `opportunity_catalog` | ADDED to JSON schema | `schemas/country_profile.json` |
| `CountryProfile (GH)` | ADDED `opportunity_catalog` (11 entries: NBSSI, GPRTU, MoMo, Makola, CIDA, …) | `config/ghana_urban_informal.json` |
| `CountryProfile (AM)` | ADDED `opportunity_catalog` (10 entries: TUMO, ATA, e-gov.am, Idram, Inasxarh, …) | `config/armenia_urban_informal.json` |
| `app/core/jobmatch.py` | NEW — BONA scoring engine: `compute_job_match`, `_score_opportunity`, `_skill_boost` | `app/core/jobmatch.py` |
| `get_opportunity_catalog()` | NEW helper on country_profile loader | `app/core/country_profile.py` |
| `OpportunityEntry`, `JobMatchSignal` | NEW Pydantic models | `app/models/schemas.py` |
| `ProfileCard.job_match` | ADDED optional field | `app/models/schemas.py` |
| `parse_for_profile()` | WIRED `compute_job_match`; `network_entry` now dynamic (top-1 opp) | `app/core/parser.py` |
| `OpportunityEntry`, `JobMatchSignal` | NEW TypeScript interfaces | `frontend/src/lib/types.ts` |
| `ProfileCard.job_match` | ADDED optional field | `frontend/src/lib/types.ts` |
| `JobMatchPanel.tsx` | NEW component — score bar + ranked opportunity list with formalization paths | `frontend/src/components/JobMatchPanel.tsx` |
| `ProfileCard.tsx` | INTEGRATED `JobMatchPanel` between hero signals and body | `frontend/src/components/ProfileCard.tsx` |
| `mock.ts` | ADDED `job_match` to GH_AMARA and AM_ANI fixtures | `frontend/src/lib/mock.ts` |
| `tests/test_jobmatch.py` | NEW — 29 tests covering scoring engine + integration | `tests/test_jobmatch.py` |
| `app/main.py` | VERSION bump `0.3.1 → 0.4.0` | `app/main.py` |

---

### 3. Scoring Algorithm (BONA-style)

For each opportunity in `opportunity_catalog`:
```
isco_score   = 1.0 if exact 4-digit ISCO match else 0.6 if same major group else 0.1
skill_boost  = max(confidence) of skills matching this opp's ISCO (exact=conf, major-group=conf*0.6)
score        = isco_score * 0.55 + skill_boost * 0.35
             + 0.15 if zero_credential && opp.accepts_zero_credential
             + 0.10 if profile_language ∈ opp.required_languages
             + 0.05 * min(len(skills)-1, 2)   [diversification]
             clamped to [0, 1]
```
Filter: keep score ≥ 0.35. Rank descending; take top 5.
Overall `job_match.score` = weighted mean of top-3 × 100 (weights 0.5/0.3/0.2), floor 10, ceil 100.

---

### 4. Test Delta

| Suite | Before | After | Delta |
|---|---|---|---|
| `test_api` | 35 | 35 | — |
| `test_bayesian` | 7 | 7 | — |
| `test_country_profile` | 8 | 8 | — |
| `test_jobmatch` | 0 | 29 | **+29** |
| `test_multilingual` | 43 | 43 | — |
| `test_parser` | 46 | 46 | — |
| `test_taxonomy` | 6 | 6 | — |
| **TOTAL** | **149** | **178** | **+29** |

---

### 5. Known Limitations (v0.4.0 MVP)
- Opportunity catalog is Accra/Yerevan-centric; city-level routing not yet implemented.
- The E5-small semantic embedder occasionally produces false-positive skill matches (pre-existing M1 issue) that can surface unexpected top opportunities for edge-case inputs.
- No opportunity freshness / TTL mechanism (catalog is static per deploy).

---

## LOG ENTRY: 2026-04-26 (v0.3.1 — Multilingual SSE Upgrade)

**Entry ID:** `LOG-0003`
**Version:** `v0.3.1`
**Branch:** `module/m1-sse`
**Author:** Claude (Senior Backend Architect — SSE Core)
**Status:** COMPLETE — 149/149 tests passing, ready for merge to `dev`

---

### 1. Change Type
`feat` — Multilingual parser upgrade. Adds `skill_alias_registry` (v0.3.1 §4.6.1) to country profiles and schema. Introduces 4-stage extraction pipeline: locale aliases → English/Armenian regex → multilingual embedder (E5-small/BGE-M3) → noun-phrase taxonomy crosswalk. Expands wage bands, growth channels, and network entries for 10 new ISCO codes. Fixes Windows UTF-8 charmap regression on Armenian/Russian input.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| `skill_alias_registry` | ADDED to schema (v0.3.1 §4.6.1) | `schemas/country_profile.json` |
| `CountryProfile (GH)` | ADDED `skill_alias_registry` (13 entries: Twi/Ga/English) | `config/ghana_urban_informal.json` |
| `CountryProfile (AM)` | ADDED `skill_alias_registry` (13 entries: Armenian/Russian) | `config/armenia_urban_informal.json` |
| `MultilingualEmbedder` | ADDED — lazy E5-small / BGE-M3 via env var | `app/core/multilingual.py` |
| `AliasMatcher` | ADDED — Unicode-NFC case-insensitive alias lookup | `app/core/multilingual.py` |
| `EvidenceParser` | MODIFIED — 4-stage pipeline, `enable_embedder` flag | `app/core/parser.py` |
| `WageBands (GH/AM)` | EXTENDED — new codes 4211, 5120, 7112, 7531, 9211, 9621, 2166, 2411, 8322, 5141 | `app/core/signals.py` |
| `NetworkEntries (GH/AM)` | EXTENDED — entries for all new ISCO codes | `app/core/signals.py` |
| `country_profile.py` | ADDED `get_skill_alias_registry()` + UTF-8 file open fix | `app/core/country_profile.py` |
| API version | BUMPED `parser_version` to `sse-0.3.1` | `app/api/routes.py` |
| Tests | ADDED 43 multilingual tests (Twi, Ga, Armenian, Russian, locale swap) | `tests/test_multilingual.py` |

---

### 3. Summary of Changes

**3.1 skill_alias_registry — primary low-resource path**

Added `skill_alias_registry` block to `schemas/country_profile.json` and both config files. Ghana profile has 13 entries covering Twi (kayayo, trotro, dwadini), Ga colloquial terms (chop bar, kiosk), and English-GH slang (MoMo, Makola trader). Armenia profile has 13 entries covering Armenian script (ուսուցիչ, թարգմանիչ, ծրագրավորող, վարորդ, դերձակ) and Russian inflected forms (переводчик/переводчиком, программист, учитель, портниха).

**3.2 AliasMatcher (`app/core/multilingual.py`)**

Case-insensitive, Unicode-NFC word-bounded regex matching. Longer aliases take priority (sorted descending by length). Returns one `AliasHit` per distinct `canonical_label` — no duplicates. Runs before all other extraction stages.

**3.3 MultilingualEmbedder (`app/core/multilingual.py`)**

Lazy-loaded `intfloat/multilingual-e5-small` (~118 MB, 100+ languages) via raw Hugging Face `transformers.AutoModel` with mean-pool + L2-norm. No `sentence_transformers` dependency. Model selectable via `UNMAPPED_EMBED_MODEL` env var (default: E5-small; production: `BAAI/bge-m3`). Disabled via `UNMAPPED_EMBED_DISABLE=1`. Degrades silently to alias+regex path if unavailable.

**3.4 4-stage extraction pipeline**

`Stage 1` alias_registry (exact/NFC) → `Stage 2` English+Armenian regex → `Stage 3` multilingual embedder (semantic paraphrase, threshold 0.74) → `Stage 4` spaCy noun-phrase taxonomy crosswalk. Each stage skips canonical_labels already locked in by earlier stages to prevent duplication.

**3.5 Extended ISCO coverage**

10 new ISCO codes added to wage bands + network entries for GH and AM: kayayei/porter (9621), mobile-money agent (4211), cook/food-vendor (5120), tailor/seamstress (7531), construction artisan (7112), smallholder farmer (9211), graphic designer (2166), accountant (2411), driver/taxi (8322), hairdresser (5141).

**3.6 Bug fix — Windows UTF-8 encoding**

All `country_profile.py` file opens now pass `encoding="utf-8"` explicitly. Fixes `'charmap' codec can't decode byte 0x81` error that caused Armenia parse to return `{"ok": false}` on Windows when the JSON contains Armenian/Russian Unicode characters.

---

### 4. Tests

- **Regression:** 106 existing tests unchanged — all pass.
- **New:** 43 multilingual tests in `tests/test_multilingual.py`.
  - `TestTwiAliasDetection` (5 parametrized + 4 named = 9 tests): kayayo, trotro, MoMo, dwadini, chop-bar, ISCO codes, wage GHS, network entry.
  - `TestGaAliasDetection` (3 tests): chop bar, phone repair, kiosk.
  - `TestArmenianAliasDetection` (6 tests): Armenian-script teacher/translator/Idram/programmer, AMD wage, USSD *404#.
  - `TestRussianAliasDetection` (6 parametrized + 1 named = 7 tests): teacher/translator/programmer/driver/tailor/accountant; AMD wage.
  - `TestLocaleSwap` (6 tests): GHS vs AMD, USSD codes, network coords differ, zero_credential defaults.
  - `TestAliasMatcher` (7 unit tests): empty, case-insensitive, Unicode NFC, no-duplicate, longest-wins, Twi kayayo→9621, Russian translator→2643.
  - `TestCandidatePhrases` (5 tests): English, Armenian, Russian, deduplication, max_words.
- **Total:** 149/149 passing.

---

### 5. Breaking Changes
None. `parser_version` bumped to `sse-0.3.1` (informational only — SPA surfaces it in latency display).

---

### 6. Next Steps
- [ ] Module 2: Job-match signal (connect VSS to live opportunity feeds)
- [ ] Docker image size audit: confirm `intfloat/multilingual-e5-small` + torch CPU wheel fits ≤ 2 GB
- [ ] Production: set `UNMAPPED_EMBED_MODEL=BAAI/bge-m3` if GPU available
- [ ] Extend alias registry: Ewe (ee-GH), Hausa (ha), Tigrinya for future SSA expansions

---

## LOG ENTRY: 2026-04-26 (v0.3.0 — SSE Hardening)

**Entry ID:** `LOG-0002`
**Version:** `v0.3.0`
**Branch:** `module/m1-sse`
**Author:** Claude (Senior Backend Architect — SSE Core)
**Status:** COMPLETE — 106/106 tests passing, ready for merge to `dev`

---

### 1. Change Type
`feat` + `fix` — Harden Module 1 SSE to match the frozen frontend API contract; add Armenia (AM) locale; add wage/growth/network-entry signals.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| `ProfileCard` | ADDED (new public response shape) | `app/core/parser.py` |
| `WageSignal` | ADDED | `app/core/signals.py` |
| `GrowthSignal` | ADDED | `app/core/signals.py` |
| `NetworkEntryPoint` | ADDED | `app/core/signals.py` |
| `CountryProfile (AM)` | ADDED | `config/armenia_urban_informal.json` |
| `EvidenceParser` | MODIFIED — `parse_for_profile()`, Armenian patterns, `taxonomy_code` | `app/core/parser.py` |
| API contract | BREAKING CHANGE — request now `raw_input/country`, response now `profile/latency_ms` | `app/api/routes.py`, `app/models/schemas.py` |

---

### 3. Summary of Changes

**3.1 Frontend contract alignment (breaking from v0.3-alpha.1)**

After reading `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, and
`docs/api-contract.md`, the API was completely realigned:

| Field | Old (alpha.1) | New (v0.3.0) |
|---|---|---|
| Request key | `text` | `raw_input` |
| Country key | `country_code` | `country` |
| Response wrapper | flat `user/skills/vss_list` | `{ok, profile, latency_ms, country, parser_version}` |
| Skill shape | `label/category/source_phrases` | `name/confidence/evidence` |
| Location | `{city, country_code}` dict | human string `"Accra, Greater Accra"` |
| Languages | BCP-47 list `["ak-GH","en"]` | human names `["Twi","English"]` |
| SMS | `{text, char_count}` object | plain string ≤ 160 chars |
| USSD | nested tree object | `string[]` ≤ 40 chars/line |
| New fields | — | `wage_signal`, `growth_signal`, `network_entry`, `pseudonym`, `age`, `profile_id` |

**3.2 Armenia (AM) locale**

Added `config/armenia_urban_informal.json` (AMD currency, Idram rails, e-gov.am
network entry, hy-AM/ru language support) and registered it in the profile
registry. Added Armenian Unicode script detection + Armenian-specific skill
patterns (teaching "դաս", translation "թարգման", Idram mobile money).

**3.3 Signals engine (`app/core/signals.py` — new module)**

- `compute_wage_signal()`: per-country ISCO-08 wage bands → score 0-100 +
  currency-formatted `display_value` + rationale.
- `compute_growth_signal()`: ambition keyword scoring + digital/financial
  skill boosts + experience multiplier → score 0-100 + rationale.
- `get_network_entry()`: skill taxonomy code → formal-economy entry channel
  + WGS84 coordinates (GH: Accra/MTN MoMo/NBSSI; AM: Gyumri/e-gov.am/Idram).
- `detect_age()`: English + Armenian ("31 տարեկան") age extraction.
- `bcp47_to_human()`: BCP-47 → human-readable language names.

**3.4 Endpoint layout**

- `POST /parse` — primary endpoint (SPA calls `http://localhost:8000/parse`)
- `POST /api/v1/parse` — legacy alias
- `POST /api/v1/generate_profile_card` — explicit card regeneration

---

### 4. Test Results

```
106 passed in 7.18s
  tests/test_api.py          39 passed  (contract compliance + locale swap)
  tests/test_parser.py       46 passed  (Amara GH + Ani AM canonical vectors)
  tests/test_country_profile.py  8 passed
  tests/test_taxonomy.py      6 passed
  tests/test_bayesian.py      7 passed
```

Key test additions:
- Amara canonical: age=27, bookkeeping, fish trading, mobile money, GHS wage
- Ani canonical: age=31 (Armenian script), translation, teaching, AMD wage, AM USSD `*404#`
- Locale swap: GHS vs AMD in wage signal
- Zero-credential path: self-taught / no formal degree
- SMS ≤ 160 chars, USSD 4-8 lines each ≤ 40 chars
- Profile ID deterministic (SHA-256 of input)

---

### 5. Files Modified / Added

```
app/
  main.py                    — mount public_router at "/" + v1_router at "/api/v1"
  api/routes.py              — POST /parse (public), /api/v1/parse, /generate_profile_card
  core/parser.py             — parse_for_profile(), Armenian patterns, taxonomy_code on skills
  core/signals.py            NEW — wage/growth signals + network entry + age/language helpers
  models/schemas.py          — ParseRequest (raw_input/country), ProfileCard, Signal, NetworkEntryPoint
config/
  armenia_urban_informal.json  NEW
tests/
  test_api.py                — full rewrite for new contract (39 tests)
  test_parser.py             — full rewrite inc. Ani Armenia story (46 tests)
docker-compose.yml           — image tag updated to v0.3.0
```

---

### 6. Breaking Changes

Request shape change from `{text, country_code}` → `{raw_input, country}`.
Response shape change from flat VSS list → `{ok, profile, latency_ms, country, parser_version}`.
These break the alpha.1 contract — all clients should migrate to the new shape.
The `/api/v1/parse` alias accepts the new shape too (no old-shape backward compat).

---

### 7. Rollback Path
1. `git revert HEAD` (single commit) restores alpha.1 state.
2. No DB migrations, no persistent state — purely stateless API.

---

## LOG ENTRY: 2026-04-26

**Entry ID:** `LOG-0004`
**Version:** `v0.3.0-sse-alpha.4`
**Branch:** `module/m1-sse-ui` (rebased onto `origin/dev`; no manual conflicts)
**Author:** Claude 2 (frontend / DevOps owner)
**Status:** COMPLETE — lint + 25/25 tests + build all green; ready for PR to `dev`.

---

### 1. Change Type
`feat` (canonical Section 4.2 ProfileCard, two econometric signals as
first-class primitives, AM live) + `chore` (re-align SPA contract to
backend `module/m1-sse` commit `33e13e4`).

This is technically a **breaking** change for the SPA's internal API
shape, but the public `POST /parse` contract is now hardened: the SPA
client matches `app/models/schemas.py` field-for-field.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| `ProfileCard` (Section 4.2) | REBUILT | `frontend/src/components/ProfileCard.tsx` — flat shape with hero row for the two econometric signals |
| `Signal` (wage + growth) | NEW (re-introduced) | `frontend/src/components/SignalBar.tsx` — gradient hero card variant + inline variant |
| `Skill` confidence list | NEW | `frontend/src/components/SkillList.tsx` — derives tier label from `Skill.confidence` (0..1) |
| `NetworkEntryPoint` | UPDATED | `frontend/src/components/NetworkEntryMap.tsx` — accepts `entry` directly, exposes lat/lng caption |
| `OwnershipStatement` (Section 4.2) | UPDATED | now keys off `profile_id` instead of `hl_id` |
| Constraint Layer — SMS | SIMPLIFIED | `SmsPreview` now takes a flat `string` message |
| Constraint Layer — USSD | SIMPLIFIED | `UssdSimulator` now takes a flat `string[]` menu (the recursive tree was removed when the backend reverted to a flat `ussd_menu`) |
| API client | UPDATED | `frontend/src/lib/api.ts` — endpoint moved from `/api/v1/parse` back to canonical `/parse`; request shape `{raw_input, country, language_hint?}`; response `{ok, profile, latency_ms, country, parser_version}` |
| Vite proxy | UPDATED | `vite.config.ts` proxies `/parse`, `/api`, and `/health` to `${VITE_API_URL}` |
| Localization | UPDATED | `LOCALES.AM.backendSupported = true` (Claude 1 shipped `config/armenia_urban_informal.json` in commit `33e13e4`) |

---

### 3. Summary of Changes

Claude 1 hardened the backend `/parse` contract in commit `33e13e4`
("harden SSE to frontend contract — Armenia locale + signals engine"),
reverting from the nested `human_layer.profile_card` shape (which had
been the alpha.2 baseline) to a flat ProfileCard with **explicit
top-level `wage_signal` and `growth_signal`** — exactly the two
econometric signals the v0.2 Section 4.2 spec requires. They also
shipped `config/armenia_urban_informal.json`, making AM a first-class
country.

This entry brings the SPA back into byte-faithful sync with that
contract:

- `frontend/src/lib/types.ts` is now a literal mirror of
  `app/models/schemas.py` (POST /parse).
- `frontend/src/lib/mock.ts` ships canonical Amara (GH) and Ani (AM)
  fixtures with full `wage_signal`, `growth_signal`, `network_entry`,
  flat `sms_summary`, and `ussd_menu` — the SPA renders identically in
  live and offline-fallback modes.
- The `ProfileCard` layout follows v0.2 Section 4.2 exactly: header
  (pseudonym + age + location + parser-source meta), **hero row** with
  the two econometric signals in side-by-side gradient cards, and a
  two-column body (left: languages, network-entry map, ownership
  statement; right: skills with confidence bars).
- `App.tsx` now sends `{raw_input, country}` and reads the flat shape.
- The Constraint Tier switcher (Smartphone / SMS / USSD) is unchanged
  in behaviour but rebuilt against the flat primitives.
- AM no longer requires the offline fallback — the SPA marks it as
  `backendSupported: true`.

#### Anti-conflict rule notes
- `git pull --rebase origin develop` — `develop` does not exist on
  origin (verified via `git ls-remote --heads origin`); the integration
  branch is `dev`. Rebased against `origin/dev`; no manual conflicts.
- New PROJECT_LOG entry placed at the top of the file. All older
  entries (LOG-0001, LOG-0002, alpha.1, alpha.2) preserved verbatim
  per the append-only rule. CHANGELOG updated likewise.

---

### 4. Architecture Decisions

**4.1 Hero row for the two econometric signals**
v0.2 Section 4.2 names wage and growth as the headline primitives of
the Skills Signal Profile. Promoted them out of the body grid into
their own gradient row directly under the header — they should be the
first thing a judge sees.

**4.2 Skill tier derived from confidence on the SPA side**
The backend returns `Skill.confidence` (0..1) without an explicit tier.
The SPA derives the tier label (`Emerging` / `Developing` /
`Established` / `Expert`) from the score using fixed thresholds
(`< 0.45` / `< 0.65` / `< 0.85` / `≥ 0.85`). Same boundaries the
backend uses internally per Claude 1's `app/core/bayesian.py`.

**4.3 Vite proxy widened to /parse + /api + /health**
The canonical backend route moved from `/api/v1/parse` to `/parse` in
alpha.4. The proxy now forwards both, so existing standalone setups
that pointed at `/api/v1/parse` keep working.

---

### 5. Files Created/Modified

```
frontend/src/lib/types.ts                  REWRITTEN (matches schemas.py)
frontend/src/lib/api.ts                    UPDATED  (endpoint /parse)
frontend/src/lib/mock.ts                   REWRITTEN (full GH + AM fixtures)
frontend/src/lib/locales.ts                UPDATED  (AM backendSupported=true)
frontend/src/components/ProfileCard.tsx    REBUILT  (Section 4.2 layout)
frontend/src/components/SignalBar.tsx      REBUILT  (hero + inline variants)
frontend/src/components/SkillList.tsx      NEW      (tier-derived bars)
frontend/src/components/NetworkEntryMap.tsx UPDATED (accepts entry directly)
frontend/src/components/SmsPreview.tsx     UPDATED  (flat string message)
frontend/src/components/UssdSimulator.tsx  UPDATED  (flat string[] menu)
frontend/src/components/OwnershipStatement.tsx UPDATED (profile_id)
frontend/src/App.tsx                       UPDATED  (new request shape)
frontend/vite.config.ts                    UPDATED  (proxy /parse + /api + /health)
frontend/package.json                      UPDATED  (version 0.3.0-sse-alpha.4)
frontend/src/test/fixtures.ts              UPDATED
frontend/src/lib/__tests__/api.test.ts     UPDATED  (new request shape)
frontend/src/components/__tests__/{ProfileCard,SmsPreview,UssdSimulator}.test.tsx UPDATED
frontend/src/__tests__/App.test.tsx        UPDATED  (asserts on Wage/Growth headings)
```

---

### 6. Backward Compatibility

- The `POST /parse` contract is now stable and shared with backend
  (`module/m1-sse@33e13e4`). The SPA does not retain support for the
  alpha.2 nested shape because no production consumer exists.
- Vite proxy still forwards the legacy `/api/v1/parse` route, so any
  pre-existing standalone curl/Postman tests against that path
  continue to work end-to-end through the dev server.
- `VITE_API_URL` semantic continues to be "Vite proxy target", as set
  in alpha.3.

---

### 7. Test Plan

```bash
# Frontend (verified locally in this session)
cd frontend && npm install && npm run lint && npm test && npm run build
#   lint     — clean
#   test     — 8 suites · 25 cases · all passing
#   build    — 182 KB JS / 60 KB gz · 4 KB CSS gz · ~3s

# Backend (Claude 1)
pytest tests/ -v --cov=app
#   Includes test_parser.py canonical Amara vector and AM coverage
#   in tests/test_parser.py + tests/test_api.py.

# Full-stack (NOT executed in this session — Docker Desktop offline)
docker compose up --build
#   Expected:
#     - http://localhost:5173        — SPA, "Try the Amara story" → submit
#     - http://localhost:8000/parse  — POST returns full ProfileCard
#     - http://localhost:8000/health — {"status":"ok",...}
#     - "Live parser" badge with real backend latency_ms / parser_version
```

---

### 8. Rollback Path
1. `git revert <alpha.4 head>` — restores alpha.3 SPA (nested shape +
   recursive USSD navigator).
2. The compose stack is fully stateless; rollback is safe at any time.

---

### 9. Notes for Reviewers / Claude 1

- The SPA is now strictly downstream of `app/models/schemas.py`. If
  the backend changes any field there, the matching change must land
  on this branch in the same PR cycle.
- `frontend/src/lib/mock.ts` doubles as a golden fixture set. Backend
  tests in `tests/test_parser.py` should produce shape-equivalent
  output for the canonical Amara story.
- Two open backend follow-ups (not blocking for the demo):
  1. Wire `network_entry` for AM through `app/core/signals.py` against
     actual Yerevan/Gyumri pin coordinates.
  2. The `/api/v1/parse` legacy alias can be removed once nothing
     external depends on it.

---

*End of LOG-0004*

---

## LOG ENTRY: 2026-04-26

**Entry ID:** `LOG-0003`
**Version:** `v0.3.0-sse-alpha.3`
**Branch:** `module/m1-sse-ui` (rebased onto `origin/dev`)
**Author:** Claude 2 (frontend / DevOps owner)
**Status:** COMPLETE — full-stack docker-compose authored, lint+build+tests green

---

### 1. Change Type
`feat` (compose stack) + `chore` (rebase integration). No external API contract change.

---

### 2. Primitives Affected

| Primitive | Action | File |
|---|---|---|
| Build/Deploy | NEW | `docker-compose.yml` (rewritten), `frontend/Dockerfile.dev` (new), `.dockerignore` (new), `frontend/.dockerignore` (new) |
| Frontend HTTP client | CHANGED | `frontend/src/lib/api.ts` — relative `/api/v1/*` URLs always; `VITE_API_URL` is now interpreted as the *proxy target*, not a browser-side origin |
| Vite config | CHANGED | `frontend/vite.config.ts` — adds `server.proxy['/api'] → ${VITE_API_URL}` keyed off `loadEnv` |
| Test suite | CHANGED | `frontend/src/lib/__tests__/api.test.ts` — asserts on relative URL fetch; obsolete "empty URL → demo" case removed |
| Frontend env defaults | CHANGED | `frontend/.env.example` — documents the three modes (standalone / docker-compose / demo) |

---

### 3. Summary of Changes

#### 3.1 Branch integration (anti-conflict rule)
`develop` does not exist on origin. The actual integration branch is
`origin/dev`, with PR #1 (backend, `module/m1-sse`) and PR #2 (frontend
alpha.1, `module/m1-sse-ui`) already merged. Ran
`git pull --rebase origin dev` from `module/m1-sse-ui`; alpha.2 + the
test/build fixes replayed cleanly with no manual conflict resolution
(non-overlapping line edits across PROJECT_LOG, CHANGELOG, .gitignore).

After the rebase the working tree contains both halves of the project
in one place — backend (`app/`, `config/`, `schemas/`, `tests/`,
`Dockerfile`, `requirements*.txt`) plus frontend (`frontend/`).
PROJECT_LOG and CHANGELOG were preserved verbatim per the append-only
rule; this entry is added at the top per the same rule.

#### 3.2 Full-stack docker-compose
Rewrote the root `docker-compose.yml` (which previously only ran the
backend as `sse-api`):

- Service renamed to `backend` (matches user spec for "internal
  communication via service name").
- New `frontend` service builds from `frontend/Dockerfile.dev`, runs
  `vite dev --host 0.0.0.0 --strictPort`, bind-mounts the source for
  hot reload, keeps `node_modules` in an anonymous volume so the
  host's lockfile/state never leaks in.
- Both services have healthchecks + `restart: unless-stopped`.
  `frontend` `depends_on: backend (service_healthy)`.
- Dedicated bridge network `unmapped` so service-name DNS works.
- Backend `CORS_ORIGINS` extended to include `http://frontend:5173` for
  intra-cluster CORS preflights (browser-origin entries kept too).
- Removed legacy `version: "3.9"` (Compose v2 ignores it).

#### 3.3 Browser-vs-container DNS resolution

The brief specified `VITE_API_URL=http://backend:8000`, but a browser
on the developer's host **cannot resolve** the docker-internal hostname
`backend`. Resolved this by promoting `VITE_API_URL` to a
**Vite-dev-server proxy target** rather than a browser-side base URL:

- `api.ts` now always fetches `/api/v1/parse` (relative, same-origin).
- `vite.config.ts` reads `VITE_API_URL` via `loadEnv` and configures
  `server.proxy['/api'] → ${VITE_API_URL}`. Vite, running inside the
  frontend container, resolves `backend` against docker DNS and forwards
  the call.
- Net effect: same SPA code path works for standalone dev
  (`VITE_API_URL=http://localhost:8000`), docker-compose
  (`VITE_API_URL=http://backend:8000`, set in the compose service), and
  pure-mock demo (`VITE_DEMO_MODE=true`, no fetch).

#### 3.4 Verification

- `docker compose config` — validates clean (full normalized output
  inspected: services, networks, volumes, healthchecks all parse).
- `docker compose build` / `up` — **NOT** executed in this session: the
  Docker Desktop Linux engine pipe was not responsive on the dev box
  (`open //./pipe/dockerDesktopLinuxEngine: file not found`). Verification
  step belongs to the user (Docker Desktop running) — see Section 7.
- `npm run lint` — clean.
- `npm test` — 8 suites / 25 cases passing (the obsolete "empty
  VITE_API_URL → demo" case was deliberately removed).
- `npm run build` — 187 KB JS / 61 KB gz, 4 KB CSS gz, ~2 s.

---

### 4. Architecture Decisions

**4.1 Vite proxy over browser-side absolute URL**
The user spec asks for `VITE_API_URL=http://backend:8000`, but browsers
can't resolve docker-only DNS names. Treating it as a proxy target
honors the spirit of the spec (frontend talks to backend by service
name) without breaking from the browser's perspective. Same-origin =
no CORS preflight = simpler.

**4.2 Bind-mount source, anonymous-volume node_modules**
The classic Node-on-docker pattern. Without the anonymous volume the
host's `node_modules/` (with its native bindings compiled for the host
OS) would shadow the container's, breaking esbuild and friends.

**4.3 Healthcheck-gated startup ordering**
`depends_on: backend (service_healthy)` ensures the SPA doesn't try
to proxy before FastAPI has loaded spaCy and warmed the parser cache.
Backend's `start_period: 30s` accommodates the cold-start cost.

**4.4 Two .dockerignore files**
Root `.dockerignore` excludes `frontend/` from the backend image. A
separate `frontend/.dockerignore` excludes `node_modules`, `dist`,
`.tsbuildinfo`, etc. from the frontend image. Without these, the
backend image would balloon with frontend artefacts and vice versa.

---

### 5. Files Created/Modified

```
docker-compose.yml                  REWRITTEN — backend + frontend, healthchecks, network
.dockerignore                       NEW — scopes the backend image build
frontend/Dockerfile.dev             NEW — node:20-alpine + vite --host 0.0.0.0
frontend/.dockerignore              NEW
frontend/vite.config.ts             CHANGED — server.proxy keyed off VITE_API_URL
frontend/src/lib/api.ts             CHANGED — always-relative /api/v1/parse
frontend/src/lib/__tests__/api.test.ts CHANGED — relative-URL assertion, dropped obsolete case
frontend/.env.example               CHANGED — three-mode documentation
.gitignore                          CLEANED — deduped after rebase auto-merge
```

---

### 6. Backward Compatibility
- `VITE_API_URL` semantic shifted from "browser-side origin" to "Vite
  proxy target". Any downstream user of alpha.2 who pointed it at a
  browser-resolvable hostname continues to work — the proxy will still
  forward to it. No change to the public `/api/v1/parse` contract.
- Internal SPA test that relied on "empty `VITE_API_URL` ⇒ demo mode"
  is removed; demo mode is now controlled exclusively by
  `VITE_DEMO_MODE=true`.

---

### 7. Test Plan

```bash
# Frontend (already verified locally)
cd frontend && npm install && npm run lint && npm test && npm run build

# Backend (run on a machine with the spaCy model fetchable)
pip install -r requirements-dev.txt
python -m spacy download xx_ent_wiki_sm
pytest tests/ -v --cov=app

# Full-stack (NOT run in this session — Docker Desktop daemon offline)
docker compose up --build
# Expected:
#   - http://localhost:5173 — SPA loads, profile card renders
#   - http://localhost:8000/health — {"status":"ok",...}
#   - "Try the Amara story" → submit → "Live parser" badge with real
#     processing_time_ms / parser_version from /api/v1/parse
#   - http://localhost:8000/docs — FastAPI Swagger UI
```

---

### 8. Rollback Path
1. `git revert <alpha.3 head>` — restores alpha.2 SPA + standalone backend.
2. `docker compose down --volumes --remove-orphans` to clear local state.
3. The compose stack is fully stateless (no DB), so rollback is safe at any time.

---

### 9. Instructions for Claude 1 (handoff)
- The Vite proxy approach means CORS preflights from the SPA disappear in
  docker-compose mode (same-origin from browser POV). You can leave
  `CORS_ORIGINS` as-is — it still matters for standalone dev where the
  browser hits the backend directly on port 8000.
- AM (Armenia) `country_profile` is the natural next backend task —
  the SPA is already fully wired for it; today AM falls back to the
  bundled mock with an "Offline fallback" badge.
- A multi-stage production frontend Dockerfile (`npm run build` → nginx)
  is the obvious follow-up; `Dockerfile.dev` was scoped to dev only.

---

*End of LOG-0003*

---


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
Append-only running record of every major contribution. Format follows v0.2
Section 12.4: each entry starts with a level-2 header `## YYYY-MM-DD — vX.Y.Z[-tag]`
and uses the seven canonical fields below. Never edit a past entry; correct via
a follow-up entry.

> ⚠️ **Inference note (Claude 2):** I do not have direct access to the
> `UNMAPPED_Protocol_v0.2_Complete.docx` file in this session. The Section 12.4
> field set below is reconstructed from the prompt brief. When the canonical
> spec is shared, please reconcile and amend in a follow-up entry rather than
> rewriting history.

---

## 2026-04-26 — v0.3.0-sse-alpha.1

- **Module:** M1 — Skills Signal Engine (Frontend / Human + Constraint Layer)
- **Author:** Claude 2 (frontend) — coordinating with Claude 1 (backend) via
  this log and `docs/api-contract.md`.
- **Branch:** `module/m1-sse-ui` from `main`.
- **Change type:** Feature (additive; first feature release on top of the
  empty `Initial commit`).
- **Primitives affected:**
  - **Human Layer** — `ProfileCard`, `SignalBar`, `NetworkEntryMap`,
    `QrSimulation` render the v0.2 Section 4.2 layout.
  - **Constraint Layer** — `SmsPreview`, `UssdSimulator` provide the
    low-bandwidth fallback experience.
  - **Localization Layer** — `LocaleSwitcher` toggles Ghana ↔ Armenia
    `country_profile`s; samples and USSD shortcodes per locale.
  - **Interface contract** — `docs/api-contract.md` + `frontend/src/lib/types.ts`
    define `POST /parse` for Claude 1.
- **Backward compatibility:** N/A — first feature release. `docs/api-contract.md`
  becomes the baseline for future SemVer decisions.
- **Test plan:**
  - `npm run lint` (strict TypeScript, no unused locals/params).
  - `npm run build` to confirm the production bundle compiles.
  - Manual: load SPA → paste Ghana sample → verify ProfileCard renders all
    primitives (header, skills, both signals, map, QR), SMS card shows
    correct segment count, USSD simulator dials *789# and renders the menu.
  - Manual: switch to Armenia → sample button populates Armenian text →
    re-parse → verify USSD shortcode flips to *404# and Armenian menu lines.
  - Manual offline: stop the backend / unset `VITE_API_URL` → verify the
    "Offline fallback" badge appears and the card still renders.
- **Rollback path:** `git checkout main && git branch -D module/m1-sse-ui` —
  no migrations, no data, no third-party state to revert. Tag
  `v0.3.0-sse-alpha.1` is not yet pushed; the branch remains the only artifact
  until the PR is merged.
- **Next step (handoff to Claude 1):** Implement FastAPI `POST /parse`
  matching `docs/api-contract.md`. Use the two fixtures in
  `frontend/src/lib/mock.ts` as your golden tests so the SPA renders
  identically in live and fallback modes. CORS allow-list:
  `http://localhost:5173` for dev.

---

## 2026-04-26 — v0.3.0-sse-alpha.2

- **Module:** M1 — Skills Signal Engine (Frontend / Human + Constraint Layer)
- **Author:** Claude 2 (frontend) — reconciling with Claude 1's LOG-0001 on
  branch `module/m1-sse`.
- **Branch:** `module/m1-sse-ui` (continuation; v0.3.0-sse-alpha.1 base).
- **Change type:** `feat` + `breaking` for the internal API client (the
  external SPA UX is additive — this is the first integration with a real
  backend, so there is no production consumer to break).
- **Primitives affected:**
  - **Interface contract** — replaced the inferred alpha.1 contract with
    Claude 1's canonical shape. Endpoint moved from `/parse` to
    `/api/v1/parse`. Request fields: `raw_input → text`, `country → country_code`,
    added `context_tag`. Response fields: flat `profile` → nested
    `{ user, skills, vss_list, human_layer, meta }`.
  - **Human Layer** — `ProfileCard` rebuilt against `human_layer.profile_card`
    (display_name, headline, location, languages, skills_summary,
    bio_snippet, zero_credential_badge, top_skill); skills bars now read
    `confidence_score` + `confidence_tier ∈ {emerging, developing, established, expert}`
    with tier-coloured rendering; ISCO/ESCO codes surfaced as inline chips;
    `<details>` evidence-chain reveal renders the full VSS list when judges
    want depth.
  - **Ownership Layer** — new `OwnershipStatement` component placed inside
    the profile card per Section 4.2: portable, revocable, holder-controlled.
  - **Constraint Layer** — new `ConstraintTierSwitcher` (smartphone / SMS /
    USSD) lets a judge collapse the same profile across the three delivery
    tiers in one click. `UssdSimulator` rewritten as a recursive tree
    navigator that walks `human_layer.ussd_tree` node-by-node with a
    Back stack. `SmsPreview` reads the structured `sms_summary` and shows
    char_count + segment math.
  - **Localization Layer** — Armenia keeps its locale UX; backend coverage
    is Ghana-only for now, so AM transparently uses the bundled mock and
    surfaces an "Offline fallback" badge instead of a broken card.
  - **Test infrastructure (NEW)** — Vitest + jsdom + RTL. Suites cover
    InputPanel, LocaleSwitcher, ProfileCard, SmsPreview, UssdSimulator,
    ConstraintTierSwitcher, the api fallback wrapper, and an App-level
    integration test that walks input → submit → tier-swap.
- **Files added/changed:**
  - Modified: `frontend/src/lib/{types.ts, api.ts, mock.ts, locales.ts, storage.ts}`,
    `frontend/src/components/{ProfileCard, SignalBar, NetworkEntryMap, QrSimulation, SmsPreview, UssdSimulator, InputPanel}.tsx`,
    `frontend/src/App.tsx`, `frontend/{package.json, vite.config.ts, tsconfig.json}`,
    `docs/api-contract.md`, `CHANGELOG.md`.
  - Added: `frontend/src/components/{OwnershipStatement, ConstraintTierSwitcher}.tsx`,
    `frontend/src/test/{setup.ts, fixtures.ts}`,
    `frontend/src/{components/__tests__/*, lib/__tests__/api.test.ts, __tests__/App.test.tsx}`.
- **Backward compatibility:** N/A for the SPA-as-product (first real
  release). The contract change is breaking against the inferred alpha.1
  contract — that contract had no consumers because no backend implemented
  it; the canonical contract from Claude 1 is now the baseline.
- **Test plan:**
  - `npm install && npm run lint` — strict TS, no unused locals/params.
  - `npm test` — 7 suites, 23 cases (InputPanel × 6, LocaleSwitcher × 2,
    ProfileCard × 2, SmsPreview × 3, UssdSimulator × 3, ConstraintTier × 2,
    api × 5, App-integration × 3 — note: not all run yet, dependencies
    need installing first).
  - Manual: load SPA → click "Try the Amara story" → submit → verify
    profile card renders headline + zero-credential badge + both skills
    with correct tier chips (`Established` / `Developing`) + ISCO codes
    + evidence chain `<details>`.
  - Manual: click `SMS` tier → verify Tier-2 framing renders the
    `sms_summary.text` with the segment counter; click `USSD` tier →
    verify dial / option-tap / `0. Back` walk through the tree.
  - Manual: switch to Armenia → verify "Offline fallback" badge,
    Armenian/Russian USSD strings render.
  - Live integration: with Claude 1's backend up at `http://localhost:8000`
    + `VITE_API_URL=http://localhost:8000` set, a Ghana submission should
    show a `Live parser` badge with `parser_version` from `meta`.
- **Rollback path:** `git revert <alpha.2 commit>` — no migrations, no
  shared state, the alpha.1 SPA is a clean previous state. If the
  contract reconciliation itself is the issue, `git checkout
  v0.3.0-sse-alpha.1` (tag will be created at PR-merge time).
- **Open issues / next steps:**
  - Run `npm install` in CI and add a GitHub Action to gate `npm run lint`
    + `npm test` on every PR.
  - Add an Armenia `country_profile` to the backend (Claude 1 task) to
    replace the mock-only AM path with live data.
  - Replace the offline SVG `NetworkEntryMap` with MapLibre + a small set
    of country bounding boxes in v0.4.
  - Real verifiable-credential resolver behind the QR (currently a demo
    `unmapped.demo/hl/...` URL).
