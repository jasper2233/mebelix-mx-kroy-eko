/** Kroy kartasidagi detal yozuvlari (raqam, uzunlik, en, nom) joylashuvi — bir-birining ustiga tushmasin va detaldan chiqmasin.
 *
 *  Xodim skrini (2026-11-24): tor tik detallarda (35×340) en raqamlari ustma-ust ustuni va detal raqami bir joyga tushib
 *  o'qilmasdi. Onlayn tizimda («test uchun», shu turdagi detallar bilan jonli tekshirildi) ham yozuvlar ustma-ust tushadi —
 *  u yerda yechim yo'q. MX qoidasi: har yozuvning bir nechta joyi (afzal tartibda) bor; detal ichida, bir-biriga tegmaydigan
 *  eng yaxshi to'plam tanlanadi. Ustuvorlik: detal raqami (operator detalni ro'yxatdan shu bilan topadi) → uzunlik / en → nom.
 *  Oddiy detallarda birinchi variantlar — avvalgi ko'rinish (raqam markazda, uzunlik pastki-chapda, en o'ngda ustma-ust).
 *  Backend chop kartasi (`render.part_label_layout`) — xuddi shu qoida. */

export type LabelKind = "num" | "len" | "wid" | "name";
/** h — gorizontal matn; s — belgilar ustma-ust (tik ustun); r — 90° burilgan (pastga o'qiladi) */
export type LabelItem = {
  kind: LabelKind; text: string; mode: "h" | "s" | "r";
  /** h / s: matn langari x va (birinchi qator) asos chizig'i y; r — burish nuqtasi */
  x: number; y: number; anchor: "start" | "middle" | "end";
  /** nom — boshqa shrift o'lchami (fs ulushi) */
  scale?: number;
};

export const CW = 0.6;       // monospace qalin raqam eni, fs ulushi
const ASC = 0.74;            // raqam balandligi asos chizig'idan yuqoriga
const DESC = 0.06;
export const STEP = 0.95;    // ustma-ust belgilar qadami
const GAP_X = 0.5;          // yozuvlar orasidagi eng kichik bo'shliq: yonma-yon — taxminan bitta belgi ("340 15 45")
const GAP_Y = 0.75;         // ustma-ust: bitta qator (tik ustunda «10» va «45» bitta «1045» bo'lib o'qilmasin)
const EDGE = 0.12;           // detal chetidan eng kichik masofa

type Box = [number, number, number, number];     // x0, y0, x1, y1

function boxOf(it: LabelItem, fs: number): Box {
  const sc = it.scale ?? 1, f = fs * sc, n = [...it.text].length;
  if (it.mode === "h") {
    const w = n * CW * f;
    const x0 = it.anchor === "start" ? it.x : it.anchor === "end" ? it.x - w : it.x - w / 2;
    return [x0, it.y - ASC * f, x0 + w, it.y + DESC * f];
  }
  if (it.mode === "s") {
    const w = CW * f;
    const x0 = it.anchor === "start" ? it.x : it.anchor === "end" ? it.x - w : it.x - w / 2;
    return [x0, it.y - ASC * f, x0 + w, it.y + (n - 1) * STEP * f + DESC * f];
  }
  // 90° burilgan: matn (x, y) dan pastga o'sadi, harflar o'ng tomonda (rotate(90): yuqori → o'ng)
  return [it.x - DESC * f, it.y, it.x + ASC * f, it.y + n * CW * f];
}

