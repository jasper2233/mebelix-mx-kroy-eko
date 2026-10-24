"""`.project` (XML) faylining element / atribut lug'ati va tekshiruvchisi (eksport o'zini-o'zi tekshirishi va testlar uchun).

Manba: formatning OCHIQ tavsifi (yordam sahifasi «Формат файлов проектов») + foydalanuvchining o'z fayllaridagi (945 ta
GibLab saqlagan + 303 ta Bazis eksporti) haqiqiy teg/atribut NOMLARI. Mijoz ma'lumoti jadvalga kirmagan, faqat nomlar.
XSD fayli topilmadi (`lxml` ham o'rnatilmagan) — shu sababli sxema bu yerda jadval ko'rinishida; tekshiruv
`validate_project_xml()`: teg/atribut lug'ati, atribut turlari (int / double / bool), id lar (noyob), havolalar
(`tool1`, `material`, `part`, `@operation#N`) va XNC `program` ichki XML i.

`strict=True` — bizning eksportimiz uchun (mantiqiy qiymat faqat `true`/`false`, id lar butun loyiha bo'ylab noyob);
`strict=False` — real fayllar uchun (`1`/`0` ham qabul qilinadi, id lar faqat tur ichida noyob bo'lishi shart).
"""
from __future__ import annotations

import math
import re
from typing import Iterable

try:  # xavfsiz XML o'qish
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET  # noqa: N817

# tur belgilari: i — butun, d — haqiqiy, b — mantiqiy, s — matn, l — long (epoch ms), r — `@operation#N` havolasi,
# x — ifoda (XNC; har qanday bo'sh bo'lmagan matn), id — butun id
_NUM = "d"


def _t(spec: str, t: str) -> dict[str, str]:
    return {k: t for k in spec.split()}


PROJECT_ATTRS = {**_t("name currency description project.uuid importBMV", "s"), **_t("date orderDate", "l"),
                 **_t("version", "i"), **_t("cost costMaterial costOperation", "d")}

# good (typeId bo'yicha)
_GOOD_COMMON = {**_t("id", "i"), **_t("typeId code name unit", "s")}
GOOD_ATTRS: dict[str, dict[str, str]] = {
    "product": {**_GOOD_COMMON, **_t("count", "i"), **_t("costMaterial costOperation cost", "d"),
                **_t("description phone1 phone2 program", "s"), **_t("orderDate date", "l")},
    "simple": {**_GOOD_COMMON, **_t("count cost", "d")},
    "band": {**_GOOD_COMMON, **_t("w t l count cost", "d")},
    "sheet": {**_GOOD_COMMON, **_t("l w t count cost", "d")},
    "tool.cutting": {**_GOOD_COMMON,
                     **_t("swSawthick swSawthickDiv swPackageHeight swMinSizeBand swMaxSizeBand swMaxLengthBand "
                          "swMinPruning", "d"), **_t("swMaxturns swSort swSortInBand", "i"),
                     **_t("swComplexBand swTrimIncludeSaw", "b")},
    "tool.edgeline": {**_GOOD_COMMON, **_t("elCost elRestSide elMinSize elWidthPreJoint", "d")},
}
GOOD_PATTERN_ATTRS = {"product": re.compile(r"^product\.[A-Za-z0-9_.\-]+$"),     # product.order, product.import ...
                      # (O) oddiy material: foydalanuvchi parametrlari «material.<nom>» (jadval «Настроенный Параметры» ustunlari)
                      "simple": re.compile(r"^material\.[\w.\-]+$")}
# mahsulot ichidagi detal: foydalanuvchi parametrlari «part.<nom>» (part.code / part.designation / part.position — o'z ma'nosida)
PART_PATTERN_ATTR = re.compile(r"^part\.[\w.\-]+$")

# detal (mahsulot ichida)
PRODUCT_PART_ATTRS = {
    **_t("id count usedCount minusCount groupInBlock groupInBlockMC groupInBlockMaxC", "i"),
    **_t("l w dl dw jl jw cl cw allowanceT allowanceB allowanceL allowanceR", "d"),
    **_t("name description code part.code part.designation part.position eltMat elbMat ellMat elrMat", "s"),
    **_t("txt grts grbs grls grrs", "b"), **_t("elt elb ell elr grt grb grl grr", "r"),
}
# list / qoldiq (sheet / band ichida)
STOCK_PART_ATTRS = {
    **_t("id count usedCount sheetId", "i"), **_t("l w rl rw cTrimL cTrimW cTrimEL cTrimEW", "d"),
    **_t("waste business", "b"), **_t("description", "s"),
}

