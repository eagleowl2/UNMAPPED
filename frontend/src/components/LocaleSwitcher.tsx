import { LOCALES } from '@/lib/locales';
import type { CountryCode } from '@/lib/types';

interface Props {
  value: CountryCode;
  onChange: (next: CountryCode) => void;
}

export function LocaleSwitcher({ value, onChange }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Select country profile"
      className="inline-flex rounded-full bg-white/70 p-1 ring-1 ring-clay-200/70 shadow-sm"
    >
      {Object.values(LOCALES).map((loc) => {
        const active = loc.code === value;
        return (
          <button
            key={loc.code}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(loc.code)}
            className={[
              'rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors',
              active
                ? 'bg-clay-900 text-clay-50 shadow-sm'
                : 'text-clay-700 hover:bg-clay-100',
            ].join(' ')}
          >
            <span aria-hidden className="mr-1.5">
              {loc.flag}
            </span>
            {loc.name}
          </button>
        );
      })}
    </div>
  );
}
