// «Очистить проект» (W14; GibLab yordamida ma'nosi yo'q — TAXMINIY, xavfsiz talqin): kroy natijalari va ulardan
// hisoblangan sanoqlar tozalanadi, detallar va operatsiyalar saqlanadi. Tasdiq oynasi bilan; Ctrl+Z qaytaradi.
import { call } from "../../api/hooks";
import { post } from "../../api/client";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";

export function clearStats(p: Project) {
  const withResult = p.operations.filter((o) => o.result);
  return {
    ops: withResult.length,
    maps: withResult.reduce((s, o) => s + (o.result?.maps.length ?? 0), 0),
    saved: withResult.filter((o) => o.result?.remnants_saved).length,
  };
}

type T = (k: string, o?: Record<string, unknown>) => string;

export async function clearProjectWithConfirm(project: Project, t: T): Promise<boolean> {
  const ui = useUI.getState();
  const s = clearStats(project);
  if (!s.ops) { ui.toast(t("clear.nothing"), "info"); return false; }
  const lines = [t("clear.text", { ops: s.ops, maps: s.maps })];
  if (s.saved) lines.push(t("clear.text_wh", { n: s.saved }));
  if (project.status >= 2) lines.push(t("clear.text_order", { status: t(`status.${project.status}`) }));
  const ok = await askConfirm(t("clear.q", { name: project.name }),
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>{lines.map((l, i) => <div key={i}>{l}</div>)}</div>,
    { danger: true, ok: t("clear.ok") });
  if (!ok) return false;
  const r = await call(() => post<Project>(`/projects/${project.id}/actions/clear`));
  if (r) ui.toast(t("clear.done", { ops: s.ops, maps: s.maps }), "ok");
  return !!r;
}
