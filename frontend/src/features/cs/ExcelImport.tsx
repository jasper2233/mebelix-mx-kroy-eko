// «Импорт из Excel» v2: loyiha darajasida (CS siz ham), ko'p tabli («Детали» / «Изделия»), guruhlash (izdeliya / material),
// o'lcham rejimi, boshlang'ich/oxirgi qator, varaq, profillar, «faqat mahsulot soni» rejimi. .xlsx / .xls / .csv.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pencil, Save, Trash, ArrowDownToLine } from "lucide-react";
import { call, qc, useProfiles } from "../../api/hooks";
import { api, del, post, put } from "../../api/client";
import type { ImportPreview, Operation, Profile, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm, askText } from "../../shared/dialogs";
import { Btn, Check, IconBtn, Modal, Num, Sel, Tabs, Txt } from "../../shared/ui";
import "./excelImport.css";

type Mode = "full" | "products_qty";
type SizeMode = "project" | "blank" | "detail" | "jointed";
type TabKey = "parts" | "products" | "simple" | "materials";

const PART_FIELDS = ["length", "width", "qty", "grain", "name", "number_in_name", "description", "code",
  "edge_top", "edge_bottom", "edge_left", "edge_right"] as const;
// W18 (XLS-009): qo'shimcha ustun guruhlari — (SP) Обработка поверхности, (GR) Пазование, (XNC) Обработка 1/2
const EXTRA_FIELDS = ["sp_front", "sp_back", "gr_top", "gr_bottom", "gr_left", "gr_right", "xnc1", "xnc2"] as const;
const PROD_FIELDS = ["code", "name", "qty", "description", "phone1", "phone2", "date"] as const;
const SIMPLE_FIELDS = ["code", "name", "unit", "qty", "price", "operation", "product"] as const;       // «Простые операции» (O)
const MAT_FIELDS = ["code", "name", "kind", "thickness", "length", "width", "price"] as const;        // «Материалы»
const MAT_KINDS = ["sheet", "edge", "surface", "linear"] as const;
type PF = (typeof PART_FIELDS)[number] | (typeof EXTRA_FIELDS)[number] | "material" | "product";
type RF = (typeof PROD_FIELDS)[number];
type SF = (typeof SIMPLE_FIELDS)[number];
type MF = (typeof MAT_FIELDS)[number];
type ColMap<K extends string> = Partial<Record<K, string>>;

interface Range { sheet_name: string; start_row: number; end_row: number }
interface PartsCfg extends Range {
  enabled: boolean; map: ColMap<PF>; size_mode: SizeMode; skip_zero_qty: boolean; target_op: string;
  linear_no_width: boolean; target_cl: string;
}
interface ProdCfg extends Range { enabled: boolean; map: ColMap<RF>; link: "code" | "name"; skip_zero_qty: boolean; add_empty: boolean }
interface SimpleCfg extends Range { enabled: boolean; map: ColMap<SF>; op_name: string; target_op: string }
interface MatCfg extends Range { enabled: boolean; map: ColMap<MF>; create_missing: boolean; default_kind: (typeof MAT_KINDS)[number] }

/** Saqlanadigan profil: v2 shakli (`parts` / `products` / `simple` / `materials`) yoki eski `{ map, start }` (faqat «Детали» ustun xaritasi). */
interface ExcelProfile {
  map?: Record<string, string>; start?: number;
  mode?: Mode; parts?: Partial<PartsCfg>; products?: Partial<ProdCfg>; simple?: Partial<SimpleCfg>; materials?: Partial<MatCfg>;
}

interface Report {
  imported: number; skipped: { row: number; reason: string; tab?: string }[]; warnings: string[];
  created_edges: { id: string; name: string }[]; created_ops: { id: string; name: string; type?: string }[];
  created_products: number; updated_products: number; zero_skipped: number; size_mode_changed?: string | null;
  created_o?: { id: string; name: string; rows: number }[]; simple_rows?: number; materials_added?: number;
  materials_existing?: number; linear_imported?: number; linked?: { sp: number; gr: number; xnc: number; xnc_new: number };
}

