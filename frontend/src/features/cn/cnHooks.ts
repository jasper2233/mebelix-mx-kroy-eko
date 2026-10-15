// (CN) so'rovlar va FON VAZIFASI: hisob miqdorlari, detal shakllari, nesting vazifasi (progress / to'xtatish), ko'rinish sozlamalari.
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { create } from "zustand";
import { ApiError, del, get, post } from "../../api/client";
import { qc } from "../../api/hooks";
import type { CnJob, CnQuantities, CnShapes, Operation, Project, Quality } from "../../api/types";
import { showError } from "../../shared/dialogs";
import { useUI } from "../../store/ui";
import i18n from "../../i18n";

/** Hisoblanadigan maydonlar (usage_m2 / multiplicity) so'rov izidan chiqariladi — ular o'zi o'zgarib so'rovni qayta-qayta yurgizmasin. */
const cnKey = (op: Operation) => {
  if (!op.cn) return null;
  const { usage_m2: _u, multiplicity: _m, ...rest } = op.cn;
  return rest;
};

export function useCnQuantities(project: Project, op: Operation) {
  const stamp = useMemo(() => JSON.stringify([project.size_mode, cnKey(op), op.sheets.map((s) => [s.length, s.width, s.qty, s.is_remnant, s.source_remnant_id]),
    op.parts.map((p) => [p.length, p.width, p.qty, p.minus_qty, p.product_id, p.allow_left, p.allow_right, p.allow_top, p.allow_bottom,
      p.edge_top.op_id, p.edge_bottom.op_id, p.edge_left.op_id, p.edge_right.op_id]),
    project.products.map((p) => [p.id, p.qty]), op.result?.total_sheets ?? null, op.result?.material_qty_m2 ?? null]),
  [project.size_mode, project.products, op.cn, op.sheets, op.parts, op.result]);
  return useQuery({
    queryKey: ["cn-quantities", project.id, op.id, stamp],
    queryFn: () => get<CnQuantities>(`/projects/${project.id}/operations/${op.id}/cn-quantities`),
    placeholderData: (prev) => prev,
  });
}

/** Detal shakllari: bog'langan XNC dasturlari ham izga kiradi (kontur shularning freza konturidan olinadi). */
export function useCnShapes(project: Project, op: Operation) {
  const stamp = useMemo(() => {
    const ids = new Set(op.parts.flatMap((p) => p.xnc_op_ids));
    return JSON.stringify([project.size_mode, cnKey(op), op.parts.map((p) => [p.id, p.length, p.width, p.qty, p.xnc_op_ids]),
      project.operations.filter((o) => ids.has(o.id)).map((o) => [o.id, o.xnc])]);
  }, [project.size_mode, project.operations, op.cn, op.parts]);
  return useQuery({
    queryKey: ["cn-shapes", project.id, op.id, stamp],
    queryFn: () => get<CnShapes>(`/projects/${project.id}/operations/${op.id}/cn-shapes`),
    placeholderData: (prev) => prev,
  });
}

// ───────────────────────── Fon vazifasi ─────────────────────────
interface JobsState {
  jobs: Record<string, CnJob | undefined>;      // operatsiya id → oxirgi vazifa holati
  fresh: Record<string, string | undefined>;     // operatsiya id → hozirgina tugagan vazifa id (panel o'qib, tozalaydi)
}
export const useCnJobs = create<JobsState>(() => ({ jobs: {}, fresh: {} }));

const setJob = (oid: string, job: CnJob) => useCnJobs.setState((s) => ({ jobs: { ...s.jobs, [oid]: job } }));
const polling = new Set<string>();
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Vazifa tugagan, xato yoki to'xtatilgan (panel yopilgan bo'lsa ham ishlaydi — so'rov modul darajasida). */
async function finish(pid: string, oid: string, job: CnJob) {
  const ui = useUI.getState();
  if (job.state === "done") {
    await qc.invalidateQueries({ queryKey: ["project", pid] });
    void qc.invalidateQueries({ queryKey: ["history", pid] });
    void qc.invalidateQueries({ queryKey: ["projects"] });
    if (useUI.getState().opId === oid) ui.set({ mapIndex: 1 });
    const r = job.result;
    if (r) {
      const msg = i18n.t("cn.cut.done", { n: r.sheets, fill: r.fill, s: r.elapsed_s });
      ui.toast(r.unplaced ? `${msg} · ${i18n.t("cut.unplaced", { n: r.unplaced })}` : msg, r.unplaced ? "error" : "ok");
    }
    useCnJobs.setState((s) => ({ fresh: { ...s.fresh, [oid]: job.id } }));
  } else if (job.state === "cancelled") {
    ui.toast(i18n.t("cn.cut.cancelled"), "info");
  } else if (job.state === "error") {
    ui.toast(job.error || i18n.t("cn.cut.failed"), "error");
  }
}

