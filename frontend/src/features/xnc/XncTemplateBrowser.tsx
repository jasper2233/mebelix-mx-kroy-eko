// «Добавить» (XNC «Шаблон» yorlig'i, onlayn «Открыть шаблоны обработки» oynasidagidek — 2026-10-23 jonli ko'rildi): papkalar
// va rasmli shablonlar plitkalari, yo'l satri, asboblar: Добавить папку, Переместить, Переименовать, Удалить, Перейти в верхнюю
// папку, Домой; pastda «Наименование» va Открыть / Отмена. «Открыть» (yoki ikki marta bosish) — shablon dasturi joriy dastur
// OXIRIGA qo'shiladi (onlayndagidek). O'rnatilgan papkalar («Типовые фрезеровки», «Фасады МДФ», «Образцы MebeliX») — o'qish uchun.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpFromLine, Folder, FolderInput, FolderPlus, House, Pencil, Trash } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del, get, patch, post } from "../../api/client";
import type { Operation, Project, XncTemplateInfo } from "../../api/types";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, IconBtn, Modal, cx } from "../../shared/ui";
import { useUI } from "../../store/ui";
import { isLang } from "../../i18n/lang";
import { useXncTemplates } from "./xncApi";

type Info = XncTemplateInfo & { folder?: string };
interface Folders { builtin: string[]; user: string[] }

const parentOf = (p: string) => (p.includes("/") ? p.slice(0, p.lastIndexOf("/")) : "");
const leaf = (p: string) => p.slice(p.lastIndexOf("/") + 1);

function Thumb({ id, lang }: { id: string; lang: string }) {
  const q = useQuery({ queryKey: ["xnc-tpl-thumb", id, lang], staleTime: 5 * 60_000,
    queryFn: () => get<string>(`/xnc/templates/${id}/thumb.svg`, { lang, w: 200, h: 150 }) });
  return <div className="xtb-thumb" dangerouslySetInnerHTML={{ __html: typeof q.data === "string" ? q.data : "" }} />;
}

