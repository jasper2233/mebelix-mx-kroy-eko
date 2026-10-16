"""`.project` dagi LB (etiketkalar) operatsiyasi → LBParams (korxonaning o'z loyiha fayllari uchun; plugins/legacy_project.py chaqiradi).

O'qiladigan atributlar (parametr nomlari inventar 03 §2.4 / §4.3 bilan mos):
  printMode (0 — A4 varaq, 1 — etiketka printeri ❓), columns, rows, gap, margin (bayroq), source (0 foydalanuvchi, 1 mahsulotlar,
  2 detallar va qoldiqlar), printParts, partEach, partONZ, printWastes, wasteEach, productEach, productONZ,
  fields (BASE64 XML — foydalanuvchi ma'lumotlari sxemasi: name/type/width/default).
Etiketka o'lchami faylda yo'q: A4 rejimida (printMode=0, rows ≥ 1) u sahifa, maydon, to'r va oraliqdan hisoblanadi
(`LBParams.label_size`, masalan 2×4, gap 10, margin → 94×63.75 mm). `program` ildizidagi dx/dy (bo'lsa) — width_mm/height_mm ga
yoziladi (rulon rejimi va eski rows=0 uchun). Atribut yo'q bo'lsa — yangi operatsiya standarti (kuzatilgan tizimdagi kabi).
`program` (eski shablon matni) W9 dan boshlab `label_gl_import` bilan shablonga o'giriladi (`LBParams.template`; operatsiya shuni
ishlatadi); o'girib bo'lmasa — eskicha: o'qilmaydi, standart shablon ishlatiladi. Asl matn har holda ma'lumot yo'qolmasin uchun
`LBParams.legacy_program` da saqlanadi. `data` (ikkilik foydalanuvchi qatorlari) o'qilmaydi.
`partSelected` — tanlov bayrog'i xolos (qaysi detallar ekani faylda yo'q): e'tiborga olinmaydi.
"""
from __future__ import annotations

import base64
import re
from typing import Optional

try:  # xavfsiz XML o'qish
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET  # noqa: N817

from ..i18n import _
from ..models import LB_MARGIN_MM, LBParams

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$")
_TYPES = {"int": "integer", "long": "integer", "float": "double", "number": "double", "decimal": "double", "bool": "boolean", "str": "string",
          "text": "string"}                     # fayldagi turlar → bizning 4 ta tur (noma'lum — string)
_DX =re.compile(r"<program\b[^>]*?\bdx=\"([0-9.]+)\"")
_DY = re.compile(r"<program\b[^>]*?\bdy=\"([0-9.]+)\"")


def _f(v, d: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


def _b(v, d: bool = False) -> bool:
    if v is None:
        return d
    return str(v).strip().lower() in ("true", "1", "yes", "да")


def _clamp(v: float, lo: float, hi: float) -> float:
    return min(max(v, lo), hi)


def _fields(raw: Optional[str]) -> list[dict]:
    """`fields="BASE64:<xml>"` → [{name, title, type, width, default}] (xato — bo'sh ro'yxat)."""
    if not raw:
        return []
    try:
        txt = raw[7:] if raw.startswith("BASE64:") else raw
        xml = base64.b64decode(txt, validate=False).decode("utf-8", "replace")
        root = ET.fromstring(xml)
    except Exception:  # noqa: BLE001 — buzuq/begona format: sxema tashlab ketiladi, loyiha ochiladi
        return []
    out = []
    seen: set[str] = set()
    for f in root.iter("field"):
        name = f.get("name") or ""
        if not _NAME_RE.match(name) or name in seen or len(out) >= 50:       # takror nom — `LBParams.fields` tekshiruvi (W15) rad etardi
            continue
        seen.add(name)
        tp = (f.get("type") or "string").strip().lower()[:20]
        tp = _TYPES.get(tp, tp if tp in ("string", "integer", "double", "boolean") else "string")
        out.append({"name": name, "title": (f.get("description") or f.get("title") or name)[:100],
                    "type": tp, "width": _clamp(_f(f.get("width"), 10), 1, 200),
                    "default": (f.get("default") or "")[:200]})
    return out


def from_project_xml(oe, warnings: list[str]) -> tuple[LBParams, str]:
    """`<operation typeId="LB" …>` → (LBParams, operatsiya nomi)."""
    program = oe.get("program") or ""
    kw: dict = dict(
        source={0: "user", 1: "products", 2: "parts"}.get(int(_f(oe.get("source"), 2)), "parts"),
        mode="sheet" if int(_f(oe.get("printMode"), 0)) == 0 else "roll",
        columns=int(_clamp(_f(oe.get("columns"), 1), 1, 20)),
        rows=int(_clamp(_f(oe.get("rows"), 1), 0, 50)),
        gap_mm=_clamp(_f(oe.get("gap"), 0), 0, 50),
        margin_mm=LB_MARGIN_MM if _b(oe.get("margin"), False) else None,
        print_parts=_b(oe.get("printParts"), True),
        part_each=_b(oe.get("partEach"), False),
        part_only_nonzero=_b(oe.get("partONZ"), False),
        print_wastes=_b(oe.get("printWastes"), True),
        waste_each=_b(oe.get("wasteEach"), False),
        product_each=_b(oe.get("productEach"), False),
        product_only_nonzero=_b(oe.get("productONZ"), False),
        fields=_fields(oe.get("fields")),
    )
    if oe.get("border") is not None:                         # «Границы»: 0 — yo'q, boshqasi — perimetr bo'yicha
        kw["border_mode"] = "none" if int(_f(oe.get("border"), 1)) == 0 else "perimeter"
    mx, my = _DX.search(program), _DY.search(program)
    if mx and my:                                            # A4 (rows ≥ 1) da chopda hisoblangan o'lcham ishlatiladi (LBParams.label_size)
        kw["width_mm"] = _clamp(_f(mx.group(1), 58), 5, 500)
        kw["height_mm"] = _clamp(_f(my.group(1), 40), 5, 500)
    name = oe.get("typeName") or oe.get("name") or _(f"lb.op_name_{kw['source']}")
    if program:
        kw["legacy_program"] = program[:300_000]            # asl matn har doim saqlanadi (ma'lumot yo'qolmasin)
        res = _convert(program, name)
        if res is not None:                                  # W9: o'girildi — operatsiya shu shablonni ishlatadi
            kw["template"] = res.template
            det = "; ".join(w["message"] + (f" ×{w['count']}" if w["count"] > 1 else "") for w in res.warnings[:3])
            warnings.append(_("imp_lb_converted", name=name, n=len(res.warnings), details=f": {det}" if det else ""))
        else:                                                # o'girib bo'lmadi — eskicha: standart shablon ishlatiladi
            warnings.append(_("imp_lb_program", name=name))
    return LBParams(**kw), name


def _convert(program: str, name: str):
    """`program` XML → shablon (label_gl_import); o'girib bo'lmasa yoki bo'sh chiqsa — None (loyiha importi to'xtamaydi)."""
    from . import label_gl_import
    try:
        return label_gl_import.convert_program(program, name)
    except Exception:  # noqa: BLE001 — buzuq/begona matn: eski xulq (legacy_program + standart shablon)
        return None
