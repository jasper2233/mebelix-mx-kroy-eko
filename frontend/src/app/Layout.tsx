// Umumiy joylashuv (UI_SPEC §0): chap akkordeon + asosiy maydon.
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { LucideIcon } from "lucide-react";
import { FileText, FolderOpen, CircleQuestionMark, Languages, Printer, Settings, User, SquareX } from "lucide-react";
import { useMe, useProject } from "../api/hooks";
import { useUI, type Section } from "../store/ui";
import { cx } from "../shared/ui";
import { useHotkeys } from "../shared/hotkeys";
import { Logo } from "./Logo";
import { ProjectsMenu, ProjectsView } from "../features/projects/Projects";
import { ProjectMenu } from "../features/project/ProjectMenu";
import { ProjectView } from "../features/project/ProjectView";
import { PrintMenu, PrintView } from "../features/print/Print";
import { SettingsMenu, SettingsView } from "../features/settings/Settings";
import { HelpMenu, HelpView } from "../features/help/Help";
import { Workshop } from "../features/workshop/Workshop";

function SideButton(props: { icon: LucideIcon; label: ReactNode; active?: boolean; onClick: () => void; testid?: string }) {
  const Icon = props.icon;
  return (
    <button type="button" className={cx("side-btn", props.active && "side-btn-active")} onClick={props.onClick}
      data-testid={props.testid}>
      <Icon size={18} /> <span>{props.label}</span>
    </button>
  );
}

export function Layout() {
  const { t } = useTranslation();
  const ui = useUI();
  const me = useMe();
  const project = useProject(ui.projectId);
  const open = !!ui.projectId && !!project.data;
  const sec = ui.section;
  const go = (s: Section) => ui.set({ section: s, view: "main" });

  useHotkeys("global", {
    f1: () => ui.set({ section: "help" }),
  });

  if (ui.view === "workshop") return <Workshop />;

  let menu: ReactNode = null;
  let main: ReactNode;
  if (sec === "print") {
    menu = <PrintMenu />;
    main = <PrintView />;
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
          {(["ru", "uz"] as const).map((l) => (
            <button key={l} type="button" className={cx("side-item", ui.lang === l && "side-item-active")}
              onClick={() => ui.setLang(l)} data-testid={`lang-${l}`}>
              {l === "ru" ? "Русский (+ ўзбекча устунлар)" : "O'zbekcha (lotin)"}
            </button>
          ))}
        </div>
      );
    } else menu = open ? <ProjectMenu project={project.data!} /> : <ProjectsMenu />;
    main = open ? <ProjectView project={project.data!} /> : <ProjectsView />;
  }

  return (
    <div className="app">
      <aside className="side">
        <Logo />
        <div className="side-user"><User size={13} /> {me.data?.name ?? "…"}</div>
        <SideButton icon={Languages} label={t("menu.language")} active={sec === "lang"} onClick={() => go("lang")} />
        <SideButton icon={open ? FileText : FolderOpen} label={open ? t("menu.project") : t("menu.projects")}
          active={sec === "project"} onClick={() => go("project")} testid="side-project" />
        {(sec === "lang" || sec === "project") && <div className="side-scroll">{menu}</div>}
        <div className="side-bottom">
          <SideButton icon={Printer} label={t("menu.print")} active={sec === "print"} onClick={() => go("print")}
            testid="side-print" />
          {sec === "print" && <div className="side-scroll">{menu}</div>}
          <SideButton icon={Settings} label={t("menu.settings")} active={sec === "settings"}
            onClick={() => go("settings")} testid="side-settings" />
          {sec === "settings" && <div className="side-scroll">{menu}</div>}
          {open && <SideButton icon={SquareX} label={t("menu.close_project")} onClick={() => ui.openProject(null)}
            testid="side-close" />}
          <SideButton icon={CircleQuestionMark} label={t("menu.help")} active={sec === "help"} onClick={() => go("help")} />
          {sec === "help" && <div className="side-scroll">{menu}</div>}
        </div>
      </aside>
      <main className="main">{main}</main>
    </div>
  );
}
