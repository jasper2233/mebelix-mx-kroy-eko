// GR — Пазование: paz parametrlari (eni, chuqurligi, chetdan masofa, narx) va shu pazli detallar.
import { useTranslation } from "react-i18next";
import { call } from "../../api/hooks";
import { patch } from "../../api/client";
import type { GRParams, Operation, Project } from "../../api/types";
import { Field, Num, Tabs } from "../../shared/ui";

export function GrPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const g = op.gr ?? { width: 4, depth: 10, offset: 16, price: 0 };
  const pg = (f: Partial<GRParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { gr: { ...g, ...f } }));
  const parts = project.operations.filter((o) => o.type === "CS").flatMap((o) => o.parts.map((p) => ({ o, p })))
    .filter(({ p }) => (["top", "bottom", "left", "right"] as const).some((s) => p[`groove_${s}`]?.op_id === op.id));
  return (
    <div className="panel">
      <Tabs value="params" onChange={() => undefined} tabs={[{ key: "params", label: t("cs.tab.params") }]} />
      <div className="form2 scroll">
        <div className="form-col">
          <div className="form-h">{t("optype.GR")}</div>
          <Field label={t("gr.width")} unit={t("u.mm")}><Num value={g.width} min={0} onCommit={(v) => pg({ width: v ?? 4 })} /></Field>
          <Field label={t("gr.depth")} unit={t("u.mm")}><Num value={g.depth} min={0} onCommit={(v) => pg({ depth: v ?? 10 })} /></Field>
          <Field label={t("gr.offset")} unit={t("u.mm")}><Num value={g.offset} min={0} onCommit={(v) => pg({ offset: v ?? 16 })} /></Field>
          <Field label={t("gr.price")} unit={project.currency}><Num value={g.price} min={0} onCommit={(v) => pg({ price: v ?? 0 })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.tab.parts")} ({parts.length})</div>
          <table className="simple">
            <tbody>{parts.map(({ o, p }) => <tr key={p.id}><td>{p.uid}</td><td>{p.name}</td><td>{p.length}×{p.width}</td><td className="muted">{o.name}</td></tr>)}</tbody>
          </table>
          {!parts.length && <p className="muted">{t("gr.hint")}</p>}
        </div>
      </div>
    </div>
  );
}
