"""Abonent (korxona) konteksti — ko'p abonentli rejim (docs/mebelix/Y_MASSHTAB_ABONENTLAR.md).

Har so'rov / fon ishi qaysi korxonaga tegishli ekani shu yerda (ContextVar — so'rov ichidagi oqimlarga ham o'tadi).
PostgreSQL da har tranzaksiya boshida `app.cid` o'rnatiladi va Row-Level Security siyosati boshqa korxona qatorlarini bermaydi
(db.py `_tenant_guc`). SQLite (bitta korxona, testlar) — ajratish yo'q, hamma narsa 1-korxona.

Qoidalar:
  • so'rovda korxona tokendan olinadi (`auth.current_user` → middleware `bind_request`);
  • tokensiz mahalliy rejim, CLI, start-up — `DEFAULT_CID` (bizning ishxona, 1-korxona);
  • tizim ishlari (sxema migratsiyasi, ko'chirish, barcha korxonalarni aylanish) — `system()`: RLS chetlab o'tiladi.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from typing import Callable, Iterator, Optional

DEFAULT_CID = int(os.getenv("MEBELIX_DEFAULT_COMPANY", "1"))

_cid: ContextVar[Optional[int]] = ContextVar("mx_company_id", default=None)
_system: ContextVar[bool] = ContextVar("mx_tenant_system", default=False)


def current() -> int:
    """Joriy korxona (berilmagan bo'lsa — standart, ya'ni bizning ishxona)."""
    v = _cid.get()
    return DEFAULT_CID if v is None else v


def explicit() -> Optional[int]:
    """Aniq o'rnatilgan korxona (yoki None)."""
    return _cid.get()


def is_system() -> bool:
    return _system.get()


def set_current(cid: Optional[int]):
    """So'rov boshida o'rnatish (middleware). Qaytaradi: tiklash uchun token."""
    return _cid.set(cid)


def reset(token) -> None:
    _cid.reset(token)


@contextmanager
def use(cid: int) -> Iterator[None]:
    """Blok ichida berilgan korxona nomidan ishlash (fon ishi, CLI, korxona yaratish)."""
    t = _cid.set(int(cid))
    try:
        yield
    finally:
        _cid.reset(t)


@contextmanager
def system() -> Iterator[None]:
    """Tizim rejimi: RLS chetlab o'tiladi (sxema, ko'chirish, barcha korxonalar bo'yicha xizmat ishlari). Faqat ichki kod."""
    t = _system.set(True)
    try:
        yield
    finally:
        _system.reset(t)


def bind(fn: Callable, *args, **kwargs) -> Callable[[], object]:
    """Yangi `threading.Thread` uchun: joriy korxona konteksti bilan ishlaydigan funksiya (Thread kontekstni o'zi ko'chirmaydi)."""
    ctx = copy_context()
    return lambda: ctx.run(fn, *args, **kwargs)