export function XncTemplateBrowser({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t, i18n } = useTranslation();
  const lang = isLang(i18n.language) ? i18n.language : "ru";
  const list = useXncTemplates(lang);
  const folders = useQuery({ queryKey: ["xnc-tpl-folders", lang], queryFn: () => get<Folders>("/xnc/template-folders", { lang }) });
  const [path, setPath] = useState("");
  const [sel, setSel] = useState<{ kind: "folder" | "tpl"; id: string } | null>(null);
  const items = (list.data ?? []) as Info[];
  const builtinFolders = new Set(folders.data?.builtin ?? []);
  const allFolders = useMemo(() => [...(folders.data?.builtin ?? []), ...(folders.data?.user ?? [])], [folders.data]);
  const subFolders = allFolders.filter((f) => parentOf(f) === path);
  const tpls = items.filter((i) => (i.folder ?? "") === path).sort((a, b) => a.name.localeCompare(b.name));
  const selTpl = sel?.kind === "tpl" ? items.find((i) => i.id === sel.id) : undefined;
  const isBuiltinFolder = (f: string) => builtinFolders.has(f.split("/")[0]) && !folders.data?.user.includes(f);
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ["xnc-templates"] }); void qc.invalidateQueries({ queryKey: ["xnc-tpl-folders"] });
    void qc.invalidateQueries({ queryKey: ["xnc-tpl-thumb"] });
  };

  const open = async (id = selTpl?.id) => {
    if (!id) return;
    const r = await call(() => post<Project>(`/projects/${project.id}/operations/${op.id}/xnc/apply-template`,
      { template: id, mode: "append", lang }));
    if (r) { useUI.getState().toast(t("xnc.tpl.applied"), "ok"); onClose(); }
  };
  const addFolder = async () => {
    const name = (await askText(t("xtb.folder_new_q")))?.trim();
    if (!name) return;
    if (await call(() => post("/xnc/template-folders", { path: path ? `${path}/${name}` : name }))) refresh();
  };
  const rename = async () => {
    if (!sel) return;
    if (sel.kind === "folder") {
      if (isBuiltinFolder(sel.id)) { useUI.getState().toast(t("xtb.builtin_ro"), "warn"); return; }
      const name = (await askText(t("xtb.rename_q"), leaf(sel.id)))?.trim();
      if (!name) return;
      const np = parentOf(sel.id) ? `${parentOf(sel.id)}/${name}` : name;
      if (await call(() => patch("/xnc/template-folders", { path: sel.id, new_path: np }))) { setSel({ kind: "folder", id: np }); refresh(); }
      return;
    }
    if (!selTpl || selTpl.builtin) { useUI.getState().toast(t("xtb.builtin_ro"), "warn"); return; }
    const name = (await askText(t("xtb.rename_q"), selTpl.name))?.trim();
    if (name && await call(() => patch(`/xnc/templates/${selTpl.id}`, { name }))) refresh();
  };
  const move = async () => {
    if (!selTpl || selTpl.builtin) { useUI.getState().toast(t("xtb.builtin_ro"), "warn"); return; }
    const target = await askText(t("xtb.move_q", { list: (folders.data?.user ?? []).join(", ") || "—" }), path);
    if (target === null) return;
    if (await call(() => patch(`/xnc/templates/${selTpl.id}`, { folder: target.trim() }))) { setSel(null); refresh(); }
  };
  const remove = async () => {
    if (!sel) return;
    if (sel.kind === "folder") {
      if (isBuiltinFolder(sel.id)) { useUI.getState().toast(t("xtb.builtin_ro"), "warn"); return; }
      if (!(await askConfirm(t("xtb.folder_del_q", { n: leaf(sel.id) }), undefined, { danger: true }))) return;
      if (await call(() => del("/xnc/template-folders", { path: sel.id }))) { setSel(null); refresh(); }
      return;
    }
    if (!selTpl || selTpl.builtin) { useUI.getState().toast(t("xtb.builtin_ro"), "warn"); return; }
    if (!(await askConfirm(t("xnc.tpl.delete_q", { n: selTpl.name }), undefined, { danger: true }))) return;
    if (await call(() => del(`/xnc/templates/${selTpl.id}`))) { setSel(null); refresh(); }
  };
  const go = (p: string) => { setPath(p); setSel(null); };

  return (
    <Modal title={t("xtb.title")} onClose={onClose} width={760} height={600} scope="xnc-tpl-browser" testid="xtb"
      footer={<>
        <input className="inp grow" readOnly value={selTpl ? selTpl.name : sel ? leaf(sel.id) : ""} data-testid="xtb-name" />
        <span className="muted">{t("xtb.name")}</span>
        <Btn kind="primary" label={t("xtb.open")} disabled={!selTpl} onClick={() => void open()} testid="xtb-open" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="xtb-cancel" />
      </>}>
      <div className="toolbar xtb-bar">
        <IconBtn icon={FolderPlus} title={t("xtb.add_folder")} onClick={() => void addFolder()} testid="xtb-add-folder" />
        <IconBtn icon={FolderInput} title={t("xtb.move")} onClick={() => void move()} disabled={!selTpl || selTpl.builtin} testid="xtb-move" />
        <IconBtn icon={Pencil} title={t("xtb.rename")} onClick={() => void rename()} disabled={!sel} testid="xtb-rename" />
        <IconBtn icon={Trash} title={t("app.delete")} color="#c0392b" onClick={() => void remove()} disabled={!sel} testid="xtb-delete" />
        <IconBtn icon={ArrowUpFromLine} title={t("xtb.up")} onClick={() => go(parentOf(path))} disabled={!path} testid="xtb-up" />
        <IconBtn icon={House} title={t("xtb.home")} onClick={() => go("")} disabled={!path} testid="xtb-home" />
        <b className="xtb-path" data-testid="xtb-path">{path ? `${path} /` : ""}</b>
      </div>
      <div className="xtb-grid scroll" data-testid="xtb-grid">
        {subFolders.map((f) => (
          <div key={f} className={cx("xtb-tile", sel?.kind === "folder" && sel.id === f && "sel")} data-testid={`xtb-folder-${leaf(f)}`}
            onClick={() => setSel({ kind: "folder", id: f })} onDoubleClick={() => go(f)}>
            <div className="xtb-thumb xtb-folder"><Folder size={56} /></div>
            <div className="xtb-label">{leaf(f)}</div>
          </div>
        ))}
        {tpls.map((it) => (
          <div key={it.id} className={cx("xtb-tile", sel?.kind === "tpl" && sel.id === it.id && "sel")} title={it.description}
            data-testid={`xtb-tpl-${it.id}`} onClick={() => setSel({ kind: "tpl", id: it.id })} onDoubleClick={() => void open(it.id)}>
            <Thumb id={it.id} lang={lang} />
            <div className="xtb-label">{it.name}</div>
          </div>
        ))}
        {!subFolders.length && !tpls.length && <div className="muted" style={{ padding: 12 }}>{t("xtb.empty")}</div>}
      </div>
    </Modal>
  );
}
