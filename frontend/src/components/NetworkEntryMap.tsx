import type { LocaleConfig } from '@/lib/locales';

interface Props {
  locale: LocaleConfig;
  city: string;
}

/**
 * Lightweight, fully-offline map placeholder for the Network Entry primitive.
 * Real geo rendering (MapLibre + vector tiles) lands in v0.4 — for the
 * hackathon demo we render a stylized SVG with a pulsing entry pin so the
 * card works at 0 kbps.
 */
export function NetworkEntryMap({ locale, city }: Props) {
  return (
    <figure
      className="relative overflow-hidden rounded-xl bg-gradient-to-br from-clay-50 to-clay-100 ring-1 ring-clay-200/70"
      aria-label={`Network-entry map for ${city}`}
    >
      <svg
        viewBox="0 0 320 140"
        className="h-36 w-full"
        role="img"
        aria-hidden
      >
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(60,40,15,0.06)" strokeWidth="1" />
          </pattern>
          <radialGradient id="haze" cx="50%" cy="55%" r="60%">
            <stop offset="0%" stopColor="rgba(255,138,0,0.18)" />
            <stop offset="100%" stopColor="rgba(255,138,0,0)" />
          </radialGradient>
        </defs>
        <rect width="320" height="140" fill="url(#grid)" />
        <rect width="320" height="140" fill="url(#haze)" />
        <path
          d="M30,100 C60,72 90,86 120,72 C150,58 180,82 210,68 C240,54 270,72 300,62 L300,140 L20,140 Z"
          fill="rgba(60,40,15,0.08)"
        />
        <g transform="translate(160 70)">
          <circle r="22" fill="rgba(255,138,0,0.18)" className="pulse-ring" />
          <circle r="9" fill="#ff8a00" stroke="white" strokeWidth="2.5" />
        </g>
      </svg>
      <figcaption className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-3 bg-white/80 px-3 py-2 text-xs backdrop-blur-sm">
        <span className="font-medium text-clay-800">{city}</span>
        <span className="text-clay-600">{locale.flag} {locale.name}</span>
      </figcaption>
    </figure>
  );
}
