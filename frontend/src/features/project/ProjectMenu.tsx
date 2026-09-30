// Chap «Проект» menyusi (UI_SPEC §2).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Download, FileInput, FileSpreadsheet, CircleQuestionMark, Maximize, Redo2, RefreshCw, Save, ShoppingCart, Undo2, Upload, WandSparkles,
} from "lucide-react";
import { call, qc, useHistory } from "../../api/hooks";
import { download, patch, post } from "../../api/client";
import type { OrderStatus, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal, Sel, money } from "../../shared/ui";
import { enterFullscreenWithKeys } from "../../shared/hotkeys";
import { importProjectFile, STATUS_KEYS } from "../projects/Projects";
import { ExcelImportDialog } from "../cs/ExcelImport";

export async function undo(pid: string) { await call(() => post(`/projects/${pid}/undo`)); }
export async function redo(pid: string) { await call(() => post(`/projects/${pid}/redo`)); }

function CommonActions({ pid, onClose }: { pid: string; onClose: () => void }) {
  const { t } = useTranslation();
  const run = async (path: string) => {
    const r = await call(() => post(`/projects/${pid}/actions/${path}`));
    if (r) { useUI.getState().toast(t("common.done"), "ok"); onClose(); }
  };
  return (
    <Modal title={t("menu.common_actions")} onClose={onClose} width={520} testid="common-actions">
      <div className="action-list">
        <button type="button" className="action" onClick={() => void run("merge-same")}>
          <b>{t("common.merge")}</b><span>{t("common.merge_hint")}</span></button>
        <button type="button" className="action" onClick={() => void run("split-edges")}>
          <b>{t("common.split_edges")}</b><span>{t("common.split_edges_hint")}</span></button>
        <button type="button" className="action" onClick={() => void run("optimize-ops")}>
          <b>{t("common.optimize_ops")}</b><span>{t("common.optimize_ops_hint")}</span></button>
      </div>
    </Modal>
  );
}

function ImportOther({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const formats = [
    { name: ".project (XML)", ok: true },
    { name: "PRO100", ok: false }, { name: "Imos (fxm)", ok: false }, { name: "БМ (xml, obl)", ok: false },
    { name: "BCAD (xml)", ok: false }, { name: "Woody2", ok: false }, { name: "WoodWop (mpr)", ok: false },
    { name: "iLENIA (pd4)", ok: false },
  ];
  const pick = () => {
    const inp = document.createElement("input");
    inp.type = "file";
    inp.accept = ".project,.xml";
    inp.onchange = () => { if (inp.files?.[0]) { onClose(); void importProjectFile(inp.files[0], t); } };
    inp.click();
  };
  return (
    <Modal title={t("menu.import_other")} onClose={onClose} width={460}
      footer={<><Btn kind="primary" icon={Upload} label={t("import.choose_file")} onClick={pick} />
        <Btn label={t("app.close")} onClick={onClose} /></>}>
      <p className="muted">{t("import.other_hint")}</p>
      <table className="simple">
        <tbody>
          {formats.map((f) => (
            <tr key={f.name}><td>{f.name}</td><td className={f.ok ? "ok" : "muted"}>
              {f.ok ? t("import.supported") : t("import.plugin_later")}</td></tr>
          ))}
        </tbody>
      </table>
    </Modal>
  );
}

export function ProjectMenu({ project }: { project: Project }) {
  const { t } = useTranslation();
  const hist = useHistory(project.id);
  const ui = useUI();
  const [dlg, setDlg] = useState<"" | "common" | "excel" | "other">("");
  const cost_m = project.operations.reduce((s, o) => s + o.cost_material, 0);
  const cost_o = project.operations.reduce((s, o) => s + o.cost_operation, 0);
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
        if (await call(() => post(`/projects/${project.id}/save`))) ui.toast(t("app.saved"), "ok");
      })}
      {item(WandSparkles, t("menu.common_actions"), () => setDlg("common"))}
      {item(Download, t("menu.export"), () => void download(`/projects/${project.id}/export`, {}, `${project.number}.mxk.json`))}
      {item(Upload, t("menu.import"), () => {
        const inp = document.createElement("input");
        inp.type = "file"; inp.accept = ".json,.mxk,.project";
        inp.onchange = () => { if (inp.files?.[0]) void importProjectFile(inp.files[0], t); };
        inp.click();
      })}
      {item(FileSpreadsheet, t("menu.import_excel"), () => setDlg("excel"), !csOp)}
      {item(FileInput, t("menu.import_other"), () => setDlg("other"))}
      {item(Maximize, t("menu.fullscreen"), () => void enterFullscreenWithKeys(), false, t("menu.fullscreen_hint"))}
      <div className="side-order">
        <div className="side-order-title"><ShoppingCart size={14} /> {t("menu.order")}</div>
        <Sel<OrderStatus> value={project.status} width="100%" testid="order-status"
          options={[0, 1, 2, 3].map((s) => ({ value: s as OrderStatus, label: t(STATUS_KEYS[s]) }))}
          onChange={(v) => void call(() => patch(`/projects/${project.id}`, { status: v }))} />
        <table className="mini">
          <tbody>
            <tr><td>{t("menu.order_id")}</td><td>{project.number}</td></tr>
            <tr><td>{t("menu.cost")}</td><td>{money(cost_m + cost_o)} {project.currency}</td></tr>
            <tr><td>{t("menu.cost_mat")}</td><td>{money(cost_m)} {project.currency}</td></tr>
            <tr><td>{t("menu.cost_op")}</td><td>{money(cost_o)} {project.currency}</td></tr>
            {project.mes_order_ref && <tr><td>MES</td><td>{project.mes_order_ref}</td></tr>}
          </tbody>
        </table>
      </div>
      {dlg === "common" && <CommonActions pid={project.id} onClose={() => setDlg("")} />}
      {dlg === "other" && <ImportOther onClose={() => setDlg("")} />}
      {dlg === "excel" && csOp && <ExcelImportDialog project={project} op={csOp} onClose={() => setDlg("")} />}
    </div>
  );
}
