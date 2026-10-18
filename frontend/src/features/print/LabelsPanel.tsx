// LB — Этикетки (W4): parametrlar, shablon (jadval + JSON), jonli ko'rish, chop; kroy kartalari miniatyurasi (A4 da 4/6).
// `LbPanel` — loyiha operatsiyasi (LB) paneli; `LabelsPrint` — «Печать отчета → Этикетки» (operatsiyasiz, qoralama parametrlar).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ArrowDown, ArrowUp, ChevronDown, ChevronUp, CircleQuestionMark, Copy, ExternalLink, FilePlus, Pencil, Plus, Printer, RefreshCw, SaveAll, Trash, FileUp } from "lucide-react";
import { call, qc, useDefaults, useProject } from "../../api/hooks";
import { del, fetchHtml, openHtml, patch, post, put } from "../../api/client";
import type { LBParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText, showError } from "../../shared/dialogs";
import { Btn, Check, Dropdown, Empty, Field, IconBtn, Num, Sel, Tabs, Txt, cx } from "../../shared/ui";
import {
  CHILD_KEYS, DEFAULT_LB, DEFAULT_TEMPLATE_ID, LB_MARGIN_MM, NEW_ELEMENTS, borderKind, lbAutoSize, lbSize, cloneTpl, selectedOnly, fieldMap, flatten, getField, locate, setField, useLabelVars,
  useTemplate, useTemplates,
  type ElPath, type LabelIssue, type LabelTemplate, type LbPreview, type TplElement, type TplMeta,
} from "./labelsApi";
import { LabelFileTools } from "./LabelImport";
import { LabelDesigner } from "./designer/LabelDesigner";
import { UserDataTab, defaultUserFields, fieldName, userTemplate, type UField } from "./UserData";
import { openHelp } from "../help/helpStore";
import { ZplDialog } from "./ZplDialog";
import "./labels.css";
import { isLang, PRINT_LANGS, type Lang } from "../../i18n/lang";

type Tab = "params" | "template" | "designer" | "data" | "maps";
const asTpl = (t: LabelTemplate | null | undefined) => (t ?? null) as unknown as Record<string, unknown> | null;

interface EditorProps {
  project: Project;
  lb: LBParams;
  onChange: (patch: Partial<LBParams>) => void | Promise<unknown>;
  header?: ReactNode;
  onSaveDefaults?: () => void;
}

