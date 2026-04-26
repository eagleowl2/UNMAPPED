export type ConstraintTier = 'smartphone' | 'sms' | 'ussd';

interface Props {
  value: ConstraintTier;
  onChange: (next: ConstraintTier) => void;
}

const TIERS: Array<{
  key: ConstraintTier;
  label: string;
  hint: string;
  icon: string;
}> = [
  { key: 'smartphone', label: 'Smartphone', hint: 'Tier 1 · 3G/Wi-Fi', icon: '📱' },
  { key: 'sms', label: 'SMS', hint: 'Tier 2 · 2G', icon: '✉️' },
  { key: 'ussd', label: 'USSD', hint: 'Tier 3 · feature phone', icon: '☎️' },
];

/**
 * Constraint-Layer tier switcher. Lets a judge see the same profile collapsed
 * across the three delivery channels — smartphone (full SPA card), SMS (≤160
 * chars), USSD (interactive *789# tree). Demonstrates that UNMAPPED works at
 * every rung of the connectivity ladder.
 */
export function ConstraintTierSwitcher({ value, onChange }: Props) {
  return (
    <div
      role="tablist"
      aria-label="Constraint Layer delivery tier"
      className="card flex flex-col gap-2 p-2 sm:flex-row sm:items-stretch"
    >
      {TIERS.map((t) => {
        const active = t.key === value;
        return (
          <button
            key={t.key}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.key)}
            className={[
              'group flex flex-1 items-center justify-between gap-3 rounded-xl px-4 py-3 text-left transition-colors',
              active
                ? 'bg-clay-900 text-clay-50 shadow-sm'
                : 'bg-transparent text-clay-800 hover:bg-clay-100',
            ].join(' ')}
          >
            <div className="min-w-0">
              <p className="text-sm font-semibold">
                <span aria-hidden className="mr-2 text-base">
                  {t.icon}
                </span>
                {t.label}
              </p>
              <p className={['text-[11px]', active ? 'text-clay-200' : 'text-clay-600'].join(' ')}>
                {t.hint}
              </p>
            </div>
            {active && (
              <span aria-hidden className="text-xs uppercase tracking-wider">
                showing
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
