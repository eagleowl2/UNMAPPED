/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { resolveProxyTarget } from './vite.proxy';

/**
 * UNMAPPED frontend — Vite config.
 *
 * Proxy strategy:
 *   The SPA always fetches relative `/parse`, `/api/*`, `/health` URLs from
 *   the browser. Vite's dev-server proxies those to the resolved backend
 *   target (see vite.proxy.ts for the resolution rules).
 *
 *   Default is `http://localhost:8000` — bare-metal `uvicorn` parking spot.
 *   docker-compose overrides via `VITE_API_URL=http://backend:8000`.
 *   `VITE_DEMO_MODE=true` disables the proxy entirely so the SPA uses the
 *   bundled mock for offline pitches.
 *
 *   The resolved target is logged on every Vite startup so you can see in
 *   the terminal exactly which backend is being targeted — silent
 *   misconfigurations are how this got mis-diagnosed once already.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = resolveProxyTarget(env);

  if (proxyTarget) {
    // eslint-disable-next-line no-console
    console.log(
      `[unmapped/vite] mode=${mode}  proxy /parse, /api, /health → ${proxyTarget}`,
    );
  } else {
    // eslint-disable-next-line no-console
    console.log(
      `[unmapped/vite] mode=${mode}  VITE_DEMO_MODE=true — proxy disabled (SPA will use bundled mock)`,
    );
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 5173,
      host: true,
      strictPort: true,
      proxy: proxyTarget
        ? {
            '/parse': { target: proxyTarget, changeOrigin: true, secure: false },
            '/api': { target: proxyTarget, changeOrigin: true, secure: false },
            '/health': { target: proxyTarget, changeOrigin: true, secure: false },
          }
        : undefined,
    },
    build: {
      target: 'es2020',
      sourcemap: true,
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      css: false,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['src/main.tsx', 'src/test/**', 'src/**/*.d.ts'],
      },
    },
  };
});
