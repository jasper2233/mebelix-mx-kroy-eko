// «Редактирование раскроя» (UI_SPEC §5.4): detallar ro'yxati + karta; har amal serverda tekshiriladi.
// W13 (CSE rejimlari): ko'p tanlash (Ctrl+bosish, ramka), Shift — tahrir rejimi (Shift+A ko'p qo'yish, Shift+W blok),
// kartalar tartibi (Ctrl+↑/↓), karta torsovkasi, detalni burish/almashtirish, F2 izoh, saralanadigan jadval.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowLeftRight, ArrowLeftToLine, ArrowRightToLine, ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, ChevronsDown, ChevronsUp,
  CircleQuestionMark, Columns2, LayoutGrid, List, CopyPlus, Funnel, Expand, FilePlus2, FileX2, Grid3x3, Hash, Boxes, ListChecks, Maximize, MessageSquare, Redo2, Replace,
  RefreshCw, RotateCw, Rows2, Shrink, SquareDashed, Trash, Undo2, Wand,
} from "lucide-react";
import { ApiError, get, post, put } from "../../api/client";
import { call, useAppSettings } from "../../api/hooks";
import type { CuttingResult, Operation, PackCorner, Project, TreeNode } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { enterFullscreenWithKeys, exitFullscreen, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sel, Sep, cx, fmt } from "../../shared/ui";
import { indicator, indWidth, shownIndicators } from "./cutIndicators";
import { CutTrimDialog, type TrimValues } from "./CutTrimDialog";
import { MapView, nodeAt, nodesInRect, samePath, type BandInfo, type PickInfo } from "./MapView";
import { computeSizes, edgeParams, totalQty } from "./sizes";
import { MapViewport } from "../cn/NestMap";
import "../cn/cn.css";
import "./cseW13.css";

type Action = Record<string, unknown> & { type: string };
type SortKey = "uid" | "product" | "length" | "width" | "qty" | "used" | "left" | "grain" | "name";
type Mode = "select" | "multi" | "block";          // sichqoncha rejimi: oddiy / ko'p qo'yish (Shift+A) / blok kengaytirish (Shift+W)

/** Tanlov → amal parametrlari: bitta element — `path`, bir nechta — `paths` (server ikkalasini ham qabul qiladi). */
const pathParams = (sel: number[][]) => (sel.length === 1 ? { path: sel[0] } : { paths: sel });

/** Kroy qilinmagan operatsiyada «Редактирование раскроя» — kartalar qo'lda qo'shiladi (onlayn tizimdagidek). */
const EMPTY_RESULT = { maps: [], unplaced: [] } as unknown as CuttingResult;

