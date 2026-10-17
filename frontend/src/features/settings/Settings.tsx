// «Настройки» (UI_SPEC §9): umumiy, postprotsessorlar (shablon), qoldiqlar ombori, katalog, MES, profillar.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import type { ColDef, CellValueChangedEvent } from "ag-grid-community";
import { ArrowDownToLine, ArrowUpFromLine, AtSign, Box, Cloud, Copy, Cpu, Drill, FolderClosed, FolderSync, Gauge, HardDriveDownload, KeyRound, Layers, Library, LogOut, Plug, Plus, Save, Send, ShoppingCart, SlidersHorizontal, Trash, Warehouse, type LucideIcon } from "lucide-react";
import { call, qc, useAppSettings, usePpMachines, useProfiles, useProject, useRemnants } from "../../api/hooks";
import { del, downloadPost, get, patch, post, put, setToken } from "../../api/client";
import type { AppSettings, PostprocessorProfile, PpMachine, PpMachines, Profile, Remnant } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { askConfirm, showError } from "../../shared/dialogs";
import { Btn, Check, Field, Modal, Num, Sel, Txt, cx } from "../../shared/ui";
import { CatalogPage } from "../catalog/CatalogPage";
import { XncSettings } from "../xnc/XncSettings";
import { MachineSettings } from "./machines/MachineSettings";
import { MinPartSetting } from "./MinPartSetting";
import { OeeView } from "../oee/OeeView";

type Page = "general" | "pp" | "xnc" | "remnants" | "catalog" | "production" | "mes" | "backup";
const usePage = create<{ page: Page; set: (p: Page) => void }>((set) => ({ page: "general", set: (p) => set({ page: p }) }));

// menyu belgilari: postprotsessor — mikrosxema, XNC — parma, ombor, katalog va h.k.
const PAGE_ICON: Record<Page, LucideIcon> = {
  general: SlidersHorizontal, pp: Cpu, xnc: Drill, remnants: Warehouse, catalog: Library, production: Gauge, mes: Plug,
  backup: FolderSync,
};

export function SettingsMenu() {
  const { t } = useTranslation();
  const { page, set } = usePage();
  const [im, setIm] = useState(false);
  const toast = useUI((s) => s.toast);
  // Tartib — xodimlar o'rgangan menyu bo'yicha; `mes` — MES serveri bajaradigan bandlar (keyin ulanadi); oxirida — o'z bo'limlarimiz.
  const mes = (k: string, Icon: LucideIcon) => (
    <button key={k} type="button" className="side-item side-item-mes" data-testid={`settings-mes-${k}`}
      title={t("settings.mes_later")} onClick={() => toast(t("settings.mes_later"), "info")}>
      <Icon size={15} /> {t(`settings.m.${k}`)} <sup className="mes-tag">MES</sup></button>
  );
  const pg = (p: Page) => (
    <button key={p} type="button" className={cx("side-item", page === p && "side-item-active")} onClick={() => set(p)}
      data-testid={`settings-${p}`}>{(() => { const I = PAGE_ICON[p]; return <I size={15} />; })()} {t(`settings.page.${p}`)}</button>
  );
  const saveAll = async () => {          // «Сохранить данные на локальный диск»: barcha loyihalar bitta ZIP da
    try {
      const rows = await get<{ id: string }[]>("/projects", { all_folders: true });
      if (!rows.length) { toast(t("app.no_rows"), "info"); return; }
      await downloadPost("/projects/export/project-zip", { ids: rows.map((r) => r.id) }, "projects.zip");
    } catch (e) { showError(e); }
  };
  return (
    <div className="side-menu">
      {im && <InputModesDialog onClose={() => setIm(false)} />}
      {mes("password", KeyRound)}
      {mes("email", AtSign)}
      <button type="button" className="side-item" onClick={() => setIm(true)} data-testid="settings-inputmodes">
        <Layers size={15} /> {t("settings.inputmodes")}</button>
      {pg("pp")}
      {pg("xnc")}
      <button type="button" className="side-item" onClick={() => void saveAll()} data-testid="settings-save-local">
        <HardDriveDownload size={15} /> {t("settings.m.save_local")}</button>
      <button type="button" className="side-item" data-testid="settings-import3d"
        onClick={() => { useUI.getState().set({ section: "project" }); toast(t("settings.m.import3d_hint"), "info"); }}>
        <Box size={15} /> {t("settings.m.import3d")}</button>
      <div className="side-gap" />
      {mes("dropbox", Cloud)}
      {mes("dir_projects", FolderClosed)}
      {mes("dir_xnc", FolderClosed)}
      {mes("dir_labels", FolderClosed)}
      {pg("catalog")}
      <div className="side-gap" />
      {mes("orders", ShoppingCart)}
      <div className="side-gap" />
      {pg("backup")}
      <div className="side-gap" />
      {pg("general")}
      {pg("remnants")}
      {pg("production")}
      {pg("mes")}
      <div className="side-gap" />
      {mes("logout", LogOut)}
    </div>
  );
}

