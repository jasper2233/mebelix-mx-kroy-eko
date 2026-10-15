// CS «Раскрой» (UI_SPEC §5.4): holat qatori, karta, miniatyuralar / buyruqlar jadvali, kroy amallari.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, CircleQuestionMark, GitCompareArrows, MessageSquare, PencilRuler, Play, PlusSquare, Settings2, Tags, Trash, Warehouse, Cpu, LayoutGrid,
} from "lucide-react";
import { PpPickDialog } from "./PpPick";
import { call, qc, useAppSettings, usePostprocessors } from "../../api/hooks";
import { del, download, patch, post } from "../../api/client";
import type { CuttingResult, Operation, Project, Quality } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, Field, IconBtn, Modal, Sel, Sep, cx, fmt } from "../../shared/ui";
import { CsTabs } from "./CsPanel";
import { MapView } from "./MapView";
import { CutEditor } from "./CutEditor";
import { INDICATORS, indicator } from "./cutIndicators";
import { VariantsDialog } from "./VariantsDialog";
import { RemnantCommitDialog } from "./RemnantCommit";
import { PartProperties } from "./PartDialogs";

export async function runCutting(project: Project, op: Operation, t: (k: string, o?: Record<string, unknown>) => string,
  opts: { quality?: Quality; only_remaining?: boolean } = {}) {
  const res = await call(() => post<CuttingResult>(`/projects/${project.id}/operations/${op.id}/optimize`, undefined, {
    quality: opts.quality, only_remaining: opts.only_remaining ? true : undefined,
  }), opts.only_remaining ? t("cut.busy_rest") : t("cut.busy"));
  if (!res) return null;
  useUI.getState().set({ mapIndex: 1 });
  await qc.invalidateQueries({ queryKey: ["project", project.id] });
  const msg = t("cut.done", { sheets: res.total_sheets, fill: res.total_fill_percent, s: res.elapsed_s });
  useUI.getState().toast(res.unplaced.length ? `${msg} · ${t("cut.unplaced", { n: res.unplaced.length })}` : msg,
    res.unplaced.length ? "error" : "ok");
  return res;
}

