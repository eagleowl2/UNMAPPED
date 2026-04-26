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
    network_entry: {
      channel: 'Mobile-money cooperative onboarding (Vodafone Cash → MTN MoMo SME)',
      lat: 5.5502,
      lng: -0.2174,
      label: 'Makola, Accra',
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
    network_entry: {
      channel: 'Sole-proprietor e-registration via e-gov.am + Idram for-business',
      lat: 40.7894,
      lng: 43.8475,
      label: 'Gyumri',
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