async function poll(pid: string, oid: string, jid: string) {
  if (polling.has(oid)) return;
  polling.add(oid);
  let fails = 0;
  try {
    for (;;) {
      await sleep(300);
      let job: CnJob;
      try {
        job = await get<CnJob>(`/projects/${pid}/operations/${oid}/cn/jobs/${jid}`);
        fails = 0;
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {                     // vazifa topilmadi (server qayta ishga tushgan)
          const cur = useCnJobs.getState().jobs[oid];
          if (cur) setJob(oid, { ...cur, state: "error", error: e.message });
          void finish(pid, oid, { ...(cur as CnJob), state: "error", error: e.message });
          return;
        }
        if (++fails >= 8) {
          const cur = useCnJobs.getState().jobs[oid];
          if (cur) setJob(oid, { ...cur, state: "error", error: String((e as Error).message ?? e) });
          showError(e);
          return;
        }
        continue;
      }
      setJob(oid, job);
      if (job.state !== "running") { await finish(pid, oid, job); return; }
    }
  } finally {
    polling.delete(oid);
  }
}

/** «Раскроить»: nestingni fon vazifasi sifatida boshlash (UI bloklanmaydi). 409 — shu operatsiya uchun hisob ketmoqda. */
export async function startCnJob(pid: string, oid: string, quality: Quality): Promise<boolean> {
  try {
    const job = await post<CnJob>(`/projects/${pid}/operations/${oid}/cn/jobs`, undefined, { quality });
    setJob(oid, job);
    void poll(pid, oid, job.id);
    return true;
  } catch (e) {
    showError(e);
    return false;
  }
}

/** Panel ochilganda / sahifa qayta yuklanganda: shu operatsiya uchun ketayotgan vazifa bo'lsa — progress holatiga o'tish (polling shu job id bilan davom etadi). */
export async function resumeCnJob(pid: string, oid: string): Promise<void> {
  if (polling.has(oid)) return;                             // allaqachon kuzatilmoqda
  try {
    const job = await get<CnJob | null>(`/projects/${pid}/operations/${oid}/cn/jobs/current`);
    if (job && job.state === "running" && !polling.has(oid)) {
      setJob(oid, job);
      void poll(pid, oid, job.id);
    }
  } catch { /* tarmoq xatosi — progress tiklanmaydi, hisob serverda davom etadi */ }
}

export async function cancelCnJob(pid: string, oid: string) {
  const job = useCnJobs.getState().jobs[oid];
  if (!job || job.state !== "running") return;
  try {
    const j = await del<CnJob>(`/projects/${pid}/operations/${oid}/cn/jobs/${job.id}`);
    if (j) setJob(oid, j);
  } catch (e) {
    showError(e);
  }
}

/** Operatsiyaning hozir ishlayotgan vazifasi (bo'lsa). */
export const useRunningCnJob = (oid: string): CnJob | undefined => useCnJobs((s) => (s.jobs[oid]?.state === "running" ? s.jobs[oid] : undefined));

// ───────────────────────── Ko'rinish sozlamalari ─────────────────────────
function load(key: string, dflt: boolean): boolean {
  try { const v = localStorage.getItem(key); return v === null ? dflt : v === "1"; } catch { return dflt; }
}
export const useCnPrefs = create<{ labels: boolean; setLabels: (v: boolean) => void }>((set) => ({
  labels: load("mxk_cn_labels", false),
  setLabels: (v) => { try { localStorage.setItem("mxk_cn_labels", v ? "1" : "0"); } catch { /* yo'q */ } set({ labels: v }); },
}));

/** CN holat qatori ko'rsatkichlari (CsCut bilan bir xil `indicator()`; «T» — torsovka — nestingda yo'q). */
export const CN_IND = ["num", "S", "C", "Cp", "LT", "F", "R", "CT", "AP", "AM", "AW"];
