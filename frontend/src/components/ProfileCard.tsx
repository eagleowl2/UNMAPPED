import type { LocaleConfig } from '@/lib/locales';
import type { ParseResponse } from '@/lib/types';
import type { ParseSource } from '@/lib/api';
import { AutomationRisk } from './AutomationRisk';
import { NetworkEntryMap } from './NetworkEntryMap';
import { OwnershipStatement } from './OwnershipStatement';
import { QrSimulation } from './QrSimulation';
import { SignalBar } from './SignalBar';
import { SkillList } from './SkillList';

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

/**
 * v0.2 Section 4.2 profile card. Layout:
 *
 *   ┌─ Header (gradient): pseudonym, headline-ish "country · profile",
 *      meta pills (parser source / latency / version / skill count),
 *      QR for the share link.
 *   ├─ Hero row: the two econometric signals — Wage and Growth —
 *      side by side, with their own gradient cards.
 *   ├─ Body: 2-column. Left = languages, network entry map, ownership
 *      statement. Right = skills list with confidence bars.
 *   └─ (SMS / USSD live outside this card in the App, controlled by the
 *      ConstraintTierSwitcher.)
 */
export function ProfileCard({ locale, data, source }: Props) {
  const { profile, latency_ms, parser_version } = data;
  const badge = SOURCE_BADGE[source];

  return (
    <article
      aria-label={`Profile card for ${profile.pseudonym}`}
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
              {profile.pseudonym}
              {profile.age !== undefined && (
                <span className="ml-2 text-base font-medium text-clay-600">
                  · {profile.age}
                </span>
              )}
            </h2>
            <p className="text-sm text-clay-700">{profile.location}</p>
          </div>
          <QrSimulation profileId={profile.profile_id} />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className={`pill ${badge.tone}`}>{badge.label}</span>
          <span className="pill bg-clay-100 text-clay-700">
            <span aria-hidden>⚡</span> {Math.round(latency_ms)} ms
          </span>
          <span className="pill bg-clay-100 text-clay-700 font-mono">{parser_version}</span>
          <span className="pill bg-clay-100 text-clay-700">
            {profile.skills.length} skill{profile.skills.length === 1 ? '' : 's'}
          </span>
        </div>
      </header>

      {/* Hero row — two econometric signals */}
      <section
        aria-label="Econometric signals"
        className="grid gap-3 border-t border-clay-100 px-5 py-4 sm:grid-cols-2 sm:px-7 sm:py-5"
      >
        <SignalBar label="Wage signal" signal={profile.wage_signal} tone="wage" variant="hero" />
        <SignalBar
          label="Growth signal"
          signal={profile.growth_signal}
          tone="growth"
          variant="hero"
        />
      </section>

      {/* Body — two columns */}
      <div className="grid gap-5 border-t border-clay-100 px-5 py-5 sm:grid-cols-2 sm:px-7 sm:py-6">
        <section aria-label="Languages and network entry" className="space-y-4">
          {profile.languages.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-clay-800">Languages</h3>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {profile.languages.map((l) => (
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
              {profile.network_entry.channel}
            </p>
            <div className="mt-2">
              <NetworkEntryMap locale={locale} entry={profile.network_entry} />
            </div>
          </div>

          <OwnershipStatement
            pseudonym={profile.pseudonym}
            profileId={profile.profile_id}
          />
        </section>

        <section aria-label="Skills">
          <h3 className="text-sm font-semibold text-clay-800">
            Skills <span className="text-xs font-normal text-clay-500">(parser-detected)</span>
          </h3>
          <div className="mt-2">
            <SkillList skills={profile.skills} />
          </div>
        </section>
      </div>

      {profile.automation_risk && (
        <div className="border-t border-clay-100 px-5 py-4 sm:px-7 sm:py-5">
          <AutomationRisk risk={profile.automation_risk} />
        </div>
      )}

      {profile.neet_context && (
        <div className="border-t border-clay-100 bg-clay-50/30 px-5 py-3 sm:px-7 sm:py-4">
          <p className="text-xs leading-snug text-clay-700">
            <span className="font-semibold text-clay-800">Local context · </span>
            {profile.neet_context.narrative}
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-wider text-clay-600">
            Source: {profile.neet_context.source} · {profile.neet_context.year}
          </p>
        </div>
      )}
    </article>
  );
}
