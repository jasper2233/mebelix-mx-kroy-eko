// «Детали на остаток» (2026-10-25, foydalanuvchi talabi): qoldiqqa qaysi detallar (nechta dona) kirishini xodim tanlaydi —
// «Авто» (eng ko'p tejaydigan to'plam) yoki qo'lda ptichka / soni. Tanlov detallar ro'yxatiga o'zi yoziladi (detal aniq qoldiqqa
// bog'lanadi). Tanlangan detallar qoldiqqa sig'masa — saqlanmaydi, kroy boshlanmaydi: «tanlangan detallar bu qoldiqqa sig'maydi».
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Eraser, Scissors, Sparkles } from "lucide-react";
import { qc } from "../../api/hooks";
import { get, post } from "../../api/client";
import type { Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal, fmt } from "../../shared/ui";
import { runCutting } from "../cs/CsCut";
import "./remnantTabs.css";

interface Row { id: string; name: string; code: string; length: number; width: number; qty: number; fits: boolean; count: number;
  other: number | null }
interface View { remnant_id: number; sheet: { length: number; width: number; in_sheets: boolean } | null; parts: Row[] }

function errText(e: unknown): string {
  const m = e instanceof Error ? e.message : String(e);
  return m;
}

export function RemnantAssignDialog({ project, op, rid, onClose }: { project: Project; op: Operation; rid: number; onClose: () => void }) {
  const { t } = useTranslation();
  const base = `/projects/${project.id}/operations/${op.id}`;
  const [v, setV] = useState<View | null>(null);
  const [cnt, setCnt] = useState<Record<string, number>>({});
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [autoNote, setAutoNote] = useState("");
  useEffect(() => {
    void get<View>(`${base}/remnant-assign/${rid}`).then((x) => {
      setV(x);
      setCnt(Object.fromEntries(x.parts.map((p) => [p.id, p.count])));
    }).catch((e) => setErr(errText(e)));
  }, [base, rid]);
  const set = (id: string, n: number, max: number) => { setErr(""); setCnt((c) => ({ ...c, [id]: Math.max(0, Math.min(max, Math.round(n || 0))) })); };
  const auto = async () => {
    setBusy(true); setErr("");
    try {
      const a = await post<{ parts: { id: string; count: number }[]; saving: boolean }>(`${base}/remnant-auto/${rid}`);
      const next: Record<string, number> = Object.fromEntries((v?.parts ?? []).map((p) => [p.id, 0]));
      for (const p of a.parts) next[p.id] = p.count;
      setCnt(next);
      setAutoNote(t(a.saving ? "ra.auto_saving" : "ra.auto_fill"));
    } catch (e) { setErr(errText(e)); } finally { setBusy(false); }
  };
  const save = async (cut: boolean) => {
    setBusy(true); setErr("");
    try {
      const parts = Object.entries(cnt).filter(([, n]) => n > 0).map(([id, count]) => ({ id, count }));
      await post(`${base}/remnant-assign`, { remnant_id: rid, parts });
      await qc.invalidateQueries({ queryKey: ["project", project.id] });
      void qc.invalidateQueries({ queryKey: ["remnants"] });
      void qc.invalidateQueries({ queryKey: ["remnant-match"] });
      if (cut) {
        const fresh = await get<Project>(`/projects/${project.id}`);
        const o2 = fresh.operations.find((o) => o.id === op.id) ?? op;
        const r = await runCutting(fresh, o2, t);
        if (!r) return;                                          // xato xabari (masalan sig'maydi) — oyna ochiq qoladi
      } else {
        useUI.getState().toast(t("ra.saved"), "ok");
      }
      onClose();
    } catch (e) { setErr(errText(e)); } finally { setBusy(false); }
  };
  const total = (v?.parts ?? []).reduce((s, p) => s + (cnt[p.id] ?? 0), 0);
  const area = (v?.parts ?? []).reduce((s, p) => s + (cnt[p.id] ?? 0) * p.length * p.width / 1e6, 0);
  return (
    <Modal title={t("ra.title", { id: rid, s: v?.sheet ? `${fmt(v.sheet.length)} × ${fmt(v.sheet.width)}` : "" })} onClose={onClose}
      width={860} height={560} testid="remnant-assign"
      footer={<>
        <Btn icon={Sparkles} label={t("ra.auto")} onClick={() => void auto()} disabled={busy || !v} testid="ra-auto" />
        <Btn icon={Eraser} label={t("ra.clear")} onClick={() => { setErr(""); setAutoNote(""); setCnt(Object.fromEntries((v?.parts ?? []).map((p) => [p.id, 0]))); }}
          disabled={busy || !v} testid="ra-clear" />
        <span className="grow" />
        <span className="muted">{t("ra.total", { n: total, a: fmt(area, 3) })}</span>
        <Btn icon={Scissors} kind="primary" label={t("ra.save_cut")} onClick={() => void save(true)} disabled={busy || !v} testid="ra-save-cut" />
        <Btn label={t("ra.save")} onClick={() => void save(false)} disabled={busy || !v} testid="ra-save" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <p className="muted">{t("ra.hint")}</p>
      {autoNote && <p className="ra-note" data-testid="ra-note">{autoNote}</p>}
      {err && <p className="ra-err" data-testid="ra-err">{err}</p>}
      <div className="ra-scroll">
        <table className="simple rt-table ra-table" data-testid="ra-table">
          <thead><tr><th /><th>{t("ra.part")}</th><th>{t("ro.size")}</th><th>{t("sheets.col.qty")}</th><th>{t("ra.on_remnant")}</th><th /></tr></thead>
          <tbody>
            {(v?.parts ?? []).map((p) => {
              const n = cnt[p.id] ?? 0;
              return (
                <tr key={p.id} className={n > 0 ? "rt-keep" : ""} data-testid={`ra-row-${p.id}`}>
                  <td><input type="checkbox" checked={n > 0} disabled={!p.fits && n === 0} data-testid={`ra-check-${p.id}`}
                    onChange={(e) => set(p.id, e.target.checked ? p.qty : 0, p.qty)} /></td>
                  <td>{p.name || p.code || p.id}</td>
                  <td className="num">{fmt(p.length)} × {fmt(p.width)}</td>
                  <td className="num">{p.qty}</td>
                  <td><input className="inp ra-num" type="number" min={0} max={p.qty} value={n} data-testid={`ra-count-${p.id}`}
                    onChange={(e) => set(p.id, Number(e.target.value), p.qty)} /> / {p.qty}</td>
                  <td className="muted">{!p.fits ? t("ra.too_big") : p.other ? t("ra.other", { id: p.other }) : ""}</td>
                </tr>
              );
            })}
            {v && !v.parts.length && <tr><td colSpan={6} className="muted">{t("rt.none_fit")}</td></tr>}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
