// (O) Комплектация и другие действия: «Параметры» (egasi, narxlar, izoh) va «Материалы» (jadval: Код, Наименование, Ед.И,
// Кол, Цена, Стоимость) — qo'shish / o'chirish / nusxalash / ko'chirish, Excel dan Ctrl+V, katalogdan tanlash.
// Butun jadval bitta so'rov (PUT .../o/materials) bilan almashtiriladi — har tahrir bitta undo qadami.
import { useEffect, useMemo, useRef, useState, type ClipboardEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, SuppressKeyboardEventParams } from "ag-grid-community";
import {
  ChevronDown, ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, ChevronUp, CircleQuestionMark, ClipboardPaste, Columns3,
  CopyPlus, Library, ListChecks, ListEnd, ListPlus, Save, Trash, X,
} from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { patch, post, put } from "../../api/client";
import type { CatalogItem, OMaterial, OParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import type { UserColContext, UserColsSource } from "../../shared/grid/userColumns";
import { scopeProps, suppressGridKey, useHotkeys } from "../../shared/hotkeys";
import { Area, Field, IconBtn, Num, Sel, Sep, Toolbar, money } from "../../shared/ui";
import { OCatalogPicker } from "./OCatalogPicker";


interface ODefaults { work_cost: number; unit: string }
type PasteReply = Project & { added?: number; skipped?: { row: number; reason: string }[]; warnings?: string[] };

const newId = () => Math.random().toString(36).slice(2, 14);
const r2 = (v: number) => Math.round(v * 100) / 100;
// «Материалы» ustunlari katalogi («Настройки», Ctrl+P): nom, tavsif (sarlavha maslahati), kenglik — belgilarda
const O_COLUMNS: GridKind = { scope: "o_columns", specs: [
  { key: "code", name: "o.col.code", width: 20 },
  { key: "name", name: "o.col.name", width: 35 },
  { key: "unit", name: "o.col.unit", desc: "o.col.unit_desc", width: 8 },
  { key: "qty", name: "o.col.qty", desc: "o.col.qty_desc", width: 8 },
  { key: "price", name: "o.col.price", width: 8 },
  { key: "sum", name: "o.col.sum", width: 10 },
  { key: "used", name: "o.col.used", desc: "o.col.used_desc", width: 8 },
  { key: "total", name: "o.col.total", desc: "o.col.total_hint", width: 10 },
] };
// ifoda o'zgaruvchilari (foydalanuvchi «Выражение» ustunlari): kalit va rus qisqa nomi
const O_VARS: [string, string, string | null][] = [["code", "o.col.code", "Код"], ["name", "o.col.name", "Наименование"],
  ["unit", "o.col.unit", null], ["qty", "o.col.qty", "Кол"], ["price", "o.col.price", "Цена"], ["sum", "o.col.sum", "Стоимость"],
  ["used", "o.col.used", "ИК"], ["total", "o.col.total", "Всего"]];
const emptyParams = (): OParams => ({ owner_product_id: null, materials: [], work_cost: 0, multiplier: 1, messages: [] });


/** (O) GibLab kabi bitta sahifa: yuqorida parametrlar (Владелец, narxlar, Описание), pastda «Материалы» jadvali. */
export function OPanel({ project, op }: { project: Project; op: Operation }) {
  return (
    <div className="panel">
      <OParamsTab project={project} op={op} />
      <OMaterialsTab project={project} op={op} />
    </div>
  );
}

/** «Сохранить текущие параметры для использования по умолчанию»: ish narxi + oxirgi qatorning birligi. */
function useSaveDefault(op: Operation) {
  const { t } = useTranslation();
  const defaults = useDefaults<ODefaults>("o_defaults");
  return async () => {
    const o = op.o ?? emptyParams();
    const unit = o.materials[o.materials.length - 1]?.unit || defaults.data?.unit || "шт";
    const r = await call(() => put("/settings/o_defaults/default", { work_cost: o.work_cost, unit }));
    if (r) { useUI.getState().toast(t("o.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults", "o_defaults"] }); }
  };
}

