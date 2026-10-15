// «Скачать ZPL»: shablonni ZPL II (Zebra) matniga o'girib `.zpl` fayl sifatida yuklab olish (printerga to'g'ridan yuborish yo'q).
// Sozlamalar: printer zichligi (203/300 dpi), «ZPL Header» (har etiketka boshiga), UTF-8 (^CI28), shrift (printerdagi TTF — kirill uchun), o'lcham buyruqlari.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Save, ArrowUpFromLine } from "lucide-react";
import { call } from "../../api/hooks";
import { downloadPost, get, post, put } from "../../api/client";
import type { LBParams } from "../../api/types";
import { useUI } from "../../store/ui";
import { showError } from "../../shared/dialogs";
import { Btn, Check, Field, Modal, Sel, Txt } from "../../shared/ui";
import type { LabelIssue } from "./labelsApi";

export interface ZplSettings { dpi: 203 | 300; header: string; utf8: boolean; font: string; emit_size: boolean }
interface ZplWarning { code: string; key: string; count: number; message: string }
interface ZplPreview {
  zpl: string; total: number; rendered: number; truncated: boolean; warnings: ZplWarning[]; errors: LabelIssue[]; dpi: number; template_name: string; max_labels: number;
}
const DEFAULTS: ZplSettings = { dpi: 203, header: "", utf8: true, font: "0", emit_size: true };

export function ZplDialog({ projectId, lb, lang, onClose }: { projectId: string; lb: LBParams; lang: "ru" | "uz"; onClose: () => void }) {
  const { t } = useTranslation();
  const [zs, setZs] = useState<ZplSettings | null>(null);
  const [pv, setPv] = useState<ZplPreview | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const seq = useRef(0);

  useEffect(() => {
    get<ZplSettings>("/settings/label_zpl/default").then((s) => setZs({ ...DEFAULTS, ...s })).catch(() => setZs(DEFAULTS));
  }, []);

  useEffect(() => {
    if (!zs) return;
    const my = ++seq.current;
    setBusy(true);
    const h = setTimeout(() => {
      post<ZplPreview>(`/projects/${projectId}/lb/labels/zpl/preview`, { lb, zpl: zs, shown: 2 }, { lang })
        .then((r) => { if (my === seq.current) { setPv(r); setErr(""); } })
        .catch((e: unknown) => { if (my === seq.current) { setPv(null); setErr(e instanceof Error ? e.message : String(e)); } })
        .finally(() => { if (my === seq.current) setBusy(false); });
    }, 300);
    return () => clearTimeout(h);
  }, [zs, projectId, JSON.stringify({ ...lb, template: lb.template ? 1 : 0 }), JSON.stringify(lb.template), lang]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (p: Partial<ZplSettings>) => setZs((s) => ({ ...(s ?? DEFAULTS), ...p }));
  const download = async () => {
    if (!zs) return;
    try { await downloadPost(`/projects/${projectId}/lb/labels/zpl?lang=${lang}`, { lb, zpl: zs }, "labels.zpl"); }
    catch (e) { showError(e); }
  };
  const saveDefault = async () => {
    if (!zs) return;
    const r = await call(() => put("/settings/label_zpl/default", zs));
    if (r) useUI.getState().toast(t("app.saved"), "ok");
  };
  const blocked = !pv || pv.total === 0 || pv.total > pv.max_labels || (pv.errors.length > 0 && !pv.zpl);

  return (
    <Modal title={t("lbz.title")} width={900} height="82vh" onClose={onClose} testid="lbz-dialog"
      footer={<>
        <Btn icon={ArrowUpFromLine} kind="primary" label={t("lbz.download")} onClick={() => void download()} disabled={!zs || blocked} testid="lbz-download" />
        <Btn icon={Save} label={t("lbz.save_default")} onClick={() => void saveDefault()} disabled={!zs} testid="lbz-save-default" />
        <Btn label={t("app.close")} onClick={onClose} testid="lbz-close" />
      </>}>
      <div className="lbz">
        <div className="lbz-left">
          <p className="muted small">{t("lbz.hint")}</p>
          {zs && <>
            <Field label={t("lbz.dpi")}><Sel<number> value={zs.dpi} width={120} testid="lbz-dpi" onChange={(v) => set({ dpi: v === 300 ? 300 : 203 })}
              options={[{ value: 203, label: "203 dpi" }, { value: 300, label: "300 dpi" }]} /></Field>
            <Field label={t("lbz.font")} hint={t("lbz.font_hint")}><Txt value={zs.font} width={150} testid="lbz-font" onCommit={(v) => set({ font: v.trim() || "0" })} /></Field>
            <Check checked={zs.utf8} label={t("lbz.utf8")} onChange={(v) => set({ utf8: v })} testid="lbz-utf8" />
            <Check checked={zs.emit_size} label={t("lbz.emit_size")} onChange={(v) => set({ emit_size: v })} testid="lbz-size" />
            <div className="lbz-h">{t("lbz.header")}</div>
            <textarea className="inp area lbz-header" rows={5} spellCheck={false} placeholder="^PR4&#10;~SD15" defaultValue={zs.header} data-testid="lbz-header"
              onBlur={(e) => { if (e.target.value !== zs.header) set({ header: e.target.value }); }} />
            <div className="muted small">{t("lbz.header_hint")}</div>
          </>}
        </div>
        <div className="lbz-right">
          {busy && <div className="muted">{t("app.loading")}</div>}
          {err && <div className="lbx-issues lbx-issues-err" data-testid="lbz-error">{err}</div>}
          {pv && <>
            <div className="muted" data-testid="lbz-count">{t("lbz.count", { n: pv.total, shown: pv.rendered })} · {pv.dpi} dpi</div>
            {pv.total > pv.max_labels && <div className="lbx-issues lbx-issues-err">{t("lb.too_many", { n: pv.total, max: pv.max_labels })}</div>}
            {pv.errors.length > 0 && (
              <div className="lbx-issues lbx-issues-err" data-testid="lbz-errors">
                <b>{t("lb.errors")} ({pv.errors.length})</b>
                <ul>{pv.errors.map((e, i) => <li key={i}>{e.path ? <b>#{e.path}</b> : null} {e.field} — {e.message}</li>)}</ul>
              </div>)}
            {pv.warnings.length > 0 && (
              <div className="lbx-issues" data-testid="lbz-warnings">
                <ul>{pv.warnings.map((w, i) => <li key={i} className="lbx-warn" data-testid="lbz-warn">{w.message}{w.count > 1 ? ` ×${w.count}` : ""}</li>)}</ul>
              </div>)}
            <div className="lbz-h">{t("lbz.preview")}</div>
            <pre className="lbz-pre" data-testid="lbz-pre">{pv.zpl}</pre>
          </>}
        </div>
      </div>
    </Modal>
  );
}
