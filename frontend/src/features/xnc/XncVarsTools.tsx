// XNC «Шаблон»: «Переменные» (tizim o'zgaruvchilari + dasturning Par / Var lari, joriy hisoblangan qiymatlar — faqat o'qish)
// va «Инструменты» (Настройки → XNC редактор → Инструменты jadvali — ko'rish) oynalari.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { get } from "../../api/client";
import type { Operation, Project } from "../../api/types";
import { Btn, Modal } from "../../shared/ui";
import { useXncTools } from "./xncSettingsApi";

export interface XncVarRow {
  name: string; kind: "system" | "par" | "var"; type: "double" | "integer" | "boolean" | "string";
  value: number | string | boolean | null; description: string;
}

const fmt = (v: number | string | boolean | null): string => {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return String(Number(v.toFixed(6)));
  return String(v);
};

export function XncVarsDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [rows, setRows] = useState<XncVarRow[] | null>(null);
  useEffect(() => {
    let alive = true;
    void get<{ rows: XncVarRow[] }>(`/projects/${project.id}/operations/${op.id}/xnc-vars`)
      .then((r) => alive && setRows(r.rows)).catch(() => alive && setRows([]));
    return () => { alive = false; };
  }, [project.id, op.id, op.xnc]);
  return (
    <Modal title={t("xnc.vars.title")} onClose={onClose} width={720} testid="xnc-vars-dialog"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} testid="xnc-vars-ok" />}>
      <div className="scroll xnc-dlg-wrap">
        <table className="simple xnc-dlg-table" data-testid="xnc-vars-table">
          <thead><tr><th>№</th><th>{t("xnc.vars.col.name")}</th><th>{t("xnc.vars.col.desc")}</th><th>{t("xnc.vars.col.type")}</th>
            <th>{t("xnc.vars.col.value")}</th></tr></thead>
          <tbody>
            {(rows ?? []).map((r, i) => (
              <tr key={r.name} data-testid={`xnc-var-${r.name}`}>
                <td className="num">{i + 1}</td>
                <td className="mono">{r.name}</td>
                <td>{r.kind === "system" ? t(`xnc.vars.d.${r.name.replace(".", "_")}`, { defaultValue: r.description || "" }) : r.description}</td>
                <td>{r.type}</td>
                <td className={r.type === "string" || r.type === "boolean" ? undefined : "num"}>
                  {r.type === "boolean" && typeof r.value !== "string" && r.value !== null
                    ? <input type="checkbox" checked={Boolean(r.value)} readOnly disabled />
                    : fmt(r.value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows === null && <div className="muted" style={{ padding: 8 }}>{t("app.loading")}</div>}
      </div>
    </Modal>
  );
}

export function XncToolsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const q = useXncTools();
  // bir xil asbob bir necha tekislikda yozilgan bo'lishi mumkin — ro'yxatda bir marta
  const rows = useMemo(() => {
    const seen = new Set<string>();
    return (q.data?.tools ?? []).filter((x) => {
      const k = `${x.name}\u0000${x.d}\u0000${x.comment}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }, [q.data]);
  return (
    <Modal title={t("xnc.tools.title")} onClose={onClose} width={520} testid="xnc-tools-dialog"
      footer={<>
        <Btn kind="primary" label={t("app.ok")} onClick={onClose} testid="xnc-tools-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="xnc-tools-cancel" />
      </>}>
      <div className="scroll xnc-dlg-wrap">
        <table className="simple xnc-dlg-table" data-testid="xnc-tools-table">
          <thead><tr><th>{t("xs.col.name")}</th><th>{t("xs.col.d")}</th><th>{t("xs.col.comment")}</th></tr></thead>
          <tbody>
            {rows.map((x, i) => (
              <tr key={i}><td className="mono">{x.name}</td><td className="num">{x.d}</td><td>{x.comment}</td></tr>
            ))}
          </tbody>
        </table>
        {q.data && !rows.length && <div className="muted" style={{ padding: 8 }}>{t("app.no_rows")}</div>}
      </div>
      <p className="muted xnc-dlg-hint">{t("xnc.tools.hint")}</p>
    </Modal>
  );
}
