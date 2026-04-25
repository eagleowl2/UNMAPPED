import type { CountryCode } from './types';

export interface LocaleConfig {
  code: CountryCode;
  flag: string;
  name: string;
  currency: string;
  primaryLanguages: string[];
  ussdShortcode: string;
  smsSender: string;
  /** Bbox center for the network-entry map. */
  mapCenter: { lat: number; lng: number; zoomLabel: string };
  /** Placeholder prompt rendered in the input textarea. */
  placeholder: string;
  /** Sample chaotic input button label. */
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
    mapCenter: { lat: 5.56, lng: -0.2, zoomLabel: 'Greater Accra' },
    placeholder:
      'Tell us about yourself in any language — what you do, where, what you have learned…',
    sampleLabel: 'Try a Ghana sample',
    sample:
      'I am Amara, 27, I sell smoked fish at Makola three days a week and braid hair on the other days. ' +
      'I learned book-keeping from my aunt and I keep my own ledger in a notebook. I have a Vodafone Cash account. ' +
      'I want to start a small frozen-fish stall.',
  },
  AM: {
    code: 'AM',
    flag: '🇦🇲',
    name: 'Armenia',
    currency: 'AMD',
    primaryLanguages: ['Armenian', 'Russian', 'English'],
    ussdShortcode: '*404#',
    smsSender: 'UNMAPPED',
    mapCenter: { lat: 40.18, lng: 44.51, zoomLabel: 'Yerevan' },
    placeholder:
      'Պատմեք ձեր մասին ցանկացած լեզվով — ինչ եք անում, որտեղ, ինչ եք սովորել…',
    sampleLabel: 'Try an Armenia sample',
    sample:
      'Իմ անունը Անի է, 31 տարեկան, Գյումրիից եմ։ Անգլերեն դասեր եմ տալիս տանը և շաբաթական ' +
      'մի քանի անգամ թարգմանում փոքր ընկերությունների համար։ Ունեմ Idram հաշիվ։ Ուզում եմ բացել իմ ' +
      'դասավանդման փոքր ստուդիան։',
  },
};

export const DEFAULT_LOCALE: CountryCode = 'GH';
