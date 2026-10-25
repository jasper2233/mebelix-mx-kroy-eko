// «XNC → MES» (2026-10-25, foydalanuvchi talabi): XNC ishini MES (ERP + moliya) ga yuborish sozlamasi — yoqish, nima yuboriladi,
// har asbobning MES dagi kodi (moliya narxni shu kod bo'yicha qo'yadi) va loyiha bo'yicha oldindan ko'rish. Ham «XNC ishi» jadvali
// (loyihaning yuqori panelida) shu yerdagi `XncWorkTable` dan.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { get, put } from "../../api/client";
import { useUI } from "../../store/ui";
import { Btn, Check, Sel, fmt } from "../../shared/ui";
import "./xncMes.css";

export interface XncMesSettings {
  enabled: boolean; send_holes: boolean; send_mill: boolean; send_mill_passes: boolean; send_saw: boolean; send_parts: boolean;
  codes: { kind: string; name: string; d: number; side: string; through: boolean; mes_code: string; comment: string }[];
}
export interface ToolRow { key: string; kind: "drill" | "mill" | "saw"; name: string; d: number; side: string; through: boolean;
  mes_code: string; comment?: string; in_project?: boolean }
export interface ToolWork extends ToolRow { depths: number[]; holes: number; mill_m: number; mill_pass_m: number; saw_m: number;
  parts: number; ops: number; uses: { op_id: string; code: string; part_name: string; qty: number; holes: number; mill_m: number; saw_m: number }[] }
export interface XncWork { xnc_ops: number; xnc_parts: number; tools: ToolWork[]; errors: { op_id: string; code: string; error: string }[];
  mes: { enabled: boolean; xnc_ops: number; xnc_parts: number; tools: ToolWork[] } }

const DEF: XncMesSettings = { enabled: true, send_holes: true, send_mill: true, send_mill_passes: true, send_saw: true, send_parts: true, codes: [] };

/** Asbob turi / tomoni yozuvi. */
function useToolText() {
  const { t } = useTranslation();
  return {
    kind: (k: string) => t(`xm.kind.${k}`),
    side: (r: { kind: string; side: string; through: boolean }) =>
      r.kind !== "drill" ? "" : `${t(`xm.side.${r.side || "face"}`)}${r.through ? ` · ${t("xm.through")}` : ""}`,
  };
}

/** Loyiha bo'yicha XNC ishi jadvali (asbob kesimida) — MES ga ketadigani belgilanadi. */
export function XncWorkTable({ work, testid }: { work: XncWork; testid?: string }) {
  const { t } = useTranslation();
  const tt = useToolText();
  const sent = new Set(work.mes.tools.map((x) => x.key));
  return (
    <>
      <p className="xm-sum">{t("xm.summary", { ops: work.xnc_ops, parts: work.xnc_parts })}
        {!work.mes.enabled && <b className="xm-off"> · {t("xm.disabled")}</b>}</p>
      <table className="simple xm-table" data-testid={testid}>
        <thead><tr><th>{t("xm.col.kind")}</th><th>{t("xm.col.tool")}</th><th>Ø</th><th>{t("xm.col.side")}</th><th>{t("xm.col.holes")}</th>
          <th>{t("xm.col.mill")}</th><th>{t("xm.col.passes")}</th><th>{t("xm.col.saw")}</th><th>{t("xm.col.parts")}</th>
          <th>{t("xm.col.code")}</th><th>{t("xm.col.mes")}</th></tr></thead>
        <tbody>
          {work.tools.map((r) => (
            <tr key={r.key} className={sent.has(r.key) ? "" : "xm-skip"}
              title={r.uses.map((u) => `${u.part_name || u.code || u.op_id} ×${u.qty}`).join("\n")}>
              <td>{tt.kind(r.kind)}</td><td><b>{r.name}</b></td><td className="num">{fmt(r.d)}</td><td>{tt.side(r)}</td>
              <td className="num">{r.kind === "drill" ? r.holes : ""}</td>
              <td className="num">{r.kind === "mill" ? fmt(r.mill_m, 3) : ""}</td>
              <td className="num">{r.kind === "mill" ? fmt(r.mill_pass_m, 3) : ""}</td>
              <td className="num">{r.kind === "saw" ? fmt(r.saw_m, 3) : ""}</td>
              <td className="num">{r.parts}</td>
              <td>{r.mes_code || <span className="muted">{t("xm.no_code")}</span>}</td>
              <td>{sent.has(r.key) ? "✓" : "—"}</td>
            </tr>
          ))}
          {!work.tools.length && <tr><td colSpan={11} className="muted">{t("xm.no_xnc")}</td></tr>}
        </tbody>
      </table>
      {work.errors.length > 0 && <p className="xm-err">{t("xm.errors")}: {work.errors.map((e) => e.code || e.op_id).join(", ")}</p>}
    </>
  );
}

