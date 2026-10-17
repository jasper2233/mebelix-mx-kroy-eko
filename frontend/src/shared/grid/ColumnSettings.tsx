// Ustunlar sozlamasi («Настройки», Ctrl+P) — barcha jadvallar uchun umumiy: profillar (qo'shish / nomlash / o'chirish),
// ustunni yoqish, nom, tavsif (sarlavha maslahati), kenglik va tartib. CS detallari (`part_columns`, kenglik — px) va boshqa
// jadvallar (`o_columns`, `el_columns`, `cl_columns`, `cn_columns`; kenglik — belgilarda) shu komponentni ishlatadi.
import { useCallback, useMemo, useState, useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { ColDef } from "ag-grid-community";
import { ChevronDown, ChevronUp, Pencil, Plus, RotateCcw, Save, Trash } from "lucide-react";
import { call, qc, useDefaults, useProfiles } from "../../api/hooks";
import { del, post, put } from "../../api/client";
import type { Profile } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../dialogs";
import { Btn, IconBtn, Modal, Sel, cx } from "../ui";

/** Profildagi bitta ustun: kalit, yoqilgan, foydalanuvchi nomi (bo'lmasa — standart), kenglik (px yoki belgi). */
export interface ColSetting<K extends string = string> { key: K; visible: boolean; title?: string; width?: number }
type Cols<K extends string> = { columns: ColSetting<K>[] };

/** Kenglik belgilarda → px (Arial 11pt: ~8 px belgi + katak chekkalari). */
export const chToPx = (ch: number) => Math.round(ch * 8 + 8);

export interface ColumnSettingsProps<K extends string> {
  /** backend profillar doirasi (`/settings/{scope}`) */
  scope: string;
  title: ReactNode;
  /** tanlangan profil (null — «Стандарт») va uni saqlash (store) */
  profileId: number | null;
  onProfile: (id: number | null) => void;
  current: ColSetting<K>[];
  /** profil ustunlari → to'liq ro'yxat; `undefined` — standart ro'yxat */
  normalize: (cols: ColSetting<K>[] | undefined) => ColSetting<K>[];
  label: (key: K) => string;
  desc: (key: K) => string;
  /** «Ш-на» birligi: px (CS detallari) yoki belgi */
  unit?: "px" | "ch";
  /** «Настройка значений по умолчанию»: joriy ustunlarni shu jadval turi uchun standart qilib saqlash */
  onSaveDefault?: (cols: ColSetting<K>[]) => Promise<unknown>;
  onClose: () => void;
  testid?: string;
}

export function ColumnSettings<K extends string>(props: ColumnSettingsProps<K>) {
  const { scope, normalize, onProfile, onClose, onSaveDefault } = props;
  const { t } = useTranslation();
  const profiles = useProfiles<Cols<K>>(scope);
  const [pid, setPid] = useState<number | null>(props.profileId);
  const [cols, setCols] = useState<ColSetting<K>[]>(props.current);
  const [sel, setSel] = useState(0);
  const [dirty, setDirty] = useState(false);
  // standart profil (is_default) ro'yxatda alohida ko'rinmaydi — u «Стандарт» bandi ortida turadi
  const list: Profile<Cols<K>>[] = (profiles.data ?? []).filter((p) => !onSaveDefault || !p.is_default);
  const url = `/settings/${scope}`;

  useEffect(() => {
    const pr = list.find((p) => p.id === pid);
    setCols(normalize(pr?.data?.columns));
    setDirty(false);
  }, [pid, profiles.data]); // eslint-disable-line react-hooks/exhaustive-deps

  const upd = (i: number, f: Partial<ColSetting<K>>) => { setCols(cols.map((c, j) => (j === i ? { ...c, ...f } : c))); setDirty(true); };
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (j < 0 || j >= cols.length) return;
    const c = [...cols];
    [c[sel], c[j]] = [c[j], c[sel]];
    setCols(c); setSel(j); setDirty(true);
  };
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", scope] });
  const create = async (name?: string) => {
    const n = name ?? (await askText(t("cols.new_profile"), t("cols.profile_name")));
    if (!n) return null;
    const r = await call(() => post<Profile<Cols<K>>>(url, { name: n, data: { columns: cols } }));
    if (r) { await refresh(); setPid(r.id); }
    return r;
  };
  const ok = async () => {
    if (dirty) {
      if (pid === null) { const r = await create(); if (!r) return; onProfile(r.id); onClose(); return; }
      await call(() => put(`${url}/${pid}`, { data: { columns: cols } }));
      await refresh();
    }
    onProfile(pid);
    onClose();
  };
  const reset = () => { setCols(normalize(undefined)); setDirty(true); };
  return (
    <Modal title={props.title} onClose={onClose} width={760} height={600} testid={props.testid ?? "column-settings"}
      footer={<>
        {onSaveDefault
          ? <Btn icon={Save} label={t("cols.save_default")} title={t("cols.save_default_hint")}
              onClick={() => void onSaveDefault(cols)} testid="cols-save-default" />
          : <Btn icon={RotateCcw} label={t("cols.reset")} onClick={reset} />}
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
          if (n && pid !== null) { await call(() => put(`${url}/${pid}`, { name: n })); await refresh(); }
        }} />
        <IconBtn icon={Trash} title={t("app.delete")} disabled={pid === null} onClick={async () => {
          if (pid === null || !(await askConfirm(t("cols.delete_q")))) return;
          await call(() => del(`${url}/${pid}`));
          await refresh(); setPid(null); onProfile(null);
        }} />
        {onSaveDefault && (
          <button type="button" className="linkbtn" onClick={reset} data-testid="cols-reset">{t("cols.reset")}</button>)}
        <span className="grow" />
        <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(-1)} />
        <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(1)} />
      </div>
      <div className="scroll colset">
        <table className="simple">
          <thead><tr><th>№</th><th>{t("cols.on")}</th><th>{t("cols.name")}</th><th>{t("cols.desc")}</th>
            <th title={props.unit === "ch" ? t("cols.width_ch") : undefined}>{t("cols.width")}</th></tr></thead>
          <tbody>
            {cols.map((c, i) => (
              <tr key={c.key} className={cx(sel === i && "tr-sel", !c.visible && "muted")} onClick={() => setSel(i)}
                data-testid={`cols-row-${c.key}`}>
                <td>{i + 1}</td>
                <td className="center"><input type="checkbox" checked={c.visible} onChange={(e) => upd(i, { visible: e.target.checked })}
                  data-testid={`cols-on-${c.key}`} /></td>
                <td><input className="inp" value={c.title ?? props.label(c.key)} onChange={(e) => upd(i, { title: e.target.value })} style={{ width: 130 }} /></td>
                <td>{props.desc(c.key)}</td>
                <td><input className="inp num" style={{ width: 56 }} value={c.width ?? ""} placeholder={t("colset.auto")}
                  onChange={(e) => upd(i, { width: e.target.value ? Number(e.target.value) || undefined : undefined })} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}

// ───────────────────────── boshqa jadvallar: ustunlar katalogi + profil ─────────────────────────

/** Jadval ustuni katalogda: kalit (= ColDef.colId / field), nom va tavsif i18n kalitlari, standart kenglik (belgi). */
export interface ColSpec<K extends string = string> {
  key: K;
  name: string;
  /** sarlavha maslahati («Описание»); bo'lmasa — nom */
  desc?: string;
  /** kenglik, belgilarda */
  width: number;
  /** standart holatda ko'rinadimi (bo'lmasa — ha) */
  visible?: boolean;
}

/** Jadval turi: profillar doirasi (backend `settings` scope) + ustunlar katalogi. */
export interface GridKind<K extends string = string> { scope: string; specs: ColSpec<K>[] }

const keyOf = <T,>(d: ColDef<T>) => d.colId ?? (d.field as string | undefined) ?? "";

/** Profil ustunlari → katalog bo'yicha to'liq ro'yxat (noma'lum kalitlar tashlanadi, yangilari oxiriga — yashirin). */
export function normalizeKind<K extends string>(specs: ColSpec<K>[], cols: ColSetting<K>[] | undefined,
  fallback?: ColSetting<K>[]): ColSetting<K>[] {
  const builtin = () => specs.map((s) => ({ key: s.key, visible: s.visible ?? true, width: s.width }));
  const src = cols && cols.length ? cols : fallback && fallback.length ? fallback : null;
  if (!src) return builtin();
  const byKey = new Map(specs.map((s) => [s.key, s]));
  const seen = new Set<string>();
  const out: ColSetting<K>[] = [];
  for (const c of src) {
    const s = byKey.get(c.key);
    if (!s || seen.has(c.key)) continue;
    seen.add(c.key);
    out.push({ key: c.key, visible: !!c.visible, ...(c.title ? { title: c.title } : {}), width: c.width && c.width > 0 ? c.width : s.width });
  }
  for (const s of specs) if (!seen.has(s.key)) out.push({ key: s.key, visible: false, width: s.width });
  return out;
}

/** Ustunlarga profilni qo'llash: tartib, ko'rinish, nom, maslahat (tavsif), kenglik (belgi → px).
 *  Katalogda yo'q ustunlar (masalan «№») joyida qoladi: boshidagilari boshda, qolganlari oxirida. */
export function applyColumns<T, K extends string>(defs: ColDef<T>[], settings: ColSetting<K>[], specs: ColSpec<K>[],
  t: (k: string) => string): ColDef<T>[] {
  const byKey = new Map<string, ColSpec<K>>(specs.map((s) => [s.key, s]));
  const defOf = new Map(defs.map((d) => [keyOf(d), d]));
  const first = defs.findIndex((d) => byKey.has(keyOf(d)));
  const lead = first < 0 ? defs : defs.slice(0, first).filter((d) => !byKey.has(keyOf(d)));
  const tail = first < 0 ? [] : defs.slice(first).filter((d) => !byKey.has(keyOf(d)));
  const mid: ColDef<T>[] = [];
  for (const s of settings) {
    const spec = byKey.get(s.key);
    const d = defOf.get(s.key);
    if (!s.visible || !spec || !d) continue;
    const px = chToPx(s.width && s.width > 0 ? s.width : spec.width);
    const col: ColDef<T> = { ...d, colId: s.key, headerName: s.title || t(spec.name), headerTooltip: t(spec.desc ?? spec.name) };
    // cho'ziluvchi ustun (flex) jadvalni to'ldiradi — kenglik uning eng kichik qiymati
    if (d.flex) { delete col.width; col.minWidth = px; } else { col.width = px; delete col.flex; }
    mid.push(col);
  }
  return [...lead, ...mid, ...tail];
}

/** Jadval turi uchun: tanlangan profil (store), standart (server), qo'llangan ustunlar va «Настройки» oynasi. */
export function useGridColumns<T, K extends string>(kind: GridKind<K>, defs: ColDef<T>[]) {
  const { t } = useTranslation();
  const ui = useUI();
  const { scope, specs } = kind;
  const profiles = useProfiles<Cols<K>>(scope);
  const dflt = useDefaults<Partial<Cols<K>>>(scope);
  const pid = ui.gridColumnProfiles[scope] ?? null;
  const [open, setOpen] = useState(false);
  const normalize = useCallback((cols: ColSetting<K>[] | undefined) => normalizeKind(specs, cols, dflt.data?.columns),
    [specs, dflt.data]);
  const settings = useMemo(() => {
    const pr = pid === null ? undefined : profiles.data?.find((p) => p.id === pid);
    return normalize(pr?.data?.columns);
  }, [profiles.data, pid, normalize]);
  const columnDefs = useMemo(() => applyColumns(defs, settings, specs, t), [defs, settings, specs, t]);
  const saveDefault = async (cols: ColSetting<K>[]) => {
    const r = await call(() => put(`/settings/${scope}/default`, { columns: cols }));
    if (r) { ui.toast(t("cols.default_saved"), "ok"); await qc.invalidateQueries({ queryKey: ["defaults", scope] }); }
  };
  const byKey = new Map(specs.map((s) => [s.key, s]));
  const dialog = open ? (
    <ColumnSettings<K> scope={scope} title={t("cols.title")} profileId={pid} current={settings} normalize={normalize} unit="ch"
      onProfile={(id) => ui.set({ gridColumnProfiles: { ...useUI.getState().gridColumnProfiles, [scope]: id } })}
      label={(k) => t(byKey.get(k)?.name ?? k)} desc={(k) => { const s = byKey.get(k); return s ? t(s.desc ?? s.name) : ""; }}
      onSaveDefault={saveDefault} onClose={() => setOpen(false)} testid={`${scope}-settings`} />
  ) : null;
  return { columnDefs, settings, open: () => setOpen(true), dialog };
}
