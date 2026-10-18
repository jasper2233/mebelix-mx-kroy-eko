// Etiketka vizual redaktori (LB-C, W15): sahifa mm masshtabida, elementlarni sichqoncha bilan tanlash/ko'chirish/o'lcham o'zgartirish,
// xossalar paneli, qatlamlar, o'zgaruvchilar, bekor qilish/qaytarish, klaviatura. Ma'lumot modeli — W4 JSON shablon (o'zgarmagan).
// Jonli ko'rinish serverda (`POST /label-templates/design`): ifodalar faqat services/expr.py da hisoblanadi (ikkinchi dvigatel yo'q).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  AlignHorizontalJustifyCenter, AlignHorizontalJustifyEnd, AlignHorizontalJustifyStart, AlignVerticalJustifyCenter, AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart, BringToFront, ChevronDown, ChevronUp, CopyPlus, FilePlus, GitBranch, Grid3x3, Group, Magnet,
  Maximize2, Minimize2, Plus, Redo2, Ruler, Scan, SendToBack, Trash, Undo2, Ungroup, ZoomIn, ZoomOut,
} from "lucide-react";
import { post } from "../../../api/client";
import { call, qc } from "../../../api/hooks";
import type { LBParams, Project } from "../../../api/types";
import { scopeProps, useHotkeys } from "../../../shared/hotkeys";
import { askConfirm, askText, showError } from "../../../shared/dialogs";
import { useUI } from "../../../store/ui";
import { Dropdown, IconBtn, Sel, Tabs, cx } from "../../../shared/ui";
import {
  DEFAULT_TEMPLATE_ID, NEW_ELEMENTS, cloneTpl, lbSize, useTemplate, useTemplates,
  type LabelTemplate, type TplElement, type TplMeta,
} from "../labelsApi";
import { LabelFileTools } from "../LabelImport";
import { DesignCanvas, type ElBoxes } from "./DesignCanvas";
import { canonJson, useDesignPreview, type SampleKind } from "./designerApi";
import { Inspector } from "./Inspector";
import { PagePanel } from "./PagePanel";
import { ExprModal, LayersPanel, VarsPanel } from "./SidePanels";
import {
  MAX_DEPTH, MAX_ELEMENTS, addTo, alignDeltas, applyResize, clamp, cloneEl, countElements, depthOf, getEl, groupSiblings, matInv, matVec, moveVertex, normalizeSel,
  parsePathKey, pathKey, r3, removeAt, reorderSiblings, resizeMode, samePath, translateEl, unionBox, unwrap,
  type AlignKind, type ElPath,
} from "./model";
import "./designer.css";
import type { Lang } from "../../../i18n/lang";

interface Snap { doc: LabelTemplate; sel: string[] }
type SideTab = "props" | "layers";
const PAD = 36;
const HISTORY_MAX = 100;
const ADD_KEYS = ["text", "rect", "line", "qr", "code128", "polyline", "arc", "ellipse", "image", "part", "edges", "group", "if", "var"] as const;
const GRIDS = [0.5, 1, 2, 5];
let clipboard: TplElement[] = [];            // ichki bufer (redaktor qayta ochilganda ham saqlanadi)

interface Props {
  project: Project; lb: LBParams; lang: Lang;
  onChange: (p: Partial<LBParams>) => void | Promise<unknown>;
  actions?: ReactNode;                       // LabelsEditor: «Печать», «Скачать ZPL» …
}

