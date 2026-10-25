// «Остатки: приход» / «Остатки: расход» (2026-10-24, foydalanuvchi talabi): «Операции | Изделия» yonida, tanlangan CS operatsiya uchun.
// Приход — kroydan bazaga: har qoldiq bo'lagi foizi, qoida bo'yicha «на склад / клиенту», texnolog tanlovi, «Записать в базу».
// Расход — bazadagi AYNAN shu material (kod / nom) qoldiqlari: avval material sarfini kamaytiradiganlari (tejash, mijozga narxi),
// keyin detallari sig'adigan barcha qoldiqlar (qaysi detallar) — «В раскрой» (band qilinadi va qayta kesiladi).
// Ombor ma'lumotlari MES bazasida (manba — «Правила остатков»), MX o'qiydi va qayd qiladi.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownToLine, ArrowUpFromLine, ListChecks, RotateCcw, Undo2 } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, post, put } from "../../api/client";
import type { Operation, Project, Remnant } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Empty, Sel, Tabs, fmt } from "../../shared/ui";
import { runCutting } from "../cs/CsCut";
import { topTabs, type TopTab } from "./topTabs";
import { RemnantAssignDialog } from "./RemnantAssign";
import "./remnantTabs.css";

interface Piece { key: string; map: number; length: number; width: number; area_m2: number; percent: number; keep: boolean;
  auto_keep: boolean; manual: boolean; qty: number }
interface Intake { saved: boolean; keep_percent: number | null; rule_source: string | null; sheet_m2: number | null; material: string;
  code: string; type: string; pieces: Piece[]; consumed: { id: number; qty: number; length: number; width: number; area_m2: number;
  sale_price: number }[]; source: "local" | "mes"; pending: boolean; has_result: boolean }
type Rem = Remnant & { percent: number | null; sale_price: number };
type FitPart = { id: string; name: string; length: number; width: number; qty: number; left: number };
type FitRow = Rem & { in_sheets: boolean; fit_count: number; fit_left: number; fit_parts: FitPart[] };
interface Match { saving: (Rem & { saving_m2: number; fit_parts: number })[]; cut: boolean; material: string; code: string; type: string;
  fitting: FitRow[]; left: number }

/** Tanlangan operatsiya (CS bo'lmasa — loyihadagi birinchi CS) va operatsiya tanlovi. */
function useCsOp(project: Project): [Operation | undefined, Operation[]] {
  const opId = useUI((s) => s.opId);
  const cs = project.operations.filter((o) => o.type === "CS");
  return [cs.find((o) => o.id === opId) ?? cs[0], cs];
}

function Head({ project, kind, op, cs }: { project: Project; kind: TopTab; op?: Operation; cs: Operation[] }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Tabs tabs={topTabs(t)} value={kind} onChange={(k) => ui.set({ topTab: k })}
      right={cs.length > 1 ? <Sel value={op?.id ?? ""} width={260} testid="rt-op" onChange={(v) => ui.set({ opId: v, mapIndex: 1 })}
        options={cs.map((o) => ({ value: o.id, label: `(CS) ${o.name || o.code}` }))} /> : undefined} />
  );
}

