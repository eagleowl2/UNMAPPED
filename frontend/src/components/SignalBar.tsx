import type { Signal } from '@/lib/types';

interface Props {
  label: string;
  signal: Signal;
  tone: 'wage' | 'growth';
}

const TONE = {
  wage: { fill: 'bg-signal-wage', text: 'text-signal-wage' },
  growth: { fill: 'bg-signal-growth', text: 'text-signal-growth' },
} as const;

export function SignalBar({ label, signal, tone }: Props) {
  const pct = clamp(signal.score, 0, 100);
  const t = TONE[tone];

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <h4 className="text-sm font-semibold text-clay-800">{label}</h4>
        <div className="flex items-baseline gap-2">
          {signal.display_value && (
            <span className="text-xs font-medium text-clay-600">{signal.display_value}</span>
          )}
          <span className={`font-mono text-sm font-semibold ${t.text}`}>{pct}/100</span>
        </div>
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-clay-100"
      >
        <div
          className={`h-full ${t.fill} transition-[width] duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-1.5 text-xs leading-snug text-clay-600">{signal.rationale}</p>
    </div>
  );
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
