import type { CountryCode, ParseResponse } from './types';

/**
 * Bundled offline parser used when:
 *   - VITE_DEMO_MODE=true (deliberate, e.g. flaky-wifi pitch)
 *   - the backend /parse call fails (network / 5xx / timeout)
 *
 * Heuristics are intentionally simple: we surface what the user actually typed
 * back to them so the demo never feels canned. The real intelligence lives in
 * Claude 1's parser.
 */

const GH_SAMPLE: ParseResponse = {
  ok: true,
  country: 'GH',
  parser_version: 'mock-0.3.0',
  latency_ms: 240,
  profile: {
    profile_id: 'gh-amara-001',
    display_name: 'Amara A.',
    pseudonym: 'Amara',
    age: 27,
    location: 'Accra, Greater Accra',
    languages: ['English', 'Twi'],
    skills: [
      { name: 'Smoked-fish trading', confidence: 0.92, evidence: 'Makola 3 days/week' },
      { name: 'Hair braiding', confidence: 0.88 },
      { name: 'Bookkeeping (manual ledger)', confidence: 0.74, evidence: 'learned from aunt' },
      { name: 'Mobile money (Vodafone Cash)', confidence: 0.81 },
    ],
    wage_signal: {
      score: 64,
      display_value: 'GHS 38 / day',
      rationale: 'Daily-wage band typical for Makola fresh-market vendors with own stock.',
    },
    growth_signal: {
      score: 78,
      rationale:
        'Stated ambition (frozen-fish stall) + active ledger + mobile-money rails = high formalization potential.',
    },
    network_entry: {
      channel: 'Mobile-money cooperative onboarding (Vodafone Cash → MTN MoMo SME)',
      lat: 5.5502,
      lng: -0.2174,
      label: 'Makola Market',
    },
    sms_summary:
      'UNMAPPED: Amara, 27, Accra. Trader+braider, ledger, VodafoneCash. Wage 64/100 Growth 78/100. Reply 1 for SME plan.',
    ussd_menu: [
      'UNMAPPED *789#',
      '1. View my profile',
      '2. Wage signal: 64/100',
      '3. Growth signal: 78/100',
      '4. Share to MTN MoMo SME',
      '0. Exit',
    ],
  },
};

const AM_SAMPLE: ParseResponse = {
  ok: true,
  country: 'AM',
  parser_version: 'mock-0.3.0',
  latency_ms: 220,
  profile: {
    profile_id: 'am-ani-001',
    display_name: 'Ani H.',
    pseudonym: 'Ani',
    age: 31,
    location: 'Gyumri, Shirak',
    languages: ['Armenian', 'Russian', 'English'],
    skills: [
      { name: 'English tutoring', confidence: 0.93, evidence: 'home lessons' },
      { name: 'Translation (EN/RU/HY)', confidence: 0.85, evidence: 'small companies, weekly' },
      { name: 'Digital payments (Idram)', confidence: 0.78 },
    ],
    wage_signal: {
      score: 71,
      display_value: 'AMD 4 500 / hr',
      rationale: 'In-line with regional private-tutor rates; multi-client diversification adds floor.',
    },
    growth_signal: {
      score: 82,
      rationale:
        'Studio ambition + multilingual stack + Idram rail makes EduTech micro-formalization viable.',
    },
    network_entry: {
      channel: 'Sole-proprietor e-registration via e-gov.am + Idram for-business',
      lat: 40.7894,
      lng: 43.8475,
      label: 'Gyumri',
    },
    sms_summary:
      'UNMAPPED: Ani, 31, Gyumri. Tutor+translator, Idram. Wage 71/100 Growth 82/100. Reply 1 for studio plan.',
    ussd_menu: [
      'UNMAPPED *404#',
      '1. Իմ պրոֆիլը',
      '2. Աշխատավարձ՝ 71/100',
      '3. Աճ՝ 82/100',
      '4. Կիսվել e-gov.am-ի հետ',
      '0. Ելք',
    ],
  },
};

export function mockParse(rawInput: string, country: CountryCode): ParseResponse {
  const base = country === 'GH' ? GH_SAMPLE : AM_SAMPLE;
  if (!rawInput.trim()) return base;

  // Tiny gesture so the user sees their words reflected — keeps the demo honest.
  const echoed = rawInput.trim().slice(0, 80);
  return {
    ...base,
    latency_ms: 180 + Math.floor(Math.random() * 120),
    profile: {
      ...base.profile,
      sms_summary: `${base.profile.sms_summary.slice(0, 80)} | "${echoed}"`.slice(0, 320),
    },
  };
}
