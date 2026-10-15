// Ifoda kiritish maydoni (redaktor): joriy qiymat mahalliy holatda, Enter/blur da saqlanadi; xato — qizil; «ƒ» — ExprHelper oynasi;
// o'zgaruvchilar paneli shu maydonga kursor o'rniga matn qo'yadi (`fxFocus`).
import { useEffect, useRef, useState } from "react";
import { cx } from "../../../shared/ui";

/** Fokusdagi ifoda maydoni: «Переменные» paneli bosilganda matn shu yerga qo'yiladi (yo'q bo'lsa — nusxa olinadi). */
export const fxFocus: { cur: { insert: (text: string) => void } | null } = { cur: null };

interface Props {
  value: string; onCommit: (v: string) => void; error?: string; multiline?: boolean; rows?: number; testid?: string; placeholder?: string;
  onFx?: (current: string, apply: (v: string) => void) => void; width?: number | string; className?: string; mono?: boolean; disabled?: boolean;
}

export function FxInput({ value, onCommit, error, multiline, rows = 2, testid, placeholder, onFx, width, className, mono, disabled }: Props) {
  const [s, setS] = useState(value);
  const ref = useRef<HTMLInputElement & HTMLTextAreaElement>(null);
  const latest = useRef({ s, value, onCommit });
  latest.current = { s, value, onCommit };
  useEffect(() => { setS(value); }, [value]);

  const commit = (v?: string) => {
    const nv = v ?? latest.current.s;
    if (nv !== latest.current.value) latest.current.onCommit(nv);
  };
  const api = useRef({
    insert: (text: string) => {
      const el = ref.current;
      const cur = latest.current.s;
      const a = el?.selectionStart ?? cur.length, b = el?.selectionEnd ?? cur.length;
      const nv = cur.slice(0, a) + text + cur.slice(b);
      setS(nv);
      latest.current.onCommit(nv);
      requestAnimationFrame(() => { el?.focus(); el?.setSelectionRange(a + text.length, a + text.length); });
    },
  });
  useEffect(() => () => { if (fxFocus.cur === api.current) fxFocus.cur = null; }, []);

  const common = {
    ref, value: s, placeholder, disabled, spellCheck: false as const, "data-testid": testid, title: error,
    className: cx("inp", "lbd-fx", error && "lbd-fx-err", mono && "lbd-mono", className),
    style: { width },
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setS(e.target.value),
    onFocus: () => { fxFocus.cur = api.current; },
    onBlur: () => { commit(); setTimeout(() => { if (fxFocus.cur === api.current && document.activeElement !== ref.current) fxFocus.cur = null; }, 250); },
  };
  return (
    <span className={cx("lbd-fxw", multiline && "lbd-fxw-ml")}>
      {multiline
        ? <textarea {...common} rows={rows} onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); commit(); } if (e.key === "Escape") { setS(value); } }} />
        : <input {...common} onKeyDown={(e) => { if (e.key === "Enter") { commit(); (e.target as HTMLInputElement).select(); } if (e.key === "Escape") { setS(value); } }} />}
      {onFx && (
        <button type="button" className="lbd-fxbtn" tabIndex={-1} title="ƒ" data-testid={testid ? `${testid}-fx` : undefined}
          onMouseDown={(e) => e.preventDefault()} onClick={() => onFx(s, (v) => { setS(v); onCommit(v); })}>ƒ</button>
      )}
    </span>
  );
}
