// XNC «Шаблон» yorlig'i: buyruqlar palitrasi, ichma-ich daraxt muharriri (If / Else / While / DoWhile / Sub ichiga qo'shish,
// ko'chirish, chekinish), buyruq xossalari, holat paneli. Daraxt amallari — treeOps.ts (toza funksiyalar).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  Activity, ChevronDown, ChevronRight, ChevronUp, Copy, CornerDownRight, IndentDecrease, IndentIncrease, ListTree, Maximize,
  Settings2, Trash, Variable, Wrench,
} from "lucide-react";
import { call } from "../../api/hooks";
import { get, patch, post } from "../../api/client";
import type { Operation, Project, XncCommand, XncStats } from "../../api/types";
import { askText } from "../../shared/dialogs";
import { Modal } from "../../shared/ui";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, Sel, cx } from "../../shared/ui";
import { LazyInput, parseParam } from "./LazyInput";
import { CmdIcon, cmdLine } from "./cmdView";
import { defOf, isTextParam, missingKeys, summary, type PDef } from "./xncSchema";
import { useTreeDnd } from "./treeDnd";
import { XncIssues } from "./XncIssues";
import { PLANE_OF_CMD, PLANES, usePaletteOrder, useXncTools } from "./xncSettingsApi";
import {
  cloneAt, countAll, flatten, getAt, indent, insertAt, isContainer, moveSibling, outdent, pathKey, removeAt, reveal, samePath,
  updateAt, type Edit, type Path,
} from "./treeOps";

interface PalItem { cmd: string; short: string; params: Record<string, string | number>; svc?: boolean }

/** Palitra: birinchi 15 ta — xizmat (boshqaruv) buyruqlari (F4 — ko'rsatish / yashirish). */
export const PALETTE: PalItem[] = [
  { cmd: "Com", short: "Com", params: {}, svc: true }, { cmd: "Par", short: "Par", params: { name: "p1", value: 0, label: "", type: "double" }, svc: true },
  { cmd: "Var", short: "Var", params: { name: "v1", value: "dz" }, svc: true }, { cmd: "Set", short: "Set", params: { name: "v1", value: 0 }, svc: true },
  { cmd: "If", short: "IF", params: { cond: "dx>500" }, svc: true }, { cmd: "Else", short: "Else", params: {}, svc: true },
  { cmd: "While", short: "WD", params: { cond: "" }, svc: true }, { cmd: "DoWhile", short: "DW", params: { cond: "" }, svc: true },
  { cmd: "Break", short: "Brk", params: {}, svc: true }, { cmd: "Continue", short: "Con", params: {}, svc: true },
  { cmd: "Sub", short: "Sub", params: { name: "s1" }, svc: true }, { cmd: "Call", short: "Call", params: { name: "s1" }, svc: true },
  { cmd: "Ret", short: "Ret", params: {}, svc: true }, { cmd: "Msg", short: "Msg", params: { text: "" }, svc: true },
  { cmd: "Err", short: "Err", params: { text: "" }, svc: true }, { cmd: "Tool", short: "Tool", params: { N: "Bore8", D: 8 } },
  { cmd: "DrillFront", short: "⊙", params: { X: 50, Y: 50, DP: 12, T: "Bore8", AC: 1, AS: 32, AV: "false" } },
  { cmd: "DrillLeft", short: "⇠", params: { Y: 50, Z: "dz/2", DP: 30, T: "Bore8" } },
  { cmd: "DrillRight", short: "⇢", params: { Y: 50, Z: "dz/2", DP: 30, T: "Bore8" } },
  { cmd: "DrillTop", short: "⇡", params: { X: 50, Z: "dz/2", DP: 30, T: "Bore8" } },
  { cmd: "DrillBottom", short: "⇣", params: { X: 50, Z: "dz/2", DP: 30, T: "Bore8" } },
  { cmd: "MillStart", short: "M↦", params: { X: 0, Y: 0, DP: "dz", T: "Mill8" } },
  { cmd: "MillLine", short: "M—", params: { X: 100, Y: 0 } },
  { cmd: "MillArc", short: "M⌒", params: { X: 100, Y: 100, R: 50 } },
  { cmd: "MillArcCenter", short: "M◠", params: { X: 100, Y: 100, CX: 100, CY: 0, DIR: "true" } },
  { cmd: "MillArc3P", short: "M∿", params: { X: 100, Y: 100, X2: 50, Y2: 60 } },
  { cmd: "MillFillet", short: "M╮", params: { R: 10 } },
  { cmd: "MillRect", short: "M▭", params: { X: 100, Y: 100, L: 100, W: 50, R: 5 } },
  { cmd: "MillEllipse", short: "M◯", params: { X: 100, Y: 100, RL: 40, RW: 20 } },
  { cmd: "Groove", short: "Paz", params: { X1: 0, Y1: 16, X2: "dx", Y2: 16, DP: 8, W: 4 } },
  { cmd: "Origin", short: "O", params: { X: 0, Y: 0 } },
];

