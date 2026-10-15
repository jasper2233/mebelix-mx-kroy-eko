// Boshqaruv buyruqlari daraxt muharriri (W12: mahsulot «Программа» si): palitra Com Par Var Set If Else WD DW Brk Con Sub Call Ret Msg Err,
// ichma-ich daraxt (blok ichiga qo'shish, ko'chirish, chekinish), buyruq xossalari. Daraxt amallari — treeOps.ts (W1), parametr
// qatori — XncProgramTab.ParamRow. Geometriya buyruqlari yo'q. XNC «Шаблон» yorlig'idagi muharrir (XncProgramTab) alohida qoladi
// (W8 bilan parallel o'zgarmasligi uchun): ikkalasini birlashtirish — keyingi bosqich.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronRight, ChevronUp, Copy, CornerDownRight, IndentDecrease, IndentIncrease, Trash } from "lucide-react";
import type { XncCommand } from "../../api/types";
import { askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, cx } from "../../shared/ui";
import { LazyInput } from "./LazyInput";
import { PALETTE, ParamRow, defaultFor } from "./XncProgramTab";
import { defOf, isTextParam, missingKeys, summary } from "./xncSchema";
import { useTreeDnd } from "./treeDnd";
import {
  cloneAt, countAll, flatten, getAt, indent, insertAt, isContainer, moveSibling, outdent, pathKey, removeAt, reveal, samePath,
  updateAt, type Edit, type Path,
} from "./treeOps";
import "./xnc.css";

/** Mahsulot dasturi palitrasi: faqat boshqaruv buyruqlari; standart parametrlar mahsulotga mos (dx/dy/dz yo'q). */
const PRODUCT_DEFAULTS: Record<string, Record<string, string | number>> = {
  Var: { name: "v1", value: 0 }, If: { cond: "p1>0" },
};
const PRODUCT_PALETTE = PALETTE.filter((p) => p.svc).map((p) => ({ ...p, params: { ...p.params, ...(PRODUCT_DEFAULTS[p.cmd] ?? {}) } }));

