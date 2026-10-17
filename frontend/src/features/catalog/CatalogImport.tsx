// «Товары» — katalogni Excel/CSV dan yuklash. Varaqlar «Файл» (fayl, list, boshlang'ich qator, ildiz kategoriya, «Отображать колонки»)
// va «Столбцы» (maydon → fayl ustuni): ID, ota ID, papka belgisi, kod, nom, birlik, narx, ombor, rasm, parametrlar, o'lcham,
// qalinlik, uzunlik, en. Sozlamalar brauzerda eslab qolinadi; ildiz papka ID lari — serverda (`import_settings`).
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { ArrowDownToLine } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { api, get, put } from "../../api/client";
import type { ImportPreview } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Field, Modal, Num, Sel, Tabs, Txt } from "../../shared/ui";
import { CATALOG_KINDS } from "./api";
import "./catalog.css";

// tartib — oynadagi ustunlar ro'yxati kabi; «kind» (aniq tur ustuni) — bizning qo'shimcha
const FIELDS = ["id", "parent_id", "isfolder", "code", "name", "unit", "price", "stock", "image", "params", "size", "thickness",
  "length", "width", "kind"] as const;
type F = (typeof FIELDS)[number];
type Kind = (typeof CATALOG_KINDS)[number];
type Roots = Record<Kind, string>;
/** «Корневая категория» ro'yxati tartibi: Листовой, Погонажный, Кромки, Поверхности. */
const ROOT_KINDS: Kind[] = ["sheet", "linear", "edge", "surface"];

