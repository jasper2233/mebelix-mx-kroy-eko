// Detallar paneli → «XNC Редактор»: tanlangan detal ishlovi alohida oynada (onlayn tizimdagidek).
//   Yorliqlar: «XNC Редактор» (dastur + chizma, o'ngda «Сверление» ro'yxati) va «Чертеж» (o'lchamli chizma, teshiklar jadvali, shtamp).
//   Yuqori asboblar paneli onlayn tartibida: Обратная сторона, Свойства, Начало координат, Поворот, Горизонтальное / Вертикальное
//   отзеркаливание (butun dastur), Перенос выделенных элементов с копированием, Горизонтальное / Вертикальное отзеркаливание выделенных
//   элементов с копированием, Отменить / Вернуть, Удалить, Вверх / Вниз, Инструменты, Показать все изображение, Настройки, Справка.
//   «Ok» — saqlangan holda yopadi; «Отмена» — oyna ochilgandagi holatga qaytaradi (yaratilgan XNC o'chiriladi, dastur va parametrlar tiklanadi).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowDown, ArrowUp, CircleQuestionMark, CopyPlus, TrianglesCenterlineDashedVertical as MirrorHIcon, TrianglesCenterlineDashedHorizontal as MirrorVIcon, Maximize, Redo2, Settings2, SquarePen,
  Trash, Undo2, Wrench, RotateCw, Crosshair, Layers } from "lucide-react";
import { call, useXncStats } from "../../api/hooks";
import { del, get, patch } from "../../api/client";
import type { Project, XNCParams, XncCommand } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, IconBtn, Modal, Sel } from "../../shared/ui";
import { XncPanel } from "./XncPanel";
import type { XncProgApi } from "./XncProgramTab";
import { XncToolsDialog } from "./XncVarsTools";
import { XncSettingsDialog } from "./XncSettings";
import { getAt } from "./treeOps";
import { mirrorCmd, mirrorProgram, shiftCmd } from "./xncTransform";
import { usePanelOn, useXncTools, type Plane, type XncToolRow } from "./xncSettingsApi";

const CMD_OF: Record<Plane, string> = {
  front: "DrillFront", left: "DrillLeft", right: "DrillRight", top: "DrillTop", bottom: "DrillBottom",
};
const ORIGINS = ["LT", "LB", "RT", "RB"] as const;

