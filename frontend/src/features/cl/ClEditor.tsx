// CLE — «Редактирование погонажного раскроя» (hujjat D-CL6): chapda detallar jadvali (soni / ishlatilgan / qoldi), o'ngda polosa kartalari.
// Har amal serverda bajariladi va tekshiriladi (`cl_editor.apply` → qoralama); sig'maydigan / ortiqcha joylash qaytarilmaydi.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowDownToLine, ArrowLeftToLine, ArrowRightToLine, ArrowUpToLine, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, FilePlus2,
  FileX2, Funnel, Maximize, MoveDown, MoveUp, Redo2, Trash, Undo2, Wand,
} from "lucide-react";
import { ApiError, get, post, put } from "../../api/client";
import { call } from "../../api/hooks";
import type { CuttingResult, Operation, Part, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { enterFullscreenWithKeys, exitFullscreen, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Num, Sep, cx, fmt } from "../../shared/ui";
import { computeSizes, edgeParams, totalQty } from "../cs/sizes";
import { StripMap, mapTrims, type StripPick } from "./StripMap";

type Action = Record<string, unknown> & { type: string };

/** Kroy qilinmagan operatsiyada «Редактирование раскроя» — kartalar qo'lda qo'shiladi (onlayn tizimdagidek). */
const EMPTY_RESULT = { kind: "linear", maps: [], unplaced: [] } as unknown as CuttingResult;

export function ClEditor({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const cl = op.cl!;
  const [draft, setDraft] = useState<CuttingResult>(() => JSON.parse(JSON.stringify(op.result ?? EMPTY_RESULT)));   // kroysiz — bo'sh natijadan (qo'lda)
  const [past, setPast] = useState<CuttingResult[]>([]);
  const [future, setFuture] = useState<CuttingResult[]>([]);
  const [mi, setMi] = useState(Math.min(ui.mapIndex, op.result?.maps.length ?? 1));
  const [sel, setSel] = useState<number | null>(null);          // joriy kartada tanlangan detal (0 dan)
  const [multi, setMulti] = useState<number[]>([]);              // Ctrl+bosish bilan qo'shimcha tanlangan detallar (onlayn yordam)
  const heldA = useRef(false);                                   // [SHIFT]+[A]+click — ko'p nusxa qo'yish
  useEffect(() => {
    const f = (v: boolean) => (e: KeyboardEvent) => { if (e.code === "KeyA") heldA.current = v; };
    const d = f(true), u = f(false);
    window.addEventListener("keydown", d); window.addEventListener("keyup", u);
    return () => { window.removeEventListener("keydown", d); window.removeEventListener("keyup", u); };
  }, []);
  const allSel = (): number[] => [...new Set([...multi, ...(sel !== null ? [sel] : [])])];
  const [partUid, setPartUid] = useState<number | null>(null);   // chap jadvalda tanlangan detal
  const [onlyLeft, setOnlyLeft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rev, setRev] = useState<string | null>(null);
  const scope = "cl-editor";
  const m = draft.maps[mi - 1];
  useEffect(() => { void get<{ rev: string }>(`/projects/${project.id}/operations/${op.id}/cl-edit/rev`).then((r) => setRev(r.rev)).catch(() => undefined); },
    [project.id, op.id]);

  const used = useMemo(() => {
    const u = new Map<string, number>();
    draft.maps.forEach((mm) => mm.placements.forEach((p) => u.set(p.part_id, (u.get(p.part_id) ?? 0) + mm.copies)));
    return u;
  }, [draft]);
  const rows = useMemo(() => {
    const edges = edgeParams(project);
    return op.parts.filter((p) => p.length > 0).map((p) => {
      const need = Math.max(0, totalQty(project, p) - (p.minus_qty || 0));
      const us = used.get(p.id) ?? 0;
      const saw = computeSizes({ ...p, width: cl.width }, project.size_mode, edges, 0).saw[0];
      return { p, need, used: us, left: need - us, saw };
    }).filter((r) => r.need > 0 && r.saw > 0 && (!onlyLeft || r.left > 0));
  }, [op.parts, used, onlyLeft, project, cl.width]);

  /** `nextSel`: amaldan keyin tanlangan detalning yangi o'rni (ko'chirishda tanlov detal ketidan boradi); `keepSel` — o'zgarmaydi. */
  const act = async (action: Action, keepSel = false, nextSel?: number) => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await post<CuttingResult>(`/projects/${project.id}/operations/${op.id}/edit`, { result: draft, action });
      setPast([...past, draft]);
      setFuture([]);
      setDraft(r);
      if (nextSel !== undefined) setSel(nextSel);
      else if (!keepSel) setSel(null);
      if (!keepSel) setMulti([]);
      if (action.type === "add_map") setMi(r.maps.length);
      else if (action.type === "delete_map") setMi(Math.max(1, Math.min(mi, r.maps.length)));
      else if (action.type === "move_map") setMi(Math.max(1, Math.min(r.maps.length, mi + (action.to === "up" ? -1 : 1))));
    } catch (e) {
      ui.toast(e instanceof ApiError ? e.message : String(e), "error", e instanceof ApiError ? e.details : undefined);
    } finally {
      setBusy(false);
    }
  };
  const undo = () => { if (!past.length) return; setFuture([draft, ...future]); setDraft(past[past.length - 1]); setPast(past.slice(0, -1)); setSel(null); };
  const redo = () => { if (!future.length) return; setPast([...past, draft]); setDraft(future[0]); setFuture(future.slice(1)); setSel(null); };

  const onPick = (p: StripPick) => {
    if (p.button === 2) {                                        // o'ng tugma: detalni (tanlov ichida bo'lsa — butun tanlovni) olib tashlash
      if (p.index === null) return;
      const all = allSel();
      if (all.length > 1 && all.includes(p.index)) void act({ type: "remove", map: mi, indices: all });
      else void act({ type: "remove", map: mi, index: p.index });
      return;
    }
    if (p.index !== null) {
      if (p.ctrl && !p.shift) {                                   // [CTRL]+click — tanlovga qo'shish / olib tashlash
        const all = allSel();
        const next = all.includes(p.index) ? all.filter((i) => i !== p.index) : [...all, p.index];
        setSel(next.length ? next[next.length - 1] : null);
        setMulti(next.slice(0, -1));
        return;
      }
      setSel(p.index); setMulti([]); return;
    }
    const r = rows.find((x) => x.p.uid === partUid);             // bo'sh joyga bosish (Shift — onlayn tahrir rejimi): tanlangan detalni qo'yish
    if (r && r.left >= (m?.copies ?? 1)) void act({ type: "place", map: mi, uid: partUid, index: p.insertAt, ...(p.shift && heldA.current ? { fill: true } : {}) });
    else { setSel(null); setMulti([]); }
  };

  const needSel = (fn: (i: number) => void) => () => { if (sel !== null) fn(sel); else ui.toast(t("cl.ed.select_first"), "info"); };
  const ops = {
    start: needSel((i) => void act({ type: "move", map: mi, index: i, to: "start" }, true, 0)),
    end: needSel((i) => void act({ type: "move", map: mi, index: i, to: "end" }, true, Math.max(0, (m?.placements.length ?? 1) - 1))),
    left: needSel((i) => void act({ type: "move", map: mi, index: i, to: "left" }, true, Math.max(0, i - 1))),
    right: needSel((i) => void act({ type: "move", map: mi, index: i, to: "right" }, true, Math.min(Math.max(0, (m?.placements.length ?? 1) - 1), i + 1))),
    remove: needSel((i) => void act(multi.length ? { type: "remove", map: mi, indices: allSel() } : { type: "remove", map: mi, index: i })),
    prevMap: needSel((i) => mi > 1 && void act({ type: "transfer", map: mi, index: i, to_map: mi - 1 })),
    nextMap: needSel((i) => mi < draft.maps.length && void act({ type: "transfer", map: mi, index: i, to_map: mi + 1 })),
    auto: () => { if (partUid !== null) void act({ type: "place_auto", map: mi, uid: partUid }); else ui.toast(t("cl.ed.select_part"), "info"); },
  };
  // tanlangan detal indeksi qoralama o'zgarganda (ko'chirish) shu detal ketidan boradi
  const trims: [number, number] = m ? mapTrims(m, op) : [0, 0];

  const ok = async () => {
    if (op.result?.remnants_saved && !(await askConfirm(t("cut.recut_saved")))) return;
    const r = await call(() => put(`/projects/${project.id}/operations/${op.id}/result${rev ? `?base=${encodeURIComponent(rev)}` : ""}`,
      { ...draft, manual: true }));
    if (r) { ui.toast(t("editor.saved"), "ok"); ui.set({ mapIndex: mi }); onClose(); }
  };
  const cancel = async () => {
    if (past.length && !(await askConfirm(t("editor.discard_q")))) return;
    onClose();
  };

  const enteredFs = useRef(false);
  const toggleFullscreen = () => {
    if (document.fullscreenElement) { exitFullscreen(); enteredFs.current = false; }
    else { enteredFs.current = true; void enterFullscreenWithKeys(); }
  };
  useEffect(() => () => { if (enteredFs.current) exitFullscreen(); }, []);

  useHotkeys(scope, {
    "ctrl+z": undo, "ctrl+y": redo, "ctrl+arrowleft": ops.start, "ctrl+arrowright": ops.end,
    "alt+arrowleft": ops.left, "alt+arrowright": ops.right, delete: ops.remove, "ctrl+f": () => setOnlyLeft(!onlyLeft),
    "ctrl+arrowup": () => mi > 1 && void act({ type: "move_map", map: mi, to: "up" }),
    "ctrl+arrowdown": () => mi < draft.maps.length && void act({ type: "move_map", map: mi, to: "down" }),
    "pageup,arrowup": () => { setMi(Math.max(1, mi - 1)); setSel(null); }, "pagedown,arrowdown": () => { setMi(Math.min(draft.maps.length, mi + 1)); setSel(null); },
    home: () => { setMi(1); setSel(null); }, end: () => { setMi(Math.max(1, draft.maps.length)); setSel(null); },
    "shift+arrowup": ops.prevMap, "shift+arrowdown": ops.nextMap,
    f9: toggleFullscreen, "ctrl+enter": () => void ok(),
  });

  return (
    <Modal title={t("cl.ed.title")} onClose={() => void cancel()} full scope={scope} testid="cl-editor"
      headerRight={<button type="button" className="linkbtn" onClick={toggleFullscreen} data-testid="cl-ed-fullscreen"
        title={`${t("editor.fullscreen")} (F9)`}><Maximize size={14} /> {t("editor.fullscreen")}</button>}
      footer={<>
        <div className="editor-hint">
          <b>[{t("editor.lmb")}]</b> {t("cl.ed.h_left")}; <b>[{t("editor.rmb")}]</b> {t("cl.ed.h_right")};<br />
          <b>[Ctrl]+[{t("editor.lmb")}]</b> {t("cl.ed.h_ctrl")}; <b>[Shift]+[A]+[{t("editor.lmb")}]</b> {t("cl.ed.h_fill")};<br />
          <b>Ctrl+←/→</b> {t("cl.ed.h_ends")}; <b>Alt+←/→</b> {t("cl.ed.h_step")}; <b>Shift+↑/↓</b> {t("cl.ed.h_transfer")}
        </div>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="cl-editor-ok" />
        <Btn label={t("app.cancel")} onClick={() => void cancel()} />
      </>}>
      <div className="editor">
        <div className="editor-list">
          <table className="simple ed-parts" data-testid="cl-ed-parts">
            {/* onlayn yordam tartibi: Длина, Ширина, Кол-во, Исп. Кол., Остаток, Ткт, Наименование */}
            <thead><tr><th>№</th><th title={t("cl.ed.size_hint")}>{t("cl.col.length")}</th><th>{t("pp.width")}</th><th>{t("editor.col.qty")}</th>
              <th>{t("editor.col.used")}</th><th>{t("editor.col.left")}</th><th>{t("editor.col.grain")}</th><th>{t("pc.name")}</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.p.id} className={cx(partUid === r.p.uid && "tr-sel", r.left <= 0 && "muted", r.left > 0 && "row-left")}
                  onClick={() => setPartUid(r.p.uid)} onDoubleClick={() => { setPartUid(r.p.uid); void act({ type: "place_auto", map: mi, uid: r.p.uid }); }}
                  data-testid={`cl-ed-part-${r.p.uid}`}>
                  <td>{r.p.uid}</td><td className="num">{fmt(r.saw)}</td><td className="num">{fmt(cl.width)}</td><td className="num">{r.need}</td>
                  <td className="num">{r.used}</td><td className="num" data-testid={`cl-ed-left-${r.p.uid}`}>{r.left}</td>
                  <td className="center">{r.p.grain ? "✓" : ""}</td><td>{r.p.name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="editor-main">
          <div className="toolbar">
            <IconBtn icon={Undo2} title={`${t("menu.undo")} (Ctrl+Z)`} onClick={undo} disabled={!past.length} />
            <IconBtn icon={Redo2} title={`${t("menu.redo")} (Ctrl+Y)`} onClick={redo} disabled={!future.length} />
            <Sep />
            <IconBtn icon={FilePlus2} title={t("editor.add_map")} onClick={() => void act({ type: "add_map", sheet_id: m?.sheet_id })} testid="cl-ed-add-map" />
            <IconBtn icon={FileX2} title={t("editor.delete_map")} disabled={!m}
              onClick={async () => { if (await askConfirm(t("editor.delete_map_q"))) void act({ type: "delete_map", map: mi }); }} testid="cl-ed-del-map" />
            <IconBtn icon={MoveUp} title={`${t("cl.ed.map_up")} (Ctrl+↑)`} onClick={() => void act({ type: "move_map", map: mi, to: "up" })} disabled={mi <= 1} />
            <IconBtn icon={MoveDown} title={`${t("cl.ed.map_down")} (Ctrl+↓)`} onClick={() => void act({ type: "move_map", map: mi, to: "down" })}
              disabled={mi >= draft.maps.length} />
            <Sep />
            <IconBtn icon={ArrowLeftToLine} title={`${t("editor.to_start")} (Ctrl+←)`} onClick={ops.start} disabled={sel === null} testid="cl-ed-start" />
            <IconBtn icon={ChevronLeft} title={`${t("cl.ed.step_left")} (Alt+←)`} onClick={ops.left} disabled={sel === null} />
            <IconBtn icon={ChevronRight} title={`${t("cl.ed.step_right")} (Alt+→)`} onClick={ops.right} disabled={sel === null} />
            <IconBtn icon={ArrowRightToLine} title={`${t("editor.to_end")} (Ctrl+→)`} onClick={ops.end} disabled={sel === null} testid="cl-ed-end" />
            <IconBtn icon={ArrowUpToLine} title={`${t("cl.ed.to_prev_map")} (Shift+↑)`} onClick={ops.prevMap} disabled={sel === null || mi <= 1} />
            <IconBtn icon={ArrowDownToLine} title={`${t("cl.ed.to_next_map")} (Shift+↓)`} onClick={ops.nextMap}
              disabled={sel === null || mi >= draft.maps.length} />
            <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={ops.remove} disabled={sel === null} color="#c0392b" testid="cl-ed-delete" />
            <IconBtn icon={Wand} title={`${t("editor.auto_place")} (${t("cl.ed.dblclick")})`} onClick={ops.auto} disabled={partUid === null} testid="cl-ed-auto" />
            <IconBtn icon={Funnel} title={`${t("editor.only_left")} (Ctrl+F)`} active={onlyLeft} onClick={() => setOnlyLeft(!onlyLeft)} />
            <Sep />
            <IconBtn icon={ChevronUp} title={`${t("cut.prev")} (PgUp)`} onClick={() => { setMi(Math.max(1, mi - 1)); setSel(null); }} disabled={mi <= 1} />
            <IconBtn icon={ChevronDown} title={`${t("cut.next")} (PgDn)`} onClick={() => { setMi(Math.min(draft.maps.length, mi + 1)); setSel(null); }}
              disabled={mi >= draft.maps.length} />
            {m && <span className="row gap" title={t("cl.ed.copies_hint")}>C: <Num value={m.copies} min={1} width={48} testid="cl-ed-copies"
              onCommit={(v) => v && v !== m.copies && void act({ type: "copies", map: mi, copies: Math.round(v) }, true)} /></span>}
            {m && <span className="row gap" title={t("cl.ed.trims_hint")}>{t("cl.ed.trim")}: <Num value={trims[0]} min={0} max={500} width={44} testid="cl-ed-trim-start"
              onCommit={(v) => v !== null && v !== trims[0] && void act({ type: "trims", map: mi, trim_start: v, trim_end: trims[1] }, true)} />
              / <Num value={trims[1]} min={0} max={500} width={44} testid="cl-ed-trim-end"
                onCommit={(v) => v !== null && v !== trims[1] && void act({ type: "trims", map: mi, trim_start: trims[0], trim_end: v }, true)} /></span>}
          </div>
          <div className="thumbs-row">
            {draft.maps.map((mm) => (
              <button key={mm.index} type="button" className={cx("thumb small cl-thumb-btn", mm.index === mi && "thumb-active")}
                onClick={() => { setMi(mm.index); setSel(null); }}>
                <StripMap map={mm} project={project} op={op} thumb className="thumbsvg cl-thumb" />
                <span>№{mm.index} C:{mm.copies}</span>
              </button>
            ))}
          </div>
          {m ? (
            <>
              <div className="statusline">
                <span>№: <b>{mi}/{draft.maps.length}</b></span>
                <span>S: <b>{fmt(m.sheet_length)}/{fmt(m.sheet_width)}</b></span>
                <span>C: <b>{m.copies}/{draft.total_sheets}</b></span>
                <span>Cp: <b>{m.parts_count}/{draft.total_parts}</b></span>
                <span>LT: <b>{fmt(m.cut_length_m)}/{fmt(draft.total_cut_length_m)}</b></span>
                <span>F: <b data-testid="cl-ed-fill">{fmt(m.fill_percent)}%/{fmt(draft.total_fill_percent)}%</b></span>
                {draft.unplaced.length > 0 && <span className="warn" data-testid="cl-ed-unplaced">{t("cut.unplaced", { n: draft.unplaced.length })}</span>}
                {sel !== null && m.placements[sel] && <span className="muted">{t("editor.sel_part")} {m.placements[sel].part_uid}: {fmt(m.placements[sel].length)}</span>}
              </div>
              <div className={cx("editor-map cl-editor-map", busy && "is-busy")}>
                <StripMap map={m} project={project} op={op} selectedIndex={sel} selectedMore={multi} onPick={onPick} testid="cl-editor-map"
                  highlightPartId={partUid !== null ? op.parts.find((p: Part) => p.uid === partUid)?.id ?? null : null} />
              </div>
            </>
          ) : <div className="empty">{t("editor.no_maps")}</div>}
        </div>
      </div>
    </Modal>
  );
}
