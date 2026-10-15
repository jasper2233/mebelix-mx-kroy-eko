// «Печать отчета» → (CS): W2 qo'shimcha sozlamalar — sarlavha, mahsulot bo'yicha guruhlash, kromka ustunini ajratish (CS-161/163/164),
// kartalar: yo'nalish, ishlov belgilari, pripusk, shrift o'lcham/qalinligi, detal/chiqindi rangi va shtrixlash (CS-169/170/174–177).
// Maydonlar eski profillarda bo'lmasligi mumkin — `??` bilan backend standartlari (PrintSettings) ishlatiladi.
import { useTranslation } from "react-i18next";
import type { HatchKind, PrintSettings } from "../../api/types";
import { Check, Field, Num, Sel } from "../../shared/ui";
import "../cs/csW2.css";

type Upd = (f: Partial<PrintSettings>) => void;
const HATCH: HatchKind[] = ["none", "diag", "cross", "horizontal", "vertical"];

function ColorField({ value, onChange, testid }: { value: string; onChange: (v: string) => void; testid: string }) {
  return (
    <span className="pcolor">
      <input type="color" value={value} onChange={(e) => onChange(e.target.value)} data-testid={testid} />
      <span className="muted">{value.toUpperCase()}</span>
    </span>
  );
}

/** «(CS) Детали и листы» bo'limi: detallar jadvali sozlamalari. */
export function CsPrintExtras({ s, upd }: { s: PrintSettings; upd: Upd }) {
  const { t } = useTranslation();
  return (
    <div className="pf-group" data-testid="pf-cs-extra">
      <div className="form-h">{t("print.group.cs_parts")}</div>
      <Check checked={s.cs_title ?? true} label={t("print.f.cs_title")} onChange={(v) => upd({ cs_title: v })} testid="pf-cs_title" />
      <Check checked={s.cs_group_by_product ?? false} label={t("print.f.cs_group_by_product")}
        onChange={(v) => upd({ cs_group_by_product: v })} testid="pf-cs_group_by_product" />
      <Check checked={s.cs_edge_highlight ?? false} label={t("print.f.cs_edge_highlight")}
        onChange={(v) => upd({ cs_edge_highlight: v })} testid="pf-cs_edge_highlight" />
    </div>
  );
}

/** «(CS) Карты кроя» bo'limi: karta ko'rinishi. */
export function MapsPrintExtras({ s, upd }: { s: PrintSettings; upd: Upd }) {
  const { t } = useTranslation();
  const hatch = (v: HatchKind, on: (v: HatchKind) => void, testid: string) => (
    <Sel<HatchKind> value={v} width={150} testid={testid} onChange={on}
      options={HATCH.map((h) => ({ value: h, label: t(`print.hatch.${h}`) }))} />
  );
  return (
    <div className="pf-group" data-testid="pf-maps-extra">
      <div className="form-h">{t("print.group.cs_maps_style")}</div>
      <Field label={t("print.f.map_orientation")} hint={t("print.orient_hint")}>
        <Sel<"portrait" | "landscape"> value={s.map_orientation ?? "portrait"} width={150} testid="pf-map_orientation"
          onChange={(v) => upd({ map_orientation: v })}
          options={(["portrait", "landscape"] as const).map((v) => ({ value: v, label: t(`print.orient.${v}`) }))} /></Field>
      <Check checked={s.map_part_marks ?? false} label={t("print.f.map_part_marks")} onChange={(v) => upd({ map_part_marks: v })} testid="pf-map_part_marks" />
      <Check checked={s.map_allowance ?? true} label={t("print.f.map_allowance")} onChange={(v) => upd({ map_allowance: v })} testid="pf-map_allowance" />
      <Field label={t("print.f.map_num")} unit="pt">
        <span className="pcolor">
          <Num value={s.map_num_font ?? 0} min={0} max={40} width={52} testid="pf-map_num_font" onCommit={(v) => upd({ map_num_font: v ?? 0 })} />
          <Check checked={s.map_num_bold ?? true} label={t("print.f.bold")} onChange={(v) => upd({ map_num_bold: v })} testid="pf-map_num_bold" />
        </span></Field>
      <Field label={t("print.f.map_dim")} unit="pt" hint={t("print.f.font_size")}>
        <span className="pcolor">
          <Num value={s.map_dim_font ?? 0} min={0} max={40} width={52} testid="pf-map_dim_font" onCommit={(v) => upd({ map_dim_font: v ?? 0 })} />
          <Check checked={s.map_dim_bold ?? false} label={t("print.f.bold")} onChange={(v) => upd({ map_dim_bold: v })} testid="pf-map_dim_bold" />
        </span></Field>
      <Check checked={s.map_dim_rotate ?? true} label={t("print.f.map_dim_rotate")} onChange={(v) => upd({ map_dim_rotate: v })} testid="pf-map_dim_rotate" />
      <Field label={t("print.f.map_part_fill")}>
        <span className="pcolor">
          <ColorField value={s.map_part_fill ?? "#F2A541"} onChange={(v) => upd({ map_part_fill: v })} testid="pf-map_part_fill" />
          {hatch(s.map_part_hatch ?? "none", (v) => upd({ map_part_hatch: v }), "pf-map_part_hatch")}
        </span></Field>
      <Field label={t("print.f.map_waste_fill")}>
        <span className="pcolor">
          <ColorField value={s.map_waste_fill ?? "#CBCED3"} onChange={(v) => upd({ map_waste_fill: v })} testid="pf-map_waste_fill" />
          {hatch(s.map_waste_hatch ?? "none", (v) => upd({ map_waste_hatch: v }), "pf-map_waste_hatch")}
        </span></Field>
    </div>
  );
}
