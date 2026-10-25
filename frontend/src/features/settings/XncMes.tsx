// «XNC → MES» (2026-10-25, foydalanuvchi talabi): XNC ishini MES (ERP + moliya) ga yuborish sozlamasi — yoqish, nima yuboriladi,
// har asbobning MES dagi kodi (moliya narxni shu kod bo'yicha qo'yadi) va loyiha bo'yicha oldindan ko'rish. Ham «XNC ishi» jadvali
// (loyihaning yuqori panelida) shu yerdagi `XncWorkTable` dan.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { FolderSearch, Plus, Save, Trash } from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { get, post, put } from "../../api/client";
import { useUI } from "../../store/ui";
import { Btn, Check, IconBtn, Sel, fmt } from "../../shared/ui";
import "./xncMes.css";

export interface XncMesSettings {
  enabled: boolean; send_holes: boolean; send_mill: boolean; send_mill_passes: boolean; send_saw: boolean; send_parts: boolean;
  codes: { kind: string; name: string; d: number; side: string; through: boolean; mes_code: string; comment: string; active?: boolean; usage?: number }[];
}
export interface ToolRow { key: string; kind: "drill" | "mill" | "saw"; name: string; d: number; side: string; through: boolean;
  mes_code: string; comment?: string; in_project?: boolean; active?: boolean; usage?: number; mismatch?: boolean; unknown?: boolean }
export interface ToolWork extends ToolRow { known?: boolean; depths: number[]; holes: number; mill_m: number; mill_pass_m: number; saw_m: number;
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
  const mes = work.mes ?? { enabled: true, tools: work.tools ?? [] };          // eski server javobida `mes` bo'lmasligi mumkin
  const sent = new Set((mes.tools ?? []).map((x) => x.key));
  return (
    <>
      <p className="xm-sum">{t("xm.summary", { ops: work.xnc_ops, parts: work.xnc_parts })}
        {!mes.enabled && <b className="xm-off"> · {t("xm.disabled")}</b>}</p>
      <table className="simple xm-table" data-testid={testid}>
        <thead><tr><th>{t("xm.col.kind")}</th><th>{t("xm.col.tool")}</th><th>Ø</th><th>{t("xm.col.side")}</th><th>{t("xm.col.holes")}</th>
          <th>{t("xm.col.mill")}</th><th>{t("xm.col.passes")}</th><th>{t("xm.col.saw")}</th><th>{t("xm.col.parts")}</th>
          <th>{t("xm.col.code")}</th><th>{t("xm.col.mes")}</th></tr></thead>
        <tbody>
          {(work.tools ?? []).map((r) => (
            <tr key={r.key} className={sent.has(r.key) ? "" : "xm-skip"}
              title={(r.uses ?? []).map((u) => `${u.part_name || u.code || u.op_id} ×${u.qty}`).join("\n")}>
              <td>{tt.kind(r.kind)}</td>
              <td><b>{r.name}</b>{r.known === false && <span className="xm-unknown" data-testid={`xm-unknown-${r.key}`}> {t("xm.unknown")}</span>}
                {r.mismatch && <span className="xm-mis" title={t("xm.mismatch_hint")}> ⚠ {t("xm.mismatch")}</span>}</td>
              <td className="num">{fmt(r.d)}</td><td>{tt.side(r)}</td>
              <td className="num">{r.kind === "drill" ? r.holes : ""}</td>
              <td className="num">{r.kind === "mill" ? fmt(r.mill_m, 3) : ""}</td>
              <td className="num">{r.kind === "mill" ? fmt(r.mill_pass_m, 3) : ""}</td>
              <td className="num">{r.kind === "saw" ? fmt(r.saw_m, 3) : ""}</td>
              <td className="num">{r.parts}</td>
              <td>{r.mes_code || <span className="muted">{t("xm.no_code")}</span>}</td>
              <td>{sent.has(r.key) ? "✓" : "—"}</td>
            </tr>
          ))}
          {!(work.tools ?? []).length && <tr><td colSpan={11} className="muted">{t("xm.no_xnc")}</td></tr>}
        </tbody>
      </table>
      {(work.errors ?? []).length > 0 && <p className="xm-err">{t("xm.errors")}: {work.errors.map((e) => e.code || e.op_id).join(", ")}</p>}
    </>
  );
}

const NEW_TOOL = { kind: "drill" as ToolRow["kind"], name: "", d: 8, side: "face", through: false };

