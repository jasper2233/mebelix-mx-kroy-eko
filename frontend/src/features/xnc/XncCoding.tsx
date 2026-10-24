// «Кодирование» (XNC Параметры, onlayn tizimdagidek — 2026-10-23 jonli ko'rildi): «Коды XNC обработок будут перекодированы.
// Продолжить?» — Настройки / Ок / Отмена; «Кодирование Настройки»: «Добавить номер операции», «Добавить номер стороны
// обработки», «Выражение» (namuna kod — server hisobi, services/xnc_coding.py), По умолчанию / Ок / Отмена.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Project } from "../../api/types";
import { call } from "../../api/hooks";
import { get, post, put } from "../../api/client";
import { Btn, Check, Modal } from "../../shared/ui";
import { useUI } from "../../store/ui";

interface Coding { add_op_number: boolean; add_side_number: boolean; expr: string }
const DEFAULT: Coding = { add_op_number: true, add_side_number: false,
  expr: "now('yyMMddHHmmss')+rspace(crc16(project.name),5,'0')+rspace(part.id,4,'0')" };

export function XncCodingDialog({ project, onClose, note }: { project: Project; onClose: () => void; note?: string }) {
  const { t } = useTranslation();
  const ui = useUI();
  const [mode, setMode] = useState<"ask" | "settings">("ask");
  const [cfg, setCfg] = useState<Coding>(DEFAULT);
  const [sample, setSample] = useState<{ sample: string | null; error: string } | null>(null);
  useEffect(() => { void get<Coding>("/settings/xnc_coding/default").then(setCfg).catch(() => undefined); }, []);
  // namuna kod: ifoda o'zgarishi bilan (biroz kutib) serverda hisoblanadi
  useEffect(() => {
    if (mode !== "settings") return;
    const h = setTimeout(() => {
      void post<{ sample: string | null; error: string }>(`/projects/${project.id}/actions/xnc-coding?preview=1`, cfg)
        .then(setSample).catch((e: unknown) => setSample({ sample: null, error: String((e as Error).message ?? e) }));
    }, 250);
    return () => clearTimeout(h);
  }, [cfg, mode, project.id]);

  const run = async () => {
    const r = await call(() => post<{ changed: number; skipped: number; errors: string[] }>(`/projects/${project.id}/actions/xnc-coding`, {}));
    onClose();
    if (r) ui.toast(t("xnc.coding.done", { n: r.changed }) + (r.errors.length ? `\n${r.errors.join("\n")}` : ""),
      r.errors.length ? "warn" : "ok");
  };
  const saveSettings = async () => {
    const ok = await call(() => put("/settings/xnc_coding/default", cfg));
    if (ok !== undefined) setMode("ask");
  };

  if (mode === "ask") return (
    <Modal title={t("xnc.recode")} onClose={onClose} width={440} scope="xnccoding" testid="xnc-coding"
      footer={<>
        <Btn label={t("xnc.coding.settings")} onClick={() => setMode("settings")} testid="xnc-coding-settings" />
        <Btn kind="primary" label={t("app.ok")} onClick={() => void run()} testid="xnc-coding-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="xnc-coding-cancel" />
      </>}>
      {note && <div className="ask-text" data-testid="xnc-coding-note">{note}</div>}
      <div className="ask-text">{t("xnc.coding.q")}</div>
    </Modal>
  );
  return (
    <Modal title={t("xnc.coding.settings_title")} onClose={() => setMode("ask")} width={600} scope="xnccodingset" testid="xnc-coding-set"
      footer={<>
        <Btn label={t("xnc.coding.default")} onClick={() => setCfg(DEFAULT)} testid="xnc-coding-default" />
        <Btn kind="primary" label={t("app.ok")} onClick={() => void saveSettings()} testid="xnc-coding-set-ok" />
        <Btn label={t("app.cancel")} onClick={() => setMode("ask")} />
      </>}>
      <div className="col gap">
        <Check checked={cfg.add_op_number} onChange={(v) => setCfg({ ...cfg, add_op_number: v })} label={t("xnc.coding.add_op")}
          testid="xnc-coding-op" />
        <Check checked={cfg.add_side_number} onChange={(v) => setCfg({ ...cfg, add_side_number: v })} label={t("xnc.coding.add_side")}
          testid="xnc-coding-side" />
        <label className="row gap">
          <span>{t("xnc.coding.expr")}</span>
          <input className="inp grow" value={cfg.expr} onChange={(e) => setCfg({ ...cfg, expr: e.target.value })} data-testid="xnc-coding-expr" />
        </label>
        <div className={sample?.error ? "bad" : "muted"} data-testid="xnc-coding-sample">
          {sample?.error || sample?.sample || (sample ? t("xnc.coding.no_part") : "…")}
        </div>
      </div>
    </Modal>
  );
}
