// «Импорт из других программ» (W18): format katalogi, parametrlar sxemasi, profillar, import. Server: `api_import_w18.py`.
import { useQuery } from "@tanstack/react-query";
import { api, del, get, post, put } from "../../api/client";
import { qc } from "../../api/hooks";
import type { Project } from "../../api/types";
import type { ParamValue, SchemaGroup, SchemaParam } from "../settings/machines/machinesApi";

export type ImportStatus = "ready" | "no_module";
export interface ImportFormatRow {
  key: string; name: { ru: string; uz: string }; exts: string[]; icon: string; status: ImportStatus; reason: string; n_params: number;
}
/** Parametr + «Справка» matni (ParamGrid `note` ni o'zi ko'rsatadi, `help` — dialogdagi «Справка» paneli uchun). */
export type ImportParam = SchemaParam & { help?: { ru: string; uz: string } };
export interface ImportSchema {
  key: string; name: { ru: string; uz: string }; exts: string[]; icon: string; status: ImportStatus; reason: string;
  groups: (Omit<SchemaGroup, "params"> & { params: ImportParam[] })[];
  values: Record<string, ParamValue>; defaults: Record<string, ParamValue>; modified: string[]; help: { ru: string; uz: string };
}
export interface ImportProfileRow { id: number; name: string; format: string; params: Record<string, ParamValue>; is_default: boolean }
export interface ProfilesReport {
  created: number; replaced: number; renamed: number; skipped: number; total: number;
  invalid: { name: string; format: string; error: string }[];
}
export interface ImportRunResult { project: Project; warnings: string[]; format: string; options: Record<string, ParamValue> }

export const useImportCatalog = () =>
  useQuery({ queryKey: ["import-catalog"], staleTime: 0, queryFn: () => get<ImportFormatRow[]>("/import/catalog") });

export const useImportSchema = (key: string | null) =>
  useQuery({ queryKey: ["import-schema", key], enabled: !!key, staleTime: 0,
    queryFn: () => get<ImportSchema>(`/import/formats/${key as string}/schema`) });

export const useImportProfiles = (format: string | null) =>
  useQuery({ queryKey: ["import-profiles", format], enabled: !!format, staleTime: 0,
    queryFn: () => get<ImportProfileRow[]>("/import/profiles", { format: format as string }) });

export const refreshImportProfiles = () => qc.invalidateQueries({ queryKey: ["import-profiles"] });

/** Standartdan farq qiladigan qiymatlar (profilda saqlanadi, importga yuboriladi). */
export function sparse(values: Record<string, ParamValue>, defaults: Record<string, ParamValue>): Record<string, ParamValue> {
  return Object.fromEntries(Object.entries(values).filter(([k, v]) => k in defaults && v !== defaults[k]));
}

export const createProfile = (name: string, format: string, params: Record<string, ParamValue>) =>
  post<{ id: number }>("/settings/import_profile", { name, data: { format, params } });
export const updateProfile = (id: number, format: string, params: Record<string, ParamValue>, name?: string) =>
  put<{ id: number }>(`/settings/import_profile/${id}`, { ...(name !== undefined ? { name } : {}), data: { format, params } });
export const renameProfile = (id: number, name: string) => put(`/settings/import_profile/${id}`, { name });
export const deleteProfile = (id: number) => del(`/settings/import_profile/${id}`);

export function importProfilesFile(file: File, onConflict = "replace") {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("on_conflict", onConflict);
  return api<ProfilesReport>("/import/profiles/import", { form: fd });
}

/** Faylni tanlangan format importeri bilan yangi loyiha sifatida yuklash. `params` — standartdan farqli qiymatlar. */
export function runImport(file: File, format: string, params: Record<string, ParamValue>, folderId?: string | null) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("format", format);
  fd.append("params", JSON.stringify(params));
  if (folderId) fd.append("folder_id", folderId);
  return api<ImportRunResult>("/import/run", { form: fd });
}
