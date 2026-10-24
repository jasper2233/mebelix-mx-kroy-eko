// Stanok sozlamasidagi etiketka shabloni havolasi (`template` turi, W18): W4 kutubxonasidan tanlash (`LabelsPanel` dagi bilan bir xil
// ro'yxat) va «Открыть» — shablon ko'rinishi (namuna ma'lumot bilan). Vizual tahrirlagich (W15) alohida; bu yerda faqat tanlov + ko'rinish.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import { post } from "../../../api/client";
import { useUI } from "../../../store/ui";
import { Btn, Modal, Sel } from "../../../shared/ui";
import { useTemplate, useTemplates, type LabelIssue } from "../../print/labelsApi";

interface PreviewResult { html: string; errors: LabelIssue[]; warnings: string[] }

function TemplatePreview({ id, onClose }: { id: string; onClose: () => void }) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const tpl = useTemplate(id, lang);
  const prev = useQuery({
    queryKey: ["label-template-preview", id, lang], enabled: !!tpl.data, staleTime: 0,
    queryFn: () => post<PreviewResult>("/label-templates/preview", { template: tpl.data?.template, params: {} }, { lang }),
  });
  return (
    <Modal title={tpl.data?.name ?? t("ppm.tpl_open")} onClose={onClose} width={760} height="min(560px, calc(90 * var(--vh)))" testid="pg-tpl-preview"
      footer={<Btn label={t("app.close")} onClick={onClose} />}>
      {(tpl.isLoading || prev.isLoading) && <div className="muted">{t("app.loading")}</div>}
      {(tpl.error || prev.error) && <div className="warn">{String(((tpl.error ?? prev.error) as Error).message)}</div>}
      {prev.data && (
        <>
          {prev.data.errors.length > 0 && (
            <ul className="warn" data-testid="pg-tpl-errors">{prev.data.errors.slice(0, 5).map((e, i) => <li key={i}>{e.field} — {e.message}</li>)}</ul>
          )}
          <iframe title="label-template" className="pg-tpl-frame" srcDoc={prev.data.html} sandbox="allow-same-origin"
            data-testid="pg-tpl-frame" />
          <p className="muted small">{t("ppm.tpl_hint")}</p>
        </>
      )}
    </Modal>
  );
}

export function LabelTemplateField({ value, disabled, onChange, testid }: {
  value: string; disabled: boolean; onChange: (v: string) => void; testid?: string;
}) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const list = useTemplates(lang);
  const [open, setOpen] = useState(false);
  const meta = list.data?.find((m) => m.id === value);
  const missing = value !== "" && !!list.data && !meta;
  const options = [{ value: "", label: t("ppm.tpl_none") },
    ...(list.data ?? []).map((m) => ({ value: m.id, label: (m.builtin ? "★ " : "") + m.name })),
    ...(missing ? [{ value, label: `${value} (!)` }] : [])];
  return (
    <span className="row gap pg-tpl" data-testid={testid}>
      <Sel<string> value={value} width={260} disabled={disabled} options={options} testid={testid ? `${testid}-sel` : undefined}
        onChange={onChange} />
      <Btn small icon={ExternalLink} label={t("ppm.tpl_open")} disabled={disabled || value === "" || missing}
        testid={testid ? `${testid}-open` : undefined} onClick={() => setOpen(true)} />
      {meta && <span className="muted">{meta.size.w} × {meta.size.h} {t("u.mm")}</span>}
      {missing && <span className="warn" data-testid={testid ? `${testid}-missing` : undefined}>{t("ppm.tpl_missing")}</span>}
      {open && <TemplatePreview id={value} onClose={() => setOpen(false)} />}
    </span>
  );
}
