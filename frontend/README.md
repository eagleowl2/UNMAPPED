# UNMAPPED Frontend — Skills Signal Engine

Single-page React app that turns chaotic personal stories into a portable
**Skills Signal Profile** (Human Layer) plus an SMS + USSD fallback (Constraint
Layer). Hackathon module **M1 — SSE UI**, version `v0.3-sse-alpha.1`.

## Quick start

```bash
cd frontend
npm install
cp .env.example .env       # set VITE_API_URL to Claude 1's FastAPI base
npm run dev                # http://localhost:5173
```

Without a backend the SPA falls back to the bundled `mockParse` so the demo
always works — useful when the conference wifi gives up.

## Scripts

| Script         | Purpose                                                   |
| -------------- | --------------------------------------------------------- |
| `npm run dev`  | Vite dev server with HMR.                                 |
| `npm run build`| Type-check + production bundle into `dist/`.              |
| `npm run preview` | Preview the production build on :4173.                 |
| `npm run lint` | `tsc --noEmit` — strict mode, no unused locals/params.    |

## Backend integration

The SPA expects a single endpoint:

```
POST {VITE_API_URL}/parse
Content-Type: application/json

{ "raw_input": "...", "country": "GH" | "AM", "language_hint"?: "..." }
```

Full schema lives in [`../docs/api-contract.md`](../docs/api-contract.md) and
matching TypeScript types in [`src/lib/types.ts`](src/lib/types.ts).

## Architecture (one screen)

```
src/
├── App.tsx                      ← state machine (input ↔ result ↔ error)
├── components/
│   ├── InputPanel.tsx           ← single textarea, hotkey, sample input
│   ├── ProfileCard.tsx          ← Section 4.2 layout: header, skills, signals
│   ├── SignalBar.tsx            ← wage / growth bar + rationale
│   ├── NetworkEntryMap.tsx      ← offline SVG map with pulsing entry pin
│   ├── QrSimulation.tsx         ← QR for the profile share-link
│   ├── SmsPreview.tsx           ← 160-char fallback rendered as a phone bubble
│   ├── UssdSimulator.tsx        ← interactive *789# / *404# feature-phone shell
│   └── LocaleSwitcher.tsx       ← Ghana ↔ Armenia
└── lib/
    ├── api.ts                   ← fetch wrapper + abort + mock fallback
    ├── locales.ts               ← Ghana + Armenia config (samples included)
    ├── mock.ts                  ← bundled offline parser
    ├── storage.ts               ← localStorage cache (last input, locale, result)
    └── types.ts                 ← canonical request/response types
```

## Accessibility & low-bandwidth

- Mobile-first layout, responsive at 320 px upward.
- All interactive elements keyboard-reachable; focus rings on every control.
- `prefers-reduced-motion` disables the pulsing entry-pin animation.
- No images, no map tiles, no analytics — initial payload is a few KB gzipped.
- Bundled mock parser keeps the demo working on a captive-portal network.
