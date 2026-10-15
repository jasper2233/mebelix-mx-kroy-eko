"""(CL) `.project` importi (W11): `<operation typeId="CL">` + `<good typeId="band">` → `Operation(type=CL)` (CLParams, polosalar).

Format tavsifi (ochiq): CL atributlari — tool1 (arra: swSawthick, swPackageHeight), cTrimW (torsovka), cTrimEW (minimal otstup
oxirida), cFillRep, cCPF, cCostType, cCostCut, cCostByItem(Round), cMinDimRegWaste1, cBusinessWaste, cTrimWaste(r), cMinDimDetail;
material — `band` tovari (w — polosa eni, t — qalinlik, cost — 1 m narxi, ichida `<part count l w>` — polosa qatorlari).
Hisoblash natijasi (ikkilik `data`, `cFilling` …) O'QILMAYDI — loyiha qayta «Раскроить» qilinadi.

Manfiy uzunlik qoidasi (T_W11_CL.md §4): CL detalida `l < 0` (masalan `l="-350"`, `w="7"`) — Bazis hisoblab bo'lmagan detal belgisi.
Bunday detal `length = 0` bilan import qilinadi (kroyga kirmaydi), xom qiymat `Part.src_length` da saqlanadi, importda ogohlantirish
beriladi (`imp_cl_uncomputed`). `|l|` uzunlik sifatida ISHLATILMAYDI (taxmin qilinmaydi) — `CL_NEGATIVE_LENGTH_MODE` konstantasi
orqali almashtiriladi: "uncomputed" (standart) | "abs".
"""
from __future__ import annotations

from ..models import CL_DEFAULTS, CLCostBase, CLParams, Operation, SheetRounding, StockSheet

CL_NEGATIVE_LENGTH_MODE = "uncomputed"
BUSINESS_M_THRESHOLD = 50.0      # cBusinessWaste: formatda «m» (standart 1 m); ≥ 50 bo'lsa mm deb olinadi (50 m li otxod bo'lmaydi)


def negative_length(raw: float) -> tuple[float, float]:
    """Manfiy xom uzunlik → (length, src_length). Standart: (0, raw) — hisoblanmagan; "abs": (|raw|, raw)."""
    from . import import_formats               # W18: import dialogi parametri («cl_negative_length»: uncomputed | abs)
    if import_formats.option("cl_negative_length", CL_NEGATIVE_LENGTH_MODE) == "abs":
        return abs(raw), raw
    return 0.0, raw


def _business_mm(v) -> float:
    from ..plugins.legacy_project import _f
    x = _f(v, CL_DEFAULTS["business_min"] / 1000)
    mm = x if x >= BUSINESS_M_THRESHOLD else x * 1000
    return max(0.0, min(mm, 20000.0))


def from_project_xml(oe, goods: dict, warnings: list[str]) -> Operation:
    """`oe` — `<operation typeId="CL">`, `goods` — {id: <good>}. Detallar (`<part id>`) chaqiruvchi tomonidan biriktiriladi."""
    from ..plugins.legacy_project import _b, _f, _fill_pct, _i, _opt_len
    me = oe.find("material")
    band = goods.get(me.get("id")) if me is not None else None
    tool = goods.get(oe.get("tool1") or "")

    def tg(k, d=None):
        return tool.get(k) if tool is not None and tool.get(k) is not None else d

    def bg(k, d=None):
        return band.get(k) if band is not None and band.get(k) is not None else d

    width = _f(bg("w"), 0) or _f(oe.get("w"), 0) or CL_DEFAULTS["width"]
    thick = _f(bg("t"), 0) or _f(oe.get("t"), 0) or CL_DEFAULTS["thickness"]
    if thick > 1000:
        thick = 1000.0
    trim = oe.get("cTrimW") if oe.get("cTrimW") is not None else oe.get("cTrimL")
    base_i = _i(oe.get("cCostType"), 0)
    rnd = str(_i(oe.get("cCostByItemRound"), 11))
    cl = CLParams(
        width=min(max(width, 0.01), 20000.0), thickness=thick,
        kerf=max(0.01, _f(tg("swSawthick"), CL_DEFAULTS["kerf"])) if _f(tg("swSawthick"), 0) > 0 else CL_DEFAULTS["kerf"],
        trim=max(0.0, _f(trim, CL_DEFAULTS["trim"])), end_offset=_opt_len(oe.get("cTrimEW")),
        pack_height=_f(tg("swPackageHeight"), CL_DEFAULTS["pack_height"]),
        fill_packet=_fill_pct(oe.get("cFillRep")),
        waste_min=_f(oe.get("cMinDimRegWaste1"), CL_DEFAULTS["waste_min"]),
        business_min=_business_mm(oe.get("cBusinessWaste")),
        waste_incl_trim=_b(oe.get("cTrimWaste") if oe.get("cTrimWaste") is not None else oe.get("cTrimWaster"), True),
        min_part_len=max(0.0, _f(oe.get("cMinDimDetail"), 0)),
        max_part_types_per_map=min(max(_i(oe.get("cMaxPartsOnPattern"), 0), 0), 10000),
        merge_parts=_b(oe.get("cCombiningParts"), False),
        group_parts=min(max(_i(oe.get("cGroupParts"), 0), 0), 1000000),
        save_drawings=_b(oe.get("cSaveDrawCut"), False),
        price=max(0.0, _f(bg("cost"), 0)), price_by_strip=_b(oe.get("cCostByItem"), False),
        strip_rounding=next((r for r in SheetRounding if r.value == rnd and rnd in ("11", "32", "33", "34")), SheetRounding.WHOLE),
        est_fill_percent=_fill_pct(oe.get("cCPF") if oe.get("cCPF") is not None else oe.get("cFillRep")),
        op_cost_base=CLCostBase(base_i) if 0 <= base_i <= 3 else CLCostBase.CUT_WITH_TRIM,
        op_price=max(0.0, _f(oe.get("cCostCut"), 0)),
    )
    sheets: list[StockSheet] = []
    if band is not None:
        for sp in band.findall("part"):
            if _b(sp.get("waste")):
                continue                       # oldingi kroydan qolgan qoldiq — natija emas
            qty = _i(sp.get("count"), 0)
            ln = _f(sp.get("l"), 0)
            if qty <= 0 or ln <= 0:
                continue
            sheets.append(StockSheet(length=min(ln, 20000.0), width=cl.width, qty=min(qty, 10000),
                                     description=(sp.get("description") or "")[:500]))
    sheets.sort(key=lambda s: s.qty)           # ustuvorlik: avval soni cheklanganlar, «cheksiz» (10000) oxirida (CS bilan bir xil)
    if not sheets:
        ln = _f(bg("l"), 0) or _f(oe.get("l"), 0) or CL_DEFAULTS["strip_length"]
        sheets = [StockSheet(length=min(ln, 20000.0), width=cl.width)]
    desc = oe.get("description") or ""
    op = Operation(type="CL", code=(band.get("code") or "") if band is not None else "",
                   name=(band.get("name") or "") if band is not None else "", cl=cl, sheets=sheets, description=desc,
                   print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
    if not op.name:
        op.name = oe.get("typeName") or "CL"
    return op
