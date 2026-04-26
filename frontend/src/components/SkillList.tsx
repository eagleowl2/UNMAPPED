import type { Skill } from '@/lib/types';

interface Props {
  skills: Skill[];
}

/**
 * Confidence-bar list for the skills primitive. Tier label is derived from
 * the 0..1 confidence score for visual hierarchy; the score itself stays
 * the source of truth.
 */
export function SkillList({ skills }: Props) {
  return (
    <ul className="space-y-2.5">
      {skills.map((s) => {
        const pct = Math.round(clamp(s.confidence, 0, 1) * 100);
        const tier = tierFor(s.confidence);
        return (
          <li key={s.name} className="rounded-lg bg-clay-50 px-3 py-2.5">
            <div className="flex items-baseline justify-between gap-3">
              <div className="min-w-0">
                <h4 className="truncate text-sm font-semibold text-clay-900">{s.name}</h4>
                {s.evidence && (
                  <p className="truncate text-[11px] leading-snug text-clay-600">
                    &ldquo;{s.evidence}&rdquo;
                  </p>
                )}
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`pill ${tier.chipClass}`}>{tier.label}</span>
                <span className={`shrink-0 font-mono text-sm font-semibold ${tier.pctClass}`}>
                  {pct}%
                </span>
              </div>
            </div>
            <div
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${s.name} confidence`}
              className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-clay-100"
            >
              <div
                className={`h-full ${tier.barClass} transition-[width] duration-700 ease-out`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function tierFor(c: number) {
  if (c >= 0.85) {
    return {
      label: 'Expert',
      chipClass: 'bg-sun-500/15 text-sun-600',
      barClass: 'bg-sun-500',
      pctClass: 'text-sun-600',
    };
  }
  if (c >= 0.65) {
    return {
      label: 'Established',
      chipClass: 'bg-signal-wage/15 text-signal-wage',
      barClass: 'bg-signal-wage',
      pctClass: 'text-signal-wage',
    };
  }
  if (c >= 0.45) {
    return {
      label: 'Developing',
      chipClass: 'bg-signal-growth/15 text-signal-growth',
      barClass: 'bg-signal-growth',
      pctClass: 'text-signal-growth',
    };
  }
  return {
    label: 'Emerging',
    chipClass: 'bg-clay-100 text-clay-700',
    barClass: 'bg-clay-300',
    pctClass: 'text-clay-600',
  };
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}
