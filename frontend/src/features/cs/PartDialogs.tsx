// Detal oynalari: Свойства (Ctrl+Space), Групповые действия (Ctrl+B), boshqa operatsiyaga ko'chirish (Ctrl+M),
// o'lcham kiritish rejimi.
import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronRight, Drill, Plus, Trash } from "lucide-react";
import { call } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { Operation, Part, Project, SizeMode } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Modal, Num, Sel, cx } from "../../shared/ui";
import { OpBadge } from "../project/opmeta";
import { computeSizes, edgeParams, mapsOfPart, totalQty } from "./sizes";

type Side = "top" | "bottom" | "left" | "right";
const SIDES: Side[] = ["top", "bottom", "left", "right"];

/** Detal chizmasi: kromkali tomonlar — rangli qalin chiziq + belgi, pazlar — shtrix. */
export function PartSketch({ project, part, w = 260, h = 200 }: { project: Project; part: Part; w?: number; h?: number }) {
  const L = Math.max(part.length || 1, 1), W = Math.max(part.width || 1, 1);
  const k = Math.min((w - 40) / L, (h - 40) / W);
  const pw = L * k, ph = W * k, x0 = (w - pw) / 2, y0 = (h - ph) / 2;
  const els = new Map(project.operations.filter((o) => o.type === "EL").map((o) => [o.id, o]));
  const seg: Record<Side, [number, number, number, number]> = {
    top: [x0, y0 - 5, x0 + pw, y0 - 5], bottom: [x0, y0 + ph + 5, x0 + pw, y0 + ph + 5],
    left: [x0 - 5, y0, x0 - 5, y0 + ph], right: [x0 + pw + 5, y0, x0 + pw + 5, y0 + ph],
  };
  const gseg: Record<Side, [number, number, number, number]> = {
    top: [x0 + 4, y0 + 10, x0 + pw - 4, y0 + 10], bottom: [x0 + 4, y0 + ph - 10, x0 + pw - 4, y0 + ph - 10],
    left: [x0 + 10, y0 + 4, x0 + 10, y0 + ph - 4], right: [x0 + pw - 10, y0 + 4, x0 + pw - 10, y0 + ph - 4],
  };
  return (
    <svg width={w} height={h} className="sketch">
      <rect x={x0} y={y0} width={pw} height={ph} fill={part.grain ? "url(#grain)" : "#f2a541"} stroke="#5a3a0a" />
      <defs>
        <pattern id="grain" width="8" height="8" patternUnits="userSpaceOnUse">
          <rect width="8" height="8" fill="#f2a541" /><path d="M0 4h8" stroke="#d98a1e" strokeWidth="1" />
        </pattern>
      </defs>
      {SIDES.map((s) => {
        const id = part[`edge_${s}`]?.op_id;
        const e = id ? els.get(id) : undefined;
        if (!e) return null;
        const [a, b, c, d] = seg[s];
        return (
          <g key={s}>
            <line x1={a} y1={b} x2={c} y2={d} stroke={e.el?.color && e.el.color !== "#000000" ? e.el.color : "#1b2733"} strokeWidth={5} />
            <text x={(a + c) / 2 + (s === "left" ? -10 : s === "right" ? 10 : 0)} y={(b + d) / 2 + (s === "top" ? -6 : s === "bottom" ? 14 : 4)}
              fontSize="12" textAnchor="middle" fill="#1b2733">{e.el?.symbol}</text>
          </g>
        );
      })}
      {SIDES.map((s) => (part[`groove_${s}`]?.op_id ? (
        <line key={`g${s}`} x1={gseg[s][0]} y1={gseg[s][1]} x2={gseg[s][2]} y2={gseg[s][3]} stroke="#0e7d78"
          strokeWidth={3} strokeDasharray="6 4" />) : null))}
      <text x={w / 2} y={y0 + ph / 2 + 4} textAnchor="middle" fontSize="13" fill="#241400">{part.length} × {part.width}</text>
    </svg>
  );
}

