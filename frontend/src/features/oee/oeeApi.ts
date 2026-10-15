// OEE (W17): server turlari, so'rov hooklari, holat (zustand) va yordamchi formatlash funksiyalari.
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { create } from "zustand";
import { get } from "../../api/client";

export type Band = "low" | "mid" | "high" | "none";
export type OeeTab = "overview" | "events" | "machines" | "shifts" | "reasons" | "params";
export type Group = "hour" | "shift" | "day" | "week";

export interface OeeConfig { tz_offset_min: number; idle_gap_s: number; run_cap_factor: number; unit: "sheet" | "part"; include_overtime: boolean }
export interface OeeMeta { config: OeeConfig; bands: { low: number; high: number }; groups: string[]; periods: string[]; kinds: string[];
  demo_enabled: boolean; max_batch: number }
export interface OeeMachine { id: number; key: string; name: string; kind: "saw" | "edge" | "cnc" | "other"; pp_key: string | null; pp_name: string | null;
  cut_speed_mm_s: number | null; cut_change_s: number | null; sheet_load_s: number | null; ideal_unit_s: number | null; active: boolean; note: string }
export interface OeeReason { id: number; code: string; name_ru: string; name_uz: string; kind: "downtime" | "reject"; planned: boolean; active: boolean;
  sort: number; system: boolean }
export interface OeeBreak { start: string; end: string; name: string }
export interface OeeShift { id: number; kind: "shift" | "off"; machine: string | null; name: string; weekdays: number[]; start: string | null; end: string | null;
  breaks: OeeBreak[]; valid_from: string | null; valid_to: string | null; active: boolean }
export interface ShiftPreview { name: string; date: string; start: string; end: string; planned_min: number; breaks: { start: string; end: string; name: string }[] }
export interface OeeEvent { id: number; type: "run" | "downtime" | "reject"; machine: string; start: string | null; end: string | null; qty: number | null;
  reject_qty: number | null; unit: string | null; parts: number | null; parts_per_sheet: number | null; cut_length_m: number | null; cuts: number | null;
  sheets_per_pack: number | null; ideal_cycle_s: number | null; reason: string | null; note: string | null; project_number: number | null;
  project_id: string | null; op_id: string | null; map_index: number | null; source: string | null; external_id: string | null; created_by: string | null;
  open: boolean }

export type Bands = Record<"oee" | "availability" | "performance" | "quality", Band>;
export interface Metrics {
  availability: number | null; performance: number | null; performance_raw: number | null; quality: number | null; oee: number | null;
  planned_min: number; run_min: number; stop_min: number; idle_min: number; ideal_min: number; produced: number; rejected: number; good: number;
  sheets: number; parts: number | null; avg_cycle_s: number | null; ideal_cycle_s: number | null; events: number; capped: boolean; outside: number | null;
  band: Bands;
}
export interface SeriesPoint extends Metrics { start: string; end: string; label: string; name?: string; date?: string }
export interface MachineRow extends Partial<Metrics> { machine: string; name: string; kind: string; has_data: boolean }
export interface ParetoItem { reason: string; name_ru: string; name_uz: string; minutes: number; count: number; planned: boolean; share?: number; cumulative?: number }
export interface Warning { code: string; count?: number; machines?: string[] }
/** Material samaradorligi (OEE ga kirmaydi): list to'ldirilishi va otxod (деловой qoldiq ayirilgan). */
export interface Material { sheets: number; sheet_m2: number; parts_m2: number; remnant_m2: number; fill: number | null; waste: number | null }
export interface Dashboard {
  machine: string | null; from: string; to: string; as_of: string; group_by: Group; config: OeeConfig; bands: { low: number; high: number };
  summary: Metrics & { machines: number }; machines: MachineRow[]; material: Material; series: SeriesPoint[]; extra_series: Record<string, SeriesPoint[]>;
  pareto: ParetoItem[]; pareto_total_min: number; planned_losses: ParetoItem[]; warnings: Warning[];
}

// ───────────────────────── holat ─────────────────────────
const PERIODS = ["today", "yesterday", "last7", "last14", "last30", "this_week", "this_month", "custom"] as const;
export type Period = (typeof PERIODS)[number];
export const PERIOD_LIST: readonly Period[] = PERIODS;

