// LB `source=user` — «Пользовательские данные»: maydonlar sxemasi + qatorlar jadvali (Excel Ctrl+V bilan qo'yish); shu ma'lumotdan etiketka chop etiladi.
// Qiymatlar matn bo'lib saqlanadi; chop paytida server maydon turiga keltiradi (Excel «1 234,5» → 1234.5).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ClipboardPaste, Copy, Plus, Trash, WandSparkles } from "lucide-react";
import type { LBParams } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Sel, Txt, cx } from "../../shared/ui";
import { lbSize } from "./labelsApi";
import type { Lang } from "../../i18n/lang";
import { pickLang } from "../../i18n/lang";

export interface UField { name: string; title: string; type: "string" | "integer" | "double" | "boolean"; default?: string | number | boolean | null; width?: number }
type Row = Record<string, unknown>;
const NAME_RE = /^[A-Za-z_][A-Za-z0-9_]{0,30}$/;
const TYPES: UField["type"][] = ["string", "integer", "double", "boolean"];
const PAGE = 100;
const MAX_ROWS = 10000;
const MAX_FIELDS = 50;

/** Excel/TSV matn → jadval (qo'shtirnoqli katakchalar, ichida tab va qator ko'chirish bo'lishi mumkin). */
export function parseTsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], cell = "", q = false;
  const s = text.replace(/\r\n?/g, "\n");
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (q) {
      if (ch === '"') { if (s[i + 1] === '"') { cell += '"'; i++; } else q = false; }
      else cell += ch;
    } else if (ch === '"' && cell === "") q = true;
    else if (ch === "\t") { row.push(cell); cell = ""; }
    else if (ch === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
    else cell += ch;
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  while (rows.length && rows[rows.length - 1].every((c) => c === "")) rows.pop();
  return rows;
}

/** Sarlavhadan identifikator: lotin harf/raqam/«_»; kirill va boshqalar — «f<N>». */
export function fieldName(title: string, taken: Set<string>, n: number): string {
  let base = title.trim().replace(/[^A-Za-z0-9_]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 24);
  if (!base || /^\d/.test(base)) base = `f${n}`;
  let name = base, k = 2;
  while (taken.has(name)) name = `${base}_${k++}`;
  return name;
}

