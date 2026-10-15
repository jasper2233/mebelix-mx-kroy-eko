// «Данные для этикеток» — nom → ifoda jadvali (stanokka tegishli maydonlar). Ifodalar FAQAT serverda hisoblanadi
// (`POST …/label-fields/preview`): qizil xato (sintaksis / hisoblash), tanlangan loyiha detalidagi jonli qiymat.
// Qatorlar: «+ / − / ↑ / ↓», «standart jadvalni qaytarish», ifoda yonida «fx» (ExprHelper: funksiyalar va o'zgaruvchilar).
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowDown, ArrowUp, Minus, Plus, RotateCcw } from "lucide-react";
import { useProject } from "../../../api/hooks";
import { useUI } from "../../../store/ui";
import { askConfirm } from "../../../shared/dialogs";
import { ExprHelper, type ExprVariable } from "../../../shared/ExprHelper";
import { Btn, IconBtn, Modal, Sel, cx } from "../../../shared/ui";
import { useLabelPreview, useProjectChoices, type LabelRow, type LabelTable, type PreviewField } from "./machinesApi";
import "./machines.css";

function ValueCell({ row, f }: { row: LabelRow; f: PreviewField | undefined }) {
  const { t } = useTranslation();
  if (!f) return <span className="muted">…</span>;
  if (!row.expr.trim()) return <span className="muted">{t("ppm.empty_expr")}</span>;
  if (!f.ok) {
    return (
      <span className="pg-err" data-testid="lf-error" title={f.error ?? ""}>
        <b>#ERR</b> <span>{t(`exprh.stage.${f.stage ?? "eval"}`)}: {f.error}</span>
      </span>
    );
  }
  const text = f.type === "string" ? `'${f.text}'` : f.text;
  return (
    <span className="pg-val" data-testid="lf-value">
      <span className="expr-type">{t(`exprh.type.${f.type ?? "string"}`)}</span> <code>{text}</code>
    </span>
  );
}

