// Interfeys tillari: ru — rus (+ xodimlarning o'zbekcha ustun nomlari), uz — o'zbekcha (lotin), uz-Cyrl — o'zbekcha (kirill).
// uz-Cyrl — o'sha o'zbek tili, faqat yozuvi boshqa: hamma `lang === "uz"` tekshiruvlari `isUz()` orqali ikkalasini qamraydi.
import { toCyrillic } from "./translit";

export type Lang = "ru" | "uz" | "uz-Cyrl";
export const LANGS: Lang[] = ["ru", "uz-Cyrl", "uz"];

/** Til tanlovidagi nomlar (har biri o'z tilida). */
export const LANG_LABEL: Record<Lang, string> = {
  ru: "Русский (+ ўзбекча устунлар)",
  "uz-Cyrl": "Ўзбекча (кирилл)",
  uz: "O'zbekcha (lotin)",
};

export const isLang = (v: unknown): v is Lang => v === "ru" || v === "uz" || v === "uz-Cyrl";
/** O'zbekcha (lotin yoki kirill). */
export const isUz = (l: string | undefined | null): boolean => !!l && l.toLowerCase().startsWith("uz");
export const isCyrl = (l: string | undefined | null): boolean => !!l && l.toLowerCase() === "uz-cyrl";

/** Serverdan keladigan o'zbekcha (lotin) matnni joriy yozuvga moslash: uz-Cyrl da kirillga o'giriladi. */
export const uzScript = (s: string, lang: string | undefined | null): string => (isCyrl(lang) ? toCyrillic(s) : s);

/** {ru, uz} juftligidan joriy til matni (uz-Cyrl — uz ning kirill ko'rinishi). */
export function pickLang(lang: string | undefined | null, ru: string, uz: string): string {
  return isUz(lang) ? uzScript(uz, lang) : ru;
}

/** Hisobot / etiketka tili tanlovi (Печать, Этикетки) — serverga `lang` sifatida yuboriladi. */
export const PRINT_LANGS: { value: Lang; label: string }[] = [
  { value: "ru", label: "Русский" }, { value: "uz-Cyrl", label: "Ўзбекча" }, { value: "uz", label: "O'zbekcha" },
];
