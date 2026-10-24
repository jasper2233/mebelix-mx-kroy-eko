// «Настройки → Постпроцессоры» oynasi: xodimlar o'rgangan joylashuv — o'raladigan yorliqlar qatori «Общие» + har stanok uchun
// bitta yorliq (tartib — server ro'yxati: avval pil markazlari, keyin ishlov markazlari), pastda Ок / Отмена.
// «Общие» — fayl nomiga stanok prefiksi katakchasi. O'z qo'shimchamiz — korxona format shablonlari muharriri — oxirgi yorliqda.
// Stanokni yoqish / shablon biriktirish va prefiks qoralama: «Ок» saqlaydi, «Отмена» tashlaydi. Stanok parametrlari
// (MachineSettings) o'z «Сохранить» tugmasi bilan saqlanadi (avvalgidek).
// (2026-10-18) «Постпроцессор подключён для предприятия» — mijoz uchun ochish/yopish (services/pp_access.py): faqat administrator
// o'zgartiradi (boshqalarga katakcha faol emas), «Ок» bilan alohida saqlanadi (PUT /postprocessors/access).
// (2026-10-18, 2-qaror) «Форматы MebeliX» yorlig'i (stanoklardan keyin): o'z formatlarimiz (CSV, TXT, DXF, MES JSON, XNC JSON, MES)
// va korxona shablonlari ham shu tarzda ulanadi/o'chiriladi (`closed_extra`; standart — hammasi ulangan).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Copy, Cpu, FileText, Plus, Save, Trash } from "lucide-react";
import { call, qc, usePpAccess, usePpMachines, useProfiles, useProject } from "../../api/hooks";
import { del, post, put } from "../../api/client";
import type { PostprocessorProfile, PpAccess, PpAccessExtra, PpMachine, PpMachines, Profile } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Btn, Check, Field, Modal, Sel, Txt, cx } from "../../shared/ui";
import { MachineSettings } from "./machines/MachineSettings";
import "./machines/machines.css";

const EMPTY_PP: PostprocessorProfile = {
  name: "", extension: "txt", per_map: true, encoding: "utf-8", newline: "crlf", description: "",
  template: "{# Har karta alohida fayl #}\nSHEET;{{ f(map.sheet_length) }};{{ f(map.sheet_width) }};{{ map.copies }}\n{% for c in map.commands -%}\n{{ c.code }}{{ c.level }};{{ f(c.size) }};{{ c.count }};{{ c.ref }}\n{% endfor -%}\nEND\n",
};

// Stanoklar bo'limi: faqat nomlar va ularga format shabloni biriktirish (format mantig'ini korxona dasturchilari yozadi).
type MachineBody = { enabled: Record<string, boolean>; profile: Record<string, number | null>; prefix: boolean };

const bodyOf = (m: PpMachines): MachineBody => {
  const b: MachineBody = { enabled: {}, profile: {}, prefix: m.prefix };
  m.groups.forEach((g) => g.machines.forEach((x) => { b.enabled[x.key] = x.enabled; b.profile[x.key] = x.profile_id; }));
  return b;
};

