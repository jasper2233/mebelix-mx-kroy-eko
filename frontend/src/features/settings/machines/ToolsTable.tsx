// «Инструменты» jadvali (stanok sozlamalari): asbob (tur, tekislik, diametr) → stanokdagi raqam yoki nom.
// Teshik ko'p stanoklarda diametr bo'yicha tanlanadi (bo'sh qoldirish mumkin); freza va paz arrasi uchun raqam / nom kerak.
// Server: `GET/PUT /postprocessors/machines/{key}/tools` (kalit `tur:tekislik:diametr`).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Plus, Save } from "lucide-react";
import { get, put } from "../../../api/client";
import { call, qc } from "../../../api/hooks";
import { useUI } from "../../../store/ui";
import { Btn, Sel } from "../../../shared/ui";

interface ToolRow { key: string; kind: string; plane: string; d: number; ref: string }
interface ToolsPayload { key: string; rows: ToolRow[]; kinds: string[]; planes: string[] }

export function ToolsTable({ machineKey }: { machineKey: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["pp-machine-tools", machineKey], staleTime: 0,
    queryFn: () => get<ToolsPayload>(`/postprocessors/machines/${machineKey}/tools`) });
  const [rows, setRows] = useState<ToolRow[]>([]);
  const [add, setAdd] = useState({ kind: "drill", plane: "front", d: "" });
  const sig = JSON.stringify(q.data?.rows ?? []);
  useEffect(() => { setRows(JSON.parse(sig) as ToolRow[]); }, [sig]);
  if (!q.data) return null;
  const dirty = JSON.stringify(rows) !== sig;
  const save = async () => {
    const tools: Record<string, string> = {};
    for (const r of rows) if (r.ref.trim()) tools[r.key] = r.ref.trim();
    const res = await call(() => put<ToolsPayload>(`/postprocessors/machines/${machineKey}/tools`, { tools }));
    if (res) {
      qc.setQueryData(["pp-machine-tools", machineKey], res);
      useUI.getState().toast(t("app.saved"), "ok");
    }
  };
  const addRow = () => {
    const d = Number(add.d.replace(",", "."));
    if (!(d > 0 && d <= 400)) return;
    const key = `${add.kind}:${add.plane}:${String(d)}`;
    if (!rows.some((r) => r.key === key)) setRows([...rows, { key, kind: add.kind, plane: add.plane, d, ref: "" }]);
    setAdd({ ...add, d: "" });
  };
  return (
    <div className="ms-tools" data-testid="machine-tools">
      <div className="ms-head">
        <h4>{t("ppm.tools.title")}</h4>
        <Btn icon={Save} kind="primary" label={t("app.save")} testid="mt-save" disabled={!dirty} onClick={() => void save()} />
      </div>
      <p className="muted">{t("ppm.tools.hint")}</p>
      <table className="ms-tools-table">
        <thead><tr>
          <th>№</th><th>{t("ppm.tools.kind")}</th><th>{t("ppm.tools.plane")}</th><th>{t("ppm.tools.d")}</th><th>{t("ppm.tools.ref")}</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.key}>
              <td className="num">{i + 1}</td>
              <td>{t(`ppm.tools.k.${r.kind}`)}</td>
              <td>{t(`ppm.tools.p.${r.plane}`)}</td>
              <td className="num">{r.d}</td>
              <td><input className="inp" value={r.ref} maxLength={40} data-testid={`mt-ref-${r.key}`}
                onChange={(e) => setRows(rows.map((x) => (x.key === r.key ? { ...x, ref: e.target.value } : x)))} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="ms-tools-add">
        <Sel<string> value={add.kind} width={150} onChange={(v) => setAdd({ ...add, kind: v })}
          options={q.data.kinds.map((k) => ({ value: k, label: t(`ppm.tools.k.${k}`) }))} />
        <Sel<string> value={add.plane} width={130} onChange={(v) => setAdd({ ...add, plane: v })}
          options={q.data.planes.map((p) => ({ value: p, label: t(`ppm.tools.p.${p}`) }))} />
        <input className="inp" style={{ width: 70 }} placeholder="Ø" value={add.d} data-testid="mt-add-d"
          onChange={(e) => setAdd({ ...add, d: e.target.value })} />
        <Btn icon={Plus} label={t("ppm.tools.add")} testid="mt-add" onClick={addRow} />
      </div>
    </div>
  );
}
