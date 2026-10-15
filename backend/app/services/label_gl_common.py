"""Tayyor etiketka shabloni fayli (`<program>` XML) bilan ishlash uchun umumiy yordamchilar (W9 · LB-D).

Mijozning o'z fayllari ish vaqtida import/eksport qilinadi; bu modulda faqat **tuzilma** bilan bog'liq narsa: xavfsiz XML o'qish,
chegaralar, o'zgaruvchi nomlari jadvali (standart nomlar — fayl formatining interfeys identifikatorlari), ifoda satrlari ustida
kichik amallar (koordinata siljishi, taxallus almashtirish), rang va rasm tekshiruvi.
GibLabning namuna shablonlari, rasmlari va matnlari bu yerda yo'q.
"""
from __future__ import annotations

import base64
import binascii
import re
from typing import Callable, Iterable, Optional
from xml.etree.ElementTree import Element

from ..i18n import _
from . import label_tpl

from xml.etree.ElementTree import ParseError

try:                                   # xavfsiz XML o'qish: DTD/entity yo'q
    from defusedxml import ElementTree as _DET
    from defusedxml.common import DefusedXmlException as _DefusedErr
    _SAFE_PARSER = True
except ImportError:                    # pragma: no cover — requirements.txt da defusedxml bor
    import xml.etree.ElementTree as _DET   # noqa: N814

    class _DefusedErr(Exception):      # type: ignore[no-redef]
        pass
    _SAFE_PARSER = False

MAX_FILE_BYTES = 5 * 1024 * 1024       # yuklangan fayl
MAX_XML_NODES = 5000                   # `<program>` dagi teglar soni
MAX_XML_DEPTH = 40                     # `<program>` ichma-ich chuqurligi
MAX_IMAGE_BYTES = 256 * 1024           # rasm (ikkilik): so'ralgan chegara; shablon formati o'zi 200 KB gacha (label_tpl.MAX_IMAGE_B64)
MAX_PROGRAMS = 20                      # `.project` dan bir yo'la taklif qilinadigan shablonlar
SIZE_MIN, SIZE_MAX = label_tpl.SIZE_MIN, label_tpl.SIZE_MAX


class GLError(ValueError):
    """Fayl o'qib/yozib bo'lmaydi (xabar foydalanuvchi tilida)."""


