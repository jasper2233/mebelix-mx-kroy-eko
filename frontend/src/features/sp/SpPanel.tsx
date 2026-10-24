// SP — Обработка поверхности (W12): «Параметры» (материал, расход, цена) и «Детали» (detallar: lits / orqa tomon, soni, maydon).
// Detalga SP «Свойства» oynasidagi (SP) bo'limida yoki «ЛП / ТП» ustunlarida biriktiriladi; EL / GR panellari bilan bir xil tuzilma.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { CircleQuestionMark, Layers, Save, Settings2 } from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { Operation, Project, SPParams } from "../../api/types";
import { useUI } from "../../store/ui";
import { Area, Check, Field, IconBtn, Num, Tabs, fmt, money } from "../../shared/ui";
import { OpPartsGrid } from "../el/OpPartsGrid";
import { useSurfaceUsage, type SurfaceRow } from "./spApi";

type SpTab = "params" | "parts";

export function SpPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const [tab, setTab] = useState<SpTab>("params");
  const fallback = useDefaults<SPParams>("sp_defaults");               // op.sp yo'q bo'lsa (eski JSON) — standart qiymatlar
  const sp: SPParams | undefined = op.sp ?? fallback.data;
  const stamp = useMemo(() => JSON.stringify([op, project.operations.filter((o) => o.type === "CS").map((o) => o.parts), project.products]),
    [op, project.operations, project.products]);
  const usage = useSurfaceUsage(project.id, op.id, stamp);
  const u = usage.data;
  const cur = project.currency;
  const ps = (f: Partial<SPParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { sp: f }));
  const saveDefault = async () => {
    const r = await call(() => put("/settings/sp_defaults/default", sp));
    if (r) { ui.toast(t("sp.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };

  const cols = useMemo<ColDef<SurfaceRow>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum", sortable: false },
    { headerName: t("el.col.material"), field: "material", width: 200 },
    { headerName: t("el.col.length"), field: "length", width: 80, cellClass: "num" },
    { headerName: t("el.col.width"), field: "width", width: 80, cellClass: "num" },
    { headerName: t("sp.col.front"), field: "front", width: 60, valueFormatter: (p) => (p.value ? "+" : ""), cellClass: "ctr" },
    { headerName: t("sp.col.back"), field: "back", width: 60, valueFormatter: (p) => (p.value ? "+" : ""), cellClass: "ctr" },
    { headerName: t("el.col.qty"), field: "qty", width: 60, cellClass: "num" },
    { headerName: t("sp.col.area"), field: "area_m2", width: 100, cellClass: "num" },
    { headerName: t("el.col.name"), field: "name", flex: 1, minWidth: 120 },
  ], [t]);

  const tabs = (
    <Tabs<SpTab> value={tab} onChange={setTab} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2, testid: "sp-tab-params" },
      { key: "parts", label: `${t("cs.tab.parts")}${u ? ` (${u.rows.length})` : ""}`, icon: Layers, testid: "sp-tab-parts" }]}
      right={<>
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} testid="sp-save-default" />
        <IconBtn icon={CircleQuestionMark} title={t("sp.help")} onClick={() => ui.toast(t("sp.help"), "info")} />
      </>} />
  );
  if (!sp) return <div className="panel">{tabs}</div>;

  if (tab === "parts") {
    return (
      <div className="panel">
        {tabs}
        <OpPartsGrid<SurfaceRow> project={project} rows={u?.rows ?? []} columnDefs={cols} testid="sp-parts"
          summary={<span className="stat">{t("el.total")}: <b data-testid="sp-parts-total">{fmt(u?.area_m2 ?? 0, 4)}</b> {t("u.m2")}</span>} />
        {!u?.rows.length && <p className="muted hint">{t("sp.hint")}</p>}
      </div>
    );
  }
  return (
    <div className="panel">
      {tabs}
      <div className="form2 scroll" data-testid="sp-params">
        <div className="form-col">
          <div className="form-h">{t("sp.g.material_params")}</div>
          <Field label=" "><Check checked={sp.count_material} label={t("sp.p.count_material")} onChange={(v) => ps({ count_material: v })}
            testid="sp-count-material" /></Field>
          <Field label={t("sp.p.len")} unit={t("u.mm")}><Num value={sp.length} min={0} onCommit={(v) => ps({ length: v ?? 0 })} /></Field>
          <Field label={t("sp.p.wid")} unit={t("u.mm")}><Num value={sp.width} min={0} onCommit={(v) => ps({ width: v ?? 0 })} /></Field>
          <Field label={t("sp.p.thk")} unit={t("u.mm")}><Num value={sp.thickness} min={0} onCommit={(v) => ps({ thickness: v ?? 0 })} /></Field>
          <Field label={t("sp.p.waste")} unit="%"><Num value={sp.waste_percent} min={0} max={100} onCommit={(v) => ps({ waste_percent: v ?? 0 })}
            testid="sp-waste" /></Field>
          <Field label={t("sp.p.rest")} unit={t("u.mm")} hint={t("sp.p.rest_hint")}><Num value={sp.rest_side} min={0}
            onCommit={(v) => ps({ rest_side: v ?? 0 })} testid="sp-rest" /></Field>
          <div className="form-h" title={t("sp.p.size_mode_hint")}>{t("sp.p.size_mode")}</div>
          <div className="radio-col" data-testid="sp-size-mode">
            {([-1, 0] as const).map((v) => (
              <label key={v} className="check"><input type="radio" checked={sp.size_mode === v}
                onChange={() => ps({ size_mode: v as SPParams["size_mode"] })} /> {t(v === -1 ? "sp.size.saw" : "sp.size.blank")}</label>
            ))}
          </div>
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={4} onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cost")}</div>
          <Field label={t("sp.p.price2")} unit={cur}><Num value={sp.price} min={0} onCommit={(v) => ps({ price: v ?? 0 })} testid="sp-price" /></Field>
          <Field label={t("sp.p.mat_area")} unit={t("u.m2")}><span className="ro" data-testid="sp-material">{fmt(u?.material_m2 ?? sp.material_m2, 4)}</span></Field>
          <Field label={t("sp.p.mat_cost")} unit={cur}><span className="ro" data-testid="sp-mat-cost">{money(op.cost_material)}</span></Field>
          <Field label={t("sp.p.op_price2")} unit={cur}><Num value={sp.op_price} min={0} onCommit={(v) => ps({ op_price: v ?? 0 })}
            testid="sp-op-price" /></Field>
          <Field label={t("sp.p.work_area")} unit={t("u.m2")}><span className="ro" data-testid="sp-area">{fmt(u?.area_m2 ?? sp.area_m2, 4)}</span></Field>
          <Field label={t("sp.p.op_cost")} unit={cur}><span className="ro" data-testid="sp-op-cost">{money(op.cost_operation)}</span></Field>
          <Field label={t("sp.p.cost")} unit={cur}><span className="ro" data-testid="sp-cost">{money(op.cost_material + op.cost_operation)}</span></Field>
        </div>
      </div>
    </div>
  );
}