export function LabelFieldsTable(props: {
  machineKey: string; table: LabelTable; rows: LabelRow[]; onChange: (rows: LabelRow[]) => void; onReset: () => void;
  onIssues?: (n: number) => void;
}) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const { rows, table } = props;
  const [sel, setSel] = useState<number | null>(null);
  const [fx, setFx] = useState<number | null>(null);
  // jonli ko'rinish maqsadi: loyiha → CS operatsiya → detal (bo'sh — namuna loyiha)
  const [pid, setPid] = useState("");
  const [opId, setOpId] = useState("");
  const [partUid, setPartUid] = useState("");
  const [pq, setPq] = useState("");
  const projects = useProjectChoices(pq);
  const project = useProject(pid || null);
  const projOptions = useMemo(() => {
    const list = (projects.data ?? []).map((p) => ({ value: p.id, label: `№${p.number} ${p.name}` }));
    if (pid && !list.some((o) => o.value === pid) && project.data) list.unshift({ value: pid, label: `№${project.data.number} ${project.data.name}` });
    return [{ value: "", label: t("ppm.sample") }, ...list];
  }, [projects.data, pid, project.data, t]);
  const csOps = useMemo(() => (project.data?.operations ?? []).filter((o) => o.type === "CS" && o.parts.length > 0), [project.data]);
  const op = csOps.find((o) => o.id === opId) ?? null;
  useEffect(() => { if (pid && csOps.length && !csOps.some((o) => o.id === opId)) { setOpId(csOps[0].id); setPartUid(""); } }, [pid, csOps, opId]);
  const target = pid && op ? { project_id: pid, op_id: op.id, part_uid: partUid ? Number(partUid) : undefined } : {};
  const prev = useLabelPreview(props.machineKey, rows, target);
  const fields = prev.data?.fields ?? [];
  const issues = rows.reduce((n, _r, i) => n + (fields[i] && (fields[i].stage === "syntax" || fields[i].name_error) ? 1 : 0), 0);
  useEffect(() => { props.onIssues?.(issues); }, [issues]);       // eslint-disable-line react-hooks/exhaustive-deps

  const dflt = useMemo(() => new Map(table.defaults.map((d) => [d.name, d.expr])), [table.defaults]);   // «qatorni standartga qaytarish»
  const set = (i: number, patch: Partial<LabelRow>) => props.onChange(rows.map((r, k) => (k === i ? { ...r, ...patch } : r)));
  const add = () => {
    const at = sel === null ? rows.length : sel + 1;
    let n = rows.length + 1;
    while (rows.some((r) => r.name === `Field${n}`)) n += 1;
    props.onChange([...rows.slice(0, at), { name: `Field${n}`, expr: "" }, ...rows.slice(at)]);
    setSel(at);
  };
  const remove = () => {
    if (sel === null) return;
    props.onChange(rows.filter((_r, i) => i !== sel));
    setSel(rows.length > 1 ? Math.min(sel, rows.length - 2) : null);
  };
  const move = (d: -1 | 1) => {
    if (sel === null || sel + d < 0 || sel + d >= rows.length) return;
    const a = [...rows];
    [a[sel], a[sel + d]] = [a[sel + d], a[sel]];
    props.onChange(a);
    setSel(sel + d);
  };
  const variables: ExprVariable[] = (prev.data?.variables ?? []).map((v) => ({
    name: v.name, label: lang === "uz" ? v.uz : v.ru, sample: v.value }));
  const title = lang === "uz" ? table.title.uz : table.title.ru;

  return (
    <div className="lf" data-testid="label-fields">
      <div className="lf-head">
        <h4>{title}</h4>
        <span className="lf-tools">
          <IconBtn icon={Plus} title={t("ppm.add_row")} onClick={add} disabled={rows.length >= table.max_rows} testid="lf-add" />
          <IconBtn icon={Minus} title={t("ppm.del_row")} onClick={remove} disabled={sel === null} testid="lf-del" />
          <IconBtn icon={ArrowUp} title={t("app.up")} onClick={() => move(-1)} disabled={sel === null || sel === 0} testid="lf-up" />
          <IconBtn icon={ArrowDown} title={t("app.down")} onClick={() => move(1)} disabled={sel === null || sel === rows.length - 1} testid="lf-down" />
          <IconBtn icon={RotateCcw} title={t("ppm.reset_table")}
            onClick={() => void askConfirm(t("ppm.reset_table_q")).then((ok) => { if (ok) { props.onReset(); setSel(null); } })} testid="lf-reset" />
        </span>
      </div>
      <div className="lf-target row gap wrap">
        <span className="muted">{t("ppm.preview_for")}</span>
        <input className="inp" style={{ width: 130 }} value={pq} placeholder={t("ppm.project_search")} data-testid="lf-project-q"
          onChange={(e) => setPq(e.target.value)} />
        <Sel value={pid} width={240} testid="lf-project" onChange={(v) => { setPid(v); setOpId(""); setPartUid(""); }}
          options={projOptions} />
        {pid && (
          <Sel value={op?.id ?? ""} width={200} testid="lf-op" onChange={(v) => { setOpId(v); setPartUid(""); }}
            options={csOps.length ? csOps.map((o) => ({ value: o.id, label: o.name })) : [{ value: "", label: t("ppm.no_cs") }]} />
        )}
        {pid && op && (
          <Sel value={partUid || String(op.parts[0].uid)} width={260} testid="lf-part" onChange={setPartUid}
            options={op.parts.map((p) => ({ value: String(p.uid), label: `${p.uid}. ${p.name} (${p.length}×${p.width})` }))} />
        )}
        {prev.data && <span className="muted" data-testid="lf-part-info">
          {prev.data.source === "sample" ? t("ppm.sample_note") : `${prev.data.part.uid}. ${prev.data.part.name}`}</span>}
        {prev.error && <span className="pg-err">{prev.error}</span>}
      </div>
      <table className="simple lf-table">
        <thead><tr><th style={{ width: 34 }}>{t("ppm.col.n")}</th><th style={{ width: 230 }}>{t("ppm.col.name")}</th>
          <th>{t("ppm.col.expr")}</th><th style={{ width: 300 }}>{t("ppm.col.value")}</th></tr></thead>
        <tbody>
          {rows.map((r, i) => {
            const f = fields[i];
            const bad = !!f && !f.ok && !!r.expr.trim();
            return (
              <tr key={i} className={cx(sel === i && "tr-sel", bad && "lf-bad")} data-testid={`lf-row-${i}`}
                onMouseDown={() => setSel(i)}>
                <td className="num">{i + 1}</td>
                <td>
                  <input className="inp" value={r.name} spellCheck={false} data-testid={`lf-name-${i}`} onFocus={() => setSel(i)}
                    onChange={(e) => set(i, { name: e.target.value })} />
                  {f?.name_error && <div className="pg-err pg-small">{f.name_error}</div>}
                </td>
                <td>
                  <span className="lf-expr">
                    <input className={cx("inp", "code-inp", bad && "inp-bad")} value={r.expr} spellCheck={false}
                      data-testid={`lf-expr-${i}`} onFocus={() => setSel(i)} onChange={(e) => set(i, { expr: e.target.value })} />
                    <button type="button" className="btn btn-sm" title={t("ppm.fx_title")} data-testid={`lf-fx-${i}`}
                      onClick={() => { setSel(i); setFx(i); }}>fx</button>
                    {dflt.has(r.name) && dflt.get(r.name) !== r.expr && (
                      <button type="button" className="ibtn" title={`${t("ppm.reset_row")}: ${dflt.get(r.name)}`} data-testid={`lf-reset-${i}`}
                        onClick={() => set(i, { expr: dflt.get(r.name) ?? "" })}><RotateCcw size={13} /></button>
                    )}
                  </span>
                </td>
                <td><ValueCell row={r} f={f} /></td>
              </tr>
            );
          })}
          {!rows.length && <tr><td colSpan={4} className="muted">{t("ppm.table_empty")}</td></tr>}
        </tbody>
      </table>
      {fx !== null && rows[fx] && (
        <Modal title={`${t("ppm.fx_title")}: ${rows[fx].name}`} width={820} onClose={() => setFx(null)} testid="lf-fx-modal"
          footer={<Btn kind="primary" label={t("app.ok")} onClick={() => setFx(null)} />}>
          <ExprHelper value={rows[fx].expr} onChange={(v) => set(fx, { expr: v })} variables={variables} compact />
        </Modal>
      )}
    </div>
  );
}
