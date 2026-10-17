// OEE hodisalari: ro'yxat (filtr), qo'lda qo'shish/tahrirlash/o'chirish, hodisasiz bo'shliqlarga sabab belgilash.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Pencil, Plus, Trash, ArrowUpFromLine } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del, download, patch, post } from "../../api/client";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Btn, Field, Modal, Sel } from "../../shared/ui";
import { OeeFilters } from "./OeeDashboard";
import {
  fmtLocal, fmtMin, inputToIso, isoToInput, periodQuery, reasonName, tzStr, useOeeEvents, useOeeGaps, useOeeMachines, useOeeMeta, useOeeReasons,
  useOeeUI, type OeeEvent,
} from "./oeeApi";

const PAGE = 50;
type EType = "run" | "downtime" | "reject";

interface Form {
  type: EType; machine: string; start: string; end: string; qty: string; reject_qty: string; unit: "part" | "sheet"; parts: string;
  cut_length_m: string; cuts: string; ideal_cycle_s: string; reason: string; note: string;
}

const num = (s: string): number | null => { const v = s.trim().replace(",", "."); if (v === "") return null; const n = Number(v); return Number.isFinite(n) ? n : null; };
const str = (v: number | null | undefined) => (v === null || v === undefined ? "" : String(v));

function formOf(e: OeeEvent | null, machine: string, off: number): Form {
  if (!e) {
    const now = isoToInput(new Date().toISOString(), off);
    return { type: "run", machine, start: "", end: now, qty: "1", reject_qty: "0", unit: "part", parts: "", cut_length_m: "", cuts: "", ideal_cycle_s: "",
      reason: "", note: "" };
  }
  return { type: e.type, machine: e.machine, start: isoToInput(e.start, off), end: isoToInput(e.end, off), qty: str(e.qty), reject_qty: str(e.reject_qty),
    unit: e.unit === "sheet" ? "sheet" : "part", parts: str(e.parts), cut_length_m: str(e.cut_length_m), cuts: str(e.cuts),
    ideal_cycle_s: str(e.ideal_cycle_s), reason: e.reason ?? "", note: e.note ?? "" };
}

