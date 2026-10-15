// EL — Кромка (UI_SPEC §6): Параметры (chap — material, o'ng — narx) va Детали (CS dan yig'iladi).
// Har parametr yonida «?» (kontekst yordami); «Детали» jadvali: saralash, Ctrl+Space, Home/End/↑/↓ (OpPartsGrid).
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { CircleQuestionMark, Palette, Save, Settings2, Layers } from "lucide-react";
import { ElSymbolsDialog } from "./ElSymbolsDialog";
import { call, qc, useEdgeUsage } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { ELParams, EdgeUsage, Operation, Project } from "../../api/types";
import { useUI, type ElTab } from "../../store/ui";
import { Area, Check, Field, IconBtn, Num, Sel, Tabs, money } from "../../shared/ui";
import { Lbl } from "../help/HelpTip";
import { openHelp } from "../help/helpStore";
import { OpPartsGrid } from "./OpPartsGrid";

type EdgeRow = EdgeUsage["rows"][number];

// Yaxlitlash kodlari: o'nlik xonalar × 10 + rejim (0 — yaqiniga, 1 — kattaga, 2 — kichikka)
const ROUND = [0, 1, 2, 10, 11, 12, 20, 21, 22, 30, 31, 32, 40, 41, 42];
const roundMask = (code: number) => {
  const d = Math.floor(code / 10);
  const z = d ? `0.${"0".repeat(d)}` : "0";
  return [`[${z}]`, `⌈${z}⌉`, `⌊${z}⌋`][code % 10];
};

