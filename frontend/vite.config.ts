/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

/**
 * UNMAPPED frontend — Vite config.
 *
 * Proxy strategy:
 *   The SPA always fetches relative `/api/v1/*` URLs from the browser. Vite's
 *   dev-server proxies those to whatever absolute target lives in
 *   `VITE_API_URL`. In docker-compose that's the docker-internal hostname
 *   `http://backend:8000`; for standalone dev it's `http://localhost:8000`.
 *
 *   This keeps the SPA same-origin (no CORS), works whether the backend is
 *   accessed by service name or host port, and never asks the browser to
 *   resolve a docker-only DNS name.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = env.VITE_API_URL?.replace(/\/+$/, '') || '';

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
            '/api': {
              target: proxyTarget,
              changeOrigin: true,
              secure: false,
            },
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
