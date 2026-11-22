// EL — Кромка (UI_SPEC §6): Параметры (chap — material, o'ng — narx) va Детали (CS dan yig'iladi).
// Har parametr yonida «?» (kontekst yordami); «Детали» jadvali: saralash, Ctrl+Space, Home/End/↑/↓ (OpPartsGrid).
import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { CellValueChangedEvent, ColDef } from "ag-grid-community";
import { CircleQuestionMark, Palette, RotateCcw, Save, Settings2, Layers } from "lucide-react";
import { ElSymbolsDialog } from "./ElSymbolsDialog";
import { call, qc, useEdgeUsage } from "../../api/hooks";
import { get, patch, post, put } from "../../api/client";
import type { ELParams, EdgeUsage, Operation, Part, Project } from "../../api/types";
import { useUI, type ElTab } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Area, CheckRow, Field, IconBtn, Num, Sel, Tabs, money } from "../../shared/ui";
import { Lbl } from "../help/HelpTip";
import { openHelp } from "../help/helpStore";
import { OpPartsGrid } from "./OpPartsGrid";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import type { UserColContext, UserColsSource } from "../../shared/grid/userColumns";
import { partVarList, partVars } from "../cs/columns";
import { EL_EXTRA_SPECS, elExtraCols } from "./elExtraCols";

type EdgeRow = EdgeUsage["rows"][number];

