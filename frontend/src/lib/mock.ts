import type { CountryCode, ParseResponse } from './types';

/**
 * Bundled offline parser used when:
 *   - VITE_DEMO_MODE=true (deliberate, e.g. flaky-wifi pitch)
 *   - the backend /parse call fails (network / 4xx / 5xx / timeout)
 *
 * Shape mirrors Claude 1's hardened ProfileCard contract (commit 33e13e4)
 * exactly, so the SPA renders identically in live and fallback modes.
 */

const GH_AMARA: ParseResponse = {
  ok: true,
  country: 'GH',
  parser_version: 'mock-0.3.0-alpha.4',
  latency_ms: 240,
  profile: {
    profile_id: 'gh-amara-001',
    display_name: 'Amara A.',
    pseudonym: 'Amara',
    age: 27,
    location: 'Accra, Greater Accra',
    languages: ['English', 'Twi', 'Ga'],
    skills: [
      { name: 'Phone Repair', confidence: 0.68, evidence: 'fix phones in Accra · 3 years · 20 customers/wk' },
      { name: 'Software Development', confidence: 0.52, evidence: 'learned coding on YouTube' },
      { name: 'Mobile money (Vodafone Cash)', confidence: 0.74 },
    ],
    wage_signal: {
      score: 64,
      display_value: 'GHS 38 / day',
      rationale:
        'Daily-wage band typical for Accra electronics-repair specialists with sustained customer volume (~20/wk).',
    },
    growth_signal: {
      score: 78,
      rationale:
        'Multi-skill stack (repair + software + mobile-money) on a zero-credential profile — high formalisation upside via SME onboarding.',
    },
    job_match: {
      score: 82,
      rationale: 'Phone Repair + Software Development profile matches 4 opportunities in the GH labor market — best fit: Mobile Repair SME — NBSSI Registry. High job-market alignment.',
      opportunity_count: 4,
      matched_opportunities: [
        {
          title: 'Mobile Repair SME — NBSSI Registry',
          employer_type: 'government',
          channel: 'NBSSI mobile-device repair SME registry + MTN MoMo business account',
          lat: 5.5502, lng: -0.2174,
          label: 'Accra Central — NBSSI',
          wage_range: 'GHS 35–60 / day',
          isco_code: '7421',
          formalization_path: '1. Register at nbssi.gov.gh  2. Open MTN MoMo SME account  3. List on GiG Ghana marketplace',
          match_score: 0.91,
        },
        {
          title: 'Ghana Tech Lab — Digital Entrepreneur Track',
          employer_type: 'ngo',
          channel: 'Ghana Tech Lab / iSpace accelerator onboarding (Accra)',
          lat: 5.6037, lng: -0.1870,
          label: 'Accra Tech Hub — iSpace',
          wage_range: 'GHS 60–150 / day',
          isco_code: '2512',
          formalization_path: '1. Apply at ghanatech.lab  2. Complete 4-week digital track  3. Demo day → SME grant up to GHS 5 000',
          match_score: 0.74,
        },
        {
          title: 'MTN MoMo / Vodafone Cash Agent Cooperative',
          employer_type: 'cooperative',
          channel: 'GhIPSS agent registration + MTN MoMo agent network',
          lat: 5.5502, lng: -0.2174,
          label: 'Accra — GhIPSS',
          wage_range: 'GHS 30–65 / day',
          isco_code: '4211',
          formalization_path: '1. Register at ghipss.net  2. Attend 1-day agent training  3. Receive float credit from MTN/Vodafone',
          match_score: 0.62,
        },
        {
          title: 'Makola Market Vendor Cooperative',
          employer_type: 'cooperative',
          channel: 'Makola Market Traders\' Association + MoMo SME savings rail',
          lat: 5.5489, lng: -0.2083,
          label: 'Makola Market, Accra',
          wage_range: 'GHS 25–55 / day',
          isco_code: '5221',
          formalization_path: '1. Join Makola Traders\' Association (GHS 20 fee)  2. Link MTN MoMo for daily settlements  3. Apply for GCB micro-loan',
          match_score: 0.47,
        },
      ],
    },
    network_entry: {
      channel: 'NBSSI mobile-device repair SME registry + MTN MoMo business account',
      lat: 5.5502,
      lng: -0.2174,
      label: 'Accra Central — NBSSI',
    },
    sms_summary:
      'UNMAPPED:Amara, Accra | Phone Repair 68%, Software 52%, MoMo 74% | Wage 64/100 Growth 78/100 | Reply 1 for SME plan',
    ussd_menu: [
      'UNMAPPED *789#',
      '1. View profile',
      '2. Wage signal: 64/100',
      '3. Growth signal: 78/100',
      '4. Share to MoMo SME',
      '0. Exit',
    ],
    automation_risk: {
      automation_probability: 0.23,
      raw_probability: 0.41,
      risk_tier: 'low',
      trajectory_2035: 'growing',
      durable_skills: ['right-to-repair diagnostics', 'customer trust'],
      adjacent_skills: ['IoT diagnostics', 'right-to-repair instruction'],
      rationale:
        'Phone Repair: Frey-Osborne raw exposure 41% (SOC 49-2094); ILO LMIC calibration → 23% in GH. Trajectory to 2035: growing. By 2035, 27% of working-age Ghanaians are projected to have post-secondary education (Wittgenstein Centre, SSP2).',
      sources: [
        'Frey & Osborne (2017), Oxford Martin School',
        'ILO Future of Work — LMIC task indices (2018, 2021)',
        'Wittgenstein Centre Human Capital, SSP2 (2024)',
      ],
    },
    neet_context: {
      neet_pct: 24.9,
      narrative:
        'About 1 in 4 young Ghanaians aged 15–24 is not in work, school, or training (ILO/World Bank, 2022).',
      source: 'World Bank Data360 / ILO ILOSTAT (SDG 8.6.1)',
      year: 2022,
    },
  },
};

