interface Props {
  pseudonym: string;
  hlId: string;
}

/**
 * Section 4.2 ownership statement. The user owns their VSS bundle: it is
 * portable, revocable, and never silently shared. This component renders
 * that promise visibly inside the profile card.
 */
export function OwnershipStatement({ pseudonym, hlId }: Props) {
  return (
    <aside
      aria-label="Ownership and control"
      className="rounded-xl border border-clay-200/70 bg-clay-50/70 p-3 text-xs text-clay-700"
    >
      <p className="mb-1 font-semibold text-clay-800">
        <span aria-hidden>🛡️</span> This profile belongs to {pseudonym}.
      </p>
      <p className="leading-snug">
        Generated from {pseudonym}&rsquo;s own words. Portable across SMS, USSD, and the
        formal economy. Shareable only with the holder&rsquo;s consent — and revocable at
        any time.
      </p>
      <p className="mt-1 font-mono text-[10px] text-clay-500">{hlId}</p>
    </aside>
  );
}
