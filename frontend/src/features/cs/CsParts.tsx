// CS «Детали» — asosiy ish joyi (UI_SPEC §5.2): Excel kabi tezkor kiritish, Ctrl+V, kromka, tekstura, yorliqlar.
import { useCallback, useEffect, useMemo, useRef, useState, type ClipboardEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, SuppressKeyboardEventParams } from "ag-grid-community";
import {
  ArrowDownUp, ArrowLeftRight, ChevronDown, ChevronUp, CircleQuestionMark, ClipboardPaste, Columns3, CopyPlus, Drill,
  FileSpreadsheet, Funnel, Group, ListOrdered, Plus, Replace, SquareCheck, SquarePen, Square, Trash,
} from "lucide-react";
import { call, useProfiles } from "../../api/hooks";
import { post } from "../../api/client";
import type { Operation, Part, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, suppressGridKey, useHotkeys } from "../../shared/hotkeys";
import { Dropdown, IconBtn, Sep, Toolbar } from "../../shared/ui";
import { CsTabs } from "./CsPanel";
import { buildColumns, NEW_ID, normalizeColumns, partTooltip, type ColSetting, type PartCol } from "./columns";
import { computeSizes, edgeParams, totalQty } from "./sizes";
import { GroupActions, MoveToOp, PartProperties, SizeModeDialog } from "./PartDialogs";
import { ColumnSettings } from "./ColumnSettings";
import { ExcelImportDialog } from "./ExcelImport";

