// CL «Раскрой» (hujjat D-CL5): holat qatori (№ S C Cp LT F …), 1D karta, miniatyuralar ↔ buyruqlar jadvali, kroy amallari. CsCut namunasida.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, CircleQuestionMark, GitCompareArrows, MessageSquare, PencilRuler, Play, PlusSquare, Settings2, Trash, Warehouse, Cpu, LayoutGrid,
} from "lucide-react";
import { PpPickDialog } from "../cs/PpPick";
import { call, qc, useAppSettings, usePostprocessors } from "../../api/hooks";
import { del, download, patch, post } from "../../api/client";
import type { CutMap, CuttingResult, Operation, Project, Quality } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText, showError } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, Field, IconBtn, Modal, Sel, Sep, cx, fmt } from "../../shared/ui";
import { RemnantCommitDialog, offerRemnants, useRemnantOfferOpen } from "../cs/RemnantCommit";
import { ClTabs } from "./ClPanel";
import { ClEditor } from "./ClEditor";
import { ClVariantsDialog } from "./ClVariants";
import { StripMap, mapTrims } from "./StripMap";

export async function runClCutting(project: Project, op: Operation, t: (k: string, o?: Record<string, unknown>) => string,
  opts: { quality?: Quality; only_remaining?: boolean } = {}) {
  const res = await call(() => post<CuttingResult>(`/projects/${project.id}/operations/${op.id}/optimize`, undefined, {
    quality: opts.quality, only_remaining: opts.only_remaining ? true : undefined,
  }), opts.only_remaining ? t("cut.busy_rest") : t("cut.busy"));
  if (!res) return null;
  useUI.getState().set({ mapIndex: 1 });
  await qc.invalidateQueries({ queryKey: ["project", project.id] });
  const msg = t("cl.cut.done", { n: res.total_sheets, m: fmt(res.material_len_m ?? 0, 2), fill: res.total_fill_percent, s: res.elapsed_s });
  useUI.getState().toast(res.unplaced.length ? `${msg}\n${t("cut.unplaced", { n: res.unplaced.length })}` : msg,
    res.unplaced.length ? "warn" : "ok");
  return res;
}

/** Holat qatori ko'rsatkichlari (CL): karta qiymati / jami. */
const CL_IND = ["num", "S", "C", "Cp", "LT", "F", "CT", "T", "M"];

function indicator(k: string, m: CutMap, res: CuttingResult, nMaps: number, op: Operation): string {
  switch (k) {
    case "num": return `${m.index}/${nMaps}`;
    case "S": return `${fmt(m.sheet_length)}/${fmt(m.sheet_width)}`;
    case "C": return `${m.copies}/${res.total_sheets}`;
    case "Cp": return `${m.parts_count}/${res.total_parts}`;
    case "LT": return `${fmt(m.cut_length_m)}/${fmt(res.total_cut_length_m)}`;
    case "F": return `${fmt(m.fill_percent)}%/${fmt(res.total_fill_percent)}%`;
    case "CT": return `${m.cuts_count}/${res.total_cuts}`;
    case "T": { const [a, b] = mapTrims(m, op); return `${fmt(a)}/${fmt(b)}`; }
    case "M": return `${fmt((m.sheet_length * m.copies) / 1000, 2)}/${fmt(res.material_len_m ?? 0, 2)}`;
    default: return "";
  }
}

