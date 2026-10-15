"""W11 — (CL) Погонажный раскрой: qo'shimcha endpointlar. Asosiy kroy / tahrir / qoldiq amallari umumiy yo'llarda (main.py:
`optimize`, `edit`, `result`, `remnants/*`, `sheets/from-remnants`) operatsiya turiga qarab CL ga yo'naltiriladi."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import store
from .i18n import _
from .models import OpType
from .services import cl_calc, cl_editor

router = APIRouter()


def _cl(p, oid):
    op = store.op_of(p, oid)
    if op.type != OpType.CL:
        raise HTTPException(400, _("cl_only"))
    return op


@router.get("/projects/{pid}/operations/{oid}/cl-quantities", tags=["kroy"])
def cl_quantities(pid: str, oid: str):
    """«Количество материала» (m), polosalar, kesim uzunligi, narx: kroygacha — taxminiy (`estimated=true`, Σ detal × (2 − p/100)),
    kroydan keyin — natijadan. Hech narsa saqlanmaydi."""
    p = store.load(pid)
    return cl_calc.cl_cost(p, _cl(p, oid))


@router.get("/projects/{pid}/operations/{oid}/cl-edit/rev", tags=["kroy"])
def cl_edit_rev(pid: str, oid: str):
    """Natijaning joriy «izi» — CLE ochilganda olinadi, saqlashda `PUT …/result?base=` bilan yuboriladi (parallel tahrir → 409)."""
    p = store.load(pid)
    return dict(rev=cl_editor.result_rev(_cl(p, oid).result))