export function XncMesSection() {
  const { t } = useTranslation();
  const tt = useToolText();
  const cfg = useDefaults<XncMesSettings>("xnc_mes");
  const [d, setD] = useState<XncMesSettings | null>(null);
  const [pid, setPid] = useState("");
  const [edits, setEdits] = useState<Record<string, { mes_code: string; comment: string }>>({});
  useEffect(() => { if (cfg.data) setD({ ...DEF, ...cfg.data }); }, [cfg.data]);
  const projects = useQuery({ queryKey: ["projects", "xm"], queryFn: () => get<{ id: string; number: number; name: string }[]>("/projects", { all_folders: true, limit: 300 }) });
  const tools = useQuery({ queryKey: ["xnc-mes-tools", pid, cfg.data], queryFn: () => get<ToolRow[]>("/xnc-mes/tools", { pid: pid || undefined }) });
  const work = useQuery({ enabled: !!pid, queryKey: ["xnc-work", pid, cfg.data], queryFn: () => get<XncWork>(`/projects/${pid}/xnc-tools`) });
  const rows = useMemo(() => (tools.data ?? []).map((r) => ({ ...r, ...(edits[r.key] ?? {}) })), [tools.data, edits]);
  if (!d) return null;
  const setRow = (r: ToolRow, f: "mes_code" | "comment", v: string) =>
    setEdits((e) => ({ ...e, [r.key]: { mes_code: f === "mes_code" ? v : (e[r.key]?.mes_code ?? r.mes_code ?? ""), comment: f === "comment" ? v : (e[r.key]?.comment ?? r.comment ?? "") } }));
  const save = async () => {
    const codes = rows.filter((r) => (r.mes_code ?? "").trim() || (r.comment ?? "").trim())
      .map((r) => ({ kind: r.kind, name: r.name, d: r.d, side: r.side, through: r.through, mes_code: (r.mes_code ?? "").trim(), comment: (r.comment ?? "").trim() }));
    const ok = await call(() => put("/settings/xnc_mes/default", { ...d, codes }));
    if (ok) {
      setEdits({});
      void qc.invalidateQueries({ queryKey: ["defaults", "xnc_mes"] });
      useUI.getState().toast(t("app.saved"), "ok");
    }
  };
  const chk = (k: keyof XncMesSettings, label: string) => (
    <Check checked={!!d[k]} label={label} onChange={(v) => setD({ ...d, [k]: v })} testid={`xm-${k}`} disabled={k !== "enabled" && !d.enabled} />
  );
  return (
    <div className="xm" data-testid="xnc-mes">
      <div className="xm-head"><h3>{t("xm.title")}</h3><Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} testid="xm-save" /></div>
      <p className="muted">{t("xm.hint")}</p>
      {chk("enabled", t("xm.enabled"))}
      <div className="xm-checks">
        {chk("send_holes", t("xm.send_holes"))}
        {chk("send_mill", t("xm.send_mill"))}
        {chk("send_mill_passes", t("xm.send_mill_passes"))}
        {chk("send_saw", t("xm.send_saw"))}
        {chk("send_parts", t("xm.send_parts"))}
      </div>
      <h4>{t("xm.tools")}</h4>
      <p className="muted">{t("xm.tools_hint")}</p>
      <div className="xm-proj">{t("xm.project")}:{" "}
        <Sel value={pid} width={360} testid="xm-project" onChange={(v) => setPid(v)}
          options={[{ value: "", label: t("xm.project_none") }, ...(projects.data ?? []).map((p) => ({ value: p.id, label: `№${p.number} ${p.name}` }))]} /></div>
      <table className="simple xm-table" data-testid="xm-tools">
        <thead><tr><th>{t("xm.col.kind")}</th><th>{t("xm.col.tool")}</th><th>Ø</th><th>{t("xm.col.side")}</th><th>{t("xm.col.in_project")}</th>
          <th>{t("xm.col.code")}</th><th>{t("xm.col.comment")}</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className={r.in_project ? "xm-inproj" : ""}>
              <td>{tt.kind(r.kind)}</td><td><b>{r.name}</b></td><td className="num">{fmt(r.d)}</td><td>{tt.side(r)}</td>
              <td>{r.in_project ? "✓" : ""}</td>
              <td><input className="inp xm-code" value={r.mes_code ?? ""} placeholder={t("xm.code_ph")} data-testid={`xm-code-${r.key}`}
                onChange={(e) => setRow(r, "mes_code", e.target.value)} /></td>
              <td><input className="inp" value={r.comment ?? ""} onChange={(e) => setRow(r, "comment", e.target.value)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      {pid && <>
        <h4>{t("xm.preview")}</h4>
        {work.data ? <XncWorkTable work={work.data} testid="xm-preview" /> : <p className="muted">…</p>}
      </>}
    </div>
  );
}
