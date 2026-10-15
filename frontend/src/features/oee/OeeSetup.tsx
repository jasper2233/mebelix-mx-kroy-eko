// OEE sozlamalari: stanoklar va ideal tezliklar, smena kalendari, sabablar ro'yxati, hisob parametrlari (+ demo).
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { FlaskConical, Pencil, Plus, Save, Trash, Wrench } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del, get, patch, post, put } from "../../api/client";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Btn, Check, Field, Modal, Num, Sel, Txt } from "../../shared/ui";
import {
  fmtLocal, reasonName, tzStr, useOeeMachines, useOeeMeta, useOeeReasons, useOeeShifts, type OeeConfig, type OeeMachine, type OeeReason, type OeeShift, type ShiftPreview,
} from "./oeeApi";

const refresh = () => qc.invalidateQueries({ queryKey: ["oee"] });
const KINDS = ["saw", "edge", "cnc", "other"] as const;

// ───────────────────────── Stanoklar ─────────────────────────
interface CatalogRow { key: string; name: string; group: string; added: boolean }

function MachineDialog({ m, onClose }: { m: OeeMachine | null; onClose: () => void }) {
  const { t } = useTranslation();
  const cat = useQuery({ queryKey: ["oee", "catalog"], queryFn: () => get<CatalogRow[]>("/oee/machines/catalog") });
  const [f, setF] = useState({
    key: m?.key ?? "", name: m?.name ?? "", kind: (m?.kind ?? "saw") as OeeMachine["kind"], pp_key: m?.pp_key ?? "",
    speed: m?.cut_speed_mm_s ?? 1000, change: m?.cut_change_s ?? 5, load: m?.sheet_load_s ?? 25, unit_s: m?.ideal_unit_s ?? null as number | null,
    active: m?.active ?? true, note: m?.note ?? "",
  });
  const set = (p: Partial<typeof f>) => setF((x) => ({ ...x, ...p }));
  const editing = !!m;
  const pickPp = (k: string) => {
    const row = cat.data?.find((c) => c.key === k);
    set({ pp_key: k, ...(row && !editing ? { key: f.key || row.key, name: f.name || row.name, kind: row.group === "cnc" ? "cnc" as const : "saw" as const } : {}) });
  };
  const suggest = async () => {
    if (!m) return;
    const r = await call(() => get<{ suggested: { cut_speed_mm_s?: number }; assumption: string }>(`/oee/machines/${m.key}/suggest`));
    if (!r) return;
    if (r.suggested.cut_speed_mm_s) { set({ speed: r.suggested.cut_speed_mm_s }); useUI.getState().toast(t("oee.m.suggest_ok", { v: r.suggested.cut_speed_mm_s, a: r.assumption }), "ok"); }
    else useUI.getState().toast(t("oee.m.suggest_none"), "info");
  };
  const save = async () => {
    const body = { name: f.name.trim() || undefined, kind: f.kind, pp_key: f.pp_key || null, cut_speed_mm_s: f.speed, cut_change_s: f.change,
      sheet_load_s: f.load, ideal_unit_s: f.unit_s, active: f.active, note: f.note };
    const r = editing ? await call(() => patch(`/oee/machines/${m!.key}`, body)) : await call(() => post("/oee/machines", { ...body, key: f.key.trim() || undefined }));
    if (r) { void refresh(); onClose(); }
  };
  // namunaviy karta bo'yicha ideal sikl (formula ko'rinishi): 12 m, 20 kesim
  const ex = (12 * 1000) / Math.max(f.speed, 1e-9) + 20 * f.change + f.load;
  const canSave = editing ? !!f.name.trim() : !!(f.key.trim() || f.pp_key);
  return (
    <Modal title={editing ? t("oee.m.edit") : t("oee.m.add")} onClose={onClose} width={600} testid="oee-machine-dialog"
      footer={<><Btn kind="primary" label={t("app.save")} disabled={!canSave} onClick={() => void save()} testid="oee-m-save" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("oee.m.pp")} hint={t("oee.m.pp_hint")}>
          <Sel value={f.pp_key} width={280} testid="oee-m-pp" onChange={pickPp}
            options={[{ value: "", label: t("oee.m.pp_none") }, ...(cat.data ?? []).map((c) => ({ value: c.key, label: `${c.name}${c.added && c.key !== m?.key ? " ✓" : ""}` }))]} />
        </Field>
        <Field label={t("oee.m.key")} hint={t("oee.m.key_hint")}>
          <Txt value={f.key} width={200} disabled={editing} testid="oee-m-key" onCommit={(v) => set({ key: v })} />
        </Field>
        <Field label={t("oee.m.name")}><Txt value={f.name} width={280} testid="oee-m-name" onCommit={(v) => set({ name: v })} /></Field>
        <Field label={t("oee.m.kind")}>
          <Sel value={f.kind} width={200} testid="oee-m-kind" onChange={(v) => set({ kind: v })} options={KINDS.map((k) => ({ value: k, label: t(`oee.kind.${k}`) }))} />
        </Field>
        <h4 className="oee-sub">{t("oee.m.ideal")}</h4>
        <Field label={t("oee.m.speed")} unit={t("oee.u.mm_s")} hint={t("oee.m.speed_hint")}>
          <span className="row gap"><Num value={f.speed} min={1} width={90} testid="oee-m-speed" onCommit={(v) => set({ speed: v ?? 1000 })} />
            <span className="muted" data-testid="oee-m-speed-conv">= {(f.speed * 0.06).toFixed(1)} {t("oee.u.m_min")}</span>
            {editing && m?.pp_key && <Btn small icon={Wrench} label={t("oee.m.from_pp")} testid="oee-m-suggest" onClick={() => void suggest()} />}</span>
        </Field>
        <Field label={t("oee.m.change")} unit={t("oee.u.s")} hint={t("oee.m.change_hint")}>
          <Num value={f.change} min={0} width={90} testid="oee-m-change" onCommit={(v) => set({ change: v ?? 0 })} /></Field>
        <Field label={t("oee.m.load")} unit={t("oee.u.s")} hint={t("oee.m.load_hint")}>
          <Num value={f.load} min={0} width={90} testid="oee-m-load" onCommit={(v) => set({ load: v ?? 0 })} /></Field>
        <Field label={t("oee.m.unit_s")} unit={t("oee.u.s")} hint={t("oee.m.unit_s_hint")}>
          <Num value={f.unit_s} allowEmpty min={0.1} width={90} testid="oee-m-unit-s" onCommit={(v) => set({ unit_s: v })} /></Field>
        <p className="muted oee-note" data-testid="oee-m-example">{t("oee.m.example", { s: ex.toFixed(1) })}</p>
        <Field label=" "><Check checked={f.active} label={t("oee.m.active")} onChange={(v) => set({ active: v })} testid="oee-m-active" /></Field>
        <Field label={t("oee.ev.note")}><Txt value={f.note} width={300} onCommit={(v) => set({ note: v })} /></Field>
      </div>
    </Modal>
  );
}

