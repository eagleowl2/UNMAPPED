import type { LocaleConfig } from '@/lib/locales';
import type { ParseResponse } from '@/lib/types';
import type { ParseSource } from '@/lib/api';
import { NetworkEntryMap } from './NetworkEntryMap';
import { OwnershipStatement } from './OwnershipStatement';
import { QrSimulation } from './QrSimulation';
import { SignalBar } from './SignalBar';

interface Props {
  locale: LocaleConfig;
  data: ParseResponse;
  source: ParseSource;
}

const SOURCE_BADGE: Record<ParseSource, { label: string; tone: string }> = {
  live: { label: 'Live parser', tone: 'bg-signal-wage/15 text-signal-wage' },
  'mock-fallback': { label: 'Offline fallback', tone: 'bg-sun-500/15 text-sun-600' },
  demo: { label: 'Demo mode', tone: 'bg-signal-growth/15 text-signal-growth' },
};

export function ProfileCard({ locale, data, source }: Props) {
  const { human_layer, vss_list, meta } = data;
  const card = human_layer.profile_card;
  const badge = SOURCE_BADGE[source];
  const city = card.location || 'Unknown location';

  return (
    <article
      aria-label={`Profile card for ${card.display_name}`}
      className="card overflow-hidden"
    >
      {/* Header */}
      <header className="relative bg-gradient-to-br from-sun-400/30 to-clay-200/30 px-5 py-5 sm:px-7 sm:py-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wider text-clay-700">
              {locale.flag} {locale.name} · Skills Signal Profile
            </p>
            <h2 className="mt-1 text-2xl font-bold text-clay-900 sm:text-3xl">
              {card.display_name}
            </h2>
            <p className="text-sm text-clay-700">{card.headline}</p>

            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {card.zero_credential_badge && (
                <span className="pill bg-sun-500/15 text-sun-600">
                  <span aria-hidden>✦</span> Zero-credential verified
                </span>
              )}
              {card.top_skill && (
                <span className="pill bg-clay-100 text-clay-700">
                  Top: <strong className="ml-1 font-semibold">{card.top_skill}</strong>
                </span>
              )}
            </div>
          </div>
          <QrSimulation hlId={human_layer.hl_id} />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className={`pill ${badge.tone}`}>{badge.label}</span>
          {meta.processing_time_ms !== undefined && (
            <span className="pill bg-clay-100 text-clay-700">
              <span aria-hidden>⚡</span> {Math.round(meta.processing_time_ms)} ms
            </span>
          )}
          {meta.parser_version && (
            <span className="pill bg-clay-100 text-clay-700 font-mono">{meta.parser_version}</span>
          )}
          {meta.skills_detected !== undefined && (
            <span className="pill bg-clay-100 text-clay-700">
              {meta.skills_detected} skill{meta.skills_detected === 1 ? '' : 's'} detected
            </span>
          )}
        </div>
      </header>

      {/* Body */}
      <div className="grid gap-5 px-5 py-5 sm:grid-cols-2 sm:px-7 sm:py-6">
        <section aria-label="Bio and languages" className="space-y-4">
          {card.bio_snippet && (
            <p className="text-sm leading-relaxed text-clay-800">{card.bio_snippet}</p>
          )}

          {card.languages && card.languages.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-clay-800">Languages</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {card.languages.map((l) => (
                  <span key={l} className="pill bg-clay-100 text-clay-800">
                    {l}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="text-sm font-semibold text-clay-800">Network entry</h3>
            <p className="mt-1 text-xs leading-snug text-clay-600">
              Where this profile most-naturally crosses into the formal economy:
            </p>
            <div className="mt-2">
              <NetworkEntryMap locale={locale} city={city} />
            </div>
          </div>

          <OwnershipStatement pseudonym={card.display_name} hlId={human_layer.hl_id} />
        </section>

        <section aria-label="Skills and confidence" className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-clay-800">
              Skills <span className="text-xs font-normal text-clay-500">(Bayesian confidence)</span>
            </h3>
            <ul className="mt-2 space-y-3">
              {card.skills_summary.map((s) => (
                <li key={s.label} className="rounded-lg bg-clay-50 px-3 py-2.5">
                  <SignalBar entry={s} />
                </li>
              ))}
            </ul>
          </div>

          {vss_list && vss_list.length > 0 && (
            <details className="group rounded-lg bg-clay-50 px-3 py-2 text-xs text-clay-700">
              <summary className="cursor-pointer select-none font-medium text-clay-800 outline-none">
                Evidence chain ({vss_list.length} VSS)
              </summary>
              <ul className="mt-2 space-y-2">
                {vss_list.map((v) => (
                  <li key={v.vss_id} className="rounded-md bg-white p-2 ring-1 ring-clay-200/60">
                    <p className="text-sm font-medium text-clay-900">
                      {v.skill.label}
                      <span className="ml-2 font-mono text-[10px] text-clay-500">
                        {v.taxonomy_crosswalk.primary.framework}:{v.taxonomy_crosswalk.primary.code}
                      </span>
                    </p>
                    <ul className="mt-1 space-y-0.5">
                      {v.evidence_chain.slice(0, 3).map((e, i) => (
                        <li key={i} className="text-[11px] leading-snug text-clay-600">
                          <span className="font-mono text-clay-500">{e.evidence_type}</span>{' '}
                          · &ldquo;{e.raw_signal}&rdquo;{' '}
                          <span className="font-mono text-clay-500">w={e.weight.toFixed(2)}</span>
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
      </div>
    </article>
  );
}
