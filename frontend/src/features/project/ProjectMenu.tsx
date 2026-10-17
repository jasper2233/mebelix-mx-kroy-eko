// Chap «Проект» menyusi (UI_SPEC §2).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FileInput, FileSpreadsheet, CircleQuestionMark, Maximize, Redo2, RefreshCw, Save, Undo2, WandSparkles, ArrowDownToLine,
  ArrowUpFromLine,
} from "lucide-react";
import { call, qc, useHistory } from "../../api/hooks";
import { post } from "../../api/client";
import type { ParametricReport, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal } from "../../shared/ui";
import { enterFullscreenWithKeys } from "../../shared/hotkeys";
import { importProjectFile } from "../projects/Projects";
import { ExcelImportDialog } from "../cs/ExcelImport";
import { ImportOtherDialog } from "../importer/ImportDialog";
import { OrderPanel } from "../order/OrderPanel";
import { clearProjectWithConfirm } from "../order/clearProject";
import { xncDuplicates } from "./xncCodes";
import { ExportDialog } from "./ExportDialog";

export async function undo(pid: string) { await call(() => post(`/projects/${pid}/undo`)); }
export async function redo(pid: string) { await call(() => post(`/projects/${pid}/redo`)); }

function CommonActions({ project, pid, dups, onClose }: { project: Project; pid: string; dups: number; onClose: () => void }) {
  const { t } = useTranslation();
  const run = async (path: string) => {
    const r = await call(() => post(`/projects/${pid}/actions/${path}`));
    if (r) { useUI.getState().toast(t("common.done"), "ok"); onClose(); }
  };
  // «Раскроить все операции» (bizning qo'shimcha): barcha CS/CL/CN ketma-ket, bitta tarix qadami; ish davomida band
  // pardasi (QA #6); detalsiz/listsiz operatsiyalar — «пропущено» (xato emas), xatolar va sabablar toastda
  const cutAll = async () => {
    type Row = { name: string; error?: string; sheets?: number; skipped?: boolean; reason?: string };
    const r = await call(() => post<{ results: Row[] }>(`/projects/${pid}/actions/optimize-all`), t("common.cut_all_busy"));
    if (!r) return;
    void qc.invalidateQueries({ queryKey: ["project", pid] });
    const errs = r.results.filter((x) => x.error);
    const skipped = r.results.filter((x) => x.skipped);
    const lines = [...errs.map((x) => `${x.name}: ${x.error}`), ...skipped.map((x) => `${x.name}: ${x.reason ?? ""}`)].slice(0, 8);
    const head = t("common.cut_all_done", { n: r.results.filter((x) => x.sheets !== undefined).length, s: skipped.length, e: errs.length });
    // sabablar (qaysi operatsiya o'tkazib yuborilgan / xato) — xabarnomada ro'yxat (bitta bo'lsa ham ko'rsatiladi)
    useUI.getState().toast(head, errs.length ? "error" : skipped.length ? "warn" : "ok", lines);
    onClose();
  };
  // «Пересчитать параметричность» (W12): mahsulot dasturlari va XNC ifodalari qayta hisoblanadi; natija — qisqa xulosa
  const recalcParametric = async () => {
    const r = await call(() => post<{ report: ParametricReport }>(`/projects/${pid}/actions/recalc-parametric`));
    if (!r) return;
    const tt = r.report.totals;
    const bad = tt.errors + tt.warnings + tt.xnc_errors;
    useUI.getState().toast(t("common.recalc_parametric_done", { p: tt.programs, x: tt.xnc, n: bad }), bad ? "warn" : "ok",
      [...r.report.products.flatMap((p) => p.messages.map((m) => `${p.name}: ${m.text}`)),
        ...r.report.xnc.flatMap((x) => x.messages.map((m) => `${x.code || x.name}: ${m}`))].slice(0, 8));
    onClose();
  };
  return (
    <Modal title={t("menu.common_actions")} onClose={onClose} width={520} testid="common-actions"
      footer={<Btn label={t("app.cancel")} onClick={onClose} />}>
      <div className="action-list">
        <button type="button" className="action" onClick={() => void run("merge-same")}>
          <b>{t("common.merge")}</b><span>{t("common.merge_hint")}</span></button>
        <button type="button" className="action" onClick={() => void run("split-edges")}>
          <b>{t("common.split_edges")}</b><span>{t("common.split_edges_hint")}</span></button>
        <button type="button" className="action" onClick={() => void run("optimize-ops")}>
          <b>{t("common.optimize_ops")}</b><span>{t("common.optimize_ops_hint")}</span></button>
        <button type="button" className="action" data-testid="action-cut-all" onClick={() => void cutAll()}
          disabled={!project.operations.some((o) => (o.type === "CS" || o.type === "CL" || o.type === "CN") && o.parts.length > 0)}>
          <b>{t("common.cut_all")}</b><span>{t("common.cut_all_hint")}</span></button>
        <button type="button" className="action" onClick={() => void run("recode-xnc")} disabled={dups === 0}
          data-testid="action-recode-xnc">
          <b>{t("common.recode_xnc")}</b>
          <span>{dups > 0 ? t("common.recode_xnc_dups", { n: dups }) : t("common.recode_xnc_none")}</span></button>
        <button type="button" className="action" data-testid="action-recalc-parametric" onClick={() => void recalcParametric()}>
          <b>{t("common.recalc_parametric")}</b><span>{t("common.recalc_parametric_hint")}</span></button>
        <button type="button" className="action" data-testid="action-clear"
          onClick={() => { onClose(); void clearProjectWithConfirm(project, t); }}>
          <b>{t("common.clear")}</b><span>{t("common.clear_hint")}</span></button>
      </div>
    </Modal>
  );
}

