// Oyna kichrayganda butun interfeys mutanosib kichrayadi (foydalanuvchi, 2026-10-22): sarlavha, jadvallar, oynalar qatorlarga
// bo'linib pastga tushmaydi — tuzilish katta oynadagidek qoladi, faqat masshtab kichrayadi. Katta oynada (≥ REF) o'zgarish yo'q.
// `#root` ga CSS `zoom`; `vh` / `vw` o'rniga `--vh` / `--vw` (zoom ichida 100vh oynadan kichik chiqadi). Sichqoncha koordinatasini
// CSS pikselga aylantiradigan joylar `uiZoom()` ga bo'ladi (SVG `getScreenCTM` va `getBoundingClientRect` o'zi hisobga oladi).
import { useEffect, useState } from "react";

export const REF_W = 1200;           // shu enidan tor oynada masshtab kichrayadi
export const REF_H = 640;            // shu balandlikdan past oynada ham
export const MIN_ZOOM = 0.5;

let zoom = 1;
const subs = new Set<() => void>();

/** Joriy masshtab (1 — o'zgarishsiz). */
export function uiZoom(): number {
  return zoom;
}

/** Oyna balandligi `#root` ichidagi CSS pikselda (masshtab hisobga olingan). */
export function layoutHeight(): number {
  return window.innerHeight / zoom;
}

export function layoutWidth(): number {
  return window.innerWidth / zoom;
}

export function fitZoom(w: number, h: number): number {
  const z = Math.min(1, w / REF_W, h / REF_H);
  return Math.max(MIN_ZOOM, Math.round(z * 1000) / 1000);
}

function apply() {
  const z = fitZoom(window.innerWidth, window.innerHeight);
  const root = document.getElementById("root");
  const de = document.documentElement;
  de.style.setProperty("--vh", `${window.innerHeight / 100 / z}px`);
  de.style.setProperty("--vw", `${window.innerWidth / 100 / z}px`);
  // jadval (AG Grid) pastki qotirilgan qator + gorizontal chiziq balandligini ekran px da o'lchab, joyni z marta kam qoldiradi —
  // oxirgi qator yarim yopilardi; farq (21 + 16) × (1 − z) qo'shimcha pastki joy bilan qoplanadi
  de.style.setProperty("--ag-zoom-fix", `${((21 + 16) * (1 - z)).toFixed(2)}px`);
  if (root) root.style.zoom = z === 1 ? "" : String(z);
  de.dataset.uiZoom = String(z);
  if (z !== zoom) {
    zoom = z;
    subs.forEach((f) => f());
  }
}

let inited = false;
export function initUiZoom() {
  if (inited || typeof window === "undefined") return;
  inited = true;
  apply();
  window.addEventListener("resize", apply);
}

/** Komponentlar uchun: masshtab o'zgarganda qayta chiziladi. */
export function useUiZoom(): number {
  const [z, setZ] = useState(zoom);
  useEffect(() => {
    const f = () => setZ(zoom);
    subs.add(f);
    f();
    return () => { subs.delete(f); };
  }, []);
  return z;
}

// modul yuklanishi bilan (boshqa modullar boshlang'ich qiymatlarni hisoblashidan oldin)
initUiZoom();
