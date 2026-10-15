// «Настройки → Каталог товаров»: daraxt + rasm + jadval, Excel importi, o'chirish (papka bilan).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FileSpreadsheet, Trash } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del } from "../../api/client";
import type { CatalogItem } from "../../api/types";
import { askConfirm } from "../../shared/dialogs";
import { Btn } from "../../shared/ui";
import { CatalogBrowser } from "./CatalogBrowser";
import { CatalogImport } from "./CatalogImport";

export function CatalogPage() {
  const { t } = useTranslation();
  const [kind, setKind] = useState("");
  const [sel, setSel] = useState<CatalogItem | null>(null);
  const [imp, setImp] = useState(false);
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.catalog")}</h2>
        <Btn icon={FileSpreadsheet} label={t("catalog.import")} onClick={() => setImp(true)} testid="catalog-import-open" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={!sel} onClick={async () => {
          if (!sel || !(await askConfirm(t("catalog.delete_q")))) return;
          await call(() => del(`/catalog/${encodeURIComponent(sel.id)}`));
          setSel(null);
          void qc.invalidateQueries({ queryKey: ["catalog"] });
        }} />
      </div>
      <p className="muted">{t("catalog.mes_hint")}</p>
      <CatalogBrowser kind={kind} onKind={setKind} selected={sel} onSelect={setSel} editable testid="settings-catalog" />
      {imp && <CatalogImport onClose={() => setImp(false)} />}
    </div>
  );
}
