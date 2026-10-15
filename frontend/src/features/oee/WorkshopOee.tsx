// Sex rejimida OEE: stanok tanlovi («bajarildi» belgisi shu stanokka yoziladi) va «To'xtash» tugmasi (sabab tanlab).
// OEE stanoklari sozlanmagan bo'lsa — hech narsa ko'rsatilmaydi (sex rejimi avvalgidek).
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { OctagonPause, Play } from "lucide-react";
import { create } from "zustand";
import { call, qc } from "../../api/hooks";
import { get, post } from "../../api/client";
import { useUI } from "../../store/ui";
import { Btn, Modal, Sel } from "../../shared/ui";
import { reasonName, useOeeReasons, useOeeMachines, type OeeEvent } from "./oeeApi";
import "./oee.css";

const KEY = "mxk_ws_machine";
function loadKey(): string { try { return localStorage.getItem(KEY) ?? ""; } catch { return ""; } }

/** Tanlangan stanok (brauzerda eslab qolinadi) — «bajarildi» so'rovi `machine` sifatida yuboradi. */
export const useWsMachine = create<{ machine: string; set: (m: string) => void }>((set) => ({
  machine: loadKey(),
  set: (machine) => { try { localStorage.setItem(KEY, machine); } catch { /* yo'q */ } set({ machine }); },
}));

function useNow(ms: number): number {
  const [n, setN] = useState(() => Date.now());
  useEffect(() => { const id = setInterval(() => setN(Date.now()), ms); return () => clearInterval(id); }, [ms]);
  return n;
}

export function WorkshopOee() {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const machines = useOeeMachines();
  const reasons = useOeeReasons();
  const ws = useWsMachine();
  const [pick, setPick] = useState(false);
  const [note, setNote] = useState("");
  const now = useNow(15_000);
  const list = (machines.data ?? []).filter((m) => m.active);
  const cur = list.find((m) => m.key === ws.machine) ?? (list.length === 1 ? list[0] : undefined);
  useEffect(() => { if (cur && cur.key !== ws.machine) ws.set(cur.key); }, [cur, ws]);
  const open = useQuery({ queryKey: ["oee", "open-dt", cur?.key], enabled: !!cur, refetchInterval: 20_000,
    queryFn: () => get<{ open: OeeEvent | null }>("/oee/downtime/open", { machine: cur!.key }) });
  if (list.length === 0) return null;
  const ev = open.data?.open ?? null;
  const rs = (reasons.data ?? []).filter((r) => r.kind === "downtime" && r.active);
  const startStop = async (reason: string) => {
    if (!cur) return;
    const r = await call(() => post("/oee/downtime/start", { machine: cur.key, reason, note }));
    setPick(false); setNote("");
    if (r) void qc.invalidateQueries({ queryKey: ["oee", "open-dt"] });
  };
  const resume = async () => {
    if (!cur) return;
    const r = await call(() => post("/oee/downtime/stop", { machine: cur.key }));
    if (r) { void qc.invalidateQueries({ queryKey: ["oee", "open-dt"] }); useUI.getState().toast(t("oee.ws.resumed"), "ok"); }
  };
  const mins = ev?.start ? Math.max(0, Math.floor((now - Date.parse(ev.start)) / 60000)) : 0;
  const rname = reasonName(rs.find((r) => r.code === ev?.reason), lang, ev?.reason ?? "");
  return (
    <>
      <div className="ws-oee" data-testid="ws-oee">
        <span><b>{t("oee.ws.machine")}</b></span>
        <Sel value={cur?.key ?? ""} width={240} testid="ws-oee-machine" onChange={(v) => ws.set(v)}
          options={[...(cur ? [] : [{ value: "", label: t("oee.ws.choose") }]), ...list.map((m) => ({ value: m.key, label: m.name }))]} />
        <span className="grow" />
        {!ev && <Btn icon={OctagonPause} kind="danger" label={t("oee.ws.stop")} disabled={!cur} testid="ws-oee-stop" onClick={() => setPick(true)} />}
      </div>
      {ev && (
        <div className="ws-stop" data-testid="ws-oee-open">
          <OctagonPause size={26} />
          <span>{t("oee.ws.stopped")}: <b>{rname}</b> · {t("oee.ws.since", { m: mins })}</span>
          <span className="grow" />
          <Btn icon={Play} kind="big" label={t("oee.ws.resume")} testid="ws-oee-resume" onClick={() => void resume()} />
        </div>
      )}
      {pick && (
        <Modal title={t("oee.ws.stop_title")} onClose={() => setPick(false)} width={640} testid="ws-oee-dialog">
          <p className="muted">{t("oee.ws.stop_hint", { m: cur?.name ?? "" })}</p>
          <div className="ws-reasons">
            {rs.map((r) => <Btn key={r.code} label={reasonName(r, lang)} testid={`ws-oee-reason-${r.code}`} onClick={() => void startStop(r.code)} />)}
          </div>
          <input className="inp" placeholder={t("oee.ws.note")} value={note} onChange={(e) => setNote(e.target.value)} data-testid="ws-oee-note" />
        </Modal>
      )}
    </>
  );
}
