// LB shablon fayllari (W9): «Импорт из файла» (fayl → ogohlantirishlar → kutubxonaga saqlash), «Экспорт JSON», «Экспорт XML».
// Mijozning o'z fayli faqat serverga yuboriladi va o'qiladi (saqlanmaydi); natija — kutubxona profili (`label_template`).
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { FileCode, FileJson, FileDown, FolderOpen, Save } from "lucide-react";
import { api, post } from "../../api/client";
import type { LBParams } from "../../api/types";
import { useUI } from "../../store/ui";
import { showError } from "../../shared/dialogs";
import { Btn, Check, IconBtn, Modal, Txt, cx } from "../../shared/ui";
import { lbSize, type GlImport, type GlItem, type GlWarning, type LabelTemplate } from "./labelsApi";

interface Props {
  current: LabelTemplate | null;
  lb: LBParams;
  lang: "ru" | "uz";
  /** Yangi shablon kutubxonaga saqlandi: uni tanlash (+ ixtiyoriy: o'lcham va sahifa joylashuvi). */
  onImported: (id: string, patch: Partial<LBParams>) => void;
  refreshLib: () => void;
  /** «Параметры» asboblar qatori: faqat ikonkalar — «Открыть» (import) va «Сохранить» (XML eksport). */
  compact?: boolean;
}

const ACCEPT = ".lbl,.xml,.project,.json,application/json,text/xml,application/xml";

