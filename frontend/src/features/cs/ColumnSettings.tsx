// «Настройки колонок» (Ctrl+P): ustunlar profillari — yoqish, nom, kenglik, tartib.
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp, Pencil, Plus, RotateCcw, Trash } from "lucide-react";
import { call, qc, useProfiles } from "../../api/hooks";
import { del, post, put } from "../../api/client";
import type { Profile } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, IconBtn, Modal, Sel, cx } from "../../shared/ui";
import { defaultColumns, normalizeColumns, type ColSetting } from "./columns";

type P = Profile<{ columns: ColSetting[] }>;

export function ColumnSettings({ current, onClose }: { current: ColSetting[]; onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const profiles = useProfiles<{ columns: ColSetting[] }>("part_columns");
  const [pid, setPid] = useState<number | null>(ui.columnProfile);
  const [cols, setCols] = useState<ColSetting[]>(current);
  const [sel, setSel] = useState(0);
  const [dirty, setDirty] = useState(false);
  const list: P[] = profiles.data ?? [];

  useEffect(() => {
    const pr = list.find((p) => p.id === pid);
    setCols(normalizeColumns(pr?.data?.columns));
    setDirty(false);
  }, [pid, profiles.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const upd = (i: number, f: Partial<ColSetting>) => { setCols(cols.map((c, j) => (j === i ? { ...c, ...f } : c))); setDirty(true); };
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (j < 0 || j >= cols.length) return;
    const c = [...cols];
    [c[sel], c[j]] = [c[j], c[sel]];
    setCols(c); setSel(j); setDirty(true);
  };
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "part_columns"] });
  const create = async (name?: string) => {
    const n = name ?? (await askText(t("cols.new_profile"), t("cols.profile_name")));
    if (!n) return null;
    const r = await call(() => post<P>("/settings/part_columns", { name: n, data: { columns: cols } }));
    if (r) { await refresh(); setPid(r.id); }
    return r;
  };
  const ok = async () => {
    if (dirty) {
      if (pid === null) { const r = await create(); if (!r) return; ui.set({ columnProfile: r.id }); onClose(); return; }
      await call(() => put(`/settings/part_columns/${pid}`, { data: { columns: cols } }));
      await refresh();
    }
    ui.set({ columnProfile: pid });
    onClose();
  };
  return (
    <Modal title={t("parts.columns")} onClose={onClose} width={760} height={600} testid="column-settings"
      footer={<>
        <Btn icon={RotateCcw} label={t("cols.reset")} onClick={() => { setCols(defaultColumns()); setDirty(true); }} />
        <span className="grow" />
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="cols-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="row gap">
        <span>{t("cols.profile")}</span>
        <Sel<string> value={pid === null ? "" : String(pid)} width={220}
          onChange={(v) => setPid(v === "" ? null : Number(v))}
          options={[{ value: "", label: t("cols.standard") }, ...list.map((p) => ({ value: String(p.id), label: p.name }))]} />
        <IconBtn icon={Plus} title={t("cols.new_profile")} onClick={() => void create()} />
        <IconBtn icon={Pencil} title={t("menu.rename")} disabled={pid === null} onClick={async () => {
          const pr = list.find((p) => p.id === pid);
          const n = await askText(t("menu.rename"), pr?.name ?? "");
          if (n && pid !== null) { await call(() => put(`/settings/part_columns/${pid}`, { name: n })); await refresh(); }
        }} />
        <IconBtn icon={Trash} title={t("app.delete")} disabled={pid === null} onClick={async () => {
          if (pid === null || !(await askConfirm(t("cols.delete_q")))) return;
          await call(() => del(`/settings/part_columns/${pid}`));
          await refresh(); setPid(null); ui.set({ columnProfile: null });
        }} />
        <span className="grow" />
        <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(-1)} />
        <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(1)} />
      </div>
      <div className="scroll colset">
        <table className="simple">
          <thead><tr><th>№</th><th>{t("cols.on")}</th><th>{t("cols.name")}</th><th>{t("cols.desc")}</th><th>{t("cols.width")}</th></tr></thead>
          <tbody>
            {cols.map((c, i) => (
              <tr key={c.key} className={cx(sel === i && "tr-sel", !c.visible && "muted")} onClick={() => setSel(i)}>
                <td>{i + 1}</td>
                <td className="center"><input type="checkbox" checked={c.visible} onChange={(e) => upd(i, { visible: e.target.checked })} /></td>
                <td><input className="inp" value={c.title ?? t(`pc.${c.key}`)} onChange={(e) => upd(i, { title: e.target.value })} style={{ width: 130 }} /></td>
                <td>{t(`pcd.${c.key}`)}</td>
                <td><input className="inp num" style={{ width: 56 }} value={c.width ?? ""} placeholder="auto"
                  onChange={(e) => upd(i, { width: e.target.value ? Number(e.target.value) || undefined : undefined })} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
