// CS «Детали» — asosiy ish joyi (UI_SPEC §5.2): Excel kabi tezkor kiritish, Ctrl+V, kromka, tekstura, yorliqlar.
import { useCallback, useEffect, useMemo, useRef, useState, type ClipboardEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, SuppressKeyboardEventParams } from "ag-grid-community";
import {
  ArrowDownUp, ArrowLeftRight, ChevronDown, ChevronUp, CircleQuestionMark, ClipboardPaste, Columns3, CopyPlus, Drill,
  FileSpreadsheet, Funnel, Group, ListOrdered, Plus, Replace, SquareCheck, SquarePen, Square, Trash,
} from "lucide-react";
import { call, useAppSettings, useProfiles } from "../../api/hooks";
import { post } from "../../api/client";
import type { Operation, Part, Project, SizeMode } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, suppressGridKey, useHotkeys } from "../../shared/hotkeys";
import { Dropdown, IconBtn, Sep, Toolbar } from "../../shared/ui";
import { CsTabs } from "./CsPanel";
import { buildColumns, NEW_ID, normalizeColumns, partsUserSource, partTooltip, type ColSetting, type PartCol } from "./columns";
import { useUserColumns } from "../../shared/grid/userColumns";
import { computeSizes, edgeParams, totalQty } from "./sizes";
import { GroupActions, MoveToOp, PartProperties, SizeModeDialog } from "./PartDialogs";
import { ColumnSettings } from "./ColumnSettings";
import { ExcelImportDialog } from "./ExcelImport";
import { SortDialog } from "../../shared/SortDialog";

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

const TRUE = new Set(["1", "да", "ha", "yes", "true", "+", "x", "✓", "да.", "y"]);
/** Excel dan Ctrl+V ustun tartibi (D6): «Д-на» katagidan boshlanganda. */
const PASTE_ORDER = ["length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right", "name"];

