# UNMAPPED `/parse` API Contract — reconciled v0.3-sse-alpha.2

**Status:** Reconciled with backend `module/m1-sse` (Claude 1, LOG-0001).
**Source of truth:**

- Backend Pydantic models: `app/models/schemas.py` (in `module/m1-sse`)
- JSON Schemas: `schemas/verifiable_skill_signal.json`, `schemas/human_layer.json`
- Frontend TS twin: `frontend/src/lib/types.ts` (this branch)

> Any contract change requires a SemVer bump (Section 12.1) + matching update
> on both sides of the wire + a `PROJECT_LOG.md` entry on each branch.

---

## 1. Endpoint

```
POST {API_URL}/api/v1/parse
Content-Type: application/json
```

CORS: backend ships allow-list `localhost:3000, localhost:5173, localhost:8080`
by default (`CORS_ORIGINS` env var override). The SPA runs on 5173.

## 2. Request

```ts
interface ParseRequest {
  text: string;            // 3..5000 chars, any language
  country_code: 'GH' | 'AM';   // ISO 3166-1 alpha-2
  context_tag: 'urban_informal' | string;
}
```

Backend currently ships `GH` × `urban_informal`. Other locales 404 with a
FileNotFoundError → `HTTPException(404)`; the SPA transparently falls back
to its bundled mock so the demo still works.

## 3. Response (HTTP 200)

```ts
interface ParseResponse {
  ok: true;
  user: UserEntity;                    // USER primitive
  skills: SkillEntity[];               // SKILL primitives, sorted by confidence
  vss_list: VerifiableSkillSignal[];   // one per skill, with evidence chain + Bayesian confidence + ISCO/ESCO crosswalk
  human_layer: HumanLayer;             // profile_card + sms_summary + ussd_tree
  meta: {
    country_code?: string;
    context_tag?: string;
    skills_detected?: number;
    processing_time_ms?: number;
    parser_version?: string;
  };
}
```

The full nested types are in
[`frontend/src/lib/types.ts`](../frontend/src/lib/types.ts) — kept byte-faithful
to the JSON Schemas in `schemas/`.

### Key conventions the SPA depends on

| Convention                                       | Why the SPA cares                                   |
| ------------------------------------------------ | --------------------------------------------------- |
| `confidence.tier ∈ {emerging, developing, established, expert}` | Drives `SignalBar` colour + chip label.    |
| `confidence.score ∈ [0, 1]`                       | Rendered as a percentage.                           |
| `taxonomy_crosswalk.primary.{framework, code}`   | Rendered as `ISCO-08:7421`-style chip on each skill. |
| `profile_card.zero_credential_badge: boolean`    | Triggers the "Zero-credential verified" pill.       |
| `sms_summary.text` ≤ 160 chars                    | Segment counter assumes ≤ 160 = 1 segment.          |
| `ussd_tree.root` recursive `options[].next`      | Rendered by the recursive `UssdSimulator` navigator. |

### What the SPA explicitly does NOT do

- Inject `profile_card.rendered_html`. The backend may include this convenience
  field but the SPA renders structured fields itself to keep the XSS surface
  zero. Don't rely on it for browser delivery from this client.

## 4. Error response

Any non-200 OR `ok: false` → SPA transparently renders the bundled mock and
flags `source = 'mock-fallback'` + `fallbackReason`. Backend errors should
still carry useful detail for the PROJECT_LOG forensics.

## 5. Timeouts & retries

- Frontend timeout: **8 s** (`AbortController`).
- No client-side retries — backend SHOULD keep parsing idempotent.

## 6. Reference fixtures

`frontend/src/lib/mock.ts` exports `GH_AMARA` and `AM_ANI` ParseResponse
fixtures. Use them as golden tests so both sides agree on shape and tone.
