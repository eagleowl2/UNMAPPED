/**
 * Canonical types for UNMAPPED Protocol v0.3-sse-alpha.2.
 *
 * Source of truth: backend module/m1-sse — `app/models/schemas.py` and the JSON
 * Schemas under `/schemas`. This file MUST stay in lock-step with that branch;
 * any contract change requires a SemVer bump + matching update on both sides
 * per Section 12.1.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Request
// ─────────────────────────────────────────────────────────────────────────────

export type CountryCode = 'GH' | 'AM';

export type ContextTag = 'urban_informal' | 'rural_subsistence' | string;

export interface ParseRequest {
  /** Any unstructured personal/professional text. min 3, max 5000 chars. */
  text: string;
  /** ISO 3166-1 alpha-2; backend currently ships GH, AM falls back to mock. */
  country_code: CountryCode;
  /** Context tag matching a loaded country profile. */
  context_tag: ContextTag;
}

// ─────────────────────────────────────────────────────────────────────────────
// Response — VSS (Verifiable Skill Signal)
// ─────────────────────────────────────────────────────────────────────────────

export type ConfidenceTier = 'emerging' | 'developing' | 'established' | 'expert';

export type SkillCategory =
  | 'technical'
  | 'digital'
  | 'trade'
  | 'agricultural'
  | 'care'
  | 'creative'
  | 'managerial'
  | 'language'
  | 'financial'
  | 'other';

export interface UserEntity {
  user_id: string;
  display_name?: string;
  location?: {
    country_code?: string;
    city?: string;
    context_tag?: string;
  };
  languages?: string[];
  source_text_hash?: string;
  zero_credential?: boolean;
}

export interface SkillEntity {
  skill_id: string;
  label: string;
  label_local?: string;
  category: SkillCategory;
  subcategory?: string;
  source_phrases: string[];
  experience_signals?: string[];
  /** Surfaced flat from VSS for convenience. */
  confidence_score?: number;
}

export interface TaxonomyEntry {
  framework: string;
  code: string;
  label: string;
  match_score?: number;
}

export interface VerifiableSkillSignal {
  vss_id: string;
  schema_version: string;
  user: UserEntity;
  skill: SkillEntity;
  evidence_chain: Array<{
    evidence_type:
      | 'self_report'
      | 'peer_endorsement'
      | 'transaction_record'
      | 'digital_footprint'
      | 'formal_credential'
      | 'community_attestation';
    raw_signal: string;
    normalized_signal?: string;
    weight: number;
  }>;
  confidence: {
    score: number; // 0..1
    lower_95?: number;
    upper_95?: number;
    alpha?: number;
    beta?: number;
    method: 'bayesian_beta' | 'rule_based' | 'ml_classifier';
    tier: ConfidenceTier;
  };
  taxonomy_crosswalk: {
    primary: TaxonomyEntry;
    secondary?: TaxonomyEntry[];
  };
  country_code?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Response — Human Layer
// ─────────────────────────────────────────────────────────────────────────────

export interface SkillSummaryEntry {
  label: string;
  confidence_tier: ConfidenceTier;
  confidence_score: number; // 0..1
  taxonomy_code?: string;
  category?: string;
}

export interface ProfileCardData {
  display_name: string;
  headline: string;
  location: string;
  languages?: string[];
  skills_summary: SkillSummaryEntry[];
  zero_credential_badge?: boolean;
  top_skill?: string;
  bio_snippet?: string;
  /** Backend-rendered HTML — NOT injected by the SPA (XSS posture); the SPA
   *  renders structured fields itself. */
  rendered_html?: string;
}

export interface SmsSummaryData {
  text: string; // ≤ 160 chars
  char_count: number;
  language?: string;
}

export interface UssdNode {
  id: string;
  text: string; // ≤ 182 chars
  input_type?: 'none' | 'numeric' | 'text';
  is_terminal?: boolean;
  options?: Array<{
    key: string;
    label: string;
    next: UssdNode;
  }>;
}

export interface UssdTree {
  root: UssdNode;
  session_timeout_sec?: number;
}

export interface HumanLayer {
  hl_id: string;
  schema_version: string;
  created_at: string;
  user_id: string;
  vss_ids?: string[];
  profile_card: ProfileCardData;
  sms_summary: SmsSummaryData;
  ussd_tree: UssdTree;
}

// ─────────────────────────────────────────────────────────────────────────────
// Response envelope
// ─────────────────────────────────────────────────────────────────────────────

export interface ParseResponse {
  ok: true;
  user: UserEntity;
  skills: SkillEntity[];
  vss_list: VerifiableSkillSignal[];
  human_layer: HumanLayer;
  meta: {
    country_code?: string;
    context_tag?: string;
    skills_detected?: number;
    processing_time_ms?: number;
    parser_version?: string;
  };
}

export interface ParseError {
  ok: false;
  error: string;
  detail?: string;
}

export type ParseResult = ParseResponse | ParseError;