function MachinePane({ m, profiles, onChange, opened, canEdit, onAccess }: { m: PpMachine; profiles: Profile<PostprocessorProfile>[];
  onChange: (fn: (b: MachineBody) => void) => void; opened: boolean; canEdit: boolean; onAccess: (v: boolean) => void }) {
  const { t } = useTranslation();
  return (
    <div className="pp-edit" data-testid="pp-machine-pane">
      <h3>{m.name}</h3>
      <div className="muted">{t(`pp.group.${m.group}`)}</div>
      <Check checked={opened} label={t("pp.access_open")} testid="pp-machine-access" disabled={!canEdit}
        title={canEdit ? undefined : t("pp.access_admin_only")} onChange={onAccess} />
      {!canEdit && <p className="muted" data-testid="pp-access-readonly">{t("pp.access_admin_only")}</p>}
      {!opened && <p className="warn" data-testid="pp-access-closed">{t("pp.access_closed_note")}</p>}
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

/** Korxona format shablonlari muharriri (avvalgi sahifadagi bilan bir xil; endi oynaning oxirgi yorlig'ida). */
function TemplatesPane({ list }: { list: Profile<PostprocessorProfile>[] }) {
  const { t } = useTranslation();
  const mach = usePpMachines();
  const pid = useUI((s) => s.projectId);
  const project = useProject(pid);
  const [sel, setSel] = useState<number | null>(null);
  const [d, setD] = useState<PostprocessorProfile | null>(null);
  const [isNew, setIsNew] = useState(false);          // «Новый» / «Клонировать» — hali saqlanmagan qoralama
  const [opId, setOpId] = useState("");
  const [pv, setPv] = useState<{ ok: boolean; text?: string; error?: string; files?: number } | null>(null);
  const [pvMachine, setPvMachine] = useState("");        // shablon konteksti uchun stanok (W7: `machine`, `label`)
  const cur = list.find((p) => p.id === sel);
  useEffect(() => { if (cur) setD({ ...EMPTY_PP, ...cur.data, name: cur.name }); }, [cur]);
  useEffect(() => { if (sel === null && !isNew && list.length) setSel(list[0].id); }, [list, sel, isNew]);
  const csOps = project.data?.operations.filter((o) => o.type === "CS" && o.result) ?? [];
  useEffect(() => { if (!opId && csOps.length) setOpId(csOps[0].id); }, [csOps, opId]);
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "postprocessor"] });
  const save = async () => {
    if (!d) return;
    if (!d.name.trim()) { useUI.getState().toast(t("pp_ed.name_required"), "error"); return; }
    const r = sel === null
      ? await call(() => post<Profile<PostprocessorProfile>>("/settings/postprocessor", { name: d.name.trim(), data: d }))
      : await call(() => put<Profile<PostprocessorProfile>>(`/settings/postprocessor/${sel}`, { name: d.name.trim(), data: d }));
    if (r) { await refresh(); setIsNew(false); setSel(r.id); void qc.invalidateQueries({ queryKey: ["postprocessors"] }); void qc.invalidateQueries({ queryKey: ["pp-access"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const preview = async () => {
    if (!d || !pid || !opId) return;
    const r = await call(() => post<{ ok: boolean; text?: string; error?: string; files?: number }>("/postprocessors/preview",
      { project_id: pid, op_id: opId, profile: d, machine: pvMachine || null }));
    if (r) setPv(r);
  };
  return (
    <div className="pp-tpl-pane" data-testid="pp-templates">
      <div className="row gap">
        <Btn icon={Plus} label={t("pp_ed.new")} testid="pp-new"
          onClick={() => { setIsNew(true); setSel(null); setD({ ...EMPTY_PP, name: t("pp_ed.new_name") }); setPv(null); }} />
        <Btn icon={Copy} label={t("app.clone")} disabled={!d} testid="pp-clone"
          onClick={() => { if (d) { setIsNew(true); setSel(null); setD({ ...d, name: d.name + " (2)" }); } }} />
        <Btn icon={Save} kind="primary" label={t("app.save")} disabled={!d} onClick={() => void save()} testid="pp-save" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={sel === null} onClick={async () => {
          if (sel === null || !(await askConfirm(t("pp_ed.delete_q")))) return;
          await call(() => del(`/settings/postprocessor/${sel}`)); await refresh(); setIsNew(false); setSel(null); setD(null);
          void qc.invalidateQueries({ queryKey: ["postprocessors"] });
          void qc.invalidateQueries({ queryKey: ["pp-access"] });       // shablon «Форматы MebeliX» ro'yxatidan ham ketsin
        }} />
      </div>
      <div className="pp-page">
        <div className="pp-list">
          <div className="side-label">{t("pp_ed.builtin")}</div>
          {(["csv", "commands", "dxf", "json"] as const).map((b) => <div key={b} className="pp-item muted">{t(`pp.builtin.${b}`)}</div>)}
          <div className="side-label">{t("pp_ed.user")}</div>
          {list.map((p) => (
            <button key={p.id} type="button" className={cx("pp-item", sel === p.id && "pp-item-active")}
              onClick={() => { setIsNew(false); setSel(p.id); }}>{p.name}</button>
          ))}
        </div>
        {d ? (
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

// MebeliX formatlari va shablonlar: bo'limlar (kroy, XNC, MES, shablonlar) — har qatorda «подключён» katakchasi (faqat admin)
const EXTRA_SECTIONS: { id: string; match: (x: PpAccessExtra) => boolean }[] = [
  { id: "saw", match: (x) => x.kind === "mx" && x.group === "saw" },
  { id: "cnc", match: (x) => x.kind === "mx" && x.group === "cnc" },
  { id: "mes", match: (x) => x.kind === "mx" && x.group === "mes" },
  { id: "templates", match: (x) => x.kind === "template" },
];

function ExtrasPane({ extras, closed, canEdit, onToggle }: { extras: PpAccessExtra[]; closed: string[]; canEdit: boolean;
  onToggle: (key: string, open: boolean) => void }) {
  const { t } = useTranslation();
  return (
    <div className="pp-edit" data-testid="pp-extras-pane">
      <h3>{t("pp.tab.extras")}</h3>
      <p className="muted">{t("pp.extras_hint")}</p>
      {!canEdit && <p className="muted" data-testid="pp-extras-readonly">{t("pp.access_admin_only")}</p>}
      {EXTRA_SECTIONS.map((sec) => {
        const rows = extras.filter(sec.match);
        if (!rows.length) return null;
        return (
          <fieldset key={sec.id} className="pp-extras-sec" data-testid={`pp-extras-${sec.id}`}>
            <legend>{t(`pp.extras_sec.${sec.id}`)}</legend>
            {rows.map((x) => {
              const open = !closed.includes(x.key);
              const k = x.key.slice(3);       // mx:csv → csv (kroy formatlari nomi «Постпроцессоры» oynasidagidek)
              const name = x.kind === "mx" ? t([`pp.extra.${k}`, `pp.builtin.${k}`], { defaultValue: x.label }) : x.label;
              return (
                <div key={x.key} className={cx("pp-extra-row", !open && "pp-extra-closed")}>
                  <Check checked={open} disabled={!canEdit} testid={`pp-extra-${x.key}`}
                    title={canEdit ? undefined : t("pp.access_admin_only")} onChange={(v) => onToggle(x.key, v)}
                    label={<>{name}{x.extension ? <span className="muted"> (.{x.extension})</span> : null}
                      {!open && <span className="muted"> — {t("pp.closed")}</span>}</>} />
                </div>
              );
            })}
          </fieldset>
        );
      })}
    </div>
  );
}

const TAB_GENERAL = "@general", TAB_EXTRAS = "@extras", TAB_TEMPLATES = "@templates";

export function PostprocessorsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const list = useProfiles<PostprocessorProfile>("postprocessor");
  const mach = usePpMachines();
  const acc = usePpAccess();
  const [tab, setTab] = useState(TAB_GENERAL);
  const [draft, setDraft] = useState<MachineBody | null>(null);
  const [accDraft, setAccDraft] = useState<string[] | null>(null);     // ochilgan stanoklar qoralamasi (faqat admin o'zgartiradi)
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (mach.data && !draft) setDraft(bodyOf(mach.data)); }, [mach.data, draft]);
  useEffect(() => { if (acc.data && !accDraft) setAccDraft([...acc.data.open].sort()); }, [acc.data, accDraft]);
  const canEdit = !!acc.data?.can_edit;
  const isOpen = (key: string) => (accDraft ?? acc.data?.open ?? []).includes(key);
  const setOpen = (key: string, v: boolean) => setAccDraft((d) => {
    const cur = new Set(d ?? acc.data?.open ?? []);
    if (v) cur.add(key); else cur.delete(key);
    return [...cur].sort();
  });
  const accDirty = !!(canEdit && accDraft && acc.data && JSON.stringify(accDraft) !== JSON.stringify([...acc.data.open].sort()));
  // yopilgan MebeliX formatlari / shablonlar qoralamasi (standart — hammasi ulangan)
  const [extDraft, setExtDraft] = useState<string[] | null>(null);
  useEffect(() => { if (acc.data && !extDraft) setExtDraft([...(acc.data.closed_extra ?? [])].sort()); }, [acc.data, extDraft]);
  const extClosed = extDraft ?? acc.data?.closed_extra ?? [];
  const setExtra = (key: string, open: boolean) => setExtDraft((d) => {
    const cur = new Set(d ?? acc.data?.closed_extra ?? []);
    if (open) cur.delete(key); else cur.add(key);
    return [...cur].sort();
  });
  const extDirty = !!(canEdit && extDraft && acc.data
    && JSON.stringify(extDraft) !== JSON.stringify([...(acc.data.closed_extra ?? [])].sort()));
  const profiles = list.data ?? [];
  const change = (fn: (b: MachineBody) => void) => setDraft((d) => {
    if (!d) return d;
    const n: MachineBody = { enabled: { ...d.enabled }, profile: { ...d.profile }, prefix: d.prefix };
    fn(n);
    return n;
  });
  const machDirty = !!(draft && mach.data && JSON.stringify(draft) !== JSON.stringify(bodyOf(mach.data)));
  const dirty = machDirty || accDirty || extDirty;
  // qoralama stanok holati (yoqilgan / biriktirilgan shablon) — ro'yxat va yorliqda shu ko'rinadi
  const view = (m: PpMachine): PpMachine => {
    if (!draft) return m;
    const prof = draft.profile[m.key] ?? null;
    const changed = prof !== m.profile_id;
    return { ...m, enabled: draft.enabled[m.key] ?? m.enabled, profile_id: prof,
      bound: changed ? prof !== null || !!m.native : m.bound,
      profile_name: changed ? (profiles.find((p) => p.id === prof)?.name ?? null) : m.profile_name };
  };
  const ok = async () => {
    if (!dirty || !draft) { onClose(); return; }
    setBusy(true);
    try {
      if (accDirty || extDirty) {
        const body: { open?: string[] | null; closed_extra?: string[] } = {};
        if (accDirty) body.open = accDraft;
        if (extDirty) body.closed_extra = extDraft ?? [];
        const a = await call(() => put<PpAccess>("/postprocessors/access", body));
        if (!a) return;
        qc.setQueryData(["pp-access"], a);
      }
      const r = machDirty ? await call(() => put<PpMachines>("/postprocessors/machines", draft)) : true;
      if (r) {
        void qc.invalidateQueries({ queryKey: ["pp-machines"] });
        void qc.invalidateQueries({ queryKey: ["postprocessors"] });
        void qc.invalidateQueries({ queryKey: ["xnc-postprocessors"] });
        onClose();
      }
    } finally { setBusy(false); }
  };
  const all = mach.data?.groups.flatMap((g) => g.machines) ?? [];
  const cur = all.find((m) => m.key === tab);
  const tabBtn = (key: string, label: string, testid: string, off = false, closed = false, Icon = Cpu) => (
    <button key={key} type="button" className={cx("tab", tab === key && "tab-active", off && "pp-off", closed && "pp-closed")}
      data-testid={testid} title={closed ? t("pp.closed_tip") : undefined}
      onClick={() => setTab(key)}><Icon size={13} />{label}</button>
  );
  return (
    <Modal title={t("settings.page.pp")} onClose={onClose} width={1040} height="calc(88 * var(--vh))" scope="pp-settings" testid="pp-settings"
      footer={<>
        {dirty && <span className="warn grow" data-testid="pp-unsaved">{t("xs.unsaved")}</span>}
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} disabled={busy} testid="pp-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="pp-cancel" />
      </>}>
      <div className="pp-dialog">
        <div className="tabs pp-tabs">
          {tabBtn(TAB_GENERAL, t("pp.tab.general"), "pp-tab-general")}
          {mach.data?.groups.map((g) => (
            <span key={g.key} className="pp-tabgrp" data-testid={`pp-group-${g.key}`}>
              {g.machines.map((m) => tabBtn(m.key, m.name, `pp-machine-${m.key}`, !view(m).enabled, !isOpen(m.key)))}
            </span>
          ))}
          {tabBtn(TAB_EXTRAS, t("pp.tab.extras"), "pp-tab-extras", false, false, FileText)}
          {tabBtn(TAB_TEMPLATES, t("pp.tab.templates"), "pp-tab-templates")}
        </div>
        <div className="pp-tabbody">
          {tab === TAB_GENERAL && draft && (
            <Check checked={draft.prefix} label={t("pp.machine_prefix")} testid="pp-machine-prefix"
              onChange={(v) => change((b) => { b.prefix = v; })} />
          )}
          {cur && <MachinePane key={cur.key} m={view(cur)} profiles={profiles} onChange={change}
            opened={isOpen(cur.key)} canEdit={canEdit} onAccess={(v) => setOpen(cur.key, v)} />}
          {tab === TAB_EXTRAS && <ExtrasPane extras={acc.data?.extras ?? []} closed={extClosed} canEdit={canEdit} onToggle={setExtra} />}
          {tab === TAB_TEMPLATES && <TemplatesPane list={profiles} />}
        </div>
      </div>
    </Modal>
  );
}
