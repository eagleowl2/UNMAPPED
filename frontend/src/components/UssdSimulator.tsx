import { useState } from 'react';
import type { LocaleConfig } from '@/lib/locales';
import type { UssdNode, UssdTree } from '@/lib/types';

interface Props {
  locale: LocaleConfig;
  tree: UssdTree;
  /** When true, render the standalone Constraint Tier framing (full-card mode). */
  emphasized?: boolean;
}

/**
 * Interactive USSD-tree navigator. Renders the parser-supplied tree node by
 * node — tap a numeric option, advance to the child node, "0" to go back.
 * Pure DOM, no telephony — judges navigate end-to-end without a SIM.
 */
export function UssdSimulator({ locale, tree, emphasized }: Props) {
  const [stack, setStack] = useState<UssdNode[]>([]);
  const [dialed, setDialed] = useState(false);

  const current = stack[stack.length - 1] ?? tree.root;

  const dial = () => {
    setDialed(true);
    setStack([tree.root]);
  };
  const hangUp = () => {
    setDialed(false);
    setStack([]);
  };
  const choose = (next: UssdNode) => setStack((s) => [...s, next]);
  const back = () => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s));

  return (
    <div className={emphasized ? 'card p-5' : 'card p-4'}>
      <header className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-clay-800">
          {emphasized ? 'Tier 3 — USSD' : 'USSD demo'}
        </h3>
        <button
          type="button"
          onClick={dialed ? hangUp : dial}
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
              <div>
                <pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-snug text-clay-900">
                  {current.text}
                </pre>

                {current.options && current.options.length > 0 && (
                  <div className="mt-2 flex flex-col gap-1">
                    {current.options.map((opt) => (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => choose(opt.next)}
                        className="rounded-md bg-clay-900 px-2 py-1 text-left font-mono text-[11px] text-clay-50 hover:bg-clay-800"
                      >
                        {opt.key}. {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                {stack.length > 1 && (
                  <button
                    type="button"
                    onClick={back}
                    className="mt-2 w-full rounded-md bg-clay-200 px-2 py-1 font-mono text-[11px] text-clay-800 hover:bg-clay-300"
                  >
                    0. Back
                  </button>
                )}
              </div>
            ) : (
              <p className="font-mono text-[12px] text-clay-500">
                Press &ldquo;Dial {locale.ussdShortcode}&rdquo; to enter the feature-phone flow.
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
          signal condition. Tree depth ≤ 3, each node ≤ 182 chars, session
          timeout {tree.session_timeout_sec ?? 180} s.
        </p>
      )}
    </div>
  );
}
