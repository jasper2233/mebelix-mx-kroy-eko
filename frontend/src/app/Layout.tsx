// Umumiy joylashuv (UI_SPEC §0): chap akkordeon + asosiy maydon.
import { openHelp } from "../features/help/helpStore";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { LucideIcon } from "lucide-react";
import { toneProps } from "../shared/iconTone";
import { Factory, FileText, FolderOpen, CircleQuestionMark, Languages, LogOut, Printer, Settings, User, SquareX } from "lucide-react";
import { qc, useAppSettings, useMe, useProject } from "../api/hooks";
import { hasToken, setToken } from "../api/client";
import { useUI, type Section } from "../store/ui";
import { cx } from "../shared/ui";
import { useHotkeys } from "../shared/hotkeys";
import { Logo } from "./Logo";
import { ProjectsMenu, ProjectsView } from "../features/projects/Projects";
import { ProjectMenu } from "../features/project/ProjectMenu";
import { ProjectView } from "../features/project/ProjectView";
import { PrintMenu, PrintView } from "../features/print/Print";
import { SettingsMenu, SettingsView } from "../features/settings/Settings";
import { HelpMenu, HelpModal, HelpView } from "../features/help/Help";
import { MesMenu, MesView } from "../features/mes/MesPanel";
import { Workshop } from "../features/workshop/Workshop";
import "./layout.css";
import { LANGS, LANG_LABEL } from "../i18n/lang";

function SideButton(props: { icon: LucideIcon; label: ReactNode; active?: boolean; onClick: () => void; testid?: string;
  disabled?: boolean; title?: string }) {
  const Icon = props.icon;
  return (
    <button type="button" className={cx("side-btn", props.active && "side-btn-active")} onClick={props.onClick}
      data-testid={props.testid} disabled={props.disabled} title={props.title}>
      <span className="side-ico"><Icon size={16} {...toneProps(props.icon, props.disabled)} /></span> <span>{props.label}</span>
    </button>
  );
}

