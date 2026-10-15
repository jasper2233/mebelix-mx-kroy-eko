// «Товары» (Каталог товаров) — materialni kategoriyalar daraxtidan tanlab operatsiya qo'shish.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { CatalogItem } from "../../api/types";
import { Btn, Modal } from "../../shared/ui";
import { CatalogBrowser } from "../catalog/CatalogBrowser";

/** Operatsiyaga aylantiriladigan turlar: list (CS), погонаж (CL, W11), kromka (EL) va sirt materiali (SP). */
const PICKABLE = ["sheet", "linear", "edge", "surface"];

export function CatalogPicker({ onPick, onClose, kind: kind0 = "" }: { onPick: (i: CatalogItem) => void; onClose: () => void; kind?: string }) {
  const { t } = useTranslation();
  const [kind, setKind] = useState(kind0);
  const [sel, setSel] = useState<CatalogItem | null>(null);
  return (
    <Modal title={t("ops.catalog")} onClose={onClose} width={960} height={680} testid="catalog-picker"
      footer={<><Btn kind="primary" label={t("app.choose")} disabled={!sel || !PICKABLE.includes(sel.kind)} testid="catalog-pick"
        title={sel && !PICKABLE.includes(sel.kind) ? t("catalog.not_supported") : undefined} onClick={() => sel && onPick(sel)} />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <CatalogBrowser kind={kind} onKind={setKind} selected={sel} onSelect={setSel}
        onActivate={(i) => PICKABLE.includes(i.kind) && onPick(i)} />
    </Modal>
  );
}
