// XNC «Шаблон» yorlig'i: buyruqlar palitrasi, ichma-ich daraxt muharriri (If / Else / While / DoWhile / Sub ichiga qo'shish,
// ko'chirish, chekinish), buyruq xossalari, holat paneli. Daraxt amallari — treeOps.ts (toza funksiyalar).
import { useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  Activity, ChevronDown, ChevronRight, ChevronUp, ClipboardPaste, Copy, CopyPlus, CornerDownRight, EyeOff, TrianglesCenterlineDashedVertical as MirrorHIcon, TrianglesCenterlineDashedHorizontal as MirrorVIcon, IndentDecrease,
  IndentIncrease, ListChecks, ListTree, Maximize, Redo2, Scissors, Settings2, Trash, Undo2, Variable, Wrench,
} from "lucide-react";
import { call } from "../../api/hooks";
import { get, patch, post } from "../../api/client";
import type { Operation, Project, XncCommand, XncStats } from "../../api/types";
import { askChoice, askConfirm, askText } from "../../shared/dialogs";
import { Btn, Modal, Sep } from "../../shared/ui";
import { useContextMenu } from "../../shared/grid/ContextMenu";
import { redo, undo } from "../project/ProjectMenu";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, Sel, cx } from "../../shared/ui";
import { LazyInput, parseParam } from "./LazyInput";
import { CmdIcon, cmdLine } from "./cmdView";
import { SCHEMA, defOf, isTextParam, missingKeys, summary, type PDef } from "./xncSchema";
import { useTreeDnd } from "./treeDnd";
import { XncIssues } from "./XncIssues";
import { MIRRORABLE, mirrorCmd } from "./xncTransform";
import { PLANE_OF_CMD, PLANES, usePaletteOrder, useXncTools } from "./xncSettingsApi";
import {
  cloneAt, countAll, flatten, getAt, indent, insertAt, isContainer, moveSibling, outdent, pathKey, removeMany, reveal, samePath,
  updateAt, type Edit, type Path,
} from "./treeOps";

interface PalItem { cmd: string; short: string; params: Record<string, string | number>; svc?: boolean }

/** Palitra guruhlari (onlayn tizimdagi kabi ustun ichida bo'shliq bilan ajraladi): guruhning birinchi buyrug'i. */
const PAL_GROUP_START = new Set(["Par", "If", "While", "Sub", "Msg", "DrillFront", "MillStart", "Groove", "Origin"]);

/** «Вырезать / Копировать / Вставить» buyruqlar buferi (dasturlar orasida ham ishlaydi; sahifa yangilanguncha). */
let cmdClipboard: XncCommand[] = [];

/** Palitradan qo'shilgan buyruq uchun xossalar oynasi darhol ochiladi (onlayn tizimdagidek; qiymatlar — bizning standartlar). */
const PROPS_ON_ADD = true;

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

export function ParamRow({ cmd, k, v, onChange, onDelete, text, toolOpts, onVars, ctx, disabled }: {
  cmd: string; k: string; v: string | number; onChange: (v: string | number) => void; onDelete: () => void;
  /** maydon faol emas (masalan, «Середина по Z» yoqilganda Z) */
  disabled?: boolean;
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
    editor = <LazyInput className="inp" value={String(v)} testid={`pv-${k}`} list={listId} disabled={disabled}
      onCommit={(raw) => onChange(text ? raw : parseParam(raw))} />;
  }
  const numField = !text && def?.kind !== "bool" && def?.kind !== "enum" && k !== "T" && k !== "N";
  const expr = numField && typeof v === "string" && v.trim() !== "" && Number.isNaN(Number(v));
  // son (yoki «34.0» kabi o'zgarmas yozuv) — hisoblangan qiymat serversiz ko'rsatiladi: «70», «34»
  const plain = numField && !expr && String(v).trim() !== "" && Number.isFinite(Number(v)) ? String(Number(v)) : null;
  // ifoda ostida hisoblangan qiymat (onlayn oynadagi kabi): /expr/check, 250 ms kechikish bilan
  // xato bo'lsa (`bad`) — matn qizil va maslahatda to'liq sabab (to'g'ri qiymatdan ajralib tursin)
  const [val, setVal] = useState<string | null>(null);
  const [bad, setBad] = useState(false);
  useEffect(() => {
    if (!expr || !ctx) { setVal(null); setBad(false); return; }
    const h = setTimeout(() => {
      post<{ ok: boolean; value_text: string; error?: string | null }>("/expr/check", { expr: String(v), context: ctx })
        .then((r) => { setVal(r.ok ? r.value_text : (r.error || "?")); setBad(!r.ok); })
        .catch(() => { setVal(null); setBad(false); });
    }, 250);
    return () => clearTimeout(h);
  }, [v, expr, ctx]);
  return (
    <div className="row gap pv-row">
      <span className="pk" title={hint ? `${k} — ${hint}` : k}>{label}</span>
      <div className="pv-col">
        {editor}
        {(val ?? plain) !== null && (bad
          ? <div className="pv-val bad" data-testid={`pv-val-${k}`} role="alert"
              title={`${t("xnc.expr_err")}: ${val}`}>{t("xnc.expr_err")}: {val}</div>
          : <div className="pv-val muted" data-testid={`pv-val-${k}`}>{val ?? plain}</div>)}
      </div>
      {onVars && expr !== undefined && <button type="button" className="pvs" title={t("xnc.vars.title")} onClick={onVars}>Vs</button>}
      <IconBtn icon={Trash} title={t("app.delete")} onClick={onDelete} />
    </div>
  );
}

