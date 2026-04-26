import type { AutomationRisk as AutomationRiskT } from '@/lib/types';

interface Props {
  risk: AutomationRiskT;
}

const TIER_STYLE: Record<AutomationRiskT['risk_tier'], { dot: string; chip: string; label: string }> = {
  low: {
    dot: 'bg-signal-wage',
    chip: 'bg-signal-wage/15 text-signal-wage',
    label: 'Low',
  },
  medium: {
    dot: 'bg-sun-500',
    chip: 'bg-sun-500/15 text-sun-600',
    label: 'Medium',
  },
  high: {
    dot: 'bg-signal-risk',
    chip: 'bg-signal-risk/15 text-signal-risk',
    label: 'High',
  },
};

const TRAJECTORY_LABEL: Record<AutomationRiskT['trajectory_2035'], string> = {
  growing: '↗ growing',
  stable: '→ stable',
  declining: '↘ declining',
};

/**
 * Module 2 — AI Readiness card. Surfaces the LMIC-calibrated automation
 * probability, the 2035 trajectory direction, and the durable + adjacent
 * skills the brief calls "human-edge" recommendations.
 *
 * Sources are listed verbatim — the brief explicitly demands transparent
 * provenance on every visible signal.
 */
export function AutomationRisk({ risk }: Props) {
  const tier = TIER_STYLE[risk.risk_tier];
  const probabilityPct = Math.round(risk.automation_probability * 100);
  const rawPct = Math.round(risk.raw_probability * 100);

  return (
    <section
      aria-label="AI readiness and automation risk"
      className="card border border-clay-200/60 bg-clay-50/40 px-5 py-4 sm:px-7 sm:py-5"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-clay-800">
            AI readiness · automation risk to 2035
          </h3>
          <p className="text-[11px] uppercase tracking-wider text-clay-600">
            LMIC-calibrated · Frey-Osborne × ILO
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`pill ${tier.chip}`}>
            <span aria-hidden className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${tier.dot}`} />
            {tier.label} risk
          </span>
          <span className="pill bg-clay-100 text-clay-700">
            {TRAJECTORY_LABEL[risk.trajectory_2035]}
          </span>
        </div>
      </header>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-medium text-clay-700">Adjusted probability</span>
            <span className="font-mono text-sm font-semibold text-clay-900">{probabilityPct}%</span>
          </div>
          <div
            role="progressbar"
            aria-valuenow={probabilityPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Automation probability"
            className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-clay-100"
          >
            <div
              className={`h-full ${tier.dot} transition-[width] duration-700 ease-out`}
              style={{ width: `${probabilityPct}%` }}
            />
          </div>
          <p className="mt-1 text-[11px] text-clay-600">
            Raw US-context Frey-Osborne: <span className="font-mono">{rawPct}%</span> · LMIC dampening applied.
          </p>
        </div>

        <p className="text-xs leading-snug text-clay-700">{risk.rationale}</p>
      </div>

      {(risk.durable_skills.length > 0 || risk.adjacent_skills.length > 0) && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {risk.durable_skills.length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold uppercase tracking-wider text-clay-700">
                Durable (human-edge) skills
              </h4>
              <ul className="mt-1 flex flex-wrap gap-1.5">
                {risk.durable_skills.map((s) => (
                  <li key={s} className="pill bg-signal-wage/10 text-signal-wage">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {risk.adjacent_skills.length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold uppercase tracking-wider text-clay-700">
                Adjacent skills to grow into
              </h4>
              <ul className="mt-1 flex flex-wrap gap-1.5">
                {risk.adjacent_skills.map((s) => (
                  <li key={s} className="pill bg-signal-growth/10 text-signal-growth">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {risk.sources.length > 0 && (
        <p className="mt-3 text-[10px] uppercase tracking-wider text-clay-600">
          Sources: {risk.sources.join(' · ')}
        </p>
      )}
    </section>
  );
}
