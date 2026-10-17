/**
 * `.project` (XML) faylini o'qish — faqat solishtirish uchun kerak bo'lgan qism:
 * operatsiyalar ro'yxati va kroy (CS/CL) operatsiyalarida saqlangan natija statistikasi
 * (listlar soni, to'ldirilganlik, деловой qoldiq, kesish uzunligi, detallar soni).
 * Ikkilik kroy natijasi (`data`) o'qilmaydi.
 */
import fs from "node:fs/promises";

export interface SavedCsStats {
  sheets: number | null;        // cMaterialCount — ishlatilgan listlar
  fill: number | null;          // cFilling (0..1) → foiz
  businessM2: number | null;    // cBusinessWasteAmount, m²
  cutLengthM: number | null;    // cTrimLength, m
  cutsCount: number | null;     // cTrimCount
  parts: number | null;         // cPartCount (Σ qty)
  packets: number | null;       // cCountPackets
  wasteM2: number | null;       // cWasteAmount
  materialM2: number | null;    // cMaterialAmount
  partsM2: number | null;       // cPartAmount
}

export interface FileOperation {
  index: number;                // fayldagi tartib (0 dan)
  id: string;
  type: string;                 // CS, CL, EL, XNC, GR, SP, O, LB, CN
  name: string;                 // material / operatsiya nomi
  code: string;
  materialId: string | null;
  sheet: { length: number; width: number; thickness: number } | null;
  stock: Array<{ length: number; width: number; qty: number; waste: boolean; business: boolean }>;
  partsRefs: number;            // <part id/> havolalari soni
  partsQty: number;             // havola qilingan detallar Σ count
  cut: { kerf: number | null; maxTurns: number | null; trimL: number | null; trimW: number | null; minPruning: number | null; texture: boolean | null; complexBand: boolean | null };
  saved: SavedCsStats | null;   // CS / CL da saqlangan natija
}

export interface ProjectFile {
  path: string;
  name: string;
  version: string;
  currency: string;
  products: number;
  partsTotal: number;           // mahsulotlardagi detallar Σ count
  counts: Record<string, number>;
  operations: FileOperation[];
}

const ENT: Record<string, string> = { "&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": '"', "&apos;": "'" };
export function decodeEntities(s: string): string {
  return s.replace(/&(lt|gt|amp|quot|apos);|&#(\d+);|&#x([0-9a-fA-F]+);/g, (m, n, d, h) =>
    n ? ENT[m] : d ? String.fromCodePoint(Number(d)) : String.fromCodePoint(parseInt(h, 16)));
}

/** Teg atributlarini o'qish (qiymatlar ichidagi `>` XML da doim &gt; bo'ladi). */
export function parseAttrs(tag: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = /([A-Za-z_][\w.:-]*)\s*=\s*"([^"]*)"/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(tag))) out[m[1]] = decodeEntities(m[2]);
  return out;
}

