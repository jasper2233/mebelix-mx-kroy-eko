// «Товары» oynasi mazmuni: chapda kategoriyalar daraxti, o'ngda rasm, pastda «Материалы» paneli — sarlavha satrida qidiruv (chapda),
// «Обновить» va «Настройки» (o'ngda; ustunlar profillari `catalog_columns`), xodimlar o'rgangan joylashuvdagidek.
// Material turi (list / kromka / pogonaj / sirt) bo'yicha filtr daraxtni ham torayutiradi (bo'sh papkalar yashiriladi).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { ChevronDown, ChevronRight, Folder, FolderOpen, ImageOff, ImageUp, List, RefreshCw, Settings2, Trash } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { api, del } from "../../api/client";
import type { CatalogItem } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Grid } from "../../shared/grid/Grid";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import { useHotkeys, scopeProps } from "../../shared/hotkeys";
import { IconBtn, Sel, cx, money } from "../../shared/ui";
import {
  CATALOG_KINDS, ITEM_LIMIT, safeImage, useCatalogItem, useCatalogItems, useCatalogTree, useDebounced,
  type CatalogNode, type CatalogSel,
} from "./api";
import "./catalog.css";

const MAX_IMAGE_KB = 256;

/** «Настройки»: materiallar jadvali ustunlari (№ — doim chapda; «Тип» — MebeliX qo'shimchasi, oxirida). */
const CAT_COLUMNS: GridKind = { scope: "catalog_columns", specs: [
  { key: "code", name: "catalog.code", width: 16 },
  { key: "name", name: "catalog.name", width: 40 },
  { key: "unit", name: "catalog.unit", width: 6 },
  { key: "price", name: "catalog.price", width: 11 },
  { key: "stock", name: "catalog.stock", width: 8 },
  { key: "thickness", name: "catalog.th", width: 6 },
  { key: "length", name: "catalog.len", width: 7 },
  { key: "width", name: "catalog.wid", width: 7 },
  { key: "kind", name: "catalog.kind", width: 10 },
] };

interface Props {
  kind: string;
  onKind: (k: string) => void;
  selected: CatalogItem | null;
  onSelect: (i: CatalogItem | null) => void;
  onActivate?: (i: CatalogItem) => void;          // ikki marta bosish
  editable?: boolean;                             // rasm yuklash/o'chirish, papkani o'chirish (Sozlamalar sahifasi)
  testid?: string;
}

