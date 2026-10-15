"""SP (Обработка поверхности) API: sirt ishlovi hisobi — ishlov maydoni, material sarfi, narx va sirt ishlovi bor detallar jadvali
(«Детали» yorlig'i uchun). Parametrlar — umumiy `PATCH /projects/{pid}/operations/{oid}` (`{sp: {...}}`); yaratish —
`POST /projects/{pid}/operations {type: "SP"}`; standart — `PUT /settings/sp_defaults/default`; detalga biriktirish —
detal maydonlari `surface_face_op` / `surface_back_op` (`PATCH .../parts/{ptid}`)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import store
from .i18n import _
from .models import OpType
from .services import calc

router = APIRouter(tags=["sirt ishlovi (SP)"])


@router.get("/projects/{pid}/operations/{oid}/surface-usage")
def surface_usage(pid: str, oid: str):
    """Sirt ishlovi hisobi (calc.surface_usage): rows (detal, lits / orqa, soni, maydon), area_m2, material_m2, cost_*."""
    p = store.load(pid)
    op = store.op_of(p, oid)
    if op.type != OpType.SP:
        raise HTTPException(400, _("sp_only"))
    return calc.surface_usage(p, op)
