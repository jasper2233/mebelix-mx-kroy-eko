// Ustun «Свойства» oynasi (jadval «Настройки» ichida): Тип («Настроенный Параметры» / «Выражение»), Наименование (parametr nomi,
// prefiks bilan), Описание (sarlavha maslahati), Заголовок, Тип колонки, Выражение («Vs» — o'zgaruvchilar, «?» — ifoda yordamchisi).
// O'rnatilgan ustunda faqat «Заголовок» tahrirlanadi.
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark } from "lucide-react";
import { ExprHelper } from "../ExprHelper";
import { Btn, IconBtn, Modal, Sel } from "../ui";
import { PARAM_NAME_MAX, PARAM_NAME_RE, type ExprVar, type UserCol, type UserColKind, type UserColType } from "./userColumns";

export interface UserColDraft { key: string; title?: string; user?: UserCol }

export function UserColumnProps(props: {
  initial: UserColDraft;
  /** o'rnatilgan ustun: nom va tavsif katalogdan (o'zgarmaydi) */
  builtin?: { label: string; desc: string };
  /** boshqa ustunlar kalitlari (nom takrorlanmasin) */
  taken: string[];
  prefix: string;
  vars: ExprVar[];
  onOk: (d: UserColDraft) => void;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const b = props.builtin;
  const u0: UserCol = props.initial.user ?? { kind: "param", vtype: "string" };
  const [kind, setKind] = useState<UserColKind>(u0.kind);
  const [name, setName] = useState(props.initial.key);
  const [desc, setDesc] = useState(u0.desc ?? "");
  const [title, setTitle] = useState(props.initial.title ?? "");
  const [vtype, setVtype] = useState<UserColType>(u0.vtype);
  const [expr, setExpr] = useState(u0.expr ?? "");
  const [vs, setVs] = useState(false);
  const [help, setHelp] = useState(false);
  const [err, setErr] = useState("");
  const area = useRef<HTMLTextAreaElement>(null);
  const isExpr = !b && kind === "expr";

  const insert = (text: string) => {
    const el = area.current;
    const a = el?.selectionStart ?? expr.length, z = el?.selectionEnd ?? expr.length;
    setExpr(expr.slice(0, a) + text + expr.slice(z));
    setVs(false);
    requestAnimationFrame(() => { el?.focus(); el?.setSelectionRange(a + text.length, a + text.length); });
  };
  const ok = () => {
    if (b) { props.onOk({ ...props.initial, title: title.trim() || undefined }); return; }
    const n = name.trim();
    if (!n || n.length > PARAM_NAME_MAX || !PARAM_NAME_RE.test(n)) { setErr(t("ucol.bad_name", { n: PARAM_NAME_MAX })); return; }
    if (props.taken.includes(n)) { setErr(t("ucol.dup_name")); return; }
    props.onOk({ key: n, title: title.trim() || undefined,
      user: { kind, vtype, ...(desc.trim() ? { desc: desc.trim().slice(0, 300) } : {}), ...(kind === "expr" ? { expr: expr.trim() } : {}) } });
  };
  const row = (label: string, ctl: React.ReactNode) => (
    <tr><td className="ucol-lbl">{label}</td><td>{ctl}</td></tr>
  );
  return (
    <Modal title={t("ucol.title")} onClose={props.onClose} width={560} scope="ucol" testid="ucol-dialog"
      footer={<>
        <span className="grow" />
        <Btn kind="primary" label={t("app.ok")} onClick={ok} testid="ucol-ok" />
        <Btn label={t("app.cancel")} onClick={props.onClose} />
      </>}>
      <table className="ucol-form">
        <tbody>
          {row(t("ucol.kind"), (
            <Sel<UserColKind> value={kind} width={260} disabled={!!b} onChange={setKind} testid="ucol-kind"
              options={[{ value: "param", label: t("ucol.kind_param") }, { value: "expr", label: t("ucol.kind_expr") }]} />))}
          {row(t("ucol.name"), (
            <input className="inp" style={{ width: 260 }} value={b ? b.label : name} disabled={!!b} maxLength={PARAM_NAME_MAX}
              onChange={(e) => { setName(e.target.value); setErr(""); }} data-testid="ucol-name" />))}
          {row(t("ucol.desc"), (
            <input className="inp" style={{ width: 360 }} value={b ? b.desc : desc} disabled={!!b} maxLength={300}
              onChange={(e) => setDesc(e.target.value)} data-testid="ucol-desc" />))}
          {row(t("ucol.header"), (
            <input className="inp" style={{ width: 260 }} value={title} placeholder={b?.label ?? name} maxLength={100}
              onChange={(e) => setTitle(e.target.value)} data-testid="ucol-title" />))}
          {row(t("ucol.vtype"), (
            <Sel<UserColType> value={vtype} width={180} disabled={!!b} onChange={setVtype} testid="ucol-vtype"
              options={(["string", "int", "double", "bool"] as const).map((v) => ({ value: v, label: t(`ucol.vt.${v}`) }))} />))}
          {row(t("ucol.expr"), (
            <div className="ucol-expr">
              <textarea ref={area} className="inp" rows={3} value={expr} disabled={!isExpr} maxLength={1000}
                onChange={(e) => setExpr(e.target.value)} data-testid="ucol-expr" />
              <div className="ucol-expr-btns">
                <button type="button" className="pvs" title={t("ucol.vars")} disabled={!isExpr} onClick={() => setVs(!vs)}
                  data-testid="ucol-vs">Vs</button>
                <IconBtn icon={CircleQuestionMark} title={t("ucol.expr_help")} disabled={!isExpr} onClick={() => setHelp(true)} />
              </div>
              {vs && isExpr && (
                <div className="ucol-vars" data-testid="ucol-vars">
                  {props.vars.map((v) => (
                    <button key={v.name} type="button" className="dd-item" onClick={() => insert(v.name)} title={v.label}>
                      <code>{v.name}</code> <span className="muted">{v.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>))}
        </tbody>
      </table>
      {isExpr && <div className="hint" data-testid="ucol-note">{t("ucol.expr_note", { prefix: props.prefix })}</div>}
      {err && <div className="warn" data-testid="ucol-err">{err}</div>}
      {help && (
        <Modal title={t("ucol.expr_help")} width={820} scope="ucol-help" onClose={() => setHelp(false)} testid="ucol-help"
          footer={<Btn kind="primary" label={t("app.ok")} onClick={() => setHelp(false)} />}>
          <ExprHelper value={expr} onChange={setExpr} variables={props.vars.map((v) => ({ name: v.name, label: v.label }))} compact />
        </Modal>
      )}
    </Modal>
  );
}