export function OeeMachines() {
  const { t } = useTranslation();
  const q = useOeeMachines();
  const [dlg, setDlg] = useState<{ m: OeeMachine | null } | null>(null);
  const remove = async (m: OeeMachine) => {
    if (!(await askConfirm(t("oee.m.delete_q", { n: m.name })))) return;
    const r = await call(() => del<{ events_deleted: number }>(`/oee/machines/${m.key}`));
    if (r === undefined) {
      if (await askConfirm(t("oee.m.force_q", { n: m.name }), undefined, { danger: true })) await call(() => del(`/oee/machines/${m.key}`, { force: true }));
    }
    void refresh();
  };
  return (
    <div className="oee-body" data-testid="oee-machines">
      <div className="oee-bar"><h3>{t("oee.tab.machines")}</h3><span className="grow" />
        <Btn kind="primary" small icon={Plus} label={t("oee.add_machine")} testid="oee-m-add" onClick={() => setDlg({ m: null })} /></div>
      <p className="muted oee-note">{t("oee.m.intro")}</p>
      <div className="oee-card">
        {(q.data?.length ?? 0) === 0 ? <div className="oee-empty">{t("oee.m.none")}</div> : (
          <div className="scroll oee-tablewrap">
            <table className="simple oee-table" data-testid="oee-m-table">
              <thead><tr><th>{t("oee.m.key")}</th><th>{t("oee.m.name")}</th><th>{t("oee.m.kind")}</th><th>{t("oee.m.pp")}</th><th>{t("oee.m.speed_short")}</th>
                <th>{t("oee.m.change_short")}</th><th>{t("oee.m.load_short")}</th><th>{t("oee.m.unit_s_short")}</th><th>{t("oee.m.active")}</th><th /></tr></thead>
              <tbody>{q.data!.map((m) => (
                <tr key={m.key} data-testid={`oee-m-${m.key}`} className={m.active ? "" : "muted"}>
                  <td><code>{m.key}</code></td><td>{m.name}</td><td>{t(`oee.kind.${m.kind}`)}</td><td>{m.pp_name ?? "—"}</td>
                  <td className="num">{m.cut_speed_mm_s ?? "—"}</td><td className="num">{m.cut_change_s ?? "—"}</td><td className="num">{m.sheet_load_s ?? "—"}</td>
                  <td className="num">{m.ideal_unit_s ?? "—"}</td><td>{m.active ? "✓" : "—"}</td>
                  <td className="oee-act">
                    <button type="button" className="ibtn" title={t("app.edit")} onClick={() => setDlg({ m })} data-testid={`oee-m-edit-${m.key}`}><Pencil size={14} /></button>
                    <button type="button" className="ibtn" title={t("app.delete")} onClick={() => void remove(m)} data-testid={`oee-m-del-${m.key}`}><Trash size={14} /></button>
                  </td>
                </tr>))}</tbody>
            </table>
          </div>
        )}
      </div>
      {dlg && <MachineDialog m={dlg.m} onClose={() => setDlg(null)} />}
    </div>
  );
}