const AM_ANI: ParseResponse = {
  ok: true,
  country: 'AM',
  parser_version: 'mock-0.3.0-alpha.4',
  latency_ms: 220,
  profile: {
    profile_id: 'am-ani-001',
    display_name: 'Ani H.',
    pseudonym: 'Ani',
    age: 31,
    location: 'Gyumri, Shirak',
    languages: ['Armenian', 'Russian', 'English'],
    skills: [
      { name: 'English Tutoring', confidence: 0.74, evidence: 'home lessons' },
      { name: 'Translation (HY/RU/EN)', confidence: 0.62, evidence: 'weekly small-business contracts' },
      { name: 'Digital payments (Idram)', confidence: 0.78 },
    ],
    wage_signal: {
      score: 71,
      display_value: 'AMD 4 500 / hr',
      rationale:
        'Aligned with regional private-tutor rates; multi-client diversification adds an income floor.',
    },
    growth_signal: {
      score: 82,
      rationale:
        'Multilingual EduTech stack + Idram rail → micro-formalisation viable through e-gov.am sole-prop registration.',
    },
    job_match: {
      score: 76,
      rationale: 'English Tutoring + Translation profile matches 3 opportunities in the AM labor market — best fit: GES Community Teaching — e-gov.am Sole-Proprietor Track. High job-market alignment.',
      opportunity_count: 3,
      matched_opportunities: [
        {
          title: 'GES Community Teaching — e-gov.am Sole-Proprietor Track',
          employer_type: 'government',
          channel: 'e-gov.am sole-proprietor registration + private tutoring marketplace',
          lat: 40.1872, lng: 44.5152,
          label: 'Yerevan — e-gov.am',
          wage_range: 'AMD 40 000–90 000 / mo',
          isco_code: '2320',
          formalization_path: '1. Register sole proprietor at e-gov.am (free, 1 day)  2. Open ACBA Bank account  3. List on Masiv.am tutoring board',
          match_score: 0.88,
        },
        {
          title: 'Armenia Translators Association — Freelance Registry',
          employer_type: 'cooperative',
          channel: 'Armenia Translators Association (ATA) + Smartling platform onboarding',
          lat: 40.1872, lng: 44.5136,
          label: 'Yerevan — ATA',
          wage_range: 'AMD 45 000–120 000 / mo',
          isco_code: '2643',
          formalization_path: '1. Register at ata.am  2. Pass ATA language proficiency test  3. List on Smartling/Gengo freelance marketplace',
          match_score: 0.79,
        },
        {
          title: 'Idram / Telcell Digital Wallet Agent Network',
          employer_type: 'cooperative',
          channel: 'Idram agent network registration + EasyPay terminal onboarding',
          lat: 40.1887, lng: 44.5152,
          label: 'Yerevan — Idram HQ',
          wage_range: 'AMD 35 000–75 000 / mo',
          isco_code: '4211',
          formalization_path: '1. Register at idram.am/agents  2. Attend 1-day training  3. Receive terminal + float credit from Idram',
          match_score: 0.58,
        },
      ],
    },
    network_entry: {
      channel: 'e-gov.am sole-proprietor registration + private tutoring marketplace',
      lat: 40.1872,
      lng: 44.5152,
      label: 'Yerevan — e-gov.am',
    },
    sms_summary:
      'UNMAPPED:Ani, Gyumri | EN tutor 74%, Translator 62%, Idram 78% | Wage 71/100 Growth 82/100 | Reply 1 for studio plan',
    ussd_menu: [
      'UNMAPPED *404#',
      '1. Իմ պրոֆիլը',
      '2. Աշխատավարձ՝ 71/100',
      '3. Աճ՝ 82/100',
      '4. Կիսվել e-gov.am-ի հետ',
      '0. Ելք',
    ],
    automation_risk: {
      automation_probability: 0.12,
      raw_probability: 0.16,
      risk_tier: 'low',
      trajectory_2035: 'growing',
      durable_skills: ['mentorship', 'youth motivation'],
      adjacent_skills: ['Education-coach mentorship', 'Digital-literacy training'],
      rationale:
        'Vocational education teachers: Frey-Osborne raw exposure 16% (SOC 25-1194); ILO LMIC calibration → 12% in AM. Trajectory to 2035: growing. By 2035, 55% of working-age Armenians are projected to have post-secondary education (Wittgenstein Centre, SSP2).',
      sources: [
        'Frey & Osborne (2017), Oxford Martin School',
        'ILO Future of Work — LMIC task indices (2018, 2021)',
        'Wittgenstein Centre Human Capital, SSP2 (2024)',
      ],
    },
    neet_context: {
      neet_pct: 31.5,
      narrative:
        'About 1 in 3 young Armenians aged 15–24 is not in work, school, or training (ILO/World Bank, 2022) — among the highest rates in Eastern Europe & Central Asia.',
      source: 'World Bank Data360 / ILO ILOSTAT (SDG 8.6.1)',
      year: 2022,
    },
  },
};

export function mockParse(rawInput: string, country: CountryCode): ParseResponse {
  const base = country === 'GH' ? GH_AMARA : AM_ANI;
  const echoed = rawInput.trim().slice(0, 60);
  if (!echoed) return base;
  return {
    ...base,
    latency_ms: 180 + Math.floor(Math.random() * 120),
    profile: {
      ...base.profile,
      sms_summary: clampSms(`${base.profile.sms_summary} | "${echoed}"`),
    },
  };
}

function clampSms(s: string): string {
  return s.length > 320 ? `${s.slice(0, 319)}…` : s;
}
