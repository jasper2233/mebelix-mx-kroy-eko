// Stanok sozlamalari sxemasi (ParamGrid) va «Данные для этикеток» (nom → ifoda) — W7. Server: `api_pp_machines.py`.
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { get, post, put } from "../../../api/client";
import { qc } from "../../../api/hooks";
import type { ProjectRow } from "../../../api/types";

export type ParamType = "bool" | "int" | "mm" | "float" | "string" | "path" | "choice" | "template";
export type ParamValue = boolean | number | string;

export interface SchemaOption { value: string; ru: string; uz: string }
export interface SchemaParam {
  key: string; type: ParamType; ru: string; uz: string; default: ParamValue; value: ParamValue; modified: boolean;
  min?: number; max?: number; options?: SchemaOption[]; custom?: boolean; enabled_if?: string; note?: { ru: string; uz: string };
}
export interface SchemaGroup { key: string; ru: string; uz: string; params: SchemaParam[] }
export interface LabelRow { name: string; expr: string }
export interface LabelTable {
  title: { ru: string; uz: string }; kind: "labels" | "udi"; max_rows: number; rows: LabelRow[]; defaults: LabelRow[]; is_default: boolean;
}
export interface MachineSchema {
  key: string; name: string; group: "saw" | "cnc"; info: { ru: string; uz: string } | null; groups: SchemaGroup[];
  values: Record<string, ParamValue>; defaults: Record<string, ParamValue>; modified: string[]; label_table: LabelTable | null;
}

export interface PreviewField {
  index: number; name: string; expr: string; ok: boolean; type: string | null; value: unknown; text: string;
  error: string | null; stage: "syntax" | "eval" | null; name_error: string | null;
}
export interface PreviewVariable { name: string; ru: string; uz: string; value: string | number | boolean | null }
export interface LabelPreview {
  source: "project" | "sample"; part: { uid: number; name: string; code: string; index: number }; map_index: number | null;
  fields: PreviewField[]; variables: PreviewVariable[];
}
export interface PreviewTarget { project_id?: string; op_id?: string; part_uid?: number }

const base = (key: string) => `/postprocessors/machines/${key}`;

export const useMachineSchema = (key: string | null) =>
  useQuery({ queryKey: ["pp-machine-schema", key], enabled: !!key, staleTime: 0,
    queryFn: () => get<MachineSchema>(`${base(key as string)}/schema`) });

/** Jonli ko'rinish uchun loyihalar: hamma papkalardan (qidiruv bo'lsa — qidiruv bo'yicha), yangilari birinchi, ko'pi bilan 60 ta. */
export const useProjectChoices = (q: string) =>
  useQuery({ queryKey: ["pp-label-projects", q.trim()], staleTime: 10_000,
    queryFn: () => get<ProjectRow[]>("/projects", q.trim() ? { q: q.trim() } : { all_folders: true })
      .then((rows) => [...rows].sort((a, b) => b.number - a.number).slice(0, 60)) });

function store(s: MachineSchema): MachineSchema {
  qc.setQueryData(["pp-machine-schema", s.key], s);
  return s;
}

/** Parametrlarni saqlash (to'liq almashtirish: yuborilmagan parametr — standart). Xato — `ApiError` (400, xabar tilga mos). */
export const saveParams = (key: string, params: Record<string, ParamValue>) =>
  put<MachineSchema>(`${base(key)}/params`, { params }).then(store);

export const saveLabelFields = (key: string, rows: LabelRow[]) =>
  put<MachineSchema>(`${base(key)}/label-fields`, { label_fields: rows }).then(store);

export const previewLabelFields = (key: string, rows: LabelRow[], target: PreviewTarget) =>
  post<LabelPreview>(`${base(key)}/label-fields/preview`, { ...target, fields: rows });

/** Kechiktirilgan (debounce) jonli ko'rinish: qoralama qatorlar tanlangan detal kontekstida serverda hisoblanadi. */
export function useLabelPreview(key: string, rows: LabelRow[], target: PreviewTarget, delay = 350) {
  const [data, setData] = useState<LabelPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const seq = useRef(0);
  const sig = JSON.stringify([rows, target]);
  useEffect(() => {
    const my = ++seq.current;
    setBusy(true);
    const timer = setTimeout(() => {
      const [r, tg] = JSON.parse(sig) as [LabelRow[], PreviewTarget];
      previewLabelFields(key, r, tg)
        .then((d) => { if (my === seq.current) { setData(d); setError(null); } })
        .catch((e: Error) => { if (my === seq.current) setError(e.message); })
        .finally(() => { if (my === seq.current) setBusy(false); });
    }, delay);
    return () => clearTimeout(timer);
  }, [key, sig, delay]);
  return { data, error, busy };
}
