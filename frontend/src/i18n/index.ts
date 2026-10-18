import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ru from "./ru.json";
import uz from "./uz.json";
import uzCyrl from "./uz-Cyrl.json";
import { useUI } from "../store/ui";
import { isUz } from "./lang";

// Standart til — rus yorliqlari + xodimlar odatlangan o'zbekcha ustun nomlari; sozlamada to'liq o'zbekcha (lotin yoki kirill).
// uz-Cyrl.json — uz.json dan avtomatik (scripts/i18n_src.py, backend/app/uz_translit.py).
void i18n.use(initReactI18next).init({
  resources: { ru: { translation: ru }, uz: { translation: uz }, "uz-Cyrl": { translation: uzCyrl } },
  lng: useUI.getState().lang,
  fallbackLng: { "uz-Cyrl": ["ru"], default: ["ru"] },
  load: "currentOnly",
  interpolation: { escapeValue: false },
  returnNull: false,
});

// <html lang> — til almashganda ham to'g'ri (ekran o'qiydigan dasturlar, orfografiya uchun): uz-Cyrl / uz-Latn / ru
const applyLang = (l: string) => {
  if (typeof document !== "undefined") document.documentElement.lang = l === "uz-Cyrl" ? "uz-Cyrl" : isUz(l) ? "uz" : "ru";
};
applyLang(useUI.getState().lang);

useUI.subscribe((s, prev) => {
  if (s.lang !== prev.lang) { void i18n.changeLanguage(s.lang); applyLang(s.lang); }
});

export default i18n;
