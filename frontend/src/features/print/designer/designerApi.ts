// Etiketka vizual redaktori: server jonli ko'rinishi (`POST /label-templates/design`) va yordamchi turlar.
import { useEffect, useRef, useState } from "react";
import { post } from "../../../api/client";
import type { LBParams } from "../../../api/types";
import type { LabelIssue, LabelTemplate } from "../labelsApi";

export type SampleKind = "part" | "waste" | "product" | "user";
export interface DesignMeta { source: "sample" | "project"; total: number; index: number; kind: string }
export interface DesignResult {
  svg: string; width: number; height: number; errors: LabelIssue[]; warnings: string[];
  values: Record<string, unknown>; tpl_values: Record<string, unknown>; meta: DesignMeta;
}

export interface DesignArgs {
  tpl: LabelTemplate | null; params: Record<string, unknown>; width: number; height: number; kind: SampleKind;
  fields: Record<string, unknown>[]; row: Record<string, unknown> | null;
  projectId: string | null; lb: LBParams | null; index: number; lang: "ru" | "uz";
}

/** Jonli ko'rinish: shablon/parametr o'zgarganda kechiktirilib (debounce) serverdan so'raladi; eski javob tashlanadi. */
export function useDesignPreview(a: DesignArgs, delay = 140) {
  const [data, setData] = useState<DesignResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const seq = useRef(0);
  const key = JSON.stringify([a.tpl, a.params, a.width, a.height, a.kind, a.fields, a.row, a.projectId, a.projectId ? { ...a.lb, template: null } : null,
    a.index, a.lang]);
  useEffect(() => {
    if (!a.tpl) return;
    const my = ++seq.current;
    setLoading(true);
    const h = setTimeout(() => {
      const body: Record<string, unknown> = {
        template: a.tpl, params: a.params, width_mm: a.width, height_mm: a.height, kind: a.kind, fields: a.fields,
        ...(a.row ? { row: a.row } : {}),
        ...(a.projectId && a.lb ? { project_id: a.projectId, lb: { ...a.lb, template: null }, index: a.index } : {}),
      };
      post<DesignResult>("/label-templates/design", body, { lang: a.lang })
        .then((r) => { if (my === seq.current) { setData(r); setError(""); } })
        .catch((e: unknown) => { if (my === seq.current) setError(e instanceof Error ? e.message : String(e)); })
        .finally(() => { if (my === seq.current) setLoading(false); });
    }, delay);
    return () => clearTimeout(h);
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return { data, loading, error };
}

/** Shablonni solishtirish uchun kanonik JSON: kalit tartibi va server normalizatsiyasi (v, nom, parametr sarlavhasi) farqi hisobga olinmaydi. */
export function canonJson(t: LabelTemplate | null | undefined): string {
  if (!t) return "";
  const sort = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(sort);
    if (v && typeof v === "object") {
      return Object.fromEntries(Object.entries(v as Record<string, unknown>).sort(([a], [b]) => (a < b ? -1 : 1)).map(([k, x]) => [k, sort(x)]));
    }
    return v;
  };
  const n = { ...t, v: 1, name: t.name ?? "", size: { w: t.size?.w, h: t.size?.h }, params: (t.params ?? []).map((p) => ({ ...p, title: p.title ?? "" })),
    vars: t.vars ?? [], elements: t.elements ?? [] };
  return JSON.stringify(sort(n));
}

/** SVG matnini xavfsiz tekshirib, hujjatga qo'shishga tayyor element qaytaradi (server o'zi ham escape qiladi — chuqur himoya). */
export function sanitizeSvg(text: string): SVGSVGElement | null {
  if (!text) return null;
  const doc = new DOMParser().parseFromString(text, "image/svg+xml");
  if (doc.querySelector("parsererror")) return null;
  const root = doc.documentElement;
  if (root.tagName.toLowerCase() !== "svg") return null;
  const BAD = new Set(["script", "foreignobject", "iframe", "object", "embed", "style", "link", "use"]);
  const walk = (node: Element) => {
    for (const child of Array.from(node.children)) {
      if (BAD.has(child.tagName.toLowerCase())) { child.remove(); continue; }
      walk(child);
    }
    for (const at of Array.from(node.attributes)) {
      const n = at.name.toLowerCase();
      if (n.startsWith("on")) node.removeAttribute(at.name);
      else if ((n === "href" || n === "xlink:href") && !/^data:image\/(png|jpeg);base64,/i.test(at.value)) node.removeAttribute(at.name);
    }
  };
  walk(root);
  return document.importNode(root, true) as unknown as SVGSVGElement;
}
