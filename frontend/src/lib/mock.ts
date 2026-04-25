import type { CountryCode, ParseResponse } from './types';

/**
 * Bundled offline parser used when:
 *   - VITE_DEMO_MODE=true (deliberate, e.g. flaky-wifi pitch)
 *   - the backend /api/v1/parse call fails (network / 5xx / timeout / unsupported locale)
 *
 * Shape mirrors Claude 1's actual ParseResponse exactly so the SPA renders
 * identically in live and fallback modes.
 */

const GH_AMARA: ParseResponse = {
  ok: true,
  user: {
    user_id: 'usr_8b1c4f2a-4a3b-4c5d-9e8f-1234567890ab',
    display_name: 'Amara',
    location: { country_code: 'GH', city: 'Accra', context_tag: 'urban_informal' },
    languages: ['ak-GH', 'en-GH', 'gaa'],
    zero_credential: true,
    source_text_hash: 'sha256:mock-amara',
  },
  skills: [
    {
      skill_id: 'skl_1',
      label: 'Phone Repair',
      category: 'technical',
      source_phrases: ['fix phones in Accra', 'been fixing phones for 3 years'],
      experience_signals: ['3 years', '20 customers a week'],
      confidence_score: 0.68,
    },
    {
      skill_id: 'skl_2',
      label: 'Software Development',
      category: 'digital',
      source_phrases: ['learned coding on YouTube'],
      experience_signals: ['self-taught'],
      confidence_score: 0.52,
    },
  ],
  vss_list: [
    {
      vss_id: 'vss_1',
      schema_version: 'v0.2',
      user: {
        user_id: 'usr_8b1c4f2a-4a3b-4c5d-9e8f-1234567890ab',
        zero_credential: true,
        source_text_hash: 'sha256:mock-amara',
      },
      skill: {
        skill_id: 'skl_1',
        label: 'Phone Repair',
        category: 'technical',
        source_phrases: ['fix phones in Accra'],
      },
      evidence_chain: [
        { evidence_type: 'self_report', raw_signal: 'I fix phones in Accra', weight: 0.6 },
        {
          evidence_type: 'transaction_record',
          raw_signal: '20 customers a week',
          normalized_signal: 'sustained-volume',
          weight: 0.85,
        },
      ],
      confidence: { score: 0.68, method: 'bayesian_beta', tier: 'established', alpha: 6.8, beta: 3.2 },
      taxonomy_crosswalk: {
        primary: { framework: 'ISCO-08', code: '7421', label: 'Electronics mechanics and servicers' },
        secondary: [
          { framework: 'ESCO', code: '7421.1', label: 'Mobile phone repair technician' },
        ],
      },
      country_code: 'GH',
    },
    {
      vss_id: 'vss_2',
      schema_version: 'v0.2',
      user: {
        user_id: 'usr_8b1c4f2a-4a3b-4c5d-9e8f-1234567890ab',
        zero_credential: true,
        source_text_hash: 'sha256:mock-amara',
      },
      skill: {
        skill_id: 'skl_2',
        label: 'Software Development',
        category: 'digital',
        source_phrases: ['learned coding on YouTube'],
      },
      evidence_chain: [
        { evidence_type: 'self_report', raw_signal: 'learned coding on YouTube', weight: 0.55 },
      ],
      confidence: { score: 0.52, method: 'bayesian_beta', tier: 'developing', alpha: 4.2, beta: 3.8 },
      taxonomy_crosswalk: {
        primary: { framework: 'ISCO-08', code: '2512', label: 'Software developers' },
      },
      country_code: 'GH',
    },
  ],
  human_layer: {
    hl_id: 'hl_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    schema_version: 'v0.2',
    created_at: '2026-04-26T10:00:00Z',
    user_id: 'usr_8b1c4f2a-4a3b-4c5d-9e8f-1234567890ab',
    vss_ids: ['vss_1', 'vss_2'],
    profile_card: {
      display_name: 'Amara',
      headline: 'Phone Repair & Software Development specialist | Accra',
      location: 'Accra, Ghana',
      languages: ['English', 'Twi', 'Ga'],
      zero_credential_badge: true,
      top_skill: 'Phone Repair',
      bio_snippet:
        'Self-taught technician serving ~20 customers a week from a stall in Accra. Trilingual (Twi/English/Ga) with active YouTube-led self-study in software.',
      skills_summary: [
        {
          label: 'Phone Repair',
          confidence_tier: 'established',
          confidence_score: 0.68,
          taxonomy_code: 'ISCO-08:7421',
          category: 'technical',
        },
        {
          label: 'Software Development',
          confidence_tier: 'developing',
          confidence_score: 0.52,
          taxonomy_code: 'ISCO-08:2512',
          category: 'digital',
        },
      ],
    },
    sms_summary: {
      text: 'UNMAPPED:Amara in Accra | Phone Repair 68% (established), Software Dev 52% (developing) | zero-credential verified',
      char_count: 119,
      language: 'en-GH',
    },
    ussd_tree: {
      session_timeout_sec: 180,
      root: {
        id: 'root',
        text: 'UNMAPPED *789#\n1. View profile\n2. Skills\n3. Share to MoMo\n0. Exit',
        input_type: 'numeric',
        options: [
          {
            key: '1',
            label: 'View profile',
            next: {
              id: 'profile',
              text: 'Amara, Accra (GH)\nLanguages: EN/TW/GA\nZero-credential ✓\n0. Back',
              input_type: 'numeric',
              is_terminal: true,
            },
          },
          {
            key: '2',
            label: 'Skills',
            next: {
              id: 'skills',
              text: 'Skills:\n1. Phone Repair (established 68%)\n2. Software Dev (developing 52%)\n0. Back',
              input_type: 'numeric',
              options: [
                {
                  key: '1',
                  label: 'Phone Repair detail',
                  next: {
                    id: 'phone',
                    text: 'Phone Repair · ISCO 7421\n3 yrs · 20 cust/wk\nTier: established\n0. Back',
                    is_terminal: true,
                  },
                },
                {
                  key: '2',
                  label: 'Software Dev detail',
                  next: {
                    id: 'sw',
                    text: 'Software Dev · ISCO 2512\nSelf-taught (YouTube)\nTier: developing\n0. Back',
                    is_terminal: true,
                  },
                },
              ],
            },
          },
          {
            key: '3',
            label: 'Share to MoMo',
            next: {
              id: 'momo',
              text: 'Profile shared to MTN MoMo SME onboarding.\nRef: AMA-7421-68\n0. Done',
              is_terminal: true,
            },
          },
        ],
      },
    },
  },
  meta: {
    country_code: 'GH',
    context_tag: 'urban_informal',
    skills_detected: 2,
    processing_time_ms: 240,
    parser_version: 'mock-0.3.0-alpha.2',
  },
};

