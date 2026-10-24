// «Проект → Импортировать»: tanlangan loyiha fayllari ochiq loyihaga qo'shiladi (`POST /projects/{pid}/import-merge`).
import { api } from "../../api/client";
import { call, qc } from "../../api/hooks";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";

interface MergeFile { file: string; ok: boolean; error?: string; warnings?: string[]; operations?: number; parts?: number }

export async function importIntoProject(pid: string, files: File[], t: (k: string, o?: Record<string, unknown>) => string) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const r = await call(() => api<{ project: Project; files: MergeFile[] }>(`/projects/${pid}/import-merge`, { form: fd }),
    t("projects.importing"));
  if (!r) return;
  qc.setQueryData(["project", pid], r.project);
  void qc.invalidateQueries({ queryKey: ["project", pid] });
  const ok = r.files.filter((f) => f.ok);
  const details = [
    ...ok.map((f) => t("import.merge_line", { file: f.file, ops: f.operations ?? 0, parts: f.parts ?? 0 })),
    ...r.files.filter((f) => !f.ok).map((f) => `${f.file}: ${f.error ?? ""}`),
    ...ok.flatMap((f) => (f.warnings ?? []).map((w) => `${f.file}: ${w}`)),
  ];
  useUI.getState().toast(t("import.merged", { n: ok.length, total: r.files.length }),
    ok.length === r.files.length ? "ok" : "error", details);
}
