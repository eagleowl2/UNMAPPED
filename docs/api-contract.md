# UNMAPPED `/parse` API Contract

**Owner:** Claude 1 (backend) ⇄ Claude 2 (frontend)
**Module:** M1 — Skills Signal Engine
**Version:** `v0.3-sse-alpha.1`
**Status:** Draft, frozen for the hackathon. Changes require a SemVer bump
(Section 12.1) + a `PROJECT_LOG.md` entry (Section 12.4).

This document is the **single source of truth** for how the SPA in `/frontend`
talks to the FastAPI backend. The TypeScript twin lives at
`frontend/src/lib/types.ts` — keep them in lock-step.

---

## 1. Endpoint

```
POST {API_URL}/parse
Content-Type: application/json
```

CORS must allow `http://localhost:5173` during development and the deployed
SPA origin in production.

## 2. Request

```ts
interface ParseRequest {
  raw_input: string;          // any language, any length up to ~8 KB
  country: 'GH' | 'AM';       // selected country profile
  language_hint?: string;     // optional ISO 639-1; backend may auto-detect
}
```

- `raw_input` MUST NOT be trimmed by the backend before parsing — preserve
  user's punctuation/casing for evidence spans.
- `country` drives currency, wage bands, USSD shortcode, network-entry
  channels, and SMS sender ID. Treat as authoritative.

## 3. Successful response (HTTP 200)

```ts
interface ParseResponse {
  ok: true;
  profile: ProfileCard;
  latency_ms: number;            // server-measured parse time
  country: 'GH' | 'AM';          // echo of input
  parser_version: string;        // e.g. "sse-0.3.0+abcd123"
}

interface ProfileCard {
  profile_id: string;            // opaque, stable, encoded in QR
  display_name: string;          // safe-to-show (may equal pseudonym)
  pseudonym: string;             // first-name display, e.g. "Amara"
  age?: number;
  location: string;              // human-readable, e.g. "Accra, Greater Accra"
  languages: string[];           // human-readable language names
  skills: Skill[];               // 1-8 entries, sorted by confidence desc
  wage_signal: Signal;           // 0-100, with currency-formatted display_value
  growth_signal: Signal;         // 0-100, no currency
  network_entry: NetworkEntryPoint;
  sms_summary: string;           // ≤ 320 chars, target ≤ 160 (1 SMS segment)
  ussd_menu: string[];           // 4-8 lines, ≤ 40 chars per line
}

interface Skill { name: string; confidence: number; evidence?: string }
interface Signal { score: number; rationale: string; display_value?: string }
interface NetworkEntryPoint { channel: string; lat: number; lng: number; label: string }
```

### Field constraints

| Field                       | Constraint                                                |
| --------------------------- | --------------------------------------------------------- |
| `score` (both signals)      | integer 0–100, clamped server-side                        |
| `confidence`                | float 0–1, two decimals enough                            |
| `sms_summary`               | UTF-8; backend SHOULD prefer GSM-7 chars when feasible    |
| `ussd_menu[i]`              | ≤ 40 visible chars to fit 2G handsets                     |
| `lat` / `lng`               | WGS84; approximate location is fine                       |
| `parser_version`            | semver + optional `+sha` build metadata                    |

## 4. Error response

Any non-200 OR a parser-level error MUST conform to:

```ts
interface ParseError {
  ok: false;
  error: string;                 // human-readable, EN ok for hackathon
  code?: 'EMPTY_INPUT' | 'RATE_LIMIT' | 'PARSER_FAILURE' | 'UNSUPPORTED_LOCALE';
}
```

The frontend treats **any** non-200 as "fall back to local mock" so judges
never see a broken card. Backend should still return useful messages for the
PROJECT_LOG.

## 5. Timeouts & retries

- Frontend timeout: **8 s** (AbortController). On timeout the SPA renders a
  mock card and shows an "Offline fallback" badge.
- No retries on the client. Backend SHOULD implement idempotent parsing so a
  client retry is safe.

## 6. Versioning

- This contract is `v0.3.0` per Section 12.1.
- Additive changes (new optional fields) → bump **patch**, no PROJECT_LOG
  required beyond the standard module entry.
- Renaming or removing fields → **minor** bump, mandatory PROJECT_LOG entry,
  and the frontend `types.ts` MUST be updated in the same PR.
- Breaking the request shape → **major** bump.

## 7. Reference samples

Two canonical inputs/outputs are bundled in `frontend/src/lib/mock.ts`. Use
them as fixtures for backend tests so both sides agree on shape and tone.
