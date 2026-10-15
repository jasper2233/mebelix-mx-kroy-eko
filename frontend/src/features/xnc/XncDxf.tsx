// DXF → XNC kontur (ixtiyoriy): ASCII DXF dagi LINE / ARC / LWPOLYLINE / CIRCLE frezalash konturiga aylantiriladi.
// Qoidalar bizniki (qatlam / rang e'tiborsiz) — backend: services/xnc_dxf.py.
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { FileDown } from "lucide-react";
import { call } from "../../api/hooks";
import { api } from "../../api/client";
import type { Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Modal, Num, Sel } from "../../shared/ui";

interface DxfResult { project: Project; warnings: string[]; stats: { contours: number; circles: number; drills: number } }

export function XncDxfDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const file = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"append" | "replace">("append");
  const [origin, setOrigin] = useState<"bbox" | "zero">("bbox");
  const [flip, setFlip] = useState(true);
  const [depth, setDepth] = useState("dz");
  const [toolD, setToolD] = useState(6);
  const [corr, setCorr] = useState(0);
  const [drillD, setDrillD] = useState(0);

  const run = async () => {
    const f = file.current?.files?.[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    fd.append("mode", mode); fd.append("origin", origin); fd.append("flip_y", String(flip));
    fd.append("depth", depth || "dz"); fd.append("tool_d", String(toolD)); fd.append("correction", String(corr));
    if (drillD > 0) fd.append("drill_max_d", String(drillD));
    const r = await call(() => api<DxfResult>(`/projects/${project.id}/operations/${op.id}/xnc/import-dxf`, { form: fd }));
    if (r) {
      useUI.getState().toast(t("xnc.dxf.done", { c: r.stats.contours + r.stats.circles, d: r.stats.drills }), r.warnings.length ? "info" : "ok", r.warnings);
      onClose();
    }
  };

  return (
    <Modal title={t("xnc.dxf.title")} onClose={onClose} width={560} scope="xnc-dxf" testid="xnc-dxf-dialog"
      footer={<>
        <Btn kind="primary" icon={FileDown} label={t("xnc.dxf.run")} onClick={() => void run()} disabled={!name} testid="xnc-dxf-run" />
        <Btn label={t("app.close")} onClick={onClose} />
      </>}>
      <div className="xpp">
        <div className="xpp-row"><span>{t("xnc.dxf.file")}</span>
          <input ref={file} type="file" accept=".dxf" data-testid="xnc-dxf-file" onChange={(e) => setName(e.target.files?.[0]?.name ?? "")} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.mode")}</span>
          <Sel<"append" | "replace"> value={mode} width="100%" onChange={setMode} testid="xnc-dxf-mode"
            options={[{ value: "append", label: t("xnc.tpl.apply_append") }, { value: "replace", label: t("xnc.tpl.apply_replace") }]} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.origin")}</span>
          <Sel<"bbox" | "zero"> value={origin} width="100%" onChange={setOrigin}
            options={[{ value: "bbox", label: t("xnc.dxf.origin_bbox") }, { value: "zero", label: t("xnc.dxf.origin_zero") }]} /></div>
        <div className="xpp-row"><span /><Check checked={flip} onChange={setFlip} label={t("xnc.dxf.flip")} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.depth")}</span>
          <input className="inp" value={depth} onChange={(e) => setDepth(e.target.value)} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.tool_d")}</span><Num value={toolD} min={0.1} onCommit={(v) => setToolD(v ?? 6)} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.corr")}</span>
          <Sel<number> value={corr} width="100%" onChange={setCorr}
            options={[0, 1, 2, 3].map((v) => ({ value: v, label: t(`xnc.opt.corr${v}`) }))} /></div>
        <div className="xpp-row"><span>{t("xnc.dxf.drill_max")}</span><Num value={drillD} min={0} onCommit={(v) => setDrillD(v ?? 0)} /></div>
        <div className="muted">{t("xnc.dxf.note")}</div>
      </div>
    </Modal>
  );
}
