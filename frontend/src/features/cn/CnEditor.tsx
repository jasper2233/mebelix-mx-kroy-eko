// CNE — «Редактирование нестингового раскроя»: chapda detallar jadvali (soni / ishlatilgan / qoldi), o'ngda konturli karta.
// Tanlash (Shift — ko'p), tortib ko'chirish, strelkalar (1 mm / Shift 10 mm), yopishtirish («chet bo'yicha» — Ctrl+strelkalar, «nuqta bo'yicha»), burish (R / Shift+R / burchak),
// o'chirish, joylanmaganlarni qo'yish (jadvalda ikki marta bosish — avto; xaritaga bosish — shu joyga), qayta joylash, karta amallari, undo/redo.
// Har amal serverda bajariladi va tekshiriladi (`cn_editor.apply` → qoralama + `validate_cn`); buzilsa 422 va qoralama o'zgarmaydi. CLE (ClEditor) namunasida.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowDownToLine, ArrowLeftToLine, ArrowRightToLine, ArrowUpToLine, ChevronDown, ChevronUp, Crosshair, FilePlus2, FileX2, Funnel, Maximize,
  MessageSquare, MoveDown, MoveUp, Redo2, RefreshCw, RotateCcw, RotateCw, Trash, Undo2, Wand, Tag, Ruler,
} from "lucide-react";
import { ApiError, get, post, put } from "../../api/client";
import { applyProject } from "../../api/hooks";
import type { CuttingResult, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText, showError } from "../../shared/dialogs";
import { enterFullscreenWithKeys, exitFullscreen, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Num, Sel, Sep, cx, fmt, parseNum } from "../../shared/ui";
import { indicator } from "../cs/cutIndicators";
import { totalQty } from "../cs/sizes";
import { MapViewport, NestMap, type NestPick } from "./NestMap";
import { bboxOf, clientToSvg, keyPoints, placementKeyPoints, placementRing, svgToClient, type Pt } from "./cnGeom";
import { useCnPrefs, useCnShapes } from "./cnHooks";

type Action = Record<string, unknown> & { type: string };
type Mode = "select" | "snap";

const SNAP_PX = 12;          // yopishtirish nuqtasini tanlash radiusi (piksel)
const r2 = (v: number) => Math.round(v * 100) / 100;