// Tartib muhim: «Длина детали» uzunlik bo'lsin (nom emas) — shuning uchun o'lchamlar nomdan oldin; «детал» faqat zaxira.
const GUESS_PARTS: [PF, RegExp][] = [
  // qo'shimcha guruhlar umumiy «Сверху / Слева» (kromka) qoidalaridan oldin: «Паз сверху» — GR, «Обработка 1» — XNC
  ["xnc1", /xnc.*1|обработк[а-яё]*\s*1|ishlov\s*1/i], ["xnc2", /xnc.*2|обработк[а-яё]*\s*2|ishlov\s*2/i],
  ["sp_front", /(sp|поверх|sirt).*(лиц|old|front)/i], ["sp_back", /(sp|поверх|sirt).*(обр|orqa|back)/i],
  ["gr_top", /(gr|паз).*(сверх|yuqori|top)/i], ["gr_bottom", /(gr|паз).*(сниз|past|bottom)/i],
  ["gr_left", /(gr|паз).*(слев|chap|left)/i], ["gr_right", /(gr|паз).*(справ|o'ng|ong|right)/i],
  ["length", /длин|д-на|uzun|length|^l$/i], ["width", /шир|ш-на|^en$|eni|width|^w$/i],
  ["qty", /кол|сони|soni|qty|count|шт/i], ["grain", /текст|ткт|txt|grain/i], ["edge_top", /^ов$|сверх|yuqori/i],
  ["edge_bottom", /^он$|сниз|past/i], ["edge_left", /^ол$|слев|chap/i], ["edge_right", /^оп$|справ|o'ng|ong/i],
  ["material", /материал|material|mat\.?$/i], ["product", /издел|mahsulot|product|модел/i],
  ["description", /описан|tavsif|descr|примеч/i], ["number_in_name", /^№$|^n$|номер|^поз|raqam|pos/i],
  ["code", /код|code|kod|арт/i], ["name", /наим|назв|nom|name/i],
];
const GUESS_PRODUCTS: [RF, RegExp][] = [
  ["phone1", /тел.*1|phone.*1|telefon.*1/i], ["phone2", /тел.*2|phone.*2|telefon.*2/i], ["qty", /кол|сони|soni|qty|count|шт/i],
  ["description", /описан|tavsif|descr/i], ["date", /дата|sana|date/i], ["code", /код|code|kod|арт/i], ["name", /наим|назв|nom|name/i],
];
const GUESS_SIMPLE: [SF, RegExp][] = [
  ["operation", /операц|operatsiya/i], ["product", /издел|mahsulot|product/i], ["unit", /ед\.?\s*и|ед\.?\s*изм|^ед|unit|birlik/i],
  ["qty", /кол|сони|soni|qty|count|шт/i], ["price", /цен|narx|price/i], ["code", /код|code|kod|арт/i], ["name", /наим|назв|nom|name/i],
];
const GUESS_MATS: [MF, RegExp][] = [
  ["kind", /^тип|^вид|kind|^tur/i], ["thickness", /толщ|^т-на|thick|qalin|^т$/i], ["length", /длин|^д-на|length|uzun|^д$/i],
  ["width", /шир|^ш-на|width|^en$|eni|^ш$/i], ["price", /цен|narx|price/i], ["code", /код|code|kod|арт/i], ["name", /наим|назв|nom|name/i],
];
const WEAK_NAME = /детал|detal/i;
const PARTS_SHEET = /детал|detal|part/i;
const PRODUCTS_SHEET = /издел|mahsulot|product|заказ|buyurtma/i;
const SIMPLE_SHEET = /прост|oddiy|simple|комплект|furnit/i;
const MATS_SHEET = /материал|material/i;

const emptyPartsCfg = (target: string): PartsCfg => ({ enabled: true, sheet_name: "", start_row: 2, end_row: 0, map: {},
  size_mode: "project", skip_zero_qty: false, target_op: target, linear_no_width: false, target_cl: "" });
const emptyProdCfg = (): ProdCfg => ({ enabled: false, sheet_name: "", start_row: 2, end_row: 0, map: {}, link: "name",
  skip_zero_qty: false, add_empty: false });
const emptySimpleCfg = (): SimpleCfg => ({ enabled: false, sheet_name: "", start_row: 2, end_row: 0, map: {}, op_name: "", target_op: "" });
const emptyMatCfg = (): MatCfg => ({ enabled: false, sheet_name: "", start_row: 2, end_row: 0, map: {}, create_missing: true,
  default_kind: "sheet" });

function guess<K extends string>(rules: [K, RegExp][], pv: ImportPreview, row = 0): ColMap<K> {
  const head = pv.rows[row] ?? [];
  const m: ColMap<K> = {};
  head.forEach((h, i) => {
    for (const [f, re] of rules) if (!m[f] && re.test(h.trim())) { m[f] = pv.columns[i]; break; }
  });
  return m;
}

function guessParts(pv: ImportPreview): ColMap<PF> {
  const m = guess(GUESS_PARTS, pv);
  if (!m.name) {            // zaxira: «детал…» sarlavhasi (boshqa maydonga olinmagan bo'lsa)
    const taken = new Set(Object.values(m));
    const i = (pv.rows[0] ?? []).findIndex((h, k) => !taken.has(pv.columns[k]) && WEAK_NAME.test(h.trim()));
    if (i >= 0) m.name = pv.columns[i];
  }
  if (!m.length && !m.width && pv.columns.length >= 3) {    // sarlavhasiz fayl: nom, uzunlik, en, soni
    m.name = pv.columns[0]; m.length = pv.columns[1]; m.width = pv.columns[2]; if (pv.columns[3]) m.qty = pv.columns[3];
  }
  return m;
}

function clean<K extends string>(m: ColMap<K>): Record<string, string> {
  return Object.fromEntries(Object.entries(m).filter(([, v]) => v)) as Record<string, string>;
}

export function ExcelImportDialog({ project, op, onClose, initialFile }: { project: Project; op?: Operation; onClose: () => void;
  /** chap menyudagi «Импорт из Excel»: fayl avval tanlanadi (onlayn tizimdagidek), oyna shu fayl bilan ochiladi */
  initialFile?: File }) {
  const { t } = useTranslation();
  const csOps = useMemo(() => project.operations.filter((o) => o.type === "CS"), [project.operations]);
  const clOps = useMemo(() => project.operations.filter((o) => o.type === "CL"), [project.operations]);
  const oOps = useMemo(() => project.operations.filter((o) => o.type === "O"), [project.operations]);
  const [file, setFile] = useState<File | null>(null);
  const [names, setNames] = useState<string[]>([]);
  const [previews, setPreviews] = useState<Record<string, ImportPreview>>({});
  const [mode, setMode] = useState<Mode>("full");
  const [tab, setTab] = useState<TabKey>("parts");
  const [parts, setParts] = useState<PartsCfg>(() => emptyPartsCfg(op?.type === "CS" ? op.id : ""));
  const [prods, setProds] = useState<ProdCfg>(emptyProdCfg);
  const [simple, setSimple] = useState<SimpleCfg>(emptySimpleCfg);
  const [mats, setMats] = useState<MatCfg>(emptyMatCfg);
  const [report, setReport] = useState<Report | null>(null);
  const [profileId, setProfileId] = useState<number | null>(null);
  const profiles = useProfiles<ExcelProfile>("excel_import");
  const list: Profile<ExcelProfile>[] = profiles.data ?? [];
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "excel_import"] });
  const tmp = useRef({ parts, prods, simple, mats });
  tmp.current = { parts, prods, simple, mats };

  const sheetOf = (k: TabKey) => ({ parts: parts.sheet_name, products: prods.sheet_name, simple: simple.sheet_name,
    materials: mats.sheet_name }[k]);
  const pvOf = (k: TabKey): ImportPreview | undefined => previews[sheetOf(k)] ?? (names.length === 0 ? previews[""] : undefined);
  const effTab: TabKey = mode === "products_qty" ? "products" : tab;
  const pv = pvOf(effTab);

  const fetchPreview = async (f: File, sheetName: string): Promise<ImportPreview | undefined> => {
    const cached = previews[sheetName];
    if (cached) return cached;
    const fd = new FormData();
    fd.append("file", f);
    fd.append("sheet_name", sheetName);
    fd.append("rows", "30");
    const r = await call(() => api<ImportPreview>("/import/preview", { form: fd }));
    if (r) setPreviews((p) => ({ ...p, [sheetName]: r, [r.sheet ?? sheetName]: r }));
    return r;
  };

  // profil: v2 shakli yoki eski {map, start}; varaq nomi — fayldagi mavjud nomlardan
  const applyProfile = (p: Profile<ExcelProfile> | undefined, sheets: string[]) => {
    if (!p) return;
    const d = p.data ?? {};
    const sheetOk = (n?: string) => sheets.find((s) => s.trim().toLowerCase() === (n ?? "").trim().toLowerCase());
    if (d.mode) setMode(d.mode);
    setParts((c) => ({ ...c, ...(d.parts ?? {}), map: { ...(d.map ?? {}), ...(d.parts?.map ?? {}) } as ColMap<PF>,
      start_row: d.parts?.start_row ?? d.start ?? c.start_row, sheet_name: sheetOk(d.parts?.sheet_name) ?? c.sheet_name,
      target_op: csOps.some((o) => o.id === d.parts?.target_op) ? (d.parts?.target_op as string) : c.target_op,
      target_cl: c.target_cl }));
    if (d.products) setProds((c) => ({ ...c, ...d.products, map: (d.products?.map ?? {}) as ColMap<RF>,
      sheet_name: sheetOk(d.products?.sheet_name) ?? c.sheet_name }));
    if (d.simple) setSimple((c) => ({ ...c, ...d.simple, map: (d.simple?.map ?? {}) as ColMap<SF>,
      sheet_name: sheetOk(d.simple?.sheet_name) ?? c.sheet_name, target_op: c.target_op }));
    if (d.materials) setMats((c) => ({ ...c, ...d.materials, map: (d.materials?.map ?? {}) as ColMap<MF>,
      sheet_name: sheetOk(d.materials?.sheet_name) ?? c.sheet_name }));
  };

  const onFile = async (f: File) => {
    setFile(f); setPreviews({}); setReport(null);
    const fd = new FormData();
    fd.append("file", f);
    fd.append("rows", "30");
    const first = await call(() => api<ImportPreview>("/import/preview", { form: fd }));
    if (!first) return;
    const sheets = first.sheets ?? [];
    setNames(sheets);
    const pSheet = sheets.find((s) => PARTS_SHEET.test(s)) ?? sheets[0] ?? "";
    const rSheet = sheets.find((s) => PRODUCTS_SHEET.test(s)) ?? sheets[1] ?? sheets[0] ?? "";
    const sSheet = sheets.find((s) => SIMPLE_SHEET.test(s)) ?? sheets[0] ?? "";
    const mSheet = sheets.find((s) => MATS_SHEET.test(s)) ?? sheets[0] ?? "";
    const got: Record<string, ImportPreview> = { [first.sheet ?? ""]: first, "": first };
    for (const s of new Set([pSheet, rSheet, sSheet, mSheet])) {
      if (s && !got[s]) {
        const fd2 = new FormData();
        fd2.append("file", f); fd2.append("sheet_name", s); fd2.append("rows", "30");
        const r = await call(() => api<ImportPreview>("/import/preview", { form: fd2 }));
        if (r) got[s] = r;
      }
    }
    setPreviews(got);
    setParts((c) => ({ ...c, sheet_name: pSheet, map: guessParts(got[pSheet] ?? first) }));
    setProds((c) => ({ ...c, sheet_name: rSheet, map: guess(GUESS_PRODUCTS, got[rSheet] ?? first) }));
    setSimple((c) => ({ ...c, sheet_name: sSheet, map: guess(GUESS_SIMPLE, got[sSheet] ?? first) }));
    setMats((c) => ({ ...c, sheet_name: mSheet, map: guess(GUESS_MATS, got[mSheet] ?? first) }));
    applyProfile(list.find((p) => p.id === profileId), sheets);
  };

  const onSheet = async (k: TabKey, name: string) => {
    if (!file) return;
    const r = await fetchPreview(file, name);
    if (k === "parts") setParts((c) => ({ ...c, sheet_name: name, map: r ? guessParts(r) : c.map }));
    else if (k === "products") setProds((c) => ({ ...c, sheet_name: name, map: r ? guess(GUESS_PRODUCTS, r) : c.map }));
    else if (k === "simple") setSimple((c) => ({ ...c, sheet_name: name, map: r ? guess(GUESS_SIMPLE, r) : c.map }));
    else setMats((c) => ({ ...c, sheet_name: name, map: r ? guess(GUESS_MATS, r) : c.map }));
  };

  const config = () => {
    const { parts: p, prods: r, simple: s, mats: m } = tmp.current;
    const range = (x: Range) => ({ sheet_name: x.sheet_name, start_row: x.start_row, end_row: x.end_row });
    const products = { enabled: mode === "products_qty" || r.enabled, ...range(r), link: r.link, map: clean(r.map),
      skip_zero_qty: r.skip_zero_qty, add_empty: r.add_empty };
    if (mode === "products_qty") return { mode, products };
    return { mode, parts: { enabled: p.enabled, ...range(p), map: clean(p.map), size_mode: p.size_mode,
      skip_zero_qty: p.skip_zero_qty, target_op: p.target_op || null, linear_no_width: p.linear_no_width,
      target_cl: p.target_cl || null }, products,
    simple: { enabled: s.enabled, ...range(s), map: clean(s.map), op_name: s.op_name, target_op: s.target_op || null },
    materials: { enabled: m.enabled, ...range(m), map: clean(m.map), create_missing: m.create_missing, default_kind: m.default_kind } };
  };

  const submit = async (dry: boolean) => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("config", JSON.stringify(config()));
    fd.append("dry_run", dry ? "true" : "false");
    const r = await call(() => api<Project & Report>(`/projects/${project.id}/import/excel`, { form: fd }),
      t("import.importing"));
    if (!r) return;
    if (dry) { setReport(r); return; }
    const ui = useUI.getState();
    const msg = mode === "products_qty" ? t("import.done_qty", { n: r.updated_products })
      : t("import.done_ext", { n: r.imported, m: (r.created_ops ?? []).filter((o) => !o.type || o.type === "CS").length, p: r.created_products ?? 0 });
    ui.toast(msg, "ok");
    // jim tashlab yuborilmaydi: o'tkazib yuborilgan qatorlar va ogohlantirishlar ko'rsatiladi
    if (r.skipped?.length) ui.toast(t("import.skipped", { n: r.skipped.length }), "warn",
      r.skipped.slice(0, 8).map((s) => `${s.row}: ${s.reason}`));
    else if (r.warnings?.length) ui.toast(r.warnings[0], "warn", r.warnings);
    const target = r.created_ops?.find((o) => o.type === "CS")?.id || parts.target_op || csOps[0]?.id;
    if (mode === "full" && parts.enabled && target) ui.set({ opId: target, csTab: "parts" });
    onClose();
  };

  const saveProfile = async () => {
    const cur = list.find((p) => p.id === profileId);
    const data: ExcelProfile = { mode, parts: { ...parts, map: clean(parts.map) as ColMap<PF> },
      products: { ...prods, map: clean(prods.map) as ColMap<RF> },
      simple: { ...simple, map: clean(simple.map) as ColMap<SF> }, materials: { ...mats, map: clean(mats.map) as ColMap<MF> } };
    // «Операция» (target_op / target_cl) — loyihaga xos, profilga yozilmaydi
    delete data.parts?.target_op;
    delete data.parts?.target_cl;
    delete data.simple?.target_op;
    if (cur) {
      if (await call(() => put(`/settings/excel_import/${cur.id}`, { data }))) { await refresh(); useUI.getState().toast(t("app.saved"), "ok"); }
      return;
    }
    const n = await askText(t("import.profile_new"), t("import.profile_name"));
    if (!n) return;
    const r = await call(() => post<Profile<ExcelProfile>>("/settings/excel_import", { name: n, data }));
    if (r) { await refresh(); setProfileId(r.id); useUI.getState().toast(t("app.saved"), "ok"); }
  };

  useEffect(() => { setReport(null); }, [mode, tab, parts, prods, simple, mats]);
  // fayl oyna ochilishidan oldin tanlangan bo'lsa — darhol o'qiladi (bir marta)
  useEffect(() => { if (initialFile) void onFile(initialFile); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // profil boshqa varaqni ko'rsatsa — uning ko'rinishi ham yuklanadi
  useEffect(() => {
    if (!file) return;
    for (const s of new Set([parts.sheet_name, prods.sheet_name, simple.sheet_name, mats.sheet_name]))
      if (s && !previews[s]) void fetchPreview(file, s);
  }, [file, parts.sheet_name, prods.sheet_name, simple.sheet_name, mats.sheet_name]); // eslint-disable-line react-hooks/exhaustive-deps

  const partsOk = !!parts.map.length && !!parts.map.width;
  const prodsLinkOk = !!prods.map[prods.link] && (mode !== "products_qty" || !!prods.map.qty);
  const simpleOk = !!(simple.map.code || simple.map.name);
  const matsOk = !!(mats.map.code || mats.map.name);
  const canRun = !!file && (mode === "products_qty" ? prodsLinkOk
    : (parts.enabled || prods.enabled || simple.enabled || mats.enabled) && (!parts.enabled || partsOk)
    && (!prods.enabled || prodsLinkOk) && (!simple.enabled || simpleOk) && (!mats.enabled || matsOk));
  const cfgOf = (k: TabKey): Range & { map: Record<string, string | undefined> } =>
    ({ parts, products: prods, simple, materials: mats }[k]) as Range & { map: Record<string, string | undefined> };

  return (
    <Modal title={t("menu.import_excel")} onClose={onClose} width={1040} height="min(800px, 96vh)" testid="excel-import"
      footer={<>
        {/* onlayn tartib: Ок, Отмена; «Проверить» — bizning qo'shimcha (oxirida) */}
        <Btn kind="primary" label={t("app.ok")} title={t("import.run")} disabled={!canRun} onClick={() => void submit(false)} testid="excel-run" />
        <Btn label={t("app.cancel")} onClick={onClose} />
        <Btn label={t("import.check")} title={t("import.check_hint")} disabled={!canRun} onClick={() => void submit(true)} testid="excel-check" /></>}>
      <div className="row gap wrap">
        <label className="btn btn-default">
          <ArrowDownToLine size={15} /> {file ? file.name : t("import.choose_file")}
          <input type="file" accept=".xlsx,.xlsm,.xls,.csv" hidden data-testid="excel-file"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) void onFile(f); }} />
        </label>
        <span className="muted">{t("import.profile")}</span>
        <Sel<string> value={profileId === null ? "" : String(profileId)} width={200} testid="excel-profile"
          onChange={(v) => { const id = v === "" ? null : Number(v); setProfileId(id); applyProfile(list.find((p) => p.id === id), names); }}
          options={[{ value: "", label: t("import.profile_none") }, ...list.map((p) => ({ value: String(p.id), label: p.name }))]} />
        <IconBtn icon={Save} title={profileId === null ? t("import.profile_new") : t("import.profile_save")} disabled={!file}
          onClick={() => void saveProfile()} testid="excel-profile-save" />
        <IconBtn icon={Pencil} title={t("menu.rename")} disabled={profileId === null} onClick={async () => {
          const n = await askText(t("menu.rename"), list.find((p) => p.id === profileId)?.name ?? "");
          if (n && profileId !== null) { await call(() => put(`/settings/excel_import/${profileId}`, { name: n })); await refresh(); }
        }} />
        <IconBtn icon={Trash} title={t("app.delete")} disabled={profileId === null} onClick={async () => {
          if (profileId === null || !(await askConfirm(t("import.profile_delete_q")))) return;
          await call(() => del(`/settings/excel_import/${profileId}`)); await refresh(); setProfileId(null);
        }} />
        <span className="xi-spacer" />
        <label className="check" title={t("import.qty_only_hint")}>
          <input type="checkbox" checked={mode === "products_qty"} data-testid="excel-qty-only"
            onChange={(e) => setMode(e.target.checked ? "products_qty" : "full")} />
          <span>{t("import.qty_only")}</span>
        </label>
      </div>
      {!file && <p className="muted">{t("import.excel_hint")}</p>}
      {file && (
        <>
          {mode === "full" && (
            <Tabs<TabKey> tabs={[{ key: "parts", label: t("import.tabs.parts"), testid: "xi-tab-parts" },
              { key: "simple", label: t("import.tabs.simple"), testid: "xi-tab-simple" },
              { key: "materials", label: t("import.tabs.materials"), testid: "xi-tab-materials" },
              { key: "products", label: t("import.tabs.products"), testid: "xi-tab-products" }]} value={tab} onChange={setTab} />
          )}
          {mode === "products_qty" && <p className="muted">{t("import.qty_only_hint")}</p>}
          {effTab === "parts" && (
            <PartsForm cfg={parts} onChange={setParts} names={names} pv={pv} csOps={csOps} clOps={clOps}
              onSheet={(s) => void onSheet("parts", s)} />
          )}
          {effTab === "products" && (
            <ProductsForm cfg={prods} onChange={setProds} names={names} pv={pv} qtyOnly={mode === "products_qty"}
              onSheet={(s) => void onSheet("products", s)} />
          )}
          {effTab === "simple" && (
            <SimpleForm cfg={simple} onChange={setSimple} names={names} pv={pv} oOps={oOps} onSheet={(s) => void onSheet("simple", s)} />
          )}
          {effTab === "materials" && (
            <MaterialsForm cfg={mats} onChange={setMats} names={names} pv={pv} onSheet={(s) => void onSheet("materials", s)} />
          )}
          {pv && <PreviewTable pv={pv} cfg={cfgOf(effTab)} map={cfgOf(effTab).map} tab={effTab} />}
          {report && <ReportBox r={report} qtyOnly={mode === "products_qty"} />}
        </>
      )}
    </Modal>
  );
}

