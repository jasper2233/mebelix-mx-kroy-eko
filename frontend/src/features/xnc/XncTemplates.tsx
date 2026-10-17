// XNC shablonlar kutubxonasi: o'rnatilgan namunalar + o'z shablonlari; operatsiyaga qo'llash (almashtirish / oxiriga qo'shish),
// dasturni shablon sifatida saqlash, JSON eksport / import, o'chirish.
import { Fragment, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Save, Trash, ArrowDownToLine, FileUp } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del, download, post } from "../../api/client";
import type { Operation, Project, XncCommand, XncTemplateInfo } from "../../api/types";
import { askConfirm, askText, showError } from "../../shared/dialogs";
import { useUI } from "../../store/ui";
import { Btn, Modal, cx } from "../../shared/ui";
import { useXncTemplate, useXncTemplates } from "./xncApi";
import { flatten, type Row } from "./treeOps";
import { summary } from "./xncSchema";

const CATS = ["mill", "drill", "facade", "groove"];

function progText(prog: XncCommand[]): string {
  return flatten(prog, new Set()).map((r: Row) => `${"  ".repeat(r.depth)}${r.cmd.cmd} ${summary(r.cmd)}${r.cmd.comment ? `  ; ${r.cmd.comment}` : ""}`).join("\n");
}

