"""`.project` (XML) fayllaridan import — korxonaning mavjud loyihalari (Bazis eksporti) uchun.

Faqat foydalanuvchining o'z ma'lumotlari o'qiladi: mahsulotlar, detallar (o'lchamlar, soni, tekstura,
kromkalar), material/kromka parametrlari, kesish parametrlari va detallarga bog'langan CNC dasturlari
(teshik, freza, paz). Fayldagi ikkilik kroy natijasi (`data`) O'QILMAYDI — import qilingan loyiha
MebeliX optimizatori bilan qayta «Раскроить» qilinadi. Oldingi natijaning ochiq ko'rsatkichlari
(listlar soni, to'ldirish %) faqat solishtirish uchun operatsiya izohiga yoziladi.

Loyiha o'lcham rejimi — «детали (с кромкой)»: detal uzunligi/eni = tayyor detal o'lchami;
kromka qalinligi va prifugovka EL parametrlaridan olinadi (zagotovka/arra o'lchami qayta hisoblanadi).
"""
from __future__ import annotations

import re
from datetime import date
from uuid import uuid4

try:  # xavfsiz XML o'qish (XXE / «billion laughs» dan himoya)
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET  # noqa: N817

from ..models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, FirstCutDir, OpCostBase, OpType,
                      Operation, Part, Product, Project, SizeMode, StockSheet, StripSort, XncCommand,
                      XNCParams)
from . import register

CURRENCY = {"сум": "UZS", "сўм": "UZS", "so'm": "UZS", "uzs": "UZS", "руб": "RUB", "руб.": "RUB", "$": "USD",
            "usd": "USD", "eur": "EUR", "€": "EUR", "тенге": "KZT"}


def _f(v, d: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


def _i(v, d: int = 0) -> int:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return d


def _b(v, d: bool = False) -> bool:
    if v is None:
        return d
    return str(v).strip().lower() in ("true", "1", "yes", "да")


def _num_or_expr(v):
    """Son bo'lsa float, aks holda ifoda matni (masalan 'dz+3' yoki o'zgaruvchi nomi)."""
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return str(v)


def _date(v) -> date | None:
    if not v:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v) or re.match(r"(\d{2})\.(\d{2})\.(\d{4})", v)
    if not m:
        return None
    g = m.groups()
    try:
        return date(int(g[0]), int(g[1]), int(g[2])) if len(g[0]) == 4 else date(int(g[2]), int(g[1]), int(g[0]))
    except ValueError:
        return None


# ───────────────────────── CNC dasturi (XML) → XncCommand ─────────────────────────
DRILL = {"bf": "DrillFront", "bl": "DrillLeft", "br": "DrillRight", "bt": "DrillTop", "bb": "DrillBottom"}


def program_to_commands(xml_text: str) -> tuple[list[XncCommand], tuple[float, float, float] | None]:
    """Detal CNC dasturini MebeliX buyruqlar daraxtiga o'giradi. Qaytaradi: (buyruqlar, (dx, dy, dz))."""
    if not xml_text:
        return [], None
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except Exception:  # noqa: BLE001 — buzilgan dastur: tashlab ketiladi
        return [], None
    size = (_f(root.get("dx")), _f(root.get("dy")), _f(root.get("dz")))
    out: list[XncCommand] = []
    for el in root:
        a = el.attrib
        tag = el.tag
        p: dict = {}
        cmd = None
        comment = a.get("comment", "")
        if tag == "tool":
            cmd, p = "Tool", {"N": a.get("name", ""), "D": _f(a.get("d"))}
        elif tag == "var":
            cmd, p = "Var", {"name": a.get("name", ""), "value": _num_or_expr(a.get("expr", "0")),
                             "type": a.get("type", "double")}
        elif tag in DRILL:
            cmd = DRILL[tag]
            for k_src, k_dst in (("x", "X"), ("y", "Y"), ("z", "Z"), ("dp", "DP")):
                if a.get(k_src) is not None:
                    p[k_dst] = _num_or_expr(a.get(k_src))
            if a.get("name"):
                p["T"] = a["name"]
        elif tag == "ms":
            cmd = "MillStart"
            p = {"X": _num_or_expr(a.get("x", "0")), "Y": _num_or_expr(a.get("y", "0")),
                 "DP": _num_or_expr(a.get("dp", "0")), "T": a.get("name", ""), "C": _i(a.get("c"), 0)}
        elif tag == "ml":
            cmd, p = "MillLine", {"X": _num_or_expr(a.get("x", "0")), "Y": _num_or_expr(a.get("y", "0"))}
        elif tag == "mac":
            cmd, p = "MillArcCenter", {"X": _num_or_expr(a.get("x", "0")), "Y": _num_or_expr(a.get("y", "0")),
                                       "CX": _num_or_expr(a.get("cx", "0")), "CY": _num_or_expr(a.get("cy", "0")),
                                       "DIR": a.get("dir", "false")}
        elif tag == "gr":
            cmd = "Groove"
            p = {"X1": _num_or_expr(a.get("x1", "0")), "Y1": _num_or_expr(a.get("y1", "0")),
                 "X2": _num_or_expr(a.get("x2", "0")), "Y2": _num_or_expr(a.get("y2", "0")),
                 "DP": _num_or_expr(a.get("dp", "0")), "W": _num_or_expr(a.get("t", "4")), "T": a.get("name", "")}
        if cmd:
            p = {k: v for k, v in p.items() if v is not None}
            out.append(XncCommand(cmd=cmd, params=p, comment=comment))
    return out, size


