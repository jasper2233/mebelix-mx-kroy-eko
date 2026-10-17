import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import i18n from "i18next";
import { DialogHost, Toasts, showError } from "../shared/dialogs";
import { ApiError } from "../api/client";
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
  // #/sex — sex (planshet) rejimi
  useEffect(() => {
    const h = () => { if (window.location.hash === "#/sex") useUI.getState().set({ view: "workshop" }); };
    h();
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  return (
    <>
      <Layout />
      <DialogHost />
      <Toasts />
      {busy && <div className="busy-back"><Busy text={busy || t("app.loading")} /></div>}
    </>
  );
}
