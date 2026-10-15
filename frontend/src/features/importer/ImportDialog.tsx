// «Импорт из других программ» (W18, IMP-001/004/005/006): formatlar plagin reestridan (nom, kengaytma, ikonka, holat), har format
// uchun parametrlar jadvali (ParamGrid), import profillari (nomlangan sozlamalar), «Восстановить стандартные», «Справка» va
// profillarni JSON / XML ga eksport / import. Importeri yo'q format — xira: «Нет модуля импорта — предоставьте образец файла».
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  CircleQuestionMark, Pencil, Plus, RotateCcw, Save, Trash, TriangleAlert, type LucideIcon, ArrowDownToLine, ArrowUpFromLine,
} from "lucide-react";
import { call, qc } from "../../api/hooks";
import { download } from "../../api/client";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, Dropdown, IconBtn, Modal, Sel, cx } from "../../shared/ui";
import { ParamGrid, paramLabel } from "../settings/machines/ParamGrid";
import type { ParamValue } from "../settings/machines/machinesApi";
import { IMPORT_ICONS } from "./importIcons";
import {
  createProfile, deleteProfile, importProfilesFile, refreshImportProfiles, renameProfile, runImport, sparse, updateProfile,
  useImportCatalog, useImportProfiles, useImportSchema, type ImportFormatRow, type ImportSchema,
} from "./importApi";
import "./importer.css";

const NO_PROFILE = "";

function FormatIcon({ icon, size = 18 }: { icon: string; size?: number }) {
  const Icon: LucideIcon = IMPORT_ICONS[icon] ?? IMPORT_ICONS["file-code"];
  return <Icon size={size} strokeWidth={1.8} />;
}

function pickFile(accept: string, cb: (f: File) => void) {
  const inp = document.createElement("input");
  inp.type = "file";
  inp.accept = accept;
  inp.onchange = () => { if (inp.files?.[0]) cb(inp.files[0]); };
  inp.click();
}

