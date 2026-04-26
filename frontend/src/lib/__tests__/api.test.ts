import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

const VALID_BODY = {
  ok: true,
  country: 'GH',
  parser_version: 'sse-0.3.0',
  latency_ms: 42,
  profile: {
    profile_id: 'gh-test-1',
    display_name: 'Test',
    pseudonym: 'Test',
    location: 'Accra',
    languages: ['English'],
    skills: [{ name: 'Phone Repair', confidence: 0.6 }],
    wage_signal: { score: 50, rationale: 'mid', display_value: 'GHS 30 / day' },
    growth_signal: { score: 60, rationale: 'ok' },
    network_entry: { channel: 'MoMo', lat: 5.5, lng: -0.2, label: 'Accra' },
    sms_summary: 'hi',
    ussd_menu: ['*789#', '1', '2', '3'],
  },
};

describe('parse() — fetch wrapper', () => {
  it('returns a live result when fetch returns 200 with a ParseResponse body', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => VALID_BODY,
    });
    vi.stubGlobal('fetch', fetchSpy);

    const { parse } = await import('../api');
    const out = await parse({ raw_input: 'x', country: 'GH' });
    expect(out.source).toBe('live');
    expect(out.result.ok).toBe(true);
    expect(fetchSpy).toHaveBeenCalledWith(
      '/parse',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('falls back to mock when fetch rejects', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    const { parse } = await import('../api');
    const out = await parse({ raw_input: 'amara', country: 'GH' });
    expect(out.source).toBe('mock-fallback');
    expect(out.fallbackReason).toBe('network down');
    expect(out.result.ok).toBe(true);
  });

  it('falls back to mock on non-200 with reason', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({}) }),
    );
    const { parse } = await import('../api');
    const out = await parse({ raw_input: 'x', country: 'GH' });
    expect(out.source).toBe('mock-fallback');
    expect(out.fallbackReason).toBe('HTTP 503');
  });

  it('uses demo mode when VITE_DEMO_MODE=true (no fetch call)', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'true');
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const { parse } = await import('../api');
    const out = await parse({ raw_input: 'x', country: 'GH' });
    expect(out.source).toBe('demo');
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
