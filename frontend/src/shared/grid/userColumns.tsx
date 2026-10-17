// Foydalanuvchi ustunlari (jadval «Настройки» → «Свойства» / «Добавить» / «Удалить»): «Настроенный Параметры» — qiymat har qatorda
// `user_params[nom]` da MATN sifatida saqlanadi (tahrirlanadi); «Выражение» — qator maydonlari va parametrlaridan serverda hisoblanadi
// (`POST /expr/eval-rows`, faqat o'qish; ikkinchi dvigatel yo'q). Ustun turi (Строковой / Целое / Дробное / Логический) — ko'rinish va tahrir.
import { useEffect, useMemo, useRef, useState } from "react";
import type { ColDef, ITooltipParams } from "ag-grid-community";
import { post } from "../../api/client";
import { parseCellNum } from "./Grid";

export type UserColKind = "param" | "expr";
export type UserColType = "string" | "int" | "double" | "bool";
/** Profildagi foydalanuvchi ustuni (kalit = parametr nomi, masalan «material.name1»). */
export interface UserCol { kind: UserColKind; vtype: UserColType; desc?: string; expr?: string }
/** «Vs» ro'yxatidagi o'zgaruvchi: ifodaga qo'yiladigan nom va izoh. */
export interface ExprVar { name: string; label: string }
/** Profil ustuni (umumiy ko'rinish): foydalanuvchi ustunida `user` bor. */
export interface UserColSetting { key: string; visible: boolean; title?: string; width?: number; user?: UserCol }

/** Parametr nomi — ifoda tilidagi o'zgaruvchi (backend `USER_PARAM_NAME_RE` bilan bir xil): «part.name1», «material.rang». */
export const PARAM_NAME_RE = /^[\p{L}_][\p{L}\p{N}_]*(?:\.[\p{L}_][\p{L}\p{N}_]*)*$/u;
export const PARAM_NAME_MAX = 40;

/** Prefiks bo'yicha keyingi bo'sh nom: «material.name1», «material.name2» … */
export function nextParamName(prefix: string, taken: Iterable<string>): string {
  const s = new Set(taken);
  for (let i = 1; ; i++) { const n = `${prefix}.name${i}`; if (!s.has(n)) return n; }
}

const TRUE = new Set(["true", "1", "да", "ha", "yes", "y", "+", "✓", "x"]);
export const toBool = (v: unknown) => (typeof v === "boolean" ? v : typeof v === "number" ? v !== 0
  : TRUE.has(String(v ?? "").trim().toLowerCase()));

/** Saqlangan matn (yoki ifoda natijasi) → ustun turidagi qiymat (ko'rsatish / tahrir). Son bo'lmagan matn — o'zicha. */
export function typed(vtype: UserColType, raw: unknown): unknown {
  if (raw === undefined || raw === null || raw === "") return vtype === "bool" ? false : null;
  if (vtype === "bool") return toBool(raw);
  if (vtype === "int" || vtype === "double") {
    const n = typeof raw === "number" ? raw : typeof raw === "boolean" ? (raw ? 1 : 0) : parseCellNum(raw);
    if (n === null) return String(raw);
    return vtype === "int" ? Math.trunc(n) : n;
  }
  return typeof raw === "boolean" ? (raw ? "true" : "false") : String(raw);
}

/** Kiritilgan qiymat → saqlanadigan matn ("" — parametr o'chiriladi); son kutilgan joyda son bo'lmasa — null (o'zgarmaydi). */
export function stored(vtype: UserColType, v: unknown): string | null {
  if (v === null || v === undefined || v === "") return "";
  if (vtype === "bool") return toBool(v) ? "true" : "false";
  if (vtype === "int" || vtype === "double") {
    const n = typeof v === "number" ? v : parseCellNum(v);
    if (n === null) return null;
    return String(vtype === "int" ? Math.round(n) : n);
  }
  return String(v).slice(0, 1000);
}

