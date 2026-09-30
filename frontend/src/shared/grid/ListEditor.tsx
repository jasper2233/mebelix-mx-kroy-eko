// Jadval katagi uchun ro'yxat muharriri (kromka, mahsulot, paz): sichqoncha yoki ↑↓ Enter, harf bilan tez tanlash.
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { CustomCellEditorProps } from "ag-grid-react";
import { cx } from "../ui";

export interface ListOption { value: string; label: string; color?: string; key?: string }

export function ListEditor(props: CustomCellEditorProps & { options: ListOption[] }) {
  const opts = props.options ?? [];
  const [i, setI] = useState(() => Math.max(0, opts.findIndex((o) => o.value === (props.value ?? ""))));
  const ref = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  useEffect(() => {
    const el = listRef.current?.children[i] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [i]);
  const move = (k: number) => {
    const j = Math.max(0, Math.min(opts.length - 1, k));
    setI(j);
    props.onValueChange(opts[j]?.value ?? "");
  };
  const pick = (k: number) => {
    props.onValueChange(opts[k]?.value ?? "");
    props.stopEditing();
  };
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "ArrowDown") { move(i + 1); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "ArrowUp") { move(i - 1); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "Enter") { pick(i); e.preventDefault(); e.stopPropagation(); }
    else if (e.key === "Delete" || e.key === "Backspace") { pick(0); e.preventDefault(); e.stopPropagation(); }
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
    <div ref={ref} className="list-editor" tabIndex={0} onKeyDown={onKey} data-testid="list-editor">
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
