import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { DialogHost, Toasts } from "../shared/dialogs";
import { Busy } from "../shared/ui";
import { useBusy, useProject } from "../api/hooks";
import { useUI } from "../store/ui";
import { Layout } from "./Layout";

export function App() {
  const busy = useBusy((s) => s.busy);
  const { t } = useTranslation();
  const projectId = useUI((s) => s.projectId);
  const q = useProject(projectId);
  // saqlangan loyiha o'chirilgan bo'lsa — ro'yxatga qaytish
  useEffect(() => {
    if (projectId && q.isError) useUI.getState().openProject(null);
  }, [projectId, q.isError]);
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