export function RemnantInPanel({ project }: { project: Project }) {
  const { t } = useTranslation();
  const [op, cs] = useCsOp(project);
  const stamp = op?.result?.maps.length ? `${op.result.elapsed_s}-${op.result.remnants_saved}` : "none";
  const q = useQuery({ enabled: !!op, queryKey: ["remnant-intake", project.id, op?.id, stamp],
    queryFn: () => get<Intake>(`/projects/${project.id}/operations/${op!.id}/remnant-intake`) });
  const d = q.data;
  const refresh = () => { void qc.invalidateQueries({ queryKey: ["project", project.id] }); void qc.invalidateQueries({ queryKey: ["remnant-intake"] });
    void qc.invalidateQueries({ queryKey: ["remnants"] }); };
  const setKeep = async (key: string, keep: boolean | null) => {
    const r = await call(() => put(`/projects/${project.id}/operations/${op!.id}/remnant-intake`, { key, keep }));
    if (r) void qc.invalidateQueries({ queryKey: ["remnant-intake"] });
  };
  const commit = async () => {
    const r = await call(() => post<{ added: unknown[] }>(`/projects/${project.id}/operations/${op!.id}/remnants/commit`));
    if (r) { useUI.getState().toast(t("rem.committed", { n: r.added.length }), "ok"); refresh(); }
  };
  const rollback = async () => {
    const r = await call(() => post(`/projects/${project.id}/operations/${op!.id}/remnants/rollback`));
    if (r) { useUI.getState().toast(t("rem.rolled_back"), "info"); refresh(); }
  };
  const keepN = (d?.pieces ?? []).filter((p) => p.keep).reduce((s, p) => s + p.qty, 0);
  const keepA = (d?.pieces ?? []).filter((p) => p.keep).reduce((s, p) => s + p.area_m2 * p.qty, 0);
  return (
    <div className="panel rt" data-testid="rt-in">
      <Head project={project} kind="rem_in" op={op} cs={cs} />
      {!op ? <Empty>{t("rt.no_cs")}</Empty> : !d ? null : !d.has_result ? <Empty>{t("rt.no_cut")}</Empty> : (
        <div className="rt-body">
          <div className="rt-bar">
            <b>(CS) {d.material}</b>{d.code && <span className="muted"> · {d.code}</span>}<span className="muted"> · {d.type || "—"}</span>
            <span className="rt-rule">{d.keep_percent != null ? t("rem.rule_line", { p: d.keep_percent }) : t("rt.no_rule")}</span>
            <span className="grow" />
            <span className="muted">{t("rt.keep_total", { n: keepN, a: fmt(keepA) })}</span>
            {d.saved
              ? <><span className="rt-saved">{t(d.source === "mes" ? "rt.saved_mes" : "rt.saved")}</span>
                <Btn icon={Undo2} kind="danger" label={t("rem.rollback")} onClick={() => void rollback()} testid="rt-rollback" /></>
              : <>{!keepN && !d.consumed.length && <span className="muted" data-testid="rt-nothing">{t("rt.nothing")}</span>}
                <Btn icon={ArrowDownToLine} kind="primary" label={t(d.source === "mes" ? "rt.commit_mes" : "rt.commit")} testid="rt-commit"
                  disabled={!keepN && !d.consumed.length} onClick={() => void commit()} /></>}
          </div>
          <table className="simple rt-table" data-testid="rt-in-table">
            <thead><tr><th>{t("rt.map")}</th><th>{t("sheets.col.length")}</th><th>{t("sheets.col.width")}</th><th>{t("sheets.col.qty")}</th>
              <th>{t("u.m2")}</th><th>%</th><th>{t("rt.by_rule")}</th><th>{t("rt.decision")}</th></tr></thead>
            <tbody>
              {d.pieces.map((p) => (
                <tr key={p.key} className={p.keep ? "rt-keep" : "rt-client"} data-testid={`rt-piece-${p.key}`}>
                  <td className="num">{p.map}</td><td className="num">{fmt(p.length)}</td><td className="num">{fmt(p.width)}</td>
                  <td className="num">{p.qty}</td><td className="num">{fmt(p.area_m2, 3)}</td><td className="num">{fmt(p.percent, 1)}</td>
                  <td>{t(p.auto_keep ? "rt.to_stock" : "rt.to_client")}</td>
                  <td className="rt-dec">
                    <label><input type="radio" disabled={d.saved} checked={p.keep} onChange={() => void setKeep(p.key, true)}
                      data-testid={`rt-keep-${p.key}`} /> {t("rt.to_stock")}</label>
                    <label><input type="radio" disabled={d.saved} checked={!p.keep} onChange={() => void setKeep(p.key, false)}
                      data-testid={`rt-client-${p.key}`} /> {t("rt.to_client")}</label>
                    {p.manual && !d.saved && <button type="button" className="linkbtn" title={t("rt.reset")} onClick={() => void setKeep(p.key, null)}>
                      <RotateCcw size={12} /></button>}
                  </td>
                </tr>
              ))}
              {!d.pieces.length && <tr><td colSpan={8} className="muted">{t("rem.none")}</td></tr>}
            </tbody>
          </table>
          {d.consumed.length > 0 && <>
            <div className="rt-sub">{t("rt.consumed")}</div>
            <table className="simple rt-table">
              <thead><tr><th>ID</th><th>{t("sheets.col.length")}</th><th>{t("sheets.col.width")}</th><th>{t("sheets.col.qty")}</th>
                <th>{t("u.m2")}</th><th>{t("ro.price")}</th></tr></thead>
              <tbody>{d.consumed.map((c) => (
                <tr key={c.id}><td className="num">{c.id}</td><td className="num">{fmt(c.length)}</td><td className="num">{fmt(c.width)}</td>
                  <td className="num">{c.qty}</td><td className="num">{fmt(c.area_m2, 3)}</td><td className="num">{fmt(c.sale_price)}</td></tr>))}</tbody>
            </table></>}
          {d.pending && !d.saved && <p className="muted">{t("rem.pending_note")}</p>}
        </div>
      )}
    </div>
  );
}

