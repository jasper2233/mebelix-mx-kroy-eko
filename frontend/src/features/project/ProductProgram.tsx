// Mahsulot «Программа» yorlig'i (W12, parametrik mahsulot): chapda boshqaruv buyruqlari muharriri (ProgramEditor), o'ngda «Параметры»
// (Par kiritish maydonlari, ParForm), hisoblangan o'zgaruvchilar (`product.<nom>`) va pastda «Сообщения» (Msg / Err / xatolar).
// Dastur va `par_values` o'zgarishi darhol mahsulotga yoziladi (PATCH …/products/{id}); hisob — serverda (services/product_program.py).
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { CircleX, Info, TriangleAlert } from "lucide-react";
import { call } from "../../api/hooks";
import { get, patch } from "../../api/client";
import type { Product, ProgMessage, ProgramState, XncCommand } from "../../api/types";
import { cx } from "../../shared/ui";
import { ParForm } from "../xnc/ParForm";
import { ProgramEditor } from "../xnc/ProgramEditor";
import "./pprog.css";

const LEVEL_ICON = { info: Info, warning: TriangleAlert, error: CircleX } as const;

export function ProgramMessages({ messages, testid = "pprog-messages" }: { messages: ProgMessage[]; testid?: string }) {
  const { t } = useTranslation();
  return (
    <div className="pprog-msgs" data-testid={testid}>
      {messages.length === 0 && <div className="muted pprog-none">{t("pprops.no_messages")}</div>}
      {messages.map((m, i) => {
        const Icon = LEVEL_ICON[m.level];
        return (
          <div key={i} className={cx("pprog-msg", m.level)} data-level={m.level}>
            <Icon size={13} className="pprog-ic" />
            <span className="pprog-txt">{m.text}</span>
            {m.path && <span className="pth" title={t("pprog.path")}>{m.path}</span>}
          </div>
        );
      })}
    </div>
  );
}

export function ProductProgram({ pid, product, scope }: { pid: string; product: Product; scope: string }) {
  const { t } = useTranslation();
  const program = product.program ?? [];
  const values = product.par_values ?? {};
  const stamp = useMemo(() => JSON.stringify([program, values, product.qty]), [program, values, product.qty]);
  const st = useQuery({ queryKey: ["product-program", pid, product.id, stamp],
    queryFn: () => get<ProgramState>(`/projects/${pid}/products/${product.id}/program-state`) });
  const state = st.data;
  const patchProduct = (f: Partial<Product>) => void call(() => patch(`/projects/${pid}/products/${product.id}`, f));
  const setPar = (name: string, v: number | string | null) => {
    const next = { ...values };
    if (v === null) delete next[name]; else next[name] = v;
    patchProduct({ par_values: next });
  };
  const vars = Object.entries(state?.vars ?? product.prog_vars ?? {});
  return (
    <div className="pprog" data-testid="pprog">
      <div className="pprog-ed">
        <ProgramEditor program={program} scope={scope} onSave={(p: XncCommand[]) => patchProduct({ program: p })} />
      </div>
      <div className="pprog-side">
        <ParForm x={{ par_values: values }} params={state?.params} onSet={setPar} title={t("pprog.params")} hint={t("pprog.par_hint")} />
        <div>
          <div className="form-h">{t("pprog.vars")}</div>
          {vars.length === 0
            ? <div className="muted par-note">{t("pprog.vars_none")}</div>
            : <table className="simple pprog-vars" data-testid="pprog-vars"><tbody>
                {vars.map(([k, v]) => <tr key={k}><td className="pk">product.{k}</td><td className="num">{Math.round(v * 1e6) / 1e6}</td></tr>)}
              </tbody></table>}
          <div className="par-note">{t("pprog.vars_hint")}</div>
        </div>
        <div>
          <div className="form-h">{t("pprops.messages")}{state ? ` (${state.messages.length})` : ""}</div>
          <ProgramMessages messages={state?.messages ?? product.prog_messages ?? []} />
        </div>
      </div>
    </div>
  );
}
