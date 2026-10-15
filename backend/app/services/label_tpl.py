"""LB shablon dvigateli: JSON shablon → har etiketka uchun SVG (mm koordinatalar; chap-yuqori boshlang'ich nuqta, X o'ngga, Y pastga).

Shablon (o'zimizniki, inventar 03 §4.4):
    {"v": 1, "name": "...", "size": {"w": 58, "h": 40},
     "params": [{"name": "margin", "type": "double", "default": 2, "title": "Поля"}],
     "vars":   [{"name": "code", "expr": "'MXK:'+project.number+':'+part.id"}],
     "elements": [ {"t": "text", "x": "2", "y": "3", "text": "left(project.name,24)", "size": 2.6}, ... ]}

Elementlar: text, rect, line, image, barcode (qr | code128), part (detal chizmasi), edges (kromka sxemasi), group (siljish +
burish), if (shart), var (hisoblangan o'zgaruvchi); W15 dan: polyline (nuqtalar ro'yxati), arc (yoy), ellipse (ellips/aylana).
Har geometrik va mazmun maydoni — **ifoda** (services/expr.py; oddiy son ham ifoda; matn literali `'...'` bilan yoziladi).
Ifoda xatosi jim 0 bermaydi: xato yig'iladi (chop oldidan muharrirda ko'rinadi), etiketkada esa qizil «#ERR» belgisi chiqadi.

W15 qo'shimchalari (ma'lumot modeli kengaydi, eski shablonlar o'zgarishsiz ochiladi):
  polyline  {points: [[x, y], …] (2…200 nuqta), closed (ifoda/bool), stroke, fill}
  arc       {cx, cy, r, a1, a2 (gradus; 0 — o'ngga, musbat yo'nalish soat strelkasi bo'yicha: Y pastga), stroke, fill (sektor)}
  ellipse   {cx, cy, rx, ry, stroke, fill}
`Renderer(mark=True)` (vizual redaktor): har element `<g data-p="<yo'l>" data-t="<tur>">…</g>` ichiga o'raladi.

Xavfsizlik: matn escape qilinadi; rasm faqat data:image/png|jpeg (≤ 200 KB, SVG rad etiladi); shtrixkod/QR faqat SVG yo'l;
rang — safe_color; o'lchamlar chegaralangan; ≤ 500 element, ≤ 8 ichma-ich daraja, har ifoda ≤ 1000 belgi.
"""
from __future__ import annotations

import json
import math
import random
import re
from html import escape
from typing import Any, Callable, Optional

from ..i18n import _
from . import expr
from .barcode import code128_group, qr_cells, qr_group
from .labels import edge_icon_parts
from .render import safe_color

MAX_ELEMENTS = 500
MAX_DEPTH = 8
MAX_PARAMS = 50
MAX_VARS = 100
MAX_JSON = 1_000_000
MAX_IMAGE_B64 = 270_000          # ≈ 200 KB ikkilik
MAX_TEXT = 1000
MAX_POINTS = 200                 # polyline: nuqtalar soni
COORD = 5000.0
SIZE_MIN, SIZE_MAX = 5.0, 500.0

TYPES = ("text", "rect", "line", "image", "barcode", "part", "edges", "group", "if", "var", "polyline", "arc", "ellipse")
_NAME_RE = re.compile(r"^[^\W\d]\w*(?:\.[^\W\d]\w*)*$", re.UNICODE)
_IMG_RE = re.compile(r"^data:image/(png|jpeg|jpg);base64,[A-Za-z0-9+/=]+$")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\ud800-\udfff￾￿]")      # \t va \n qoladi, boshqa boshqaruv/XML-yaroqsiz belgilar (yakka surrogat ham) — bo'sh joy

# element xossalari: num — son yoki ifoda; expr — ifoda (matn/ma'lumot); flag — bool yoki ifoda; lit — literal matn
SPEC: dict[str, dict] = {
    "text": dict(num=("x", "y", "size", "maxw", "lines", "rotate", "line_h"), expr=("text",), flag=("bold", "wrap", "italic"),
                 lit=("align", "font", "color")),
    "rect": dict(num=("x", "y", "w", "h", "radius"), lit=("fill",), stroke=True),
    "line": dict(num=("x1", "y1", "x2", "y2"), stroke=True),
    "image": dict(num=("x", "y", "w", "h"), lit=("src",)),
    "barcode": dict(num=("x", "y", "size", "w", "h", "rotate", "quiet"), expr=("data",), flag=("caption",),
                    lit=("kind", "ec", "color")),
    "part": dict(num=("x", "y", "w", "h")),
    "edges": dict(num=("x", "y", "w", "h")),
    "group": dict(num=("rotate",), origin=True, children=("elements",)),
    "if": dict(expr=("cond",), children=("then", "else")),
    "var": dict(expr=("expr",), lit=("name",)),
    # W15: chizma elementlari (LB-D)
    "polyline": dict(flag=("closed",), lit=("fill",), stroke=True, points=True),
    "arc": dict(num=("cx", "cy", "r", "a1", "a2"), lit=("fill",), stroke=True),
    "ellipse": dict(num=("cx", "cy", "rx", "ry"), lit=("fill",), stroke=True),
}
_COMMON_KEYS = {"t", "comment", "id"}
PARAM_TYPES = ("double", "integer", "string", "boolean")


class TemplateError(ValueError):
    """Shablon tuzilmasi noto'g'ri (saqlab/chop qilib bo'lmaydi)."""


