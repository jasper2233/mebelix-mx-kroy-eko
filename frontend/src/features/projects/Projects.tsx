// Loyihalar ro'yxati (Проекты, UI_SPEC §1): papkalar + loyihalar, ochish (dbl-click / Ctrl+Space).
import { useEffect, useMemo, useRef, useState } from "react";
import { fmtDateWd } from "../../shared/dates";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import type { AgGridReact } from "ag-grid-react";
import type { ColDef, GridApi } from "ag-grid-community";
import {
  CircleQuestionMark, Copy, CornerLeftUp, Folder as FolderIcon, FolderInput, FolderOpen, FolderPlus, House, ListChecks, ListOrdered,
  Pencil, Plus, RefreshCw, ScanLine, Search, Trash, ArrowDownToLine, ArrowUpFromLine, FileText,
} from "lucide-react";
import { QueueDialog } from "./QueueDialog";
import { call, qc, useAllFolders, useAppSettings, useFolderPath, useFolders, useMe, useProjects } from "../../api/hooks";
import { api, del, download, downloadPost, patch, post } from "../../api/client";
import type { Folder, Project, ProjectRow } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, selectFirstIfNone } from "../../shared/grid/Grid";
import { askConfirm, askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sel, Toolbar, cx, money } from "../../shared/ui";
import { fmtDateTime } from "../order/orderApi";

interface Row { kind: "folder" | "project"; id: string; name: string; number?: number; owner?: string; status?: number;
  order_date?: string; cost?: number; customer?: string; updated_at?: string | null }

// row — fokusdagi (oxirgi tanlangan) qator; rows — barcha tanlanganlar (Ctrl/Shift/Ctrl+A); move — «Переместить» oynasi
const useSel = create<{ row: Row | null; rows: Row[]; move: boolean; set: (r: Row | null) => void;
  setRows: (rows: Row[]) => void; setMove: (b: boolean) => void }>((set) => ({
  row: null, rows: [], move: false,
  set: (r) => set({ row: r, rows: r ? [r] : [] }),
  setRows: (rows) => set({ rows, row: rows.length ? rows[rows.length - 1] : null }),
  setMove: (move) => set({ move }),
}));
// doimiy obyekt: har chizishda yangi obyekt berilsa, jadval «sozlama o'zgardi» deb tanlovni tiklab yuboradi (Ctrl+A buzilardi)
const ROW_SELECTION = { mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true } as const;
let gridApi: GridApi<Row> | null = null;      // «Выделить все» menyu bandi uchun

/** Tanlov do'konidagi qator nusxasi eskirgan bo'lishi mumkin (qayta nomlashdan keyin ro'yxat yangilanadi, tanlov hodisasi
 *  kelmaydi) — amal oldidan jadvaldagi joriy ma'lumot olinadi: «Переименовать»/F2 va «Удалить» oynalari hozirgi nomni ko'rsatadi. */
function liveRow(r: Row | null): Row | null {
  if (!r) return null;
  return (gridApi?.getRowNode(`${r.kind}:${r.id}`)?.data as Row | undefined) ?? r;
}

export const STATUS_KEYS = ["status.0", "status.1", "status.2", "status.3"];

function refresh() {
  void qc.invalidateQueries({ queryKey: ["projects"] });
  void qc.invalidateQueries({ queryKey: ["folders"] });
}

async function openRow(r: Row | null) {
  if (!r) return;
  if (r.kind === "folder") useUI.getState().set({ folderId: r.id });
  else useUI.getState().openProject(r.id);
}

async function addProject(t: (k: string) => string) {
  const name = await askText(t("projects.new_name"), t("projects.default_name"));
  if (!name) return;
  const p = await call(() => post<Project>("/projects", { name, folder_id: useUI.getState().folderId }));
  if (p) useUI.getState().openProject(p.id);
}

async function addFolder(t: (k: string) => string) {
  const name = await askText(t("projects.new_folder"), t("projects.default_folder"));
  if (!name) return;
  await call(() => post<Folder>("/folders", { name, parent_id: useUI.getState().folderId }));
  refresh();
}