_OP_COMMON = {**_t("id owner", "i"), **_t("typeId typeName description code", "s"),
              **_t("costOperation costMaterial costTotal", "d"), **_t("printable startNewPage", "b")}
_CS_STATS = ("cFilling cBusinessWasteAmount cTrimLength cTrimLengthP cPartAmount cPartsAmountP cPartAmountP cWasteAmount "
             "cWasteAmountP cMaterialAmount cMaterialAmountP")
OP_ATTRS: dict[str, dict[str, str]] = {
    "CS": {**_OP_COMMON, **_t("tool1 csDirectCut cCostType cCostByItemRound cSizeMode cMaxPartsOnPattern cGroupParts "
                              "cSortPatterns cCountPackets cTrimCount cTrimCountP cPartCount cPartCountP cWasteCount "
                              "cMaterialCount", "i"),
           **_t("cTrimL cTrimW cTrimEL cTrimEW cFillRep cAllowanceWorkpiece cCostCut cCPF cMinDimRegWaste1 "
                "cMinDimRegWaste2 cBusinessWaste cMinDimDetail l w t " + _CS_STATS, "d"),
           **_t("csTexture cCostByItem cTrimWaste cTrimWaster cSaveDrawCut cCombiningParts cPrefLargePacket", "b"),
           **_t("data draw patternComments cutLength cutCount", "s")},       # cutLength / cutCount: «0=64.592;1=64.592;»
    "CL": {**_OP_COMMON, **_t("tool1 cCostType cCostByItemRound cSizeMode cMaxPartsOnPattern cGroupParts cSortPatterns "
                              "cCountPackets cTrimCountP cPartCount cPartCountP cWasteCount cMaterialCount", "i"),
           **_t("cTrimL cTrimW cTrimEW cFillRep cAllowanceWorkpiece cCostCut cCPF cMinDimRegWaste1 cMinDimRegWaste2 "
                "cBusinessWaste cMinDimDetail l w t cFilling cBusinessWasteAmount cTrimLengthP cPartAmount "
                "cPartsAmountP cWasteAmount cWasteAmountP cMaterialAmount cMaterialAmountP", "d"),
           **_t("cCostByItem cTrimWaste cSaveDrawCut cCombiningParts cPrefLargePacket", "b"),
           **_t("data draw patternComments", "s")},
    "EL": {**_OP_COMMON, **_t("tool1 elRoundMat elRoundLength elLineMark", "i"),
           **_t("elLength elWastePRC elMinDimDetail w t", "d"), **_t("elCalcMat elPreMillingEqual", "b"),
           **_t("elSymbol elColor", "s")},
    "SP": {**_OP_COMMON, **_t("spSizeMode", "i"), **_t("spWastePRC spRestSide spCost", "d"), **_t("spCalcMat", "b")},
    "GR": {**_OP_COMMON, **_t("grWidth grDepth grOffset grSawthick grCuttingLength grCost", "d"),
           **_t("grOffsetIncl", "b")},
    "XNC": {**_OP_COMMON, **_t("count turn countBore", "i"),
            **_t("priceBore costBore priceMill countMill costMill priceCut countCut costCut price cost", "d"),
            **_t("side mirHor mirVert bySizeDetail", "b"), **_t("program", "s")},
    "LB": {**_OP_COMMON, **_t("columns rows border source printMode", "i"), **_t("gap", "d"),
           **_t("margin printParts printWastes partEach partONZ partSelected wasteEach productEach productONZ", "b"),
           **_t("fields data program", "s")},
    "O": {**_OP_COMMON},
}
MATERIAL_ATTRS = {**_t("id", "i"), **_t("count", "d"), **_t("used", "s")}
PRODUCT_OP_REF_ATTRS = {**_t("id", "i")}          # mahsulot ichidagi `<operation id="N"/>` — operatsiya egasi (O)
OP_PART_ATTRS = {**_t("id", "i")}

