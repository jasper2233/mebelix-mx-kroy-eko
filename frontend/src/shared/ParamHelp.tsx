// Parametr yordami oynasi (kontekst): matn o'zimiz yozgan, ru/uz (i18n `phelp.<kalit>`).
import { useTranslation } from "react-i18next";
import { useUI } from "../store/ui";
import { Btn, Modal } from "./ui";
import { useParamHelp } from "./paramHelpStore";
import "./ParamHelp.css";

export function ParamHelpHost() {
  const { t, i18n } = useTranslation();
  const key = useParamHelp((s) => s.key);
  const close = useParamHelp((s) => s.close);
  if (!key) return null;
  const titleKey = [`phelp_t.${key}`, `cs.p.${key}`].find((k) => i18n.exists(k));
  return (
    <Modal title={titleKey ? t(titleKey) : key} onClose={close} width={480} testid="param-help"
      footer={<>
        <Btn label={t("phelp.open_help")} onClick={() => { close(); useUI.getState().set({ section: "help" }); }} />
        <Btn kind="primary" label={t("app.ok")} onClick={close} testid="param-help-ok" />
      </>}>
      <p className="help-text" data-testid="param-help-text">{i18n.exists(`phelp.${key}`) ? t(`phelp.${key}`) : t("phelp.none")}</p>
    </Modal>
  );
}
