// «Справка»: klaviatura yorliqlari, ish oqimi, formulalar, MES.
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import { HOTKEYS } from "../../shared/hotkeys";
import { cx } from "../../shared/ui";

type Topic = "keys" | "flow" | "cut" | "edge" | "mes" | "about";
const useTopic = create<{ t: Topic; set: (t: Topic) => void }>((set) => ({ t: "keys", set: (t) => set({ t }) }));

export function HelpMenu() {
  const { t } = useTranslation();
  const { t: topic, set } = useTopic();
  return (
    <div className="side-menu">
      {(["keys", "flow", "cut", "edge", "mes", "about"] as Topic[]).map((k) => (
        <button key={k} type="button" className={cx("side-item", topic === k && "side-item-active")} onClick={() => set(k)}>
          {t(`help.topic.${k}`)}</button>
      ))}
    </div>
  );
}

export function HelpView() {
  const { t } = useTranslation();
  const topic = useTopic((s) => s.t);
  return (
    <div className="page">
      <div className="page-head"><h2>{t(`help.topic.${topic}`)}</h2></div>
      <div className="scroll doc" data-testid="help">
        {topic === "keys" && (
          <>
            <table className="simple keys">
              <thead><tr><th>{t("help.key")}</th><th>{t("help.action")}</th></tr></thead>
              <tbody>{HOTKEYS.map((h) => <tr key={h.keys}><td><kbd>{h.keys}</kbd></td><td>{t(`help.hk.${h.action}`)}</td></tr>)}</tbody>
            </table>
            <p className="muted">{t("help.keys_note")}</p>
          </>
        )}
        {topic !== "keys" && <div className="help-text">{t(`help.text.${topic}`)}</div>}
      </div>
    </div>
  );
}
