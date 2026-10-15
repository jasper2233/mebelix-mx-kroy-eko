"""Tayyor etiketka shabloni fayli (`<program>` XML) → W4 ning JSON shabloni (W9 · LB-D importyor).

Mijozning o'z fayli ish vaqtida o'qiladi (`.lbl` / `.xml` — ildizi `program`; `.project` — undagi `<operation typeId="LB" program="…">`
lar). Qo'llab-quvvatlanmaydigan narsa jim tushib ketmaydi: natijada `warnings` ro'yxati `{code, key, count, message}` — teg/atribut
nomi va soni bilan. XML xavfsiz o'qiladi (`label_gl_common.safe_fromstring`: DTD/entity yo'q, teglar soni va chuqurligi chegaralangan).

Moslik jadvali (batafsil — docs/mebelix/T_LB_W9_IMPORT_EKSPORT.md):

  par (standart nom)        → o'tkazib yuboriladi (muharrir uchun sinov qiymati; haqiqiy qiymat loyihadan olinadi) — `info.std_pars`
  par (boshqa nom)          → `params[]` (name, type, default, title ← comment); standart qiymati ifoda bo'lsa — `vars[]` + ogohlantirish
  var (ildizda)             → `vars[]` (+ `type`, `comment`); ichma-ich var — `{"t":"var"}` elementi
  text                      → `text` (x y text size bold italic color font; w → `maxw`; align+w → x siljishi; wordBreak/multiline → `wrap`)
  qrcode                    → `barcode` kind=qr (sz → size, text → data, fillColor → color)
  rect                      → `rect` (stroke, fill); h=0 yoki w=0 — `line`
  image                     → `image` (imgdata — ichki PNG/JPEG ≤ 200 KB; ifodali rasm — faqat ichki rasm)
  part                      → `part` (x y w h; detal chizmasi o'zimizcha chiziladi — ogohlantirish)
  if / else                 → `if` (condition → cond; `else` — keyingi aka-uka teg)
  xy                        → `group` origin=[x,y] (keyingi aka-ukalarni o'z ichiga oladi; 0,0 bo'lsa — shunchaki olib tashlanadi)
  dx, dy (ifodada)          → `label.width`, `label.height`

Tizim qiymatlari yo'qolmasin uchun `layout` (printMode/columns/rows/gap/margin) shablon ichida `layout` kaliti bilan saqlanadi
(`LBParams` maydon nomlari bilan) — eksport ham, «o'lchamni qo'llash» ham shuni ishlatadi.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Optional
from xml.etree.ElementTree import Element

from ..i18n import _
from . import expr, label_tpl
from . import label_gl_common as C
from .label_gl_common import GLError, Warnings

KNOWN_ATTRS: dict[str, set[str]] = {
    "program": {"columns", "dx", "dy", "gap", "margin", "printMode", "rows"},
    "par": {"name", "type", "expr", "comment"},
    "var": {"name", "type", "expr", "comment"},
    "xy": {"enable", "x", "y"},
    "if": {"condition", "expand", "comment"},
    "else": {"expand"},
    "text": {"enable", "x", "y", "w", "h", "text", "fillColor", "fontName", "fontSize", "fontBold", "fontItalic", "rowHeight",
             "ratio", "align", "valign", "multiline", "wordBreak", "comment"},
    "qrcode": {"enable", "x", "y", "sz", "text", "fillColor", "comment"},
    "rect": {"enable", "x", "y", "w", "h", "strokeColor", "strokeWidth", "strokeDash", "fillColor", "fillHatch", "comment"},
    "image": {"enable", "x", "y", "w", "h", "imgdata", "ratio", "expr", "comment"},
    "part": {"enable", "x", "y", "w", "h", "optimalTurn", "size", "size.fontBold", "size.fontItalic", "size.top", "size.left",
             "size.fontName", "size.fontSize", "edgeband", "edgeband.fontBold", "edgeband.fontItalic", "edgeband.fontName",
             "edgeband.fontSize", "edgeband.offset", "ett", "ebt", "elt", "ert", "etd", "ebd", "eld", "erd", "length", "width",
             "comment"},
}
DRAWING = ("text", "qrcode", "rect", "image", "part")
TYPES = {"double": "double", "float": "double", "number": "double", "integer": "integer", "int": "integer", "long": "integer",
         "string": "string", "str": "string", "boolean": "boolean", "bool": "boolean"}


class _Skip(Exception):
    """Element o'tkazib yuboriladi (majburiy qiymat yo'q / ifoda juda uzun)."""


@dataclass
class GLResult:
    template: dict
    warnings: list[dict] = field(default_factory=list)
    info: dict = field(default_factory=dict)


def _b(v, default: bool = False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("true", "1", "yes", "да")


def _f(v, d: float = 0.0) -> float:
    try:
        r = float(str(v).replace(",", ".").strip())
        return r if math.isfinite(r) else d
    except (TypeError, ValueError):
        return d


def count_elements(els: list) -> int:
    return sum(1 for _p, _e in label_tpl.walk(els))


class _Conv:
    def __init__(self, root: Element, name: str):
        self.root = root
        self.name = name
        self.w = Warnings("lbx.w_")
        self.params: list[dict] = []
        self.vars: list[dict] = []
        self.std_pars = 0
        self.images = 0
        from .label_vars import VAR_NAMES
        self.var_names = VAR_NAMES
        self.declared = {e.get("name") for e in root.iter() if e.tag in ("par", "var") and e.get("name")}

    # — ifoda —
    def _idents(self, s: str) -> str:
        def fn(tok: str) -> str:
            if tok in self.declared:
                return tok
            if tok in C.LABEL_SIZE_VARS:
                return C.LABEL_SIZE_VARS[tok]
            if tok in self.var_names or tok.lower() in expr._CONST:
                return tok
            if tok in C.GL_STD:
                self.w.add("var_nodata", tok)
            else:
                self.w.add("unknown_var", tok[:40])
            return tok
        return C.rewrite_idents(s, fn)

    def _ex(self, v, keep_str: bool = False):
        """Atribut qiymati → son (literal) yoki ifoda satri; bo'sh — None; juda uzun — _Skip."""
        if v is None:
            return None
        s = v.strip()
        if not s:
            return None
        if not keep_str:
            n = C.parse_num(s)
            if n is not None:
                return n
        if len(s) > expr.MAX_SRC:
            raise _Skip()
        return self._idents(s)

    def _color(self, v) -> Optional[str]:
        c = C.norm_color(v)
        if c is None and isinstance(v, str) and v.strip():
            self.w.add("color", v.strip()[:30])
        return c

    def _enable(self, k: Element) -> tuple[bool, Optional[str]]:
        v = k.get("enable")
        if v is None:
            return True, None
        s = v.strip()
        low = s.lower()
        if low in ("", "true", "1", "yes"):
            return True, None
        if low in ("false", "0", "no"):
            return False, None
        return True, self._ex(s, keep_str=True)

    # — par / var —
    def _par(self, k: Element) -> None:
        name = (k.get("name") or "").strip()
        if not C.valid_name(name):
            self.w.add("name", name[:30])
            return
        # standart o'zgaruvchi: fayl formatining standart nomi yoki dotli kanonik nom (`part.code`); fayldagi qiymat — sinov qiymati.
        # Faqat bizning taxallusimiz bo'lgan nom (`qty`, `counter` …) — foydalanuvchi parametri (qiymati taxallusdan ustun turadi).
        if name in C.GL_STD or ("." in name and name in self.var_names):
            self.std_pars += 1
            return
        raw_t = (k.get("type") or "string").strip().lower()
        typ = TYPES.get(raw_t)
        if typ is None:
            self.w.add("par_type", raw_t[:20])
            typ = "string"
        raw = k.get("expr")
        title = (k.get("comment") or "")[:100]
        default: object
        as_var = False
        if typ == "boolean":
            if raw is None or raw.strip() == "":
                default = False
            elif raw.strip().lower() in ("true", "false"):
                default = raw.strip().lower() == "true"
            else:
                as_var = True
        elif typ in ("double", "integer"):
            n = 0 if raw is None or not raw.strip() else C.parse_num(raw)
            if n is None:
                as_var = True
            else:
                default = float(n) if typ == "double" else int(n)
        else:
            default = raw if raw is not None else ""
        if as_var:
            self.w.add("par_expr", name)
            self._add_var({"name": name, "expr": self._ex(raw, keep_str=True) or "''", "type": typ,
                           **({"comment": title} if title else {})})
            return
        if any(p["name"] == name for p in self.params):
            self.w.add("dup", name)
            self.params = [p for p in self.params if p["name"] != name]
        if len(self.params) >= label_tpl.MAX_PARAMS:
            self.w.add("limit", f"params ≤ {label_tpl.MAX_PARAMS}")
            return
        self.params.append({"name": name, "type": typ, "default": default, "title": title})

    def _var_obj(self, k: Element) -> Optional[dict]:
        name = (k.get("name") or "").strip()
        if not C.valid_name(name):
            self.w.add("name", name[:30])
            return None
        raw_t = (k.get("type") or "double").strip().lower()
        typ = TYPES.get(raw_t)
        if typ is None:
            self.w.add("par_type", raw_t[:20])
            typ = "string"
        e = self._ex(k.get("expr"), keep_str=False)
        if e is None:
            e = "''"
        elif typ == "double" and isinstance(e, int) and not isinstance(e, bool):
            e = float(e)                                  # double turi: butun literal ham haqiqiy son (7/2 = 3.5)
        v = {"name": name, "expr": e, "type": typ}
        if k.get("comment"):
            v["comment"] = k.get("comment")[:200]
        return v

    def _add_var(self, v: dict) -> None:
        if any(x["name"] == v["name"] for x in self.vars):
            self.w.add("dup", v["name"])
            self.vars = [x for x in self.vars if x["name"] != v["name"]]
        if len(self.vars) >= label_tpl.MAX_VARS:
            self.w.add("limit", f"vars ≤ {label_tpl.MAX_VARS}")
            return
        self.vars.append(v)

    # — elementlar —
    def _block(self, kids: list[Element]) -> list[dict]:
        out: list[dict] = []
        i, n = 0, len(kids)
        while i < n:
            k = kids[i]
            i += 1
            tag = k.tag
            if tag in KNOWN_ATTRS:
                for a in k.attrib:
                    if a not in KNOWN_ATTRS[tag]:
                        self.w.add("attr", f"{tag}.{a}"[:50])
            try:
                if tag == "if":
                    el = self._if(k, kids[i] if i < n and kids[i].tag == "else" else None)
                    if i < n and kids[i].tag == "else":
                        i += 1
                    out.append(el)
                elif tag == "else":
                    self.w.add("orphan_else", "else")
                elif tag == "xy":
                    on, cond = self._enable(k)
                    if not on:
                        self.w.add("disabled", "xy")
                        continue
                    ox, oy = self._ex(k.get("x")), self._ex(k.get("y"))
                    ox, oy = (0 if ox is None else ox), (0 if oy is None else oy)
                    rest = self._block(kids[i:])
                    i = n
                    if C.is_num(ox) and C.is_num(oy) and ox == 0 and oy == 0:
                        out.extend(rest)                       # nol siljish — guruh keraksiz
                    else:
                        out.append({"t": "group", "origin": [ox, oy], "elements": rest})
                elif tag == "par":
                    self._par(k)
                elif tag == "var":
                    v = self._var_obj(k)
                    if v is not None:                             # ichma-ich var: tur saqlanmaydi (shablon formatida elementga `type` yo'q)
                        out.append({"t": "var", **{a: b for a, b in v.items() if a != "type"}})
                elif tag in DRAWING:
                    on, cond = self._enable(k)
                    if not on:
                        self.w.add("disabled", tag)
                        continue
                    el = getattr(self, f"_{tag}")(k)
                    if k.get("comment") and el is not None:
                        el["comment"] = k.get("comment")[:200]
                    if el is None:
                        continue
                    if cond:
                        el = {"t": "if", "cond": cond, "then": [el]}
                    out.append(el)
                else:
                    for d in k.iter():
                        self.w.add("tag", d.tag[:30])
            except _Skip:
                self.w.add("skipped", tag)
        return out

    def _if(self, k: Element, els: Optional[Element]) -> dict:
        cond = self._ex(k.get("condition"), keep_str=True)
        if cond is None:
            raise _Skip()
        el: dict = {"t": "if", "cond": cond, "then": self._block(list(k))}
        if els is not None:
            for a in els.attrib:
                if a not in KNOWN_ATTRS["else"]:
                    self.w.add("attr", f"else.{a}"[:50])
            el["else"] = self._block(list(els))
        if k.get("comment"):
            el["comment"] = k.get("comment")[:200]
        return el

    def _text(self, k: Element) -> dict:
        x, y = self._ex(k.get("x")), self._ex(k.get("y"))
        if x is None or y is None:
            raise _Skip()
        txt = self._ex(k.get("text"), keep_str=True)
        size = self._ex(k.get("fontSize"))
        # matn `y` si — asosiy chiziq (Java drawString kabi; kromka nomlari tagiga tortilgan chiziq buni ko'rsatadi) ❓;
        # bizda `y` — yuqori chet: y_top = y − size·0.82 (label_tpl asosiy chiziqni y + size·0.82 ga qo'yadi)
        el: dict = {"t": "text", "x": x, "y": C.baseline_to_top(y, size if size is not None else 3),
                    "text": txt if txt is not None else "''"}
        if size is not None:
            el["size"] = size
        w, h = self._ex(k.get("w")), self._ex(k.get("h"))
        align = (k.get("align") or "left").strip().lower()
        if align not in ("left", "center", "right"):
            self.w.add("align", align[:20])
            align = "left"
        if w is not None:
            el["maxw"] = w
            if align == "center":
                el["x"] = C.add(x, C.half(w))
            elif align == "right":
                el["x"] = C.add(x, w)
            if align != "left":
                el["align"] = align
        elif align != "left":
            self.w.add("align", align)
        if _b(k.get("wordBreak")) or _b(k.get("multiline")):
            self.w.add("multiline", "text")
            if w is not None:
                el["wrap"] = True
                rh = self._ex(k.get("rowHeight"))
                if rh is not None:
                    el["line_h"] = rh
                el["lines"] = max(1, int(h // rh)) if C.is_num(h) and C.is_num(rh) and rh > 0 else 20
        valign = (k.get("valign") or "top").strip().lower()
        if valign != "top":                                  # faylda faqat «top» uchragan; boshqasi — ma'nosi noaniq
            self.w.add("valign", valign[:20])
        if _b(k.get("fontBold")):
            el["bold"] = True
        if _b(k.get("fontItalic")):
            el["italic"] = True
        col = self._color(k.get("fillColor"))
        if col and col != "#000000":
            el["color"] = col
        fn = (k.get("fontName") or "").strip()
        low = fn.lower()
        if low in ("", "arial", "helvetica", "sans-serif"):
            pass
        elif "courier" in low or low in ("mono", "monospace"):
            el["font"] = "mono"
        else:
            el["font"] = fn[:40]
            self.w.add("font", fn[:40])
        return el

    def _qrcode(self, k: Element) -> dict:
        x, y, sz = self._ex(k.get("x")), self._ex(k.get("y")), self._ex(k.get("sz"))
        data = self._ex(k.get("text"), keep_str=True)
        if x is None or y is None or sz is None or data is None:
            raise _Skip()
        el: dict = {"t": "barcode", "kind": "qr", "x": x, "y": y, "size": sz, "data": data}
        col = self._color(k.get("fillColor"))
        if col and col != "#000000":
            el["color"] = col
        return el

    def _rect(self, k: Element) -> dict:
        x, y, w, h = (self._ex(k.get(a)) for a in ("x", "y", "w", "h"))
        if x is None or y is None or w is None or h is None:
            raise _Skip()
        sw = self._ex(k.get("strokeWidth"))
        sc = self._color(k.get("strokeColor")) or "#000000"
        fill = self._color(k.get("fillColor"))
        dash = (k.get("strokeDash") or "0").strip()
        if dash not in ("", "0", "0.0"):
            self.w.add("dash", "rect")
        stroke = {"w": sw, "color": sc} if sw is not None and not (C.is_num(sw) and sw <= 0) else None
        if fill and (k.get("fillHatch") or "").strip() not in ("", "0"):
            self.w.add("hatch", "rect")
        if C.is_num(h) and h == 0 and not (C.is_num(w) and w == 0):          # h=0 — gorizontal chiziq
            return {"t": "line", "x1": x, "y1": y, "x2": C.add(x, w), "y2": y, "stroke": stroke or {"w": 0.2, "color": sc}}
        if C.is_num(w) and w == 0 and not (C.is_num(h) and h == 0):          # w=0 — vertikal chiziq
            return {"t": "line", "x1": x, "y1": y, "x2": x, "y2": C.add(y, h), "stroke": stroke or {"w": 0.2, "color": sc}}
        el: dict = {"t": "rect", "x": x, "y": y, "w": w, "h": h}
        if stroke:
            el["stroke"] = stroke
        if fill:
            el["fill"] = fill
        return el

    def _image(self, k: Element) -> Optional[dict]:
        x, y, w, h = (self._ex(k.get(a)) for a in ("x", "y", "w", "h"))
        if x is None or y is None or w is None or h is None:
            raise _Skip()
        if (k.get("expr") or "").strip():
            self.w.add("image_expr", "image")
        if not _b(k.get("ratio"), True):
            self.w.add("image_ratio", "image")
        data = (k.get("imgdata") or "").strip()
        if not data:
            self.w.add("image_none", "image")
            return None
        src, why = C.check_image(data)
        if src is None:
            if why == "size":
                self.w.add("image_size", "image", n=min(C.MAX_IMAGE_BYTES, label_tpl.MAX_IMAGE_B64 * 3 // 4) // 1024)
            else:
                self.w.add("image_type" if why == "type" else "image_invalid", "image")
            return None
        self.images += 1
        return {"t": "image", "x": x, "y": y, "w": w, "h": h, "src": src}

    def _part(self, k: Element) -> dict:
        x, y, w, h = (self._ex(k.get(a)) for a in ("x", "y", "w", "h"))
        if x is None or y is None or w is None or h is None:
            raise _Skip()
        self.w.add("part", "part")
        return {"t": "part", "x": x, "y": y, "w": w, "h": h}

    # — butun dastur —
    def run(self) -> GLResult:
        r = self.root
        for a in r.attrib:
            if a not in KNOWN_ATTRS["program"]:
                self.w.add("attr", f"program.{a}"[:50])
        raw_w, raw_h = _f(r.get("dx"), 58.0), _f(r.get("dy"), 40.0)
        W = min(max(raw_w, C.SIZE_MIN), C.SIZE_MAX)
        H = min(max(raw_h, C.SIZE_MIN), C.SIZE_MAX)
        if (W, H) != (raw_w, raw_h):
            self.w.add("size", f"{raw_w:g}×{raw_h:g}")
        W, H = round(W, 4), round(H, 4)
        layout = {"mode": "sheet" if int(_f(r.get("printMode"), 0)) == 0 else "roll",
                  "columns": int(min(max(_f(r.get("columns"), 3), 1), 20)), "rows": int(min(max(_f(r.get("rows"), 0), 0), 50)),
                  "gap_mm": round(min(max(_f(r.get("gap"), 2), 0), 50), 4),
                  "margin_mm": 6.0 if _b(r.get("margin"), True) else None}
        rest: list[Element] = []
        for k in r:                                              # par/var — ildizda e'lon, ketma-ket
            if k.tag in KNOWN_ATTRS and k.tag in ("par", "var"):
                for a in k.attrib:
                    if a not in KNOWN_ATTRS[k.tag]:
                        self.w.add("attr", f"{k.tag}.{a}"[:50])
            if k.tag == "par":
                self._par(k)
            elif k.tag == "var":
                v = self._var_obj(k)
                if v is not None:
                    self._add_var(v)
            else:
                rest.append(k)
        elements = self._block(rest)
        tpl = {"v": 1, "name": (self.name or "")[:100], "size": {"w": W, "h": H}, "layout": layout,
               "params": self.params, "vars": self.vars, "elements": elements}
        try:
            tpl = label_tpl.normalize_template(tpl)
        except label_tpl.TemplateError as e:
            raise GLError(_("lbx.e_tpl", e=str(e))) from e
        n_el = count_elements(tpl["elements"])
        if n_el == 0:
            raise GLError(_("lbx.e_empty"))
        info = {"elements": n_el, "params": len(tpl["params"]), "vars": len(tpl["vars"]), "images": self.images,
                "std_pars": self.std_pars}
        return GLResult(tpl, self.w.to_list(), info)


# ───────────────────────── Ochiq funksiyalar ─────────────────────────
def parse_program(data: bytes | str) -> Element:
    """`<program>` XML ini xavfsiz o'qiydi; ildiz `program` bo'lmasa — aniq xato."""
    if isinstance(data, (bytes, str)) and len(data) > C.MAX_FILE_BYTES:
        raise GLError(_("lbx.e_big", n=C.MAX_FILE_BYTES // (1024 * 1024)))
    root = C.safe_fromstring(data)
    if root.tag != "program":
        raise GLError(_("lbx.e_root", tag=str(root.tag)[:30], want="program"))
    C.check_limits(root)
    return root


def convert_program(data: bytes | str | Element, name: str = "") -> GLResult:
    """`<program>` → shablon (+ ogohlantirishlar). Xato — GLError."""
    root = data if isinstance(data, Element) else parse_program(data)
    if root.tag != "program":
        raise GLError(_("lbx.e_root", tag=str(root.tag)[:30], want="program"))
    return _Conv(root, name).run()


def programs_from_project(data: bytes) -> tuple[list[dict], int]:
    """`.project` dagi LB operatsiyalar → [{name, program, ops}] (bir xil matnli dasturlar birlashtiriladi), chegaradan ortiq soni."""
    if len(data) > C.MAX_FILE_BYTES:
        raise GLError(_("lbx.e_big", n=C.MAX_FILE_BYTES // (1024 * 1024)))
    root = C.safe_fromstring(data)
    if root.tag != "project":
        raise GLError(_("lbx.e_root", tag=str(root.tag)[:30], want="project"))
    seen: dict[str, dict] = {}
    extra = 0
    for oe in root.iter("operation"):
        if oe.get("typeId") != "LB":
            continue
        prog = oe.get("program") or ""
        if not prog.strip():
            continue
        h = hashlib.sha1(prog.encode("utf-8", "replace")).hexdigest()
        if h in seen:
            seen[h]["ops"] += 1
            continue
        if len(seen) >= C.MAX_PROGRAMS:
            extra += 1
            continue
        seen[h] = {"name": (oe.get("typeName") or oe.get("name") or oe.get("code") or _("lb.op_name"))[:100], "program": prog, "ops": 1}
    if not seen:
        raise GLError(_("lbx.e_no_lb"))
    return list(seen.values()), extra