# XNC dasturi (`program` atributidagi ichki XML)
_X = "x"
_BASE = {"comment": "s", "enable": "b"}
XNC_PROGRAM_ATTRS = _t("dx dy dz", "d")
XNC_TAGS: dict[str, dict[str, str]] = {
    "tool": {**_BASE, "name": "s", "d": _X},
    "var": {"comment": "s", "name": "s", "type": "s", "expr": _X, "enable": "b"},
    "bf": {**_BASE, "name": "s", **_t("x y dp ac as", _X), "av": _X},
    "bl": {**_BASE, "name": "s", **_t("y z dp ac as ver", _X), "m": "b", "av": _X},
    "br": {**_BASE, "name": "s", **_t("y z dp ac as ver", _X), "m": "b", "av": _X},
    "bt": {**_BASE, "name": "s", **_t("x z dp ac as ver", _X), "m": "b", "av": _X},
    "bb": {**_BASE, "name": "s", **_t("x z dp ac as ver", _X), "m": "b", "av": _X},
    "ms": {**_BASE, "name": "s", **_t("x y dp sdp sxy", _X), **_t("c in out", "i")},
    "ml": {**_BASE, **_t("x y dp", _X)},
    "ma": {**_BASE, **_t("x y dp r", _X), "dir": "b"},
    "mac": {**_BASE, **_t("x y cx cy dp", _X), "dir": "b"},
    "gr": {**_BASE, "name": "s", **_t("x1 y1 x2 y2 t dp", _X), **_t("c p", "i")},
    "xy": {**_BASE, **_t("x y", _X)},
}

_OP_REF = re.compile(r"^@operation#(\d+)$")
_INT = re.compile(r"^-?\d+$")
_NAME_OK = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def _check_value(kind: str, v: str, strict: bool) -> bool:
    if kind in ("s", "x"):
        return kind == "s" or v.strip() != ""
    if kind in ("i", "l"):
        if _INT.match(v):
            return True
        return not strict and _is_float(v)            # real fayllarda «1.0» kabi butun sonlar uchraydi
    if kind == "d":
        return _is_float(v)
    if kind == "b":
        return v in ("true", "false") if strict else v.lower() in ("true", "false", "1", "0")
    if kind == "r":
        return bool(_OP_REF.match(v))
    return True


def _is_float(v: str) -> bool:
    try:
        return math.isfinite(float(v))
    except ValueError:
        return False


def _vocab_key_good(e) -> str:
    return f"good[{e.get('typeId')}]"


def vocabulary(xml: bytes | str) -> set[tuple[str, str]]:
    """Faylning (element, atribut) to'plami; element kaliti: `project`, `good[typeId]`, `operation[typeId]`,
    `part@good[typeId]`, `part@operation[typeId]`, `material`, `xnc.program`, `xnc.<teg>`. Bo'sh atributsiz element ham
    `(kalit, "")` sifatida hisoblanadi (element to'plami uchun)."""
    root = ET.fromstring(xml)
    out: set[tuple[str, str]] = set()

    def add(key: str, e) -> None:
        out.add((key, ""))
        for a in e.attrib:
            out.add((key, a))

    add("project", root)
    for g in root.findall("good"):
        k = _vocab_key_good(g)
        add(k, g)
        for p in g.findall("part"):
            add(f"part@{k}", p)
        for r in g.findall("operation"):
            add(f"operation@{k}", r)
    for op in root.findall("operation"):
        k = f"operation[{op.get('typeId')}]"
        add(k, op)
        for ch in op:
            add(f"part@{k}" if ch.tag == "part" else ch.tag, ch)
        if op.get("typeId") == "XNC" and op.get("program"):
            try:
                pr = ET.fromstring(op.get("program").encode("utf-8"))
            except Exception:  # noqa: BLE001
                continue
            add("xnc.program", pr)
            for c in pr:
                add(f"xnc.{c.tag}", c)
    return out


def schema_vocabulary() -> set[tuple[str, str]]:
    """Sxema bo'yicha ruxsat etilgan (element, atribut) to'plami (`vocabulary` bilan bir xil kalitlar)."""
    out: set[tuple[str, str]] = {("project", "")}
    out |= {("project", a) for a in PROJECT_ATTRS}
    for t, attrs in GOOD_ATTRS.items():
        out |= {(f"good[{t}]", ""), *((f"good[{t}]", a) for a in attrs)}
    for t in ("product", "sheet", "band"):
        attrs = PRODUCT_PART_ATTRS if t == "product" else STOCK_PART_ATTRS
        out |= {(f"part@good[{t}]", ""), *((f"part@good[{t}]", a) for a in attrs)}
    for t, attrs in OP_ATTRS.items():
        out |= {(f"operation[{t}]", ""), *((f"operation[{t}]", a) for a in attrs)}
        out |= {(f"part@operation[{t}]", ""), (f"part@operation[{t}]", "id")}
    out |= {("material", ""), *(("material", a) for a in MATERIAL_ATTRS)}
    out |= {("operation@good[product]", ""), *(("operation@good[product]", a) for a in PRODUCT_OP_REF_ATTRS)}
    out |= {("xnc.program", ""), *(("xnc.program", a) for a in XNC_PROGRAM_ATTRS)}
    for tag, attrs in XNC_TAGS.items():
        out |= {(f"xnc.{tag}", ""), *((f"xnc.{tag}", a) for a in attrs)}
    return out