export function PartXncDialog({ project, opId, created, onClose }: {
  project: Project; opId: string; created: boolean; onClose: () => void;
}) {
  const { t } = useTranslation();
  const ui = useUI();
  const op = project.operations.find((o) => o.id === opId);
  // ochilgandagi holat («Отмена» uchun): dastur va oynadan o'zgartiriladigan parametrlar
  const snap = useRef<Partial<XNCParams> | null>(null);
  if (snap.current === null && op?.xnc) {
    const x = op.xnc;
    snap.current = JSON.parse(JSON.stringify({ program: x.program, face_side: x.face_side, origin: x.origin, rotation: x.rotation }));
  }
  useEffect(() => {
    const prev = useUI.getState().xncTab;
    ui.set({ xncTab: "program" });
    return () => ui.set({ xncTab: prev });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const toolsQ = useXncTools();
  const drillPanel = usePanelOn("drill");          // «Палитра» → «Сверление» o'chirilsa — o'ng panel yashirinadi
  const tools = useMemo(() => toolsQ.data?.tools ?? [], [toolsQ.data]);
  const [drill, setDrill] = useState<XncToolRow | null>(null);
  const [tab, setTab] = useState<"editor" | "sheet">("editor");
  // «Чертеж» → «Операция»: detalning barcha XNC ishlovlari (yuz / orqa tomon) — onlayn tizimdagidek tanlanadi
  const partOps = useMemo(() => {
    const pt = project.operations.flatMap((o) => o.parts).find((q) => q.xnc_op_ids.includes(opId));
    const ids = pt ? pt.xnc_op_ids : [opId];
    return ids.map((id) => project.operations.find((o) => o.id === id)).filter((o): o is NonNullable<typeof o> => !!o?.xnc);
  }, [project.operations, opId]);
  const [sheetOp, setSheetOp] = useState(opId);
  const [sheetTick, setSheetTick] = useState(0);
  const [dlg, setDlg] = useState<"" | "move" | "tools" | "settings">("");
  const api = useRef<XncProgApi | null>(null);
  const stamp = useMemo(() => JSON.stringify(op?.xnc ?? null), [op?.xnc]);
  const stats = useXncStats(project.id, opId, stamp);

  const cancel = async () => {
    if (created) await call(() => del(`/projects/${project.id}/operations/${opId}`));
    else if (op?.xnc && snap.current) {
      const cur = { program: op.xnc.program, face_side: op.xnc.face_side, origin: op.xnc.origin, rotation: op.xnc.rotation };
      if (JSON.stringify(cur) !== JSON.stringify(snap.current))
        await call(() => patch(`/projects/${project.id}/operations/${opId}`, { xnc: snap.current }));
    }
    onClose();
  };
  if (!op?.xnc) return null;
  const x = op.xnc;
  const px = (f: Partial<XNCParams>) => void call(() => patch(`/projects/${project.id}/operations/${opId}`, { xnc: f }));
  const addCmd = (c: XncCommand) => px({ program: [...x.program, c] });
  // tanlangan buyruqlar nusxasi (akslantirilgan / siljitilgan) — dastur oxiriga (onlayn tizimdagidek)
  const copySelected = (f: (c: XncCommand) => XncCommand[]) => api.current?.apply((prog, sel) => {
    const src = sel.map((p) => getAt(prog, p)).filter((c): c is XncCommand => !!c);
    if (!src.length) { ui.toast(t("xnc.tb.select_first"), "info"); return prog; }
    return [...prog, ...src.flatMap((c) => f(JSON.parse(JSON.stringify(c)) as XncCommand))];
  });
  const toolLabel = (r: XncToolRow) => `Ø${r.d}${t("u.mm")} ${t(`xnc.pdrill.plane.${r.plane}`)}`;
  const head = `DX=${x.length} DY=${x.width} DZ=${x.thickness} ${t(x.face_side ? "xnc.face" : "xnc.back_side")}`
    // onlayndagidek: «(По размеру детали (с кромкой))» — loyihaning detal kiritish rejimi nomi
    + (x.by_part_size ? ` (${t(`settings.im.${project.size_mode}`, { defaultValue: t("xnc.by_part") })})` : "");
  const msgs = [...(stats.data?.warnings ?? []), ...(stats.data?.constraint_issues ?? []).map((i) => i.text)];
  const toolbar = (
    <div className="pxd-toolbar" data-testid="pxd-toolbar">
      <IconBtn icon={Layers} title={t("xnc.tb.back_side")} active={!x.face_side} onClick={() => px({ face_side: !x.face_side })} testid="pxd-back" />
      <IconBtn icon={SquarePen} title={`${t("app.properties")} [CTRL]+[SPACE]`} onClick={() => api.current?.props()} testid="pxd-props" />
      <span className="pxd-sep" />
      <IconBtn icon={Crosshair} title={t("xnc.origin")} onClick={() => px({ origin: ORIGINS[(ORIGINS.indexOf(x.origin) + 1) % 4] })} testid="pxd-origin-next" />
      <Sel<string> value={x.origin} width={58} testid="pxd-origin" onChange={(v) => px({ origin: v as XNCParams["origin"] })}
        options={ORIGINS.map((o) => ({ value: o, label: t(`xnc.tb.origin.${o}`) }))} />
      <IconBtn icon={RotateCw} title={t("xnc.rotation")} onClick={() => px({ rotation: ((x.rotation + 90) % 360) as XNCParams["rotation"] })} testid="pxd-rot-next" />
      <Sel<string> value={String(x.rotation)} width={58} testid="pxd-rotation" onChange={(v) => px({ rotation: Number(v) as XNCParams["rotation"] })}
        options={[0, 90, 180, 270].map((v) => ({ value: String(v), label: `${v}°` }))} />
      <IconBtn icon={MirrorHIcon} title={t("xnc.mirror_h")} testid="pxd-mirror-h"
        onClick={() => api.current?.apply((prog) => mirrorProgram(prog, "x"))} />
      <IconBtn icon={MirrorVIcon} title={t("xnc.mirror_v")} testid="pxd-mirror-v"
        onClick={() => api.current?.apply((prog) => mirrorProgram(prog, "y"))} />
      <span className="pxd-sep" />
      <IconBtn icon={CopyPlus} title={t("xnc.tb.move_copy")} onClick={() => setDlg("move")} testid="pxd-move-copy" />
      <IconBtn icon={MirrorHIcon} title={t("xnc.tb.mirror_h_copy")} testid="pxd-mirror-h-copy" color="#1f7a3a"
        onClick={() => copySelected((c) => [mirrorCmd(c, "x")])} />
      <IconBtn icon={MirrorVIcon} title={t("xnc.tb.mirror_v_copy")} testid="pxd-mirror-v-copy" color="#1f7a3a"
        onClick={() => copySelected((c) => [mirrorCmd(c, "y")])} />
      <span className="pxd-sep" />
      <IconBtn icon={Undo2} title={`${t("menu.undo")} [CTRL]+[Z]`} onClick={() => api.current?.undo()} testid="pxd-undo" />
      <IconBtn icon={Redo2} title={`${t("menu.redo")} [CTRL]+[Y]`} onClick={() => api.current?.redo()} testid="pxd-redo" />
      <IconBtn icon={Trash} title={`${t("app.delete")} [DEL]`} onClick={() => api.current?.del()} color="#c0392b" testid="pxd-del" />
      <IconBtn icon={ArrowUp} title={`${t("app.move_up")}`} onClick={() => api.current?.up()} testid="pxd-up" />
      <IconBtn icon={ArrowDown} title={`${t("app.move_down")}`} onClick={() => api.current?.down()} testid="pxd-down" />
      <span className="pxd-sep" />
      <IconBtn icon={Wrench} title={t("xnc.tools.title")} onClick={() => setDlg("tools")} testid="pxd-tools" />
      <IconBtn icon={Maximize} title={t("xnc.fit")} onClick={() => api.current?.fit()} testid="pxd-fit" />
      <IconBtn icon={Settings2} title={t("menu.settings")} onClick={() => setDlg("settings")} testid="pxd-settings" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} [F1]`} onClick={() => ui.set({ section: "help" })} testid="pxd-help" />
    </div>
  );
  return (
    <Modal title={t("parts.xnc_editor")} onClose={() => void cancel()} width={1560} height={780} testid="part-xnc-dialog"
      footer={<>
        <span className="pxd-msg-label">{t("xnc.tb.messages")}</span>
        <select className="inp pxd-msgs" data-testid="pxd-messages" value="" onChange={() => undefined}>
          <option value="">{msgs.length ? t("xnc.tb.messages_n", { n: msgs.length }) : ""}</option>
          {msgs.map((m, i) => <option key={i} value={String(i)}>{m}</option>)}
        </select>
        <span className="grow" />
        <Btn kind="primary" label={t("app.ok")} onClick={onClose} testid="part-xnc-ok" />
        <Btn label={t("app.cancel")} onClick={() => void cancel()} testid="part-xnc-cancel" />
      </>}>
      <div className="part-xnc-body">
        <div className="part-xnc-main">
          <div className="pxd-tabs">
            <button type="button" className={tab === "editor" ? "pxd-tab on" : "pxd-tab"} onClick={() => setTab("editor")} data-testid="pxd-tab-editor">
              {t("parts.xnc_editor")}</button>
            <button type="button" className={tab === "sheet" ? "pxd-tab on" : "pxd-tab"} onClick={() => setTab("sheet")} data-testid="pxd-tab-sheet">
              {t("xnc.tb.sheet")}</button>
            <span className="grow" />
            {tab === "editor" && toolbar}
            {tab === "sheet" && (
              <span className="pxd-sheet-op">
                <span>{t("xnc.tb.operation")}</span>
                <Sel<string> value={partOps.some((o) => o.id === sheetOp) ? sheetOp : opId} width={260} testid="pxd-sheet-op" onChange={setSheetOp}
                  options={partOps.map((o, i) => ({ value: o.id, label: `${i + 1}: ${o.code ? `(${o.code}) ` : ""}${o.name}` }))} />
                <IconBtn icon={RotateCw} title={t("menu.refresh")} onClick={() => setSheetTick((n) => n + 1)} testid="pxd-sheet-refresh" />
                <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} [F1]`} onClick={() => ui.set({ section: "help" })} />
              </span>
            )}
          </div>
          {tab === "editor" ? <>
            <div className="pxd-head" data-testid="pxd-head">{head}</div>
            <div className="pxd-panel"><XncPanel project={project} op={op} progApi={api} hideTabs /></div>
          </> : <XncSheet project={project} opId={partOps.some((o) => o.id === sheetOp) ? sheetOp : opId}
            stamp={`${JSON.stringify(project.operations.find((o) => o.id === sheetOp)?.xnc ?? null)}|${sheetTick}`} />}
        </div>
        {drillPanel && <div className="part-xnc-drills" data-testid="part-xnc-drills">
          <div className="part-xnc-drills-h">{t("xnc.pdrill.title")}</div>
          {tools.map((r, i) => (
            <button key={i} type="button" className="linkbtn part-xnc-drill" onClick={() => setDrill(r)} data-testid={`pdrill-${i}`}>
              {r.comment ? <span className="muted">{r.comment} </span> : null}{toolLabel(r)}
            </button>
          ))}
          {!tools.length && <div className="muted">{t("app.no_rows")}</div>}
        </div>}
      </div>
      {drill && <DrillDialog tool={drill} tools={tools.filter((r) => r.plane === drill.plane)} dims={`DX=${x.length} DY=${x.width} DZ=${x.thickness}`}
        onClose={() => setDrill(null)} onOk={(c) => { addCmd(c); setDrill(null); }} />}
      {dlg === "move" && <MoveCopyDialog onClose={() => setDlg("")} onOk={(dx, dy, n) => {
        copySelected((c) => Array.from({ length: n }, (_, i) => shiftCmd(c, dx * (i + 1), dy * (i + 1)))); setDlg("");
      }} />}
      {dlg === "tools" && <XncToolsDialog onClose={() => setDlg("")} />}
      {dlg === "settings" && <XncSettingsDialog onClose={() => setDlg("")} />}
    </Modal>
  );
}

