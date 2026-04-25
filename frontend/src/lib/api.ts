import { mockParse } from './mock';
import type { ParseRequest, ParseResponse, ParseResult } from './types';

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '');
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const TIMEOUT_MS = 8000;

/** Backend route prefix per Claude 1's main.py (`app.include_router(router, prefix="/api/v1")`). */
const PARSE_PATH = '/api/v1/parse';

export type ParseSource = 'live' | 'mock-fallback' | 'demo';

export interface ParseOutcome {
  result: ParseResult;
  source: ParseSource;
  /** When `mock-fallback`, the underlying network/HTTP reason for telemetry. */
  fallbackReason?: string;
}

export async function parse(req: ParseRequest): Promise<ParseOutcome> {
  if (DEMO_MODE || !API_URL) {
    return { result: mockParse(req.text, req.country_code), source: 'demo' };
  }

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${API_URL}${PARSE_PATH}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    if (!res.ok) {
      return {
        result: mockParse(req.text, req.country_code),
        source: 'mock-fallback',
        fallbackReason: `HTTP ${res.status}`,
      };
    }

    const data = (await res.json()) as ParseResponse;
    return { result: data, source: 'live' };
  } catch (err) {
    return {
      result: mockParse(req.text, req.country_code),
      source: 'mock-fallback',
      fallbackReason: err instanceof Error ? err.message : 'unknown',
    };
  } finally {
    window.clearTimeout(timer);
  }
}