# ───────────────────────── Asosiy import ─────────────────────────
@register(".project", "Loyiha fayli (.project, XML)")
def import_project(data: bytes, filename: str = "") -> tuple[Project, list[str]]:
    warnings: list[str] = []
    try:
        root = ET.fromstring(data)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Fayl o'qilmadi (XML emas yoki buzilgan): {e}") from e
    if root.tag != "project":
        raise ValueError("Bu .project loyiha fayli emas")

    goods = {g.get("id"): g for g in root.findall("good")}
    name = root.get("name") or re.sub(r"\.project$", "", filename.rsplit("/", 1)[-1], flags=re.I) or "Import"
    cur = (root.get("currency") or "UZS").strip()
    p = Project(name=name, currency=CURRENCY.get(cur.lower(), cur.upper()[:3] if cur.isascii() else "UZS"),
                size_mode=SizeMode.DETAIL, note=root.get("description", "") or "")
    d = _date(root.get("orderDate") or root.get("date"))
    if d:
        p.order_date = d

    # Mahsulotlar va detallar (fayldagi detal id → Part)
    src_parts: dict[str, Part] = {}
    src_part_el: dict[str, object] = {}
    for g in root.findall("good"):
        if g.get("typeId") != "product":
            continue
        prod = Product(code=g.get("code", "") or "", name=g.get("name") or "Mahsulot", qty=max(0, _i(g.get("count"), 1)))
        p.products.append(prod)
        for pe in g.iter("part"):
            pid = pe.get("id")
            L = _f(pe.get("dl")) or _f(pe.get("l"))
            W = _f(pe.get("dw")) or _f(pe.get("w"))
            desig = pe.get("part.designation") or ""
            code = pe.get("code") or pe.get("part.code") or ""
            part = Part(uid=0, product_id=prod.id, name=pe.get("name", "") or "", code=code,
                        description=desig if desig and desig != code else "",
                        length=L, width=W, qty=max(0, _i(pe.get("count"), 1)), grain=_b(pe.get("txt")))
            src_parts[pid] = part
            src_part_el[pid] = pe

    ops_by_src: dict[str, Operation] = {}
    edge_ops: dict[str, Operation] = {}      # '@operation#N' → EL operatsiya
    used_parts: set[str] = set()
    copies: dict[str, list[Part]] = {}       # fayldagi detal id → CS dagi Part(lar)
    ordered: list[Operation] = []
    xnc_links: list[tuple[str, Operation]] = []
    stats = {"CS": 0, "EL": 0, "XNC": 0, "skip": 0}

    for oe in root.findall("operation"):
        t = oe.get("typeId")
        oid = oe.get("id")
        if t == "EL":
            band = goods.get((oe.find("material").get("id") if oe.find("material") is not None else None) or "")
            tool = goods.get(oe.get("tool1") or "")
            el = ELParams(
                count_material=_b(oe.get("elCalcMat"), True),
                width=_f(oe.get("w"), _f(band.get("w") if band is not None else None, 19)),
                thickness=_f(oe.get("t"), _f(band.get("t") if band is not None else None, 0)),
                jointing_width=_f(tool.get("elWidthPreJoint") if tool is not None else None, 0),
                waste_percent=_f(oe.get("elWastePRC"), 0),
                overhang=_f(tool.get("elRestSide") if tool is not None else None, 20),
                min_glue_length=_f(tool.get("elMinSize") if tool is not None else None, 0),
                symbol=(oe.get("elSymbol") or "A")[:1],
                color=oe.get("elColor") or "#000000",
                marker_lines=max(1, min(3, _i(oe.get("elLineMark"), 1) or 1)),
                min_perp_side=_f(oe.get("elMinDimDetail"), 0),
                price=_f(band.get("cost") if band is not None else None, 0),
                op_price=_f(tool.get("elCost") if tool is not None else None, 0),
            )
            op = Operation(type=OpType.EL, code=(band.get("code") or "") if band is not None else "",
                           name=(band.get("name") or "Kromka") if band is not None else "Kromka", el=el,
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            edge_ops[f"@operation#{oid}"] = op
            ops_by_src[oid] = op
            ordered.append(op)
            stats["EL"] += 1
        elif t == "CS":
            me = oe.find("material")
            sheet = goods.get(me.get("id")) if me is not None else None
            tool = goods.get(oe.get("tool1") or "")
            tg = (lambda k, dflt=None: tool.get(k) if tool is not None else dflt)
            kerf_div = _f(tg("swSawthickDiv"), -1)
            mat = CSMaterialParams(
                thickness=_f(oe.get("t"), _f(sheet.get("t") if sheet is not None else None, 16)),
                price=_f(sheet.get("cost") if sheet is not None else None, 0),
                est_fill_percent=round(_f(oe.get("cFillRep"), 0.9) * 100, 2),
                cost_by_sheets=_i(oe.get("cCostByItem"), 1) != 0,
                op_cost_base=OpCostBase(min(3, max(0, _i(oe.get("cCostType"), 0)))),
                op_price=_f(oe.get("cCostCut"), 0),
                remnant_min_side1=_f(oe.get("cMinDimRegWaste1"), 1000),
                remnant_min_side2=_f(oe.get("cMinDimRegWaste2"), 500),
                remnant_min_area=_f(oe.get("cBusinessWaste"), 0.5),
                remnant_size_incl_trim=_b(oe.get("cTrimWaste"), True),
                min_part_size=_f(oe.get("cMinDimDetail"), 30),
            )
            cut = CSCutParams(
                kerf=_f(tg("swSawthick"), 3),
                kerf_group=kerf_div if kerf_div >= 0 else None,
                trim_length=_f(oe.get("cTrimL"), 2),
                trim_width=_f(oe.get("cTrimW"), 2),
                trim_includes_kerf=_b(tg("swTrimIncludeSaw"), False),
                first_cut=FirstCutDir(min(4, max(0, _i(oe.get("csDirectCut"), 0)))),
                use_grain=_b(oe.get("csTexture"), True),
                complex_strips=_b(tg("swComplexBand"), True),
                max_rotations=max(2, min(6, _i(tg("swMaxturns"), 6))),
                pack_height=_f(tg("swPackageHeight"), 40),
                fill_packet=round(_f(oe.get("cCPF"), 0.9) * 100, 2),
                max_part_types_per_map=_i(oe.get("cMaxPartsOnPattern"), 0),
                prefer_big_pack=_b(oe.get("cPrefLargePacket"), True),
                strip_sort=StripSort(min(3, max(0, _i(tg("swSort"), 0)))),
                in_strip_sort=StripSort(min(3, max(0, _i(tg("swSortInBand"), 3)))),
                min_strip_width=_f(tg("swMinSizeBand"), 0),
                max_strip_width=_f(tg("swMaxSizeBand"), 0),
                max_strip_length=_f(tg("swMaxLengthBand"), 10000) or 10000,
                min_trim_cut=_f(tg("swMinPruning"), 5),
                merge_parts=_b(oe.get("cCombiningParts"), False),
                save_drawings=_b(oe.get("cSaveDrawCut"), True),
                machining_allowance=_f(oe.get("cAllowanceWorkpiece"), 0),
            )
            sheets: list[StockSheet] = []
            if sheet is not None:
                for sp in sheet.findall("part"):
                    if _b(sp.get("waste")):
                        continue            # oldingi kroydan qolgan qoldiq — natija emas, o'tkazib yuboriladi
                    qty = _i(sp.get("count"), 0)
                    if qty <= 0 or _f(sp.get("l")) <= 0 or _f(sp.get("w")) <= 0:
                        continue
                    sheets.append(StockSheet(length=_f(sp.get("l")), width=_f(sp.get("w")), qty=qty))
            if not sheets:
                L, W = _f(oe.get("l"), 2750), _f(oe.get("w"), 1830)
                if sheet is not None and not oe.get("l"):
                    L, W = _f(sheet.get("l"), 2750), _f(sheet.get("w"), 1830)
                sheets = [StockSheet(length=L, width=W)]
            desc = ""
            if oe.get("cMaterialCount"):
                fill = _f(oe.get("cFilling"), 0) * 100
                desc = f"Import: oldingi kroy — {_i(oe.get('cMaterialCount'))} list" + (f", F {fill:.2f}%" if fill else "")
            op = Operation(type=OpType.CS, code=(sheet.get("code") or "") if sheet is not None else "",
                           name=(sheet.get("name") or "Material") if sheet is not None else "Material",
                           cs_material=mat, cs_cut=cut, sheets=sheets, description=desc,
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            for pr in oe.findall("part"):
                sp = pr.get("id")
                part = src_parts.get(sp)
                if part is None:
                    continue
                if sp in used_parts:
                    part = part.model_copy(deep=True, update={"id": uuid4().hex[:12]})
                    warnings.append(f"Detal {sp} bir nechta kroy operatsiyasida — nusxa olindi")
                used_parts.add(sp)
                copies.setdefault(sp, []).append(part)
                op.parts.append(part)
            ops_by_src[oid] = op
            ordered.append(op)
            stats["CS"] += 1
        elif t == "XNC":
            cmds, size = program_to_commands(oe.get("program") or "")
            side = (oe.get("side") or "true").strip().lower()
            turn = _i(oe.get("turn"), 0)
            rot = turn if turn in (0, 90, 180, 270) else {1: 90, 2: 180, 3: 270}.get(turn, 0)
            x = XNCParams(by_part_size=_b(oe.get("bySizeDetail"), True),
                          length=size[0] if size else 0, width=size[1] if size else 0,
                          thickness=size[2] if size else 16, qty=max(1, _i(oe.get("count"), 1)),
                          face_side=side in ("true", "1"), rotation=rot,
                          mirror_x=_b(oe.get("mirHor")), mirror_y=_b(oe.get("mirVert")),
                          program=cmds, drill_price=_f(oe.get("priceBore")), mill_price_m=_f(oe.get("priceMill")),
                          saw_price_m=_f(oe.get("priceCut")), extra_cost=_f(oe.get("price")))
            op = Operation(type=OpType.XNC, code=oe.get("code") or "", name=oe.get("typeName") or "", xnc=x,
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            ref = oe.find("part")
            if ref is not None:
                xnc_links.append((ref.get("id"), op))
            ops_by_src[oid] = op
            ordered.append(op)
            stats["XNC"] += 1
        else:
            stats["skip"] += 1

    # kromka havolalari va CNC bog'lanishlari
    for sp, part in src_parts.items():
        pe = src_part_el[sp]
        for side, attr in (("top", "elt"), ("bottom", "elb"), ("left", "ell"), ("right", "elr")):
            ref = pe.get(attr)
            if ref and ref in edge_ops:
                for target in copies.get(sp, [part]):
                    setattr(target, f"edge_{side}", EdgeRef(op_id=edge_ops[ref].id))
            elif ref:
                warnings.append(f"Detal {sp}: kromka {ref} topilmadi")
    for sp, op in xnc_links:
        targets = copies.get(sp, [])
        if targets:
            op.xnc_part_id = targets[0].id
            for pt in targets:            # detal bir nechta CS da bo'lsa — har nusxasiga
                if op.id not in pt.xnc_op_ids:
                    pt.xnc_op_ids.append(op.id)

    # detal ID (uid) — ketma-ket, operatsiyalar tartibida
    uid = 0
    for o in ordered:
        for pt in o.parts:
            uid += 1
            pt.uid = uid
    missing = [sp for sp in src_parts if sp not in used_parts]
    if missing:
        warnings.append(f"{len(missing)} ta detal hech bir kroy operatsiyasiga kirmagan (import qilinmadi)")
    if stats["skip"]:
        warnings.append(f"{stats['skip']} ta boshqa turdagi operatsiya o'tkazib yuborildi")
    p.operations = ordered
    return p, warnings
