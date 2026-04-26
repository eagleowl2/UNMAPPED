/**
 * Canonical types for UNMAPPED Protocol v0.3-sse-alpha.4.
 *
 * Source of truth: backend `module/m1-sse` — `app/models/schemas.py`.
 * Claude 1 (commit 33e13e4) hardened the contract to a flat ProfileCard
 * with explicit `wage_signal` + `growth_signal` (the "2 econometric signals"
 * the v0.2 spec requires). Armenia is now a first-class country.
 *
 * Endpoint: POST /parse  (the legacy /api/v1/parse alias is also kept).
 */

// ─────────────────────────────────────────────────────────────────────────────
// Request
// ─────────────────────────────────────────────────────────────────────────────

export type CountryCode = 'GH' | 'AM';

export interface ParseRequest {
  raw_input: string;
  country: CountryCode;
  language_hint?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Response sub-models
// ─────────────────────────────────────────────────────────────────────────────

export interface Skill {
  name: string;
  /** 0..1 — backend Bayesian posterior. */
  confidence: number;
  /** Optional evidence span pulled from the raw input. */
  evidence?: string;
}

/**
 * Signal — a 0..100 normalized econometric signal with a short rationale.
 * Wage and growth share this shape.
 */
export interface Signal {
  score: number;
  rationale: string;
  /** Currency-formatted wage, e.g. "GHS 38 / day". Wage signal only. */
  display_value?: string;
}

export interface NetworkEntryPoint {
  /** Where in the formal economy this profile most-naturally enters. */
  channel: string;
  /** WGS84 lat/lng for the map pin (best-effort, may be approximate). */
  lat: number;
  lng: number;
  /** Short label rendered next to the pin. */
  label: string;
}

export interface ProfileCard {
  profile_id: string;
  display_name: string;
  pseudonym: string;
  age?: number;
  location: string;
  languages: string[];
  skills: Skill[];
  wage_signal: Signal;
  growth_signal: Signal;
  network_entry: NetworkEntryPoint;
  /** ≤ 320 chars; backend targets ≤ 160 (one SMS segment). */
  sms_summary: string;
  /** 4..8 lines, ≤ 40 visible chars each. */
  ussd_menu: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Response envelope
// ─────────────────────────────────────────────────────────────────────────────

export interface ParseResponse {
  ok: true;
  profile: ProfileCard;
  /** Backend-measured parse time in ms. */
  latency_ms: number;
  country: CountryCode;
  parser_version: string;
}

export interface ParseError {
  ok: false;
  error: string;
  code?: string;
}

export type ParseResult = ParseResponse | ParseError;