def _is_pattern_attr(key: str, attr: str) -> bool:
    if key == "part@good[product]":
        return bool(PART_PATTERN_ATTR.match(attr))
    kind = key[5:-1] if key.startswith("good[") else ""
    pat = GOOD_PATTERN_ATTRS.get(kind)
    return bool(pat and pat.match(attr))


def unknown_vocabulary(found: Iterable[tuple[str, str]]) -> set[tuple[str, str]]:
    """`found` ichidan sxemada yo'q (element, atribut) juftlari (`product.*` kabi naqshli atributlar hisobga olinadi)."""
    allowed = schema_vocabulary()
    return {(k, a) for k, a in found if (k, a) not in allowed and not _is_pattern_attr(k, a)}


# ───────────────────────── Tekshiruvchi ─────────────────────────
def _attrs_ok(key: str, e, spec: dict[str, str], errs: list[str], strict: bool, pattern=None) -> None:
    for a, v in e.attrib.items():
        kind = spec.get(a)
        if kind is None:
            if pattern is not None and pattern.match(a):
                continue
            errs.append(f"{key}: noma'lum atribut «{a}»")
            continue
        if _NAME_OK.search(v):
            errs.append(f"{key}.{a}: XML da ruxsat etilmagan belgi")
        elif not _check_value(kind, v, strict):
            errs.append(f"{key}.{a}: noto'g'ri qiymat «{v[:40]}» (tur {kind})")


def _check_program(code: str, text: str, errs: list[str], strict: bool) -> None:
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        errs.append(f"XNC «{code}»: program XML emas ({e})")
        return
    if root.tag != "program":
        errs.append(f"XNC «{code}»: program ildizi <{root.tag}>")
        return
    _attrs_ok("xnc.program", root, XNC_PROGRAM_ATTRS, errs, strict)
    for a in ("dx", "dy", "dz"):
        if root.get(a) is None:
            errs.append(f"XNC «{code}»: program/@{a} yo'q")
    for c in root:
        spec = XNC_TAGS.get(c.tag)
        if spec is None:
            errs.append(f"XNC «{code}»: noma'lum teg <{c.tag}>")
            continue
        _attrs_ok(f"xnc.{c.tag}", c, spec, errs, strict)


