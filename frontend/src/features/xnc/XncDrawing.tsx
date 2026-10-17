// XNC chizmasi: server SVG si ko'rinadigan maydonga to'liq sig'dirib ko'rsatiladi (zoom = 1); sichqoncha g'ildiragi —
// kattalashtirish / kichraytirish (kursor ostidagi nuqta joyida qoladi), «Показать все изображение» (fitTick o'zgarsa) —
// yana to'liq sig'dirish. `hl` — tanlangan buyruqlar yo'llari: server elementlardagi `data-cmd` bo'yicha qizil belgilanadi (CSS klass,
// SVG qayta so'ralmaydi); chizmadagi elementni bosish — `onPick` (buyruqni tanlash).
import { useEffect, useLayoutEffect, useRef, useState, type MouseEvent } from "react";

const MAX_ZOOM = 16;
const STEP = 1.2;

/** `data-cmd` qiymati (bo'sh joy bilan ajratilgan yo'llar) tanlangan yo'llardan biriga yoki uning ichidagisiga tegishlimi. */
export function cmdMatches(tags: string, keys: string[]): boolean {
  if (!keys.length) return false;
  return tags.split(" ").some((t) => t && keys.some((k) => t === k || t.startsWith(`${k}.`)));
}

export function XncDrawing({ svg, fitTick, onBox, hl, onPick }: { svg: string; fitTick: number;
  /** maydon o'lchami (px, 40 px qadam bilan) — server chizmadagi minimal ko'rinadigan o'lchamlarni shu masshtabda hisoblaydi */
  onBox?: (w: number, h: number) => void;
  /** belgilanadigan buyruqlar yo'llari (`pathKey`, 0 dan); blok yo'li — uning ichidagi barcha buyruqlar */
  hl?: string[];
  /** chizmadagi element bosildi: manba buyruq yo'li, `add` — Ctrl bilan (ko'p tanlovga qo'shish) */
  onPick?: (key: string, add: boolean) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const onBoxRef = useRef(onBox);
  onBoxRef.current = onBox;
  const [zoom, setZoom] = useState(1);
  const [box, setBox] = useState({ w: 0, h: 0 });
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;
  // kattalashtirishdan keyin kursor ostidagi nuqtani joyida qoldirish: (chizmadagi nisbiy nuqta, kursorning maydondagi o'rni)
  const anchor = useRef<{ fx: number; fy: number; px: number; py: number } | null>(null);

  useEffect(() => { anchor.current = null; setZoom(1); }, [fitTick]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const q = (n: number) => Math.max(100, Math.round(n / 40) * 40);
    const measure = () => {
      const w = el.offsetWidth - 4, h = el.offsetHeight - 4;      // chegara + zaxira (aylantirish chizig'i chiqmasin)
      onBoxRef.current?.(q(w), q(h));
      setBox((b) => (b.w === w && b.h === h ? b : { w, h }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    const onWheel = (e: WheelEvent) => {
      const z0 = zoomRef.current;
      const z1 = Math.max(1, Math.min(MAX_ZOOM, e.deltaY < 0 ? z0 * STEP : z0 / STEP));
      if (z1 === z0) return;                                      // chegarada — sahifa odatdagidek aylanadi
      e.preventDefault();
      const s = el.querySelector("svg");
      const r = el.getBoundingClientRect();
      const sr = s?.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      anchor.current = sr && sr.width > 0 && sr.height > 0
        ? { fx: (e.clientX - sr.left) / sr.width, fy: (e.clientY - sr.top) / sr.height, px, py } : null;
      setZoom(z1 < 1.0001 ? 1 : z1);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => { ro.disconnect(); el.removeEventListener("wheel", onWheel); };
  }, []);

  useLayoutEffect(() => {
    const el = ref.current;
    const s = el?.querySelector("svg");
    if (!el || !s) return;
    const vb = s.viewBox?.baseVal;
    const vw = vb && vb.width > 0 ? vb.width : 0, vh = vb && vb.height > 0 ? vb.height : 0;
    if (!(vw > 0 && vh > 0 && box.w > 8 && box.h > 8)) return;   // o'lcham noma'lum — CSS dagi standart ko'rinish
    const k = Math.min(box.w / vw, box.h / vh) * zoom;
    s.style.width = `${vw * k}px`;
    s.style.height = `${vh * k}px`;
    s.style.maxWidth = s.style.maxHeight = "none";
    s.style.flex = "none";
    s.style.margin = zoom > 1 ? "0" : "";
    const a = anchor.current;
    anchor.current = null;
    if (zoom <= 1) { el.scrollLeft = 0; el.scrollTop = 0; return; }
    if (a) {
      const er = el.getBoundingClientRect(), sr = s.getBoundingClientRect();
      // chizmaning maydon ichidagi (aylantirishsiz) boshlanish nuqtasi
      const ox = sr.left - er.left + el.scrollLeft, oy = sr.top - er.top + el.scrollTop;
      el.scrollLeft = ox + a.fx * sr.width - a.px;
      el.scrollTop = oy + a.fy * sr.height - a.py;
    }
  }, [svg, zoom, box]);

  // tanlangan buyruq geometriyasi — `xnc-hl` klassi (yuza va yon ko'rinishlardagi barcha elementlar)
  const hlKey = (hl ?? []).join(" ");
  useLayoutEffect(() => {
    const s = ref.current?.querySelector("svg");
    if (!s) return;
    const keys = hlKey ? hlKey.split(" ") : [];
    s.querySelectorAll("[data-cmd]").forEach((el) => el.classList.toggle("xnc-hl", cmdMatches(el.getAttribute("data-cmd") ?? "", keys)));
  }, [svg, hlKey]);

  const click = (e: MouseEvent<HTMLDivElement>) => {
    const t = e.target as Element;
    // geometriya elementi yoki xato yozuvi (`data-err-cmd` — xato bergan buyruq)
    const el = t.closest?.("[data-cmd]");
    const key = el ? el.getAttribute("data-cmd")?.split(" ")[0] : t.closest?.("[data-err-cmd]")?.getAttribute("data-err-cmd")?.split(" ")[0];
    if (key && onPick) onPick(key, e.ctrlKey || e.metaKey);
  };

  return (
    <div ref={ref} className="xnc-draw" data-testid="xnc-drawing" data-zoom={zoom === 1 ? "fit" : zoom.toFixed(2)}
      style={zoom > 1 ? { justifyContent: "flex-start", alignItems: "flex-start" } : undefined}
      onClick={onPick ? click : undefined}
      dangerouslySetInnerHTML={{ __html: svg }} />
  );
}