/** Maydonlar bo'yicha oddiy shablon: sarlavha, qatorlar va (birinchi maydon bo'sh bo'lmasa) QR. */
export function userTemplate(fields: UField[], w: number, h: number, lang: Lang = "ru"): Record<string, unknown> {
  const pad = 2;
  const qr = Math.max(8, Math.min(h * 0.4, 16));
  const first = fields[0];
  const els: Record<string, unknown>[] = [];
  if (first) els.push({ t: "text", x: pad, y: pad, size: 4.2, bold: true, maxw: `label.width - ${pad * 2} - ${qr + 1}`, text: first.type === "string" ? `user.${first.name}` : `''+user.${first.name}` });
  fields.slice(1, 8).forEach((f, i) => {
    const title = (f.title || f.name).replace(/'/g, "").slice(0, 24);
    els.push({ t: "text", x: pad, y: pad + 7.2 + i * 4.3, size: 2.7, maxw: `label.width - ${pad * 2} - ${qr + 1}`, text: `'${title}: '+user.${f.name}` });
  });
  if (first) els.push({ t: "if", cond: `len(''+user.${first.name}) > 0`, then: [{ t: "barcode", kind: "qr", x: `label.width - ${pad} - ${qr}`, y: `label.height - ${pad} - ${qr}`, size: qr, data: `''+user.${first.name}` }] });
  return { v: 1, name: pickLang(lang, "Пользовательские данные", "Foydalanuvchi ma'lumotlari"), size: { w, h }, params: [], vars: [], elements: els };
}

export const defaultUserFields = (lang: Lang): UField[] => [
  { name: "title", title: pickLang(lang, "Наименование", "Nomi"), type: "string", default: null },
  { name: "code", title: pickLang(lang, "Код", "Kod"), type: "string", default: null },
];

interface Props { lb: LBParams; lang: Lang; onChange: (p: Partial<LBParams>) => void | Promise<unknown>; onOpenDesigner?: () => void }

export function UserDataTab({ lb, lang, onChange, onOpenDesigner }: Props) {
  const { t } = useTranslation();
  const toast = useUI((s) => s.toast);
  const fieldsIn = useMemo(() => (lb.fields as unknown as UField[]) ?? [], [lb.fields]);
  const [fields, setFields] = useState<UField[]>(fieldsIn);
  const [rows, setRows] = useState<Row[]>((lb.data as Row[]) ?? []);
  const [page, setPage] = useState(0);
  const [header, setHeader] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pending = useRef<Partial<LBParams> | null>(null);
  const last = useRef({ f: JSON.stringify(lb.fields), d: JSON.stringify(lb.data) });
  const tableRef = useRef<HTMLTableElement>(null);

  // tashqi o'zgarish (boshqa operatsiya/yuklash) — mahalliy nusxani yangilaymiz; o'zimiz yuborganimiz — e'tiborsiz
  useEffect(() => {
    const f = JSON.stringify(lb.fields), d = JSON.stringify(lb.data);
    if (pending.current) return;
    if (f !== last.current.f) { setFields((lb.fields as unknown as UField[]) ?? []); last.current.f = f; }
    if (d !== last.current.d) { setRows((lb.data as Row[]) ?? []); last.current.d = d; }
  }, [lb.fields, lb.data]);

  const flush = () => {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    const p = pending.current;
    if (!p) return;
    pending.current = null;
    void Promise.resolve(onChange(p));
  };
  const flushRef = useRef(flush);
  flushRef.current = flush;
  useEffect(() => () => flushRef.current(), []);

  const fieldsOk = (fs: UField[]): boolean => {
    const seen = new Set<string>();
    for (const f of fs) { if (!NAME_RE.test(f.name) || seen.has(f.name)) return false; seen.add(f.name); }
    return fs.length <= MAX_FIELDS;
  };
  const commit = (next: { fields?: UField[]; data?: Row[] }) => {
    const p: Partial<LBParams> = { ...(pending.current ?? {}) };
    if (next.fields) { setFields(next.fields); if (fieldsOk(next.fields)) { p.fields = next.fields as unknown as Record<string, unknown>[]; last.current.f = JSON.stringify(next.fields); } }
    if (next.data) { setRows(next.data); p.data = next.data; last.current.d = JSON.stringify(next.data); }
    pending.current = p;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(flush, 500);
  };

  const names = fields.map((f) => f.name);
  const dup = (f: UField) => names.filter((n) => n === f.name).length > 1;
  const total = rows.reduce((s, r) => { const q = Number(String(r.qty ?? 1).replace(",", ".")); return s + (Number.isFinite(q) && q > 0 ? Math.floor(q) : 0); }, 0);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const pg = Math.min(page, pages - 1);
  const slice = rows.slice(pg * PAGE, pg * PAGE + PAGE);

  const setCell = (ri: number, key: string, v: unknown) => {
    const next = rows.slice();
    next[ri] = { ...next[ri], [key]: v };
    commit({ data: next });
  };
  const addField = () => {
    if (fields.length >= MAX_FIELDS) return;
    const taken = new Set(names);
    const n = fieldName("", taken, fields.length + 1);
    commit({ fields: [...fields, { name: n, title: `${t("lbu.field")} ${fields.length + 1}`, type: "string", default: null }] });
  };
  const setField = (i: number, patch: Partial<UField>) => commit({ fields: fields.map((f, j) => (j === i ? { ...f, ...patch } : f)) });
  const delField = (i: number) => {
    const f = fields[i];
    commit({ fields: fields.filter((_x, j) => j !== i), data: rows.map((r) => { const { [f.name]: _drop, ...rest } = r; return rest; }) });
  };
  const addRow = () => {
    if (rows.length >= MAX_ROWS) return;
    commit({ data: [...rows, { qty: 1 }] });
    setPage(Math.floor(rows.length / PAGE));
  };
  const delRow = (ri: number) => commit({ data: rows.filter((_r, j) => j !== ri) });

  /** Jadvalga matn qo'yish: (r0, c0) dan boshlab (c0=0 — «Кол-во» ustuni). Yetishmagan qator/maydonlar yaratiladi. */
  const pasteAt = (text: string, r0: number, c0: number) => {
    let table = parseTsv(text);
    if (!table.length) return;
    let fs = fields.slice();
    const data = rows.map((r) => ({ ...r }));
    let titles: string[] | null = null;
    if (header && table.length > 1) { titles = table[0]; table = table.slice(1); }
    const width = Math.max(...table.map((r) => r.length), titles?.length ?? 0);
    // ustunlar: 0 — qty, 1.. — maydonlar
    const need = c0 + width - 1;
    while (fs.length < need && fs.length < MAX_FIELDS) {
      const i = fs.length;
      const tt = titles?.[i + 1 - c0]?.trim() ?? "";
      fs.push({ name: fieldName(tt, new Set(fs.map((f) => f.name)), i + 1), title: tt || `${t("lbu.field")} ${i + 1}`, type: "string", default: null });
    }
    if (titles) titles.forEach((tt, j) => { const fi = c0 - 1 + j; if (fi >= 0 && fs[fi] && tt.trim()) fs[fi] = { ...fs[fi], title: tt.trim() }; });
    table.forEach((cells, i) => {
      const ri = r0 + i;
      if (ri >= MAX_ROWS) return;
      while (data.length <= ri) data.push({ qty: 1 });
      cells.forEach((v, j) => {
        const ci = c0 + j;
        if (ci === 0) { const n = parseInt(v.replace(/\s/g, ""), 10); data[ri].qty = Number.isFinite(n) && n >= 0 ? n : 1; }
        else if (fs[ci - 1]) data[ri][fs[ci - 1].name] = fs[ci - 1].type === "boolean" ? /^(1|true|да|yes|ha|\+|x)$/i.test(v.trim()) : v;
      });
    });
    commit({ fields: fs, data });
    toast(t("lbu.pasted", { n: table.length }), "ok");
  };
  const onPaste = (e: React.ClipboardEvent) => {
    const el = e.target as HTMLElement;
    const text = e.clipboardData.getData("text");
    const inCell = el instanceof HTMLInputElement && el.dataset.r !== undefined;
    if (!inCell || !/[\t\n]/.test(text.trim())) return;           // bitta qiymat — oddiy qo'yish
    e.preventDefault();
    pasteAt(text, pg * PAGE + Number(el.dataset.r), Number(el.dataset.c));
  };
  const pasteClipboard = async () => {
    try { pasteAt(await navigator.clipboard.readText(), rows.length, 0); }
    catch { toast(t("lbu.paste_denied"), "error"); }
  };

  const usesUser = JSON.stringify(lb.template ?? "").includes("user.");
  const makeTemplate = () => {
    const ok = fields.filter((f) => NAME_RE.test(f.name));
    void onChange({ template: userTemplate(ok, lbSize(lb).w, lbSize(lb).h, lang), template_id: null, params: {} });
  };

  return (
    <div className="lbu" data-testid="lbu">
      <p className="muted small">{t("lbu.hint")}</p>
      {!usesUser && fields.length > 0 && (
        <div className="lbx-copy row gap" data-testid="lbu-notpl">
          <span>{t("lbu.no_template")}</span>
          <Btn small icon={WandSparkles} label={t("lbu.make_template")} onClick={makeTemplate} testid="lbu-make-template" />
          {onOpenDesigner && <Btn small label={t("lbu.open_designer")} onClick={onOpenDesigner} testid="lbu-open-designer" />}
        </div>)}

      <div className="form-h row">{t("lbu.fields")}<span className="grow" />
        <Btn small icon={Plus} label={t("lbu.add_field")} onClick={addField} testid="lbu-add-field" disabled={fields.length >= MAX_FIELDS} /></div>
      {fields.length > 0 && (
        <table className="lbx-table lbu-fields" data-testid="lbu-fields">
          <thead><tr><th>{t("lbu.f_name")}</th><th>{t("lbu.f_title")}</th><th>{t("lbu.f_type")}</th><th>{t("lbu.f_default")}</th><th /></tr></thead>
          <tbody>{fields.map((f, i) => (
            <tr key={i} data-testid="lbu-field">
              <td><Txt value={f.name} width="100%" testid={`lbu-fname-${i}`} onCommit={(s) => setField(i, { name: s.trim() })} />
                {(!NAME_RE.test(f.name) || dup(f)) && <div className="lbx-bad small" data-testid="lbu-fname-bad">{t("lbu.name_bad")}</div>}</td>
              <td><Txt value={f.title} width="100%" testid={`lbu-ftitle-${i}`} onCommit={(s) => setField(i, { title: s })} /></td>
              <td><Sel<string> value={f.type} width={96} onChange={(v) => setField(i, { type: v as UField["type"] })} options={TYPES.map((x) => ({ value: x, label: x }))} testid={`lbu-ftype-${i}`} /></td>
              <td><Txt value={f.default === null || f.default === undefined ? "" : String(f.default)} width={80} onCommit={(s) => setField(i, { default: s === "" ? null : s })} /></td>
              <td className="lbx-w-act"><button type="button" className="ibtn" title={t("app.delete")} onClick={() => delField(i)}><Trash size={14} /></button></td>
            </tr>))}</tbody>
        </table>)}
      {fields.length > 0 && (
        <div className="lbu-chips">{fields.filter((f) => NAME_RE.test(f.name)).map((f) => (
          <button type="button" key={f.name} className="lbx-chip" title={t("lb.copied", { s: `user.${f.name}` })}
            onClick={() => { void navigator.clipboard?.writeText(`user.${f.name}`); toast(t("lb.copied", { s: `user.${f.name}` }), "ok"); }}>
            <Copy size={10} /> user.{f.name}</button>))}</div>)}

      <div className="form-h row">{t("lbu.rows")}<span className="grow" />
        <Check checked={header} label={t("lbu.header_row")} onChange={setHeader} testid="lbu-header" />
        <Btn small icon={ClipboardPaste} label={t("lbu.paste")} title={t("lbu.paste_hint")} onClick={() => void pasteClipboard()} testid="lbu-paste" />
        <Btn small icon={Plus} label={t("lbu.add_row")} onClick={addRow} testid="lbu-add-row" disabled={rows.length >= MAX_ROWS} />
        <Btn small label={t("lbu.clear")} onClick={() => commit({ data: [] })} disabled={!rows.length} testid="lbu-clear" /></div>
      <div className="muted small" data-testid="lbu-count">{t("lbu.count", { rows: rows.length, labels: total })}</div>
      {fields.length === 0 && <p className="muted">{t("lbu.no_fields")}</p>}
      <div className="lbu-grid-wrap">
        <table className="lbx-table lbu-grid" ref={tableRef} onPaste={onPaste} data-testid="lbu-grid">
          <thead><tr><th className="lbx-n">№</th><th className="lbu-qty">{t("lbu.qty")}</th>{fields.map((f, i) => <th key={i} title={`user.${f.name}`}>{f.title || f.name}</th>)}<th /></tr></thead>
          <tbody>{slice.map((r, k) => {
            const ri = pg * PAGE + k;
            return (
              <tr key={ri} data-testid="lbu-row">
                <td className="lbx-n">{ri + 1}</td>
                <td><Cell value={String(r.qty ?? 1)} r={k} c={0} onCommit={(v) => { const n = parseInt(v.replace(/\s/g, ""), 10); setCell(ri, "qty", Number.isFinite(n) && n >= 0 ? n : 1); }} testid={`lbu-cell-${ri}-qty`} narrow /></td>
                {fields.map((f, ci) => (
                  <td key={ci}>{f.type === "boolean"
                    ? <input type="checkbox" checked={Boolean(r[f.name])} onChange={(e) => setCell(ri, f.name, e.target.checked)} />
                    : <Cell value={r[f.name] === undefined || r[f.name] === null ? "" : String(r[f.name])} r={k} c={ci + 1} onCommit={(v) => setCell(ri, f.name, v)} testid={`lbu-cell-${ri}-${f.name}`} />}</td>))}
                <td className="lbx-w-act"><button type="button" className="ibtn" title={t("app.delete")} onClick={() => delRow(ri)}><Trash size={13} /></button></td>
              </tr>);
          })}</tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="row gap lbu-pager">
          <Btn small label="‹" onClick={() => setPage(Math.max(0, pg - 1))} disabled={pg === 0} />
          <span className="muted">{pg + 1} / {pages}</span>
          <Btn small label="›" onClick={() => setPage(Math.min(pages - 1, pg + 1))} disabled={pg >= pages - 1} />
        </div>)}
    </div>
  );
}

function Cell({ value, onCommit, r, c, testid, narrow }: { value: string; onCommit: (v: string) => void; r: number; c: number; testid: string; narrow?: boolean }) {
  const [s, setS] = useState(value);
  useEffect(() => { setS(value); }, [value]);
  return (
    <input className={cx("inp", narrow && "lbu-narrow")} value={s} data-r={r} data-c={c} data-testid={testid}
      onChange={(e) => setS(e.target.value)} onBlur={() => { if (s !== value) onCommit(s); }}
      onKeyDown={(e) => { if (e.key === "Enter") { if (s !== value) onCommit(s); (e.target as HTMLInputElement).blur(); } }} />
  );
}
