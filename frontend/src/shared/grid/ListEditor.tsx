// Jadval katagi uchun ro'yxat muharriri (kromka, mahsulot, paz): sichqoncha yoki ↑↓ Enter, harf bilan tez tanlash,
// Del / Backspace — tozalash («—»).
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { CustomCellEditorProps } from "ag-grid-react";
import { cx } from "../ui";

export interface ListOption { value: string; label: string; color?: string; key?: string }

/** Katakning haqiqiy joriy qiymati: AG Grid tahrir modeli yaqinda saqlangan katakda eski qiymatni berishi mumkin,
 *  shuning uchun ustunning valueGetter i bilan to'g'ridan-to'g'ri qator ma'lumotidan olinadi. */
function currentValue(props: CustomCellEditorProps): string {
  const vg = props.colDef?.valueGetter;
  if (typeof vg === "function") {
    try {
      return String((vg as (p: unknown) => unknown)({ data: props.data, node: props.node, colDef: props.colDef,
        column: props.column, api: props.api, context: props.context, getValue: () => undefined }) ?? "");
    } catch { /* pastdagiga */ }
  }
  return String(props.value ?? "");
}

export function ListEditor(props: CustomCellEditorProps & { options: ListOption[] }) {
  const opts = props.options ?? [];
  const [i, setI] = useState(() => Math.max(0, opts.findIndex((o) => o.value === currentValue(props))));
  const ref = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  useEffect(() => {
    const el = listRef.current?.children[i] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [i]);
  // «—» (bo'sh) tanlovi null bo'lib yuboriladi: bo'sh satrni grid «o'zgarmadi» deb hisoblab qo'yishi mumkin
  const out = (v: string) => (v === "" ? null : v);
  const move = (k: number) => {
    const j = Math.max(0, Math.min(opts.length - 1, k));
    setI(j);
    props.onValueChange(out(opts[j]?.value ?? ""));
  };
  // tanlangach yopish — grid yangi qiymatni props orqali qaytargandan keyin (aks holda eski qiymat qoladi)
  const [closing, setClosing] = useState(false);
  useEffect(() => { if (closing) props.stopEditing(); }, [closing, props.value]); // eslint-disable-line react-hooks/exhaustive-deps
  const pick = (k: number) => {
    props.onValueChange(out(opts[k]?.value ?? ""));
    setClosing(true);
  };
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "ArrowDown") { move(i + 1); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "ArrowUp") { move(i - 1); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "Enter") { pick(i); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "Delete" || e.key === "Backspace") { setI(0); pick(0); e.preventDefault(); e.stopPropagation(); }
    else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
      const ch = e.key.toLowerCase();
      const start = (i + 1) % Math.max(1, opts.length);
      const order = [...opts.slice(start), ...opts.slice(0, start)];
      const hit = order.find((o) => (o.key ?? o.label).toLowerCase().startsWith(ch));
      if (hit) move(opts.indexOf(hit));
      e.stopPropagation();
    }
  };
  return (
    <div ref={ref} className="list-editor" tabIndex={0} onKeyDown={onKey} data-testid="list-editor" data-hotkeys-off="">
      <div ref={listRef}>
        {opts.map((o, k) => (
          <div key={o.value || "__none"} className={cx("le-item", k === i && "le-active")}
            onMouseDown={(e) => { e.preventDefault(); pick(k); }} onMouseEnter={() => setI(k)}>
            <span className="le-sw" style={{ background: o.color ?? "transparent", borderColor: o.color ? "#0003" : "transparent" }} />
            {o.label}
          </div>
        ))}
      </div>
    </div>
  );
}
