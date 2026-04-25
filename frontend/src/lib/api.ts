import { mockParse } from './mock';
import type { ParseRequest, ParseResponse, ParseResult } from './types';

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '');
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const TIMEOUT_MS = 8000;

export type ParseSource = 'live' | 'mock-fallback' | 'demo';

export interface ParseOutcome {
  result: ParseResult;
  source: ParseSource;
}

export async function parse(req: ParseRequest): Promise<ParseOutcome> {
  if (DEMO_MODE || !API_URL) {
    return { result: mockParse(req.raw_input, req.country), source: 'demo' };
  }

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${API_URL}/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    if (!res.ok) {
      return {
        result: mockParse(req.raw_input, req.country),
        source: 'mock-fallback',
      };
    }

    const data = (await res.json()) as ParseResponse;
    return { result: data, source: 'live' };
  } catch {
    return {
      result: mockParse(req.raw_input, req.country),
      source: 'mock-fallback',
    };
  } finally {
    window.clearTimeout(timer);
  }
}
