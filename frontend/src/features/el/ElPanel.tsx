// EL — Кромка (UI_SPEC §6): Параметры (chap — material, o'ng — narx) va Детали (CS dan yig'iladi).
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { CircleQuestionMark, Save, Settings2, Layers } from "lucide-react";
import { call, qc, useEdgeUsage } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { ELParams, EdgeUsage, Operation, Project } from "../../api/types";
import { useUI, type ElTab } from "../../store/ui";
import { Grid } from "../../shared/grid/Grid";
import { Area, Check, Field, IconBtn, Num, Sel, Tabs, money } from "../../shared/ui";

const ROUND = [0, 0.1, 0.5, 1, 5, 10];

export function ElPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const el = op.el!;
  const stamp = useMemo(() => JSON.stringify([op, project.operations.filter((o) => o.type === "CS").map((o) => o.parts), project.products]),
    [op, project.operations, project.products]);
  const usage = useEdgeUsage(project.id, op.id, stamp);
  const u: EdgeUsage | undefined = usage.data;
  const pe = (f: Partial<ELParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { el: f }));
  const cur = project.currency;
  const n = (v: number | null, d = 0) => (v === null ? d : v);
  const cols = useMemo<ColDef<EdgeUsage["rows"][number]>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("el.col.material"), field: "material", width: 220 },
    { headerName: t("el.col.length"), field: "length", width: 80, cellClass: "num" },
    { headerName: t("el.col.edges_len"), field: "edges_len", width: 80, cellClass: "num" },
    { headerName: t("el.col.width"), field: "width", width: 80, cellClass: "num" },
    { headerName: t("el.col.edges_wid"), field: "edges_wid", width: 80, cellClass: "num" },
    { headerName: t("el.col.qty"), field: "qty", width: 60, cellClass: "num" },
    { headerName: t("el.col.edge_m"), field: "edge_m", width: 100, cellClass: "num" },
    { headerName: t("el.col.name"), field: "name", flex: 1 },
  ], [t]);
  const saveDefault = async () => {
    const r = await call(() => put("/settings/el_defaults/default", el));
    if (r) { ui.toast(t("el.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  const tabs = (
    <Tabs<ElTab> value={ui.elTab} onChange={(k) => ui.set({ elTab: k })} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2 }, { key: "parts", label: t("cs.tab.parts"), icon: Layers, testid: "el-tab-parts" }]}
      right={<>
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
  );
  if (ui.elTab === "parts") {
    return (
      <div className="panel">
        {tabs}
        <Grid className="grow" rowData={u?.rows ?? []} columnDefs={cols} testid="el-parts" />
        <div className="hint">{t("el.total")}: {u?.work_m ?? 0} {t("u.m")} ({t("el.work")}), {u?.material_m ?? 0} {t("u.m")} ({t("el.material")})</div>
      </div>
    );
  }
  return (
    <div className="panel">
      {tabs}
      <div className="form2 scroll" data-testid="el-params">
        <div className="form-col">
          <div className="form-h">{t("el.p.material")}</div>
          <Field label=" "><Check checked={el.count_material} label={t("el.p.count_material")} onChange={(v) => pe({ count_material: v })} /></Field>
          <Field label={t("el.p.width")} unit={t("u.mm")}><Num value={el.width} onCommit={(v) => pe({ width: n(v, 19) })} /></Field>
          <Field label={t("el.p.thickness")} unit={t("u.mm")} hint={t("el.p.thickness_hint")}><Num value={el.thickness} min={0} onCommit={(v) => pe({ thickness: n(v) })} testid="el-thickness" /></Field>
          <Field label={t("el.p.jointing")} unit={t("u.mm")}><Num value={el.jointing_width} min={0} onCommit={(v) => pe({ jointing_width: n(v) })} /></Field>
          <div className="form-h">{t("el.p.usage")}</div>
          <Field label={t("el.p.waste")} unit="%"><Num value={el.waste_percent} min={0} onCommit={(v) => pe({ waste_percent: n(v) })} /></Field>
          <Field label={t("el.p.overhang")} unit={t("u.mm")}><Num value={el.overhang} min={0} onCommit={(v) => pe({ overhang: n(v, 20) })} /></Field>
          <Field label={t("el.p.min_glue")} unit={t("u.mm")}><Num value={el.min_glue_length} min={0} onCommit={(v) => pe({ min_glue_length: n(v) })} /></Field>
          <div className="form-h">{t("el.p.marking")}</div>
          <Field label={t("el.p.symbol")} unit={t("el.p.one_char")}>
            <input className="inp" style={{ width: 50, textAlign: "center" }} maxLength={1} value={el.symbol}
              onChange={(e) => e.target.value && pe({ symbol: e.target.value.slice(0, 1) })} /></Field>
          <Field label={t("el.p.color")}><input type="color" className="inp color" value={el.color || "#000000"}
            onChange={(e) => pe({ color: e.target.value })} /></Field>
          <Field label={t("el.p.lines")}><Sel value={el.marker_lines} width={60} onChange={(v) => pe({ marker_lines: v })}
            options={[1, 2, 3].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <div className="form-h">{t("cs.p.limits")}</div>
          <Field label={t("el.p.min_perp")} unit={t("u.mm")}><Num value={el.min_perp_side} min={0} onCommit={(v) => pe({ min_perp_side: n(v) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cost")}</div>
          <Field label={t("el.p.price")} unit={cur}><Num value={el.price} min={0} onCommit={(v) => pe({ price: n(v) })} /></Field>
          <Field label={t("el.p.mat_round")}><Sel value={el.material_rounding} width={170} onChange={(v) => pe({ material_rounding: v })}
            options={ROUND.map((v) => ({ value: v, label: v ? t("el.round_up", { v }) : t("el.round_none") }))} /></Field>
          <Field label={t("el.p.mat_len")} unit={t("u.m")}><span className="ro" data-testid="el-material-m">{u?.material_m ?? "…"}</span></Field>
          <Field label={t("el.p.mat_cost")} unit={cur}><span className="ro">{money(op.cost_material)}</span></Field>
          <Field label={t("el.p.op_price")} unit={cur}><Num value={el.op_price} min={0} onCommit={(v) => pe({ op_price: n(v) })} /></Field>
          <Field label={t("el.p.work_round")}><Sel value={el.work_rounding} width={170} onChange={(v) => pe({ work_rounding: v })}
            options={ROUND.map((v) => ({ value: v, label: v ? t("el.round_up", { v }) : t("el.round_none") }))} /></Field>
          <Field label={t("el.p.work_len")} unit={t("u.m")}><span className="ro" data-testid="el-work-m">{u?.work_m ?? "…"}</span></Field>
          <Field label={t("el.p.op_cost")} unit={cur}><span className="ro">{money(op.cost_operation)}</span></Field>
          <Field label={t("el.p.cost")} unit={cur}><span className="ro">{money(op.cost_material + op.cost_operation)}</span></Field>
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={4} onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
        </div>
      </div>
    </div>
  );
}
