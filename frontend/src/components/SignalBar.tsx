import type { Signal } from '@/lib/types';

interface Props {
  label: string;
  signal: Signal;
  tone: 'wage' | 'growth';
  /** Subtle (in-card) vs hero (top of profile) framing. */
  variant?: 'hero' | 'inline';
}

const TONE = {
  wage: {
    fill: 'bg-signal-wage',
    text: 'text-signal-wage',
    glow: 'from-signal-wage/12 to-signal-wage/0',
    accent: 'GHS / AMD',
    icon: '💰',
  },
  growth: {
    fill: 'bg-signal-growth',
    text: 'text-signal-growth',
    glow: 'from-signal-growth/12 to-signal-growth/0',
    accent: 'trajectory',
    icon: '📈',
  },
} as const;

/**
 * Econometric signal bar — used for the two top-line wage + growth signals
 * in the profile card (the "wow" primitives from v0.2 Section 4.2).
 */
export function SignalBar({ label, signal, tone, variant = 'hero' }: Props) {
  const pct = clamp(signal.score, 0, 100);
  const t = TONE[tone];
  const isHero = variant === 'hero';

  return (
    <div
      className={
        isHero
          ? `relative overflow-hidden rounded-xl bg-gradient-to-br ${t.glow} p-4 ring-1 ring-clay-200/70`
          : ''
      }
    >
      <div className="flex items-baseline justify-between gap-3">
        <h3
          className={
            isHero
              ? 'text-sm font-semibold uppercase tracking-wide text-clay-700'
              : 'text-sm font-semibold text-clay-800'
          }
        >
          {isHero && <span aria-hidden className="mr-1.5">{t.icon}</span>}
          {label}
        </h3>
        <div className="flex items-baseline gap-2">
          {signal.display_value && (
            <span className="font-mono text-xs font-medium text-clay-700">
              {signal.display_value}
            </span>
          )}
          <span className={`font-mono ${isHero ? 'text-2xl' : 'text-sm'} font-bold ${t.text}`}>
            {pct}
            <span className="text-xs font-medium text-clay-500">/100</span>
          </span>
        </div>
      </div>

      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        className={`mt-${isHero ? '2' : '1.5'} h-2 w-full overflow-hidden rounded-full bg-clay-100`}
      >
        <div
          className={`h-full ${t.fill} transition-[width] duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="mt-2 text-xs leading-snug text-clay-600">{signal.rationale}</p>
    </div>
  );
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
