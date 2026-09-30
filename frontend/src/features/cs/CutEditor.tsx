// «Редактирование раскроя» (UI_SPEC §5.4): detallar ro'yxati + karta; har amal serverda tekshiriladi.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowLeftToLine, ArrowRightToLine, ChevronDown, ChevronUp, Columns2, CopyPlus, Funnel, Expand, FilePlus2, FileX2,
  Redo2, RotateCw, Rows2, Trash, Undo2, Wand,
} from "lucide-react";
import { ApiError, post, put } from "../../api/client";
import { call } from "../../api/hooks";
import type { CuttingResult, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Num, Sel, Sep, cx, fmt } from "../../shared/ui";
import { MapView, nodeAt, type PickInfo } from "./MapView";
import { totalQty } from "./sizes";

type Action = Record<string, unknown> & { type: string };

export function CutEditor({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const [draft, setDraft] = useState<CuttingResult>(() => JSON.parse(JSON.stringify(op.result)));
  const [past, setPast] = useState<CuttingResult[]>([]);
  const [future, setFuture] = useState<CuttingResult[]>([]);
  const [mi, setMi] = useState(Math.min(ui.mapIndex, op.result?.maps.length ?? 1));
  const [sel, setSel] = useState<number[] | null>(null);
  const [partUid, setPartUid] = useState<number | null>(null);
  const [horizontal, setHorizontal] = useState(false);
  const [onlyLeft, setOnlyLeft] = useState(false);
  const [busy, setBusy] = useState(false);
  const scope = "editor";
  const m = draft.maps[mi - 1];
  const root = m?.strips?.[0];
  const selNode = root && sel ? nodeAt(root, sel) : null;

  const used = useMemo(() => {
    const u = new Map<string, number>();
    draft.maps.forEach((mm) => mm.placements.forEach((p) => u.set(p.part_id, (u.get(p.part_id) ?? 0) + mm.copies)));
    return u;
  }, [draft]);
  const rows = useMemo(() => op.parts.map((p) => {
    const tot = totalQty(project, p);
    const us = used.get(p.id) ?? 0;
    return { p, tot, used: us, left: tot - us, prod: project.products.find((x) => x.id === p.product_id)?.name ?? "" };
  }).filter((r) => !onlyLeft || r.left > 0), [op.parts, used, onlyLeft, project]);

  const act = async (action: Action, keepSel = false) => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await post<CuttingResult>(`/projects/${project.id}/operations/${op.id}/edit`, { result: draft, action });
      setPast([...past, draft]);
      setFuture([]);
      setDraft(r);
      if (!keepSel) setSel(null);
      if (action.type === "add_map") setMi(r.maps.length);
      else if (action.type === "delete_map") setMi(Math.max(1, Math.min(mi, r.maps.length)));
    } catch (e) {
      ui.toast(e instanceof ApiError ? e.message : String(e), "error", e instanceof ApiError ? e.details : undefined);
    } finally {
      setBusy(false);
    }
  };
  const undo = () => { if (!past.length) return; setFuture([draft, ...future]); setDraft(past[past.length - 1]); setPast(past.slice(0, -1)); setSel(null); };
  const redo = () => { if (!future.length) return; setPast([...past, draft]); setDraft(future[0]); setFuture(future.slice(1)); setSel(null); };

  const onPick = (p: PickInfo) => {
    const path = p.shift && p.path.length ? p.path.slice(0, -1) : p.path;
    if (p.button === 2) {
      if (path.length) void act({ type: "remove", map: mi, path });
      return;
    }
    const node = root ? nodeAt(root, path) : null;
    if (node?.k === "W" && partUid !== null && !p.shift) {
      const r = rows.find((x) => x.p.uid === partUid);
      if (r && r.left > 0) { void act({ type: "place", map: mi, path, uid: partUid, rotated: p.alt || p.ctrl }); return; }
    }
    setSel(path);
  };

  const needSel = (fn: (path: number[]) => void) => () => { if (sel && sel.length) fn(sel); else ui.toast(t("editor.select_first"), "info"); };
  const ops = {
    start: needSel((path) => void act({ type: "move", map: mi, path, to: "start" })),
    end: needSel((path) => void act({ type: "move", map: mi, path, to: "end" })),
    clone: needSel((path) => void act({ type: "clone", map: mi, path })),
    rotate: () => void act({ type: "rotate", map: mi, path: sel ?? [] }),
    expand: needSel((path) => void act({ type: "expand", map: mi, path })),
    remove: needSel((path) => void act({ type: "remove", map: mi, path })),
    parent: () => { if (sel && sel.length) setSel(sel.slice(0, -1)); },
    auto: () => { if (partUid !== null) void act({ type: "place_auto", map: mi, uid: partUid }); },
  };
  const [sheetForNew, setSheetForNew] = useState(op.sheets[0]?.id ?? "");

  const ok = async () => {
    if (op.result?.remnants_saved && !(await askConfirm(t("cut.recut_saved")))) return;
    const r = await call(() => put(`/projects/${project.id}/operations/${op.id}/result`, { ...draft, manual: true }));
    if (r) { ui.toast(t("editor.saved"), "ok"); ui.set({ mapIndex: mi }); onClose(); }
  };
  const cancel = async () => {
    if (past.length && !(await askConfirm(t("editor.discard_q")))) return;
    onClose();
  };

  useHotkeys(scope, {
    "ctrl+z": undo, "ctrl+y": redo, "ctrl+arrowleft": ops.start, "ctrl+arrowright": ops.end, "ctrl+c": ops.clone,
    "ctrl+r": ops.rotate, "ctrl+q": ops.expand, delete: ops.remove, "ctrl+f": () => setOnlyLeft(!onlyLeft),
    "pageup,arrowup": () => setMi(Math.max(1, mi - 1)), "pagedown,arrowdown": () => setMi(Math.min(draft.maps.length, mi + 1)),
    backspace: ops.parent, "ctrl+enter": () => void ok(),
  });

  return (
    <Modal title={t("editor.title")} onClose={() => void cancel()} full scope={scope} testid="cut-editor"
      headerRight={<button type="button" className="linkbtn" onClick={() => setHorizontal(!horizontal)}>
        {horizontal ? <Columns2 size={14} /> : <Rows2 size={14} />} {t("editor.horizontal")}</button>}
      footer={<>
        <div className="editor-hint">
          <b>[Shift]</b> {t("editor.h_shift")}; <b>[{t("editor.lmb")}]</b> {t("editor.h_left")};<br />
          <b>[Alt]/[Ctrl]</b> {t("editor.h_alt")}; <b>[{t("editor.rmb")}]</b> {t("editor.h_right")}
        </div>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="editor-ok" />
        <Btn label={t("app.cancel")} onClick={() => void cancel()} />
      </>}>
      <div className={cx("editor", horizontal && "editor-h")}>
        <div className="editor-list">
          <table className="simple ed-parts">
            <thead><tr><th>№</th><th>{t("editor.col.product")}</th><th>{t("pp.length")}</th><th>{t("pp.width")}</th>
              <th>{t("editor.col.qty")}</th><th>{t("editor.col.used")}</th><th>{t("editor.col.left")}</th><th>{t("pp.name")}</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.p.id} className={cx(partUid === r.p.uid && "tr-sel", r.left <= 0 && "muted", r.left > 0 && "row-left")}
                  onClick={() => setPartUid(r.p.uid)} onDoubleClick={() => { setPartUid(r.p.uid); void act({ type: "place_auto", map: mi, uid: r.p.uid }); }}
                  data-testid={`ed-part-${r.p.uid}`}>
                  <td>{r.p.uid}</td><td>{r.prod}</td><td className="num">{fmt(r.p.length)}</td><td className="num">{fmt(r.p.width)}</td>
                  <td className="num">{r.tot}</td><td className="num">{r.used}</td><td className="num">{r.left}</td><td>{r.p.name}</td>
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
            <Sel value={sheetForNew} width={130} onChange={setSheetForNew}
              options={op.sheets.map((s) => ({ value: s.id, label: `${s.length}×${s.width}${s.is_remnant ? " ⟲" : ""}` }))} />
            <IconBtn icon={FilePlus2} title={t("editor.add_map")} onClick={() => void act({ type: "add_map", sheet_id: sheetForNew })} testid="ed-add-map" />
            <IconBtn icon={FileX2} title={t("editor.delete_map")} disabled={!m}
              onClick={async () => { if (await askConfirm(t("editor.delete_map_q"))) void act({ type: "delete_map", map: mi }); }} />
            <Sep />
            <IconBtn icon={ArrowLeftToLine} title={`${t("editor.to_start")} (Ctrl+←)`} onClick={ops.start} disabled={!sel?.length} />
            <IconBtn icon={ArrowRightToLine} title={`${t("editor.to_end")} (Ctrl+→)`} onClick={ops.end} disabled={!sel?.length} />
            <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+C)`} onClick={ops.clone} disabled={!sel?.length} />
            <IconBtn icon={RotateCw} title={`${t("editor.rotate")} (Ctrl+R)`} onClick={ops.rotate} disabled={!selNode || selNode.k !== "C"} />
            <IconBtn icon={Expand} title={`${t("editor.expand")} (Ctrl+Q)`} onClick={ops.expand} disabled={!selNode || selNode.k !== "C"} />
            <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={ops.remove} disabled={!sel?.length} color="#c0392b" testid="ed-delete" />
            <IconBtn icon={Wand} title={t("editor.auto_place")} onClick={ops.auto} disabled={partUid === null} testid="ed-auto" />
            <IconBtn icon={Funnel} title={`${t("editor.only_left")} (Ctrl+F)`} active={onlyLeft} onClick={() => setOnlyLeft(!onlyLeft)} />
            <Sep />
            <IconBtn icon={ChevronUp} title={`${t("cut.prev")} (PgUp)`} onClick={() => setMi(Math.max(1, mi - 1))} disabled={mi <= 1} />
            <IconBtn icon={ChevronDown} title={`${t("cut.next")} (PgDn)`} onClick={() => setMi(Math.min(draft.maps.length, mi + 1))} disabled={mi >= draft.maps.length} />
            {m && <span className="row gap">C: <Num value={m.copies} min={1} width={44}
              onCommit={(v) => v && v !== m.copies && void act({ type: "copies", map: mi, copies: Math.round(v) }, true)} /></span>}
          </div>
          <div className="thumbs-row">
            {draft.maps.map((mm) => (
              <button key={mm.index} type="button" className={cx("thumb small", mm.index === mi && "thumb-active")}
                onClick={() => { setMi(mm.index); setSel(null); }}>
                <MapView map={mm} project={project} op={op} thumb className="thumbsvg" />
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
                <span>F: <b>{fmt(m.fill_percent)}%/{fmt(draft.total_fill_percent)}%</b></span>
                {draft.unplaced.length > 0 && <span className="warn">{t("cut.unplaced", { n: draft.unplaced.length })}</span>}
                {selNode && <span className="muted">{selNode.k === "P" ? `${t("editor.sel_part")} ${selNode.u}` :
                  selNode.k === "W" ? t("editor.sel_free") : t("editor.sel_strip")}: {fmt(selNode.l)}×{fmt(selNode.w)}</span>}
              </div>
              <div className={cx("editor-map", busy && "is-busy")}>
                <MapView map={m} project={project} op={op} selectedPath={sel} onPick={onPick} testid="editor-map"
                  highlightPartId={partUid !== null ? op.parts.find((p) => p.uid === partUid)?.id ?? null : null} />
              </div>
            </>
          ) : <div className="empty">{t("editor.no_maps")}</div>}
        </div>
      </div>
    </Modal>
  );
}
