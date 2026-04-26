import { useCallback, useEffect, useMemo, useState } from 'react';
import { ConstraintTierSwitcher, type ConstraintTier } from './components/ConstraintTierSwitcher';
import { InputPanel } from './components/InputPanel';
import { LocaleSwitcher } from './components/LocaleSwitcher';
import { ProfileCard } from './components/ProfileCard';
import { SmsPreview } from './components/SmsPreview';
import { UssdSimulator } from './components/UssdSimulator';
import { parse, type ParseSource } from './lib/api';
import { DEFAULT_LOCALE, LOCALES, type LocaleConfig } from './lib/locales';
import { storage } from './lib/storage';
import type { CountryCode, ParseResponse } from './lib/types';

export function App() {
  const [country, setCountry] = useState<CountryCode>(() => {
    const saved = storage.loadLocale();
    return saved === 'GH' || saved === 'AM' ? saved : DEFAULT_LOCALE;
  });
  // Per protocol §5.4 / Master Context §6.5: raw_input and the parse
  // result are PII. They are NEVER persisted to localStorage. Both live
  // only in component state and are cleared on tab close / refresh.
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorTrace, setErrorTrace] = useState<string[] | null>(null);
  const [data, setData] = useState<ParseResponse | null>(null);
  const [source, setSource] = useState<ParseSource>('live');
  const [tier, setTier] = useState<ConstraintTier>('smartphone');

  const locale = useMemo(() => LOCALES[country], [country]);

  useEffect(() => storage.saveLocale(country), [country]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setError(null);
    setErrorTrace(null);
    try {
      const { result, source: src } = await parse({
        raw_input: input,
        country,
      });
      if (result.ok) {
        setData(result);
        setSource(src);
      } else {
        setError(result.error);
        setErrorTrace(result.traceback_tail ?? null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected parser error');
    } finally {
      setLoading(false);
    }
  }, [input, country, loading]);

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
      <Header country={country} setCountry={setCountry} />

      <main className="mt-6 grid gap-6">
        <InputPanel
          locale={locale}
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {error && (
          <div
            role="alert"
            className="card border border-signal-risk/30 bg-signal-risk/5 p-4 text-sm text-signal-risk"
          >
            <p className="font-semibold">{error}</p>
            {errorTrace && errorTrace.length > 0 && (
              <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-clay-900/5 p-2 font-mono text-[11px] leading-snug text-clay-800">
                {errorTrace.join('\n')}
              </pre>
            )}
          </div>
        )}

        {data?.profile?.sms_summary ? (
          <>
            <ConstraintTierSwitcher value={tier} onChange={setTier} />
            <TierView locale={locale} data={data} source={source} tier={tier} />
          </>
        ) : (
          <EmptyState />
        )}
      </main>

      <Footer />
    </div>
  );
}

function TierView({
  locale,
  data,
  source,
  tier,
}: {
  locale: LocaleConfig;
  data: ParseResponse;
  source: ParseSource;
  tier: ConstraintTier;
}) {
  if (tier === 'sms') {
    return <SmsPreview locale={locale} message={data.profile.sms_summary} emphasized />;
  }
  if (tier === 'ussd') {
    return <UssdSimulator locale={locale} menu={data.profile.ussd_menu} emphasized />;
  }
  return (
    <>
      <ProfileCard locale={locale} data={data} source={source} />
      <div className="grid gap-4 sm:grid-cols-2">
        <SmsPreview locale={locale} message={data.profile.sms_summary} />
        <UssdSimulator locale={locale} menu={data.profile.ussd_menu} />
      </div>
    </>
  );
}

function Header({
  country,
  setCountry,
}: {
  country: CountryCode;
  setCountry: (c: CountryCode) => void;
}) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-clay-700">
          UNMAPPED Protocol
        </p>
        <h1 className="mt-1 text-3xl font-bold text-clay-900 sm:text-4xl">
          Skills Signal Engine
        </h1>
        <p className="mt-1 max-w-xl text-sm text-clay-700">
          Paste a chaotic story in any language. Get a portable profile with
          two econometric signals — wage and growth — that work on a smartphone,
          a feature phone, and the formal economy.
        </p>
      </div>
      <LocaleSwitcher value={country} onChange={setCountry} />
    </header>
  );
}

function EmptyState() {
  return (
    <section className="card flex flex-col items-center justify-center gap-2 p-10 text-center">
      <div className="text-4xl" aria-hidden>
        ✨
      </div>
      <h3 className="text-base font-semibold text-clay-800">No profile yet</h3>
      <p className="max-w-sm text-sm text-clay-600">
        Type or paste anything above and hit <kbd className="font-mono">Generate Profile</kbd>.
        It works in any language, online or offline.
      </p>
    </section>
  );
}

function Footer() {
  return (
    <footer className="mt-12 border-t border-clay-200/70 pt-4 text-center text-xs text-clay-600">
      v0.3.0-sse-alpha.4 · UNMAPPED Protocol · Hackathon demo · Built for low-bandwidth users
    </footer>
  );
}
