// Matn maydoni: yozish lokal (tez), serverga — Enter / fokus chiqishi / 0.7 s pauzadan keyin.
import { useEffect, useRef, useState } from "react";

export function LazyInput({ value, onCommit, className, placeholder, testid, list, disabled }: {
  value: string; onCommit: (v: string) => void; className?: string; placeholder?: string; testid?: string; disabled?: boolean;
  /** `<datalist>` id — avtoto'ldirish takliflari (masalan, asboblar jadvalidan T / N nomlari) */
  list?: string;
}) {
  const [v, setV] = useState(value);
  const [focused, setFocused] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const last = useRef(value);
  useEffect(() => { if (!focused) { setV(value); last.current = value; } }, [value, focused]);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const commit = (nv: string) => {
    window.clearTimeout(timer.current);
    if (nv !== last.current) { last.current = nv; onCommit(nv); }
  };
  return (
    <input className={className} placeholder={placeholder} value={v} data-testid={testid} list={list} disabled={disabled}
      onFocus={() => setFocused(true)}
      onBlur={() => { setFocused(false); commit(v); }}
      onChange={(e) => {
        const nv = e.target.value;
        setV(nv);
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => commit(nv), 700);
      }}
      onKeyDown={(e) => { if (e.key === "Enter") commit(v); }} />
  );
}

/** Kiritilgan matn: son bo'lsa son, aks holda ifoda (satr). */
export function parseParam(raw: string): string | number {
  const n = Number(raw.replace(",", "."));
  return raw.trim() !== "" && !Number.isNaN(n) ? n : raw;
}