// ───────────────────────── Smenalar ─────────────────────────
interface ShiftForm {
  kind: "shift" | "off"; name: string; machine: string; weekdays: number[]; start: string; end: string; breaks: { start: string; end: string; name: string }[];
  valid_from: string; valid_to: string; active: boolean;
}

function ShiftDialog({ s, kind, onClose }: { s: OeeShift | null; kind: "shift" | "off"; onClose: () => void }) {
  const { t } = useTranslation();
  const machines = useOeeMachines();
  const [f, setF] = useState<ShiftForm>({
    kind: s?.kind ?? kind, name: s?.name ?? "", machine: s?.machine ?? "", weekdays: s?.weekdays ?? [0, 1, 2, 3, 4, 5], start: s?.start ?? "08:00",
    end: s?.end ?? "17:00", breaks: s?.breaks ?? [{ start: "12:00", end: "13:00", name: "" }], valid_from: s?.valid_from ?? "", valid_to: s?.valid_to ?? "",
    active: s?.active ?? true,
  });
  const set = (p: Partial<ShiftForm>) => setF((x) => ({ ...x, ...p }));
  const off = f.kind === "off";
  const save = async () => {
    const body = off
      ? { kind: "off", name: f.name, machine: f.machine || null, valid_from: f.valid_from || null, valid_to: f.valid_to || null, active: f.active }
      : { kind: "shift", name: f.name, machine: f.machine || null, weekdays: f.weekdays, start: f.start, end: f.end, breaks: f.breaks,
        valid_from: f.valid_from || null, valid_to: f.valid_to || null, active: f.active };
    const r = s ? await call(() => put(`/oee/shifts/${s.id}`, body)) : await call(() => post("/oee/shifts", body));
    if (r) { void refresh(); onClose(); }
  };
  const tgl = (d: number) => set({ weekdays: f.weekdays.includes(d) ? f.weekdays.filter((x) => x !== d) : [...f.weekdays, d].sort() });
  return (
    <Modal title={off ? t("oee.s.off_title") : s ? t("oee.s.edit") : t("oee.s.add")} onClose={onClose} width={560} testid="oee-shift-dialog"
      footer={<><Btn kind="primary" label={t("app.save")} onClick={() => void save()} testid="oee-s-save" disabled={off ? !f.valid_from || !f.valid_to : f.weekdays.length === 0} />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("oee.s.name")}><Txt value={f.name} width={240} testid="oee-s-name" onCommit={(v) => set({ name: v })} /></Field>
        <Field label={t("oee.col.machine")} hint={t("oee.s.machine_hint")}>
          <Sel value={f.machine} width={240} testid="oee-s-machine" onChange={(v) => set({ machine: v })}
            options={[{ value: "", label: t("oee.all_machines") }, ...(machines.data ?? []).map((m) => ({ value: m.key, label: m.name }))]} />
        </Field>
        {!off && <>
          <Field label={t("oee.s.weekdays")}>
            <span className="oee-wd">{[0, 1, 2, 3, 4, 5, 6].map((d) => (
              <label key={d} className={f.weekdays.includes(d) ? "on" : ""}><input type="checkbox" checked={f.weekdays.includes(d)} onChange={() => tgl(d)} data-testid={`oee-s-wd-${d}`} />{t(`oee.wd.${d}`)}</label>))}</span>
          </Field>
          <Field label={t("oee.s.time")} hint={t("oee.s.time_hint")}>
            <span className="row gap"><input type="time" className="inp" value={f.start} data-testid="oee-s-start" onChange={(e) => set({ start: e.target.value })} /> —
              <input type="time" className="inp" value={f.end} data-testid="oee-s-end" onChange={(e) => set({ end: e.target.value })} /></span>
          </Field>
          <h4 className="oee-sub">{t("oee.s.breaks")}</h4>
          {f.breaks.map((b, i) => (
            <div key={i} className="row gap oee-brk">
              <input type="time" className="inp" value={b.start} onChange={(e) => set({ breaks: f.breaks.map((x, j) => (j === i ? { ...x, start: e.target.value } : x)) })} /> —
              <input type="time" className="inp" value={b.end} onChange={(e) => set({ breaks: f.breaks.map((x, j) => (j === i ? { ...x, end: e.target.value } : x)) })} />
              <input className="inp" placeholder={t("oee.s.break_name")} value={b.name} style={{ width: 140 }}
                onChange={(e) => set({ breaks: f.breaks.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })} />
              <button type="button" className="ibtn" onClick={() => set({ breaks: f.breaks.filter((_, j) => j !== i) })}><Trash size={14} /></button>
            </div>
          ))}
          <Btn small icon={Plus} label={t("oee.s.add_break")} onClick={() => set({ breaks: [...f.breaks, { start: "12:00", end: "12:30", name: "" }] })} />
        </>}
        <Field label={off ? t("oee.s.dates") : t("oee.s.valid")} hint={t("oee.s.valid_hint")}>
          <span className="row gap"><input type="date" className="inp" value={f.valid_from} data-testid="oee-s-from" onChange={(e) => set({ valid_from: e.target.value })} /> —
            <input type="date" className="inp" value={f.valid_to} data-testid="oee-s-to" onChange={(e) => set({ valid_to: e.target.value })} /></span>
        </Field>
        <Field label=" "><Check checked={f.active} label={t("oee.m.active")} onChange={(v) => set({ active: v })} /></Field>
      </div>
    </Modal>
  );
}