/** Tanlangan format: parametrlar + profillar. `s` — server sxemasi (holat `ready` bo'lsa jadval chiqadi). */
function FormatPane({ s, onRun }: { s: ImportSchema; onRun: (params: Record<string, ParamValue>) => void }) {
  const { t } = useTranslation();
  const lang = useUI((x) => x.lang);
  const profiles = useImportProfiles(s.status === "ready" ? s.key : null);
  const list = profiles.data ?? [];
  const [profileId, setProfileId] = useState<number | null>(null);
  const [vals, setVals] = useState<Record<string, ParamValue>>(s.defaults);
  const [help, setHelp] = useState(false);
  const cur = list.find((p) => p.id === profileId) ?? null;

  // format almashganda / profil tanlanganda qiymatlar: standart ← profil (siyrak)
  useEffect(() => { setProfileId(null); setVals(s.defaults); setHelp(false); }, [s.key]); // eslint-disable-line react-hooks/exhaustive-deps
  const choose = (id: number | null) => {
    setProfileId(id);
    const p = list.find((x) => x.id === id);
    setVals({ ...s.defaults, ...(p?.params ?? {}) });
  };
  useEffect(() => {          // profil o'chirilgan/yo'qolgan bo'lsa — standartga
    if (profileId !== null && !list.some((p) => p.id === profileId) && !profiles.isFetching) { setProfileId(null); setVals(s.defaults); }
  }, [list, profileId, profiles.isFetching]); // eslint-disable-line react-hooks/exhaustive-deps

  const mod = useMemo(() => sparse(vals, s.defaults), [vals, s.defaults]);
  const nMod = Object.keys(mod).length;
  const saved = cur?.params ?? {};
  const dirty = JSON.stringify(Object.entries(mod).sort()) !== JSON.stringify(Object.entries(saved).sort());
  const ui = useUI.getState;

  const saveCurrent = async () => {
    if (cur) {
      if (await call(() => updateProfile(cur.id, s.key, mod))) { await refreshImportProfiles(); ui().toast(t("app.saved"), "ok"); }
      return;
    }
    await saveNew();
  };
  const saveNew = async () => {
    const n = (await askText(t("importx.profile_new"), t("importx.profile_name")))?.trim();
    if (!n) return;
    const dup = list.find((p) => p.name.trim().toLowerCase() === n.toLowerCase());     // shu formatda shu nomli profil bor — almashtiriladi
    if (dup) {
      if (!(await askConfirm(t("importx.profile_replace_q", { name: dup.name })))) return;
      if (await call(() => updateProfile(dup.id, s.key, mod))) { await refreshImportProfiles(); setProfileId(dup.id); ui().toast(t("app.saved"), "ok"); }
      return;
    }
    const r = await call(() => createProfile(n, s.key, mod));
    if (r) { await refreshImportProfiles(); setProfileId(r.id); ui().toast(t("app.saved"), "ok"); }
  };
  const rename = async () => {
    if (!cur) return;
    const n = await askText(t("menu.rename"), cur.name);
    if (n && n !== cur.name && (await call(() => renameProfile(cur.id, n)))) await refreshImportProfiles();
  };
  const remove = async () => {
    if (!cur || !(await askConfirm(t("importx.profile_delete_q", { name: cur.name }), undefined, { danger: true, ok: t("app.delete") }))) return;
    if (await call(() => deleteProfile(cur.id))) { await refreshImportProfiles(); setProfileId(null); setVals(s.defaults); }
  };
  const exportAs = async (as: "json" | "xml") => {
    if (await call(async () => { await download("/import/profiles/export", { as, format: s.key }, `import_profiles.${as}`); return true; }))
      ui().toast(t("export.done"), "ok");
  };
  const importFile = () => pickFile(".json,.xml", async (f) => {
    const r = await call(() => importProfilesFile(f));
    if (!r) return;
    await refreshImportProfiles();
    ui().toast(t("importx.profiles_done", { c: r.created, r: r.replaced, n: r.renamed, s: r.skipped }), r.invalid.length ? "info" : "ok",
      r.invalid.map((x) => `${x.name || "?"}: ${x.error}`));
  });

  const noModule = s.status === "no_module";
  const label = (o: { ru: string; uz: string }) => (lang === "uz" ? o.uz : o.ru);
  return (
    <div className={cx("imx-pane", noModule && "imx-dim")} data-testid="imx-pane" data-format={s.key} data-status={s.status}>
      <div className="imx-head">
        <span className="imx-ico"><FormatIcon icon={s.icon} size={22} /></span>
        <div className="imx-title"><b>{label(s.name)}</b><span className="muted">{s.exts.join("  ")}</span></div>
        {!noModule && <Btn icon={CircleQuestionMark} label={t("importx.help")} active={help} testid="imx-help-btn"
          onClick={() => setHelp(!help)} />}
      </div>

      {noModule && (
        <div className="imx-nomod" data-testid="imx-nomodule" role="status">
          <TriangleAlert size={16} /> <span>{t("importx.no_module")}</span>
        </div>
      )}
      {(help || noModule) && (
        <div className="imx-help" data-testid="imx-help">
          <p>{label(s.help)}</p>
          {!noModule && s.groups.length > 0 && (
            <dl>{s.groups.flatMap((g) => g.params).map((p) => (
              <div key={p.key}><dt>{paramLabel(p, lang)}</dt><dd>{p.help ? label(p.help) : "—"}</dd></div>
            ))}</dl>
          )}
        </div>
      )}

      {!noModule && (
        <>
          <div className="imx-bar">
            <span className="muted">{t("importx.profile")}</span>
            <Sel<string> value={profileId === null ? NO_PROFILE : String(profileId)} width={230} testid="imx-profile"
              onChange={(v) => choose(v === NO_PROFILE ? null : Number(v))}
              options={[{ value: NO_PROFILE, label: t("importx.profile_none") }, ...list.map((p) => ({ value: String(p.id), label: p.name }))]} />
            <IconBtn icon={Save} title={cur ? t("importx.profile_save") : t("importx.profile_new")} testid="imx-profile-save"
              disabled={cur ? !dirty : nMod === 0} onClick={() => void saveCurrent()} />
            <IconBtn icon={Plus} title={t("importx.profile_new")} testid="imx-profile-new" disabled={nMod === 0 && !cur}
              onClick={() => void saveNew()} />
            <IconBtn icon={Pencil} title={t("menu.rename")} disabled={!cur} testid="imx-profile-rename" onClick={() => void rename()} />
            <IconBtn icon={Trash} title={t("app.delete")} disabled={!cur} testid="imx-profile-delete" onClick={() => void remove()} />
            {cur && dirty && <span className="warn" data-testid="imx-dirty">{t("importx.dirty")}</span>}
            <span className="imx-spacer" />
            <Btn icon={RotateCcw} label={t("importx.reset_all")} testid="imx-reset-all" disabled={nMod === 0}
              onClick={() => setVals(s.defaults)} />
            <Dropdown icon={ArrowUpFromLine} title={t("importx.export")} testid="imx-export" items={[
              { label: t("importx.export_json"), onClick: () => void exportAs("json"), testid: "imx-export-json" },
              { label: t("importx.export_xml"), onClick: () => void exportAs("xml"), testid: "imx-export-xml" }]} />
            <IconBtn icon={ArrowDownToLine} title={t("importx.import_profiles")} testid="imx-import-profiles" onClick={importFile} />
          </div>
          <h4 className="imx-sub">{t("importx.params")}{nMod > 0 && <span className="pg-badge" title={t("ppm.modified")}>{nMod}</span>}</h4>
          {s.groups.length > 0
            ? <ParamGrid groups={s.groups} values={vals} testid="imx-grid"
              onChange={(k, v) => setVals({ ...vals, [k]: v })} onReset={(k) => setVals({ ...vals, [k]: s.defaults[k] })} />
            : <p className="muted">{t("importx.no_params")}</p>}
          <div className="imx-run">
            <Btn kind="primary" icon={ArrowDownToLine} label={t("importx.run")} testid="imx-run" onClick={() => onRun(mod)} />
            <span className="muted">{t("importx.run_hint", { x: s.exts.join(", ") })}</span>
          </div>
        </>
      )}
    </div>
  );
}