function EventDialog({ ev, defMachine, onClose }: { ev: OeeEvent | null; defMachine: string; onClose: () => void }) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const meta = useOeeMeta();
  const off = meta.data?.config.tz_offset_min ?? 0;
  const machines = useOeeMachines();
  const reasons = useOeeReasons();
  const [f, setF] = useState<Form>(() => formOf(ev, defMachine || machines.data?.[0]?.key || "", off));
  const set = (p: Partial<Form>) => setF((x) => ({ ...x, ...p }));
  const kind = f.type === "reject" ? "reject" : "downtime";
  const rs = (reasons.data ?? []).filter((r) => r.kind === kind && (r.active || r.code === f.reason));
  const editing = !!ev;

  const save = async () => {
    const end = inputToIso(f.end, off), start = inputToIso(f.start, off);
    const body: Record<string, unknown> = { machine: f.machine, note: f.note.trim() || null };
    if (f.type === "run") {
      Object.assign(body, { end, start, qty: num(f.qty) ?? 1, reject_qty: num(f.reject_qty) ?? 0, unit: f.unit, parts: num(f.parts),
        cut_length_m: num(f.cut_length_m), cuts: num(f.cuts), ideal_cycle_s: num(f.ideal_cycle_s) });
    } else if (f.type === "downtime") {
      Object.assign(body, { start, end, reason: f.reason });
    } else {
      Object.assign(body, { end, qty: num(f.qty) ?? 1, unit: f.unit, reason: f.reason || null });
    }
    const r = editing
      ? await call(() => patch(`/oee/events/${ev!.id}`, body))
      : await call(() => post("/oee/events", { type: f.type, source: "manual", ...Object.fromEntries(Object.entries(body).filter(([, v]) => v !== null)) }));
    if (r) { void qc.invalidateQueries({ queryKey: ["oee"] }); useUI.getState().toast(t("app.saved"), "ok"); onClose(); }
  };
  const dt = (k: "start" | "end", testid: string) => (
    <input type="datetime-local" className="inp" value={f[k]} data-testid={testid} onChange={(e) => set({ [k]: e.target.value } as Partial<Form>)} />
  );
  const numInp = (k: keyof Form, testid: string, w = 90) => (
    <input className="inp num" style={{ width: w }} value={f[k] as string} data-testid={testid} onChange={(e) => set({ [k]: e.target.value } as Partial<Form>)} />
  );
  const needEnd = f.type !== "downtime";
  const ok = !!f.machine && (needEnd ? !!inputToIso(f.end, off) : !!inputToIso(f.start, off)) && (f.type !== "downtime" || !!f.reason);
  return (
    <Modal title={editing ? t("oee.ev.edit") : t("oee.ev.add")} onClose={onClose} width={560} testid="oee-event-dialog"
      footer={<><Btn kind="primary" label={t("app.save")} disabled={!ok} onClick={() => void save()} testid="oee-ev-save" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("oee.ev.type")}>
          <Sel value={f.type} width={220} disabled={editing} testid="oee-ev-type" onChange={(v) => {
            // turga mos boshlang'ich vaqtlar: to'xtash — boshlanish (tugash bo'sh = davom etmoqda); qolganlari — tugash vaqti
            const now = isoToInput(new Date().toISOString(), off);
            set(v === "downtime" ? { type: v, reason: "", start: f.start || f.end || now, end: "" } : { type: v as EType, reason: "", end: f.end || f.start || now });
          }}
            options={(["run", "downtime", "reject"] as const).map((x) => ({ value: x, label: t(`oee.type.${x}`) }))} />
        </Field>
        <Field label={t("oee.col.machine")}>
          <Sel value={f.machine} width={260} testid="oee-ev-machine" onChange={(v) => set({ machine: v })}
            options={(machines.data ?? []).map((m) => ({ value: m.key, label: m.name }))} />
        </Field>
        {f.type === "downtime" && <>
          <Field label={t("oee.ev.start")} hint={t("oee.ev.tz_hint", { h: tzStr(off) })}>{dt("start", "oee-ev-start")}</Field>
          <Field label={t("oee.ev.end_open")} hint={t("oee.ev.end_open_hint")}>{dt("end", "oee-ev-end")}</Field>
          <Field label={t("oee.ev.reason")}>
            <Sel value={f.reason} width={260} testid="oee-ev-reason" onChange={(v) => set({ reason: v })}
              options={[{ value: "", label: "—" }, ...rs.map((r) => ({ value: r.code, label: reasonName(r, lang) }))]} />
          </Field>
        </>}
        {f.type === "run" && <>
          <Field label={t("oee.ev.run_end")} hint={t("oee.ev.tz_hint", { h: tzStr(off) })}>{dt("end", "oee-ev-end")}</Field>
          <Field label={t("oee.ev.run_start")} hint={t("oee.ev.run_start_hint")}>{dt("start", "oee-ev-start")}</Field>
          <Field label={t("oee.ev.sheets")}>{numInp("qty", "oee-ev-qty")}</Field>
          <Field label={t("oee.ev.parts")}>{numInp("parts", "oee-ev-parts")}</Field>
          <Field label={t("oee.ev.reject_qty")} unit={<Sel value={f.unit} width={110} onChange={(v) => set({ unit: v })}
            options={[{ value: "part" as const, label: t("oee.unit_short.part") }, { value: "sheet" as const, label: t("oee.unit_short.sheet") }]} />}>
            {numInp("reject_qty", "oee-ev-reject")}</Field>
          <Field label={t("oee.ev.cut_length")} unit="m">{numInp("cut_length_m", "oee-ev-cutlen")}</Field>
          <Field label={t("oee.ev.cuts")}>{numInp("cuts", "oee-ev-cuts")}</Field>
          <Field label={t("oee.ev.ideal")} hint={t("oee.ev.ideal_hint")} unit="s">{numInp("ideal_cycle_s", "oee-ev-ideal")}</Field>
        </>}
        {f.type === "reject" && <>
          <Field label={t("oee.ev.reject_time")} hint={t("oee.ev.tz_hint", { h: tzStr(off) })}>{dt("end", "oee-ev-end")}</Field>
          <Field label={t("oee.ev.reject_count")} unit={<Sel value={f.unit} width={110} onChange={(v) => set({ unit: v })}
            options={[{ value: "part" as const, label: t("oee.unit_short.part") }, { value: "sheet" as const, label: t("oee.unit_short.sheet") }]} />}>
            {numInp("qty", "oee-ev-qty")}</Field>
          <Field label={t("oee.ev.reason")}>
            <Sel value={f.reason} width={260} testid="oee-ev-reason" onChange={(v) => set({ reason: v })}
              options={[{ value: "", label: "—" }, ...rs.map((r) => ({ value: r.code, label: reasonName(r, lang) }))]} />
          </Field>
        </>}
        <Field label={t("oee.ev.note")}>
          <input className="inp" style={{ width: 300 }} value={f.note} data-testid="oee-ev-note" onChange={(e) => set({ note: e.target.value })} />
        </Field>
      </div>
    </Modal>
  );
}

