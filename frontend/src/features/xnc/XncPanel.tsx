// XNC — Обработка (UI_SPEC §7): Параметры | Шаблон (dastur) | Стоимость.
// «Шаблон» yorlig'i — XncProgramTab (ichma-ich daraxt), «Параметры» — o'lcham, Par kiritish (ParForm), shablonlar kutubxonasi
// (XncTemplates) va ishlov markazi postprotsessori (XncPostprocess).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, Coins, Download, Drill, FileCode, FileDown, FolderOpen, LibraryBig, Cpu, Link2, Unlink, Hash, FlipHorizontal2,
  FlipVertical2, Save, Settings2, SquarePen } from "lucide-react";
import { call, useXncStats } from "../../api/hooks";
import { api, download, get, patch, post, put } from "../../api/client";
import type { Operation, Project, XNCParams, XncStats } from "../../api/types";
import { useUI, type XncTab } from "../../store/ui";
import { Area, Btn, Check, Field, IconBtn, Modal, Num, Sel, Tabs, money } from "../../shared/ui";
import { askConfirm, showError } from "../../shared/dialogs";
import { LazyInput } from "./LazyInput";
import { ParForm } from "./ParForm";
import { XncIssues } from "./XncIssues";
import { XncProgramTab } from "./XncProgramTab";
import { XncDxfDialog } from "./XncDxf";
import { XncDrawing } from "./XncDrawing";
import { XncVarsDialog, XncToolsDialog } from "./XncVarsTools";
import { XncPostprocessDialog } from "./XncPostprocess";
import { XncTemplatesDialog } from "./XncTemplates";
import { XncSettingsDialog } from "./XncSettings";
import { PartProperties } from "../cs/PartDialogs";
import "./xnc.css";

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
  const [machine, setMachine] = useState(false);          // chizma stanokdagi (cheklov burishi bilan) holatda (W18)
  const [dims, setDims] = useState(false);                // eni / bo'yi yozuvlari (standart yo'q — onlayn ko'rinishdagi kabi)
  const [drawBox, setDrawBox] = useState({ w: 520, h: 0 }); // chizma maydoni (px): server minimal ko'rinadigan o'lchamlarni shu masshtabda oladi
  const svg = useSvg(`/projects/${project.id}/operations/${op.id}/xnc.svg?width=${drawBox.w}${drawBox.h ? `&height=${drawBox.h}` : ""}`
    + `${machine ? "&machine=true" : ""}${dims ? "&dims=true" : ""}`, stamp);
  const hasTurn = svg.includes('class="xnc-turn"');       // stanok cheklovi qo'shimcha burish bergan (server chizmaga belgi qo'yadi)
  const statsQ = useXncStats(project.id, op.id, stamp);
  // so'rov yangilanayotganda forma yo'qolib qolmasin — oxirgi muvaffaqiyatli natija
  const lastStats = useRef<XncStats | undefined>(undefined);
  if (statsQ.data) lastStats.current = statsQ.data;
  const stats = statsQ.data ?? lastStats.current;
  const px = (f: Partial<XNCParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { xnc: f }));
  const part = project.operations.flatMap((o) => o.parts.map((p) => ({ o, p }))).find(({ p }) => p.xnc_op_ids.includes(op.id));
  const prod = part ? project.products.find((pp) => pp.id === part.p.product_id) : undefined;
  const [dlg, setDlg] = useState<"" | "tpl" | "pp" | "dxf" | "pick" | "vars" | "tools" | "editor" | "props">("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [fitTick, setFitTick] = useState(0);              // «Показать все изображение»: chizmani maydonga qayta sig'dirish
  const link = (partId: string | null) => void call(() => post(`/projects/${project.id}/operations/${op.id}/xnc/link`, { part_id: partId }));
  const recode = async () => {                              // «Кодирование»: takror XNC kodlari -2, -3 … (butun loyiha)
    if (await askConfirm(t("xnc.recode_q"))) void call(() => post(`/projects/${project.id}/actions/recode-xnc`));
  };

  const saveDefaults = async () => {
    const r = await call(() => put("/settings/xnc_defaults/default", {
      drill_price: x.drill_price, mill_price_m: x.mill_price_m, saw_price_m: x.saw_price_m, extra_cost: x.extra_cost }));
    if (r) ui.toast(t("xnc.defaults_saved"), "ok");
  };
  // «Открыть»: dastur fayli (.xnc / .xml — <program> XML, .json — shablon fayli) joriy dastur o'rniga yuklanadi
  const openFile = async (f: File | undefined) => {
    if (!f) return;
    if (x.program.length && !(await askConfirm(t("xnc.file.replace_q")))) return;
    const fd = new FormData();
    fd.append("file", f);
    const r = await call(() => api<{ unknown: string[] }>(`/projects/${project.id}/operations/${op.id}/xnc/program-file`, { form: fd }));
    if (r) ui.toast(t("xnc.file.opened", { n: f.name }), r.unknown.length ? "info" : "ok",
      r.unknown.length ? [t("xnc.file.unknown", { tags: r.unknown.join(", ") })] : undefined);
  };
  // «Сохранить»: dastur faylga (.xnc; parametrli / shartli dastur — .xnc.json, shunda Par lar yo'qolmaydi)
  const saveFile = () => void download(`/projects/${project.id}/operations/${op.id}/xnc/program-file`, undefined,
    `${op.code || op.name || "xnc"}.xnc`).catch(showError);
  const lockSize = x.by_part_size && !!part;          // bog'langan detal o'lchami / soni — o'zgartirib bo'lmaydi (onlayndagidek)
  // DZ: detal bog'langanda material qalinligidan olinadi — o'zgartirib bo'lmaydi; faqat dastur DZ ni ataylab material
  // qalinligidan farqli saqlagan bo'lsa (korxona loyihalarida 32 mm li dasturlar bor, calc.sync_xnc ularga tegmaydi) — tahrirlanadi
  const matT = x.part_vars?.matThickness;
  const lockDz = lockSize && (matT === undefined || Math.abs(x.thickness - matT) < 1e-9);
  const tabs = (
    <Tabs<XncTab> value={ui.xncTab} onChange={(k) => ui.set({ xncTab: k })} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2 },
      { key: "program", label: t("xnc.tab.program"), icon: FileCode, testid: "xnc-tab-program" },
      { key: "cost", label: t("xnc.tab.cost"), icon: Coins }]}
      right={ui.xncTab === "cost" ? <>
        {/* «Стоимость»: faqat narxlarni standart sifatida saqlash va yordam */}
        <IconBtn icon={Save} title={t("xnc.save_defaults")} onClick={() => void saveDefaults()} testid="xnc-save-defaults" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </> : <>
        {/* tartib — xodimlar o'rgangan: detal tanlash, XNC Редактор, kodlash, bog'lanishni bekor qilish, detal xossalari,
            standart sifatida saqlash, faylni ochish / saqlash, yordam, PP, DXF; o'z qo'shimchamiz («Шаблоны») — oxirida */}
        <Btn small icon={Link2} label={t("xnc.pick_part")} onClick={() => setDlg("pick")} testid="xnc-pick-part" />
        <IconBtn icon={Drill} title={t("settings.page.xnc")} onClick={() => setDlg("editor")} testid="xnc-editor-settings" />
        <IconBtn icon={Hash} title={t("xnc.recode")} onClick={() => void recode()} />
        <IconBtn icon={Unlink} title={t("xnc.unlink_part")} onClick={() => link(null)} disabled={!part} testid="xnc-unlink" />
        <IconBtn icon={SquarePen} title={t("app.properties")} onClick={() => setDlg("props")} disabled={!part}
          testid="xnc-part-props" />
        <IconBtn icon={Save} title={t("xnc.save_defaults")} onClick={() => void saveDefaults()} testid="xnc-save-defaults" />
        <IconBtn icon={FolderOpen} title={t("xnc.file.open")} onClick={() => fileRef.current?.click()} testid="xnc-file-open" />
        <IconBtn icon={Download} title={t("xnc.file.save")} onClick={saveFile} testid="xnc-file-save" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
        <IconBtn icon={Cpu} title={t("xnc.pp.title")} onClick={() => setDlg("pp")} testid="xnc-pp" />
        <IconBtn icon={FileDown} title={t("xnc.dxf.import")} onClick={() => setDlg("dxf")} testid="xnc-dxf" />
        <Btn small icon={LibraryBig} label={t("xnc.templates")} onClick={() => setDlg("tpl")} testid="xnc-templates" />
        <input ref={fileRef} type="file" accept=".xnc,.xml,.json,application/xml,application/json" hidden data-testid="xnc-file-input"
          onChange={(e) => { void openFile(e.target.files?.[0]); e.target.value = ""; }} />
      </>} />
  );
  // chizma: dastur yorlig'ida tanlangan buyruqlar (`hl`) belgilanadi va chizmadan buyruq tanlanadi (`onPick`)
  const drawing = (hl?: string[], onPick?: (key: string, add: boolean) => void) => (
    <div className="xnc-draw-box">
      <div className="xnc-draw-bar row gap">
        <Check checked={dims} onChange={setDims} label={t("xnc.show_dims")} title={t("xnc.show_dims_hint")} testid="xnc-dims" />
        {(hasTurn || machine) && (
          <Check checked={machine} onChange={setMachine} label={t("xnc.machine_view")} title={t("xnc.machine_view_hint")} testid="xnc-machine-view" />
        )}
      </div>
      <XncDrawing svg={svg} fitTick={fitTick} hl={hl} onPick={onPick}
        onBox={(w, h) => setDrawBox((b) => (b.w === w && b.h === h ? b : { w, h }))} />
    </div>
  );
  const dialogs = (
    <>
      {dlg === "tpl" && <XncTemplatesDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "pp" && <XncPostprocessDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "dxf" && <XncDxfDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "vars" && <XncVarsDialog project={project} op={op} onClose={() => setDlg("")} />}
      {dlg === "tools" && <XncToolsDialog onClose={() => setDlg("")} />}
      {dlg === "editor" && <XncSettingsDialog onClose={() => setDlg("")} />}
      {dlg === "props" && part && <PartProperties project={project} op={part.o} part={part.p} onClose={() => setDlg("")} />}
      {dlg === "pick" && <PartPickDialog project={project} current={part?.p.id} onClose={() => setDlg("")}
        onPick={(id) => { link(id); setDlg(""); }} />}
    </>
  );

  if (ui.xncTab === "program") {
    return <><XncProgramTab key={op.id} project={project} op={op} drawing={drawing} tabs={tabs} stats={stats}
      onFit={() => setFitTick((n) => n + 1)} onVars={() => setDlg("vars")} onTools={() => setDlg("tools")} />{dialogs}</>;
  }
  if (ui.xncTab === "cost") {
    const s = stats;
    const cur = project.currency;
    return (
      <div className="panel">
        {tabs}
        <div className="form2 scroll" data-testid="xnc-cost">
          <div className="form-col">
            <Field label={t("xnc.c.drill_price")} unit={cur}><Num value={x.drill_price} min={0} onCommit={(v) => px({ drill_price: v ?? 0 })} /></Field>
            <Field label={t("xnc.c.drills")} unit={t("app.pcs")}><span className="ro">{s?.drills ?? 0}</span></Field>
            <Field label={t("xnc.c.drill_cost")} unit={cur}><span className="ro">{money((s?.drills ?? 0) * x.drill_price)}</span></Field>
            <Field label={t("xnc.c.mill_price")} unit={cur}><Num value={x.mill_price_m} min={0} onCommit={(v) => px({ mill_price_m: v ?? 0 })} /></Field>
            <Field label={t("xnc.c.mill_len")} unit={t("u.m")}><span className="ro">{s?.mill_m ?? 0}</span></Field>
            <Field label={t("xnc.c.mill_cost")} unit={cur}><span className="ro">{money((s?.mill_m ?? 0) * x.mill_price_m)}</span></Field>
            <Field label={t("xnc.c.saw_price")} unit={cur}><Num value={x.saw_price_m} min={0} onCommit={(v) => px({ saw_price_m: v ?? 0 })} /></Field>
            <Field label={t("xnc.c.saw_len")} unit={t("u.m")}><span className="ro">{s?.saw_m ?? 0}</span></Field>
            <Field label={t("xnc.c.saw_cost")} unit={cur}><span className="ro">{money((s?.saw_m ?? 0) * x.saw_price_m)}</span></Field>
          </div>
          <div className="form-col">
            <Field label={t("xnc.c.extra")} unit={cur}><Num value={x.extra_cost} min={0} onCommit={(v) => px({ extra_cost: v ?? 0 })} /></Field>
            <Field label={t("xnc.unit_cost")} unit={cur}><span className="ro">{money(s?.unit_cost)}</span></Field>
            <Field label={t("xnc.qty")} unit={t("app.pcs")}><span className="ro">{x.qty}</span></Field>
            <Field label={t("xnc.op_cost")} unit={cur}><span className="ro">{money(s?.cost)}</span></Field>
          </div>
        </div>
        {dialogs}
      </div>
    );
  }
  const setPar = (name: string, v: number | string | null) => {
    const cur = { ...(x.par_values ?? {}) };
    if (v === null) delete cur[name]; else cur[name] = v;
    px({ par_values: cur });
  };
  return (
    <div className="panel">
      {tabs}
      <div className="xnc-params-wrap" data-testid="xnc-params">
        <div className="form-col xnc-params-col scroll">
          <Field label={t("xnc.product")} stack><span className="ro">{prod?.name ?? "—"}</span></Field>
          <Field label={t("xnc.material")} stack><span className="ro">{part?.o.name ?? "—"}</span></Field>
          <Field label={t("xnc.op_name")} stack><LazyInput className="inp" value={op.name} testid="xnc-op-name" disabled={lockSize}
            onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { name: v }))} /></Field>
          <Field label={t("xnc.detail")}><span className="ro">{part ? `${part.p.uid} ${part.p.name}` : "—"}</span></Field>
          <Field label=" "><Check checked={x.by_part_size} label={t("xnc.by_part")} onChange={(v) => px({ by_part_size: v })} /></Field>
          <Field label={t("xnc.dx")} unit={t("u.mm")}><Num value={x.length} min={0} disabled={lockSize} onCommit={(v) => px({ length: v ?? 0 })} /></Field>
          <Field label={t("xnc.dy")} unit={t("u.mm")}><Num value={x.width} min={0} disabled={lockSize} onCommit={(v) => px({ width: v ?? 0 })} /></Field>
          <Field label={t("xnc.dz")} unit={t("u.mm")}><Num value={x.thickness} min={0} disabled={lockDz} testid="xnc-dz" onCommit={(v) => px({ thickness: v ?? 16 })} /></Field>
          <Field label={t("xnc.qty")} unit={t("app.pcs")}><Num value={x.qty} min={1} disabled={lockSize} onCommit={(v) => px({ qty: Math.round(v ?? 1) })} /></Field>
          <Field label=" "><Check checked={x.face_side} label={t("xnc.face")} onChange={(v) => px({ face_side: v })} /></Field>
          <Field label={t("xnc.rotation")}><Sel value={x.rotation} width={80} onChange={(v) => px({ rotation: v })}
            options={([0, 90, 180, 270] as const).map((v) => ({ value: v, label: `${v}°` }))} /></Field>
          <Field label={t("xnc.mirror")}><span className="row gap xnc-mirror">
            {/* onlayn ko'rinishdagi kabi: ikkita belgi-tugma (gorizontal / vertikal ko'zgu), bosilgan — faol */}
            {/* tartib: avval gorizontal, keyin vertikal ko'zgu */}
            <IconBtn icon={FlipHorizontal2} title={t("xnc.mirror_h")} active={x.mirror_x} onClick={() => px({ mirror_x: !x.mirror_x })} testid="xnc-mirror-x" />
            <IconBtn icon={FlipVertical2} title={t("xnc.mirror_v")} active={x.mirror_y} onClick={() => px({ mirror_y: !x.mirror_y })} testid="xnc-mirror-y" /></span></Field>
          <Field label={t("xnc.origin")} stack><Sel value={x.origin} width="100%" testid="xnc-origin" onChange={(v) => px({ origin: v })}
            options={(["LT", "RT", "LB", "RB"] as const).map((v) => ({ value: v, label: t(`xnc.origin_v.${v}`) }))} /></Field>
          <Field label={t("xnc.cost")} unit={project.currency}><span className="ro">{money(op.cost_operation)}</span></Field>
          <XncIssues issues={stats?.constraint_issues ?? []} turn={stats?.constraint_turn} />
          <div className="form-h">{t("el.p.description")}</div>
          <Area value={op.description} rows={3} onCommit={(v) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { description: v }))} />
          <ParForm x={x} params={stats?.params} onSet={setPar} />
        </div>
        <div className="xnc-params-draw">{drawing()}</div>
      </div>
      {dialogs}
    </div>
  );
}