const PALETTE_CMDS = PALETTE.map((p) => p.cmd);
const PALETTE_BY_CMD = new Map(PALETTE.map((p) => [p.cmd, p]));

/** Asbob nomi maydoni uchun `<datalist>`: teshik buyruqlari — o'z tekisligidagi asboblar, boshqalari (Tool, freza, paz) — hammasi. */
function toolListId(cmd: string, k: string): string | undefined {
  if (k !== "T" && !(cmd === "Tool" && k === "N")) return undefined;
  const plane = PLANE_OF_CMD[cmd];
  return plane ? `xnc-tl-${plane}` : "xnc-tl-all";
}

const NUMERIC_DEFAULT = new Set(["X", "Y", "Z", "DP", "D", "AC", "AS", "R", "CX", "CY", "X2", "Y2", "L", "W", "A", "RL", "RW", "X1", "Y1",
  "SDP", "SXY", "value"]);

export function defaultFor(def: PDef | undefined, key: string): string | number {
  if (def?.kind === "enum") return def.options?.[0]?.value ?? 0;
  if (def?.kind === "bool") return "false";
  return NUMERIC_DEFAULT.has(key) ? 0 : "";
}

export function ParamRow({ cmd, k, v, onChange, onDelete, text, toolOpts, onVars, ctx }: {
  cmd: string; k: string; v: string | number; onChange: (v: string | number) => void; onDelete: () => void;
  /** matn qiymati (Par type=string): kiritilgan matn o'zgarishsiz saqlanadi — songa aylantirilmaydi («007» → 7 bo'lmasin) */
  text?: boolean;
  /** dasturdagi asboblar (Tool buyruqlari) — T maydoni uchun ro'yxat «N=… D=…» (onlayn oynadagi kabi) */
  toolOpts?: { value: string; label: string }[];
  /** «Vs» — o'zgaruvchilar oynasi (ifoda kiritishda yordam) */
  onVars?: () => void;
  /** o'zgaruvchilar qiymatlari (dx, dy, dz, Par / Var …) — ifoda ostida hisoblangan qiymatni ko'rsatish uchun */
  ctx?: Record<string, string | number | boolean | null>;
}) {
  const listId = toolListId(cmd, k);
  const { t } = useTranslation();
  const def = defOf(cmd, k);
  const hint = t(`xnc.p.${k}`, { defaultValue: "" });
  const label = t(`xnc.pl.${k}`, { defaultValue: k });
  let editor: ReactNode;
  if (k === "T" && toolOpts && toolOpts.length) {
    const opts = toolOpts.some((o) => o.value === String(v)) ? toolOpts : [...toolOpts, { value: String(v), label: String(v) }];
    editor = <Sel<string> value={String(v)} options={opts} width="100%" testid={`pv-${k}`} onChange={(sv) => onChange(sv)} />;
  } else if (def?.kind === "enum" && def.options) {
    const opts = def.options.map((o) => ({ value: String(o.value), label: t(o.label) }));
    if (!opts.some((o) => o.value === String(v))) opts.push({ value: String(v), label: String(v) });
    const numeric = typeof def.options[0].value === "number";
    editor = <Sel<string> value={String(v)} options={opts} width="100%" testid={`pv-${k}`}
      onChange={(s) => onChange(numeric ? Number(s) : s)} />;
  } else if (def?.kind === "bool" && ["true", "false"].includes(String(v).toLowerCase())) {
    editor = <label className="pv-check"><input type="checkbox" checked={String(v).toLowerCase() === "true"} data-testid={`pv-${k}`}
      onChange={(e) => onChange(e.target.checked ? "true" : "false")} /></label>;
  } else {
    editor = <LazyInput className="inp" value={String(v)} testid={`pv-${k}`} list={listId}
      onCommit={(raw) => onChange(text ? raw : parseParam(raw))} />;
  }
  const expr = !text && def?.kind !== "bool" && def?.kind !== "enum" && k !== "T" && k !== "N" && typeof v === "string" && v.trim() !== "" && Number.isNaN(Number(v));
  // ifoda ostida hisoblangan qiymat (onlayn oynadagi kabi): /expr/check, 250 ms kechikish bilan
  const [val, setVal] = useState<string | null>(null);
  useEffect(() => {
    if (!expr || !ctx) { setVal(null); return; }
    const h = setTimeout(() => {
      post<{ ok: boolean; value_text: string; error?: string | null }>("/expr/check", { expr: String(v), context: ctx })
        .then((r) => setVal(r.ok ? r.value_text : (r.error || "?"))).catch(() => setVal(null));
    }, 250);
    return () => clearTimeout(h);
  }, [v, expr, ctx]);
  return (
    <div className="row gap pv-row">
      <span className="pk" title={hint ? `${k} — ${hint}` : k}>{label}</span>
      <div className="pv-col">
        {editor}
        {val !== null && <div className="pv-val muted" data-testid={`pv-val-${k}`}>{val}</div>}
      </div>
      {onVars && expr !== undefined && <button type="button" className="pvs" title={t("xnc.vars.title")} onClick={onVars}>Vs</button>}
      <IconBtn icon={Trash} title={t("app.delete")} onClick={onDelete} />
    </div>
  );
}