export function OeeShifts() {
  const { t } = useTranslation();
  const q = useOeeShifts();
  const machines = useOeeMachines();
  const off = useOeeMeta().data?.config.tz_offset_min ?? 0;
  const [dlg, setDlg] = useState<{ s: OeeShift | null; kind: "shift" | "off" } | null>(null);
  const [pm, setPm] = useState("");
  const prev = useQuery({ queryKey: ["oee", "shift-preview", pm, q.data], queryFn: () => get<ShiftPreview[]>("/oee/shifts/preview", { machine: pm || undefined, period: "this_week" }) });
  const mname = (k: string | null) => (k ? machines.data?.find((m) => m.key === k)?.name ?? k : t("oee.all_machines"));
  const remove = async (s: OeeShift) => {
    if (!(await askConfirm(t("oee.s.delete_q")))) return;
    await call(() => del(`/oee/shifts/${s.id}`));
    void refresh();
  };
  const rows = (kind: "shift" | "off") => (q.data ?? []).filter((s) => s.kind === kind);
  const acts = (s: OeeShift) => (
    <td className="oee-act">
      <button type="button" className="ibtn" title={t("app.edit")} onClick={() => setDlg({ s, kind: s.kind })} data-testid={`oee-s-edit-${s.id}`}><Pencil size={14} /></button>
      <button type="button" className="ibtn" title={t("app.delete")} onClick={() => void remove(s)} data-testid={`oee-s-del-${s.id}`}><Trash size={14} /></button>
    </td>
  );
  return (
    <div className="oee-body" data-testid="oee-shifts">
      <div className="oee-bar"><h3>{t("oee.tab.shifts")}</h3><span className="grow" />
        <Btn small icon={Plus} label={t("oee.s.add_off")} testid="oee-s-add-off" onClick={() => setDlg({ s: null, kind: "off" })} />
        <Btn kind="primary" small icon={Plus} label={t("oee.s.add")} testid="oee-s-add" onClick={() => setDlg({ s: null, kind: "shift" })} /></div>
      <p className="muted oee-note">{t("oee.s.intro", { h: tzStr(off) })}</p>
      <div className="oee-card">
        {rows("shift").length === 0 ? <div className="oee-empty">{t("oee.s.none")}</div> : (
          <div className="scroll oee-tablewrap">
            <table className="simple oee-table" data-testid="oee-s-table">
              <thead><tr><th>{t("oee.s.name")}</th><th>{t("oee.col.machine")}</th><th>{t("oee.s.weekdays")}</th><th>{t("oee.s.time")}</th><th>{t("oee.s.breaks")}</th>
                <th>{t("oee.s.valid")}</th><th>{t("oee.m.active")}</th><th /></tr></thead>
              <tbody>{rows("shift").map((s) => (
                <tr key={s.id} className={s.active ? "" : "muted"}>
                  <td>{s.name}</td><td>{mname(s.machine)}</td><td>{s.weekdays.map((d) => t(`oee.wd.${d}`)).join(" ")}</td><td>{s.start}–{s.end}</td>
                  <td>{s.breaks.map((b) => `${b.start}–${b.end}`).join(", ") || "—"}</td>
                  <td>{s.valid_from || s.valid_to ? `${s.valid_from ?? "…"} → ${s.valid_to ?? "…"}` : "—"}</td><td>{s.active ? "✓" : "—"}</td>{acts(s)}
                </tr>))}</tbody>
            </table>
          </div>
        )}
      </div>
      <div className="oee-card" data-testid="oee-off-card">
        <div className="oee-card-head"><h3>{t("oee.s.off_title")}</h3></div>
        {rows("off").length === 0 ? <div className="oee-empty">{t("oee.s.off_none")}</div> : (
          <table className="simple oee-table"><tbody>{rows("off").map((s) => (
            <tr key={s.id}><td>{s.name || "—"}</td><td>{mname(s.machine)}</td><td>{s.valid_from} → {s.valid_to}</td>{acts(s)}</tr>))}</tbody></table>
        )}
      </div>
      <div className="oee-card" data-testid="oee-s-preview">
        <div className="oee-card-head"><h3>{t("oee.s.preview")}</h3>
          <Sel value={pm} width={220} onChange={setPm} options={[{ value: "", label: t("oee.all_machines") }, ...(machines.data ?? []).map((m) => ({ value: m.key, label: m.name }))]} /></div>
        {(prev.data?.length ?? 0) === 0 ? <div className="oee-empty">{t("oee.s.preview_none")}</div> : (
          <table className="simple oee-table"><thead><tr><th>{t("oee.col.date")}</th><th>{t("oee.col.shift")}</th><th>{t("oee.s.time")}</th><th>{t("oee.col.planned")}</th></tr></thead>
            <tbody>{prev.data!.map((p) => (<tr key={p.start}><td>{p.date}</td><td>{p.name}</td>
              <td>{fmtLocal(p.start, off).slice(6)}–{fmtLocal(p.end, off).slice(6)}</td><td className="num">{p.planned_min} {t("oee.u.min")}</td></tr>))}</tbody></table>
        )}
      </div>
      {dlg && <ShiftDialog s={dlg.s} kind={dlg.kind} onClose={() => setDlg(null)} />}
    </div>
  );
}