export function ClCut({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const pps = usePostprocessors();
  const cl = op.cl!;
  const res = op.result;
  const maps = res?.maps ?? [];
  const n = maps.length;
  const idx = Math.min(Math.max(1, ui.mapIndex), Math.max(1, n));
  const m = maps[idx - 1];
  const [quality, setQuality] = useState<Quality>(cl.quality);
  const [dlg, setDlg] = useState<"" | "editor" | "commit" | "view" | "variants">("");
  useRemnantOfferOpen(op.id, () => setDlg("commit"));       // xabardagi «Записать на склад» tugmasi
  const [ppOpen, setPp] = useState(false);          // «Постпроцессоры» oynasi
  const [hiPart, setHiPart] = useState<string | null>(null);
  const [pinPart, setPinPart] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const mapWrap = useRef<HTMLDivElement>(null);
  useEffect(() => setQuality(cl.quality), [cl.quality]);
  useEffect(() => setZoom(1), [idx, op.id]);
  useEffect(() => {
    const el = mapWrap.current;
    if (!el) return;
    const h = (e: WheelEvent) => { e.preventDefault(); setZoom((z) => Math.min(8, Math.max(1, z * (e.deltaY < 0 ? 1.15 : 1 / 1.15)))); };
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, [!!m]);                                                          // eslint-disable-line react-hooks/exhaustive-deps

  const go = (i: number) => ui.set({ mapIndex: Math.min(Math.max(1, i), Math.max(1, n)) });
  const cut = async (only_remaining = false) => {
    if (!only_remaining && res && !(await askConfirm(t("cut.recut_q"), res.remnants_saved ? t("cut.recut_saved") : undefined))) return;
    const r = await runClCutting(project, op, t, { quality, only_remaining });
    offerRemnants(op, r, app.data?.remnant_confirm);   // oyna o'zi ochilmaydi — xabarda tugma
  };
  const act = {
    remove: async () => {
      if (!res || !(await askConfirm(t("cut.delete_q"),
        // oqibati: kartalar o'chadi (detal / listlar qoladi), omborga yozilgan qoldiqlar bekor qilinadi
        [t("cut.delete_text"), res.remnants_saved ? t("cut.recut_saved") : ""].filter(Boolean).join(" "), { danger: true }))) return;
      await call(() => del(`/projects/${project.id}/operations/${op.id}/result`));
    },
    comment: async () => {
      if (!m) return;
      const c = await askText(t("cut.comment"), m.comment, { multiline: true });
      if (c !== null) await call(() => patch(`/projects/${project.id}/operations/${op.id}/maps/${idx}`, { comment: c }));
    },
    pp: (key: string, profile_id?: number) => void download(`/projects/${project.id}/operations/${op.id}/postprocess`,
      profile_id ? { profile_id } : { key }).catch(showError),
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
      <Sel<Quality> value={quality} width={120} onChange={setQuality} testid="cl-cut-quality"
        options={(["fast", "normal", "max"] as const).map((q) => ({ value: q, label: t(`cs.quality.${q}`) }))} />
      <Btn icon={Play} kind="primary" small label={t("cut.run")} onClick={() => void cut()} testid="btn-cl-cut" disabled={!op.parts.length} />
      <IconBtn icon={GitCompareArrows} title={t("cut.variants")} onClick={() => setDlg("variants")} disabled={!op.parts.length}
        testid="btn-cl-variants" />
      <IconBtn icon={PencilRuler} title={t("cut.edit")} onClick={() => setDlg("editor")} disabled={!res} testid="btn-cl-edit" />
      <IconBtn icon={PlusSquare} title={t("cut.rest")} onClick={() => void cut(true)} disabled={!res || !res.unplaced.length}
        testid="btn-cl-rest" />
      <IconBtn icon={MessageSquare} title={t("cut.comment")} onClick={() => void act.comment()} disabled={!m} />
      <IconBtn icon={Trash} title={t("cut.delete")} onClick={() => void act.remove()} disabled={!res} color="#c0392b" />
      <IconBtn icon={Cpu} title={t("cut.pp")} onClick={() => setPp(true)} disabled={!res} testid="btn-cl-pp" />
      {ppOpen && <PpPickDialog items={(pps.data ?? []).filter((p) => p.builtin || p.profile_id)} onClose={() => setPp(false)}
        onPick={(p) => act.pp(p.key, p.profile_id)} />}
      <IconBtn icon={Warehouse} title={res?.remnants_saved ? t("cut.remnants_saved") : t("cut.remnants_commit")}
        active={res?.remnants_saved} onClick={() => setDlg("commit")} disabled={!res} testid="btn-cl-remnants" />
      <Sep />
      <IconBtn icon={Settings2} title={`${t("cut.view_settings")} (Ctrl+P)`} onClick={() => setDlg("view")} testid="btn-cl-view" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  if (!res || !n) {
    return (
      <div className="panel" {...scopeProps("cut")}>
        <ClTabs right={toolbar} />
        <div className="cut-empty">
          <button type="button" className="cut-link" onClick={() => void cut()} disabled={!op.parts.length} data-testid="btn-cl-cut-big">
            <LayoutGrid size={16} /> {t("cut.run")}</button>
          <div className="muted">{op.parts.length ? t("cl.cut.empty_hint") : t("cut.no_parts")}</div>
          {op.description && <div className="muted">{op.description}</div>}
        </div>
        {dlg === "variants" && <ClVariantsDialog project={project} op={op} onClose={() => setDlg("")} />}
      </div>
    );
  }

  const shown = CL_IND.filter((k) => ui.cutIndicators.includes(k));
  const mapParts = (() => {
    const cnt = new Map<string, { uid: number; length: number; c: number; name: string }>();
    for (const pl of m.placements) {
      const e = cnt.get(pl.part_id) ?? { uid: pl.part_uid, length: pl.length, c: 0, name: op.parts.find((p) => p.id === pl.part_id)?.name ?? "" };
      e.c += 1;
      cnt.set(pl.part_id, e);
    }
    return [...cnt.entries()];
  })();
  return (
    <div className="panel" {...scopeProps("cut")}>
      <ClTabs right={toolbar} />
      <div className="statusline" data-testid="cl-cut-status">
        {shown.map((k) => (
          <span key={k} title={t(`cl.ind.${k}`)}>{k === "num" ? "№" : k}: <b data-testid={k === "F" ? "cl-cut-fill" : undefined}>
            {indicator(k, m, res, n, op)}</b>{k === "S" && m.is_remnant ? ` (${t("cl.cut.remnant_strip")})` : ""}</span>))}
        {(res.sheets_per_pack ?? 1) > 1 && (
          <span title={t("cut.packs_hint", { n: res.sheets_per_pack })} data-testid="cl-cut-packs">
            {t("cut.packs")}: <b>{m.packs}/{res.total_packs}</b></span>)}
        <Check checked={ui.mapEdges} label={t("cut.edges_toggle")} title={t("print.f.map_edges")}
          onChange={(v) => ui.set({ mapEdges: v })} testid="cl-cut-edges-toggle" />
        <span className="nav">
          <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => go(1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => go(idx - 1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => go(idx + 1)} disabled={idx >= n} testid="cl-map-next" />
          <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => go(n)} disabled={idx >= n} />
        </span>
      </div>
      {(unplaced.length > 0 || m.comment || res.manual || m.done_count > 0 || (res.warnings ?? []).length > 0) && (
        <div className="cut-notes">
          {(res.warnings ?? []).map((w, i) => <span key={i} className="warn" data-testid="cl-cut-warning">{w}</span>)}
          {unplaced.length > 0 && <span className="warn" data-testid="cl-cut-unplaced">{t("cut.unplaced", { n: res.unplaced.length })}: {unplaced.map((u) =>
            `${u.part?.uid ?? "?"}×${u.c}`).join(", ")}</span>}
          {m.comment && <span className="comment"><MessageSquare size={12} /> {m.comment}</span>}
          {res.manual && <span className="muted">{t("cut.manual")}</span>}
          {m.done_count > 0 && <span className="ok">{t("cut.done_count", { d: m.done_count, c: m.copies })}</span>}
        </div>
      )}
      <div className="cut-body">
        <div className="cut-map cl-map-col" data-testid="cl-map-wrap" ref={mapWrap}>
          <div className="cut-zoom cl-zoom" style={{ width: `${zoom * 100}%` }}>
            <StripMap map={m} project={project} op={op} label={ui.mapLabel} showEdges={ui.mapEdges} highlightPartId={hiPart ?? pinPart}
              testid="cl-map" onPart={(id) => setPinPart((cur) => (id && cur !== id ? id : null))} />
          </div>
          <table className="simple cl-map-parts" data-testid="cl-map-parts">
            <thead><tr><th>№</th><th>{t("cl.col.length")}</th><th>{t("pc.qty")}</th><th>{t("pc.name")}</th></tr></thead>
            <tbody>
              {mapParts.map(([pid, e]) => (
                <tr key={pid} className={cx(pinPart === pid && "tr-sel")} onClick={() => setPinPart((cur) => (cur === pid ? null : pid))}>
                  <td>{e.uid}</td><td className="num">{fmt(e.length)}</td><td className="num">{e.c}</td><td>{e.name}</td>
                </tr>))}
            </tbody>
          </table>
        </div>
        <div className="cut-side">
          <button type="button" className="linkbtn cut-side-head" onClick={() => ui.set({ showCommands: !ui.showCommands })}
            data-testid="cl-toggle-commands">
            {ui.showCommands ? t("cut.maps_table") : t("cut.commands")}
          </button>
          {ui.showCommands ? (
            <div className="scroll">
              <table className="simple cmds" data-testid="cl-commands-table">
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
                  <StripMap map={mm} project={project} op={op} thumb className="thumbsvg cl-thumb" />
                  <span>№:{mm.index} S:{fmt(mm.sheet_length)}/{fmt(mm.sheet_width)} C:{mm.copies}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {dlg === "variants" && <ClVariantsDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "editor" && <ClEditor project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "commit" && <RemnantCommitDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "view" && <CutViewSettings onClose={() => setDlg("")} />}
    </div>
  );
}

/** «Настройки» (Ctrl+P): detal yozuvi, kromka belgilari, buyruqlar jadvali, holat qatori ko'rsatkichlari. */
function CutViewSettings({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Modal title={t("cut.view_settings")} onClose={onClose} width={420} testid="cl-view-settings"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} />}>
      <div className="form1">
        <Field label={t("print.f.map_part_label")}>
          <Sel value={ui.mapLabel} width={200} onChange={(v) => ui.set({ mapLabel: v })} testid="cl-view-label"
            options={(["number", "name", "number_name"] as const).map((v) => ({ value: v, label: t(`print.label.${v}`) }))} />
        </Field>
        <Field label=" "><Check checked={ui.mapEdges} label={t("print.f.map_edges")} onChange={(v) => ui.set({ mapEdges: v })} /></Field>
        <Field label=" "><Check checked={ui.showCommands} label={t("cut.show_commands")} onChange={(v) => ui.set({ showCommands: v })} /></Field>
        <div className="form-h">{t("cut.indicators")}</div>
        <table className="simple" data-testid="cl-indicators">
          <tbody>{CL_IND.map((k) => (
            <tr key={k}><td><Check checked={ui.cutIndicators.includes(k)} onChange={(v) => ui.set({
              cutIndicators: v ? [...ui.cutIndicators.filter((x) => x !== k), k] : ui.cutIndicators.filter((x) => x !== k) })} /></td>
              <td><b>{k === "num" ? "№" : k}</b></td><td>{t(`cl.ind.${k}`)}</td></tr>))}</tbody>
        </table>
        <Btn small label={t("cut.ind_reset")} onClick={() => ui.set({ cutIndicators: ["num", "S", "C", "Cp", "LT", "F"] })} />
      </div>
    </Modal>
  );
}