export function CsCut({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const pps = usePostprocessors();
  const res = op.result;
  const maps = res?.maps ?? [];
  const n = maps.length;
  const idx = Math.min(Math.max(1, ui.mapIndex), Math.max(1, n));
  const m = maps[idx - 1];
  const [quality, setQuality] = useState<Quality>(op.cs_cut?.quality ?? "normal");
  const label = ui.mapLabel;
  const [dlg, setDlg] = useState<"" | "editor" | "variants" | "commit" | "view">("");
  const [ppOpen, setPp] = useState(false);          // «Постпроцессоры» oynasi
  const [hiPart, setHiPart] = useState<string | null>(null);
  const [pinPart, setPinPart] = useState<string | null>(null);     // bosilgan detal — barcha nusxalari ajratiladi
  const [propsPart, setPropsPart] = useState<string | null>(null);  // ikki marta bosish — detal xossalari
  const [zoom, setZoom] = useState(1);                              // sichqoncha g'ildiragi — masshtab
  const mapWrap = useRef<HTMLDivElement>(null);
  useEffect(() => setQuality(op.cs_cut?.quality ?? "normal"), [op.cs_cut?.quality]);
  useEffect(() => setZoom(1), [idx, op.id]);                         // karta/operatsiya almashsa masshtab asliga qaytadi
  // g'ildirak: passiv bo'lmagan tinglovchi (preventDefault xatosiz; sahifa siljimaydi)
  useEffect(() => {
    const el = mapWrap.current;
    if (!el) return;
    const h = (e: WheelEvent) => { e.preventDefault(); setZoom((z) => Math.min(6, Math.max(1, z * (e.deltaY < 0 ? 1.15 : 1 / 1.15)))); };
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, [!!m]);                                                          // eslint-disable-line react-hooks/exhaustive-deps

  const go = (i: number) => ui.set({ mapIndex: Math.min(Math.max(1, i), Math.max(1, n)) });
  const cut = async (only_remaining = false) => {
    if (!only_remaining && res && !(await askConfirm(t("cut.recut_q"), res.remnants_saved ? t("cut.recut_saved") : undefined))) return;
    const r = await runCutting(project, op, t, { quality, only_remaining });
    if (r && app.data?.remnant_confirm === true && r.maps.some((mm) => mm.offcuts.some((o) => o.kind === "remnant" && o.business))) {
      setDlg("commit");
    }
  };
  const act = {
    remove: async () => {
      if (!res || !(await askConfirm(t("cut.delete_q"), res.remnants_saved ? t("cut.recut_saved") : undefined, { danger: true }))) return;
      await call(() => del(`/projects/${project.id}/operations/${op.id}/result`));
    },
    comment: async () => {
      if (!m) return;
      const c = await askText(t("cut.comment"), m.comment, { multiline: true });
      if (c !== null) await call(() => patch(`/projects/${project.id}/operations/${op.id}/maps/${idx}`, { comment: c }));
    },
    pp: (key: string, profile_id?: number) => void download(`/projects/${project.id}/operations/${op.id}/postprocess`,
      profile_id ? { profile_id } : { key }).then(async (h) => {
      const n = h.get("X-PP-Refit");              // stanok formati kesim darajasini cheklaydi — kroy qayta bajarildi
      if (n) {
        await qc.invalidateQueries({ queryKey: ["project", project.id] });
        ui.toast(t("pp.refit", { n }), "info");
      }
    }).catch((e) => ui.toast(String(e.message ?? e), "error")),
  };
  useHotkeys("cut", {
    home: () => go(1), end: () => go(n), arrowup: () => go(idx - 1), arrowdown: () => go(idx + 1),
    arrowleft: () => go(idx - 1), arrowright: () => go(idx + 1),
    "ctrl+p": () => setDlg("view"), f2: () => void act.comment(),
  });

  const unplaced = useMemo(() => {
    if (!res?.unplaced.length) return [];
    const cnt = new Map<string, number>();
    res.unplaced.forEach((id) => cnt.set(id, (cnt.get(id) ?? 0) + 1));
    return [...cnt.entries()].map(([id, c]) => ({ part: op.parts.find((p) => p.id === id), c }));
  }, [res, op.parts]);

  const toolbar = (
    <>
      <Sel<Quality> value={quality} width={120} onChange={setQuality} testid="cut-quality"
        options={(["fast", "normal", "max"] as const).map((q) => ({ value: q, label: t(`cs.quality.${q}`) }))} />
      <Btn icon={Play} kind="primary" small label={t("cut.run")} onClick={() => void cut()} testid="btn-cut" disabled={!op.parts.length} />
      <IconBtn icon={GitCompareArrows} title={t("cut.variants")} onClick={() => setDlg("variants")} disabled={!op.parts.length} testid="btn-variants" />
      <IconBtn icon={PencilRuler} title={t("cut.edit")} onClick={() => setDlg("editor")} disabled={!res} testid="btn-edit-cut" />
      <IconBtn icon={PlusSquare} title={t("cut.rest")} onClick={() => void cut(true)} disabled={!res || !res.unplaced.length} />
      <IconBtn icon={MessageSquare} title={t("cut.comment")} onClick={() => void act.comment()} disabled={!m} />
      <IconBtn icon={Trash} title={t("cut.delete")} onClick={() => void act.remove()} disabled={!res} color="#c0392b" />
      <IconBtn icon={Cpu} title={t("cut.pp")} onClick={() => setPp(true)} disabled={!res} testid="btn-pp" />
      {ppOpen && <PpPickDialog items={(pps.data ?? [])} onClose={() => setPp(false)}
        onPick={(p) => act.pp(p.key, p.profile_id)} />}
      <IconBtn icon={Warehouse} title={res?.remnants_saved ? t("cut.remnants_saved") : t("cut.remnants_commit")}
        active={res?.remnants_saved} onClick={() => setDlg("commit")} disabled={!res} testid="btn-remnants" />
      <IconBtn icon={Tags} title={t("cut.labels")} onClick={() => ui.set({ section: "print" })} disabled={!res} />
      <Sep />
      <IconBtn icon={Settings2} title={`${t("cut.view_settings")} (Ctrl+P)`} onClick={() => setDlg("view")} testid="btn-cut-view" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  if (!res || !n) {
    return (
      <div className="panel" {...scopeProps("cut")}>
        <CsTabs right={toolbar} />
        <div className="cut-empty">
          <button type="button" className="cut-link" onClick={() => void cut()} disabled={!op.parts.length} data-testid="btn-cut-big">
            <LayoutGrid size={16} /> {t("cut.run")}</button>
          <div className="muted">{op.parts.length ? t("cut.empty_hint") : t("cut.no_parts")}</div>
          {op.description && <div className="muted">{op.description}</div>}
          {dlg === "variants" && <VariantsDialog project={project} op={op} onClose={() => setDlg("")} />}
        </div>
      </div>
    );
  }

  return (
    <div className="panel" {...scopeProps("cut")}>
      <CsTabs right={toolbar} />
      <div className="statusline" data-testid="cut-status">
        {INDICATORS.filter((k) => ui.cutIndicators.includes(k)).map((k) => (
          <span key={k} title={t(`cut.ind.${k}`)}>{k === "num" ? "№" : k}: <b data-testid={k === "F" ? "cut-fill" : undefined}>
            {indicator(k, m, res, n)}</b>{k === "S" && m.is_remnant ? ` (${t("cut.remnant_sheet")})` : ""}</span>))}
        {(res.sheets_per_pack ?? 1) > 1 && (
          <span title={t("cut.packs_hint", { n: res.sheets_per_pack })} data-testid="cut-packs">
            {t("cut.packs")}: <b>{m.packs}/{res.total_packs}</b></span>)}
        <Check checked={ui.mapEdges} label={t("cut.edges_toggle")} title={t("print.f.map_edges")}
          onChange={(v) => ui.set({ mapEdges: v })} testid="cut-edges-toggle" />
        <span className="nav">
          <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => go(1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => go(idx - 1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => go(idx + 1)} disabled={idx >= n} testid="map-next" />
          <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => go(n)} disabled={idx >= n} />
        </span>
      </div>
      {(unplaced.length > 0 || m.comment || res.manual || m.done_count > 0 || (res.warnings ?? []).length > 0) && (
        <div className="cut-notes">
          {(res.warnings ?? []).map((w, i) => <span key={i} className="warn" data-testid="cut-warning">{w}</span>)}
          {unplaced.length > 0 && <span className="warn">{t("cut.unplaced", { n: res.unplaced.length })}: {unplaced.map((u) =>
            `${u.part?.uid ?? "?"}×${u.c}`).join(", ")}</span>}
          {m.comment && <span className="comment"><MessageSquare size={12} /> {m.comment}</span>}
          {res.manual && <span className="muted">{t("cut.manual")}</span>}
          {m.done_count > 0 && <span className="ok">{t("cut.done_count", { d: m.done_count, c: m.copies })}</span>}
        </div>
      )}
      <div className="cut-body">
        <div className="cut-map" data-testid="cut-map-wrap" ref={mapWrap}>
          <div className="cut-zoom" style={{ width: `${zoom * 100}%`, height: `${zoom * 100}%` }}>
            <MapView map={m} project={project} op={op} label={label} showEdges={ui.mapEdges} highlightPartId={hiPart ?? pinPart}
              testid="cut-map" onPart={(id, dbl) => {
                if (dbl && id) { setPropsPart(id); return; }
                setPinPart((cur) => (id && cur !== id ? id : null));
              }} />
          </div>
        </div>
        <div className="cut-side">
          <button type="button" className="linkbtn cut-side-head" onClick={() => ui.set({ showCommands: !ui.showCommands })}
            data-testid="toggle-commands">
            {ui.showCommands ? t("cut.maps") : t("cut.commands")}
          </button>
          {ui.showCommands ? (
            <div className="scroll">
              <table className="simple cmds" data-testid="commands-table">
                <thead><tr><th>№</th><th>{t("cut.cmd.code")}</th><th>{t("cut.cmd.size")}</th><th>{t("cut.cmd.count")}</th><th>{t("cut.cmd.ref")}</th></tr></thead>
                <tbody>
                  {m.commands.map((c, i) => (
                    <tr key={i} className={`cmd-${c.code}`}
                      onMouseEnter={() => { if (c.code === "P") setHiPart(op.parts.find((p) => String(p.uid) === c.ref)?.id ?? null); }}
                      onMouseLeave={() => setHiPart(null)}>
                      <td>{i + 1}</td><td>{c.code}{c.level}</td><td className="num">{fmt(c.size)}</td>
                      <td className="num">{c.count > 1 ? c.count : ""}</td><td>{c.ref}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="scroll thumbs">
              {maps.map((mm) => (
                <button key={mm.index} type="button" className={cx("thumb", mm.index === idx && "thumb-active")} onClick={() => go(mm.index)}>
                  <MapView map={mm} project={project} op={op} thumb className="thumbsvg" />
                  <span>№{mm.index} S:{fmt(mm.sheet_length)}/{fmt(mm.sheet_width)} C:{mm.copies}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {dlg === "editor" && <CutEditor project={project} op={op} onClose={(saved) => {
        // saqlangan qo'lda natijada деловой qoldiq bo'lsa — omborga yozishni taklif qilamiz (kroydan keyingidek)
        const r = saved?.operations.find((o) => o.id === op.id)?.result;
        const offer = !!r && app.data?.remnant_confirm === true && !r.remnants_saved
          && r.maps.some((mm) => mm.offcuts.some((o) => o.kind === "remnant" && o.business));
        setDlg(offer ? "commit" : "");
      }} />}
      {dlg === "variants" && <VariantsDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "commit" && <RemnantCommitDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "view" && <CutViewSettings onClose={() => setDlg("")} />}
      {propsPart && <PartPropsById project={project} op={op} partId={propsPart} onClose={() => setPropsPart(null)} />}
    </div>
  );
}

function PartPropsById({ project, op, partId, onClose }: { project: Project; op: Operation; partId: string;
  onClose: () => void }) {
  const part = op.parts.find((p) => p.id === partId);
  if (!part) return null;
  return <PartProperties project={project} op={op} part={part} onClose={onClose} />;
}

/** «Настройки» (Ctrl+P) — karta ko'rinishi: detal yozuvi, kromka belgilari, o'ng panel. */
function CutViewSettings({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Modal title={t("cut.view_settings")} onClose={onClose} width={420} testid="cut-view-settings"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} />}>
      <div className="form1">
        <Field label={t("print.f.map_part_label")}>
          <Sel value={ui.mapLabel} width={200} onChange={(v) => ui.set({ mapLabel: v })} testid="cut-view-label"
            options={(["number", "name", "number_name"] as const).map((v) => ({ value: v, label: t(`print.label.${v}`) }))} />
        </Field>
        <Field label=" "><Check checked={ui.mapEdges} label={t("print.f.map_edges")} onChange={(v) => ui.set({ mapEdges: v })} /></Field>
        <Field label=" "><Check checked={ui.showCommands} label={t("cut.show_commands")} onChange={(v) => ui.set({ showCommands: v })} /></Field>
        <div className="form-h">{t("cut.indicators")}</div>
        <table className="simple" data-testid="cut-indicators">
          <tbody>{INDICATORS.map((k) => (
            <tr key={k}><td><Check checked={ui.cutIndicators.includes(k)} onChange={(v) => ui.set({
              cutIndicators: v ? INDICATORS.filter((x) => x === k || ui.cutIndicators.includes(x)) : ui.cutIndicators.filter((x) => x !== k) })} /></td>
              <td><b>{k === "num" ? "№" : k}</b></td><td>{t(`cut.ind.${k}`)}</td></tr>))}</tbody>
        </table>
        <Btn small label={t("cut.ind_reset")} onClick={() => ui.set({ cutIndicators: ["num", "S", "C", "Cp", "LT", "F"] })} />
      </div>
    </Modal>
  );
}