// ───────────────────────── Sabablar ─────────────────────────
function ReasonDialog({ r, onClose }: { r: OeeReason | null; onClose: () => void }) {
  const { t } = useTranslation();
  const [f, setF] = useState({ code: r?.code ?? "", name_ru: r?.name_ru ?? "", name_uz: r?.name_uz ?? "", kind: r?.kind ?? "downtime" as OeeReason["kind"],
    planned: r?.planned ?? false, active: r?.active ?? true });
  const set = (p: Partial<typeof f>) => setF((x) => ({ ...x, ...p }));
  const save = async () => {
    const res = r ? await call(() => patch(`/oee/reasons/${r.code}`, { name_ru: f.name_ru, name_uz: f.name_uz, kind: f.kind, planned: f.planned, active: f.active }))
      : await call(() => post("/oee/reasons", f));
    if (res) { void refresh(); onClose(); }
  };
  return (
    <Modal title={r ? t("oee.r.edit") : t("oee.r.add")} onClose={onClose} width={520} testid="oee-reason-dialog"
      footer={<><Btn kind="primary" label={t("app.save")} onClick={() => void save()} testid="oee-r-save" disabled={!f.code || !(f.name_ru || f.name_uz)} /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("oee.r.code")} hint={t("oee.r.code_hint")}><Txt value={f.code} width={180} disabled={!!r} testid="oee-r-code" onCommit={(v) => set({ code: v.trim().toLowerCase() })} /></Field>
        <Field label={t("oee.r.name_ru")}><Txt value={f.name_ru} width={260} testid="oee-r-ru" onCommit={(v) => set({ name_ru: v })} /></Field>
        <Field label={t("oee.r.name_uz")}><Txt value={f.name_uz} width={260} testid="oee-r-uz" onCommit={(v) => set({ name_uz: v })} /></Field>
        <Field label={t("oee.r.kind")}>
          <Sel value={f.kind} width={200} testid="oee-r-kind" onChange={(v) => set({ kind: v })} options={(["downtime", "reject"] as const).map((k) => ({ value: k, label: t(`oee.r.kind_${k}`) }))} />
        </Field>
        {f.kind === "downtime" && <Field label=" "><Check checked={f.planned} label={t("oee.r.planned")} onChange={(v) => set({ planned: v })} testid="oee-r-planned" /></Field>}
        {f.kind === "downtime" && <p className="muted oee-note">{t("oee.r.planned_hint")}</p>}
        <Field label=" "><Check checked={f.active} label={t("oee.m.active")} onChange={(v) => set({ active: v })} /></Field>
      </div>
    </Modal>
  );
}

