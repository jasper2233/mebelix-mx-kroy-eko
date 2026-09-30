// Loyiha sarlavhasi: Наименование, Валюта (+ standart sifatida saqlash), sanalar, izoh, yopish.
import { useTranslation } from "react-i18next";
import { Save, X } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { AppSettings, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Area, IconBtn, Txt } from "../../shared/ui";

export function Header({ project }: { project: Project }) {
  const { t } = useTranslation();
  const upd = (fields: Partial<Project>) => void call(() => patch(`/projects/${project.id}`, fields));
  const saveCurrency = async () => {
    const cur = qc.getQueryData<AppSettings>(["defaults", "app"]);
    const r = await call(() => put("/settings/app/default", { ...(cur ?? {}), currency: project.currency }));
    if (r) {
      void qc.invalidateQueries({ queryKey: ["defaults", "app"] });
      useUI.getState().toast(t("header.currency_saved", { cur: project.currency }), "ok");
    }
  };
  return (
    <div className="phead" data-testid="project-header">
      <div className="phead-grid">
        <label className="phead-l">{t("header.name")}</label>
        <div className="phead-row">
          <div className="phead-name"><Txt value={project.name} onCommit={(v) => upd({ name: v })} width="100%" testid="project-name" /></div>
          <label className="phead-l2">{t("header.customer")}</label>
          <Txt value={project.customer} onCommit={(v) => upd({ customer: v })} width={200} />
        </div>
        <label className="phead-l">{t("header.currency")}</label>
        <div className="phead-row">
          <Txt value={project.currency} onCommit={(v) => upd({ currency: v.toUpperCase() })} width={64} maxLength={5} />
          <IconBtn icon={Save} title={t("header.save_currency")} onClick={() => void saveCurrency()} />
          <label className="phead-l2">{t("header.order_date")}</label>
          <input type="date" className="inp" value={project.order_date}
            onChange={(e) => e.target.value && upd({ order_date: e.target.value })} />
          <label className="phead-l2">{t("header.ready_date")}</label>
          <input type="date" className="inp" value={project.ready_date}
            onChange={(e) => e.target.value && upd({ ready_date: e.target.value })} />
          <span className="phead-num">№ {project.number}{project.mes_order_ref ? ` · MES ${project.mes_order_ref}` : ""}</span>
        </div>
      </div>
      <div className="phead-note"><Area value={project.note} rows={2} placeholder={t("header.note")}
        onCommit={(v) => upd({ note: v })} /></div>
      <button type="button" className="phead-close" title={t("menu.close_project")} data-testid="close-project"
        onClick={() => useUI.getState().openProject(null)}><X size={18} /></button>
    </div>
  );
}
