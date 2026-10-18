// Sichqonchaning o'ng tugmasi menyusi (jadvallar uchun): mavjud amallar va ularning yorliqlari ([DEL], [CTRL]+[K] …) ko'rsatiladi.
// O'ng tugma tanlovni o'zgartirmaydi; menyu tashqarida bosilganda, Esc yoki aylantirishda yopiladi.
// Ko'rinish xodimlar o'rgangan menyudek: 11pt (14.67px) ko'k yozuv, har bandda 16px ikonka joyi, yorliq «[CTRL]+[PAGE DOWN]».
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { LucideIcon } from "lucide-react";
import { fmtKeys, splitKeys } from "../keyLabel";
import "./contextMenu.css";

export interface CtxItem {
  label: ReactNode;
  /** yorliq (masalan «Ctrl+K») — o'ng tomonda; «[CTRL]+[K]» ko'rinishida chiqadi */
  hint?: string;
  /** chapdagi 16px ikonka (bo'lmasa — bo'sh joy, yozuvlar bir chiziqda) */
  icon?: LucideIcon;
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
  // ketma-ket / boshida / oxirida turgan ajratuvchilar ko'rsatilmaydi (bandlar shartli bo'lsa ham chiziqlar toza qoladi)
  const shown = items.filter((it, i, a) => !it.sep || (i > 0 && i < a.length - 1 && !a[i - 1].sep));
  return createPortal(
    <div ref={ref} className="ctx-menu" style={pos} data-testid={testid ?? "ctx-menu"} role="menu"
      onContextMenu={(e) => { e.preventDefault(); e.stopPropagation(); }}>
      {shown.map((it, i) => {
        if (it.sep) return <div key={i} className="ctx-sep" />;
        const Icon = it.icon;
        // yozuv ichidagi yorliq («Переместить вверх [CTRL]+[UP]») o'ng ustunga ko'chadi — ikki marta chiqmaydi
        const sp = typeof it.label === "string" ? splitKeys(it.label) : null;
        const label = sp?.keys ? sp.text : it.label;
        const hint = it.hint ? fmtKeys(it.hint) : sp?.keys ?? undefined;
        return (
          <button key={i} type="button" role="menuitem" className="ctx-item" disabled={it.disabled} data-testid={it.testid}
            onClick={() => { onClose(); it.onClick?.(); }}>
            <span className="ctx-ico">{Icon ? <Icon size={16} strokeWidth={1.8} /> : null}</span>
            <span className="ctx-label">{label}</span>
            {hint && <span className="ctx-hint">{hint}</span>}
          </button>
        );
      })}
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
