// «Печать отчета» (UI_SPEC §8): profil, bo'limlar sozlamasi, ko'rish (A4), chop etish / PDF; etiketkalar.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import { ExternalLink, Pencil, Plus, Printer, RefreshCw, Save, Trash } from "lucide-react";
import { call, qc, useDefaults, useProfiles, useProject } from "../../api/hooks";
import { del, fetchHtml, post, put, showHtml } from "../../api/client";
import type { LabelSettings, PrintSettings, Profile } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, Check, Empty, Field, IconBtn, Modal, Num, Sel, Tabs, cx } from "../../shared/ui";
import { xncDuplicates } from "../project/xncCodes";
import { CsPrintExtras, MapsPrintExtras } from "./PrintCsExtra";       // W2: (CS) qo'shimcha chop sozlamalari
import { LabelsPrint } from "./LabelsPanel";                           // W4: «Этикетки» bo'limi (LB parametrlari + shablon + A4 karta miniatyurasi)

type Sec = "general" | "cs" | "cn" | "cl" | "maps" | "header" | "el" | "sp" | "gr" | "xnc" | "o" | "labels";
/** Sozlamalar oynasi (GibLab kabi: chap menyudagi havola → oyna; «Ок» qo'llaydi, «Отмена» qaytaradi). */
type Dlg = "margins" | "general" | "products" | "cs" | "cn" | "cl" | "el" | "sp" | "gr" | "xnc" | "o";

interface PState {
  profile: number | null; sec: Sec; lang: "ru" | "uz"; draft: PrintSettings | null; labels: LabelSettings | null;
  labelOp: string; stamp: number; dlg: Dlg | null; set: (p: Partial<PState>) => void;
}
const usePrint = create<PState>((set) => ({
  profile: null, sec: "general", lang: "ru", draft: null, labels: null, labelOp: "", stamp: 0, dlg: null, set: (p) => set(p),
}));

const HEADER_FIELDS = ["N", "S", "C", "Cp", "LT", "CT", "F", "AP", "AM", "AW", "PK"];
const recodeAsked = new Set<string>();       // XNC kodlarini qayta kodlash so'ralgan loyihalar (sessiya davomida)

