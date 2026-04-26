import type { BonaReport, BonaTier } from '@/lib/types';

interface Props {
  bona: BonaReport;
}

const TIER_STYLE: Record<BonaTier, { dot: string; chip: string; bar: string; label: string }> = {
  low: {
    dot: 'bg-signal-wage',
    chip: 'bg-signal-wage/15 text-signal-wage',
    bar: 'bg-signal-wage',
    label: 'Low',
  },
  medium: {
    dot: 'bg-sun-500',
    chip: 'bg-sun-500/15 text-sun-600',
    bar: 'bg-sun-500',
    label: 'Medium',
  },
  high: {
    dot: 'bg-signal-risk',
    chip: 'bg-signal-risk/15 text-signal-risk',
    bar: 'bg-signal-risk',
    label: 'High',
  },
};

const SUB_LABELS = {
  network_capture: {
    title: 'Network capture',
    blurb: 'How concentrated is the path into the formal economy?',
  },
  ghost_listings: {
    title: 'Ghost listings',
    blurb: 'Are the matched opportunities real and verifiable?',
  },
  programme_leakage: {
    title: 'Programme leakage',
    blurb: 'Does the programme actually reach this profile?',
  },
} as const;

/**
 * BONA — Bidirectional Opaque Network Auditor (UNMAPPED §6.7).
 *
 * Surfaces the three forensic sub-scores (capture / ghost listings / leakage)
 * with verbatim flags and source citations. Lower scores are better; the
 * tier chip uses the same low/medium/high vocabulary as automation risk so
 * the user only learns one scale.
 */
export function BonaPanel({ bona }: Props) {
  const overallTier = TIER_STYLE[bona.overall_tier];
  const overallPct = Math.round(bona.overall_score * 100);

  return (
    <section
      aria-label="BONA forensic audit"
      className="card border border-clay-200/60 bg-clay-50/40 px-5 py-4 sm:px-7 sm:py-5"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-clay-800">
            BONA · network &amp; programme audit
          </h3>
          <p className="text-[11px] uppercase tracking-wider text-clay-600">
            Forensic layer · Protocol §6.7
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`pill ${overallTier.chip}`}>
            <span aria-hidden className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${overallTier.dot}`} />
            {overallTier.label} concern
          </span>
          <span className="pill bg-clay-100 text-clay-700 font-mono">
            {overallPct}%
          </span>
        </div>
      </header>

      <p className="mt-2 text-xs leading-snug text-clay-700">{bona.rationale}</p>

      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        <BonaSub
          title={SUB_LABELS.network_capture.title}
          blurb={SUB_LABELS.network_capture.blurb}
          score={bona.network_capture.score}
          tier={bona.network_capture.tier}
        />
        <BonaSub
          title={SUB_LABELS.ghost_listings.title}
          blurb={SUB_LABELS.ghost_listings.blurb}
          score={bona.ghost_listings.score}
          tier={bona.ghost_listings.tier}
          extra={
            bona.ghost_listings.ghost_count > 0
              ? `${bona.ghost_listings.ghost_count} flagged`
              : undefined
          }
        />
        <BonaSub
          title={SUB_LABELS.programme_leakage.title}
          blurb={SUB_LABELS.programme_leakage.blurb}
          score={bona.programme_leakage.score}
          tier={bona.programme_leakage.tier}
        />
      </div>

      {bona.flags.length > 0 && (
        <div className="mt-3">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-clay-700">
            Flags
          </h4>
          <ul className="mt-1 space-y-1">
            {bona.flags.map((flag, i) => (
              <li
                key={i}
                className="rounded-md bg-white/70 px-2 py-1 text-[11px] leading-snug text-clay-700 ring-1 ring-clay-200/60"
              >
                <span aria-hidden className="mr-1 text-clay-400">·</span>
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {bona.sources.length > 0 && (
        <p className="mt-3 text-[10px] uppercase tracking-wider text-clay-600">
          Sources: {bona.sources.join(' · ')}
        </p>
      )}
    </section>
  );
}

interface SubProps {
  title: string;
  blurb: string;
  score: number;
  tier: BonaTier;
  extra?: string;
}

function BonaSub({ title, blurb, score, tier, extra }: SubProps) {
  const t = TIER_STYLE[tier];
  const pct = Math.round(score * 100);
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-semibold text-clay-800">{title}</span>
        <span className={`pill text-[10px] ${t.chip}`}>{t.label}</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${title} score`}
        className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-clay-100"
      >
        <div
          className={`h-full ${t.bar} transition-[width] duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-1 text-[11px] leading-snug text-clay-600">{blurb}</p>
      {extra && (
        <p className="mt-0.5 text-[10px] font-mono text-clay-500">{extra}</p>
      )}
    </div>
  );
}