/** «Режимы ввода деталей»: yangi loyihada qaysi o'lcham rejimi taklif qilinadi (GibLab kabi alohida oyna). */
function InputModesDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const app = useAppSettings();
  const [v, setV] = useState<AppSettings["input_mode_suggest"] | null>(null);
  const cur = v ?? app.data?.input_mode_suggest ?? "none";
  const ok = async () => {
    if (app.data && cur !== app.data.input_mode_suggest) {
      const r = await call(() => put("/settings/app/default", { ...app.data, input_mode_suggest: cur }));
      if (r) void qc.invalidateQueries({ queryKey: ["defaults", "app"] });
    }
    onClose();
  };
  return (
    <Modal title={t("settings.inputmodes")} onClose={onClose} width={480} testid="inputmodes-dialog"
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <p><b>{t("settings.inputmodes_q")}</b></p>
      <div className="type-list">
        {(["none", "blank", "detail", "jointed"] as const).map((m) => (
          <label key={m} className="type-item"><input type="radio" checked={cur === m} onChange={() => setV(m)} /> {t(`settings.im.${m}`)}</label>
        ))}
      </div>
    </Modal>
  );
}

export function SettingsView() {
  const page = usePage((s) => s.page);
  if (page === "pp") return <Postprocessors />;
  if (page === "xnc") return <XncSettings />;
  if (page === "remnants") return <RemnantsWarehouse />;
  if (page === "catalog") return <CatalogPage />;
  if (page === "production") return <OeeView />;          // W17: OEE — MES sozlamasi o'chiq bo'lsa ham shu yerdan ochiladi
  if (page === "mes") return <MesPage />;
  if (page === "backup") return <Backup />;
  return <General />;
}

function General() {
  const { t } = useTranslation();
  const app = useAppSettings();
  const ui = useUI();
  const [d, setD] = useState<AppSettings | null>(null);
  useEffect(() => { if (app.data) setD(app.data); }, [app.data]);
  if (!d) return null;
  const save = async () => {
    const r = await call(() => put("/settings/app/default", d));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "app"] }); ui.setLang(d.language); ui.toast(t("app.saved"), "ok"); }
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.general")}</h2><Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} testid="settings-save" /></div>
      <div className="form1 scroll">
        <Field label={t("settings.currency")}><Txt value={d.currency} width={80} onCommit={(v) => setD({ ...d, currency: v.trim().toUpperCase() || "UZS" })} /></Field>
        <Field label={t("settings.language")}><Sel value={d.language} width={220} onChange={(v) => setD({ ...d, language: v })}
          options={[{ value: "ru", label: "Русский (+ ўзбекча устунлар)" }, { value: "uz", label: "O'zbekcha (lotin)" }]} /></Field>
        <Field label=" "><Check checked={d.remnant_confirm} label={t("settings.remnant_confirm")} onChange={(v) => setD({ ...d, remnant_confirm: v })} /></Field>
        <Field label={t("settings.default_sheet")} unit={t("u.mm")}>
          <span className="row gap"><Num value={d.default_sheet_length} width={70} min={1} onCommit={(v) => setD({ ...d, default_sheet_length: v && v > 0 ? v : 2750 })} /> ×
            <Num value={d.default_sheet_width} width={70} min={1} onCommit={(v) => setD({ ...d, default_sheet_width: v && v > 0 ? v : 1830 })} /></span></Field>
        <MinPartSetting />
        <p className="muted">{t("settings.min_part_note")}</p>
        <p className="muted">{t("settings.fullscreen_hint")}</p>
      </div>
    </div>
  );
}