// ───────────────────────── «Детали» ─────────────────────────
function colOptions(pv: ImportPreview | undefined, selected: (string | undefined)[]) {
  const cols = [...(pv?.columns ?? [])];
  for (const s of selected) if (s && !cols.includes(s)) cols.push(s);
  return [{ value: "", label: "—" }, ...cols.map((c) => ({ value: c, label: c }))];
}

function SheetRow({ cfg, names, onChange, onSheet }: { cfg: Range; names: string[]; onChange: (p: Partial<Range>) => void; onSheet: (s: string) => void }) {
  const { t } = useTranslation();
  return (
    <div className="xi-sect">
      <h4>{t("import.general")}</h4>
      {names.length > 0 && (
        <label className="xi-row"><span>{t("import.sheet")}</span>
          <Sel value={cfg.sheet_name} width={190} testid="xi-sheet" onChange={onSheet}
            options={names.map((n) => ({ value: n, label: n }))} /></label>
      )}
      <label className="xi-row"><span>{t("import.start_row")}</span>
        <Num value={cfg.start_row} min={1} width={70} testid="xi-start" onCommit={(v) => onChange({ start_row: Math.round(v ?? 2) })} /></label>
      <label className="xi-row"><span>{t("import.end_row")}</span>
        <Num value={cfg.end_row} min={0} width={70} testid="xi-end" onCommit={(v) => onChange({ end_row: Math.round(v ?? 0) })} />
        <span className="muted small">{t("import.end_row_hint")}</span></label>
    </div>
  );
}