export function ProgramEditor({ program, onSave, scope, testid = "pprog" }: {
  program: XncCommand[]; onSave: (p: XncCommand[]) => void; scope: string; testid?: string;
}) {
  const { t } = useTranslation();
  // `view` — optimistik dastur: server javobigacha ketma-ket o'zgarishlar bir-birini o'chirmasin (XNC muharriri kabi)
  const [view, setView] = useState<XncCommand[]>(program);
  const viewRef = useRef(view);
  viewRef.current = view;
  useEffect(() => setView(program), [program]);
  const [sel, setSel] = useState<Path | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const [inside, setInside] = useState(false);
  const editRef = useRef<HTMLDivElement>(null);

  const save = (pr: XncCommand[]) => { viewRef.current = pr; setView(pr); onSave(pr); };
  const commit = (e: Edit, keepInside = false) => {
    if (e.prog !== viewRef.current) save(e.prog);
    setSel(e.sel);
    if (e.sel) setCollapsed((c) => reveal(c, e.sel as Path));
    if (!keepInside) setInside(false);
  };
  const select = (p: Path | null) => { setSel(p); setInside(false); };
  const dnd = useTreeDnd(() => viewRef.current, (e) => commit(e), (p) => select(p));      // sudrab ko'chirish (W18)

  const rows = useMemo(() => flatten(view, collapsed), [view, collapsed]);
  const c = sel ? getAt(view, sel) : null;
  const idx = sel ? rows.findIndex((r) => samePath(r.path, sel)) : -1;

  const add = (tpl: (typeof PRODUCT_PALETTE)[number]) => {
    const cmd: XncCommand = { cmd: tpl.cmd, params: { ...tpl.params }, comment: "", enabled: true, children: [] };
    const cur = viewRef.current;
    const target = sel ? getAt(cur, sel) : null;
    let e: Edit;
    if (sel && target && inside && isContainer(target)) e = insertAt(cur, sel, undefined, cmd);
    else if (sel && target) e = insertAt(cur, sel.slice(0, -1), sel[sel.length - 1] + 1, cmd);
    else e = insertAt(cur, [], undefined, cmd);
    commit(e, true);
    setInside(isContainer(cmd));
  };
  const act = {
    up: () => sel && commit(moveSibling(viewRef.current, sel, -1)),
    down: () => sel && commit(moveSibling(viewRef.current, sel, 1)),
    indent: () => sel && commit(indent(viewRef.current, sel)),
    outdent: () => sel && commit(outdent(viewRef.current, sel)),
    clone: () => sel && commit(cloneAt(viewRef.current, sel)),
    del: () => sel && commit(removeAt(viewRef.current, sel)),
  };
  const toggle = (p: Path) => setCollapsed((cs) => {
    const n = new Set(cs);
    const k = pathKey(p);
    if (n.has(k)) n.delete(k); else n.add(k);
    return n;
  });
  const nav = (to: number) => { const r = rows[Math.max(0, Math.min(rows.length - 1, to))]; if (r) select(r.path); };
  const upd = (f: (cc: XncCommand) => Partial<XncCommand>, at: Path | null = sel) => {
    if (!at) return;
    commit({ prog: updateAt(viewRef.current, at, f), sel: at }, true);
  };

  useHotkeys(scope, {
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
    "ctrl+arrowup": act.up, "ctrl+arrowdown": act.down, "ctrl+arrowright": act.indent, "ctrl+arrowleft": act.outdent,
    "ctrl+k": act.clone, delete: act.del,
    "ctrl+space": () => editRef.current?.querySelector<HTMLInputElement | HTMLSelectElement>("input, select")?.focus(),
  });

  const container = isContainer(c);
  return (
    <div className="xnc-editor" {...scopeProps(scope)} data-testid={`${testid}-editor`}>
      <div className="xnc-palette">
        {PRODUCT_PALETTE.map((p) => (
          <button key={p.cmd} type="button" className="pal" onClick={() => add(p)}
            title={t(`xnc.cmd.${p.cmd}`, { defaultValue: p.cmd })} data-testid={`${testid}-pal-${p.cmd}`}>{p.short}</button>
        ))}
      </div>
      <div className="xnc-prog">
        <div className="toolbar prog-bar">
          <b>{t("pprog.program")}</b><span className="grow" />
          <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={act.up} disabled={!sel} testid={`${testid}-up`} />
          <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={act.down} disabled={!sel} testid={`${testid}-down`} />
          <IconBtn icon={IndentDecrease} title={t("xnc.outdent")} onClick={act.outdent} disabled={!sel || sel.length < 2} />
          <IconBtn icon={IndentIncrease} title={t("xnc.indent")} onClick={act.indent}
            disabled={!sel || sel[sel.length - 1] === 0 || !isContainer(getAt(view, [...sel.slice(0, -1), sel[sel.length - 1] - 1]))} />
          <IconBtn icon={CornerDownRight} title={t("xnc.inside")} active={inside} onClick={() => setInside(!inside)} disabled={!container}
            testid={`${testid}-inside`} />
          <IconBtn icon={Copy} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!sel} testid={`${testid}-clone`} />
          <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} color="#c0392b" onClick={act.del} disabled={!sel} testid={`${testid}-delete`} />
        </div>
        <div className="scroll prog-list prog-tree" style={{ minHeight: 160 }} data-testid={`${testid}-tree`}>
          {rows.map((r) => {
            const k = pathKey(r.path);
            const block = isContainer(r.cmd);
            return (
              <div key={k} className={cx("prog-row", samePath(sel, r.path) && "prog-sel", r.cmd.enabled === false && "prog-off")}
                style={{ paddingLeft: 2 + r.depth * 16 }} data-testid={`${testid}-item-${k}`} data-depth={r.depth}
                {...dnd.rowProps(r.path, r.cmd)}
                onClick={() => select(r.path)} onDoubleClick={() => r.hasChildren && toggle(r.path)}>
                {r.hasChildren
                  ? <button type="button" className="prog-chev" aria-label={r.collapsed ? t("xnc.expand") : t("xnc.collapse")}
                      onClick={(e) => { e.stopPropagation(); toggle(r.path); }}>
                      {r.collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                    </button>
                  : <span className="prog-chev-ph" />}
                <input type="checkbox" checked={r.cmd.enabled !== false} title={t("xnc.enabled")} onClick={(e) => e.stopPropagation()}
                  onChange={(e) => { const el = e.target; upd(() => ({ enabled: el.checked }), r.path); el.blur(); }} />
                <span className={cx("prog-txt", block && "prog-block")} title={summary(r.cmd)}>
                  <b>{r.cmd.cmd}</b> {summary(r.cmd)}
                  {r.cmd.comment && <span className="muted"> ; {r.cmd.comment}</span>}
                </span>
                {r.collapsed && <span className="prog-badge">{countAll(r.cmd.children)}</span>}
              </div>
            );
          })}
          {!view.length && <div className="muted" style={{ padding: 6 }}>{t("pprog.empty")}</div>}
        </div>
        {c && sel && (
          <div className="prog-edit" ref={editRef} data-testid={`${testid}-edit`}>
            <div className="form-h">{t(`xnc.cmd.${c.cmd}`, { defaultValue: c.cmd })} <span className="muted">({c.cmd})</span></div>
            <div className="prog-edit-scroll">
              {Object.entries(c.params).map(([k, v]) => (
                <ParamRow key={`${pathKey(sel)}-${c.cmd}-${k}`} cmd={c.cmd} k={k} v={v} text={isTextParam(c, k)}
                  onChange={(nv) => upd((cc) => ({ params: { ...cc.params, [k]: nv } }))}
                  onDelete={() => upd((cc) => { const pr = { ...cc.params }; delete pr[k]; return { params: pr }; })} />
              ))}
            </div>
            <div className="row gap">
              <select className="inp sel" value="" style={{ width: "100%" }} data-testid={`${testid}-add-param`}
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
            <LazyInput key={`${pathKey(sel)}-comment`} className="inp w100" placeholder={t("xnc.comment")} value={c.comment}
              onCommit={(v) => upd(() => ({ comment: v }))} />
          </div>
        )}
      </div>
    </div>
  );
}
