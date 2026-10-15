"""LB `source=user` — «Пользовательские данные» (W15 · LB-D): maydonlar sxemasi, qiymatlarni turga keltirish, tekshiruv.

Sxema (`LBParams.fields`): [{name, title, type: string|integer|double|boolean, width, default}] — `name` shablonda `user.<name>`
o'zgaruvchisi bo'ladi (lotin harf/raqam/pastki chiziq, ≤ 31 belgi). Qatorlar (`LBParams.data`): [{qty, <name>: qiymat, …}] — `qty`
(zarur emas, standart 1) shu qator etiketkasining nusxalari soni. Excel dan qo'yilgan qiymatlar matn bo'lib keladi: ular chop paytida
maydon turiga keltiriladi (`coerce_user_value`; probel/NBSP olib tashlanadi, vergul — kasr nuqtasi). Tur ko'rsatilmagan eski maydon
(`type` yo'q) qiymatni o'zgartirmay uzatadi (avvalgi xulq).
"""
from __future__ import annotations

import re
from typing import Any

from ..i18n import _

FIELD_TYPES = ("string", "integer", "double", "boolean")
MAX_FIELDS = 50
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$")
_NUM_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
_TRUE = {"1", "true", "yes", "y", "t", "да", "ха", "ha", "+", "x", "on"}
MAX_TEXT = 1000


def _num(v: Any):
    """Qiymat → son (butun yoki kasr) yoki None."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = re.sub(r"[\s  ]", "", v).replace(",", ".")
        if _NUM_RE.match(s):
            return float(s) if "." in s else int(s)
    return None


def user_field_specs(fields: Any) -> dict[str, tuple[str, Any]]:
    """`LBParams.fields` → {nom: (tur, standart qiymat)}; noto'g'ri nomli maydonlar tashlanadi (eski JSON bilan mos)."""
    out: dict[str, tuple[str, Any]] = {}
    for f in fields or []:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name", ""))
        if not NAME_RE.match(name) or name in out:
            continue
        tp = f.get("type")
        out[name] = (tp if tp in FIELD_TYPES else "any", f.get("default"))
    return out


def coerce_user_value(v: Any, tp: str = "any", default: Any = None) -> Any:
    """Qator qiymati → ifoda dvigateli turi (str | int | float | bool). Bo'sh qiymat — maydon standarti (yo'q bo'lsa tur nolini)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        v = default
    if tp == "integer":
        n = _num(v)
        return int(n) if n is not None else 0
    if tp == "double":
        n = _num(v)
        return float(n) if n is not None else 0.0
    if tp == "boolean":
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        return str(v or "").strip().lower() in _TRUE
    if v is None:
        return ""
    if tp == "string":
        return str(v)[:MAX_TEXT] if not isinstance(v, str) else v[:MAX_TEXT]
    return v if isinstance(v, (int, float, bool, str)) else str(v)         # "any": avvalgi xulq


def normalize_fields(fields: Any, strict: bool = True) -> list[dict]:
    """Maydonlar sxemasini tozalab qaytaradi. `strict=True` — noto'g'ri nom/takror/tur/standart qiymat uchun ValueError (matn foydalanuvchi
    tilida); `strict=False` (`LBParams` validatori) — yaroqsiz maydonlar tashlanadi, noma'lum tur «string» bo'ladi: har PATCH butun
    operatsiyani qayta tekshirgani uchun saqlangan eski ma'lumot (importdan kelgan sxema) operatsiyani buzmasligi shart. UI faqat to'g'ri sxemani yuboradi."""
    if not isinstance(fields, list):
        raise ValueError(_("lb.u_fields_max", n=MAX_FIELDS))
    if len(fields) > MAX_FIELDS:
        if strict:
            raise ValueError(_("lb.u_fields_max", n=MAX_FIELDS))
        fields = fields[:MAX_FIELDS]
    out: list[dict] = []
    seen: set[str] = set()
    for i, f in enumerate(fields, 1):
        if not isinstance(f, dict):
            if strict:
                raise ValueError(_("lb.u_field_bad", i=i))
            continue
        name = f.get("name")
        if not isinstance(name, str) or not NAME_RE.match(name):
            if strict:
                raise ValueError(_("lb.u_field_name", i=i, name=str(name)[:40]))
            continue
        if name in seen:
            if strict:
                raise ValueError(_("lb.u_field_dup", name=name))
            continue
        seen.add(name)
        tp = f.get("type", "string")
        if tp not in FIELD_TYPES:
            if strict:
                raise ValueError(_("lb.u_field_type", name=name, t=str(tp)[:20]))
            tp = "string"
        item: dict = {"name": name, "title": str(f.get("title") or name)[:60], "type": tp}
        w = f.get("width")
        if isinstance(w, (int, float)) and not isinstance(w, bool) and 0 < w <= 5000:       # ustun eni (ko'rsatish uchun): o'zgartirilmaydi
            item["width"] = w
        d = f.get("default")
        if d is not None and not isinstance(d, (str, int, float, bool)):
            if strict:
                raise ValueError(_("lb.u_field_default", name=name))
            d = None
        item["default"] = d if d is None or not isinstance(d, str) else d[:MAX_TEXT]
        out.append(item)
    return out


def sample_row(fields: Any, lang: str = "ru") -> dict:
    """Maydonlar uchun namuna qator (shablon ko'rinishi): satr — maydon sarlavhasi, son — 1, mantiqiy — true."""
    row: dict = {"qty": 1}
    for f in fields or []:
        if not isinstance(f, dict) or not NAME_RE.match(str(f.get("name", ""))):
            continue
        tp = f.get("type")
        row[f["name"]] = (f.get("default") if f.get("default") not in (None, "") else
                          {"integer": 1, "double": 1.0, "boolean": True}.get(tp, str(f.get("title") or f["name"])))
    return row
