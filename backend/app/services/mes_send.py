"""«Отправить в MES»: tayyor kroy paketini MES buyurtmasiga yuborish va loyihani qulflash (MES_PAKET_V1 §2).

Yuborishdan oldin `check` (kroy bormi, hamma detal joylashganmi) — xato bo'lsa so'rov ketmaydi. MES paketni o'zi tekshiradi
(QR, stanok fayli, postda skan bo'lsa rad) va xodim tokeni bo'yicha huquq / kim yuborganini yozadi — shuning uchun so'rovga
xizmat tokenidan tashqari xodimning SSO tokeni ham qo'shiladi.

Yuborilgan loyiha qulf: tarkibni o'zgartiruvchi so'rovlar 409 (`order_flow.edit_guard`), arradan kelgan «karta bajarildi» —
ochiq. O'zgartirish uchun «Открыть заново»: MES ga `project.reopened` boradi, MES texnologga ogohlantirish ko'rsatadi.
Belgi tarixsiz saqlanadi: Ctrl+Z qulfni olib tashlamaydi.
"""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlsplit

from fastapi import HTTPException

from ..i18n import _
from ..models import MesSent, OpType, Project
from . import mes_package
from .order_flow import now_iso

SEND_TIMEOUT_S = 120.0
_CUT_TYPES = (OpType.CS, OpType.CN)


def _webhook() -> str:
    return (os.getenv("MES_WEBHOOK_URL") or "").strip()


def check(p: Project) -> None:
    """Yuborib bo'lmasa — 409 / 422 (sabab foydalanuvchi tilida)."""
    if not (p.mes_order_ref or "").strip():
        raise HTTPException(422, _("mes_send_no_order"))
    if p.mes_sent is not None:
        raise HTTPException(409, _("mes_send_already", v=p.mes_sent.version))
    ops = [o for o in p.operations if o.type in _CUT_TYPES and o.parts]
    if not ops:
        raise HTTPException(422, _("mes_send_no_parts"))
    no_cut = [o.name for o in ops if o.result is None]
    if no_cut:
        raise HTTPException(422, _("mes_send_no_cut", ops=", ".join(no_cut[:3])))
    left = sum(pt.left_qty for o in ops for pt in o.parts if pt.left_qty > 0)
    if left:
        raise HTTPException(422, _("mes_send_left", n=left))


def send(p: Project, user_token: Optional[str]) -> dict:
    """Paketni MES ga yuboradi; MES javobi (`order_id`, `redirect_url`, `version` …) + brauzer uchun `mes_url`."""
    import httpx

    url = _webhook()
    if not url:
        raise HTTPException(503, _("mes_send_no_url"))
    pkg = mes_package.build(p, mes_order_number=p.mes_order_ref, pp="enabled", files="inline")
    headers = {"Content-Type": "application/json"}
    token = os.getenv("MES_WEBHOOK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if user_token:
        headers["X-Mes-User-Token"] = user_token
    target = f"{url.rsplit('/', 1)[0]}/loyiha/{p.id}/paket"
    try:
        r = httpx.post(target, content=pkg.model_dump_json(), headers=headers, timeout=SEND_TIMEOUT_S)
    except httpx.HTTPError as e:
        raise HTTPException(502, _("mes_send_unreachable", e=type(e).__name__)) from e
    try:
        body = r.json()
    except ValueError:
        body = {}
    if r.status_code != 201:
        # MES sababi o'zbekcha va aniq (postda skan bor, QR mos emas, huquq yo'q) — o'zgartirmasdan ko'rsatiladi
        code = r.status_code if r.status_code in (401, 403, 404, 409, 422) else 502
        raise HTTPException(code, str(body.get("detail") or _("mes_send_unreachable", e=f"HTTP {r.status_code}")))
    origin = urlsplit(url)
    base = (os.getenv("MES_PUBLIC_URL") or f"{origin.scheme}://{origin.netloc}").rstrip("/")
    return {**body, "mes_url": f"{base}{body.get('redirect_url') or ''}"}


def mark_sent(p: Project, *, version: int, order_number: str, by: str) -> None:
    p.mes_sent = MesSent(version=version, at=now_iso(), by=by[:100], order_number=order_number[:60])
