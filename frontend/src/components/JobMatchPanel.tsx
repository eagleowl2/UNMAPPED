import type { JobMatchSignal, OpportunityEntry } from '@/lib/types';

interface Props {
  jobMatch: JobMatchSignal;
}

const EMPLOYER_BADGE: Record<string, string> = {
  government: 'bg-sky-100 text-sky-700',
  cooperative: 'bg-emerald-100 text-emerald-700',
  ngo: 'bg-violet-100 text-violet-700',
  platform: 'bg-orange-100 text-orange-700',
  sme: 'bg-amber-100 text-amber-700',
};

const SCORE_COLOR = (pct: number) =>
  pct >= 0.7 ? 'bg-signal-growth' : pct >= 0.5 ? 'bg-signal-wage' : 'bg-clay-300';

const TIER_LABEL = (score: number) =>
  score >= 70 ? 'High alignment' : score >= 45 ? 'Moderate alignment' : 'Early-stage match';

const TIER_COLOR = (score: number) =>
  score >= 70 ? 'text-signal-growth' : score >= 45 ? 'text-signal-wage' : 'text-clay-500';

export function JobMatchPanel({ jobMatch }: Props) {
  const { score, rationale, opportunity_count, matched_opportunities } = jobMatch;
  const pct = Math.max(0, Math.min(100, score));
  const top3 = matched_opportunities.slice(0, 3);

  return (
    <section
      aria-label="Job-match signal"
      className="border-t border-clay-100 px-5 py-4 sm:px-7 sm:py-5"
    >
      <div className="rounded-xl bg-gradient-to-br from-sky-500/10 to-sky-500/0 p-4 ring-1 ring-clay-200/70">
        {/* Header row */}
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-clay-700">
            <span aria-hidden className="mr-1.5">🎯</span>
            Job-match signal
          </h3>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-xs font-medium text-clay-500">
              {opportunity_count} opportunit{opportunity_count === 1 ? 'y' : 'ies'}
            </span>
            <span className={`font-mono text-2xl font-bold ${TIER_COLOR(score)}`}>
              {pct}
              <span className="text-xs font-medium text-clay-500">/100</span>
            </span>
          </div>
        </div>

        {/* Score bar */}
        <div
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Job-match score"
          className="mt-2 h-2 w-full overflow-hidden rounded-full bg-clay-100"
        >
          <div
            className={`h-full ${SCORE_COLOR(pct / 100)} transition-[width] duration-700 ease-out`}
            style={{ width: `${pct}%` }}
          />
        </div>

        <p className="mt-2 text-xs leading-snug text-clay-600">{rationale}</p>

        {/* Opportunity list */}
        {top3.length > 0 && (
          <ul className="mt-3 space-y-2">
            {top3.map((opp, i) => (
              <OpportunityRow key={opp.isco_code + i} opp={opp} rank={i + 1} />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function OpportunityRow({ opp, rank }: { opp: OpportunityEntry; rank: number }) {
  const matchPct = Math.round(opp.match_score * 100);
  const badgeTone = EMPLOYER_BADGE[opp.employer_type] ?? 'bg-clay-100 text-clay-700';

  return (
    <li className="rounded-lg bg-white/70 px-3 py-2.5 ring-1 ring-clay-200/60">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-clay-500">#{rank}</span>
            <span className={`pill text-[10px] ${badgeTone}`}>{opp.employer_type}</span>
          </div>
          <p className="mt-0.5 text-xs font-semibold leading-snug text-clay-800">{opp.title}</p>
          <p className="mt-0.5 text-[10px] font-mono text-clay-500">{opp.wage_range}</p>
        </div>
        <div className="flex-shrink-0 text-right">
          <span className={`font-mono text-sm font-bold ${TIER_COLOR(matchPct)}`}>
            {matchPct}%
          </span>
        </div>
      </div>

      {/* Mini score bar */}
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-clay-100">
        <div
          className={`h-full ${SCORE_COLOR(opp.match_score)} transition-[width] duration-500`}
          style={{ width: `${matchPct}%` }}
        />
      </div>

      <details className="mt-1.5 group">
        <summary className="cursor-pointer select-none text-[10px] font-medium text-clay-500 hover:text-clay-700 list-none flex items-center gap-1">
          <span className="group-open:hidden">▶ Formalization path</span>
          <span className="hidden group-open:inline">▼ Formalization path</span>
        </summary>
        <p className="mt-1 text-[10px] leading-relaxed text-clay-600">{opp.formalization_path}</p>
      </details>
    </li>
  );
}
