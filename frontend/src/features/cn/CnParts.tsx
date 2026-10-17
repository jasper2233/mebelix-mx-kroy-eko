// (CN) «Детали»: Д-на · Ш-на · Кол · Ткт · ОВ/ОН/ОЛ/ОП · Наименование · Форма · ОК · ИК · Ост. Kontur detal — bog'langan XNC dasturining yopiq freza konturi;
// pastda tanlangan detalning kichik kontur chizmasi (cn-shapes) va shakl ogohlantirishlari. CS «Детали» (CsParts) namunasida.
import { useCallback, useEffect, useMemo, useRef, useState, type ClipboardEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, ITooltipParams, SuppressKeyboardEventParams } from "ag-grid-community";
import {
  ArrowDownUp, ArrowLeftRight, ChevronDown, ChevronUp, CircleQuestionMark, ClipboardPaste, Columns3, CopyPlus, Drill, Funnel, Group, ListOrdered,
  Plus, Replace, SquareCheck, SquarePen, Square, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { post } from "../../api/client";
import type { CnShapeRow, Operation, Part, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import { scopeProps, suppressGridKey, useHotkeys } from "../../shared/hotkeys";
import { Dropdown, IconBtn, Sep, Toolbar, fmt } from "../../shared/ui";
import { SortDialog } from "../../shared/SortDialog";
import { buildColumns, NEW_ID, partsUserSource, partTooltip, type ColKey, type ColSetting, type PartCol } from "../cs/columns";
import { totalQty } from "../cs/sizes";
import { GroupActions, MoveToOp, PartProperties, SizeModeDialog } from "../cs/PartDialogs";
import { CnTabs } from "./CnPanel";
import { useCnShapes } from "./cnHooks";
import { bboxOf, ringPath } from "./cnGeom";

const SHOWN: ColKey[] = ["num", "length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right", "name", "total", "used", "left"];
const CN_WIDTH: Partial<Record<ColKey, number>> = { edge_top: 54, edge_bottom: 54, edge_left: 54, edge_right: 54, name: 150, used: 50, left: 50 };    // kromka nestingda ikkinchi darajali
// «Настройки» (Ctrl+P) uchun qo'shimcha (standartda yashirin) ustunlar
const EXTRA: ColKey[] = ["code", "uid", "description", "product_name", "article", "product_qty", "minus"];
const CN_COLS: ColSetting[] = [...SHOWN, ...EXTRA].map((key) => ({ key, visible: true, width: CN_WIDTH[key] }));
/** Ustunlar katalogi: nom / tavsif — CS detallari bilan bir xil (`pc.*`, `pcd.*`) + «Форма»; kenglik — belgilarda. */
const CN_CH: Record<string, number> = { length: 7, width: 7, qty: 5, grain: 4, edge_top: 6, edge_bottom: 6, edge_left: 6, edge_right: 6,
  name: 18, shape: 19, total: 5, used: 5, left: 5, code: 12, uid: 6, description: 21, product_name: 19, article: 9, product_qty: 6, minus: 6 };
const CN_COLUMNS: GridKind = { scope: "cn_columns", specs: [
  ...SHOWN.filter((k) => k !== "num").flatMap((key) => [{ key, name: `pc.${key}`, desc: `pcd.${key}`, width: CN_CH[key] ?? 8 },
    ...(key === "name" ? [{ key: "shape", name: "cn.col.shape", desc: "cn.col.shape_hint", width: CN_CH.shape }] : [])]),
  ...EXTRA.map((key) => ({ key, name: `pc.${key}`, desc: `pcd.${key}`, width: CN_CH[key] ?? 8, visible: false })),
] };
/** Excel dan Ctrl+V ustun tartibi: Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование. */
const PASTE_ORDER = ["length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right", "name"];
const TRUE = new Set(["1", "да", "ha", "yes", "true", "+", "x", "✓", "да.", "y"]);

function emptyDraft(grain = false): Part {
  return {
    id: NEW_ID, uid: 0, product_id: null, name: "", description: "", code: "",
    length: null as unknown as number, width: null as unknown as number, qty: 1, minus_qty: 0, grain,
    edge_top: { op_id: null }, edge_bottom: { op_id: null }, edge_left: { op_id: null }, edge_right: { op_id: null },
    groove_top: { op_id: null, back_side: false }, groove_bottom: { op_id: null, back_side: false },
    groove_left: { op_id: null, back_side: false }, groove_right: { op_id: null, back_side: false },
    allow_top: 0, allow_bottom: 0, allow_left: 0, allow_right: 0, group_by: "none", group_min: 0, group_max: 0,
    xnc_op_ids: [], surface_face_op: null, surface_back_op: null, used_qty: 0, left_qty: 0,
  };
}

function Tip(p: { value?: string }) {
  return p.value ? <div className="grid-tip">{p.value}</div> : null;
}

/** Tanlangan detalning kichik kontur chizmasi: tashqi kontur + ichki kesimlar (evenodd), etiketka o'rni (punktir), o'lchamlar va ogohlantirishlar. */
export function ShapeSketch({ shape, part, w = 260, h = 190 }: { shape?: CnShapeRow; part?: Part; w?: number; h?: number }) {
  const { t } = useTranslation();
  if (!shape) {
    return <div className="cn-sketch-empty muted">{part ? t("cn.shape.none") : t("cn.shape.pick")}</div>;
  }
  const [x0, y0, x1, y1] = bboxOf(shape.outline.length >= 3 ? shape.outline : [[0, 0], [shape.width, 0], [shape.width, shape.height], [0, shape.height]]);
  const bw = Math.max(1, x1 - x0), bh = Math.max(1, y1 - y0);
  const pad = Math.max(bw, bh) * 0.06;
  const rings = shape.outline.length >= 3 ? [shape.outline, ...shape.hole_rings] : [[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]];
  const lab = shape.label;
  const sw = Math.max(bw, bh) / 160;
  return (
    <svg className="cn-sketch" viewBox={`${x0 - pad} ${y0 - pad} ${bw + 2 * pad} ${bh + 2 * pad}`} width={w} height={h} preserveAspectRatio="xMidYMid meet"
      data-testid="cn-sketch">
      <path d={ringPath(rings)} fillRule="evenodd" fill="#f2a541" stroke="#5a3a0a" strokeWidth={sw} strokeLinejoin="round" />
      {lab && lab.length >= 4 && (
        <rect x={lab[0] - lab[2] / 2} y={lab[1] - lab[3] / 2} width={lab[2]} height={lab[3]} fill="rgba(255,255,255,.55)" stroke={shape.label_fits ? "#5a3a0a" : "#c0392b"}
          strokeWidth={sw} strokeDasharray={`${sw * 4} ${sw * 3}`} transform={lab[4] ? `rotate(${lab[4]} ${lab[0]} ${lab[1]})` : undefined}
          data-testid="cn-sketch-label" />
      )}
    </svg>
  );
}

export function ShapeInfo({ shape }: { shape?: CnShapeRow }) {
  const { t } = useTranslation();
  if (!shape) return null;
  return (
    <div className="cn-shape-info" data-testid="cn-shape-info">
      <div><b>{shape.kind === "rect" ? t("cn.shape.rect") : t("cn.shape.contour")}</b>{shape.holes > 0 && ` · ${t("cn.shape.holes", { n: shape.holes })}`}</div>
      <div>{t("cn.shape.bbox")}: {fmt(shape.width)} × {fmt(shape.height)} {t("u.mm")}</div>
      <div>{t("parts.area")}: {fmt(shape.area_mm2 / 1e6, 4)} {t("u.m2")} · {t("cn.shape.perimeter")}: {fmt(shape.perimeter_mm, 1)} {t("u.mm")}</div>
      {shape.label && <div className={shape.label_fits ? "" : "warn"}>{shape.label_fits ? t("cn.shape.label_ok") : t("cn.shape.label_no")}</div>}
      {shape.warnings.map((w, i) => <div key={i} className="warn cn-shape-warn" data-testid="cn-shape-warning">⚠ {w}</div>)}
    </div>
  );
}

export function CnParts({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const pid = project.id;
  const cn = op.cn!;
  const grid = useRef<AgGridReact<Part>>(null);
  const [dlg, setDlg] = useState<"" | "props" | "group" | "move" | "mode" | "sort">("");
  const [filter, setFilter] = useState(false);
  const [focusId, setFocusId] = useState<string | null>(null);
  const draftRef = useRef<Part>(emptyDraft(cn.use_grain));
  const [draftVer, setDraftVer] = useState(0);
  const creating = useRef(false);
  const shapes = useCnShapes(project, op).data;
  const byId = useMemo(() => new Map((shapes?.parts ?? []).map((s) => [s.id, s])), [shapes]);

  const cols = useMemo(() => {
    const base = buildColumns(t, project, op, CN_COLS);
    const shapeCol: PartCol = {
      colId: "shape", headerName: t("cn.col.shape"), headerTooltip: t("cn.col.shape_hint"), width: 160,
      valueGetter: (p) => {
        const s = p.data && p.data.id !== NEW_ID ? byId.get(p.data.id) : undefined;
        if (!s) return "";
        return `${s.warnings.length ? "⚠ " : ""}${s.kind === "rect" ? t("cn.shape.rect") : t("cn.shape.contour")}${s.holes > 0 ? ` · ${t("cn.shape.holes", { n: s.holes })}` : ""}`;
      },
      cellClass: (p) => (p.data && byId.get(p.data.id)?.warnings.length ? "warn" : ""),
      tooltipValueGetter: (p) => {
        const s = p.data ? byId.get(p.data.id) : undefined;
        return s ? [`${fmt(s.width)} × ${fmt(s.height)} ${t("u.mm")}`, `${t("parts.area")}: ${fmt(s.area_mm2 / 1e6, 4)} ${t("u.m2")}`,
          `${t("cn.shape.perimeter")}: ${fmt(s.perimeter_mm, 1)} ${t("u.mm")}`, ...s.warnings].join("\n") : "";
      },
    };
    const i = base.findIndex((c) => c.colId === "name");
    base.splice(i >= 0 ? i + 1 : base.length, 0, shapeCol);
    return base;
  }, [t, project, op, byId]);
  // foydalanuvchi ustunlari («Настроенный Параметры» — part.*, «Выражение»)
  const userSrc = useMemo(() => partsUserSource(t, project, op.parts), [t, project, op.parts]);
  const colset = useGridColumns(CN_COLUMNS, cols, userSrc);
  const tooltip = useMemo(() => partTooltip(t, project, op), [t, project, op]);
  const defaultColDef = useMemo<ColDef<Part>>(() => ({
    tooltipValueGetter: (p: ITooltipParams<Part>) => tooltip(p), tooltipComponent: Tip,
    suppressKeyboardEvent: (p: SuppressKeyboardEventParams<Part>) => {
      // Excel kabi: Enter/Tab — keyingi katak; Shift — oldingi; Ctrl+Tab/Enter — pastga (jadval oxirida — yangi qator)
      const ev = p.event;
      if (ev.type === "keydown" && (ev.key === "Enter" || ev.key === "Tab")) {
        if ((ev.ctrlKey || ev.metaKey) && !ev.altKey) {
          p.api.stopEditing();
          const fc = p.api.getFocusedCell();
          const ids = p.api.getAllDisplayedColumns().map((c) => c.getColId());
          const first = ids.find((id) => id !== "num") ?? ids[0];
          if (fc && first) {
            if (fc.rowPinned == null && fc.rowIndex + 1 < p.api.getDisplayedRowCount()) p.api.setFocusedCell(fc.rowIndex + 1, first);
            else p.api.setFocusedCell(0, first, "bottom");
          }
          ev.preventDefault();
          return true;
        }
        if (p.editing || (ev.shiftKey && ev.key === "Enter")) {
          p.api.stopEditing();
          if (ev.shiftKey) p.api.tabToPreviousCell();
          else p.api.tabToNextCell();
          ev.preventDefault();
          return true;
        }
      }
      return suppressGridKey(p);
    },
  }), [tooltip]);

  const rows = useMemo(() => (filter ? op.parts.filter((p) => (op.result ? p.left_qty > 0 : totalQty(project, p) > 0)) : op.parts),
    [filter, op, project]);
  const selected = useMemo(() => op.parts.filter((p) => ui.partSel.includes(p.id)), [op.parts, ui.partSel]);
  const focusPart = (): Part | undefined => {
    const fc = grid.current?.api.getFocusedCell();
    if (fc && fc.rowPinned == null) {
      const n = grid.current?.api.getDisplayedRowAtIndex(fc.rowIndex);
      if (n?.data) return n.data;
    }
    return selected[0];
  };
  const selIds = () => (selected.length ? selected.map((p) => p.id) : (focusPart() ? [focusPart()!.id] : []));
  const shownPart = op.parts.find((p) => p.id === (focusId ?? selected[0]?.id)) ?? selected[0];

  // jami maydon (m²: kontur maydoni × soni) va detallar soni
  const summary = useMemo(() => {
    let area = 0, n = 0;
    for (const p of op.parts) {
      const q = totalQty(project, p);
      const s = byId.get(p.id);
      area += ((s ? s.area_mm2 : Math.max(0, p.length) * Math.max(0, p.width)) * q) / 1e6;
      n += q;
    }
    return { area: Math.round(area * 1000) / 1000, n };
  }, [op.parts, project, byId]);

  const focusRowCol = useCallback((rowIndex: number, colId: string, edit = true) => {
    setTimeout(() => {
      const api = grid.current?.api;
      if (!api) return;
      api.ensureIndexVisible(rowIndex);
      api.setFocusedCell(rowIndex, colId);
      if (edit) api.startEditingCell({ rowIndex, colKey: colId });
    }, 60);
  }, []);

  const createFromDraft = useCallback(async () => {
    if (creating.current) return;
    const d = draftRef.current;
    if (!(d.length > 0 && d.width > 0)) return;
    creating.current = true;
    const fc = grid.current?.api.getFocusedCell();
    const nextCol = fc?.rowPinned === "bottom" ? fc.column.getColId() : "qty";
    grid.current?.api.stopEditing(true);
    const { id: _id, uid: _uid, used_qty: _u, left_qty: _l, ...body } = d;
    body.product_id = useUI.getState().productId ?? project.products[0]?.id ?? null;
    body.qty = body.qty || 1;
    draftRef.current = emptyDraft(cn.use_grain);
    setDraftVer((v) => v + 1);
    const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`, [body]));
    creating.current = false;
    if (p) {
      const o = p.operations.find((x) => x.id === op.id);
      const idx = (o?.parts.length ?? 1) - 1;
      focusRowCol(idx, ["num", "name", "length", "width"].includes(nextCol) ? "qty" : nextCol, false);
    }
  }, [pid, op.id, project.products, focusRowCol, cn.use_grain]);

  const onChange = (e: CellValueChangedEvent<Part>) => {
    if (!e.data) return;
    if (e.node.rowPinned === "bottom") {
      draftRef.current = e.data;
      if (e.data.length > 0 && e.data.width > 0) setTimeout(() => void createFromDraft(), 0);
      return;
    }
    const patchFn = (e.colDef as PartCol).context?.patch;
    if (!patchFn) return;
    if ((e.oldValue ?? "") === (e.newValue ?? "")) return;
    const fields = patchFn(e.newValue, e.data);
    void call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, [{ id: e.data!.id, fields }]));
  };

  const act = {
    props: () => focusPart() && setDlg("props"),
    move: (d: "up" | "down") => { const ids = selIds(); if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/move?direction=${d}`, { ids })); },
    insert: async () => {
      const cur = focusPart();
      const pos = cur ? op.parts.findIndex((p) => p.id === cur.id) : op.parts.length;
      const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`,
        [{ name: "", length: 0, width: 0, qty: 1, grain: cn.use_grain, product_id: ui.productId ?? project.products[0]?.id ?? null }], { position: pos }));
      if (p) focusRowCol(pos, "name");
    },
    clone: () => { const ids = selIds(); if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/clone`, { ids })); },
    remove: async () => {
      const ids = selIds();
      if (!ids.length) return;
      const r = await call(() => post(`/projects/${pid}/operations/${op.id}/parts/delete`, { ids }));
      if (r) { ui.set({ partSel: [] }); ui.toast(t("parts.deleted", { n: ids.length }), "info"); }
    },
    bulk: (a: "swap" | "grain-on" | "grain-off", all = false) => {
      const ids = all ? op.parts.map((p) => p.id) : selIds();
      if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/bulk/${a}`, { ids }));
    },
    sort: (by: string, desc = false) => void call(() => post(`/projects/${pid}/operations/${op.id}/parts/sort?by=${by}&desc=${desc}`)),
    xnc: async () => {                    // kontur detal: bog'langan XNC dasturini ochish (yo'q bo'lsa — yaratish)
      const part = focusPart();
      if (!part) return;
      if (part.xnc_op_ids.length) { ui.set({ opId: part.xnc_op_ids[0], xncTab: "program" }); return; }
      const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts/${part.id}/xnc`));
      if (p) ui.set({ opId: p.operations[p.operations.length - 1].id, xncTab: "program" });
    },
  };

  // Excel dan Ctrl+V: fokusdagi katakdan boshlab yangilash, ortiqcha qatorlar — yangi detallar
  const onPaste = (e: ClipboardEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
    const text = e.clipboardData.getData("text/plain");
    if (!text.trim()) return;
    e.preventDefault();
    void pasteText(text);
  };
  // o'ng tugma menyusidagi «Вставить»: buferdan o'qib, Ctrl+V kabi qo'yish (brauzer ruxsat bermasa — Ctrl+V maslahati)
  const pasteFromClipboard = async () => {
    let text = "";
    try { text = await navigator.clipboard.readText(); } catch { /* ruxsat yo'q */ }
    if (text.trim()) void pasteText(text);
    else ui.toast(t("ctx.paste_hint"), "info");
  };
  const pasteText = async (text: string) => {
    const api = grid.current?.api;
    if (!api) return;
    const lines = text.replace(/\r/g, "").split("\n").filter((l) => l.trim() !== "").map((l) => l.split("\t"));
    const visCols = api.getAllDisplayedColumns().map((c) => c.getColDef() as PartCol);
    const fc = api.getFocusedCell();
    const startColIdx = fc ? Math.max(0, visCols.findIndex((c) => c.colId === fc.column.getColId())) : 1;
    const startRow = fc && fc.rowPinned == null ? fc.rowIndex : rows.length;
    const specStart = visCols[startColIdx]?.colId === "length";
    const colAt = (j: number): PartCol | undefined =>
      (specStart && j < PASTE_ORDER.length ? visCols.find((c) => c.colId === PASTE_ORDER[j]) : undefined) ?? visCols[startColIdx + j];
    let els = project.operations.filter((o) => o.type === "EL");
    const findEl = (v: string) => {
      const s = v.trim().toLowerCase();
      if (!s) return null;
      return els.find((o) => [o.name, o.code, o.el?.symbol].some((x) => (x ?? "").trim().toLowerCase() === s))?.id ?? null;
    };
    const unknown = new Set<string>();
    lines.forEach((cells) => cells.forEach((raw, j) => {
      const col = colAt(j);
      if (col && String(col.colId).startsWith("edge_") && raw.trim() && !findEl(raw)) unknown.add(raw.trim());
    }));
    for (const name of unknown) {
      const p = await call(() => post<Project>(`/projects/${pid}/operations`, { type: "EL", name }));
      if (p) els = p.operations.filter((o) => o.type === "EL");
    }
    if (unknown.size) ui.toast(t("parts.edges_created", { n: unknown.size, names: [...unknown].join(", ") }), "info");
    const conv = (col: PartCol, raw: string): [string, unknown] | null => {
      const key = col.colId as string;
      const v = raw.trim();
      if (["length", "width"].includes(key)) { const n = parseCellNum(v); return n === null ? null : [key, n]; }
      if (key === "qty") { const n = parseCellNum(v); return n === null ? null : [key, Math.max(0, Math.round(n))]; }
      if (key === "grain") return ["grain", TRUE.has(v.toLowerCase())];
      if (key.startsWith("edge_")) return [key, { op_id: findEl(v) }];
      if (["name", "code"].includes(key)) return [key, v];
      return null;
    };
    const updates: { id: string; fields: Record<string, unknown> }[] = [];
    const creates: Record<string, unknown>[] = [];
    let skipped = 0;
    lines.forEach((cells, i) => {
      const fields: Record<string, unknown> = {};
      cells.forEach((raw, j) => {
        const col = colAt(j);
        if (!col) return;
        const kv = conv(col, raw);
        if (kv) fields[kv[0]] = kv[1];
      });
      if (!Object.keys(fields).length) { skipped++; return; }
      const rowIdx = startRow + i;
      const node = rowIdx < rows.length ? api.getDisplayedRowAtIndex(rowIdx) : null;
      if (node?.data && node.data.id !== NEW_ID) updates.push({ id: node.data.id, fields });
      else if (Number(fields.length) > 0 && Number(fields.width) > 0) {
        creates.push({ qty: 1, name: "", grain: cn.use_grain, product_id: ui.productId ?? project.products[0]?.id ?? null, ...fields });
      } else skipped++;
    });
    if (updates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, updates));
    if (creates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts`, creates));
    if (updates.length || creates.length) ui.toast(t("parts.pasted", { u: updates.length, c: creates.length }), "ok");
    else ui.toast(t("parts.paste_nothing"), "info");
    if (skipped) ui.toast(t("parts.paste_skipped", { n: skipped }), "warn");
  };

  // Space: Ткт katagida — belgini almashtirish; ОВ/ОН/ОЛ/ОП katagida — navbatdagi kromka; Shift+Space: to'rt tomonga bir xil
  const cycleEdge = (cur: string | null): string | null => {
    const ids = project.operations.filter((o) => o.type === "EL").map((o) => o.id);
    if (!ids.length) return null;
    const i = cur ? ids.indexOf(cur) : -1;
    return i + 1 < ids.length ? ids[i + 1] : null;
  };
  const spaceKey = (perimeter: boolean) => {
    const api = grid.current?.api;
    const fc = api?.getFocusedCell();
    if (!api || !fc) return;
    const col = fc.column.getColId();
    const isDraft = fc.rowPinned != null;
    const row = isDraft ? draftRef.current : api.getDisplayedRowAtIndex(fc.rowIndex)?.data;
    if (!row) return;
    let fields: Partial<Part> | null = null;
    if (perimeter) {
      const base = col.startsWith("edge_") ? (row[col as keyof Part] as { op_id: string | null }).op_id : row.edge_top.op_id;
      const nxt = { op_id: cycleEdge(base) };
      fields = { edge_top: nxt, edge_bottom: nxt, edge_left: nxt, edge_right: nxt };
    } else if (col === "grain") {
      fields = { grain: !row.grain };
    } else if (["edge_top", "edge_bottom", "edge_left", "edge_right"].includes(col)) {
      fields = { [col]: { op_id: cycleEdge((row[col as keyof Part] as { op_id: string | null }).op_id) } };
    }
    if (!fields) return;
    if (isDraft) {
      draftRef.current = { ...draftRef.current, ...fields };
      setDraftVer((v) => v + 1);
      return;
    }
    void call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, [{ id: row.id, fields }]));
  };
  const gotoDraft = () => {
    const api = grid.current?.api;
    if (!api) return;
    api.ensureIndexVisible(Math.max(0, rows.length - 1));
    api.setFocusedCell(0, "length", "bottom");
  };

  useHotkeys("parts", {
    space: () => spaceKey(false), "shift+space": () => spaceKey(true),
    "ctrl+pagedown,alt+pagedown": gotoDraft,
    "ctrl+space": act.props, "ctrl+arrowup": () => act.move("up"), "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert": () => void act.insert(), "ctrl+k": act.clone, "delete,shift+delete": () => void act.remove(),
    "ctrl+b": () => selIds().length && setDlg("group"), "ctrl+d": () => act.bulk("grain-off"), "ctrl+e": () => act.bulk("grain-on"),
    "ctrl+w,alt+w": () => act.bulk("swap"), "ctrl+m": () => selIds().length && setDlg("move"), "ctrl+f": () => setFilter((f) => !f),
    "ctrl+p": () => colset.open(), "ctrl+a": () => grid.current?.api?.selectAll("filtered"),
  });

  useEffect(() => { grid.current?.api?.refreshCells({ force: true }); }, [project, byId]);

  const pinned = useMemo(() => [draftRef.current], [draftVer]); // eslint-disable-line react-hooks/exhaustive-deps
  const modeLabel = t(`sizemode.${project.size_mode}`);
  const shape = shownPart ? byId.get(shownPart.id) : undefined;

  return (
    <div className="panel" {...scopeProps("parts")} onPaste={(e) => void onPaste(e)}>
      <CnTabs right={<>
        <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={act.props} disabled={!op.parts.length} testid="cn-parts-props" />
        <IconBtn icon={Drill} title={t("cn.xnc_contour")} onClick={() => void act.xnc()} disabled={!op.parts.length} testid="cn-parts-xnc" />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move("up")} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move("down")} />
        <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="cn-parts-insert" />
        <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} color="#c0392b" />
        <IconBtn icon={ClipboardPaste} title={t("parts.paste_hint")} onClick={() => ui.toast(t("parts.paste_hint"), "info")} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Toolbar className="subbar">
        <button type="button" className="linkbtn" onClick={() => setDlg("mode")} data-testid="cn-size-mode">
          {t("parts.size_mode")}: <b>{modeLabel}</b></button>
        <Sep />
        <IconBtn icon={Square} label="TXT" title={t("parts.grain_off_all")} onClick={() => act.bulk("grain-off", true)} testid="cn-grain-off-all" />
        <IconBtn icon={SquareCheck} label="TXT" title={t("parts.grain_on_all")} onClick={() => act.bulk("grain-on", true)} testid="cn-grain-on-all" />
        <IconBtn icon={ArrowLeftRight} title={`${t("parts.swap")} (Ctrl+W)`} onClick={() => act.bulk("swap")} />
        <IconBtn icon={Group} title={`${t("parts.group")} (Ctrl+B)`} onClick={() => selIds().length && setDlg("group")} />
        <Dropdown icon={ArrowDownUp} title={t("app.sort")} items={[
          { label: t("parts.sort.uid"), onClick: () => act.sort("uid") },
          { label: t("parts.sort.name"), onClick: () => act.sort("name") },
          { label: t("parts.sort.length"), onClick: () => act.sort("length", true) },
          { label: t("parts.sort.width"), onClick: () => act.sort("width", true) },
          { label: t("parts.sort.area"), onClick: () => act.sort("area", true) },
          { label: t("parts.sort.product"), onClick: () => act.sort("product") },
          { label: t("sort.dialog"), onClick: () => setDlg("sort") },
        ]} />
        <IconBtn icon={Replace} title={`${t("parts.move_to")} (Ctrl+M)`} onClick={() => selIds().length && setDlg("move")} />
        <IconBtn icon={Funnel} title={`${t("parts.filter")} (Ctrl+F)`} active={filter} onClick={() => setFilter(!filter)} />
        <IconBtn icon={Columns3} title={`${t("parts.columns")} (Ctrl+P)`} onClick={colset.open} testid="cn-parts-columns" />
        <div className="grow" />
        <span className="stat"><ListOrdered size={13} /> {t("parts.area")}: <b data-testid="cn-parts-area">{summary.area}</b> {t("u.m2")}</span>
        <span className="stat">{t("parts.count")}: <b data-testid="cn-parts-count">{summary.n}</b> {t("app.pcs")}</span>
        {!!shapes && shapes.bad + shapes.small > 0 && (
          <span className="stat warn" title={t("cn.parts.skipped_hint", { mm: cn.min_part_size })} data-testid="cn-parts-skipped">
            {t("cn.parts.skipped", { n: shapes.bad + shapes.small })}</span>)}
      </Toolbar>
      <div className="cn-parts-body">
        <div className="cn-grid-col">
          <Grid<Part> ref={grid} className="grow parts-grid" rowData={rows} columnDefs={colset.columnDefs} testid="cn-parts-grid"
            getRowId={(p) => p.data.id} defaultColDef={defaultColDef} pinnedBottomRowData={pinned}
            rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }} autoSelectFirst
            onSelectionChanged={(e) => ui.set({ partSel: e.api.getSelectedRows().filter((r) => r.id !== NEW_ID).map((r) => r.id) })}
            onCellFocused={(e) => {
              const n = e.rowIndex != null && e.rowPinned == null ? e.api.getDisplayedRowAtIndex(e.rowIndex) : null;
              if (n?.data) setFocusId(n.data.id);
            }}
            onCellValueChanged={onChange}
            onCellDoubleClicked={(e) => { if (e.column.getColId() === "num" && e.data && e.data.id !== NEW_ID) setDlg("props"); }}
        menu={() => {
          const none = !selIds().length;
          return [
            { label: t("menu.add"), hint: "Ctrl+PgDn", onClick: gotoDraft, testid: "ctx-cn-add" },
            { label: t("ctx.insert_row"), hint: "Insert", onClick: () => void act.insert() },
            { label: t("app.clone"), hint: "Ctrl+K", onClick: act.clone, disabled: none },
            { label: t("app.delete"), hint: "Del", onClick: () => void act.remove(), disabled: none, testid: "ctx-cn-delete" },
            { sep: true, label: "" },
            { label: t("app.move_up"), hint: "Ctrl+↑", onClick: () => act.move("up"), disabled: none },
            { label: t("app.move_down"), hint: "Ctrl+↓", onClick: () => act.move("down"), disabled: none },
            { sep: true, label: "" },
            { label: t("ctx.paste"), hint: "Ctrl+V", onClick: () => void pasteFromClipboard() },
            { label: t("ctx.select_all"), hint: "Ctrl+A", onClick: () => grid.current?.api?.selectAll("filtered") },
            { sep: true, label: "" },
            { label: t("parts.swap"), hint: "Ctrl+W", onClick: () => act.bulk("swap"), disabled: none },
            { label: t("parts.group"), hint: "Ctrl+B", onClick: () => selIds().length && setDlg("group"), disabled: none },
            { label: t("parts.move_to"), hint: "Ctrl+M", onClick: () => selIds().length && setDlg("move"), disabled: none },
            { label: t("parts.filter"), hint: "Ctrl+F", onClick: () => setFilter((f) => !f) },
            { sep: true, label: "" },
            { label: t("app.properties"), hint: "Ctrl+Space", onClick: act.props, disabled: none },
            { label: t("cols.title"), hint: "Ctrl+P", onClick: colset.open, testid: "ctx-cn-settings" },
            { label: t("menu.help"), hint: "F1", onClick: () => ui.set({ section: "help" }) },
          ];
        }}
            getRowClass={(p) => (p.data?.id === NEW_ID ? "row-new" : p.data && byId.get(p.data.id)?.warnings.length ? "row-warn"
              : p.data && op.result && p.data.left_qty > 0 ? "row-left" : "")} />
        </div>
        <div className="cn-shape-pane" data-testid="cn-shape-pane">
          <div className="cn-shape-title">{shownPart ? `№${shownPart.uid} ${shownPart.name}` : t("cn.shape.title")}</div>
          <ShapeSketch shape={shape} part={shownPart} />
          <ShapeInfo shape={shape} />
        </div>
      </div>
      {colset.dialog}
      {dlg === "props" && focusPart() && <PartProperties project={project} op={op} part={focusPart()!} onClose={() => setDlg("")} />}
      {dlg === "group" && <GroupActions project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "move" && <MoveToOp project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "mode" && <SizeModeDialog project={project} onClose={() => setDlg("")} />}
      {dlg === "sort" && (
        <SortDialog testid="cn-parts-sort" onClose={() => setDlg("")}
          cols={["uid", "product", "name", "length", "width", "qty", "grain", "code", "area", "description"].map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/operations/${op.id}/parts/sort`, specs))} />
      )}
    </div>
  );
}