/** Xossalar oynasidagi maydonlar tartibi: koordinatalar → chuqurlik → «Середина по Z» (M) → Z → «Массив» (AC, AS, AV) → asbob →
 *  qolganlari (onlayn oynadagidek: «Y, DP, Середина по Z, Смещение по Z, T»). */
const PARAM_ORDER = ["X", "Y", "X1", "Y1", "X2", "Y2", "CX", "CY", "DP", "M", "Z", "L", "W", "R", "RL", "RW", "D", "N",
  "AC", "AS", "AV", "T", "C", "DIR", "IN", "OUT", "SDP", "SXY", "A", "P"];
/** Oynada ko'rsatilmaydigan ichki atributlar (import qilingan format versiyasi — saqlanadi, tahrir qilinmaydi). */
const HIDDEN_PARAMS = new Set(["VER"]);
const ARRAY_KEYS = new Set(["AC", "AS", "AV"]);

function orderedParams(params: Record<string, string | number>): [string, string | number][] {
  const rank = (k: string) => { const i = PARAM_ORDER.indexOf(k); return i < 0 ? PARAM_ORDER.length : i; };
  const out = Object.entries(params).filter(([k]) => !HIDDEN_PARAMS.has(k));
  // «Массив» guruhi to'liq ko'rinadi (Количество, Шаг, По вертикали — onlayn oynadagidek): yo'q maydon bo'sh qiymat bilan
  if (out.some(([k]) => ARRAY_KEYS.has(k))) for (const k of ARRAY_KEYS) if (!(k in params)) out.push([k, ""]);
  return out.sort((a, b) => rank(a[0]) - rank(b[0]));
}

/** Tashqi boshqaruv (detal «XNC Редактор» oynasining yuqori asboblar paneli): tanlov, dasturni o'zgartirish va mavjud amallar. */
export interface XncProgApi {
  selected: () => Path[];
  apply: (fn: (prog: XncCommand[], sel: Path[]) => XncCommand[]) => void;
  del: () => void; up: () => void; down: () => void; props: () => void; undo: () => void; redo: () => void; fit: () => void;
}