function emptyDraft(): Part {
  return {
    id: NEW_ID, uid: 0, product_id: null, name: "", description: "", code: "",
    length: null as unknown as number, width: null as unknown as number, qty: 1, grain: false,
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

const TRUE = new Set(["1", "да", "ha", "yes", "true", "+", "x", "✓", "да.", "y"]);

export function CsParts({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const pid = project.id;
  const grid = useRef<AgGridReact<Part>>(null);
  const profiles = useProfiles<{ columns: ColSetting[] }>("part_columns");
  const [dlg, setDlg] = useState<"" | "props" | "group" | "cols" | "move" | "mode" | "excel">("");
  const [filter, setFilter] = useState(false);
  const draftRef = useRef<Part>(emptyDraft());
  const [draftVer, setDraftVer] = useState(0);
  const creating = useRef(false);

  const colSettings = useMemo(() => {
    const pr = profiles.data?.find((p) => p.id === ui.columnProfile);
    return normalizeColumns(pr?.data?.columns);
  }, [profiles.data, ui.columnProfile]);
  const cols = useMemo(() => buildColumns(t, project, op, colSettings), [t, project, op, colSettings]);
  const tooltip = useMemo(() => partTooltip(t, project, op), [t, project, op]);
  const defaultColDef = useMemo<ColDef<Part>>(() => ({
    tooltipValueGetter: tooltip, tooltipComponent: Tip,
    suppressKeyboardEvent: (p: SuppressKeyboardEventParams<Part>) => {
      if (p.editing && p.event.key === "Enter" && p.event.type === "keydown" && !p.event.shiftKey) {
        p.api.tabToNextCell();     // Enter → keyingi katak (oxirgisidan keyin — keyingi qator)
        return true;
      }
      return suppressGridKey(p);
    },
  }), [tooltip]);

  const rows = useMemo(() => (filter
    ? op.parts.filter((p) => (op.result ? p.left_qty > 0 : totalQty(project, p) > 0))
    : op.parts), [filter, op, project]);
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

  // umumiy maydon va soni
  const summary = useMemo(() => {
    const edges = edgeParams(project);
    let area = 0, n = 0;
    for (const p of op.parts) {
      const q = totalQty(project, p);
      const s = computeSizes(p, project.size_mode, edges).detail;
      area += (s[0] * s[1] * q) / 1e6;
      n += q;
    }
    return { area: Math.round(area * 1000) / 1000, n };
  }, [op.parts, project]);

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
    draftRef.current = emptyDraft();
    setDraftVer((v) => v + 1);
    const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`, [body]));
    creating.current = false;
    if (p) {
      const o = p.operations.find((x) => x.id === op.id);
      const idx = (o?.parts.length ?? 1) - 1;
      focusRowCol(idx, ["num", "name", "length", "width"].includes(nextCol) ? "qty" : nextCol);
    }
  }, [pid, op.id, project.products, focusRowCol]);

  const onChange = (e: CellValueChangedEvent<Part>) => {
    if (!e.data) return;
    if (e.node.rowPinned === "bottom") {
      draftRef.current = e.data;
      if (e.data.length > 0 && e.data.width > 0) setTimeout(() => void createFromDraft(), 0);
      return;
    }
    const patchFn = (e.colDef as PartCol).context?.patch;
    if (!patchFn) return;
    const fields = patchFn(e.newValue, e.data);
    void call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, [{ id: e.data!.id, fields }]));
  };

  // ── amallar ──
  const act = {
    props: () => focusPart() && setDlg("props"),
    move: (d: "up" | "down") => { const ids = selIds(); if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/move?direction=${d}`, { ids })); },
    insert: async () => {
      const cur = focusPart();
      const pos = cur ? op.parts.findIndex((p) => p.id === cur.id) : op.parts.length;
      const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`,
        [{ name: "", length: 0, width: 0, qty: 1, product_id: ui.productId ?? project.products[0]?.id ?? null }], { position: pos }));
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
    xnc: async () => {
      const part = focusPart();
      if (!part) return;
      if (part.xnc_op_ids.length) { ui.set({ opId: part.xnc_op_ids[0], xncTab: "program" }); return; }
      const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts/${part.id}/xnc`));
      if (p) ui.set({ opId: p.operations[p.operations.length - 1].id, xncTab: "program" });
    },
  };

  // Excel dan Ctrl+V: fokusdagi katakdan boshlab yangilash, ortiqcha qatorlar — yangi detallar
  const onPaste = async (e: ClipboardEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
    const text = e.clipboardData.getData("text/plain");
    if (!text.trim()) return;
    e.preventDefault();
    const api = grid.current?.api;
    if (!api) return;
    const lines = text.replace(/\r/g, "").split("\n").filter((l) => l.trim() !== "").map((l) => l.split("\t"));
    const visCols = api.getAllDisplayedColumns().map((c) => c.getColDef() as PartCol);
    const fc = api.getFocusedCell();
    const startColIdx = fc ? Math.max(0, visCols.findIndex((c) => c.colId === fc.column.getColId())) : 1;
    const startRow = fc && fc.rowPinned == null ? fc.rowIndex : rows.length;
    const els = project.operations.filter((o) => o.type === "EL");
    const findEl = (v: string) => {
      const s = v.trim().toLowerCase();
      if (!s) return null;
      return els.find((o) => [o.name, o.code, o.el?.symbol].some((x) => (x ?? "").trim().toLowerCase() === s))?.id ?? null;
    };
    const conv = (col: PartCol, raw: string): [string, unknown] | null => {
      const key = col.colId as string;
      const v = raw.trim();
      if (["length", "width", "allow_top", "allow_bottom", "allow_left", "allow_right"].includes(key)) {
        const n = parseCellNum(v); return n === null ? null : [key, n];
      }
      if (["qty", "group_min", "group_max"].includes(key)) { const n = parseCellNum(v); return n === null ? null : [key, Math.max(0, Math.round(n))]; }
      if (key === "grain") return ["grain", TRUE.has(v.toLowerCase())];
      if (key.startsWith("edge_")) return [key, { op_id: findEl(v) }];
      if (["name", "code", "description"].includes(key)) return [key, v];
      return null;
    };
    const updates: { id: string; fields: Record<string, unknown> }[] = [];
    const creates: Record<string, unknown>[] = [];
    lines.forEach((cells, i) => {
      const fields: Record<string, unknown> = {};
      cells.forEach((raw, j) => {
        const col = visCols[startColIdx + j];
        if (!col) return;
        const kv = conv(col, raw);
        if (kv) fields[kv[0]] = kv[1];
      });
      if (!Object.keys(fields).length) return;
      const rowIdx = startRow + i;
      const node = rowIdx < rows.length ? api.getDisplayedRowAtIndex(rowIdx) : null;
      if (node?.data && node.data.id !== NEW_ID) updates.push({ id: node.data.id, fields });
      else if (Number(fields.length) > 0 && Number(fields.width) > 0) {
        creates.push({ qty: 1, name: "", product_id: ui.productId ?? project.products[0]?.id ?? null, ...fields });
      }
    });
    if (updates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, updates));
    if (creates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts`, creates));
    if (updates.length || creates.length) ui.toast(t("parts.pasted", { u: updates.length, c: creates.length }), "ok");
    else ui.toast(t("parts.paste_nothing"), "info");
  };

  useHotkeys("parts", {
    "ctrl+space": act.props, "ctrl+arrowup": () => act.move("up"), "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert": () => void act.insert(), "ctrl+k": act.clone, delete: () => void act.remove(),
    "ctrl+b": () => selIds().length && setDlg("group"), "ctrl+d": () => act.bulk("grain-off"), "ctrl+e": () => act.bulk("grain-on"),
    "ctrl+w,alt+w": () => act.bulk("swap"), "ctrl+m": () => selIds().length && setDlg("move"), "ctrl+p": () => setDlg("cols"),
    "ctrl+f": () => setFilter((f) => !f),
  });

  useEffect(() => { grid.current?.api?.refreshCells({ force: true }); }, [project]);

  const modeLabel = t(`sizemode.${project.size_mode}`);
  const pinned = useMemo(() => [draftRef.current], [draftVer]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="panel" {...scopeProps("parts")} onPaste={(e) => void onPaste(e)}>
      <CsTabs right={<>
        <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={act.props} disabled={!op.parts.length} />
        <IconBtn icon={Drill} title={t("parts.xnc_editor")} onClick={() => void act.xnc()} disabled={!op.parts.length} />
        <Sep />
        <IconBtn icon={ChevronUp} title={`${t("app.up")} (Ctrl+↑)`} onClick={() => act.move("up")} />
        <IconBtn icon={ChevronDown} title={`${t("app.down")} (Ctrl+↓)`} onClick={() => act.move("down")} />
        <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="parts-insert" />
        <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} color="#c0392b" />
        <IconBtn icon={ClipboardPaste} title={t("parts.paste_hint")} onClick={() => ui.toast(t("parts.paste_hint"), "info")} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Toolbar className="subbar">
        <button type="button" className="linkbtn" onClick={() => setDlg("mode")} data-testid="size-mode">
          {t("parts.size_mode")}: <b>{modeLabel}</b></button>
        <Sep />
        <IconBtn icon={FileSpreadsheet} title={t("menu.import_excel")} onClick={() => setDlg("excel")} color="#1f7a3a" />
        <IconBtn icon={Square} label="TXT" title={t("parts.grain_off_all")} onClick={() => act.bulk("grain-off", true)} />
        <IconBtn icon={SquareCheck} label="TXT" title={t("parts.grain_on_all")} onClick={() => act.bulk("grain-on", true)} />
        <IconBtn icon={ArrowLeftRight} title={`${t("parts.swap")} (Ctrl+W)`} onClick={() => act.bulk("swap")} />
        <IconBtn icon={Group} title={`${t("parts.group")} (Ctrl+B)`} onClick={() => selIds().length && setDlg("group")} />
        <Dropdown icon={ArrowDownUp} title={t("app.sort")} items={[
          { label: t("parts.sort.uid"), onClick: () => act.sort("uid") },
          { label: t("parts.sort.name"), onClick: () => act.sort("name") },
          { label: t("parts.sort.length"), onClick: () => act.sort("length", true) },
          { label: t("parts.sort.width"), onClick: () => act.sort("width", true) },
          { label: t("parts.sort.area"), onClick: () => act.sort("area", true) },
          { label: t("parts.sort.product"), onClick: () => act.sort("product") },
        ]} />
        <IconBtn icon={Square} title={`${t("parts.grain_off")} (Ctrl+D)`} onClick={() => act.bulk("grain-off")} />
        <IconBtn icon={SquareCheck} title={`${t("parts.grain_on")} (Ctrl+E)`} onClick={() => act.bulk("grain-on")} />
        <IconBtn icon={Replace} title={`${t("parts.move_to")} (Ctrl+M)`} onClick={() => selIds().length && setDlg("move")} />
        <IconBtn icon={Columns3} title={`${t("parts.columns")} (Ctrl+P)`} onClick={() => setDlg("cols")} testid="parts-columns" />
        <IconBtn icon={Funnel} title={`${t("parts.filter")} (Ctrl+F)`} active={filter} onClick={() => setFilter(!filter)} />
        <div className="grow" />
        <span className="stat"><ListOrdered size={13} /> {t("parts.area")}: <b data-testid="parts-area">{summary.area}</b> {t("u.m2")}</span>
        <span className="stat">{t("parts.count")}: <b data-testid="parts-count">{summary.n}</b> {t("app.pcs")}</span>
      </Toolbar>
      <Grid<Part> ref={grid} className="grow parts-grid" rowData={rows} columnDefs={cols} testid="parts-grid"
        getRowId={(p) => p.data.id} defaultColDef={defaultColDef} pinnedBottomRowData={pinned}
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }}
        onSelectionChanged={(e) => ui.set({ partSel: e.api.getSelectedRows().filter((r) => r.id !== NEW_ID).map((r) => r.id) })}
        onCellValueChanged={onChange} getRowClass={(p) => (p.data?.id === NEW_ID ? "row-new" : p.data && op.result && p.data.left_qty > 0 ? "row-left" : "")} />
      {dlg === "props" && focusPart() && <PartProperties project={project} op={op} part={focusPart()!} onClose={() => setDlg("")} />}
      {dlg === "group" && <GroupActions project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "move" && <MoveToOp project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "mode" && <SizeModeDialog project={project} onClose={() => setDlg("")} />}
      {dlg === "cols" && <ColumnSettings current={colSettings} onClose={() => setDlg("")} />}
      {dlg === "excel" && <ExcelImportDialog project={project} op={op} onClose={() => setDlg("")} />}
    </div>
  );
}

