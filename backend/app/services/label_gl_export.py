"""W4 ning JSON shabloni → `<program>` XML (W9 · LB-D eksport): fayl mijoz tizimlarida ham ishlatilishi uchun.

Faqat `label_gl_import.py` o'qiydigan tuzilma yoziladi (boshqa manba yo'q). Moslik jadvali:

  bizning element            XML                              izoh
  text                       text                             maxw → w, align+maxw → x ni qaytarish; rotate — yo'q (ogohlantirish)
  rect                       rect                             stroke/fill; radius — yo'q (ogohlantirish)
  line                       rect (h=0 yoki w=0)              qiyshiq chiziq — o'tkazib yuboriladi (ogohlantirish)
  polyline (W15)             rect (h=0 yoki w=0) segmentlari  faqat gorizontal/vertikal segmentli; qiyshiq segment bo'lsa — butunlay
                                                              o'tkazib yuboriladi (`polyline`); to'ldirish yozilmaydi (`poly_fill`)
  arc, ellipse (W15)         —                                o'tkazib yuboriladi (`arc`, `ellipse`): formatda mos teg yo'q
  image                      image                            imgdata = src
  barcode qr                 qrcode                           rotate — yo'q (ogohlantirish)
  barcode code128            —                                o'tkazib yuboriladi (ogohlantirish): formatda 1D shtrixkod tegi yo'q
  part                       part                             standart detal chizmasi atributlari
  edges                      part                             eng yaqin element (ogohlantirish)
  group (rotate = 0)         xy + ichidagilar                 rotate ≠ 0 — o'tkazib yuboriladi (ogohlantirish)
  if / else                  if + else (aka-uka)
  var (element)              var                              tur — avtomatik aniqlanadi
  params                     par                              title → comment
  vars                       var                              `type` bo'lsa shu, bo'lmasa avtomatik
  ishlatilgan standart nom   par (e'lon)                      sinov qiymati — neytral (bo'sh/0/false)

Ifodalardagi o'zgaruvchi nomlari fayl formatidagi nomga qaytariladi (`label.width` → `dx`, `part.thickness` → `thick` …);
faqat bizda bor nomlar — ogohlantirish. Natija bir qatorli (`<?xml …?><program …>`), UTF-8.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree as ET

from ..i18n import _
from . import expr, label_tpl
from . import label_gl_common as C
from .label_gl_common import GLError, Warnings

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
_CMP = {"<", ">", "<=", ">=", "=", "==", "<>", "!="}
_STR_FUNCS = {"format", "ns", "left", "right", "mid", "lspace", "rspace", "rept", "trim", "ltrim", "rtrim", "ucase", "lcase",
              "replace", "now", "translit", "uuid", "dectohex", "dectooct", "dectobin", "roman"}
_BOOL_FUNCS = {"empty", "startswith", "endswith", "boolean"}
_DEFAULT = {"string": "", "integer": "0", "double": "0", "boolean": "false"}


@dataclass
class ExportResult:
    xml: str
    warnings: list[dict] = field(default_factory=list)


def _clean(v) -> str:
    return _CTRL.sub("", str(v))


def _color_out(c) -> str:
    n = C.norm_color(c) if isinstance(c, str) else None
    if n is None:
        return "#000000"
    return n.upper() if n.startswith("#") else n


def _flag_lit(v) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "false"):
        return v.strip().lower() == "true"
    if v is None:
        return False
    return None


class _Exp:
    def __init__(self, tpl: dict, layout: Optional[dict]):
        from .label_vars import VAR_NAMES, VAR_TYPES, ALIASES
        self.tpl = tpl
        self.w = Warnings("lbx.x_")
        self.used: set[str] = set()
        self.var_names, self.var_types, self.aliases = VAR_NAMES, VAR_TYPES, ALIASES
        self.c2g = C.canon_to_gl()
        self.layout = layout or {}
        self.declared = {p["name"] for p in tpl["params"]} | {v["name"] for v in tpl["vars"]}
        self.declared |= {el["name"] for _p, el in label_tpl.walk(tpl["elements"]) if el.get("t") == "var" and el.get("name")}

    # — ifoda —
    def fx(self, v) -> str:
        """Son yoki ifoda → atribut matni (o'zgaruvchi nomlari fayl formatiga qaytariladi)."""
        if isinstance(v, bool):
            return "true" if v else "false"
        if C.is_num(v):
            return C.fmt_num(v)
        s = str(v).strip()

        def fn(tok: str) -> str:
            if tok in self.declared:
                return tok
            g = self.c2g.get(tok, tok)
            if g in C.GL_STD:
                self.used.add(g)
            elif g in ("dx", "dy"):
                pass
            elif tok in self.var_names and not tok.startswith("user."):
                self.w.add("var", tok[:40])
            return g
        return C.rewrite_idents(s, fn)

    def flag(self, v, key: str) -> str:
        b = _flag_lit(v)
        if b is None:
            self.w.add("skipped", f"{key} (expr)")
            return "false"
        return "true" if b else "false"

    # — tur aniqlash (var uchun) —
    def _ident_type(self, tok: str) -> Optional[str]:
        g = self.c2g.get(tok, tok)
        if g in C.GL_STD:
            return C.GL_STD[g]
        src = self.aliases.get(tok, tok)
        return self.var_types.get(src)

    def infer_type(self, e) -> str:
        if isinstance(e, bool):
            return "boolean"
        if C.is_num(e):
            return "double"
        try:
            toks = expr._tokenize(str(e).strip())
        except ValueError:
            return "string"
        return self._infer_tokens(toks)

    def _infer_tokens(self, toks: list) -> str:
        if not toks:
            return "double"
        depth = 0
        has_str = False
        for kind, val in toks:
            if kind == "op" and val == "(":
                depth += 1
            elif kind == "op" and val == ")":
                depth -= 1
            elif depth == 0:
                if (kind == "op" and val in _CMP) or (kind == "kw" and val in ("not", "and", "or", "xor")):
                    return "boolean"
                if kind == "str":
                    has_str = True
        if has_str:
            return "string"
        k0, v0 = toks[0]
        if (k0 in ("id", "kw")) and len(toks) > 1 and toks[1] == ("op", "("):
            name = str(v0).lower()
            if name in _STR_FUNCS:
                return "string"
            if name in _BOOL_FUNCS:
                return "boolean"
            if name == "if":                                       # if(shart, a, b): a ning turi
                args, cur, d = [], [], 0
                for t in toks[2:]:
                    if t == ("op", "(") :
                        d += 1
                    elif t == ("op", ")"):
                        if d == 0:
                            break
                        d -= 1
                    if t == ("op", ",") and d == 0:
                        args.append(cur)
                        cur = []
                    else:
                        cur.append(t)
                args.append(cur)
                if len(args) >= 2:
                    return self._infer_tokens(args[1])
        if len(toks) == 1 and k0 == "id":
            return self._ident_type(str(v0)) or "double"
        if k0 == "kw" and v0 in ("true", "false"):
            return "boolean"
        return "double"

    # — XML qurish —
    @staticmethod
    def sub(parent: ET.Element, tag: str, **attrs) -> ET.Element:
        return ET.SubElement(parent, tag, {k.replace("_", ".") if k.startswith(("size_", "edgeband_")) else k: _clean(v)
                                           for k, v in attrs.items() if v is not None})

    def _comment(self, el: dict) -> dict:
        c = el.get("comment")
        return {"comment": c} if isinstance(c, str) and c else {}

    def elements(self, els: list, parent: ET.Element, path: str = "") -> None:
        for i, el in enumerate(els, 1):
            p = f"{path}{i}"
            t = el.get("t")
            rest_follow = i < len(els)
            if t == "text":
                self._text(el, parent, p)
            elif t == "rect":
                self._rect(el, parent, p)
            elif t == "line":
                self._line(el, parent, p)
            elif t in ("polyline", "arc", "ellipse", "bezier"):
                self._shape(el, parent, p)
            elif t == "image":
                self.sub(parent, "image", enable="true", x=self.fx(el.get("x", 0)), y=self.fx(el.get("y", 0)),
                         w=self.fx(el.get("w", 0)), h=self.fx(el.get("h", 0)), imgdata=el.get("src", ""), ratio="true", expr="",
                         **self._comment(el))
            elif t == "barcode":
                self._barcode(el, parent, p)
            elif t in ("part", "edges"):
                if t == "edges":
                    self.w.add("edges", p)
                self._part(el, parent)
            elif t == "group":
                self._group(el, parent, p, rest_follow)
            elif t == "if":
                self._if(el, parent, p)
            elif t == "var":
                v = {"name": el["name"], "expr": el.get("expr", "''")}
                self.sub(parent, "var", name=v["name"], type=self.var_type(v, p), expr=self.fx(v["expr"]), **self._comment(el))

    def var_type(self, v: dict, key: str) -> str:
        t = v.get("type")
        if t in ("double", "integer", "string", "boolean"):
            return t
        self.w.add("type")                                         # bitta umumiy ogohlantirish (soni bilan)
        return self.infer_type(v.get("expr", "''"))

    def _text(self, el: dict, parent: ET.Element, p: str) -> None:
        x = el.get("x", 0)
        maxw = el.get("maxw")
        align = str(el.get("align") or "left").lower()
        align = align if align in ("left", "center", "right") else "left"
        if maxw is not None and align in ("center", "right"):
            tail = C.half(maxw) if align == "center" else maxw
            back = C.unadd_tail(x, tail)
            x = back if back is not None else C.sub(x, tail)
        if el.get("rotate") not in (None, 0, 0.0, "0", ""):
            self.w.add("rotate", p)
        wrap = _flag_lit(el.get("wrap"))
        if wrap is None:
            self.flag(el.get("wrap"), "wrap")
            wrap = False
        rh = el.get("line_h", 3) if wrap else 3
        size = el.get("size", 3)
        a: dict = dict(enable="true", x=self.fx(x), y=self.fx(C.top_to_baseline(el.get("y", 0), size)))     # y — asosiy chiziq
        if maxw is not None:
            a["w"] = self.fx(maxw)
        font = str(el.get("font") or "")
        a.update(text=self.fx(el.get("text", "''")), fillColor=_color_out(el.get("color")),
                 fontName="Courier New" if font.lower() in ("mono", "monospace", "courier") else (font or "Arial"),
                 fontSize=self.fx(size), fontBold=self.flag(el.get("bold"), "bold"),
                 fontItalic=self.flag(el.get("italic"), "italic"), rowHeight=self.fx(rh),
                 ratio="true" if maxw is not None else "false", align=align, valign="top",
                 multiline="true" if wrap else "false", wordBreak="true" if wrap else "false")
        lines = el.get("lines")
        if wrap and C.is_num(lines) and C.is_num(rh) and lines < 20:
            a["h"] = C.fmt_num(round(lines * rh, 4))
        a.update(self._comment(el))
        self.sub(parent, "text", **a)

    def _stroke(self, el: dict) -> tuple[object, str]:
        st = el.get("stroke")
        if st is None:
            return 0, "#000000"
        if isinstance(st, dict):
            return st.get("w", 0.2), _color_out(st.get("color"))
        return st, "#000000"

    def _rect(self, el: dict, parent: ET.Element, p: str) -> None:
        sw, sc = self._stroke(el)
        fill = C.norm_color(el.get("fill")) if el.get("fill") not in (None, "", "none") else None
        if el.get("radius") not in (None, 0, 0.0, "0", ""):
            self.w.add("radius", p)
        self.sub(parent, "rect", enable="true", x=self.fx(el.get("x", 0)), y=self.fx(el.get("y", 0)), w=self.fx(el.get("w", 0)),
                 h=self.fx(el.get("h", 0)), strokeColor=sc, strokeWidth=self.fx(sw), strokeDash="0",
                 fillColor=_color_out(fill) if fill else "", fillHatch="8" if fill else "1", **self._comment(el))

    def _seg_kind(self, x1, y1, x2, y2) -> Optional[str]:
        """«h» (gorizontal), «v» (vertikal) yoki None (qiyshiq / nuqta) — formatda faqat birinchi ikkitasi bor."""
        if self.fx(y1) == self.fx(y2) and self.fx(x1) != self.fx(x2):
            return "h"
        if self.fx(x1) == self.fx(x2) and self.fx(y1) != self.fx(y2):
            return "v"
        return None

    def _write_seg(self, kind: str, x1, y1, x2, y2, sw, sc: str, parent: ET.Element, comment: dict) -> None:
        if kind == "h":
            w, h = C.unadd_head(x2, x1), 0
            if w is None:
                w = C.sub(x2, x1)
        else:
            h, w = C.unadd_head(y2, y1), 0
            if h is None:
                h = C.sub(y2, y1)
        self.sub(parent, "rect", enable="true", x=self.fx(x1), y=self.fx(y1), w=self.fx(w), h=self.fx(h), strokeColor=sc,
                 strokeWidth=self.fx(sw if sw else 0.2), strokeDash="0", fillColor="", fillHatch="1", **comment)

    def _line(self, el: dict, parent: ET.Element, p: str) -> None:
        x1, y1, x2, y2 = (el.get(k, 0) for k in ("x1", "y1", "x2", "y2"))
        sw, sc = self._stroke(el)
        kind = self._seg_kind(x1, y1, x2, y2)
        if kind is None:
            self.w.add("line", p)
            return
        self._write_seg(kind, x1, y1, x2, y2, sw, sc, parent, self._comment(el))

    def _shape(self, el: dict, parent: ET.Element, p: str) -> None:
        """W15: poliliniya / yoy / ellips — formatda mos teg yo'q. Faqat gorizontal-vertikal segmentli poliliniya (to'ldirishsiz
        qismi) chiziqlar bilan yoziladi; qolganlari o'tkazib yuboriladi (ogohlantirish)."""
        t = el.get("t")
        if t != "polyline":
            self.w.add(str(t), p)
            return
        pts = [pt for pt in (el.get("points") or []) if isinstance(pt, list) and len(pt) == 2]
        segs = list(zip(pts, pts[1:]))
        if _flag_lit(el.get("closed")) and len(pts) > 2:
            segs.append((pts[-1], pts[0]))
        kinds = [self._seg_kind(a[0], a[1], b[0], b[1]) for a, b in segs]
        if not segs or None in kinds:
            self.w.add("polyline", p)
            return
        if el.get("fill") not in (None, "", "none"):
            self.w.add("poly_fill", p)
        sw, sc = self._stroke(el)
        for (a, b), k in zip(segs, kinds):
            self._write_seg(k, a[0], a[1], b[0], b[1], sw, sc, parent, {})

    def _barcode(self, el: dict, parent: ET.Element, p: str) -> None:
        kind = str(el.get("kind", "qr")).lower()
        if kind != "qr":
            self.w.add("barcode", p)
            return
        if el.get("rotate") not in (None, 0, 0.0, "0", ""):
            self.w.add("rotate", p)
        self.sub(parent, "qrcode", enable="true", x=self.fx(el.get("x", 0)), y=self.fx(el.get("y", 0)),
                 sz=self.fx(el.get("size", 15)), text=self.fx(el.get("data", "''")), fillColor=_color_out(el.get("color")),
                 **self._comment(el))

    def _part(self, el: dict, parent: ET.Element) -> None:
        a: dict = dict(enable="true", x=self.fx(el.get("x", 0)), y=self.fx(el.get("y", 0)), w=self.fx(el.get("w", 0)),
                       h=self.fx(el.get("h", 0)), optimalTurn="true", size="true", size_fontBold="false", size_fontItalic="false",
                       size_top="false", size_left="false", edgeband="true", edgeband_fontBold="true", edgeband_fontItalic="false")
        for s in "tblr":                                           # chiziq qalinligi va yozuv — standart ifodalar (nomlar standart)
            a[f"e{s}t"] = f"double(e{s}t)/2"
        for s in "tblr":
            a[f"e{s}d"] = f"if(empty(e{s}s),'','('+e{s}s+') '+format('0.#',double(e{s}t)))"
            self.used.update({f"e{s}s", f"e{s}t"})
        a.update(length="format('00.#',double(length))", width="format('00.#',double(width))", size_fontName="Arial",
                 edgeband_fontName="Arial", size_fontSize="2", edgeband_fontSize="2", edgeband_offset="1")
        self.used.update({"length", "width"})
        a.update(self._comment(el))
        self.sub(parent, "part", **a)

    def _group(self, el: dict, parent: ET.Element, p: str, rest_follow: bool) -> None:
        rot = el.get("rotate")
        if rot not in (None, 0, 0.0, "0", ""):
            self.w.add("group_rot", p)
            return
        o = el.get("origin") or [0, 0]
        zero = all(C.is_num(v) and v == 0 for v in o)
        if not zero:
            self.sub(parent, "xy", enable="true", x=self.fx(o[0]), y=self.fx(o[1]))
            if rest_follow:
                self.w.add("xy_scope", p)
        self.elements(el.get("elements") or [], parent, p + ".elements.")

    def _if(self, el: dict, parent: ET.Element, p: str) -> None:
        e = self.sub(parent, "if", condition=self.fx(el.get("cond", "false")), expand="true", **self._comment(el))
        self.elements(el.get("then") or [], e, p + ".then.")
        other = el.get("else") or []
        if other:
            e2 = self.sub(parent, "else", expand="true")
            self.elements(other, e2, p + ".else.")

    # — butun dastur —
    def run(self) -> ExportResult:
        tpl, lay = self.tpl, {**(self.tpl.get("layout") or {}), **self.layout}
        W = lay.get("width_mm", tpl["size"]["w"])
        H = lay.get("height_mm", tpl["size"]["h"])
        margin = lay["margin_mm"] if "margin_mm" in lay else 6.0                  # None — «Поля страницы» o'chiq
        root = ET.Element("program", {
            "columns": str(int(lay.get("columns") or 3)), "dx": C.fmt_num(round(float(W), 4)), "dy": C.fmt_num(round(float(H), 4)),
            "gap": C.fmt_num(round(float(lay.get("gap_mm", 2) or 0), 4)),
            "margin": "false" if margin is None else "true",
            "printMode": "0" if lay.get("mode", "sheet") == "sheet" else "1", "rows": str(int(lay.get("rows") or 0))})
        for p in tpl["params"]:
            t = p.get("type", "string")
            d = p.get("default")
            if t == "boolean":
                ex = "true" if (d if isinstance(d, bool) else str(d).strip().lower() in ("1", "true")) else "false"
            elif t in ("double", "integer") and C.is_num(d):
                ex = C.fmt_num(d)
            else:
                ex = "" if d is None else str(d)
            self.sub(root, "par", name=p["name"], type=t, expr=ex, **({"comment": p["title"]} if p.get("title") else {}))
        n_pars = len(list(root))
        for v in tpl["vars"]:
            self.sub(root, "var", name=v["name"], type=self.var_type(v, v["name"]), expr=self.fx(v.get("expr", "''")),
                     **self._comment(v))
        self.elements(tpl["elements"], root)
        decl = [(n, C.GL_STD[n]) for n in sorted(self.used) if n not in self.declared]
        for k, (n, t) in enumerate(decl):                          # ishlatilgan standart nomlar e'loni (sinov qiymati neytral)
            e = ET.Element("par", {"name": n, "type": t, "expr": _DEFAULT[t]})
            root.insert(n_pars + k, e)
        xml = '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(root, encoding="unicode")
        return ExportResult(xml, self.w.to_list())


def export_program(template: dict, layout: Optional[dict] = None) -> ExportResult:
    """Shablon (JSON) → `<program>` XML matni + ogohlantirishlar. `layout` — LBParams maydonlari (mode, columns, rows, gap_mm,
    margin_mm, width_mm, height_mm): berilsa — shablon ichidagi `layout` o'rniga. Xato — GLError."""
    try:
        tpl = label_tpl.normalize_template(template)
    except label_tpl.TemplateError as e:
        raise GLError(_("lbx.e_tpl", e=str(e))) from e
    return _Exp(tpl, layout).run()
