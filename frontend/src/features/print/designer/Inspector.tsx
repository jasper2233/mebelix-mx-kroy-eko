// Etiketka vizual redaktori: tanlangan element xossalari (x, y, w, h, shrift, tekislash, rang, ifoda maydonlari + «ƒ» ExprHelper).
import { useRef } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Trash, Upload, X } from "lucide-react";
import { showError } from "../../../shared/dialogs";
import { Check, cx } from "../../../shared/ui";
import type { LabelIssue, TplElement } from "../labelsApi";
import { FxInput } from "./FxInput";
import { getStroke, numLit, parseField, setStroke } from "./model";

type Kind = "n" | "a" | "f" | "c" | "s" | "k" | "p" | "i" | "t";
interface F { k: string; kind: Kind; opts?: string[]; half?: boolean }
const n = (k: string): F => ({ k, kind: "n", half: true });
const IMG_MAX = 200 * 1024;

function specFor(el: TplElement): F[] {
  switch (el.t) {
    case "text": return [{ k: "text", kind: "a" }, n("x"), n("y"), n("size"), n("maxw"), { k: "align", kind: "s", opts: ["left", "center", "right"], half: true }, n("rotate"),
      { k: "font", kind: "s", opts: ["", "mono"], half: true }, { k: "bold", kind: "f", half: true }, { k: "italic", kind: "f", half: true }, { k: "wrap", kind: "f", half: true },
      n("lines"), n("line_h"), { k: "color", kind: "c" }];
    case "rect": return [n("x"), n("y"), n("w"), n("h"), { k: "stroke", kind: "k" }, { k: "fill", kind: "c" }, n("radius")];
    case "line": return [n("x1"), n("y1"), n("x2"), n("y2"), { k: "stroke", kind: "k" }];
    case "bezier": return [n("x1"), n("y1"), n("c1x"), n("c1y"), n("c2x"), n("c2y"), n("x2"), n("y2"), { k: "stroke", kind: "k" }];
    case "image": return [n("x"), n("y"), n("w"), n("h"), { k: "src", kind: "i" }];
    case "barcode": return String(el.kind ?? "qr").toLowerCase() === "code128"
      ? [{ k: "kind", kind: "s", opts: ["qr", "code128"] }, { k: "data", kind: "a" }, n("x"), n("y"), n("w"), n("h"), n("quiet"), n("rotate"), { k: "caption", kind: "f" }, { k: "color", kind: "c" }]
      : [{ k: "kind", kind: "s", opts: ["qr", "code128"] }, { k: "data", kind: "a" }, n("x"), n("y"), n("size"), n("quiet"), { k: "ec", kind: "s", opts: ["l", "m", "q", "h"], half: true },
        n("rotate"), { k: "color", kind: "c" }];
    case "part": case "edges": return [n("x"), n("y"), n("w"), n("h")];
    case "group": return [n("origin.0"), n("origin.1"), n("rotate")];
    case "if": return [{ k: "cond", kind: "a" }];
    case "var": return [{ k: "name", kind: "t" }, { k: "expr", kind: "a" }];
    case "polyline": return [{ k: "points", kind: "p" }, { k: "closed", kind: "f" }, { k: "stroke", kind: "k" }, { k: "fill", kind: "c" }];
    case "arc": return [n("cx"), n("cy"), n("r"), n("a1"), n("a2"), { k: "stroke", kind: "k" }, { k: "fill", kind: "c" }];
    case "ellipse": return [n("cx"), n("cy"), n("rx"), n("ry"), { k: "stroke", kind: "k" }, { k: "fill", kind: "c" }];
    default: return [];
  }
}

const valOf = (el: TplElement, k: string): string => {
  const v = k.startsWith("origin.") ? (Array.isArray(el.origin) ? el.origin[Number(k.slice(7))] : undefined) : el[k];
  return v === undefined || v === null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v);
};
const errKey = (k: string): string => (k.startsWith("origin.") ? `origin[${Number(k.slice(7)) + 1}]` : k);
const HEX_RE = /^#[0-9a-fA-F]{6}$/;

export interface InspectorProps {
  el: TplElement; path: string; errors: LabelIssue[];
  onEdit: (fn: (el: TplElement) => void, merge?: string) => void;
  onFx: (current: string, apply: (v: string) => void) => void;
  branch: "then" | "else"; onBranch: (b: "then" | "else") => void;
}