export function PrintMenu() {
  const { t } = useTranslation();
  const ps = usePrint();
  const profiles = useProfiles<PrintSettings>("print");
  const list: Profile<PrintSettings>[] = profiles.data ?? [];
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "print"] });
  const ops: Dlg[] = ["cs", "cl", "cn", "el", "sp", "gr", "xnc", "o"];
  const link = (d: Dlg, label: string) => (
    <button key={d} type="button" className="side-item" onClick={() => ps.set({ dlg: d, sec: ps.sec === "labels" ? "general" : ps.sec })}
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
      <div className="side-label">{t("print.language")}</div>
      <Sel value={ps.lang} width="100%" onChange={(v) => ps.set({ lang: v, stamp: ps.stamp + 1 })}
        options={[{ value: "ru", label: "Русский" }, { value: "uz", label: "O'zbekcha" }]} />
      <div className="side-gap" />
      {link("margins", t("print.dlg.margins"))}
      {link("general", t("print.dlg.general"))}
      {link("products", t("print.dlg.products"))}
      <div className="side-label">{t("print.ops_settings")}</div>
      {ops.map((d) => link(d, t(d === "cs" ? "print.sec.cs_main" : `print.sec.${d}`)))}
      <button type="button" className={cx("side-item", ps.sec === "labels" && "side-item-active")}
        onClick={() => ps.set({ sec: ps.sec === "labels" ? "general" : "labels" })} data-testid="print-sec-labels">{t("print.sec.labels")}</button>
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
  const [csTab, setCsTab] = useState<"cs" | "maps" | "header">("cs");
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
    const q = labelsMode
      ? fetchHtml(`/projects/${pid}/labels`, { lang: ps.lang, op_id: ps.labelOp || undefined }, ls)
      : fetchHtml(`/projects/${pid}/report`, { lang: ps.lang }, s);
    q.then((h) => { if (alive) setHtml(h); }).catch(() => undefined).finally(() => alive && setLoading(false));
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
  if (labelsMode) return <LabelsPrint />;          // W4: eski qat'iy shakl (quyidagi `labelsMode` bloki) endi ishlatilmaydi
  const upd = (f: Partial<PrintSettings>) => ps.set({ draft: { ...s, ...f } });
  const chk = (k: keyof PrintSettings, label?: string) => (
    <Check key={k} checked={Boolean(s[k])} label={label ?? t(`print.f.${k}`)} onChange={(v) => upd({ [k]: v } as Partial<PrintSettings>)}
      testid={`pf-${k}`} />
  );
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
  const body = (d: Dlg) => {
    switch (d) {
      case "margins": return (["left", "right", "top", "bottom"] as const).map((k) => {
        const key = `page_margin_${k}` as const;
        return <Field key={k} label={t(`print.margin.${k}`)} unit={t("u.mm")}>
          <Num value={s[key] ?? (k === "top" ? 8 : 10)} min={0} max={50} testid={`print-margin-${k}`}
            onCommit={(v) => upd({ [key]: v ?? (k === "top" ? 8 : 10) } as Partial<PrintSettings>)} /></Field>;
      });
      case "general": return <>{chk("header")}{chk("materials_list")}{chk("warehouse")}{chk("warehouse_cut_work")}
        {chk("warehouse_edge_work")}{chk("operations")}{chk("xnc_stats")}</>;
      case "products": return chk("products_list");
      case "cs": return <>
        <Tabs<"cs" | "maps" | "header"> value={csTab} onChange={setCsTab} tabs={[
          { key: "cs", label: t("print.cstab.cs") }, { key: "maps", label: t("print.cstab.maps") },
          { key: "header", label: t("print.cstab.header") }]} />
        {csTab === "cs" && <div className="checks-col">
          {chk("cs_parts")}{chk("cs_unplaced")}{chk("cs_sheets")}{chk("cs_remnants")}{chk("cs_maps")}{chk("cs_commands")}
          <Field label={t("print.f.cs_size_mode")}>
            <Sel<string> value={s.cs_size_mode ?? ""} width={200} onChange={(v) => upd({ cs_size_mode: (v || null) as PrintSettings["cs_size_mode"] })}
              options={[{ value: "", label: t("print.project_mode") }, { value: "blank", label: t("sizemode.blank") },
                { value: "detail", label: t("sizemode.detail") }, { value: "jointed", label: t("sizemode.jointed") }]} /></Field>
          <CsPrintExtras s={s} upd={upd} />
        </div>}
        {csTab === "maps" && <div className="checks-col">
          {chk("map_parts_list")}{chk("map_edges")}{chk("map_remnant_number")}{chk("map_qr")}{chk("map_mirror")}
          <Field label={t("print.f.map_part_label")}>
            <Sel value={s.map_part_label} width={200} onChange={(v) => upd({ map_part_label: v })}
              options={(["number", "name", "number_name"] as const).map((v) => ({ value: v, label: t(`print.label.${v}`) }))} /></Field>
          <MapsPrintExtras s={s} upd={upd} />
        </div>}
        {csTab === "header" && <div className="checks-col">
          <p className="muted">{t("print.header_hint")}</p>
          {HEADER_FIELDS.map((f) => (
            <Check key={f} checked={s.map_header_fields.includes(f)} label={`${f} — ${t(`print.hf.${f}`)}`}
              onChange={(v) => upd({ map_header_fields: v ? HEADER_FIELDS.filter((x) => x === f || s.map_header_fields.includes(x))
                : s.map_header_fields.filter((x) => x !== f) })} />
          ))}
        </div>}
      </>;
      case "el": return <>{chk("el_params")}{chk("el_parts")}{chk("el_header_work")}{chk("el_header_material")}</>;
      case "cn": return <div data-testid="print-cn-form">{chk("cn_params")}{chk("cn_parts")}{chk("cn_unplaced")}{chk("cn_sheets")}
        {chk("cn_remnants")}{chk("cn_maps")}</div>;
      case "cl": return <div data-testid="print-cl-form">{chk("cl_header")}{chk("cl_parts")}{chk("cl_group_by_product")}{chk("cl_unplaced")}
        {chk("cl_strips")}{chk("cl_remnants")}{chk("cl_maps")}{chk("cl_commands")}</div>;
      case "sp": return <>{chk("sp_params")}{chk("sp_parts")}</>;
      case "gr": return <>{chk("gr_params")}{chk("gr_parts")}</>;
      case "xnc": return <>{chk("xnc_drawing")}{chk("xnc_stats")}</>;
      case "o": return <>{chk("o_params")}{chk("o_materials")}</>;
    }
  };
  const dlgTitle = (d: Dlg) => (d === "margins" || d === "general" || d === "products") ? t(`print.dlg.${d}`)
    : t(d === "cs" ? "print.sec.cs_main" : `print.sec.${d}`);
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
        <Modal title={dlgTitle(ps.dlg)} onClose={() => closeDlg(false)} width={ps.dlg === "cs" ? 620 : 460} testid="print-form"
          footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => closeDlg(true)} testid="print-dlg-ok" />
            <Btn label={t("app.cancel")} onClick={() => closeDlg(false)} /></>}>
          <div className="checks-col print-dlg">{body(ps.dlg)}</div>
        </Modal>
      )}
    </div>
  );
}
