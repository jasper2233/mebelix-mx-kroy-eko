// CL detal «Свойства» (Ctrl+Space, W18): CS dagi PartProperties namunasida, lekin pogonaj kroyga mos — detal eni = polosa eni
// (tahrirlanmaydi), tekstura / paz / XNC yo'q; o'lchamlar jadvalida faqat uzunlik (◁ ▷ — uch kromkalari va pripusk), kromka
// (ОВ ОН ОЛ ОП) va (SP) lits / orqa sirt ishlovi.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { call } from "../../api/hooks";
import { post } from "../../api/client";
import type { Operation, Part, Project } from "../../api/types";
import { Btn, Modal, Num, Sel, cx } from "../../shared/ui";
import { OpBadge } from "../project/opmeta";
import { FragmentRow, PartSketch, Section } from "../cs/PartDialogs";
import { computeSizes, edgeParams, mapsOfPart, totalQty } from "../cs/sizes";

type Side = "top" | "bottom" | "left" | "right";
const SIDES: Side[] = ["top", "bottom", "left", "right"];
const NOT_SENT = ["id", "uid", "used_qty", "left_qty", "xnc_op_ids", "width", "grain"];    // CL: eni polosa eni, tekstura ma'nosiz

export function ClPartProps({ project, op, part, onClose }: { project: Project; op: Operation; part: Part; onClose: () => void }) {
  const { t } = useTranslation();
  const cl = op.cl!;
  const [p, setP] = useState<Part>(() => JSON.parse(JSON.stringify(part)));
  const set = (f: Partial<Part>) => setP((x) => ({ ...x, ...f }));
  const els = project.operations.filter((o) => o.type === "EL");
  const sps = project.operations.filter((o) => o.type === "SP");
  const edges = edgeParams(project);
  const mode = project.size_mode;
  const view = { ...p, width: cl.width };                                       // hisobda va chizmada detal eni = polosa eni
  const s = computeSizes(view, mode, edges, 0);
  const relOps = [op, ...els.filter((o) => SIDES.some((sd) => p[`edge_${sd}`]?.op_id === o.id)),
    ...sps.filter((o) => p.surface_face_op === o.id || p.surface_back_op === o.id)];
  const same = project.operations.flatMap((o) => o.parts).filter((x) => x.product_id === p.product_id);
  const uncomputed = !(p.length > 0) && p.src_length != null;

  const save = async () => {
    const fields: Record<string, unknown> = {};
    for (const k of Object.keys(p) as (keyof Part)[]) {
      if (NOT_SENT.includes(k)) continue;
      if (JSON.stringify(p[k]) !== JSON.stringify(part[k])) fields[k] = p[k];
    }
    if (Object.keys(fields).length) {
      await call(() => post(`/projects/${project.id}/operations/${op.id}/parts/batch-update`, [{ id: part.id, fields }]));
    }
    onClose();
  };

  // ◁ ▷: har qatorda uch o'zgarishi (DM-006 kabi): «prifugovkadan keyin» — kromka qalinligi ayiriladi, «zagotovka» — prifugovka eni qo'shiladi
  const sideDelta = (key: "detail" | "jointed" | "blank" | "saw", side: Side): number => {
    const id = p[`edge_${side}`]?.op_id;
    const e = id ? edges.get(id) : undefined;
    if (key === "jointed") return -(e?.thickness ?? 0);
    if (key === "blank") return e?.jointing_width ?? 0;
    return 0;
  };
  const sizeRow = (label: string, key: "detail" | "jointed" | "blank" | "saw", cls: string) => {
    const editable = key === mode;
    return (
      <tr className={cls}>
        <td>{label}</td>
        <td>{editable ? <Num value={p.length} min={0} onCommit={(v) => v !== null && set({ length: v })} width={70} testid="clp-length" />
          : s[key][0]}</td>
        {(["left", "right"] as const).map((sd) => {
          if (key === "saw") {
            const a = `allow_${sd}` as const;
            return <td key={sd}><Num value={p[a]} min={0} onCommit={(v) => set({ [a]: v ?? 0 })} width={44} testid={`clp-allow-${sd}`} /></td>;
          }
          const d = Math.round(sideDelta(key, sd) * 100) / 100;
          return <td key={sd} className={cx("dl", d < 0 && "dl-minus", d > 0 && "dl-plus")}>{d === 0 ? "" : d > 0 ? `+${d}` : `−${-d}`}</td>;
        })}
      </tr>
    );
  };
  return (
    <Modal title={<>{t("pp.title")}: {part.name || "—"} (id={part.uid})</>} onClose={onClose} width={860} testid="cl-part-props"
      footer={<>
        <span className="muted grow">{t("tip.num_in_product")}: {same.findIndex((x) => x.id === part.id) + 1} ·{" "}
          {t("cl.pp.num_in_strips")}: {mapsOfPart(op, part.id).join(", ") || "—"}</span>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void save()} testid="cl-part-props-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="pp">
        <div className="pp-left">
          <PartSketch project={project} part={view} w={340} h={150} />
          <p className="muted small">{t("cl.pp.sketch_hint", { w: cl.width })}</p>
          <div className="pp-ops-head"><b>{t("pp.operations")}</b></div>
          <table className="simple">
            <thead><tr><th>№</th><th>{t("ops.col.type")}</th><th>{t("ops.col.code")}</th><th>{t("ops.col.name")}</th></tr></thead>
            <tbody>
              {relOps.map((o, i) => <tr key={o.id}><td>{i + 1}</td><td><OpBadge type={o.type} /></td><td>{o.code}</td><td>{o.name}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div className="pp-right">
          {uncomputed && <p className="warn" data-testid="clp-uncomputed">{t("cl.tip.uncomputed", { v: p.src_length })}</p>}
          <div className="grid2">
            <span>{t("pp.product")}</span>
            <Sel value={p.product_id ?? ""} width="100%" testid="clp-product" onChange={(v) => set({ product_id: v || null })}
              options={project.products.map((x, i) => ({ value: x.id, label: `№${i + 1} ${x.name} (${x.qty} ${t("app.pcs")})` }))} />
            <span>{t("pp.name")}</span>
            <input className="inp" value={p.name} onChange={(e) => set({ name: e.target.value })} data-testid="clp-name" />
            <span>{t("pp.description")}</span>
            <input className="inp" value={p.description} onChange={(e) => set({ description: e.target.value })} data-testid="clp-description" />
            <span>{t("pp.code")}</span>
            <input className="inp" value={p.code} onChange={(e) => set({ code: e.target.value })} data-testid="clp-code" />
          </div>
          <div className="row gap wrap">
            <span>{t("cl.pp.strip_width")}: <b>{cl.width}</b> {t("u.mm")}</span>
            <span>{t("cs.p.thickness")}: <b>{cl.thickness}</b> {t("u.mm")}</span>
            <span>{t("pp.qty")}: <Num value={p.qty} min={0} width={60} testid="clp-qty" onCommit={(v) => set({ qty: Math.round(v ?? 1) })} /></span>
            <span>{t("pp.total")}: <b data-testid="clp-total">{totalQty(project, p)}</b></span>
          </div>
          <table className="simple sizes">
            <thead><tr><th>{t("pp.size")}</th><th>{t("pp.length")}</th><th>◁</th><th>▷</th></tr></thead>
            <tbody>
              {sizeRow(t("pp.sz.detail"), "detail", "sz-detail")}
              {sizeRow(t("pp.sz.jointed"), "jointed", "sz-jointed")}
              {sizeRow(t("pp.sz.blank"), "blank", "sz-blank")}
              {sizeRow(t("pp.sz.saw"), "saw", "sz-saw")}
            </tbody>
          </table>
          <p className="muted small">{t("cl.pp.delta_hint")}</p>
          <Section title={`(EL) ${t("optype.EL")}`} open>
            <div className="grid2">
              {SIDES.map((sd) => (
                <FragmentRow key={sd} label={t(`pp.side.${sd}`)}>
                  <Sel value={p[`edge_${sd}`]?.op_id ?? ""} width="100%" testid={`clp-edge-${sd}`}
                    onChange={(v) => set({ [`edge_${sd}`]: { op_id: v || null } } as Partial<Part>)}
                    options={[{ value: "", label: "—" }, ...els.map((o) => ({ value: o.id, label: `${o.el?.symbol ?? ""} ${o.name || o.code}` }))]} />
                </FragmentRow>
              ))}
            </div>
          </Section>
          <Section title={`(SP) ${t("optype.SP")}`} open={!!(p.surface_face_op || p.surface_back_op)}>
            <div className="grid2">
              {(["surface_face_op", "surface_back_op"] as const).map((k) => (
                <FragmentRow key={k} label={t(k === "surface_face_op" ? "pp.surface_face" : "pp.surface_back")}>
                  <Sel value={p[k] ?? ""} width="100%" testid={`clp-${k}`} onChange={(v) => set({ [k]: v || null } as Partial<Part>)}
                    options={[{ value: "", label: "—" }, ...sps.map((o) => ({ value: o.id, label: o.name || o.code || "SP" }))]} />
                </FragmentRow>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </Modal>
  );
}
