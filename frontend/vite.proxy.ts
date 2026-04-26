/**
 * Pure resolver for the Vite dev-server proxy target.
 *
 * Lives outside `src/` because `vite.config.ts` (Node side) imports it, and
 * we don't want it bundled into the SPA. It's reachable from Vitest tests
 * via a relative import — see `src/lib/__tests__/proxy.test.ts`.
 *
 * Resolution order:
 *   1. `VITE_DEMO_MODE === 'true'` → return `null` (no proxy; SPA falls
 *      back to bundled mock for offline pitches).
 *   2. `VITE_API_URL` non-empty after trimming + trailing-slash strip →
 *      use it (this is the docker-compose path: `http://backend:8000`).
 *   3. Default → `http://localhost:8000` so `npm run dev` Just Works™
 *      against a bare-metal `uvicorn ... --port 8000`.
 */
export interface ProxyEnv {
  VITE_API_URL?: string;
  VITE_DEMO_MODE?: string;
}

export const DEFAULT_PROXY_TARGET = 'http://localhost:8000';

export function resolveProxyTarget(env: ProxyEnv): string | null {
  if (env.VITE_DEMO_MODE === 'true') return null;
  const explicit = env.VITE_API_URL?.trim().replace(/\/+$/, '');
  if (explicit) return explicit;
  return DEFAULT_PROXY_TARGET;
}