export function ImportOtherDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const lang = useUI((x) => x.lang);
  const cat = useImportCatalog();
  const rows: ImportFormatRow[] = cat.data ?? [];
  const [sel, setSel] = useState<string | null>(null);
  const key = sel ?? rows.find((r) => r.status === "ready")?.key ?? rows[0]?.key ?? null;
  const schema = useImportSchema(key);
  const cur = rows.find((r) => r.key === key);

  const run = (params: Record<string, ParamValue>) => {
    if (!cur) return;
    pickFile(cur.exts.join(","), async (f) => {
      const ui = useUI.getState();
      const r = await call(() => runImport(f, cur.key, params, ui.folderId), t("projects.importing"));
      if (!r) return;
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["folders"] });
      if (r.warnings.length) ui.toast(t("projects.import_warnings", { n: r.warnings.length }), "info", r.warnings);
      else ui.toast(t("projects.imported", { name: r.project.name }), "ok");
      onClose();
      ui.openProject(r.project.id);
    });
  };

  return (
    <Modal title={t("menu.import_other")} onClose={onClose} width={1040} height="min(740px, 94vh)" testid="import-other"
      footer={<Btn label={t("app.close")} onClick={onClose} testid="imx-close" />}>
      <div className="imx">
        <aside className="imx-list" data-testid="imx-list" aria-label={t("importx.formats")}>
          <div className="imx-list-h muted">{t("importx.formats")}</div>
          {rows.map((r) => (
            <button key={r.key} type="button" className={cx("imx-fmt", r.key === key && "on", r.status === "no_module" && "dim")}
              data-testid={`imx-fmt-${r.key}`} data-status={r.status} title={r.status === "no_module" ? r.reason : undefined}
              onClick={() => setSel(r.key)}>
              <span className="imx-ico"><FormatIcon icon={r.icon} /></span>
              <span className="imx-fmt-t">
                <b>{lang === "uz" ? r.name.uz : r.name.ru}</b>
                <small>{r.exts.join("  ")}</small>
              </span>
              <span className={cx("imx-chip", r.status === "ready" ? "ok" : "off")}>
                {r.status === "ready" ? t("importx.ready") : t("importx.none")}
              </span>
            </button>
          ))}
        </aside>
        <section className="imx-main">
          {cat.isLoading || schema.isLoading ? <div className="muted">{t("app.loading")}</div>
            : schema.data ? <FormatPane s={schema.data} onRun={run} />
              : <div className="warn">{String((schema.error as Error | null)?.message ?? "")}</div>}
        </section>
      </div>
    </Modal>
  );
}
