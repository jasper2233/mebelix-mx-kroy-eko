// «Настройки» (UI_SPEC §9): umumiy, postprotsessorlar (shablon), qoldiqlar ombori, katalog, MES, profillar.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { create } from "zustand";
import type { ColDef, CellValueChangedEvent } from "ag-grid-community";
import { Copy, Download, FileSpreadsheet, Plus, Save, Send, Trash, Upload } from "lucide-react";
import { call, qc, useAppSettings, useCatalog, useProfiles, useProject, useRemnants } from "../../api/hooks";
import { api, del, get, patch, post, put, setToken } from "../../api/client";
import type { AppSettings, CatalogItem, ImportPreview, PostprocessorProfile, Profile, Remnant } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { Btn, Check, Field, Modal, Num, Sel, Txt, cx, money } from "../../shared/ui";

type Page = "general" | "pp" | "remnants" | "catalog" | "mes" | "backup";
const usePage = create<{ page: Page; set: (p: Page) => void }>((set) => ({ page: "general", set: (p) => set({ page: p }) }));

export function SettingsMenu() {
  const { t } = useTranslation();
  const { page, set } = usePage();
  const pages: Page[] = ["general", "pp", "remnants", "catalog", "mes", "backup"];
  return (
    <div className="side-menu">
      {pages.map((p) => (
        <button key={p} type="button" className={cx("side-item", page === p && "side-item-active")} onClick={() => set(p)}
          data-testid={`settings-${p}`}>{t(`settings.page.${p}`)}</button>
      ))}
    </div>
  );
}

export function SettingsView() {
  const page = usePage((s) => s.page);
  if (page === "pp") return <Postprocessors />;
  if (page === "remnants") return <RemnantsWarehouse />;
  if (page === "catalog") return <Catalog />;
  if (page === "mes") return <MesPage />;
  if (page === "backup") return <Backup />;
  return <General />;
}

function General() {
  const { t } = useTranslation();
  const app = useAppSettings();
  const ui = useUI();
  const [d, setD] = useState<AppSettings | null>(null);
  useEffect(() => { if (app.data) setD(app.data); }, [app.data]);
  if (!d) return null;
  const save = async () => {
    const r = await call(() => put("/settings/app/default", d));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "app"] }); ui.setLang(d.language); ui.toast(t("app.saved"), "ok"); }
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.general")}</h2><Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} testid="settings-save" /></div>
      <div className="form1 scroll">
        <Field label={t("settings.currency")}><Txt value={d.currency} width={80} onCommit={(v) => setD({ ...d, currency: v.toUpperCase() })} /></Field>
        <Field label={t("settings.language")}><Sel value={d.language} width={220} onChange={(v) => setD({ ...d, language: v })}
          options={[{ value: "ru", label: "Русский (+ ўзбекча устунлар)" }, { value: "uz", label: "O'zbekcha (lotin)" }]} /></Field>
        <Field label={t("settings.input_mode")} hint={t("settings.input_mode_hint")}>
          <Sel value={d.input_mode_suggest} width={220} onChange={(v) => setD({ ...d, input_mode_suggest: v })}
            options={(["none", "blank", "detail", "jointed"] as const).map((v) => ({ value: v, label: v === "none" ? t("settings.no_suggest") : t(`sizemode.${v}`) }))} /></Field>
        <Field label=" "><Check checked={d.remnant_confirm} label={t("settings.remnant_confirm")} onChange={(v) => setD({ ...d, remnant_confirm: v })} /></Field>
        <Field label={t("settings.default_sheet")} unit={t("u.mm")}>
          <span className="row gap"><Num value={d.default_sheet_length} width={70} onCommit={(v) => setD({ ...d, default_sheet_length: v ?? 2750 })} /> ×
            <Num value={d.default_sheet_width} width={70} onCommit={(v) => setD({ ...d, default_sheet_width: v ?? 1830 })} /></span></Field>
        <p className="muted">{t("settings.fullscreen_hint")}</p>
      </div>
    </div>
  );
}