function PartsForm({ cfg, onChange, names, pv, csOps, clOps, onSheet }: {
  cfg: PartsCfg; onChange: (c: PartsCfg) => void; names: string[]; pv?: ImportPreview; csOps: Operation[]; clOps: Operation[];
  onSheet: (s: string) => void;
}) {
  const { t } = useTranslation();
  const set = (p: Partial<PartsCfg>) => onChange({ ...cfg, ...p });
  const col = (f: PF) => (
    <label key={f} className="map-field"><span>{t(`import.f.${f}`)}{(f === "length" || f === "width") && " *"}</span>
      <Sel value={cfg.map[f] ?? ""} width={70} testid={`xi-col-${f}`} onChange={(v) => set({ map: { ...cfg.map, [f]: v || undefined } })}
        options={colOptions(pv, [cfg.map[f]])} /></label>
  );
  return (
    <div className="xi-form" data-testid="xi-parts">
      <Check checked={cfg.enabled} label={t("import.tab_enabled")} onChange={(v) => set({ enabled: v })} testid="xi-parts-enabled" />
      <div className="xi-top">
        <SheetRow cfg={cfg} names={names} onChange={set} onSheet={onSheet} />
        <div className="xi-sect" title={t("import.grouping_hint")}>
          <h4>{t("import.grouping")}</h4>
          <div className="map-fields">{col("product")}{col("material")}</div>
          <p className="muted small">{t("import.grouping_short")}</p>
        </div>
        <div className="xi-sect">
          <h4>{t("import.data")}</h4>
          {/* onlayn tartib: «Базовая операция», so'ng «По размеру» */}
          <label className="xi-row"><span>{t("import.target")}</span>
            <Sel value={cfg.target_op} width={190} testid="xi-target" onChange={(v) => set({ target_op: v })}
              options={[{ value: "", label: t("import.target_auto") }, ...csOps.map((o) => ({ value: o.id, label: o.name || o.code || "CS" }))]} /></label>
          <label className="xi-row"><span>{t("import.by_size")}</span>
            <Sel<SizeMode> value={cfg.size_mode} width={190} testid="xi-size-mode" onChange={(v) => set({ size_mode: v })}
              options={(["project", "blank", "detail", "jointed"] as SizeMode[]).map((m) => ({ value: m, label: t(`import.size_mode.${m}`) }))} /></label>
          <Check checked={cfg.skip_zero_qty} label={t("import.skip_zero")} onChange={(v) => set({ skip_zero_qty: v })} testid="xi-skip-zero" />
          <Check checked={cfg.linear_no_width} label={t("xi18.linear")} onChange={(v) => set({ linear_no_width: v })}
            testid="xi-linear" title={t("xi18.linear_hint")} />
          {cfg.linear_no_width && (
            <label className="xi-row"><span>{t("xi18.target_cl")}</span>
              <Sel value={cfg.target_cl} width={190} testid="xi-target-cl" onChange={(v) => set({ target_cl: v })}
                options={[{ value: "", label: t("import.target_auto") }, ...clOps.map((o) => ({ value: o.id, label: o.name || o.code || "CL" }))]} /></label>
          )}
        </div>
      </div>
      <div className="xi-sect">
        <h4>{t("import.columns")}</h4>
        <div className="map-fields">{PART_FIELDS.map((f) => col(f))}</div>
        <p className="muted small">{t("import.required_hint")}</p>
      </div>
      <div className="xi-sect" data-testid="xi-extra">
        <h4>{t("xi18.group_extra")}</h4>
        <div className="map-fields">{EXTRA_FIELDS.map((f) => col(f))}</div>
        <p className="muted small">{t("xi18.extra_hint")}</p>
      </div>
    </div>
  );
}