export function Layout() {
  const { t } = useTranslation();
  const ui = useUI();
  const me = useMe();
  const project = useProject(ui.projectId);
  const open = !!ui.projectId && !!project.data;
  const app = useAppSettings();
  const mesOn = !!app.data?.mes_enabled;           // «MES интеграция» yoqilganda chap paneldagi qator faollashadi
  const sec: Section = (ui.section === "mes" && !mesOn) || (ui.section === "print" && !open) ? "project" : ui.section;
  const go = (s: Section) => ui.set({ section: s, view: "main" });

  // F1 (onlayn yordamdagidek — kontekst bo'yicha): ochiq operatsiya EL / GR / CS bo'lsa — o'sha mavzu, aks holda — «Справка» bo'limi
  useHotkeys("global", {
    f1: () => {
      const typ = ui.section === "project" ? project.data?.operations.find((o) => o.id === ui.opId)?.type : undefined;
      const topic = typ === "EL" ? "el" : typ === "GR" ? "gr" : typ === "CS" ? "cut" : typ === "CL" ? "cl" : typ === "O" ? "o"
        : typ === "LB" ? "lb" : null;
      if (topic) openHelp(topic);
      else ui.set({ section: "help" });
    },
  });

  if (ui.view === "workshop") return <Workshop />;

  let menu: ReactNode = null;
  let main: ReactNode;
  if (sec === "print") {
    menu = <PrintMenu />;
    main = <PrintView />;
  } else if (sec === "mes") {
    menu = <MesMenu />;
    main = <MesView />;
  } else if (sec === "settings") {
    menu = <SettingsMenu />;
    main = <SettingsView />;
  } else if (sec === "help") {
    menu = <HelpMenu />;
    main = <HelpView />;
  } else {
    if (sec === "lang") {
      menu = (
        <div className="side-menu">
          {LANGS.map((l) => (
            <button key={l} type="button" className={cx("side-item", ui.lang === l && "side-item-active")}
              onClick={() => ui.setLang(l)} data-testid={`lang-${l}`} lang={l}>
              {LANG_LABEL[l]}
            </button>
          ))}
        </div>
      );
    } else menu = open ? <ProjectMenu project={project.data!} /> : <ProjectsMenu />;
    main = open ? <ProjectView project={project.data!} /> : <ProjectsView />;
  }

  // «Выйти»: JWT (MES SSO) tokeni bo'lsa — o'chiriladi va ma'lumot qayta so'raladi; mahalliy rejimda kirish talab qilinmaydi
  const logout = () => {
    if (hasToken()) {
      setToken(null);
      void qc.invalidateQueries();
      ui.toast(t("menu.logout_done"), "ok");
    } else ui.toast(t("menu.logout_local"), "info");
  };
  // Akkordeon: faol bo'limgacha bo'lgan tugmalar yuqorida, uning menyusi qolgan joyni egallaydi, keyingilari pastda
  // (bo'sh oraliq qolmaydi — xodimlarga tanish joylashuv). Pastki tartib xodimlar o'rgangandek: [Печать отчета], Настройки,
  // Закрыть проект / Выйти, Справка; MebeliX qo'shimchasi «MES» — eng oxirida (boshqa bandlarni surmaydi).
  const items: { key: Section | "close" | "logout"; node: ReactNode }[] = [
    { key: "lang", node: <SideButton icon={Languages} label={t("menu.language")} active={sec === "lang"} onClick={() => go("lang")} /> },
    { key: "project", node: <SideButton icon={open ? FileText : FolderOpen} label={open ? t("menu.project") : t("menu.projects")}
        active={sec === "project"} onClick={() => go("project")} testid="side-project" /> },
    // «Печать отчета» — faqat ochiq loyihada (loyihalar ro'yxatida bo'lim yo'q)
    ...(open ? [{ key: "print" as const, node: <SideButton icon={Printer} label={t("menu.print")} active={sec === "print"}
        onClick={() => go("print")} testid="side-print" /> }] : []),
    { key: "settings", node: <SideButton icon={Settings} label={t("menu.settings")} active={sec === "settings"}
        onClick={() => go("settings")} testid="side-settings" /> },
    open
      ? { key: "close" as const, node: <SideButton icon={SquareX} label={t("menu.close_project")}
          onClick={() => ui.openProject(null)} testid="side-close" /> }
      : { key: "logout" as const, node: <SideButton icon={LogOut} label={t("menu.logout")} onClick={logout} testid="side-logout" /> },
    { key: "help", node: <SideButton icon={CircleQuestionMark} label={t("menu.help")} active={sec === "help"}
        onClick={() => go("help")} testid="side-help" /> },
    { key: "mes", node: <SideButton icon={Factory} label={t("menu.mes")} active={sec === "mes"} onClick={() => go("mes")} testid="side-mes"
        disabled={!mesOn} title={mesOn ? undefined : t("menu.mes_off")} /> },
  ];
  // «Язык» menyusi «Проект» menyusi o'rnida ko'rsatiladi (tanlash — bitta bosish)
  const cut = items.findIndex((i) => i.key === (sec === "lang" ? "project" : sec)) + 1;
  const head = items.slice(0, cut);
  const rest = items.slice(cut);

  return (
    <div className="app">
      <aside className="side">
        <Logo />
        <div className="side-user"><User size={13} /> {me.data?.name ?? "…"}</div>
        {head.map((i) => <div key={i.key} style={{ display: "contents" }}>{i.node}</div>)}
        <div className="side-scroll">{menu}</div>
        <div className="side-rest">
          {rest.map((i) => <div key={i.key} style={{ display: "contents" }}>{i.node}</div>)}
        </div>
      </aside>
      <main className="main">{main}</main>
      {ui.helpModal && <HelpModal />}
    </div>
  );
}
