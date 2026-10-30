// «Раскроечные станки» (2026-10-30, xodim loyihasi «1275»): stanok parametrlari (pila, торцовка, вращения, polosalar …) operatsiyada
// o'zgartirilsa — faqat shu loyihada; standart — stanokda, faqat login paroli bilan o'zgaradi (backend `services/saw_machines.py`).
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Plus, Save, Trash2 } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, post, put } from "../../api/client";
import type { CSCutParams, CSMaterialParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Btn, Field, IconBtn, Modal, Num, Sel } from "../../shared/ui";
import "./sawMachines.css";

export interface SawMachine { id: string; name: string; cut: Partial<CSCutParams>; updated_by: string; updated_at: string }
export interface SawMachinesDoc {
  machines: SawMachine[]; default_id: string | null; my_machine_id: string; my_choice: string | null; login: string;
  password_required: boolean; fields: (keyof CSCutParams)[];
}

export const useSawMachines = () => useQuery({ queryKey: ["saw-machines"], queryFn: () => get<SawMachinesDoc>("/saw-machines") });
const refresh = (d?: SawMachinesDoc) => { if (d) qc.setQueryData(["saw-machines"], d); };

export const machineName = (m: SawMachine | undefined, t: (k: string) => string) => (m?.name || t("saw.main"));

/** Operatsiya parametrlari stanok standartidan farq qiladigan maydonlar. */
export function machineDiff(c: CSCutParams, m: SawMachine | undefined, fields: (keyof CSCutParams)[]) {
  if (!m) return [] as (keyof CSCutParams)[];
  return fields.filter((k) => k in m.cut && (m.cut[k] ?? null) !== (c[k] ?? null));
}

/** CS «Параметры» boshida: stanok tanlovi + standartdan farq ogohlantirishi («Вернуть стандарт станка»). */
export function MachineRow({ project, op, onCut }: { project: Project; op: Operation; onCut: (f: Partial<CSCutParams>) => unknown }) {
  const { t } = useTranslation();
  const q = useSawMachines();
  const c = op.cs_cut!;
  if (!q.data) return null;
  const d = q.data;
  const mid = c.machine_id && d.machines.some((m) => m.id === c.machine_id) ? c.machine_id : (d.default_id ?? d.machines[0]?.id);
  const m = d.machines.find((x) => x.id === mid);
  const diff = machineDiff(c, m, d.fields);
  const label = (k: string) => t(`saw.f.${k}`);
  const val = (v: unknown) => (v === null || v === undefined ? "—" : typeof v === "boolean" ? (v ? "✓" : "—") : String(v));
  return (
    <>
      <Field label={t("saw.machine")}>
        <Sel value={mid ?? ""} width={190} testid="cs-machine"
          onChange={(v) => { const x = d.machines.find((y) => y.id === v); if (x) void onCut({ ...x.cut, machine_id: x.id }); }}
          options={d.machines.map((x) => ({ value: x.id, label: machineName(x, t) + (x.id === d.default_id ? ` (${t("saw.default_s")})` : "") }))} />
      </Field>
      {diff.length > 0 && (
        <div className="saw-diff" data-testid="cs-machine-diff" data-project={project.id}>
          <div>{t("saw.diff", { m: machineName(m, t) })}</div>
          <ul>{diff.map((k) => <li key={k}>{label(k)}: <b>{val(c[k])}</b> ({t("saw.std")} {val(m!.cut[k])})</li>)}</ul>
          <Btn label={t("saw.restore")} testid="cs-machine-restore" onClick={() => void onCut({ ...m!.cut, machine_id: m!.id })} />
        </div>
      )}
    </>
  );
}

