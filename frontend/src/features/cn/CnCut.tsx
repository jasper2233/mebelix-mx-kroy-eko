// (CN) «Раскрой»: nesting FON VAZIFASI (progress, «Остановить»), holat qatori (№ S C Cp LT F CT …), konturli karta (NestMap), miniatyuralar ↔ karta detallari,
// qoldiqlarni omborga yozish, postprotsessor, karta izohi (F2), Home/End/↑↓ navigatsiya, g'ildirak masshtabi. CsCut / ClCut namunasida.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, CircleQuestionMark, MessageSquare, PencilRuler, Play, Settings2, Square, Tag, Trash, Warehouse, Cpu, LayoutGrid,
} from "lucide-react";
import { PpPickDialog } from "../cs/PpPick";
import { call, useAppSettings, usePostprocessors } from "../../api/hooks";
import { del, download, patch } from "../../api/client";
import type { CutMap, Operation, Project, Quality } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText, showError } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, Field, IconBtn, Modal, Sel, Sep, cx, fmt } from "../../shared/ui";
import { RemnantCommitDialog } from "../cs/RemnantCommit";
import { PartProperties } from "../cs/PartDialogs";
import { indicator } from "../cs/cutIndicators";
import { CnTabs } from "./CnPanel";
import { CnEditor } from "./CnEditor";
import { CN_IND, cancelCnJob, startCnJob, useCnJobs, useCnPrefs, useRunningCnJob } from "./cnHooks";
import { MapViewport, NestMap } from "./NestMap";
import { bboxOf, placementRing } from "./cnGeom";

/** Postprotsessor: nesting uchun faqat shu to'rt o'rnatilgan format (backend `cn_post`). */
const CN_PP = ["json", "csv", "dxf", "commands"];

/** Jon bo'lgan vazifa (progress, o'tgan vaqt, «Остановить»). */
export function CnProgress({ project, op, compact }: { project: Project; op: Operation; compact?: boolean }) {
  const { t } = useTranslation();
  const job = useRunningCnJob(op.id);
  if (!job) return null;
  const pct = Math.round(job.progress * 100);
  return (
    <div className={cx("cn-progress", compact && "cn-progress-compact")} data-testid="cn-progress">
      <div className="cn-pbar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="cn-pbar-fill" style={{ width: `${pct}%` }} data-testid="cn-progress-fill" />
      </div>
      <span className="cn-progress-text" data-testid="cn-progress-text">
        {pct}% · {t("cn.cut.elapsed", { s: fmt(job.elapsed_s, 1) })}{job.message ? ` · ${job.message}` : ""}</span>
      <Btn small kind="danger" icon={Square} label={t("cn.cut.stop")} onClick={() => void cancelCnJob(project.id, op.id)} testid="btn-cn-stop" />
    </div>
  );
}