function Section({ title, children, open: open0 = false, disabled = false }: { title: ReactNode; children?: ReactNode; open?: boolean; disabled?: boolean }) {
  const [open, setOpen] = useState(open0);
  return (
    <div className={cx("sec", disabled && "sec-off")}>
      <button type="button" className="sec-head" onClick={() => !disabled && setOpen(!open)}>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />} {title}
      </button>
      {open && !disabled && <div className="sec-body">{children}</div>}
    </div>
  );
}

export function PartProperties({ project, op, part, onClose }: { project: Project; op: Operation; part: Part; onClose: () => void }) {
  const { t } = useTranslation();
  const [p, setP] = useState<Part>(() => JSON.parse(JSON.stringify(part)));
  const set = (f: Partial<Part>) => setP((x) => ({ ...x, ...f }));
  const els = project.operations.filter((o) => o.type === "EL");
  const grs = project.operations.filter((o) => o.type === "GR");
  const edges = edgeParams(project);
  const s = computeSizes(p, project.size_mode, edges, op.cs_cut?.machining_allowance ?? 0);
  const mode = project.size_mode;
  const xncOps = project.operations.filter((o) => p.xnc_op_ids.includes(o.id));
  const relOps = [op, ...els.filter((o) => SIDES.some((sd) => p[`edge_${sd}`]?.op_id === o.id)),
    ...grs.filter((o) => SIDES.some((sd) => p[`groove_${sd}`]?.op_id === o.id)), ...xncOps];
  const same = project.operations.flatMap((o) => o.parts).filter((x) => x.product_id === p.product_id);
  const save = async () => {
    const fields: Record<string, unknown> = {};
    for (const k of Object.keys(p) as (keyof Part)[]) {
      if (["id", "uid", "used_qty", "left_qty", "xnc_op_ids"].includes(k)) continue;
      if (JSON.stringify(p[k]) !== JSON.stringify(part[k])) fields[k] = p[k];
    }
    if (Object.keys(fields).length) {
      await call(() => post(`/projects/${project.id}/operations/${op.id}/parts/batch-update`, [{ id: part.id, fields }]));
    }
    onClose();
  };
  const addXnc = async () => {
    await save();
    const r = await call(() => post<Project>(`/projects/${project.id}/operations/${op.id}/parts/${part.id}/xnc`));
    if (r) useUI.getState().set({ opId: r.operations[r.operations.length - 1].id, xncTab: "program" });
  };
  const sizeRow = (label: string, key: "detail" | "jointed" | "blank" | "saw", cls: string) => {
    const editable = (key === mode) || (key === "detail" && mode === "detail");
    return (
      <tr className={cls}>
        <td>{label}</td>
        <td>{editable ? <Num value={p.length} onCommit={(v) => v !== null && set({ length: v })} width={62} /> : s[key][0]}</td>
        <td>{editable ? <Num value={p.width} onCommit={(v) => v !== null && set({ width: v })} width={62} /> : s[key][1]}</td>
        {(["allow_top", "allow_bottom", "allow_left", "allow_right"] as const).map((a) => (
          <td key={a}>{key === "saw" ? <Num value={p[a]} min={0} onCommit={(v) => set({ [a]: v ?? 0 })} width={38} /> : ""}</td>
        ))}
      </tr>
    );
  };
  return (
    <Modal title={<>{t("pp.title")}: {part.name || "—"} (id={part.uid})</>} onClose={onClose} width={900} testid="part-props"
      footer={<>
        <span className="muted grow">{t("tip.num_in_product")}: {same.findIndex((x) => x.id === part.id) + 1} ·{" "}
          {t("tip.num_in_cut")}: {mapsOfPart(op, part.id).join(", ") || "—"}</span>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void save()} testid="part-props-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="pp">
        <div className="pp-left">
          <PartSketch project={project} part={p} w={340} h={240} />
          <div className="pp-ops-head">
            <b>{t("pp.operations")}</b>
            <Btn icon={Plus} small kind="ghost" label={t("pp.add_xnc")} onClick={() => void addXnc()} />
          </div>
          <table className="simple">
            <thead><tr><th>№</th><th>{t("ops.col.type")}</th><th>{t("ops.col.code")}</th><th>{t("ops.col.name")}</th><th /></tr></thead>
            <tbody>
              {relOps.map((o, i) => (
                <tr key={o.id}><td>{i + 1}</td><td><OpBadge type={o.type} /></td><td>{o.code}</td><td>{o.name}</td>
                  <td>{o.type === "XNC" && (
                    <button type="button" className="ibtn" title={t("app.delete")}
                      onClick={() => void call(() => del(`/projects/${project.id}/operations/${o.id}`)).then(onClose)}>
                      <Trash size={13} /></button>)}
                    {o.type === "XNC" && (
                      <button type="button" className="ibtn" title={t("parts.xnc_editor")}
                        onClick={() => { useUI.getState().set({ opId: o.id, xncTab: "program" }); onClose(); }}>
                        <Drill size={13} /></button>)}
                  </td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pp-right">
          <div className="grid2">
            <span>{t("pp.product")}</span>
            <Sel value={p.product_id ?? ""} width="100%" onChange={(v) => set({ product_id: v || null })}
              options={project.products.map((x, i) => ({ value: x.id, label: `№${i + 1} ${x.name} (${x.qty} ${t("app.pcs")})` }))} />
            <span>{t("pp.name")}</span>
            <input className="inp" value={p.name} onChange={(e) => set({ name: e.target.value })} data-testid="pp-name" />
            <span>{t("pp.description")}</span>
            <input className="inp" value={p.description} onChange={(e) => set({ description: e.target.value })} />
            <span>{t("pp.code")}</span>
            <input className="inp" value={p.code} onChange={(e) => set({ code: e.target.value })} />
          </div>
          <div className="row gap wrap">
            <span>{t("cs.p.thickness")}: <b>{op.cs_material?.thickness}</b> {t("u.mm")}</span>
            <span>{t("pp.qty")}: <Num value={p.qty} min={0} width={60} onCommit={(v) => set({ qty: Math.round(v ?? 1) })} /></span>
            <span>{t("pp.total")}: <b>{totalQty(project, p)}</b></span>
            <Check checked={p.grain} label={t("pp.grain")} onChange={(v) => set({ grain: v })} />
          </div>
          <table className="simple sizes">
            <thead><tr><th>{t("pp.size")}</th><th>{t("pp.length")}</th><th>{t("pp.width")}</th><th>▽</th><th>△</th><th>▷</th><th>◁</th></tr></thead>
            <tbody>
              {sizeRow(t("pp.sz.detail"), "detail", "sz-detail")}
              {sizeRow(t("pp.sz.jointed"), "jointed", "sz-jointed")}
              {sizeRow(t("pp.sz.blank"), "blank", "sz-blank")}
              {sizeRow(t("pp.sz.saw"), "saw", "sz-saw")}
            </tbody>
          </table>
          <Section title={t("pp.grouping")}>
            <div className="row gap wrap">
              {(["none", "length", "width"] as const).map((g) => (
                <label key={g} className="check"><input type="radio" checked={p.group_by === g} onChange={() => set({ group_by: g })} />
                  {t(`pp.group.${g}`)}</label>
              ))}
            </div>
            <div className="row gap">
              <span>{t("pp.group_min")}</span><Num value={p.group_min} min={0} width={60} onCommit={(v) => set({ group_min: v ?? 0 })} />
              <span>{t("pp.group_max")}</span><Num value={p.group_max} min={0} width={60} onCommit={(v) => set({ group_max: v ?? 0 })} />
            </div>
            <p className="muted small">{t("pp.group_hint")}</p>
          </Section>
          <Section title={`(EL) ${t("optype.EL")}`} open>
            <div className="grid2">
              {SIDES.map((sd) => (
                <FragmentRow key={sd} label={t(`pp.side.${sd}`)}>
                  <Sel value={p[`edge_${sd}`]?.op_id ?? ""} width="100%" onChange={(v) => set({ [`edge_${sd}`]: { op_id: v || null } } as Partial<Part>)}
                    options={[{ value: "", label: "—" }, ...els.map((o) => ({ value: o.id, label: `${o.el?.symbol ?? ""} ${o.name || o.code}` }))]} />
                </FragmentRow>
              ))}
            </div>
          </Section>
          <Section title={`(SP) ${t("optype.SP")}`} disabled />
          <Section title={`(GR) ${t("optype.GR")}`}>
            <div className="grid3">
              {SIDES.map((sd) => (
                <FragmentRow key={sd} label={t(`pp.side.${sd}`)}>
                  <Check checked={p[`groove_${sd}`]?.back_side ?? false} title={t("pp.back_side")}
                    onChange={(v) => set({ [`groove_${sd}`]: { ...p[`groove_${sd}`], back_side: v } } as Partial<Part>)} />
                  <Sel value={p[`groove_${sd}`]?.op_id ?? ""} width="100%"
                    onChange={(v) => set({ [`groove_${sd}`]: { ...p[`groove_${sd}`], op_id: v || null } } as Partial<Part>)}
                    options={[{ value: "", label: "—" }, ...grs.map((o) => ({ value: o.id, label: o.name || o.code || "GR" }))]} />
                </FragmentRow>
              ))}
            </div>
          </Section>
          <Section title={t("pp.xnc_params")}>
            {xncOps.length ? xncOps.map((o) => <div key={o.id}>{o.code} {o.name}</div>) : <span className="muted">—</span>}
          </Section>
        </div>
      </div>
    </Modal>
  );
}

function FragmentRow({ label, children }: { label: string; children: ReactNode }) {
  return <><span>{label}</span>{children}</>;
}

// ───────────────────────── Групповые действия ─────────────────────────
export function GroupActions({ project, op, ids, onClose }: { project: Project; op: Operation; ids: string[]; onClose: () => void }) {
  const { t } = useTranslation();
  const first = op.parts.find((p) => p.id === ids[0]);
  const [on, setOn] = useState<Record<string, boolean>>({});
  const [v, setV] = useState<Record<string, unknown>>(() => first ? {
    product_id: first.product_id, name: first.name, description: first.description, length: first.length,
    width: first.width, qty: first.qty, grain: first.grain,
    ...Object.fromEntries(SIDES.map((s) => [`edge_${s}`, first[`edge_${s}`]?.op_id ?? ""])),
    ...Object.fromEntries(SIDES.map((s) => [`groove_${s}`, first[`groove_${s}`]?.op_id ?? ""])),
    ...Object.fromEntries(SIDES.map((s) => [`groove_${s}_back`, first[`groove_${s}`]?.back_side ?? false])),
  } : {});
  const els = project.operations.filter((o) => o.type === "EL");
  const grs = project.operations.filter((o) => o.type === "GR");
  const row = (key: string, label: string, ctl: ReactNode) => (
    <div className="ga-row" key={key}>
      <Check checked={!!on[key]} onChange={(x) => setOn({ ...on, [key]: x })} testid={`ga-${key}`} />
      <span className={cx("ga-label", !on[key] && "muted")}>{label}</span>
      <div className={cx("ga-ctl", !on[key] && "ga-off")}>{ctl}</div>
    </div>
  );
  const apply = async () => {
    const fields: Record<string, unknown> = {};
    for (const k of Object.keys(on)) {
      if (!on[k]) continue;
      if (k.startsWith("edge_")) fields[k] = { op_id: (v[k] as string) || null };
      else if (k.startsWith("groove_")) fields[k] = { op_id: (v[k] as string) || null, back_side: Boolean(v[`${k}_back`]) };
      else fields[k] = v[k];
    }
    if (!Object.keys(fields).length) { onClose(); return; }
    const r = await call(() => post(`/projects/${project.id}/operations/${op.id}/parts/group-update`, { ids, fields }));
    if (r) onClose();
  };
  const upd = (k: string, x: unknown) => setV({ ...v, [k]: x });
  const edgeOpts = [{ value: "", label: "—" }, ...els.map((o) => ({ value: o.id, label: o.name || o.code }))];
  return (
    <Modal title={`${t("parts.group")} (${ids.length})`} onClose={onClose} width={560} testid="group-actions"
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => void apply()} testid="ga-ok" /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      {row("product_id", t("pp.product"), <Sel value={(v.product_id as string) ?? ""} width="100%" onChange={(x) => upd("product_id", x || null)}
        options={project.products.map((x, i) => ({ value: x.id, label: `№${i + 1} ${x.name}` }))} />)}
      {row("name", t("pp.name"), <input className="inp w100" value={String(v.name ?? "")} onChange={(e) => upd("name", e.target.value)} />)}
      {row("description", t("pp.description"), <input className="inp w100" value={String(v.description ?? "")} onChange={(e) => upd("description", e.target.value)} />)}
      {row("length", t("pp.length"), <Num value={v.length as number} onCommit={(x) => upd("length", x)} />)}
      {row("width", t("pp.width"), <Num value={v.width as number} onCommit={(x) => upd("width", x)} />)}
      {row("qty", t("pp.qty"), <Num value={v.qty as number} min={0} onCommit={(x) => upd("qty", Math.round(x ?? 1))} testid="ga-qty-val" />)}
      {row("grain", t("pp.grain"), <Sel value={v.grain ? "1" : "0"} onChange={(x) => upd("grain", x === "1")}
        options={[{ value: "0", label: t("app.no") }, { value: "1", label: t("app.yes") }]} />)}
      <div className="form-h">(EL) {t("optype.EL")}</div>
      {SIDES.map((s) => row(`edge_${s}`, t(`pp.side.${s}`), <Sel value={String(v[`edge_${s}`] ?? "")} width="100%"
        onChange={(x) => upd(`edge_${s}`, x)} options={edgeOpts} />))}
      <div className="form-h">(GR) {t("optype.GR")}</div>
      {SIDES.map((s) => row(`groove_${s}`, t(`pp.side.${s}`), <span className="row gap">
        <Check checked={Boolean(v[`groove_${s}_back`])} title={t("pp.back_side")} onChange={(x) => upd(`groove_${s}_back`, x)} />
        <Sel value={String(v[`groove_${s}`] ?? "")} width={260} onChange={(x) => upd(`groove_${s}`, x)}
          options={[{ value: "", label: "—" }, ...grs.map((o) => ({ value: o.id, label: o.name || o.code || "GR" }))]} /></span>))}
    </Modal>
  );
}

// ───────────────────────── Boshqa operatsiyaga ko'chirish ─────────────────────────
export function MoveToOp({ project, op, ids, onClose }: { project: Project; op: Operation; ids: string[]; onClose: () => void }) {
  const { t } = useTranslation();
  const targets = project.operations.filter((o) => (o.type === "CS" || o.type === "CL") && o.id !== op.id);
  const [dst, setDst] = useState(targets[0]?.id ?? "");
  return (
    <Modal title={`${t("parts.move_to")} (${ids.length})`} onClose={onClose} width={480}
      footer={<><Btn kind="primary" label={t("app.ok")} disabled={!dst}
        onClick={() => void call(() => post(`/projects/${project.id}/operations/${op.id}/parts/move-to/${dst}`, { ids })).then(onClose)} />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      {targets.length ? (
        <div className="type-list">
          {targets.map((o) => (
            <label key={o.id} className="type-item"><input type="radio" checked={dst === o.id} onChange={() => setDst(o.id)} />
              <OpBadge type={o.type} /> {o.name || o.code}</label>
          ))}
        </div>
      ) : <p className="muted">{t("parts.no_target")}</p>}
    </Modal>
  );
}

// ───────────────────────── O'lcham kiritish rejimi ─────────────────────────
export function SizeModeDialog({ project, onClose }: { project: Project; onClose: () => void }) {
  const { t } = useTranslation();
  const [m, setM] = useState<SizeMode>(project.size_mode);
  const modes: SizeMode[] = ["blank", "detail", "jointed"];
  const hint = useMemo(() => t("sizemode.hint"), [t]);
  return (
    <Modal title={t("parts.size_mode")} onClose={onClose} width={480} testid="size-mode-dialog"
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => {
        if (m !== project.size_mode) void call(() => patch(`/projects/${project.id}`, { size_mode: m }));
        onClose();
      }} /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="type-list">
        {modes.map((x) => (
          <label key={x} className="type-item"><input type="radio" checked={m === x} onChange={() => setM(x)} /> {t(`sizemode.${x}`)}</label>
        ))}
      </div>
      <p className="muted">{hint}</p>
    </Modal>
  );
}
