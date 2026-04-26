# UNMAPPED Protocol — Skills Signal Engine

> Make the chaotic, multilingual reality of LMIC livelihoods legible to the formal economy — without forcing anyone to flatten themselves first.

UNMAPPED is a **full-stack skills recognition system** for Low and Middle-Income Countries. It transforms free-form, multilingual narratives about livelihoods into portable **Skills Signal Profiles** (SSP) that bridge informal economies and formal institutions.

**Current Release:** `v0.4.0` — Module 2 (Dynamic Job-Match Signal) + Module 1 (Skills Signal Engine UI) ✓ 178 tests passing

---

## 📋 Table of Contents

- [What is UNMAPPED?](#what-is-unmapped)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
  - [Backend (Python / FastAPI)](#backend-python--fastapi)
  - [Frontend (React / TypeScript)](#frontend-react--typescript)
- [Supported Countries & Languages](#supported-countries--languages)
- [API Contract](#api-contract)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Key Features](#key-features)

---

## What is UNMAPPED?

UNMAPPED solves a critical problem: **2+ billion informal workers lack formal proof of their skills.**

### The Problem
People in informal economies (street vendors, mobile-money agents, tailors, porters) have real skills but:
- No formal credentials
- No standardized way to signal competence
- No pathway to formal-sector credit, contracts, or advancement

### The UNMAPPED Solution
1. **Human Layer** — Accept messy, free-form stories in any language (English, Twi, Ga, Armenian, Russian, etc.)
2. **Constraint Layer** — Deliver results via low-bandwidth channels (SMS, USSD *404#, QR-linked profiles)
3. **Localization Layer** — Country-specific skill taxonomies, wage bands, and formal-economy entry points (NBSSI, e-gov.am, Idram, MTN MoMo)

The system extracts skills using a **4-stage multilingual pipeline**, scores them using Bayesian inference, and synthesizes **three econometric signals**:
- **Wage signal** — ISCO-08 median wage per skill cluster (GHS/AMD)
- **Growth signal** — Estimated earning trajectory based on ambition, digital skills, and experience
- **Job-match signal** — Ranked opportunities matching the person's skill profile (v0.4.0 new)

---

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose v2** (recommended)
- *or* **Python 3.11+** + **Node 20+** (bare-metal dev)

### Option 1: Docker (Recommended)

```bash
# Clone and run the stack
git clone https://github.com/eagleowl2/UNMAPPED.git
cd UNMAPPED
make dev

# Access the app
# Frontend SPA:   http://localhost:5173
# FastAPI docs:   http://localhost:8000/docs
# Health check:   http://localhost:8000/health
```

**First-time build:** ~3–5 minutes (downloads torch CPU, spaCy model, E5-small embedder, npm deps)  
**Subsequent builds:** <30 seconds

### Option 2: Bare-Metal Development

#### Backend Setup
```bash
make install-backend    # Creates .venv + installs Python deps + spaCy model
make run-backend        # Starts FastAPI on http://localhost:8000
```

#### Frontend Setup (in a new terminal)
```bash
make install-frontend
make run-frontend       # Starts Vite dev server on http://localhost:5173
```

### Option 3: Pure Frontend Demo (No Backend)

The SPA includes a **bundled offline parser** that works even without a backend:

```bash
cd frontend
npm install
npm run dev
# Set VITE_DEMO_MODE=true in .env to use mock data
```

---

## 🏗 Architecture

### High-Level Data Flow

```
User Input (any language)
    ↓
[Frontend SPA] → HTTP POST /parse → [Backend Parser]
    ↓
  4-Stage Pipeline:
    1. Locale Alias Registry (exact match: Twi, Ga, Armenian, Russian)
    2. English + Armenian Regex (35 patterns)
    3. Multilingual Embedder (E5-small semantic matching)
    4. Noun-Phrase Taxonomy Crosswalk (spaCy + ISCO-08/ESCO)
    ↓
  Signals Engine:
    - Compute Wage Signal (ISCO code → country-specific wage band)
    - Compute Growth Signal (ambition + digital skills + experience)
    - Compute Job-Match Signal (VSS + taxonomy code → ranked opportunities)
    ↓
ProfileCard JSON + SMS Summary + USSD Menu
    ↓
[Frontend SPA] renders profile, QR code, SMS/USSD previews
```

---

## 🔧 Backend (Python / FastAPI)

**Location:** `app/` directory

### Architecture

```
app/
├── main.py                    ← FastAPI app setup, CORS, route mounting
├── api/
│   └── routes.py              ← POST /parse (primary), POST /api/v1/parse (legacy)
├── core/
│   ├── parser.py              ← EvidenceParser (4-stage pipeline, orchestration)
│   ├── signals.py             ← Wage/Growth/Job-Match signals, network entries
│   ├── multilingual.py        ← AliasMatcher, MultilingualEmbedder (E5-small, BGE-M3)
│   ├── bayesian.py            ← Bayesian Beta conjugate update (confidence scoring)
│   ├── taxonomy.py            ← ISCO-08 / ESCO graph, noun-phrase matching
│   └── country_profile.py     ← Profile loader, skill_alias_registry, wage bands
├── models/
│   └── schemas.py             ← Pydantic models (ParseRequest, ProfileCard, Signal, etc.)
└── __init__.py
```

### Key Modules

#### **parser.py** — Extraction Pipeline
- **`EvidenceParser`** class orchestrates 4 stages:
  1. **Locale alias registry** — exact, Unicode-NFC, case-insensitive match against country-specific skill aliases
  2. **English + Armenian regex** — 35+ predefined patterns
  3. **Multilingual embedder** — semantic paraphrase lookup via E5-small (or BGE-M3 w/ GPU)
  4. **Noun-phrase taxonomy crosswalk** — spaCy entity extraction → ISCO-08 codes
- **`parse_for_profile()`** — main entry point; returns `ProfileCard`

#### **signals.py** — Econometric Signals
- **`compute_wage_signal()`** — per-ISCO wage bands → score (0–100) + currency display (GHS/AMD)
- **`compute_growth_signal()`** — ambition keywords, digital/financial skills, experience → score
- **`compute_job_match()`** *(v0.4.0)* — BONA-style opportunity ranking; top-5 matches per person
- **`get_network_entry()`** — skill taxonomy code → formal-economy channel (NBSSI, e-gov.am, MoMo, etc.) + WGS84 coords

#### **multilingual.py** — Language Support
- **`AliasMatcher`** — Unicode-NFC, case-insensitive regex lookup; longest-wins priority
- **`MultilingualEmbedder`** — lazy-loaded E5-small (~118 MB, CPU-only) or BGE-M3 (GPU)
- Supports: English, Armenian, Twi, Ga, Russian, and 100+ more languages

#### **bayesian.py** — Confidence Scoring
- Beta conjugate prior/posterior update (no MCMC for MVP)
- Maps evidence weight → posterior mean confidence (0–1)
- Confidence tiers: `emerging` (0–0.4), `developing` (0.4–0.6), `established` (0.6–0.8), `expert` (0.8–1.0)

#### **country_profile.py** — Locale Configuration
- Loads JSON profiles from `config/` (Ghana, Armenia)
- Exposes:
  - `skill_alias_registry` — language-specific aliases
  - `wage_bands` — ISCO code → median wage + currency
  - `network_entries` — entry points with coordinates
  - `opportunity_catalog` *(v0.4.0)* — ranked jobs/services/programs

### Configuration

```
config/
├── ghana_urban_informal.json   ← GH locale (GHS currency, Twi/Ga/English, Accra)
└── armenia_urban_informal.json ← AM locale (AMD currency, Armenian/Russian, Yerevan/Gyumri)
```

Each profile includes:
- **wage_bands** — ISCO-08 codes mapped to median wages
- **skill_alias_registry** — multilingual aliases → canonical ISCO codes
- **network_entries** — formal-economy touchpoints (NGOs, gov, fintech)
- **opportunity_catalog** *(v0.4.0)* — jobs/programs with ISCO codes, credential requirements

### Example Request/Response

**Request:**
```json
{
  "raw_input": "I repair phones and do some computer fix. I know English and Twi. I've been doing this for 3 years, hoping to get into a bigger business.",
  "country": "GH",
  "language_hint": "en"
}
```

**Response (HTTP 200):**
```json
{
  "ok": true,
  "profile": {
    "profile_id": "prf-a1b2c3d4e5f6",
    "display_name": "John D.",
    "pseudonym": "John",
    "age": null,
    "location": "Accra, Greater Accra",
    "languages": ["English", "Twi"],
    "skills": [
      {
        "name": "Mobile phone repair technician",
        "confidence": 0.87,
        "evidence": "repair phones and do some computer fix"
      },
      {
        "name": "Computer systems technician",
        "confidence": 0.62,
        "evidence": "computer fix"
      }
    ],
    "wage_signal": {
      "score": 72,
      "rationale": "ISCO 7231 median wage cluster for phone technicians in Accra.",
      "display_value": "GHS 38 / day"
    },
    "growth_signal": {
      "score": 68,
      "rationale": "3 years experience, digital skills, ambition to scale — strong trajectory.",
      "display_value": null
    },
    "job_match": {
      "score": 76,
      "rationale": "Strong match for NBSSI SME formalization track + MoMo payment networks.",
      "opportunities": [
        {
          "name": "NBSSI – Digital Skills & Formalization Track",
          "isco_code": "7231",
          "score": 0.89,
          "formalization_path": "business registration + tax ID"
        }
      ]
    },
    "network_entry": {
      "channel": "MTN MoMo SME registry via NBSSI",
      "lat": 5.5553,
      "lng": -0.1969,
      "label": "Accra Central"
    },
    "sms_summary": "John: mobile repair technician, 3yr exp, GHS 38/day → NBSSI formalization track + MoMo SME registry.",
    "ussd_menu": [
      "1. View full profile",
      "2. NBSSI contact +233-XXX-XXX",
      "3. Learn about USSD banking",
      "*. Back"
    ]
  },
  "latency_ms": 245,
  "country": "GH",
  "parser_version": "sse-0.4.0"
}
```

### Environment Variables

```bash
# Core
LOG_LEVEL=INFO                                    # DEBUG | INFO | WARNING | ERROR
CORS_ORIGINS=http://localhost:3000,...           # Comma-separated origins

# Embedder (multilingual NLP)
UNMAPPED_EMBED_MODEL=intfloat/multilingual-e5-small  # or BAAI/bge-m3 w/ GPU
# UNMAPPED_EMBED_DISABLE=1                        # Skip embedding stage (faster, less accurate)
# UNMAPPED_EMBED_THRESHOLD=0.74                   # Cosine similarity threshold (0–1)
# HF_HOME=/tmp/hf_cache                           # HuggingFace cache (optional)
```

---

## 💻 Frontend (React / TypeScript)

**Location:** `frontend/` directory

### Architecture

```
frontend/src/
├── App.tsx                        ← Main state machine (input ↔ result ↔ error)
├── main.tsx                       ← React entry point
├── index.css                      ← Global styles (Tailwind)
├── components/
│   ├── InputPanel.tsx             ← Textarea input, sample buttons, country selector
│   ├── ProfileCard.tsx            ← Main layout (Section 4.2): header, hero signals, body
│   ├── SignalBar.tsx              ← Wage/Growth/Job-Match bar charts (hero + inline variants)
│   ├── SkillList.tsx              ← Skill cards with confidence tiers + evidence
│   ├── NetworkEntryMap.tsx        ← Offline SVG map with pulsing entry pin
│   ├── JobMatchPanel.tsx          ← Job-match signal + ranked opportunities list
│   ├── QrSimulation.tsx           ← QR code to share profile (qrcode.react)
│   ├── SmsPreview.tsx             ← SMS summary in phone-bubble mockup (160 chars)
│   ├── UssdSimulator.tsx          ← Interactive *404# / *789# menu navigator
│   └── LocaleSwitcher.tsx         ← Ghana ↔ Armenia toggle
├── lib/
│   ├── api.ts                     ← fetch wrapper, 8s timeout, mock fallback
│   ├── types.ts                   ← TypeScript interfaces (mirrors backend schemas.py)
│   ├── mock.ts                    ← Bundled offline GH + AM fixtures
│   ├── locales.ts                 ← Ghana + Armenia config (samples, display names)
│   └── storage.ts                 ← localStorage cache (last input, locale, result)
├── __tests__/                     ← Vitest suites (25 tests)
└── test/fixtures.ts               ← Test utilities
```

### Key Components

#### **App.tsx** — State Machine
- Manages: `input`, `isLoading`, `result`, `error`, `selectedCountry`
- Calls `POST /parse` on submit
- Falls back to mock on network failure or timeout (8s)
- Renders: `InputPanel` → `ProfileCard` → SMS/USSD previews

#### **ProfileCard.tsx** — Main Layout (v0.2 Section 4.2)
**Header:**
- Profile ID, pseudonym, age, location, languages
- Parser latency + version badge

**Hero Row:**
- Two side-by-side gradient cards:
  1. **Wage Signal** (left) — GHS 38 / day
  2. **Growth Signal** (right) — Earning trajectory score

**Body (Two Columns):**
- **Left:** Languages, network entry map, ownership statement
- **Right:** Skills list (up to 8, sorted by confidence)

**Footer:**
- Constraint Layer switcher (Smartphone / SMS / USSD)

#### **SignalBar.tsx** — Econometric Signals
- **Hero variant** — large gradient background, big number, rationale text
- **Inline variant** — compact bar for secondary signals
- Displays: score (0–100), rationale, optional formatted value (GHS/AMD)

#### **JobMatchPanel.tsx** *(v0.4.0)*
- Displays job-match score + top 5 ranked opportunities
- Each card shows: job name, ISCO code, match score, formalization path
- Expandable for more details

#### **SmsPreview.tsx** — SMS Fallback
- Renders 160-char SMS summary in iPhone-style bubble
- Uses monospace font to show exact char count
- Fallback for low-bandwidth environments

#### **UssdSimulator.tsx** — USSD Menu
- Interactive USSD *404# / *789# feature-phone simulator
- Flat menu structure (no nested trees, per backend)
- Responsive to keyboard (number keys + Enter)
- Shows: options, selection, navigation

#### **NetworkEntryMap.tsx** — Offline SVG Map
- No map tiles, no external API calls
- SVG circle at entry pin location (e.g., Accra Central, 5.5553°N, 0.1969°W)
- Pulsing animation (disabled if `prefers-reduced-motion`)
- Fallback label if geolocation unknown

#### **LocaleSwitcher.tsx** — Country Selection
- Ghana (GH) ↔ Armenia (AM) toggle
- Updates selected country + localStorage
- Resets input when switched

### API Integration (lib/api.ts)

```typescript
export async function parseProfile(
  raw_input: string,
  country: 'GH' | 'AM',
  language_hint?: string
): Promise<ParseResponse> {
  // POST {VITE_API_URL}/parse with 8s AbortController timeout
  // Falls back to mockParse if timeout or network error
}
```

### Environment Variables

```bash
# Backend API URL for Vite dev-server proxy
VITE_API_URL=http://localhost:8000           # Set to backend URL

# When true, never call backend; always use mock
VITE_DEMO_MODE=false
```

### Accessibility & Performance

- **Mobile-first** — responsive from 320 px upward
- **Keyboard navigation** — all interactive elements reachable via Tab + Enter
- **Motion preferences** — respects `prefers-reduced-motion` (disables pulsing animation)
- **No images, no analytics** — initial payload < 5 KB gzipped
- **Bundled mock parser** — SPA works fully offline on captive-portal networks (e.g., conference WiFi)

### Build & Development

```bash
cd frontend

# Development
npm install
npm run dev              # Vite dev server w/ HMR on :5173

# Production
npm run build            # Type-check + bundle to dist/
npm run preview          # Preview build on :4173

# Testing
npm test                 # Vitest (25 tests, 8 suites)
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report

# Linting
npm run lint            # tsc --noEmit (strict mode)
```

---

## 🌍 Supported Countries & Languages

| Country | Code | Currency | Languages | Network Entries | Wage Bands |
|---------|------|----------|-----------|-----------------|-----------|
| **Ghana** | `GH` | GHS | English, Twi, Ga, Ewe, Hausa | Accra (MTN MoMo, NBSSI) | 30+ ISCO codes |
| **Armenia** | `AM` | AMD | Armenian, Russian, English | Yerevan, Gyumri (e-gov.am, Idram) | 25+ ISCO codes |

**Multilingual Support:**
- **Alias Registry** — Twi kayayo (porter), dwadini (trading), trotro (minibus); Ga chop bar; Armenian ուսուցիչ (teacher); Russian учитель
- **Embedder** — E5-small supports 100+ languages via semantic similarity
- **Auto-detection** — backend detects language; `language_hint` is optional

---

## 📡 API Contract

### Endpoint: `POST /parse`

**Request:**
```json
{
  "raw_input": "string (3–8000 chars, any language)",
  "country": "GH" | "AM",
  "language_hint": "en" | "ak" | "hy" | "ru" (optional)
}
```

**Response (Success, HTTP 200):**
```json
{
  "ok": true,
  "profile": { ... },  // Full ProfileCard
  "latency_ms": 245,
  "country": "GH",
  "parser_version": "sse-0.4.0"
}
```

**Response (Error, HTTP 200):**
```json
{
  "ok": false,
  "error": "UNSUPPORTED_LOCALE | PARSER_FAILURE",
  "code": "..."
}
```

**Frontend Behavior on Error:**
- Timeout (8s) → mock fallback
- `ok: false` response → mock fallback
- Network error → mock fallback

See [`docs/api-contract.md`](docs/api-contract.md) for full schema & examples.

---

## 🧪 Testing

### Backend (Python)

```bash
# All tests (178 passing)
make test              # Runs pytest with default settings

# With coverage
make test-cov          # pytest --cov=app --cov-report=term-missing

# Specific suites
make test-multilingual  # tests/test_multilingual.py (43 tests: Twi, Ga, Armenian, Russian)

# Test composition
tests/
├── test_api.py               (35 tests) — POST /parse contract, locale swap
├── test_parser.py            (46 tests) — canonical Amara (GH) + Ani (AM) vectors
├── test_multilingual.py      (43 tests) — Twi, Ga, Armenian, Russian alias detection
├── test_jobmatch.py          (29 tests) — v0.4.0 job-match scoring engine (NEW)
├── test_country_profile.py   (8 tests)  — profile loading, wage bands
├── test_taxonomy.py          (6 tests)  — ISCO-08 graph traversal
└── test_bayesian.py          (7 tests)  — confidence scoring
```

### Frontend (TypeScript)

```bash
npm test                 # Vitest (25 tests)
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report

# Test suites
src/__tests__/App.test.tsx                          — Main flow (Input → Result)
src/components/__tests__/ProfileCard.test.tsx       — Layout + hero signals
src/components/__tests__/SmsPreview.test.tsx        — 160-char constraint
src/components/__tests__/UssdSimulator.test.tsx     — Menu navigation
src/lib/__tests__/api.test.ts                       — Mock fallback + timeout
```

### Integration Tests

```bash
# Full-stack via Docker Compose
make dev
# SPA at http://localhost:5173 makes real HTTP calls to backend
# Verify: "Live parser" badge appears with real latency
```

---

## 📂 Project Structure

```
UNMAPPED/
├── app/                           ← Backend (FastAPI + Python)
│   ├── main.py                    ← App setup, route mounting
│   ├── api/routes.py              ← POST /parse endpoint
│   ├── core/
│   │   ├── parser.py              ← 4-stage extraction pipeline
│   │   ├── signals.py             ← Wage/Growth/Job-Match signals
│   │   ├── multilingual.py        ← E5-small embedder + alias matcher
│   │   ├── bayesian.py            ← Confidence scoring
│   │   ├── taxonomy.py            ← ISCO-08 graph
│   │   └── country_profile.py     ← Profile loader
│   ├── models/schemas.py          ← Pydantic models
│   └── __init__.py
├── config/                        ← Country profiles
│   ├── ghana_urban_informal.json
│   └── armenia_urban_informal.json
├── frontend/                      ← SPA (React + TypeScript)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/            ← React components
│   │   ├── lib/                   ← API client, types, mock data
│   │   └── __tests__/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile.dev
├── schemas/                       ← JSON schemas
│   └── country_profile.json
├── tests/                         ← Backend tests
│   ├── test_api.py
│   ├── test_parser.py
│   ├── test_multilingual.py
│   ├── test_jobmatch.py
│   ├── test_country_profile.py
│   ├── test_taxonomy.py
│   └── test_bayesian.py
├── docs/
│   └── api-contract.md            ← Full API specification
├── Dockerfile                     ← Backend image
├── docker-compose.yml             ← Full-stack compose
├── Makefile                       ← Development shortcuts
├── requirements.txt               ← Python dependencies
├── requirements-dev.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── .dockerignore
├── README.md                      ← This file
├── CHANGELOG.md
└── PROJECT_LOG.md                 ← Append-only development log
```

---

## ✨ Key Features

### Human Layer (Section 4.2)
- ✅ Accept **any free-form text** — street vendors, porters, traders, etc. describe themselves
- ✅ **Multilingual** — English, Twi, Ga, Armenian, Russian, and 100+ more via E5-small
- ✅ **Privacy-preserving** — display names ("John D."), not full names; profile ID is deterministic SHA-256 hash

### Signal Tier (Econometric)
- ✅ **Wage Signal** — ISCO-08 median wage per skill cluster (GHS 38/day, AMD 4,500/hr)
- ✅ **Growth Signal** — earning trajectory based on ambition + digital skills + experience
- ✅ **Job-Match Signal** *(v0.4.0)* — dynamic opportunity ranking (BONA-style VSS + taxonomy scoring)

### Constraint Layer (Section 4.3)
- ✅ **SMS Fallback** — 160-char profile summary (1 SMS segment)
- ✅ **USSD Menu** — interactive *404# / *789# for feature phones
- ✅ **QR Share Link** — share profile via QR code

### Localization Layer (Section 4.4)
- ✅ **Ghana (GH)** — NBSSI SME registry, MTN MoMo, Accra-centric entry points
- ✅ **Armenia (AM)** — e-gov.am, Idram digital banking, Yerevan/Gyumri
- ✅ **Extensible** — add new countries via `config/*.json` + skill aliases

### Technical Excellence
- ✅ **Multilingual Embeddings** — E5-small (118 MB CPU, no GPU needed)
- ✅ **Bayesian Confidence** — Beta conjugate priors (not hand-tuned heuristics)
- ✅ **Modular Signals** — wage, growth, job-match as composable primitives
- ✅ **Full-Stack Testing** — 178 backend tests + 25 frontend tests
- ✅ **Zero External Dependencies** — no map APIs, no analytics, no auth required
- ✅ **Offline Capable** — SPA works on captive-portal networks w/ bundled mock

---

## 🛠 Development Workflow

### 1. Local Setup (Docker)
```bash
make dev          # Launches both backend + frontend in containers
```

### 2. Local Setup (Bare-Metal)
```bash
# Terminal 1: Backend
make install-backend
make run-backend

# Terminal 2: Frontend
make install-frontend
make run-frontend
```

### 3. Making Changes

**Backend:**
- Edit files in `app/` or `config/`
- Tests auto-run if using `pytest-watch` or `make test`
- API changes require coordination with frontend (update `docs/api-contract.md` + `PROJECT_LOG.md`)

**Frontend:**
- Edit files in `frontend/src/`
- Vite dev server has HMR (hot reload)
- TypeScript strict mode enforced on build

### 4. Versioning & Branches

- **SemVer:** `major.minor.patch-module-alpha.N` (e.g., `v0.4.0`, `v0.3.1-sse-alpha.1`)
- **Branches:** Each module ships from `module/<id>-<slug>` (e.g., `module/m2`, `module/m1-sse`)
- **Logging:** Every major contribution appends to `PROJECT_LOG.md` (append-only)

### 5. PR & Review Process

1. Create branch from `dev`
2. Make changes + pass tests (`make test`, `npm test`)
3. Update `PROJECT_LOG.md` at the top with entry ID, version, and delta
4. Create PR against `dev`
5. Assign reviewers (backend/frontend owners)
6. Merge once all CI checks pass

---

## 📚 Documentation

- **[`docs/api-contract.md`](docs/api-contract.md)** — Full `/parse` endpoint specification
- **[`PROJECT_LOG.md`](PROJECT_LOG.md)** — Append-only development log (178 tests added in v0.4.0, etc.)
- **[`CHANGELOG.md`](CHANGELOG.md)** — User-facing release notes
- **[`LICENSE`](LICENSE)** — Apache 2.0

---

## 🤝 Contributing

This is a **World Bank hackathon submission**. The codebase is **open and collaborative**.

### Steps to Contribute

1. **Fork** or create a branch from `dev`
2. **Follow versioning** — SemVer + module-tagged releases
3. **Add tests** — both sides of the wire (backend + frontend)
4. **Document changes** — update `PROJECT_LOG.md` (append-only)
5. **Submit PR** against `dev`

### Code Style

- **Python:** Ruff linter (`make lint`)
- **TypeScript:** tsc strict mode + Prettier (`npm run lint`)
- **Commits:** Conventional Commits (feat, fix, docs, test, chore)

---

## 🚀 Production Deployment

### Backend Docker Image

```bash
# Build
docker build -t unmapped-backend:v0.4.0 .

# Run
docker run -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e CORS_ORIGINS=https://unmapped.example.com \
  -e UNMAPPED_EMBED_MODEL=BAAI/bge-m3 \
  unmapped-backend:v0.4.0
```

### Frontend

```bash
# Build SPA
cd frontend && npm run build  # → dist/

# Deploy dist/ to CDN or static host
# Set VITE_API_URL={production-backend-url} at build time
```

### Environment Scaling

- **Workers:** Default 1. Scale via `--workers N` (uvicorn)
- **Embedder:** CPU-only by default (E5-small). GPU: set `UNMAPPED_EMBED_MODEL=BAAI/bge-m3`
- **Cache:** Frontend localStorage (last input, locale, result)
- **Monitoring:** Health check at `GET /health`

---

## 🎯 Current Roadmap

### Completed
- ✅ **v0.3.0** — Frontend SPA + basic backend (Module M1 — SSE UI)
- ✅ **v0.3.1** — Multilingual embedder + Armenia locale + 43 new tests
- ✅ **v0.4.0** — Job-match signal + opportunity catalog + 29 new tests

### Planned
- [ ] **Module 3** — Credential verification (zero-knowledge proofs)
- [ ] **Module 4** — Credit integration (linkage to digital lenders)
- [ ] **City-level routing** — opportunity catalog by geography
- [ ] **More countries** — Ewe (ee-GH), Hausa (ha), Tigrinya (ti), etc.

---

## ❓ FAQ

**Q: Can I run UNMAPPED without an internet connection?**  
A: Yes! The SPA includes a bundled offline parser. Set `VITE_DEMO_MODE=true` in `.env` to use mock data entirely.

**Q: What ISCO codes are supported?**  
A: See `config/ghana_urban_informal.json` and `config/armenia_urban_informal.json`. Currently 30+ GH codes + 25+ AM codes. Easy to extend by adding new entries.

**Q: Is there a mobile app?**  
A: Not yet. The SPA is mobile-responsive (320 px+) and works on feature phones via USSD *404#.

**Q: How accurate is the multilingual parser?**  
A: Depends on language + input clarity. Twi aliases have 95%+ accuracy; Russian ~85%. Semantic embedder (E5-small) adds ~10–15% recall on paraphrases. See `tests/test_multilingual.py` for detailed metrics.

**Q: Can I add my own country?**  
A: Yes! Create a new JSON file in `config/` (copy `ghana_urban_informal.json` as template), register it in `app/core/country_profile.py`, and add tests.

---

## 📞 Support & Contact

- **Issues:** GitHub Issues on this repo
- **Discussion:** GitHub Discussions
- **Documentation:** See `docs/api-contract.md` for detailed API specs

---

## 📄 License

Apache License 2.0 — see [`LICENSE`](LICENSE) for details.

---

**Built with ❤️ for the 2+ billion informal workers without formal proof of their skills.**
