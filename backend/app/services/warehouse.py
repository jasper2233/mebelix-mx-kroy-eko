"""Qoldiqlar ombori (деловые остатки): kroy natijasini omborga «yozish» va bekor qilish.

commit  — (tasdiqdan keyin) 1) kroyda ishlatilgan ombor qoldiqlari hisobdan chiqariladi,
          2) yangi деловой qoldiqlar omborga qo'shiladi (xom o'lcham — list chetigacha).
rollback — natija o'zgarsa/o'chirilsa: qo'shilgan qoldiqlar o'chiriladi (hali ishlatilmagan bo'lsa),
          ishlatilganlari qaytariladi.
"""
from __future__ import annotations

import math
from collections import Counter

from ..db import RemnantRow, SessionLocal
from ..i18n import _
from ..models import Operation, OpType, Project


def _fin(v) -> float:
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return 0.0
    return f if math.isfinite(f) else 0.0


def row_dict(r: RemnantRow) -> dict:
    L, W = _fin(r.length), _fin(r.width)
    return dict(id=r.id, material_code=r.material_code or "", material_name=r.material_name or "",
                length=L, width=W, thickness=_fin(r.thickness), qty=r.qty,
                area_m2=round(L * W / 1e6, 3),
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


class WarehouseConflict(ValueError):
    """Omborda kroy ishlatgan qoldiq yetarli emas (boshqa loyiha ishlatib bo'lgan yoki o'chirilgan)."""


WH_FIELDS = ("remnants_saved", "saved_remnant_ids", "saved_remnant_qty", "consumed_remnants")


def detach_result(res) -> None:
    """Natijaning omborga bog'lanishini uzish (import/nusxa/eski versiya — ombor qatorlari boshqa natijaniki)."""
    if res is not None:
        res.remnants_saved = False
        res.saved_remnant_ids = []
        res.saved_remnant_qty = {}
        res.consumed_remnants = {}


def detach(op: Operation) -> None:
    detach_result(op.result)


def _same_remnant(r: RemnantRow, sh, key: str) -> bool:
    """Ombor qatori kroydagi qoldiq listi bilan bir xilmi (material va o'lcham)."""
    if (r.material_code or "") and key and (r.material_code or "").strip() != key:
        return False
    a = sorted((_fin(r.length), _fin(r.width)))
    b = sorted((float(sh.length), float(sh.width)))
    return abs(a[0] - b[0]) <= 0.5 and abs(a[1] - b[1]) <= 0.5


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
        need = consumed(op)
        rows = {rid: s.get(RemnantRow, rid, with_for_update=True) for rid in need}
        sheets = {sh.source_remnant_id: sh for sh in op.sheets if sh.source_remnant_id}
        key = material_key(op)
        for rid in need:              # qator boshqa qoldiq bo'lib qolgan (o'chirilib, raqam qayta berilgan)
            r, sh = rows[rid], sheets.get(rid)
            if r is not None and sh is not None and not _same_remnant(r, sh, key):
                rows[rid] = None
        short = [(rid, n, (rows[rid].qty or 0) if rows[rid] is not None else 0)
                 for rid, n in need.items() if rows[rid] is None or (rows[rid].qty or 0) < n]
        if short:
            raise WarehouseConflict(_("remnant_short", items=", ".join(
                _("remnant_short_item", id=rid, need=n, have=h) for rid, n, h in short)))
        for rid, n in need.items():
            r = rows[rid]
            r.qty = (r.qty or 0) - n
            used[str(rid)] = n
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
    res.saved_remnant_qty = {str(r["id"]): int(r["qty"] or 0) for r in out_added}
    res.consumed_remnants = used
    return dict(added=out_added, consumed=used)


def rollback(op: Operation) -> dict:
    """Omborga yozuvni bekor qilish. Qo'shilgan qoldiq boshqa loyihada ishlatilmagan bo'lsa — o'chiriladi;
    qisman ishlatilgan bo'lsa — faqat ishlatilmagan qismi hisobdan chiqariladi (qator saqlanadi, chunki
    boshqa loyiha unga bog'langan). Ishlatilgan ombor qoldiqlari qaytariladi."""
    res = op.result
    if not res or not res.remnants_saved:
        return dict(removed=[], restored={}, kept=[])
    removed, restored, kept = [], {}, []
    with SessionLocal() as s:
        for rid in res.saved_remnant_ids:
            r = s.get(RemnantRow, rid, with_for_update=True)
            if r is None:
                continue
            have = r.qty or 0
            added = int(res.saved_remnant_qty.get(str(rid), have))
            if have == added:
                s.delete(r)
                removed.append(rid)
            elif have > added:
                r.qty = have - added
                removed.append(rid)
            else:                       # bir qismi boshqa kroyda ishlatilgan
                r.qty = 0
                kept.append(rid)
        for rid, n in res.consumed_remnants.items():
            r = s.get(RemnantRow, int(rid), with_for_update=True)
            if r is not None:
                r.qty = (r.qty or 0) + n
                restored[rid] = n
        s.commit()
    detach(op)
    return dict(removed=removed, restored=restored, kept=kept)
