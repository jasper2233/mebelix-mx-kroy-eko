// Loyihalar ro'yxati (Проекты, UI_SPEC §1): papkalar + loyihalar, ochish (dbl-click / Ctrl+Space).
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import type { AgGridReact } from "ag-grid-react";
import type { ColDef } from "ag-grid-community";
import {
  ArrowUpToLine, Copy, CornerLeftUp, Folder as FolderIcon, FolderInput, FolderOpen, FolderPlus, House, Pencil, Plus,
  RefreshCw, ScanLine, Search, Trash, Upload,
} from "lucide-react";
import { call, qc, useAllFolders, useFolderPath, useFolders, useProjects } from "../../api/hooks";
import { api, del, patch, post } from "../../api/client";
import type { Folder, Project, ProjectRow } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid } from "../../shared/grid/Grid";
import { askConfirm, askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Toolbar, cx, money } from "../../shared/ui";

interface Row { kind: "folder" | "project"; id: string; name: string; number?: number; owner?: string; status?: number;
  order_date?: string; cost?: number; customer?: string }

const useSel = create<{ row: Row | null; set: (r: Row | null) => void }>((set) => ({ row: null, set: (r) => set({ row: r }) }));

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

async function renameRow(r: Row | null, t: (k: string) => string) {
  if (!r) return;
  const name = await askText(t("menu.rename"), r.name);
  if (!name || name === r.name) return;
  if (r.kind === "folder") await call(() => patch(`/folders/${r.id}`, { name }));
  else await call(() => patch(`/projects/${r.id}`, { name }));
  refresh();
}

async function copyRow(r: Row | null) {
  if (!r || r.kind !== "project") return;
  await call(() => post(`/projects/${r.id}/copy`));
  refresh();
}

async function deleteRow(r: Row | null, t: (k: string, o?: Record<string, unknown>) => string) {
  if (!r) return;
  if (r.kind === "folder") {
    if (!(await askConfirm(t("projects.delete_folder_q", { name: r.name }), t("projects.delete_folder_text"),
      { danger: true, ok: t("app.delete") }))) return;
    await call(() => del(`/folders/${r.id}`, { recursive: true }));
  } else {
    if (!(await askConfirm(t("projects.delete_q", { name: r.name }), undefined, { danger: true, ok: t("app.delete") }))) return;
    await call(() => del(`/projects/${r.id}`));
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
  const [move, setMove] = useState(false);
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
      {item(RefreshCw, t("menu.refresh"), refresh)}
      {item(FolderOpen, t("menu.open"), () => void openRow(sel), !sel)}
      {item(Plus, t("menu.add"), () => void addProject(t), false, "menu-add-project")}
      {item(FolderPlus, t("menu.add_folder"), () => void addFolder(t), false, "menu-add-folder")}
      {item(FolderInput, t("menu.move"), () => setMove(true), !sel)}
      {item(Pencil, t("menu.rename"), () => void renameRow(sel, t), !sel)}
      {item(Copy, t("menu.copy"), () => void copyRow(sel), !sel || sel.kind !== "project")}
      {item(Trash, t("menu.delete"), () => void deleteRow(sel, t), !sel)}
      {item(Upload, t("menu.import"), () => pickFile(".json,.mxk,.project", (f) => void importProjectFile(f, t)), false,
        "menu-import")}
      {item(ScanLine, t("menu.workshop"), () => { window.location.hash = "#/sex"; })}
      {move && sel && (
        <FolderPicker title={t("menu.move")} exclude={sel.kind === "folder" ? sel.id : undefined}
          onClose={() => setMove(false)}
          onPick={async (fid) => {
            setMove(false);
            if (sel.kind === "folder") await call(() => patch(`/folders/${sel.id}`, { parent_id: fid }));
            else await call(() => post("/projects/move", { ids: [sel.id], folder_id: fid }));
            refresh();
          }} />
      )}
    </div>
  );
}

/** Asosiy maydon: papkalar va loyihalar jadvali. */
export function ProjectsView() {
  const { t } = useTranslation();
  const folderId = useUI((s) => s.folderId);
  const setUI = useUI((s) => s.set);
  const [q, setQ] = useState("");
  const folders = useFolders(q ? "__none__" : folderId);
  const projects = useProjects(folderId, q);
  const path = useFolderPath(folderId);
  const sel = useSel();
  const grid = useRef<AgGridReact<Row>>(null);

  const rows = useMemo<Row[]>(() => [
    ...(q ? [] : (folders.data ?? []).map((f) => ({ kind: "folder" as const, id: f.id, name: f.name }))),
    ...(projects.data ?? []).map((p: ProjectRow) => ({ kind: "project" as const, id: p.id, name: p.name, number: p.number,
      owner: p.owner, status: p.status, order_date: p.order_date, cost: p.cost, customer: p.customer })),
  ], [folders.data, projects.data, q]);

  const cols = useMemo<ColDef<Row>[]>(() => [
    { headerName: t("projects.col.id"), field: "number", width: 90, cellClass: "num" },
    { headerName: t("projects.col.owner"), field: "owner", width: 120 },
    { headerName: t("projects.col.status"), field: "status", width: 120,
      valueFormatter: (p) => (p.data?.kind === "project" ? t(STATUS_KEYS[p.value ?? 0]) : ""),
      cellClass: (p) => (p.data?.kind === "project" ? `st st-${p.value}` : "") },
    { headerName: t("projects.col.date"), field: "order_date", width: 100 },
    { headerName: t("projects.col.cost"), field: "cost", width: 120, cellClass: "num",
      valueFormatter: (p) => (p.data?.kind === "project" ? money(p.value) : "") },
    { headerName: t("projects.col.name"), field: "name", flex: 1, minWidth: 200,
      cellRenderer: (p: { data?: Row; value: string }) => p.data?.kind === "folder"
        ? <span className="folder-cell"><FolderIcon size={14} /> {p.value}</span>
        : <span>{p.value}{p.data?.customer ? <span className="muted"> · {p.data.customer}</span> : null}</span> },
  ], [t]);

  const up = () => {
    const pth = path.data ?? [];
    setUI({ folderId: pth.length >= 2 ? pth[pth.length - 2].id : null });
  };
  useHotkeys("projects", {
    "ctrl+space,enter": () => void openRow(sel.row),
    delete: () => void deleteRow(sel.row, t),
    backspace: up,
    f2: () => void renameRow(sel.row, t),
  });

  return (
    <div className="page" {...scopeProps("projects")}>
      <div className="page-head">
        <h2>{t("menu.projects")}</h2>
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
          <Btn icon={Plus} kind="primary" label={t("projects.new")} onClick={() => void addProject(t)}
            testid="btn-new-project" />
          <IconBtn icon={FolderPlus} title={t("menu.add_folder")} onClick={() => void addFolder(t)} />
          <IconBtn icon={ArrowUpToLine} title={t("menu.import")}
            onClick={() => pickFile(".json,.mxk,.project", (f) => void importProjectFile(f, t))} />
        </Toolbar>
      </div>
      <Grid<Row> ref={grid} className="grow" rowData={rows} columnDefs={cols} testid="projects-grid"
        getRowId={(p) => `${p.data.kind}:${p.data.id}`}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onRowClicked={(e) => sel.set(e.data ?? null)}
        onRowDoubleClicked={(e) => void openRow(e.data ?? null)}
        onCellFocused={(e) => { const r = e.rowIndex != null ? grid.current?.api.getDisplayedRowAtIndex(e.rowIndex) : null;
          if (r?.data) sel.set(r.data); }} />
    </div>
  );
}