class _Fail(Exception):
    """Element hisoblanmadi (xato `errors` ga yozilgan)."""


# ───────────────────────── Tuzilma tekshiruvi ─────────────────────────
def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _check_expr_value(v, path: str, field: str) -> None:
    if _is_num(v) or isinstance(v, bool):
        return
    if isinstance(v, str):
        if len(v) > expr.MAX_SRC:
            raise TemplateError(_("lb.t_expr_long", path=path, f=field, n=expr.MAX_SRC))
        return
    raise TemplateError(_("lb.t_field_type", path=path, f=field))


def _normalize_elements(els, path: str, depth: int, counter: list) -> None:
    if not isinstance(els, list):
        raise TemplateError(_("lb.t_field_type", path=path, f="elements"))
    if depth > MAX_DEPTH:
        raise TemplateError(_("lb.t_too_deep", n=MAX_DEPTH))
    for i, el in enumerate(els, 1):
        p = f"{path}{i}"
        if not isinstance(el, dict):
            raise TemplateError(_("lb.t_field_type", path=p, f="t"))
        counter[0] += 1
        if counter[0] > MAX_ELEMENTS:
            raise TemplateError(_("lb.t_too_many", n=MAX_ELEMENTS))
        t = el.get("t")
        if t not in SPEC:
            raise TemplateError(_("lb.t_unknown_type", path=p, t=str(t)[:30]))
        spec = SPEC[t]
        for f in spec.get("num", ()):
            if f in el and el[f] is not None:
                _check_expr_value(el[f], p, f)
        for f in spec.get("expr", ()):
            if f in el and el[f] is not None:
                _check_expr_value(el[f], p, f)
        for f in spec.get("flag", ()):
            if f in el and el[f] is not None:
                _check_expr_value(el[f], p, f)
        for f in spec.get("lit", ()):
            if f in el and el[f] is not None and not isinstance(el[f], str):
                raise TemplateError(_("lb.t_field_type", path=p, f=f))
        if spec.get("stroke") and el.get("stroke") is not None:
            st = el["stroke"]
            if isinstance(st, dict):
                if "w" in st and st["w"] is not None:
                    _check_expr_value(st["w"], p, "stroke.w")
                if "color" in st and st["color"] is not None and not isinstance(st["color"], str):
                    raise TemplateError(_("lb.t_field_type", path=p, f="stroke.color"))
            else:
                _check_expr_value(st, p, "stroke")
        if spec.get("origin") and el.get("origin") is not None:
            o = el["origin"]
            if not (isinstance(o, list) and len(o) == 2):
                raise TemplateError(_("lb.t_field_type", path=p, f="origin"))
            for v in o:
                _check_expr_value(v, p, "origin")
        if spec.get("points"):
            pts = el.get("points")
            if not (isinstance(pts, list) and 2 <= len(pts) <= MAX_POINTS):
                raise TemplateError(_("lb.t_points", path=p, n=MAX_POINTS))
            for pt in pts:
                if not (isinstance(pt, list) and len(pt) == 2):
                    raise TemplateError(_("lb.t_points", path=p, n=MAX_POINTS))
                for v in pt:
                    _check_expr_value(v, p, "points")
        if t == "image":
            src = el.get("src")
            if not isinstance(src, str) or len(src) > MAX_IMAGE_B64 or not _IMG_RE.match(src):
                raise TemplateError(_("lb.t_image", path=p, n=200))
        if t == "var":
            nm = el.get("name")
            if not isinstance(nm, str) or not _NAME_RE.match(nm) or len(nm) > 60:
                raise TemplateError(_("lb.t_var", path=p))
        if t == "barcode":
            kind = str(el.get("kind", "qr")).lower()
            if kind not in ("qr", "code128"):
                raise TemplateError(_("lb.t_bc_kind", path=p, k=kind[:20]))
        for ch in spec.get("children", ()):
            if ch in el and el[ch] is not None:
                _normalize_elements(el[ch], f"{p}.{ch}.", depth + 1, counter)


