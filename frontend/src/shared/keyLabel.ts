// Klaviatura yorliqlarini xodimlar o'rgangan ko'rinishda yozish: «Ctrl+PgDn» → «[CTRL]+[PAGE DOWN]», «Del» → «[DEL]».
// Menyular (ContextMenu hint) va tugmalar maslahati (IconBtn title: «Клонировать (Ctrl+K)» → «Клонировать [CTRL]+[K]») shu
// funksiyalardan o'tadi — barcha ekranlarda bitta format.

const NAMES: Record<string, string> = {
  ctrl: "CTRL", shift: "SHIFT", alt: "ALT", del: "DEL", delete: "DEL", insert: "INSERT", ins: "INSERT", enter: "ENTER",
  esc: "ESC", escape: "ESC", space: "SPACE", пробел: "SPACE", home: "HOME", end: "END", tab: "TAB", backspace: "BACKSPACE",
  pgup: "PAGE UP", pgdn: "PAGE DOWN", pageup: "PAGE UP", pagedown: "PAGE DOWN", "page up": "PAGE UP", "page down": "PAGE DOWN",
  up: "UP", down: "DOWN", left: "LEFT", right: "RIGHT", "↑": "UP", "↓": "DOWN", "←": "LEFT", "→": "RIGHT",
};

/** Bitta tugma nomi → «[X]»; tanilmasa null. */
function keyName(tok: string): string | null {
  const s = tok.trim();
  const br = /^\[(.+)\]$/.exec(s);                 // allaqachon «[CTRL]» ko'rinishida
  if (br) return keyName(br[1]);
  const low = s.toLowerCase();
  if (NAMES[low]) return NAMES[low];
  if (/^f([1-9]|1[0-2])$/i.test(s)) return s.toUpperCase();
  if (/^[a-z0-9]$/i.test(s)) return s.toUpperCase();
  return null;
}

/** «Ctrl+PgDn» → «[CTRL]+[PAGE DOWN]». Bir nechta variant « / » yoki «, » bilan. Tanilmasa — null. */
export function parseKeys(s: string): string | null {
  const alts = s.split(/\s*(?:\/|,)\s*/).filter(Boolean);
  if (!alts.length) return null;
  const out: string[] = [];
  for (const a of alts) {
    // «+» ning o'zi tugma bo'lishi mumkin emas (bizda yo'q) — oddiy bo'lish
    const parts = a.split("+");
    const names = parts.map(keyName);
    if (names.some((n) => n === null)) return null;
    out.push(names.map((n) => `[${n}]`).join("+"));
  }
  return out.join(", ");
}

/** Menyu yorlig'i: tanilsa yangi format, aks holda o'zi. */
export function fmtKeys(s: string | undefined): string | undefined {
  if (!s) return s;
  return parseKeys(s) ?? s;
}

/** Tugma maslahati: oxiridagi «(Ctrl+K)» → « [CTRL]+[K]». Qavs ichida faqat tugmalar bo'lsagina o'zgaradi. */
export function fmtTitle(s: string | undefined): string | undefined {
  if (!s) return s;
  const m = /^(.*?)\s*\(([^()]+)\)\s*$/.exec(s);
  if (!m) return s;
  const k = parseKeys(m[2]);
  return k ? `${m[1]} ${k}` : s;
}

/** Menyu bandi yozuvi oxiridagi yorliqni ajratish: «Переместить вверх [CTRL]+[UP]» yoki «Настройки (Ctrl+P)» →
 *  { text: «Переместить вверх», keys: «[CTRL]+[UP]» }. Yorliq bo'lmasa keys = null. */
export function splitKeys(s: string): { text: string; keys: string | null } {
  const br = /^(.*?)\s+((?:\[[^\]]+\]\+?)+)$/.exec(s);
  if (br) { const k = parseKeys(br[2]); if (k) return { text: br[1], keys: k }; }
  const pa = /^(.*?)\s*\(([^()]+)\)\s*$/.exec(s);
  if (pa) { const k = parseKeys(pa[2]); if (k) return { text: pa[1], keys: k }; }
  return { text: s, keys: null };
}