// ───────────────────────── Postprotsessorlar ─────────────────────────
const EMPTY_PP: PostprocessorProfile = {
  name: "", extension: "txt", per_map: true, encoding: "utf-8", newline: "crlf", description: "",
  template: "{# Har karta alohida fayl #}\nSHEET;{{ f(map.sheet_length) }};{{ f(map.sheet_width) }};{{ map.copies }}\n{% for c in map.commands -%}\n{{ c.code }}{{ c.level }};{{ f(c.size) }};{{ c.count }};{{ c.ref }}\n{% endfor -%}\nEND\n",
};

// Stanoklar bo'limi: faqat nomlar va ularga format shabloni biriktirish (format mantig'ini korxona dasturchilari yozadi).
type MachineBody = { enabled: Record<string, boolean>; profile: Record<string, number | null>; prefix: boolean };

function MachinePane({ m, profiles, onChange }: { m: PpMachine; profiles: Profile<PostprocessorProfile>[];
  onChange: (fn: (b: MachineBody) => void) => void }) {
  const { t } = useTranslation();
  return (
    <div className="pp-edit" data-testid="pp-machine-pane">
      <h3>{m.name}</h3>
      <div className="muted">{t(`pp.group.${m.group}`)}</div>
      <Check checked={m.enabled} label={t("pp.machine_enable")} testid="pp-machine-enable"
        onChange={(v) => onChange((b) => { b.enabled[m.key] = v; })} />
      <Field label={t("pp.machine_template")}>
        <Sel value={m.profile_id === null ? "" : String(m.profile_id)} width={320} testid="pp-machine-profile"
          onChange={(v) => onChange((b) => { b.profile[m.key] = v ? Number(v) : null; })}
          options={[{ value: "", label: t("pp.machine_none") }, ...profiles.map((p) => ({ value: String(p.id), label: p.name }))]} />
      </Field>
      <p className={m.bound ? "ok" : "warn"}>{m.bound ? t("pp.machine_bound", { n: m.profile_name }) : t("pp.machine_unbound_note")}</p>
      <p className="muted">{t("pp.machine_hint")}</p>
      <MachineSettings key={m.key} machineKey={m.key} />
    </div>
  );
}