/** «Сохранить» holati: loyiha ochilganda / oxirgi saqlashdagi obyekt (kesh bir xil ma'lumotda o'sha obyektni qaytaradi —
 *  obyekt boshqa bo'lsa, loyiha o'zgargan). Ma'lumot har amalda saqlanadi; tugma faqat o'zgarish bo'lganda faol (onlayn kabi). */
const savedRef = new Map<string, Project>();

export function ProjectMenu({ project }: { project: Project }) {
  const { t } = useTranslation();
  const [, bump] = useState(0);
  if (!savedRef.has(project.id)) savedRef.set(project.id, project);
  const dirty = savedRef.get(project.id) !== project;
  const hist = useHistory(project.id);
  const ui = useUI();
  const [dlg, setDlg] = useState<"" | "common" | "excel" | "other" | "export">("");
  const item = (Icon: typeof Save, label: string, fn: () => void, disabled = false, hint?: string, testid?: string) => (
    <button type="button" className="side-item" onClick={fn} disabled={disabled} title={hint} data-testid={testid}>
      <Icon size={15} /> {label}
    </button>
  );
  const csOp = project.operations.find((o) => o.id === ui.opId && o.type === "CS")
    ?? project.operations.find((o) => o.type === "CS");
  return (
    <div className="side-menu">
      {item(CircleQuestionMark, t("menu.help"), () => ui.set({ section: "help" }), false, "F1")}
      {item(RefreshCw, t("menu.refresh"), () => { void qc.invalidateQueries({ queryKey: ["project", project.id] }); })}
      {item(Undo2, t("menu.undo"), () => void undo(project.id), !hist.data?.can_undo, "Ctrl+Z", "menu-undo")}
      {item(Redo2, t("menu.redo"), () => void redo(project.id), !hist.data?.can_redo, "Ctrl+Y", "menu-redo")}
      {item(Save, t("menu.save"), async () => {
        if (await call(() => post(`/projects/${project.id}/save`))) {
          savedRef.set(project.id, qc.getQueryData<Project>(["project", project.id]) ?? project);
          bump((n) => n + 1);
          ui.toast(t("app.saved"), "ok");
        }
      }, !dirty, undefined, "menu-save")}
      {item(WandSparkles, t("menu.common_actions"), () => setDlg("common"))}
      {item(ArrowUpFromLine, t("menu.export"), () => setDlg("export"), false, undefined, "menu-export")}
      {item(ArrowDownToLine, t("menu.import"), () => {
        const inp = document.createElement("input");
        inp.type = "file"; inp.accept = ".json,.mxk,.project";
        inp.onchange = () => { if (inp.files?.[0]) void importProjectFile(inp.files[0], t); };
        inp.click();
      })}
      {item(FileSpreadsheet, t("menu.import_excel"), () => setDlg("excel"), false, undefined, "menu-import-excel")}
      {item(FileInput, t("menu.import_other"), () => setDlg("other"), false, undefined, "menu-import-other")}
      {item(Maximize, t("menu.fullscreen"), () => void enterFullscreenWithKeys(), false, t("menu.fullscreen_hint"))}
      <OrderPanel project={project} />
      {dlg === "common" && <CommonActions project={project} pid={project.id} dups={xncDuplicates(project)} onClose={() => setDlg("")} />}
      {dlg === "other" && <ImportOtherDialog onClose={() => setDlg("")} />}
      {dlg === "export" && <ExportDialog project={project} onClose={() => setDlg("")} />}
      {dlg === "excel" && <ExcelImportDialog project={project} op={csOp} onClose={() => setDlg("")} />}
    </div>
  );
}
