"""Qoldiq harakatlarini MES ga yuborish navbati (2026-10-24).

Har ombor harakati (`remnant_moves` jurnali) `sent_at` bo'sh holda yoziladi; `flush` ularni tartib bilan `remnant.move`
voqeasi sifatida MES webhook manziliga yuboradi (`MES_WEBHOOK_URL`, `MES_WEBHOOK_TOKEN` — services/mes.py). Yuborilmasa
(MES ishlamayapti) — navbatda qoladi va keyingi harakatda yoki `POST /api/mes/remnants/resend` bilan qayta yuboriladi: server
qayta ishga tushsa ham voqea yo'qolmaydi. Bir nechta jarayon bir vaqtda yuborsa — PostgreSQL `SKIP LOCKED` bir qatorni ikki marta
olmaydi. Shartnoma: docs/mebelix/MES_QOLDIQ_V1.md.
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime

from sqlalchemy import func, select

from .. import tenant
from ..db import IS_PG, RemnantMoveRow, RemnantRow, SessionLocal

log = logging.getLogger("mebelix.remnant_outbox")
_lock = threading.Lock()          # shu jarayonda bitta yuboruvchi (boshqa jarayonlar — PostgreSQL SKIP LOCKED)
_kicked = threading.Event()


def configured() -> bool:
    return bool(os.getenv("MES_WEBHOOK_URL"))


def flush(limit: int = 500) -> dict:
    """Navbatdagi harakatlarni yuborish. Qaytaradi: {configured, sent, queued (qolgani)}."""
    from . import mes, warehouse
    with _lock, tenant.system():
        with SessionLocal() as s:
            if not configured():
                left = s.scalar(select(func.count()).select_from(RemnantMoveRow).where(RemnantMoveRow.sent_at.is_(None))) or 0
                return dict(configured=False, sent=0, queued=int(left))
            st = select(RemnantMoveRow).where(RemnantMoveRow.sent_at.is_(None)).order_by(RemnantMoveRow.id).limit(limit)
            if IS_PG:
                st = st.with_for_update(skip_locked=True)
            rows = s.scalars(st).all()
            sent = 0
            for m in rows:
                r = s.get(RemnantRow, m.remnant_id) if m.remnant_id else None
                payload = dict(company_id=m.company_id, move=warehouse.move_dict(m),
                               remnant=warehouse.row_dict(r) if r is not None else None)
                res = mes.send_webhook("remnant.move", payload, attempts=1)
                if not res.get("sent"):
                    break                                  # tartib buzilmasin — keyingisi keyin
                m.sent_at = datetime.utcnow()
                sent += 1
            s.commit()
            left = s.scalar(select(func.count()).select_from(RemnantMoveRow).where(RemnantMoveRow.sent_at.is_(None))) or 0
    return dict(configured=True, sent=sent, queued=int(left))


def _run() -> None:
    try:
        while _kicked.is_set():
            _kicked.clear()
            flush()
    except Exception:  # noqa: BLE001
        log.exception("qoldiq harakatlarini MES ga yuborishda xato")


_thread: "threading.Thread | None" = None


def kick() -> None:
    """Fonda yuborish (MES manzili sozlangan bo'lsa; jarayonda bitta oqim — ketma-ket «kick» lar bitta yurishga qo'shiladi)."""
    global _thread
    if not configured():
        return
    _kicked.set()
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=_run, name="mx-remnant-outbox", daemon=True)
        _thread.start()
