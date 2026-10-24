"""(CL) `.project` eksporti (W11): `Operation(type=CL)` → `<good tool.cutting>` + `<good band>` (+ polosa qatorlari `part`) +
`<operation typeId="CL">`. `services/project_export.py` (W10) shu funksiyalarni chaqiradi; `cl_import.py` ning teskarisi.

Manfiy uzunlik qoidasi: hisoblanmagan detal (`length = 0`, `src_length` bor) — xom manfiy qiymat (`l="-350"`) qaytariladi (Bazis belgisi).
`cBusinessWaste` formatda metrda (standart 1 m) — `business_min` (mm) / 1000 yoziladi. Kroy natijasi / statistika yozilmaydi."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models import CLParams, Operation, Part, Project, SizeMode
from .sizes import compute_sizes


def part_size_attrs(project: Project, op: Operation, pt: Part, dims: tuple[str, str], edges: dict) -> dict[str, str]:
    """CL detali o'lcham atributlari: eni = polosa eni (`cl.width`); hisoblanmagan detal — xom manfiy `src_length`."""
    from .project_export_xnc import num
    cl = op.cl or CLParams()
    w = num(cl.width)
    if pt.length <= 0 and pt.src_length is not None:
        v = num(pt.src_length)
        return {"l": v, "w": w, "dl": v, "dw": w, "jl": v, "jw": w, "cl": v, "cw": w}
    a = {dims[0]: num(pt.length), dims[1]: w}
    if pt.length > 0:
        s = compute_sizes(pt.model_copy(update={"width": cl.width}), project.size_mode, edges, 0)
        for kl, kw_, vals in (("l", "w", s.blank), ("dl", "dw", s.detail), ("jl", "jw", s.jointed), ("cl", "cw", s.saw)):
            if kl not in a and vals[0] >= 0 and vals[1] >= 0:
                a[kl], a[kw_] = num(round(vals[0], 4)), num(round(vals[1], 4))
    return a


def cl_operation(ex, root: ET.Element, op: Operation, mode: SizeMode) -> ET.Element:
    """`ex` — `project_export._Exporter`. Goods (asbob, material) `root` ga qo'shiladi, operatsiya elementi qaytariladi."""
    from .project_export import MODE_ID, _s
    from .project_export_xnc import boolean, num
    cl = op.cl or CLParams()
    tool_id, band_id = ex.nid(), ex.nid()
    ET.SubElement(root, "good", id=tool_id, typeId="tool.cutting", swSawthick=num(cl.kerf),
                  swSawthickDiv=num(cl.kerf_group if cl.kerf_group is not None else -1), swPackageHeight=num(cl.pack_height))
    first = next((s for s in op.sheets if not s.is_remnant and not s.source_remnant_id), op.sheets[0] if op.sheets else None)
    bg = ET.SubElement(root, "good", id=band_id, typeId="band", name=_s(op.name), w=num(cl.width), t=num(cl.thickness),
                       cost=num(cl.price))
    if op.code:
        bg.set("code", _s(op.code))
    if first is not None:
        bg.set("l", num(first.length))
    stock_ids: list[str] = []
    remn = 0
    for sh in op.sheets:
        sid = ex.nid()
        stock_ids.append(sid)
        a = {"id": sid, "count": str(sh.qty), "l": num(sh.length), "w": num(cl.width)}
        if sh.description:
            a["description"] = _s(sh.description)
        ET.SubElement(bg, "part", a)
        if sh.is_remnant or sh.source_remnant_id:
            remn += 1
    if remn:
        ex.warn("remnant_sheet", name=ex._opname(op), n=remn)
    a = {"id": ex.op_eid[op.id], "typeId": "CL", "tool1": tool_id, "cSizeMode": str(MODE_ID[mode]),
         "cTrimL": num(cl.trim), "cTrimW": num(cl.trim)}
    if cl.end_offset is not None:
        a["cTrimEW"] = num(cl.end_offset)
    a.update(cFillRep=num(cl.fill_packet / 100), cCPF=num(cl.est_fill_percent / 100), cCostType=str(int(cl.op_cost_base)),
             cCostCut=num(cl.op_price), cCostByItem=boolean(cl.price_by_strip),
             cCostByItemRound=str(int(cl.strip_rounding.value)), cMinDimRegWaste1=num(cl.waste_min),
             cBusinessWaste=num(round(cl.business_min / 1000, 4)), cTrimWaste=boolean(cl.waste_incl_trim),
             cMinDimDetail=num(cl.min_part_len), t=num(cl.thickness), w=num(cl.width))
    # W-parity: (CS) bilan bir xil nomli atributlar — faqat standartdan farq qilsa yoziladi (standart loyihada eksport o'zgarmaydi)
    if cl.max_part_types_per_map:
        a["cMaxPartsOnPattern"] = str(cl.max_part_types_per_map)
    if cl.merge_parts:
        a["cCombiningParts"] = boolean(True)
    if cl.group_parts:
        a["cGroupParts"] = str(cl.group_parts)
    if cl.save_drawings:
        a["cSaveDrawCut"] = boolean(True)
    if cl.machining_allowance:
        a["cAllowanceWorkpiece"] = num(cl.machining_allowance)
    if first is not None:
        a["l"] = num(first.length)
    a.update(printable=boolean(op.print), startNewPage=boolean(op.new_page))
    if op.description:
        a["description"] = _s(op.description)
    for k in ("cGroupParts", "cTrimLengthP", "cTrimCountP", "cPartCountP", "cPartsAmountP", "cWasteAmountP", "cMaterialAmountP",
              "costMaterial", "costOperation", "costTotal"):
        a.setdefault(k, "0")                              # onlayn eksportdagidek (o'z qiymati bo'lsa — o'zi qoladi)
    oe = ET.Element("operation", a)
    ET.SubElement(oe, "material", id=band_id)
    for pt in op.parts:
        ET.SubElement(oe, "part", id=ex.part_eid[id(pt)])
    for sid in stock_ids:
        ET.SubElement(oe, "part", id=sid)
    return oe