/** Xossalar oynasidagi maydonlar tartibi: koordinatalar → chuqurlik → «Массив» (AC, AS, AV) → asbob → qolganlari. */
const PARAM_ORDER = ["X", "Y", "Z", "X1", "Y1", "X2", "Y2", "CX", "CY", "DP", "L", "W", "R", "RL", "RW", "D", "N",
  "AC", "AS", "AV", "T", "C", "M", "DIR", "IN", "OUT", "SDP", "SXY", "A", "P", "VER"];
const ARRAY_KEYS = new Set(["AC", "AS", "AV"]);

function orderedParams(params: Record<string, string | number>): [string, string | number][] {
  const rank = (k: string) => { const i = PARAM_ORDER.indexOf(k); return i < 0 ? PARAM_ORDER.length : i; };
  return Object.entries(params).sort((a, b) => rank(a[0]) - rank(b[0]));
}

export function XncProgramTab({ project, op, drawing, tabs, stats, onFit, onVars, onTools }: {
  project: Project; op: Operation; drawing: ReactNode; tabs: ReactNode; stats?: XncStats;
  /** «Показать все изображение» / «Переменные» / «Инструменты» (oynalar va chizma holati — XncPanel da) */
  onFit?: () => void; onVars?: () => void; onTools?: () => void;
}) {
  const { t } = useTranslation();
  const prog = op.xnc!.program;
  // `view` — ko'rsatilayotgan (optimistik) dastur: server javobigacha ketma-ket o'zgarishlar bir-birini o'chirmasin
  const [view, setView] = useState<XncCommand[]>(prog);
  const viewRef = useRef(view);
  viewRef.current = view;
  useEffect(() => setView(prog), [prog]);
  const [sel, setSel] = useState<Path | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const [inside, setInside] = useState(false);          // palitradan «tanlangan blok ichiga» qo'shish
  const [svc, setSvc] = useState(true);                 // F4: xizmat buyruqlari
  const [showState, setShowState] = useState(false);    // F9: holat paneli
  const editRef = useRef<HTMLDivElement>(null);
  // sozlamalar (W8): asboblar jadvali (T / N avtoto'ldirish) va palitra tartibi / yoqilganligi
  const toolsQ = useXncTools();
  const libTools = useMemo(() => toolsQ.data?.tools ?? [], [toolsQ.data]);
  const palCmds = usePaletteOrder(PALETTE_CMDS);
  const palItems = useMemo(() => palCmds.map((c) => PALETTE_BY_CMD.get(c)).filter((p): p is PalItem => !!p), [palCmds]);
  const issues = stats?.constraint_issues ?? [];

  const save = (pr: XncCommand[]) => {
    viewRef.current = pr;
    setView(pr);
    void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { xnc: { program: pr } }));
  };
  const commit = (e: Edit, keepInside = false) => {
    if (e.prog !== viewRef.current) save(e.prog);
    setSel(e.sel);
    if (e.sel) setCollapsed((c) => reveal(c, e.sel as Path));
    if (!keepInside) setInside(false);
  };
  const select = (p: Path | null) => { setSel(p); setInside(false); };
  // xossalar oynasi (onlayn kabi: ikki marta bosish / Enter / F2); «Отмена» — ochilgandagi holatga qaytaradi
  const [propsOpen, setPropsOpen] = useState(false);
  const propsSnap = useRef<XncCommand | null>(null);
  const [exprCtx, setExprCtx] = useState<Record<string, string | number | boolean | null> | undefined>(undefined);
  useEffect(() => {
    if (!propsOpen) return;
    let alive = true;
    get<{ rows: { name: string; value: string | number | boolean | null }[] }>(`/projects/${project.id}/operations/${op.id}/xnc-vars`)
      .then((r) => { if (alive) setExprCtx(Object.fromEntries(r.rows.map((x) => [x.name, x.value]))); })
      .catch(() => { if (alive) setExprCtx(undefined); });
    return () => { alive = false; };
  }, [propsOpen, project.id, op.id, view]);
  // sichqoncha bilan sudrab ko'chirish (W18): qator → boshqa qator oldiga / keyiniga / blok ichiga
  const dnd = useTreeDnd(() => viewRef.current, (e) => commit(e), (p) => select(p));

  const rows = useMemo(() => flatten(view, collapsed), [view, collapsed]);
  const selCmd = sel ? getAt(view, sel) : null;
  const idx = sel ? rows.findIndex((r) => samePath(r.path, sel)) : -1;

  const add = (tpl: PalItem) => {
    const cmd: XncCommand = { cmd: tpl.cmd, params: { ...tpl.params }, comment: "", enabled: true, children: [] };
    const cur = viewRef.current;
    const target = sel ? getAt(cur, sel) : null;
    let e: Edit;
    if (sel && target && inside && isContainer(target)) e = insertAt(cur, sel, undefined, cmd);   // blok ichiga (oxiriga)
    else if (sel && target) e = insertAt(cur, sel.slice(0, -1), sel[sel.length - 1] + 1, cmd);    // tanlanganidan keyin (shu darajada)
    else e = insertAt(cur, [], undefined, cmd);
    commit(e, true);
    setInside(isContainer(cmd));                      // yangi blok — keyingi buyruq uning ichiga tushadi
  };

  const act = {
    up: () => sel && commit(moveSibling(viewRef.current, sel, -1)),
    down: () => sel && commit(moveSibling(viewRef.current, sel, 1)),
    indent: () => sel && commit(indent(viewRef.current, sel)),
    outdent: () => sel && commit(outdent(viewRef.current, sel)),
    clone: () => sel && commit(cloneAt(viewRef.current, sel)),
    del: () => sel && commit(removeAt(viewRef.current, sel)),
  };
  const toggle = (p: Path) => setCollapsed((c) => {
    const n = new Set(c);
    const k = pathKey(p);
    if (n.has(k)) n.delete(k); else n.add(k);
    return n;
  });
  const nav = (to: number) => { const r = rows[Math.max(0, Math.min(rows.length - 1, to))]; if (r) select(r.path); };
  const upd = (f: (c: XncCommand) => Partial<XncCommand>, at: Path | null = sel) => {
    if (!at) return;
    commit({ prog: updateAt(viewRef.current, at, f), sel: at }, true);
  };
  /** Tool buyrug'ida nom jadvaldagi asbobga mos kelsa — diametr (D) ham shundan olinadi. */
  const toolExtra = (cmd: string, k: string, nv: string | number): Record<string, number> => {
    if (cmd !== "Tool" || k !== "N") return {};
    const tl = libTools.find((x) => x.name === String(nv));
    return tl ? { D: tl.d } : {};
  };
  const pickIssue = (p: Path) => { setCollapsed((c) => reveal(c, p)); select(p); };

  const openProps = () => {
    const cur = sel ? getAt(view, sel) : null;
    if (!cur) return;
    propsSnap.current = JSON.parse(JSON.stringify(cur)) as XncCommand;
    setPropsOpen(true);
  };
  const cancelProps = () => {
    const sn = propsSnap.current;
    if (sn && sel) upd(() => ({ params: { ...sn.params }, comment: sn.comment, enabled: sn.enabled }));
    setPropsOpen(false);
  };
  // dasturdagi asboblar — T maydoni ro'yxati («N=Bore3 D=3»)
  const toolOpts = useMemo(() => {
    const out: { value: string; label: string }[] = [];
    const walk = (l: XncCommand[]) => l.forEach((c) => {
      if (c.cmd === "Tool" && c.params.N !== undefined) out.push({ value: String(c.params.N), label: `N=${c.params.N} D=${c.params.D ?? ""}` });
      walk(c.children ?? []);
    });
    walk(view);
    return out;
  }, [view]);

  useHotkeys("xnc", {
    enter: openProps, f2: openProps,
    arrowup: () => nav(idx < 0 ? rows.length - 1 : idx - 1), arrowdown: () => nav(idx + 1),
    home: () => nav(0), end: () => nav(rows.length - 1),
    arrowleft: () => {
      const r = rows[idx];
      if (!r) return;
      if (r.hasChildren && !r.collapsed) toggle(r.path);
      else if (r.path.length > 1) select(r.path.slice(0, -1));
    },
    arrowright: () => {
      const r = rows[idx];
      if (!r || !r.hasChildren) return;
      if (r.collapsed) toggle(r.path); else nav(idx + 1);
    },
    "ctrl+arrowup": act.up, "ctrl+arrowdown": act.down,
    "ctrl+arrowright": act.indent, "ctrl+arrowleft": act.outdent,
    "ctrl+k": act.clone, delete: act.del,
    "ctrl+space": () => {
      if (!propsOpen) { openProps(); return; }
      editRef.current?.querySelector<HTMLInputElement | HTMLSelectElement>("input, select")?.focus();
    },
    f4: () => setSvc((v) => !v), f9: () => setShowState((v) => !v),
  });

  const c = selCmd;
  const container = isContainer(c);
  const warns = stats?.warnings ?? [];

  return (
    <div className="panel">
      {tabs}
      <div className="xnc-editor" {...scopeProps("xnc")}>
        <div className="xnc-palette">
          {palItems.map((p) => (
            <button key={p.cmd} type="button" className={cx("pal", p.svc && !svc && "pal-off")} onClick={() => add(p)}
              title={t(`xnc.cmd.${p.cmd}`, { defaultValue: p.cmd })} data-testid={`pal-${p.cmd}`}>{p.svc ? p.short : <CmdIcon cmd={p.cmd} />}</button>
          ))}
          {/* asboblar jadvali (Настройки → XNC): T / N maydonlari avtoto'ldirish takliflari */}
          {PLANES.map((pl) => (
            <datalist key={pl} id={`xnc-tl-${pl}`}>
              {libTools.filter((x) => x.plane === pl).map((x) => <option key={x.name} value={x.name}>{`⌀${x.d}`}</option>)}
            </datalist>
          ))}
          <datalist id="xnc-tl-all">
            {[...new Map(libTools.map((x) => [x.name, x])).values()].map((x) => <option key={x.name} value={x.name}>{`⌀${x.d}`}</option>)}
          </datalist>
        </div>
        {drawing}
        <div className="xnc-prog">
          <div className="toolbar prog-bar">
            <b>{t("xnc.program")}</b><span className="grow" />
            {onFit && <IconBtn icon={Maximize} title={t("xnc.fit")} onClick={onFit} testid="xnc-fit" />}
            <IconBtn icon={Settings2} title={t("xnc.props_btn")} onClick={openProps} disabled={!sel} testid="xnc-props-btn" />
            <IconBtn icon={ListTree} title={t("xnc.svc")} active={svc} onClick={() => setSvc(!svc)} testid="xnc-svc" />
            <IconBtn icon={Activity} title={t("xnc.state")} active={showState} onClick={() => setShowState(!showState)} testid="xnc-state-btn"
              label={issues.length ? String(issues.length) : undefined} />
            {onVars && <IconBtn icon={Variable} title={t("xnc.vars.title")} onClick={onVars} testid="xnc-vars" />}
            {onTools && <IconBtn icon={Wrench} title={t("xnc.tools.title")} onClick={onTools} testid="xnc-tools" />}
          </div>
          <div className="toolbar prog-bar">
            <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={act.up} disabled={!sel} testid="xnc-up" />
            <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={act.down} disabled={!sel} testid="xnc-down" />
            <IconBtn icon={IndentDecrease} title={t("xnc.outdent")} onClick={act.outdent} disabled={!sel || sel.length < 2} testid="xnc-outdent" />
            <IconBtn icon={IndentIncrease} title={t("xnc.indent")} onClick={act.indent} testid="xnc-indent"
              disabled={!sel || sel[sel.length - 1] === 0 || !isContainer(getAt(view, [...sel.slice(0, -1), sel[sel.length - 1] - 1]))} />
            <IconBtn icon={CornerDownRight} title={t("xnc.inside")} active={inside} onClick={() => setInside(!inside)}
              disabled={!container} testid="xnc-inside" />
            <span className="grow" />
            <IconBtn icon={Copy} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!sel} testid="xnc-clone" />
            <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} color="#c0392b" onClick={act.del} disabled={!sel} testid="xnc-delete" />
          </div>
          <div className="scroll prog-list prog-tree" data-testid="xnc-program" title={`${t("xnc.dnd_hint")} ${t("xnc.props_hint")}`}>
            {rows.map((r) => {
              const k = pathKey(r.path);
              const isSel = samePath(sel, r.path);
              const block = isContainer(r.cmd);
              return (
                <div key={k} className={cx("prog-row", isSel && "prog-sel", r.cmd.enabled === false && "prog-off")}
                  style={{ paddingLeft: 2 + r.depth * 16 }} data-testid={`prog-item-${k}`} data-depth={r.depth}
                  {...dnd.rowProps(r.path, r.cmd)}
                  onClick={() => select(r.path)} onDoubleClick={() => { select(r.path); setTimeout(openProps, 0); }}>
                  {r.hasChildren
                    ? <button type="button" className="prog-chev" aria-label={r.collapsed ? t("xnc.expand") : t("xnc.collapse")} data-testid={`prog-fold-${k}`}
                        onClick={(e) => { e.stopPropagation(); toggle(r.path); }}>
                        {r.collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                      </button>
                    : <span className="prog-chev-ph" />}
                  <input type="checkbox" checked={r.cmd.enabled !== false} title={t("xnc.enabled")} data-testid={`prog-enable-${k}`}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => { const el = e.target; upd(() => ({ enabled: el.checked }), r.path); el.blur(); }} />   {/* blur: ↑↓ / F4 yorliqlari ishlayversin */}
                  <span className={cx("prog-txt", block && "prog-block")}
                    title={`${t(`xnc.cmd.${r.cmd.cmd}`, { defaultValue: r.cmd.cmd })} (${r.cmd.cmd}): ${summary(r.cmd)}`}>
                    <CmdIcon cmd={r.cmd.cmd} />{cmdLine(r.cmd)}
                    {r.cmd.comment && <span className="muted"> ;{r.cmd.comment}</span>}
                  </span>
                  {r.collapsed && <span className="prog-badge" title={t("xnc.collapse")}>{countAll(r.cmd.children)}</span>}
                </div>
              );
            })}
            {!view.length && <div className="muted" style={{ padding: 6 }}>{t("xnc.empty")}</div>}
          </div>
          {showState && (
            <div className="prog-state" data-testid="xnc-state">
              <div>{t("xnc.stats_line", { d: stats?.drills ?? 0, m: stats?.mill_m ?? 0, s: stats?.saw_m ?? 0 })}</div>
              {warns.length === 0
                ? (issues.length === 0 && <div className="good">{t("xnc.state_ok")}</div>)
                : <><div className="bad">{t("xnc.state_n", { n: stats?.errors ?? warns.length })}</div>
                    {warns.map((w, i) => <div key={i} className="bad">• {w}</div>)}</>}
              <XncIssues issues={issues} turn={stats?.constraint_turn} onPick={pickIssue} />
            </div>
          )}
          {c && sel && propsOpen && (
            <Modal title={t("xnc.props_title", { name: t(`xnc.cmd.${c.cmd}`, { defaultValue: c.cmd }) })} onClose={cancelProps}
              width={460} scope="xncprops" testid="xnc-props"
              footer={<>
                <button type="button" className="btn btn-primary" data-testid="xnc-props-ok" onClick={() => setPropsOpen(false)}>{t("app.ok")}</button>
                <button type="button" className="btn" data-testid="xnc-props-cancel" onClick={cancelProps}>{t("app.cancel")}</button>
              </>}>
            <div className="prog-edit" ref={editRef} data-testid="xnc-edit">
              <div className="prog-edit-scroll">
                {orderedParams(c.params).map(([k, v], i, arr) => (
                  <div key={`${pathKey(sel)}-${c.cmd}-${k}`}>
                    {ARRAY_KEYS.has(k) && (i === 0 || !ARRAY_KEYS.has(arr[i - 1][0])) && <div className="form-h prog-group">{t("xnc.array")}</div>}
                    <ParamRow cmd={c.cmd} k={k} v={v} text={isTextParam(c, k)} toolOpts={toolOpts} onVars={onVars} ctx={exprCtx}
                      onChange={(nv) => upd((cc) => ({ params: { ...cc.params, [k]: nv, ...toolExtra(cc.cmd, k, nv) } }))}
                      onDelete={() => upd((cc) => { const pr = { ...cc.params }; delete pr[k]; return { params: pr }; })} />
                  </div>
                ))}
              </div>
              <div className="row gap">
                <select className="inp sel" value="" data-testid="xnc-add-param" style={{ width: "100%" }}
                  onChange={async (e) => {
                    const key = e.target.value;
                    if (!key) return;
                    if (key === "__custom") {
                      const nk = await askText(t("xnc.param_name"), "");
                      if (nk && sel) upd((cc) => ({ params: { ...cc.params, [nk]: 0 } }));
                    } else {
                      upd((cc) => ({ params: { ...cc.params, [key]: defaultFor(defOf(cc.cmd, key), key) } }));
                    }
                  }}>
                  <option value="">+ {t("xnc.add_known")}</option>
                  {missingKeys(c).map((k) => <option key={k} value={k}>{k} — {t(`xnc.p.${k}`, { defaultValue: "" })}</option>)}
                  <option value="__custom">{t("xnc.param_custom")}</option>
                </select>
              </div>
              <div className="row gap">
                <span className="pk">{t("xnc.comment")}</span>
                <LazyInput key={`${pathKey(sel)}-comment`} className="inp w100" placeholder={t("xnc.comment")} value={c.comment}
                  onCommit={(v) => upd(() => ({ comment: v }))} />
              </div>
            </div>
            </Modal>
          )}
        </div>
      </div>
    </div>
  );
}
