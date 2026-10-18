// O'zbek lotin → kirill transliteratori (brauzer uchun). Qoidalar `backend/app/uz_translit.py` bilan aynan bir xil —
// UI matnlari (uz-Cyrl.json) Python da yaratiladi, bu modul esa serverdan {ru, uz} juftligi bilan keladigan ma'lumot
// matnlari (stanok parametrlari, import formatlari, OEE sabablari …) uchun. Moslik: `node scripts/check_translit_parity.mjs`.
// Istisnolar — `uz_cyrl_overrides.json` (i18n_src.py backend/app dan nusxalaydi).
import OV from "./uz_cyrl_overrides.json" with { type: "json" };

interface Overrides {
  words: Record<string, string>; stems: Record<string, string>; keep: string[]; keep_lower: string[];
  phrases: string[]; abbr: Record<string, string>; funcs: string[]; tags: string[];
}
const ov = OV as unknown as Overrides;

const APOS = "'ʻ’`‘ʼ";
const reEsc = (s: string) => s.replace(/[.*+?^${}()|[\]\\/-]/g, "\\$&");
const WORDS = new Map(Object.entries(ov.words ?? {}).map(([k, v]) => [k.toLowerCase(), v]));
const STEMS = new Map(Object.entries(ov.stems ?? {}).map(([k, v]) => [k.toLowerCase(), v]));
const STEM_KEYS = [...STEMS.keys()].sort((a, b) => b.length - a.length);
const KEEP = new Set((ov.keep ?? []).map((w) => w.toLowerCase()));
const KEEP_LOWER = new Set(ov.keep_lower ?? []);
const SUFFIX_RE = /^(?:lar|ning|ni|ga|ka|qa|dagi|da|ta|dan|tan|gacha|cha|imiz|ingiz|miz|ngiz|im|ing|si|i|m|ng|lik|li|siz|chi|day|dek|mi|ku|yu|u|ham|lashtir|lash|lan|langan|la|dir|gi)*$/;

const A = `[${APOS}]`;
const B = "(?<![A-Za-z0-9_])";
const E = "(?![A-Za-z0-9_])";
const KEYS = "F[0-9]{1,2}|PgUp|PgDn|PageUp|PageDown|Home|End|Del|Delete|Insert|Ins|Enter|Esc|Tab|Space|Backspace|Up|Down|Left"
  + "|Right|Ctrl|CTRL|Alt|ALT|Shift|SHIFT|Cmd|Win|Meta|[A-Za-z0-9](?:/[A-Za-z0-9])*|[^\\sA-Za-z0-9]";
const PROTECT = new RegExp([
  "\\{\\{.*?\\}\\}",
  "\\{[^{}\\s]*\\}",
  "%\\([A-Za-z_]+\\)[sdif]|%[sdif]",
  "\\$t\\([^)]*\\)",
  "</?(?:" + (ov.tags ?? []).join("|") + ")(?:\\s[^<>\\n]*)?/?>",
  "`[^`\\n]*`",
  "\\[[A-Za-z0-9 ]+\\](?:\\s*\\+\\s*\\[[A-Za-z0-9 ]+\\])*",
  "(?:https?|ftp|file)://[^\\s«»\"')]+",
  B + "www\\.[^\\s«»\"')]+",
  B + "data:[A-Za-z]+/[A-Za-z0-9.+-]+(?:;base64)?",
  "[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\\.[A-Za-z0-9.-]+",
  B + "(?:Ctrl|CTRL|Alt|ALT|Shift|SHIFT|Cmd|Win|Meta)(?:\\s*\\+\\s*(?:" + KEYS + "))+(?![A-Za-z0-9_" + APOS + "])",
  B + "(?:" + (ov.funcs ?? []).join("|") + ")\\(",
  "(?<![A-Za-z0-9])/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.{}<>-]+)+",
  "#/[A-Za-z0-9_/-]*",
  B + "[A-Za-z_][A-Za-z0-9_]+(?:\\.[A-Za-z_][A-Za-z0-9_]+)+" + E,
  "(?<![A-Za-z0-9])\\.[A-Za-z][A-Za-z0-9]{0,5}" + E,
  B + "[A-Za-z_]+[0-9_][A-Za-z0-9_]*",
  B + "[A-Za-z]+(?:[ \\t]*\\|[ \\t]*[A-Za-z_]+)+" + E,
  ...[...(ov.phrases ?? [])].sort((a, b) => b.length - a.length).map((p) => "(?<![A-Za-z])" + reEsc(p) + "(?![A-Za-z])"),
].join("|"), "g");
const ABBR: [RegExp, string][] = Object.entries(ov.abbr ?? {}).sort((a, b) => b[0].length - a[0].length)
  .map(([k, v]) => [new RegExp("(?<![A-Za-z])" + reEsc(k) + "(?![A-Za-z])", "g"), v]);
const WORD = new RegExp(`[A-Za-z]+(?:${A}[A-Za-z]+)*(?:(?<=[oOgG])${A})?`, "g");
const APOS_RE = new RegExp(A, "g");

