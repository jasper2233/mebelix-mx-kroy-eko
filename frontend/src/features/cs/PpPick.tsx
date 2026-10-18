// «Постпроцессоры» oynasi (kroy → stanok formati): stanoklar ro'yxati (mikrosxema belgisi bilan), «Настройки», «Отмена».
// Xodimlarga tanish ko'rinish: bitta bosish — fayl yuklab olinadi.
import { useTranslation } from "react-i18next";
import { Cpu, FileText } from "lucide-react";
import type { PostprocessorInfo } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal } from "../../shared/ui";

export function PpPickDialog(props: {
  items: PostprocessorInfo[]; onPick: (p: PostprocessorInfo) => void; onClose: () => void; testid?: string;
}) {
  const { t } = useTranslation();
  const ui = useUI();
  // onlayn ro'yxatdagidek avval stanoklar (o'z tartibida), bizning formatlar (CSV, TXT, DXF, MES JSON, shablonlar) — oxirida
  const items = [...props.items.filter((p) => p.machine), ...props.items.filter((p) => !p.machine)];
  const label = (p: PostprocessorInfo) => (p.machine ? (p.label || p.name) : p.builtin ? t(`pp.builtin.${p.key}`, { defaultValue: p.name || p.key }) : p.name);
  return (
    <Modal title={t("pp.dialog_title")} onClose={props.onClose} width={460} testid={props.testid ?? "pp-dialog"}
      footer={<>
        <Btn label={t("menu.settings")} onClick={() => { props.onClose(); ui.set({ section: "settings" }); }} />
        <Btn label={t("app.cancel")} onClick={props.onClose} />
      </>}>
      <div className="ppick-list">
        {items.map((p) => {
          // mijoz uchun ochilmagan (admin) — nomi bilan ko'rinadi, xira, bosilganda hech narsa bo'lmaydi (server ham 403 beradi)
          const closed = !!p.machine && p.opened === false;
          const off = !!p.machine && !p.available && !closed;
          const Icon = p.machine ? Cpu : FileText;
          return (
            <button key={p.key} type="button" className={closed ? "ppick-item ppick-closed" : "ppick-item"} disabled={off}
              aria-disabled={closed || undefined} data-testid={`pp-${p.key}`}
              title={closed ? t("pp.closed_tip") : off ? t("pp.machine_unbound") : p.note || undefined}
              onClick={() => { if (closed) return; props.onPick(p); props.onClose(); }}>
              <Icon size={15} /> <span>{label(p)}</span>
              {/* stanok nomida format allaqachon ko'rsatilgan (onlayn kabi) — kengaytma faqat bizning formatlarda */}
              {p.extension && !p.machine ? <span className="muted"> (.{p.extension})</span> : null}
              {closed ? <span className="muted"> — {t("pp.closed")}</span> : off ? <span className="muted"> — {t("pp.machine_unbound")}</span> : null}
            </button>
          );
        })}
      </div>
    </Modal>
  );
}