async function renameRow(r0: Row | null, t: (k: string) => string) {
  const r = liveRow(r0);
  if (!r) return;
  const name = await askText(t("menu.rename"), r.name);
  if (!name || name === r.name) return;
  if (r.kind === "folder") await call(() => patch(`/folders/${r.id}`, { name }));
  else await call(() => patch(`/projects/${r.id}`, { name }));
  refresh();
}

async function copyRows(rows: Row[]) {
  const ps = rows.filter((r) => r.kind === "project");
  if (!ps.length) return;
  for (const r of ps) await call(() => post(`/projects/${r.id}/copy`));
  refresh();
}

/** Tanlangan loyihalarni `.project` ga eksport (W10): bittasi — fayl, bir nechtasi — ZIP (har loyiha alohida fayl). */
async function exportRows(rows: Row[], t: (k: string) => string) {
  const ps = rows.filter((r) => r.kind === "project");
  if (!ps.length) return;
  const ok = await call(async () => {
    if (ps.length === 1) await download(`/projects/${ps[0].id}/export/project`, {}, `${ps[0].number ?? ps[0].id}.project`);
    else await downloadPost("/projects/export/project-zip", { ids: ps.map((r) => r.id) }, "projects.zip");
    return true;
  });
  if (ok) useUI.getState().toast(t("export.done"), "ok");
}

async function deleteRows(rows0: Row[], t: (k: string, o?: Record<string, unknown>) => string) {
  const rows = rows0.map((r) => liveRow(r) ?? r);
  if (!rows.length) return;
  const folders = rows.filter((r) => r.kind === "folder");
  if (rows.length > 1) {
    if (!(await askConfirm(t("projects.delete_many_q", { n: rows.length }), folders.length ? t("projects.delete_folder_text") : undefined,
      { danger: true, ok: t("app.delete") }))) return;
  } else if (rows[0].kind === "folder") {
    if (!(await askConfirm(t("projects.delete_folder_q", { name: rows[0].name }), t("projects.delete_folder_text"),
      { danger: true, ok: t("app.delete") }))) return;
  } else if (!(await askConfirm(t("projects.delete_q", { name: rows[0].name }), undefined, { danger: true, ok: t("app.delete") }))) return;
  for (const r of rows) {
    if (r.kind === "folder") await call(() => del(`/folders/${r.id}`, { recursive: true }));
    else await call(() => del(`/projects/${r.id}`));
  }
  useSel.getState().set(null);
  refresh();
}

export async function importProjectFile(file: File, t: (k: string, o?: Record<string, unknown>) => string) {
  const fd = new FormData();
  fd.append("file", file);
  const folder = useUI.getState().folderId;
  if (folder) fd.append("folder_id", folder);
  const r = await call(() => api<{ project: Project; warnings: string[] }>("/projects/import-file", { form: fd }),
    t("projects.importing"));
  if (!r) return;
  refresh();
  if (r.warnings.length) useUI.getState().toast(t("projects.import_warnings", { n: r.warnings.length }), "info", r.warnings);
  else useUI.getState().toast(t("projects.imported", { name: r.project.name }), "ok");
  useUI.getState().openProject(r.project.id);
}

function pickFile(accept: string, cb: (f: File) => void) {
  const inp = document.createElement("input");
  inp.type = "file";
  inp.accept = accept;
  inp.onchange = () => { if (inp.files?.[0]) cb(inp.files[0]); };
  inp.click();
}

export function FolderPicker(props: { title: string; exclude?: string; onPick: (id: string | null) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const [cur, setCur] = useState<string | null>(null);
  const all = useAllFolders().data ?? [];
  const kids = (pid: string | null) => all.filter((f) => f.parent_id === pid && f.id !== props.exclude);
  const Node = ({ f, depth }: { f: Folder; depth: number }) => (
    <>
      <div className={cx("tree-item", cur === f.id && "tree-item-active")} style={{ paddingLeft: 8 + depth * 16 }}
        onClick={() => setCur(f.id)} onDoubleClick={() => props.onPick(f.id)}>
        <FolderIcon size={14} /> {f.name}
      </div>
      {kids(f.id).map((k) => <Node key={k.id} f={k} depth={depth + 1} />)}
    </>
  );
  return (
    <Modal title={props.title} onClose={props.onClose} width={420} height={460}
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => props.onPick(cur)} />
        <Btn label={t("app.cancel")} onClick={props.onClose} /></>}>
      <div className="tree">
        <div className={cx("tree-item", cur === null && "tree-item-active")} onClick={() => setCur(null)}
          onDoubleClick={() => props.onPick(null)}>
          <House size={14} /> {t("projects.root")}
        </div>
        {kids(null).map((f) => <Node key={f.id} f={f} depth={1} />)}
      </div>
    </Modal>
  );
}

