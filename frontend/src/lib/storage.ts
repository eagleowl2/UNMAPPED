import type { ParseResponse } from './types';

const KEY_LAST_RESULT = 'unmapped:last_result_v2';
const KEY_LAST_INPUT = 'unmapped:last_input_v2';
const KEY_LOCALE = 'unmapped:locale_v2';

export const storage = {
  saveResult(result: ParseResponse): void {
    try {
      localStorage.setItem(KEY_LAST_RESULT, JSON.stringify(result));
    } catch {
      /* private mode / quota — ignore, the demo still works in-memory */
    }
  },
  loadResult(): ParseResponse | null {
    try {
      const raw = localStorage.getItem(KEY_LAST_RESULT);
      return raw ? (JSON.parse(raw) as ParseResponse) : null;
    } catch {
      return null;
    }
  },
  saveInput(text: string): void {
    try {
      localStorage.setItem(KEY_LAST_INPUT, text);
    } catch {
      /* ignore */
    }
  },
  loadInput(): string {
    try {
      return localStorage.getItem(KEY_LAST_INPUT) ?? '';
    } catch {
      return '';
    }
  },
  saveLocale(code: string): void {
    try {
      localStorage.setItem(KEY_LOCALE, code);
    } catch {
      /* ignore */
    }
  },
  loadLocale(): string | null {
    try {
      return localStorage.getItem(KEY_LOCALE);
    } catch {
      return null;
    }
  },
};