export function Inspector({ el, path, errors, onEdit, onFx, branch, onBranch }: InspectorProps) {
  const { t } = useTranslation();
  const fileRef = useRef<HTMLInputElement>(null);
  const err = (k: string): string | undefined => {
    const ek = errKey(k);
    const hit = errors.find((e) => e.path === path && (e.field === ek || e.field.startsWith(`${ek}[`) || e.field.startsWith(`${ek}.`)));
    return hit?.message;
  };
  const tid = (k: string) => `lbd-prop-${k}`;
  const edit = (k: string, merge?: string) => (raw: string) => onEdit((e) => {
    if (k.startsWith("origin.")) {
      const o = Array.isArray(e.origin) ? [...e.origin] : [0, 0];
      o[Number(k.slice(7))] = parseField(raw || "0");
      e.origin = o;
    } else if (raw.trim() === "") delete e[k];
    else e[k] = parseField(raw);
  }, merge ?? `f:${path}:${k}`);

  const uploadImage = (f: File | undefined) => {
    if (!f) return;
    if (!/^image\/(png|jpeg)$/.test(f.type)) { showError(new Error(t("lbd.img_type"))); return; }
    if (f.size > IMG_MAX) { showError(new Error(t("lbd.img_size"))); return; }
    const rd = new FileReader();
    rd.onload = () => { const src = String(rd.result); onEdit((e) => { e.src = src; if (numLit(e.w) === null) e.w = 12; if (numLit(e.h) === null) e.h = 12; }); };
    rd.readAsDataURL(f);
    if (fileRef.current) fileRef.current.value = "";
  };

  const row = (f: F) => {
    const label = t(`lbd.f.${f.k}`);
    const e = err(f.k);
    switch (f.kind) {
      case "n":
        return <label key={f.k} className="lbd-f lbd-half"><span>{label}</span>
          <FxInput value={valOf(el, f.k)} onCommit={edit(f.k)} error={e} testid={tid(f.k)} onFx={onFx} /></label>;
      case "a":
        return <label key={f.k} className="lbd-f"><span>{label}</span>
          <FxInput value={valOf(el, f.k)} onCommit={edit(f.k, "")} error={e} multiline rows={f.k === "text" ? 3 : 2} testid={tid(f.k)} onFx={onFx} mono /></label>;
      case "t":
        return <label key={f.k} className="lbd-f"><span>{label}</span>
          <FxInput value={valOf(el, f.k)} onCommit={(v) => onEdit((x) => { x[f.k] = v; })} error={e} testid={tid(f.k)} /></label>;
      case "s":
        return <label key={f.k} className="lbd-f lbd-half"><span>{label}</span>
          <select className="inp sel" value={valOf(el, f.k) || (f.opts?.[0] ?? "")} data-testid={tid(f.k)}
            onChange={(ev) => onEdit((x) => {
              const v = ev.target.value;
              if (v === "") delete x[f.k]; else x[f.k] = v;
              if (f.k === "kind") {                                             // QR ↔ Code128: yetishmaydigan o'lchamlar
                if (v === "code128") { if (x.w === undefined) x.w = 40; if (x.h === undefined) x.h = 10; delete x.size; }
                else { if (x.size === undefined) x.size = 15; delete x.w; delete x.h; }
              }
            })}>
            {(f.opts ?? []).map((o) => <option key={o} value={o}>{o === "" ? t("lbd.default") : o}</option>)}
          </select></label>;
      case "f": {
        const v = el[f.k];
        const isLit = v === undefined || v === null || typeof v === "boolean";
        return <div key={f.k} className="lbd-f lbd-half lbd-flag">
          {isLit
            ? <Check checked={Boolean(v)} label={label} testid={tid(f.k)} onChange={(c) => onEdit((x) => { x[f.k] = c; }, `f:${path}:${f.k}`)} />
            : <><span>{label}</span><FxInput value={String(v)} onCommit={edit(f.k)} error={e} testid={tid(f.k)} onFx={onFx} /></>}
          <button type="button" className="lbd-fxbtn" title={isLit ? t("lbd.flag_expr") : t("lbd.flag_lit")} data-testid={`${tid(f.k)}-mode`}
            onClick={() => onEdit((x) => { x[f.k] = isLit ? String(Boolean(v)) : String(v).trim().toLowerCase() === "true"; })}>{isLit ? "ƒ" : "☑"}</button>
        </div>;
      }
      case "c": {
        const v = valOf(el, f.k);
        return <label key={f.k} className="lbd-f"><span>{label}</span>
          <span className="lbd-color">
            <input type="color" value={HEX_RE.test(v) ? v : "#000000"} data-testid={`${tid(f.k)}-pick`}
              onChange={(ev) => onEdit((x) => { x[f.k] = ev.target.value; }, `f:${path}:${f.k}`)} />
            <input className="inp" value={v} placeholder="#000000" data-testid={tid(f.k)} onChange={(ev) => onEdit((x) => { if (ev.target.value) x[f.k] = ev.target.value; else delete x[f.k]; }, `f:${path}:${f.k}`)} />
            {v && <button type="button" className="lbd-fxbtn" title={t("lbd.clear")} onClick={() => onEdit((x) => { delete x[f.k]; })}><X size={11} /></button>}
          </span></label>;
      }
      case "k": {
        const st = getStroke(el);
        return <div key={f.k} className="lbd-f lbd-pair"><span>{t("lbd.f.stroke")}</span>
          <FxInput value={String(st.w)} placeholder="mm" error={err("stroke")} testid={tid("stroke_w")} onFx={onFx}
            onCommit={(v) => onEdit((x) => { const s2 = getStroke(x); setStroke(x, v.trim() === "" ? "" : parseField(v), s2.color); }, `f:${path}:stroke`)} />
          <input type="color" value={HEX_RE.test(st.color) ? st.color : "#000000"} data-testid={tid("stroke_color")}
            onChange={(ev) => onEdit((x) => { const s2 = getStroke(x); setStroke(x, s2.w === "" ? 0.2 : s2.w, ev.target.value); }, `f:${path}:strokec`)} />
        </div>;
      }
      case "p": {
        const pts = (Array.isArray(el.points) ? el.points : []) as unknown[][];
        return <div key={f.k} className="lbd-f lbd-points" data-testid={tid("points")}><span>{label}</span>
          {pts.map((p, i) => (
            <div key={i} className="lbd-pt">
              <FxInput value={String(p?.[0] ?? "")} onCommit={(v) => onEdit((x) => { const a = JSON.parse(JSON.stringify(x.points)) as unknown[][]; a[i][0] = parseField(v); x.points = a; })}
                error={err(`points[${i + 1}][1]`)} testid={`lbd-pt-${i}-x`} onFx={onFx} />
              <FxInput value={String(p?.[1] ?? "")} onCommit={(v) => onEdit((x) => { const a = JSON.parse(JSON.stringify(x.points)) as unknown[][]; a[i][1] = parseField(v); x.points = a; })}
                error={err(`points[${i + 1}][2]`)} testid={`lbd-pt-${i}-y`} onFx={onFx} />
              <button type="button" className="lbd-fxbtn" disabled={pts.length <= 2} title={t("app.delete")}
                onClick={() => onEdit((x) => { const a = JSON.parse(JSON.stringify(x.points)) as unknown[][]; a.splice(i, 1); x.points = a; })}><Trash size={11} /></button>
            </div>))}
          <button type="button" className="lbd-add" data-testid="lbd-pt-add" disabled={pts.length >= 200}
            onClick={() => onEdit((x) => {
              const a = JSON.parse(JSON.stringify(x.points)) as unknown[][];
              const last = a[a.length - 1] ?? [0, 0];
              a.push([shiftNum(last[0]), shiftNum(last[1])]);
              x.points = a;
            })}><Plus size={12} /> {t("lbd.pt_add")}</button>
        </div>;
      }
      case "i": {
        const src = typeof el.src === "string" ? el.src : "";
        return <div key={f.k} className="lbd-f"><span>{label}</span>
          <span className="lbd-img">
            {src ? <img src={src} alt="" /> : <em className="muted">{t("lbd.no_image")}</em>}
            <button type="button" className="btn btn-sm" onClick={() => fileRef.current?.click()} data-testid="lbd-img-pick"><Upload size={13} /> {t("lbd.img_pick")}</button>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg" hidden data-testid="lbd-img-file" onChange={(ev) => uploadImage(ev.target.files?.[0])} />
          </span></div>;
      }
      default: return null;
    }
  };

  const fields = specFor(el);
  return (
    <div className="lbd-insp" data-testid="lbd-inspector">
      <div className="lbd-insp-h"><b>{typeTitle(el, t)}</b> <span className="muted">#{path}</span></div>
      {el.t === "if" && (
        <label className="lbd-f lbd-half"><span>{t("lbd.branch")}</span>
          <select className="inp sel" value={branch} onChange={(ev) => onBranch(ev.target.value === "else" ? "else" : "then")} data-testid="lbd-branch">
            <option value="then">then</option><option value="else">else</option>
          </select></label>
      )}
      <div className="lbd-fields">{fields.map(row)}</div>
      <label className="lbd-f"><span>{t("lbd.f.comment")}</span>
        <input className="inp" value={typeof el.comment === "string" ? el.comment : ""} data-testid={tid("comment")}
          onChange={(ev) => onEdit((x) => { if (ev.target.value) x.comment = ev.target.value; else delete x.comment; }, `f:${path}:comment`)} /></label>
      <div className={cx("lbd-errs")}>
        {errors.filter((e) => e.path === path).map((e, i) => <div key={i} className="lbx-bad" data-testid="lbd-insp-err">{e.field} — {e.message}</div>)}
      </div>
    </div>
  );
}

const shiftNum = (v: unknown): number | string => {
  const x = numLit(v);
  return x === null ? v as string : Math.round((x + 5) * 1000) / 1000;
};

export function typeTitle(el: TplElement, t: (k: string) => string): string {
  if (el.t === "barcode") return t(String(el.kind ?? "qr").toLowerCase() === "code128" ? "lb.el.code128" : "lb.el.qr");
  return t(`lb.el.${el.t}`);
}