function Postprocessors() {
  const { t } = useTranslation();
  const list = useProfiles<PostprocessorProfile>("postprocessor");
  const mach = usePpMachines();
  const [mk, setMk] = useState<string | null>(null);      // tanlangan stanok (null — shablon muharriri)
  const saveMach = async (fn: (b: MachineBody) => void) => {
    if (!mach.data) return;
    const b: MachineBody = { enabled: {}, profile: {}, prefix: mach.data.prefix };
    mach.data.groups.forEach((g) => g.machines.forEach((m) => { b.enabled[m.key] = m.enabled; b.profile[m.key] = m.profile_id; }));
    fn(b);
    const r = await call(() => put<PpMachines>("/postprocessors/machines", b));
    if (r) { qc.setQueryData(["pp-machines"], r); void qc.invalidateQueries({ queryKey: ["postprocessors"] }); }
  };
  const curMachine = mach.data?.groups.flatMap((g) => g.machines).find((m) => m.key === mk);
  const pid = useUI((s) => s.projectId);
  const project = useProject(pid);
  const [sel, setSel] = useState<number | null>(null);
  const [d, setD] = useState<PostprocessorProfile | null>(null);
  const [isNew, setIsNew] = useState(false);          // «Новый» / «Клонировать» — hali saqlanmagan qoralama
  const [opId, setOpId] = useState("");
  const [pv, setPv] = useState<{ ok: boolean; text?: string; error?: string; files?: number } | null>(null);
  const [pvMachine, setPvMachine] = useState("");        // shablon konteksti uchun stanok (W7: `machine`, `label`)
  const cur = list.data?.find((p) => p.id === sel);
  useEffect(() => { if (cur) setD({ ...EMPTY_PP, ...cur.data, name: cur.name }); }, [cur]);
  useEffect(() => { if (sel === null && !isNew && list.data?.length) setSel(list.data[0].id); }, [list.data, sel, isNew]);
  const csOps = project.data?.operations.filter((o) => o.type === "CS" && o.result) ?? [];
  useEffect(() => { if (!opId && csOps.length) setOpId(csOps[0].id); }, [csOps, opId]);
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "postprocessor"] });
  const save = async () => {
    if (!d) return;
    if (!d.name.trim()) { useUI.getState().toast(t("pp_ed.name_required"), "error"); return; }
    const r = sel === null
      ? await call(() => post<Profile<PostprocessorProfile>>("/settings/postprocessor", { name: d.name.trim(), data: d }))
      : await call(() => put<Profile<PostprocessorProfile>>(`/settings/postprocessor/${sel}`, { name: d.name.trim(), data: d }));
    if (r) { await refresh(); setIsNew(false); setSel(r.id); void qc.invalidateQueries({ queryKey: ["postprocessors"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const preview = async () => {
    if (!d || !pid || !opId) return;
    const r = await call(() => post<{ ok: boolean; text?: string; error?: string; files?: number }>("/postprocessors/preview",
      { project_id: pid, op_id: opId, profile: d, machine: pvMachine || null }));
    if (r) setPv(r);
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.pp")}</h2>
        <Btn icon={Plus} label={t("pp_ed.new")} testid="pp-new"
          onClick={() => { setMk(null); setIsNew(true); setSel(null); setD({ ...EMPTY_PP, name: t("pp_ed.new_name") }); setPv(null); }} />
        <Btn icon={Copy} label={t("app.clone")} disabled={!d || !!mk} testid="pp-clone"
          onClick={() => { if (d) { setIsNew(true); setSel(null); setD({ ...d, name: d.name + " (2)" }); } }} />
        <Btn icon={Save} kind="primary" label={t("app.save")} disabled={!d || !!mk} onClick={() => void save()} testid="pp-save" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={sel === null || !!mk} onClick={async () => {
          if (sel === null || !(await askConfirm(t("pp_ed.delete_q")))) return;
          await call(() => del(`/settings/postprocessor/${sel}`)); await refresh(); setIsNew(false); setSel(null); setD(null);
          void qc.invalidateQueries({ queryKey: ["postprocessors"] });
        }} />
      </div>
      <div className="pp-page">
        <div className="pp-list">
          <div className="side-label">{t("pp_ed.builtin")}</div>
          {(["csv", "commands", "dxf", "json"] as const).map((b) => <div key={b} className="pp-item muted">{t(`pp.builtin.${b}`)}</div>)}
          <div className="side-label">{t("pp_ed.user")}</div>
          {(list.data ?? []).map((p) => (
            <button key={p.id} type="button" className={cx("pp-item", !mk && sel === p.id && "pp-item-active")}
              onClick={() => { setMk(null); setIsNew(false); setSel(p.id); }}>{p.name}</button>
          ))}
          {mach.data && (
            <>
              <div className="side-label">{t("pp.machines")}</div>
              <Check checked={mach.data.prefix} label={t("pp.machine_prefix")} testid="pp-machine-prefix"
                onChange={(v) => void saveMach((b) => { b.prefix = v; })} />
              {mach.data.groups.map((g) => (
                <div key={g.key} data-testid={`pp-group-${g.key}`}>
                  <div className="side-label">{t(`pp.group.${g.key}`)}</div>
                  {g.machines.map((m) => (
                    <button key={m.key} type="button" data-testid={`pp-machine-${m.key}`}
                      className={cx("pp-item", mk === m.key && "pp-item-active", !m.enabled && "muted")}
                      onClick={() => setMk(m.key)}>{m.enabled ? "● " : "○ "}{m.name}</button>
                  ))}
                </div>
              ))}
            </>
          )}
        </div>
        {curMachine ? (
          <MachinePane m={curMachine} profiles={list.data ?? []} onChange={(fn) => void saveMach(fn)} />
        ) : d ? (
          <div className="pp-edit">
            <div className="row gap wrap">
              <Field label={t("pp_ed.name")}><Txt value={d.name} width={220} onCommit={(v) => setD({ ...d, name: v })} testid="pp-name" /></Field>
              <Field label={t("pp_ed.ext")}><Txt value={d.extension} width={60} onCommit={(v) => setD({ ...d, extension: v.replace(/^\./, "") })} /></Field>
              <Field label={t("pp_ed.encoding")}><Sel value={d.encoding} width={110} onChange={(v) => setD({ ...d, encoding: v })}
                options={["utf-8", "cp1251", "cp866", "ascii"].map((v) => ({ value: v, label: v }))} /></Field>
              <Field label={t("pp_ed.newline")}><Sel value={d.newline} width={90} onChange={(v) => setD({ ...d, newline: v })}
                options={[{ value: "crlf", label: "CRLF" }, { value: "lf", label: "LF" }]} /></Field>
              <Check checked={d.per_map} label={t("pp_ed.per_map")} onChange={(v) => setD({ ...d, per_map: v })} />
            </div>
            <textarea className="inp code" value={d.template} spellCheck={false} data-testid="pp-template"
              onChange={(e) => setD({ ...d, template: e.target.value })} />
            <details className="pp-doc"><summary>{t("pp_ed.context")}</summary><pre>{t("pp_ed.context_doc")}</pre></details>
            <div className="row gap">
              <Sel value={opId} width={260} onChange={setOpId}
                options={csOps.length ? csOps.map((o) => ({ value: o.id, label: `${project.data?.name}: ${o.name}` })) : [{ value: "", label: t("pp_ed.no_sample") }]} />
              <Sel value={pvMachine} width={200} testid="pp-preview-machine" onChange={setPvMachine}
                options={[{ value: "", label: t("ppm.ctx_machine_none") },
                  ...(mach.data?.groups.find((g) => g.key === "saw")?.machines ?? []).map((x) => ({ value: x.key, label: x.name }))]} />
              <Btn label={t("pp_ed.preview")} onClick={() => void preview()} disabled={!opId} testid="pp-preview" />
              {pv && <span className={pv.ok ? "ok" : "warn"}>{pv.ok ? t("pp_ed.files", { n: pv.files }) : pv.error}</span>}
            </div>
            {pv?.ok && <pre className="pp-out" data-testid="pp-output">{pv.text}</pre>}
          </div>
        ) : <div className="empty">{t("pp_ed.choose")}</div>}
      </div>
    </div>
  );
}

// ───────────────────────── Qoldiqlar ombori ─────────────────────────
function RemnantsWarehouse() {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const data = useRemnants(undefined, q);
  const [add, setAdd] = useState(false);
  const [sel, setSel] = useState<number | null>(null);
  const cols = useMemo<ColDef<Remnant>[]>(() => [
    { headerName: "ID", field: "id", width: 60, cellClass: "num" },
    { headerName: t("rem.code"), field: "material_code", width: 140, editable: true },
    { headerName: t("rem.material"), field: "material_name", flex: 1, editable: true },
    // o'lchamlar faqat musbat, soni — 0 yoki musbat butun: manfiy / nol qiymat serverga (422) yetib bormaydi (#12)
    { headerName: t("sheets.col.length"), field: "length", width: 80, editable: true, cellClass: "num", valueParser: (p) => posNum(p.newValue, p.oldValue) },
    { headerName: t("sheets.col.width"), field: "width", width: 80, editable: true, cellClass: "num", valueParser: (p) => posNum(p.newValue, p.oldValue) },
    { headerName: t("rem.thickness"), field: "thickness", width: 70, editable: true, cellClass: "num", valueParser: (p) => posNum(p.newValue, p.oldValue) },
    { headerName: t("sheets.col.qty"), field: "qty", width: 60, editable: true, cellClass: "num",
      valueParser: (p) => { const v = parseCellNum(p.newValue); return v === null || v < 0 ? p.oldValue : Math.round(v); } },   // manfiy — eski qiymat
    { headerName: t("u.m2"), field: "area_m2", width: 70, cellClass: "num" },
    { headerName: t("rem.source"), width: 90, valueGetter: (p) => (p.data?.source_number ? `№${p.data.source_number}` : "") },
    { headerName: t("rem.date"), field: "created_at", width: 110, valueFormatter: (p) => (p.value ? String(p.value).slice(0, 10) : "") },
    { headerName: t("rem.note"), field: "note", width: 200, editable: true },
  ], [t]);
  const onChange = (e: CellValueChangedEvent<Remnant>) => {
    if (!e.data || !e.colDef.field) return;
    void call(() => patch(`/remnants/${e.data!.id}`, { [e.colDef.field as string]: e.newValue })).then(() => qc.invalidateQueries({ queryKey: ["remnants"] }));
  };
  const total = (data.data ?? []).reduce((s, r) => s + r.area_m2 * r.qty, 0);
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.remnants")}</h2>
        <input className="inp" placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} />
        <Btn icon={Plus} label={t("app.add")} onClick={() => setAdd(true)} testid="rem-add" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={sel === null} onClick={async () => {
          if (sel === null || !(await askConfirm(t("rem.delete_q")))) return;
          await call(() => del(`/remnants/${sel}`)); void qc.invalidateQueries({ queryKey: ["remnants"] });
        }} />
        <span className="muted">{t("rem.total", { n: data.data?.length ?? 0, a: Math.round(total * 100) / 100 })}</span>
      </div>
      <Grid<Remnant> className="grow" rowData={data.data ?? []} columnDefs={cols} getRowId={(p) => String(p.data.id)} testid="remnants-grid"
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows()[0]?.id ?? null)} onCellValueChanged={onChange} />
      {add && <AddRemnant onClose={() => setAdd(false)} />}
    </div>
  );
}

