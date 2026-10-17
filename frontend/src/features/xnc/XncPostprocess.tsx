// XNC → ishlov markazi (postprotsessor). Ikki bosqich (xodimlarga tanish tartib):
//  1) «Постпроцессоры» — stanoklar ro'yxati (+ JSON va shablon profillari);
//  2) stanok oynasi: «Операции» (loyihaning XNC dasturlari, belgilash katakchalari — joriy operatsiya belgilangan) va
//     «Параметры» (detalni uzun tomoni bilan burish, eslatma). «Ок» — bitta dastur fayli yoki belgilanganlar zip da.
// O'rnatilgan formati yo'q chiqishlar (JSON, shablon profili) — ro'yxatdan bosilganda darhol joriy operatsiya uchun yuklanadi.
import { showError } from "../../shared/dialogs";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { CheckSquare, Cpu, FileText, ListChecks, SlidersHorizontal, Square } from "lucide-react";
import { download } from "../../api/client";
import type { Operation, PostprocessorInfo, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, IconBtn, Modal, Sel, Tabs } from "../../shared/ui";
import { useXncPostprocessors } from "./xncApi";

type LongSide = "any" | "horizontal" | "vertical";
const fail = (e: unknown) => showError(e);

export function XncPostprocessDialog({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const ui = useUI();
  const pps = useXncPostprocessors();
  const items = (pps.data ?? []).filter((i) => i.kind !== "saw");     // pil markazi shablonlari XNC uchun emas (QA #14)
  const [cur, setCur] = useState<PostprocessorInfo | null>(null);
  const label = (i: PostprocessorInfo) => i.builtin ? t(`xnc.pp.builtin.${i.key}`, { defaultValue: i.name })
    : (i.machine && i.label) || i.name;
  const pick = (i: PostprocessorInfo) => {
    if (i.machine && i.native) { setCur(i); return; }
    const q: Record<string, string | number | undefined> = i.profile_id && !i.machine ? { profile_id: i.profile_id } : { key: i.key };
    void download(`/projects/${project.id}/operations/${op.id}/postprocess`, q).then(onClose).catch(fail);
  };
  if (cur) return <MachineDialog project={project} op={op} item={cur} title={label(cur)} onClose={onClose} onBack={() => setCur(null)} />;
  return (
    <Modal title={t("pp.dialog_title")} onClose={onClose} width={520} scope="xnc-pp" testid="xnc-pp-dialog"
      footer={<>
        <Btn label={t("menu.settings")} onClick={() => { onClose(); ui.set({ section: "settings" }); }} />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="ppick-list">
        {items.map((i) => {
          const off = !!i.machine && !i.available;
          const Icon = i.machine ? Cpu : FileText;
          return (
            <button key={i.key} type="button" className="ppick-item" disabled={off} data-testid={`xnc-pp-${i.key}`}
              title={off ? t("xnc.pp.unbound") : i.note || undefined} onClick={() => pick(i)}>
              <Icon size={15} /> <span>{label(i)}</span>
              {i.extension ? <span className="muted"> (.{i.extension})</span> : null}
              {off ? <span className="muted"> — {t("xnc.pp.unbound")}</span> : null}
            </button>
          );
        })}
      </div>
    </Modal>
  );
}

function MachineDialog({ project, op, item, title, onClose, onBack }: {
  project: Project; op: Operation; item: PostprocessorInfo; title: string; onClose: () => void; onBack: () => void;
}) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"ops" | "params">("ops");
  const [side, setSide] = useState<LongSide>("any");
  const ops = useMemo(() => project.operations.filter((o) => o.type === "XNC" && o.xnc), [project.operations]);
  const [sel, setSel] = useState<Set<string>>(() => new Set([op.id]));
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const run = () => {
    const ls = side === "any" ? undefined : side;
    const ids = ops.filter((o) => sel.has(o.id)).map((o) => o.id);
    const req = ids.length === 1
      ? download(`/projects/${project.id}/operations/${ids[0]}/postprocess`, { key: item.key, long_side: ls })
      : download(`/projects/${project.id}/postprocess-xnc`, { key: item.key, long_side: ls, ops: ids.join(",") });
    void req.then(onClose).catch(fail);
  };
  return (
    <Modal title={title} onClose={onClose} width={760} height={520} scope="xnc-pp" testid="xnc-pp-machine"
      footer={<>
        <Btn kind="primary" label={t("app.ok")} onClick={run} disabled={!sel.size} testid="xnc-pp-run" />
        <Btn label={t("xnc.pp.back")} onClick={onBack} />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <Tabs<"ops" | "params"> value={tab} onChange={setTab}
        tabs={[{ key: "ops", label: t("xnc.pp.tab_ops"), icon: ListChecks, testid: "xnc-pp-tab-ops" },
          { key: "params", label: t("xnc.pp.tab_params"), icon: SlidersHorizontal, testid: "xnc-pp-tab-params" }]}
        right={tab === "ops" ? <>
          <IconBtn icon={CheckSquare} title={t("xnc.pp.select_all")} testid="xnc-pp-all" onClick={() => setSel(new Set(ops.map((o) => o.id)))} />
          <IconBtn icon={Square} title={t("xnc.pp.select_none")} testid="xnc-pp-none" onClick={() => setSel(new Set())} />
        </> : undefined} />
      {tab === "ops" ? (
        <div className="xpp-ops">
          <table className="plain-table">
            <thead><tr>
              <th style={{ width: 40 }}>№</th><th style={{ width: 44 }}>{t("xnc.pp.col_sel")}</th>
              <th>{t("xnc.pp.col_code")}</th><th>{t("xnc.pp.col_name")}</th><th style={{ width: 54 }}>{t("xnc.pp.col_qty")}</th>
            </tr></thead>
            <tbody>
              {ops.map((o, i) => (
                <tr key={o.id} className={o.id === op.id ? "row-cur" : undefined} onClick={() => toggle(o.id)}>
                  <td className="num">{i + 1}</td>
                  <td className="ctr"><input type="checkbox" checked={sel.has(o.id)} readOnly data-testid={`xnc-pp-op-${i}`} /></td>
                  <td>{o.code}</td><td>{o.name}</td><td className="num">{o.xnc?.qty ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="xpp">
          <div className="xpp-row">
            <span>{t("xnc.pp.long_side")}</span>
            <Sel<LongSide> value={side} width="100%" testid="xnc-pp-side" onChange={setSide}
              options={(["any", "horizontal", "vertical"] as const).map((v) => ({ value: v, label: t(`xnc.pp.ls.${v}`) }))} />
          </div>
          {item.note && <div className="warn-note">{item.note}</div>}
          <div className="muted">{t("xnc.pp.params_hint")}</div>
        </div>
      )}
    </Modal>
  );
}