// ───────────────────────── «Простые операции» (O) ─────────────────────────
function SimpleForm({ cfg, onChange, names, pv, oOps, onSheet }: {
  cfg: SimpleCfg; onChange: (c: SimpleCfg) => void; names: string[]; pv?: ImportPreview; oOps: Operation[]; onSheet: (s: string) => void;
}) {
  const { t } = useTranslation();
  const set = (p: Partial<SimpleCfg>) => onChange({ ...cfg, ...p });
  return (
    <div className="xi-form" data-testid="xi-simple">
      <Check checked={cfg.enabled} label={t("import.tab_enabled")} onChange={(v) => set({ enabled: v })} testid="xi-simple-enabled" />
      <div className="xi-top">
        <SheetRow cfg={cfg} names={names} onChange={set} onSheet={onSheet} />
        <div className="xi-sect">
          <h4>{t("xi18.simple_op")}</h4>
          <label className="xi-row"><span>{t("xi18.simple_op_name")}</span>
            <Txt value={cfg.op_name} width={190} maxLength={300} testid="xi-simple-opname" onCommit={(v) => set({ op_name: v })} /></label>
          <label className="xi-row"><span>{t("xi18.simple_target")}</span>
            <Sel value={cfg.target_op} width={190} testid="xi-simple-target" onChange={(v) => set({ target_op: v })}
              options={[{ value: "", label: t("xi18.simple_new") }, ...oOps.map((o) => ({ value: o.id, label: o.name || "O" }))]} /></label>
          <p className="muted small">{t("xi18.simple_hint")}</p>
        </div>
      </div>
      <div className="xi-sect">
        <h4>{t("import.columns")}</h4>
        <div className="map-fields">
          {SIMPLE_FIELDS.map((f) => (
            <label key={f} className="map-field"><span>{t(`import.sf.${f}`)}{(f === "code" || f === "name") && " *"}</span>
              <Sel value={cfg.map[f] ?? ""} width={70} testid={`xi-scol-${f}`}
                onChange={(v) => set({ map: { ...cfg.map, [f]: v || undefined } })} options={colOptions(pv, [cfg.map[f]])} /></label>
          ))}
        </div>
        <p className="muted small">{t("xi18.simple_cols_hint")}</p>
      </div>
    </div>
  );
}