def validate_project_xml(xml: bytes | str, *, strict: bool = True) -> list[str]:
    """Faylni sxemaga solishtiradi; xatolar ro'yxati (bo'sh = to'g'ri)."""
    errs: list[str] = []
    try:
        root = ET.fromstring(xml)
    except Exception as e:  # noqa: BLE001
        return [f"XML o'qilmadi: {e}"]
    if root.tag != "project":
        return [f"ildiz <{root.tag}>, <project> kerak"]
    _attrs_ok("project", root, PROJECT_ATTRS, errs, strict)

    good_ids: dict[str, str] = {}          # id → typeId
    part_ids: dict[str, str] = {}          # id → «product» | «stock»
    op_ids: dict[str, str] = {}            # id → typeId
    all_ids: dict[str, str] = {}
    prod_op_refs: list[tuple[str | None, str | None]] = []     # (mahsulot id, operatsiya id) — mahsulot ichidagi havolalar
    for ch in root:
        if ch.tag not in ("good", "operation"):
            errs.append(f"project ichida noma'lum teg <{ch.tag}>")

    def reg(table: dict, kind: str, i: str | None, what: str) -> None:
        if i is None or not _INT.match(i):
            errs.append(f"{what}: id yo'q yoki butun emas")
            return
        if i in table:
            errs.append(f"{what}: takroriy id {i}")
        table[i] = kind
        if strict:
            if i in all_ids and all_ids[i] != what:
                errs.append(f"{what}: id {i} butun loyihada noyob emas ({all_ids[i]} bilan to'qnashdi)")
            all_ids.setdefault(i, what)

    for g in root.findall("good"):
        t = g.get("typeId")
        spec = GOOD_ATTRS.get(t or "")
        if spec is None:
            errs.append(f"good: noma'lum typeId «{t}»")
            continue
        _attrs_ok(f"good[{t}]", g, spec, errs, strict, GOOD_PATTERN_ATTRS.get(t))
        reg(good_ids, t, g.get("id"), "good")
        for ch in g:
            if ch.tag == "operation" and t == "product":          # operatsiya egasi havolasi (O)
                _attrs_ok("operation@good[product]", ch, PRODUCT_OP_REF_ATTRS, errs, strict)
                prod_op_refs.append((g.get("id"), ch.get("id")))
                continue
            if ch.tag != "part" or t not in ("product", "sheet", "band"):
                errs.append(f"good[{t}] ichida ruxsat etilmagan teg <{ch.tag}>")
                continue
            pspec = PRODUCT_PART_ATTRS if t == "product" else STOCK_PART_ATTRS
            _attrs_ok(f"part@good[{t}]", ch, pspec, errs, strict, PART_PATTERN_ATTR if t == "product" else None)
            reg(part_ids, "product" if t == "product" else "stock", ch.get("id"), "part")
    ops = root.findall("operation")
    for o in ops:
        t = o.get("typeId")
        spec = OP_ATTRS.get(t or "")
        if spec is None:
            errs.append(f"operation: noma'lum typeId «{t}»")
            continue
        _attrs_ok(f"operation[{t}]", o, spec, errs, strict)
        reg(op_ids, t, o.get("id"), "operation")
    for gid, rid in prod_op_refs:
        if rid not in op_ids:
            errs.append(f"good[product] #{gid}: operation id {rid} topilmadi")
    for o in ops:
        t = o.get("typeId")
        if t not in OP_ATTRS:
            continue
        if t in ("CS", "CL"):
            tool = o.get("tool1")
            if tool is None or good_ids.get(tool) != "tool.cutting":
                errs.append(f"operation[{t}] #{o.get('id')}: tool1 «{tool}» tool.cutting emas")
        if t == "EL":
            tool = o.get("tool1")
            if tool is None or good_ids.get(tool) != "tool.edgeline":
                errs.append(f"operation[EL] #{o.get('id')}: tool1 «{tool}» tool.edgeline emas")
        if t == "XNC":
            prog = o.get("program")
            if not prog:
                errs.append(f"operation[XNC] #{o.get('id')}: program majburiy")
            else:
                _check_program(o.get("code") or o.get("id") or "?", prog, errs, strict)
        for ch in o:
            if ch.tag == "part":
                _attrs_ok(f"part@operation[{t}]", ch, OP_PART_ATTRS, errs, strict)
                if ch.get("id") not in part_ids:
                    errs.append(f"operation[{t}] #{o.get('id')}: part id {ch.get('id')} topilmadi")
            elif ch.tag == "material":
                _attrs_ok("material", ch, MATERIAL_ATTRS, errs, strict)
                if ch.get("id") not in good_ids:
                    errs.append(f"operation[{t}] #{o.get('id')}: material id {ch.get('id')} topilmadi")
            else:
                errs.append(f"operation[{t}] ichida ruxsat etilmagan teg <{ch.tag}>")
        if t in ("CS", "EL") and not o.findall("material"):
            errs.append(f"operation[{t}] #{o.get('id')}: <material> yo'q")
    # detal → operatsiya havolalari
    for g in root.findall("good"):
        if g.get("typeId") != "product":
            continue
        for p in g.findall("part"):
            for a in ("elt", "elb", "ell", "elr"):
                v = p.get(a)
                m = _OP_REF.match(v) if v else None
                if v and (not m or op_ids.get(m.group(1)) != "EL"):
                    errs.append(f"part #{p.get('id')}.{a}: «{v}» EL operatsiyasiga havola emas")
            for a in ("grt", "grb", "grl", "grr"):
                v = p.get(a)
                m = _OP_REF.match(v) if v else None
                if v and (not m or op_ids.get(m.group(1)) != "GR"):
                    errs.append(f"part #{p.get('id')}.{a}: «{v}» GR operatsiyasiga havola emas")
    # o'lchamlar: musbat (detalning o'lcham rejimiga mos atributi mavjud bo'lishi kerak — hech bo'lmasa bittasi)
    for g in root.findall("good"):
        if g.get("typeId") != "product":
            continue
        for p in g.findall("part"):
            if not any(p.get(a) is not None for a in ("l", "dl", "jl")) or not any(p.get(a) is not None
                                                                                   for a in ("w", "dw", "jw")):
                errs.append(f"part #{p.get('id')}: o'lcham atributlari (l/w yoki dl/dw yoki jl/jw) yo'q")
    return errs