// ───────────────────────── Postprotsessorlar ─────────────────────────
const EMPTY_PP: PostprocessorProfile = {
  name: "Yangi stanok", extension: "txt", per_map: true, encoding: "utf-8", newline: "crlf", description: "",
  template: "{# Har karta alohida fayl #}\nSHEET;{{ f(map.sheet_length) }};{{ f(map.sheet_width) }};{{ map.copies }}\n{% for c in map.commands -%}\n{{ c.code }}{{ c.level }};{{ f(c.size) }};{{ c.count }};{{ c.ref }}\n{% endfor -%}\nEND\n",
};

function Postprocessors() {
  const { t } = useTranslation();
  const list = useProfiles<PostprocessorProfile>("postprocessor");
  const pid = useUI((s) => s.projectId);
  const project = useProject(pid);
  const [sel, setSel] = useState<number | null>(null);
  const [d, setD] = useState<PostprocessorProfile | null>(null);
  const [opId, setOpId] = useState("");
  const [pv, setPv] = useState<{ ok: boolean; text?: string; error?: string; files?: number } | null>(null);
  const cur = list.data?.find((p) => p.id === sel);
  useEffect(() => { if (cur) setD({ ...EMPTY_PP, ...cur.data, name: cur.name }); }, [cur]);
  useEffect(() => { if (sel === null && list.data?.length) setSel(list.data[0].id); }, [list.data, sel]);
  const csOps = project.data?.operations.filter((o) => o.type === "CS" && o.result) ?? [];
  useEffect(() => { if (!opId && csOps.length) setOpId(csOps[0].id); }, [csOps, opId]);
  const refresh = () => qc.invalidateQueries({ queryKey: ["profiles", "postprocessor"] });
  const save = async () => {
    if (!d) return;
    const r = sel === null
      ? await call(() => post<Profile<PostprocessorProfile>>("/settings/postprocessor", { name: d.name, data: d }))
      : await call(() => put<Profile<PostprocessorProfile>>(`/settings/postprocessor/${sel}`, { name: d.name, data: d }));
    if (r) { await refresh(); setSel(r.id); void qc.invalidateQueries({ queryKey: ["postprocessors"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  const preview = async () => {
    if (!d || !pid || !opId) return;
    const r = await call(() => post<{ ok: boolean; text?: string; error?: string; files?: number }>("/postprocessors/preview",
      { project_id: pid, op_id: opId, profile: d }));
    if (r) setPv(r);
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.pp")}</h2>
        <Btn icon={Plus} label={t("pp_ed.new")} onClick={() => { setSel(null); setD({ ...EMPTY_PP }); setPv(null); }} />
        <Btn icon={Copy} label={t("app.clone")} disabled={!d} onClick={() => { if (d) { setSel(null); setD({ ...d, name: d.name + " (2)" }); } }} />
        <Btn icon={Save} kind="primary" label={t("app.save")} disabled={!d} onClick={() => void save()} testid="pp-save" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={sel === null} onClick={async () => {
          if (sel === null || !(await askConfirm(t("pp_ed.delete_q")))) return;
          await call(() => del(`/settings/postprocessor/${sel}`)); await refresh(); setSel(null); setD(null);
          void qc.invalidateQueries({ queryKey: ["postprocessors"] });
        }} />
      </div>
      <div className="pp-page">
        <div className="pp-list">
          <div className="side-label">{t("pp_ed.builtin")}</div>
          {["CSV", "TXT (buyruqlar)", "DXF", "JSON (MES)"].map((b) => <div key={b} className="pp-item muted">{b}</div>)}
          <div className="side-label">{t("pp_ed.user")}</div>
          {(list.data ?? []).map((p) => (
            <button key={p.id} type="button" className={cx("pp-item", sel === p.id && "pp-item-active")} onClick={() => setSel(p.id)}>{p.name}</button>
          ))}
        </div>
        {d ? (
          <div className="pp-edit">
            <div className="row gap wrap">
              <Field label={t("pp_ed.name")}><Txt value={d.name} width={220} onCommit={(v) => setD({ ...d, name: v })} testid="pp-name" /></Field>
              <Field label={t("pp_ed.ext")}><Txt value={d.extension} width={60} onCommit={(v) => setD({ ...d, extension: v.replace(/^\./, "") })} /></Field>
              <Field label={t("pp_ed.encoding")}><Sel value={d.encoding} width={110} onChange={(v) => setD({ ...d, encoding: v })}
                options={["utf-8", "cp1251", "cp866", "ascii"].map((v) => ({ value: v, label: v }))} /></Field>
              <Field label={t("pp_ed.newline")}><Sel value={d.newline} width={90} onChange={(v) => setD({ ...d, newline: v })}
                options={[{ value: "crlf", label: "CRLF" }, { value: "lf", label: "LF" }]} /></Field>
              <Check checked={d.per_map} label={t("pp_ed.per_map")} onChange={(v) => setD({ ...d, per_map: v })} />
            </div>
            <textarea className="inp code" value={d.template} spellCheck={false} data-testid="pp-template"
              onChange={(e) => setD({ ...d, template: e.target.value })} />
            <details className="pp-doc"><summary>{t("pp_ed.context")}</summary><pre>{t("pp_ed.context_doc")}</pre></details>
            <div className="row gap">
              <Sel value={opId} width={260} onChange={setOpId}
                options={csOps.length ? csOps.map((o) => ({ value: o.id, label: `${project.data?.name}: ${o.name}` })) : [{ value: "", label: t("pp_ed.no_sample") }]} />
              <Btn label={t("pp_ed.preview")} onClick={() => void preview()} disabled={!opId} testid="pp-preview" />
              {pv && <span className={pv.ok ? "ok" : "warn"}>{pv.ok ? t("pp_ed.files", { n: pv.files }) : pv.error}</span>}
            </div>
            {pv?.ok && <pre className="pp-out" data-testid="pp-output">{pv.text}</pre>}
          </div>
        ) : <div className="empty">{t("pp_ed.choose")}</div>}
      </div>
    </div>
  );
}

// ───────────────────────── Qoldiqlar ombori ─────────────────────────
function RemnantsWarehouse() {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const data = useRemnants(undefined, q);
  const [add, setAdd] = useState(false);
  const [sel, setSel] = useState<number | null>(null);
  const cols = useMemo<ColDef<Remnant>[]>(() => [
    { headerName: "ID", field: "id", width: 60, cellClass: "num" },
    { headerName: t("rem.code"), field: "material_code", width: 140, editable: true },
    { headerName: t("rem.material"), field: "material_name", flex: 1, editable: true },
    { headerName: t("sheets.col.length"), field: "length", width: 80, editable: true, cellClass: "num", valueParser: (p) => parseCellNum(p.newValue) ?? p.oldValue },
    { headerName: t("sheets.col.width"), field: "width", width: 80, editable: true, cellClass: "num", valueParser: (p) => parseCellNum(p.newValue) ?? p.oldValue },
    { headerName: t("rem.thickness"), field: "thickness", width: 70, editable: true, cellClass: "num", valueParser: (p) => parseCellNum(p.newValue) ?? p.oldValue },
    { headerName: t("sheets.col.qty"), field: "qty", width: 60, editable: true, cellClass: "num", valueParser: (p) => Math.round(parseCellNum(p.newValue) ?? p.oldValue) },
    { headerName: t("u.m2"), field: "area_m2", width: 70, cellClass: "num" },
    { headerName: t("rem.source"), width: 90, valueGetter: (p) => (p.data?.source_number ? `№${p.data.source_number}` : "") },
    { headerName: t("rem.date"), field: "created_at", width: 110, valueFormatter: (p) => (p.value ? String(p.value).slice(0, 10) : "") },
    { headerName: t("rem.note"), field: "note", width: 200, editable: true },
  ], [t]);
  const onChange = (e: CellValueChangedEvent<Remnant>) => {
    if (!e.data || !e.colDef.field) return;
    void call(() => patch(`/remnants/${e.data!.id}`, { [e.colDef.field as string]: e.newValue })).then(() => qc.invalidateQueries({ queryKey: ["remnants"] }));
  };
  const total = (data.data ?? []).reduce((s, r) => s + r.area_m2 * r.qty, 0);
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.remnants")}</h2>
        <input className="inp" placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} />
        <Btn icon={Plus} label={t("app.add")} onClick={() => setAdd(true)} testid="rem-add" />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={sel === null} onClick={async () => {
          if (sel === null || !(await askConfirm(t("rem.delete_q")))) return;
          await call(() => del(`/remnants/${sel}`)); void qc.invalidateQueries({ queryKey: ["remnants"] });
        }} />
        <span className="muted">{t("rem.total", { n: data.data?.length ?? 0, a: Math.round(total * 100) / 100 })}</span>
      </div>
      <Grid<Remnant> className="grow" rowData={data.data ?? []} columnDefs={cols} getRowId={(p) => String(p.data.id)} testid="remnants-grid"
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows()[0]?.id ?? null)} onCellValueChanged={onChange} />
      {add && <AddRemnant onClose={() => setAdd(false)} />}
    </div>
  );
}

function AddRemnant({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const [r, setR] = useState({ material_code: "", material_name: "", length: 1000, width: 600, thickness: 16, qty: 1, note: "" });
  const ok = async () => {
    const x = await call(() => post("/remnants", r));
    if (x) { void qc.invalidateQueries({ queryKey: ["remnants"] }); onClose(); }
  };
  return (
    <Modal title={t("rem.add")} onClose={onClose} width={420}
      footer={<><Btn kind="primary" label={t("app.add")} onClick={() => void ok()} disabled={!r.material_code} /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form1">
        <Field label={t("rem.code")}><Txt value={r.material_code} onCommit={(v) => setR({ ...r, material_code: v })} /></Field>
        <Field label={t("rem.material")}><Txt value={r.material_name} onCommit={(v) => setR({ ...r, material_name: v })} /></Field>
        <Field label={t("sheets.col.length")} unit={t("u.mm")}><Num value={r.length} onCommit={(v) => setR({ ...r, length: v ?? 0 })} /></Field>
        <Field label={t("sheets.col.width")} unit={t("u.mm")}><Num value={r.width} onCommit={(v) => setR({ ...r, width: v ?? 0 })} /></Field>
        <Field label={t("rem.thickness")} unit={t("u.mm")}><Num value={r.thickness} onCommit={(v) => setR({ ...r, thickness: v ?? 16 })} /></Field>
        <Field label={t("sheets.col.qty")}><Num value={r.qty} min={1} onCommit={(v) => setR({ ...r, qty: Math.round(v ?? 1) })} /></Field>
        <Field label={t("rem.note")}><Txt value={r.note} onCommit={(v) => setR({ ...r, note: v })} /></Field>
      </div>
    </Modal>
  );
}

// ───────────────────────── Katalog ─────────────────────────
function Catalog() {
  const { t } = useTranslation();
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const data = useCatalog(kind, q);
  const [imp, setImp] = useState(false);
  const [sel, setSel] = useState<string | null>(null);
  const cols = useMemo<ColDef<CatalogItem>[]>(() => [
    { headerName: "ID", field: "id", width: 90 },
    { headerName: t("catalog.kind"), field: "kind", width: 80, valueFormatter: (p) => t(`catalog.kinds.${p.value}`, { defaultValue: p.value }) },
    { headerName: t("catalog.code"), field: "code", width: 130 },
    { headerName: t("catalog.name"), field: "name", flex: 1 },
    { headerName: t("catalog.unit"), field: "unit", width: 60 },
    { headerName: t("catalog.thickness"), field: "thickness", width: 70, cellClass: "num" },
    { headerName: t("catalog.size"), width: 110, valueGetter: (p) => (p.data?.length ? `${p.data.length}×${p.data.width}` : "") },
    { headerName: t("catalog.price"), field: "price", width: 100, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("catalog.stock"), field: "stock", width: 80, cellClass: "num" },
  ], [t]);
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.catalog")}</h2>
        <Sel value={kind} onChange={setKind} width={140} options={[{ value: "", label: t("catalog.all") },
          ...["sheet", "edge", "linear", "surface"].map((k) => ({ value: k, label: t(`catalog.kinds.${k}`) }))]} />
        <input className="inp" placeholder={t("projects.search")} value={q} onChange={(e) => setQ(e.target.value)} />
        <Btn icon={FileSpreadsheet} label={t("catalog.import")} onClick={() => setImp(true)} />
        <Btn icon={Trash} kind="danger" label={t("app.delete")} disabled={!sel} onClick={async () => {
          if (!sel || !(await askConfirm(t("catalog.delete_q")))) return;
          await call(() => del(`/catalog/${sel}`)); void qc.invalidateQueries({ queryKey: ["catalog"] });
        }} />
      </div>
      <p className="muted">{t("catalog.mes_hint")}</p>
      <Grid<CatalogItem> className="grow" rowData={data.data ?? []} columnDefs={cols} getRowId={(p) => p.data.id}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows()[0]?.id ?? null)} />
      {imp && <CatalogImport onClose={() => setImp(false)} />}
    </div>
  );
}

