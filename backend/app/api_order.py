"""W14 — «Заказать» oqimi va «Очистить проект» endpointlari. `main.py` da `api.include_router(order_router)`.

GET  /projects/{pid}/order          — holat, ruxsat etilgan o'tishlar (rol bo'yicha), ogohlantirishlar, tarix
POST /projects/{pid}/order          — {status (standart 1 = «Заказан»), ready_date?, executor?, comment?} → loyiha;
                                      holat o'zgarsa MES ga mavjud `project.status` webhooki (fon vazifasi)
POST /projects/{pid}/actions/clear  — «Очистить проект» (taxminiy talqin, services/order_flow.clear_project): kroy natijalari
POST /projects/{pid}/mes-send       — kroy paketini MES buyurtmasiga yuboradi va loyihani qulflaydi (services/mes_send.py)
GET  /mes-url                       — brauzer ochadigan MES manzili (chap paneldagi «MES» tugmasi)
GET  /projects/{pid}/mes-orders     — MES dagi uzatilmagan buyurtmalar (MES siz ochilgan loyihaga biriktirish uchun)
POST /projects/{pid}/mes-check      — tasdiq oynasi: buyurtma, ogohlantirishlar (hech narsa yozilmaydi)
POST /projects/{pid}/mes-detach     — bog'lanish va qulfni olib tashlaydi (MES xizmat tokeni, navbat orqali)
POST /projects/{pid}/mes-reopen     — qulfni ochadi; MES ga `project.reopened`
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import store
from .auth import current_user
from .i18n import _
from .models import OrderStatus
from .services import mes, mes_send, order_flow

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


class MesTanlov(BaseModel):
    """MES siz ochilgan loyihada tanlangan buyurtma; bog'langan loyihada bo'sh."""
    order_id: Optional[int] = Field(None, ge=1)
    order_number: Optional[str] = Field(None, max_length=60)


def _token(authorization: Optional[str]) -> Optional[str]:
    return authorization.split(" ", 1)[1].strip() if authorization and " " in authorization else None


@router.get("/mes-url")
def mes_url_get():
    return {"url": mes_send.public_url()}


@router.get("/projects/{pid}/mes-orders")
def mes_orders_get(pid: str, q: str = Query("", max_length=100), authorization: Optional[str] = Header(None)):
    return mes_send.orders(store.load(pid), _token(authorization), q)


@router.post("/projects/{pid}/mes-check")
def mes_check_post(pid: str, inp: MesTanlov, authorization: Optional[str] = Header(None)):
    return mes_send.preview(store.load(pid), _token(authorization), inp.order_id, inp.order_number)


@router.post("/projects/{pid}/mes-send")
def mes_send_post(pid: str, inp: Optional[MesTanlov] = None, user: dict = Depends(current_user),
                  authorization: Optional[str] = Header(None)):
    """Tekshiradi, MES ga yuboradi (uzoq so'rov — loyiha qulfi ostida emas) va faqat qabul qilingach belgilaydi."""
    t = inp or MesTanlov()
    p = store.load(pid)
    mes_send.check(p)
    if not (t.order_id or (p.mes_order_ref or "").strip()):
        raise HTTPException(422, _("mes_send_no_order"))
    res = mes_send.send(p, _token(authorization), t.order_id, t.order_number)
    with store.editing(pid, history=False) as cur:
        mes_send.mark_sent(cur, version=int(res.get("version") or 1), order_number=str(res.get("order_number") or ""),
                           by=str(user.get("name") or ""), customer=str(res.get("mijoz") or ""))
    return {**res, "project": cur}


@router.post("/projects/{pid}/mes-detach")
def mes_detach_post(pid: str, user: dict = Depends(current_user)):
    """Buyurtma boshqa loyihaga o'tdi yoki kroyi tozalandi: loyiha yana mustaqil, qulf yo'q (navbat qayta yuborsa — xavfsiz)."""
    with store.editing(pid, history=False) as cur:
        cur.mes_order_ref = None
        cur.mes_sent = None
    return {"ok": True}


@router.post("/projects/{pid}/mes-reopen")
def mes_reopen_post(pid: str, background: BackgroundTasks, user: dict = Depends(current_user)):
    """Qulfni ochish — holatni orqaga qaytarish bilan bir xil huquq (admin, texnolog)."""
    if not order_flow.user_caps(user)["can_back"]:
        raise HTTPException(403, _("order_back_forbidden"))
    with store.editing(pid, history=False) as p:
        sent = p.mes_sent
        p.mes_sent = None
    if sent is not None:
        background.add_task(mes.send_webhook, "project.reopened",
                            dict(project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, version=sent.version,
                                 at=order_flow.now_iso(), by=str(user.get("name") or "")))
    return p