const GUESS: [F, RegExp][] = [
  ["parent_id", /paren|родит|ota/i], ["isfolder", /folder|папк|papka/i], ["id", /^id$|^№$/i], ["code", /код|code|kod/i],
  ["name", /наим|name|nom/i], ["unit", /ед\.?\s*изм|^ед|единиц|unit|birlik/i], ["price", /цен|price|narx/i], ["stock", /склад|stock|ombor/i],
  ["image", /изобр|image|rasm|картин/i], ["params", /парам|param/i], ["size", /размер|^size|o'lcham/i], ["thickness", /толщ|thick|qalin/i],
  ["length", /длин|length|uzun/i], ["width", /шир|width|eni|^en$/i], ["kind", /^тип|^kind|^tur/i],
];
const KEY = "mxk_catalog_import";
type ITab = "file" | "cols";

interface Saved { map: Partial<Record<F, string>>; roots: Roots; start: number; kind: string; prefix: string; hidden: F[] }

function loadSaved(): Partial<Saved> {
  try { return JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<Saved>; } catch { return {}; }
}

export function CatalogImport({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const saved = useMemo(loadSaved, []);
  const [tab, setTab] = useState<ITab>("file");
  const [file, setFile] = useState<File | null>(null);
  const [pv, setPv] = useState<ImportPreview | null>(null);
  const [sheet, setSheet] = useState("");
  const [map, setMap] = useState<Partial<Record<F, string>>>(saved.map ?? {});
  const [start, setStart] = useState(saved.start ?? 2);
  const [end, setEnd] = useState(0);
  const [kind, setKind] = useState<string>(ROOT_KINDS.includes(saved.kind as Kind) ? (saved.kind as string) : "sheet");
  const [prefix, setPrefix] = useState(saved.prefix ?? "");
  // «Отображать колонки»: yashirilgan maydonlar «Столбцы» varag'ida ko'rinmaydi va import qilinmaydi («Наименование» — har doim bor)
  const [hidden, setHidden] = useState<F[]>((saved.hidden ?? []).filter((f) => FIELDS.includes(f) && f !== "name"));
  const [roots, setRoots] = useState<Roots>({ sheet: "", edge: "", linear: "", surface: "", ...(saved.roots ?? {}) });
  // W18: ildiz kategoriya ID lari serverda (umumiy sozlama `import_settings`) — hamma ish joyi uchun bir xil; brauzerdagi qiymat — zaxira
  const server = useQuery({ queryKey: ["import-settings"], staleTime: 0,
    queryFn: () => get<{ catalog_roots?: Partial<Roots> }>("/settings/import_settings/default") });
  const rootsLoaded = useRef(false);
  useEffect(() => {
    if (!server.data || rootsLoaded.current) return;
    rootsLoaded.current = true;
    const sr = server.data.catalog_roots ?? {};
    if (Object.keys(sr).length > 0) setRoots({ sheet: "", edge: "", linear: "", surface: "", ...sr });
  }, [server.data]);

  const load = async (f: File, sheetName: string, guessMap: boolean) => {
    const fd = new FormData();
    fd.append("file", f);
    fd.append("sheet_name", sheetName);
    const r = await call(() => api<ImportPreview>("/import/preview", { form: fd }));
    if (!r) return;
    setPv(r);
    setSheet(r.sheet ?? sheetName);
    if (guessMap) {
      const m: Partial<Record<F, string>> = {};
      (r.rows[0] ?? []).forEach((h, i) => {
        for (const [k, re] of GUESS) if (!m[k] && re.test(h.trim())) { m[k] = r.columns[i]; break; }
      });
      // saqlangan xarita — faqat sarlavhalar bo'yicha topilmaganlar uchun
      setMap({ ...(saved.map ?? {}), ...m });
    }
  };

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify({ map, roots, start, kind, prefix, hidden } satisfies Saved)); } catch { /* yopiq xotira */ }
  }, [map, roots, start, kind, prefix, hidden]);

  const shown = FIELDS.filter((f) => !hidden.includes(f));
  const used = Object.fromEntries(Object.entries(map).filter(([k, v]) => v && shown.includes(k as F))) as Partial<Record<F, string>>;
  const toggle = (f: F, on: boolean) => setHidden(on ? hidden.filter((x) => x !== f) : [...hidden, f]);

  const run = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("col_map", JSON.stringify(used));
    fd.append("sheet_name", sheet);
    fd.append("start_row", String(start));
    fd.append("end_row", String(end));
    fd.append("kind", kind);
    fd.append("id_prefix", prefix);
    fd.append("roots", JSON.stringify(Object.fromEntries(Object.entries(roots).filter(([, v]) => v.trim() !== ""))));
    const r = await call(() => api<{ count: number; folders: number; items: number; images: number; warnings: string[];
      skipped: { row: number; reason: string }[] }>("/catalog/import", { form: fd }), t("import.importing"));
    if (!r) return;
    const ui = useUI.getState();
    ui.toast(t("catalog.import_done", { n: r.count, f: r.folders, m: r.items, i: r.images }), "ok");
    if (r.skipped.length) ui.toast(t("import.skipped", { n: r.skipped.length }), "warn", r.skipped.slice(0, 8).map((s) => `${s.row}: ${s.reason}`));
    else if (r.warnings.length) ui.toast(r.warnings[0], "warn", r.warnings);
    // ildizlar serverda saqlanadi (keyingi importda va boshqa ish joylarida shu qiymatlar chiqadi)
    const keep = Object.fromEntries(Object.entries(roots).filter(([, v]) => v.trim() !== ""));
    await put("/settings/import_settings/default", { catalog_roots: keep }).catch(() => undefined);
    void qc.invalidateQueries({ queryKey: ["import-settings"] });
    void qc.invalidateQueries({ queryKey: ["catalog"] });
    onClose();
  };

  const opts = [{ value: "", label: "—" }, ...(pv?.columns ?? []).map((c) => ({ value: c, label: c }))];
  /** «Столбцы» varag'idagi namuna: birinchi import qilinadigan qatordagi qiymat. */
  const sample = (f: F): string => {
    const i = pv && map[f] ? pv.columns.indexOf(map[f] as string) : -1;
    return i < 0 || !pv ? "" : pv.rows[Math.max(0, start - 1)]?.[i] ?? "";
  };
  return (
    <Modal title={t("catalog.imp.title")} onClose={onClose} width={960} height={680} testid="catalog-import"
      footer={<><Btn kind="primary" label={t("import.run")} disabled={!pv || !used.name} onClick={() => void run()} testid="catalog-import-run" />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <Tabs<ITab> value={tab} onChange={setTab} tabs={[
        { key: "file", label: t("catalog.imp.tab_file"), testid: "catalog-tab-file" },
        { key: "cols", label: t("catalog.imp.tab_cols"), testid: "catalog-tab-cols" }]} />
      {tab === "file" && <>
        <div className="cat-imp-form" data-testid="catalog-import-file-tab">
          <div className="row gap wrap">
            <label className="btn btn-default"><ArrowDownToLine size={15} /> {file ? file.name : t("import.choose_file")}
              <input type="file" hidden accept=".xlsx,.xlsm,.xls,.csv" data-testid="catalog-import-file"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) { setFile(f); void load(f, "", true); } }} /></label>
          </div>
          <Field label={t("import.sheet")}>
            <Sel value={sheet} width={200} disabled={!pv || pv.sheets.length === 0} testid="catalog-sheet"
              onChange={(s) => { setSheet(s); if (file) void load(file, s, false); }}
              options={pv && pv.sheets.length > 0 ? pv.sheets.map((s) => ({ value: s, label: s })) : [{ value: sheet, label: sheet || "—" }]} /></Field>
          <Field label={t("import.start_row")}><Num value={start} min={1} width={64} testid="catalog-start-row" onCommit={(v) => setStart(Math.round(v ?? 2))} /></Field>
          <Field label={t("catalog.imp.root")} hint={t("catalog.imp.root_hint")}>
            <Sel value={kind} width={200} testid="catalog-root-kind" onChange={setKind}
              options={ROOT_KINDS.map((k) => ({ value: k as string, label: t(`catalog.roots_${k}`) }))} /></Field>
          <div className="field cat-imp-top" title={t("catalog.imp.show_cols_hint")}>
            <span className="field-label">{t("catalog.imp.show_cols")}</span>
            <span className="field-ctl cat-imp-shown" data-testid="catalog-show-cols">
              {FIELDS.map((f) => (
                <Check key={f} checked={!hidden.includes(f)} disabled={f === "name"} label={t(`catalog.f.${f}`)} testid={`catalog-show-${f}`}
                  onChange={(v) => toggle(f, v)} />))}
            </span>
            <span className="field-unit" />
          </div>
          <details className="cat-imp-extra">
            <summary>{t("catalog.imp.extra")}</summary>
            <Field label={t("import.end_row")} unit={<span className="muted">{t("import.end_row_hint")}</span>}>
              <Num value={end} min={0} width={64} onCommit={(v) => setEnd(Math.round(v ?? 0))} /></Field>
            <Field label={t("catalog.id_prefix")}><Txt value={prefix} width={110} maxLength={20} placeholder="g1-" onCommit={setPrefix} /></Field>
            <div><b>{t("catalog.imp.root_ids")}</b> <span className="muted">{t("catalog.roots_hint")}</span></div>
            <div className="cat-import-roots">
              {ROOT_KINDS.map((k) => (
                <label key={k}><span>{t(`catalog.roots_${k}`)}</span>
                  <Txt value={roots[k]} placeholder="ID" testid={`catalog-root-${k}`} onCommit={(v) => setRoots({ ...roots, [k]: v.trim() })} /></label>
              ))}
            </div>
          </details>
        </div>
        {pv && <div className="scroll preview"><table className="simple">
          <thead><tr><th>#</th>{pv.columns.map((c) => <th key={c}>{c}{Object.entries(used).filter(([, v]) => v === c)
            .map(([k]) => <div key={k} className="map-tag">{t(`catalog.f.${k}`)}</div>)}</th>)}</tr></thead>
          <tbody>{pv.rows.map((r, i) => {
            const n = i + 1;
            const out = n < start || (end > 0 && n > end);
            return <tr key={i} className={out ? "muted" : ""}><td>{n}</td>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>;
          })}</tbody></table></div>}
        {!pv && <p className="muted">{t("catalog.import_hint")}</p>}
      </>}
      {tab === "cols" && (
        <div className="scroll preview" data-testid="catalog-import-cols-tab">
          {!pv && <p className="muted cat-imp-pad">{t("catalog.imp.no_file")}</p>}
          <table className="simple cat-imp-cols">
            <thead><tr><th>№</th><th>{t("catalog.imp.field")}</th><th>{t("catalog.imp.col")}</th><th>{t("catalog.imp.sample")}</th></tr></thead>
            <tbody>{shown.map((f, i) => (
              <tr key={f} data-testid={`catalog-field-${f}`}>
                <td>{i + 1}</td>
                <td>{t(`catalog.f.${f}`)}{f === "name" && " *"}</td>
                <td><Sel value={map[f] ?? ""} width={90} disabled={!pv} testid={`catalog-col-${f}`}
                  onChange={(v) => setMap({ ...map, [f]: v || undefined })} options={opts} /></td>
                <td className="muted">{sample(f)}</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}