# ───────────────────────── Xavfsiz XML ─────────────────────────
_DECL_RE = re.compile(r"^\s*<\?xml[^>]*\?>")
_DTD_RE = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)
_DTD_RE_S = re.compile(r"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def safe_fromstring(data: bytes | str) -> Element:
    """XML ni xavfsiz o'qiydi: DTD/entity (billion-laughs, tashqi manba) rad etiladi; xato — GLError."""
    if isinstance(data, str):
        if _DTD_RE_S.search(data):
            raise GLError(_("lbx.e_dtd"))
        data = _DECL_RE.sub("", data.lstrip(), count=1)     # str ichida kodlash e'lonini parser qabul qilmasligi mumkin
    else:
        if _DTD_RE.search(data):
            raise GLError(_("lbx.e_dtd"))
        data = data.lstrip()                                # e'londan oldingi bo'sh joy/qator — xato emas
    try:
        return _DET.fromstring(data, forbid_dtd=True) if _SAFE_PARSER else _DET.fromstring(data)
    except _DefusedErr as e:
        raise GLError(_("lbx.e_dtd")) from e
    except ParseError as e:
        raise GLError(_("lbx.e_xml", e=str(e)[:120])) from e
    except (ValueError, UnicodeError) as e:
        raise GLError(_("lbx.e_xml", e=str(e)[:120])) from e


def check_limits(root: Element) -> int:
    """Teglar soni va chuqurligi chegarada ekanini tekshiradi (rekursiyasiz); teglar sonini qaytaradi."""
    n = 0
    stack: list[tuple[Element, int]] = [(root, 1)]
    while stack:
        el, d = stack.pop()
        n += 1
        if n > MAX_XML_NODES:
            raise GLError(_("lbx.e_nodes", n=MAX_XML_NODES))
        if d > MAX_XML_DEPTH:
            raise GLError(_("lbx.e_depth", n=MAX_XML_DEPTH))
        stack.extend((c, d + 1) for c in el)
    return n


# ───────────────────────── Standart o'zgaruvchilar (fayl formati nomlari) ─────────────────────────
def _std_types() -> dict[str, str]:
    t: dict[str, str] = {}
    for n in ("name", "date", "description", "currency", "crc16", "crc32"):
        t[f"project.{n}"] = "string"
    for n in ("index", "name", "code", "description", "phone1", "phone2", "date"):
        t[f"product.{n}"] = "string"
    t["product.count"] = "integer"
    t["material.name"] = t["material.code"] = "string"
    t["part.id"] = "integer"
    t["part.code"] = "string"
    t["part.counter"] = "integer"
    for n in ("good", "name", "description", "index", "indexInOperation", "fullName", "surfFront", "surfBack"):
        t[n] = "string"
    for n in ("length", "width", "detail.length", "detail.width", "thick"):
        t[n] = "double"
    for n in ("waste", "business", "txt", "groove", "drill", "mill"):
        t[n] = "boolean"
    for n in ("count", "totalCount", "usedCount"):
        t[n] = "integer"
    for s in "tblr":
        t[f"e{s}c"] = t[f"e{s}n"] = t[f"e{s}s"] = "string"
        t[f"e{s}t"] = t[f"e{s}j"] = "double"
        t[f"gr{s}c"] = t[f"gr{s}n"] = "string"
        t[f"gr{s}w"] = t[f"gr{s}d"] = t[f"gr{s}o"] = "double"
        t[f"gr{s}oi"] = t[f"gr{s}s"] = "boolean"
    for i in range(1, 6):
        t[f"XNC{i}"] = "string"
        t[f"xncSide{i}"] = t[f"xncBSD{i}"] = "boolean"
    return t


GL_STD: dict[str, str] = _std_types()          # 104 ta standart nom → tur (string | integer | double | boolean)
LABEL_SIZE_VARS = {"dx": "label.width", "dy": "label.height"}      # «etiketka o'lchami» (faylda e'lonsiz ishlatiladi)


def _canon_to_gl() -> dict[str, str]:
    """Bizning kanonik nomlar → fayl formatidagi nom (faqat aynan mos keluvchilari)."""
    from .label_vars import ALIASES, SIDES, SIDE_CH
    m = {
        "label.width": "dx", "label.height": "dy", "part.thickness": "thick", "part.grain": "txt", "part.qty": "count",
        "part.total_qty": "totalCount", "part.used_qty": "usedCount", "part.name": "name", "part.description": "description",
        "part.index": "index", "part.uid": "part.id", "part.detail_length": "detail.length", "part.detail_width": "detail.width",
        "part.blank_length": "length", "part.blank_width": "width", "part.groove": "groove", "part.mill": "mill",
        "part.drill": "drill", "waste.business": "business", "product.qty": "product.count",
    }
    for s in SIDES:
        for suffix, f in (("symbol", "s"), ("code", "c"), ("name", "n"), ("thickness", "t"), ("jointing", "j")):
            m[f"edge.{s}.{suffix}"] = f"e{SIDE_CH[s]}{f}"
        for suffix, f in (("code", "c"), ("name", "n"), ("width", "w"), ("depth", "d"), ("offset", "o")):
            m[f"groove.{s}.{suffix}"] = f"gr{SIDE_CH[s]}{f}"
    for i in range(1, 6):
        m[f"xnc{i}.code"], m[f"xnc{i}.side"], m[f"xnc{i}.by_size"] = f"XNC{i}", f"xncSide{i}", f"xncBSD{i}"
    for alias, src in ALIASES.items():                   # snake_case taxalluslar (part_uid, project_name …) → dotli nom
        if alias not in GL_STD and src in GL_STD and alias not in m:
            m[alias] = src
    return m


_CANON_TO_GL: Optional[dict[str, str]] = None


def canon_to_gl() -> dict[str, str]:
    global _CANON_TO_GL
    if _CANON_TO_GL is None:
        _CANON_TO_GL = _canon_to_gl()
    return _CANON_TO_GL


# ───────────────────────── Ifoda satrlari ustida amallar ─────────────────────────
_TOKEN_RE = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?"""
                       r"""|[^\W\d]\w*(?:\.[^\W\d]\w*)*""", re.UNICODE)
_KEYWORDS = {"and", "or", "not", "xor", "true", "false", "null", "if", "else"}
_NUM_LIT = re.compile(r"^-?\d+(?:\.\d+)?$")
_ATOM = re.compile(r"^-?[\w.]+$", re.UNICODE)


def iter_idents(src: str) -> Iterable[tuple[int, int, str]]:
    """Ifodadagi o'zgaruvchi nomlari (matn literali, son, funksiya nomi va kalit so'zlar tashqarida): (boshi, oxiri, nom)."""
    for m in _TOKEN_RE.finditer(src):
        tok = m.group(0)
        if tok[0] in "'\"." or tok[0].isdigit() or tok.lower() in _KEYWORDS:
            continue
        if src[m.end():].lstrip().startswith("("):         # funksiya chaqiruvi
            continue
        yield m.start(), m.end(), tok


def rewrite_idents(src: str, fn: Callable[[str], str]) -> str:
    out: list[str] = []
    pos = 0
    for a, b, tok in iter_idents(src):
        new = fn(tok)
        if new != tok:
            out.append(src[pos:a])
            out.append(new)
            pos = b
    out.append(src[pos:])
    return "".join(out)


def parse_num(s) -> Optional[int | float]:
    """«12», «-0.5» → son; boshqasi — None."""
    if isinstance(s, bool):
        return None
    if isinstance(s, (int, float)):
        return s
    if isinstance(s, str) and _NUM_LIT.match(s.strip()):
        t = s.strip()
        return float(t) if "." in t else int(t)
    return None


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt_num(v: int | float) -> str:
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def par(v) -> str:
    """Ifoda bo'lagi (son yoki satr) — murakkab bo'lsa qavsga olingan."""
    if is_num(v):
        return fmt_num(v)
    s = str(v).strip()
    return s if _ATOM.match(s) else f"({s})"


def unparen(s: str) -> str:
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        depth = 0
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i < len(s) - 1:
                    return s
        return s[1:-1]
    return s


def add(a, b):
    """a + b: ikkalasi son bo'lsa — son; aks holda `(a)+(b)` ifodasi (`unadd_tail` teskarisi)."""
    if is_num(a) and is_num(b):
        r = round(a + b, 4)
        return int(r) if isinstance(a, int) and isinstance(b, int) else r
    if is_num(b) and b == 0:
        return a
    if is_num(a) and a == 0:
        return b
    return f"{par(a)}+{par(b)}"