export function XncProgramTab({ project, op, drawing, tabs, right, stats, onFit, onVars, onTools, apiRef }: {
  project: Project; op: Operation; stats?: XncStats;
  /** yuqori asboblar paneli uchun boshqaruv nuqtasi (berilsa — har renderda yangilanadi) */
  apiRef?: MutableRefObject<XncProgApi | null>;
  /** yorliqlar qatori (asboblar paneli o'ng tomonda) va XncPanel ning qo'shimcha tugmalari (Пересчитать, Справка, fayl …) */
  tabs: (right: ReactNode) => ReactNode; right?: ReactNode;
  /** chizma: `hl` — belgilanadigan buyruqlar yo'llari, `onPick` — chizmada bosilgan element buyrug'i (Ctrl — qo'shish) */
  drawing: (hl: string[], onPick: (key: string, add: boolean) => void) => ReactNode;
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
  // ochilganda birinchi buyruq tanlangan (boshqa jadvallardagi kabi doim bitta tanlangan qator bor)
  const [sel, setSel] = useState<Path | null>(() => (prog.length ? [0] : null));
  // ko'p tanlov (Ctrl / Shift + bosish, Ctrl + chizmada bosish): qo'shimcha qatorlar — faqat chizmada belgilash uchun;
  // tahrir amallari (ko'chirish, o'chirish, xossalar) asosiy tanlangan qator (`sel`) bilan ishlaydi
  const [extra, setExtra] = useState<string[]>([]);
  const listRef = useRef<HTMLDivElement>(null);
  const scrollTo = useRef<string | null>(null);         // chizmadan tanlangan qator — ro'yxatda ko'rinadigan joyga aylantiriladi
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const [inside, setInside] = useState(false);          // palitradan «tanlangan blok ichiga» qo'shish
  const [svc, setSvc] = useState(true);                 // F4: xizmat buyruqlari
  const [showState, setShowState] = useState(false);    // holat paneli (xatolar / cheklovlar — bizning qo'shimcha)
  const [stateDlg, setStateDlg] = useState(false);      // F9: «Состояние» oynasi
  const editRef = useRef<HTMLDivElement>(null);
  // sozlamalar (W8): asboblar jadvali (T / N avtoto'ldirish) va palitra tartibi / yoqilganligi
  const toolsQ = useXncTools();
  const libTools = useMemo(() => toolsQ.data?.tools ?? [], [toolsQ.data]);
  const palCmds = usePaletteOrder(PALETTE_CMDS);
  const palItems = useMemo(() => palCmds.map((c) => PALETTE_BY_CMD.get(c)).filter((p): p is PalItem => !!p), [palCmds]);
  const issues = stats?.constraint_issues ?? [];
  // dastur xatolari → qator yo'li (pathKey) bo'yicha xabarlar: qator qizil belgilanadi, sichqoncha ustida — xabar matni
  const errByKey = useMemo(() => {
    const m = new Map<string, string[]>();
    (stats?.warning_src ?? []).forEach((src, i) => {
      const w = stats?.warnings?.[i];
      if (!w) return;
      for (const k of src) m.set(k, [...(m.get(k) ?? []), w]);
    });
    return m;
  }, [stats?.warning_src, stats?.warnings]);
  const errKeys = useMemo(() => [...errByKey.keys()], [errByKey]);

  const save = (pr: XncCommand[]) => {
    viewRef.current = pr;
    setView(pr);
    void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { xnc: { program: pr } }));
  };
  const commit = (e: Edit, keepInside = false) => {
    if (e.prog !== viewRef.current) save(e.prog);
    setSel(e.sel);
    setExtra([]);
    anchor.current = e.sel ? { key: pathKey(e.sel), base: [] } : null;
    if (e.sel) setCollapsed((c) => reveal(c, e.sel as Path));
    if (!keepInside) setInside(false);
  };
  // Shift + bosish langari: oxirgi (oddiy yoki Ctrl bilan) bosilgan qator va o'sha paytdagi tanlov — Shift oralig'i shunga qo'shiladi
  const anchor = useRef<{ key: string; base: string[] } | null>(null);
  const select = (p: Path | null) => {
    setSel(p); setExtra([]); setInside(false);
    anchor.current = p ? { key: pathKey(p), base: [] } : null;
  };
  // xossalar oynasi (onlayn kabi: ikki marta bosish / Enter / F2); «Отмена» — ochilgandagi holatga qaytaradi
  const [propsOpen, setPropsOpen] = useState(false);
  const propsSnap = useRef<XncCommand | null>(null);
  const propsNew = useRef(false);                       // oyna yangi qo'shilgan buyruq uchun ochilgan
  const propsOnAdd = useRef(false);
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
  const hl = useMemo(() => (sel ? [pathKey(sel), ...extra.filter((k) => k !== pathKey(sel))] : extra), [sel, extra]);

  /** Qatorni bosish: oddiy — tanlash; Ctrl — qo'shimcha tanlovga qo'shish / olib tashlash; Shift — `sel` dan shu qatorgacha. */
  const clickRow = (p: Path, e: { ctrlKey: boolean; metaKey: boolean; shiftKey: boolean }) => {
    const k = pathKey(p);
    if ((e.ctrlKey || e.metaKey) && sel) {
      if (samePath(sel, p)) return;
      const nx = extra.includes(k) ? extra.filter((q) => q !== k) : [...extra, k];
      setExtra(nx);
      anchor.current = { key: k, base: nx };                // Shift oralig'i endi shu qatordan, Ctrl tanlovlari saqlanadi
      return;
    }
    if (e.shiftKey && sel) {
      const a = anchor.current ?? { key: pathKey(sel), base: [] };
      const i = rows.findIndex((r) => pathKey(r.path) === a.key);
      const j = rows.findIndex((r) => samePath(r.path, p));
      if (i >= 0 && j >= 0) {
        const range = rows.slice(Math.min(i, j), Math.max(i, j) + 1).map((r) => pathKey(r.path));
        setExtra([...new Set([...a.base, ...range])]);
        return;
      }
    }
    select(p);
  };
  /** Chizmada bosilgan element buyrug'i: daraxtda ochiladi, tanlanadi (Ctrl — qo'shiladi) va ro'yxatda ko'rinadigan joyga aylantiriladi. */
  const pickFromDrawing = (key: string, add: boolean) => {
    const p = key.split(".").map(Number);
    if (p.some((n) => !Number.isInteger(n) || n < 0) || !getAt(viewRef.current, p)) return;
    setCollapsed((c) => reveal(c, p));
    scrollTo.current = key;
    if (add && sel) clickRow(p, { ctrlKey: true, metaKey: false, shiftKey: false });
    else select(p);
  };
  useEffect(() => {
    const k = scrollTo.current;
    if (!k) return;
    scrollTo.current = null;
    listRef.current?.querySelector(`[data-testid="prog-item-${k}"]`)?.scrollIntoView({ block: "nearest" });
  });

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
    if (PROPS_ON_ADD && (SCHEMA[cmd.cmd]?.length ?? 0) > 0) propsOnAdd.current = true;   // onlayn kabi: darhol «Свойства»
  };

  const act = {
    up: () => sel && commit(moveSibling(viewRef.current, sel, -1)),
    down: () => sel && commit(moveSibling(viewRef.current, sel, 1)),
    indent: () => sel && commit(indent(viewRef.current, sel)),
    outdent: () => sel && commit(outdent(viewRef.current, sel)),
    clone: () => sel && commit(cloneAt(viewRef.current, sel)),
    // «Удалить» [DEL] (onlayn kabi): tasdiqlash so'raladi; tanlangan barcha qatorlar (Shift / Ctrl / Ctrl+A) o'chiriladi
    del: async () => {
      const ps = selPaths();
      if (!ps.length || !(await askConfirm(t(ps.length > 1 ? "xnc.delete_many_q" : "xnc.delete_q", { count: ps.length }), undefined, { danger: true }))) return;
      commit(removeMany(viewRef.current, ps));
    },
    // «Выключить» [CTRL]+[D]: buyruq dasturda qoladi, lekin bajarilmaydi (qayta bosilsa — yoqiladi)
    toggle: () => sel && upd((cc) => ({ enabled: cc.enabled === false })),
    // nusxalash / kesish — tanlangan barcha qatorlar, dastur tartibida
    copy: () => {
      const cs = selPaths().map((p) => getAt(viewRef.current, p)).filter((c): c is XncCommand => !!c);
      if (cs.length) cmdClipboard = JSON.parse(JSON.stringify(cs)) as XncCommand[];
    },
    cut: () => {
      const ps = selPaths();
      const cs = ps.map((p) => getAt(viewRef.current, p)).filter((c): c is XncCommand => !!c);
      if (!cs.length) return;
      cmdClipboard = JSON.parse(JSON.stringify(cs)) as XncCommand[];
      commit(removeMany(viewRef.current, ps));
    },
    // bufer tanlangan qatordan keyin (shu darajada) qo'yiladi
    paste: () => {
      if (!cmdClipboard.length) return;
      let cur = viewRef.current;
      let at = sel;
      let e: Edit | null = null;
      for (const c of cmdClipboard) {
        const cmd = JSON.parse(JSON.stringify(c)) as XncCommand;
        e = at && getAt(cur, at) ? insertAt(cur, at.slice(0, -1), at[at.length - 1] + 1, cmd) : insertAt(cur, [], undefined, cmd);
        cur = e.prog; at = e.sel;
      }
      if (e) commit(e);
    },
    selectAll: () => setExtra(rows.map((r) => pathKey(r.path))),
    // «Горизонтальное / Вертикальное отзеркаливание» (onlayn tartib): «С копированием» — akslantirilgan nusxa oxirgi tanlangan
    // buyruqdan keyin qo'yiladi (kontur nusxasi bir joyda), «Без копирования» — tanlangan buyruqlarning o'zi akslantiriladi.
    // Onlayn tizimdan farqli — yoylar (yo'nalish), korreksiya tomoni va ko'p tanlov ham akslantiriladi.
    mirror: async (axis: "x" | "y") => {
      const paths = mirrorPaths();
      if (!paths.length) return;
      const ans = await askChoice(t("xnc.mirror_copy_q"), { ok: t("xnc.mirror_copy"), no: t("xnc.mirror_inplace") });
      if (!ans) return;
      let cur = viewRef.current;
      if (ans === "no") {
        for (const p of paths) cur = updateAt(cur, p, (c) => mirrorCmd(c, axis));
        commit({ prog: cur, sel: paths[0] });
        return;
      }
      let at = paths[paths.length - 1];
      let e: Edit | null = null;
      for (const p of paths) {
        const src = getAt(viewRef.current, p);
        if (!src) continue;
        e = insertAt(cur, at.slice(0, -1), at[at.length - 1] + 1, mirrorCmd(JSON.parse(JSON.stringify(src)) as XncCommand, axis));
        cur = e.prog; at = e.sel ?? at;
      }
      if (e) commit(e);
    },
    // «Отменить / Вернуть»: dastur har o'zgarishda loyihaga yoziladi — loyiha tarixi bo'yicha
    undo: () => void undo(project.id),
    redo: () => void redo(project.id),
  };
  /** Tanlov: asosiy + qo'shimcha tanlangan qatorlar, dastur tartibida (blok tanlangan bo'lsa — ichidagilari alohida emas). */
  function selPaths(): Path[] {
    const keys = new Set([...(sel ? [pathKey(sel)] : []), ...extra]);
    const ps = rows.map((r) => r.path).filter((p) => keys.has(pathKey(p)));
    return ps.filter((p) => !ps.some((q) => q.length < p.length && samePath(q, p.slice(0, q.length))));
  }
  /** Akslantiriladigan tanlov: geometrik buyruqlar va bloklar (xizmat buyruqlari — Tool, Var … — o'zgarmaydi). */
  function mirrorPaths(): Path[] {
    return selPaths().filter((p) => { const c = getAt(viewRef.current, p); return !!c && (MIRRORABLE.has(c.cmd) || isContainer(c)); });
  }
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

  const openProps = (isNew: unknown = false) => {     // tugma / yorliq hodisasi uzatilsa ham — faqat aniq `true` yangi
    const cur = sel ? getAt(view, sel) : null;
    if (!cur) return;
    propsSnap.current = JSON.parse(JSON.stringify(cur)) as XncCommand;
    propsNew.current = isNew === true;
    setPropsOpen(true);
  };
  // palitradan qo'shilgan buyruq — tanlov yangilangach xossalar oynasi ochiladi
  useEffect(() => {
    if (propsOnAdd.current && sel && !propsOpen) { propsOnAdd.current = false; openProps(true); }
  });
  const cancelProps = () => {
    const sn = propsSnap.current;
    // yangi qo'shilgan buyruqda «Отмена» — buyruq olib tashlanadi (onlayn tizimda bo'sh qator qolardi)
    if (propsNew.current && sel) commit(removeMany(viewRef.current, [sel]));
    else if (sn && sel) upd(() => ({ params: { ...sn.params }, comment: sn.comment, enabled: sn.enabled }));
    propsNew.current = false;
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
    "ctrl+k": act.clone, delete: act.del, "ctrl+d": act.toggle,
    "ctrl+c": act.copy, "ctrl+x": act.cut, "ctrl+v": act.paste, "ctrl+a": act.selectAll, "ctrl+z": act.undo, "ctrl+y": act.redo,
    "ctrl+space": () => {
      if (!propsOpen) { openProps(); return; }
      editRef.current?.querySelector<HTMLInputElement | HTMLSelectElement>("input, select")?.focus();
    },
    f4: () => setSvc((v) => !v), f9: () => setStateDlg(true),
  });
  // o'ng tugma menyusi (onlayn tartib): Отменить, Вернуть | Вырезать, Копировать, Вставить, Выделить все | Удалить | Свойства |
  // Выключить | Горизонтальное, Вертикальное отзеркаливание; bizning qo'shimchalar (Клонировать, chekinish) — oxirida
  const ctx = useContextMenu(() => [
    { label: t("menu.undo"), hint: "Ctrl+Z", icon: Undo2, onClick: act.undo },
    { label: t("menu.redo"), hint: "Ctrl+Y", icon: Redo2, onClick: act.redo },
    { sep: true, label: "" },
    { label: t("xnc.cut"), hint: "Ctrl+X", icon: Scissors, onClick: act.cut, disabled: !sel },
    { label: t("ops.copy"), hint: "Ctrl+C", icon: Copy, onClick: act.copy, disabled: !sel, testid: "xnc-ctx-copy" },
    { label: t("ctx.paste"), hint: "Ctrl+V", icon: ClipboardPaste, onClick: act.paste, disabled: !cmdClipboard.length, testid: "xnc-ctx-paste" },
    { label: t("ctx.select_all"), hint: "Ctrl+A", icon: ListChecks, onClick: act.selectAll, disabled: !rows.length },
    { sep: true, label: "" },
    { label: t("app.delete"), hint: "Del", icon: Trash, onClick: act.del, disabled: !sel },
    { sep: true, label: "" },
    { label: t("app.properties"), hint: "Ctrl+Space", icon: Settings2, onClick: openProps, disabled: !sel },
    { sep: true, label: "" },
    { label: t("xnc.disable"), hint: "Ctrl+D", icon: EyeOff, onClick: act.toggle, disabled: !sel, testid: "xnc-ctx-toggle" },
    { sep: true, label: "" },
    { label: t("xnc.mirror_h"), icon: MirrorHIcon, onClick: () => void act.mirror("x"), disabled: !mirrorPaths().length,
      testid: "xnc-ctx-mirror-h" },
    { label: t("xnc.mirror_v"), icon: MirrorVIcon, onClick: () => void act.mirror("y"), disabled: !mirrorPaths().length,
      testid: "xnc-ctx-mirror-v" },
    { sep: true, label: "" },
    { label: t("app.clone"), hint: "Ctrl+K", icon: CopyPlus, onClick: act.clone, disabled: !sel },
    { label: t("xnc.outdent"), hint: "Ctrl+←", icon: IndentDecrease, onClick: act.outdent, disabled: !sel || sel.length < 2 },
    { label: t("xnc.indent"), hint: "Ctrl+→", icon: IndentIncrease, onClick: act.indent, disabled: !sel },
  ], "xnc-prog-menu");

  const c = selCmd;
  const container = isContainer(c);
  const warns = stats?.warnings ?? [];

  if (apiRef) apiRef.current = {
    selected: () => {
      const ks = [...(sel ? [pathKey(sel)] : []), ...extra.filter((k) => !sel || k !== pathKey(sel))];
      return ks.map((k) => k.split(".").map(Number));
    },
    apply: (fn) => {
      const ks = [...(sel ? [pathKey(sel)] : []), ...extra.filter((k) => !sel || k !== pathKey(sel))];
      const next = fn(viewRef.current, ks.map((k) => k.split(".").map(Number)));
      if (next !== viewRef.current) save(next);
    },
    del: act.del, up: act.up, down: act.down, props: openProps, undo: act.undo, redo: act.redo, fit: () => onFit?.(),
  };

  return (
    <div className="panel">
      {/* yorliqlar qatori (onlayn tartib): Показать все изображение, Служебные команды (F4), Состояние (F9), Переменные,
          Инструменты, so'ng XncPanel tugmalari (Пересчитать параметричность, Справка, Экспорт, Импорт, «Шаблоны»);
          xatolar paneli — bizning qo'shimcha, oxirida */}
      {tabs(<>
        {onFit && <IconBtn icon={Maximize} title={t("xnc.fit")} onClick={onFit} testid="xnc-fit" />}
        <IconBtn icon={ListTree} title={t("xnc.svc")} active={svc} onClick={() => setSvc(!svc)} testid="xnc-svc" />
        <IconBtn icon={Activity} title={t("xnc.state")} onClick={() => setStateDlg(true)} testid="xnc-state-btn" />
        {onVars && <IconBtn icon={Variable} title={t("xnc.vars.title")} onClick={onVars} testid="xnc-vars" />}
        {onTools && <IconBtn icon={Wrench} title={t("xnc.tools.title")} onClick={onTools} testid="xnc-tools" />}
        {right}
        <IconBtn icon={ListChecks} title={t("xnc.issues_panel")} active={showState} onClick={() => setShowState(!showState)}
          testid="xnc-issues-btn" label={issues.length ? String(issues.length) : undefined} />
      </>)}
      <div className="xnc-editor" {...scopeProps("xnc")}>
        <div className="xnc-palette">
          {/* ikki ustun: chapda xizmat buyruqlari (F4), o'ngda geometriya; guruhlar orasida bo'shliq (onlayn joylashuv) */}
          {[palItems.filter((p) => p.svc), palItems.filter((p) => !p.svc)].map((col, ci) => (
            <div key={ci} className={cx("pal-col", ci === 0 && !svc && "pal-col-off")}>
              {col.map((p, i) => (
                <button key={p.cmd} type="button" className={cx("pal", i > 0 && PAL_GROUP_START.has(p.cmd) && "pal-gap")} onClick={() => add(p)}
                  title={t(`xnc.cmd.${p.cmd}`, { defaultValue: p.cmd })} data-testid={`pal-${p.cmd}`}>{p.svc ? p.short : <CmdIcon cmd={p.cmd} />}</button>
              ))}
            </div>
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
        {drawing(hl, pickFromDrawing)}
        <div className="xnc-prog">
          {/* «Программа» sarlavhasi (onlayn tartib): ← (darajadan chiqish), → (blok ichiga), ↑, ↓, Удалить, Свойства, Отменить,
              Вернуть, Выключить; bizning qo'shimchalar (yangi buyruq blok ichiga, Клонировать) — oxirida */}
          <div className="toolbar prog-bar">
            <b>{t("xnc.program")}</b><span className="grow" />
            <IconBtn icon={IndentDecrease} title={`${t("xnc.outdent")} (Ctrl+←)`} onClick={act.outdent} disabled={!sel || sel.length < 2} testid="xnc-outdent" />
            <IconBtn icon={IndentIncrease} title={`${t("xnc.indent")} (Ctrl+→)`} onClick={act.indent} testid="xnc-indent"
              disabled={!sel || sel[sel.length - 1] === 0 || !isContainer(getAt(view, [...sel.slice(0, -1), sel[sel.length - 1] - 1]))} />
            <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={act.up} disabled={!sel} testid="xnc-up" />
            <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={act.down} disabled={!sel} testid="xnc-down" />
            <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} color="#c0392b" onClick={act.del} disabled={!sel} testid="xnc-delete" />
            <IconBtn icon={Settings2} title={`${t("app.properties")} (Ctrl+Space)`} onClick={openProps} disabled={!sel} testid="xnc-props-btn" />
            <IconBtn icon={Undo2} title={`${t("menu.undo")} (Ctrl+Z)`} onClick={act.undo} testid="xnc-undo" />
            <IconBtn icon={Redo2} title={`${t("menu.redo")} (Ctrl+Y)`} onClick={act.redo} testid="xnc-redo" />
            <IconBtn icon={EyeOff} title={`${t("xnc.disable")} (Ctrl+D)`} onClick={act.toggle} disabled={!sel} active={selCmd?.enabled === false}
              testid="xnc-toggle" />
            <Sep />
            <IconBtn icon={CornerDownRight} title={t("xnc.inside")} active={inside} onClick={() => setInside(!inside)}
              disabled={!container} testid="xnc-inside" />
            <IconBtn icon={Copy} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!sel} testid="xnc-clone" />
          </div>
          <div ref={listRef} className="scroll prog-list prog-tree" data-testid="xnc-program" onContextMenu={(e) => {
            // o'ng tugma qatorni tanlaydi (agar u tanlovda bo'lmasa), so'ng menyu
            const row = (e.target as HTMLElement).closest<HTMLElement>("[data-testid^=prog-item-]");
            const k = row?.dataset.testid?.slice("prog-item-".length);
            if (k && !(sel && pathKey(sel) === k) && !extra.includes(k)) select(k.split(".").map(Number));
            ctx.open(e);
          }} title={`${t("xnc.dnd_hint")} ${t("xnc.props_hint")}`}>
            {rows.map((r) => {
              const k = pathKey(r.path);
              const isSel = samePath(sel, r.path);
              const block = isContainer(r.cmd);
              const errs = errByKey.get(k);
              // yig'ilgan blok ichida xato bo'lsa — blok qatori ham belgilanadi
              const errIn = !errs && r.collapsed && errKeys.some((q) => q.startsWith(`${k}.`));
              return (
                <div key={k} className={cx("prog-row", isSel && "prog-sel", !isSel && extra.includes(k) && "prog-sel2", r.cmd.enabled === false && "prog-off",
                  (errs || errIn) && "prog-err")} data-err={errs ? "1" : errIn ? "in" : undefined}
                  style={{ paddingLeft: 2 + r.depth * 16 }} data-testid={`prog-item-${k}`} data-depth={r.depth}
                  {...dnd.rowProps(r.path, r.cmd)}
                  onClick={(e) => clickRow(r.path, e)} onDoubleClick={() => { select(r.path); setTimeout(openProps, 0); }}>
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
                  {(errs || errIn) && <span className="prog-err-ico" data-testid={`prog-err-${k}`}
                    title={errs ? errs.join("\n") : t("xnc.err_inside")}>✖</span>}
                </div>
              );
            })}
            {!view.length && <div className="muted" style={{ padding: 6 }}>{t("xnc.empty")}</div>}
          </div>
          {ctx.node}
          {stateDlg && <StateDialog op={op} prog={view} onClose={() => setStateDlg(false)} />}
          {showState && (
            <div className="prog-state" data-testid="xnc-state">
              <div>{t("xnc.stats_line", { d: stats?.drills ?? 0, m: stats?.mill_m ?? 0, s: stats?.saw_m ?? 0 })}</div>
              {warns.length === 0
                ? (issues.length === 0 && <div className="good">{t("xnc.state_ok")}</div>)
                : <><div className="bad">{t("xnc.state_n", { n: stats?.errors ?? warns.length })}</div>
                    {warns.map((w, i) => {
                      const src = stats?.warning_src?.[i]?.[0];
                      const p = src ? src.split(".").map(Number) : null;
                      const ok = !!p && p.every((n) => Number.isInteger(n) && n >= 0) && !!getAt(view, p);
                      return <div key={i} className={cx("bad", ok && "xs-link")} title={ok ? t("xs.issues.go") : undefined}
                        onClick={ok ? () => pickIssue(p!) : undefined}>• {w}</div>;
                    })}</>}
              <XncIssues issues={issues} turn={stats?.constraint_turn} onPick={pickIssue} />
            </div>
          )}
          {c && sel && propsOpen && (
            <Modal title={t("xnc.props_title", { name: t(`xnc.cmd.${c.cmd}`, { defaultValue: c.cmd }) })} onClose={cancelProps}
              width={460} scope="xncprops" testid="xnc-props"
              footer={<>
                <button type="button" className="btn btn-primary" data-testid="xnc-props-ok" onClick={() => { propsNew.current = false; setPropsOpen(false); }}>{t("app.ok")}</button>
                <button type="button" className="btn" data-testid="xnc-props-cancel" onClick={cancelProps}>{t("app.cancel")}</button>
              </>}>
            <div className="prog-edit" ref={editRef} data-testid="xnc-edit">
              <div className="prog-edit-scroll">
                {orderedParams(c.params).map(([k, v], i, arr) => (
                  <div key={`${pathKey(sel)}-${c.cmd}-${k}`}>
                    {ARRAY_KEYS.has(k) && (i === 0 || !ARRAY_KEYS.has(arr[i - 1][0])) && <div className="form-h prog-group">{t("xnc.array")}</div>}
                    <ParamRow cmd={c.cmd} k={k} v={v} text={isTextParam(c, k)} toolOpts={toolOpts} onVars={onVars} ctx={exprCtx}
                      disabled={k === "Z" && "M" in c.params && String(c.params.M).toLowerCase() !== "false"}
                      onChange={(nv) => upd((cc) => ({ params: { ...cc.params, [k]: nv, ...toolExtra(cc.cmd, k, nv) } }))}
                      onDelete={() => upd((cc) => { const pr = { ...cc.params }; delete pr[k]; return { params: pr }; })} />
                  </div>
                ))}
              </div>
              <div className="row gap">
                <span className="pk">{t("xnc.comment")}</span>
                <LazyInput key={`${pathKey(sel)}-comment`} className="inp w100" placeholder={t("xnc.comment")} value={c.comment}
                  onCommit={(v) => upd(() => ({ comment: v }))} />
              </div>
              {/* bizning qo'shimcha: yangi parametr qo'shish — «Коментарий» dan keyin (onlayn maydonlar tartibi buzilmaydi) */}
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
            </div>
            </Modal>
          )}
        </div>
      </div>
    </div>
  );
}