export function LabelDesigner({ project, lb, lang, onChange, actions }: Props) {
  const { t } = useTranslation();
  const toast = useUI((s) => s.toast);
  const tplId = lb.template_id ?? DEFAULT_TEMPLATE_ID;
  const list = useTemplates(lang);
  const base = useTemplate(lb.template ? null : tplId, lang);
  const current = (lb.template as unknown as LabelTemplate | null) ?? base.data?.template ?? null;
  const meta = list.data?.find((m) => m.id === tplId);

  // ───────── ishchi nusxa, tarix, saqlash ─────────
  const [doc, setDoc] = useState<LabelTemplate | null>(null);
  const docRef = useRef<LabelTemplate | null>(null);
  const [sel, setSelState] = useState<string[]>([]);
  const selRef = useRef<string[]>([]);
  const past = useRef<Snap[]>([]);
  const future = useRef<Snap[]>([]);
  const [, setTick] = useState(0);
  const merge = useRef<{ key: string; at: number }>({ key: "", at: 0 });
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toSave = useRef<LabelTemplate | null>(null);
  const inflight = useRef(0);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  const bump = () => setTick((n) => n + 1);

  const setSel = (keys: string[]) => { selRef.current = keys; setSelState(keys); };
  const adopt = (tpl: LabelTemplate) => {
    const d = cloneTpl(tpl);
    docRef.current = d;
    setDoc(d);
    past.current = []; future.current = [];
    setSel([]);
    bump();
  };
  const curCanon = canonJson(current);
  useEffect(() => {     // tashqaridan o'zgardi (kutubxonadan tanlash, import, boshqa operatsiya) — ishchi nusxani almashtiramiz
    if (!current) return;
    if (inflight.current > 0 || saveTimer.current) return;
    if (canonJson(docRef.current) === curCanon) return;
    adopt(current);
  }, [curCanon]); // eslint-disable-line react-hooks/exhaustive-deps

  const flushSave = () => {
    if (saveTimer.current) { clearTimeout(saveTimer.current); saveTimer.current = null; }
    const d = toSave.current;
    if (!d) return;
    toSave.current = null;
    inflight.current += 1;
    void Promise.resolve(onChangeRef.current({ template: d as unknown as Record<string, unknown> })).finally(() => { inflight.current -= 1; });
  };
  const flushRef = useRef(flushSave);
  flushRef.current = flushSave;
  useEffect(() => () => flushRef.current(), []);
  const scheduleSave = (d: LabelTemplate) => {
    toSave.current = d;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(flushSave, 350);
  };

  /** Hujjatni o'zgartirish: `mut` nusxani tahrirlaydi (ixtiyoriy: yangi tanlovni qaytaradi). `merge` — yaqin vaqtdagi bir xil kalitli o'zgarishlar bitta bekor qilish qadami. */
  const commit = (mut: (d: LabelTemplate) => string[] | void, opts: { merge?: string } = {}) => {
    const cur = docRef.current;
    if (!cur) return;
    const d = cloneTpl(cur);
    const ns = mut(d);
    if (countElements(d.elements) > MAX_ELEMENTS || depthOf(d.elements) > MAX_DEPTH) { toast(t("lbd.limit", { n: MAX_ELEMENTS, d: MAX_DEPTH }), "error"); return; }
    const now = Date.now();
    const same = !!opts.merge && merge.current.key === opts.merge && now - merge.current.at < 900;
    if (!same) { past.current.push({ doc: cur, sel: selRef.current }); if (past.current.length > HISTORY_MAX) past.current.shift(); }
    merge.current = { key: opts.merge ?? "", at: now };
    future.current = [];
    docRef.current = d;
    setDoc(d);
    if (Array.isArray(ns)) setSel(ns);
    scheduleSave(d);
    bump();
  };
  const undo = () => {
    const s = past.current.pop();
    if (!s || !docRef.current) return;
    future.current.push({ doc: docRef.current, sel: selRef.current });
    docRef.current = s.doc; setDoc(s.doc); setSel(s.sel); scheduleSave(s.doc); merge.current = { key: "", at: 0 }; bump();
  };
  const redo = () => {
    const s = future.current.pop();
    if (!s || !docRef.current) return;
    past.current.push({ doc: docRef.current, sel: selRef.current });
    docRef.current = s.doc; setDoc(s.doc); setSel(s.sel); scheduleSave(s.doc); merge.current = { key: "", at: 0 }; bump();
  };

  // ───────── jonli ko'rinish ─────────
  const [kind, setKind] = useState<SampleKind>(lb.source === "user" ? "user" : lb.source === "products" ? "product" : "part");
  const [dataSrc, setDataSrc] = useState<"sample" | "project">("sample");
  const [rowIdx, setRowIdx] = useState(0);
  const design = useDesignPreview({
    tpl: doc, params: lb.params, width: lbSize(lb).w, height: lbSize(lb).h, kind, fields: lb.fields,      // A4: hisoblangan o'lcham
    row: kind === "user" && lb.data.length > 0 ? lb.data[0] : null,
    projectId: dataSrc === "project" ? project.id : null, lb: dataSrc === "project" ? lb : null, index: rowIdx, lang,
  });
  const dres = design.data;
  const errors = dres?.errors ?? [];
  const errorKeys = useMemo(() => new Set(errors.map((e) => e.path).filter(Boolean)), [errors]);
  const boxesRef = useRef<ElBoxes>(new Map());

  // ───────── ko'rinish: masshtab, to'r, yopishish ─────────
  const stageRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState<{ fit: boolean; scale: number }>({ fit: true, scale: 8 });
  const [stageSize, setStageSize] = useState({ w: 800, h: 500 });
  const [showGrid, setShowGrid] = useState(true);
  const [snap, setSnap] = useState(true);
  const [guides, setGuides] = useState(true);
  const [grid, setGrid] = useState(1);
  const [max, setMax] = useState(false);
  const [cursor, setCursor] = useState<[number, number] | null>(null);
  const [side, setSide] = useState<SideTab>("props");
  const [varsOpen, setVarsOpen] = useState(true);
  const [branch, setBranch] = useState<"then" | "else">("then");
  const [fx, setFx] = useState<{ initial: string; apply: (v: string) => void } | null>(null);
  const imgRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setStageSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setStageSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, [!!doc, max]);
  const { w: W, h: H } = lbSize(lb);
  const fitScale = clamp(Math.min((stageSize.w - 2 * PAD) / W, (stageSize.h - 2 * PAD) / H), 1.5, 40);
  const scale = zoom.fit ? fitScale : zoom.scale;
  const zoomTo = (s: number) => setZoom({ fit: false, scale: clamp(s, 1.5, 60) });
  useEffect(() => {      // Ctrl + g'ildirak — masshtab
    const el = stageRef.current;
    if (!el) return;
    const h = (e: WheelEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault();
      setZoom((z) => ({ fit: false, scale: clamp((z.fit ? fitScale : z.scale) * (e.deltaY < 0 ? 1.15 : 1 / 1.15), 1.5, 60) }));
    };
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, [fitScale, !!doc]); // eslint-disable-line react-hooks/exhaustive-deps

  // ───────── tanlov va asosiy amallar ─────────
  const paths = (keys = selRef.current): ElPath[] => normalizeSel(keys.map(parsePathKey));
  const keysOf = (ps: ElPath[]): string[] => ps.map(pathKey);
  const local = (key: string, dx: number, dy: number): [number, number] => {
    const b = boxesRef.current.get(key);
    return b ? matVec(matInv(b.m), dx, dy) : [dx, dy];
  };

  const select = (keys: string[], additive = false) => {
    if (additive) {
      const cur = selRef.current;
      const k = keys[0];
      setSel(cur.includes(k) ? cur.filter((x) => x !== k) : [...cur, k]);
    } else setSel(keys);
  };
  const del = () => {
    const ps = paths();
    if (!ps.length) return;
    commit((d) => { for (const p of [...ps].reverse()) removeAt(d, p); return []; });
  };
  const duplicate = () => {
    const ps = paths();
    if (!ps.length) return;
    commit((d) => {
      const out: ElPath[] = [];
      for (const p of [...ps].reverse()) {
        const el = getEl(d, p);
        if (!el) continue;
        const c = cloneEl(el);
        const [lx, ly] = local(pathKey(p), 2, 2);
        translateEl(c, r3(lx), r3(ly));
        const par = p.slice(0, -1);
        const i = p[p.length - 1] as number;
        const host = par.length ? getEl(d, par.slice(0, -1)) : null;
        const lst = par.length ? (host?.[par[par.length - 1] as string] as TplElement[]) : d.elements;
        lst.splice(i + 1, 0, c);
      }
      for (const p of ps) {                                   // yangi yo'llar: o'zidan oldingi tanlangan aka-ukalar soni bo'yicha siljigan
        const par = p.slice(0, -1);
        const i = p[p.length - 1] as number;
        const before = ps.filter((q) => samePath(q.slice(0, -1), par) && (q[q.length - 1] as number) < i).length;
        out.push([...par, i + 1 + before]);
      }
      return keysOf(out);
    });
  };
  const copy = () => { clipboard = paths().map((p) => getEl(docRef.current!, p)).filter((e): e is TplElement => !!e).map(cloneEl); if (clipboard.length) toast(t("lbd.copied", { n: clipboard.length }), "ok"); };
  const paste = () => {
    if (!clipboard.length) return;
    const items = clipboard.map(cloneEl);
    commit((d) => {
      const ps = paths();
      const last = ps[ps.length - 1];
      const par = last ? last.slice(0, -1) : [];
      const idx = last ? (last[last.length - 1] as number) + 1 : undefined;
      const out: ElPath[] = [];
      items.forEach((el, i) => {
        translateEl(el, 2, 2);
        const host = par.length >= 2 ? par.slice(0, -1) : null;
        const key = (par.length >= 2 ? par[par.length - 1] : "elements") as "elements" | "then" | "else";
        out.push(addTo(d, host, key, el, idx === undefined ? undefined : idx + i));
      });
      return keysOf(out);
    });
  };
  const selectAll = () => { const d = docRef.current; if (d) setSel(d.elements.map((_e, i) => pathKey([i]))); };
  const nudge = (dx: number, dy: number) => {
    const ps = paths();
    if (!ps.length) return;
    commit((d) => { for (const p of ps) { const el = getEl(d, p); if (!el) continue; const [lx, ly] = local(pathKey(p), dx, dy); translateEl(el, r3(lx), r3(ly)); } },
      { merge: `nudge:${selRef.current.join(",")}` });
  };
  const doGroup = (kindOf: "group" | "if") => {
    const ps = paths();
    if (!ps.length) return;
    let ok = true;
    commit((d) => { const np = groupSiblings(d, ps, kindOf); if (!np) { ok = false; return undefined; } return [pathKey(np)]; });
    if (!ok) toast(t("lbd.group_siblings"), "error");
  };
  const doUnwrap = () => {
    const ps = paths();
    if (ps.length !== 1) return;
    let ok = true;
    commit((d) => { const r = unwrap(d, ps[0]); if (!r) { ok = false; return undefined; } return keysOf(r); });
    if (!ok) toast(t("lbd.unwrap_fail"), "error");
  };
  const order = (op: "forward" | "backward" | "front" | "back") => {
    const ps = paths();
    if (!ps.length) return;
    commit((d) => keysOf(reorderSiblings(d, ps, op)));
  };
  const align = (kindOf: AlignKind) => {
    const ps = paths();
    const items = ps.map((p) => ({ p, b: boxesRef.current.get(pathKey(p)) })).filter((x): x is { p: ElPath; b: NonNullable<typeof x.b> } => !!x.b);
    if (items.length < 2) return;
    const deltas = alignDeltas(items.map((x) => x.b.hull), kindOf);
    commit((d) => {
      items.forEach((it, i) => {
        const el = getEl(d, it.p);
        if (!el) return;
        const [lx, ly] = local(pathKey(it.p), deltas[i][0], deltas[i][1]);
        translateEl(el, r3(lx), r3(ly));
      });
    });
  };

  const addElement = (key: string, src?: string) => {
    const proto = key === "image" ? { t: "image", x: 2, y: 2, w: 12, h: 12, src: src ?? "" } : NEW_ELEMENTS[key];
    if (!proto) return;
    const el = cloneEl(proto);
    commit((d) => {
      const off = (d.elements.length % 6) * 2;
      if (key !== "group" && key !== "var" && key !== "if") translateEl(el, off, off);
      const ps = paths();
      const host = ps.length === 1 ? getEl(d, ps[0]) : null;
      let np: ElPath;
      if (host && (host.t === "group" || host.t === "if")) np = addTo(d, ps[0], host.t === "group" ? "elements" : branch, el);
      else np = addTo(d, null, "elements", el);
      return [pathKey(np)];
    });
    setSide("props");
  };
  const onImageFile = (f: File | undefined) => {
    if (!f) return;
    if (!/^image\/(png|jpeg)$/.test(f.type)) { showError(new Error(t("lbd.img_type"))); return; }
    if (f.size > 200 * 1024) { showError(new Error(t("lbd.img_size"))); return; }
    const rd = new FileReader();
    rd.onload = () => addElement("image", String(rd.result));
    rd.readAsDataURL(f);
    if (imgRef.current) imgRef.current.value = "";
  };

  // ───────── kanvasdan keladigan o'zgarishlar ─────────
  const onMove = (moves: { key: string; dx: number; dy: number }[]) => {
    commit((d) => {
      for (const m of moves) { const el = getEl(d, parsePathKey(m.key)); if (el) translateEl(el, r3(m.dx), r3(m.dy)); }
    });
  };
  const onResize = (key: string, o: { x: number; y: number; w: number; h: number }, n: { x: number; y: number; w: number; h: number }) => {
    commit((d) => { const el = getEl(d, parsePathKey(key)); if (el) applyResize(el, o, n); });
  };
  const onVertex = (key: string, idx: number, dx: number, dy: number) => {
    commit((d) => { const el = getEl(d, parsePathKey(key)); if (el) moveVertex(el, idx, r3(dx), r3(dy)); });
  };

  // ───────── klaviatura ─────────
  const st = 0.5;
  useHotkeys("label-designer", {
    "delete,backspace": del, "ctrl+d": duplicate, "ctrl+z": undo, "ctrl+y,ctrl+shift+z": redo, "ctrl+a": selectAll, "ctrl+c": copy, "ctrl+v": paste,
    escape: () => setSel([]),
    arrowleft: () => nudge(-st, 0), arrowright: () => nudge(st, 0), arrowup: () => nudge(0, -st), arrowdown: () => nudge(0, st),
    "shift+arrowleft": () => nudge(-10 * st, 0), "shift+arrowright": () => nudge(10 * st, 0), "shift+arrowup": () => nudge(0, -10 * st), "shift+arrowdown": () => nudge(0, 10 * st),
    "alt+arrowleft": () => nudge(-0.1, 0), "alt+arrowright": () => nudge(0.1, 0), "alt+arrowup": () => nudge(0, -0.1), "alt+arrowdown": () => nudge(0, 0.1),
    "ctrl+g": () => doGroup("group"), "ctrl+shift+g": doUnwrap, "ctrl+]": () => order("forward"), "ctrl+[": () => order("backward"),
    "ctrl+shift+]": () => order("front"), "ctrl+shift+[": () => order("back"),
    "ctrl+0": () => setZoom({ fit: true, scale }), "ctrl+=": () => zoomTo(scale * 1.25), "ctrl+-": () => zoomTo(scale / 1.25),
  });

  // ───────── kutubxona ─────────
  const refreshLib = () => {
    void qc.invalidateQueries({ queryKey: ["label-templates"] });
    void qc.invalidateQueries({ queryKey: ["label-template"] });
  };
  const pick = async (id: string) => {
    const m = list.data?.find((x) => x.id === id);
    if (lb.template && id !== tplId && !(await askConfirm(t("lbd.replace_q"), t("lbd.replace_text"), { ok: t("lbd.replace_ok"), danger: true }))) return;
    flushSave();
    if (m && (m.kind === "part" || m.kind === "waste" || m.kind === "product")) setKind(m.kind);        // shablon qaysi qator turi uchun — namuna ham shunday
    void onChange({ template_id: id, template: null, params: {}, ...(m ? { width_mm: m.size.w, height_mm: m.size.h } : {}) });
  };
  const saveLib = async () => {
    const d = docRef.current;
    if (!d) return;
    const name = await askText(t("lb.tpl_save"), d.name || meta?.name || "", { text: t("lb.tpl_name") });
    if (!name) return;
    const r = await call(() => post<{ id: number }>("/settings/label_template", { name, data: { ...d, name } }));
    if (r) {
      refreshLib();
      flushSave();
      void onChange({ template_id: `profile:${r.id}`, template: null, params: {} });
      toast(t("app.saved"), "ok");
    }
  };

  // ───────── ko'rinish ─────────
  const selPaths = paths(sel);
  const single = selPaths.length === 1 ? selPaths[0] : null;
  const singleEl = single && doc ? getEl(doc, single) : null;
  const total = doc ? countElements(doc.elements) : 0;
  const selHull = (() => {
    const hs = sel.map((k) => boxesRef.current.get(k)?.hull).filter((b): b is NonNullable<typeof b> => !!b);
    return hs.length ? unionBox(hs) : null;
  })();
  const ctxValues = useMemo(() => ({ ...(dres?.values ?? {}), ...(dres?.tpl_values ?? {}) }), [dres]);
  const canUndo = past.current.length > 0, canRedo = future.current.length > 0;
  const hasSel = selPaths.length > 0;
  const sameParent = selPaths.length > 1 && selPaths.every((p) => samePath(p.slice(0, -1), selPaths[0].slice(0, -1)));
  const openFx = (cur: string, apply: (v: string) => void) => setFx({ initial: cur, apply });

  if (!doc) {
    return <div className="lbd lbd-loading" data-testid="lbd-root"><div className="muted">{t("app.loading")}</div></div>;
  }
  const kinds: { value: SampleKind; label: string }[] = [
    { value: "part", label: t("lbd.kind.part") }, { value: "waste", label: t("lbd.kind.waste") },
    { value: "product", label: t("lbd.kind.product") }, { value: "user", label: t("lbd.kind.user") }];
  const meta2 = dres?.meta;

  return (
    <div className={cx("lbd", max && "lbd-max")} {...scopeProps("label-designer")} data-testid="lbd-root">
      <div className="lbd-top">
        <div className="toolbar lbd-tb">
          <Sel<string> value={tplId} width={230} testid="lbd-tpl-select" onChange={(id) => void pick(id)}
            options={(list.data ?? [{ id: DEFAULT_TEMPLATE_ID, name: "…" } as TplMeta]).map((m) => ({ value: m.id, label: (m.builtin ? "★ " : "") + m.name }))} />
          <IconBtn icon={FilePlus} title={t("lb.tpl_save")} onClick={() => void saveLib()} testid="lbd-tpl-save" />
          {lb.template && <button type="button" className="btn btn-sm" data-testid="lbd-tpl-reset" title={t("lb.tpl_copy")}
            onClick={async () => {
              if (!(await askConfirm(t("lbd.replace_q"), t("lbd.replace_text"), { ok: t("lbd.replace_ok"), danger: true }))) return;
              flushSave(); void onChange({ template: null, params: {} });
            }}>{t("lb.tpl_reset")}</button>}
          <LabelFileTools current={doc} lb={lb} lang={lang} refreshLib={refreshLib} onImported={(_id, p) => void onChange(p)} />
          <span className="grow" />
          {actions}
          <IconBtn icon={max ? Minimize2 : Maximize2} title={t(max ? "lbd.restore" : "lbd.maximize")} onClick={() => setMax(!max)} testid="lbd-max" active={max} />
        </div>
        <div className="toolbar lbd-tb">
          <IconBtn icon={Undo2} title={`${t("menu.undo")} (Ctrl+Z)`} onClick={undo} disabled={!canUndo} testid="lbd-undo" />
          <IconBtn icon={Redo2} title={`${t("menu.redo")} (Ctrl+Y)`} onClick={redo} disabled={!canRedo} testid="lbd-redo" />
          <span className="tsep" />
          <Dropdown icon={Plus} title={t("lb.add")} label={t("lb.add")} testid="lbd-add"
            items={ADD_KEYS.map((k) => ({ label: t(`lb.el.${k}`), onClick: () => (k === "image" ? imgRef.current?.click() : addElement(k)), testid: `lbd-add-${k}` }))} />
          <input ref={imgRef} type="file" accept="image/png,image/jpeg" hidden data-testid="lbd-add-image-file" onChange={(e) => onImageFile(e.target.files?.[0])} />
          <IconBtn icon={CopyPlus} title={`${t("lbd.dup")} (Ctrl+D)`} onClick={duplicate} disabled={!hasSel} testid="lbd-dup" />
          <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={del} disabled={!hasSel} testid="lbd-del" color="#c0392b" />
          <span className="tsep" />
          <IconBtn icon={Group} title={`${t("lbd.group")} (Ctrl+G)`} onClick={() => doGroup("group")} disabled={!hasSel} testid="lbd-group" />
          <IconBtn icon={GitBranch} title={t("lbd.wrap_if")} onClick={() => doGroup("if")} disabled={!hasSel} testid="lbd-wrap-if" />
          <IconBtn icon={Ungroup} title={`${t("lbd.unwrap")} (Ctrl+Shift+G)`} onClick={doUnwrap} disabled={!(singleEl && (singleEl.t === "group" || singleEl.t === "if"))} testid="lbd-unwrap" />
          <span className="tsep" />
          <IconBtn icon={BringToFront} title={`${t("lbd.front")} (Ctrl+Shift+])`} onClick={() => order("front")} disabled={!hasSel} testid="lbd-front" />
          <IconBtn icon={ChevronUp} title={`${t("lbd.forward")} (Ctrl+])`} onClick={() => order("forward")} disabled={!hasSel} testid="lbd-forward" />
          <IconBtn icon={ChevronDown} title={`${t("lbd.backward")} (Ctrl+[)`} onClick={() => order("backward")} disabled={!hasSel} testid="lbd-backward" />
          <IconBtn icon={SendToBack} title={`${t("lbd.back")} (Ctrl+Shift+[)`} onClick={() => order("back")} disabled={!hasSel} testid="lbd-back" />
          <Dropdown icon={AlignHorizontalJustifyCenter} title={t("lbd.align_all")} testid="lbd-align" disabled={!(sameParent || selPaths.length > 1)}
            items={([["left", AlignHorizontalJustifyStart], ["centerH", AlignHorizontalJustifyCenter], ["right", AlignHorizontalJustifyEnd],
              ["top", AlignVerticalJustifyStart], ["centerV", AlignVerticalJustifyCenter], ["bottom", AlignVerticalJustifyEnd]] as const).map(([k, Ic]) => ({
              label: <span className="lbd-ddi"><Ic size={14} /> {t(`lbd.align.${k}`)}</span>, onClick: () => align(k), testid: `lbd-align-${k}` }))} />
          <span className="tsep" />
          <IconBtn icon={ZoomOut} title={`${t("lbd.zoom_out")} (Ctrl+−)`} onClick={() => zoomTo(scale / 1.25)} testid="lbd-zoom-out" />
          <span className="lbd-zoom" data-testid="lbd-zoom">{Math.round(scale * 100 / 3.78)}%</span>
          <IconBtn icon={ZoomIn} title={`${t("lbd.zoom_in")} (Ctrl+=)`} onClick={() => zoomTo(scale * 1.25)} testid="lbd-zoom-in" />
          <IconBtn icon={Scan} title={`${t("lbd.fit")} (Ctrl+0)`} onClick={() => setZoom({ fit: true, scale })} active={zoom.fit} testid="lbd-fit" />
          <span className="tsep" />
          <IconBtn icon={Grid3x3} title={t("lbd.grid")} onClick={() => setShowGrid(!showGrid)} active={showGrid} testid="lbd-grid" />
          <IconBtn icon={Magnet} title={`${t("lbd.snap")} (Alt — ${t("lbd.snap_off")})`} onClick={() => setSnap(!snap)} active={snap} testid="lbd-snap" />
          <IconBtn icon={Ruler} title={t("lbd.guides")} onClick={() => setGuides(!guides)} active={guides} testid="lbd-guides" />
          <Sel<number> value={grid} width={78} onChange={setGrid} testid="lbd-grid-step" options={GRIDS.map((g) => ({ value: g, label: `${g} ${t("u.mm")}` }))} />
          <span className="grow" />
          <Sel<string> value={kind} width={150} testid="lbd-kind" onChange={(v) => setKind(v as SampleKind)} options={kinds} />
          <Sel<string> value={dataSrc} width={150} testid="lbd-datasrc" onChange={(v) => { setDataSrc(v === "project" ? "project" : "sample"); setRowIdx(0); }}
            options={[{ value: "sample", label: t("lbd.src_sample") }, { value: "project", label: t("lbd.src_project") }]} />
          {dataSrc === "project" && (
            <span className="lbd-step" data-testid="lbd-rowstep">
              <button type="button" className="ibtn" onClick={() => setRowIdx(Math.max(0, rowIdx - 1))} disabled={rowIdx <= 0}>‹</button>
              <span>{(meta2?.index ?? rowIdx) + 1} / {meta2?.total ?? "?"}</span>
              <button type="button" className="ibtn" onClick={() => setRowIdx(Math.min((meta2?.total ?? 1) - 1, rowIdx + 1))} disabled={rowIdx >= (meta2?.total ?? 1) - 1}>›</button>
            </span>)}
        </div>
      </div>

      {design.error && <div className="lbx-issues lbx-issues-err" data-testid="lbd-error">{design.error}</div>}
      {errors.length > 0 && !errors[0].path && <div className="lbx-issues lbx-issues-err" data-testid="lbd-struct-error">{errors[0].message}</div>}

      <div className="lbd-main">
        <div className="lbd-stage" ref={stageRef} data-testid="lbd-stage">
          <div className="lbd-pad" style={{ padding: PAD }}>
            <DesignCanvas svg={dres?.svg ?? ""} pageW={W} pageH={H} scale={scale} sel={sel}
              getResizeMode={(k) => { const e = getEl(doc, parsePathKey(k)); return e ? resizeMode(e) : "none"; }}
              grid={grid} showGrid={showGrid} snap={snap} guides={guides} errorKeys={errorKeys}
              onSelect={(k) => setSel(k)} onMove={onMove} onResize={onResize} onVertex={onVertex}
              onMeasured={(m) => { boxesRef.current = m; bump(); }} onCursor={(x, y) => setCursor(x === null || y === null ? null : [x, y])} />
          </div>
        </div>
        <div className="lbd-side">
          <Tabs<SideTab> value={side} onChange={setSide} tabs={[
            { key: "props", label: t("lbd.tab.props"), testid: "lbd-tab-props" }, { key: "layers", label: `${t("lbd.tab.layers")} (${total})`, testid: "lbd-tab-layers" }]} />
          <div className="lbd-side-body scroll">
            {side === "props" && (singleEl && single
              ? <Inspector el={singleEl} path={pathKey(single)} errors={errors} branch={branch} onBranch={setBranch} onFx={openFx}
                onEdit={(fn, mk) => commit((d) => { const e = getEl(d, single); if (e) fn(e); }, mk ? { merge: mk } : {})} />
              : selPaths.length > 1
                ? <div className="lbd-insp" data-testid="lbd-multi"><b>{t("lbd.multi", { n: selPaths.length })}</b>
                  <p className="muted">{t("lbd.multi_hint")}</p></div>
                : <PagePanel tpl={doc} lb={lb} errors={errors} onFx={openFx} onLb={(p) => void onChange(p)}
                  onTpl={(fn, mk) => commit((d) => { fn(d); }, mk ? { merge: mk } : {})} />)}
            {side === "layers" && <LayersPanel tpl={doc} sel={sel} errors={errors} onSelect={select} />}
          </div>
          {dres && dres.warnings.length > 0 && <div className="lbx-issues" data-testid="lbd-warnings"><ul>{dres.warnings.map((w, i) => <li key={i} className="lbx-warn">{w}</li>)}</ul></div>}
          {errors.filter((e) => e.path).length > 0 && (
            <div className="lbx-issues lbx-issues-err" data-testid="lbd-errors"><b>{t("lb.errors")} ({errors.length})</b>
              <ul>{errors.slice(0, 8).map((e, i) => (
                <li key={i}><button type="button" className="linkbtn" onClick={() => { if (e.path) { setSel([e.path]); setSide("props"); } }}>#{e.path || "—"}</button> {e.field} — {e.message}</li>))}</ul></div>)}
          <div className={cx("lbd-dock", varsOpen && "lbd-dock-open")}>
            <button type="button" className="lbd-dock-h" onClick={() => setVarsOpen(!varsOpen)} data-testid="lbd-vars-toggle">
              {varsOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />} {t("lbd.tab.vars")} <span className="muted">· {t("lbd.vars_short")}</span>
            </button>
            {varsOpen && <div className="lbd-dock-b scroll"><VarsPanel lang={lang} values={dres?.values ?? {}} tplValues={dres?.tpl_values ?? {}} tpl={doc} /></div>}
          </div>
        </div>
      </div>
      <div className="lbd-status muted" data-testid="lbd-status">
        <span data-testid="lbd-cursor">{cursor ? `X ${cursor[0].toFixed(1)}  Y ${cursor[1].toFixed(1)} ${t("u.mm")}` : "—"}</span>
        <span>{W} × {H} {t("u.mm")}</span>
        {selHull && <span data-testid="lbd-selsize">{t("lbd.sel")}: {selHull.w.toFixed(1)} × {selHull.h.toFixed(1)}</span>}
        <span>{t("lbd.elements")}: {total}</span>
        {design.loading && <span>{t("app.loading")}</span>}
        <span className="grow" />
        <span>{t("lbd.keys_hint")}</span>
      </div>
      {fx && <ExprModal initial={fx.initial} context={ctxValues} onClose={() => setFx(null)} onApply={(v) => { fx.apply(v); setFx(null); }} />}
    </div>
  );
}