export function OeeReasons() {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const q = useOeeReasons();
  const [dlg, setDlg] = useState<{ r: OeeReason | null } | null>(null);
  const remove = async (r: OeeReason) => {
    if (!(await askConfirm(t("oee.r.delete_q", { n: reasonName(r, lang) })))) return;
    await call(() => del(`/oee/reasons/${r.code}`));
    void refresh();
  };
  const section = (kind: "downtime" | "reject") => (
    <div className="oee-card" data-testid={`oee-r-${kind}`}>
      <div className="oee-card-head"><h3>{t(`oee.r.kind_${kind}`)}</h3></div>
      <div className="scroll oee-tablewrap">
        <table className="simple oee-table"><thead><tr><th>{t("oee.r.code")}</th><th>{t("oee.r.name")}</th>{kind === "downtime" && <th>{t("oee.r.planned_short")}</th>}<th>{t("oee.m.active")}</th><th /></tr></thead>
          <tbody>{(q.data ?? []).filter((r) => r.kind === kind).map((r) => (
            <tr key={r.code} className={r.active ? "" : "muted"} data-testid={`oee-r-row-${r.code}`}>
              <td><code>{r.code}</code></td><td>{reasonName(r, lang)}</td>{kind === "downtime" && <td>{r.planned ? "✓" : "—"}</td>}<td>{r.active ? "✓" : "—"}</td>
              <td className="oee-act">
                <button type="button" className="ibtn" title={t("app.edit")} onClick={() => setDlg({ r })} data-testid={`oee-r-edit-${r.code}`}><Pencil size={14} /></button>
                {!r.system && <button type="button" className="ibtn" title={t("app.delete")} onClick={() => void remove(r)}><Trash size={14} /></button>}
              </td>
            </tr>))}</tbody></table>
      </div>
    </div>
  );
  return (
    <div className="oee-body" data-testid="oee-reasons">
      <div className="oee-bar"><h3>{t("oee.tab.reasons")}</h3><span className="grow" />
        <Btn kind="primary" small icon={Plus} label={t("oee.r.add")} testid="oee-r-add" onClick={() => setDlg({ r: null })} /></div>
      <p className="muted oee-note">{t("oee.r.intro")}</p>
      {section("downtime")}{section("reject")}
      {dlg && <ReasonDialog r={dlg.r} onClose={() => setDlg(null)} />}
    </div>
  );
}

