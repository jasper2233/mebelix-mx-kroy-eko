// GR — Пазование: «Параметры» (W / D / O, arra qalinligi, narx + hisoblangan uzunlik/narx) va «Детали» (10 ustunli jadval).
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { CircleQuestionMark, Layers, Save, Settings2 } from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { GRParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Area, Check, Field, IconBtn, Num, Tabs, money } from "../../shared/ui";
import { Lbl } from "../help/HelpTip";
import { openHelp } from "../help/helpStore";
import { GrSketch } from "./GrSketch";
import { OpPartsGrid } from "./OpPartsGrid";
import { useGrooveUsage, type GrooveRow } from "./grooveApi";

type GrTab = "params" | "parts";

export function GrPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const [tab, setTab] = useState<GrTab>("params");
  const fallback = useDefaults<GRParams>("gr_defaults");               // op.gr yo'q bo'lsa (kutilmagan) — standart qiymatlar
  const g: GRParams | undefined = op.gr ?? fallback.data;
  const stamp = useMemo(() => JSON.stringify([op, project.operations.filter((o) => o.type === "CS").map((o) => o.parts), project.products]),
    [op, project.operations, project.products]);
  const usage = useGrooveUsage(project.id, op.id, stamp);
  const u = usage.data;
  const cur = project.currency;
  const pg = (f: Partial<GRParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { gr: f }));
  const saveDefault = async () => {
    const r = await call(() => put("/settings/gr_defaults/default", g));
    if (r) { ui.toast(t("gr.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };

  const mark = (v: number) => (v === 0 ? "" : v === 1 ? "+" : `+ ${t("gr.back")}`);
  const cols = useMemo<ColDef<GrooveRow>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum", sortable: false },
    { headerName: t("el.col.material"), field: "material", width: 200 },
    { headerName: t("el.col.length"), field: "length", width: 80, cellClass: "num" },
    { headerName: t("gr.col.top"), field: "top", width: 66, valueFormatter: (p) => mark(p.value as number), cellClass: "ctr" },
    { headerName: t("gr.col.bottom"), field: "bottom", width: 66, valueFormatter: (p) => mark(p.value as number), cellClass: "ctr" },
    { headerName: t("el.col.width"), field: "width", width: 80, cellClass: "num" },
    { headerName: t("gr.col.left"), field: "left", width: 66, valueFormatter: (p) => mark(p.value as number), cellClass: "ctr" },
    { headerName: t("gr.col.right"), field: "right", width: 66, valueFormatter: (p) => mark(p.value as number), cellClass: "ctr" },
    { headerName: t("el.col.qty"), field: "qty", width: 60, cellClass: "num" },
    { headerName: t("gr.col.len_m"), field: "groove_len_m", width: 100, cellClass: "num" },
    { headerName: t("el.col.name"), field: "name", flex: 1, minWidth: 120 },
  ], [t]); // eslint-disable-line react-hooks/exhaustive-deps

  const tabs = (
    <Tabs<GrTab> value={tab} onChange={setTab} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2, testid: "gr-tab-params" },
      { key: "parts", label: `${t("cs.tab.parts")}${u ? ` (${u.rows.length})` : ""}`, icon: Layers, testid: "gr-tab-parts" }]}
      right={<>
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} testid="gr-save-default" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => openHelp("gr")} />
      </>} />
  );
  if (!g) return <div className="panel">{tabs}</div>;

  if (tab === "parts") {
    return (
      <div className="panel">
        {tabs}
        <OpPartsGrid<GrooveRow> project={project} rows={u?.rows ?? []} columnDefs={cols} testid="gr-parts"
          summary={<span className="stat">{t("el.total")}: <b data-testid="gr-parts-total">{u?.usage ?? 0}</b> {t("u.m")}</span>} />
        {!u?.rows.length && <p className="muted hint">{t("gr.hint")}</p>}
      </div>
    );
  }
  return (
    <div className="panel">
      {tabs}
      <div className="form2 scroll" data-testid="gr-params">
        <div className="form-col">
          <Field label={<Lbl text={t("gr.p.width")} topic="gr" id="width" />} unit={t("u.mm")}>
            <Num value={g.width} min={0.1} onCommit={(v) => pg({ width: v ?? g.width })} testid="gr-width" /></Field>
          <Field label={<Lbl text={t("gr.p.depth")} topic="gr" id="depth" />} unit={t("u.mm")}>
            <Num value={g.depth} min={0} onCommit={(v) => pg({ depth: v ?? g.depth })} testid="gr-depth" /></Field>
          <Field label={<Lbl text={t("gr.p.offset")} topic="gr" id="offset" />} unit={t("u.mm")}>
            <Num value={g.offset} min={0} onCommit={(v) => pg({ offset: v ?? g.offset })} testid="gr-offset" /></Field>
          <Field label=" ">
            <Check checked={g.offset_inclusive} label={<Lbl text={t("gr.p.offset_incl")} topic="gr" id="offset_incl" />}
              onChange={(v) => pg({ offset_inclusive: v })} testid="gr-offset-incl" /></Field>
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={5}
            onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cost")}</div>
          <Field label={<Lbl text={t("gr.p.price")} topic="gr" id="price" />} unit={cur}>
            <Num value={g.price} min={0} onCommit={(v) => pg({ price: v ?? 0 })} testid="gr-price" /></Field>
          <Field label={<Lbl text={t("gr.p.usage")} topic="gr" id="usage" />} unit={t("u.m")}>
            <span className="ro" data-testid="gr-usage">{u?.usage ?? g.usage}</span></Field>
          <Field label={<Lbl text={t("gr.p.cost")} topic="gr" id="cost" />} unit={cur}>
            <span className="ro" data-testid="gr-cost">{money(op.cost_material + op.cost_operation)}</span></Field>
          <Field label={<Lbl text={t("gr.p.saw")} topic="gr" id="saw" />} unit={t("u.mm")} hint={t("gr.saw_hint")}>
            <Num value={g.saw_thickness} min={0.1} onCommit={(v) => pg({ saw_thickness: v ?? g.saw_thickness })} testid="gr-saw" /></Field>
          <Field label={<Lbl text={t("gr.p.passes")} topic="gr" id="passes" />} hint={t("gr.passes_hint")}>
            <span className="ro" data-testid="gr-passes">{u?.passes ?? g.passes}</span></Field>
          <Field label={<Lbl text={t("gr.p.cut")} topic="gr" id="cut" />} unit={t("u.m")}>
            <span className="ro" data-testid="gr-cut">{u?.cut_length ?? g.cut_length}</span></Field>
          <div className="help-gr-sketch"><GrSketch vals={{ o: g.offset, w: g.width, d: g.depth }} /></div>
        </div>
      </div>
    </div>
  );
}
