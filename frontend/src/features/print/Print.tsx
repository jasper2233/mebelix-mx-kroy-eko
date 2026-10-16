// «Печать отчета» (UI_SPEC §8, X_1015 §11): chap panel — «Профиль» (+ ✚ ✎ ✕), «Поля страницы», «Настройки печати», «Изделия»,
// «Настройки печати операций» (CS, CL, CN, EL, SP, XNC) + bizning (GR), (O), «Этикетки» va «Язык отчёта»; o'ngda hisobot (A4 iframe),
// chop etish / PDF. Har sozlama oynasi — «Параметр | Значение» jadvali (printDialogs.tsx); «Ок» qo'llaydi, «Отмена» qaytaradi.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import { ExternalLink, Pencil, Plus, Printer, RefreshCw, Save, Trash } from "lucide-react";
import { call, qc, useDefaults, useProfiles, useProject } from "../../api/hooks";
import { del, fetchHtml, post, put, showHtml } from "../../api/client";
import type { LabelSettings, PrintSettings, Profile } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, Empty, IconBtn, Modal, Sel, cx } from "../../shared/ui";
import { xncDuplicates } from "../project/xncCodes";
import { DLG_WIDTH, PrintDialogBody, dlgTitle, type Dlg } from "./printDialogs";
import { LabelsPrint } from "./LabelsPanel";                           // W4: «Этикетки» bo'limi (LB parametrlari + shablon + A4 karta miniatyurasi)

type Sec = "general" | "labels";

interface PState {
  profile: number | null; sec: Sec; lang: "ru" | "uz"; draft: PrintSettings | null; labels: LabelSettings | null;
  labelOp: string; stamp: number; dlg: Dlg | null; set: (p: Partial<PState>) => void;
}
/** Chop bo'limi holati; `sec: "labels"` — «Этикетки» (CS «Раскрой» → «Этикетки деталей (QR)» tugmasi shu bo'limni ochadi). */
export const usePrint = create<PState>((set) => ({
  profile: null, sec: "general", lang: "ru", draft: null, labels: null, labelOp: "", stamp: 0, dlg: null, set: (p) => set(p),
}));

const recodeAsked = new Set<string>();       // XNC kodlarini qayta kodlash so'ralgan loyihalar (sessiya davomida)
/** Operatsiya oynalari — xodimlar o'rgangan tizim tartibida; (GR) va (O) — bizning qo'shimchalar (oxirida). */
const OPS: Dlg[] = ["cs", "cl", "cn", "el", "sp", "xnc", "gr", "o"];

export function PrintMenu() {
  const { t } = useTranslation();
  const ps = usePrint();
  const profiles = useProfiles<PrintSettings>("print");
  const list: Profile<PrintSettings>[] = profiles.data ?? [];
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "print"] });
  const link = (d: Dlg, label: string) => (
    <button key={d} type="button" className="side-item" onClick={() => ps.set({ dlg: d, sec: "general" })}
      data-testid={`print-dlg-${d}`}>{label}</button>
  );
  return (
    <div className="side-menu">
      <div className="side-label">{t("print.profile")}</div>
      <div className="row gap">
        <Sel<string> value={ps.profile === null ? "" : String(ps.profile)} width="100%" testid="print-profile"
          onChange={(v) => ps.set({ profile: v ? Number(v) : null, draft: null })}
          options={[{ value: "", label: t("print.standard") }, ...list.map((p) => ({ value: String(p.id), label: p.name }))]} />
      </div>
      <div className="row gap side-icons">
        <IconBtn icon={Plus} title={t("print.new_profile")} onClick={async () => {
          const n = await askText(t("print.new_profile"), t("print.profile_name"));
          if (!n) return;
          const r = await call(() => post<Profile<PrintSettings>>("/settings/print", { name: n, data: ps.draft ?? undefined }));
          if (r) { await refresh(); ps.set({ profile: r.id, draft: null }); }
        }} />
        <IconBtn icon={Pencil} title={t("menu.rename")} disabled={ps.profile === null} onClick={async () => {
          const cur = list.find((p) => p.id === ps.profile);
          const n = await askText(t("menu.rename"), cur?.name ?? "");
          if (n && ps.profile !== null) { await call(() => put(`/settings/print/${ps.profile}`, { name: n })); await refresh(); }
        }} />
        <IconBtn icon={Trash} title={t("app.delete")} disabled={ps.profile === null} onClick={async () => {
          if (ps.profile === null || !(await askConfirm(t("print.delete_q")))) return;
          await call(() => del(`/settings/print/${ps.profile}`)); await refresh(); ps.set({ profile: null, draft: null });
        }} />
      </div>
      <div className="side-gap" />
      {link("margins", t("print.dlg.margins"))}
      {link("general", t("print.dlg.general"))}
      {link("products", t("print.dlg.products"))}
      <div className="side-label">{t("print.ops_settings")}</div>
      {OPS.map((d) => link(d, t(d === "cs" ? "print.sec.cs_main" : `print.sec.${d}`)))}
      <button type="button" className={cx("side-item", ps.sec === "labels" && "side-item-active")}
        onClick={() => ps.set({ sec: ps.sec === "labels" ? "general" : "labels" })} data-testid="print-sec-labels">{t("print.sec.labels")}</button>
      <div className="side-gap" />
      <div className="side-label">{t("print.language")}</div>
      <Sel value={ps.lang} width="100%" onChange={(v) => ps.set({ lang: v, stamp: ps.stamp + 1 })}
        options={[{ value: "ru", label: "Русский" }, { value: "uz", label: "O'zbekcha" }]} />
    </div>
  );
}