/** Chap menyu: Проекты */
export function ProjectsMenu() {
  const { t } = useTranslation();
  const sel = useSel((s) => s.row);
  const rows = useSel((s) => s.rows);
  const move = useSel((s) => s.move);
  const setMove = useSel((s) => s.setMove);
  const setUI = useUI((s) => s.set);
  const item = (icon: typeof Plus, label: string, fn: () => void, disabled = false, testid?: string) => {
    const Icon = icon;
    return (
      <button type="button" className="side-item" onClick={fn} disabled={disabled} data-testid={testid}>
        <Icon size={15} /> {label}
      </button>
    );
  };
  return (
    <div className="side-menu">
      {/* xodimlar o'rgangan tartib va guruhlar (oraliq bilan); MebeliX qo'shimchalari — «Справка» dan keyin, chiziq ortida */}
      {item(RefreshCw, t("menu.refresh"), refresh)}
      {item(FolderOpen, t("menu.open"), () => void openRow(sel), !sel)}
      <div className="side-gap" />
      {item(Plus, t("menu.add"), () => void addProject(t), false, "menu-add-project")}
      {item(FolderPlus, t("menu.add_folder"), () => void addFolder(t), false, "menu-add-folder")}
      <div className="side-gap" />
      {item(FolderInput, t("menu.move"), () => setMove(true), !rows.length)}
      {item(Pencil, t("menu.rename"), () => void renameRow(sel, t), !sel)}
      {item(Copy, t("menu.copy"), () => void copyRows(rows), !rows.some((r) => r.kind === "project"))}
      {item(Trash, t("menu.delete"), () => void deleteRows(rows, t), !rows.length)}
      <div className="side-gap" />
      {item(CircleQuestionMark, t("menu.help"), () => setUI({ section: "help" }))}
      <div className="side-hint">{t("projects.open_hint")}</div>
      <div className="side-sep" />
      {item(ArrowUpFromLine, t("export.selected"), () => void exportRows(rows, t), !rows.some((r) => r.kind === "project"),
        "menu-export-project")}
      {item(ListChecks, t("menu.select_all"), () => gridApi?.selectAll(), false, "menu-select-all")}
      {item(ArrowDownToLine, t("menu.import"), () => pickFile(".json,.mxk,.project", (f) => void importProjectFile(f, t)), false,
        "menu-import")}
      {item(ScanLine, t("menu.workshop"), () => { window.location.hash = "#/sex"; })}
      {move && rows.length > 0 && (
        <FolderPicker title={t("menu.move")} exclude={rows.length === 1 && rows[0].kind === "folder" ? rows[0].id : undefined}
          onClose={() => setMove(false)}
          onPick={async (fid) => {
            setMove(false);
            const ps = rows.filter((r) => r.kind === "project");
            if (ps.length) await call(() => post("/projects/move", { ids: ps.map((r) => r.id), folder_id: fid }));
            for (const f of rows.filter((r) => r.kind === "folder")) await call(() => patch(`/folders/${f.id}`, { parent_id: fid }));
            refresh();
          }} />
      )}
    </div>
  );
}

