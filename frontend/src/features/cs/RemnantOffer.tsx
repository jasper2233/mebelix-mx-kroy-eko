// Ombordagi qoldiq taklifi (2026-10-24, foydalanuvchi qoidasi): kesish doim butun listlardan boshlanadi; kroydan keyin omborda
// shu materialdan bor qoldiq material sarfini kamaytirsa — tizim taklif qiladi (tejash m² bilan). «Кроить из остатка» — qoldiq
// listlar ro'yxatiga qo'shiladi (band qilinadi) va qayta kesiladi; qoldiq material tejamasa — avtomatik olib tashlanadi (band bekor).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { call, qc } from "../../api/hooks";
import { get, post, put } from "../../api/client";
import type { CuttingResult, Operation, Project, Quality, RemnantOffer } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal, fmt } from "../../shared/ui";

type Resolve = (ids: number[] | null) => void;
let opener: ((o: RemnantOffer, done: Resolve) => void) | null = null;

/** Kroydan keyin chaqiriladi: taklif bo'lsa oyna, qabul qilinsa qoldiq qo'shilib qayta kesiladi. */
export async function offerWarehouseRemnant(project: Project, op: Operation, quality: Quality,
  recut: () => Promise<CuttingResult | null>, t: (k: string, o?: Record<string, unknown>) => string): Promise<void> {
  if (op.type !== "CS") return;
  const offer = await get<RemnantOffer>(`/projects/${project.id}/operations/${op.id}/remnant-offer`).catch(() => null);
  if (!offer || !offer.rows.length || !offer.tail || !opener) return;
  const ids = await new Promise<number[] | null>((resolve) => opener?.(offer, resolve));
  if (!ids || !ids.length) return;
  const added = await call(() => post(`/projects/${project.id}/operations/${op.id}/sheets/from-remnants`, { ids }));
  if (!added) return;
  void qc.invalidateQueries({ queryKey: ["remnants"] });
  const res = await recut();
  if (!res) return;
  // qoldiq ishlatilmagan bo'lsa (material tejamadi) — ro'yxatdan olib tashlanadi, band bekor bo'ladi
  const fresh = await get<Project>(`/projects/${project.id}`).catch(() => null);
  const o2 = fresh?.operations.find((x) => x.id === op.id);
  if (!o2) return;
  const usedSheets = new Set(res.maps.map((m) => m.sheet_id));
  const unused = o2.sheets.filter((s) => s.source_remnant_id && ids.includes(s.source_remnant_id) && !usedSheets.has(s.id));
  if (unused.length) {
    await call(() => put(`/projects/${project.id}/operations/${op.id}/sheets`, o2.sheets.filter((s) => !unused.includes(s))));
    useUI.getState().toast(t("ro.unused"), "info");
  } else {
    useUI.getState().toast(t("ro.used"), "ok");
  }
  void qc.invalidateQueries({ queryKey: ["project", project.id] });
  void qc.invalidateQueries({ queryKey: ["remnants"] });
  void quality;
}

/** Oyna (CsCut ichida bir marta joylanadi). */
export function RemnantOfferHost() {
  const { t } = useTranslation();
  const [st, setSt] = useState<{ offer: RemnantOffer; done: Resolve } | null>(null);
  const [sel, setSel] = useState<number | null>(null);
  opener = (offer, done) => { setSel(offer.rows[0]?.id ?? null); setSt({ offer, done }); };
  if (!st) return null;
  const close = (ids: number[] | null) => { st.done(ids); setSt(null); };
  const first = st.offer.rows[0];
  return (
    <Modal title={t("ro.title")} onClose={() => close(null)} width={620} testid="remnant-offer"
      footer={<>
        <span className="grow" />
        <Btn kind="primary" label={t("ro.use")} disabled={sel == null} testid="ro-use" onClick={() => close(sel != null ? [sel] : null)} />
        <Btn label={t("ro.no")} testid="ro-no" onClick={() => close(null)} />
      </>}>
      <p>{t("ro.text", { s: fmt(first.saving_m2), n: first.fit_parts })}</p>
      <table className="ro-table">
        <thead><tr><th /><th>ID</th><th>{t("ro.size")}</th><th>{t("ro.thickness")}</th><th>{t("ro.area")}</th><th>{t("ro.saving")}</th><th>{t("ro.note")}</th></tr></thead>
        <tbody>
          {st.offer.rows.map((r) => (
            <tr key={r.id} className={sel === r.id ? "sel" : ""} onClick={() => setSel(r.id)} data-testid={`ro-row-${r.id}`}>
              <td><input type="radio" checked={sel === r.id} onChange={() => setSel(r.id)} /></td>
              <td>{r.id}</td><td>{fmt(r.length)} × {fmt(r.width)}</td><td>{fmt(r.thickness)}</td><td>{fmt(r.area_m2)}</td><td>{fmt(r.saving_m2)}</td>
              <td>{r.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted">{t("ro.hint")}</p>
    </Modal>
  );
}
