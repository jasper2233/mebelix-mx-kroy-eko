// «Каталог товаров» — materialni katalogdan tanlab operatsiya qo'shish.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { useCatalog } from "../../api/hooks";
import type { CatalogItem } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { Btn, Modal, Sel, money } from "../../shared/ui";

export function CatalogPicker({ onPick, onClose, kind: kind0 = "" }: { onPick: (i: CatalogItem) => void; onClose: () => void; kind?: string }) {
  const { t } = useTranslation();
  const [kind, setKind] = useState(kind0);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<CatalogItem | null>(null);
  const data = useCatalog(kind, q);
  const cols = useMemo<ColDef<CatalogItem>[]>(() => [
    { headerName: t("catalog.kind"), field: "kind", width: 80, valueFormatter: (p) => t(`catalog.kinds.${p.value}`, { defaultValue: p.value }) },
    { headerName: t("catalog.code"), field: "code", width: 130 },
    { headerName: t("catalog.name"), field: "name", flex: 1 },
    { headerName: t("catalog.thickness"), field: "thickness", width: 70, cellClass: "num" },
    { headerName: t("catalog.size"), width: 110, valueGetter: (p) => (p.data?.length ? `${p.data.length}×${p.data.width}` : "") },
    { headerName: t("catalog.price"), field: "price", width: 100, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("catalog.stock"), field: "stock", width: 80, cellClass: "num" },
  ], [t]);
  return (
    <Modal title={t("ops.catalog")} onClose={onClose} width={860} height={560} testid="catalog-picker"
      footer={<><Btn kind="primary" label={t("app.choose")} disabled={!sel} onClick={() => sel && onPick(sel)} />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="row gap">
        <Sel value={kind} onChange={setKind} width={160} options={[
          { value: "", label: t("catalog.all") }, { value: "sheet", label: t("catalog.kinds.sheet") },
          { value: "edge", label: t("catalog.kinds.edge") }, { value: "linear", label: t("catalog.kinds.linear") },
          { value: "surface", label: t("catalog.kinds.surface") }]} />
        <input className="inp" style={{ flex: 1 }} placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {data.data && data.data.length === 0 && !q && <p className="muted">{t("catalog.empty_hint")}</p>}
      <Grid<CatalogItem> className="grow" rowData={data.data ?? []} columnDefs={cols} getRowId={(p) => p.data.id}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onRowClicked={(e) => setSel(e.data ?? null)} onRowDoubleClicked={(e) => e.data && onPick(e.data)} />
    </Modal>
  );
}
