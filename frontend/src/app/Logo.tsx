// MebeliX Kroy logotipi (o'zimizniki): «M» monogramma + kesish belgisi.
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="logo" title="MebeliX Kroy">
      <svg width="34" height="34" viewBox="0 0 64 64" aria-hidden>
        <rect width="64" height="64" rx="12" fill="#f2a541" />
        <path d="M13 47V17h7l12 17 12-17h7v30h-8V31L32 46 21 31v16z" fill="#123a5c" />
        <path d="M44 44l10 10M54 44L44 54" stroke="#fff" strokeWidth="4.5" strokeLinecap="round" />
      </svg>
      {!compact && (
        <div className="logo-text">
          <span className="logo-name">Mebeli<b>X</b></span>
          <span className="logo-sub">Kroy</span>
        </div>
      )}
    </div>
  );
}
