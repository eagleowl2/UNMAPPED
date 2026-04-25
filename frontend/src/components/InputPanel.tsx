import { useEffect, useRef, useState } from 'react';
import type { LocaleConfig } from '@/lib/locales';

interface Props {
  locale: LocaleConfig;
  value: string;
  onChange: (next: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

const SUBMIT_HOTKEY_HINT = 'Cmd/Ctrl + Enter';

export function InputPanel({ locale, value, onChange, onSubmit, loading }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [chars, setChars] = useState(value.length);

  useEffect(() => setChars(value.length), [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <section
      aria-labelledby="input-heading"
      className="card p-5 sm:p-7"
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 id="input-heading" className="text-base font-semibold text-clay-800">
          Tell us about yourself
        </h2>
        <button
          type="button"
          onClick={() => onChange(locale.sample)}
          className="text-xs font-medium text-clay-600 underline-offset-4 hover:underline"
        >
          {locale.sampleLabel}
        </button>
      </div>

      <label htmlFor="raw-input" className="sr-only">
        Raw personal description
      </label>
      <textarea
        id="raw-input"
        ref={ref}
        rows={6}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={locale.placeholder}
        className="
          w-full resize-y rounded-xl border border-clay-200 bg-clay-50/70 p-4
          text-base leading-relaxed text-clay-900 placeholder:text-clay-500
          focus:border-clay-400 focus:bg-white
        "
        spellCheck={false}
      />

      <div className="mt-3 flex flex-col-reverse items-stretch justify-between gap-3 sm:flex-row sm:items-center">
        <p className="text-xs text-clay-600">
          {chars.toLocaleString()} chars · any language · press {SUBMIT_HOTKEY_HINT} to parse
        </p>

        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !value.trim()}
          className="btn-primary"
        >
          {loading ? 'Parsing…' : 'Generate Profile'}
          {!loading && <span aria-hidden>→</span>}
        </button>
      </div>
    </section>
  );
}