/** F9 «Состояние»: detal o'lchami (DX / DY / DZ), koordinatalar boshi va dasturdagi asboblar (nomi, diametri, izohi).
 *  Joriy pozitsiya (CX / CY …) bajarilish holatini talab qiladi — hozircha ko'rsatilmaydi. */
function StateDialog({ op, prog, onClose }: { op: Operation; prog: XncCommand[]; onClose: () => void }) {
  const { t } = useTranslation();
  const x = op.xnc!;
  const tools: XncCommand[] = [];
  const walk = (l: XncCommand[]) => l.forEach((c) => { if (c.cmd === "Tool") tools.push(c); walk(c.children ?? []); });
  walk(prog);
  return (
    <Modal title={t("xnc.state_title")} onClose={onClose} width={440} scope="xnc-state" testid="xnc-state-dialog"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} testid="xnc-state-ok" />}>
      <div className="row gap" style={{ alignItems: "flex-start" }}>
        <table className="simple xs-tbl">
          <thead><tr><th colSpan={2}>{t("xnc.state_size")}</th></tr></thead>
          <tbody>
            <tr><td>DX</td><td className="num">{x.length}</td></tr>
            <tr><td>DY</td><td className="num">{x.width}</td></tr>
            <tr><td>DZ</td><td className="num">{x.thickness}</td></tr>
          </tbody>
        </table>
        <table className="simple xs-tbl">
          <thead><tr><th colSpan={2}>{t("xnc.origin")}</th></tr></thead>
          <tbody>
            <tr><td colSpan={2}>{t(`xnc.origin_v.${x.origin}`)}</td></tr>
          </tbody>
        </table>
      </div>
      <table className="simple xs-tbl" style={{ marginTop: 8, width: "100%" }} data-testid="xnc-state-tools">
        <thead>
          <tr><th colSpan={3}>{t("xnc.tools.title")}</th></tr>
          <tr><th>{t("xnc.state_tname")}</th><th>{t("xnc.state_tdia")}</th><th>{t("xnc.comment")}</th></tr>
        </thead>
        <tbody>
          {tools.map((c, i) => (
            <tr key={i}><td>{String(c.params.N ?? "")}</td><td className="num">{String(c.params.D ?? "")}</td><td>{c.comment}</td></tr>
          ))}
          {!tools.length && <tr><td colSpan={3} className="muted">{t("app.no_rows")}</td></tr>}
        </tbody>
      </table>
    </Modal>
  );
}
