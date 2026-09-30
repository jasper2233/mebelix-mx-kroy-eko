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
import { Btn, Check, Empty, Field, IconBtn, Num, Sel, cx } from "../../shared/ui";

type Sec = "general" | "cs" | "maps" | "header" | "el" | "xnc" | "labels";

interface PState {
  profile: number | null; sec: Sec; lang: "ru" | "uz"; draft: PrintSettings | null; labels: LabelSettings | null;
  labelOp: string; stamp: number; set: (p: Partial<PState>) => void;
}
const usePrint = create<PState>((set) => ({
  profile: null, sec: "general", lang: "ru", draft: null, labels: null, labelOp: "", stamp: 0, set: (p) => set(p),
}));

const HEADER_FIELDS = ["N", "S", "C", "Cp", "LT", "CT", "F", "AP", "AM", "AW", "PK"];

export function PrintMenu() {
  const { t } = useTranslation();
  const ps = usePrint();
  const profiles = useProfiles<PrintSettings>("print");
  const list: Profile<PrintSettings>[] = profiles.data ?? [];
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "print"] });
  const secs: Sec[] = ["general", "cs", "maps", "header", "el", "xnc", "labels"];
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
      <div className="side-label">{t("print.sections")}</div>
      {secs.map((s) => (
        <button key={s} type="button" className={cx("side-item", ps.sec === s && "side-item-active")} onClick={() => ps.set({ sec: s })}
          data-testid={`print-sec-${s}`}>{t(`print.sec.${s}`)}</button>
      ))}
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
  const base: PrintSettings | undefined = ps.profile !== null
    ? { ...(defaults.data as PrintSettings), ...(profiles.data?.find((p) => p.id === ps.profile)?.data ?? {}) }
    : defaults.data;
  const s = ps.draft ?? base;
  const ls = ps.labels ?? labelDefaults.data;
  const labelsMode = ps.sec === "labels";

  useEffect(() => {
    if (!pid || !s || (labelsMode && !ls)) return;
    let alive = true;
    setLoading(true);
    const q = labelsMode
      ? fetchHtml(`/projects/${pid}/labels`, { lang: ps.lang, op_id: ps.labelOp || undefined }, ls)
      : fetchHtml(`/projects/${pid}/report`, { lang: ps.lang }, s);
    q.then((h) => { if (alive) setHtml(h); }).catch(() => undefined).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [pid, JSON.stringify(s), JSON.stringify(ls), ps.lang, labelsMode, ps.labelOp, ps.stamp, project.data]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!pid || !project.data) return <Empty>{t("print.open_project")}</Empty>;
  if (!s) return <Empty>{t("app.loading")}</Empty>;
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
  const saveLabels = async () => {
    const r = await call(() => put("/settings/labels/default", ls));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "labels"] }); ps.set({ labels: null }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const doPrint = () => { frame.current?.contentWindow?.focus(); frame.current?.contentWindow?.print(); };
  const openWin = () => { if (html) showHtml(html); };
  const csOps = project.data.operations.filter((o) => o.type === "CS");
  return (
    <div className="print">
      <div className="print-form scroll" data-testid="print-form">
        <div className="toolbar">
          <b>{t(`print.sec.${ps.sec}`)}</b><span className="grow" />
          {!labelsMode && <IconBtn icon={Save} title={t("print.save_profile")} onClick={() => void saveProfile()} disabled={!ps.draft} />}
          {labelsMode && <IconBtn icon={Save} title={t("print.save_profile")} onClick={() => void saveLabels()} disabled={!ps.labels} />}
        </div>
        {ps.sec === "general" && <div className="checks-col">
          {chk("header")}{chk("materials_list")}{chk("warehouse")}{chk("warehouse_cut_work")}{chk("warehouse_edge_work")}
          {chk("products_list")}{chk("operations")}{chk("xnc_stats")}
        </div>}
        {ps.sec === "cs" && <div className="checks-col">
          {chk("cs_parts")}{chk("cs_unplaced")}{chk("cs_sheets")}{chk("cs_remnants")}{chk("cs_maps")}{chk("cs_commands")}
          <Field label={t("print.f.cs_size_mode")}>
            <Sel<string> value={s.cs_size_mode ?? ""} width={200} onChange={(v) => upd({ cs_size_mode: (v || null) as PrintSettings["cs_size_mode"] })}
              options={[{ value: "", label: t("print.project_mode") }, { value: "blank", label: t("sizemode.blank") },
                { value: "detail", label: t("sizemode.detail") }, { value: "jointed", label: t("sizemode.jointed") }]} /></Field>
        </div>}
        {ps.sec === "maps" && <div className="checks-col">
          {chk("map_parts_list")}{chk("map_edges")}{chk("map_remnant_number")}{chk("map_qr")}{chk("map_mirror")}
          <Field label={t("print.f.map_part_label")}>
            <Sel value={s.map_part_label} width={200} onChange={(v) => upd({ map_part_label: v })}
              options={(["number", "name", "number_name"] as const).map((v) => ({ value: v, label: t(`print.label.${v}`) }))} /></Field>
        </div>}
        {ps.sec === "header" && <div className="checks-col">
          <p className="muted">{t("print.header_hint")}</p>
          {HEADER_FIELDS.map((f) => (
            <Check key={f} checked={s.map_header_fields.includes(f)} label={`${f} — ${t(`print.hf.${f}`)}`}
              onChange={(v) => upd({ map_header_fields: v ? HEADER_FIELDS.filter((x) => x === f || s.map_header_fields.includes(x))
                : s.map_header_fields.filter((x) => x !== f) })} />
          ))}
        </div>}
        {ps.sec === "el" && <div className="checks-col">{chk("el_params")}{chk("el_parts")}</div>}
        {ps.sec === "xnc" && <div className="checks-col">{chk("xnc_drawing")}{chk("xnc_stats")}</div>}
        {labelsMode && ls && <div className="checks-col">
          <Field label={t("print.lbl.op")}>
            <Sel value={ps.labelOp} width={200} onChange={(v) => ps.set({ labelOp: v })}
              options={[{ value: "", label: t("print.lbl.all") }, ...csOps.map((o) => ({ value: o.id, label: o.name || o.code }))]} /></Field>
          <Field label={t("print.lbl.width")} unit={t("u.mm")}><Num value={ls.width_mm} min={20} onCommit={(v) => ps.set({ labels: { ...ls, width_mm: v ?? 58 } })} /></Field>
          <Field label={t("print.lbl.height")} unit={t("u.mm")}><Num value={ls.height_mm} min={15} onCommit={(v) => ps.set({ labels: { ...ls, height_mm: v ?? 40 } })} /></Field>
          <Field label={t("print.lbl.columns")} hint={t("print.lbl.columns_hint")}><Num value={ls.columns} min={0} max={6} onCommit={(v) => ps.set({ labels: { ...ls, columns: Math.round(v ?? 3) } })} /></Field>
          {(["qr", "show_edges", "show_product", "show_map"] as const).map((k) => (
            <Check key={k} checked={ls[k]} label={t(`print.lbl.${k}`)} onChange={(v) => ps.set({ labels: { ...ls, [k]: v } })} />
          ))}
          <p className="muted">{t("print.lbl.hint")}</p>
        </div>}
      </div>
      <div className="print-preview">
        <div className="toolbar">
          <Btn icon={Printer} kind="primary" label={t("print.print")} onClick={doPrint} testid="print-btn" />
          <Btn icon={ExternalLink} label={t("print.open")} onClick={openWin} />
          <IconBtn icon={RefreshCw} title={t("menu.refresh")} onClick={() => ps.set({ stamp: ps.stamp + 1 })} />
          {loading && <span className="muted">{t("app.loading")}</span>}
          <span className="grow" />
          <span className="muted">{t("print.pdf_hint")}</span>
        </div>
        <iframe ref={frame} title="report" className="report-frame" srcDoc={html} data-testid="report-frame"
          sandbox="allow-same-origin allow-modals" />
      </div>
    </div>
  );
}
