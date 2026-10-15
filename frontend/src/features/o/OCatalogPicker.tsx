// (O) uchun «Каталог товаров» dan tanlash: bir nechta qatorni belgilab jadvalga qo'shish (kod, nom, birlik, narx).
// Umumiy CatalogPicker faqat list/kromkani operatsiyaga aylantiradi (bitta tanlov); bu oyna esa istalgan tovarni qator qiladi.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { useCatalog } from "../../api/hooks";
import type { CatalogItem } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { Btn, Modal, Sel, money } from "../../shared/ui";

export function OCatalogPicker({ onPick, onClose }: { onPick: (items: CatalogItem[]) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<CatalogItem[]>([]);
  const data = useCatalog(kind, q);
  const cols = useMemo<ColDef<CatalogItem>[]>(() => [
    { headerName: t("catalog.kind"), field: "kind", width: 90, valueFormatter: (p) => t(`catalog.kinds.${p.value}`, { defaultValue: p.value }) },
    { headerName: t("catalog.code"), field: "code", width: 130 },
    { headerName: t("catalog.name"), field: "name", flex: 1 },
    { headerName: t("o.col.unit"), field: "unit", width: 70 },
    { headerName: t("catalog.price"), field: "price", width: 100, cellClass: "num", valueFormatter: (p) => money(p.value) },
  ], [t]);
  return (
    <Modal title={t("o.catalog_title")} onClose={onClose} width={820} height={540} testid="o-catalog-picker"
      footer={<><Btn kind="primary" label={`${t("app.add")}${sel.length ? ` (${sel.length})` : ""}`} disabled={!sel.length}
        onClick={() => onPick(sel)} testid="o-catalog-add" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="row gap">
        <Sel value={kind} onChange={setKind} width={160} options={[
          { value: "", label: t("catalog.all") }, { value: "sheet", label: t("catalog.kinds.sheet") },
          { value: "edge", label: t("catalog.kinds.edge") }, { value: "linear", label: t("catalog.kinds.linear") },
          { value: "surface", label: t("catalog.kinds.surface") }]} />
        <input className="inp" style={{ flex: 1 }} placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {data.data && data.data.length === 0 && !q && <p className="muted">{t("catalog.empty_hint")}</p>}
      <Grid<CatalogItem> className="grow" rowData={data.data ?? []} columnDefs={cols} getRowId={(p) => p.data.id} testid="o-catalog-grid"
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows())}
        onRowDoubleClicked={(e) => e.data && onPick([e.data])} />
    </Modal>
  );
}
