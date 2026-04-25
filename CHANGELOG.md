# Changelog

All notable changes to UNMAPPED follow [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

> Newer entries are added at the top. Older entries below are preserved
> verbatim (append-only).

---

## [0.3.0-sse-alpha.3] — 2026-04-26

### Branch: `module/m1-sse-ui` (rebased onto `origin/dev`)

### Added
- **Full-stack `docker-compose.yml`** — `backend` (FastAPI + spaCy)
  and `frontend` (Vite dev-server) wired on a private bridge network.
  Healthchecks, restart policies, hot-reload bind-mounts, and
  `depends_on: backend (service_healthy)` for the frontend.
- **`frontend/Dockerfile.dev`** — `node:20-alpine` running
  `vite dev --host 0.0.0.0 --strictPort`. Layer-cached
  `npm install`; source bind-mounted at runtime.
- **Root `.dockerignore`** scopes the backend image (excludes
  `frontend/`, docs, tool dirs).
- **`frontend/.dockerignore`** scopes the frontend image (excludes
  `node_modules`, `dist`, `.tsbuildinfo`, `.vite`).

### Changed
- **Browser-side fetch is now always same-origin.** `api.ts` requests
  the relative `/api/v1/parse` URL. `VITE_API_URL` is reinterpreted
  as the *Vite dev-server proxy target* (read in `vite.config.ts`
  via `loadEnv`), which lets the SPA work cleanly under
  `docker-compose` (proxy to `http://backend:8000`), standalone dev
  (proxy to `http://localhost:8000`), and pure-mock demo
  (`VITE_DEMO_MODE=true`) — all from one code path. CORS preflights
  vanish in docker mode.
- **Renamed compose service** `sse-api` → `backend` to match the
  user-spec for service-name based internal communication.
- **Rebased `module/m1-sse-ui` onto `origin/dev`** (the actual
  integration branch — `develop` does not exist on origin). All
  alpha.2 commits replayed cleanly with no manual conflict
  resolution; PROJECT_LOG and CHANGELOG entries preserved verbatim.
- **`frontend/.env.example`** — documents the three runtime modes
  (standalone / docker-compose / demo).
- **Backend `CORS_ORIGINS`** in compose extended with
  `http://frontend:5173` for intra-cluster calls.

### Removed
- Obsolete legacy `version: "3.9"` line at the top of compose
  (Compose v2 ignores it with a warning).
- Obsolete API test asserting "empty `VITE_API_URL` ⇒ demo mode" —
  demo mode is now controlled exclusively by `VITE_DEMO_MODE=true`.

### Verified locally
- `docker compose config` — clean (full normalized config inspected).
- `npm run lint` — clean.
- `npm test` — 8 suites / 25 cases passing.
- `npm run build` — 187 KB JS / 61 KB gz, 4 KB CSS gz, ~2 s.

### NOT yet verified in this session
- `docker compose up --build` — Docker Desktop's Linux engine pipe
  was not responsive on the dev box. Verification path documented
  in `PROJECT_LOG.md` Section 7 (`LOG-0003`).

### Backward compatibility
- `VITE_API_URL` semantic shifted from "browser origin" to "Vite
  proxy target". Existing alpha.2 standalone setups continue to
  work — the proxy still forwards correctly. No change to the public
  `POST /api/v1/parse` contract.

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
All notable changes to UNMAPPED Protocol are tracked here.
The project follows [Semantic Versioning](https://semver.org) per the protocol's
Section 12.1, and the versions in this file map 1:1 to git tags on `main`.

## [0.3.0-sse-alpha.2] — 2026-04-26

### Added

- `OwnershipStatement` component — Section 4.2 ownership promise rendered
  visibly inside every profile card (portable, revocable, holder-controlled).
- `ConstraintTierSwitcher` — judge-friendly Smartphone / SMS / USSD tab that
  collapses the same profile across the three delivery tiers in one click.
- Recursive USSD tree navigator — `UssdSimulator` now walks
  `human_layer.ussd_tree` node-by-node with a back stack and per-option
  numeric buttons (parser-driven, no hard-coded menu).
- ISCO/ESCO taxonomy chips and confidence-tier-aware skill bars
  (`emerging` / `developing` / `established` / `expert`).
- `<details>` evidence-chain reveal that exposes the full VSS list with
  evidence types and weights.
- Vitest + jsdom + React Testing Library test harness.
  - 8 test files / 26 cases covering input, locale swap, profile rendering,
    SMS and USSD primitives, constraint-tier swap, api fallback, and an
    end-to-end App-level flow.
- `frontend/src/test/{setup.ts,fixtures.ts}` shared test plumbing.

### Changed

- **Breaking (internal):** API client reconciled with backend
  `module/m1-sse` (Claude 1 LOG-0001). Endpoint moved from `/parse` to
  `/api/v1/parse`; request shape `{raw_input, country}` →
  `{text, country_code, context_tag}`; response shape flattened `profile`
  → nested `{user, skills, vss_list, human_layer, meta}`. Full canonical
  types live in `frontend/src/lib/types.ts`.
- `docs/api-contract.md` rewritten as a thin reconciliation document that
  points at backend Pydantic models and JSON Schemas as the source of truth.
- `mock.ts` rebuilt with the canonical Amara test vector from the backend
  parser tests + an Armenia mock for AM (until the backend ships an AM
  country_profile).
- Locale switcher now annotates `backendSupported` per locale; AM goes
  through the offline fallback transparently and the SPA shows an "Offline
  fallback" badge.

### Backward compatibility

- The SPA-as-product is unreleased to end users — this is the first
  integration with a real backend, so no production consumers exist.
- The contract change is breaking against the inferred alpha.1 contract
  but has no consumers, since no backend implemented that contract.
  Claude 1's canonical contract is the new baseline.

---

## [0.3.0-sse-alpha.1] — 2026-04-26

### Added

- **`/frontend`** — single-page React + Vite + TypeScript + Tailwind app
  for the Skills Signal Engine demo (Module M1).
  - One-prompt input panel that accepts chaotic personal stories in any
    language (Ghana and Armenia samples included).
  - `ProfileCard` rendering the Human Layer per v0.2 Section 4.2: pseudonym,
    languages, parser-detected skills with evidence, wage and growth signal
    bars with rationale, and a network-entry channel + offline SVG map.
  - QR simulation (`qrcode.react`) for the share-link / verifiable claim
    handoff envisioned for v0.4.
  - Constraint-Layer demos: `SmsPreview` (160-char fallback, segment
    counter) and `UssdSimulator` (interactive feature-phone shell rendering
    the parser-supplied menu).
  - Locale switcher that reloads the SPA against a different
    `country_profile` (`GH` ↔ `AM`).
  - Offline-first behaviour: 8-second `/parse` timeout, transparent
    fallback to a bundled mock parser, `localStorage` cache of the last
    input / locale / result.
- **`docs/api-contract.md`** — frozen `/parse` contract for backend (Claude 1).
- **`PROJECT_LOG.md`** — initialized with the M1-SSE-UI entry.

### Changed

- Repository structure: introduced `frontend/`, `docs/`, top-level
  `CHANGELOG.md` and `PROJECT_LOG.md`.

### Backward compatibility

- This is the first feature release after the empty `Initial commit`. No
  consumers exist yet; the API contract in `docs/api-contract.md` becomes
  the baseline for any future change.
