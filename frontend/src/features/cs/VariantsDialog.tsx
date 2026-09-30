// Kroy variantlarini solishtirish: optimal / 1-kesish uzunlik bo'yicha / eni bo'yicha — xodim tanlaydi.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { post, put } from "../../api/client";
import { call } from "../../api/hooks";
import type { Operation, Project, Variant } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Busy, Modal, cx, fmt } from "../../shared/ui";
import { askConfirm } from "../../shared/dialogs";
import { MapView } from "./MapView";

export function VariantsDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [vs, setVs] = useState<Variant[] | null>(null);
  const [sel, setSel] = useState(0);
  useEffect(() => {
    let alive = true;
    void call(() => post<Variant[]>(`/projects/${project.id}/operations/${op.id}/variants`)).then((r) => {
      if (!alive) return;
      if (!r) { onClose(); return; }
      setVs(r);
      // eng yaxshisi: kam list → kam sig'magan → katta qoldiq → kam kesish
      let best = 0;
      r.forEach((v, i) => {
        const b = r[best];
        const key = (x: Variant) => [x.unplaced, x.sheets, -x.remnant_m2, x.cut_m];
        const a = key(v), c = key(b);
        for (let k = 0; k < a.length; k++) { if (a[k] !== c[k]) { if (a[k] < c[k]) best = i; break; } }
      });
      setSel(best);
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
    <Modal title={t("cut.variants")} onClose={onClose} width={1000} height={620} testid="variants-dialog"
      footer={<><Btn kind="primary" label={t("variants.apply")} disabled={!vs} onClick={() => void apply()} testid="variant-apply" />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      {!vs ? <Busy text={t("variants.busy")} /> : (
        <div className="variants">
          {vs.map((v, i) => (
            <button key={v.variant} type="button" className={cx("variant", sel === i && "variant-active")} onClick={() => setSel(i)}
              data-testid={`variant-${v.variant}`}>
              <div className="variant-title">{t(`variants.${v.variant}`)}</div>
              <div className="variant-map">
                {v.result.maps[0] && <MapView map={v.result.maps[0]} project={project} op={op} thumb className="thumbsvg" />}
              </div>
              <table className="kv">
                <tbody>
                  <tr><td>{t("variants.sheets")}</td><td><b>{v.sheets}</b></td></tr>
                  <tr><td>F</td><td>{fmt(v.fill)}%</td></tr>
                  <tr><td>LT</td><td>{fmt(v.cut_m)} {t("u.m")}</td></tr>
                  <tr><td>{t("variants.cuts")}</td><td>{v.cuts}</td></tr>
                  <tr><td>{t("variants.remnant")}</td><td>{fmt(v.remnant_m2, 3)} {t("u.m2")}</td></tr>
                  <tr><td>{t("variants.unplaced")}</td><td className={v.unplaced ? "warn" : ""}>{v.unplaced}</td></tr>
                  <tr><td>{t("variants.time")}</td><td>{fmt(v.result.elapsed_s)} s</td></tr>
                </tbody>
              </table>
            </button>
          ))}
        </div>
      )}
    </Modal>
  );
}