export function RemnantOutPanel({ project }: { project: Project }) {
  const { t } = useTranslation();
  const [op, cs] = useCsOp(project);
  const stamp = `${op?.result?.elapsed_s ?? "none"}-${op?.sheets.length ?? 0}`;
  const q = useQuery({ enabled: !!op, queryKey: ["remnant-match", project.id, op?.id, stamp],
    queryFn: () => get<Match>(`/projects/${project.id}/operations/${op!.id}/remnant-match`),
    placeholderData: (prev) => (prev && op ? prev : undefined) });      // yangilanayotganda eski ro'yxat ko'rinib turadi
  const [busy, setBusy] = useState(false);
  const [pick, setPick] = useState<number | null>(null);         // «Детали на остаток» oynasi — qoldiq №
  const d = q.data;
  const saveIds = useMemo(() => new Set((d?.saving ?? []).map((r) => r.id)), [d]);
  // detallar ro'yxatida aniq qoldiqqa bog'langanlar: {qoldiq №: [«nom ×n»]}
  const bound = useMemo(() => {
    const m = new Map<number, string[]>();
    for (const p of op?.parts ?? []) {
      if (p.remnant_id == null) continue;
      const n = p.remnant_count ?? p.qty;
      m.set(p.remnant_id, [...(m.get(p.remnant_id) ?? []), `${p.name || p.length + "×" + p.width}${n > 1 ? ` ×${n}` : ""}`]);
    }
    return m;
  }, [op]);
  const use = async (id: number) => {
    if (!op) return;
    setBusy(true);
    try {
      const r = await call(() => post(`/projects/${project.id}/operations/${op.id}/sheets/from-remnants`, { ids: [id] }));
      if (!r) return;
      void qc.invalidateQueries({ queryKey: ["remnants"] });
      await runCutting(project, op, t);
      void qc.invalidateQueries({ queryKey: ["remnant-match"] });
    } finally { setBusy(false); }
  };
  return (
    <div className="panel rt" data-testid="rt-out">
      <Head project={project} kind="rem_out" op={op} cs={cs} />
      {/* oyna ro'yxat qayta yuklanishiga bog'liq emas (avval ro'yxat yangilanganda kroy tugamasdan yopilib qolardi) */}
      {pick != null && op && <RemnantAssignDialog project={project} op={op} rid={pick} onClose={() => setPick(null)} />}
      {!op ? <Empty>{t("rt.no_cs")}</Empty> : !d ? <Empty>{t("rt.searching")}</Empty> : (
        <div className="rt-body">
          <div className="rt-bar"><b>(CS) {d.material}</b>{d.code && <span className="muted"> · {d.code}</span>}
            <span className="muted"> · {d.type || "—"}</span><span className="grow" /><span className="muted">{t("ro.sale_hint")}</span></div>
          {bound.size > 0 && <div className="rt-bound" data-testid="rt-bound">
            {[...bound.entries()].map(([rid, list]) => (
              <div key={rid}><b>{t("ra.bound", { id: rid })}</b> {list.join(", ")}{" "}
                <button type="button" className="linkbtn" onClick={() => setPick(rid)}>{t("ra.change")}</button></div>))}
          </div>}
          {d.left > 0 && <>
            <div className="rt-sub rt-left">{t("rt.left_title", { n: d.left })}</div>
            {!d.fitting.some((r) => r.fit_left > 0) ? <p className="muted" data-testid="rt-left-none">{t("rt.left_none")}</p>
              : <FitTable rows={d.fitting.filter((r) => r.fit_left > 0)} onlyLeft busy={busy} use={use} pick={setPick} saveIds={saveIds} testid="rt-left" />}
          </>}
          <div className="rt-sub">{t("rt.saving")}</div>
          {!d.cut ? <p className="muted">{t("rt.cut_first")}</p> : !d.saving.length ? <p className="muted" data-testid="rt-no-saving">{t("ro.empty")}</p> : (
            <table className="simple rt-table" data-testid="rt-saving">
              <thead><tr><th>ID</th><th>{t("ro.size")}</th><th>{t("u.m2")}</th><th>%</th><th>{t("ro.saving")}</th><th>{t("ro.price")}</th>
                <th>{t("rem.note")}</th><th /></tr></thead>
              <tbody>{d.saving.map((r) => (
                <tr key={r.id} className="rt-keep">
                  <td className="num">{r.id}</td><td>{fmt(r.length)} × {fmt(r.width)}</td><td className="num">{fmt(r.area_m2, 3)}</td>
                  <td className="num">{fmt(r.percent, 1)}</td><td className="num"><b>{fmt(r.saving_m2)}</b></td><td className="num">{fmt(r.sale_price)}</td>
                  <td>{r.note}</td>
                  <td className="rt-acts"><Btn icon={ListChecks} label={t("ra.btn")} disabled={busy} onClick={() => setPick(r.id)} testid={`rt-pick-${r.id}`} />
                    <Btn icon={ArrowUpFromLine} kind="primary" label={t("rt.use")} disabled={busy} onClick={() => void use(r.id)} testid={`rt-use-${r.id}`} /></td>
                </tr>))}</tbody>
            </table>)}
          <div className="rt-sub">{t("rt.fitting")}</div>
          {!d.fitting.length ? <p className="muted">{t("rt.none_fit")}</p>
            : <FitTable rows={d.fitting} busy={busy} use={use} pick={setPick} saveIds={saveIds} testid="rt-fitting" />}
        </div>
      )}
    </div>
  );
}

