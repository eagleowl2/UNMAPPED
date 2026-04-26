/**
 * Per UNMAPPED Protocol v0.2 §5.4 (and Master Context §6.5): the SPA must
 * NOT cache PII on shared devices. `raw_input` is Amara's personal story
 * and a parsed `ParseResponse` carries derived PII (name, age, location).
 * Both used to be cached under v3 keys — this revision drops them entirely.
 *
 * Only the locale *preference* is persisted, since 'GH' / 'AM' is a
 * reconfigurable transform input, not personal data. Any v3 PII keys left
 * over from earlier installs are wiped on first read.
 */

const KEY_LOCALE = 'unmapped:locale_v4';
const LEGACY_PII_KEYS = [
  'unmapped:last_input_v3',
  'unmapped:last_result_v3',
  'unmapped:last_input_v2',
  'unmapped:last_result_v2',
] as const;

function purgeLegacyPii(): void {
  try {
    for (const k of LEGACY_PII_KEYS) {
      localStorage.removeItem(k);
    }
  } catch {
    /* private mode — nothing to do */
  }
}

export const storage = {
  saveLocale(code: string): void {
    try {
      localStorage.setItem(KEY_LOCALE, code);
    } catch {
      /* ignore — quota / private mode */
    }
  },
  loadLocale(): string | null {
    try {
      purgeLegacyPii();
      return localStorage.getItem(KEY_LOCALE);
    } catch {
      return null;
    }
  },
};
