import type { ConfidenceTier, SkillSummaryEntry } from '@/lib/types';

interface Props {
  entry: SkillSummaryEntry;
}

const TIER: Record<ConfidenceTier, { label: string; bar: string; chip: string; pct: string }> = {
  emerging: {
    label: 'Emerging',
    bar: 'bg-clay-300',
    chip: 'bg-clay-100 text-clay-700',
    pct: 'text-clay-600',
  },
  developing: {
    label: 'Developing',
    bar: 'bg-signal-growth/70',
    chip: 'bg-signal-growth/15 text-signal-growth',
    pct: 'text-signal-growth',
  },
  established: {
    label: 'Established',
    bar: 'bg-signal-wage',
    chip: 'bg-signal-wage/15 text-signal-wage',
    pct: 'text-signal-wage',
  },
  expert: {
    label: 'Expert',
    bar: 'bg-sun-500',
    chip: 'bg-sun-500/15 text-sun-600',
    pct: 'text-sun-600',
  },
};

export function SignalBar({ entry }: Props) {
  const pct = clamp(entry.confidence_score * 100, 0, 100);
  const tier = TIER[entry.confidence_tier];

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="truncate text-sm font-semibold text-clay-900">{entry.label}</h4>
            <span className={`pill ${tier.chip}`}>{tier.label}</span>
          </div>
          {entry.taxonomy_code && (
            <p className="font-mono text-[10px] text-clay-500">{entry.taxonomy_code}</p>
          )}
        </div>
        <span className={`shrink-0 font-mono text-sm font-semibold ${tier.pct}`}>
          {Math.round(pct)}%
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${entry.label} confidence`}
        className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-clay-100"
      >
        <div
          className={`h-full ${tier.bar} transition-[width] duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