const AM_ANI: ParseResponse = {
  ok: true,
  user: {
    user_id: 'usr_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    display_name: 'Ani',
    location: { country_code: 'AM', city: 'Gyumri', context_tag: 'urban_informal' },
    languages: ['hy-AM', 'ru', 'en'],
    zero_credential: true,
    source_text_hash: 'sha256:mock-ani',
  },
  skills: [
    {
      skill_id: 'skl_3',
      label: 'English Tutoring',
      category: 'language',
      source_phrases: ['Անգլերեն դասեր եմ տալիս տանը'],
      confidence_score: 0.74,
    },
    {
      skill_id: 'skl_4',
      label: 'Translation EN/RU/HY',
      category: 'language',
      source_phrases: ['թարգմանում փոքր ընկերությունների համար'],
      confidence_score: 0.62,
    },
  ],
  vss_list: [
    {
      vss_id: 'vss_3',
      schema_version: 'v0.2',
      user: { user_id: 'usr_a', source_text_hash: 'sha256:mock-ani', zero_credential: true },
      skill: {
        skill_id: 'skl_3',
        label: 'English Tutoring',
        category: 'language',
        source_phrases: ['home lessons'],
      },
      evidence_chain: [
        { evidence_type: 'self_report', raw_signal: 'home English lessons', weight: 0.7 },
        { evidence_type: 'transaction_record', raw_signal: 'recurring private clients', weight: 0.78 },
      ],
      confidence: { score: 0.74, method: 'bayesian_beta', tier: 'established' },
      taxonomy_crosswalk: {
        primary: { framework: 'ISCO-08', code: '2353', label: 'Other language teachers' },
      },
      country_code: 'AM',
    },
    {
      vss_id: 'vss_4',
      schema_version: 'v0.2',
      user: { user_id: 'usr_a', source_text_hash: 'sha256:mock-ani', zero_credential: true },
      skill: {
        skill_id: 'skl_4',
        label: 'Translation',
        category: 'language',
        source_phrases: ['weekly translation work'],
      },
      evidence_chain: [
        { evidence_type: 'self_report', raw_signal: 'translates for small companies weekly', weight: 0.7 },
      ],
      confidence: { score: 0.62, method: 'bayesian_beta', tier: 'developing' },
      taxonomy_crosswalk: {
        primary: { framework: 'ISCO-08', code: '2643', label: 'Translators, interpreters' },
      },
      country_code: 'AM',
    },
  ],
  human_layer: {
    hl_id: 'hl_bbbbbbbb-cccc-dddd-eeee-ffffffffffff',
    schema_version: 'v0.2',
    created_at: '2026-04-26T10:00:00Z',
    user_id: 'usr_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    vss_ids: ['vss_3', 'vss_4'],
    profile_card: {
      display_name: 'Ani',
      headline: 'English Tutor & Multilingual Translator | Gyumri',
      location: 'Gyumri, Armenia',
      languages: ['Armenian', 'Russian', 'English'],
      zero_credential_badge: true,
      top_skill: 'English Tutoring',
      bio_snippet:
        'Multilingual educator running home tutoring with weekly translation work for small businesses. Active Idram payer.',
      skills_summary: [
        {
          label: 'English Tutoring',
          confidence_tier: 'established',
          confidence_score: 0.74,
          taxonomy_code: 'ISCO-08:2353',
          category: 'language',
        },
        {
          label: 'Translation EN/RU/HY',
          confidence_tier: 'developing',
          confidence_score: 0.62,
          taxonomy_code: 'ISCO-08:2643',
          category: 'language',
        },
      ],
    },
    sms_summary: {
      text: 'UNMAPPED:Ani in Gyumri | English Tutor 74% (established), Translation 62% (developing) | Idram-active',
      char_count: 109,
      language: 'hy-AM',
    },
    ussd_tree: {
      session_timeout_sec: 180,
      root: {
        id: 'root',
        text: 'UNMAPPED *404#\n1. Իմ պրոֆիլը\n2. Հմտություններ\n3. Ուղարկել e-gov.am\n0. Ելք',
        input_type: 'numeric',
        options: [
          {
            key: '1',
            label: 'Profile',
            next: {
              id: 'p',
              text: 'Ani, Գյումրի (AM)\nЯзыки: HY/RU/EN\nZero-cred ✓\n0. Back',
              is_terminal: true,
            },
          },
          {
            key: '2',
            label: 'Skills',
            next: {
              id: 's',
              text: '1. English Tutor (74%)\n2. Translator (62%)\n0. Back',
              is_terminal: true,
            },
          },
          {
            key: '3',
            label: 'Share',
            next: {
              id: 'g',
              text: 'Ուղարկվեց e-gov.am\nРеф: ANI-2353-74\n0. Done',
              is_terminal: true,
            },
          },
        ],
      },
    },
  },
  meta: {
    country_code: 'AM',
    context_tag: 'urban_informal',
    skills_detected: 2,
    processing_time_ms: 220,
    parser_version: 'mock-0.3.0-alpha.2',
  },
};

export function mockParse(text: string, country: CountryCode): ParseResponse {
  const base = country === 'GH' ? GH_AMARA : AM_ANI;
  const echoed = text.trim().slice(0, 64);
  if (!echoed) return base;
  return {
    ...base,
    meta: {
      ...base.meta,
      processing_time_ms: 180 + Math.floor(Math.random() * 120),
    },
    human_layer: {
      ...base.human_layer,
      sms_summary: {
        ...base.human_layer.sms_summary,
        // Append a tiny echo so judges see the user's words reflected.
        text: clampSms(`${base.human_layer.sms_summary.text} | "${echoed}"`),
        char_count: clampSms(`${base.human_layer.sms_summary.text} | "${echoed}"`).length,
      },
    },
  };
}

function clampSms(s: string): string {
  return s.length > 160 ? `${s.slice(0, 159)}…` : s;
}