/** Jadval qatorlari manbai: qator kaliti, parametrlar (o'qish / yozish), ifoda o'zgaruvchilari. `useMemo` bilan bering. */
export interface UserColsSource<T> {
  /** «Наименование» prefiksi: «part», «material» */
  prefix: string;
  rows: T[];
  rowKey: (r: T) => string;
  params: (r: T) => Record<string, string> | undefined;
  /** tahrirda qator obyektini darhol yangilash (javob kelguncha katak eski qiymatni ko'rsatmasin) */
  setParams?: (r: T, next: Record<string, string>) => void;
  /** qatorning o'rnatilgan o'zgaruvchilari (ifoda konteksti): nom → qiymat */
  vars: (r: T) => Record<string, unknown>;
  /** «Vs» ro'yxati (o'rnatilgan o'zgaruvchilar; parametrlar avtomatik qo'shiladi) */
  varList: ExprVar[];
  /** katak tahrirlanadimi */
  editable?: (r: T) => boolean;
}

/** Ustun konteksti: jadvallarning `onCellValueChanged` i `patch` orqali saqlaydi (detallar — batch-update, O — butun jadval). */
export interface UserColContext<T = unknown> { userParam: string; patch: (v: unknown, d: T) => Record<string, unknown> }

type ExprRes = { error: string | null; values: unknown[]; errors: (string | null)[] };
const MAX_CTX_TEXT = 1000;

function ctxValue(v: unknown): unknown {
  if (v === null || typeof v === "boolean") return v;
  if (typeof v === "number") return Number.isFinite(v) && Math.abs(v) <= 1e15 ? v : undefined;
  if (typeof v === "string") return v.slice(0, MAX_CTX_TEXT);
  return undefined;
}

/** Qator konteksti: o'rnatilgan o'zgaruvchilar + foydalanuvchi parametrlari (matn; ifodada integer()/double()/boolean()).
 *  Profildagi parametr ustuni qatorda to'ldirilmagan bo'lsa — bo'sh matn (ifoda «noma'lum o'zgaruvchi» xatosiga tushmaydi). */
