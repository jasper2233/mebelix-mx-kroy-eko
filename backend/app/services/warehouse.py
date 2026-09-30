"""Qoldiqlar ombori (деловые остатки): kroy natijasini omborga «yozish» va bekor qilish.

commit  — (tasdiqdan keyin) 1) kroyda ishlatilgan ombor qoldiqlari hisobdan chiqariladi,
          2) yangi деловой qoldiqlar omborga qo'shiladi (xom o'lcham — list chetigacha).
rollback — natija o'zgarsa/o'chirilsa: qo'shilgan qoldiqlar o'chiriladi (hali ishlatilmagan bo'lsa),
          ishlatilganlari qaytariladi.
"""
from __future__ import annotations

from collections import Counter

from ..db import RemnantRow, SessionLocal
from ..i18n import _
from ..models import Operation, OpType, Project


def row_dict(r: RemnantRow) -> dict:
    return dict(id=r.id, material_code=r.material_code or "", material_name=r.material_name or "",
                length=r.length, width=r.width, thickness=r.thickness, qty=r.qty,
                area_m2=round((r.length or 0) * (r.width or 0) / 1e6, 3),
                source_project=r.source_project, source_number=r.source_number, source_op=r.source_op,
                note=r.note or "", created_at=r.created_at.isoformat() if r.created_at else None)


def material_key(op: Operation) -> str:
    return (op.code or op.name or "").strip()


def business_remnants(op: Operation) -> list[dict]:
    """Natijadagi деловой qoldiqlar (nusxalar bilan), o'lcham bo'yicha guruhlangan."""
    res = op.result
    if not res:
        return []
    cnt: Counter = Counter()
    for m in res.maps:
        for o in m.offcuts:
            if o.kind == "remnant" and o.business:
                L = o.raw_length or o.length
                W = o.raw_width or o.width
                cnt[(round(max(L, W), 1), round(min(L, W), 1))] += m.copies
    return [dict(length=L, width=W, qty=n) for (L, W), n in sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1])]


def consumed(op: Operation) -> dict[int, int]:
    """Kroyda ishlatilgan ombor qoldiqlari: remnant id → soni."""
    out: dict[int, int] = {}
    for sh in op.sheets:
        if sh.source_remnant_id and sh.used_qty:
            out[sh.source_remnant_id] = out.get(sh.source_remnant_id, 0) + sh.used_qty
    return out


def commit(project: Project, op: Operation) -> dict:
    assert op.type == OpType.CS
    res = op.result
    if not res or not res.maps:
        raise ValueError(_("no_result"))
    if res.remnants_saved:
        raise ValueError(_("remnants_already"))
    thick = op.cs_material.thickness if op.cs_material else 0
    added, used = [], {}
    with SessionLocal() as s:
        for rid, n in consumed(op).items():
            r = s.get(RemnantRow, rid)
            if r is None:
                continue
            take = min(n, r.qty or 0)
            r.qty = (r.qty or 0) - take
            used[str(rid)] = take
        for rem in business_remnants(op):
            r = RemnantRow(material_code=material_key(op), material_name=op.name, length=rem["length"],
                           width=rem["width"], thickness=thick, qty=rem["qty"], source_project=project.id,
                           source_number=project.number, source_op=op.id,
                           note=f"№{project.number} {project.name}"[:500])
            s.add(r)
            s.flush()
            added.append(r)
        s.commit()
        out_added = [row_dict(r) for r in added]
    res.remnants_saved = True
    res.saved_remnant_ids = [r["id"] for r in out_added]
    res.consumed_remnants = used
    return dict(added=out_added, consumed=used)


def rollback(op: Operation) -> dict:
    res = op.result
    if not res or not res.remnants_saved:
        return dict(removed=[], restored={})
    removed, restored = [], {}
    with SessionLocal() as s:
        for rid in res.saved_remnant_ids:
            r = s.get(RemnantRow, rid)
            if r is not None:
                s.delete(r)
                removed.append(rid)
        for rid, n in res.consumed_remnants.items():
            r = s.get(RemnantRow, int(rid))
            if r is not None:
                r.qty = (r.qty or 0) + n
                restored[rid] = n
        s.commit()
    res.remnants_saved = False
    res.saved_remnant_ids = []
    res.consumed_remnants = {}
    return dict(removed=removed, restored=restored)