// ───────────────────────── «Материалы» ─────────────────────────
function MaterialsForm({ cfg, onChange, names, pv, onSheet }: {
  cfg: MatCfg; onChange: (c: MatCfg) => void; names: string[]; pv?: ImportPreview; onSheet: (s: string) => void;
}) {
  const { t } = useTranslation();
  const set = (p: Partial<MatCfg>) => onChange({ ...cfg, ...p });
  return (
    <div className="xi-form" data-testid="xi-materials">
      <Check checked={cfg.enabled} label={t("import.tab_enabled")} onChange={(v) => set({ enabled: v })} testid="xi-mat-enabled" />
      <div className="xi-top">
        <SheetRow cfg={cfg} names={names} onChange={set} onSheet={onSheet} />
        <div className="xi-sect">
          <h4>{t("import.data")}</h4>
          <Check checked={cfg.create_missing} label={t("xi18.mat_create_missing")} onChange={(v) => set({ create_missing: v })} testid="xi-mat-missing" />
          <label className="xi-row"><span>{t("xi18.mat_default_kind")}</span>
            <Sel<MatCfg["default_kind"]> value={cfg.default_kind} width={190} testid="xi-mat-kind" disabled={!cfg.create_missing}
              onChange={(v) => set({ default_kind: v })} options={MAT_KINDS.map((k) => ({ value: k, label: t(`catalog.kinds.${k}`) }))} /></label>
          <p className="muted small">{t("xi18.mat_hint")}</p>
        </div>
      </div>
      <div className="xi-sect">
        <h4>{t("import.columns")}</h4>
        <div className="map-fields">
          {MAT_FIELDS.map((f) => (
            <label key={f} className="map-field"><span>{t(`import.mf.${f}`)}{(f === "code" || f === "name") && " *"}</span>
              <Sel value={cfg.map[f] ?? ""} width={70} testid={`xi-mcol-${f}`}
                onChange={(v) => set({ map: { ...cfg.map, [f]: v || undefined } })} options={colOptions(pv, [cfg.map[f]])} /></label>
          ))}
        </div>
        <p className="muted small">{t("xi18.mat_cols_hint")}</p>
      </div>
    </div>
  );
}