const SIMPLE: Record<string, string> = {
  a: "а", b: "б", d: "д", f: "ф", g: "г", h: "ҳ", i: "и", j: "ж", k: "к", l: "л", m: "м", n: "н", o: "о", p: "п",
  q: "қ", r: "р", s: "с", t: "т", u: "у", v: "в", x: "х", z: "з", w: "в", c: "ц",
};
const CYR_V = new Set("аеёиоуэюяўАЕЁИОУЭЮЯЎ");
const LAT_V = new Set("aeiou");
const YV: Record<string, string> = { o: "ё", u: "ю", a: "я" };
const isUp = (ch: string) => ch !== ch.toLowerCase();

function rules(w: string, prev = ""): string {
  const lw = w.toLowerCase();
  const n = w.length;
  const out: string[] = [];
  const last = () => (out.length && out[out.length - 1] ? out[out.length - 1].slice(-1).toLowerCase() : prev.slice(-1).toLowerCase());
  const at = (j: number) => (j < n ? lw[j] : "");
  let i = 0;
  while (i < n) {
    const c = lw[i], nx = at(i + 1), nx2 = at(i + 2), nx3 = at(i + 3);
    const up = isUp(w[i]);
    let step = 1;
    let r: string;
    if ((c === "o" || c === "g") && nx === "'") { r = c === "o" ? "ў" : "ғ"; step = 2; }
    else if (c === "s" && nx === "h") { r = "ш"; step = 2; }
    else if (c === "c" && nx === "h") { r = "ч"; step = 2; }
    else if (c === "y" && (nx === "o" || nx === "u" || nx === "a" || nx === "e") && !(nx === "o" && nx2 === "'")) {
      if (nx === "e") { const lc = last(); r = !lc || CYR_V.has(lc) || lc === "ъ" || lc === "ь" ? "е" : "ъе"; }
      else r = YV[nx];
      step = 2;
    } else if (c === "e") { const lc = last(); r = !lc || CYR_V.has(lc) ? "э" : "е"; }
    else if (c === "t" && nx === "s" && (nx2 === "e" || (nx2 === "i" && nx3 !== "" && LAT_V.has(nx3)))) { r = "ц"; step = 2; }
    else if (c === "s" && (last() === "к" || last() === "н") && nx === "i"
      && (lw.startsWith("ya", i + 2) || (last() === "к" && lw.startsWith("on", i + 2)))) r = "ц";
    else if (c === "'") r = last() === "с" && nx === "h" ? "" : "ъ";
    else if (c === "y") r = "й";
    else r = SIMPLE[c] ?? w[i];
    out.push(up ? r.toUpperCase() : r);
    i += step;
  }
  return out.join("");
}

function applyCase(src: string, cyr: string): string {
  const letters = [...src].filter((ch) => /[A-Za-z]/.test(ch));
  if (letters.length && isUp(letters[0])) {
    if (letters.length > 1 && letters.every(isUp)) return cyr.toUpperCase();
    return cyr.slice(0, 1).toUpperCase() + cyr.slice(1);
  }
  return cyr;
}

function word(w: string): string {
  const norm = w.replace(APOS_RE, "'");
  const lw = norm.toLowerCase();
  const letters = norm.replace(/[^A-Za-z]/g, "");
  const ow = WORDS.get(lw);
  if (ow !== undefined) return applyCase(norm, ow);
  if (letters.length === 1 && lw !== "u" && !(norm.length === 2 && norm[1] === "'")) return w;
  if (letters.length >= 2 && letters === letters.toUpperCase()) return w;
  if (/[a-z][A-Z]/.test(letters)) return w;
  if (KEEP.has(lw) || KEEP_LOWER.has(norm)) return w;
  for (const st of STEM_KEYS) {
    if (lw.startsWith(st) && SUFFIX_RE.test(lw.slice(st.length))) {
      const cyr = STEMS.get(st)!;
      return applyCase(norm, cyr + rules(lw.slice(st.length), cyr));
    }
  }
  return rules(norm);
}

const words = (s: string) => s.replace(WORD, (m) => word(m));

function plain(s: string): string {
  const hits: [number, number, string][] = [];
  for (const [rx, v] of ABBR) for (const m of s.matchAll(rx)) hits.push([m.index!, m.index! + m[0].length, v]);
  hits.sort((a, b) => a[0] - b[0]);
  let out = "";
  let pos = 0;
  for (const [a, b, v] of hits) {
    if (a < pos) continue;
    out += words(s.slice(pos, a)) + v;
    pos = b;
  }
  return out + words(s.slice(pos));
}

const cache = new Map<string, string>();

/** O'zbek lotin matni → kirill (o'rinbosarlar, kodlar, qisqartmalar, birliklar o'zgarmaydi). */
export function toCyrillic(s: string): string {
  if (!s || !/[A-Za-z]/.test(s)) return s;
  const hit = cache.get(s);
  if (hit !== undefined) return hit;
  let out = "";
  let pos = 0;
  for (const m of s.matchAll(PROTECT)) {
    if (m.index! > pos) out += plain(s.slice(pos, m.index!));
    out += m[0];
    pos = m.index! + m[0].length;
  }
  out += plain(s.slice(pos));
  if (cache.size > 5000) cache.clear();
  cache.set(s, out);
  return out;
}