def normalize_template(data: Any) -> dict:
    """Shablon tuzilmasini tekshiradi va tozalangan nusxasini qaytaradi (xato — TemplateError).
    Ifoda sintaksisi bu yerda tekshirilmaydi (`check_template` — muharrirda xato ro'yxati)."""
    if not isinstance(data, dict):
        raise TemplateError(_("lb.t_not_object"))
    try:
        txt = json.dumps(data, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as e:
        raise TemplateError(_("lb.t_not_object")) from e
    if len(txt) > MAX_JSON:
        raise TemplateError(_("lb.t_too_big", n=MAX_JSON // 1000))
    tpl = json.loads(txt)
    tpl["v"] = 1
    name = tpl.get("name", "")
    tpl["name"] = str(name)[:100] if name is not None else ""
    size = tpl.get("size")
    if size is None:
        size = {"w": 58, "h": 40}
    if not (isinstance(size, dict) and _is_num(size.get("w")) and _is_num(size.get("h"))
            and SIZE_MIN <= size["w"] <= SIZE_MAX and SIZE_MIN <= size["h"] <= SIZE_MAX):
        w, h = (size.get("w"), size.get("h")) if isinstance(size, dict) else ("?", "?")
        raise TemplateError(_("lb.t_size", w=w, h=h))
    tpl["size"] = {"w": size["w"], "h": size["h"]}
    params = tpl.get("params", [])
    if not isinstance(params, list) or len(params) > MAX_PARAMS:
        raise TemplateError(_("lb.t_params", n=MAX_PARAMS))
    for i, pr in enumerate(params, 1):
        if not (isinstance(pr, dict) and isinstance(pr.get("name"), str) and _NAME_RE.match(pr["name"])
                and pr.get("type", "string") in PARAM_TYPES):
            raise TemplateError(_("lb.t_param", path=f"params[{i}]"))
        pr.setdefault("type", "string")
        pr["title"] = str(pr.get("title", ""))[:100]
    tpl["params"] = params
    vars_ = tpl.get("vars", [])
    if not isinstance(vars_, list) or len(vars_) > MAX_VARS:
        raise TemplateError(_("lb.t_vars", n=MAX_VARS))
    for i, v in enumerate(vars_, 1):
        if not (isinstance(v, dict) and isinstance(v.get("name"), str) and _NAME_RE.match(v["name"])):
            raise TemplateError(_("lb.t_var", path=f"vars[{i}]"))
        _check_expr_value(v.get("expr", "''"), f"vars[{i}]", "expr")
    tpl["vars"] = vars_
    els = tpl.get("elements", [])
    _normalize_elements(els, "", 1, [0])
    tpl["elements"] = els
    return tpl


def walk(els: list, path: str = ""):
    """Hamma elementlar (ichma-ich ham): (yo'l, element)."""
    for i, el in enumerate(els, 1):
        p = f"{path}{i}"
        yield p, el
        for ch in SPEC.get(el.get("t"), {}).get("children", ()):
            if isinstance(el.get(ch), list):
                yield from walk(el[ch], f"{p}.{ch}.")


# ───────────────────────── Matn o'lchami ─────────────────────────
def text_width(s: str, size: float, bold: bool = False) -> float:
    """Taxminiy matn eni (mm): Arial o'rtacha belgi kengliklari bo'yicha. Shrift o'lchamlari brauzerga bog'liq bo'lgani uchun
    sig'dirish (maxw) shu baho bilan hisoblanadi."""
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.28
        elif ch.isdigit():
            w += 0.556
        elif ch in "il.,:;'|!jI":
            w += 0.27
        elif ch in "mwMW":
            w += 0.85
        elif ch.isupper():
            w += 0.70
        else:
            w += 0.56
    return w * size * (1.10 if bold else 1.0)


def _fit_text(s: str, size: float, maxw: float, bold: bool) -> tuple[str, float]:
    """Bir qatorli matnni maxw ga sig'dirish: avval shrift kichraytiriladi (≥ 60 %), keyin «…» bilan kesiladi."""
    w = text_width(s, size, bold)
    if w <= maxw or maxw <= 0:
        return s, size
    scale = maxw / w
    if scale >= 0.6:
        return s, size * scale
    size *= 0.6
    while len(s) > 1 and text_width(s + "…", size, bold) > maxw:
        s = s[:-1]
    return s + "…", size


def _wrap_text(s: str, size: float, maxw: float, bold: bool, max_lines: int) -> list[str]:
    lines: list[str] = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word) if cur else word
            if cur and text_width(t, size, bold) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = t
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while len(last) > 1 and text_width(last + "…", size, bold) > maxw:
            last = last[:-1]
        lines[-1] = last + "…"
    return lines


def _n(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def label_text(v) -> str:
    """Ifoda natijasi → chop matni (son: ortiqcha «.0» siz, 2 xona; mantiqiy: true/false; null: bo'sh)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        r = round(v, 2)
        return str(int(r)) if r == int(r) else f"{r:g}"
    s = v if isinstance(v, str) else str(v)
    return _CTRL_RE.sub(" ", s)[:MAX_TEXT]


_NUM_LIT = re.compile(r"^-?\d+(?:\.\d+)?$")
_STR_LIT = re.compile(r"^'([^'\\]*)'$")
_VAR_RE = re.compile(r"^[^\W\d]\w*(?:\.[^\W\d]\w*)*$", re.UNICODE)


# ───────────────────────── Render ─────────────────────────
class Renderer:
    """Bir chop (ko'p etiketka) uchun: shablon bir marta tayyorlanadi, har etiketka `render(env)`.
    `errors` / `warnings` — takrorlanmas (yo'l, maydon, matn) bo'yicha yig'iladi (soni va birinchi etiketka raqami bilan)."""

    def __init__(self, tpl: dict, *, width_mm: float, height_mm: float, params: Optional[dict] = None, lang: str = "ru",
                 fast_qr: bool = False, clock=None, mark: bool = False):
        self.tpl = tpl
        self.W, self.H = float(width_mm), float(height_mm)
        self.lang = lang if lang in ("ru", "uz") else "ru"
        self.fast_qr = fast_qr
        self.clock = clock
        self.mark = mark                         # vizual redaktor: har element `<g data-p="yo'l">` ichida
        self.rng = random.Random()               # bitta manba (har ifodada yangisini yaratish ≈ 35 % vaqt oladi)
        self.errors: dict[tuple, dict] = {}
        self.warnings: dict[tuple, dict] = {}
        self.label_no = 0
        self._fast: dict[str, tuple] = {}
        self._ph = 0
        self.values: dict = {}
        params = params or {}
        for p in tpl.get("params", []):
            self.values[p["name"]] = self._coerce(p.get("type", "string"), params.get(p["name"], p.get("default")))
        # qator ma'lumotiga bog'liq bo'lmagan o'zgaruvchilar (faqat o'lcham/parametrlar) bir marta hisoblanadi
        static_names = {"label.width", "label.height", "label.lang", *self.values}
        self._static: list[dict] = []
        self._dynamic: list[dict] = []
        for v in tpl.get("vars", []):
            if self._is_static(v.get("expr", "''"), static_names):
                static_names.add(v["name"])
                self._static.append(v)
            else:
                self._dynamic.append(v)
        self._static_vals: Optional[dict] = None
        self._head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(self.W)} {_n(self.H)}" '
                      f'font-family="Arial, Helvetica, sans-serif">')
        self._handlers: dict[str, Callable] = {
            "text": self._text, "rect": self._rect, "line": self._line, "image": self._image, "barcode": self._barcode,
            "part": self._part, "edges": self._edges, "group": self._group, "if": self._if, "var": self._var,
            "polyline": self._polyline, "arc": self._arc, "ellipse": self._ellipse,
        }

    @staticmethod
    def _is_static(src, names: set) -> bool:
        """Ifoda faqat `names` dagi o'zgaruvchilarga (va konstantalarga) tayansa va tasodifiy/vaqt funksiyasi bo'lmasa — True."""
        if not isinstance(src, str):
            return True
        try:
            toks = expr._tokenize(src.strip())
        except ValueError:
            return False
        for i, (kind, val) in enumerate(toks):
            if kind != "id":
                continue
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            if nxt == ("op", "("):                                  # funksiya chaqiruvi
                if val.lower() in expr._IMPURE:
                    return False
            elif val not in names and val.lower() not in expr._CONST:
                return False
        return True

    @staticmethod
    def _coerce(tp: str, v):
        try:
            if tp == "double":
                return float(v) if v is not None and v != "" else 0.0
            if tp == "integer":
                return int(float(v)) if v is not None and v != "" else 0
            if tp == "boolean":
                return v if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes", "да")
        except (TypeError, ValueError):
            return {"double": 0.0, "integer": 0, "boolean": False}.get(tp, "")
        return "" if v is None else str(v)

    # — xato / ogohlantirish —
    def _record(self, bucket: dict, path: str, field: str, src, msg: str) -> None:
        key = (path, field, msg)
        d = bucket.get(key)
        if d is not None:
            d["count"] += 1
        elif len(bucket) < 100:
            bucket[key] = {"path": path, "field": field, "expr": str(src)[:120], "message": msg, "label": self.label_no, "count": 1}

    def error(self, path: str, field: str, src, msg: str) -> None:
        self._record(self.errors, path, field, src, msg)

    def warn(self, path: str, field: str, src, msg: str) -> None:
        self._record(self.warnings, path, field, src, msg)

    # — ifoda —
    def _eval(self, src, env: dict, path: str, field: str):
        """Ifodani hisoblaydi; xato — yozib `_Fail`."""
        if not isinstance(src, str):
            return src
        c = self._fast.get(src)
        if c is None:
            s = src.strip()
            if _NUM_LIT.match(s):
                c = ("c", float(s) if "." in s or abs(int(s)) > expr.INT_MAX else int(s))
            else:
                m = _STR_LIT.match(s)
                if m:
                    c = ("c", m.group(1))
                elif _VAR_RE.match(s):
                    c = ("v", s)
                else:
                    c = ("e", s)
            self._fast[src] = c
        kind = c[0]
        if kind == "c":
            return c[1]
        if kind == "v" and c[1] in env:
            return env[c[1]]
        try:
            return expr.evaluate(c[1], env, lang=self.lang, clock=self.clock, rng=self.rng)
        except ValueError as e:
            self.error(path, field, src, str(e))
            raise _Fail() from None

    def _num(self, el: dict, key: str, env: dict, path: str, default: Optional[float] = None, lo: float = -COORD,
             hi: float = COORD) -> float:
        if el.get(key) is None:
            if default is None:
                self.error(path, key, "", _("lb.e_missing", f=key))
                raise _Fail()
            return default
        v = self._eval(el[key], env, path, key)
        if isinstance(v, bool):
            v = 1.0 if v else 0.0
        if not isinstance(v, (int, float)):
            self.error(path, key, el[key], _("lb.e_not_number"))
            raise _Fail()
        return min(max(float(v), lo), hi)

    def _text_val(self, el: dict, key: str, env: dict, path: str, default: str = "") -> str:
        if el.get(key) is None:
            return default
        return label_text(self._eval(el[key], env, path, key))

    def _flag(self, el: dict, key: str, env: dict, path: str, default: bool = False) -> bool:
        v = el.get(key)
        if v is None:
            return default
        v = self._eval(v, env, path, key)
        if isinstance(v, str):
            return v.strip().lower() in ("true", "t", "1")
        return bool(v)

    def _stroke(self, el: dict, env: dict, path: str, default_w: float = 0.2) -> tuple[float, str]:
        st = el.get("stroke")
        if st is None:
            return default_w, "#000"
        if isinstance(st, dict):
            w = self._num(st, "w", env, path, default_w, 0.0, 20.0) if "w" in st else default_w
            return w, safe_color(st.get("color"), "#000")
        return self._num(el, "stroke", env, path, default_w, 0.0, 20.0), "#000"

    # — render —
    def render(self, env: dict) -> str:
        """Bitta etiketka SVG si. `env` o'zgartiriladi (parametrlar va `vars` qo'shiladi)."""
        out = self.render_parts(env)
        return self._head + "".join(out) + "</svg>"

    def render_parts(self, env: dict) -> list[str]:
        """Bitta etiketka: o'zgaruvchilarni tayyorlab, elementlarni `handlers` orqali `out` ro'yxatiga yozadi (SVG bo'laklari;
        boshqa chiqish — ZPL — uchun `handlers` almashtiriladi: services/label_zpl.py)."""
        self.label_no += 1
        self._ph = 0
        env["label.width"], env["label.height"] = self.W, self.H          # shablon o'lchami — chop o'lchami bilan har doim bir xil
        env.update(self.values)
        if self._static_vals is None:                       # birinchi etiketkada (xato bo'lsa — bir marta yoziladi)
            vals: dict = {}
            for v in self._static:
                try:
                    vals[v["name"]] = env[v["name"]] = self._eval(v.get("expr", "''"), env, f"vars.{v['name']}", "expr")
                except _Fail:
                    vals[v["name"]] = env[v["name"]] = None
            self._static_vals = vals
        else:
            env.update(self._static_vals)
        for v in self._dynamic:
            try:
                env[v["name"]] = self._eval(v.get("expr", "''"), env, f"vars.{v['name']}", "expr")
            except _Fail:
                env[v["name"]] = None
        out: list[str] = []
        self._elements(self.tpl.get("elements", []), env, out, "")
        return out

    def _elements(self, els: list, env: dict, out: list, path: str) -> None:
        handlers = self._handlers
        mark = self.mark
        for i, el in enumerate(els, 1):
            p = f"{path}{i}"
            if mark:
                out.append(f'<g data-p="{escape(p)}" data-t="{escape(str(el["t"]))}">')
            try:
                handlers[el["t"]](el, env, out, p)
            except _Fail:
                self._placeholder(out, p)
            if mark:
                out.append("</g>")

    def _placeholder(self, out: list, p: str) -> None:
        out.append(f'<text x="1" y="{_n(3 + 2.4 * self._ph)}" font-size="2.2" font-weight="bold" fill="#c00">#ERR {escape(p)}</text>')
        self._ph += 1

    # — elementlar —
    def text_model(self, el, env, p) -> dict:
        """Matn elementini hisoblaydi (ifodalar, sig'dirish, qatorlarga bo'lish): SVG ham, ZPL ham shundan foydalanadi."""
        s = self._text_val(el, "text", env, p, "")
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        size = self._num(el, "size", env, p, 3.0, 0.3, 200.0)
        bold = self._flag(el, "bold", env, p)
        maxw = self._num(el, "maxw", env, p, 0.0, 0.0, COORD) if el.get("maxw") is not None else 0.0
        align = (el.get("align") or "left").lower()
        anchor = {"center": "middle", "middle": "middle", "right": "end", "end": "end"}.get(align, "start")
        rot = self._num(el, "rotate", env, p, 0.0, -360.0, 360.0)
        color = safe_color(el.get("color"), "#000")
        font = el.get("font") or ""
        lines = [s]
        if self._flag(el, "wrap", env, p) and maxw > 0:
            mx = int(self._num(el, "lines", env, p, 2.0, 1.0, 20.0))
            lines = _wrap_text(s, size, maxw, bold, mx)
        elif maxw > 0:
            s1, size = _fit_text(s.replace("\n", " "), size, maxw, bold)
            lines = [s1]
        else:
            lines = s.split("\n")[:20]
        lh = self._num(el, "line_h", env, p, size * 1.15, 0.3, 400.0)
        italic = self._flag(el, "italic", env, p)
        return dict(lines=lines, x=x, y=y, size=size, bold=bold, italic=italic, anchor=anchor, rot=rot, color=color,
                    font=font, lh=lh, maxw=maxw)

    def _text(self, el, env, out, p) -> None:
        m = self.text_model(el, env, p)
        lines, x, y, size, anchor, rot, color, font, lh = (m[k] for k in ("lines", "x", "y", "size", "anchor", "rot", "color",
                                                                          "font", "lh"))
        attrs = f'font-size="{_n(size)}"'
        if m["bold"]:
            attrs += ' font-weight="bold"'
        if m["italic"]:
            attrs += ' font-style="italic"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if color != "#000":
            attrs += f' fill="{color}"'
        if font.lower() in ("mono", "monospace", "courier"):
            attrs += ' font-family="\'Courier New\', Courier, monospace"'
        by = y + size * 0.82
        if rot:
            attrs += f' transform="rotate({_n(rot)} {_n(x)} {_n(y)})"'
        if len(lines) == 1:
            out.append(f'<text x="{_n(x)}" y="{_n(by)}" {attrs}>{escape(lines[0])}</text>')
        else:
            tsp = "".join(f'<tspan x="{_n(x)}" dy="{_n(0 if i == 0 else lh)}">{escape(t)}</tspan>' for i, t in enumerate(lines))
            out.append(f'<text x="{_n(x)}" y="{_n(by)}" {attrs}>{tsp}</text>')

    def _rect(self, el, env, out, p) -> None:
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=0), self._num(el, "h", env, p, lo=0)
        sw, sc = self._stroke(el, env, p, 0.2 if el.get("stroke") is not None else 0.0)
        fill = el.get("fill")
        fill_c = safe_color(fill, "none") if fill and fill != "none" else "none"
        rx = self._num(el, "radius", env, p, 0.0, 0.0, 100.0)
        a = f'x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="{fill_c}"'
        if sw > 0:
            a += f' stroke="{sc}" stroke-width="{_n(sw)}"'
        if rx:
            a += f' rx="{_n(rx)}"'
        out.append(f"<rect {a}/>")

    def _line(self, el, env, out, p) -> None:
        x1, y1 = self._num(el, "x1", env, p), self._num(el, "y1", env, p)
        x2, y2 = self._num(el, "x2", env, p), self._num(el, "y2", env, p)
        sw, sc = self._stroke(el, env, p, 0.2)
        out.append(f'<line x1="{_n(x1)}" y1="{_n(y1)}" x2="{_n(x2)}" y2="{_n(y2)}" stroke="{sc}" stroke-width="{_n(max(sw, 0.05))}"/>')

    def _image(self, el, env, out, p) -> None:
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=0), self._num(el, "h", env, p, lo=0)
        src = el.get("src", "")
        if not _IMG_RE.match(src or ""):
            self.error(p, "src", "", _("lb.t_image", path=p, n=200))
            raise _Fail()
        out.append(f'<image x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" href="{src}" preserveAspectRatio="xMidYMid meet"/>')

    def _barcode(self, el, env, out, p) -> None:
        kind = str(el.get("kind", "qr")).lower()
        data = self._text_val(el, "data", env, p, "")
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        rot = self._num(el, "rotate", env, p, 0.0, -360.0, 360.0)
        color = safe_color(el.get("color"), "#000")
        try:
            if kind == "qr":
                size = self._num(el, "size", env, p, min(self.W, self.H) * 0.4, 1.0, 500.0)
                quiet = int(self._num(el, "quiet", env, p, 1.0, 0.0, 10.0))
                ec = str(el.get("ec", "m")).lower()
                ec = ec if ec in ("l", "m", "q", "h") else "m"
                g = qr_group(data, x, y, size, quiet=quiet, ec=ec, fast=self.fast_qr, color=color)
                n_mod = qr_cells(data, ec, self.fast_qr)[0]
                if size / (n_mod + 2 * quiet) < 0.3:
                    self.warn(p, "size", data[:40], _("lb.w_bc_dense"))
            else:
                w = self._num(el, "w", env, p, lo=1.0, hi=500.0)
                h = self._num(el, "h", env, p, lo=1.0, hi=500.0)
                quiet = int(self._num(el, "quiet", env, p, 10.0, 0.0, 20.0))
                cap = self._flag(el, "caption", env, p)
                g, mw = code128_group(data, x, y, w, h, caption=cap, quiet=quiet, color=color)
                if mw < 0.19:
                    self.warn(p, "w", data[:40], _("lb.w_bc_dense"))
        except ValueError as e:
            self.error(p, "data", data[:60], str(e))
            raise _Fail() from None
        if rot:
            g = f'<g transform="rotate({_n(rot)} {_n(x)} {_n(y)})">{g}</g>'
        out.append(g)

    def _edges(self, el, env, out, p) -> None:
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=0.5), self._num(el, "h", env, p, lo=0.5)
        ed = {}
        for s in ("top", "bottom", "left", "right"):
            if env.get(f"edge.{s}.has"):
                ed[s] = {"symbol": label_text(env.get(f"edge.{s}.symbol")), "lines": int(env.get(f"edge.{s}.lines") or 0)}
        iw, ih, inner = edge_icon_parts(ed, 34)
        out.append(f'<svg x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" viewBox="0 0 {iw:.0f} {ih:.0f}" '
                   f'preserveAspectRatio="xMaxYMin meet">{inner}</svg>')

    def _part(self, el, env, out, p) -> None:
        """Detal chizmasi: nisbatga mos to'rtburchak, o'lchamlar (uzunlik — pastda, en — o'ngda), kromka — rangli qalin chiziq + belgi."""
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=2.0), self._num(el, "h", env, p, lo=2.0)
        try:
            L, Wd = float(env.get("part.length") or 0), float(env.get("part.width") or 0)
        except (TypeError, ValueError):
            L = Wd = 0.0
        fs = max(1.3, min(2.4, h * 0.13))
        aw, ah = w - fs * 1.8, h - fs * 1.7
        if L <= 0 or Wd <= 0 or aw <= 1 or ah <= 1:
            out.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="none" stroke="#999" stroke-width="0.2"/>')
            return
        k = min(aw / L, ah / Wd)
        rw, rh = L * k, Wd * k
        x0, y0 = x + (aw - rw) / 2, y + (ah - rh) / 2
        o = [f'<rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(rw)}" height="{_n(rh)}" fill="#fff" stroke="#666" stroke-width="0.2"/>']
        sw = max(0.25, min(0.9, min(rw, rh) * 0.12))
        seg = {"top": (x0, y0, x0 + rw, y0), "bottom": (x0, y0 + rh, x0 + rw, y0 + rh),
               "left": (x0, y0, x0, y0 + rh), "right": (x0 + rw, y0, x0 + rw, y0 + rh)}
        sfs = max(1.0, min(fs, sw * 3.2))
        for s, (a, b, c, d) in seg.items():
            if not env.get(f"edge.{s}.has"):
                continue
            col = safe_color(env.get(f"edge.{s}.color"), "#000")
            if int(env.get(f"edge.{s}.lines") or 0) > 0:
                o.append(f'<line x1="{_n(a)}" y1="{_n(b)}" x2="{_n(c)}" y2="{_n(d)}" stroke="{col}" stroke-width="{_n(sw)}"/>')
            sym = escape(label_text(env.get(f"edge.{s}.symbol")))
            tx, ty = {"top": ((a + c) / 2, b + sfs * 1.5 + sw / 2), "bottom": ((a + c) / 2, b - sw / 2 - sfs * 0.4),
                      "left": (a + sw / 2 + sfs * 0.7, (b + d) / 2 + sfs * 0.35),
                      "right": (a - sw / 2 - sfs * 0.7, (b + d) / 2 + sfs * 0.35)}[s]
            o.append(f'<text x="{_n(tx)}" y="{_n(ty)}" font-size="{_n(sfs)}" text-anchor="middle" fill="#222">{sym}</text>')
        o.append(f'<text x="{_n(x0 + rw / 2)}" y="{_n(y0 + rh + fs * 1.15)}" font-size="{_n(fs)}" text-anchor="middle">{escape(label_text(L))}</text>')
        tx, ty = x0 + rw + fs * 1.05, y0 + rh / 2
        o.append(f'<text x="{_n(tx)}" y="{_n(ty)}" font-size="{_n(fs)}" text-anchor="middle" '
                 f'transform="rotate(90 {_n(tx)} {_n(ty)})">{escape(label_text(Wd))}</text>')
        out.append("".join(o))

    def _group(self, el, env, out, p) -> None:
        rot = self._num(el, "rotate", env, p, 0.0, -360.0, 360.0)
        ox, oy = 0.0, 0.0
        o = el.get("origin")
        if o:
            ox = self._num({"v": o[0]}, "v", env, p, 0.0)
            oy = self._num({"v": o[1]}, "v", env, p, 0.0)
        out.append(f'<g transform="translate({_n(ox)} {_n(oy)}) rotate({_n(rot)})">')
        self._elements(el.get("elements") or [], env, out, p + ".elements.")
        out.append("</g>")

    def _if(self, el, env, out, p) -> None:
        try:
            ok = self._flag({"c": el.get("cond")}, "c", env, p, False)
        except _Fail:
            ok = False
        branch = "then" if ok else "else"
        self._elements(el.get(branch) or [], env, out, f"{p}.{branch}.")

    def _var(self, el, env, out, p) -> None:
        env[el["name"]] = self._eval(el.get("expr", "''"), env, p, "expr")

    # — W15: chizma elementlari (poliliniya, yoy, ellips) —
    def _val_num(self, v, env: dict, p: str, field: str, lo: float = -COORD, hi: float = COORD) -> float:
        """Ro'yxat ichidagi qiymat (nuqta koordinatasi) → son; xato `field` nomi bilan yoziladi."""
        r = self._eval(v, env, p, field)
        if isinstance(r, bool):
            r = 1.0 if r else 0.0
        if not isinstance(r, (int, float)):
            self.error(p, field, v, _("lb.e_not_number"))
            raise _Fail()
        return min(max(float(r), lo), hi)

    def _outline(self, el: dict, env: dict, p: str) -> tuple[float, str, str]:
        """(chiziq qalinligi, chiziq rangi, to'ldirish): `stroke` ham, `fill` ham berilmasa — 0.2 mm qora chiziq."""
        fill = el.get("fill")
        fill_c = safe_color(fill, "none") if fill and fill != "none" else "none"
        if el.get("stroke") is None:
            sw, sc = (0.0, "#000") if fill_c != "none" else (0.2, "#000")
        else:
            sw, sc = self._stroke(el, env, p, 0.2)
        return sw, sc, fill_c

    @staticmethod
    def _paint(sw: float, sc: str, fill_c: str) -> str:
        a = f'fill="{fill_c}"'
        if sw > 0:
            a += f' stroke="{sc}" stroke-width="{_n(sw)}" stroke-linejoin="round" stroke-linecap="round"'
        return a

    def poly_points(self, el, env, p) -> list[tuple[float, float]]:
        pts = []
        for i, pt in enumerate(el.get("points") or [], 1):
            pts.append((self._val_num(pt[0], env, p, f"points[{i}][1]"), self._val_num(pt[1], env, p, f"points[{i}][2]")))
        return pts

    def _polyline(self, el, env, out, p) -> None:
        pts = self.poly_points(el, env, p)
        closed = self._flag(el, "closed", env, p)
        sw, sc, fill_c = self._outline(el, env, p)
        d = "M" + " L".join(f"{_n(x)} {_n(y)}" for x, y in pts) + (" Z" if closed else "")
        out.append(f'<path d="{d}" {self._paint(sw, sc, fill_c)}/>')

    def arc_geometry(self, el, env, p) -> tuple[float, float, float, float, float]:
        """(cx, cy, r, a1, sweep): sweep = a2 − a1 (−360…360); |sweep| ≥ 360 — to'liq aylana."""
        cx, cy = self._num(el, "cx", env, p), self._num(el, "cy", env, p)
        r = self._num(el, "r", env, p, lo=0.0)
        a1 = self._num(el, "a1", env, p, 0.0, -3600.0, 3600.0)
        a2 = self._num(el, "a2", env, p, 360.0, -3600.0, 3600.0)
        return cx, cy, r, a1, max(-360.0, min(360.0, a2 - a1))

    def _arc(self, el, env, out, p) -> None:
        cx, cy, r, a1, sweep = self.arc_geometry(el, env, p)
        sw, sc, fill_c = self._outline(el, env, p)
        if r <= 0 or sweep == 0:
            return
        paint = self._paint(sw, sc, fill_c)
        if abs(sweep) >= 359.999:
            out.append(f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(r)}" ry="{_n(r)}" {paint}/>')
            return
        t1, t2 = math.radians(a1), math.radians(a1 + sweep)
        x1, y1 = cx + r * math.cos(t1), cy + r * math.sin(t1)
        x2, y2 = cx + r * math.cos(t2), cy + r * math.sin(t2)
        big, swp = int(abs(sweep) > 180), int(sweep > 0)
        d = f"M{_n(x1)} {_n(y1)} A{_n(r)} {_n(r)} 0 {big} {swp} {_n(x2)} {_n(y2)}"
        if fill_c != "none":
            d = f"M{_n(cx)} {_n(cy)} L{_n(x1)} {_n(y1)} A{_n(r)} {_n(r)} 0 {big} {swp} {_n(x2)} {_n(y2)} Z"
        out.append(f'<path d="{d}" {paint}/>')

    def _ellipse(self, el, env, out, p) -> None:
        cx, cy = self._num(el, "cx", env, p), self._num(el, "cy", env, p)
        rx, ry = self._num(el, "rx", env, p, lo=0.0), self._num(el, "ry", env, p, lo=0.0)
        sw, sc, fill_c = self._outline(el, env, p)
        if rx <= 0 or ry <= 0:
            return
        out.append(f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(rx)}" ry="{_n(ry)}" {self._paint(sw, sc, fill_c)}/>')


