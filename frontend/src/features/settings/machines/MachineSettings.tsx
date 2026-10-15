// Stanok sozlamalari (MachinePane ichida): ParamGrid (sxema parametrlari) + «Данные для этикеток» jadvali + saqlash.
// Server: `GET/PUT /postprocessors/machines/{key}/schema | params | label-fields`. Stanok formati bu yerda yo'q —
// faqat sozlama; shablon (Jinja) ularni `machine.params` va `maps[].placements[].label` orqali oladi.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { RotateCcw, Save } from "lucide-react";
import { call } from "../../../api/hooks";
import { useUI } from "../../../store/ui";
import { Btn } from "../../../shared/ui";
import { LabelFieldsTable } from "./LabelFieldsTable";
import { ParamGrid } from "./ParamGrid";
import { ToolsTable } from "./ToolsTable";
import { saveLabelFields, saveParams, useMachineSchema, type LabelRow, type ParamValue } from "./machinesApi";
import "./machines.css";

export function MachineSettings({ machineKey }: { machineKey: string }) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const q = useMachineSchema(machineKey);
  const s = q.data;
  const [vals, setVals] = useState<Record<string, ParamValue>>({});
  const [rows, setRows] = useState<LabelRow[]>([]);
  const [issues, setIssues] = useState(0);
  const [busy, setBusy] = useState(false);
  const valsSig = JSON.stringify(s?.values ?? {});
  const rowsSig = JSON.stringify(s?.label_table?.rows ?? []);
  // serverdan kelgan qiymat o'zgargandagina qoralama yangilanadi (bittasini saqlash ikkinchisining qoralamasini o'chirmasin)
  useEffect(() => { setVals(JSON.parse(valsSig) as Record<string, ParamValue>); }, [valsSig]);
  useEffect(() => { setRows(JSON.parse(rowsSig) as LabelRow[]); }, [rowsSig]);
  if (q.isLoading) return <div className="muted">{t("app.loading")}</div>;
  if (q.error || !s) return <div className="warn">{String((q.error as Error | null)?.message ?? "")}</div>;

  const paramsDirty = JSON.stringify(vals) !== valsSig && s.groups.length > 0;
  const rowsDirty = !!s.label_table && JSON.stringify(rows) !== rowsSig;
  const dirty = paramsDirty || rowsDirty;
  const hasMod = s.groups.some((g) => g.params.some((p) => vals[p.key] !== p.default));
  const save = async () => {
    setBusy(true);
    try {
      if (paramsDirty && !(await call(() => saveParams(machineKey, vals)))) return;
      if (rowsDirty && !(await call(() => saveLabelFields(machineKey, rows)))) return;
      useUI.getState().toast(t("app.saved"), "ok");
    } finally { setBusy(false); }
  };

  return (
    <div className="ms" data-testid="machine-settings">
      <div className="ms-head">
        <h4>{t("ppm.params.title")}</h4>
        <Btn icon={Save} kind="primary" label={t("app.save")} testid="ms-save" disabled={!dirty || busy || issues > 0}
          title={issues > 0 ? t("ppm.save_blocked") : undefined} onClick={() => void save()} />
        {s.groups.length > 0 && <Btn icon={RotateCcw} label={t("ppm.reset_all")} testid="ms-reset-all" disabled={!hasMod}
          onClick={() => setVals(s.defaults)} />}
        {dirty && <span className="warn" data-testid="ms-dirty">{t("ppm.dirty")}</span>}
      </div>
      {s.info && <p className="muted">{lang === "uz" ? s.info.uz : s.info.ru}</p>}
      {s.groups.length > 0
        ? <ParamGrid groups={s.groups} values={vals} onChange={(k, v) => setVals({ ...vals, [k]: v })}
          onReset={(k) => setVals({ ...vals, [k]: s.defaults[k] })} />
        : <p className="muted">{t("ppm.no_params")}</p>}
      {s.label_table && (
        <LabelFieldsTable machineKey={machineKey} table={s.label_table} rows={rows} onChange={setRows}
          onReset={() => setRows(s.label_table?.defaults ?? [])} onIssues={setIssues} />
      )}
      {s.group === "cnc" && <ToolsTable machineKey={machineKey} />}
      <details className="pp-doc"><summary>{t("ppm.ctx_title")}</summary><pre>{t("ppm.ctx_doc")}</pre></details>
    </div>
  );
}
