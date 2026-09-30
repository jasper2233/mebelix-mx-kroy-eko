// XNC — Обработка (UI_SPEC §7): Параметры | Шаблон (dastur) | Стоимость.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp, CircleQuestionMark, Copy, Plus, Trash } from "lucide-react";
import { call, useXncStats } from "../../api/hooks";
import { get, patch } from "../../api/client";
import type { Operation, Project, XNCParams, XncCommand } from "../../api/types";
import { useUI, type XncTab } from "../../store/ui";
import { askText } from "../../shared/dialogs";
import { Area, Btn, Check, Field, IconBtn, Num, Sel, Tabs, cx, money } from "../../shared/ui";

const PALETTE: { cmd: string; short: string; params: Record<string, string | number> }[] = [
  { cmd: "Com", short: "Com", params: {} }, { cmd: "Par", short: "Par", params: { name: "p1", value: 0 } },
  { cmd: "Var", short: "Var", params: { name: "v1", value: "dz" } }, { cmd: "Set", short: "Set", params: { name: "v1", value: 0 } },
  { cmd: "If", short: "IF", params: { cond: "dx>500" } }, { cmd: "Else", short: "Else", params: {} },
  { cmd: "While", short: "WD", params: { cond: "" } }, { cmd: "DoWhile", short: "DW", params: { cond: "" } },
  { cmd: "Break", short: "Brk", params: {} }, { cmd: "Continue", short: "Con", params: {} },
  { cmd: "Sub", short: "Sub", params: { name: "s1" } }, { cmd: "Call", short: "Call", params: { name: "s1" } },
  { cmd: "Ret", short: "Ret", params: {} }, { cmd: "Msg", short: "Msg", params: { text: "" } },
  { cmd: "Err", short: "Err", params: { text: "" } }, { cmd: "Tool", short: "Tool", params: { N: "Bore8", D: 8 } },
  { cmd: "DrillFront", short: "⊙", params: { X: 50, Y: 50, DP: 12, T: "Bore8" } },
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
  { cmd: "MillRect", short: "M▭", params: { X: 10, Y: 10, L: 100, W: 50, D: 8 } },
  { cmd: "MillEllipse", short: "M◯", params: { X: 100, Y: 100, A: 80, B: 40 } },
  { cmd: "Groove", short: "Paz", params: { X1: 0, Y1: 16, X2: "dx", Y2: 16, DP: 8, W: 4 } },
  { cmd: "Origin", short: "O", params: { X: 0, Y: 0 } },
];

/** Matn maydoni: yozish lokal (tez), serverga — Enter / fokus chiqishi / 0.7 s pauzadan keyin. */
function LazyInput({ value, onCommit, className, placeholder }: {
  value: string; onCommit: (v: string) => void; className?: string; placeholder?: string;
}) {
  const [v, setV] = useState(value);
  const [focused, setFocused] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const last = useRef(value);
  useEffect(() => { if (!focused) { setV(value); last.current = value; } }, [value, focused]);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const commit = (nv: string) => {
    window.clearTimeout(timer.current);
    if (nv !== last.current) { last.current = nv; onCommit(nv); }
  };
  return (
    <input className={className} placeholder={placeholder} value={v}
      onFocus={() => setFocused(true)}
      onBlur={() => { setFocused(false); commit(v); }}
      onChange={(e) => {
        const nv = e.target.value;
        setV(nv);
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => commit(nv), 700);
      }}
      onKeyDown={(e) => { if (e.key === "Enter") commit(v); }} />
  );
}

function parseParam(raw: string): string | number {
  const n = Number(raw.replace(",", "."));
  return raw.trim() !== "" && !Number.isNaN(n) ? n : raw;
}

function useSvg(path: string, stamp: unknown) {
  const [svg, setSvg] = useState("");
  useEffect(() => { let alive = true; void get<string>(path).then((s) => alive && setSvg(s)).catch(() => setSvg("")); return () => { alive = false; }; },
    [path, stamp]);
  return svg;
}

