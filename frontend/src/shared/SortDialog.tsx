// Umumiy «Сортировка» oynasi: ustunlar ro'yxati `№ | Вкл | Наименование | Напр`, ↑↓ — ustuvorlik (ko'p kalitli saralash).
// Operatsiyalar, mahsulotlar va detallar jadvallarida bir xil komponent (D0.5).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Btn, IconBtn, Modal, cx } from "./ui";

export interface SortSpec { by: string; desc: boolean }

export function SortDialog({ cols, onApply, onClose, testid = "sort-dialog" }: {
  cols: { key: string; label: string }[]; onApply: (specs: SortSpec[]) => void; onClose: () => void; testid?: string;
}) {
  const { t } = useTranslation();
  const [rows, setRows] = useState(() => cols.map((c, i) => ({ ...c, on: i === 0, desc: false })));
  const [sel, setSel] = useState(0);
  const upd = (i: number, f: Partial<{ on: boolean; desc: boolean }>) =>
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...f } : r)));
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (j < 0 || j >= rows.length) return;
    const r = [...rows];
    [r[sel], r[j]] = [r[j], r[sel]];
    setRows(r); setSel(j);
  };
  const all = rows.every((r) => r.on);
  const specs = rows.filter((r) => r.on).map((r) => ({ by: r.key, desc: r.desc }));
  return (
    <Modal title={t("sort.title")} onClose={onClose} width={520} testid={testid}
      footer={<>
        <Btn kind="primary" label={t("app.ok")} disabled={!specs.length} title={specs.length ? undefined : t("sort.none")}
          testid="sort-ok" onClick={() => { onApply(specs); onClose(); }} />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="row gap">
        <label className="check" title={t("sort.all")}>
          <input type="checkbox" checked={all} onChange={(e) => setRows(rows.map((r) => ({ ...r, on: e.target.checked })))} />
        </label>
        <span className="grow" />
        <IconBtn icon={ChevronUp} title={t("sort.up")} onClick={() => move(-1)} disabled={sel === 0} testid="sort-up" />
        <IconBtn icon={ChevronDown} title={t("sort.down")} onClick={() => move(1)} disabled={sel === rows.length - 1} testid="sort-down" />
      </div>
      {/* qisqa izoh: ustun tanlanmagan bo'lsa — nega «Ок» o'chiq (maslahatdan tashqari ko'rinadigan matn) */}
      <div className={cx("hint", !specs.length && "warn")} data-testid="sort-note">{specs.length ? t("sort.note") : t("sort.none")}</div>
      <div className="scroll colset">
        <table className="simple">
          <thead><tr><th>№</th><th>{t("sort.col.on")}</th><th>{t("sort.col.name")}</th><th title={t("sort.desc_hint")}>{t("sort.col.desc")}</th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.key} className={cx(sel === i && "tr-sel", !r.on && "muted")} onClick={() => setSel(i)} data-testid={`sort-row-${r.key}`}>
                <td>{i + 1}</td>
                <td className="center"><input type="checkbox" checked={r.on} onChange={(e) => upd(i, { on: e.target.checked })} /></td>
                <td>{r.label}</td>
                <td className="center"><input type="checkbox" checked={r.desc} disabled={!r.on} onChange={(e) => upd(i, { desc: e.target.checked })} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
