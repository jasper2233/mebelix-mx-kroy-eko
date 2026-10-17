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
  const label = (p: PostprocessorInfo) => (p.machine ? (p.label || p.name) : p.builtin ? t(`pp.builtin.${p.key}`, { defaultValue: p.name || p.key }) : p.name);
  return (
    <Modal title={t("pp.dialog_title")} onClose={props.onClose} width={460} testid={props.testid ?? "pp-dialog"}
      footer={<>
        <Btn label={t("menu.settings")} onClick={() => { props.onClose(); ui.set({ section: "settings" }); }} />
        <Btn label={t("app.cancel")} onClick={props.onClose} />
      </>}>
      <div className="ppick-list">
        {props.items.map((p) => {
          const off = !!p.machine && !p.available;
          const Icon = p.machine ? Cpu : FileText;
          return (
            <button key={p.key} type="button" className="ppick-item" disabled={off} data-testid={`pp-${p.key}`}
              title={off ? t("pp.machine_unbound") : p.note || undefined}
              onClick={() => { props.onPick(p); props.onClose(); }}>
              <Icon size={15} /> <span>{label(p)}</span>
              {p.extension ? <span className="muted"> (.{p.extension})</span> : null}
              {off ? <span className="muted"> — {t("pp.machine_unbound")}</span> : null}
            </button>
          );
        })}
      </div>
    </Modal>
  );
}
