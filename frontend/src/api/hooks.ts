// TanStack Query hooklari va loyiha o'zgarishlari uchun yordamchilar.
import { QueryClient, useQuery } from "@tanstack/react-query";
import { create } from "zustand";
import { get } from "./client";
import type {
  AppSettings, CatalogItem, EdgeUsage, Folder, HistoryInfo, Me, PostprocessorInfo, PpMachines, Profile, Project, ProjectRow,
  Remnant, XncStats,
} from "./types";
import { showError } from "../shared/dialogs";

export const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 10_000, refetchOnWindowFocus: false, retry: 1 } },
});

export const useBusy = create<{ busy: string | null; set: (b: string | null) => void }>((set) => ({
  busy: null, set: (b) => set({ busy: b }),
}));

function isProject(x: unknown): x is Project {
  return !!x && typeof x === "object" && "operations" in (x as object) && "products" in (x as object) && "number" in (x as object);
}

/** Loyiha keshini yangilash (API loyihani qaytarganda). */
export function applyProject(p: Project) {
  qc.setQueryData(["project", p.id], p);
  void qc.invalidateQueries({ queryKey: ["history", p.id] });
  void qc.invalidateQueries({ queryKey: ["projects"] });
}

/** API chaqiruvi: xato — xabarnoma; loyiha qaytsa — kesh yangilanadi. busy — uzoq amal matni. */
export async function call<T>(fn: () => Promise<T>, busy?: string): Promise<T | undefined> {
  if (busy) useBusy.getState().set(busy);
  try {
    const r = await fn();
    if (isProject(r)) applyProject(r);
    else if (r && typeof r === "object" && "project" in (r as object) && isProject((r as unknown as { project: unknown }).project)) {
      applyProject((r as unknown as { project: Project }).project);
    }
    return r;
  } catch (e) {
    showError(e);
    return undefined;
  } finally {
    if (busy) useBusy.getState().set(null);
  }
}

export const useMe = () => useQuery({ queryKey: ["me"], queryFn: () => get<Me>("/me"), staleTime: 600_000 });

export const useFolders = (parentId: string | null) =>
  useQuery({ queryKey: ["folders", parentId], queryFn: () => get<Folder[]>("/folders", { parent_id: parentId ?? undefined }) });

export const useAllFolders = (enabled = true) =>
  useQuery({ queryKey: ["folders", "all"], queryFn: () => get<Folder[]>("/folders/all"), enabled });

export const useFolderPath = (id: string | null) =>
  useQuery({ queryKey: ["folder-path", id], queryFn: () => (id ? get<Folder[]>(`/folders/${id}/path`) : Promise.resolve([])) });

export const useProjects = (folderId: string | null, q: string) =>
  useQuery({ queryKey: ["projects", folderId, q], queryFn: () => get<ProjectRow[]>("/projects", { folder_id: folderId ?? undefined, q }) });

export const useProject = (pid: string | null) =>
  useQuery({ queryKey: ["project", pid], queryFn: () => get<Project>(`/projects/${pid}`), enabled: !!pid, staleTime: 60_000 });

export const useHistory = (pid: string | null) =>
  useQuery({ queryKey: ["history", pid], queryFn: () => get<HistoryInfo>(`/projects/${pid}/history`), enabled: !!pid });

export const useEdgeUsage = (pid: string, oid: string, stamp: unknown) =>
  useQuery({ queryKey: ["edge-usage", pid, oid, stamp], queryFn: () => get<EdgeUsage>(`/projects/${pid}/operations/${oid}/edge-usage`) });

export const useXncStats = (pid: string, oid: string, stamp: unknown) =>
  useQuery({ queryKey: ["xnc-stats", pid, oid, stamp], queryFn: () => get<XncStats>(`/projects/${pid}/operations/${oid}/xnc-stats`) });

export const useRemnants = (material_code?: string, q = "", linear?: boolean) =>
  useQuery({ queryKey: ["remnants", material_code ?? "", q, linear ?? "all"],
    queryFn: () => get<Remnant[]>("/remnants", { material_code, q, linear }) });

export const useProfiles = <T,>(scope: string) =>
  useQuery({ queryKey: ["profiles", scope], queryFn: () => get<Profile<T>[]>(`/settings/${scope}`) });

export const useDefaults = <T,>(scope: string) =>
  useQuery({ queryKey: ["defaults", scope], queryFn: () => get<T>(`/settings/${scope}/default`) });

export const useAppSettings = () => useDefaults<AppSettings>("app");

export const usePostprocessors = () =>
  useQuery({ queryKey: ["postprocessors"], queryFn: () => get<PostprocessorInfo[]>("/postprocessors") });

export const usePpMachines = () =>
  useQuery({ queryKey: ["pp-machines"], queryFn: () => get<PpMachines>("/postprocessors/machines") });

export const useCatalog = (kind: string, q: string) =>
  useQuery({ queryKey: ["catalog", kind, q], queryFn: () => get<CatalogItem[]>("/catalog", { kind: kind || undefined, q }) });
