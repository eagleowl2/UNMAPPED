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

export type AutomationRiskTier = 'low' | 'medium' | 'high';
export type AutomationTrajectory = 'growing' | 'stable' | 'declining';

/**
 * Module 2 — AI Readiness & Displacement Risk Lens. LMIC-calibrated.
 * Optional on the wire so older SPA versions render unchanged when the
 * backend doesn't ship M2.
 */
export interface AutomationRisk {
  /** LMIC-adjusted probability the top occupation is automated [0..1]. */
  automation_probability: number;
  /** Raw Frey-Osborne probability before LMIC calibration [0..1]. */
  raw_probability: number;
  risk_tier: AutomationRiskTier;
  trajectory_2035: AutomationTrajectory;
  durable_skills: string[];
  adjacent_skills: string[];
  rationale: string;
  sources: string[];
}

/** Data360 / ILOSTAT NEET rate — Signal 4 from the brief's signal hierarchy. */
export interface NeetContext {
  /** % of youth (15–24) not in employment, education, or training. */
  neet_pct: number;
  narrative: string;
  source: string;
  year: number;
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
  /** Module 2 — present when the backend ships v0.3.2+ automation risk. */
  automation_risk?: AutomationRisk;
  /** Module 3 (partial) — NEET rate context for the user's country. */
  neet_context?: NeetContext;
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
  /** Dev-mode tail of the Python traceback. Present iff
   * `UNMAPPED_VERBOSE_ERRORS != "0"` on the backend. */
  traceback_tail?: string[];
}

export type ParseResult = ParseResponse | ParseError;