export function XncPanel({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const x = op.xnc!;
  const stamp = useMemo(() => JSON.stringify([op.xnc, project.operations.filter((o) => o.type === "EL").map((o) => o.el)]), [op.xnc, project.operations]);
  const svg = useSvg(`/projects/${project.id}/operations/${op.id}/xnc.svg?width=520`, stamp);
  const stats = useXncStats(project.id, op.id, stamp);
  const px = (f: Partial<XNCParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { xnc: f }));
  const part = project.operations.flatMap((o) => o.parts.map((p) => ({ o, p }))).find(({ p }) => p.xnc_op_ids.includes(op.id));
  const prod = part ? project.products.find((pp) => pp.id === part.p.product_id) : undefined;
  const [sel, setSel] = useState<number | null>(null);
  const prog = x.program;
  // oxirgi yuborilgan dastur (javob kelguncha ketma-ket o'zgarishlar bir-birini o'chirmasin)
  const progRef = useRef(prog);
  useEffect(() => { progRef.current = prog; }, [prog]);
  const saveProg = (pr: XncCommand[]) => { progRef.current = pr; px({ program: pr }); };

  const tabs = (
    <Tabs<XncTab> value={ui.xncTab} onChange={(k) => ui.set({ xncTab: k })} tabs={[
      { key: "params", label: t("cs.tab.params") }, { key: "program", label: t("xnc.tab.program"), testid: "xnc-tab-program" },
      { key: "cost", label: t("xnc.tab.cost") }]}
      right={<IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />} />
  );
  const drawing = <div className="xnc-draw" dangerouslySetInnerHTML={{ __html: svg }} />;

  if (ui.xncTab === "program") {
    const c = sel !== null ? prog[sel] : null;
    const add = (tpl: (typeof PALETTE)[number]) => {
      const cmd: XncCommand = { cmd: tpl.cmd, params: { ...tpl.params }, comment: "", children: [] };
      const cur = progRef.current;
      const at = sel === null ? cur.length : Math.min(sel + 1, cur.length);
      const pr = [...cur.slice(0, at), cmd, ...cur.slice(at)];
      saveProg(pr); setSel(at);
    };
    const move = (d: -1 | 1) => {
      if (sel === null) return;
      const j = sel + d;
      const cur = progRef.current;
      if (j < 0 || j >= cur.length) return;
      const pr = [...cur]; [pr[sel], pr[j]] = [pr[j], pr[sel]]; saveProg(pr); setSel(j);
    };
    const updCmd = (f: (cc: XncCommand) => Partial<XncCommand>, at: number | null = sel) => {
      const cur = progRef.current;
      if (at === null || !cur[at]) return;
      saveProg(cur.map((cc, i) => (i === at ? { ...cc, ...f(cc) } : cc)));
    };
    return (
      <div className="panel">
        {tabs}
        <div className="xnc-editor">
          <div className="xnc-palette">
            {PALETTE.map((p) => (
              <button key={p.cmd} type="button" className="pal" title={t(`xnc.cmd.${p.cmd}`, { defaultValue: p.cmd })} onClick={() => add(p)}
                data-testid={`pal-${p.cmd}`}>{p.short}</button>
            ))}
          </div>
          {drawing}
          <div className="xnc-prog">
            <div className="toolbar">
              <b>{t("xnc.program")}</b><span className="grow" />
              <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(-1)} disabled={sel === null} />
              <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(1)} disabled={sel === null} />
              <IconBtn icon={Copy} title={t("app.clone")} disabled={sel === null}
                onClick={() => { const cur = progRef.current; if (sel === null || !cur[sel]) return; const pr = [...cur]; pr.splice(sel + 1, 0, JSON.parse(JSON.stringify(cur[sel]))); saveProg(pr); }} />
              <IconBtn icon={Trash} title={t("app.delete")} disabled={sel === null} color="#c0392b"
                onClick={() => { if (sel === null) return; saveProg(progRef.current.filter((_, i) => i !== sel)); setSel(null); }} />
            </div>
            <div className="scroll prog-list" data-testid="xnc-program">
              {prog.map((cc, i) => (
                <div key={i} className={cx("prog-item", sel === i && "prog-sel")} onClick={() => setSel(i)}>
                  <b>{cc.cmd}</b> {Object.entries(cc.params).map(([k, v]) => `${k}=${v}`).join(" ")}
                  {cc.comment && <span className="muted"> ; {cc.comment}</span>}
                </div>
              ))}
              {!prog.length && <div className="muted">{t("xnc.empty")}</div>}
            </div>
            {c && (
              <div className="prog-edit">
                <div className="form-h">{c.cmd}</div>
                {Object.entries(c.params).map(([k, v]) => (
                  <div key={k} className="row gap">
                    <span className="pk">{k}</span>
                    <LazyInput key={`${sel}-${k}`} className="inp" value={String(v)}
                      onCommit={(raw) => updCmd((cc) => ({ params: { ...cc.params, [k]: parseParam(raw) } }))} />
                    <IconBtn icon={Trash} title={t("app.delete")}
                      onClick={() => updCmd((cc) => { const pr = { ...cc.params }; delete pr[k]; return { params: pr }; })} />
                  </div>
                ))}
                <div className="row gap">
                  <Btn small icon={Plus} label={t("xnc.add_param")} onClick={async () => {
                    const k = await askText(t("xnc.param_name"), "");
                    if (k) updCmd((cc) => ({ params: { ...cc.params, [k]: 0 } }));
                  }} />
                </div>
                <LazyInput key={`${sel}-comment`} className="inp w100" placeholder={t("xnc.comment")} value={c.comment}
                  onCommit={(v) => updCmd(() => ({ comment: v }))} />
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
  if (ui.xncTab === "cost") {
    const s = stats.data;
    const cur = project.currency;
    return (
      <div className="panel">
        {tabs}
        <div className="form1 scroll" data-testid="xnc-cost">
          <Field label={t("xnc.drill_price")} unit={`${cur} × ${s?.drills ?? 0}`}><Num value={x.drill_price} min={0} onCommit={(v) => px({ drill_price: v ?? 0 })} /></Field>
          <Field label={t("xnc.mill_price")} unit={`${cur} × ${s?.mill_m ?? 0} ${t("u.m")}`}><Num value={x.mill_price_m} min={0} onCommit={(v) => px({ mill_price_m: v ?? 0 })} /></Field>
          <Field label={t("xnc.saw_price")} unit={`${cur} × ${s?.saw_m ?? 0} ${t("u.m")}`}><Num value={x.saw_price_m} min={0} onCommit={(v) => px({ saw_price_m: v ?? 0 })} /></Field>
          <Field label={t("xnc.extra")} unit={cur}><Num value={x.extra_cost} min={0} onCommit={(v) => px({ extra_cost: v ?? 0 })} /></Field>
          <Field label={t("xnc.unit_cost")} unit={cur}><span className="ro">{money(s?.unit_cost)}</span></Field>
          <Field label={t("xnc.qty")}><span className="ro">{x.qty}</span></Field>
          <Field label={t("xnc.op_cost")} unit={cur}><span className="ro">{money(s?.cost)}</span></Field>
        </div>
      </div>
    );
  }
  return (
    <div className="panel">
      {tabs}
      <div className="form2 scroll" data-testid="xnc-params">
        <div className="form-col">
          <Field label={t("xnc.product")}><span className="ro">{prod?.name ?? "—"}</span></Field>
          <Field label={t("xnc.material")}><span className="ro">{part?.o.name ?? "—"}</span></Field>
          <Field label={t("xnc.detail")}><span className="ro">{part ? `${part.p.uid} ${part.p.name}` : "—"}</span></Field>
          <Field label=" "><Check checked={x.by_part_size} label={t("xnc.by_part")} onChange={(v) => px({ by_part_size: v })} /></Field>
          <Field label="DX" unit={t("u.mm")}><Num value={x.length} min={0} onCommit={(v) => px({ length: v ?? 0 })} /></Field>
          <Field label="DY" unit={t("u.mm")}><Num value={x.width} min={0} onCommit={(v) => px({ width: v ?? 0 })} /></Field>
          <Field label="DZ" unit={t("u.mm")}><Num value={x.thickness} min={0} onCommit={(v) => px({ thickness: v ?? 16 })} /></Field>
          <Field label={t("xnc.qty")}><Num value={x.qty} min={1} onCommit={(v) => px({ qty: Math.round(v ?? 1) })} /></Field>
          <Field label=" "><Check checked={x.face_side} label={t("xnc.face")} onChange={(v) => px({ face_side: v })} /></Field>
          <Field label={t("xnc.rotation")}><Sel value={x.rotation} width={80} onChange={(v) => px({ rotation: v })}
            options={([0, 90, 180, 270] as const).map((v) => ({ value: v, label: `${v}°` }))} /></Field>
          <Field label={t("xnc.mirror")}><span className="checks">
            <Check checked={x.mirror_x} label="X" onChange={(v) => px({ mirror_x: v })} />
            <Check checked={x.mirror_y} label="Y" onChange={(v) => px({ mirror_y: v })} /></span></Field>
          <Field label={t("xnc.origin")}><Sel value={x.origin} width={80} onChange={(v) => px({ origin: v })}
            options={(["LT", "RT", "LB", "RB"] as const).map((v) => ({ value: v, label: v }))} /></Field>
          <Field label={t("xnc.cost")} unit={project.currency}><span className="ro">{money(op.cost_operation)}</span></Field>
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={3} onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
        </div>
        <div className="form-col">{drawing}</div>
      </div>
    </div>
  );
}