export function XncMesSection() {
  const { t } = useTranslation();
  const tt = useToolText();
  const cfg = useDefaults<XncMesSettings>("xnc_mes");
  const [d, setD] = useState<XncMesSettings | null>(null);
  const [pid, setPid] = useState("");
  const [own, setOwn] = useState<ToolRow[] | null>(null);     // «bizning asboblar» (tahrirlanadigan nusxa)
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [nt, setNt] = useState(NEW_TOOL);
  useEffect(() => { if (cfg.data) setD({ ...DEF, ...cfg.data }); }, [cfg.data]);
  const projects = useQuery({ queryKey: ["projects", "xm"], queryFn: () => get<{ id: string; number: number; name: string }[]>("/projects", { all_folders: true, limit: 300 }) });
  const tools = useQuery({ queryKey: ["xnc-mes-tools", pid, cfg.data], queryFn: () => get<ToolRow[]>("/xnc-mes/tools", { pid: pid || undefined }) });
  const work = useQuery({ enabled: !!pid, queryKey: ["xnc-work", pid, cfg.data], queryFn: () => get<XncWork>(`/projects/${pid}/xnc-tools`) });
  useEffect(() => { if (tools.data && !dirty) setOwn(tools.data.filter((r) => !r.unknown)); }, [tools.data, dirty]);
  const ownKeys = useMemo(() => new Set((own ?? []).map((r) => r.key)), [own]);
  const unknown = useMemo(() => (tools.data ?? []).filter((r) => r.unknown && !ownKeys.has(r.key)), [tools.data, ownKeys]);
  if (!d || !own) return null;
  const upd = (key: string, f: Partial<ToolRow>) => { setDirty(true); setOwn(own.map((r) => (r.key === key ? { ...r, ...f } : r))); };
  const save = async () => {
    const codes = own.map((r) => ({ kind: r.kind, name: r.name, d: r.d, side: r.side, through: r.through, mes_code: (r.mes_code ?? "").trim(),
      comment: (r.comment ?? "").trim(), active: r.active !== false, usage: r.usage ?? 0 }));
    const ok = await call(() => put("/settings/xnc_mes/default", { ...d, codes }));
    if (ok) {
      setDirty(false);
      void qc.invalidateQueries({ queryKey: ["defaults", "xnc_mes"] });
      useUI.getState().toast(t("app.saved"), "ok");
    }
  };
  const scan = async () => {
    setBusy(true);
    try {
      const r = await call(() => post<{ projects: number; found: number; rows: ToolRow[] }>("/xnc-mes/tools/scan"));
      if (!r) return;
      setOwn(r.rows.filter((x) => !x.unknown));
      setDirty(false);
      void qc.invalidateQueries({ queryKey: ["defaults", "xnc_mes"] });
      useUI.getState().toast(t("xm.scanned", { p: r.projects, n: r.found }), "ok");
    } finally { setBusy(false); }
  };
  const addRow = (r: Omit<ToolRow, "key" | "mes_code">) => {
    const key = `${r.kind}|${r.name.trim().toLowerCase()}|${Number(r.d)}|${r.kind === "drill" ? r.side : ""}|${r.kind === "drill" && r.through ? 1 : 0}`;
    if (!r.name.trim() || ownKeys.has(key)) return;
    setDirty(true);
    setOwn([...own, { ...r, side: r.kind === "drill" ? r.side : "", through: r.kind === "drill" && r.through, key, mes_code: "", comment: "",
      active: true, usage: r.usage ?? 0, unknown: false }]);
  };
  const chk = (k: keyof XncMesSettings, label: string) => (
    <Check checked={!!d[k]} label={label} onChange={(v) => setD({ ...d, [k]: v })} testid={`xm-${k}`} disabled={k !== "enabled" && !d.enabled} />
  );
  return (
    <div className="xm" data-testid="xnc-mes">
      <div className="xm-head"><h3>{t("xm.title")}</h3><Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} testid="xm-save" />
        {dirty && <span className="xm-dirty">{t("xm.unsaved")}</span>}</div>
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
      <div className="xm-proj">
        <Btn icon={FolderSearch} label={t("xm.scan")} onClick={() => void scan()} disabled={busy} testid="xm-scan" />
        <span className="grow" />
        {t("xm.project")}:{" "}
        <Sel value={pid} width={360} testid="xm-project" onChange={(v) => setPid(v)}
          options={[{ value: "", label: t("xm.project_none") }, ...(projects.data ?? []).map((p) => ({ value: p.id, label: `№${p.number} ${p.name}` }))]} /></div>
      {!own.length && <p className="xm-empty">{t("xm.list_empty")}</p>}
      <table className="simple xm-table" data-testid="xm-tools">
        <thead><tr><th>{t("xm.col.active")}</th><th>{t("xm.col.kind")}</th><th>{t("xm.col.tool")}</th><th>Ø</th><th>{t("xm.col.side")}</th>
          <th>{t("xm.col.usage")}</th><th>{t("xm.col.in_project")}</th><th>{t("xm.col.code")}</th><th>{t("xm.col.comment")}</th><th /></tr></thead>
        <tbody>
          {own.map((r) => (
            <tr key={r.key} className={(r.in_project ? "xm-inproj " : "") + (r.active === false ? "xm-skip" : "")} data-testid={`xm-row-${r.key}`}>
              <td><input type="checkbox" checked={r.active !== false} onChange={(e) => upd(r.key, { active: e.target.checked })}
                data-testid={`xm-active-${r.key}`} /></td>
              <td>{tt.kind(r.kind)}</td>
              <td><b>{r.name}</b>{r.mismatch && <span className="xm-mis" title={t("xm.mismatch_hint")}> ⚠ {t("xm.mismatch")}</span>}</td>
              <td className="num">{fmt(r.d)}</td><td>{tt.side(r)}</td>
              <td className="num">{r.usage || ""}</td><td>{r.in_project ? "✓" : ""}</td>
              <td><input className="inp xm-code" value={r.mes_code ?? ""} placeholder={t("xm.code_ph")} data-testid={`xm-code-${r.key}`}
                onChange={(e) => upd(r.key, { mes_code: e.target.value })} /></td>
              <td><input className="inp" value={r.comment ?? ""} onChange={(e) => upd(r.key, { comment: e.target.value })} /></td>
              <td><IconBtn icon={Trash} title={t("app.delete")} onClick={() => { setDirty(true); setOwn(own.filter((x) => x.key !== r.key)); }} /></td>
            </tr>
          ))}
          {unknown.map((r) => (
            <tr key={r.key} className="xm-unknown-row" data-testid={`xm-unk-${r.key}`}>
              <td /><td>{tt.kind(r.kind)}</td>
              <td><b>{r.name}</b> <span className="xm-unknown">{t("xm.unknown")}</span>
                {r.mismatch && <span className="xm-mis" title={t("xm.mismatch_hint")}> ⚠ {t("xm.mismatch")}</span>}</td>
              <td className="num">{fmt(r.d)}</td><td>{tt.side(r)}</td><td /><td>✓</td>
              <td colSpan={2}><Btn icon={Plus} label={t("xm.add_to_list")} onClick={() => addRow({ ...r, usage: 1 })} testid={`xm-add-${r.key}`} /></td><td />
            </tr>
          ))}
        </tbody>
      </table>
      <div className="xm-add">
        <Sel value={nt.kind} width={110} onChange={(v) => setNt({ ...nt, kind: v as ToolRow["kind"] })}
          options={(["drill", "mill", "saw"] as const).map((k) => ({ value: k, label: tt.kind(k) }))} />
        <input className="inp" style={{ width: 120 }} placeholder={t("xm.col.tool")} value={nt.name} onChange={(e) => setNt({ ...nt, name: e.target.value })}
          data-testid="xm-new-name" />
        Ø <input className="inp" type="number" style={{ width: 70 }} value={nt.d} onChange={(e) => setNt({ ...nt, d: Number(e.target.value) })} />
        {nt.kind === "drill" && <Sel value={nt.side} width={110} onChange={(v) => setNt({ ...nt, side: v })}
          options={["face", "side"].map((x) => ({ value: x, label: t(`xm.side.${x}`) }))} />}
        {nt.kind === "drill" && nt.side === "face" && <Check checked={nt.through} label={t("xm.through")} onChange={(v) => setNt({ ...nt, through: v })} />}
        <Btn icon={Plus} label={t("app.add")} disabled={!nt.name.trim()} onClick={() => { addRow({ ...nt, usage: 0 }); setNt(NEW_TOOL); }} testid="xm-new-add" />
      </div>
      {pid && <>
        <h4>{t("xm.preview")}</h4>
        {work.data ? <XncWorkTable work={work.data} testid="xm-preview" /> : <p className="muted">…</p>}
      </>}
    </div>
  );
}
