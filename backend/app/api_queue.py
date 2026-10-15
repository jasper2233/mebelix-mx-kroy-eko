"""Buyurtmalar navbati va material bazasi tekshiruvi (2026-10-15). `main.py` da `api.include_router(queue_router)`.

GET /projects/{pid}/material-check  — loyiha kroy operatsiyalari uchun kerak / bazada / yetmaydi (katalog `stock`, qoldiqlar ombori)
GET /queue?statuses=0,1,2&limit=100 — navbat (raqam tartibida), `next` — material to'liq bor birinchi loyiha, `warnings` — bazani to'ldirish
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from . import store
from .services import material_check

router = APIRouter(tags=["navbat (material bazasi)"])


@router.get("/projects/{pid}/material-check")
def project_material_check(pid: str):
    return material_check.check_project(store.load(pid))


@router.get("/queue")
def order_queue(statuses: str = "0,1,2", folder_id: Optional[str] = None, all_folders: bool = True, limit: int = 100):
    sts = [int(x) for x in statuses.split(",") if x.strip().isdigit()] or [0, 1, 2]
    return material_check.queue(sts, folder_id, limit, all_folders)
