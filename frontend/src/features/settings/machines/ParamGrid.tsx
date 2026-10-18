// ParamGrid — sxema bo'yicha guruhlangan parametrlar jadvali (umumiy komponent): guruhlar yig'iladi, maydon turi bo'yicha
// (katakcha / son / matn / tanlov), standartdan farq belgilanadi, har parametr va hammasi «standartga qaytariladi».
// Ishlatish: <ParamGrid groups={schema.groups} values={draft} onChange={(k, v) => …} onReset={(k) => …} />
// Sxema (kalit, tur, standart, ru/uz yorliq) serverdan keladi: `GET /postprocessors/machines/{key}/schema`.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronRight, RotateCcw } from "lucide-react";
import { useUI } from "../../../store/ui";
import { Check, Num, Sel, Txt, cx } from "../../../shared/ui";
import type { ParamValue, SchemaGroup, SchemaParam } from "./machinesApi";
import { LabelTemplateField } from "./LabelTemplateField";
import "./machines.css";
import { pickLang } from "../../../i18n/lang";

const CUSTOM = "__custom__";

/** Parametr yorlig'i interfeys tilida. */
export const paramLabel = (p: { ru: string; uz: string }, lang: string) => pickLang(lang, p.ru, p.uz);

/** Qiymatning o'qiladigan ko'rinishi (standart qiymatni ko'rsatish uchun). */
export function formatValue(p: SchemaParam, v: ParamValue, lang: string, yes: string, no: string, mm: string): string {
  if (p.type === "bool") return v ? yes : no;
  if (p.type === "choice") {
    const o = p.options?.find((x) => x.value === v);
    return o ? paramLabel(o, lang) : String(v);
  }
  if (p.type === "mm") return `${v} ${mm}`;
  return v === "" ? "—" : String(v);
}

function ChoiceInput({ p, value, disabled, lang, onChange }: { p: SchemaParam; value: string; disabled: boolean; lang: string;
  onChange: (v: string) => void }) {
  const { t } = useTranslation();
  const opts = p.options ?? [];
  const known = opts.some((o) => o.value === value);
  const [other, setOther] = useState(!known && value !== "");
  useEffect(() => { if (opts.some((o) => o.value === value)) setOther(false); }, [value]);     // standartga qaytarilganda
  const showText = !!p.custom && (other || !known);
  const options = [...opts.map((o) => ({ value: o.value, label: paramLabel(o, lang) })),
    ...(p.custom ? [{ value: CUSTOM, label: t("ppm.other") }] : [])];
  return (
    <span className="row gap">
      <Sel value={showText ? CUSTOM : value} options={options} disabled={disabled} width={300} testid={`pg-sel-${p.key}`}
        onChange={(v) => { if (v === CUSTOM) { setOther(true); } else { setOther(false); onChange(v); } }} />
      {showText && <Txt value={known ? "" : value} width={160} disabled={disabled} testid={`pg-custom-${p.key}`}
        placeholder={t("ppm.other")} onCommit={(v) => { if (v.trim()) onChange(v.trim()); }} />}
    </span>
  );
}

function Control({ p, value, disabled, lang, onChange }: { p: SchemaParam; value: ParamValue; disabled: boolean; lang: string;
  onChange: (v: ParamValue) => void }) {
  const { t } = useTranslation();
  switch (p.type) {
    case "bool":
      return <Check checked={value === true} disabled={disabled} testid={`pg-chk-${p.key}`} onChange={onChange} />;
    case "int":
      return <Num value={Number(value)} width={110} min={p.min} max={p.max} disabled={disabled} testid={`pg-num-${p.key}`}
        onCommit={(v) => { if (v !== null) onChange(Math.round(v)); }} />;
    case "mm":
    case "float":
      return (
        <span className="row gap">
          <Num value={Number(value)} width={110} min={p.min} max={p.max} disabled={disabled} testid={`pg-num-${p.key}`}
            onCommit={(v) => { if (v !== null) onChange(v); }} />
          {p.type === "mm" && <span className="muted">{t("u.mm")}</span>}
        </span>
      );
    case "choice":
      return <ChoiceInput p={p} value={String(value)} disabled={disabled} lang={lang} onChange={onChange} />;
    case "path":
      return <span className="pg-path"><Txt value={String(value)} width="100%" disabled={disabled} testid={`pg-txt-${p.key}`}
        onCommit={onChange} /></span>;
    case "template":       // etiketka shabloni havolasi (W18): kutubxonadan tanlash + «Открыть» (ko'rinish)
      return <LabelTemplateField value={String(value)} disabled={disabled} testid={`pg-tpl-${p.key}`} onChange={onChange} />;
    default:
      return <Txt value={String(value)} width={260} disabled={disabled} testid={`pg-txt-${p.key}`} onCommit={onChange} />;
  }
}

export function ParamGrid(props: {
  groups: SchemaGroup[]; values: Record<string, ParamValue>;
  onChange: (key: string, value: ParamValue) => void; onReset: (key: string) => void; testid?: string;
}) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const [closed, setClosed] = useState<Record<string, boolean>>({});
  return (
    <div className="pg" data-testid={props.testid ?? "param-grid"}>
      {props.groups.map((g) => {
        const nMod = g.params.filter((p) => props.values[p.key] !== p.default).length;
        return (
          <div key={g.key} className="pg-group" data-testid={`pg-group-${g.key}`}>
            <button type="button" className="pg-head" aria-expanded={!closed[g.key]}
              onClick={() => setClosed({ ...closed, [g.key]: !closed[g.key] })}>
              {closed[g.key] ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
              <b>{paramLabel(g, lang)}</b>
              {nMod > 0 && <span className="pg-badge" title={t("ppm.modified")}>{nMod}</span>}
            </button>
            {!closed[g.key] && g.params.map((p) => {
              const v = props.values[p.key] ?? p.default;
              const mod = v !== p.default;
              const off = !!p.enabled_if && props.values[p.enabled_if] === false;
              const dflt = formatValue(p, p.default, lang, t("app.yes"), t("app.no"), t("u.mm"));
              return (
                <div key={p.key} className={cx("pg-row", mod && "pg-mod", off && "pg-off")} data-testid={`pg-row-${p.key}`}
                  data-modified={mod ? "1" : "0"} title={t("ppm.default_is", { v: dflt })}>
                  <div className="pg-label">
                    {paramLabel(p, lang)}
                    {p.note && <span className="muted"> — {paramLabel(p.note, lang)}</span>}
                  </div>
                  <div className="pg-ctl">
                    <Control p={p} value={v} disabled={off} lang={lang} onChange={(nv) => props.onChange(p.key, nv)} />
                  </div>
                  <div className="pg-act">
                    {mod && (
                      <button type="button" className="ibtn" title={`${t("ppm.reset_one")} (${dflt})`} aria-label={t("ppm.reset_one")}
                        data-testid={`pg-reset-${p.key}`} onClick={() => props.onReset(p.key)}><RotateCcw size={13} /></button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
      {props.groups.some((g) => g.params.some((p) => p.type === "path")) && <div className="pg-foot">{t("ppm.path_hint")}</div>}
    </div>
  );
}
