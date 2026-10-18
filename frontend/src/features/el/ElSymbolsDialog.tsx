// (EL) «Настройка символов и цветов»: yangi kromka operatsiyalariga beriladigan belgi va ranglar jadvali
// (ilova sozlamasi `el_symbols`; backend — services/el_symbols.py).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp, Plus, Trash } from "lucide-react";
import { call, qc, useDefaults } from "../../api/hooks";
import { put } from "../../api/client";
import { useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sep, cx } from "../../shared/ui";

export interface ElSymbolRow { symbol: string; color: string }
interface ElSymbolsDoc { rows: ElSymbolRow[] }

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const SCOPE = "el-symbols";

/** Yangi qator: band bo'lmagan birinchi belgi va jadvaldagilardan farqli rang (oltin burchak bo'yicha tus). */
function freshRow(rows: ElSymbolRow[]): ElSymbolRow {
  const used = new Set(rows.map((r) => r.symbol));
  const symbol = [...LETTERS].find((c) => !used.has(c)) ?? "?";
  const colors = new Set(rows.map((r) => r.color.toLowerCase()));
  for (let i = rows.length; i < rows.length + 400; i++) {
    const color = hslHex((i * 137.508) % 360, 65, 45);
    if (!colors.has(color)) return { symbol, color };
  }
  return { symbol, color: "#808080" };
}

function hslHex(h: number, s: number, l: number): string {
  const a = (s / 100) * Math.min(l / 100, 1 - l / 100);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const c = l / 100 - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(255 * c).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

export function ElSymbolsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const q = useDefaults<ElSymbolsDoc>("el_symbols");
  const [rows, setRows] = useState<ElSymbolRow[] | null>(null);
  const [sel, setSel] = useState(0);
  useEffect(() => { if (q.data && rows === null) setRows(q.data.rows.map((r) => ({ ...r }))); }, [q.data, rows]);
  const list = rows ?? [];
  const bad = list.some((r) => r.symbol.trim().length !== 1 || !/^#[0-9a-f]{6}$/i.test(r.color));

  const insert = () => {                       // tanlangan qator oldiga (jadval bo'sh bo'lsa — birinchi qator)
    const at = Math.max(0, Math.min(sel, list.length));
    setRows([...list.slice(0, at), freshRow(list), ...list.slice(at)]);
    setSel(at);
  };
  const del = () => {
    if (!list[sel]) return;
    setRows(list.filter((_, i) => i !== sel));
    setSel(Math.max(0, Math.min(sel, list.length - 2)));
  };
  const move = (d: -1 | 1) => {
    const to = sel + d;
    if (!list[sel] || to < 0 || to >= list.length) return;
    const next = [...list];
    [next[sel], next[to]] = [next[to], next[sel]];
    setRows(next);
    setSel(to);
  };
  const upd = (i: number, f: Partial<ElSymbolRow>) => setRows(list.map((r, k) => (k === i ? { ...r, ...f } : r)));
  const save = async () => {
    if (rows === null || bad) return;
    const r = await call(() => put("/settings/el_symbols/default", { rows }));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults", "el_symbols"] }); onClose(); }
  };

  useHotkeys(SCOPE, {
    "ctrl+pageup, alt+pageup, insert": insert, delete: del,
    "ctrl+arrowup": () => move(-1), "ctrl+arrowdown": () => move(1),
    arrowup: () => setSel((s) => Math.max(0, s - 1)), arrowdown: () => setSel((s) => Math.min(list.length - 1, s + 1)),
  });

  return (
    <Modal title={t("el.sym.title")} onClose={onClose} width={380} scope={SCOPE} testid="el-symbols-dialog"
      footer={<>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void save()} disabled={rows === null || bad} testid="el-sym-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="el-sym-cancel" />
      </>}>
      {/* onlayn joylashuv: tugmalar o'ngda — Вставить, Удалить | ↑ ↓ */}
      <div className="toolbar" style={{ justifyContent: "flex-end" }}>
        <IconBtn icon={Plus} title={t("el.sym.insert")} onClick={insert} disabled={rows === null} testid="el-sym-insert" />
        <IconBtn icon={Trash} color="#c0392b" title={t("el.sym.delete")} onClick={del} disabled={!list[sel]} testid="el-sym-delete" />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => move(-1)} disabled={!list[sel] || sel <= 0} testid="el-sym-up" />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => move(1)} disabled={!list[sel] || sel >= list.length - 1}
          testid="el-sym-down" />
      </div>
      <div className="scroll el-sym-wrap">
        <table className="simple el-sym-table" data-testid="el-sym-table">
          <thead><tr><th className="el-sym-n">№</th><th>{t("el.sym.col.symbol")}</th><th>{t("el.sym.col.color")}</th></tr></thead>
          <tbody>
            {list.map((r, i) => (
              <tr key={i} className={cx(i === sel && "tr-sel")} onClick={() => setSel(i)} data-testid={`el-sym-row-${i}`}>
                <td className="num el-sym-n">{i + 1}</td>
                <td><input className={cx("inp el-sym-inp", r.symbol.trim().length !== 1 && "inp-bad")} maxLength={1} value={r.symbol}
                  title={t("el.p.one_char")} data-testid={`el-sym-symbol-${i}`} onFocus={() => setSel(i)}
                  onChange={(e) => upd(i, { symbol: e.target.value.slice(0, 1) })} /></td>
                <td className="el-sym-color" style={{ background: r.color }}>
                  <input type="color" value={r.color} title={t("el.pick_color")} data-testid={`el-sym-color-${i}`}
                    onFocus={() => setSel(i)} onChange={(e) => upd(i, { color: e.target.value })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows !== null && !list.length && <div className="muted" style={{ padding: 8 }}>{t("app.no_rows")}</div>}
      </div>
    </Modal>
  );
}
