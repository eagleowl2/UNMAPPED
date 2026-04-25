/**
 * UNMAPPED Protocol — Skills Signal Engine response contract (v0.3-sse-alpha.1).
 *
 * Inferred from v0.2 Section 4.2 (Human Layer profile card). When the canonical
 * spec lands, fields here are the source of truth for both the backend (Claude 1)
 * and this SPA. Any change MUST bump SemVer + add a PROJECT_LOG entry.
 */

export type CountryCode = 'GH' | 'AM';

export interface ParseRequest {
  /** Free-form chaotic input from the user, any language. */
  raw_input: string;
  /** Locale / country profile to apply on the parser side. */
  country: CountryCode;
  /** Optional ISO 639-1 hint; backend may auto-detect when absent. */
  language_hint?: string;
}

/** A 0–100 normalized signal with a short human-readable rationale. */
export interface Signal {
  score: number;
  /** One-sentence explanation; renders below the bar. */
  rationale: string;
  /** Optional unit-specific value, e.g. "GHS 38/day", "AMD 4500/hr". */
  display_value?: string;
}

export interface NetworkEntryPoint {
  /** Where in the formal economy this profile most-naturally enters. */
  channel: string;
  /** Latitude/longitude for the map pin (best-effort, may be approximate). */
  lat: number;
  lng: number;
  /** Short label rendered next to the pin. */
  label: string;
}

export interface Skill {
  name: string;
  /** Confidence score 0–1 from the parser. */
  confidence: number;
  /** Optional evidence span pulled from the raw input. */
  evidence?: string;
}

export interface ProfileCard {
  /** Canonical display name; backend may default to a respectful placeholder. */
  display_name: string;
  /** Pseudonym shown in the corner of the card (e.g. "Amara"). */
  pseudonym: string;
  age?: number;
  location: string;
  languages: string[];
  skills: Skill[];
  wage_signal: Signal;
  growth_signal: Signal;
  network_entry: NetworkEntryPoint;
  /** Short summary suitable for SMS (≤ 140 chars). */
  sms_summary: string;
  /** USSD menu lines the user would see on a feature phone. */
  ussd_menu: string[];
  /** Opaque ID the backend assigns for sharing / QR encoding. */
  profile_id: string;
}

export interface ParseResponse {
  ok: true;
  profile: ProfileCard;
  /** Total parsing time in ms — surfaced in the UI for the wow factor. */
  latency_ms: number;
  /** Echo of country profile used. */
  country: CountryCode;
  /** Parser version, useful in PROJECT_LOG forensics. */
  parser_version: string;
}

export interface ParseError {
  ok: false;
  error: string;
  /** Optional machine-readable code (e.g. "RATE_LIMIT", "EMPTY_INPUT"). */
  code?: string;
}

export type ParseResult = ParseResponse | ParseError;