export function CatalogBrowser({ kind, onKind, selected, onSelect, onActivate, editable, testid }: Props) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const dq = useDebounced(q.trim());
  const [node, setNode] = useState<CatalogSel>({ type: "all" });
  const [open, setOpen] = useState<Set<string>>(new Set());
  const tree = useCatalogTree(kind, dq);
  const items = useCatalogItems(kind, dq, node);
  const inited = useRef(false);

  // birinchi yuklanishda: papkalar kam bo'lsa hammasi ochiq, ko'p bo'lsa — dastlabki ikki daraja
  useEffect(() => {
    if (inited.current || !tree.data || !tree.data.nodes.length) return;
    inited.current = true;
    const all: { id: string; depth: number }[] = [];
    const walk = (ns: CatalogNode[], depth: number) => ns.forEach((n) => { all.push({ id: n.id, depth }); walk(n.children, depth + 1); });
    walk(tree.data.nodes, 1);
    setOpen(new Set(all.filter((x) => all.length <= 40 || x.depth <= 2).map((x) => x.id)));
  }, [tree.data]);
  // tanlangan papka (yoki tur/qidiruv) daraxtdan yo'qolsa — «Все» ga qaytish
  useEffect(() => {
    if (node.type !== "folder" || !tree.data) return;
    const has = (ns: CatalogNode[]): boolean => ns.some((n) => n.id === node.id || has(n.children));
    if (!has(tree.data.nodes)) setNode({ type: "all" });
  }, [tree.data, node]);
  useEffect(() => { onSelect(null); }, [node, kind, dq]); // eslint-disable-line react-hooks/exhaustive-deps

  // ro'yxat yangilansa (masalan, rasm yuklandi) tanlangan qator ham yangi ma'lumot bilan almashadi
  useEffect(() => {
    if (!selected || !items.data) return;
    const fresh = items.data.find((r) => r.id === selected.id);
    if (fresh && fresh !== selected) onSelect(fresh);
  }, [items.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) => setOpen((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const searching = dq !== "";
  const total = tree.data?.total ?? 0;
  const rows = items.data ?? [];

  const cols = useMemo<ColDef<CatalogItem>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 52, cellClass: "num rownum" },
    { headerName: t("catalog.code"), field: "code", width: 140 },
    { headerName: t("catalog.name"), field: "name", flex: 1, minWidth: 180 },
    { headerName: t("catalog.unit"), field: "unit", width: 62 },
    { headerName: t("catalog.price"), field: "price", width: 100, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("catalog.stock"), field: "stock", width: 80, cellClass: "num" },
    { headerName: t("catalog.th"), field: "thickness", width: 62, cellClass: "num" },
    { headerName: t("catalog.len"), field: "length", width: 70, cellClass: "num" },
    { headerName: t("catalog.wid"), field: "width", width: 70, cellClass: "num" },
    { headerName: t("catalog.kind"), field: "kind", width: 84, valueFormatter: (p) => t(`catalog.kinds.${p.value}`, { defaultValue: p.value }) },
  ], [t]);
  const colset = useGridColumns(CAT_COLUMNS, cols);
  useHotkeys("catalog", { "ctrl+p": () => colset.open() });

  const refresh = () => { void qc.invalidateQueries({ queryKey: ["catalog"] }); };
  const deleteFolder = async () => {
    if (node.type !== "folder" || !(await askConfirm(t("catalog.delete_folder_q")))) return;
    if (await call(() => del(`/catalog/${encodeURIComponent(node.id)}`, { recursive: true }))) { setNode({ type: "all" }); refresh(); }
  };

  return (
    <div className="cat" data-testid={testid ?? "catalog-browser"} {...scopeProps("catalog")}>
      <div className="cat-top">
        <div className="cat-panel">
          <div className="cat-title">{t("catalog.categories")}</div>
          <div className="tree cat-tree" data-testid="catalog-tree">
            <div className={cx("tree-item", node.type === "all" && "tree-item-active")} onClick={() => setNode({ type: "all" })}
              data-testid="catalog-node-all">
              <Folder size={14} /><span className="cat-name">{t("catalog.all_materials")}</span><span className="muted">{total}</span>
            </div>
            {(tree.data?.nodes ?? []).map((n) => (
              <TreeRow key={n.id} n={n} depth={1} open={open} force={searching} toggle={toggle} node={node} setNode={setNode} />
            ))}
            {(tree.data?.unfiled ?? 0) > 0 && (tree.data?.nodes.length ?? 0) > 0 && (
              <div className={cx("tree-item", node.type === "unfiled" && "tree-item-active")} onClick={() => setNode({ type: "unfiled" })}
                data-testid="catalog-node-unfiled">
                <Folder size={14} /><span className="cat-name">{t("catalog.unfiled")}</span><span className="muted">{tree.data?.unfiled}</span>
              </div>
            )}
          </div>
        </div>
        <ImagePanel item={selected} editable={!!editable} onChanged={refresh} />
      </div>
      <div className="cat-mat">
        <div className="cat-title cat-mat-head">
          <span className="cat-mat-name"><List size={14} /> {t("catalog.materials")}</span>
          <input className="inp cat-search" placeholder={t("projects.search")} value={q}
            onChange={(e) => setQ(e.target.value)} data-testid="catalog-search" />
          <Sel value={kind} onChange={onKind} width={130} testid="catalog-kind" options={[
            { value: "", label: t("catalog.all") }, ...CATALOG_KINDS.map((k) => ({ value: k as string, label: t(`catalog.kinds.${k}`) }))]} />
          {editable && <IconBtn icon={Trash} title={t("catalog.delete_folder")} disabled={node.type !== "folder"}
            onClick={() => void deleteFolder()} testid="catalog-delete-folder" />}
          <span className="cat-actions">
            <IconBtn icon={RefreshCw} label={t("menu.refresh")} title={t("menu.refresh")} onClick={refresh} testid="catalog-refresh" />
            <IconBtn icon={Settings2} label={t("ops.settings")} title={`${t("ops.settings")} (Ctrl+P)`} onClick={colset.open}
              testid="catalog-settings" />
          </span>
        </div>
        {!items.isLoading && rows.length === 0 && !dq && total === 0 && <p className="muted cat-pad">{t("catalog.empty_hint")}</p>}
        {rows.length >= ITEM_LIMIT && <p className="muted small cat-pad">{t("catalog.limit_hint", { n: ITEM_LIMIT })}</p>}
        <Grid<CatalogItem> className="grow" rowData={rows} columnDefs={colset.columnDefs} getRowId={(p) => p.data.id} testid="catalog-grid"
          rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
          onRowClicked={(e) => onSelect(e.data ?? null)}
          onRowDoubleClicked={(e) => e.data && onActivate?.(e.data)} />
      </div>
      {colset.dialog}
    </div>
  );
}

