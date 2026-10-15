// CL «Варианты» (W18): pogonaj kroy variantlarini solishtirish — kam material / kam sarf (material − деловой otxod) / kam kesim /
// maksimal sifat. VariantsDialog (CS) namunasida; tanlangan variant `PUT .../result` bilan saqlanadi (CLE bilan bir xil tekshiruv).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { post, put } from "../../api/client";
import { call } from "../../api/hooks";
import type { Operation, Project, Variant } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Busy, Modal, cx, fmt } from "../../shared/ui";
import { askConfirm } from "../../shared/dialogs";
import { StripMap } from "./StripMap";

/** Eng yaxshisi: hamma detal joylansin → kam material → ko'proq деловой otxod → kam karta → kam kesim («material» maqsadi). */
export function bestVariant(vs: Variant[]): number {
  const key = (x: Variant) => [x.unplaced, x.material_len_m ?? 0, -(x.business_len_m ?? 0), x.maps ?? 0, x.cuts];
  let best = 0;
  vs.forEach((v, i) => {
    const a = key(v), c = key(vs[best]);
    for (let k = 0; k < a.length; k++) { if (a[k] !== c[k]) { if (a[k] < c[k]) best = i; break; } }
  });
  return best;
}

export function ClVariantsDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [vs, setVs] = useState<Variant[] | null>(null);
  const [sel, setSel] = useState(0);
  useEffect(() => {
    let alive = true;
    void call(() => post<Variant[]>(`/projects/${project.id}/operations/${op.id}/variants`)).then((r) => {
      if (!alive) return;
      if (!r) { onClose(); return; }
      setVs(r);
      setSel(bestVariant(r));
    });
    return () => { alive = false; };
  }, [project.id, op.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const apply = async () => {
    if (!vs) return;
    if (op.result?.remnants_saved && !(await askConfirm(t("cut.recut_saved")))) return;
    const r = await call(() => put(`/projects/${project.id}/operations/${op.id}/result`, vs[sel].result));
    if (r) { useUI.getState().set({ mapIndex: 1 }); useUI.getState().toast(t("variants.applied"), "ok"); onClose(); }
  };
  return (
    <Modal title={t("cut.variants")} onClose={onClose} width={1040} height={640} testid="cl-variants-dialog"
      footer={<><Btn kind="primary" label={t("variants.apply")} disabled={!vs} onClick={() => void apply()} testid="cl-variant-apply" />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      {!vs ? <Busy text={t("cl.variants.busy")} /> : (
        <>
          <p className="muted small">{t("cl.variants.hint")}</p>
          <div className="variants cl-variants">
            {vs.map((v, i) => (
              <button key={v.variant} type="button" className={cx("variant", sel === i && "variant-active")} onClick={() => setSel(i)}
                data-testid={`cl-variant-${v.variant}`} title={t(`cl.variants.${v.variant}_hint`)}>
                <div className="variant-title">{t(`cl.variants.${v.variant}`)}</div>
                <div className="variant-map">
                  {v.result.maps[0] && <StripMap map={v.result.maps[0]} project={project} op={op} thumb className="thumbsvg cl-thumb" />}
                </div>
                {v.same_as && <div className="muted small" data-testid={`cl-variant-same-${v.variant}`}>
                  {t("cl.variants.same_as", { name: t(`cl.variants.${v.same_as}`) })}</div>}
                <table className="kv">
                  <tbody>
                    <tr><td>{t("cl.variants.strips")}</td><td><b>{v.sheets}</b> ({t("cl.variants.maps", { n: v.maps ?? v.result.maps.length })})</td></tr>
                    <tr><td>{t("cl.variants.row_material")}</td><td>{fmt(v.material_len_m ?? v.result.material_len_m ?? 0, 2)} {t("u.m")}</td></tr>
                    <tr><td>{t("cl.variants.row_consumption")}</td><td>{fmt((v.material_len_m ?? 0) - (v.business_len_m ?? 0), 2)} {t("u.m")}</td></tr>
                    <tr><td>F</td><td>{fmt(v.fill)}%</td></tr>
                    <tr><td>LT</td><td>{fmt(v.cut_m)} {t("u.m")}</td></tr>
                    <tr><td>{t("variants.cuts")}</td><td>{v.cuts}</td></tr>
                    <tr><td>{t("variants.unplaced")}</td><td className={v.unplaced ? "warn" : ""}>{v.unplaced}</td></tr>
                    <tr><td>{t("variants.time")}</td><td>{fmt(v.result.elapsed_s)} s</td></tr>
                  </tbody>
                </table>
              </button>
            ))}
          </div>
        </>
      )}
    </Modal>
  );
}