function saveBlob(text: string, name: string, type: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

const fileStem = (s: string) => (s || "label").replace(/[^\p{L}\p{N}._-]+/gu, "_");

function Warnings({ items, testid }: { items: GlWarning[]; testid: string }) {
  return (
    <ul className="lbio-warns" data-testid={testid}>
      {items.map((w, i) => (
        <li key={i} className="lbx-warn" data-testid="lb-io-warn">
          {w.message}{w.count > 1 ? ` ×${w.count}` : ""}
        </li>))}
    </ul>
  );
}

export function LabelFileTools({ current, lb, lang, onImported, refreshLib, compact }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [exportWarn, setExportWarn] = useState<GlWarning[] | null>(null);

  const exportJson = () => {
    if (!current) return;
    saveBlob(JSON.stringify(current, null, 1), `${fileStem(current.name)}.label.json`, "application/json");
  };
  const exportXml = async () => {
    if (!current) return;
    try {
      const r = await api<{ xml: string; warnings: GlWarning[]; filename: string }>("/labels/export-xml", {
        method: "POST",
        body: {
          template: current,
          layout: { mode: lb.mode, columns: lb.columns, rows: lb.rows, gap_mm: lb.gap_mm, margin_mm: lb.margin_mm,
            width_mm: lbSize(lb).w, height_mm: lbSize(lb).h },        // A4: hisoblangan o'lcham
        },
      });
      saveBlob(r.xml, r.filename, "application/xml");
      useUI.getState().toast(t("lb.io.export_ok", { name: r.filename }), "ok");
      setExportWarn(r.warnings);
    } catch (e) { showError(e); }
  };

  return (
    <div className={cx("row gap lbio-tools", compact && "lbio-compact")}>
      {compact ? <>
        <IconBtn icon={FolderOpen} title={t("lb.tb.open")} onClick={() => setOpen(true)} testid="lb-tb-open" />
        <IconBtn icon={Save} title={t("lb.tb.save")} onClick={() => void exportXml()} disabled={!current} testid="lb-tb-save" />
      </> : <>
        <Btn small icon={FileDown} label={t("lb.io.import")} title={t("lb.io.import_hint")} onClick={() => setOpen(true)} testid="lb-io-import" />
        <Btn small icon={FileJson} label={t("lb.io.export_json")} onClick={exportJson} disabled={!current} testid="lb-io-export-json" />
        <Btn small icon={FileCode} label={t("lb.io.export_xml")} title={t("lb.io.export_xml_hint")} onClick={() => void exportXml()}
          disabled={!current} testid="lb-io-export-xml" />
      </>}
      {open && <ImportDialog lang={lang} onClose={() => setOpen(false)} refreshLib={refreshLib}
        onImported={(id, patch) => { setOpen(false); onImported(id, patch); }} />}
      {exportWarn && exportWarn.length > 0 && (
        <Modal title={t("lb.io.export_title")} width={640} onClose={() => setExportWarn(null)} testid="lb-io-export-dialog"
          footer={<Btn kind="primary" label={t("app.ok")} onClick={() => setExportWarn(null)} testid="lb-io-export-close" />}>
          <p className="muted">{t("lb.io.export_warn_hint", { n: exportWarn.length })}</p>
          <Warnings items={exportWarn} testid="lb-io-export-warns" />
        </Modal>
      )}
    </div>
  );
}

// ───────────────────────── Import oynasi ─────────────────────────
interface Row { item: GlItem; name: string; on: boolean }

function ImportDialog({ lang, onClose, refreshLib, onImported }: {
  lang: "ru" | "uz"; onClose: () => void; refreshLib: () => void; onImported: Props["onImported"];
}) {
  const { t } = useTranslation();
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<GlImport | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [active, setActive] = useState(0);
  const [applyLayout, setApplyLayout] = useState(true);
  const [html, setHtml] = useState("");
  const [err, setErr] = useState("");

  const load = async (f: File | undefined) => {
    if (!f) return;
    setBusy(true); setErr(""); setRes(null); setRows([]); setHtml("");
    try {
      let r: GlImport;
      if (/\.json$/i.test(f.name)) {                       // MebeliX JSON: xuddi shu oyna, o'zgartirishsiz
        const tpl = JSON.parse(await f.text()) as LabelTemplate;
        const chk = await post<{ errors: GlItem["errors"] }>("/label-templates/check", { template: tpl }, { lang });
        const size = tpl.size ?? { w: 58, h: 40 };
        const name = (tpl.name || f.name.replace(/\.label\.json$|\.json$/i, "")).slice(0, 100);
        r = { filename: f.name, kind: "program", skipped: [], more: 0, items: [{
          index: 0, source: f.name, name, ops: 1, template: tpl, size, layout: tpl.layout ?? null, warnings: [], errors: chk.errors,
          info: { elements: tpl.elements?.length ?? 0, params: tpl.params?.length ?? 0, vars: tpl.vars?.length ?? 0, images: 0, std_pars: 0 } }] };
      } else {
        const form = new FormData();
        form.append("file", f);
        r = await api<GlImport>("/labels/import-file", { method: "POST", form });
      }
      setRes(r);
      setRows(r.items.map((item) => ({ item, name: item.name, on: true })));
      setActive(0);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    setBusy(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  // tanlangan shablonning ko'rinishi (namuna ma'lumot bilan)
  const cur = rows[active]?.item;
  useEffect(() => {
    if (!cur) { setHtml(""); return; }
    let alive = true;
    post<{ html: string }>("/label-templates/preview", { template: cur.template, width_mm: cur.size.w, height_mm: cur.size.h }, { lang })
      .then((p) => { if (alive) setHtml(p.html); })
      .catch(() => { if (alive) setHtml(""); });
    return () => { alive = false; };
  }, [cur, lang]);

  const chosen = rows.filter((r) => r.on);
  const save = async () => {
    setBusy(true);
    try {
      let last: { id: string; item: GlItem } | null = null;
      for (const r of chosen) {
        const nm = r.name.trim() || r.item.name;
        const out = await post<{ id: string }>("/label-templates/import", { ...r.item.template, name: nm }, { name: nm });
        last = { id: out.id, item: r.item };
      }
      refreshLib();
      if (last) {
        const it = last.item;
        const patch: Partial<LBParams> = { template_id: last.id, template: null, params: {}, width_mm: it.size.w, height_mm: it.size.h };
        if (applyLayout && it.layout) {
          Object.assign(patch, { mode: it.layout.mode, columns: it.layout.columns, rows: it.layout.rows, gap_mm: it.layout.gap_mm,
            margin_mm: it.layout.margin_mm });
        }
        useUI.getState().toast(t("lb.io.saved", { n: chosen.length }), "ok");
        onImported(last.id, patch);
      }
    } catch (e) { showError(e); }
    setBusy(false);
  };

  return (
    <Modal title={t("lb.io.title")} width={980} height="80vh" onClose={onClose} testid="lb-io-dialog"
      footer={<>
        <Btn kind="primary" label={t("lb.io.save")} onClick={() => void save()} disabled={busy || chosen.length === 0} testid="lb-io-save" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="lb-io-cancel" />
      </>}>
      <div className="lbio">
        <div className="lbio-left">
          <p className="muted small">{t("lb.io.hint")}</p>
          <div className="row gap">
            <Btn icon={FileDown} label={t("lb.io.pick")} onClick={() => fileRef.current?.click()} disabled={busy} testid="lb-io-pick" />
            {res && <span className="muted">{res.filename}</span>}
            {busy && <span className="muted">{t("app.loading")}</span>}
          </div>
          <input ref={fileRef} type="file" accept={ACCEPT} hidden data-testid="lb-io-file" onChange={(e) => void load(e.target.files?.[0])} />
          {err && <div className="lbx-issues lbx-issues-err" data-testid="lb-io-error">{err}</div>}
          {res && <p className="muted small">{t("lb.io.found", { n: res.items.length })}{res.more ? ` · ${t("lb.io.more", { n: res.more })}` : ""}</p>}
          {rows.map((r, i) => {
            const it = r.item;
            return (
              <div key={i} className={cx("lbio-item", i === active && "lbio-active")} data-testid="lb-io-item" onClick={() => setActive(i)}>
                <div className="row gap">
                  <Check checked={r.on} onChange={(v) => setRows(rows.map((x, j) => (j === i ? { ...x, on: v } : x)))} testid="lb-io-check" />
                  <Txt value={r.name} width="100%" testid="lb-io-name"
                    onCommit={(s) => setRows(rows.map((x, j) => (j === i ? { ...x, name: s } : x)))} />
                </div>
                <div className="muted small">
                  {t("lb.io.size", { w: it.size.w, h: it.size.h })}
                  {it.layout ? ` · ${t("lb.io.layout", { c: it.layout.columns, r: it.layout.rows, g: it.layout.gap_mm })}` : ""}
                  {" · "}{t("lb.io.stats", { n: it.info.elements, p: it.info.params, v: it.info.vars })}
                  {res?.kind === "project" ? ` · ${t("lb.io.ops", { n: it.ops })}` : ""}
                </div>
                {it.info.std_pars > 0 && <div className="muted small">{t("lb.io.std_pars", { n: it.info.std_pars })}</div>}
                {it.warnings.length === 0 && it.errors.length === 0
                  ? <div className="lbio-ok" data-testid="lb-io-clean">{t("lb.io.no_warnings")}</div>
                  : <>
                    {it.warnings.length > 0 && <details open={i === active}>
                      <summary className="lbx-warn">{t("lb.io.warnings", { n: it.warnings.length })}</summary>
                      <Warnings items={it.warnings} testid="lb-io-warns" />
                    </details>}
                    {it.errors.length > 0 && <details open={i === active}>
                      <summary className="lbx-bad">{t("lb.io.errors", { n: it.errors.length })}</summary>
                      <ul className="lbio-warns">{it.errors.map((e, k) => (
                        <li key={k} className="lbx-bad" data-testid="lb-io-err">{e.path ? <b>#{e.path}</b> : null} {e.field} — {e.message}</li>))}</ul>
                    </details>}
                  </>}
              </div>);
          })}
          {res && res.skipped.length > 0 && (
            <div className="lbx-issues lbx-issues-err" data-testid="lb-io-skipped">
              <b>{t("lb.io.skipped", { n: res.skipped.length })}</b>
              <ul>{res.skipped.map((s, i) => <li key={i}>{s.source}: {s.error}</li>)}</ul>
            </div>)}
          {cur?.layout && <Check checked={applyLayout} onChange={setApplyLayout} label={t("lb.io.apply_layout")} testid="lb-io-apply-layout" />}
        </div>
        <div className="lbio-right">
          <div className="muted small">{t("lb.io.preview")}</div>
          <iframe title="import-preview" className="lbx-frame lbio-frame" srcDoc={html} sandbox="allow-same-origin" data-testid="lb-io-preview" />
        </div>
      </div>
    </Modal>
  );
}