# ───────────────────────── Tekshiruv (muharrir uchun) ─────────────────────────
def _expr_fields(el: dict):
    spec = SPEC.get(el.get("t"), {})
    for f in (*spec.get("num", ()), *spec.get("expr", ()), *spec.get("flag", ())):
        v = el.get(f)
        if isinstance(v, str):
            yield f, v
    st = el.get("stroke")
    if isinstance(st, dict) and isinstance(st.get("w"), str):
        yield "stroke.w", st["w"]
    elif isinstance(st, str):
        yield "stroke", st
    for i, v in enumerate(el.get("origin") or []):
        if isinstance(v, str):
            yield f"origin[{i + 1}]", v
    if spec.get("points"):
        for i, pt in enumerate(el.get("points") or [], 1):
            for j, v in enumerate(pt if isinstance(pt, list) else [], 1):
                if isinstance(v, str):
                    yield f"points[{i}][{j}]", v


def check_template(data: Any, params: Optional[dict] = None, lang: str = "ru", env: Optional[dict] = None,
                   width_mm: Optional[float] = None, height_mm: Optional[float] = None) -> dict:
    """Muharrir uchun: {ok, errors:[…], warnings:[…]}. Tuzilma xatosi, ifoda sintaksisi, noma'lum kalitlar va namuna qatorida
    hisoblash (noma'lum o'zgaruvchi, tur xatosi, nolga bo'lish …). Har yozuv: {path, field, expr, message, count}."""
    from ..i18n import LANG
    token = LANG.set(lang if lang in ("ru", "uz") else "ru")
    try:
        try:
            tpl = normalize_template(data)
        except TemplateError as e:
            return {"ok": False, "errors": [{"path": "", "field": "", "expr": "", "message": str(e), "count": 1}], "warnings": []}
        errors: list[dict] = []
        warnings: list[dict] = []
        for i, v in enumerate(tpl["vars"], 1):
            try:
                expr.compile_check(v.get("expr", "''") if isinstance(v.get("expr", "''"), str) else str(v["expr"]))
            except ValueError as e:
                errors.append({"path": f"vars.{v['name']}", "field": "expr", "expr": str(v.get("expr"))[:120], "message": str(e), "count": 1})
        for p, el in walk(tpl["elements"]):
            known = {*SPEC[el["t"]].get("num", ()), *SPEC[el["t"]].get("expr", ()), *SPEC[el["t"]].get("flag", ()),
                     *SPEC[el["t"]].get("lit", ()), *SPEC[el["t"]].get("children", ()), "stroke", "origin",
                     *(("points",) if SPEC[el["t"]].get("points") else ()), *_COMMON_KEYS}
            for k in el:
                if k not in known:
                    warnings.append({"path": p, "field": k, "expr": "", "message": _("lb.w_unknown_key", k=k), "count": 1})
            for f, src in _expr_fields(el):
                try:
                    expr.compile_check(src)
                except ValueError as e:
                    errors.append({"path": p, "field": f, "expr": src[:120], "message": str(e), "count": 1})
        # namuna qatorida hisoblab ko'riladi (noma'lum o'zgaruvchi, tur xatosi …); sintaksis xatosi bor maydon takrorlanmaydi
        from .label_vars import sample_env
        w = float(width_mm or tpl["size"]["w"])
        h = float(height_mm or tpl["size"]["h"])
        base = dict(env if env is not None else sample_env("part", lang))
        base["label.width"], base["label.height"] = w, h
        r = Renderer(tpl, width_mm=w, height_mm=h, params=params, lang=lang)
        r.render(base)
        seen = {(e["path"], e["field"]) for e in errors}
        errors += [e for e in r.errors.values() if (e["path"], e["field"]) not in seen]
        warnings += list(r.warnings.values())
        return {"ok": not errors, "errors": errors, "warnings": warnings}
    finally:
        LANG.reset(token)