function layoutAt(
  p: { x: number; y: number; l: number; w: number }, fs: number,
  t: { num?: string; len: string; wid: string; name?: string },
): LabelItem[] {
  const { x, y, l, w } = p;
  const cx = x + l / 2, cy = y + w / 2, R = x + l, B = y + w;
  const mid = cy + (ASC - DESC) / 2 * fs;                         // gorizontal matn markazda bo'lishi uchun asos chizig'i
  const stackMid = (n: number) => cy - ((n - 1) * STEP * fs - (ASC + DESC) * fs) / 2 - DESC * fs;
  const pad = 0.3 * fs;
  const cand: Record<LabelKind, LabelItem[]> = { num: [], len: [], wid: [], name: [] };
  if (t.num) {
    const s = t.num, n = [...s].length;
    cand.num.push(
      { kind: "num", text: s, mode: "h", x: cx, y: mid, anchor: "middle" },
      { kind: "num", text: s, mode: "s", x: cx, y: stackMid(n), anchor: "middle" },
      { kind: "num", text: s, mode: "h", x: cx, y: y + w * 0.3 + (ASC - DESC) / 2 * fs, anchor: "middle" },
      { kind: "num", text: s, mode: "h", x: cx, y: y + w * 0.7 + (ASC - DESC) / 2 * fs, anchor: "middle" },
      { kind: "num", text: s, mode: "h", x: x + l * 0.6, y: mid, anchor: "middle" },        // pastki-chapdagi uzunlikdan o'ngroqda
      { kind: "num", text: s, mode: "h", x: x + l * 0.6, y: y + w * 0.3 + (ASC - DESC) / 2 * fs, anchor: "middle" },
      { kind: "num", text: s, mode: "h", x: x + l * 0.35, y: mid, anchor: "middle" },
      { kind: "num", text: s, mode: "s", x: cx, y: y + w * 0.3 - ((n - 1) * STEP * fs) / 2 + ASC * fs / 2, anchor: "middle" },
      { kind: "num", text: s, mode: "s", x: cx, y: y + w * 0.62 - ((n - 1) * STEP * fs) / 2 + ASC * fs / 2, anchor: "middle" },
    );
  }
  const ln = [...t.len].length;
  cand.len.push(
    { kind: "len", text: t.len, mode: "h", x: x + 0.35 * fs, y: B - 0.35 * fs, anchor: "start" },
    { kind: "len", text: t.len, mode: "h", x: x + pad, y: mid, anchor: "start" },            // ingichka polosa: bitta qatorda
    { kind: "len", text: t.len, mode: "s", x: x + pad, y: B - 0.35 * fs - (ln - 1) * STEP * fs, anchor: "start" },
    { kind: "len", text: t.len, mode: "s", x: cx, y: B - 0.35 * fs - (ln - 1) * STEP * fs, anchor: "middle" },
  );
  cand.wid.push(
    { kind: "wid", text: t.wid, mode: "s", x: R - pad, y: y + 1.05 * fs, anchor: "end" },
    { kind: "wid", text: t.wid, mode: "h", x: R - 0.3 * fs, y: y + 0.95 * fs, anchor: "end" },   // ingichka uzun detal
    { kind: "wid", text: t.wid, mode: "h", x: R - pad, y: mid, anchor: "end" },                 // ingichka polosa
    { kind: "wid", text: t.wid, mode: "s", x: cx, y: y + 1.05 * fs, anchor: "middle" },         // tor tik detal
    { kind: "wid", text: t.wid, mode: "r", x: R - 1.25 * fs, y: y + 0.35 * fs, anchor: "start" },
  );
  if (t.name) {
    const below: LabelItem = { kind: "name", text: t.name, mode: "h", x: cx, y: mid + 1.1 * fs, anchor: "middle", scale: 0.85 };
    const center: LabelItem = { ...below, y: mid };
    cand.name.push(...(t.num ? [below, center] : [center, below]));   // raqam bo'lsa — uning ostida, bo'lmasa — markazda
  }

  const inside = (b: Box) => b[0] >= x + EDGE * fs && b[2] <= R - EDGE * fs && b[1] >= y + EDGE * fs && b[3] <= B - EDGE * fs;
  const sep = (a: Box, b: Box) =>
    !(a[0] < b[2] + GAP_X * fs && b[0] < a[2] + GAP_X * fs && a[1] < b[3] + GAP_Y * fs && b[1] < a[3] + GAP_Y * fs);
  const ok = (k: LabelKind) => cand[k].map((c) => ({ c, b: boxOf(c, fs) })).filter((v) => inside(v.b));
  const N = ok("num"), Ln = ok("len"), Wd = ok("wid"), Nm = ok("name");
  // baho: raqam 1000, uzunlik / en 100 dan, nom 10; afzal variantdan uzoqlashgani uchun kichik jarima
  let best: { s: number; items: LabelItem[] } = { s: -1, items: [] };
  const opt = <T,>(a: T[]) => [...a.map((v, i) => [v, i] as [T, number]), [null, 0] as [T | null, number]];
  for (const [n, ni] of opt(N)) for (const [le, li] of opt(Ln)) for (const [wd, wi] of opt(Wd)) {
    const chosen = [n, le, wd].filter(Boolean) as { c: LabelItem; b: Box }[];
    let good = true;
    for (let i = 0; i < chosen.length && good; i++) for (let j = i + 1; j < chosen.length; j++) {
      if (!sep(chosen[i].b, chosen[j].b)) { good = false; break; }
    }
    if (!good) continue;
    let s = (n ? 1000 - ni * 3 : 0) + (le ? 100 - li * 2 : 0) + (wd ? 100 - wi * 2 : 0);
    let nameItem: LabelItem | null = null;
    for (const [nm, mi] of opt(Nm)) {
      if (!nm) break;
      if (chosen.every((v) => sep(v.b, nm.b))) { s += 10 - mi; nameItem = nm.c; break; }
    }
    if (s > best.s) best = { s, items: [...chosen.map((v) => v.c), ...(nameItem ? [nameItem] : [])] };
  }
  return best.items;
}

/** Yozuv egallaydigan to'rtburchak [x0, y0, x1, y1] (testlar uchun). */
export const labelBox = boxOf;

/** Detal yozuvlari: avval odatdagi shriftda; detal raqami sig'masa (juda tor detal, masalan 35 mm) — faqat shu detalda shrift
 *  bosqichma-bosqich kichrayadi (`minFs` gacha), raqam albatta ko'rinsin. Hech bo'lmasa — odatdagi shriftdagi natija. */
export function layoutPartLabels(
  p: { x: number; y: number; l: number; w: number }, fs: number,
  t: { num?: string; len: string; wid: string; name?: string }, minFs = fs * 0.5,
): LabelItem[] {
  const first = layoutAt(p, fs, t);
  if (!t.num || first.some((it) => it.kind === "num")) return first;
  for (const k of [0.85, 0.7, 0.55, 0.45, 0.35]) {
    const f = fs * k;
    if (f < minFs) break;
    const items = layoutAt(p, f, t);
    if (items.some((it) => it.kind === "num")) return items.map((it) => ({ ...it, scale: (it.scale ?? 1) * k }));
  }
  return first;
}