// ───────────────────────── Parametrlar (+ demo) ─────────────────────────
export function OeeParams() {
  const { t } = useTranslation();
  const meta = useOeeMeta();
  const [c, setC] = useState<OeeConfig | null>(null);
  useEffect(() => { if (meta.data) setC(meta.data.config); }, [meta.data]);
  if (!c || !meta.data) return null;
  const save = async () => {
    const r = await call(() => put("/oee/config", c));
    if (r) { void refresh(); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const demo = async (on: boolean) => {
    const r = await call(() => (on ? post<{ events: number }>("/oee/demo-seed", undefined, { days: 14 }) : del<{ events: number }>("/oee/demo-seed")));
    if (r) { void refresh(); useUI.getState().toast(on ? t("oee.demo_done", { n: r.events }) : t("oee.demo_cleared"), "ok"); }
  };
  const b = meta.data.bands;
  return (
    <div className="oee-body" data-testid="oee-params">
      <div className="oee-bar"><h3>{t("oee.tab.params")}</h3><span className="grow" />
        <Btn kind="primary" small icon={Save} label={t("app.save")} testid="oee-p-save" onClick={() => void save()} /></div>
      <div className="oee-card">
        <div className="form1">
          <Field label={t("oee.p.tz")} unit={t("oee.u.h")} hint={t("oee.p.tz_hint")}>
            <Num value={c.tz_offset_min / 60} width={80} min={-12} max={14} testid="oee-p-tz" onCommit={(v) => setC({ ...c, tz_offset_min: Math.round((v ?? 0) * 60) })} /></Field>
          <Field label={t("oee.p.idle")} unit={t("oee.u.min")} hint={t("oee.p.idle_hint")}>
            <Num value={c.idle_gap_s / 60} width={80} min={0} max={120} testid="oee-p-idle" onCommit={(v) => setC({ ...c, idle_gap_s: Math.round((v ?? 5) * 60) })} /></Field>
          <Field label={t("oee.p.cap")} hint={t("oee.p.cap_hint")}>
            <Num value={c.run_cap_factor} width={80} min={1} max={20} testid="oee-p-cap" onCommit={(v) => setC({ ...c, run_cap_factor: v ?? 3 })} /></Field>
          <Field label={t("oee.p.unit")} hint={t("oee.p.unit_hint")}>
            <Sel value={c.unit} width={220} testid="oee-p-unit" onChange={(v) => setC({ ...c, unit: v })}
              options={[{ value: "sheet" as const, label: t("oee.p.unit_sheet") }, { value: "part" as const, label: t("oee.p.unit_part") }]} /></Field>
          <Field label=" "><Check checked={c.include_overtime} label={t("oee.p.overtime")} onChange={(v) => setC({ ...c, include_overtime: v })} testid="oee-p-overtime" /></Field>
          <p className="muted oee-note">{t("oee.p.overtime_hint")}</p>
        </div>
      </div>
      <div className="oee-card">
        <div className="oee-card-head"><h3>{t("oee.p.formulas")}</h3></div>
        <ul className="oee-formulas">
          <li>{t("oee.p.f_oee")}</li><li>{t("oee.p.f_a")}</li><li>{t("oee.p.f_p")}</li><li>{t("oee.p.f_q")}</li><li>{t("oee.p.f_idle", { min: c.idle_gap_s / 60 })}</li>
          <li>{t("oee.p.f_bands", { low: Math.round(b.low * 100), high: Math.round(b.high * 100) })}</li>
        </ul>
      </div>
      {meta.data.demo_enabled && (
        <div className="oee-card" data-testid="oee-demo-card">
          <div className="oee-card-head"><h3>{t("oee.demo_title")}</h3></div>
          <p className="muted oee-note">{t("oee.demo_hint")}</p>
          <div className="row gap">
            <Btn icon={FlaskConical} label={t("oee.demo_seed")} testid="oee-demo-seed" onClick={() => void demo(true)} />
            <Btn kind="danger" icon={Trash} label={t("oee.demo_clear")} testid="oee-demo-clear" onClick={() => void demo(false)} />
          </div>
        </div>
      )}
    </div>
  );
}