const CAT_FIELDS = ["id", "parent_id", "code", "name", "unit", "price", "stock", "thickness", "length", "width", "kind"];

function CatalogImport({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [pv, setPv] = useState<ImportPreview | null>(null);
  const [map, setMap] = useState<Record<string, string>>({});
  const [start, setStart] = useState(2);
  const [kind, setKind] = useState("sheet");
  const load = async (f: File) => {
    const fd = new FormData(); fd.append("file", f);
    const r = await call(() => api<ImportPreview>("/import/preview", { form: fd }));
    if (r) setPv(r);
  };
  const run = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file); fd.append("col_map", JSON.stringify(map)); fd.append("start_row", String(start)); fd.append("kind", kind);
    const r = await call(() => api<{ count: number }>("/catalog/import", { form: fd }));
    if (r) { useUI.getState().toast(t("import.done", { n: r.count }), "ok"); void qc.invalidateQueries({ queryKey: ["catalog"] }); onClose(); }
  };
  const opts = [{ value: "", label: "—" }, ...(pv?.columns ?? []).map((c) => ({ value: c, label: c }))];
  return (
    <Modal title={t("catalog.import")} onClose={onClose} width={860} height={580}
      footer={<><Btn kind="primary" label={t("import.run")} disabled={!pv || !map.name} onClick={() => void run()} /><Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="row gap wrap">
        <label className="btn btn-default"><Upload size={15} /> {file ? file.name : t("import.choose_file")}
          <input type="file" hidden accept=".xlsx,.csv" onChange={(e) => { const f = e.target.files?.[0]; if (f) { setFile(f); void load(f); } }} /></label>
        <span>{t("import.start_row")}</span><Num value={start} min={1} width={50} onCommit={(v) => setStart(Math.round(v ?? 2))} />
        <span>{t("catalog.default_kind")}</span>
        <Sel value={kind} width={120} onChange={setKind} options={["sheet", "edge", "linear", "surface"].map((k) => ({ value: k, label: t(`catalog.kinds.${k}`) }))} />
      </div>
      {pv && <div className="map-fields">{CAT_FIELDS.map((f) => (
        <label key={f} className="map-field"><span>{t(`catalog.f.${f}`)}</span>
          <Sel value={map[f] ?? ""} width={70} onChange={(v) => setMap({ ...map, [f]: v })} options={opts} /></label>))}</div>}
      {pv && <div className="scroll preview"><table className="simple"><thead><tr><th>#</th>{pv.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>{pv.rows.map((r, i) => <tr key={i}><td>{i + 1}</td>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody></table></div>}
    </Modal>
  );
}

// ───────────────────────── MES ─────────────────────────
function MesPage() {
  const { t } = useTranslation();
  const [tok, setTok] = useState("");
  const test = async () => {
    const r = await call(() => post<{ sent: boolean; reason?: string; url?: string }>("/mes/webhook-test"));
    if (r) useUI.getState().toast(r.sent ? t("mes.sent", { url: r.url }) : r.reason ?? "", r.sent ? "ok" : "info");
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.mes")}</h2></div>
      <div className="scroll doc">
        <p>{t("mes.intro")}</p>
        <table className="simple">
          <tbody>
            {[
              ["POST /api/mes/orders", t("mes.ep.orders")], ["GET /api/mes/orders/{ref}", t("mes.ep.order")],
              ["GET /api/projects/{id}/mes-export", t("mes.ep.export")], ["POST /api/catalog/sync", t("mes.ep.catalog")],
              ["GET /api/mes/scan/{qr}", t("mes.ep.scan")], ["POST /api/mes/scan/{qr}/done", t("mes.ep.done")],
              ["GET /api/remnants", t("mes.ep.remnants")], ["/docs", "OpenAPI (Swagger)"],
            ].map(([a, b]) => <tr key={a}><td><code>{a}</code></td><td>{b}</td></tr>)}
          </tbody>
        </table>
        <p>{t("mes.webhook")}</p>
        <Btn icon={Send} label={t("mes.test")} onClick={() => void test()} />
        <h3>JWT</h3>
        <p className="muted">{t("mes.jwt")}</p>
        <div className="row gap">
          <input className="inp" style={{ width: 420 }} placeholder="eyJhbGciOi..." value={tok} onChange={(e) => setTok(e.target.value)} />
          <Btn label={t("app.save")} onClick={() => { setToken(tok || null); void qc.invalidateQueries(); useUI.getState().toast(t("app.saved"), "ok"); }} />
          <Btn label={t("mes.logout")} onClick={() => { setToken(null); void qc.invalidateQueries(); }} />
        </div>
      </div>
    </div>
  );
}

// ───────────────────────── Profillar zaxirasi ─────────────────────────
const SCOPES = ["cs_defaults", "el_defaults", "print", "labels", "part_columns", "postprocessor", "app"];

function Backup() {
  const { t } = useTranslation();
  const exportAll = async () => {
    const out: Record<string, unknown> = {};
    for (const s of SCOPES) out[s] = await get(`/settings/${s}`);
    const blob = new Blob([JSON.stringify({ app: "MebeliX Kroy", version: 1, profiles: out }, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "mebelix-sozlamalar.json"; a.click();
  };
  const importAll = (f: File) => {
    void f.text().then(async (txt) => {
      try {
        const j = JSON.parse(txt) as { profiles: Record<string, Profile[]> };
        let n = 0;
        for (const [scope, list] of Object.entries(j.profiles ?? {})) {
          if (!SCOPES.includes(scope)) continue;
          for (const p of list) { await post(`/settings/${scope}`, { name: p.name, data: p.data, is_default: p.is_default }); n++; }
        }
        void qc.invalidateQueries();
        useUI.getState().toast(t("backup.imported", { n }), "ok");
      } catch (e) { useUI.getState().toast(String(e), "error"); }
    });
  };
  return (
    <div className="page">
      <div className="page-head"><h2>{t("settings.page.backup")}</h2></div>
      <div className="doc">
        <p>{t("backup.hint")}</p>
        <div className="row gap">
          <Btn icon={Download} label={t("backup.export")} onClick={() => void exportAll()} />
          <label className="btn btn-default"><Upload size={15} /> {t("backup.import")}
            <input type="file" hidden accept=".json" onChange={(e) => { const f = e.target.files?.[0]; if (f) importAll(f); }} /></label>
        </div>
      </div>
    </div>
  );
}

