// «Импорт из других программ» — ixcham oyna (xodimlar o'rgangandek): har format — bitta bosishli havola (fayl tanlash oynasi
// darhol ochiladi), pastda «Отмена». Format parametrlari va import profillari — MebeliX qo'shimchasi, ro'yxat oxiridagi
// «Параметры импорта…» havolasi to'liq oynani (ImportDialog.tsx) ochadi.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { SlidersHorizontal, type LucideIcon } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { useUI } from "../../store/ui";
import { Btn, Modal, cx } from "../../shared/ui";
import { IMPORT_ICONS } from "./importIcons";
import { runImport, useImportCatalog, type ImportFormatRow } from "./importApi";
import { ImportOtherDialog } from "./ImportDialog";
import "./importer.css";

function pickFile(accept: string, cb: (f: File) => void) {
  const inp = document.createElement("input");
  inp.type = "file";
  inp.accept = accept;
  inp.onchange = () => { if (inp.files?.[0]) cb(inp.files[0]); };
  inp.click();
}

export function ImportOtherQuick({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const lang = useUI((x) => x.lang);
  const cat = useImportCatalog();
  const [full, setFull] = useState(false);
  // boshqa dasturlar formatlari — server tartibida; MebeliX ning o'z «.project» importi — ro'yxat oxirida
  const all: ImportFormatRow[] = cat.data ?? [];
  const rows = [...all.filter((r) => r.key !== "project"), ...all.filter((r) => r.key === "project")];
  const label = (r: ImportFormatRow) => t(`importx.q.${r.key}`, { defaultValue: lang === "uz" ? r.name.uz : r.name.ru });

  const run = (r: ImportFormatRow) => {
    const ui = useUI.getState();
    if (r.status !== "ready") { ui.toast(r.reason || t("importx.no_module"), "warn"); return; }
    pickFile(r.exts.join(","), async (f) => {
      const res = await call(() => runImport(f, r.key, {}, ui.folderId), t("projects.importing"));
      if (!res) return;
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["folders"] });
      if (res.warnings.length) ui.toast(t("projects.import_warnings", { n: res.warnings.length }), "info", res.warnings);
      else ui.toast(t("projects.imported", { name: res.project.name }), "ok");
      onClose();
      ui.openProject(res.project.id);
    });
  };

  if (full) return <ImportOtherDialog onClose={onClose} />;
  return (
    <Modal title={t("menu.import_other")} onClose={onClose} width={320} testid="import-other-quick"
      footer={<Btn label={t("app.cancel")} onClick={onClose} testid="imq-cancel" />}>
      <div className="imq" data-testid="imq-list">
        {cat.isLoading && <div className="muted">{t("app.loading")}</div>}
        {rows.map((r) => {
          const Icon: LucideIcon = IMPORT_ICONS[r.icon] ?? IMPORT_ICONS["file-code"];
          return (
            <button key={r.key} type="button" className={cx("imq-item", r.status !== "ready" && "dim")} data-testid={`imq-${r.key}`}
              data-status={r.status} title={r.status === "ready" ? r.exts.join("  ") : r.reason} onClick={() => run(r)}>
              <Icon size={18} strokeWidth={1.8} /> <span>{label(r)}</span>
            </button>
          );
        })}
        <div className="side-sep" />
        <button type="button" className="imq-item imq-more" data-testid="imq-more" onClick={() => setFull(true)}>
          <SlidersHorizontal size={16} /> <span>{t("importx.q_more")}</span>
        </button>
      </div>
    </Modal>
  );
}