export function PrintView() {
  const { t } = useTranslation();
  const pid = useUI((s) => s.projectId);
  const project = useProject(pid);
  const ps = usePrint();
  const profiles = useProfiles<PrintSettings>("print");
  const defaults = useDefaults<PrintSettings>("print");
  const labelDefaults = useDefaults<LabelSettings>("labels");
  const frame = useRef<HTMLIFrameElement>(null);
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const opened = useRef<PrintSettings | null | undefined>(undefined);       // oyna ochilgandagi draft («Отмена» uchun)
  useEffect(() => { if (ps.dlg) opened.current = usePrint.getState().draft; }, [ps.dlg]);
  const base: PrintSettings | undefined = ps.profile !== null
    ? { ...(defaults.data as PrintSettings), ...(profiles.data?.find((p) => p.id === ps.profile)?.data ?? {}) }
    : defaults.data;
  const s = ps.draft ?? base;
  const ls = ps.labels ?? labelDefaults.data;
  const labelsMode = ps.sec === "labels";

  useEffect(() => {
    if (!pid || !s || labelsMode) return;          // «Этикетки» — LabelsPrint (o'z ko'rishi)
    let alive = true;
    setLoading(true);
    fetchHtml(`/projects/${pid}/report`, { lang: ps.lang }, s)
      .then((h) => { if (alive) setHtml(h); }).catch(() => undefined).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [pid, JSON.stringify(s), JSON.stringify(ls), ps.lang, labelsMode, ps.labelOp, ps.stamp, project.data]); // eslint-disable-line react-hooks/exhaustive-deps

  // bir xil kodli XNC dasturlar bo'lsa — hisobotdan oldin bir marta so'raladi (har loyiha uchun)
  useEffect(() => {
    if (!pid || !project.data || recodeAsked.has(pid)) return;
    const n = xncDuplicates(project.data);
    if (n === 0) return;
    recodeAsked.add(pid);
    void askConfirm(t("print.recode_q", { n }), t("print.recode_text"), { ok: t("common.recode_xnc_ok") })
      .then((ok) => { if (ok) void call(() => post(`/projects/${pid}/actions/recode-xnc`)); });
  }, [pid, project.data]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!pid || !project.data) return <Empty>{t("print.open_project")}</Empty>;
  if (!s) return <Empty>{t("app.loading")}</Empty>;
  if (labelsMode) return <LabelsPrint />;
  const upd = (f: Partial<PrintSettings>) => ps.set({ draft: { ...(usePrint.getState().draft ?? s), ...f } });
  const saveProfile = async () => {
    if (ps.profile === null) {
      const r = await call(() => put("/settings/print/default", s));
      if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "print"] }); ps.set({ draft: null }); useUI.getState().toast(t("app.saved"), "ok"); }
    } else {
      const r = await call(() => put(`/settings/print/${ps.profile}`, { data: s }));
      if (r) { void qc.invalidateQueries({ queryKey: ["profiles", "print"] }); ps.set({ draft: null }); useUI.getState().toast(t("app.saved"), "ok"); }
    }
  };
  const doPrint = () => { frame.current?.contentWindow?.focus(); frame.current?.contentWindow?.print(); };
  const openWin = () => { if (html) showHtml(html); };
  const closeDlg = (ok: boolean) => ps.set(ok ? { dlg: null } : { dlg: null, draft: opened.current ?? null });
  return (
    <div className="print">
      <div className="print-preview">
        <div className="toolbar">
          <Btn icon={Printer} kind="primary" label={t("print.print")} onClick={doPrint} testid="print-btn" />
          <Btn icon={ExternalLink} label={t("print.open")} onClick={openWin} />
          <IconBtn icon={RefreshCw} title={t("menu.refresh")} onClick={() => ps.set({ stamp: ps.stamp + 1 })} />
          <IconBtn icon={Save} title={t("print.save_profile")} onClick={() => void saveProfile()} disabled={!ps.draft} />
          {loading && <span className="muted">{t("app.loading")}</span>}
          <span className="grow" />
          <span className="muted">{t("print.pdf_hint")}</span>
        </div>
        <iframe ref={frame} title="report" className="report-frame" srcDoc={html} data-testid="report-frame"
          sandbox="allow-same-origin allow-modals" />
      </div>
      {ps.dlg && (
        <Modal title={dlgTitle(ps.dlg, t)} onClose={() => closeDlg(false)} width={DLG_WIDTH[ps.dlg]} testid="print-form"
          footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => closeDlg(true)} testid="print-dlg-ok" />
            <Btn label={t("app.cancel")} onClick={() => closeDlg(false)} testid="print-dlg-cancel" /></>}>
          <div className="print-dlg-body"><PrintDialogBody dlg={ps.dlg} s={s} upd={upd} /></div>
        </Modal>
      )}
    </div>
  );
}
