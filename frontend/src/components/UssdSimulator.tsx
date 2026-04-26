import { useState } from 'react';
import type { LocaleConfig } from '@/lib/locales';

interface Props {
  locale: LocaleConfig;
  menu: string[];
  /** When true, render the standalone Constraint Tier framing (full-card mode). */
  emphasized?: boolean;
}

/**
 * USSD interaction simulator. Renders the parser-supplied flat `ussd_menu`
 * array in a feature-phone shell. Pure DOM, no telephony — judges navigate
 * end-to-end without a SIM.
 */
export function UssdSimulator({ locale, menu, emphasized }: Props) {
  const [dialed, setDialed] = useState(false);

  return (
    <div className={emphasized ? 'card p-5' : 'card p-4'}>
      <header className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-clay-800">
          {emphasized ? 'Tier 3 — USSD' : 'USSD demo'}
        </h3>
        <button
          type="button"
          onClick={() => setDialed((d) => !d)}
          className="pill bg-clay-900 text-clay-50 hover:bg-clay-800"
          aria-pressed={dialed}
        >
          {dialed ? 'Hang up' : `Dial ${locale.ussdShortcode}`}
        </button>
      </header>

      <div className="mx-auto max-w-[280px]">
        <div className="rounded-[28px] bg-clay-900 p-3 shadow-card">
          <div className="rounded-2xl bg-clay-50 p-3">
            <div className="mb-1.5 flex items-center justify-between text-[10px] text-clay-600">
              <span>{locale.flag} Network</span>
              <span aria-hidden>▮▮▮▯</span>
            </div>
            {dialed ? (
              <pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-snug text-clay-900">
                {menu.join('\n')}
              </pre>
            ) : (
              <p className="font-mono text-[12px] text-clay-500">
                Press &ldquo;Dial {locale.ussdShortcode}&rdquo; to view the feature-phone flow.
              </p>
            )}
          </div>
          <div aria-hidden className="mt-2 grid grid-cols-3 gap-1 px-2">
            {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((k) => (
              <div
                key={k}
                className="rounded-md bg-clay-700 py-1 text-center font-mono text-[11px] text-clay-50/80"
              >
                {k}
              </div>
            ))}
          </div>
        </div>
      </div>

      {emphasized && (
        <p className="mt-3 text-xs leading-snug text-clay-600">
          What every UNMAPPED user can navigate on a feature phone in any
          signal condition. ≤ 8 lines, ≤ 40 chars per line, works at 2G.
        </p>
      )}
    </div>
  );
}