export function CnCut({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const pps = usePostprocessors();
  const prefs = useCnPrefs();
  const cn = op.cn!;
  const res = op.result;
  const maps = res?.maps ?? [];
  const n = maps.length;
  const idx = Math.min(Math.max(1, ui.mapIndex), Math.max(1, n));
  const m = maps[idx - 1];
  const running = !!useRunningCnJob(op.id);
  const freshId = useCnJobs((s) => s.fresh[op.id]);
  const [quality, setQuality] = useState<Quality>(cn.quality);
  const [dlg, setDlg] = useState<"" | "editor" | "commit" | "view">("");
  const [ppOpen, setPp] = useState(false);          // «Постпроцессоры» oynasi
  const [pinPart, setPinPart] = useState<string | null>(null);        // bosilgan detal — barcha nusxalari ajratiladi
  const [propsPart, setPropsPart] = useState<string | null>(null);
  const [side, setSide] = useState<"maps" | "parts">("maps");
  useEffect(() => setQuality(cn.quality), [cn.quality]);
  useEffect(() => setPinPart(null), [idx, op.id]);

  // vazifa tugagan — деловой qoldiq bo'lsa omborga yozishni taklif qilamiz (CS dagi kabi)
  useEffect(() => {
    if (!freshId || !res) return;
    useCnJobs.setState((s) => ({ fresh: { ...s.fresh, [op.id]: undefined } }));
    if (app.data?.remnant_confirm === true && res.maps.some((mm) => mm.offcuts.some((o) => o.kind === "remnant" && o.business))) setDlg("commit");
  }, [freshId, res]); // eslint-disable-line react-hooks/exhaustive-deps

  const go = (i: number) => ui.set({ mapIndex: Math.min(Math.max(1, i), Math.max(1, n)) });
  const run = async () => {
    if (running) return;
    if (res && !(await askConfirm(t("cut.recut_q"), res.remnants_saved ? t("cut.recut_saved") : undefined))) return;
    await startCnJob(project.id, op.id, quality);
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
    pp: (key: string) => void download(`/projects/${project.id}/operations/${op.id}/postprocess`, { key })
      .catch(showError),
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
      <Sel<Quality> value={quality} width={120} onChange={setQuality} testid="cn-cut-quality" disabled={running}
        options={(["fast", "normal", "max"] as const).map((q) => ({ value: q, label: t(`cs.quality.${q}`) }))} />
      <Btn icon={Play} kind="primary" small label={t("cut.run")} onClick={() => void run()} testid="btn-cn-cut" disabled={!op.parts.length || running} />
      <IconBtn icon={PencilRuler} title={t("cut.edit")} onClick={() => setDlg("editor")} disabled={!res || !n || running} testid="btn-cn-edit" />
      <IconBtn icon={MessageSquare} title={`${t("cut.comment")} (F2)`} onClick={() => void act.comment()} disabled={!m} />
      <IconBtn icon={Trash} title={t("cut.delete")} onClick={() => void act.remove()} disabled={!res || running} color="#c0392b" testid="btn-cn-delete" />
      <IconBtn icon={Cpu} title={t("cut.pp")} onClick={() => setPp(true)} disabled={!res} testid="btn-cn-pp" />
      {ppOpen && <PpPickDialog items={(pps.data ?? []).filter((p) => p.builtin && CN_PP.includes(p.key))} onClose={() => setPp(false)}
        onPick={(p) => act.pp(p.key)} />}
      <IconBtn icon={Warehouse} title={res?.remnants_saved ? t("cut.remnants_saved") : t("cut.remnants_commit")}
        active={res?.remnants_saved} onClick={() => setDlg("commit")} disabled={!res} testid="btn-cn-remnants" />
      <Sep />
      <IconBtn icon={Tag} title={t("cn.cut.label_spots")} active={prefs.labels} onClick={() => prefs.setLabels(!prefs.labels)} testid="btn-cn-labels" />
      <IconBtn icon={Settings2} title={`${t("cut.view_settings")} (Ctrl+P)`} onClick={() => setDlg("view")} testid="btn-cn-view" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  if (!res || !n) {
    return (
      <div className="panel" {...scopeProps("cut")}>
        <CnTabs right={toolbar} />
        <CnProgress project={project} op={op} />
        <div className="cut-empty">
          <button type="button" className="cut-link" onClick={() => void run()} disabled={!op.parts.length || running} data-testid="btn-cn-cut-big">
            <LayoutGrid size={16} /> {t("cut.run")}</button>
          <div className="muted">{op.parts.length ? t("cn.cut.empty_hint") : t("cut.no_parts")}</div>
          {op.description && <div className="muted">{op.description}</div>}
        </div>
        {dlg === "view" && <CnViewSettings onClose={() => setDlg("")} />}
      </div>
    );
  }

  const shown = CN_IND.filter((k) => ui.cutIndicators.includes(k));
  return (
    <div className="panel" {...scopeProps("cut")}>
      <CnTabs right={toolbar} />
      <CnProgress project={project} op={op} />
      <div className="statusline" data-testid="cn-cut-status">
        {shown.map((k) => (
          <span key={k} title={t(`cn.ind.${k}`)}>{k === "num" ? "№" : k}: <b data-testid={k === "F" ? "cn-cut-fill" : undefined}>
            {indicator(k, m, res, n)}</b>{k === "S" && m.is_remnant ? ` (${t("cut.remnant_sheet")})` : ""}</span>))}
        {(res.sheets_per_pack ?? 1) > 1 && (
          <span title={t("cut.packs_hint", { n: res.sheets_per_pack })} data-testid="cn-cut-packs">{t("cut.packs")}: <b>{m.packs}/{res.total_packs}</b></span>)}
        <span className="nav">
          <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => go(1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => go(idx - 1)} disabled={idx <= 1} />
          <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => go(idx + 1)} disabled={idx >= n} testid="cn-map-next" />
          <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => go(n)} disabled={idx >= n} />
        </span>
      </div>
      {(unplaced.length > 0 || m.comment || res.manual || m.done_count > 0 || (res.warnings ?? []).length > 0) && (
        <div className="cut-notes">
          {(res.warnings ?? []).map((w, i) => <span key={i} className="warn" data-testid="cn-cut-warning">{w}</span>)}
          {unplaced.length > 0 && <span className="warn" data-testid="cn-cut-unplaced">{t("cut.unplaced", { n: res.unplaced.length })}: {unplaced.map((u) =>
            `${u.part?.uid ?? "?"}×${u.c}`).join(", ")}</span>}
          {m.comment && <span className="comment"><MessageSquare size={12} /> {m.comment}</span>}
          {res.manual && <span className="muted">{t("cut.manual")}</span>}
          {m.done_count > 0 && <span className="ok">{t("cut.done_count", { d: m.done_count, c: m.copies })}</span>}
        </div>
      )}
      <div className="cut-body">
        <div className="cn-map-box" data-testid="cn-map-wrap">
          <MapViewport resetKey={`${op.id}-${idx}`} testid="cn-viewport">
            <NestMap map={m} op={op} label={ui.mapLabel} showLabels={prefs.labels} highlightPartId={pinPart} testid="cn-map"
              onClick={(p) => setPinPart((cur) => { const id = p.idx !== null ? m.placements[p.idx]?.part_id ?? null : null; return id && cur !== id ? id : null; })}
              onDouble={(p) => { const id = p.idx !== null ? m.placements[p.idx]?.part_id : null; if (id) setPropsPart(id); }} />
          </MapViewport>
        </div>
        <div className="cut-side">
          <button type="button" className="linkbtn cut-side-head" onClick={() => setSide(side === "maps" ? "parts" : "maps")} data-testid="cn-toggle-side">
            {side === "maps" ? t("cut.maps") : t("cn.cut.map_parts")}
          </button>
          {side === "parts" ? (
            <div className="scroll"><MapPartsTable map={m} op={op} pin={pinPart} onPin={setPinPart} /></div>
          ) : (
            <div className="scroll thumbs">
              {maps.map((mm) => (
                <button key={mm.index} type="button" className={cx("thumb", mm.index === idx && "thumb-active")} onClick={() => go(mm.index)}
                  data-testid={`cn-thumb-${mm.index}`}>
                  <NestMap map={mm} op={op} thumb className="thumbsvg" />
                  <span>№{mm.index} S:{fmt(mm.sheet_length)}/{fmt(mm.sheet_width)} C:{mm.copies}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {dlg === "editor" && <CnEditor project={project} op={op} onClose={(saved) => {
        const r = saved?.operations.find((o) => o.id === op.id)?.result;      // saqlangan qo'lda natijada деловой qoldiq bo'lsa — omborga yozishni taklif qilamiz
        const offer = !!r && app.data?.remnant_confirm === true && !r.remnants_saved
          && r.maps.some((mm) => mm.offcuts.some((o) => o.kind === "remnant" && o.business));
        setDlg(offer ? "commit" : "");
      }} />}
      {dlg === "commit" && <RemnantCommitDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "view" && <CnViewSettings onClose={() => setDlg("")} />}
      {propsPart && op.parts.find((p) => p.id === propsPart) && (
        <PartProperties project={project} op={op} part={op.parts.find((p) => p.id === propsPart)!} onClose={() => setPropsPart(null)} />)}
    </div>
  );
}

/** Karta detallari jadvali: № (uid), o'rovchi o'lcham, soni, nom — va karta qoldiqlari (Д№, detal ichidagisi ⊂). */
function MapPartsTable({ map, op, pin, onPin }: { map: CutMap; op: Operation; pin: string | null; onPin: (id: string | null) => void }) {
  const { t } = useTranslation();
  const rows = useMemo(() => {
    const cnt = new Map<string, { uid: number; w: number; h: number; c: number; angles: Set<number> }>();
    for (const pl of map.placements) {
      const [x0, y0, x1, y1] = bboxOf(placementRing(pl));
      const e = cnt.get(pl.part_id) ?? { uid: pl.part_uid, w: x1 - x0, h: y1 - y0, c: 0, angles: new Set<number>() };
      e.c += 1;
      e.angles.add(Math.round((pl.angle ?? 0) * 10) / 10);
      cnt.set(pl.part_id, e);
    }
    return [...cnt.entries()];
  }, [map]);
  const rem = map.offcuts.filter((o) => o.kind === "remnant");
  return (
    <>
      <table className="simple cn-map-parts" data-testid="cn-map-parts">
        <thead><tr><th>№</th><th>{t("cn.cut.size")}</th><th>{t("pc.qty")}</th><th>{t("pc.name")}</th></tr></thead>
        <tbody>
          {rows.map(([pid, e]) => (
            <tr key={pid} className={cx(pin === pid && "tr-sel")} onClick={() => onPin(pin === pid ? null : pid)}>
              <td>{e.uid}</td><td className="num">{fmt(e.w)}×{fmt(e.h)}</td><td className="num">{e.c}</td><td>{op.parts.find((p) => p.id === pid)?.name ?? ""}</td>
            </tr>))}
        </tbody>
      </table>
      {rem.length > 0 && (
        <table className="simple cn-map-rem" data-testid="cn-map-remnants">
          <thead><tr><th>{t("cn.cut.rem_no")}</th><th>{t("cn.cut.size")}</th><th>{t("cn.cut.rem_where")}</th></tr></thead>
          <tbody>
            {rem.map((o, i) => (
              <tr key={i} className={o.business ? "row-business" : ""}>
                <td>Д{o.number}</td><td className="num">{fmt(o.length)}×{fmt(o.width)}</td>
                <td>{(o.in_part ?? 0) > 0 ? t("cn.cut.in_part", { uid: o.in_part }) : "—"}</td>
              </tr>))}
          </tbody>
        </table>
      )}
    </>
  );
}

/** «Настройки» (Ctrl+P): detal yozuvi, etiketka o'rni, holat qatori ko'rsatkichlari. */
function CnViewSettings({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const prefs = useCnPrefs();
  return (
    <Modal title={t("cut.view_settings")} onClose={onClose} width={440} testid="cn-view-settings"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} />}>
      <div className="form1">
        <Field label={t("print.f.map_part_label")}>
          <Sel value={ui.mapLabel} width={200} onChange={(v) => ui.set({ mapLabel: v })} testid="cn-view-label"
            options={(["number", "name", "number_name"] as const).map((v) => ({ value: v, label: t(`print.label.${v}`) }))} />
        </Field>
        <Field label=" "><Check checked={prefs.labels} label={t("cn.cut.label_spots")} onChange={prefs.setLabels} testid="cn-view-labels" /></Field>
        <div className="form-h">{t("cut.indicators")}</div>
        <table className="simple" data-testid="cn-indicators">
          <tbody>{CN_IND.map((k) => (
            <tr key={k}><td><Check checked={ui.cutIndicators.includes(k)} onChange={(v) => ui.set({
              cutIndicators: v ? CN_IND.filter((x) => x === k || ui.cutIndicators.includes(x)) : ui.cutIndicators.filter((x) => x !== k) })} /></td>
              <td><b>{k === "num" ? "№" : k}</b></td><td>{t(`cn.ind.${k}`)}</td></tr>))}</tbody>
        </table>
        <Btn small label={t("cut.ind_reset")} onClick={() => ui.set({ cutIndicators: ["num", "S", "C", "Cp", "LT", "F"] })} />
      </div>
    </Modal>
  );
}