/** Jadval katagi: musbat son, aks holda eski qiymat qoladi. */
function posNum(nv: unknown, old: number): number {
  const v = parseCellNum(nv);
  return v === null || v <= 0 ? old : v;
}

function AddRemnant({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const [r, setR] = useState({ material_code: "", material_name: "", length: 1000, width: 600, thickness: 16, qty: 1, note: "" });
  const valid = !!r.material_code && r.length > 0 && r.width > 0 && r.thickness > 0 && r.qty > 0;
  const ok = async () => {
    const x = await call(() => post("/remnants", r));
    if (x) { void qc.invalidateQueries({ queryKey: ["remnants"] }); onClose(); }
  };
  return (
    <Modal title={t("rem.add")} onClose={onClose} width={420}
      footer={<><Btn kind="primary" label={t("app.add")} onClick={() => void ok()} disabled={!valid} testid="rem-add-ok" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("rem.code")}><Txt value={r.material_code} onCommit={(v) => setR({ ...r, material_code: v })} /></Field>
        <Field label={t("rem.material")}><Txt value={r.material_name} onCommit={(v) => setR({ ...r, material_name: v })} /></Field>
        <Field label={t("sheets.col.length")} unit={t("u.mm")}><Num value={r.length} min={1} max={100000} onCommit={(v) => setR({ ...r, length: v ?? 0 })} testid="rem-add-length" /></Field>
        <Field label={t("sheets.col.width")} unit={t("u.mm")}><Num value={r.width} min={1} max={100000} onCommit={(v) => setR({ ...r, width: v ?? 0 })} /></Field>
        <Field label={t("rem.thickness")} unit={t("u.mm")}><Num value={r.thickness} min={0.1} max={1000} onCommit={(v) => setR({ ...r, thickness: v ?? 16 })} /></Field>
        <Field label={t("sheets.col.qty")}><Num value={r.qty} min={1} onCommit={(v) => setR({ ...r, qty: Math.round(v ?? 1) })} /></Field>
        <Field label={t("rem.note")}><Txt value={r.note} onCommit={(v) => setR({ ...r, note: v })} /></Field>
      </div>
    </Modal>
  );
}

// ───────────────────────── MES ─────────────────────────
function MesPage() {
  const { t } = useTranslation();
  const app = useAppSettings();
  const ui = useUI();
  // «MES интеграция» yoqilmaguncha chap paneldagi «MES» qatori xira va bosilmaydi
  const toggle = async (on: boolean) => {
    if (!app.data) return;
    const r = await call(() => put("/settings/app/default", { ...app.data, mes_enabled: on }));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "app"] }); ui.toast(t(on ? "mes.enabled_on" : "mes.enabled_off"), "ok"); }
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.mes")}</h2></div>
      <div className="scroll doc">
        <Check checked={!!app.data?.mes_enabled} label={t("mes.enable")} onChange={(v) => void toggle(v)} testid="mes-enable" />
        <p className="muted">{t("mes.enable_hint")}</p>
        <MesApiDoc />
      </div>
    </div>
  );
}

