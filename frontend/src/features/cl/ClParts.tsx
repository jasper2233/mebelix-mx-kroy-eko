// CL «Детали» (hujjat D-CL3): Д-на · Кол · ОВ · ОН · ОЛ · ОП · Наименование · ОК · ИК · Ост. Detal eni — polosa eni (jadvalda ustun yo'q).
// Excel dan Ctrl+V tartibi: Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование. CS «Детали» (CsParts) namunasida.
import { useCallback, useEffect, useMemo, useRef, useState, type ClipboardEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, ITooltipParams, SuppressKeyboardEventParams } from "ag-grid-community";
import {
  ArrowDownUp, ChevronDown, ChevronUp, CircleQuestionMark, ClipboardPaste, CopyPlus, Funnel, Group, ListOrdered, Plus, Replace,
  SquarePen, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { post } from "../../api/client";
import type { Operation, Part, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, suppressGridKey, useHotkeys } from "../../shared/hotkeys";
import { Dropdown, IconBtn, Sep, Toolbar } from "../../shared/ui";
import { SortDialog } from "../../shared/SortDialog";
import { ClTabs } from "./ClPanel";
import { buildColumns, NEW_ID, type ColKey, type ColSetting, type PartCol } from "../cs/columns";
import { computeSizes, edgeParams, mapsOfPart, totalQty } from "../cs/sizes";
import { GroupActions, MoveToOp, SizeModeDialog } from "../cs/PartDialogs";
import { ClPartProps } from "./ClPartProps";

// Ustunlar tartibi — onlayn tizimdagidek: № | детал номи | Д-на | Сони | ОВ | ОН | ОЛ | ОП | Код | ID | ОК; oxirida bizning «ИК», «Ост»
const SHOWN: ColKey[] = ["num", "name", "length", "qty", "edge_top", "edge_bottom", "edge_left", "edge_right", "code", "uid", "total", "used", "left"];
const CL_COLS: ColSetting[] = SHOWN.map((key) => ({ key, visible: true }));
/** Excel dan Ctrl+V ustun tartibi (CL-044). */
const PASTE_ORDER = ["length", "qty", "edge_top", "edge_bottom", "edge_left", "edge_right", "name"];

function emptyDraft(): Part {
  return {
    id: NEW_ID, uid: 0, product_id: null, name: "", description: "", code: "",
    length: null as unknown as number, width: 0, qty: 1, minus_qty: 0, grain: false,
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

const isUncomputed = (p?: Part) => !!p && p.id !== NEW_ID && !(p.length > 0) && p.src_length != null;

export function ClParts({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const pid = project.id;
  const cl = op.cl!;
  const grid = useRef<AgGridReact<Part>>(null);
  const [dlg, setDlg] = useState<"" | "move" | "mode" | "sort" | "props" | "group">("");
  const [filter, setFilter] = useState(false);
  const draftRef = useRef<Part>(emptyDraft());
  const [draftVer, setDraftVer] = useState(0);
  const creating = useRef(false);

  const cols = useMemo(() => buildColumns(t, project, op, CL_COLS).map((c): PartCol => {
    if (c.colId === "length") {
      return { ...c, headerName: t("cl.col.length"),
        cellClass: (p) => (isUncomputed(p.data) ? "num strong warn" : "num strong"),
        valueFormatter: (p) => (isUncomputed(p.data) ? `⚠ ${p.data!.src_length}` : String(p.value ?? "")) };
    }
    if (c.colId === "edge_left" || c.colId === "edge_right") return { ...c, headerTooltip: t(`cl.col.${c.colId}_hint`) };
    return c;
  }), [t, project, op]);
  const tooltip = useMemo(() => {
    const edges = edgeParams(project);
    return (p: ITooltipParams<Part>): string => {
      const d = p.data;
      if (!d || d.id === NEW_ID) return "";
      const prod = project.products.find((x) => x.id === d.product_id);
      const same = project.operations.flatMap((o) => o.parts).filter((x) => x.product_id === d.product_id);
      const saw = computeSizes({ ...d, width: cl.width }, project.size_mode, edges, 0).saw[0];
      return [
        `${t("tip.product")}: ${prod ? prod.name : "—"}`,
        `${t("tip.num_in_product")}: ${same.findIndex((x) => x.id === d.id) + 1}`,
        `${t("tip.num_in_cut")}: ${mapsOfPart(op, d.id).join(", ") || "—"}`,
        `id: ${d.uid}`,
        `${t("cl.tip.saw")}: ${saw} × ${cl.width}`,
        ...(isUncomputed(d) ? [t("cl.tip.uncomputed", { v: d.src_length })] : []),
      ].join("\n");
    };
  }, [t, project, op, cl.width]);
  const defaultColDef = useMemo<ColDef<Part>>(() => ({
    tooltipValueGetter: tooltip, tooltipComponent: Tip,
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

  // jami uzunlik (m) va soni
  const summary = useMemo(() => {
    const edges = edgeParams(project);
    let len = 0, n = 0, unc = 0;
    for (const p of op.parts) {
      const q = totalQty(project, p);
      const saw = computeSizes({ ...p, width: cl.width }, project.size_mode, edges, 0).saw[0];
      len += (Math.max(0, saw) * q) / 1000;
      n += q;
      if (isUncomputed(p)) unc += 1;
    }
    return { len: Math.round(len * 1000) / 1000, n, unc };
  }, [op.parts, project, cl.width]);

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
    if (!(d.length > 0)) return;
    creating.current = true;
    const fc = grid.current?.api.getFocusedCell();
    const nextCol = fc?.rowPinned === "bottom" ? fc.column.getColId() : "qty";
    grid.current?.api.stopEditing(true);
    const { id: _id, uid: _uid, used_qty: _u, left_qty: _l, ...body } = d;
    body.product_id = useUI.getState().productId ?? project.products[0]?.id ?? null;
    body.qty = body.qty || 1;
    body.width = 0;
    draftRef.current = emptyDraft();
    setDraftVer((v) => v + 1);
    const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`, [body]));
    creating.current = false;
    if (p) {
      const o = p.operations.find((x) => x.id === op.id);
      const idx = (o?.parts.length ?? 1) - 1;
      focusRowCol(idx, ["num", "name", "length"].includes(nextCol) ? "qty" : nextCol, false);
    }
  }, [pid, op.id, project.products, focusRowCol]);

  const onChange = (e: CellValueChangedEvent<Part>) => {
    if (!e.data) return;
    if (e.node.rowPinned === "bottom") {
      draftRef.current = e.data;
      if (e.data.length > 0) setTimeout(() => void createFromDraft(), 0);
      return;
    }
    const patchFn = (e.colDef as PartCol).context?.patch;
    if (!patchFn) return;
    if ((e.oldValue ?? "") === (e.newValue ?? "")) return;
    const fields = patchFn(e.newValue, e.data);
    void call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, [{ id: e.data!.id, fields }]));
  };

  const act = {
    move: (d: "up" | "down") => { const ids = selIds(); if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/move?direction=${d}`, { ids })); },
    insert: async () => {
      const cur = focusPart();
      const pos = cur ? op.parts.findIndex((p) => p.id === cur.id) : op.parts.length;
      const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`,
        [{ name: "", length: 0, width: 0, qty: 1, product_id: ui.productId ?? project.products[0]?.id ?? null }], { position: pos }));
      if (p) focusRowCol(pos, "length");
    },
    clone: () => { const ids = selIds(); if (ids.length) void call(() => post(`/projects/${pid}/operations/${op.id}/parts/clone`, { ids })); },
    remove: async () => {
      const ids = selIds();
      if (!ids.length) return;
      const r = await call(() => post(`/projects/${pid}/operations/${op.id}/parts/delete`, { ids }));
      if (r) { ui.set({ partSel: [] }); ui.toast(t("parts.deleted", { n: ids.length }), "info"); }
    },
    sort: (by: string, desc = false) => void call(() => post(`/projects/${pid}/operations/${op.id}/parts/sort?by=${by}&desc=${desc}`)),
    props: () => { if (focusPart()) setDlg("props"); },                  // Ctrl+Space (W18): detal «Свойства»
    group: () => { if (selIds().length) setDlg("group"); },              // Ctrl+B (W18): «Групповые действия»
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
    const specStart = visCols[startColIdx]?.colId === "length";
    const colAt = (j: number): PartCol | undefined =>
      (specStart && j < PASTE_ORDER.length ? visCols.find((c) => c.colId === PASTE_ORDER[j]) : undefined) ?? visCols[startColIdx + j];
    let els = project.operations.filter((o) => o.type === "EL");
    const findEl = (v: string) => {
      const s = v.trim().toLowerCase();
      if (!s) return null;
      return els.find((o) => [o.name, o.code, o.el?.symbol].some((x) => (x ?? "").trim().toLowerCase() === s))?.id ?? null;
    };
    const conv = (col: PartCol, raw: string): [string, unknown] | null => {
      const key = col.colId as string;
      const v = raw.trim();
      if (key === "length") { const n = parseCellNum(v); return n === null ? null : [key, n]; }
      if (key === "qty") { const n = parseCellNum(v); return n === null ? null : [key, Math.max(0, Math.round(n))]; }
      if (key.startsWith("edge_")) return [key, { op_id: findEl(v) }];
      if (key === "name") return [key, v];
      return null;
    };
    const parse = (cells: string[]) => {
      const fields: Record<string, unknown> = {};
      cells.forEach((raw, j) => {
        const col = colAt(j);
        if (!col) return;
        const kv = conv(col, raw);
        if (kv) fields[kv[0]] = kv[1];
      });
      return fields;
    };
    // qator qabul qilinadimi (kromkaga bog'liq emas): mavjud qatorni yangilash yoki uzunligi bor yangi detal
    const nodeAt = (i: number) => { const rowIdx = startRow + i; return rowIdx < rows.length ? api.getDisplayedRowAtIndex(rowIdx) : null; };
    const isUpdate = (i: number) => { const node = nodeAt(i); return !!node?.data && node.data.id !== NEW_ID; };
    const accepted = (fields: Record<string, unknown>, i: number) =>
      Object.keys(fields).length > 0 && (isUpdate(i) || Number(fields.length) > 0);
    const okRow = lines.map((cells, i) => accepted(parse(cells), i));
    // ro'yxatda yo'q kromka nomlari — yangi EL operatsiyalari, faqat haqiqatan qo'shiladigan/yangilanadigan qatorlardan (QA #16)
    const unknown = new Set<string>();
    lines.forEach((cells, i) => okRow[i] && cells.forEach((raw, j) => {
      const col = colAt(j);
      if (col && String(col.colId).startsWith("edge_") && raw.trim() && !findEl(raw)) unknown.add(raw.trim());
    }));
    for (const name of unknown) {
      const p = await call(() => post<Project>(`/projects/${pid}/operations`, { type: "EL", name }));
      if (p) els = p.operations.filter((o) => o.type === "EL");
    }
    if (unknown.size) ui.toast(t("parts.edges_created", { n: unknown.size, names: [...unknown].join(", ") }), "info");
    const updates: { id: string; fields: Record<string, unknown> }[] = [];
    const creates: Record<string, unknown>[] = [];
    let skipped = 0;
    lines.forEach((cells, i) => {
      if (!okRow[i]) { skipped++; return; }
      const fields = parse(cells);              // kromkalar endi yangi yaratilgan EL larga ham bog'lanadi
      const node = nodeAt(i);
      if (node?.data && node.data.id !== NEW_ID) updates.push({ id: node.data.id, fields });
      else creates.push({ qty: 1, name: "", width: 0, product_id: ui.productId ?? project.products[0]?.id ?? null, ...fields });
    });
    if (updates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, updates));
    if (creates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts`, creates));
    if (updates.length || creates.length) ui.toast(t("parts.pasted", { u: updates.length, c: creates.length }), "ok");
    else ui.toast(t("cl.paste_nothing"), "info");
    if (skipped) ui.toast(t("cl.paste_skipped", { n: skipped }), "error");
  };

  // Space: ОВ/ОН/ОЛ/ОП katagida — navbatdagi kromka (— → A → B → … → —); Shift+Space: to'rt tomonga bir xil
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
    "ctrl+arrowup": () => act.move("up"), "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert": () => void act.insert(), "ctrl+k": act.clone, "delete,shift+delete": () => void act.remove(),
    "ctrl+m": () => selIds().length && setDlg("move"), "ctrl+f": () => setFilter((f) => !f),
    "ctrl+space": act.props, "ctrl+b": act.group,
  });

  useEffect(() => { grid.current?.api?.refreshCells({ force: true }); }, [project]);

  const pinned = useMemo(() => [draftRef.current], [draftVer]); // eslint-disable-line react-hooks/exhaustive-deps
  const modeLabel = t(`sizemode.${project.size_mode}`);

  return (
    <div className="panel" {...scopeProps("parts")} onPaste={(e) => void onPaste(e)}>
      <ClTabs right={<>
        <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={act.props} disabled={!op.parts.length}
          testid="cl-parts-props" />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move("up")} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move("down")} />
        <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="cl-parts-insert" />
        <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} color="#c0392b" />
        <IconBtn icon={ClipboardPaste} title={t("cl.paste_hint")} onClick={() => ui.toast(t("cl.paste_hint"), "info")} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Toolbar className="subbar">
        <button type="button" className="linkbtn" onClick={() => setDlg("mode")} data-testid="cl-size-mode">
          {t("parts.size_mode")}: <b>{modeLabel}</b></button>
        <Sep />
        <Dropdown icon={ArrowDownUp} title={t("app.sort")} items={[
          { label: t("parts.sort.uid"), onClick: () => act.sort("uid") },
          { label: t("parts.sort.name"), onClick: () => act.sort("name") },
          { label: t("parts.sort.length"), onClick: () => act.sort("length", true) },
          { label: t("cl.sort_length_asc"), onClick: () => act.sort("length", false) },
          { label: t("parts.sort.product"), onClick: () => act.sort("product") },
          { label: t("sort.dialog"), onClick: () => setDlg("sort") },
        ]} />
        <IconBtn icon={Group} title={`${t("parts.group")} (Ctrl+B)`} onClick={act.group} testid="cl-parts-group" />
        <IconBtn icon={Replace} title={`${t("parts.move_to")} (Ctrl+M)`} onClick={() => selIds().length && setDlg("move")} />
        <IconBtn icon={Funnel} title={`${t("parts.filter")} (Ctrl+F)`} active={filter} onClick={() => setFilter(!filter)} />
        <div className="grow" />
        <span className="stat"><ListOrdered size={13} /> {t("cl.length_total")}: <b data-testid="cl-parts-len">{summary.len}</b> {t("u.m")}</span>
        <span className="stat">{t("parts.count")}: <b data-testid="cl-parts-count">{summary.n}</b> {t("app.pcs")}</span>
        {summary.unc > 0 && <span className="stat warn" title={t("cl.uncomputed_hint")} data-testid="cl-parts-uncomputed">
          {t("cl.uncomputed", { n: summary.unc })}</span>}
      </Toolbar>
      <Grid<Part> ref={grid} className="grow parts-grid" rowData={rows} columnDefs={cols} testid="cl-parts-grid"
        getRowId={(p) => p.data.id} defaultColDef={defaultColDef} pinnedBottomRowData={pinned}
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }} autoSelectFirst
        onSelectionChanged={(e) => ui.set({ partSel: e.api.getSelectedRows().filter((r) => r.id !== NEW_ID).map((r) => r.id) })}
        onCellValueChanged={onChange}
        onCellDoubleClicked={(e) => { if (e.column.getColId() === "num" && e.data && e.data.id !== NEW_ID) setDlg("props"); }}
        getRowClass={(p) => (p.data?.id === NEW_ID ? "row-new" : isUncomputed(p.data) ? "row-warn"
          : p.data && op.result && p.data.left_qty > 0 ? "row-left" : "")} />
      {dlg === "props" && focusPart() && <ClPartProps project={project} op={op} part={focusPart()!} onClose={() => setDlg("")} />}
      {dlg === "group" && <GroupActions project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "move" && <MoveToOp project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "mode" && <SizeModeDialog project={project} onClose={() => setDlg("")} />}
      {dlg === "sort" && (
        <SortDialog testid="cl-parts-sort" onClose={() => setDlg("")}
          cols={["uid", "product", "name", "length", "qty", "code", "description"].map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/operations/${op.id}/parts/sort`, specs))} />
      )}
    </div>
  );
}