def sub(a, b):
    if is_num(a) and is_num(b):
        r = round(a - b, 4)
        return int(r) if isinstance(a, int) and isinstance(b, int) else r
    if is_num(b) and b == 0:
        return a
    return f"{par(a)}-{par(b)}"


def half(w):
    if is_num(w):
        r = round(w / 2.0, 4)
        return r
    return f"{par(w)}/2.0"


BASELINE_K = 0.82       # label_tpl.Renderer._text: asosiy chiziq = y + size*0.82 (y — matn qutisining yuqori chetи)


def _mul_k(size):
    return round(size * BASELINE_K, 4) if is_num(size) else f"{par(size)}*{BASELINE_K}"


def baseline_to_top(y, size):
    """Faylda matn `y` si — asosiy chiziq (chiziq tagiga qo'yilgan «tagchiziq» shundan dalolat beradi ❓); bizda — yuqori chet."""
    return sub(y, _mul_k(size))


def top_to_baseline(y_top, size):
    """`baseline_to_top` teskarisi (ifodalar uchun aniq: `(y)-(size)*0.82` shakli tiklanadi)."""
    k = _mul_k(size)
    if is_num(y_top) and is_num(k):
        return round(y_top + k, 4)
    if isinstance(y_top, str):
        suf = "-" + par(k)
        if y_top.endswith(suf):
            head = unparen(y_top[: -len(suf)])
            n = parse_num(head)
            return n if n is not None else head
    return add(y_top, k)


