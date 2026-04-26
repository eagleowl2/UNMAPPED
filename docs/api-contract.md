# UNMAPPED `/parse` API Contract — v0.3.1

**Status:** Current. Matches `app/models/schemas.py` (backend) and
`frontend/src/lib/types.ts` (frontend) exactly.

> Any contract change requires:
> 1. SemVer bump in both `app/main.py` and `frontend/package.json`
> 2. Matching schema update on both sides of the wire
> 3. A `PROJECT_LOG.md` entry on the affected branch

---

## 1. Endpoint

```
POST http://localhost:8000/parse
Content-Type: application/json
```

CORS allow-list (default): `localhost:3000`, `localhost:5173`, `localhost:8080`,
`frontend:5173` (docker-internal). Override via `CORS_ORIGINS` env var.

Legacy alias `POST /api/v1/parse` is still mounted but SPA uses `/parse`.

---

## 2. Request

```typescript
interface ParseRequest {
  raw_input: string;          // 3–8000 chars, any language, any encoding
  country: 'GH' | 'AM';      // Country profile (ISO 3166-1 alpha-2)
  language_hint?: string;     // Optional ISO 639-1 hint; backend auto-detects
}
```

**Supported locales:**

| `country` | Profile | Languages | Zero-credential default |
|-----------|---------|-----------|------------------------|
| `GH` | Ghana urban-informal | English, Twi (ak-GH), Ga, Ewe, Hausa | `true` |
| `AM` | Armenia urban-informal | Armenian (hy-AM), Russian, English | `false` |

---

## 3. Response — success (HTTP 200, `ok: true`)

```typescript
interface ParseResponse {
  ok: true;
  profile: ProfileCard;
  latency_ms: number;           // Server-side parse time in milliseconds
  country: 'GH' | 'AM';        // Echo of requested country
  parser_version: string;       // e.g. "sse-0.3.1"
}

interface ProfileCard {
  profile_id: string;           // Deterministic: "prf-" + first 12 hex of SHA-256(input)
  display_name: string;         // "Amara A." — first name + last initial (privacy)
  pseudonym: string;            // First name only — "Amara"
  age?: number;                 // Extracted from text if present; omitted otherwise
  location: string;             // Human string: "Accra, Greater Accra"
  languages: string[];          // Human-readable: ["English", "Twi", "Ga"]
  skills: Skill[];              // Max 8, sorted descending by confidence
  wage_signal: Signal;
  growth_signal: Signal;
  network_entry: NetworkEntryPoint;
  sms_summary: string;          // ≤ 160 chars (1 SMS segment)
  ussd_menu: string[];          // 4–8 lines, each ≤ 40 chars
}

interface Skill {
  name: string;                 // Canonical label: "Mobile phone repair technician"
  confidence: number;           // 0.0–1.0 (Bayesian Beta posterior mean)
  evidence?: string;            // Short excerpt from raw_input that triggered this skill
}

interface Signal {
  score: number;                // 0–100 integer
  rationale: string;            // One-sentence human explanation
  display_value?: string;       // Formatted value: "GHS 38 / day" or "AMD 4,500 / hr"
}

interface NetworkEntryPoint {
  channel: string;              // E.g. "MTN MoMo SME registry via NBSSI"
  lat: number;                  // WGS84 latitude
  lng: number;                  // WGS84 longitude
  label: string;                // Short map pin label: "Accra Central"
}
```

---

## 4. Response — error (HTTP 200, `ok: false`)

The backend always returns HTTP 200. If parsing fails, the SPA reads `ok: false`
and falls back to its bundled mock automatically.

```typescript
interface ParseError {
  ok: false;
  error: string;                // Human-readable description
  code?: string;                // Machine code: "UNSUPPORTED_LOCALE" | "PARSER_FAILURE"
}
```

---

## 5. Timeouts & retries

- **Frontend timeout:** 8 s (`AbortController`). On abort → mock fallback.
- **No client-side retries.** Parser is stateless and idempotent.
- **Backend workers:** 1 (MVP). Scale via `--workers N` in production.

---

## 6. Parser pipeline (v0.3.1)

The backend `EvidenceParser` runs four extraction stages in order:

1. **Locale alias registry** — exact/NFC match against `skill_alias_registry` in
   the country profile. Covers Twi (`kayayo`, `dwadini`, `trotro`), Ga (`chop bar`),
   Armenian script (`ուսուցիչ`, `թարգmanchich`), Russian inflected forms.
2. **English + Armenian regex** — 35 English patterns + 4 Armenian Unicode patterns.
3. **Multilingual embedder** — semantic paraphrase matching via
   `intfloat/multilingual-e5-small` (default, ~118 MB CPU) against canonical labels.
   Selectable via `UNMAPPED_EMBED_MODEL` env var. Threshold: `0.74` cosine similarity.
4. **Noun-phrase taxonomy crosswalk** — spaCy `xx_ent_wiki_sm` noun chunks →
   NetworkX ISCO-08/ESCO taxonomy graph.

---

## 7. Confidence scoring

Bayesian Beta conjugate update (no MCMC for MVP):

| Tier | Score range | Description |
|------|-------------|-------------|
| `emerging` | 0.0–0.40 | Single weak signal |
| `developing` | 0.40–0.60 | Self-reported, limited corroboration |
| `established` | 0.60–0.80 | Multiple consistent signals |
| `expert` | 0.80–1.0 | High-weight alias match + experience signals |

---

## 8. Reference fixtures

`frontend/src/lib/mock.ts` exports `GH_SAMPLE` (Amara, GH) and `AM_SAMPLE`
(Ani, AM) as canonical golden fixtures. Both sides of the wire should produce
output structurally matching these fixtures.

---

## 9. Health endpoint

```
GET /health → { status: "ok", version: "0.3.1", protocol: "UNMAPPED v0.2" }
```

---

## 10. Changelog

| Version | Change |
|---------|--------|
| v0.3.1 | `skill_alias_registry` pipeline; E5-small embedder; 10 new ISCO codes |
| v0.3.0 | Full ProfileCard contract; Armenia locale; wage/growth/network signals |
| v0.3-alpha.1 | Initial SSE contract (`text`/`country_code` — **deprecated**) |