export function CnEditor({ project, op, onClose }: { project: Project; op: Operation; onClose: (saved?: Project) => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const prefs = useCnPrefs();
  const cn = op.cn!;
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [draft, setDraft] = useState<CuttingResult>(() => JSON.parse(JSON.stringify(op.result)));
  const [past, setPast] = useState<CuttingResult[]>([]);
  const [future, setFuture] = useState<CuttingResult[]>([]);
  const [mi, setMi] = useState(Math.min(ui.mapIndex, op.result?.maps.length ?? 1));
  const [sel, setSel] = useState<number[]>([]);                     // joriy kartada tanlangan pozitsiyalar (0 dan)
  const [placeUid, setPlaceUid] = useState<number | null>(null);     // chap jadvalda tanlangan (xaritaga qo'yish uchun) detal
  const [onlyLeft, setOnlyLeft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rev, setRev] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("select");
  const [snapFrom, setSnapFrom] = useState<Pt | null>(null);
  const [drag, setDrag] = useState<{ dx: number; dy: number } | null>(null);
  const [sheetForNew, setSheetForNew] = useState(op.sheets[0]?.id ?? "");
  const suppressClick = useRef(false);
  const dragCleanup = useRef<(() => void) | null>(null);
  const scope = "cn-editor";
  const m = draft.maps[mi - 1];
  const shapes = useCnShapes(project, op).data;
  const byPart = useMemo(() => new Map((shapes?.parts ?? []).map((s) => [s.id, s])), [shapes]);

  useEffect(() => { void get<{ rev: string }>(`/projects/${project.id}/operations/${op.id}/cn-edit/rev`).then((r) => setRev(r.rev)).catch(() => undefined); },
    [project.id, op.id]);
  useEffect(() => () => dragCleanup.current?.(), []);

  const used = useMemo(() => {
    const u = new Map<string, number>();
    draft.maps.forEach((mm) => mm.placements.forEach((p) => u.set(p.part_id, (u.get(p.part_id) ?? 0) + mm.copies)));
    return u;
  }, [draft]);
  const rows = useMemo(() => op.parts.filter((p) => p.length > 0 && p.width > 0 && (!shapes || byPart.has(p.id))).map((p) => {
    const need = Math.max(0, totalQty(project, p) - (p.minus_qty || 0));
    const us = used.get(p.id) ?? 0;
    const s = byPart.get(p.id);
    return { p, need, used: us, left: need - us, w: s ? s.width : p.length, h: s ? s.height : p.width };
  }).filter((r) => r.need > 0 && (!onlyLeft || r.left > 0)), [op.parts, used, onlyLeft, project, shapes, byPart]);
  const row = rows.find((r) => r.p.uid === placeUid);

  /** `keepSel` — tanlov saqlanadi (indekslar o'zgarmaydigan amallar: ko'chirish, burish, yopishtirish). Xato (422) — toast, qoralama o'zgarmaydi. */
  const act = async (action: Action, keepSel = false) => {
    if (busy) return false;
    setBusy(true);
    try {
      const r = await post<CuttingResult>(`/projects/${project.id}/operations/${op.id}/edit`, { result: draft, action });
      setPast([...past, draft]);
      setFuture([]);
      setDraft(r);
      if (!keepSel) setSel([]);
      if (action.type === "add_map") setMi(r.maps.length);
      else if (action.type === "delete_map") setMi(Math.max(1, Math.min(mi, r.maps.length)));
      else if (action.type === "move_map") setMi(Math.max(1, Math.min(r.maps.length, { up: mi - 1, down: mi + 1, first: 1, last: r.maps.length }[String(action.to)] ?? mi)));
      return true;
    } catch (e) {
      ui.toast(e instanceof ApiError ? e.message : String(e), "error", e instanceof ApiError ? e.details : undefined);
      return false;
    } finally {
      setBusy(false);
      setDrag(null);
    }
  };
  const undo = () => { if (!past.length) return; setFuture([draft, ...future]); setDraft(past[past.length - 1]); setPast(past.slice(0, -1)); setSel([]); };
  const redo = () => { if (!future.length) return; setPast([...past, draft]); setDraft(future[0]); setFuture(future.slice(1)); setSel([]); };
  const goMap = (i: number) => { setMi(Math.max(1, Math.min(draft.maps.length, i))); setSel([]); setSnapFrom(null); };

  // ───────── yopishtirish nuqtalari (mode = "snap") ─────────
  const zonePts = useMemo<Pt[]>(() => {
    if (!m) return [];
    const k = cn.margin;
    return [[k, k], [m.sheet_length - k, k], [k, m.sheet_width - k], [m.sheet_length - k, m.sheet_width - k]];
  }, [m, cn.margin]);
  const fromDots = useMemo<Pt[]>(() => (m ? sel.flatMap((i) => (m.placements[i] ? placementKeyPoints(m.placements[i]) : [])) : []), [m, sel]);
  const targetDots = useMemo<Pt[]>(() => {
    if (!m) return [];
    const s = new Set(sel);
    return [...zonePts, ...m.placements.flatMap((p, i) => (s.has(i) ? [] : keyPoints(placementRing(p))))];
  }, [m, sel, zonePts]);
  const dots = mode === "snap" ? (snapFrom ? targetDots : fromDots) : [];
  const nearestDot = (client: [number, number]): Pt | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    let best: Pt | null = null, bd = SNAP_PX;
    for (const d of dots) {
      const c = svgToClient(svg, d[0], d[1]);
      if (!c) continue;
      const dist = Math.hypot(c[0] - client[0], c[1] - client[1]);
      if (dist <= bd) { bd = dist; best = d; }
    }
    return best;
  };

  // ───────── sichqoncha ─────────
  const startDrag = (p: NestPick, indices: number[], onPlainClick?: () => void) => {
    const svg = svgRef.current;
    if (!svg) return;
    dragCleanup.current?.();
    const [sx, sy] = p.client;
    let active = false;
    const move = (ev: MouseEvent) => {
      if (!active && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 4) return;
      active = true;
      const q = clientToSvg(svg, ev.clientX, ev.clientY);
      if (q) setDrag({ dx: q[0] - p.x, dy: q[1] - p.y });
    };
    const up = (ev: MouseEvent) => {
      dragCleanup.current?.();
      if (!active) { onPlainClick?.(); return; }          // tortilmadi — oddiy bosish
      suppressClick.current = true;
      setTimeout(() => { suppressClick.current = false; }, 0);
      const q = clientToSvg(svg, ev.clientX, ev.clientY);
      const dx = q ? r2(q[0] - p.x) : 0, dy = q ? r2(q[1] - p.y) : 0;
      if (Math.hypot(dx, dy) < 0.05) { setDrag(null); return; }
      void act({ type: "move", map: mi, indices, dx, dy }, true);         // drag `act` tugagach o'zi tozalanadi (miltillamaslik uchun)
    };
    dragCleanup.current = () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); dragCleanup.current = null; };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };
  const onDown = (p: NestPick) => {
    if (p.button !== 0 || busy) return;
    if (mode === "snap") {
      const hit = nearestDot(p.client);
      if (hit) {
        if (!snapFrom) { setSnapFrom(hit); return; }
        const from = snapFrom;
        setSnapFrom(null);
        void act({ type: "snap", map: mi, indices: sel, from: [r2(from[0]), r2(from[1])], to: [r2(hit[0]), r2(hit[1])] }, true);
        return;
      }
    }
    if (p.idx === null) return;
    const uid = m?.placements[p.idx]?.part_uid ?? null;
    setPlaceUid(null);
    if (p.shift) { setSel(sel.includes(p.idx) ? sel.filter((i) => i !== p.idx) : [...sel, p.idx]); return; }
    const idx = p.idx;
    const next = sel.includes(idx) ? sel : [idx];
    setSel(next);
    // tanlangan guruhning birortasi bosilsa: tortilsa — guruh ko'chadi; tortilmasa — tanlov shu bitta detalga qisqaradi
    if (mode === "select" && uid !== null) startDrag(p, next, next.length > 1 ? () => setSel([idx]) : undefined);
  };
  const placeAt = (cx: number, cy: number, angle: number) => {
    if (!row || !m) return;
    const [bw, bh] = angle % 180 === 90 ? [row.h, row.w] : [row.w, row.h];
    const k = cn.margin;
    const x = Math.max(k, Math.min(m.sheet_length - k - bw, cx - bw / 2));
    const y = Math.max(k, Math.min(m.sheet_width - k - bh, cy - bh / 2));
    void act({ type: "place", map: mi, uid: row.p.uid, x: r2(x), y: r2(y), angle });
  };
  const onClick = (p: NestPick) => {
    if (suppressClick.current || busy || mode === "snap") return;
    if (p.idx !== null) return;                                       // tanlash `onDown` da bajarilgan
    if (row && row.left > 0 && !p.shift) { placeAt(p.x, p.y, p.alt ? 90 : 0); return; }   // jadvaldan tanlangan detalni shu joyga qo'yish (Alt — 90° burib)
    if (!p.shift) setSel([]);
  };
  const onContext = (p: NestPick) => {
    if (p.idx === null || busy) return;
    const indices = sel.includes(p.idx) && sel.length > 1 ? sel : [p.idx];
    void act({ type: "remove", map: mi, indices });
  };

  // ───────── amallar ─────────
  const needSel = (fn: () => void) => () => { if (sel.length) fn(); else ui.toast(t("cn.ed.select_first"), "info"); };
  const nudge = (dx: number, dy: number) => needSel(() => void act({ type: "move", map: mi, indices: sel, dx, dy }, true))();
  const slide = (dir: "left" | "right" | "up" | "down") => needSel(() => void act({ type: "slide", map: mi, indices: sel, dir }, true))();
  const rotate = (delta: number) => needSel(() => void act({ type: "rotate", map: mi, indices: sel, delta }, true))();
  const rotateAngle = async () => {
    if (!sel.length) { ui.toast(t("cn.ed.select_first"), "info"); return; }
    const single = sel.length === 1 ? m?.placements[sel[0]] : undefined;
    const v = await askText(single ? t("cn.ed.angle_abs") : t("cn.ed.angle_rel"), single ? String(r2(single.angle ?? 0)) : "0", { text: t("cn.ed.angle_hint") });
    if (v === null) return;
    const a = parseNum(v);
    if (a === null) { ui.toast(t("cn.ed.angle_bad"), "error"); return; }
    void act(single ? { type: "rotate", map: mi, indices: sel, angle: a } : { type: "rotate", map: mi, indices: sel, delta: a }, true);
  };
  const remove = needSel(() => void act({ type: "remove", map: mi, indices: sel }));
  const auto = () => { if (placeUid !== null) void act({ type: "auto_place", uid: placeUid, map: mi }); else ui.toast(t("cn.ed.select_part"), "info"); };
  const renest = async () => {
    if (!m || !(await askConfirm(t("cn.ed.renest_q"), t("cn.ed.renest_text")))) return;
    void act({ type: "renest", map: mi });
  };
  const comment = async () => {
    if (!m) return;
    const c = await askText(t("cut.comment"), m.comment, { multiline: true });
    if (c !== null && c !== m.comment) void act({ type: "comment", map: mi, comment: c }, true);
  };
  const toggleSnap = () => { setMode(mode === "snap" ? "select" : "snap"); setSnapFrom(null); };
  const selectAll = () => { if (m) setSel(m.placements.map((_, i) => i)); };

  const ok = async () => {
    if (op.result?.remnants_saved && !(await askConfirm(t("cut.recut_saved")))) return;
    try {
      const r = await put<Project>(`/projects/${project.id}/operations/${op.id}/result${rev ? `?base=${encodeURIComponent(rev)}` : ""}`, { ...draft, manual: true });
      applyProject(r);
      ui.toast(t("editor.saved"), "ok");
      ui.set({ mapIndex: mi });
      onClose(r);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) ui.toast(t("cn.ed.conflict"), "error");
      else showError(e);
    }
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

  const arrow = (dx: number, dy: number, step: number) => () => {
    if (sel.length) nudge(dx * step, dy * step);
    else if (dy !== 0 && step === 1) goMap(mi + dy);                // tanlov yo'q — ↑/↓ kartalar bo'ylab
  };
  useHotkeys(scope, {
    "ctrl+z": undo, "ctrl+y": redo, r: () => rotate(90), "shift+r": () => rotate(-90), "delete,shift+delete": remove,
    arrowleft: arrow(-1, 0, 1), arrowright: arrow(1, 0, 1), arrowup: arrow(0, -1, 1), arrowdown: arrow(0, 1, 1),
    "shift+arrowleft": arrow(-1, 0, 10), "shift+arrowright": arrow(1, 0, 10), "shift+arrowup": arrow(0, -1, 10), "shift+arrowdown": arrow(0, 1, 10),
    "ctrl+arrowleft": () => slide("left"), "ctrl+arrowright": () => slide("right"), "ctrl+arrowup": () => slide("up"), "ctrl+arrowdown": () => slide("down"),
    pageup: () => goMap(mi - 1), pagedown: () => goMap(mi + 1), home: () => goMap(1), end: () => goMap(draft.maps.length),
    s: toggleSnap, "ctrl+a": selectAll, "ctrl+f": () => setOnlyLeft(!onlyLeft), f2: () => void comment(), f9: toggleFullscreen,
    "ctrl+enter": () => void ok(),
    escape: () => { if (mode === "snap") { setMode("select"); setSnapFrom(null); } else if (sel.length) setSel([]); else void cancel(); },
  });

  const selPl = sel.length === 1 && m ? m.placements[sel[0]] : undefined;
  const selBox = selPl ? bboxOf(placementRing(selPl)) : null;
  const hiPart = row ? row.p.id : null;
  const nSheetsOpts = op.sheets.map((s) => ({ value: s.id, label: `${s.length}×${s.width}${s.is_remnant ? " ⟲" : ""}` }));

  return (
    <Modal title={t("cn.ed.title")} onClose={() => void cancel()} full scope={scope} testid="cn-editor"
      headerRight={<button type="button" className="linkbtn" onClick={toggleFullscreen} data-testid="cn-ed-fullscreen"
        title={`${t("editor.fullscreen")} (F9)`}><Maximize size={14} /> {t("editor.fullscreen")}</button>}
      footer={<>
        <div className="editor-hint">
          <b>[{t("editor.lmb")}]</b> {t("cn.ed.h_left")}; <b>[Shift]</b> {t("cn.ed.h_shift")}; <b>[{t("editor.rmb")}]</b> {t("cn.ed.h_right")};<br />
          <b>←↑→↓ / Shift+←↑→↓</b> {t("cn.ed.h_arrows")}; <b>Ctrl+←↑→↓</b> {t("cn.ed.h_slide")}; <b>R / Shift+R</b> {t("cn.ed.h_rotate")}; <b>S</b> {t("cn.ed.h_snap")}
        </div>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="cn-editor-ok" />
        <Btn label={t("app.cancel")} onClick={() => void cancel()} />
      </>}>
      <div className="editor cn-editor">
        <div className="editor-list">
          <table className="simple ed-parts" data-testid="cn-ed-parts">
            <thead><tr><th>№</th><th title={t("cn.ed.size_hint")}>{t("cn.cut.size")}</th><th>{t("editor.col.qty")}</th>
              <th>{t("editor.col.used")}</th><th>{t("editor.col.left")}</th><th>{t("pc.name")}</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.p.id} className={cx(placeUid === r.p.uid && "tr-sel", r.left <= 0 && "muted", r.left > 0 && "row-left")}
                  onClick={() => { setPlaceUid(r.p.uid); setSel([]); }}
                  onDoubleClick={() => { setPlaceUid(r.p.uid); void act({ type: "auto_place", uid: r.p.uid, map: mi }); }}
                  data-testid={`cn-ed-part-${r.p.uid}`}>
                  <td>{r.p.uid}</td><td className="num">{fmt(r.w)}×{fmt(r.h)}</td><td className="num">{r.need}</td>
                  <td className="num">{r.used}</td><td className="num" data-testid={`cn-ed-left-${r.p.uid}`}>{r.left}</td><td>{r.p.name}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="hint">{t("cn.ed.list_hint")}</div>
        </div>
        <div className="editor-main">
          <div className="toolbar">
            <IconBtn icon={Undo2} title={`${t("menu.undo")} (Ctrl+Z)`} onClick={undo} disabled={!past.length} testid="cn-ed-undo" />
            <IconBtn icon={Redo2} title={`${t("menu.redo")} (Ctrl+Y)`} onClick={redo} disabled={!future.length} testid="cn-ed-redo" />
            <Sep />
            <Sel value={sheetForNew} width={120} onChange={setSheetForNew} options={nSheetsOpts} />
            <IconBtn icon={FilePlus2} title={t("editor.add_map")} onClick={() => void act({ type: "add_map", sheet_id: sheetForNew || m?.sheet_id })} testid="cn-ed-add-map" />
            <IconBtn icon={FileX2} title={t("editor.delete_map")} disabled={!m}
              onClick={async () => { if (await askConfirm(t("editor.delete_map_q"))) void act({ type: "delete_map", map: mi }); }} testid="cn-ed-del-map" />
            <IconBtn icon={MoveUp} title={t("cl.ed.map_up")} onClick={() => void act({ type: "move_map", map: mi, to: "up" })} disabled={mi <= 1} />
            <IconBtn icon={MoveDown} title={t("cl.ed.map_down")} onClick={() => void act({ type: "move_map", map: mi, to: "down" })} disabled={mi >= draft.maps.length} />
            <IconBtn icon={MessageSquare} title={`${t("cut.comment")} (F2)`} onClick={() => void comment()} disabled={!m} active={!!m?.comment} />
            <Sep />
            <IconBtn icon={ArrowLeftToLine} title={`${t("cn.ed.slide_left")} (Ctrl+←)`} onClick={() => slide("left")} disabled={!sel.length} testid="cn-ed-slide-left" />
            <IconBtn icon={ArrowRightToLine} title={`${t("cn.ed.slide_right")} (Ctrl+→)`} onClick={() => slide("right")} disabled={!sel.length} testid="cn-ed-slide-right" />
            <IconBtn icon={ArrowUpToLine} title={`${t("cn.ed.slide_up")} (Ctrl+↑)`} onClick={() => slide("up")} disabled={!sel.length} testid="cn-ed-slide-up" />
            <IconBtn icon={ArrowDownToLine} title={`${t("cn.ed.slide_down")} (Ctrl+↓)`} onClick={() => slide("down")} disabled={!sel.length} testid="cn-ed-slide-down" />
            <IconBtn icon={Crosshair} title={`${t("cn.ed.snap_mode")} (S)`} onClick={toggleSnap} active={mode === "snap"} testid="cn-ed-snap" />
            <Sep />
            <IconBtn icon={RotateCw} title={`${t("cn.ed.rot_cw")} (R)`} onClick={() => rotate(90)} disabled={!sel.length} testid="cn-ed-rot-cw" />
            <IconBtn icon={RotateCcw} title={`${t("cn.ed.rot_ccw")} (Shift+R)`} onClick={() => rotate(-90)} disabled={!sel.length} testid="cn-ed-rot-ccw" />
            <IconBtn icon={Ruler} title={t("cn.ed.rot_angle")} onClick={() => void rotateAngle()} disabled={!sel.length} testid="cn-ed-rot-angle" />
            <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={remove} disabled={!sel.length} color="#c0392b" testid="cn-ed-delete" />
            <Sep />
            <IconBtn icon={Wand} title={`${t("editor.auto_place")} (${t("cl.ed.dblclick")})`} onClick={auto} disabled={placeUid === null} testid="cn-ed-auto" />
            <IconBtn icon={RefreshCw} title={t("cn.ed.renest")} onClick={() => void renest()} disabled={!m} testid="cn-ed-renest" />
            <IconBtn icon={Funnel} title={`${t("editor.only_left")} (Ctrl+F)`} active={onlyLeft} onClick={() => setOnlyLeft(!onlyLeft)} />
            <IconBtn icon={Tag} title={t("cn.cut.label_spots")} active={prefs.labels} onClick={() => prefs.setLabels(!prefs.labels)} />
            <Sep />
            <IconBtn icon={ChevronUp} title={`${t("cut.prev")} (PgUp)`} onClick={() => goMap(mi - 1)} disabled={mi <= 1} />
            <IconBtn icon={ChevronDown} title={`${t("cut.next")} (PgDn)`} onClick={() => goMap(mi + 1)} disabled={mi >= draft.maps.length} />
            {m && <span className="row gap" title={t("cl.ed.copies_hint")}>C: <Num value={m.copies} min={1} width={48} testid="cn-ed-copies"
              onCommit={(v) => v && v !== m.copies && void act({ type: "copies", map: mi, copies: Math.round(v) }, true)} /></span>}
          </div>
          <div className="thumbs-row">
            {draft.maps.map((mm) => (
              <button key={mm.index} type="button" className={cx("thumb small", mm.index === mi && "thumb-active")} onClick={() => goMap(mm.index)}>
                <NestMap map={mm} op={op} thumb className="thumbsvg" />
                <span>№{mm.index} C:{mm.copies}</span>
              </button>
            ))}
          </div>
          {m ? (
            <>
              <div className="statusline" data-testid="cn-ed-status">
                {["num", "S", "C", "Cp", "LT", "F", "CT"].map((k) => (
                  <span key={k} title={t(`cn.ind.${k}`)}>{k === "num" ? "№" : k}: <b data-testid={k === "F" ? "cn-ed-fill" : undefined}>
                    {indicator(k, m, draft, draft.maps.length)}</b></span>))}
                {draft.unplaced.length > 0 && <span className="warn" data-testid="cn-ed-unplaced">{t("cut.unplaced", { n: draft.unplaced.length })}</span>}
                {mode === "snap" && <span className="editor-mode" data-testid="cn-ed-mode">
                  {sel.length ? (snapFrom ? t("cn.ed.snap_to") : t("cn.ed.snap_from")) : t("cn.ed.snap_select")}</span>}
                {sel.length > 1 && <span className="editor-sel-count" data-testid="cn-ed-sel-count">{t("editor.selected", { n: sel.length })}</span>}
                {selPl && selBox && <span className="muted" data-testid="cn-ed-sel-info">{t("editor.sel_part")} {selPl.part_uid}: {fmt(selBox[2] - selBox[0])}×{fmt(selBox[3] - selBox[1])}
                  {` · ∠${fmt(selPl.angle ?? 0)}°`}</span>}
                {busy && <span className="muted">…</span>}
              </div>
              <div className={cx("editor-map cn-editor-map", busy && "is-busy", mode === "snap" && "cn-snap")}>
                <MapViewport resetKey={`${mi}`} testid="cn-ed-viewport">
                  <NestMap ref={svgRef} map={m} op={op} selected={sel} drag={drag} showLabels={prefs.labels} highlightPartId={hiPart}
                    testid="cn-editor-map" onDown={onDown} onClick={onClick} onContext={onContext}>
                    {dots.map((d, i) => (
                      <path key={i} d={`M${d[0]} ${d[1]}h0`} stroke={snapFrom ? "#1a9a4a" : "#0b57d0"} strokeWidth={10} strokeLinecap="round"
                        vectorEffect="non-scaling-stroke" pointerEvents="none" data-nopan="1" data-testid="cn-snap-dot" />
                    ))}
                    {snapFrom && <path d={`M${snapFrom[0]} ${snapFrom[1]}h0`} stroke="#d92f2f" strokeWidth={14} strokeLinecap="round"
                      vectorEffect="non-scaling-stroke" pointerEvents="none" data-testid="cn-snap-from" />}
                  </NestMap>
                </MapViewport>
              </div>
            </>
          ) : <div className="empty">{t("editor.no_maps")}</div>}
        </div>
      </div>
    </Modal>
  );
}
