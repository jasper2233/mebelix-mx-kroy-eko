// «Печать отчета» sozlamalari oynalari uchun umumiy jadvallar (§11, 2026-10-15):
//  * PropGrid — «Параметр | Значение»: guruh sarlavha qatorlari (yig'iladi), qiymat katagida joyida tahrir — Да/Нет (ro'yxat),
//    tanlov, son, matn yoki maxsus (rang + shtrixlash, chiziq namunasi, 3×3 pozitsiya);
//  * ColumnsGrid — «№ | Вкл | Имя | Описание | Ш-на» ustunlar jadvali («Заголовок карт кроя», XNC «Статистика»):
//    qator tanlanadi, ↑ ↓ bilan tartib, «+» yo'q ustunni qo'shadi, «×» olib tashlaydi, «Восстановить значения по умолчанию».
import { Fragment, useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ArrowDown, ArrowUp, ChevronDown, ChevronRight, Plus, Trash } from "lucide-react";
import { IconBtn, cx } from "../../shared/ui";
import "./print.css";

export type GridRow =
  | { key: string; label: string; kind: "bool"; value: boolean; onChange: (v: boolean) => void; disabled?: boolean }
  | { key: string; label: string; kind: "select"; value: string; options: { value: string; label: string }[];
      onChange: (v: string) => void; disabled?: boolean }
  | { key: string; label: string; kind: "number"; value: number; min?: number; max?: number; onChange: (v: number) => void;
      unit?: string; disabled?: boolean }
  | { key: string; label: string; kind: "text"; value: string; placeholder?: string; onChange: (v: string) => void; maxLength?: number }
  | { key: string; label: string; kind: "custom"; node: ReactNode };

export interface GridGroup { key: string; label?: string; rows: GridRow[] }

/** Son katagi: Enter / fokus yo'qolganda saqlanadi (bo'sh yoki noto'g'ri — eski qiymat qaytadi). */
export function NumCell(props: { value: number; min?: number; max?: number; onCommit: (v: number) => void; testid?: string;
  disabled?: boolean }) {
  const [s, setS] = useState(String(props.value));
  useEffect(() => { setS(String(props.value)); }, [props.value]);
  const commit = () => {
    const n = Number(String(s).replace(",", "."));
    if (!Number.isFinite(n) || s.trim() === "") { setS(String(props.value)); return; }
    let v = n;
    if (props.min !== undefined) v = Math.max(props.min, v);
    if (props.max !== undefined) v = Math.min(props.max, v);
    if (v !== props.value) props.onCommit(v); else setS(String(v));
  };
  return (
    <input className="pgrid-inp num" value={s} disabled={props.disabled} data-testid={props.testid}
      onChange={(e) => setS(e.target.value)} onBlur={commit}
      onKeyDown={(e) => { if (e.key === "Enter") { commit(); (e.target as HTMLInputElement).select(); } }} />
  );
}

function TextCell(props: { value: string; placeholder?: string; maxLength?: number; onCommit: (v: string) => void; testid?: string }) {
  const [s, setS] = useState(props.value);
  useEffect(() => { setS(props.value); }, [props.value]);
  const commit = () => { if (s !== props.value) props.onCommit(s); };
  return (
    <input className="pgrid-inp" value={s} placeholder={props.placeholder} maxLength={props.maxLength} data-testid={props.testid}
      onChange={(e) => setS(e.target.value)} onBlur={commit} onKeyDown={(e) => { if (e.key === "Enter") commit(); }} />
  );
}