// ───────────────────────── Muharrir (parametrlar + shablon + ko'rish) ─────────────────────────
export function LabelsEditor({ project, lb, onChange, header, onSaveDefaults }: EditorProps) {
  const { t, i18n } = useTranslation();
  const [tab, setTab] = useState<Tab>("params");
  const [lang, setLang] = useState<Lang>(isLang(i18n.language) ? i18n.language : "ru");
  const [prev, setPrev] = useState<LbPreview | null>(null);
  const [prevErr, setPrevErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [stamp, setStamp] = useState(0);
  const [mapHtml, setMapHtml] = useState("");
  const [perPage, setPerPage] = useState<4 | 6>(4);
  const [mapOp, setMapOp] = useState("");
  const [printHtml, setPrintHtml] = useState("");
  const [printKey, setPrintKey] = useState(0);
  const printFrame = useRef<HTMLIFrameElement>(null);
  const [zplOpen, setZplOpen] = useState(false);
  const csOps = project.operations.filter((o) => o.type === "CS" || o.type === "CL");      // etiketka manbai: CS va CL (W18)
  useEffect(() => { if (tab === "data" && lb.source !== "user") setTab("params"); }, [tab, lb.source]);

  // jonli ko'rish: birinchi etiketkalar + xatolar (debounce)
  useEffect(() => {
    if (tab === "maps" || tab === "designer") return;
    let alive = true;
    setBusy(true);
    const h = setTimeout(() => {
      post<LbPreview>(`/projects/${project.id}/lb/preview`, { lb }, { lang })
        .then((r) => { if (alive) { setPrev(r); setPrevErr(""); } })
        .catch((e: unknown) => { if (alive) setPrevErr(e instanceof Error ? e.message : String(e)); })
        .finally(() => { if (alive) setBusy(false); });
    }, 250);
    return () => { alive = false; clearTimeout(h); };
  }, [project, JSON.stringify(lb), lang, stamp, tab]); // eslint-disable-line react-hooks/exhaustive-deps

  // kartalar miniatyurasi (A4 da 4/6)
  useEffect(() => {
    if (tab !== "maps") return;
    let alive = true;
    setBusy(true);
    fetchHtml(`/projects/${project.id}/map-sheets`, { per_page: perPage, op_id: mapOp || undefined, lang })
      .then((h) => { if (alive) setMapHtml(h); })
      .catch(() => undefined)
      .finally(() => { if (alive) setBusy(false); });
    return () => { alive = false; };
  }, [tab, project, perPage, mapOp, lang, stamp]);

  const errors = prev?.errors ?? [];
  const doPrint = async () => {
    try {
      let html: string;
      if (tab === "maps") html = await fetchHtml(`/projects/${project.id}/map-sheets`, { per_page: perPage, op_id: mapOp || undefined, lang });
      else {
        if (errors.length && !(await askConfirm(t("lb.print_with_errors"), t("lb.print_with_errors_text"), { ok: t("lb.print") }))) return;
        html = await fetchHtml(`/projects/${project.id}/lb/labels`, { lang }, lb);
      }
      setPrintHtml(html);
      setPrintKey((k) => k + 1);
    } catch (e) { showError(e); }
  };
  const openWin = async () => {
    try {
      if (tab === "maps") await openHtml(`/projects/${project.id}/map-sheets`, { per_page: perPage, op_id: mapOp || undefined, lang });
      else await openHtml(`/projects/${project.id}/lb/labels`, { lang }, lb);
    } catch (e) { showError(e); }
  };

  const html = tab === "maps" ? mapHtml : prev?.html ?? "";
  const designer = tab === "designer";
  // «Печать», «Открыть», «Скачать ZPL» — oddiy rejimda o'ng panel tepasida, vizual redaktorda — uning asboblar qatorida
  const actions = (
    <>
      <Btn icon={Printer} kind="primary" label={t("lb.print")} onClick={() => void doPrint()} testid="lb-print"
        disabled={tab !== "maps" && prev !== null && (prev.total === 0 || prev.total > prev.max_labels)} />
      <Btn icon={ExternalLink} label={t("lb.open")} onClick={() => void openWin()} testid="lb-open" />
      {tab !== "maps" && <Btn icon={FileUp} label={t("lbz.btn")} title={t("lbz.btn_hint")} onClick={() => setZplOpen(true)} testid="lb-zpl" />}
    </>
  );
  return (
    <div className={cx("lbx", designer && "lbx-design")} data-testid="lb-editor">
      <div className="lbx-left">
        {header}
        <Tabs<Tab> value={tab} onChange={setTab} tabs={[
          { key: "params", label: t("lb.tab.params"), testid: "lb-tab-params" },
          { key: "template", label: t("lb.tab.template"), testid: "lb-tab-template" },
          { key: "designer", label: t("lb.tab.designer"), testid: "lb-tab-designer" },
          ...(lb.source === "user" ? [{ key: "data" as Tab, label: t("lb.tab.data"), testid: "lb-tab-data" }] : []),
          { key: "maps", label: t("lb.tab.maps"), testid: "lb-tab-maps" }]}
        right={<Sel<string> value={lang} width={92} onChange={(v) => setLang(isLang(v) ? v : "ru")}
          options={PRINT_LANGS} />} />
        <div className="lbx-body scroll">
          {tab === "params" && <ParamsTab lb={lb} onChange={onChange} csOps={csOps} counts={prev?.counts} pages={prev?.pages}
            onSaveDefaults={onSaveDefaults} lang={lang} />}
          {tab === "template" && <TemplateTab lb={lb} onChange={onChange} lang={lang} issues={errors} onOpenDesigner={() => setTab("designer")} />}
          {tab === "data" && <UserDataTab lb={lb} lang={lang} onChange={onChange} onOpenDesigner={() => setTab("designer")} />}
          {designer && <LabelDesigner project={project} lb={lb} lang={lang} onChange={onChange} actions={actions} />}
          {tab === "maps" && (
            <div className="checks-col">
              <p className="muted">{t("lb.maps_hint")}</p>
              <Field label={t("lb.maps_per")}>
                <Sel<number> value={perPage} width={90} onChange={(v) => setPerPage(v === 6 ? 6 : 4)} testid="lb-maps-per"
                  options={[{ value: 4, label: "4" }, { value: 6, label: "6" }]} /></Field>
              <Field label={t("lb.maps_op")}>
                <Sel value={mapOp} width={220} onChange={setMapOp}
                  options={[{ value: "", label: t("lb.all") }, ...csOps.map((o) => ({ value: o.id, label: o.name || o.code }))]} /></Field>
            </div>
          )}
        </div>
      </div>
      {zplOpen && <ZplDialog projectId={project.id} lb={lb} lang={lang} onClose={() => setZplOpen(false)} />}
      {!designer && <div className="lbx-right">
        <div className="toolbar">
          {actions}
          <IconBtn icon={RefreshCw} title={t("menu.refresh")} onClick={() => setStamp((s) => s + 1)} />
          {busy && <span className="muted">{t("app.loading")}</span>}
          <span className="grow" />
          {tab !== "maps" && prev && (
            <span className="muted" data-testid="lb-count">
              {t("lb.count_val", { n: prev.total, p: prev.pages })}{prev.truncated ? ` · ${t("lb.shown", { n: prev.rendered, t: prev.total })}` : ""}
            </span>
          )}
        </div>
        {prevErr && tab !== "maps" && <div className="lbx-issues lbx-issues-err" data-testid="lb-prev-error">{prevErr}</div>}
        {tab !== "maps" && prev && prev.total > prev.max_labels && (
          <div className="lbx-issues lbx-issues-err" data-testid="lb-too-many">{t("lb.too_many", { n: prev.total, max: prev.max_labels })}</div>)}
        {tab !== "maps" && prev && <Issues errors={errors} warnings={prev.warnings} />}
        <iframe title="labels" className="lbx-frame" srcDoc={html} sandbox="allow-same-origin allow-modals" data-testid="lb-frame" />
        {printHtml && (
          <iframe key={printKey} ref={printFrame} title="labels-print" className="lbx-print-frame" srcDoc={printHtml}
            sandbox="allow-same-origin allow-modals" onLoad={() => { printFrame.current?.contentWindow?.focus(); printFrame.current?.contentWindow?.print(); }} />
        )}
      </div>}
      {designer && printHtml && (
        <iframe key={printKey} ref={printFrame} title="labels-print" className="lbx-print-frame" srcDoc={printHtml}
          sandbox="allow-same-origin allow-modals" onLoad={() => { printFrame.current?.contentWindow?.focus(); printFrame.current?.contentWindow?.print(); }} />
      )}
    </div>
  );
}

function Issues({ errors, warnings }: { errors: LabelIssue[]; warnings: string[] }) {
  const { t } = useTranslation();
  if (!errors.length && !warnings.length) return null;
  return (
    <div className="lbx-issues" data-testid="lb-issues">
      {errors.length > 0 && <>
        <b className="lbx-bad">{t("lb.errors")} ({errors.length})</b>
        <ul>{errors.map((e, i) => (
          <li key={i} className="lbx-bad" data-testid="lb-issue">
            {e.path ? <b>#{e.path}</b> : null} {e.field} — {e.message}{e.expr ? <code> {e.expr}</code> : null}{(e.count ?? 1) > 1 ? ` ×${e.count}` : ""}
          </li>))}</ul>
        <div className="muted">{t("lb.errors_hint")}</div>
      </>}
      {warnings.length > 0 && <ul>{warnings.map((w, i) => <li key={i} className="lbx-warn">{w}</li>)}</ul>}
    </div>
  );
}

// ───────────────────────── Parametrlar ─────────────────────────
// Kuzatilgan tizimdagi kabi (2026-10-16): «Источник», «Печатать» (А4 / принтер), «Размер» (A4 da hisoblanadi — faqat ko'rsatiladi,
// rulonda kiritiladi), to'r (Столбцы / Строки / Промежуток / Поля страницы / Границы), «Количество»; asboblar qatori.
function ParamsTab({ lb, onChange, csOps, counts, pages, onSaveDefaults, lang }: {
  lb: LBParams; onChange: (p: Partial<LBParams>) => void | Promise<unknown>; csOps: Operation[];
  counts?: { total: number; parts: number; wastes: number; products: number }; pages?: number; onSaveDefaults?: () => void; lang: Lang;
}) {
  const { t } = useTranslation();
  const set = (p: Partial<LBParams>) => { void onChange(p); };
  const sheet = lb.mode === "sheet";
  const auto = lbAutoSize(lb);
  const size = lbSize(lb);
  const user = lb.source === "user";
  const ufields = (lb.fields as unknown as UField[]) ?? [];
  const [selF, setSelF] = useState(0);
  const tplId = lb.template_id ?? DEFAULT_TEMPLATE_ID;
  const base = useTemplate(lb.template ? null : tplId, lang);
  const current: LabelTemplate | null = (lb.template as unknown as LabelTemplate | null) ?? base.data?.template ?? null;
  const refreshLib = () => { void qc.invalidateQueries({ queryKey: ["label-templates"] }); void qc.invalidateQueries({ queryKey: ["label-template"] }); };
  /** Manba «Пользовательские данные»: birinchi marta tanlanganda standart maydonlar va ularni chop etadigan shablon yaratiladi (W15). */
  const setSource = (v: LBParams["source"]) => {
    if (v === "user" && lb.fields.length === 0) {
      const fields: UField[] = defaultUserFields(lang);
      set({ source: v, fields: fields as unknown as Record<string, unknown>[], template: userTemplate(fields, size.w, size.h, lang), template_id: null, params: {} });
    } else set({ source: v });
  };
  // «Пользов-кие данные» maydonlari: Вставить / Удалить / ↑↓ (qiymatlar — «Данные» varag'ida)
  const setFields = (fs: UField[], data?: Record<string, unknown>[]) =>
    set({ fields: fs as unknown as Record<string, unknown>[], ...(data ? { data } : {}) });
  const sel = Math.min(selF, Math.max(0, ufields.length - 1));
  const insertField = () => {
    if (!user || ufields.length >= 50) return;
    const name = fieldName("", new Set(ufields.map((f) => f.name)), ufields.length + 1);
    const at = ufields.length ? sel + 1 : 0;
    const next: UField[] = [...ufields.slice(0, at), { name, title: `${t("lbu.field")} ${ufields.length + 1}`, type: "string", default: null }, ...ufields.slice(at)];
    setFields(next);
    setSelF(at);
  };
  const deleteField = () => {
    const f = ufields[sel];
    if (!user || !f) return;
    setFields(ufields.filter((_x, j) => j !== sel), (lb.data as Record<string, unknown>[]).map((r) => { const { [f.name]: _drop, ...rest } = r; return rest; }));
    setSelF(Math.max(0, sel - 1));
  };
  const moveField = (d: -1 | 1) => {
    const j = sel + d;
    if (!user || j < 0 || j >= ufields.length) return;
    const next = ufields.slice();
    [next[sel], next[j]] = [next[j], next[sel]];
    setFields(next);
    setSelF(j);
  };
  const onKey = (e: React.KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
    if (e.ctrlKey && e.key === "PageUp") { e.preventDefault(); insertField(); }
    else if (e.key === "Delete") { e.preventDefault(); deleteField(); }
  };
  const parts = lb.source === "parts";
  const selOn = selectedOnly(lb);
  const userTip = user ? "" : ` — ${t("lb.tb.user_only")}`;
  return (
    <div className="lbp" data-testid="lb-params" onKeyDown={onKey}>
      <div className="toolbar lbp-toolbar" data-testid="lb-params-toolbar">
        <IconBtn icon={Plus} title={t("lb.tb.insert") + userTip} onClick={insertField} disabled={!user || ufields.length >= 50} testid="lb-tb-insert" />
        <IconBtn icon={Trash} title={t("lb.tb.delete") + userTip} onClick={deleteField} disabled={!user || !ufields.length} testid="lb-tb-delete" />
        <IconBtn icon={ArrowUp} title={t("lb.tb.up") + userTip} onClick={() => moveField(-1)} disabled={!user || sel <= 0} testid="lb-tb-up" />
        <IconBtn icon={ArrowDown} title={t("lb.tb.down") + userTip} onClick={() => moveField(1)} disabled={!user || sel >= ufields.length - 1} testid="lb-tb-down" />
        <span className="lbp-tb-sep" />
        <LabelFileTools compact current={current} lb={lb} lang={lang} refreshLib={refreshLib} onImported={(_id, patch) => set(patch)} />
        {onSaveDefaults && <IconBtn icon={SaveAll} title={t("lb.tb.defaults")} onClick={onSaveDefaults} testid="lb-save-defaults" />}
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => openHelp("flow")} testid="lb-tb-help" />
      </div>
      <div className="lbp-cols">
        {/* chap ustun: manba, chop turi, o'lcham, maket, soni */}
        <div className="lbp-col" data-testid="lb-params-left">
          <Field label={t("lb.source")}>
            <Sel<string> value={lb.source} width={190} testid="lb-source" onChange={(v) => setSource(v as LBParams["source"])}
              options={[{ value: "user", label: t("lb.src.user") }, { value: "products", label: t("lb.src.products") },
                { value: "parts", label: t("lb.src.parts") }]} /></Field>
          <div className="field lbp-top">
            <span className="field-label">{t("lb.print_mode")}</span>
            <span className="field-ctl radio-col" data-testid="lb-mode" role="radiogroup">
              {(["sheet", "roll"] as const).map((m) => (
                <label key={m} className="check"><input type="radio" name="lb-mode" checked={lb.mode === m} data-testid={`lb-mode-${m}`}
                  onChange={() => set({ mode: m })} /> {t(`lb.mode.${m}`)}</label>))}
            </span>
            <span className="field-unit" />
          </div>
          <Field label={t("lb.size")} unit={t("u.mm")} hint={auto ? t("lb.size_auto_hint") : sheet ? t("lb.size_legacy") : t("lb.size_hint")}>
            {auto ? (
              <span className="lbp-size" data-testid="lb-size-auto">
                <input className="inp" readOnly tabIndex={-1} value={`${fmtMm(size.w)}x${fmtMm(size.h)}`} style={{ width: 128 }} data-testid="lb-size-value" />
              </span>
            ) : (
              <span className="lbp-size">
                <Num value={lb.width_mm} min={5} max={500} width={58} testid="lb-width" onCommit={(v) => set({ width_mm: v ?? 58 })} />
                <span className="muted">x</span>
                <Num value={lb.height_mm} min={5} max={500} width={58} testid="lb-height" onCommit={(v) => set({ height_mm: v ?? 40 })} />
              </span>)}
          </Field>
          <Field label={t("lb.columns")} unit={t("u.pcs")}>
            <Num value={lb.columns} min={1} max={20} disabled={!sheet} testid="lb-columns" onCommit={(v) => set({ columns: Math.max(1, Math.round(v ?? 1)) })} /></Field>
          <Field label={t("lb.rows")} unit={t("u.pcs")} hint={t("lb.rows_hint")}>
            <Num value={lb.rows} min={1} max={50} disabled={!sheet} testid="lb-rows" onCommit={(v) => set({ rows: Math.max(1, Math.round(v ?? 1)) })} /></Field>
          <Field label={t("lb.gap")} unit={t("u.mm")}>
            <Num value={lb.gap_mm} min={0} max={50} disabled={!sheet} testid="lb-gap" onCommit={(v) => set({ gap_mm: v ?? 0 })} /></Field>
          <div className="lbp-margin">
            <Check checked={lb.margin_mm !== null} label={t("lb.margin_on")} disabled={!sheet} testid="lb-margin-on"
              onChange={(v) => set({ margin_mm: v ? LB_MARGIN_MM : null })} />
            {lb.margin_mm !== null && <>
              <Num value={lb.margin_mm} min={0} max={50} width={52} disabled={!sheet} testid="lb-margin"
                onCommit={(v) => set({ margin_mm: v ?? LB_MARGIN_MM })} />
              <span className="muted" title={t("lb.margin_mm_hint")}>{t("u.mm")}</span></>}
          </div>
          <Field label={t("lb.border")}>
            <Sel<string> value={borderKind(lb)} width={190} testid="lb-border"
              onChange={(v) => set({ border_mode: v === "none" ? "none" : "perimeter", border: v !== "none" })}
              options={[{ value: "none", label: t("lb.border_none") }, { value: "perimeter", label: t("lb.border_perimeter") }]} /></Field>
          <Field label={t("lb.count")} unit={<>{t("u.pcs")}{counts && sheet && (pages ?? 0) > 0 ? <span>· {t("lb.pages", { p: pages })}</span> : null}</>}
            hint={counts ? t("lb.count_detail", { parts: counts.parts, wastes: counts.wastes, products: counts.products }) : undefined}>
            <span data-testid="lb-count-box"><input className="inp num" readOnly tabIndex={-1} value={counts ? String(counts.total) : "…"}
              style={{ width: 70 }} data-testid="lb-count-total" /></span></Field>
        </div>
        {/* o'ng ustun: «Детали», «Остатки» (manba «Изделия» — «Изделия»; «Пользов-кие данные» — maydonlar ro'yxati) */}
        <div className="lbp-col" data-testid="lb-params-right">
          {parts && <>
            <div className="form-h">{t("lb.parts_h")}</div>
            <Check checked={lb.print_parts} label={t("lb.print_parts")} testid="lb-print-parts" onChange={(v) => set({ print_parts: v })} />
            <Check checked={lb.part_each} label={t("lb.part_each")} title={t("lb.part_each_hint")} disabled={!lb.print_parts}
              testid="lb-part-each" onChange={(v) => set({ part_each: v })} />
            <Check checked={lb.part_only_nonzero} label={t("lb.part_nonzero")} disabled={!lb.print_parts} testid="lb-part-nonzero"
              onChange={(v) => set({ part_only_nonzero: v })} />
            <Check checked={selOn} label={t("lb.selected")} disabled={!lb.print_parts} testid="lb-selected-only"
              onChange={(v) => set({ part_selected_only: v })} />
            {selOn && (
              <div className="lbp-sub">
                <span className="muted">{t("lb.selected_ids")}</span>
                <Txt value={lb.part_selected.join(", ")} width={200} placeholder={t("lb.selected_hint")} testid="lb-selected"
                  onCommit={(s) => set({ part_selected_only: true,
                    part_selected: s.split(/[\s,;]+/).map((x) => parseInt(x, 10)).filter((x) => Number.isFinite(x) && x > 0).slice(0, 20000) })} />
              </div>)}
            <div className="form-h">{t("lb.wastes_h")}</div>
            <Check checked={lb.print_wastes} label={t("lb.print_wastes")} onChange={(v) => set({ print_wastes: v })} testid="lb-print-wastes" />
            <Check checked={lb.waste_each} label={t("lb.waste_each")} title={t("lb.waste_each_hint")} disabled={!lb.print_wastes}
              testid="lb-waste-each" onChange={(v) => set({ waste_each: v })} />
          </>}
          {lb.source === "products" && <>
            <div className="form-h">{t("lb.products_h")}</div>
            <Check checked={lb.product_each} label={t("lb.product_each")} onChange={(v) => set({ product_each: v })} />
            <Check checked={lb.product_only_nonzero} label={t("lb.product_nonzero")} onChange={(v) => set({ product_only_nonzero: v })} />
          </>}
          {user && <>
            <div className="form-h">{t("lb.ufields_h")}</div>
            {ufields.length === 0 ? <p className="muted small">{t("lb.ufields_empty")}</p> : (
              <table className="lbx-table lbp-ufields" data-testid="lb-ufields" tabIndex={0}>
                <thead><tr><th>{t("lbu.f_name")}</th><th>{t("lbu.f_title")}</th><th>{t("lbu.f_type")}</th></tr></thead>
                <tbody>{ufields.map((f, i) => (
                  <tr key={i} className={cx(i === sel && "sel")} onClick={() => setSelF(i)} data-testid="lb-ufield">
                    <td>{f.name}</td><td>{f.title}</td><td>{f.type}</td></tr>))}</tbody>
              </table>)}
          </>}
        </div>
      </div>
      {/* MebeliX Kroy qo'shimchalari (kuzatilgan panelda yo'q) */}
      <div className="lbp-extra" data-testid="lb-params-extra">
        <div className="form-h">{t("lb.extra_h")}</div>
        <Check checked={lb.rotate_page === 90} label={t("lb.rotate")} onChange={(v) => set({ rotate_page: v ? 90 : 0 })} />
        {parts && <>
          <Field label={t("lb.label_count")} unit={t("u.pcs")}>
            <Num value={lb.label_count} min={1} max={20} testid="lb-label-count" onCommit={(v) => set({ label_count: Math.round(v ?? 1) })} /></Field>
          <Field label={t("lb.cs_op")}>
            <Sel value={lb.cs_op_id ?? ""} width={240} onChange={(v) => set({ cs_op_id: v || null })}
              options={[{ value: "", label: t("lb.all") }, ...csOps.map((o) => ({ value: o.id, label: o.name || o.code }))]} /></Field>
          <Check checked={lb.waste_business_only} label={t("lb.waste_business")} disabled={!lb.print_wastes} onChange={(v) => set({ waste_business_only: v })} />
        </>}
        {lb.legacy_program && !lb.template && <p className="muted small">{t("lb.legacy_note")}</p>}
      </div>
    </div>
  );
}

/** mm qiymati: ortiqcha nollarsiz (94, 63.75). */
const fmtMm = (v: number) => String(Math.round(v * 100) / 100);

// ───────────────────────── Shablon ─────────────────────────
function TemplateTab({ lb, onChange, lang, issues, onOpenDesigner }: {
  lb: LBParams; onChange: (p: Partial<LBParams>) => void | Promise<unknown>; lang: Lang; issues: LabelIssue[]; onOpenDesigner?: () => void;
}) {
  const { t } = useTranslation();
  const tplId = lb.template_id ?? DEFAULT_TEMPLATE_ID;
  const list = useTemplates(lang);
  const base = useTemplate(lb.template ? null : tplId, lang);
  const vars = useLabelVars(lang);
  const current: LabelTemplate | null = (lb.template as unknown as LabelTemplate | null) ?? base.data?.template ?? null;
  const [json, setJson] = useState(false);
  const [jsonErr, setJsonErr] = useState("");
  const meta = list.data?.find((m) => m.id === tplId);
  const refreshLib = () => { void qc.invalidateQueries({ queryKey: ["label-templates"] }); void qc.invalidateQueries({ queryKey: ["label-template"] }); };

  const edit = (fn: (tpl: LabelTemplate) => void) => {
    if (!current) return;
    const tpl = cloneTpl(current);
    fn(tpl);
    onChange({ template: asTpl(tpl) });
  };
  const pick = (id: string) => {
    const m = list.data?.find((x) => x.id === id);
    onChange({ template_id: id, template: null, params: {}, ...(m ? { width_mm: m.size.w, height_mm: m.size.h } : {}) });
  };
  const errByPath = useMemo(() => {
    const m = new Map<string, LabelIssue[]>();
    for (const e of issues) m.set(e.path, [...(m.get(e.path) ?? []), e]);
    return m;
  }, [issues]);

  const saveLib = async () => {
    if (!current) return;
    const name = await askText(t("lb.tpl_save"), current.name || meta?.name || "", { text: t("lb.tpl_name") });
    if (!name) return;
    const r = await call(() => post<{ id: number }>("/settings/label_template", { name, data: current }));
    if (r) { refreshLib(); onChange({ template_id: `profile:${r.id}`, template: null, params: {} }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const rename = async () => {
    if (!meta || meta.builtin || meta.profile_id === undefined) return;
    const name = await askText(t("menu.rename"), meta.name);
    if (name) { await call(() => put(`/settings/label_template/${meta.profile_id}`, { name })); refreshLib(); }
  };
  const remove = async () => {
    if (!meta || meta.builtin || meta.profile_id === undefined) return;
    if (!(await askConfirm(t("lb.tpl_delete_q", { name: meta.name }), undefined, { danger: true, ok: t("app.delete") }))) return;
    await onChange({ template_id: null, template: null, params: {} });       // avval havolani olib tashlaymiz (o'chirilgan shablonni so'ramaslik uchun)
    await call(() => del(`/settings/label_template/${meta.profile_id}`));
    refreshLib();
  };
  const flat = current ? flatten(current.elements) : [];
  const move = (path: ElPath, d: -1 | 1) => edit((tpl) => {
    const loc = locate(tpl, path);
    if (!loc) return;
    const [l, i] = loc;
    const j = i + d;
    if (j < 0 || j >= l.length) return;
    [l[i], l[j]] = [l[j], l[i]];
  });
  const remove1 = (path: ElPath) => edit((tpl) => { const loc = locate(tpl, path); if (loc) loc[0].splice(loc[1], 1); });
  const addEl = (key: string) => edit((tpl) => { tpl.elements.push(JSON.parse(JSON.stringify(NEW_ELEMENTS[key])) as TplElement); });
  const typeName = (el: TplElement) => el.t === "barcode"
    ? t(String(el.kind ?? "qr").toLowerCase() === "code128" ? "lb.el.code128" : "lb.el.qr") : t(`lb.el.${el.t}`);

  return (
    <div className="checks-col" data-testid="lb-template">
      <div className="row gap">
        <Sel<string> value={tplId} width={260} testid="lb-tpl-select" onChange={pick}
          options={(list.data ?? [{ id: DEFAULT_TEMPLATE_ID, name: "…" } as TplMeta]).map((m) => ({ value: m.id, label: (m.builtin ? "★ " : "") + m.name }))} />
        <IconBtn icon={FilePlus} title={t("lb.tpl_save")} onClick={() => void saveLib()} testid="lb-tpl-save" />
        <IconBtn icon={Pencil} title={t("menu.rename")} onClick={() => void rename()} disabled={!meta || meta.builtin} testid="lb-tpl-rename" />
        <IconBtn icon={Trash} title={t("lb.tpl_delete")} onClick={() => void remove()} disabled={!meta || meta.builtin} color="#c0392b"
          testid="lb-tpl-delete" />
      </div>
      <LabelFileTools current={current} lb={lb} lang={lang} refreshLib={refreshLib} onImported={(_id, patch) => void onChange(patch)} />
      {onOpenDesigner && <div><Btn small label={t("lb.open_designer")} onClick={onOpenDesigner} testid="lb-open-designer" /></div>}
      {lb.template && (
        <div className="row gap lbx-copy" data-testid="lb-tpl-copy">
          <span className="muted">{t("lb.tpl_copy")}</span>
          <Btn small label={t("lb.tpl_reset")} onClick={() => onChange({ template: null, params: {} })} />
        </div>
      )}
      {!current && <Empty>{t("app.loading")}</Empty>}
      {current && <>
        {current.params.length > 0 && <>
          <div className="form-h">{t("lb.tpl_params")}</div>
          {current.params.map((p) => {
            const v = lb.params[p.name] ?? p.default;
            const setP = (nv: string | number | boolean) => onChange({ params: { ...lb.params, [p.name]: nv } });
            const label = p.title || p.name;
            if (p.type === "boolean") return <Check key={p.name} checked={Boolean(v)} label={label} onChange={setP} testid={`lb-par-${p.name}`} />;
            if (p.type === "string") return <Field key={p.name} label={label}><Txt value={String(v ?? "")} width={200} onCommit={setP} /></Field>;
            return <Field key={p.name} label={label}><Num value={Number(v ?? 0)} onCommit={(n) => setP(n ?? 0)} testid={`lb-par-${p.name}`} /></Field>;
          })}
        </>}
        <div className="form-h row">{t("lb.tpl_vars")}<span className="grow" />
          <IconBtn icon={Plus} title={t("app.add")} onClick={() => edit((tpl) => { tpl.vars.push({ name: `v${tpl.vars.length + 1}`, expr: "1" }); })} /></div>
        {current.vars.length > 0 && (
          <table className="lbx-table"><tbody>{current.vars.map((v, i) => {
            const er = errByPath.get(`vars.${v.name}`);
            return (
              <tr key={i} className={cx(er && "lbx-err-row")} title={er?.map((e) => e.message).join("\n")}>
                <td className="lbx-w-name"><Txt value={v.name} width="100%" onCommit={(s) => edit((tpl) => { tpl.vars[i].name = s; })} /></td>
                <td><Txt value={v.expr} width="100%" onCommit={(s) => edit((tpl) => { tpl.vars[i].expr = s; })} /></td>
                <td className="lbx-w-act"><IconBtn icon={Trash} title={t("app.delete")} onClick={() => edit((tpl) => { tpl.vars.splice(i, 1); })} /></td>
              </tr>);
          })}</tbody></table>
        )}
        <div className="form-h row">{t("lb.tpl_elements")}<span className="grow" />
          <Dropdown icon={Plus} title={t("lb.add")} testid="lb-add-el"
            items={Object.keys(NEW_ELEMENTS).map((k) => ({ label: t(`lb.el.${k}`), onClick: () => addEl(k), testid: `lb-add-${k}` }))} />
          <Btn small kind="ghost" label="JSON" active={json} onClick={() => setJson(!json)} testid="lb-json-toggle" /></div>
        {json ? (
          <div className="lbx-json">
            <textarea className="inp area" rows={16} spellCheck={false} defaultValue={JSON.stringify(current, null, 1)} key={JSON.stringify(current)}
              data-testid="lb-json" onBlur={(e) => {
                try { const o = JSON.parse(e.target.value) as Record<string, unknown>; setJsonErr(""); if (JSON.stringify(o) !== JSON.stringify(current)) onChange({ template: o }); }
                catch (er) { setJsonErr(`${t("lb.json_bad")}: ${(er as Error).message}`); }
              }} />
            {jsonErr && <div className="lbx-bad">{jsonErr}</div>}
          </div>
        ) : (
          <table className="lbx-table" data-testid="lb-elements">
            <thead><tr><th>№</th><th>{t("lb.col.type")}</th><th>X</th><th>Y</th><th>{t("lb.col.size")}</th><th /><th>{t("lb.col.expr")}</th><th /></tr></thead>
            <tbody>{flat.map((f) => {
              const fm = fieldMap(f.el);
              const er = errByPath.get(f.label);
              const cell = (key: string | undefined, isExpr = false) => key ? (
                <Txt value={getField(f.el, key)} width="100%" testid={`lb-cell-${f.label}-${key}`}
                  onCommit={(s) => edit((tpl) => { const loc = locate(tpl, f.path); if (loc) setField(loc[0][loc[1]], key, s, isExpr); })} />) : null;
              const nested = CHILD_KEYS.some((k) => Array.isArray(f.el[k]));
              return (
                <tr key={f.label} className={cx(er && "lbx-err-row")} title={er?.map((e) => `${e.field}: ${e.message}`).join("\n")} data-testid="lb-el-row">
                  <td className="lbx-n">{f.label}</td>
                  <td style={{ paddingLeft: 4 + f.depth * 12 }}>{typeName(f.el)}{nested ? " …" : ""}</td>
                  <td className="lbx-w-c">{cell(fm.x)}</td><td className="lbx-w-c">{cell(fm.y)}</td>
                  <td className="lbx-w-c">{cell(fm.a)}</td><td className="lbx-w-c">{cell(fm.b)}</td>
                  <td>{cell(fm.e, true)}</td>
                  <td className="lbx-w-act nowrap">
                    <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(f.path, -1)} />
                    <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(f.path, 1)} />
                    <IconBtn icon={Trash} title={t("app.delete")} onClick={() => remove1(f.path)} />
                  </td>
                </tr>);
            })}</tbody>
          </table>
        )}
        <details className="lbx-vars">
          <summary>{t("lb.vars_h")}</summary>
          {vars.data?.groups.map((g) => (
            <div key={g.key} className="lbx-vgroup"><b>{g.key}</b>
              {g.vars.map((v) => (
                <button key={v.name} type="button" className="lbx-chip" title={`${v.title} (${v.type})`}
                  onClick={() => { void navigator.clipboard?.writeText(v.name); useUI.getState().toast(t("lb.copied", { s: v.name }), "ok"); }}>
                  <Copy size={10} /> {v.name}</button>))}
            </div>))}
          {vars.data && <div className="lbx-vgroup"><b>f(x)</b>
            {vars.data.functions.map((f) => (
              <button key={f.name} type="button" className="lbx-chip lbx-fn" title={f.group}
                onClick={() => { void navigator.clipboard?.writeText(f.sig); useUI.getState().toast(t("lb.copied", { s: f.sig }), "ok"); }}>{f.sig}</button>))}
          </div>}
        </details>
      </>}
    </div>
  );
}

// ───────────────────────── LB operatsiyasi paneli ─────────────────────────
export function LbPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const lb = op.lb ?? DEFAULT_LB;
  const onChange = (p: Partial<LBParams>) => call(() => patch(`/projects/${project.id}/operations/${op.id}`, { lb: p }));
  const saveDefaults = async () => {
    const r = await call(() => put("/settings/lb_defaults/default", lb));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "lb_defaults"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  return <LabelsEditor project={project} lb={lb} onChange={onChange} onSaveDefaults={() => void saveDefaults()} />;
}

// ───────────────────────── Печать → Этикетки ─────────────────────────
export function LabelsPrint() {
  const { t } = useTranslation();
  const pid = useUI((s) => s.projectId);
  const project = useProject(pid);
  const defaults = useDefaults<LBParams>("lb_defaults");
  const [opId, setOpId] = useState("");
  const [draft, setDraft] = useState<LBParams | null>(null);
  if (!pid || !project.data) return <Empty>{t("print.open_project")}</Empty>;
  const p = project.data;
  const lbOps = p.operations.filter((o) => o.type === "LB");
  const op = lbOps.find((o) => o.id === opId);
  const lb: LBParams = op ? op.lb ?? DEFAULT_LB : draft ?? defaults.data ?? DEFAULT_LB;
  const onChange = (patchLb: Partial<LBParams>) => {
    if (op) return call(() => patch(`/projects/${p.id}/operations/${op.id}`, { lb: patchLb }));
    setDraft({ ...lb, ...patchLb });
    return undefined;
  };
  const toOp = async () => {
    const r = await call(() => post<Project>(`/projects/${p.id}/operations`, { type: "LB" }));
    const created = r?.operations[r.operations.length - 1];
    if (created) {
      await call(() => patch(`/projects/${p.id}/operations/${created.id}`, { lb }));
      setOpId(created.id);
      setDraft(null);
    }
  };
  const saveDefaults = async () => {
    const r = await call(() => put("/settings/lb_defaults/default", lb));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "lb_defaults"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const header = (
    <div className="row gap lbx-head">
      <span className="muted">{t("lb.use_op")}</span>
      <Sel<string> value={opId} width={240} testid="lb-op-select" onChange={(v) => { setOpId(v); setDraft(null); }}
        options={[{ value: "", label: t("lb.new_params") }, ...lbOps.map((o) => ({ value: o.id, label: o.name || "LB" }))]} />
      {!op && <Btn small icon={Plus} label={t("lb.to_op")} title={t("lb.to_op_hint")} onClick={() => void toOp()} testid="lb-to-op" />}
    </div>
  );
  return <LabelsEditor project={p} lb={lb} onChange={onChange} header={header} onSaveDefaults={() => void saveDefaults()} />;
}

