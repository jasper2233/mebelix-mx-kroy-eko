// «Правила остатков» (2026-10-24, foydalanuvchi talabi): ombor ma'lumotlari MES bazasida; MX da — bazaga YUBORISH qoidasi
// (qoldiq / butun list ≥ foiz — korxona olib qoladi, kichigi mijozga), bazadan TOPIB QO'SHISH qoidasi va umumiy sozlamalar.
// Foiz material turi bo'yicha (LDSP, AKRIL, HDF …), kerak bo'lsa aniq material uchun (tur qoidasidan ustun).
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Plus, Save, Trash } from "lucide-react";
import { call, qc, useAppSettings, useDefaults } from "../../api/hooks";
import { get, put } from "../../api/client";
import type { CSCutParams, RemnantRules as Rules, RemnantSummary } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Field, IconBtn, Num, Txt, fmt } from "../../shared/ui";
import "./remnantRules.css";

const EMPTY: Rules = { types: [], materials: [], wait_mes: true, auto_commit: false, source: "local", mes_url: "",
  find_limit: 5, find_seconds: 8 };

export function RemnantRulesPage() {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const rules = useDefaults<Rules>("remnant_rules");
  const csd = useDefaults<{ material: unknown; cut: CSCutParams }>("cs_defaults");
  const sum = useQuery({ queryKey: ["remnants", "summary"], queryFn: () => get<RemnantSummary>("/remnants/summary") });
  const [d, setD] = useState<Rules | null>(null);
  const [useWh, setUseWh] = useState<boolean | null>(null);
  const [newType, setNewType] = useState("");
  const [newMat, setNewMat] = useState("");
  useEffect(() => { if (rules.data) setD({ ...EMPTY, ...rules.data }); }, [rules.data]);
  // namuna list maydoni (tur foizini m² da ko'rsatish uchun) — umumiy sozlamadagi yangi list o'lchami
  const sheetM2 = ((app.data?.default_sheet_length ?? 2750) * (app.data?.default_sheet_width ?? 1830)) / 1e6;
  const stat = useMemo(() => new Map((sum.data?.types ?? []).map((g) => [g.type, g])), [sum.data]);
  if (!d) return null;
  const pct = (type: string) => d.types.find((r) => r.type === type)?.keep_percent ?? null;
  const setPct = (type: string, v: number | null) => {
    const rest = d.types.filter((r) => r.type !== type);
    setD({ ...d, types: v && v > 0 ? [...rest, { type, keep_percent: Math.min(100, v) }] : rest });
  };
  const typeRows = Array.from(new Set([...(sum.data?.types ?? []).map((g) => g.type), ...d.types.map((r) => r.type)]));
  const knownMats = Array.from(new Set((sum.data?.materials ?? []).map((m) => m.material).filter(Boolean)));
  const save = async () => {
    const r = await call(() => put("/settings/remnant_rules/default", d));
    if (r && useWh !== null && csd.data && useWh !== !!csd.data.cut.use_warehouse)
      await call(() => put("/settings/cs_defaults/default", { ...csd.data, cut: { ...csd.data!.cut, use_warehouse: useWh } }));
    if (r) {
      void qc.invalidateQueries({ queryKey: ["defaults"] });
      void qc.invalidateQueries({ queryKey: ["remnants"] });
      ui.toast(t("app.saved"), "ok");
    }
  };
  return (
    <div className="page" data-testid="remnant-rules">
      <div className="page-head"><h2>{t("settings.page.remnant_rules")}</h2>
        <Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} testid="rr-save" /></div>
      <div className="scroll doc rr">
        <h3>{t("rr.source")}</h3>
        <div className="type-list">
          {(["mes", "local"] as const).map((k) => (
            <label key={k} className="type-item"><input type="radio" checked={d.source === k} data-testid={`rr-source-${k}`}
              onChange={() => setD({ ...d, source: k })} /> {t(`rr.source_${k}`)}</label>
          ))}
        </div>
        {d.source === "mes" && <Field label={t("rr.mes_url")}><Txt value={d.mes_url} width={420} placeholder="https://mes.example.uz/api/v1/kroy"
          onCommit={(v) => setD({ ...d, mes_url: v.trim() })} testid="rr-mes-url" /></Field>}
        <p className="muted">{t(d.source === "mes" ? "rr.source_mes_hint" : "rr.source_local_hint")}</p>

        <h3>{t("rr.send")}</h3>
        <p className="muted">{t("rr.send_hint")}</p>
        <table className="simple rr-table" data-testid="rr-types">
          <thead><tr><th>{t("rr.type")}</th><th>{t("rr.keep_pct")}</th><th>{t("rr.threshold", { a: fmt(sheetM2) })}</th>
            <th>{t("rr.in_stock")}</th><th>{t("rr.pending")}</th><th>{t("u.m2")}</th><th>{t("rr.total_pct")}</th></tr></thead>
          <tbody>
            {typeRows.map((ty) => {
              const g = stat.get(ty);
              const p = pct(ty);
              return (
                <tr key={ty} data-testid={`rr-type-${ty}`}>
                  <td><b>{ty}</b></td>
                  <td><Num value={p} allowEmpty min={0} max={100} width={60} onCommit={(v) => setPct(ty, v)} testid={`rr-pct-${ty}`} /> %</td>
                  <td className="num">{p ? `${fmt(Math.round(p * sheetM2) / 100)} ${t("u.m2")}` : t("rr.no_rule")}</td>
                  <td className="num">{g?.count ?? 0}</td><td className="num">{g?.pending ?? 0}</td>
                  <td className="num">{fmt(g?.area_m2 ?? 0)}</td><td className="num">{g?.percent_total ? `${fmt(g.percent_total)} %` : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="row gap">
          <Txt value={newType} width={140} placeholder={t("rr.type_new")} onCommit={setNewType} testid="rr-type-new" />
          <Btn icon={Plus} label={t("app.add")} disabled={!newType.trim()} onClick={() => { setPct(newType.trim().toUpperCase(), 30); setNewType(""); }} />
        </div>

        <h4>{t("rr.materials")}</h4>
        <p className="muted">{t("rr.materials_hint")}</p>
        <table className="simple rr-table" data-testid="rr-materials">
          <thead><tr><th>{t("rem.material")}</th><th>{t("rem.code")}</th><th>{t("rr.keep_pct")}</th><th /></tr></thead>
          <tbody>
            {d.materials.map((m, i) => (
              <tr key={`${m.code}|${m.material}|${i}`}>
                <td>{m.material}</td><td>{m.code}</td>
                <td><Num value={m.keep_percent} min={0.1} max={100} width={60} onCommit={(v) => setD({ ...d,
                  materials: d.materials.map((x, j) => (j === i ? { ...x, keep_percent: v && v > 0 ? Math.min(100, v) : x.keep_percent } : x)) })} /> %</td>
                <td><IconBtn icon={Trash} title={t("app.delete")} onClick={() => setD({ ...d, materials: d.materials.filter((_x, j) => j !== i) })} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row gap">
          <input className="inp" list="rr-known-mats" value={newMat} placeholder={t("rr.material_new")} style={{ width: 320 }}
            onChange={(e) => setNewMat(e.target.value)} data-testid="rr-mat-new" />
          <datalist id="rr-known-mats">{knownMats.map((m) => <option key={m} value={m} />)}</datalist>
          <Btn icon={Plus} label={t("app.add")} disabled={!newMat.trim()} testid="rr-mat-add"
            onClick={() => { setD({ ...d, materials: [...d.materials, { material: newMat.trim(), code: "", keep_percent: 30 }] }); setNewMat(""); }} />
        </div>
        <Check checked={d.auto_commit} label={t("rr.auto_commit")} onChange={(v) => setD({ ...d, auto_commit: v })} testid="rr-auto" />
        <Check checked={d.wait_mes} label={t("rr.wait_mes")} onChange={(v) => setD({ ...d, wait_mes: v })} testid="rr-wait" />
        {d.wait_mes && d.source === "local" && !app.data?.mes_enabled && <p className="muted">{t("rr.wait_mes_off")}</p>}

        <h3>{t("rr.find")}</h3>
        <p className="muted">{t("rr.find_hint")}</p>
        <Check checked={useWh ?? !!csd.data?.cut.use_warehouse} label={t("rr.use_default")} onChange={setUseWh} testid="rr-use-default" />
        <Field label={t("rr.find_limit")}><Num value={d.find_limit} min={1} max={20} width={60}
          onCommit={(v) => setD({ ...d, find_limit: Math.max(1, Math.min(20, Math.round(v ?? 5))) })} /></Field>
        <Field label={t("rr.find_seconds")} unit={t("rr.sec")}><Num value={d.find_seconds} min={1} max={30} width={60}
          onCommit={(v) => setD({ ...d, find_seconds: Math.max(1, Math.min(30, v ?? 8)) })} /></Field>
        <p className="muted">{t("rr.sale_hint")}</p>

        <h3>{t("rr.stock")}</h3>
        <table className="simple rr-table" data-testid="rr-stock">
          <thead><tr><th>{t("rem.material")}</th><th>{t("rr.type")}</th><th>{t("rr.keep_pct")}</th><th>{t("rr.in_stock")}</th>
            <th>{t("rr.pending")}</th><th>{t("u.m2")}</th><th>{t("rr.total_pct")}</th></tr></thead>
          <tbody>
            {(sum.data?.materials ?? []).map((m) => (
              <tr key={`${m.code}|${m.material}`}>
                <td>{m.material}{m.code && m.code !== m.material ? <span className="muted"> ({m.code})</span> : null}</td><td>{m.type}</td>
                <td className="num">{m.keep_percent ? `${fmt(m.keep_percent)} %${m.rule_source === "material" ? " *" : ""}` : "—"}</td>
                <td className="num">{m.count}</td><td className="num">{m.pending}</td><td className="num">{fmt(m.area_m2)}</td>
                <td className="num">{m.percent_total ? `${fmt(m.percent_total)} %` : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
