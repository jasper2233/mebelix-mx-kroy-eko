// «Справка»: klaviatura yorliqlari, ish oqimi, formulalar, EL/GR parametrlari, ifodalar tili, stanoklar, MES, «Что нового».
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { usePpMachines } from "../../api/hooks";
import { HOTKEYS } from "../../shared/hotkeys";
import { ExprHelper, ExprLanguage, type ExprVariable } from "../../shared/ExprHelper";
import { Btn, Modal, cx } from "../../shared/ui";
import { useUI } from "../../store/ui";
import { EL_HELP, GR_HELP, HELP_TOPICS, useHelp, type HelpTopic } from "./helpStore";
import { GrSketch } from "../el/GrSketch";
import "./help.css";

/** «Проверка выражения» namunasi uchun sinov o'zgaruvchilari (qiymatlarini tahrirlash mumkin). */
const DEMO_VARS: ExprVariable[] = [{ name: "dx", sample: 720 }, { name: "dy", sample: 560 }, { name: "name", sample: "Shkaf" }, { name: "qty", sample: 3 }];

export function HelpMenu() {
  const { t } = useTranslation();
  const topic = useHelp((s) => s.topic);
  const set = useHelp((s) => s.set);
  return (
    <div className="side-menu">
      {HELP_TOPICS.map((k) => (
        <button key={k} type="button" className={cx("side-item", topic === k && "side-item-active")} onClick={() => set(k)}
          data-testid={`help-topic-${k}`}>{t(`help.topic.${k}`)}</button>
      ))}
    </div>
  );
}

/** Parametrlar bo'yicha yordam bandlari (har biri langar: `help-<bo'lim>-<id>`; panellardagi «?» shu yerga olib keladi). */
function ParamHelp({ topic, items }: { topic: "el" | "gr"; items: { id: string; label: string }[] }) {
  const { t } = useTranslation();
  return (
    <>
      {items.map((it) => (
        <section key={it.id} id={`help-${topic}-${it.id}`} className="help-param" data-testid={`help-${topic}-${it.id}`}>
          <h3>{t(it.label)}</h3>
          <p>{t(`help.${topic}.${it.id}`)}</p>
        </section>
      ))}
    </>
  );
}

/** «Что нового»: versiyalar (yangisi birinchi) — `whatsnew.<vNN>.{title,date,summary,iNN:{t,d}}` kalitlaridan. */
interface WnItem { t: string; d: string }
function WhatsNew() {
  const { t } = useTranslation();
  const all = t("whatsnew", { returnObjects: true }) as unknown as Record<string, unknown>;
  const versions = Object.keys(all).filter((k) => /^v\d/.test(k)).sort().reverse();
  return (
    <div className="wn" data-testid="whatsnew">
      <p className="muted">{t("whatsnew.intro")}</p>
      {versions.map((v) => {
        const o = all[v] as Record<string, unknown>;
        const items = Object.keys(o).filter((k) => /^i\d/.test(k)).sort().map((k) => o[k] as WnItem);
        return (
          <section key={v} className="wn-ver" data-testid={`whatsnew-${v}`}>
            <div className="wn-head"><h3>{String(o.title)}</h3><span className="wn-date">{String(o.date)}</span></div>
            {!!o.summary && <p className="wn-sum">{String(o.summary)}</p>}
            <ul>{items.map((it, i) => <li key={i}><b>{it.t}</b> — {it.d}</li>)}</ul>
          </section>
        );
      })}
    </div>
  );
}

/** «Станки»: sozlamalardagi tayyor stanok nomlari ro'yxati (yoqilganlari qalin). */
function MachineList() {
  const { t } = useTranslation();
  const mach = usePpMachines();
  if (!mach.data) return null;
  return (
    <>
      {mach.data.groups.map((g) => (
        <div key={g.key}>
          <h3>{t(`pp.group.${g.key}`)} ({g.machines.length})</h3>
          <ul className="help-machines" data-testid={`help-machines-${g.key}`}>
            {g.machines.map((m) => <li key={m.key} className={m.enabled ? "on" : ""}>{m.name}{m.enabled ? " ✓" : ""}</li>)}
          </ul>
        </div>
      ))}
    </>
  );
}

function Topic({ topic }: { topic: HelpTopic }) {
  const { t } = useTranslation();
  switch (topic) {
    case "keys":
      return (
        <>
          <table className="simple keys">
            <thead><tr><th>{t("help.key")}</th><th>{t("help.action")}</th></tr></thead>
            <tbody>{HOTKEYS.map((h) => <tr key={h.keys}><td><kbd>{h.keys}</kbd></td><td>{t(`help.hk.${h.action}`)}</td></tr>)}</tbody>
          </table>
          <p className="muted">{t("help.keys_note")}</p>
        </>
      );
    case "el":
      return <div className="help-article"><div className="help-intro">{t("help.el.intro")}</div><ParamHelp topic="el" items={EL_HELP} /></div>;
    case "gr":
      return (
        <div className="help-article">
          <div className="help-intro">{t("help.gr.intro")}</div>
          <div className="help-gr-sketch"><GrSketch /></div>
          <ParamHelp topic="gr" items={GR_HELP} />
        </div>
      );
    case "expr":
      return (
        <div className="help-article" data-testid="help-expr">
          <div className="help-intro">{t("help.text.expr")}</div>
          <ExprLanguage />
          <ExprHelper compact variables={DEMO_VARS.map((v) => ({ ...v, label: t(`exprh.demo.${v.name}`) }))} />
        </div>
      );
    case "machines":
      return <div className="help-article"><div className="help-intro">{t("help.text.machines")}</div><MachineList /></div>;
    case "whatsnew":
      return <WhatsNew />;
    default:
      return <div className="help-text">{t(`help.text.${topic}`)}</div>;
  }
}

export function HelpView() {
  const { t } = useTranslation();
  const { topic, anchor, clearAnchor } = useHelp();
  // panellardagi «?» tugmasi: kerakli bandga sakraydi va qisqa vaqt ajratib ko'rsatadi
  useEffect(() => {
    if (!anchor) return;
    const el = document.getElementById(`help-${topic}-${anchor}`);
    if (el) {
      el.scrollIntoView({ block: "start" });
      el.classList.add("help-flash");
      setTimeout(() => el.classList.remove("help-flash"), 2500);
    }
    clearAnchor();
  }, [topic, anchor, clearAnchor]);
  return (
    <div className="page">
      <div className="page-head"><h2>{t(`help.topic.${topic}`)}</h2></div>
      <div className="scroll doc" data-testid="help">
        <Topic topic={topic} />
      </div>
    </div>
  );
}

/** «Справка» oynasi: joriy ekran ustida (chapda bo'limlar, o'ngda matn); standart bo'lim — «Сочетания клавиш». Yopish — «Ок». */
export function HelpModal() {
  const { t } = useTranslation();
  const close = () => useUI.getState().set({ helpModal: false });
  return (
    <Modal title={t("menu.help")} onClose={close} width="min(1400px, 96vw)" height="min(820px, 92vh)" scope="help-modal" testid="help-modal"
      footer={<Btn kind="primary" label={t("app.ok")} onClick={close} testid="help-modal-ok" />}>
      <div className="help-modal-body">
        <div className="help-modal-menu"><HelpMenu /></div>
        <div className="help-modal-main"><HelpView /></div>
      </div>
    </Modal>
  );
}
