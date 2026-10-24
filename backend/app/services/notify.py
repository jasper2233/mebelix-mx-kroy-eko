"""Jarayonlararo xabarlar (2-bosqich): PostgreSQL LISTEN / NOTIFY.

Server bir nechta jarayonda ishlaydi (`uvicorn --workers N` + hisob ishchilari `app.worker`). Sozlama bir jarayonda yozilsa, boshqa
jarayonlardagi keshlar (asboblar jadvali, kromka belgilari) darhol tozalanishi kerak — aks holda TTL tugaguncha (2–3 s) eski
jadval bilan hisoblanadi. `publish` — xabar yuborish (tranzaksiyadan tashqari, darhol); `start` — shu jarayonda tinglovchi oqim
(qayta ulanish bilan). SQLite (bitta jarayon) — hech narsa qilmaydi, mahalliy tozalash yetarli.

Kanallar: `mx_settings` (yuk — sozlama sohasi), `mx_jobs` (yangi hisob vazifasi — ishchilar uyg'onadi).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable

log = logging.getLogger("mebelix.notify")

SETTINGS = "mx_settings"
JOBS = "mx_jobs"

_handlers: dict[str, list[Callable[[str], None]]] = {}
_started = False
_start_lock = threading.Lock()


def _pg_url() -> str | None:
    from ..db import IS_PG, engine
    if not IS_PG:
        return None
    return engine.url.set(drivername="postgresql").render_as_string(hide_password=False)


def publish(channel: str, payload: str = "") -> None:
    from ..db import IS_PG, engine
    if not IS_PG:
        return
    from sqlalchemy import text
    try:
        with engine.connect() as c:
            c.execute(text("SELECT pg_notify(:ch, :p)"), {"ch": channel, "p": payload[:7000]})
            c.commit()
    except Exception:  # noqa: BLE001 — xabar yetmasa ham TTL keshni baribir yangilaydi
        log.exception("NOTIFY %s yuborilmadi", channel)


def on(channel: str, fn: Callable[[str], None]) -> None:
    """Kanalga ishlov beruvchi (tinglovchi oqimda chaqiriladi; tez bo'lsin)."""
    _handlers.setdefault(channel, [])
    if fn not in _handlers[channel]:
        _handlers[channel].append(fn)


def start() -> None:
    """Shu jarayonda tinglovchi oqimni ishga tushirish (bir marta). PostgreSQL bo'lmasa — hech narsa."""
    global _started
    url = _pg_url()
    if url is None:
        return
    with _start_lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_listen, args=(url,), name="mx-notify", daemon=True).start()


def _listen(url: str) -> None:
    import psycopg
    while True:
        try:
            with psycopg.connect(url, autocommit=True) as conn:
                for ch in _handlers:
                    conn.execute(f"LISTEN {ch}")
                # qayta ulanishda o'tkazib yuborilgan xabarlar bo'lishi mumkin — keshlar baribir tozalansin
                _dispatch_all()
                for n in conn.notifies():
                    for fn in _handlers.get(n.channel, ()):
                        try:
                            fn(n.payload)
                        except Exception:  # noqa: BLE001
                            log.exception("NOTIFY ishlov beruvchi xatosi (%s)", n.channel)
        except Exception:  # noqa: BLE001 — baza qayta ishga tushsa ham tinglash davom etadi
            log.warning("NOTIFY tinglovchi uzildi, qayta ulanadi", exc_info=True)
            time.sleep(2.0)


def _dispatch_all() -> None:
    for fn in _handlers.get(SETTINGS, ()):
        try:
            fn("")
        except Exception:  # noqa: BLE001
            pass
