// Loyiha sarlavhasi: Наименование, Валюта (+ standart sifatida saqlash), sanalar, izoh, yopish.
// Joylashuv xodimlar o'rgangandek: «Наименование» — chapda, uzun maydon; 2-qatorda «Валюта», «Дата заказа», «Дата готовности» yozuvlari
// maydonlar USTIDA, sanalar nom maydoni boshlanadigan joydan boshlanadi.
import { useTranslation } from "react-i18next";
import { parseIsoDate, weekdayShort } from "../../shared/dates";
import { Save, TriangleAlert, X } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { patch, put } from "../../api/client";
import type { AppSettings, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Area, IconBtn, Txt, cx } from "../../shared/ui";
import { StatusBadge } from "../order/StatusBadge";
import { useOrderState } from "../order/orderApi";
import "./pprog.css";
import "./header.css";

export function Header({ project }: { project: Project }) {
  const { t, i18n } = useTranslation();
  // mahsulot dasturlari (W12): Err (cheklov buzildi) va xatolar — sarlavhada ogohlantirish belgisi
  const issues = project.products.flatMap((p) => p.prog_messages ?? []).filter((m) => m.level !== "info");
  const progErrors = issues.filter((m) => m.level === "error").length;
  const st = useOrderState(project, project.status >= 2).data;      // faqat «Утвержден»/«Готов» da: bloklanish holati
  // Promise qaytaradi: `Txt` server rad etganda (masalan bo'sh valyuta — 400) maydonni saqlangan qiymatga qaytaradi (#17)
  const upd = (fields: Partial<Project>) => call(() => patch(`/projects/${project.id}`, fields));
  // Sanalar: «Дата готовности» «Дата заказа» dan oldin bo'lmaydi — ogohlantirish va buyurtma sanasiga tenglashtirish
  const setDate = (k: "order_date" | "ready_date", v: string) => {
    if (!v) return;
    const f: Partial<Project> = { [k]: v };
    const order = k === "order_date" ? v : project.order_date;
    const ready = k === "ready_date" ? v : project.ready_date;
    if (order && ready && ready < order) { f.ready_date = order; useUI.getState().toast(t("header.ready_before_order"), "info"); }
    void upd(f);
  };
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
          <span className="phead-flags">
            <StatusBadge status={project.status} testid="project-status" />
            {project.status >= 2 && (
              <span className={st?.lock.active ? "ord-chip ord-chip-lock" : "ord-chip"} data-testid="order-edit-warn"
                title={t("order.edit_warn_title", { status: t(`status.${project.status}`) })}>
                {st?.lock.active ? t("order.edit_locked", { status: t(`status.${project.status}`) }) : t("order.edit_warn")}
              </span>
            )}
          </span>
        </div>
        <div className="phead-stack">
          <label className="phead-l">{t("header.currency")}</label>
          <div className="phead-row">
            <Txt value={project.currency} onCommit={(v) => upd({ currency: v.toUpperCase() })} width={64} maxLength={5} testid="project-currency" />
            <IconBtn icon={Save} title={t("header.save_currency")} onClick={() => void saveCurrency()} />
          </div>
        </div>
        <div className="phead-row phead-row2">
          <div className="phead-stack">
            <label className="phead-l">{t("header.order_date")}</label>
            <div className="phead-row">
              <span className="wd">{weekday(project.order_date, i18n.language)}</span>
              <input type="date" className="inp" value={project.order_date} data-testid="order-date"
                onChange={(e) => setDate("order_date", e.target.value)} />
            </div>
          </div>
          <div className="phead-stack">
            <label className="phead-l">{t("header.ready_date")}</label>
            <div className="phead-row">
              <span className="wd">{weekday(project.ready_date, i18n.language)}</span>
              <input type="date" className="inp" value={project.ready_date} min={project.order_date || undefined} data-testid="ready-date"
                onChange={(e) => setDate("ready_date", e.target.value)} />
            </div>
          </div>
          {issues.length > 0 && (
            <button type="button" className={cx("phead-warn", progErrors > 0 && "err")} data-testid="phead-prog-warn"
              title={t("header.prog_warn", { e: progErrors, w: issues.length - progErrors })}
              onClick={() => useUI.getState().set({ topTab: "products" })}><TriangleAlert size={13} /> {issues.length}</button>
          )}
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

/** Hafta kuni qisqa nomi («сб» / «Sh»): sana oldida («сб 26.09.2026»). */
function weekday(iso: string | undefined, lang: string): string {
  const d = parseIsoDate(iso);
  return d ? weekdayShort(d, lang) : "";
}
