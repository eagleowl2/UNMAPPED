import type { LocaleConfig } from '@/lib/locales';
import type { NetworkEntryPoint } from '@/lib/types';

interface Props {
  locale: LocaleConfig;
  entry: NetworkEntryPoint;
}

/**
 * Lightweight, fully-offline map placeholder. Real geo rendering (e.g. MapLibre +
 * vector tiles) comes in v0.4 — for the hackathon demo we render a stylized
 * SVG with a pulsing entry pin, which works at 0 kbps.
 */
export function NetworkEntryMap({ locale, entry }: Props) {
  return (
    <figure
      className="relative overflow-hidden rounded-xl bg-gradient-to-br from-clay-50 to-clay-100 ring-1 ring-clay-200/70"
      aria-label={`Network-entry map: ${entry.label}`}
    >
      <svg
        viewBox="0 0 320 160"
        className="h-44 w-full"
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
        <rect width="320" height="160" fill="url(#grid)" />
        <rect width="320" height="160" fill="url(#haze)" />

        {/* Abstract land mass — nothing geographic, just a calm shape */}
        <path
          d="M30,110 C60,80 90,95 120,80 C150,65 180,90 210,75 C240,60 270,80 300,70 L300,160 L20,160 Z"
          fill="rgba(60,40,15,0.08)"
        />

        {/* Entry pin */}
        <g transform="translate(160 80)">
          <circle r="22" fill="rgba(255,138,0,0.18)" className="pulse-ring" />
          <circle r="9" fill="#ff8a00" stroke="white" strokeWidth="2.5" />
        </g>
      </svg>

      <figcaption className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-3 bg-white/80 px-3 py-2 text-xs backdrop-blur-sm">
        <span className="font-medium text-clay-800">{entry.label}</span>
        <span className="text-clay-600">
          {locale.flag} {locale.mapCenter.zoomLabel}
        </span>
      </figcaption>
    </figure>
  );
}