export function XncTemplatesDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language.startsWith("uz") ? "uz" : "ru";
  const list = useXncTemplates(lang);
  const [sel, setSel] = useState<string | null>(null);
  const det = useXncTemplate(sel, lang);
  const file = useRef<HTMLInputElement>(null);
  const items = list.data ?? [];
  const mine = items.filter((i) => !i.builtin);
  const x = op.xnc!;
  const cur = items.find((i) => i.id === sel);
  const refresh = () => { void qc.invalidateQueries({ queryKey: ["xnc-templates"] }); void qc.invalidateQueries({ queryKey: ["xnc-template"] }); };

  const apply = async (mode: "replace" | "append") => {
    if (!sel || !cur) return;
    if (mode === "replace" && x.program.length && !(await askConfirm(t("xnc.tpl.replace_q", { n: cur.name })))) return;
    const r = await call(() => post<Project>(`/projects/${project.id}/operations/${op.id}/xnc/apply-template`, { template: sel, mode, lang }));
    if (r) { useUI.getState().toast(t("xnc.tpl.applied"), "ok"); onClose(); }
  };
  const saveCurrent = async () => {
    const part = project.operations.flatMap((o) => o.parts).find((p) => p.xnc_op_ids.includes(op.id));
    const name = (await askText(t("xnc.tpl.name_q"), op.name || part?.name || ""))?.trim();
    if (!name) return;
    const exists = mine.some((m) => m.name.trim().toLowerCase() === name.toLowerCase());
    if (exists && !(await askConfirm(t("xnc.tpl.exists_q", { n: name })))) return;
    const r = await call(() => post<XncTemplateInfo>("/xnc/templates", {
      name, program: x.program, par_values: x.par_values ?? {}, description: "",
    }, { upsert: exists }));
    if (r) { refresh(); setSel(r.id); useUI.getState().toast(t("xnc.tpl.saved"), "ok"); }
  };
  const remove = async () => {
    if (!cur || cur.builtin || !(await askConfirm(t("xnc.tpl.delete_q", { n: cur.name }), undefined, { danger: true }))) return;
    if ((await call(() => del(`/xnc/templates/${cur.id}`))) !== undefined) {
      qc.removeQueries({ queryKey: ["xnc-template", cur.id] });          // o'chirilgan shablonni qayta so'ramaslik
      setSel(null);
      void qc.invalidateQueries({ queryKey: ["xnc-templates"] });
    }
  };
  const doImport = async (f: File | undefined) => {
    if (!f) return;
    let body: unknown;
    try { body = JSON.parse(await f.text()); } catch { useUI.getState().toast(t("xnc.tpl.bad_file"), "error"); return; }
    const nm = typeof (body as { name?: unknown })?.name === "string" ? String((body as { name: string }).name).trim() : "";
    const exists = !!nm && mine.some((m) => m.name.trim().toLowerCase() === nm.toLowerCase());
    if (exists && !(await askConfirm(t("xnc.tpl.exists_q", { n: nm })))) return;
    const r = await call(() => post<XncTemplateInfo>("/xnc/templates/import", body, { upsert: exists }));
    if (r) { refresh(); setSel(r.id); useUI.getState().toast(t("xnc.tpl.imported", { n: r.name }), "ok"); }
  };

  const pars = (det.data?.program ?? []).filter((c) => c.cmd === "Par");
  return (
    <Modal title={t("xnc.tpl.title")} onClose={onClose} width={920} height={560} scope="xnc-tpl" testid="xnc-tpl-dialog"
      footer={<Btn label={t("app.close")} onClick={onClose} />}
      headerRight={<>
        <Btn small icon={Save} label={t("xnc.tpl.save_current")} onClick={() => void saveCurrent()} testid="xnc-tpl-save" />
        <Btn small icon={ArrowDownToLine} label={t("xnc.tpl.import")} onClick={() => file.current?.click()} testid="xnc-tpl-import" />
        <input ref={file} type="file" accept=".json,application/json" hidden data-testid="xnc-tpl-file"
          onChange={(e) => { void doImport(e.target.files?.[0]); e.target.value = ""; }} />
      </>}>
      <div className="xtpl">
        <div className="xtpl-left">
          <div className="xtpl-list" data-testid="xnc-tpl-list">
            <div className="xtpl-grp">{t("xnc.tpl.builtin")}</div>
            {CATS.flatMap((cat) => items.filter((i) => i.builtin && i.category === cat).map((i) => (
              <div key={i.id} className={cx("xtpl-item", sel === i.id && "sel")} onClick={() => setSel(i.id)} data-testid={`xtpl-${i.id}`}>
                <b>{i.name}</b><small>{t(`xnc.tpl.cat.${cat}`)} · {t("xnc.tpl.params", { n: i.par_count })}</small>
              </div>
            )))}
            <div className="xtpl-grp">{t("xnc.tpl.mine")}</div>
            {mine.map((i) => (
              <div key={i.id} className={cx("xtpl-item", sel === i.id && "sel")} onClick={() => setSel(i.id)} data-testid={`xtpl-${i.id}`}>
                <b>{i.name}</b><small>{t("xnc.tpl.commands", { n: i.commands })} · {t("xnc.tpl.params", { n: i.par_count })}</small>
              </div>
            ))}
            {!mine.length && <div className="hint">{t("xnc.tpl.empty")}</div>}
          </div>
        </div>
        <div className="xtpl-det">
          {!cur || !det.data
            ? <div className="muted">{t("xnc.tpl.pick")}</div>
            : <>
                <h3>{det.data.name}</h3>
                {det.data.description && <div>{det.data.description}</div>}
                {cur.builtin && <div className="muted">{t("xnc.tpl.builtin_note")}</div>}
                <div className="xtpl-actions">
                  <Btn kind="primary" label={t("xnc.tpl.apply_replace")} onClick={() => void apply("replace")} testid="xnc-tpl-replace" />
                  <Btn label={t("xnc.tpl.apply_append")} onClick={() => void apply("append")} testid="xnc-tpl-append" />
                  <Btn icon={FileUp} label={t("xnc.tpl.export")} testid="xnc-tpl-export"
                    onClick={() => void download(`/xnc/templates/${cur.id}/export`, { lang }).catch(showError)} />
                  {!cur.builtin && <Btn icon={Trash} kind="danger" label={t("app.delete")} onClick={() => void remove()} testid="xnc-tpl-delete" />}
                </div>
                {pars.length > 0 && (
                  <div className="xtpl-pars">
                    {pars.map((p) => (
                      <Fragment key={String(p.params.name)}>
                        <span>{String(p.params.name)}</span><span>{String(p.params.label ?? "")}</span>
                        <span className="muted">{String(p.params.value)}{p.params.suffix ? ` ${p.params.suffix}` : ""}</span>
                      </Fragment>
                    ))}
                  </div>
                )}
                <div className="xtpl-prog" data-testid="xnc-tpl-prog">{progText(det.data.program)}</div>
              </>}
        </div>
      </div>
    </Modal>
  );
}