const num = (v: string | undefined): number | null => (v === undefined || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
const bool = (v: string | undefined): boolean | null => (v === undefined ? null : v === "true" || v === "1");

interface RawElement { tag: string; attrs: Record<string, string>; start: number; end: number; inner: string }

/** Yuqori darajadagi (ildiz ostidagi) elementlarni topish — `good` va `operation`. Ichma-ich `part`/`material` lar `inner` da. */
function topLevel(xml: string, tag: string): RawElement[] {
  const out: RawElement[] = [];
  const re = new RegExp(`<${tag}\\b([^>]*?)(/?)>`, "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(xml))) {
    const attrs = parseAttrs(m[1]);
    if (m[2] === "/") { out.push({ tag, attrs, start: m.index, end: re.lastIndex, inner: "" }); continue; }
    const close = xml.indexOf(`</${tag}>`, re.lastIndex);
    const inner = close < 0 ? "" : xml.slice(re.lastIndex, close);
    out.push({ tag, attrs, start: m.index, end: close < 0 ? re.lastIndex : close + tag.length + 3, inner });
    if (close > 0) re.lastIndex = close + tag.length + 3;
  }
  return out;
}

function children(inner: string, tag: string): Record<string, string>[] {
  const out: Record<string, string>[] = [];
  const re = new RegExp(`<${tag}\\b([^>]*?)/?>`, "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(inner))) out.push(parseAttrs(m[1]));
  return out;
}

export function parseProjectXml(xml: string, filePath = ""): ProjectFile {
  const rootM = /<project\b([^>]*)>/.exec(xml);
  if (!rootM) throw new Error("Bu `.project` fayli emas (ildiz <project> topilmadi)");
  const root = parseAttrs(rootM[1]);
  const goods = topLevel(xml, "good");
  const goodById = new Map<string, RawElement>();
  for (const g of goods) if (g.attrs.id) goodById.set(g.attrs.id, g);
  const partCount = new Map<string, number>();     // detal id → count
  let products = 0, partsTotal = 0;
  for (const g of goods) {
    if (g.attrs.typeId !== "product") continue;
    products++;
    for (const p of children(g.inner, "part")) {
      const c = num(p.count) ?? 1;
      if (p.id) partCount.set(p.id, c);
      partsTotal += c;
    }
  }
  const ops: FileOperation[] = [];
  const counts: Record<string, number> = {};
  topLevel(xml, "operation").forEach((o, index) => {
    const a = o.attrs;
    const type = a.typeId || "?";
    counts[type] = (counts[type] || 0) + 1;
    const mat = children(o.inner, "material")[0];
    const good = mat?.id ? goodById.get(mat.id) : undefined;
    const refs = children(o.inner, "part");
    const tool = a.tool1 ? goodById.get(a.tool1)?.attrs : undefined;
    const stock = good ? children(good.inner, "part").map((s) => ({
      length: num(s.l) ?? 0, width: num(s.w) ?? 0, qty: num(s.count) ?? 0, waste: s.waste === "true", business: s.business === "true",
    })) : [];
    const isCut = type === "CS" || type === "CL";
    const saved: SavedCsStats | null = isCut && (a.cMaterialCount !== undefined || a.cFilling !== undefined) ? {
      sheets: num(a.cMaterialCount), fill: a.cFilling !== undefined ? Math.round(Number(a.cFilling) * 10000) / 100 : null,
      businessM2: num(a.cBusinessWasteAmount), cutLengthM: num(a.cTrimLength), cutsCount: num(a.cTrimCount),
      parts: num(a.cPartCount), packets: num(a.cCountPackets), wasteM2: num(a.cWasteAmount),
      materialM2: num(a.cMaterialAmount), partsM2: num(a.cPartAmount),
    } : null;
    ops.push({
      index, id: a.id || String(index), type,
      name: good?.attrs.name || a.typeName || a.name || "",
      code: good?.attrs.code || a.code || "",
      materialId: mat?.id ?? null,
      sheet: isCut ? { length: num(a.l) ?? num(good?.attrs.l) ?? 0, width: num(a.w) ?? num(good?.attrs.w) ?? 0, thickness: num(a.t) ?? num(good?.attrs.t) ?? 0 } : null,
      stock,
      partsRefs: refs.length,
      partsQty: refs.reduce((s, r) => s + (partCount.get(r.id || "") ?? 0), 0),
      cut: { kerf: num(tool?.swSawthick), maxTurns: num(tool?.swMaxturns), trimL: num(a.cTrimL), trimW: num(a.cTrimW),
             minPruning: num(tool?.swMinPruning), texture: bool(a.csTexture), complexBand: bool(tool?.swComplexBand) },
      saved,
    });
  });
  return {
    path: filePath, name: root.name || "", version: root.version || "", currency: root.currency || "",
    products, partsTotal, counts, operations: ops,
  };
}

/** Baytlarni XML e'lonidagi kodlash bo'yicha o'qish (eski fayllar `encoding="windows-1251"` — utf8 deb o'qilsa kirill nomlar buziladi). */
export function decodeXmlBytes(buf: Uint8Array): string {
  const head = new TextDecoder("latin1").decode(buf.subarray(0, 200));
  const enc = /<\?xml[^>]*encoding\s*=\s*["']([A-Za-z0-9._-]+)["']/i.exec(head)?.[1]?.toLowerCase() || "utf-8";
  try { return new TextDecoder(enc).decode(buf); } catch { return new TextDecoder("utf-8").decode(buf); }
}

export async function readProjectFile(filePath: string): Promise<ProjectFile> {
  const xml = decodeXmlBytes(await fs.readFile(filePath));
  return parseProjectXml(xml, filePath);
}

/** Qisqa jadval (matn) — tezkor ko'rish uchun. */
export function projectFileSummary(pf: ProjectFile): string {
  const lines = [`${pf.name || pf.path}  version=${pf.version}  products=${pf.products}  parts=${pf.partsTotal}  ops=${JSON.stringify(pf.counts)}`];
  for (const o of pf.operations) {
    if (o.type !== "CS" && o.type !== "CL") continue;
    const s = o.saved;
    lines.push(`  #${o.index} ${o.type} ${o.name} [${o.sheet?.length}×${o.sheet?.width}×${o.sheet?.thickness}] parts ${o.partsRefs}/${o.partsQty}` +
      (s ? ` | saqlangan: listlar ${s.sheets}, F ${s.fill}%, деловой ${s.businessM2} m², kesish ${s.cutLengthM} m` : " | natija saqlanmagan"));
  }
  return lines.join("\n");
}