export function MesApiDoc() {
  const { t } = useTranslation();
  const [tok, setTok] = useState("");
  const test = async () => {
    const r = await call(() => post<{ sent: boolean; reason?: string | null; url?: string; status?: number | null; error?: string | null }>("/mes/webhook-test"));
    if (!r) return;
    // faqat server 2xx/3xx javob bersagina «yuborildi»; aks holda sabab (status / xato / timeout) ko'rsatiladi
    if (r.sent) useUI.getState().toast(t("mes.sent", { url: r.url }), "ok");
    else useUI.getState().toast(r.reason || r.error || (r.status ? t("err.http.other", { status: r.status }) : t("mes.test_failed")), "error");
  };
  return (
    <>
      <p>{t("mes.intro")}</p>
      <table className="simple">
        <tbody>
          {[
            ["POST /api/mes/orders", t("mes.ep.orders")], ["GET /api/mes/orders/{ref}", t("mes.ep.order")],
            ["GET /api/projects/{id}/mes-export", t("mes.ep.export")], ["POST /api/catalog/sync", t("mes.ep.catalog")],
            ["GET /api/mes/scan/{qr}", t("mes.ep.scan")], ["POST /api/mes/scan/{qr}/done", t("mes.ep.done")],
            ["GET /api/remnants", t("mes.ep.remnants")], ["/docs", "OpenAPI (Swagger)"],
          ].map(([a, b]) => <tr key={a}><td><code>{a}</code></td><td>{b}</td></tr>)}
        </tbody>
      </table>
      <p>{t("mes.webhook")}</p>
      <Btn icon={Send} label={t("mes.test")} onClick={() => void test()} />
      <h3>JWT</h3>
      <p className="muted">{t("mes.jwt")}</p>
      <div className="row gap">
        <input className="inp" style={{ width: 420 }} placeholder="eyJhbGciOi..." value={tok} onChange={(e) => setTok(e.target.value)} />
        <Btn label={t("app.save")} onClick={() => { setToken(tok || null); void qc.invalidateQueries(); useUI.getState().toast(t("app.saved"), "ok"); }} />
        <Btn label={t("mes.logout")} onClick={() => { setToken(null); void qc.invalidateQueries(); }} />
      </div>
    </>
  );
}