/** Detallari sig'adigan qoldiqlar jadvali (`onlyLeft` — faqat kroyga sig'may qolgan detallar). */
function FitTable({ rows, onlyLeft, busy, use, pick, saveIds, testid }: { rows: FitRow[]; onlyLeft?: boolean; busy: boolean;
  use: (id: number) => Promise<void>; pick: (id: number) => void; saveIds: Set<number>; testid: string }) {
  const { t } = useTranslation();
  const label = (p: FitPart) => `${p.length}×${p.width}${(onlyLeft ? p.left : p.qty) > 1 ? ` ×${onlyLeft ? p.left : p.qty}` : ""}`;
  return (
    <table className="simple rt-table" data-testid={testid}>
      <thead><tr><th>ID</th><th>{t("ro.size")}</th><th>{t("u.m2")}</th><th>%</th><th>{t(onlyLeft ? "rt.fit_left" : "rt.fit_parts")}</th>
        <th>{t("ro.price")}</th><th>{t("rem.note")}</th><th /></tr></thead>
      <tbody>{rows.map((r) => {
        const fp = onlyLeft ? r.fit_parts.filter((p) => p.left > 0) : r.fit_parts;
        return (
          <tr key={r.id} className={saveIds.has(r.id) || onlyLeft ? "rt-keep" : ""}>
            <td className="num">{r.id}</td><td>{fmt(r.length)} × {fmt(r.width)}</td><td className="num">{fmt(r.area_m2, 3)}</td>
            <td className="num">{fmt(r.percent, 1)}</td>
            <td className="rt-parts" title={fp.map((p) => `${p.name || p.id} ${label(p)}`).join("\n")}>
              {fp.slice(0, 6).map(label).join(", ")}{fp.length > 6 ? ` … (+${fp.length - 6})` : ""}</td>
            <td className="num">{fmt(r.sale_price)}</td><td>{r.note}</td>
            <td className="rt-acts"><Btn icon={ListChecks} label={t("ra.btn")} disabled={busy} onClick={() => pick(r.id)} testid={`${testid}-pick-${r.id}`} />
              {r.in_sheets ? <span className="muted">{t("rt.in_sheets")}</span>
              : <Btn icon={ArrowUpFromLine} label={t("rt.use")} disabled={busy} onClick={() => void use(r.id)} testid={`${testid}-use-${r.id}`} />}</td>
          </tr>);
      })}</tbody>
    </table>
  );
}