// «Детали» ustunlari katalogi («Настройки», Ctrl+P): nom, tavsif (sarlavha maslahati), kenglik — belgilarda
const EL_COLUMNS: GridKind = { scope: "el_columns", specs: [
  // kengliklar onlayn jadvaldagi nisbatlarda (sarlavhalar qisqarmaydi)
  { key: "material", name: "el.col.material", desc: "elx.base_material", width: 30 },
  { key: "length", name: "el.col.length", desc: "elx.base_length", width: 9 },
  { key: "edges_len", name: "el.col.edges_len", desc: "elx.base_edges_len", width: 10 },
  { key: "width", name: "el.col.width", desc: "elx.base_width", width: 9 },
  { key: "edges_wid", name: "el.col.edges_wid", desc: "elx.base_edges_wid", width: 10 },
  { key: "qty", name: "el.col.qty", desc: "pcd.total", width: 7 },
  { key: "edge_m", name: "el.col.edge_m", desc: "elx.base_edge_m", width: 15 },
  { key: "name", name: "el.col.name", desc: "elx.base_name", width: 20 },
  ...EL_EXTRA_SPECS,      // onlayn tizimdagi qolgan ustunlar (standart yashirin)
] };

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
  const pe = (f: Partial<ELParams>) => call(() => patch(`/projects/${project.id}/operations/${op.id}`, { el: f }));
  // «Толщина» / «Ширина прифуговки» zagotovka o'lchamini o'zgartiradi — shu kromkali detallarning kroy natijalari o'chadi
  // (backend `_edge_size_changed`). CS «Параметры» dagi kabi oldindan tasdiq: qaysi operatsiyalar o'chishi serverdan so'raladi
  // (`edge-affected`, hech narsani o'zgartirmaydi); bekor qilinsa — PATCH yuborilmaydi.
  const guardedSize = async (field: "thickness" | "jointing_width", v: number) => {
    if (v === el[field]) return;
    type Affected = { ops: Array<{ id: string; type: string; code: string; name: string; manual: boolean; remnants_saved: boolean }> };
    const aff = await call(() => get<Affected>(`/projects/${project.id}/operations/${op.id}/edge-affected`));
    if (!aff) return;
    if (aff.ops.length) {
      const names = aff.ops.map((o) => {
        const flags = [o.manual ? t("el.inv_manual") : "", o.remnants_saved ? t("el.inv_remnants") : ""].filter(Boolean);
        return `(${o.type}) ${o.name}${flags.length ? ` — ${flags.join(", ")}` : ""}`;
      }).join("; ");
      const anyRem = aff.ops.some((o) => o.remnants_saved);
      const fieldName = t(field === "thickness" ? "el.p.thickness" : "el.p.jointing");
      const ok = await askConfirm(t("cs.params_invalidate_q"),
        t(anyRem ? "el.size_invalidate_rem" : "el.size_invalidate_text", { field: fieldName, ops: names }),
        { danger: true, ok: t("app.ok") });
      if (!ok) return;
    }
    await pe({ [field]: v } as Partial<ELParams>);
  };
  const cur = project.currency;
  const n = (v: number | null, d = 0) => (v === null ? d : v);
  const lbl = (id: string, key: string) => <Lbl text={t(key)} topic="el" id={id} />;
  const cols = useMemo<ColDef<EdgeRow>[]>(() => {
    // «Товар» = mahsulot nomi + «(CS) material» (xodimlar o'rgangan tizimdagidek): detal → mahsulot nomi xaritasi
    const multiProd = project.products.length > 1;
    const prodOf = new Map<string, string>();
    for (const o of project.operations) for (const p of o.parts) {
      prodOf.set(p.id, project.products.find((x) => x.id === p.product_id)?.name ?? "");
    }
    return [
      { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum", sortable: false },
      // onlayndagidek saralash faqat Длина / Окл. дл. / Ширина / Окл. шр. / Д-на кромки ustunlarida (2026-10-21 jonli solishtiruv)
      { headerName: t("el.col.material"), colId: "material", width: 300, sortable: false, headerTooltip: t("el.col.material_hint"),
        // onlayn tizimdagidek: mahsulot nomi faqat loyihada bir nechta mahsulot bo'lsa (aks holda «(CS) material»)
        valueGetter: (p) => (p.data ? `${multiProd ? prodOf.get(p.data.part_id) ?? "" : ""} (${p.data.op_type ?? "CS"}) ${p.data.material}`.trim() : "") },
      { headerName: t("el.col.length"), field: "length", width: 80, cellClass: "num" },
      { headerName: t("el.col.edges_len"), field: "edges_len", width: 80, cellClass: "num" },
      { headerName: t("el.col.width"), field: "width", width: 80, cellClass: "num" },
      { headerName: t("el.col.edges_wid"), field: "edges_wid", width: 80, cellClass: "num" },
      { headerName: t("el.col.qty"), field: "qty", width: 60, cellClass: "num", sortable: false },
      // sarlavha «Д-на кромки», birlik (m) — maslahatda
      { headerName: t("el.col.edge_m"), field: "edge_m", width: 100, cellClass: "num", headerTooltip: t("el.col.edge_m_hint") },
      { headerName: t("el.col.name"), field: "name", colId: "name", flex: 1, sortable: false },
      ...elExtraCols(t, project),
    ];
  }, [t, project]);
  // qatorlar detal ID (uid) tartibida (onlayn tizimdagidek); sarlavha bosilsa — boshqa saralash
  const rows = useMemo(() => [...(u?.rows ?? [])].sort((a, b) => a.uid - b.uid), [u]);
  // foydalanuvchi ustunlari: qator — detal (parametrlar detalning `user_params` ida, CS/CL «Детали» bilan umumiy, prefiks «part»)
  const partOf = useMemo(() => {
    const m = new Map<string, { opId: string; part: Part }>();
    for (const o of project.operations) for (const p of o.parts) m.set(p.id, { opId: o.id, part: p });
    return m;
  }, [project.operations]);
  const userSrc = useMemo<UserColsSource<EdgeRow>>(() => ({
    prefix: "part", rows, rowKey: (r) => r.part_id, params: (r) => partOf.get(r.part_id)?.part.user_params,
    setParams: (r, next) => { const h = partOf.get(r.part_id); if (h) h.part.user_params = next; },
    vars: (r) => {
      const h = partOf.get(r.part_id);
      return { ...(h ? partVars(project, h.part) : {}), length: r.length, width: r.width, qty: r.qty, material: r.material,
        edges_len: r.edges_len, edges_wid: r.edges_wid, edge_m: r.edge_m };
    },
    varList: [...partVarList(t), ...(["material", "edges_len", "edges_wid", "edge_m"] as const).map((k) => ({ name: k, label: t(`el.col.${k}`) }))],
    editable: (r) => partOf.has(r.part_id),
  }), [rows, partOf, project, t]);
  const colset = useGridColumns(EL_COLUMNS, cols, userSrc);
  const onCellChanged = (e: CellValueChangedEvent<EdgeRow>) => {
    const ctx = e.colDef.context as UserColContext<EdgeRow> | undefined;
    const h = e.data ? partOf.get(e.data.part_id) : undefined;
    if (!ctx?.patch || !h || !e.data) return;
    void call(() => post(`/projects/${project.id}/operations/${h.opId}/parts/batch-update`,
      [{ id: h.part.id, fields: ctx.patch(e.newValue, e.data!) }]));
  };
  // «По умолчанию»: MebeliX Kroy tavsiyasi (eni, qalinligi, prifugovka, narx, belgi, rang o'zgarmaydi)
  const applyDefault = async () => {
    const d = await call(() => get<{ el: Partial<ELParams> }>("/recommended-params"));
    if (!d || !(await askConfirm(t("cs.apply_default"), t("cs.apply_default_q"), { ok: t("app.ok") }))) return;
    await pe(d.el);
    ui.toast(t("cs.apply_default_done"), "ok");
  };
  const saveDefault = async () => {
    const r = await call(() => put("/settings/el_defaults/default", el));
    if (r) { ui.toast(t("el.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  // yorliqlar qatori: «Параметры» da — Сохранить, Настройка символов и цветов, Справка (onlayn tartib);
  // «Детали» da — detallar jadvalining asboblari (OpPartsGrid `tabs`)
  const tabsWith = (right: ReactNode) => (
    <Tabs<ElTab> value={ui.elTab} onChange={(k) => ui.set({ elTab: k })} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2 }, { key: "parts", label: t("cs.tab.parts"), icon: Layers, testid: "el-tab-parts" }]}
      right={right} />
  );
  const tabs = tabsWith(<>
    <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} />
    <IconBtn icon={RotateCcw} title={t("cs.apply_default")} onClick={() => void applyDefault()} testid="el-apply-default" />
    <IconBtn icon={Palette} title={t("el.sym.title")} onClick={() => setSymDlg(true)} testid="el-symbols" />
    <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => openHelp("el")} />
  </>);
  const symbols = symDlg && <ElSymbolsDialog onClose={() => setSymDlg(false)} />;
  if (ui.elTab === "parts") {
    return (
      <div className="panel">
        {symbols}
        <OpPartsGrid<EdgeRow> project={project} rows={rows} columnDefs={colset.columnDefs} testid="el-parts" tabs={tabsWith}
          rowClass={(r) => (r.narrow ? "row-warn" : "")} onColumns={colset.open} onCellValueChanged={onCellChanged}
          onHelp={() => openHelp("el")} />
        {colset.dialog}
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
          {/* bayroq — yorliq ustunida (onlayn tizimdagi joylashuv) */}
          <CheckRow checked={el.count_material} label={lbl("count_material", "el.p.count_material")} onChange={(v) => pe({ count_material: v })} />
          <Field label={lbl("width", "el.p.width")} unit={t("u.mm")}><Num value={el.width} min={0.1} max={1000} onCommit={(v) => pe({ width: n(v, 19) })} testid="el-width" /></Field>
          <Field label={lbl("thickness", "el.p.thickness")} unit={t("u.mm")} hint={t("el.p.thickness_hint")}><Num value={el.thickness} min={0} max={1000} onCommit={(v) => void guardedSize("thickness", n(v))} testid="el-thickness" /></Field>
          <Field label={lbl("jointing", "el.p.jointing")} unit={t("u.mm")}><Num value={el.jointing_width} min={0} max={1000} onCommit={(v) => void guardedSize("jointing_width", n(v))} testid="el-jointing" /></Field>
          <div className="form-h">{t("el.p.usage")}</div>
          <Field label={lbl("waste", "el.p.waste")} unit="%"><Num value={el.waste_percent} min={0} max={100} onCommit={(v) => pe({ waste_percent: n(v) })} /></Field>
          <Field label={lbl("overhang", "el.p.overhang")} unit={t("u.mm")}><Num value={el.overhang} min={0} max={10000} onCommit={(v) => pe({ overhang: n(v, 20) })} /></Field>
          <Field label={lbl("min_glue", "el.p.min_glue")} unit={t("u.mm")}><Num value={el.min_glue_length} min={0} max={100000} onCommit={(v) => pe({ min_glue_length: n(v) })} /></Field>
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
            testid="el-lines" options={[0, 1, 2, 3].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <div className="form-h">{t("cs.p.limits")}</div>
          <Field label={lbl("min_perp", "el.p.min_perp")} unit={t("u.mm")}><Num value={el.min_perp_side} min={0} max={100000} onCommit={(v) => pe({ min_perp_side: n(v) })} /></Field>
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