function load<T>(key: string, dflt: T): T {
  try { const v = localStorage.getItem(key); return v === null ? dflt : (JSON.parse(v) as T); } catch { return dflt; }
}
function save(key: string, v: unknown) { try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* yo'q */ } }

interface OeeUI {
  tab: OeeTab; period: Period; from: string; to: string; machine: string; group: Group; lines: string[];
  set: (p: Partial<OeeUI>) => void;
}
export const useOeeUI = create<OeeUI>((set) => ({
  tab: "overview", period: load<Period>("mxk_oee_period", "last14"), from: "", to: "", machine: load("mxk_oee_machine", ""),
  group: load<Group>("mxk_oee_group", "day"), lines: load<string[]>("mxk_oee_lines", ["oee"]),
  set: (p) => {
    set(p);
    if (p.period !== undefined) save("mxk_oee_period", p.period);
    if (p.machine !== undefined) save("mxk_oee_machine", p.machine);
    if (p.group !== undefined) save("mxk_oee_group", p.group);
    if (p.lines !== undefined) save("mxk_oee_lines", p.lines);
  },
}));

/** Davr → so'rov parametrlari (server zavod kunlari bilan hisoblaydi). */
export function periodQuery(s: { period: Period; from: string; to: string }): Record<string, string> {
  if (s.period === "custom") return s.from ? { from: s.from, ...(s.to ? { to: s.to } : {}) } : { period: "last14" };
  return { period: s.period };
}

// ───────────────────────── so'rovlar ─────────────────────────
export const useOeeMeta = () => useQuery({ queryKey: ["oee", "meta"], queryFn: () => get<OeeMeta>("/oee/config"), staleTime: 60_000 });
export const useOeeMachines = () => useQuery({ queryKey: ["oee", "machines"], queryFn: () => get<OeeMachine[]>("/oee/machines") });
export const useOeeReasons = () => useQuery({ queryKey: ["oee", "reasons"], queryFn: () => get<OeeReason[]>("/oee/reasons") });
export const useOeeShifts = () => useQuery({ queryKey: ["oee", "shifts"], queryFn: () => get<OeeShift[]>("/oee/shifts") });

export function useOeeDashboard(machine: string, group: Group, pq: Record<string, string>) {
  return useQuery({
    queryKey: ["oee", "dash", machine, group, pq],
    queryFn: () => get<Dashboard>("/oee/dashboard", { machine: machine || undefined, group_by: group, ...pq }),
    placeholderData: keepPreviousData, refetchInterval: 60_000,
  });
}

export function useOeeEvents(q: Record<string, string | number | undefined>) {
  return useQuery({ queryKey: ["oee", "events", q], queryFn: () => get<{ total: number; items: OeeEvent[] }>("/oee/events", q),
    placeholderData: keepPreviousData });
}

export function useOeeGaps(machine: string, pq: Record<string, string>) {
  return useQuery({ queryKey: ["oee", "gaps", machine, pq], enabled: !!machine,
    queryFn: () => get<{ machine: string; items: { start: string; end: string; minutes: number }[] }>("/oee/gaps", { machine, ...pq }) });
}

// ───────────────────────── formatlash ─────────────────────────
/** 0…1 → «72.5 %» (null — «—»). */
export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)} %`;
}

/** Daqiqa → «7 ч 12 мин» / «7 soat 12 daq»; h va m — birlik yorliqlari. */
export function fmtMin(min: number | null | undefined, h: string, m: string): string {
  if (min === null || min === undefined || Number.isNaN(min)) return "—";
  const r = Math.round(min);
  if (r < 60) return `${r} ${m}`;
  const mm = r % 60;
  return mm ? `${Math.floor(r / 60)} ${h} ${mm} ${m}` : `${Math.floor(r / 60)} ${h}`;
}

export function fmtNum(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return String(Math.round(v * 10 ** digits) / 10 ** digits);
}

/** Zavod vaqti siljishi (daqiqa) → «+5» / «+5:30» / «-3» (matn uchun). */
export function tzStr(off: number): string {
  const sign = off < 0 ? "-" : "+";
  const a = Math.abs(off);
  const h = Math.floor(a / 60), m = a % 60;
  return `${sign}${h}${m ? ":" + String(m).padStart(2, "0") : ""}`;
}

/** UTC ISO → zavod vaqti «dd.mm HH:MM» (off — UTC dan daqiqa siljish). */
export function fmtLocal(iso: string | null | undefined, off: number, withSeconds = false): string {
  if (!iso) return "—";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  const d = new Date(t + off * 60000);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getUTCDate())}.${p(d.getUTCMonth() + 1)} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}${withSeconds ? ":" + p(d.getUTCSeconds()) : ""}`;
}

/** UTC ISO → `datetime-local` qiymati (zavod vaqtida). */
export function isoToInput(iso: string | null | undefined, off: number): string {
  if (!iso) return "";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "";
  const d = new Date(t + off * 60000);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())}T${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
}

/** `datetime-local` qiymati (zavod vaqti) → UTC ISO (`...Z`); bo'sh — null. */
export function inputToIso(v: string, off: number): string | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(v.trim());
  if (!m) return null;
  const ms = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], m[6] ? +m[6] : 0) - off * 60000;
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

/** Grafik o'qi yorlig'i: kun «02.10», soat «08:00», smena «02.10 Smena 1», hafta «W40». */
export function axisLabel(p: { label: string; date?: string; name?: string }, group: Group): string {
  if (group === "day") return `${p.label.slice(8, 10)}.${p.label.slice(5, 7)}`;
  if (group === "hour") return p.label.slice(11, 16);
  if (group === "week") return p.label.slice(5);
  return `${(p.date ?? p.label).slice(8, 10)}.${(p.date ?? p.label).slice(5, 7)} ${p.name ?? ""}`.trim();
}

export function reasonName(r: { name_ru: string; name_uz: string } | undefined, lang: string, fallback = ""): string {
  if (!r) return fallback;
  return lang === "uz" ? r.name_uz || r.name_ru : r.name_ru || r.name_uz;
}
