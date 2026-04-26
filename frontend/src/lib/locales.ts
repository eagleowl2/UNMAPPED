import type { CountryCode } from './types';

export interface LocaleConfig {
  code: CountryCode;
  flag: string;
  name: string;
  currency: string;
  primaryLanguages: string[];
  ussdShortcode: string;
  smsSender: string;
  /** True if backend ships a country_profile for this locale. */
  backendSupported: boolean;
  placeholder: string;
  sampleLabel: string;
  sample: string;
}

export const LOCALES: Record<CountryCode, LocaleConfig> = {
  GH: {
    code: 'GH',
    flag: '🇬🇭',
    name: 'Ghana',
    currency: 'GHS',
    primaryLanguages: ['English', 'Twi', 'Ga'],
    ussdShortcode: '*789#',
    smsSender: 'UNMAPPED',
    backendSupported: true,
    placeholder:
      'Tell us about yourself in any language — what you do, where, what you have learned…',
    sampleLabel: 'Try the Amara story',
    // Canonical Amara story — matches the backend's test_parser.py vector.
    sample:
      'My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube, ' +
      'been fixing phones for 3 years, I have about 20 customers a week.',
  },
  AM: {
    code: 'AM',
    flag: '🇦🇲',
    name: 'Armenia',
    currency: 'AMD',
    primaryLanguages: ['Armenian', 'Russian', 'English'],
    ussdShortcode: '*404#',
    smsSender: 'UNMAPPED',
    // Backend ships armenia_urban_informal.json since alpha.4 (Claude 1 commit 33e13e4).
    backendSupported: true,
    placeholder:
      'Պատմեք ձեր մասին ցանկացած լեզվով — ինչ եք անում, որտեղ, ինչ եք սովորել…',
    sampleLabel: 'Try the Ani story',
    sample:
      'Իմ անունը Անի է, 31 տարեկան, Գյումրիից եմ։ Անգլերեն դասեր եմ տալիս տանը և շաբաթական ' +
      'մի քանի անգամ թարգմանում փոքր ընկերությունների համար։ Ունեմ Idram հաշիվ։ Ուզում եմ բացել իմ ' +
      'դասավանդման փոքր ստուդիան։',
  },
};

export const DEFAULT_LOCALE: CountryCode = 'GH';
