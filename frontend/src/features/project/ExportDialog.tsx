// «Проект → Экспортировать» (W10): .project (XML) — ochiq format, yoki .mxk.json (to'liq nusxa).
// .project: avval hisobot (nima yoziladi / nima o'tkazib yuboriladi), keyin «Скачать».
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { FileCode, FileJson, Info, TriangleAlert, ArrowUpFromLine } from "lucide-react";
import { call } from "../../api/hooks";
import { download, get } from "../../api/client";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal } from "../../shared/ui";

interface ExportWarning { level: "warn" | "info"; code: string; text: string }
export interface ExportReport {
  filename: string; bytes: number; format_version: string; warnings: ExportWarning[];
  counts: { products: number; part_rows: number; operations: Record<string, number>; skipped_operations: number };
}

/** Faylni yuklab olib, ogohlantirishlar bo'lsa xabar beradi (UI ro'yxat sahifasi ham shundan foydalanadi). */
export async function downloadProjectFile(pid: string, fallback: string): Promise<boolean> {
  try { await download(`/projects/${pid}/export/project`, {}, fallback); return true; }
  catch (e) { useUI.getState().toast(e instanceof Error ? e.message : String(e), "error"); return false; }
}

export function ExportDialog({ project, onClose }: { project: Project; onClose: () => void }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"" | "project">("");
  const [rep, setRep] = useState<ExportReport | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (mode !== "project") return;
    let off = false;
    setRep(null);
    void call(() => get<ExportReport>(`/projects/${project.id}/export/project/report`)).then((r) => { if (!off && r) setRep(r); });
    return () => { off = true; };
  }, [mode, project.id]);

  const saveProject = async () => {
    setBusy(true);
    const ok = await downloadProjectFile(project.id, rep?.filename ?? `${project.number}.project`);
    setBusy(false);
    if (ok) { useUI.getState().toast(t("export.done"), "ok"); onClose(); }
  };
  const saveJson = async () => {
    await call(() => download(`/projects/${project.id}/export`, {}, `${project.number}.mxk.json`));
    onClose();
  };
  const warns = rep?.warnings.filter((w) => w.level === "warn") ?? [];
  const infos = rep?.warnings.filter((w) => w.level === "info") ?? [];
  const ops = rep ? Object.entries(rep.counts.operations).map(([k, n]) => `${k} × ${n}`).join(", ") : "";

  return (
    <Modal title={t("export.title")} onClose={onClose} width={560} testid="export-dialog"
      footer={mode === "project"
        ? <><Btn kind="primary" icon={ArrowUpFromLine} label={t("export.download")} disabled={!rep || busy} onClick={() => void saveProject()}
            testid="export-download" />
          <Btn label={t("export.back")} onClick={() => setMode("")} />
          <Btn label={t("app.close")} onClick={onClose} /></>
        : <Btn label={t("app.close")} onClick={onClose} />}>
      {mode === "" ? (
        <div className="action-list">
          <button type="button" className="action" onClick={() => setMode("project")} data-testid="export-project">
            <b><FileCode size={14} /> {t("export.project")}</b><span>{t("export.project_hint")}</span></button>
          <button type="button" className="action" onClick={() => void saveJson()} data-testid="export-json">
            <b><FileJson size={14} /> {t("export.json")}</b><span>{t("export.json_hint")}</span></button>
        </div>
      ) : !rep ? (
        <p className="muted">{t("export.preparing")}</p>
      ) : (
        <div data-testid="export-report">
          <table className="simple">
            <tbody>
              <tr><td>{t("export.file")}</td><td data-testid="export-filename">{rep.filename}</td></tr>
              <tr><td>{t("export.size")}</td><td>{(rep.bytes / 1024).toFixed(1)} KB</td></tr>
              <tr><td>{t("export.contents")}</td>
                <td>{t("export.counts", { products: rep.counts.products, parts: rep.counts.part_rows })}{ops ? `; ${ops}` : ""}</td></tr>
            </tbody>
          </table>
          {warns.length > 0 && <>
            <div className="form-h"><TriangleAlert size={14} /> {t("export.warnings", { n: warns.length })}</div>
            <ul data-testid="export-warnings" style={{ margin: "4px 0 8px", paddingLeft: 18 }}>
              {warns.map((w, i) => <li key={i}>{w.text}</li>)}
            </ul></>}
          {infos.length > 0 && <>
            <div className="form-h"><Info size={14} /> {t("export.notes")}</div>
            <ul data-testid="export-notes" className="muted" style={{ margin: "4px 0 8px", paddingLeft: 18 }}>
              {infos.map((w, i) => <li key={i}>{w.text}</li>)}
            </ul></>}
          {warns.length === 0 && infos.length === 0 && <p className="ok">{t("export.no_warnings")}</p>}
        </div>
      )}
    </Modal>
  );
}