/** Asosiy maydon: papkalar va loyihalar jadvali. */
export function ProjectsView() {
  const { t, i18n } = useTranslation();
  const folderId = useUI((s) => s.folderId);
  const setUI = useUI((s) => s.set);
  const [q, setQ] = useState("");
  const [stFilter, setStFilter] = useState("all");               // holat bo'yicha filtr: all | 0..3 (faqat loyihalar)
  const folders = useFolders(q ? "__none__" : folderId);
  const projects = useProjects(folderId, q);
  const path = useFolderPath(folderId);
  const sel = useSel();
  const currency = useAppSettings().data?.currency ?? "UZS";
  const me = useMe().data;                             // «Владелец»: o'z loyihasi — «Мой»
  const grid = useRef<AgGridReact<Row>>(null);
  const [queue, setQueue] = useState(false);          // «Очередь заказов» — material bazasi tekshiruvi

  const rows = useMemo<Row[]>(() => [
    ...(q ? [] : (folders.data ?? []).map((f) => ({ kind: "folder" as const, id: f.id, name: f.name }))),
    ...(projects.data ?? []).filter((p: ProjectRow) => stFilter === "all" || String(p.status) === stFilter)
      .map((p: ProjectRow) => ({ kind: "project" as const, id: p.id, name: p.name, number: p.number,
        owner: p.owner, status: p.status, order_date: p.order_date, cost: p.cost, customer: p.customer, updated_at: p.updated_at })),
  ], [folders.data, projects.data, q, stFilter]);
  // ro'yxat yangilangach (qayta nomlash, nusxa, holat) tanlov do'konidagi qator nusxalari ham yangilanadi (#2: eskirgan nom)
  useEffect(() => {
    const s = useSel.getState();
    if (!s.rows.length) return;
    const byKey = new Map(rows.map((r) => [`${r.kind}:${r.id}`, r]));
    const fresh = (r: Row) => byKey.get(`${r.kind}:${r.id}`) ?? r;
    const nrows = s.rows.map(fresh);
    const nrow = s.row ? fresh(s.row) : null;
    if (nrow === s.row && nrows.every((r, i) => r === s.rows[i])) return;      // o'zgarmagan — qayta chizish yo'q
    useSel.setState({ rows: nrows, row: nrow });
  }, [rows]);

  // Ustunlar 1024 px da ham sig'adi: «Наименование» egiluvchan (minWidth 150), «Владелец» egiluvchan, tor jadvalda «Изменено» yashirinadi
  const cols = useMemo<ColDef<Row>[]>(() => [
    // «№» — ko'rinadigan qator raqami (OL-007; saralash/filtrdan keyin qayta hisoblanadi); «ID» — buyurtma raqami
    { colId: "n", headerName: t("projects.col.no"), width: 44, cellClass: "num rownum", sortable: false,
      valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1 },
    { colId: "kind", headerName: "", width: 34, sortable: false, cellClass: "kind-cell",
      cellRenderer: (p: { data?: Row }) => (p.data?.kind === "folder" ? <FolderIcon size={15} className="ico-folder" />
        : p.data ? <FileText size={15} className="ico-doc" /> : null) },
    { headerName: t("projects.col.id"), field: "number", width: 80, cellClass: "num" },
    // o'z loyihasi — «Мой» (xodimlar o'rgangan tizimdagidek), boshqalarniki — foydalanuvchi nomi
    { headerName: t("projects.col.owner"), field: "owner", flex: 1, minWidth: 70, maxWidth: 130,
      valueFormatter: (p) => (p.data?.kind !== "project" ? ""
        : p.value && me && (p.value === me.name || p.value === me.sub) ? t("projects.owner_me") : (p.value ?? "")) },
    { headerName: t("projects.col.status"), field: "status", width: 118,
      valueFormatter: (p) => (p.data?.kind === "project" ? t(STATUS_KEYS[p.value ?? 0]) : "") },
    { headerName: t("projects.col.date"), field: "order_date", width: 108,
      valueFormatter: (p) => (p.data?.kind === "project" ? fmtDateWd(p.value, i18n.language) : "") },
    { colId: "updated_at", headerName: t("projects.col.changed"), field: "updated_at", width: 130, cellClass: "muted",     // OL-007: «Изменено»
      valueFormatter: (p) => (p.data?.kind === "project" ? fmtDateTime(p.value) : "") },
    { headerName: t("projects.col.cost"), field: "cost", width: 118, cellClass: "num",
      valueFormatter: (p) => (p.data?.kind === "project" ? `${money(p.value)} ${currency}` : "") },
    { headerName: t("projects.col.name"), field: "name", flex: 3, minWidth: 150,
      cellRenderer: (p: { data?: Row; value: string }) => p.data?.kind === "folder"
        ? <b>{p.value}</b>
        : <span>{p.value}{p.data?.customer ? <span className="muted"> · {p.data.customer}</span> : null}</span> },
  ], [t, i18n.language, currency, me]);

  const up = () => {
    const pth = path.data ?? [];
    setUI({ folderId: pth.length >= 2 ? pth[pth.length - 2].id : null });
  };
  useHotkeys("projects", {
    "ctrl+space,enter": () => void openRow(sel.row),
    // tanlov — to'g'ridan-to'g'ri jadvaldan: jadval «tanlov o'zgardi» hodisasini kechikib yuboradi (Ctrl+A dan darhol Del)
    "delete,shift+delete": () => {
      const live = (grid.current?.api ?? gridApi)?.getSelectedRows() as Row[] | undefined;
      void deleteRows(live?.length ? live : useSel.getState().rows, t);
    },
    backspace: up,
    f2: () => void renameRow(sel.row, t),
    f4: () => { if (sel.rows.length) sel.setMove(true); },
    "ctrl+pagedown": () => void addProject(t),
    "ctrl+a": () => (grid.current?.api ?? gridApi)?.selectAll(),   // ref bo'sh bo'lishi mumkin — onGridReady API si
  });
  // tanlov yo'q bo'lsa: oxirgi tanlangan (masalan hozir yopilgan) qator qayta tanlanadi, u yo'q bo'lsa — birinchi qator
  const restoreSel = (api: GridApi<Row>) => {
    if (api.getSelectedNodes().length) return;
    const r = useSel.getState().row;
    const node = r ? api.getRowNode(`${r.kind}:${r.id}`) : undefined;
    if (node) { node.setSelected(true, true); api.ensureNodeVisible(node); return; }
    selectFirstIfNone(api);
  };
  const menu = () => {
    const s = useSel.getState();
    const anyProject = s.rows.some((r) => r.kind === "project");
    // tartib xodimlar o'rgangan menyudek; «Открыть» va «Экспорт .project» (MebeliX qo'shimchalari) — oxirida
    return [
      { label: t("menu.add"), hint: "Ctrl+PgDn", icon: Plus, onClick: () => void addProject(t), testid: "ctx-proj-add" },
      { label: t("menu.rename"), hint: "F2", icon: Pencil, onClick: () => void renameRow(s.row, t), disabled: !s.row, testid: "ctx-proj-rename" },
      { label: t("menu.add_folder"), icon: FolderPlus, onClick: () => void addFolder(t) },
      { label: t("menu.move"), hint: "F4", icon: FolderInput, onClick: () => s.setMove(true), disabled: !s.rows.length },
      { label: t("menu.copy"), icon: Copy, onClick: () => void copyRows(s.rows), disabled: !anyProject },
      { label: t("menu.delete"), hint: "Del", icon: Trash, onClick: () => void deleteRows(s.rows, t), disabled: !s.rows.length,
        testid: "ctx-proj-delete" },
      { sep: true, label: "" },
      { label: t("menu.select_all"), hint: "Ctrl+A", icon: ListChecks, onClick: () => (grid.current?.api ?? gridApi)?.selectAll() },
      { sep: true, label: "" },
      { label: t("menu.help"), hint: "F1", icon: CircleQuestionMark, onClick: () => setUI({ section: "help" }) },
      { sep: true, label: "" },
      { label: t("menu.open"), hint: "Enter", icon: FolderOpen, onClick: () => void openRow(s.row), disabled: !s.row, testid: "ctx-proj-open" },
      { label: t("export.selected"), icon: ArrowUpFromLine, onClick: () => void exportRows(s.rows, t), disabled: !anyProject },
    ];
  };
  // klaviatura bilan yurganda tanlov fokusga ergashadi (Shift/Ctrl bilan — AG Grid ning ko'p tanlovi)
  const mods = useRef(false);
  const lastFocus = useRef<number | null>(null);

  return (
    <div className="page" {...scopeProps("projects")}>
      {/* sarlavha so'zi yo'q: ↑ va «Домой» ikonkalari chap chetda, keyin papka yo'li (xodimlar o'rgangan joylashuv) */}
      <div className="page-head">
        <Toolbar>
          <IconBtn icon={CornerLeftUp} title={t("projects.up")} onClick={up} disabled={!folderId} />
          <IconBtn icon={House} title={t("projects.home")} onClick={() => setUI({ folderId: null })} />
          <div className="crumbs">
            <span className="crumb" onClick={() => setUI({ folderId: null })}>{t("projects.root")}</span>
            {(path.data ?? []).map((f) => (
              <span key={f.id} className="crumb" onClick={() => setUI({ folderId: f.id })}> / {f.name}</span>
            ))}
          </div>
          <div className="search">
            <Search size={14} />
            <input className="inp" placeholder={t("projects.search")} value={q} data-testid="projects-search"
              onChange={(e) => setQ(e.target.value)} />
          </div>
          <Sel<string> value={stFilter} width={150} testid="projects-status-filter"
            options={[{ value: "all", label: t("projects.filter.all") },
              ...STATUS_KEYS.map((k, i) => ({ value: String(i), label: t(k) }))]}
            onChange={setStFilter} />
          <Btn icon={Plus} kind="primary" label={t("projects.new")} onClick={() => void addProject(t)}
            testid="btn-new-project" />
          <IconBtn icon={FolderPlus} title={t("menu.add_folder")} onClick={() => void addFolder(t)} />
          <IconBtn icon={ArrowDownToLine} title={t("menu.import")}
            onClick={() => pickFile(".json,.mxk,.project", (f) => void importProjectFile(f, t))} />
          <IconBtn icon={ListOrdered} title={t("queue.title")} onClick={() => setQueue(true)} testid="btn-queue" />
        </Toolbar>
      </div>
      <div className="grow" style={{ minHeight: 0, display: "flex" }}
        onKeyDownCapture={(e) => { mods.current = e.shiftKey || e.ctrlKey || e.metaKey; }}
        onKeyUpCapture={() => { mods.current = false; }}>
        <Grid<Row> ref={grid} className="grow" rowData={rows} columnDefs={cols} testid="projects-grid"
          getRowId={(p) => `${p.data.kind}:${p.data.id}`} defaultColDef={{ sortable: true }} onRefresh={refresh}
          postSortRows={(p) => {     // papkalar doim yuqorida
            const n = p.nodes;
            const folders = n.filter((x) => x.data?.kind === "folder");
            n.splice(0, n.length, ...folders, ...n.filter((x) => x.data?.kind !== "folder"));
          }}
          onGridReady={(e) => { gridApi = e.api; }}
          onFirstDataRendered={(e) => restoreSel(e.api)}
          onRowDataUpdated={(e) => restoreSel(e.api)}
          menu={menu}
          onGridSizeChanged={(e) => {      // tor oyna: «Изменено» yashirin (faqat holat o'zgarganda — fokus/tanlovga tegilmaydi)
            const show = e.clientWidth >= 900;
            if (e.api.getColumn("updated_at")?.isVisible() !== show) e.api.setColumnsVisible(["updated_at"], show);
          }}
          onSortChanged={(e) => e.api.refreshCells({ columns: ["n"], force: true })}
          rowSelection={ROW_SELECTION}
          onSelectionChanged={(e) => sel.setRows(e.api.getSelectedRows())}
          onRowDoubleClicked={(e) => void openRow(e.data ?? null)}
          onCellFocused={(e) => {
            // fokus boshqa qatorga o'tgandagina tanlov ergashadi (fokus qaytishi — masalan oyna yopilgach — Ctrl+A ni buzmasin)
            if (e.rowIndex == null) return;               // fokus vaqtincha yo'qolishi (qayta chizish) — eslab qolinmaydi
            lastFocus.current = e.rowIndex;
            // modifikator bilan — tanlovga tegilmaydi; aks holda fokusdagi qator tanlanadi
            if (mods.current) return;
            const node = e.api.getDisplayedRowAtIndex(e.rowIndex);
            // Fokus allaqachon tanlangan qatorga tushsa — tanlovga tegilmaydi: Ctrl+A dan keyin kechikib kelgan fokus hodisasi
            // (bosilgan qator) ko'p tanlovni bitta qatorga qisqartirmasin (e2e lists.spec.ts da vaqti-vaqti bilan yiqilardi)
            if (node && !node.isSelected()) node.setSelected(true, true);
          }} />
      </div>
      {queue && <QueueDialog onClose={() => setQueue(false)} />}
    </div>
  );
}