function rowContext<T>(src: UserColsSource<T>, r: T, paramNames: string[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  const put = (k: string, v: unknown) => {
    const x = ctxValue(v);
    if (x !== undefined && k && k.length <= 100 && Object.keys(out).length < 200) out[k] = x;
  };
  for (const [k, v] of Object.entries(src.vars(r))) put(k, v);
  const up = src.params(r) ?? {};
  for (const k of paramNames) if (!(k in up)) put(k, "");
  for (const [k, v] of Object.entries(up)) put(k, v);
  return out;
}

/** «Выражение» ustunlarini serverda hisoblash: kechiktirib (yozish paytida har belgi uchun emas), eskirgan javob tashlanadi. */
function useExprRows(exprs: string[], keys: string[], ctxs: Record<string, unknown>[]) {
  const body = useMemo(() => (exprs.length && ctxs.length ? JSON.stringify({ exprs, rows: ctxs }) : ""), [exprs, ctxs]);
  const [res, setRes] = useState<{ body: string; idx: Map<string, number>; results: ExprRes[] } | null>(null);
  const seq = useRef(0);
  useEffect(() => {
    if (!body) return;
    const my = ++seq.current;
    const idx = new Map(keys.map((k, i) => [k, i]));
    const h = setTimeout(() => {
      post<{ results: ExprRes[] }>("/expr/eval-rows", JSON.parse(body))
        .then((r) => { if (my === seq.current) setRes({ body, idx, results: r.results }); })
        .catch(() => { if (my === seq.current) setRes(null); });
    }, 120);
    return () => clearTimeout(h);
  }, [body]); // eslint-disable-line react-hooks/exhaustive-deps
  return body ? res : null;
}

/** Profil ustunlaridan foydalanuvchi ustunlari ColDef lari (`build`) va «Vs» ro'yxati. */
export function useUserColumns<T>(settings: UserColSetting[], src: UserColsSource<T> | undefined) {
  const exprCols = useMemo(() => (src ? settings.filter((s) => s.visible && s.user?.kind === "expr") : []), [settings, src]);
  const exprs = useMemo(() => exprCols.map((s) => s.user?.expr ?? ""), [exprCols]);
  const rows = src?.rows;
  // katak tahririda qator obyekti joyida yangilanadi (`setParams`); server javobi tuzilmaviy ulashish (structural sharing) tufayli
  // o'sha obyektlarni qaytarishi mumkin — ifodalar konteksti shu hisoblagich bilan qayta tuziladi
  const [ver, setVer] = useState(0);
  const keys = useMemo(() => (src && exprs.length ? src.rows.map(src.rowKey) : []), [rows, exprs.length]); // eslint-disable-line react-hooks/exhaustive-deps
  const paramKey = settings.filter((s) => s.user?.kind === "param").map((s) => s.key).join("|");
  const ctxs = useMemo(() => {
    const names = paramKey ? paramKey.split("|") : [];
    return src && exprs.length ? src.rows.map((r) => rowContext(src, r, names)) : [];
  }, [rows, src, exprs.length, paramKey, ver]); // eslint-disable-line react-hooks/exhaustive-deps
  const res = useExprRows(exprs, keys, ctxs);

  const varList = useMemo<ExprVar[]>(() => {
    if (!src) return [];
    const params = settings.filter((s) => s.user?.kind === "param").map((s) => ({ name: s.key, label: s.title || s.user?.desc || "" }));
    return [...src.varList, ...params];
  }, [src, settings]);

  const build = useMemo(() => (s: UserColSetting): ColDef<T> | null => {
    const u = s.user;
    if (!u || !src) return null;
    const name = s.key;
    const base: ColDef<T> = { colId: name, headerName: s.title || name, headerTooltip: u.desc || s.title || name };
    const typedCls = u.vtype === "bool" ? "center" : u.vtype === "string" ? "" : "num";
    const look: Partial<ColDef<T>> = u.vtype === "bool"
      ? { cellRenderer: "agCheckboxCellRenderer", cellEditor: "agCheckboxCellEditor" }
      : u.vtype === "string" ? {} : { headerClass: "ag-right-aligned-header" };
    if (u.kind === "param") {
      const ctx: UserColContext<T> = {
        userParam: name,
        patch: (v, d) => {
          const st = stored(u.vtype, v) ?? "";
          const next = { ...(src.params(d) ?? {}) };
          if (st === "") delete next[name]; else next[name] = st;
          return { user_params: next };
        },
      };
      return {
        ...base, ...look, cellClass: `${typedCls} user-col`.trim(), context: ctx,
        editable: (p) => !!p.data && (src.editable?.(p.data) ?? true),
        valueGetter: (p) => (p.data ? typed(u.vtype, src.params(p.data)?.[name]) : null),
        valueSetter: (p) => {
          if (!p.data) return false;
          const st = stored(u.vtype, p.newValue);
          if (st === null) return false;                       // son kutilgan joyda matn — qiymat o'zgarmaydi
          const cur = src.params(p.data) ?? {};
          if ((cur[name] ?? "") === st) return false;
          const next = { ...cur };
          if (st === "") delete next[name]; else next[name] = st;
          src.setParams?.(p.data, next);
          setVer((v) => v + 1);
          return true;
        },
      };
    }
    // «Выражение»: faqat o'qish; xato — «⚠» va maslahatda matni
    const i = exprCols.findIndex((c) => c.key === name);
    const cell = (d: T | undefined): { v: unknown; err: string | null } => {
      if (!d || i < 0 || !res) return { v: null, err: null };
      const r = res.results[i];
      if (!r) return { v: null, err: null };
      if (r.error) return { v: null, err: r.error };
      const j = res.idx.get(src.rowKey(d));
      if (j === undefined) return { v: null, err: null };
      return { v: r.values[j], err: r.errors[j] };
    };
    return {
      ...base, ...look, editable: false, context: { userExpr: true },
      cellClass: (p) => `${typedCls} user-col user-expr${cell(p.data).err ? " warn" : ""}`.trim(),
      valueGetter: (p) => {
        const c = cell(p.data);
        if (c.err) return u.vtype === "bool" ? false : "⚠";
        return c.v === null || c.v === undefined ? (u.vtype === "bool" ? false : null) : typed(u.vtype, c.v);
      },
      tooltipValueGetter: (p: ITooltipParams<T>) => cell(p.data).err ?? (u.expr ? `= ${u.expr}` : ""),
    };
  }, [src, exprCols, res]);

  return { build, varList };
}
