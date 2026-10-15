// Parametr yonidagi kichik «?» tugmasi: «Справка» ning shu parametr bandini ochadi (kontekst yordami).
import { useTranslation } from "react-i18next";
import { openHelp, type HelpTopic } from "./helpStore";
import "./help.css";

export function HelpTip({ topic, id }: { topic: HelpTopic; id: string }) {
  const { t } = useTranslation();
  return (
    <button type="button" className="helptip" title={t("help.about_param")} aria-label={t("help.about_param")}
      data-testid={`helptip-${topic}-${id}`}
      onMouseDown={(e) => e.stopPropagation()}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); openHelp(topic, id); }}>?</button>
  );
}

/** Maydon yorlig'i + «?» (Field.label uchun). */
export function Lbl({ text, topic, id }: { text: string; topic: HelpTopic; id: string }) {
  return <>{text}<HelpTip topic={topic} id={id} /></>;
}