export function CutEditor({ project, op, onClose }: { project: Project; op: Operation; onClose: (saved?: Project) => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const [draft, setDraft] = useState<CuttingResult>(() => JSON.parse(JSON.stringify(op.result ?? EMPTY_RESULT)));   // kroysiz — bo'sh natijadan (qo'lda)
  const [past, setPast] = useState<CuttingResult[]>([]);
  const [future, setFuture] = useState<CuttingResult[]>([]);
  const [mi, setMi] = useState(Math.min(ui.mapIndex, op.result?.maps.length ?? 1));
  const [sel, setSel] = useState<number[][]>([]);                  // ko'p tanlash: manzillar (oxirgisi — asosiy)
  const [partUid, setPartUid] = useState<number | null>(null);
  const [horizontal, setHorizontal] = useState(false);
  const [onlyLeft, setOnlyLeft] = useState(true);              // onlayn kabi: ro'yxatda faqat joylashtirilishi kerak bo'lganlar
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<Mode>("select");
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 } | null>(null);
  const [trimOpen, setTrimOpen] = useState(false);
  const [showCmds, setShowCmds] = useState(false);                  // «Таблица команд» kartalar ro'yxati o'rnida
  const [rev, setRev] = useState<string | null>(null);              // parallel tahrirni aniqlash izi (saqlashda `base`)
  const scope = "editor";
  const m = draft.maps[mi - 1];
  const root = m?.strips?.[0];
  const primary = sel.length ? sel[sel.length - 1] : null;
  const selNode = root && primary ? nodeAt(root, primary) : null;
  const selNodes = useMemo(() => (root ? sel.map((p) => nodeAt(root, p)) : []), [root, sel]);

  useEffect(() => {
    let on = true;
    get<{ rev: string }>(`/projects/${project.id}/operations/${op.id}/edit/rev`).then((r) => { if (on) setRev(r.rev); }, () => undefined);
    return () => { on = false; };
  }, [project.id, op.id]);

  // Shift+A / Shift+W: tugma bosib turilganini kuzatish (bosish paytida rejim tanlanadi)
  const held = useRef({ a: false, w: false });
  const shiftRef = useRef(false);
  // Shift bosib turilganda — detal sharpasi kursor ortidan yuradi; Shift bilan birga Ctrl yoki Alt BOSIB TURILSA — detal
  // aylantirilgan (onlayn yordam: «[SHIFT]+[CTRL]/[ALT]+[Левая кнопка мыши] — режим редактирования с разворотом детали»;
  // bosish tartibi ahamiyatsiz). Alt brauzer menyusiga o'tmasin — hodisa to'xtatiladi.
  const [shiftOn, setShiftOn] = useState(false);
  const [ghostRot, setGhostRot] = useState(false);
  useEffect(() => {
    const set = (e: KeyboardEvent, v: boolean) => {
      if (e.code === "KeyA") held.current.a = v;
      if (e.code === "KeyW") held.current.w = v;
      if (e.key === "Shift") { setShiftOn(v); shiftRef.current = v; }
      if (e.key === "Alt" && (e.shiftKey || shiftRef.current)) e.preventDefault();
      setGhostRot(e.ctrlKey || e.altKey);
    };
    const kd = (e: KeyboardEvent) => set(e, true), ku = (e: KeyboardEvent) => set(e, false);
    const bl = () => { held.current = { a: false, w: false }; setShiftOn(false); setGhostRot(false); };
    window.addEventListener("keydown", kd); window.addEventListener("keyup", ku); window.addEventListener("blur", bl);
    return () => { window.removeEventListener("keydown", kd); window.removeEventListener("keyup", ku); window.removeEventListener("blur", bl); };
  }, []);

  const used = useMemo(() => {
    const u = new Map<string, number>();
    draft.maps.forEach((mm) => mm.placements.forEach((p) => u.set(p.part_id, (u.get(p.part_id) ?? 0) + mm.copies)));
    return u;
  }, [draft]);
  // CSE-002: ro'yxatda zagotovka (pripuskli, kartadagi) o'lchami — kiritilgan qiymat emas — va Ткт ustuni
  const allRows = useMemo(() => {
    const edges = edgeParams(project);
    const allowance = op.cs_cut?.machining_allowance ?? 0;
    return op.parts.map((p, i) => {
      const tot = totalQty(project, p);
      const us = used.get(p.id) ?? 0;
      // no — «Детали» jadvalidagi № (kartadagi raqam bilan bir xil)
      return { p, no: i + 1, tot, used: us, left: tot - us, prod: project.products.find((x) => x.id === p.product_id)?.name ?? "",
        saw: computeSizes(p, project.size_mode, edges, allowance).saw };
    });
  }, [op.parts, op.cs_cut?.machining_allowance, used, project]);
  const rows = useMemo(() => {
    const out = allRows.filter((r) => !onlyLeft || r.left > 0);
    if (!sort) return out;
    const val = (r: (typeof out)[number]): number | string => {
      switch (sort.key) {
        case "uid": return r.no;
        case "product": return r.prod;
        case "length": return r.saw[0];
        case "width": return r.saw[1];
        case "qty": return r.tot;
        case "used": return r.used;
        case "left": return r.left;
        case "grain": return r.p.grain ? 1 : 0;
        default: return r.p.name;
      }
    };
    return [...out].sort((a, b) => {
      const x = val(a), y = val(b);
      const c = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true });
      return c * sort.dir || a.no - b.no;
    });
  }, [allRows, onlyLeft, sort]);
  const totals = useMemo(() => ({ tot: rows.reduce((s, r) => s + r.tot, 0), used: rows.reduce((s, r) => s + r.used, 0),
    left: rows.reduce((s, r) => s + r.left, 0) }), [rows]);
  const cycleSort = (key: SortKey) => setSort((cur) => (cur?.key !== key ? { key, dir: 1 } : cur.dir === 1 ? { key, dir: -1 } : null));

  const act = async (action: Action, keepSel = false, onErr?: (e: ApiError) => boolean): Promise<boolean> => {
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
      else if (action.type === "move_map") setMi({ up: mi - 1, down: mi + 1, first: 1, last: r.maps.length }[String(action.to)] ?? mi);
      return true;
    } catch (e) {
      if (e instanceof ApiError && onErr?.(e)) return false;
      ui.toast(e instanceof ApiError ? e.message : String(e), "error", e instanceof ApiError ? e.details : undefined);
      return false;
    } finally {
      setBusy(false);
    }
  };
  const undo = () => { if (!past.length) return; setFuture([draft, ...future]); setDraft(past[past.length - 1]); setPast(past.slice(0, -1)); setSel([]); };
  const redo = () => { if (!future.length) return; setPast([...past, draft]); setDraft(future[0]); setFuture(future.slice(1)); setSel([]); };

  // ───────── sichqoncha: tanlash, tahrir rejimi (Shift), ko'p tanlash (Ctrl), ramka ─────────
  const onPick = (p: PickInfo) => {
    const path = p.path;
    if (p.button === 2) {                                           // o'ng tugma: o'chirish (tanlov ichida bo'lsa — butun tanlov)
      const inSel = sel.some((s) => samePath(s, path));
      // bo'sh joyga o'ng tugma — uning butun qatori (polosasi) qaytarib olinadi (onlayn tizimdagidek)
      const tgt = root && nodeAt(root, path)?.k === "W" ? path.slice(0, -1) : path;
      const paths = inSel && sel.length > 1 ? sel : tgt.length ? [tgt] : [];
      if (paths.length) void act({ type: "remove", map: mi, ...pathParams(paths) });
      return;
    }
    const node = root ? nodeAt(root, path) : null;
    const row = allRows.find((x) => x.p.uid === partUid);
    const blockMode = held.current.w || mode === "block";
    const multiMode = held.current.a || mode === "multi";
    if (p.shift || mode !== "select") {                              // CSE-020: tahrir rejimi — bosilgan joyga ta'sir qiladi
      if (blockMode && path.length && node && node.k !== "W") { void act({ type: "expand_block", map: mi, path }); return; }
      if (node?.k === "W") {
        if (!row || row.left <= 0) { ui.toast(t("editor.pick_part_first"), "info"); return; }
        const rotated = ghostRot || p.ctrl || p.alt;                   // Shift + Ctrl / Alt bosib turilgan — aylantirib
        if (multiMode) void act({ type: "place_multi", map: mi, path, uid: partUid, rotated });
        else void act({ type: "place", map: mi, path, uid: partUid, rotated, x: p.x, y: p.y });      // kesim yo'nalishi — kursor bo'yicha
        return;
      }
    }
    if (p.ctrl && !p.shift) {                                        // CSE-019: Ctrl+bosish — tanlovga qo'shish / olib tashlash
      if (path.length) setSel(sel.some((s) => samePath(s, path)) ? sel.filter((s) => !samePath(s, path)) : [...sel, path]);
      return;
    }
    if (node?.k === "W" && row && row.left > 0 && !p.shift) {         // qulaylik: detal tanlangan bo'lsa — bosish uni qo'yadi (Alt — burib)
      void act({ type: "place", map: mi, path, uid: partUid, rotated: p.alt });
      return;
    }
    // onlayn tizimdagidek: bo'sh joy bosilsa — uning polosasi tanlanadi (list darajasidagi bo'sh joy — tanlov yo'q)
    if (node?.k === "W" && !p.shift) { setSel(path.length > 1 ? [path.slice(0, -1)] : []); return; }
    setSel([path]);
  };
  // Shift + sudrash: kartadagi detalni boshqa bo'sh joyga (kesish chizig'iga tekislab), Ctrl bilan aylantirib
  const onMove = (path: number[], q: { x: number; y: number }) => {
    const node = root ? nodeAt(root, path) : null;
    if (!node || node.k !== "P") return;
    void act({ type: "relocate", map: mi, path, x: q.x, y: q.y, rotated: Boolean(node.o) !== ghostRot });
  };
  const ghostRow = partUid !== null ? allRows.find((x) => x.p.uid === partUid) : undefined;
  const ghost = (shiftOn || mode !== "select") && ghostRow && ghostRow.left > 0
    ? (ghostRot ? { l: ghostRow.saw[1], w: ghostRow.saw[0] } : { l: ghostRow.saw[0], w: ghostRow.saw[1] }) : null;
  const onBand = (b: BandInfo) => {                                  // CSE-019: ramka — to'liq ichidagi detal/polosalar
    if (!root) return;
    const hit = nodesInRect(root, b);
    if (b.ctrl || b.shift) {
      const merged = [...sel];
      hit.forEach((h) => { if (!merged.some((s) => samePath(s, h))) merged.push(h); });
      setSel(merged);
    } else {
      setSel(hit);
    }
  };
  const selectAll = () => {
    if (!root) return;
    const out: number[][] = [];
    const walk = (n: TreeNode, path: number[]) => (n.c ?? []).forEach((c, i) => {
      if (c.k === "P") out.push([...path, i]); else if (c.k === "C") walk(c, [...path, i]);
    });
    walk(root, []);
    setSel(out);
  };

  /** bo'sh joy tanlangan bo'lsa — uning polosasi */
  const stripOf = (pth: number[]) => (root && nodeAt(root, pth)?.k === "W" ? pth.slice(0, -1) : pth);
  const stepMove = (s: number[][], dir: -1 | 1) => {
    // bitta tanlov: qo'shni element bo'sh joy bo'lmasa — o'rin almashadi, tanlov yangi manzilga o'tadi
    let next: number[][] | null = null;
    if (s.length === 1 && root && s[0].length) {
      const pp = s[0].slice(0, -1), i = s[0][s[0].length - 1];
      const kids = (pp.length ? nodeAt(root, pp) : root)?.c ?? [];
      const nb = kids[i + dir];
      next = nb && nb.k !== "W" ? [[...pp, i + dir]] : s;
    }
    void act({ type: "move", map: mi, ...pathParams(s), to: dir < 0 ? "prev" : "next" }, s.length === 1)
      .then((ok) => { if (ok && next) setSel(next); });
  };
  const needSel = (fn: (paths: number[][]) => void) => () => { if (sel.length) fn(sel); else ui.toast(t("editor.select_first"), "info"); };
  const ops = {
    // onlayn tizimdagidek: «Переместить в начало / в конец» — har bosishda bir qadam, tanlov detal bilan birga ko'chadi
    start: needSel((s) => stepMove(s, -1)),
    end: needSel((s) => stepMove(s, 1)),
    clone: needSel((s) => void act({ type: "clone", map: mi, ...pathParams(s) })),
    // «Развернуть резы»: tanlanmasa — butun list; bo'sh joy tanlansa — uning polosasi (onlayn tizimdagidek)
    rotate: () => {
      let ps = sel.map((s) => (root && nodeAt(root, s)?.k === "W" ? s.slice(0, -1) : s));
      // detallar tanlangan bo'lsa (Ctrl bilan) — ularni o'z ichiga olgan polosa (onlayn tizimdagidek)
      if (root && ps.length && ps.every((s) => nodeAt(root, s)?.k === "P")) {
        let common = ps[0].slice(0, -1);
        for (const s of ps.slice(1)) {
          let k = 0;
          while (k < common.length && k < s.length - 1 && common[k] === s[k]) k++;
          common = common.slice(0, k);
        }
        ps = [common];
      }
      const uniq = ps.filter((s, i) => ps.findIndex((q) => samePath(q, s)) === i);
      const target = uniq.length ? pathParams(uniq) : { path: [] };
      // detallar joyida aylanmasa (onlayn tizim bu holatda hech narsa qilmaydi) — operatordan so'raladi: hududni boshqa
      // yo'nalishda qayta kesish (arra yo'li o'zgaradi, detallar o'rni ham)
      void act({ type: "rotate", map: mi, ...target }, true, (e) => {
        if (e.code !== "rotate_keep") return false;
        void askConfirm(t("editor.rotate_relayout_q"), e.message).then((yes) => {
          if (yes) void act({ type: "rotate", map: mi, ...target, mode: "relayout" }, true);
        });
        return true;
      });
    },
    expand: needSel((s) => void act({ type: "expand", map: mi, path: stripOf(s[s.length - 1]) })),
    narrow: needSel((s) => void act({ type: "narrow", map: mi, path: stripOf(s[s.length - 1]) }, true)),
    // Ctrl+Q (lokal yordam: «Сузить полосы», onlayn: «Расширить полосу»): toraytirish mumkin bo'lsa — toraytiradi, aks holda kengaytiradi
    narrowOrExpand: needSel((s) => {
      const path = stripOf(s[s.length - 1]);
      void act({ type: "narrow", map: mi, path }, true, (e) => {
        if (e.code !== "narrow_none") return false;
        void act({ type: "expand", map: mi, path });
        return true;
      });
    }),
    remove: needSel((s) => void act({ type: "remove", map: mi, ...pathParams(s) })),
    parent: () => { if (primary && primary.length) setSel([...sel.slice(0, -1), primary.slice(0, -1)]); },
    auto: () => { if (partUid !== null) void act({ type: "place_auto", map: mi, uid: partUid }); },
    flip: needSel((s) => void act({ type: "flip", map: mi, ...pathParams(s) })),
    replace: needSel((s) => {
      if (partUid === null) { ui.toast(t("editor.pick_part_first"), "info"); return; }
      void act({ type: "replace", map: mi, path: s[s.length - 1], uid: partUid });
    }),
    swap: () => { if (sel.length === 2) void act({ type: "swap", map: mi, paths: sel }); else ui.toast(t("editor.swap_two"), "info"); },
    block: needSel((s) => void act({ type: "expand_block", map: mi, path: s[s.length - 1] })),
  };
  const moveMap = (to: "up" | "down" | "first" | "last") => { if (m) void act({ type: "move_map", map: mi, to }); };
  const comment = async () => {
    if (!m) return;
    const c = await askText(t("cut.comment"), m.comment, { multiline: true });
    if (c !== null && c !== m.comment) void act({ type: "comment", map: mi, comment: c }, true);
  };
  // «Количество» — karta nusxalari soni (onlayn tugma; avvalgi «С:» maydoni o'rnida)
  const askCopies = async () => {
    if (!m) return;
    const v = await askText(t("editor.qty"), String(m.copies));
    if (v === null) return;
    const c = Math.round(Number(v.replace(",", ".")));
    if (!(c >= 1)) { ui.toast(t("editor.qty_bad"), "warn"); return; }
    if (c !== m.copies) void act({ type: "copies", map: mi, copies: c }, true);
  };
  const applyTrim = (changes: Partial<TrimValues>) => { void act({ type: "map_trim", map: mi, ...changes }); };
  // zichlash burchagi: kartaning o'zi yoki umumiy sozlama (Настройки → «Угол уплотнения раскроя»)
  const appCfg = useAppSettings();
  const defCorner: PackCorner = appCfg.data?.edit_pack_corner ?? "LT";
  const setCorner = (v: string) => { if (m) void act({ type: "pack_corner", map: mi, corner: v || null }, true); };
  const [sheetForNew, setSheetForNew] = useState(op.sheets[0]?.id ?? "");

  const ok = async () => {
    if (op.result?.remnants_saved && !(await askConfirm(t("cut.recut_saved")))) return;
    const q = rev ? `?base=${encodeURIComponent(rev)}` : "";
    const r = await call(() => put<Project>(`/projects/${project.id}/operations/${op.id}/result${q}`, { ...draft, manual: true }));
    if (r) { ui.toast(t("editor.saved"), "ok"); ui.set({ mapIndex: mi }); onClose(r); }
  };
  const cancel = async () => {
    if (past.length && !(await askConfirm(t("editor.discard_q")))) return;
    onClose();
  };

  // F9 (CSE-003): brauzer to'liq ekrani (Ctrl+W/Ctrl+PgUp kabi yorliqlar ham ishlaydi); oyna yopilganda o'zi qo'ygan bo'lsa — qaytariladi
  const enteredFs = useRef(false);
  const toggleFullscreen = () => {
    if (document.fullscreenElement) { exitFullscreen(); enteredFs.current = false; }
    else { enteredFs.current = true; void enterFullscreenWithKeys(); }
  };
  useEffect(() => () => { if (enteredFs.current) exitFullscreen(); }, []);

  useHotkeys(scope, {
    "ctrl+z": undo, "ctrl+y": redo, "ctrl+arrowleft": ops.start, "ctrl+arrowright": ops.end, "ctrl+c": ops.clone,
    "ctrl+r": ops.rotate, "ctrl+q": ops.narrowOrExpand, "delete,shift+delete": ops.remove, "ctrl+f": () => setOnlyLeft(!onlyLeft),
    "pageup,arrowup": () => setMi(Math.max(1, mi - 1)), "pagedown,arrowdown": () => setMi(Math.min(draft.maps.length, mi + 1)),
    home: () => setMi(1), end: () => setMi(Math.max(1, draft.maps.length)),         // CSE-017: birinchi / oxirgi karta
    "ctrl+arrowup": () => moveMap("up"), "ctrl+arrowdown": () => moveMap("down"),   // CSE-016: kartani yuqoriga / pastga
    "ctrl+a": selectAll, f2: () => void comment(), "alt+t": () => setTrimOpen(true), "alt+r": ops.flip,
    f9: toggleFullscreen,
    backspace: ops.parent, "ctrl+enter": () => void ok(),
  });

  const nSel = sel.length;
  const allP = nSel > 0 && selNodes.every((n) => n?.k === "P");
  const th = (key: SortKey, label: string, title?: string, cls?: string) => (
    <th className={cx("sortable", cls)} title={title ?? t("editor.sort_hint")} onClick={() => cycleSort(key)} data-testid={`ed-sort-${key}`}>
      {label}{sort?.key === key && <span className="sort-mark">{sort.dir === 1 ? "▲" : "▼"}</span>}</th>
  );

  return (
    <Modal title={t("editor.title")} onClose={() => void cancel()} full scope={scope} testid="cut-editor"
      headerRight={<>
        <button type="button" className="linkbtn" onClick={() => setHorizontal(!horizontal)}>
          {horizontal ? <Columns2 size={14} /> : <Rows2 size={14} />} {t("editor.horizontal")}</button>
        <button type="button" className="linkbtn" onClick={toggleFullscreen} data-testid="ed-fullscreen"
          title={`${t("editor.fullscreen")} [F9]`}><Maximize size={14} /></button></>}
      footer={<>
        <div className="editor-hint">
          <b>[{t("editor.lmb")}]</b> {t("editor.h_left")}; <b>[Ctrl]</b>+{t("editor.h_ctrl")}; <b>[{t("editor.drag")}]</b> {t("editor.h_band")}; <b>[{t("editor.rmb")}]</b> {t("editor.h_right")};<br />
          <b>[Shift]</b> {t("editor.h_shift")}; <b>[Shift]+[Ctrl]/[Alt]</b> {t("editor.h_alt")}; <b>[Shift]+[A]</b> {t("editor.h_multi")}; <b>[Shift]+[W]</b> {t("editor.h_block")}
        </div>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="editor-ok" />
        <Btn label={t("app.cancel")} onClick={() => void cancel()} />
      </>}>
      <div className={cx("editor", horizontal && "editor-h")}>
        <div className="editor-list">
          <table className="simple ed-parts">
            <thead><tr>{th("uid", "№")}{th("product", t("editor.col.product"))}{th("length", t("pp.length"), t("editor.size_hint"))}
              {th("width", t("pp.width"), t("editor.size_hint"))}{th("qty", t("editor.col.qty"))}{th("used", t("editor.col.used"))}
              {th("left", t("editor.col.left"))}{th("grain", t("editor.col.grain"))}{th("name", t("pp.name"))}</tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.p.id} className={cx(partUid === r.p.uid && "tr-sel", r.left <= 0 && "muted", r.left > 0 && "row-left")}
                  onClick={() => setPartUid(r.p.uid)} onDoubleClick={() => { setPartUid(r.p.uid); void act({ type: "place_auto", map: mi, uid: r.p.uid }); }}
                  data-testid={`ed-part-${r.p.uid}`}>
                  <td>{r.no}</td><td>{r.prod}</td><td className="num" data-testid={`ed-len-${r.p.uid}`}>{fmt(r.saw[0])}</td>
                  <td className="num">{fmt(r.saw[1])}</td>
                  <td className="num">{r.tot}</td><td className="num">{r.used}</td><td className="num" data-testid={`ed-left-${r.p.uid}`}>{r.left}</td>
                  <td className="center" data-testid={`ed-grain-${r.p.uid}`}>{r.p.grain ? "✓" : ""}</td><td>{r.p.name}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr data-testid="ed-totals"><td colSpan={4}>{t("editor.totals")}</td><td className="num">{totals.tot}</td>
              <td className="num">{totals.used}</td><td className="num">{totals.left}</td><td colSpan={2} /></tr></tfoot>
          </table>
        </div>
        <div className="editor-main">
          {/* onlayn tartib: Отменить, Вернуть | Добавить / Удалить карту, Количество, Торцовка | В начало, В конец |
              Клонировать, Развернуть резы, Расширить полосу | Удалить | Фильтр | Вверх, Вниз (karta) | Справка;
              bizning qo'shimchalar (list tanlash, izoh, avtomatik joylash, burish, almashtirish, rejimlar, kartalar) — oxirida */}
          <div className="toolbar">
            <IconBtn icon={Undo2} title={`${t("menu.undo")} [CTRL]+[Z]`} onClick={undo} disabled={!past.length} />
            <IconBtn icon={Redo2} title={`${t("menu.redo")} [CTRL]+[Y]`} onClick={redo} disabled={!future.length} />
            <Sep />
            <IconBtn icon={FilePlus2} title={t("editor.add_map")} onClick={() => void act({ type: "add_map", sheet_id: sheetForNew })} testid="ed-add-map" />
            <IconBtn icon={FileX2} title={t("editor.delete_map")} disabled={!m}
              onClick={async () => { if (await askConfirm(t("editor.delete_map_q"))) void act({ type: "delete_map", map: mi }); }} />
            <IconBtn icon={Hash} title={`${t("editor.qty")}${m ? `: ${m.copies}` : ""}`} onClick={() => void askCopies()} disabled={!m} testid="ed-qty" />
            <IconBtn icon={SquareDashed} title={`${t("editor.trim_title")} [ALT]+[T]`} onClick={() => setTrimOpen(true)} disabled={!m}
              active={!!m && (m.trim_length != null || m.trim_width != null || m.end_offset_bottom != null || m.end_offset_right != null)}
              testid="ed-trim" />
            <Sep />
            <IconBtn icon={ArrowLeftToLine} title={`${t("editor.to_start")} [CTRL]+[LEFT]`} onClick={ops.start} disabled={!nSel} />
            <IconBtn icon={ArrowRightToLine} title={`${t("editor.to_end")} [CTRL]+[RIGHT]`} onClick={ops.end} disabled={!nSel} />
            <Sep />
            <IconBtn icon={CopyPlus} title={`${t("app.clone")} [CTRL]+[C]`} onClick={ops.clone} disabled={!nSel} />
            <IconBtn icon={RotateCw} title={`${t("editor.rotate")} [CTRL]+[R]`} onClick={ops.rotate} testid="ed-rotate"
              disabled={!m} />
            <IconBtn icon={Expand} title={`${t("editor.expand")} [CTRL]+[Q]`} onClick={ops.expand} disabled={!selNode || selNode.k === "P"} testid="ed-expand" />
            <IconBtn icon={Shrink} title={`${t("editor.narrow")} [CTRL]+[Q]`} onClick={ops.narrow} disabled={!selNode || selNode.k === "P"} testid="ed-narrow" />
            <Sep />
            <IconBtn icon={Trash} title={`${t("app.delete")} [DEL]`} onClick={ops.remove} disabled={!nSel} color="#c0392b" testid="ed-delete" />
            <Sep />
            <IconBtn icon={Funnel} title={`${t("editor.only_left")} [CTRL]+[F]`} active={onlyLeft} onClick={() => setOnlyLeft(!onlyLeft)} testid="ed-only-left" />
            <Sep />
            <IconBtn icon={ChevronsUp} title={`${t("editor.map_up")} [CTRL]+[UP]`} onClick={() => moveMap("up")} disabled={!m || mi <= 1} testid="ed-map-up" />
            <IconBtn icon={ChevronsDown} title={`${t("editor.map_down")} [CTRL]+[DOWN]`} onClick={() => moveMap("down")}
              disabled={!m || mi >= draft.maps.length} testid="ed-map-down" />
            <Sep />
            <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} [F1]`} onClick={() => ui.set({ section: "help" })} testid="ed-help" />
            <Sep />
            <span title={t("editor.sheet_for_new")}><Sel value={sheetForNew} width={130} onChange={setSheetForNew}
              options={op.sheets.map((s) => ({ value: s.id, label: `${s.length}×${s.width}${s.is_remnant ? " ⟲" : ""}` }))} /></span>
            <span title={t("editor.corner_hint")}><Sel value={m?.pack_corner ?? ""} width={150} onChange={setCorner} testid="ed-corner"
              disabled={!m} options={[{ value: "", label: t("editor.corner_default", { c: t(`editor.c.${defCorner}`) }) },
                ...(["LT", "RT", "LB", "RB"] as const).map((c) => ({ value: c, label: `${t("editor.corner")}: ${t(`editor.c.${c}`)}` }))]} /></span>
            <IconBtn icon={MessageSquare} title={`${t("cut.comment")} [F2]`} onClick={() => void comment()} disabled={!m} active={!!m?.comment} testid="ed-comment" />
            <IconBtn icon={Wand} title={t("editor.auto_place")} onClick={ops.auto} disabled={partUid === null} testid="ed-auto" />
            <IconBtn icon={RefreshCw} title={`${t("editor.flip")} [ALT]+[R]`} onClick={ops.flip} disabled={!allP} testid="ed-flip" />
            <IconBtn icon={Replace} title={t("editor.replace")} onClick={ops.replace} disabled={!selNode || selNode.k !== "P" || partUid === null} testid="ed-replace" />
            <IconBtn icon={ArrowLeftRight} title={t("editor.swap")} onClick={ops.swap} disabled={nSel !== 2} testid="ed-swap" />
            <IconBtn icon={ListChecks} title={`${t("editor.select_all")} [CTRL]+[A]`} onClick={selectAll} disabled={!m} testid="ed-select-all" />
            <IconBtn icon={Grid3x3} title={`${t("editor.mode_multi")} [SHIFT]+[A]`} active={mode === "multi"} testid="ed-mode-multi"
              onClick={() => setMode(mode === "multi" ? "select" : "multi")} />
            <IconBtn icon={Boxes} title={`${t("editor.mode_block")} [SHIFT]+[W]`} active={mode === "block"} testid="ed-mode-block"
              onClick={() => setMode(mode === "block" ? "select" : "block")} />
          </div>
          {/* onlayn tizimdagidek: kartalar ro'yxati ustida «Таблица команд» ↔ «Таблица карт» almashtirgichi */}
          <button type="button" className="linkbtn ed-cmds-toggle" onClick={() => setShowCmds(!showCmds)} data-testid="ed-toggle-commands">
            {showCmds ? <LayoutGrid size={14} /> : <List size={14} />} {showCmds ? t("cut.maps_table") : t("cut.commands")}</button>
          {showCmds && m ? (
            <div className="scroll ed-cmds">
              <table className="simple cmds" data-testid="ed-commands-table">
                <thead><tr><th>№</th><th>{t("cut.cmd.code")}</th><th>{t("cut.cmd.size")}</th><th>{t("cut.cmd.count")}</th><th>{t("cut.cmd.ref")}</th></tr></thead>
                <tbody>
                  {m.commands.map((c, i) => (
                    <tr key={i} className={`cmd-${c.code}`}>
                      <td>{i + 1}</td><td>{c.code}{c.level}</td><td className="num">{fmt(c.size)}</td>
                      <td className="num">{c.code === "T" ? "" : c.count || 1}</td><td>{c.ref}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="thumbs-row">
            {draft.maps.map((mm) => (
              <button key={mm.index} type="button" className={cx("thumb small", mm.index === mi && "thumb-active")}
                onClick={() => { setMi(mm.index); setSel([]); }}>
                <MapView map={mm} project={project} op={op} thumb className="thumbsvg" />
                <span>№{mm.index} C:{mm.copies}</span>
              </button>
            ))}
          </div>}
          {m ? (
            <>
              <div className="statusline" data-testid="ed-status">
                {shownIndicators(ui).map((k) => (
                  <span key={k} title={t(`cut.ind.${k}`)} style={{ flexGrow: indWidth(k, ui.cutIndWidths) }}>{k === "num" ? "№" : k}: <b>{indicator(k, m, draft, draft.maps.length)}</b></span>))}
                {draft.unplaced.length > 0 && <span className="warn">{t("cut.unplaced", { n: draft.unplaced.length })}</span>}
                {mode !== "select" && <span className="editor-mode" data-testid="ed-mode">{t(mode === "multi" ? "editor.mode_multi" : "editor.mode_block")}</span>}
                {nSel > 1 && <span className="editor-sel-count" data-testid="ed-sel-count">{t("editor.selected", { n: nSel })}</span>}
                {nSel === 1 && selNode && <span className="muted">{selNode.k === "P" ? `${t("editor.sel_part")} ${selNode.u}` :
                  selNode.k === "W" ? t("editor.sel_free") : t("editor.sel_strip")}: {fmt(selNode.l)}×{fmt(selNode.w)}</span>}
                <span className="nav cut-nav">
                  <IconBtn icon={ChevronFirst} title={`${t("cut.first")} [HOME]`} onClick={() => setMi(1)} disabled={mi <= 1} />
                  <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} [UP]`} onClick={() => setMi(Math.max(1, mi - 1))} disabled={mi <= 1} />
                  <IconBtn icon={ChevronRight} title={`${t("cut.next")} [DOWN]`} onClick={() => setMi(Math.min(draft.maps.length, mi + 1))}
                    disabled={mi >= draft.maps.length} testid="ed-map-next" />
                  <IconBtn icon={ChevronLast} title={`${t("cut.last")} [END]`} onClick={() => setMi(draft.maps.length)} disabled={mi >= draft.maps.length} />
                </span>
              </div>
              <div className={cx("editor-map", busy && "is-busy")}>
                {/* g'ildirak — kattalashtirish (onlayn tahrirdagidek), o'rta tugma — surish; chap tugma — tanlash / ramka / sudrash */}
                <MapViewport resetKey={`${op.id}-${mi}`} middleOnly testid="editor-viewport">
                  <MapView map={m} project={project} op={op} selectedPaths={sel} onPick={onPick} onBand={onBand} testid="editor-map"
                    ghost={ghost} ghostRot={ghostRot} onMove={onMove} wasteDims
                    highlightPartId={partUid !== null ? op.parts.find((p) => p.uid === partUid)?.id ?? null : null} />
                </MapViewport>
              </div>
            </>
          ) : <div className="empty">{t("editor.no_maps")}</div>}
        </div>
      </div>
      {trimOpen && m && <CutTrimDialog op={op} map={m} onApply={applyTrim} onClose={() => setTrimOpen(false)} />}
    </Modal>
  );
}