export function ElPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const el = op.el!;
  const [symDlg, setSymDlg] = useState(false);       // «Настройка символов и цветов»
  const stamp = useMemo(() => JSON.stringify([op, project.operations.filter((o) => o.type === "CS").map((o) => o.parts), project.products]),
    [op, project.operations, project.products]);
  const usage = useEdgeUsage(project.id, op.id, stamp);
  const u: EdgeUsage | undefined = usage.data;
  const pe = (f: Partial<ELParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { el: f }));
  const cur = project.currency;
  const n = (v: number | null, d = 0) => (v === null ? d : v);
  const lbl = (id: string, key: string) => <Lbl text={t(key)} topic="el" id={id} />;
  const cols = useMemo<ColDef<EdgeRow>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum", sortable: false },
    { headerName: t("el.col.material"), colId: "material", width: 240,
      valueGetter: (p) => (p.data ? `(${p.data.op_type ?? "CS"}) ${p.data.material}` : "") },
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
        <IconBtn icon={Palette} title={t("el.sym.title")} onClick={() => setSymDlg(true)} testid="el-symbols" />
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => openHelp("el")} />
      </>} />
  );
  const symbols = symDlg && <ElSymbolsDialog onClose={() => setSymDlg(false)} />;
  if (ui.elTab === "parts") {
    return (
      <div className="panel">
        {tabs}
        {symbols}
        <OpPartsGrid<EdgeRow> project={project} rows={u?.rows ?? []} columnDefs={cols} testid="el-parts"
          rowClass={(r) => (r.narrow ? "row-warn" : "")} />
        <div className="hint">{t("el.total")}: {u?.work_m ?? 0} {t("u.m")} ({t("el.work")}), {u?.material_m ?? 0} {t("u.m")} ({t("el.material")})
          {(u?.narrow ?? 0) > 0 && <span className="warn" data-testid="el-narrow"> · {t("el.narrow", { n: u?.narrow, mm: el?.min_perp_side ?? 0 })}</span>}</div>
      </div>
    );
  }
  return (
    <div className="panel">
      {tabs}
      {symbols}
      <div className="form2 scroll" data-testid="el-params">
        <div className="form-col">
          <div className="form-h">{t("el.p.material")}</div>
          <Field label=" "><Check checked={el.count_material} label={lbl("count_material", "el.p.count_material")} onChange={(v) => pe({ count_material: v })} /></Field>
          <Field label={lbl("width", "el.p.width")} unit={t("u.mm")}><Num value={el.width} onCommit={(v) => pe({ width: n(v, 19) })} /></Field>
          <Field label={lbl("thickness", "el.p.thickness")} unit={t("u.mm")} hint={t("el.p.thickness_hint")}><Num value={el.thickness} min={0} onCommit={(v) => pe({ thickness: n(v) })} testid="el-thickness" /></Field>
          <Field label={lbl("jointing", "el.p.jointing")} unit={t("u.mm")}><Num value={el.jointing_width} min={0} onCommit={(v) => pe({ jointing_width: n(v) })} /></Field>
          <div className="form-h">{t("el.p.usage")}</div>
          <Field label={lbl("waste", "el.p.waste")} unit="%"><Num value={el.waste_percent} min={0} onCommit={(v) => pe({ waste_percent: n(v) })} /></Field>
          <Field label={lbl("overhang", "el.p.overhang")} unit={t("u.mm")}><Num value={el.overhang} min={0} onCommit={(v) => pe({ overhang: n(v, 20) })} /></Field>
          <Field label={lbl("min_glue", "el.p.min_glue")} unit={t("u.mm")}><Num value={el.min_glue_length} min={0} onCommit={(v) => pe({ min_glue_length: n(v) })} /></Field>
          <div className="form-h">{t("el.p.marking")}</div>
          <Field label={lbl("symbol", "el.p.symbol")} unit={t("el.p.one_char")}>
            <input className="inp" style={{ width: 50, textAlign: "center" }} maxLength={1} value={el.symbol}
              onChange={(e) => e.target.value && pe({ symbol: e.target.value.slice(0, 1) })} /></Field>
          <Field label={lbl("color", "el.p.color")}>
            {/* «Цвет» tugmasi (maslahat «Выбор цвета»): tizim rang tanlash oynasi; yonida joriy rang */}
            <span className="btn btn-default btn-sm el-color-btn" title={t("el.pick_color")}>
              <span>{t("el.color_btn")}</span>
              <span className="el-color-swatch" style={{ background: el.color || "#000000" }} />
              <input type="color" title={t("el.pick_color")} aria-label={t("el.pick_color")} value={el.color || "#000000"}
                data-testid="el-color" onChange={(e) => pe({ color: e.target.value })} />
            </span></Field>
          <Field label={lbl("lines", "el.p.lines")}><Sel value={el.marker_lines} width={60} onChange={(v) => pe({ marker_lines: v })}
            options={[1, 2, 3].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <div className="form-h">{t("cs.p.limits")}</div>
          <Field label={lbl("min_perp", "el.p.min_perp")} unit={t("u.mm")}><Num value={el.min_perp_side} min={0} onCommit={(v) => pe({ min_perp_side: n(v) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cost")}</div>
          <Field label={lbl("price", "el.p.price")} unit={cur}><Num value={el.price} min={0} onCommit={(v) => pe({ price: n(v) })} /></Field>
          <Field label={lbl("mat_round", "el.p.mat_round")} hint={t("el.round_hint")}><Sel value={el.material_round} width={190} onChange={(v) => pe({ material_round: v })}
            testid="el-mat-round" options={ROUND.map((v) => ({ value: v, label: `${roundMask(v)} ${t(`el.round.${v % 10}`)}` }))} /></Field>
          <Field label={lbl("mat_len", "el.p.mat_len")} unit={t("u.m")}><span className="ro" data-testid="el-material-m">{u?.material_m ?? "…"}</span></Field>
          <Field label={lbl("mat_cost", "el.p.mat_cost")} unit={cur}><span className="ro">{money(op.cost_material)}</span></Field>
          <Field label={lbl("op_price", "el.p.op_price")} unit={cur}><Num value={el.op_price} min={0} onCommit={(v) => pe({ op_price: n(v) })} /></Field>
          <Field label={lbl("work_round", "el.p.work_round")} hint={t("el.round_hint")}><Sel value={el.work_round} width={190} onChange={(v) => pe({ work_round: v })}
            options={ROUND.map((v) => ({ value: v, label: `${roundMask(v)} ${t(`el.round.${v % 10}`)}` }))} /></Field>
          <Field label={lbl("work_len", "el.p.work_len")} unit={t("u.m")}><span className="ro" data-testid="el-work-m">{u?.work_m ?? "…"}</span></Field>
          <Field label={lbl("op_cost", "el.p.op_cost")} unit={cur}><span className="ro">{money(op.cost_operation)}</span></Field>
          <Field label={lbl("cost", "el.p.cost")} unit={cur}><span className="ro">{money(op.cost_material + op.cost_operation)}</span></Field>
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={4} onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
        </div>
      </div>
    </div>
  );
}
