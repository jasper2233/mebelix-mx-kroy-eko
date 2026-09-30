import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ru from "./ru.json";
import uz from "./uz.json";
import { useUI } from "../store/ui";

// Standart til — rus yorliqlari + xodimlar odatlangan o'zbekcha ustun nomlari; sozlamada to'liq o'zbekcha.
void i18n.use(initReactI18next).init({
  resources: { ru: { translation: ru }, uz: { translation: uz } },
  lng: useUI.getState().lang,
  fallbackLng: "ru",
  interpolation: { escapeValue: false },
  returnNull: false,
});

useUI.subscribe((s, prev) => {
  if (s.lang !== prev.lang) void i18n.changeLanguage(s.lang);
});

export default i18n;