// ───────────────────────── Параметры ─────────────────────────
function OParamsTab({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const o = op.o ?? emptyParams();
  const cur = project.currency;
  const url = `/projects/${project.id}/operations/${op.id}`;
  const po = (f: Partial<OParams>) => void call(() => patch(url, { o: f }));
  const owner = project.products.find((p) => p.id === o.owner_product_id);
  const mult = owner ? owner.qty : 1;
  const base = r2(o.materials.reduce((s, m) => s + m.qty * m.price, 0));
  const ownerOpts = [{ value: "", label: t("o.p.owner_project") },
    ...project.products.map((p, i) => ({ value: p.id, label: t("o.p.owner_item", { n: i + 1, name: p.name, qty: p.qty }) }))];
  const times = owner ? ` = ${money(base)} × ${mult}` : "";
  return (
    <div className="o-head">
      <div className="form2" data-testid="o-params">
        <div className="form-col">
          <Field label={t("o.p.owner")} hint={t("o.p.owner_hint")}>
            <Sel<string> value={o.owner_product_id ?? ""} width={280} testid="o-owner" options={ownerOpts}
              onChange={(v) => po({ owner_product_id: v || null, messages: [] })} />
          </Field>
          <Field label={t("o.p.mat_cost")} unit={cur}>
            <span className="ro" data-testid="o-cost-material" title={times ? times.slice(3) : undefined}>{money(op.cost_material)}</span>
          </Field>
          <Field label={t("o.p.op_cost")} unit={cur}>
            <Num value={o.work_cost} min={0} onCommit={(v) => po({ work_cost: v ?? 0 })} testid="o-work-cost" />

          </Field>
          {/* tartib: Стоимость (jami, mahsulot soniga ko'paytirilgan), keyin «Стоимость x 1шт» — bitta mahsulot uchun */}
          <Field label={t("o.p.cost")} unit={cur} hint={owner ? t("o.p.mult_hint", { n: mult }) : undefined}>
            <span className="ro" data-testid="o-cost">{money(op.cost_material + op.cost_operation)}</span>
          </Field>
          <Field label={t("o.p.cost_one")} unit={cur} hint={t("o.p.cost_one_hint")}>
            <span className="ro" data-testid="o-cost-one">{money(r2(base + o.work_cost))}</span>
          </Field>
          {o.messages.map((m) => (
            <div key={m} className="warn row gap" data-testid="o-msg">
              <span>{t(`o.msg.${m}`, { defaultValue: m })}</span>
              <IconBtn icon={X} title={t("app.close")} onClick={() => po({ messages: [] })} />
            </div>
          ))}
        </div>
        <div className="form-col">
          <div className="form-h">{t("o.p.description")}</div>
          <Area value={op.description} rows={4} testid="o-description"
            onCommit={(v) => void call(() => patch(url, { description: v }))} />
        </div>
      </div>
    </div>
  );
}

// ───────────────────────── Материалы ─────────────────────────
function OMaterialsTab({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const grid = useRef<AgGridReact<OMaterial>>(null);
  const [dlg, setDlg] = useState(false);
  const defaults = useDefaults<ODefaults>("o_defaults");
  const saveDefault = useSaveDefault(op);
  const o = op.o ?? emptyParams();
  const rows = o.materials;
  const unit = defaults.data?.unit || "шт";
  const cur = project.currency;
  const url = `/projects/${project.id}/operations/${op.id}/o/materials`;

  // Saqlash navbati. Katak tahriri jadvalni darhol serverga yubormaydi: tez yozayotganda (Tab → keyingi katak) javob kelib
  // jadval yangilansa, yozilayotgan katak tahriri uzilib qoladi. Shuning uchun tahrirlar yig'iladi (`pend`) va hech bir katak
  // tahrirda bo'lmay qolganda (350 ms tinchlikdan keyin) bitta so'rov (= bitta undo qadami) bilan yuboriladi. `desired` —
  // oxirgi kutilgan jadval (server javobi kelguncha keyingi amallar shundan davom etadi); so'rovlar ketma-ket (`inflight`).
  const pend = useRef<{ url: string; rows: OMaterial[] } | null>(null);
  const desired = useRef<{ url: string; rows: OMaterial[] } | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inflight = useRef<Promise<unknown>>(Promise.resolve());
  const flushRef = useRef<() => void>(() => undefined);
  const send = (u: string, next: OMaterial[]) => {
    const run = inflight.current.then(() => call(() => put<Project>(u, next)));
    inflight.current = run;
    void run.then(() => { if (inflight.current === run && !pend.current) desired.current = null; });
    return run;
  };
  flushRef.current = () => {
    timer.current = null;
    const p = pend.current;
    if (!p) return;
    if ((grid.current?.api?.getEditingCells().length ?? 0) > 0) { timer.current = setTimeout(() => flushRef.current(), 300); return; }
    pend.current = null;
    void send(p.url, p.rows);
  };
  const stop = () => { if (timer.current) { clearTimeout(timer.current); timer.current = null; } };
  const current = (): OMaterial[] => (desired.current && desired.current.url === url ? desired.current.rows : rows);
  const queue = (next: OMaterial[]) => {                // katak tahriri: yig'iladi, tinchlikda yuboriladi
    desired.current = pend.current = { url, rows: next };
    stop();
    timer.current = setTimeout(() => flushRef.current(), 350);
  };
  const push = (next: OMaterial[]) => {                 // tuzilma amali: darhol (kutayotgan tahrirlar shu jadvalga kiradi)
    stop();
    pend.current = null;
    desired.current = { url, rows: next };
    return send(url, next);
  };
  // boshqa operatsiyaga o'tilganda / panel yopilganda kutayotgan tahrirlar yo'qolmasin
  useEffect(() => () => {
    stop();
    const p = pend.current;
    if (p) { pend.current = null; void send(p.url, p.rows); }
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  const owner = project.products.find((p) => p.id === o.owner_product_id);
  const mult = owner ? owner.qty : 1;
  const base = r2(rows.reduce((s, m) => s + m.qty * m.price, 0));

  const selectedIds = (): string[] => {
    const sel = grid.current?.api.getSelectedRows().map((r) => r.id) ?? [];
    if (sel.length) return sel;
    const fc = grid.current?.api.getFocusedCell();
    const n = fc && fc.rowPinned == null ? grid.current?.api.getDisplayedRowAtIndex(fc.rowIndex) : null;
    return n?.data ? [n.data.id] : [];
  };
  const focusIndex = (): number => {
    const ids = selectedIds();
    return ids.length ? current().findIndex((r) => r.id === ids[0]) : -1;
  };
  const focusCell = (idx: number, colId = "name") => setTimeout(() => {
    const api = grid.current?.api;
    if (!api) return;
    api.ensureIndexVisible(idx);
    api.setFocusedCell(idx, colId);
    api.startEditingCell({ rowIndex: idx, colKey: colId });
  }, 80);
  const reselect = (ids: string[]) => setTimeout(() => {
    grid.current?.api.forEachNode((n) => n.setSelected(!!n.data && ids.includes(n.data.id)));
  }, 80);
  const blank = (): OMaterial => ({ id: newId(), code: "", name: "", unit, qty: 1, price: 0 });

  const act = {
    add: async () => {                                  // Ctrl+PgDn — oxiriga
      const cur = current();
      const r = await push([...cur, blank()]);
      if (r) focusCell(cur.length);
    },
    insert: async () => {                               // Ctrl+PgUp / Insert — joriy qatordan oldin
      const cur = current();
      const i = focusIndex();
      const at = i < 0 ? cur.length : i;
      const r = await push([...cur.slice(0, at), blank(), ...cur.slice(at)]);
      if (r) focusCell(at);
    },
    remove: async () => {                               // Del
      const ids = selectedIds();
      if (!ids.length) return;
      await push(current().filter((r) => !ids.includes(r.id)));
    },
    clone: async () => {                                // Ctrl+K — tanlanganlarni shu joyning o'zidan keyin nusxalash
      const ids = selectedIds();
      if (!ids.length) return;
      const out: OMaterial[] = [];
      for (const r of current()) { out.push(r); if (ids.includes(r.id)) out.push({ ...r, id: newId() }); }
      await push(out);
    },
    move: async (d: -1 | 1) => {                        // Ctrl+↑ / Ctrl+↓ — tanlangan qatorlarni bir qadam
      const ids = selectedIds();
      if (!ids.length) return;
      const out = [...current()];
      const hit = (r: OMaterial) => ids.includes(r.id);
      if (d < 0) for (let i = 1; i < out.length; i++) { if (hit(out[i]) && !hit(out[i - 1])) [out[i - 1], out[i]] = [out[i], out[i - 1]]; }
      else for (let i = out.length - 2; i >= 0; i--) { if (hit(out[i]) && !hit(out[i + 1])) [out[i + 1], out[i]] = [out[i], out[i + 1]]; }
      if (await push(out)) reselect(ids);
    },
    fromCatalog: async (items: CatalogItem[]) => {
      setDlg(false);
      const add: OMaterial[] = items.map((it) => ({ id: newId(), code: it.code ?? "", name: it.name, unit: (it.unit || unit).slice(0, 20),
        qty: 1, price: Math.max(0, it.price || 0) }));
      await push([...current(), ...add].slice(0, 5000));
    },
  };

  // Excel / OpenOffice dan Ctrl+V: ustunlar Код, Наименование, Ед.И, Кол, Цена — oxiriga qo'shiladi (server tahlil qiladi)
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
    stop();                                             // kutayotgan tahrirlar avval saqlanadi, so'ng qo'yiladi
    const p = pend.current;
    pend.current = null;
    if (p) void send(p.url, p.rows);
    await inflight.current;
    const r = await call(() => post<PasteReply>(`${url}/paste`, { text, mode: "append" }));
    desired.current = null;
    if (!r) return;
    if (r.added) ui.toast(t("o.pasted", { n: r.added }), "ok");
    else ui.toast(t("o.paste_nothing"), "info");
    if (r.skipped?.length) ui.toast(t("o.paste_skipped", { n: r.skipped.length }), "warn",
      r.skipped.slice(0, 8).map((s) => `${s.row}: ${s.reason}`));
  };

  // «Первая / Предыдущая / Следующая / Последняя» qator (tanlov ham ko'chadi)
  const go = (to: "first" | "prev" | "next" | "last") => {
    const api = grid.current?.api;
    const n = api?.getDisplayedRowCount() ?? 0;
    if (!api || !n) return;
    const at = api.getFocusedCell()?.rowIndex ?? api.getSelectedNodes()[0]?.rowIndex ?? -1;
    const idx = to === "first" ? 0 : to === "last" ? n - 1 : Math.max(0, Math.min(n - 1, at + (to === "prev" ? -1 : 1)));
    const col = api.getFocusedCell()?.column ?? api.getAllDisplayedColumns()[0];
    api.ensureIndexVisible(idx);
    if (col) api.setFocusedCell(idx, col);
    api.getDisplayedRowAtIndex(idx)?.setSelected(true, true);
  };

  useHotkeys("o-mat", {
    "ctrl+pagedown,alt+pagedown": () => void act.add(),
    "ctrl+pageup,alt+pageup,insert": () => void act.insert(),
    delete: () => void act.remove(), "ctrl+k": () => void act.clone(),
    "ctrl+arrowup": () => void act.move(-1), "ctrl+arrowdown": () => void act.move(1),
    "ctrl+p": () => colset.open(), "ctrl+a": () => grid.current?.api?.selectAll(),
  });

  const cols = useMemo<ColDef<OMaterial>[]>(() => {
    const txt = (field: "code" | "name" | "unit", title: string, extra: Partial<ColDef<OMaterial>> = {}): ColDef<OMaterial> =>
      ({ headerName: title, field, editable: true, valueParser: (p) => String(p.newValue ?? ""), ...extra });
    const numc = (field: "qty" | "price", title: string): ColDef<OMaterial> =>
      ({ headerName: title, field, width: 100, editable: true, cellClass: "num", headerClass: "ag-right-aligned-header",
         valueParser: (p) => { const n = parseCellNum(p.newValue); return n === null || n < 0 ? p.oldValue : n; },
         valueFormatter: (p) => (p.value == null ? "" : String(p.value)) });
    return [
      { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 50, cellClass: "num rownum" },
      txt("code", t("o.col.code"), { width: 150 }),
      txt("name", t("o.col.name"), { flex: 1, minWidth: 220 }),
      txt("unit", t("o.col.unit"), { width: 90 }),
      numc("qty", t("o.col.qty")), numc("price", t("o.col.price")),
      { colId: "sum", headerName: t("o.col.sum"), width: 120, cellClass: "num", sortable: true, headerClass: "ag-right-aligned-header",
        valueGetter: (p) => (p.data ? r2(p.data.qty * p.data.price) : 0), valueFormatter: (p) => money(p.value) },
      // «ИК» — ega mahsulot soni (har qatorda bir xil; onlayn tizimda Кол 134 / ИК 1), «Всего» = Стоимость × ИК;
      // ega «Проект» bo'lsa ИК = 1
      { colId: "used", headerName: t("o.col.used"), headerTooltip: t("o.col.used_hint"), width: 70, cellClass: "num muted", sortable: true,
        headerClass: "ag-right-aligned-header", valueGetter: (p) => (p.data ? mult : 0) },
      { colId: "total", headerName: t("o.col.total"), headerTooltip: t("o.col.total_hint"), width: 120, cellClass: "num", sortable: true,
        headerClass: "ag-right-aligned-header", valueGetter: (p) => (p.data ? r2(p.data.qty * p.data.price * mult) : 0),
        valueFormatter: (p) => money(p.value) },
    ];
  }, [t, mult]);
  // foydalanuvchi ustunlari: «Настроенный Параметры» (material.*) va «Выражение» (Кол, Цена … o'zgaruvchilari)
  const userSrc = useMemo<UserColsSource<OMaterial>>(() => ({
    prefix: "material", rows, rowKey: (r) => r.id, params: (r) => r.user_params,
    setParams: (r, next) => { r.user_params = next; },
    vars: (r) => {
      const v: Record<string, unknown> = { code: r.code, name: r.name, unit: r.unit, qty: r.qty, price: r.price,
        sum: r2(r.qty * r.price), used: mult, total: r2(r.qty * r.price * mult) };
      for (const [k, , alias] of O_VARS) if (alias) v[alias] = v[k];
      return v;
    },
    varList: O_VARS.flatMap(([k, lbl, alias]) => [{ name: k, label: t(lbl) }, ...(alias ? [{ name: alias, label: t(lbl) }] : [])]),
  }), [rows, mult, t]);
  // profil bo'yicha: tartib, ko'rinish, nom, maslahat, kenglik, foydalanuvchi ustunlari
  const colset = useGridColumns(O_COLUMNS, cols, userSrc);

  // Excel kabi: Enter/Tab — qiymat saqlanadi va fokus keyingi katakka o'tadi (tez yozishda boshlang'ich belgi yo'qolmaydi)
  const defaultColDef = useMemo<ColDef<OMaterial>>(() => ({
    suppressKeyboardEvent: (p: SuppressKeyboardEventParams<OMaterial>) => {
      if (p.editing && p.event.type === "keydown" && (p.event.key === "Enter" || p.event.key === "Tab")) {
        p.api.stopEditing();
        if (p.event.shiftKey && p.event.key === "Tab") p.api.tabToPreviousCell();
        else if (!p.event.shiftKey) p.api.tabToNextCell();
        p.event.preventDefault();
        return true;
      }
      return suppressGridKey(p);
    },
  }), []);

  const onChange = (e: CellValueChangedEvent<OMaterial>) => {
    const key = e.colDef.field as keyof OMaterial | undefined;
    const user = e.colDef.context as UserColContext<OMaterial> | undefined;     // «Настроенный Параметры» ustuni
    if (!e.data || (!key && !user?.patch) || e.newValue === e.oldValue) return;
    const fields = user?.patch ? user.patch(e.newValue, e.data) : { [key as string]: e.newValue };
    queue(current().map((r) => (r.id === e.data!.id ? { ...r, ...fields } : r)));
  };

  return (
    <div className="o-mat" {...scopeProps("o-mat")} onPaste={(e) => void onPaste(e)} data-testid="o-materials">
      {/* onlayn tartib: Первая, Предыдущая, Следующая, Последняя | ↑ ↓ | Вставить, Каталог товаров, Вставить (Ctrl+V), Удалить |
          Настройки | Справка; bizning qo'shimchalar (Добавить строку, Клонировать, Сохранить как стандарт) — oxirida */}
      <Toolbar className="sect-bar"><b>{t("o.tab.materials")}</b><span className="grow" />
        <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => go("first")} disabled={!rows.length} />
        <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => go("prev")} disabled={!rows.length} />
        <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => go("next")} disabled={!rows.length} />
        <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => go("last")} disabled={!rows.length} />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => void act.move(-1)} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => void act.move(1)} />
        <Sep />
        <IconBtn icon={ListPlus} title={`${t("o.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="o-insert" />
        <IconBtn icon={Library} title={t("o.from_catalog")} onClick={() => setDlg(true)} testid="o-catalog" />
        <IconBtn icon={ClipboardPaste} title={`${t("ctx.paste")} (Ctrl+V)`} onClick={() => void pasteFromClipboard()} testid="o-paste" />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} color="#c0392b" testid="o-remove" />
        <Sep />
        <IconBtn icon={Columns3} title={`${t("cols.title")} (Ctrl+P)`} onClick={colset.open} testid="o-columns" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
        <Sep />
        <IconBtn icon={ListEnd} title={`${t("o.add")} (Ctrl+PgDn)`} onClick={() => void act.add()} testid="o-add" />
        <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={() => void act.clone()} />
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} testid="o-save-default" />
      </Toolbar>
      <Grid<OMaterial> ref={grid} className="grow" rowData={rows} columnDefs={colset.columnDefs} testid="o-grid" getRowId={(p) => p.data.id}
        onSortChanged={(e) => e.api.refreshCells({ columns: ["n"], force: true })}
        defaultColDef={defaultColDef}
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }} autoSelectFirst
        onCellValueChanged={onChange}
        menu={() => {
          const none = !selectedIds().length;
          // onlayn tartib: Добавить, Удалить | Вставить (Ctrl+V), Выделить все | Справка; bizning qo'shimchalar — oxirida
          return [
            { label: t("menu.add"), hint: "Ctrl+PgDn", icon: ListEnd, onClick: () => void act.add(), testid: "ctx-o-add" },
            { label: t("app.delete"), hint: "Del", icon: Trash, onClick: () => void act.remove(), disabled: none, testid: "ctx-o-delete" },
            { sep: true, label: "" },
            { label: t("ctx.paste"), hint: "Ctrl+V", icon: ClipboardPaste, onClick: () => void pasteFromClipboard() },
            { label: t("ctx.select_all"), hint: "Ctrl+A", icon: ListChecks, onClick: () => grid.current?.api?.selectAll() },
            { sep: true, label: "" },
            { label: t("menu.help"), hint: "F1", icon: CircleQuestionMark, onClick: () => ui.set({ section: "help" }) },
            { sep: true, label: "" },
            { label: t("o.insert"), hint: "Ctrl+PgUp", icon: ListPlus, onClick: () => void act.insert() },
            { label: t("app.clone"), hint: "Ctrl+K", icon: CopyPlus, onClick: () => void act.clone(), disabled: none },
            { label: t("app.move_up"), hint: "Ctrl+↑", icon: ChevronUp, onClick: () => void act.move(-1), disabled: none },
            { label: t("app.move_down"), hint: "Ctrl+↓", icon: ChevronDown, onClick: () => void act.move(1), disabled: none },
            { label: t("o.from_catalog"), icon: Library, onClick: () => setDlg(true) },
            { label: t("cols.title"), hint: "Ctrl+P", icon: Columns3, onClick: colset.open, testid: "ctx-o-settings" },
          ];
        }} />
      {!rows.length && <div className="hint">{t("o.empty")}</div>}
      <div className="hint" data-testid="o-total">
        {t("o.total", { n: rows.length })} · <b>{money(base)}</b> {cur}
        {owner && <span> · {t("o.total_mult", { n: mult })}: <b>{money(op.cost_material)}</b> {cur}</span>}
      </div>
      {colset.dialog}
      {dlg && <OCatalogPicker onClose={() => setDlg(false)} onPick={(items) => void act.fromCatalog(items)} />}
    </div>
  );
}