/** «Сохранить по умолчанию»: material / boshqa parametrlar — korxona standarti; stanok parametrlari — tanlangan stanokka (parol). */
export function SaveStdDialog({ op, onClose }: { op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const q = useSawMachines();
  const c = op.cs_cut!, mat = op.cs_material!;
  const d = q.data;
  const mid0 = c.machine_id && d?.machines.some((m) => m.id === c.machine_id) ? c.machine_id : d?.default_id ?? "";
  const [mid, setMid] = useState<string | null>(null);
  const [withMachine, setWithMachine] = useState(true);
  const [pw, setPw] = useState("");
  if (!d) return null;
  const cur = mid ?? mid0;
  const m = d.machines.find((x) => x.id === cur);
  const diff = machineDiff(c, m, d.fields);
  const ok = async () => {
    if (withMachine && diff.length) {
      const cut = Object.fromEntries(d.fields.map((k) => [k, c[k]]));
      const r = await call(() => post<SawMachinesDoc>("/saw-machines/save", { password: pw, machine: { id: cur, name: m?.name ?? "", cut } }));
      if (!r) return;
      refresh(r);
    }
    const rest = Object.fromEntries(Object.entries(c).filter(([k]) => !d.fields.includes(k as keyof CSCutParams)));
    const r2 = await call(() => put("/settings/cs_defaults/default", { material: mat as CSMaterialParams, cut: { ...rest } }));
    if (r2) { useUI.getState().toast(t("cs.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); onClose(); }
  };
  return (
    <Modal title={t("cs.save_default")} onClose={onClose} width={520} testid="cs-save-std"
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="cs-save-std-ok" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <p>{t("saw.save_note")}</p>
      <label className="row gap"><input type="checkbox" checked={withMachine} onChange={(e) => setWithMachine(e.target.checked)} data-testid="cs-save-std-machine" />
        {t("saw.save_machine_too")}</label>
      {withMachine && (<>
        <Field label={t("saw.machine")}>
          <Sel value={cur} width={220} onChange={(v) => setMid(v)} options={d.machines.map((x) => ({ value: x.id, label: machineName(x, t) }))} /></Field>
        {diff.length === 0 ? <p className="muted">{t("saw.no_diff")}</p>
          : <ul className="saw-diff-list">{diff.map((k) => <li key={k}>{t(`saw.f.${k}`)}: {String(m?.cut[k] ?? "—")} → <b>{String(c[k] ?? "—")}</b></li>)}</ul>}
        {d.password_required && diff.length > 0 && (
          <Field label={t("saw.password", { login: d.login })}>
            <input type="password" className="inp" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)}
              data-testid="cs-save-std-password" /></Field>)}
      </>)}
    </Modal>
  );
}

/** «Настройки → Раскроечные станки»: stanoklar ro'yxati, standart parametrlari (parol bilan), o'z stanogini tanlash. */
export function SawMachinesPage() {
  const { t } = useTranslation();
  const q = useSawMachines();
  const [edit, setEdit] = useState<SawMachine | null>(null);
  const d = q.data;
  if (!d) return null;
  const choose = async (id: string | null) => refresh(await call(() => put<SawMachinesDoc>("/saw-machines/me", { machine_id: id })));
  const remove = async (m: SawMachine) => {
    if (!(await askConfirm(t("saw.delete"), machineName(m, t), { danger: true, ok: t("app.ok") }))) return;
    const pw = d.password_required ? window.prompt(t("saw.password", { login: d.login })) ?? "" : "";
    refresh(await call(() => post<SawMachinesDoc>(`/saw-machines/${m.id}/delete`, { password: pw })));
  };
  return (
    <div className="page" data-testid="saw-machines">
      <div className="page-head"><h2>{t("settings.page.saw_machines")}</h2>
        <Btn icon={Plus} label={t("saw.add")} testid="saw-add"
          onClick={() => { const b = d.machines.find((x) => x.id === d.default_id) ?? d.machines[0]; setEdit({ id: "", name: "", cut: { ...b.cut }, updated_by: "", updated_at: "" }); }} /></div>
      <div className="scroll form1">
        <p className="muted">{t("saw.page_note")}</p>
        <table className="saw-table">
          <thead><tr><th>{t("saw.machine")}</th><th>{t("saw.f.kerf")}</th><th>{t("saw.f.trim_length")}</th><th>{t("saw.f.max_rotations")}</th>
            <th>{t("saw.f.pack_height")}</th><th>{t("saw.changed")}</th><th>{t("saw.mine")}</th><th /></tr></thead>
          <tbody>{d.machines.map((m) => (
            <tr key={m.id} data-testid={`saw-row-${m.id}`}>
              <td><b>{machineName(m, t)}</b>{m.id === d.default_id && <span className="muted"> ({t("saw.default_s")})</span>}</td>
              <td className="num">{m.cut.kerf}</td><td className="num">{m.cut.trim_length} / {m.cut.trim_width}</td>
              <td className="num">{m.cut.max_rotations}</td><td className="num">{m.cut.pack_height}</td>
              <td className="muted">{m.updated_at ? `${m.updated_at} · ${m.updated_by}` : ""}</td>
              <td><input type="radio" name="my-machine" checked={d.my_machine_id === m.id} onChange={() => void choose(m.id)}
                data-testid={`saw-mine-${m.id}`} /></td>
              <td><Btn label={t("saw.edit")} onClick={() => setEdit(m)} testid={`saw-edit-${m.id}`} />
                {d.machines.length > 1 && <IconBtn icon={Trash2} title={t("saw.delete")} onClick={() => void remove(m)} />}</td>
            </tr>))}</tbody>
        </table>
        <p className="muted">{t("saw.mine_note", { login: d.login })}</p>
      </div>
      {edit && <MachineEdit doc={d} m={edit} onClose={() => setEdit(null)} />}
    </div>
  );
}

function MachineEdit({ doc, m, onClose }: { doc: SawMachinesDoc; m: SawMachine; onClose: () => void }) {
  const { t } = useTranslation();
  const [name, setName] = useState(m.name);
  const [cut, setCut] = useState<Partial<CSCutParams>>({ ...m.cut });
  const [def, setDef] = useState(m.id !== "" && m.id === doc.default_id);
  const [pw, setPw] = useState("");
  const num = (k: keyof CSCutParams, min: number, max: number, allowEmpty = false) => (
    <Field label={t(`saw.f.${k}`)} key={k}><Num value={(cut[k] as number | null) ?? null} min={min} max={max} allowEmpty={allowEmpty}
      onCommit={(v) => setCut({ ...cut, [k]: v })} testid={`saw-f-${k}`} /></Field>);
  const ok = async () => {
    const r = await call(() => post<SawMachinesDoc>("/saw-machines/save", { password: pw, make_default: def, machine: { id: m.id || null, name, cut } }));
    if (r) { refresh(r); useUI.getState().toast(t("app.saved"), "ok"); onClose(); }
  };
  return (
    <Modal title={m.id ? machineName(m, t) : t("saw.add")} onClose={onClose} width={520} testid="saw-edit"
      footer={<><Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void ok()} testid="saw-edit-ok" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <Field label={t("saw.name")}><input className="inp" value={name} placeholder={t("saw.main")} onChange={(e) => setName(e.target.value)} data-testid="saw-name" /></Field>
      {num("kerf", 0, 50)}{num("trim_length", 0, 500)}{num("trim_width", 0, 500)}
      <Field label={t("saw.f.max_rotations")}><Sel value={(cut.max_rotations as number) ?? 4} width={80}
        onChange={(v) => setCut({ ...cut, max_rotations: v })} options={[1, 2, 3, 4, 5, 6].map((v) => ({ value: v, label: String(v) }))} /></Field>
      {num("pack_height", 0, 1000)}{num("min_trim_cut", 0, 500)}{num("min_strip_width", 0, 20000)}{num("max_strip_width", 0, 20000)}{num("max_strip_length", 0, 100000)}
      <label className="row gap"><input type="checkbox" checked={def} onChange={(e) => setDef(e.target.checked)} /> {t("saw.make_default")}</label>
      {doc.password_required && <Field label={t("saw.password", { login: doc.login })}>
        <input type="password" className="inp" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} data-testid="saw-password" /></Field>}
    </Modal>
  );
}
