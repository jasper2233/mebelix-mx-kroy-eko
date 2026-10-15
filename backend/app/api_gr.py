"""GR (Пазование) API: paz hisobi — uzunlik, o'tishlar, narx va pazli detallar jadvali («Детали» yorlig'i uchun)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import store
from .i18n import _
from .models import OpType
from .services import calc

router = APIRouter(tags=["pazlash"])


@router.get("/projects/{pid}/operations/{oid}/groove-usage")
def groove_usage(pid: str, oid: str):
    """Paz hisobi (calc.groove_usage): rows (10 ustunli jadval), usage (m), cut_length (m), passes, cost."""
    p = store.load(pid)
    op = store.op_of(p, oid)
    if op.type != OpType.GR:
        raise HTTPException(400, _("gr_only"))
    return calc.groove_usage(p, op)