// ───────────────────────── Profillar zaxirasi ─────────────────────────
function Backup() {
  const { t } = useTranslation();
  const exportAll = async () => {
    const data = await call(() => get("/backup/settings"));
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "mebelix-sozlamalar.json"; a.click();
  };
  // Bir xil «doira + nom» — dublikat yaratilmaydi (mavjudi yangilanadi); noto'g'ri fayl muvaffaqiyat deb ko'rsatilmaydi
  const importAll = (f: File) => {
    void f.text().then(async (txt) => {
      let body: unknown;
      try { body = JSON.parse(txt); } catch { useUI.getState().toast(t("backup.bad_file"), "error"); return; }
      const r = await call(() => post<{ created: number; updated: number; skipped: number; invalid: { scope: string; name: string; error: string }[] }>(
        "/backup/settings/import", body));
      if (!r) return;
      void qc.invalidateQueries();
      useUI.getState().toast(t("backup.imported", { n: r.created + r.updated }), r.created + r.updated > 0 ? "ok" : "info",
        r.invalid.map((x) => `${x.scope}/${x.name}: ${x.error}`));
    });
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.backup")}</h2></div>
      <div className="doc">
        <p>{t("backup.hint")}</p>
        <div className="row gap">
          <Btn icon={ArrowUpFromLine} label={t("backup.export")} onClick={() => void exportAll()} />
          <label className="btn btn-default"><ArrowDownToLine size={15} /> {t("backup.import")}
            <input type="file" hidden accept=".json" onChange={(e) => { const f = e.target.files?.[0]; if (f) importAll(f); }} /></label>
        </div>
      </div>
    </div>
  );
}

