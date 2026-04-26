import { describe, expect, it } from 'vitest';
import { resolveProxyTarget, DEFAULT_PROXY_TARGET } from '../../../vite.proxy';

/**
 * Locks the dev-server proxy resolution. The user-facing contract:
 *   - `npm run dev` with no env  → proxies to localhost:8000
 *   - docker-compose VITE_API_URL=http://backend:8000 → proxies there
 *   - VITE_DEMO_MODE=true → no proxy (SPA uses mock)
 *   - Empty / whitespace VITE_API_URL is treated as not-set, NOT as opt-out
 *
 * If any of these break, the SPA silently falls back to its bundled
 * "Amara" mock — which is the bug we just fixed.
 */
describe('resolveProxyTarget', () => {
  it('defaults to localhost:8000 when no env vars are set', () => {
    expect(resolveProxyTarget({})).toBe('http://localhost:8000');
    expect(resolveProxyTarget({})).toBe(DEFAULT_PROXY_TARGET);
  });

  it('uses VITE_API_URL when set (docker-compose path)', () => {
    expect(resolveProxyTarget({ VITE_API_URL: 'http://backend:8000' })).toBe(
      'http://backend:8000',
    );
  });

  it('strips trailing slashes from VITE_API_URL', () => {
    expect(
      resolveProxyTarget({ VITE_API_URL: 'http://backend:8000///' }),
    ).toBe('http://backend:8000');
  });

  it('trims whitespace around VITE_API_URL', () => {
    expect(resolveProxyTarget({ VITE_API_URL: '  http://backend:8000  ' })).toBe(
      'http://backend:8000',
    );
  });

  it('returns null only when VITE_DEMO_MODE is exactly "true" (proxy disabled)', () => {
    expect(resolveProxyTarget({ VITE_DEMO_MODE: 'true' })).toBeNull();
  });

  it('treats truthy-looking VITE_DEMO_MODE values as NOT demo mode', () => {
    // Only the literal string 'true' opts out. Anything else falls through
    // to the default proxy. This avoids the "I set DEMO_MODE=1 expecting
    // it to work" footgun.
    expect(resolveProxyTarget({ VITE_DEMO_MODE: '1' })).toBe(DEFAULT_PROXY_TARGET);
    expect(resolveProxyTarget({ VITE_DEMO_MODE: 'TRUE' })).toBe(DEFAULT_PROXY_TARGET);
    expect(resolveProxyTarget({ VITE_DEMO_MODE: 'yes' })).toBe(DEFAULT_PROXY_TARGET);
  });

  it('falls back to default when VITE_API_URL is empty', () => {
    expect(resolveProxyTarget({ VITE_API_URL: '' })).toBe(DEFAULT_PROXY_TARGET);
  });

  it('falls back to default when VITE_API_URL is only whitespace', () => {
    expect(resolveProxyTarget({ VITE_API_URL: '   ' })).toBe(DEFAULT_PROXY_TARGET);
    expect(resolveProxyTarget({ VITE_API_URL: '\t\n' })).toBe(DEFAULT_PROXY_TARGET);
  });

  it('demo mode wins over VITE_API_URL (explicit opt-out)', () => {
    expect(
      resolveProxyTarget({
        VITE_DEMO_MODE: 'true',
        VITE_API_URL: 'http://backend:8000',
      }),
    ).toBeNull();
  });
});