def unadd_head(s, head) -> Optional[int | float | str]:
    """`add(head, T)` natijasidan T ni tiklaydi (head — son yoki ifoda); mos kelmasa — None."""
    if is_num(s) and is_num(head):
        r = round(s - head, 4)
        return int(r) if isinstance(s, int) and isinstance(head, int) else r
    if is_num(head) and head == 0:
        return s
    if not isinstance(s, str):
        return None
    if isinstance(head, str) and s == head:
        return 0
    pre = par(head) + "+"
    if s.startswith(pre):
        tail = unparen(s[len(pre):])
        n = parse_num(tail)
        return n if n is not None else tail
    return None


def unadd_tail(s, tail) -> Optional[int | float | str]:
    """`add(X, tail)` natijasidan X ni tiklaydi (tail — son yoki ifoda); mos kelmasa — None."""
    if is_num(s) and is_num(tail):
        r = round(s - tail, 4)
        return int(r) if isinstance(s, int) and isinstance(tail, int) else r
    if not isinstance(s, str):
        return None
    t = par(tail)
    if s == t or (isinstance(tail, str) and s == tail):          # X = 0 edi: add() faqat tail ni qaytargan
        return 0
    suf = "+" + t
    if s.endswith(suf):
        head = unparen(s[: -len(suf)])
        n = parse_num(head)
        return n if n is not None else head
    return None


# ───────────────────────── Rang va rasm ─────────────────────────
_RGB = re.compile(r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*[\d.]+\s*)?\)$", re.IGNORECASE)
_HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_NAMED = re.compile(r"^[a-zA-Z]{3,20}$")


def norm_color(c) -> Optional[str]:
    """Rang → `#rrggbb` (kichik harf) yoki rang nomi; bo'sh/noto'g'ri — None."""
    if not isinstance(c, str):
        return None
    c = c.strip()
    if not c:
        return None
    m = _HEX.match(c)
    if m:
        h = m.group(1).lower()
        return "#" + ("".join(ch * 2 for ch in h) if len(h) == 3 else h)
    m = _RGB.match(c)
    if m:
        r, g, b = (min(255, int(x)) for x in m.groups())
        return f"#{r:02x}{g:02x}{b:02x}"
    if _NAMED.match(c):
        return c.lower()
    return None


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_DATA_IMG = re.compile(r"^data:image/(png|jpeg|jpg);base64,([A-Za-z0-9+/=\s]+)$")


def check_image(src: str) -> tuple[Optional[str], str]:
    """Ichki rasm (data URI) tekshiruvi → (tozalangan URI | None, sabab kodi: ok | type | size | invalid)."""
    m = _DATA_IMG.match(src.strip()) if isinstance(src, str) else None
    if not m:
        return None, "type"
    b64 = re.sub(r"\s+", "", m.group(2))
    limit_b64 = min(label_tpl.MAX_IMAGE_B64, (MAX_IMAGE_BYTES * 4) // 3 + 8)
    if len(b64) > limit_b64:
        return None, "size"
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        return None, "invalid"
    kind = m.group(1)
    if kind == "png" and not raw.startswith(_PNG_MAGIC):
        return None, "invalid"
    if kind in ("jpeg", "jpg") and not raw.startswith(b"\xff\xd8\xff"):
        return None, "invalid"
    return f"data:image/{'jpeg' if kind == 'jpg' else kind};base64,{b64}", "ok"


# ───────────────────────── Ogohlantirishlar yig'uvchisi ─────────────────────────
class Warnings:
    """Takrorlanmas (kod, kalit) bo'yicha sanaydi; xabar matni chaqiruv vaqtidagi tilda tuziladi."""

    def __init__(self, prefix: str):
        self.prefix = prefix
        self._d: dict[tuple[str, str], dict] = {}

    def add(self, code: str, key: str = "", **fmt) -> None:
        k = (code, key)
        d = self._d.get(k)
        if d is None:
            self._d[k] = {"code": code, "key": key, "count": 1, "fmt": fmt}
        else:
            d["count"] += 1

    def __bool__(self) -> bool:
        return bool(self._d)

    def to_list(self) -> list[dict]:
        out = []
        for d in self._d.values():
            msg = _(f"{self.prefix}{d['code']}", **{"k": d["key"], **d["fmt"]})
            out.append({"code": d["code"], "key": d["key"], "count": d["count"], "message": msg})
        return out


def valid_name(name: Optional[str]) -> bool:
    return bool(name) and len(name) <= 60 and bool(label_tpl._NAME_RE.match(name))