function Control({ r, yes, no }: { r: GridRow; yes: string; no: string }) {
  switch (r.kind) {
    case "bool":
      return (
        <select className="pgrid-sel" value={r.value ? "1" : "0"} disabled={r.disabled} data-testid={`pf-${r.key}`}
          onChange={(e) => r.onChange(e.target.value === "1")}>
          <option value="1">{yes}</option><option value="0">{no}</option>
        </select>
      );
    case "select":
      return (
        <select className="pgrid-sel" value={r.value} disabled={r.disabled} data-testid={`pf-${r.key}`}
          onChange={(e) => r.onChange(e.target.value)}>
          {r.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      );
    case "number":
      return r.unit
        ? <span className="pgrid-cell"><NumCell value={r.value} min={r.min} max={r.max} onCommit={r.onChange} testid={`pf-${r.key}`}
            disabled={r.disabled} /><span className="muted">{r.unit}</span></span>
        : <NumCell value={r.value} min={r.min} max={r.max} onCommit={r.onChange} testid={`pf-${r.key}`} disabled={r.disabled} />;
    case "text":
      return <TextCell value={r.value} placeholder={r.placeholder} maxLength={r.maxLength} onCommit={r.onChange} testid={`pf-${r.key}`} />;
    default:
      return <span className="pgrid-cell">{r.node}</span>;
  }
}

export function PropGrid({ groups, testid }: { groups: GridGroup[]; testid?: string }) {
  const { t } = useTranslation();
  const [closed, setClosed] = useState<Record<string, boolean>>({});
  return (
    <div className="pgrid-wrap">
      <table className="pgrid" data-testid={testid}>
        {/* onlayn oynalardagidek «Параметр | Значение» sarlavhasiz; ustun kengligi — colgroup orqali */}
        <colgroup><col style={{ width: "58%" }} /><col /></colgroup>
        <tbody>
          {groups.map((g) => (
            <Fragment key={g.key}>
              {g.label && (
                <tr className="pgrid-g" data-testid={`pg-group-${g.key}`}>
                  <td colSpan={2}>
                    <button type="button" className="pgrid-gbtn" aria-expanded={!closed[g.key]}
                      onClick={() => setClosed({ ...closed, [g.key]: !closed[g.key] })}>
                      {closed[g.key] ? <ChevronRight size={13} /> : <ChevronDown size={13} />}{g.label}
                    </button>
                  </td>
                </tr>
              )}
              {!closed[g.key] && g.rows.map((r) => (
                <tr key={r.key} className="pgrid-r" data-testid={`pg-row-${r.key}`}>
                  <td className="pgrid-k" title={r.label}>{r.label}</td>
                  <td className="pgrid-v"><Control r={r} yes={t("app.yes")} no={t("app.no")} /></td>
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export interface ColDef { key: string; name: string; desc: string }
export interface ColVal { key: string; on: boolean; width: number }

/** `fixed` — ustunlar ro'yxati o'zgarmas (qo'shish / o'chirish yo'q; havola va ▲▼ o'ngda — kroy kartasi «Настройки» oynasi). */
export function ColumnsGrid({ defs, value, defaults, onChange, testid, fixed }: {
  defs: ColDef[]; value: ColVal[]; defaults: ColVal[]; onChange: (v: ColVal[]) => void; testid?: string; fixed?: boolean;
}) {
  const { t } = useTranslation();
  const [sel, setSel] = useState(-1);
  const [adding, setAdding] = useState(false);
  const byKey = new Map(defs.map((d) => [d.key, d]));
  const rows = value.filter((r) => byKey.has(r.key));
  const missing = defs.filter((d) => !rows.some((r) => r.key === d.key));
  const set = (i: number, patch: Partial<ColVal>) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (sel < 0 || j < 0 || j >= rows.length) return;
    const next = [...rows];
    [next[sel], next[j]] = [next[j], next[sel]];
    onChange(next); setSel(j);
  };
  const remove = () => { if (sel < 0) return; onChange(rows.filter((_, i) => i !== sel)); setSel(-1); };
  const add = (key: string) => {
    const d = defaults.find((x) => x.key === key);
    onChange([...rows, { key, on: true, width: d?.width ?? 10 }]); setAdding(false); setSel(rows.length);
  };
  return (
    <div className="cgrid" data-testid={testid}>
      <div className="cgrid-tools">
        {fixed && <span className="grow" />}
        <button type="button" className="linkbtn" onClick={() => { onChange(defaults); setSel(-1); }} data-testid={`${testid ?? "cgrid"}-reset`}>
          {t("print.cg.reset")}</button>
        {!fixed && <span className="grow" />}
        <IconBtn icon={ArrowUp} title={t("app.up")} disabled={sel <= 0} onClick={() => move(-1)} />
        <IconBtn icon={ArrowDown} title={t("app.down")} disabled={sel < 0 || sel >= rows.length - 1} onClick={() => move(1)} />
        {!fixed && <IconBtn icon={Plus} title={t("app.add")} disabled={!missing.length} onClick={() => setAdding(!adding)} />}
        {!fixed && <IconBtn icon={Trash} title={t("app.delete")} disabled={sel < 0} onClick={remove} />}
      </div>
      {adding && (
        <div className="cgrid-add">
          <select className="inp sel" value="" onChange={(e) => { if (e.target.value) add(e.target.value); }} data-testid={`${testid ?? "cgrid"}-add`}>
            <option value="">{t("print.cg.add_which")}</option>
            {missing.map((d) => <option key={d.key} value={d.key}>{d.name} — {d.desc}</option>)}
          </select>
        </div>
      )}
      <table className="pgrid cgrid-t">
        <thead><tr><th className="w-n">{t("print.cg.n")}</th><th className="w-on">{t("print.cg.on")}</th><th className="w-name">{t("print.cg.name")}</th>
          <th>{t("print.cg.desc")}</th><th className="w-w">{t("print.cg.width")}</th></tr></thead>
        <tbody>
          {rows.map((r, i) => {
            const d = byKey.get(r.key)!;
            return (
              <tr key={r.key} className={cx(i === sel && "tr-sel")} onClick={() => setSel(i)} data-testid={`${testid ?? "cgrid"}-row-${r.key}`}>
                <td className="c">{i + 1}</td>
                <td className="c"><input type="checkbox" checked={r.on} onChange={(e) => set(i, { on: e.target.checked })}
                  data-testid={`${testid ?? "cgrid"}-on-${r.key}`} /></td>
                <td><b>{d.name}</b></td>
                <td className="pgrid-k" title={d.desc}>{d.desc}</td>
                <td className="pgrid-v"><NumCell value={r.width} min={1} max={200} onCommit={(v) => set(i, { width: Math.round(v) })} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
