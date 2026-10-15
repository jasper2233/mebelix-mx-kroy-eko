// Sex rejimi (planshet): QR skaner → detal yoki kroy kartasi, «Kesildi» belgisi (MES kuzatuvi).
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowLeft, CircleCheck, ScanLine } from "lucide-react";
import { ApiError, get, post } from "../../api/client";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn } from "../../shared/ui";
import { Logo } from "../../app/Logo";
import { MapView } from "../cs/MapView";
import { WorkshopOee, useWsMachine } from "../oee/WorkshopOee";

interface ScanPart { kind: "part"; project: { number: number; name: string; customer: string; project_id: string }; copy: number; total: number;
  part: { uid: number; name: string; code: string; length: number; width: number; qty: number; thickness: number | null;
    grain: boolean; edges: Record<string, string>; xnc: string[] }; material: { name: string }; product: { name: string } | null; maps: number[] }
interface ScanMap { kind: "map"; project: { number: number; name: string; customer: string; project_id: string };
  material: { op_id: string; name: string }; map: { index: number; copies: number; done: number; sheet: [number, number]; fill: number;
    cut_length_m: number; comment: string; parts: { uid: number; name: string; length: number; width: number }[] } }

export function Workshop() {
  const { t } = useTranslation();
  const [code, setCode] = useState("");
  const [info, setInfo] = useState<ScanPart | ScanMap | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [err, setErr] = useState("");
  const inp = useRef<HTMLInputElement>(null);
  const lastCode = useRef("");
  useEffect(() => { inp.current?.focus(); }, [info]);

  const scan = async (c: string) => {
    const v = c.trim();
    if (!v) return;
    setErr("");
    try {
      const r = await get<ScanPart | ScanMap>(`/mes/scan/${encodeURIComponent(v).replace(/%2F/g, "/").replace(/%3A/g, ":")}`);
      lastCode.current = v;
      setInfo(r);
      if (r.kind === "map") setProject(await get<Project>(`/projects/${r.project.project_id}`));
      else setProject(null);
    } catch (e) {
      setInfo(null);
      setErr(e instanceof ApiError ? e.message : String(e));
    }
    setCode("");
  };
  const done = async () => {
    try {
      await post(`/mes/scan/${lastCode.current}/done`, undefined, { machine: useWsMachine.getState().machine || undefined });   // OEE (W17): stanok
      await scan(lastCode.current);
      useUI.getState().toast(t("ws.marked"), "ok");
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
  };
  const op = info?.kind === "map" && project ? project.operations.find((o) => o.id === info.material.op_id) : undefined;
  const map = info?.kind === "map" && op?.result ? op.result.maps[info.map.index - 1] : undefined;
  return (
    <div className="workshop">
      <div className="ws-head">
        <Logo />
        <h1>{t("ws.title")}</h1>
        <span className="grow" />
        <Btn icon={ArrowLeft} label={t("ws.back")} onClick={() => { window.location.hash = ""; useUI.getState().set({ view: "main" }); }} />
      </div>
      <div className="ws-scan">
        <ScanLine size={28} />
        <input ref={inp} className="inp ws-input" value={code} placeholder={t("ws.placeholder")} data-testid="ws-input"
          onChange={(e) => setCode(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void scan(code); }} />
        <Btn kind="primary" label={t("ws.find")} onClick={() => void scan(code)} />
      </div>
      <WorkshopOee />
      {err && <div className="ws-err">{err}</div>}
      {info?.kind === "part" && (
        <div className="ws-card" data-testid="ws-part">
          <div className="ws-big">{info.part.uid}. {info.part.name}</div>
          <div className="ws-size">{info.part.length} × {info.part.width} × {info.part.thickness ?? ""}</div>
          <table className="simple ws-kv"><tbody>
            <tr><td>{t("ws.project")}</td><td>№{info.project.number} {info.project.name} {info.project.customer && `· ${info.project.customer}`}</td></tr>
            <tr><td>{t("ws.product")}</td><td>{info.product?.name ?? "—"}</td></tr>
            <tr><td>{t("ws.material")}</td><td>{info.material.name}</td></tr>
            <tr><td>{t("ws.copy")}</td><td>{info.copy} / {info.total}</td></tr>
            <tr><td>{t("ws.edges")}</td><td>{Object.entries(info.part.edges).map(([s, n]) => `${t(`pp.side.${s}`)}: ${n}`).join("; ") || "—"}</td></tr>
            <tr><td>XNC</td><td>{info.part.xnc.join(", ") || "—"}</td></tr>
            <tr><td>{t("ws.maps")}</td><td>{info.maps.join(", ") || "—"}</td></tr>
          </tbody></table>
        </div>
      )}
      {info?.kind === "map" && (
        <div className="ws-card" data-testid="ws-map">
          <div className="row gap wrap">
            <div className="ws-big">{t("ws.map")} №{info.map.index} · {info.material.name}</div>
            <span className="grow" />
            <div className={info.map.done >= info.map.copies ? "ws-done ok" : "ws-done"}>
              {t("ws.cut")}: <b>{info.map.done} / {info.map.copies}</b></div>
            <Btn icon={CircleCheck} kind="big" label={t("ws.mark")} onClick={() => void done()} disabled={info.map.done >= info.map.copies} testid="ws-done" />
          </div>
          <div className="muted">№{info.project.number} {info.project.name} · S {info.map.sheet[0]}×{info.map.sheet[1]} · F {info.map.fill}% · LT {info.map.cut_length_m} m</div>
          {info.map.comment && <div className="comment">{info.map.comment}</div>}
          {map && project && op && <div className="ws-map"><MapView map={map} project={project} op={op} /></div>}
        </div>
      )}
      {!info && !err && <div className="ws-hint">{t("ws.hint")}</div>}
    </div>
  );
}
