import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * The api module reads import.meta.env eagerly, so we re-import inside each
 * test after stubbing env. vi.resetModules() ensures a clean read.
 *
 * Since v0.3-sse-alpha.3 the SPA always fetches the relative `/api/v1/parse`
 * URL — the Vite dev-server (or a reverse-proxy) does the forwarding. So the
 * tests no longer assert on absolute URL composition, only on outcomes.
 */

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

const VALID_BODY = {
  ok: true,
  user: { user_id: 'u1' },
  skills: [],
  vss_list: [],
  human_layer: {
    hl_id: 'hl_x',
    schema_version: 'v0.2',
    created_at: '2026-01-01T00:00:00Z',
    user_id: 'u1',
    profile_card: {
      display_name: 'X',
      headline: 'Y',
      location: 'Z',
      skills_summary: [{ label: 'a', confidence_tier: 'emerging', confidence_score: 0.1 }],
    },
    sms_summary: { text: 'hi', char_count: 2 },
    ussd_tree: { root: { id: 'r', text: 't' } },
  },
  meta: {},
};

describe('parse() — fetch wrapper', () => {
  it('returns live result when fetch returns 200 with a ParseResponse body', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => VALID_BODY,
    });
    vi.stubGlobal('fetch', fetchSpy);

    const { parse } = await import('../api');
    const out = await parse({ text: 'x', country_code: 'GH', context_tag: 'urban_informal' });
    expect(out.source).toBe('live');
    expect(out.result.ok).toBe(true);

    // Always relative — the dev-server / proxy decides the target.
    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/v1/parse',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('falls back to mock when fetch rejects', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    const { parse } = await import('../api');
    const out = await parse({ text: 'amara', country_code: 'GH', context_tag: 'urban_informal' });
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
    const out = await parse({ text: 'x', country_code: 'GH', context_tag: 'urban_informal' });
    expect(out.source).toBe('mock-fallback');
    expect(out.fallbackReason).toBe('HTTP 503');
  });

  it('uses demo mode when VITE_DEMO_MODE=true (no fetch call)', async () => {
    vi.stubEnv('VITE_DEMO_MODE', 'true');
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const { parse } = await import('../api');
    const out = await parse({ text: 'x', country_code: 'GH', context_tag: 'urban_informal' });
    expect(out.source).toBe('demo');
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