export function CsParts({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const pid = project.id;
  const grid = useRef<AgGridReact<Part>>(null);
  const profiles = useProfiles<{ columns: ColSetting[] }>("part_columns");
  const [dlg, setDlg] = useState<"" | "props" | "group" | "cols" | "move" | "mode" | "excel" | "sort">("");
  const [filter, setFilter] = useState(false);
  // yangi qatorda Ткт — «Учет текстуры» yoqilgan bo'lsa ✓ (material teksturali)
  const grainDefault = op.cs_cut?.use_grain ?? false;
  const draftRef = useRef<Part>(emptyDraft(grainDefault));
  const [draftVer, setDraftVer] = useState(0);
  const creating = useRef(false);

  const colSettings = useMemo(() => {
    const pr = profiles.data?.find((p) => p.id === ui.columnProfile);
    return normalizeColumns(pr?.data?.columns);
  }, [profiles.data, ui.columnProfile]);
  // foydalanuvchi ustunlari («Настроенный Параметры» — part.*, «Выражение»)
  const userSrc = useMemo(() => partsUserSource(t, project, op.parts), [t, project, op.parts]);
  const ucols = useUserColumns(colSettings, userSrc);
  const cols = useMemo(() => buildColumns(t, project, op, colSettings, ucols.build), [t, project, op, colSettings, ucols.build]);
  const tooltip = useMemo(() => partTooltip(t, project, op), [t, project, op]);
  const defaultColDef = useMemo<ColDef<Part>>(() => ({
    tooltipValueGetter: tooltip, tooltipComponent: Tip,
    suppressKeyboardEvent: (p: SuppressKeyboardEventParams<Part>) => {
      // Excel kabi: Enter/Tab — qiymat saqlanadi va fokus keyingi katakka o'tadi (oxirgisidan keyin — keyingi qator);
      // Shift+Tab/Shift+Enter — oldingi katakka (qator boshida — oldingi qator); Ctrl+Tab/Ctrl+Enter — pastga, keyingi
      // qatorning birinchi katagiga (jadval oxirida — yangi qator, CS-077);
      // keyingi katakda yozishni boshlash tahrirni o'sha belgi bilan boshlaydi (tez yozishda belgi yo'qolmaydi).
      const ev = p.event;
      if (ev.type === "keydown" && (ev.key === "Enter" || ev.key === "Tab")) {
        if ((ev.ctrlKey || ev.metaKey) && !ev.altKey) {
          p.api.stopEditing();
          const fc = p.api.getFocusedCell();
          const cols = p.api.getAllDisplayedColumns().map((c) => c.getColId());
          const first = cols.find((id) => id !== "num") ?? cols[0];
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
    const minPart = op.cs_material?.min_part_size ?? 0;
    const allowance = op.cs_cut?.machining_allowance ?? 0;
    let area = 0, n = 0;
    const small = new Set<string>();
    for (const p of op.parts) {
      const q = totalQty(project, p);
      const sz = computeSizes(p, project.size_mode, edges, allowance);
      const s = sz.saw;                              // «Площадь» — zagotovka + pripusk (pilniy) o'lchamidan, kromkali detal o'lchamidan emas (CS-081)
      area += (s[0] * s[1] * q) / 1e6;
      n += q;
      // «Минимальный размер детали»: arrada xavfsiz kesib bo'lmaydigan (guruhlanmagan) kichik detal
      if (minPart > 0 && sz.saw[0] > 0 && sz.saw[1] > 0 && Math.min(sz.saw[0], sz.saw[1]) < minPart - 1e-9 && p.group_by === "none") small.add(p.id);
    }
    return { area: Math.round(area * 1000) / 1000, n, small, minPart };
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
    draftRef.current = emptyDraft(grainDefault);
    setDraftVer((v) => v + 1);
    const p = await call(() => post<Project>(`/projects/${pid}/operations/${op.id}/parts`, [body]));
    creating.current = false;
    if (p) {
      const o = p.operations.find((x) => x.id === op.id);
      const idx = (o?.parts.length ?? 1) - 1;
      focusRowCol(idx, ["num", "name", "length", "width"].includes(nextCol) ? "qty" : nextCol, false);
    }
  }, [pid, op.id, project.products, focusRowCol, grainDefault]);

  const onChange = (e: CellValueChangedEvent<Part>) => {
    if (!e.data) return;
    if (e.node.rowPinned === "bottom") {
      draftRef.current = e.data;
      if (e.data.length > 0 && e.data.width > 0) setTimeout(() => void createFromDraft(), 0);
      return;
    }
    const patchFn = (e.colDef as PartCol).context?.patch;
    if (!patchFn) return;
    if ((e.oldValue ?? "") === (e.newValue ?? "")) return;        // «—» → «—» kabi o'zgarishsiz tahrir
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
    // «Д-на» katagidan boshlansa — spetsifikatsiya tartibi (D6): Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование
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
      if (["length", "width", "allow_top", "allow_bottom", "allow_left", "allow_right"].includes(key)) {
        const n = parseCellNum(v);
        if (n !== null && n <= 0 && (key === "length" || key === "width")) return null;   // 0 / manfiy o'lcham — yozilmaydi (qator «o'tkazildi» deb sanaladi)
        return n === null ? null : [key, n];
      }
      if (["qty", "group_min", "group_max"].includes(key)) { const n = parseCellNum(v); return n === null ? null : [key, Math.max(0, Math.round(n))]; }
      if (key === "grain") return ["grain", TRUE.has(v.toLowerCase())];
      if (key.startsWith("edge_")) return [key, { op_id: findEl(v) }];
      if (["name", "code", "description"].includes(key)) return [key, v];
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
    // qator qabul qilinadimi (kromkaga bog'liq emas): mavjud qatorni yangilash yoki uzunlik/en bor yangi detal
    const nodeAt = (i: number) => { const rowIdx = startRow + i; return rowIdx < rows.length ? api.getDisplayedRowAtIndex(rowIdx) : null; };
    const isUpdate = (i: number) => { const node = nodeAt(i); return !!node?.data && node.data.id !== NEW_ID; };
    const accepted = (fields: Record<string, unknown>, i: number) =>
      Object.keys(fields).length > 0 && (isUpdate(i) || (Number(fields.length) > 0 && Number(fields.width) > 0));
    const okRow = lines.map((cells, i) => accepted(parse(cells), i));
    // ro'yxatda yo'q kromka nomlari — yangi kromka (EL) operatsiyalari avtomatik yaratiladi, lekin faqat haqiqatan
    // qo'shiladigan/yangilanadigan qatorlardan (o'tkazib yuborilgan qator uchun EL yaratilmaydi — QA #16)
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
      if (!okRow[i]) { skipped++; return; }    // uzunlik/en yo'q yoki son emas — jim tashlab yuborilmaydi
      const fields = parse(cells);              // kromkalar endi yangi yaratilgan EL larga ham bog'lanadi
      const node = nodeAt(i);
      if (node?.data && node.data.id !== NEW_ID) updates.push({ id: node.data.id, fields });
      else creates.push({ qty: 1, name: "", product_id: ui.productId ?? project.products[0]?.id ?? null, ...fields });
    });
    if (updates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts/batch-update`, updates));
    if (creates.length) await call(() => post(`/projects/${pid}/operations/${op.id}/parts`, creates));
    if (updates.length || creates.length) ui.toast(t("parts.pasted", { u: updates.length, c: creates.length }), "ok");
    else ui.toast(t("parts.paste_nothing"), "info");
    if (skipped) ui.toast(t("parts.paste_skipped", { n: skipped }), "warn");
  };

  // Space: Ткт katagida — belgini almashtirish; ОВ/ОН/ОЛ/ОП katagida — navbatdagi kromka (— → A → B → … → —).
  // Shift+Space: to'rt tomonga bir xil (perimetr bo'yicha navbatdagi) kromka.
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
    "ctrl+w,alt+w": () => act.bulk("swap"), "ctrl+m": () => selIds().length && setDlg("move"), "ctrl+p": () => setDlg("cols"),
    "ctrl+f": () => setFilter((f) => !f),
    "ctrl+a": () => grid.current?.api?.selectAll("filtered"),
  });

  useEffect(() => { grid.current?.api?.refreshCells({ force: true }); }, [project]);

  // DM-007: detallar jadvali bo'sh ochilganda (har loyihada bir marta) o'lcham kiritish rejimi taklif qilinadi —
  // «Настройки → Режим ввода деталей» «Не предлагать» bo'lsa (standart) taklif yo'q; boshqa qiymat — oynada oldindan tanlangan rejim
  const app = useAppSettings();
  const [suggest, setSuggest] = useState<SizeMode | null>(null);
  useEffect(() => {
    const mode = app.data?.input_mode_suggest;
    if (!mode || mode === "none" || op.parts.length > 0) return;
    try {
      const asked: string[] = JSON.parse(localStorage.getItem("mxk_mode_asked") ?? "[]");
      if (asked.includes(project.id)) return;
      localStorage.setItem("mxk_mode_asked", JSON.stringify([...asked.slice(-200), project.id]));
    } catch { return; }
    setSuggest(mode);
    setDlg("mode");
  }, [app.data?.input_mode_suggest, op.parts.length, project.id]);

  const modeLabel = t(`sizemode.${project.size_mode}`);
  const pinned = useMemo(() => [draftRef.current], [draftVer]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="panel" {...scopeProps("parts")} onPaste={(e) => void onPaste(e)}>
      <CsTabs right={<>
        <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={act.props} disabled={!op.parts.length} />
        <IconBtn icon={Drill} title={t("parts.xnc_editor")} onClick={() => void act.xnc()} disabled={!op.parts.length} />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move("up")} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move("down")} />
        <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="parts-insert" />
        <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} color="#c0392b" />
        <IconBtn icon={ClipboardPaste} title={t("parts.paste_hint")} onClick={() => ui.toast(t("parts.paste_hint"), "info")} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      {/* 2-qator onlayn tizimdagi tartibda: havola | Групповые, Сортировка, ☐TXT, ☑TXT, Поменять, Перенести, Настройки |
          Площадь | Кол-во; bizning qo'shimchalar (Excel, filtr) — qator oxirida. TXT tugmalari tanlangan detallarga ta'sir qiladi. */}
      <Toolbar className="subbar parts-subbar">
        <span className="pb-left">
          <button type="button" className="linkbtn" onClick={() => setDlg("mode")} data-testid="size-mode">
            {t("parts.size_mode")}: <b>{modeLabel}</b></button>
        </span>
        <span className="pb-tools">
          <IconBtn icon={Group} title={`${t("parts.group")} [CTRL]+[B]`} onClick={() => selIds().length && setDlg("group")} testid="parts-group" />
          <Dropdown icon={ArrowDownUp} title={t("app.sort")} testid="parts-sort-menu" items={[
            { label: t("parts.sort.uid"), onClick: () => act.sort("uid") },
            { label: t("parts.sort.name"), onClick: () => act.sort("name") },
            { label: t("parts.sort.length"), onClick: () => act.sort("length", true) },
            { label: t("parts.sort.width"), onClick: () => act.sort("width", true) },
            { label: t("parts.sort.area"), onClick: () => act.sort("area", true) },
            { label: t("parts.sort.product"), onClick: () => act.sort("product") },
            { label: t("sort.dialog"), onClick: () => setDlg("sort") },
          ]} />
          <IconBtn icon={Square} label="TXT" title={`${t("parts.grain_off")} [CTRL]+[D]`} onClick={() => act.bulk("grain-off")} testid="grain-off" />
          <IconBtn icon={SquareCheck} label="TXT" title={`${t("parts.grain_on")} [CTRL]+[E]`} onClick={() => act.bulk("grain-on")} testid="grain-on" />
          <IconBtn icon={ArrowLeftRight} title={`${t("parts.swap")} [CTRL]+[W]`} onClick={() => act.bulk("swap")} testid="parts-swap" />
          <IconBtn icon={Replace} title={`${t("parts.move_to")} [CTRL]+[M]`} onClick={() => selIds().length && setDlg("move")} />
          <IconBtn icon={Columns3} title={`${t("menu.settings")} [CTRL]+[P]`} onClick={() => setDlg("cols")} testid="parts-columns" />
        </span>
        <span className="stat pb-area"><ListOrdered size={13} /> {t("parts.area")}: <b data-testid="parts-area">{summary.area}</b> {t("u.m2")}</span>
        <span className="stat pb-count">{t("parts.count")}: <b data-testid="parts-count">{summary.n}</b> {t("app.pcs")}</span>
        {summary.small.size > 0 && <span className="stat warn" title={t("parts.small_hint", { mm: summary.minPart })}
          data-testid="parts-small">{t("parts.small", { n: summary.small.size })}</span>}
        <span className="grow" />
        <IconBtn icon={FileSpreadsheet} title={t("menu.import_excel")} onClick={() => setDlg("excel")} color="#1f7a3a" />
        <IconBtn icon={Funnel} title={`${t("parts.filter")} [CTRL]+[F]`} active={filter} onClick={() => setFilter(!filter)} />
        {/* MX qo'shimchasi: teksturani BARCHA detallarga bir bosishda qo'yish / olib tashlash (TXT tugmalari — tanlanganlarga) */}
        <IconBtn icon={Square} label="TXT*" title={t("parts.grain_off_all")} onClick={() => act.bulk("grain-off", true)} testid="grain-off-all" />
        <IconBtn icon={SquareCheck} label="TXT*" title={t("parts.grain_on_all")} onClick={() => act.bulk("grain-on", true)} testid="grain-on-all" />
      </Toolbar>
      <Grid<Part> ref={grid} className="grow parts-grid" rowData={rows} columnDefs={cols} testid="parts-grid"
        getRowId={(p) => p.data.id} defaultColDef={defaultColDef} pinnedBottomRowData={pinned}
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }}
        onSelectionChanged={(e) => ui.set({ partSel: e.api.getSelectedRows().filter((r) => r.id !== NEW_ID).map((r) => r.id) })}
        onCellDoubleClicked={(e) => { if (e.column.getColId() === "num" && e.data && e.data.id !== NEW_ID) setDlg("props"); }}
        autoSelectFirst
        menu={() => {
          const none = !selIds().length;
          // onlayn tartib: Добавить, Клонировать, Удалить | Вставить, Выделить все | Свойства | Справка; bizning bandlar — oxirida
          return [
            { label: t("menu.add"), hint: "Ctrl+PgDn", onClick: gotoDraft, testid: "ctx-part-add" },
            { label: t("app.clone"), hint: "Ctrl+K", onClick: act.clone, disabled: none },
            { label: t("app.delete"), hint: "Del", onClick: () => void act.remove(), disabled: none, testid: "ctx-part-delete" },
            { sep: true, label: "" },
            { label: t("ctx.paste"), hint: "Ctrl+V", onClick: () => void pasteFromClipboard() },
            { label: t("ctx.select_all"), hint: "Ctrl+A", onClick: () => grid.current?.api?.selectAll("filtered") },
            { sep: true, label: "" },
            { label: t("app.properties"), hint: "Ctrl+Space", onClick: act.props, disabled: none },
            { sep: true, label: "" },
            { label: t("menu.help"), hint: "F1", onClick: () => ui.set({ section: "help" }) },
            { sep: true, label: "" },
            { label: t("ctx.insert_row"), hint: "Insert", onClick: () => void act.insert() },
            { label: t("menu.settings"), hint: "Ctrl+P", onClick: () => setDlg("cols"), testid: "ctx-part-settings" },
          ];
        }}
        onCellValueChanged={onChange} getRowClass={(p) => (p.data?.id === NEW_ID ? "row-new" : p.data && op.result && p.data.left_qty > 0 ? "row-left"
          : p.data && summary.small.has(p.data.id) ? "row-warn" : "")} />
      {dlg === "props" && focusPart() && <PartProperties project={project} op={op} part={focusPart()!} onClose={() => setDlg("")} />}
      {dlg === "group" && <GroupActions project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "move" && <MoveToOp project={project} op={op} ids={selIds()} onClose={() => setDlg("")} />}
      {dlg === "mode" && <SizeModeDialog project={project} initial={suggest ?? undefined} onClose={() => { setDlg(""); setSuggest(null); }} />}
      {dlg === "cols" && <ColumnSettings current={colSettings} onClose={() => setDlg("")} vars={ucols.varList} />}
      {dlg === "excel" && <ExcelImportDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "sort" && (
        <SortDialog testid="parts-sort" onClose={() => setDlg("")}
          cols={["uid", "product", "name", "length", "width", "qty", "grain", "code", "area", "description"]
            .map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/operations/${op.id}/parts/sort`, specs))} />
      )}
    </div>
  );
}