/** «Выбрать деталь»: kroy (CS / CN) detallari ro'yxati — XNC dasturi tanlangan detalga bog'lanadi. */
function PartPickDialog({ project, current, onClose, onPick }: { project: Project; current?: string; onClose: () => void;
  onPick: (partId: string) => void }) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const rows = project.operations.filter((o) => o.type === "CS" || o.type === "CN")
    .flatMap((o) => o.parts.map((p) => ({ o, p })))
    .filter(({ p }) => !q || `${p.uid} ${p.name} ${p.code}`.toLowerCase().includes(q.toLowerCase()));
  return (
    <Modal title={t("xnc.pick_part")} onClose={onClose} width={620} testid="xnc-pick-dialog"
      footer={<Btn label={t("app.cancel")} onClick={onClose} />}>
      <input className="inp" placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} autoFocus
        style={{ width: "100%", marginBottom: 6 }} />
      <div className="pick-list">
        {rows.map(({ o, p }) => (
          <button key={p.id} type="button" className={`pick-row${p.id === current ? " active" : ""}`} onClick={() => onPick(p.id)}>
            <span className="muted">{p.uid}</span> <b>{p.name || "—"}</b> <span>{p.length} × {p.width}</span>
            <span className="muted">{p.code}</span> <span className="muted">{o.name || o.code}</span>
          </button>
        ))}
        {!rows.length && <div className="muted">{t("app.no_rows")}</div>}
      </div>
    </Modal>
  );
}