function GapDialog({ machine, gap, onClose }: { machine: string; gap: { start: string; end: string; minutes: number }; onClose: () => void }) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const reasons = useOeeReasons();
  const off = useOeeMeta().data?.config.tz_offset_min ?? 0;
  const [reason, setReason] = useState("");
  const list = (reasons.data ?? []).filter((r) => r.kind === "downtime" && r.active);
  const save = async () => {
    const r = await call(() => post("/oee/events", { type: "downtime", machine, start: gap.start, end: gap.end, reason, source: "manual" }));
    if (r) { void qc.invalidateQueries({ queryKey: ["oee"] }); onClose(); }
  };
  return (
    <Modal title={t("oee.gap.assign")} onClose={onClose} width={440} testid="oee-gap-dialog"
      footer={<><Btn kind="primary" label={t("app.save")} disabled={!reason} onClick={() => void save()} testid="oee-gap-save" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <p>{fmtLocal(gap.start, off)} — {fmtLocal(gap.end, off)} ({t("oee.u.min_n", { n: Math.round(gap.minutes) })})</p>
      <Sel value={reason} width="100%" testid="oee-gap-reason" onChange={setReason}
        options={[{ value: "", label: t("oee.gap.choose") }, ...list.map((r) => ({ value: r.code, label: reasonName(r, lang) }))]} />
    </Modal>
  );
}

