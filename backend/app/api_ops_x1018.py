"""2026-10-18 · «Операции» jadvali amallari (joylashuv mosligi auditi D3 / D7). `main.py` da `api.include_router(ops_x1018_router)`.

POST /projects/{pid}/operations/{oid}/merge    — {ids: [...]}: «Объединить» oynasida belgilangan bir xil turdagi operatsiyalar
                                                 joriy (oid) operatsiyaga qo'shiladi (detallar, listlar; kromkada — havolalar).
                                                 Oyna tanlovsiz birlashtirmaydi: faqat ro'yxatdagi id lar. Bitta tarix qadami.
POST /projects/{pid}/operations/{oid}/convert  — {to: "CN"}: «Конвертировать в „Нестинговый раскрой“» — CS operatsiya CN ga
                                                 aylanadi (id, detallar, listlar saqlanadi; qalinlik va narx ko'chadi; kroy natijasi o'chadi).
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import store
from .i18n import MSG, _
from .models import OpType, Operation, Project

router = APIRouter(tags=["operatsiyalar"])

MSG.update({
    "merge_type": ("Эту операцию нельзя объединять (доступно для CS, CL, CN, EL)",
                   "Bu operatsiyani birlashtirib bo'lmaydi (CS, CL, CN, EL uchun)"),
    "merge_type_mismatch": ("Объединять можно только операции одного типа ({t})", "Faqat bir turdagi ({t}) operatsiyalar birlashtiriladi"),
    "merge_self": ("Операция не может быть объединена сама с собой", "Operatsiya o'zi bilan birlashtirilmaydi"),
    "convert_type": ("В «Нестинговый раскрой» конвертируется только операция (CS) Листовой раскрой",
                     "«Нестинговый раскрой» ga faqat (CS) Листовой раскрой operatsiyasi aylantiriladi"),
})

MERGEABLE = (OpType.CS, OpType.CL, OpType.CN, OpType.EL)


class MergeIn(BaseModel):
    ids: list[str] = Field(default_factory=list, max_length=500)


class ConvertIn(BaseModel):
    to: Literal["CN"] = "CN"


def _find(p: Project, oid: str) -> Operation:
    op = next((o for o in p.operations if o.id == oid), None)
    if op is None:
        raise HTTPException(404, _("op_not_found"))
    return op


def merge_into(p: Project, tgt: Operation, ids: list[str]) -> int:
    """`ids` dagi operatsiyalarni `tgt` ga qo'shish (loyiha ustida, saqlamasdan); qo'shilganlar soni qaytadi."""
    from .main import _EL_SIZE_FIELDS, _invalidate, _invalidate_where, _merge_sheets, _uses_edge   # kechiktirilgan import
    if tgt.type not in MERGEABLE:
        raise HTTPException(400, _("merge_type"))
    want = list(dict.fromkeys(ids))                       # takrorlar bir marta
    if tgt.id in want:
        raise HTTPException(400, _("merge_self"))
    srcs = [_find(p, i) for i in want]
    for o in srcs:
        if o.type != tgt.type:
            raise HTTPException(400, _("merge_type_mismatch", t=tgt.type.value))
    order = {o.id: i for i, o in enumerate(p.operations)}
    srcs.sort(key=lambda o: order[o.id])                  # loyihadagi tartibda (detallar tartibi bashorat qilinadigan)
    remap: dict[str, str] = {}
    for o in srcs:
        if o.type != OpType.EL:
            _invalidate(o)                                # olib tashlanadigan natija omborga yozilgan bo'lsa — bekor
            tgt.parts.extend(o.parts)
            _merge_sheets(tgt, o)
            _invalidate(tgt)
        elif o.el and tgt.el and any(getattr(o.el, f) != getattr(tgt.el, f) for f in _EL_SIZE_FIELDS):
            oid = o.id                                    # kromka qalinligi boshqa — shu kromkali detallar o'lchami o'zgaradi
            _invalidate_where(p, lambda pt, oid=oid: _uses_edge(pt, oid))
        remap[o.id] = tgt.id
    if not remap:
        return 0
    p.operations = [o for o in p.operations if o.id not in remap]
    for o in p.operations:                                # olib tashlangan kromka operatsiyalariga havolalar
        for pt in o.parts:
            for side in ("top", "bottom", "left", "right"):
                ref = getattr(pt, f"edge_{side}")
                if ref.op_id in remap:
                    ref.op_id = remap[ref.op_id]
    return len(remap)


@router.post("/projects/{pid}/operations/{oid}/merge")
def merge_operations(pid: str, oid: str, body: MergeIn):
    with store.editing(pid, skip_unchanged=True) as p:
        merge_into(p, _find(p, oid), body.ids)
    return p


def convert_to_cn(op: Operation) -> None:
    """CS → CN: id, detallar, listlar saqlanadi; CS material parametrlaridan qalinlik / narx / narx usuli ko'chadi."""
    from .main import _invalidate                          # kechiktirilgan import
    from .services import cn_calc, settings
    if op.type != OpType.CS:
        raise HTTPException(400, _("convert_type"))
    _invalidate(op)
    cn = cn_calc.new_cn_params(settings.get_default("cn_defaults"))
    m = op.cs_material
    if m is not None:
        cn.thickness = m.thickness
        cn.price = m.price
        cn.cost_by_sheets = m.cost_by_sheets
        cn.sheet_rounding = m.sheet_rounding
        cn.remnant_min_side1, cn.remnant_min_side2, cn.remnant_min_area = m.remnant_min_side1, m.remnant_min_side2, m.remnant_min_area
    op.type = OpType.CN
    op.cn = cn
    op.cs_material = None
    op.cs_cut = None


@router.post("/projects/{pid}/operations/{oid}/convert")
def convert_operation(pid: str, oid: str, body: ConvertIn = ConvertIn()):
    with store.editing(pid) as p:
        convert_to_cn(_find(p, oid))
    return p
