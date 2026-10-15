"""W14 — «Заказать» oqimi va «Очистить проект» endpointlari. `main.py` da `api.include_router(order_router)`.

GET  /projects/{pid}/order          — holat, ruxsat etilgan o'tishlar (rol bo'yicha), ogohlantirishlar, tarix
POST /projects/{pid}/order          — {status (standart 1 = «Заказан»), ready_date?, executor?, comment?} → loyiha;
                                      holat o'zgarsa MES ga mavjud `project.status` webhooki (fon vazifasi)
POST /projects/{pid}/actions/clear  — «Очистить проект» (taxminiy talqin, services/order_flow.clear_project): kroy natijalari
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from . import store
from .auth import current_user
from .models import OrderStatus
from .services import mes, order_flow

router = APIRouter(tags=["buyurtma (W14)"])


class OrderIn(BaseModel):
    status: OrderStatus = OrderStatus.ORDERED         # «Заказать» tugmasi — «Заказан»
    ready_date: Optional[str] = None                  # «Утвержден» da belgilanadi (ORD-006); ixtiyoriy boshqa o'tishlarda ham
    executor: str = Field("", max_length=200)         # ichki matn — MES ga yuborilmaydi
    comment: str = Field("", max_length=1000)         # ichki matn — MES ga yuborilmaydi


@router.get("/projects/{pid}/order")
def order_get(pid: str, user: dict = Depends(current_user)):
    return order_flow.order_state(store.load(pid), user)


@router.post("/projects/{pid}/order")
def order_set(pid: str, inp: OrderIn, background: BackgroundTasks, user: dict = Depends(current_user)):
    ready = order_flow.check_date(inp.ready_date) if inp.ready_date else None          # 400 — saqlashdan oldin
    with store.editing(pid) as p:
        order_flow.check_transition(p, inp.status, user, ready_given=bool(ready))     # xato — saqlanmaydi
        old = p.status
        order_flow.apply_transition(p, inp.status, user, ready_date=ready, executor=inp.executor, comment=inp.comment)
    background.add_task(mes.send_webhook, "project.status", order_flow.webhook_payload(p, old))
    return p


@router.post("/projects/{pid}/actions/clear", tags=["operatsiyalar"])
def clear_project(pid: str):
    """«Очистить проект»: kroy natijalari va ulardan hisoblangan sanoqlar tozalanadi; detallar va operatsiyalar saqlanadi.
    Bitta tarix qadami — Ctrl+Z qaytaradi (omborga yozilgan qoldiqlar bekor qilinadi va undo ularni qayta yozmaydi).
    Tozalanadigan narsa bo'lmasa — bo'sh tarix qadami yozilmaydi."""
    with store.editing(pid, skip_unchanged=True) as p:
        order_flow.clear_project(p)
    return p
