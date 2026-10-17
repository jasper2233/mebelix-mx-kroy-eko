import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import i18n from "i18next";
import { DialogHost, Toasts, showError } from "../shared/dialogs";
import { ApiError, get } from "../api/client";
import { Busy } from "../shared/ui";
import { useAppSettings, useBusy, useProject } from "../api/hooks";
import { useUI } from "../store/ui";
import { Layout } from "./Layout";

export function App() {
  const busy = useBusy((s) => s.busy);
  const { t } = useTranslation();
  const projectId = useUI((s) => s.projectId);
  const q = useProject(projectId);
  const appSettings = useAppSettings();
  // yangi brauzerda (til hali tanlanmagan) — serverdagi umumiy sozlama tili
  useEffect(() => {
    const lang = appSettings.data?.language;
    if (!lang || (lang !== "ru" && lang !== "uz")) return;
    let chosen = true;
    try { chosen = localStorage.getItem("mxk_lang") !== null; } catch { /* yo'q */ }
    if (!chosen && lang !== useUI.getState().lang) useUI.getState().setLang(lang);
  }, [appSettings.data]);
  // saqlangan loyiha o'chirilgan bo'lsa — ro'yxatga qaytish
  useEffect(() => {
    if (!(projectId && q.isError)) return;
    // jim emas: loyiha topilmadi (o'chirilgan) — ma'lumot, boshqa xato (server / tarmoq) — xato xabarnomasi
    const e = q.error;
    if (e instanceof ApiError && e.status === 404) useUI.getState().toast(i18n.t("projects.not_found"), "info");
    else showError(e);
    useUI.getState().openProject(null);
  }, [projectId, q.isError, q.error]);
  useEffect(() => {
    document.title = q.data ? `${q.data.name} — MebeliX Kroy` : "MebeliX Kroy";
  }, [q.data]);
  // #/sex — sex (planshet) rejimi; #/p/<id> — shu loyiha ochiladi (manzil localStorage dagi oxirgi loyihadan ustun).
  // <id> — loyiha id si yoki raqami (1000013): raqam bo'lsa ro'yxatdan qidiriladi; topilmasa — «Проект не найден» (pastdagi effekt)
  useEffect(() => {
    const h = () => {
      const hash = window.location.hash;
      if (hash === "#/sex") { useUI.getState().set({ view: "workshop" }); return; }
      const m = /^#\/p\/([^/?#]+)/.exec(hash);
      if (!m) return;
      const key = decodeURIComponent(m[1]).trim();
      const open = (id: string) => { if (id !== useUI.getState().projectId || useUI.getState().view !== "main") useUI.getState().openProject(id); };
      if (/^\d{1,9}$/.test(key)) {
        void get<{ id: string; number: number }[]>("/projects", { q: key })
          .then((rows) => open(rows.find((r) => r.number === Number(key))?.id ?? key))
          .catch(() => open(key));
      } else open(key);
    };
    h();
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  // ochiq loyiha manzilda ko'rinadi (#/p/<id>) — havolani nusxalab yuborish / yangilash (F5) shu loyihani ochadi.
  // replaceState — hashchange chaqirilmaydi; birinchi chizishda yozilmaydi (manzildagi loyiha hali ochilayotgan bo'lishi mumkin)
  const firstSync = useRef(true);
  useEffect(() => {
    if (firstSync.current) { firstSync.current = false; return; }
    const hash = window.location.hash;
    if (hash === "#/sex") return;
    const want = projectId ? `#/p/${encodeURIComponent(projectId)}` : "";
    if (hash === want || (!want && !hash.startsWith("#/p/"))) return;
    try { window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}${want}`); } catch { /* yo'q */ }
  }, [projectId]);
  return (
    <>
      <Layout />
      <DialogHost />
      <Toasts />
      {busy && <div className="busy-back"><Busy text={busy || t("app.loading")} /></div>}
    </>
  );
}
