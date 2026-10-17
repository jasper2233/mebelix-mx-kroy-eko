// Sichqonchaning o'ng tugmasi menyusi (jadvallar uchun): mavjud amallar va ularning yorliqlari (Del, Ctrl+K …) ko'rsatiladi.
// O'ng tugma tanlovni o'zgartirmaydi; menyu tashqarida bosilganda, Esc yoki aylantirishda yopiladi.
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import "./contextMenu.css";

export interface CtxItem {
  label: ReactNode;
  /** yorliq (masalan «Ctrl+K») — o'ng tomonda kulrang */
  hint?: string;
  onClick?: () => void;
  disabled?: boolean;
  testid?: string;
  /** ajratuvchi chiziq (bu element o'rniga) */
  sep?: boolean;
}

export function ContextMenu({ x, y, items, onClose, testid }: { x: number; y: number; items: CtxItem[]; onClose: () => void;
  testid?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ left: x, top: y });
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    // ekran chetidan chiqmasin
    const w = el.offsetWidth, h = el.offsetHeight;
    setPos({ left: Math.max(2, Math.min(x, window.innerWidth - w - 2)), top: Math.max(2, Math.min(y, window.innerHeight - h - 2)) });
  }, [x, y]);
  useEffect(() => {
    const down = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) onClose(); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onClose(); } };
    const close = () => onClose();
    window.addEventListener("mousedown", down, true);
    window.addEventListener("keydown", key, true);
    window.addEventListener("blur", close);
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("mousedown", down, true);
      window.removeEventListener("keydown", key, true);
      window.removeEventListener("blur", close);
      window.removeEventListener("resize", close);
    };
  }, [onClose]);
  return createPortal(
    <div ref={ref} className="ctx-menu" style={pos} data-testid={testid ?? "ctx-menu"} role="menu"
      onContextMenu={(e) => { e.preventDefault(); e.stopPropagation(); }}>
      {items.map((it, i) => it.sep
        ? <div key={i} className="ctx-sep" />
        : (
          <button key={i} type="button" role="menuitem" className="ctx-item" disabled={it.disabled} data-testid={it.testid}
            onClick={() => { onClose(); it.onClick?.(); }}>
            <span className="ctx-label">{it.label}</span>
            {it.hint && <span className="ctx-hint">{it.hint}</span>}
          </button>
        ))}
    </div>,
    document.body,
  );
}

/** O'ng tugma menyusi holati: `open(e)` — sichqoncha o'rnida ochish, `node` — ko'rsatiladigan element (yopiq bo'lsa null). */
export function useContextMenu(items: () => CtxItem[], testid?: string) {
  const [at, setAt] = useState<{ x: number; y: number } | null>(null);
  const close = useRef(() => setAt(null)).current;
  const open = (e: { clientX: number; clientY: number; preventDefault: () => void }) => {
    e.preventDefault();
    setAt({ x: e.clientX, y: e.clientY });
  };
  const node = at ? <ContextMenu x={at.x} y={at.y} items={items()} onClose={close} testid={testid} /> : null;
  return { open, node, close };
}
