// Kroydan keyin: деловой qoldiqlarni omborga yozish (tasdiq bilan) yoki bekor qilish.
// W2: mijoz olib ketadigan («Исп. кол-во») bo'laklar yozilmaydi; mayda qoldiq / butun list yozish — hozircha o'chirilgan (Q-5).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import i18n from "../../i18n";
import { get, post } from "../../api/client";
import { call, qc } from "../../api/hooks";
import type { CuttingResult, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Modal } from "../../shared/ui";

/** Omborga yozish oynasini ochish so'rovi (xabardagi tugmadan): operatsiya id si; shu operatsiya kroy paneli ochiq bo'lsa — oyna ochiladi. */
export const useRemnantOffer = create<{ opId: string | null }>(() => ({ opId: null }));

/** Kroy panelida: xabardagi «Записать на склад» bosilgan bo'lsa — oynani ochadi. */
export function useRemnantOfferOpen(opId: string, open: () => void) {
  const want = useRemnantOffer((s) => s.opId);
  useEffect(() => {
    if (want && want === opId) { useRemnantOffer.setState({ opId: null }); open(); }
  }, [want, opId]); // eslint-disable-line react-hooks/exhaustive-deps
}

/** Kroydan keyin деловой qoldiqlar omborga hali yozilmagan bo'lsa va sozlama («После раскроя предлагать…») yoqilgan bo'lsa —
 *  bloklamaydigan xabar va «Записать на склад» tugmasi (oyna har kroydan keyin o'zi ochilmaydi). */
export function offerRemnants(op: Operation, r: CuttingResult | null | undefined, enabled: boolean | undefined) {
  if (!r || !enabled || r.remnants_saved) return;
  const n = r.maps.reduce((s, mm) => s + mm.offcuts.filter((o) => o.kind === "remnant" && o.business).length * (mm.copies || 1), 0);
  if (!n) return;
  useUI.getState().toast(i18n.t("rem.offer", { n }), "info", undefined, { action: { label: i18n.t("rem.offer_btn"), testid: "remnant-offer",
    run: () => { useUI.getState().set({ opId: op.id }); useRemnantOffer.setState({ opId: op.id }); } } });
}

interface Info { saved: boolean; remnants: { length: number; width: number; qty: number; percent?: number | null }[];
  consumed: Record<string, number>; material_code: string;
  /** (2026-10-24) material foiz qoidasi: ≥ foiz — omborga, kichigi — mijozga; MES rejimida — MES bazasiga yuboriladi */
  keep_percent?: number | null; rule_source?: string | null; client?: { length: number; width: number; qty: number; percent: number }[];
  source?: "local" | "mes"; pending?: boolean }

export function RemnantCommitDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [info, setInfo] = useState<Info | null>(null);
  useEffect(() => { void call(() => get<Info>(`/projects/${project.id}/operations/${op.id}/remnants`)).then((r) => r && setInfo(r)); },
    [project.id, op.id, op.result]);
  const commit = async () => {
    const r = await call(() => post<{ added: unknown[] }>(`/projects/${project.id}/operations/${op.id}/remnants/commit`));
    if (r) { void qc.invalidateQueries({ queryKey: ["remnants"] }); useUI.getState().toast(t("rem.committed", { n: r.added.length }), "ok"); onClose(); }
  };
  const rollback = async () => {
    const r = await call(() => post(`/projects/${project.id}/operations/${op.id}/remnants/rollback`));
    if (r) { void qc.invalidateQueries({ queryKey: ["remnants"] }); useUI.getState().toast(t("rem.rolled_back"), "info"); onClose(); }
  };
  const consumed = Object.entries(info?.consumed ?? {});
  // mijoz olib ketadigan деловой bo'laklar («b:» kalitlar) — omborga yozilmaydi
  const taken = Object.entries(op.result?.taken_remnants ?? {}).filter(([k]) => k.startsWith("b:")).reduce((s, [, n]) => s + n, 0);
  return (
    <Modal title={t("rem.commit_title")} onClose={onClose} width={520} testid="remnant-commit"
      footer={info?.saved
        ? <><Btn kind="danger" label={t("rem.rollback")} onClick={() => void rollback()} /><Btn label={t("app.close")} onClick={onClose} /></>
        : <><Btn kind="primary" label={t("rem.commit")} onClick={() => void commit()} disabled={!info} testid="remnant-commit-ok" />
          <Btn label={t("rem.later")} onClick={onClose} /></>}>
      {!info ? null : (
        <>
          <p>{info.saved ? t("rem.already") : t(info.source === "mes" ? "rem.commit_text_mes" : "rem.commit_text", { code: info.material_code || "—" })}</p>
          {info.keep_percent != null && <p className="muted" data-testid="rem-rule">{t("rem.rule_line", { p: info.keep_percent })}</p>}
          {info.remnants.length ? (
            <table className="simple">
              <thead><tr><th>№</th><th>{t("sheets.col.length")}</th><th>{t("sheets.col.width")}</th><th>{t("sheets.col.qty")}</th><th>{t("u.m2")}</th><th>%</th></tr></thead>
              <tbody>{info.remnants.map((r, i) => (
                <tr key={i}><td>{i + 1}</td><td className="num">{r.length}</td><td className="num">{r.width}</td><td className="num">{r.qty}</td>
                  <td className="num">{Math.round((r.length * r.width) / 1e3) / 1e3}</td><td className="num">{r.percent ?? ""}</td></tr>))}</tbody>
            </table>
          ) : <p className="muted">{t("rem.none")}</p>}
          {!!info.client?.length && <p className="muted" data-testid="rem-client">{t("rem.client_line")}: {info.client.map((c) =>
            `${c.length}×${c.width}${c.qty > 1 ? ` ×${c.qty}` : ""} (${c.percent} %)`).join(", ")}</p>}
          {info.pending && !info.saved && <p className="muted">{t("rem.pending_note")}</p>}
          {taken > 0 && <p className="muted" data-testid="rem-taken-note">{t("rem.taken_note", { n: taken })}</p>}
          {consumed.length > 0 && <p className="muted">{t("rem.consumed")}: {consumed.map(([id, n]) => `#${id}×${n}`).join(", ")}</p>}
          <div className="rem-opts" data-testid="rem-opts">
            <Check checked={false} disabled label={t("rem.opt_small")} onChange={() => undefined} />
            <Check checked={false} disabled label={t("rem.opt_whole")} onChange={() => undefined} />
            <span className="param-note">{t("rem.opt_pending")}</span>
          </div>
        </>
      )}
    </Modal>
  );
}