// ───────────────────────── «Изделия» ─────────────────────────
function ProductsForm({ cfg, onChange, names, pv, qtyOnly, onSheet }: {
  cfg: ProdCfg; onChange: (c: ProdCfg) => void; names: string[]; pv?: ImportPreview; qtyOnly: boolean; onSheet: (s: string) => void;
}) {
  const { t } = useTranslation();
  const set = (p: Partial<ProdCfg>) => onChange({ ...cfg, ...p });
  const fields = qtyOnly ? (["code", "name", "qty"] as RF[]) : [...PROD_FIELDS];
  return (
    <div className="xi-form" data-testid="xi-products">
      {!qtyOnly && <Check checked={cfg.enabled} label={t("import.tab_enabled")} onChange={(v) => set({ enabled: v })} testid="xi-prod-enabled" />}
      <div className="xi-top">
        <SheetRow cfg={cfg} names={names} onChange={set} onSheet={onSheet} />
        <div className="xi-sect">
          <h4>{qtyOnly ? t("import.link_qty") : t("import.link")}</h4>
          {(["code", "name"] as const).map((k) => (
            <label key={k} className="check"><input type="radio" name="xi-link" checked={cfg.link === k} data-testid={`xi-link-${k}`}
              onChange={() => set({ link: k })} /><span>{t(`import.link_${k}`)}</span></label>
          ))}
        </div>
        <div className="xi-sect">
          <h4>{t("import.data")}</h4>
          <Check checked={cfg.skip_zero_qty} label={t("import.skip_zero_prod")} onChange={(v) => set({ skip_zero_qty: v })} />
          {!qtyOnly && <Check checked={cfg.add_empty} label={t("import.add_empty")} onChange={(v) => set({ add_empty: v })} testid="xi-add-empty" />}
        </div>
      </div>
      <div className="xi-sect">
        <h4>{t("import.columns")}</h4>
        <div className="map-fields">
          {fields.map((f) => (
            <label key={f} className="map-field"><span>{t(`import.pf.${f}`)}{(f === cfg.link || (qtyOnly && f === "qty")) && " *"}</span>
              <Sel value={cfg.map[f] ?? ""} width={70} testid={`xi-pcol-${f}`}
                onChange={(v) => set({ map: { ...cfg.map, [f]: v || undefined } })} options={colOptions(pv, [cfg.map[f]])} /></label>
          ))}
        </div>
      </div>
    </div>
  );
}

