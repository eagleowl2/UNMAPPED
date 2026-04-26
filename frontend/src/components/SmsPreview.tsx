import type { LocaleConfig } from '@/lib/locales';

interface Props {
  locale: LocaleConfig;
  message: string;
  /** When true, render the standalone Constraint Tier framing (full-card mode). */
  emphasized?: boolean;
}

const SMS_LIMIT = 160;

export function SmsPreview({ locale, message, emphasized }: Props) {
  const segments = Math.max(1, Math.ceil(message.length / SMS_LIMIT));

  return (
    <div className={emphasized ? 'card p-5' : 'card p-4'}>
      <header className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-clay-800">
          {emphasized ? 'Tier 2 — SMS' : 'SMS fallback'}
        </h3>
        <span className="pill bg-clay-100 text-clay-700">
          {message.length} chars · {segments} segment{segments > 1 ? 's' : ''}
        </span>
      </header>

      <div className="rounded-2xl bg-clay-50 p-3">
        <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-clay-500">
          From {locale.smsSender}
        </div>
        <div className="rounded-2xl rounded-tl-sm bg-white p-3 shadow-sm ring-1 ring-clay-200/60">
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-clay-900">
            {message}
          </p>
        </div>
        <div className="mt-1 text-right text-[10px] text-clay-500">delivered · 2G safe</div>
      </div>

      {emphasized && (
        <p className="mt-3 text-xs leading-snug text-clay-600">
          What every UNMAPPED user can receive on any handset, in any signal
          condition. One SMS, ≤ {SMS_LIMIT} characters per segment, no
          smartphone required.
        </p>
      )}
    </div>
  );
}