export function OeeEvents() {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const ui = useOeeUI();
  const meta = useOeeMeta();
  const off = meta.data?.config.tz_offset_min ?? 0;
  const machines = useOeeMachines();
  const reasons = useOeeReasons();
  const [type, setType] = useState("");
  const [page, setPage] = useState(0);
  const [dlg, setDlg] = useState<{ ev: OeeEvent | null } | null>(null);
  const [gap, setGap] = useState<{ start: string; end: string; minutes: number } | null>(null);
  const pq = periodQuery(ui);
  const q = useOeeEvents({ machine: ui.machine || undefined, type: type || undefined, limit: PAGE, offset: page * PAGE, ...pq });
  const gaps = useOeeGaps(ui.machine, pq);
  const h = t("oee.u.h"), mn = t("oee.u.min");
  const mname = (k: string) => machines.data?.find((m) => m.key === k)?.name ?? k;
  const rname = (c: string | null) => (c ? reasonName(reasons.data?.find((r) => r.code === c), lang, c) : "—");
  const total = q.data?.total ?? 0;

  const detail = (e: OeeEvent): string => {
    if (e.type === "run") {
      const bits = [t("oee.ev.d_sheets", { n: e.qty ?? 1 })];
      if (e.parts) bits.push(t("oee.ev.d_parts", { n: e.parts }));
      if (e.reject_qty) bits.push(t("oee.ev.d_reject", { n: e.reject_qty, u: t(`oee.unit_short.${e.unit === "sheet" ? "sheet" : "part"}`) }));
      if (e.cut_length_m !== null) bits.push(`${e.cut_length_m} m`);
      if (e.project_number) bits.push(`№${e.project_number}${e.map_index ? `/${e.map_index}` : ""}`);
      return bits.join(" · ");
    }
    if (e.type === "downtime") {
      const dur = e.start && e.end ? (Date.parse(e.end) - Date.parse(e.start)) / 60000 : null;
      return `${rname(e.reason)} · ${e.open ? t("oee.ev.open") : fmtMin(dur, h, mn)}`;
    }
    return `${t("oee.ev.d_reject", { n: e.qty ?? 1, u: t(`oee.unit_short.${e.unit === "sheet" ? "sheet" : "part"}`) })}${e.reason ? " · " + rname(e.reason) : ""}`;
  };
  const remove = async (e: OeeEvent) => {
    if (!(await askConfirm(t("oee.ev.delete_q")))) return;
    await call(() => del(`/oee/events/${e.id}`));
    void qc.invalidateQueries({ queryKey: ["oee"] });
  };

  return (
    <div className="oee-body" data-testid="oee-events">
      <div className="oee-bar">
        <OeeFilters />
        <Sel value={type} width={170} testid="oee-type-filter" onChange={(v) => { setType(v); setPage(0); }}
          options={[{ value: "", label: t("oee.all_types") }, ...(["run", "downtime", "reject"] as const).map((x) => ({ value: x, label: t(`oee.type.${x}`) }))]} />
        <span className="grow" />
        <Btn small icon={ArrowUpFromLine} label={t("oee.csv")} testid="oee-ev-csv"
          onClick={() => void download("/oee/export.csv", { kind: "events", machine: ui.machine || undefined, ...pq }, "oee_events.csv")} />
        <Btn kind="primary" small icon={Plus} label={t("oee.ev.add")} testid="oee-ev-add" onClick={() => setDlg({ ev: null })} />
      </div>

      {ui.machine && gaps.data && gaps.data.items.length > 0 && (
        <div className="oee-card" data-testid="oee-gaps">
          <div className="oee-card-head"><h3>{t("oee.gap.title")}</h3><span className="muted">{t("oee.gap.hint")}</span></div>
          <div className="oee-gaplist">
            {gaps.data.items.slice(0, 8).map((g) => (
              <div key={g.start} className="oee-gap">
                <span>{fmtLocal(g.start, off)} — {fmtLocal(g.end, off)}</span><b>{fmtMin(g.minutes, h, mn)}</b>
                <Btn small label={t("oee.gap.assign")} testid="oee-gap-assign" onClick={() => setGap(g)} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="oee-card">
        <div className="oee-card-head"><h3>{t("oee.ev.list")}</h3><span className="muted">{t("oee.ev.total", { n: total })}</span></div>
        {(q.data?.items.length ?? 0) === 0 ? <div className="oee-empty" data-testid="oee-ev-empty">{t("oee.no_events")}</div> : (
          <div className="scroll oee-tablewrap">
            <table className="simple oee-table" data-testid="oee-ev-table">
              <thead><tr><th>{t("oee.col.time")}</th><th>{t("oee.ev.type")}</th><th>{t("oee.col.machine")}</th><th>{t("oee.col.details")}</th>
                <th>{t("oee.col.source")}</th><th>{t("oee.ev.note")}</th><th /></tr></thead>
              <tbody>{q.data!.items.map((e) => (
                <tr key={e.id} data-testid={`oee-ev-${e.id}`}>
                  <td>{fmtLocal(e.end ?? e.start, off)}{e.type === "downtime" && e.start ? ` ← ${fmtLocal(e.start, off).slice(6)}` : ""}</td>
                  <td>{t(`oee.type.${e.type}`, { defaultValue: e.type })}</td><td>{mname(e.machine)}</td><td>{detail(e)}</td>
                  <td>{e.source ?? ""}</td><td className="oee-ellip" title={e.note ?? ""}>{e.note ?? ""}</td>
                  <td className="oee-act">
                    <button type="button" className="ibtn" title={t("app.edit")} onClick={() => setDlg({ ev: e })} data-testid={`oee-ev-edit-${e.id}`}><Pencil size={14} /></button>
                    <button type="button" className="ibtn" title={t("app.delete")} onClick={() => void remove(e)} data-testid={`oee-ev-del-${e.id}`}><Trash size={14} /></button>
                  </td>
                </tr>))}</tbody>
            </table>
          </div>
        )}
        {total > PAGE && (
          <div className="row gap oee-pager">
            <Btn small label="‹" disabled={page === 0} onClick={() => setPage(page - 1)} />
            <span>{page + 1} / {Math.ceil(total / PAGE)}</span>
            <Btn small label="›" disabled={(page + 1) * PAGE >= total} onClick={() => setPage(page + 1)} />
          </div>
        )}
      </div>
      {dlg && <EventDialog ev={dlg.ev} defMachine={ui.machine} onClose={() => setDlg(null)} />}
      {gap && <GapDialog machine={ui.machine} gap={gap} onClose={() => setGap(null)} />}
    </div>
  );
}
