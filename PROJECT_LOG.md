# UNMAPPED Protocol — Project Log

Format per Section 12.4 of UNMAPPED Protocol v0.2 spec.

> Per anti-conflict rule: new entries are added at the top of this file.
> Older entries below are preserved verbatim (append-only).

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
