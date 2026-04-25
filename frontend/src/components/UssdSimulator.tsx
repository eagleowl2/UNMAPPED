import { useState } from 'react';
import type { LocaleConfig } from '@/lib/locales';

interface Props {
  locale: LocaleConfig;
  menu: string[];
}

/**
 * USSD interaction simulator. The menu strings come straight from the parser,
 * we just render them in a feature-phone shell and animate the dial-up. No
 * real telephony — judges can interact end-to-end without a SIM.
 */
export function UssdSimulator({ locale, menu }: Props) {
  const [dialed, setDialed] = useState(false);

  return (
    <div className="card p-4">
      <header className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-clay-800">USSD demo</h3>
        <button
          type="button"
          onClick={() => setDialed((d) => !d)}
          className="pill bg-clay-900 text-clay-50 hover:bg-clay-800"
          aria-pressed={dialed}
        >
          {dialed ? 'Hang up' : `Dial ${locale.ussdShortcode}`}
        </button>
      </header>

      <div className="mx-auto max-w-[260px]">
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
                Press “Dial {locale.ussdShortcode}” to view the feature-phone flow.
              </p>
            )}
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1 px-2">
            {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((k) => (
              <div
                key={k}
                className="rounded-md bg-clay-700 py-1 text-center font-mono text-[11px] text-clay-50/80"
                aria-hidden
              >
                {k}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