// ───────────────────────── ko'rish / hisobot ─────────────────────────
function PreviewTable({ pv, cfg, map, tab }: { pv: ImportPreview; cfg: Range; map: Record<string, string | undefined>; tab: TabKey }) {
  const { t } = useTranslation();
  const tagKey = (k: string) => (tab === "products" ? `import.pf.${k}` : tab === "simple" ? `import.sf.${k}`
    : tab === "materials" ? `import.mf.${k}` : `import.f.${k}`);
  const tag = (c: string, i: number) => Object.entries(map).filter(([, v]) => v === c)
    .map(([k]) => <div key={k + i} className="map-tag">{t(tagKey(k), { defaultValue: t(`import.pf.${k}`) })}</div>);
  return (
    <div className="scroll preview" data-testid="xi-preview">
      <table className="simple">
        <thead><tr><th>#</th>{pv.columns.map((c, i) => <th key={c}>{c}{tag(c, i)}</th>)}</tr></thead>
        <tbody>
          {pv.rows.map((r, i) => {
            const n = i + 1;
            const out = n < cfg.start_row || (cfg.end_row > 0 && n > cfg.end_row);
            return <tr key={i} className={out ? "muted" : ""}><td>{n}</td>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>;
          })}
        </tbody>
      </table>
    </div>
  );
}

function ReportBox({ r, qtyOnly }: { r: Report; qtyOnly: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="xi-report" data-testid="xi-report">
      <b>{t("import.check_result")}: </b>
      {qtyOnly ? t("import.rep_qty", { n: r.updated_products })
        : t("import.rep_full", { n: r.imported, m: r.created_ops.filter((o) => !o.type || o.type === "CS").length, p: r.created_products, e: r.created_edges.length })}
      {r.zero_skipped > 0 && <> · {t("import.rep_zero", { n: r.zero_skipped })}</>}
      {!qtyOnly && (r.simple_rows ?? 0) > 0 && <> · {t("xi18.rep_simple", { n: r.simple_rows, m: r.created_o?.length ?? 0 })}</>}
      {!qtyOnly && ((r.materials_added ?? 0) + (r.materials_existing ?? 0)) > 0 && <> · {t("xi18.rep_materials", {
        n: r.materials_added ?? 0, m: r.materials_existing ?? 0 })}</>}
      {!qtyOnly && (r.linear_imported ?? 0) > 0 && <> · {t("xi18.rep_linear", { n: r.linear_imported })}</>}
      {!qtyOnly && r.linked && (r.linked.sp + r.linked.gr + r.linked.xnc) > 0 && <> · {t("xi18.rep_linked", {
        s: r.linked.sp, g: r.linked.gr, x: r.linked.xnc })}</>}
      {r.skipped.length > 0 && (
        <ul>{r.skipped.slice(0, 6).map((s, i) => <li key={i}>{s.row}: {s.reason}</li>)}
          {r.skipped.length > 6 && <li>… {t("import.rep_more", { n: r.skipped.length - 6 })}</li>}</ul>
      )}
      {r.warnings.length > 0 && <ul className="muted">{r.warnings.slice(0, 4).map((w, i) => <li key={i}>{w}</li>)}</ul>}
    </div>
  );
}
