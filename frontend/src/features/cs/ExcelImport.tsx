// «Импорт из Excel»: fayl → ko'rib chiqish → ustunlar xaritasi → detallar CS operatsiyasiga.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Upload } from "lucide-react";
import { call } from "../../api/hooks";
import { api } from "../../api/client";
import type { ImportPreview, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal, Num, Sel } from "../../shared/ui";

const FIELDS = ["name", "length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right", "code"] as const;
type F = (typeof FIELDS)[number];

const GUESS: [F, RegExp][] = [
  ["name", /наим|назв|nom|name|детал/i], ["length", /длин|д-на|uzun|length|^l$/i], ["width", /шир|ш-на|^en$|eni|width|^w$/i],
  ["qty", /кол|сони|soni|qty|count|шт/i], ["grain", /текст|ткт|txt|grain/i], ["edge_top", /^ов$|сверх|yuqori/i],
  ["edge_bottom", /^он$|сниз|past/i], ["edge_left", /^ол$|слев|chap/i], ["edge_right", /^оп$|справ|o'ng|ong/i],
  ["code", /код|code|kod|арт/i],
];

export function ExcelImportDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [pv, setPv] = useState<ImportPreview | null>(null);
  const [sheet, setSheet] = useState(0);
  const [start, setStart] = useState(2);
  const [map, setMap] = useState<Partial<Record<F, string>>>({});
  const [target, setTarget] = useState(op.id);
  const csOps = project.operations.filter((o) => o.type === "CS");

  const load = async (f: File, sh = 0) => {
    const fd = new FormData();
    fd.append("file", f);
    fd.append("sheet", String(sh));
    const r = await call(() => api<ImportPreview>("/import/preview", { form: fd }));
    if (!r) return;
    setPv(r);
    const head = r.rows[0] ?? [];
    const m: Partial<Record<F, string>> = {};
    head.forEach((h, i) => {
      for (const [f, re] of GUESS) if (!m[f] && re.test(h.trim())) { m[f] = r.columns[i]; break; }
    });
    if (!m.length && r.columns.length >= 3) { m.name = r.columns[0]; m.length = r.columns[1]; m.width = r.columns[2]; if (r.columns[3]) m.qty = r.columns[3]; }
    setMap(m);
  };
  const run = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("col_map", JSON.stringify(map));
    fd.append("sheet", String(sheet));
    fd.append("start_row", String(start));
    const before = project.operations.find((o) => o.id === target)?.parts.length ?? 0;
    const r = await call(() => api<Project>(`/projects/${project.id}/operations/${target}/parts/import`, { form: fd }), t("import.importing"));
    if (r) {
      const n = (r.operations.find((o) => o.id === target)?.parts.length ?? 0) - before;
      useUI.getState().toast(t("import.done", { n }), "ok");
      useUI.getState().set({ opId: target, csTab: "parts" });
      onClose();
    }
  };
  const colOpts = useMemo(() => [{ value: "", label: "—" }, ...(pv?.columns ?? []).map((c) => ({ value: c, label: c }))], [pv]);
  return (
    <Modal title={t("menu.import_excel")} onClose={onClose} width={900} height={620} testid="excel-import"
      footer={<><Btn kind="primary" label={t("import.run")} disabled={!pv || !map.length || !map.width} onClick={() => void run()} />
        <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="row gap wrap">
        <label className="btn btn-default">
          <Upload size={15} /> {file ? file.name : t("import.choose_file")}
          <input type="file" accept=".xlsx,.xlsm,.csv" hidden onChange={(e) => {
            const f = e.target.files?.[0]; if (f) { setFile(f); setSheet(0); void load(f, 0); } }} />
        </label>
        {pv && pv.sheets.length > 1 && (
          <Sel value={sheet} width={160} onChange={(v) => { setSheet(v); if (file) void load(file, v); }}
            options={pv.sheets.map((s, i) => ({ value: i, label: s }))} />
        )}
        <span>{t("import.start_row")}</span><Num value={start} min={1} width={50} onCommit={(v) => setStart(Math.round(v ?? 2))} />
        <span>{t("import.target")}</span>
        <Sel value={target} width={220} onChange={setTarget} options={csOps.map((o) => ({ value: o.id, label: o.name || o.code || "CS" }))} />
      </div>
      {pv && (
        <>
          <div className="map-fields">
            {FIELDS.map((f) => (
              <label key={f} className="map-field"><span>{t(`import.f.${f}`)}</span>
                <Sel value={map[f] ?? ""} width={70} onChange={(v) => setMap({ ...map, [f]: v || undefined })} options={colOpts} /></label>
            ))}
          </div>
          <div className="scroll preview">
            <table className="simple">
              <thead><tr><th>#</th>{pv.columns.map((c) => <th key={c}>{c}{Object.entries(map).filter(([, v]) => v === c)
                .map(([k]) => <div key={k} className="map-tag">{t(`import.f.${k}`)}</div>)}</th>)}</tr></thead>
              <tbody>
                {pv.rows.map((r, i) => (
                  <tr key={i} className={i + 1 < start ? "muted" : ""}><td>{i + 1}</td>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {!pv && <p className="muted">{t("import.excel_hint")}</p>}
    </Modal>
  );
}