function TreeRow({ n, depth, open, force, toggle, node, setNode }: {
  n: CatalogNode; depth: number; open: Set<string>; force: boolean; toggle: (id: string) => void;
  node: CatalogSel; setNode: (s: CatalogSel) => void;
}) {
  const expanded = force || open.has(n.id);
  const has = n.children.length > 0;
  const active = node.type === "folder" && node.id === n.id;
  return (
    <>
      <div className={cx("tree-item", active && "tree-item-active")} style={{ paddingLeft: 6 + depth * 14 }}
        onClick={() => setNode({ type: "folder", id: n.id })} data-testid={`catalog-node-${n.id}`}>
        <span className="cat-caret" onClick={(e) => { e.stopPropagation(); if (has) toggle(n.id); }}>
          {has ? (expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />) : null}
        </span>
        {expanded && has ? <FolderOpen size={14} /> : <Folder size={14} />}
        <span className="cat-name" title={n.name}>{n.name}</span><span className="muted">{n.count}</span>
      </div>
      {expanded && n.children.map((c) => (
        <TreeRow key={c.id} n={c} depth={depth + 1} open={open} force={force} toggle={toggle} node={node} setNode={setNode} />
      ))}
    </>
  );
}

function ImagePanel({ item, editable, onChanged }: { item: CatalogItem | null; editable: boolean; onChanged: () => void }) {
  const { t } = useTranslation();
  const detail = useCatalogItem(item?.has_image ? item.id : null);
  const src = safeImage(item?.has_image ? detail.data?.image : null);
  const input = useRef<HTMLInputElement>(null);
  const upload = async (f: File) => {
    if (!item) return;
    if (!/^image\/(png|jpeg|gif|webp)$/.test(f.type) || f.size > MAX_IMAGE_KB * 1024) {
      useUI.getState().toast(t("catalog.image_bad", { n: MAX_IMAGE_KB }), "error");
      return;
    }
    const fd = new FormData();
    fd.append("file", f);
    if (await call(() => api("/catalog/" + encodeURIComponent(item.id) + "/image", { method: "PUT", form: fd }))) onChanged();
  };
  const params = Object.entries(item?.params ?? {});
  return (
    <div className="cat-panel">
      <div className="cat-title">
        <span>{t("catalog.image")}</span>
        {editable && item && (
          <span className="cat-actions">
            <IconBtn icon={ImageUp} title={t("catalog.image_upload")} onClick={() => input.current?.click()} testid="catalog-image-upload" />
            {item.has_image && <IconBtn icon={ImageOff} title={t("catalog.image_remove")} testid="catalog-image-remove" onClick={async () => {
              if (await call(() => del("/catalog/" + encodeURIComponent(item.id) + "/image"))) onChanged();
            }} />}
            <input ref={input} type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden data-testid="catalog-image-file"
              onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) void upload(f); }} />
          </span>
        )}
      </div>
      <div className="cat-image" data-testid="catalog-image">
        {src ? <img src={src} alt={item?.name ?? ""} referrerPolicy="no-referrer" /> : <span className="muted">{t("catalog.no_image")}</span>}
      </div>
      {item && (
        <div className="cat-detail">
          <b title={item.name}>{item.name}</b>
          {item.code && <span className="muted"> · {item.code}</span>}
          {params.length > 0 && <div className="muted small">{params.map(([k, v]) => `${k}=${String(v)}`).join("; ")}</div>}
        </div>
      )}
    </div>
  );
}