/** «Чертеж»: o'lchamli chizma, teshiklar jadvali, shtamp — serverdan (hisobotdagi XNC bo'limi asosida). */
function XncSheet({ project, opId, stamp }: { project: Project; opId: string; stamp: string }) {
  const { i18n } = useTranslation();
  const [html, setHtml] = useState("");
  useEffect(() => {
    let alive = true;
    get<string>(`/projects/${project.id}/operations/${opId}/xnc-sheet?lang=${i18n.language === "uz" ? "uz" : "ru"}`)
      .then((h) => alive && setHtml(h), () => alive && setHtml(""));
    return () => { alive = false; };
  }, [project.id, opId, stamp, i18n.language]);
  return <iframe title="xnc-sheet" className="pxd-sheet" srcDoc={html} sandbox="allow-same-origin allow-modals" data-testid="pxd-sheet" />;
}

/** «Перенос выделенных элементов с копированием»: siljish (ΔX, ΔY) va nusxalar soni. */
function MoveCopyDialog({ onClose, onOk }: { onClose: () => void; onOk: (dx: number, dy: number, n: number) => void }) {
  const { t } = useTranslation();
  const [dx, setDx] = useState("0");
  const [dy, setDy] = useState("0");
  const [n, setN] = useState("1");
  const num = (s: string) => Number(s.replace(",", ".")) || 0;
  return (
    <Modal title={t("xnc.tb.move_copy")} onClose={onClose} width={360} testid="pxd-move-dialog"
      footer={<><Btn kind="primary" label={t("app.ok")} onClick={() => onOk(num(dx), num(dy), Math.max(1, Math.round(num(n))))} testid="pxd-move-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="pdrill-form">
        <label className="pdrill-row"><span>ΔX ({t("u.mm")})</span><input className="inp" value={dx} onChange={(e) => setDx(e.target.value)} data-testid="pxd-move-dx" /></label>
        <label className="pdrill-row"><span>ΔY ({t("u.mm")})</span><input className="inp" value={dy} onChange={(e) => setDy(e.target.value)} data-testid="pxd-move-dy" /></label>
        <label className="pdrill-row"><span>{t("xnc.tb.copies")}</span><input className="inp" value={n} onChange={(e) => setN(e.target.value)} data-testid="pxd-move-n" /></label>
      </div>
    </Modal>
  );
}

/** Teshik oynasi: koordinatalar, chuqurlik, diametr (shu tekislik asboblaridan), massiv va izoh → bitta buyruq. */
function DrillDialog({ tool, tools, dims, onClose, onOk }: {
  tool: XncToolRow; tools: XncToolRow[]; dims: string; onClose: () => void; onOk: (c: XncCommand) => void;
}) {
  const { t } = useTranslation();
  const front = tool.plane === "front";
  const vert = tool.plane === "left" || tool.plane === "right";            // chap / o'ng yon: Y bo'yicha, top / bottom: X bo'yicha
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [z, setZ] = useState("dz/2");
  const [dp, setDp] = useState(tool.depth != null ? String(tool.depth) : "");
  const [d, setD] = useState(String(tool.d));
  const [ac, setAc] = useState("1");
  const [as, setAs] = useState("");
  const [av, setAv] = useState(false);
  const [comment, setComment] = useState("");
  const num = (s: string) => (s.trim() !== "" && !Number.isNaN(Number(s.replace(",", "."))) ? Number(s.replace(",", ".")) : s.trim());
  const ok = () => {
    const tl = tools.find((r) => String(r.d) === d) ?? tool;
    const dpv = dp.trim() === "" ? (tl.through ? "dz" : front ? 12 : 30) : num(dp);
    const params: Record<string, string | number> = front
      ? { X: num(x) === "" ? 0 : num(x), Y: num(y) === "" ? 0 : num(y), DP: dpv, T: tl.name, AC: num(ac) === "" ? 1 : num(ac),
          AS: num(as) === "" ? 32 : num(as), AV: av ? "true" : "false" }
      : vert ? { Y: num(y) === "" ? 0 : num(y), Z: num(z) === "" ? "dz/2" : num(z), DP: dpv, T: tl.name }
        : { X: num(x) === "" ? 0 : num(x), Z: num(z) === "" ? "dz/2" : num(z), DP: dpv, T: tl.name };
    onOk({ cmd: CMD_OF[tool.plane], params, comment, enabled: true, children: [] });
  };
  const row = (label: string, v: string, set: (s: string) => void, testid: string) => (
    <label className="pdrill-row"><span>{label}</span>
      <input className="inp" value={v} onChange={(e) => set(e.target.value)} data-testid={testid} /></label>
  );
  return (
    <Modal title={t(`xnc.cmd.${CMD_OF[tool.plane]}`)} onClose={onClose} width={460} testid="pdrill-dialog"
      footer={<><span className="muted grow">{dims}</span>
        <Btn kind="primary" label={t("app.ok")} onClick={ok} testid="pdrill-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="pdrill-form">
        {(front || !vert) && row(t("xnc.pdrill.x"), x, setX, "pdrill-x")}
        {(front || vert) && row(t("xnc.pdrill.y"), y, setY, "pdrill-y")}
        {!front && row(t("xnc.pdrill.z"), z, setZ, "pdrill-z")}
        {row(t("xnc.pdrill.dp"), dp, setDp, "pdrill-dp")}
        <label className="pdrill-row"><span>{t("xnc.pdrill.d")}</span>
          <select className="inp" value={d} onChange={(e) => setD(e.target.value)} data-testid="pdrill-d">
            {[...new Set(tools.map((r) => String(r.d)))].map((v) => <option key={v} value={v}>{v}</option>)}
          </select></label>
        {front && <>
          <div className="form-h">{t("xnc.pdrill.array")}</div>
          {row(t("xnc.pdrill.ac"), ac, setAc, "pdrill-ac")}
          {row(t("xnc.pdrill.as"), as, setAs, "pdrill-as")}
          <Check checked={av} onChange={setAv} label={t("xnc.pdrill.av")} />
        </>}
        <label className="pdrill-row"><span>{t("xnc.pdrill.comment")}</span>
          <input className="inp" value={comment} onChange={(e) => setComment(e.target.value)} /></label>
      </div>
    </Modal>
  );
}
