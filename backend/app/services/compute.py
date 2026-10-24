"""Og'ir hisoblar navbati (2-bosqich, docs/mebelix/Y_MASSHTAB_ABONENTLAR.md).

Kroy (CS / CL / CN), «Раскроить все», variantlar va PDF hisobot — CPU ni uzoq band qiladi. Bitta veb-jarayonda bajarilsa o'sha
jarayondagi boshqa so'rovlar ham sekinlashadi (Python GIL). `MEBELIX_COMPUTE=queue` bo'lsa vazifa `jobs` jadvaliga yoziladi va
alohida hisob ishchilari (`python -m app.worker`) bajaradi; veb-jarayon faqat natijani kutadi (GIL bo'sh — boshqa so'rovlar tez).

API o'zgarmaydi: so'rov avvalgidek natija bilan qaytadi. Ishchi `CLAIM_WAIT` soniya ichida vazifani olmasa (ishchilar ishlamayapti) —
veb-jarayon vazifani qaytarib oladi va o'zi bajaradi (server hech qachon «osilib» qolmaydi). `inline` (standart: testlar, SQLite,
bitta jarayon) — hammasi avvalgidek shu jarayonda.

Vazifa — `@task("nom")` bilan ro'yxatdan o'tgan funksiya: kirish — JSON `payload`, chiqish — JSON ga aylanadigan qiymat. Korxona
(RLS) va so'rov tili ishchiga ham o'tadi. HTTPException → shu kod va matn bilan qaytadi.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Callable

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

log = logging.getLogger("mebelix.compute")

CLAIM_WAIT = float(os.getenv("MEBELIX_COMPUTE_CLAIM_WAIT", "3"))   # s: ishchi shuncha vaqtda olmasa — o'zimiz bajaramiz
STALE_SECONDS = 120                                                 # ishchi shuncha yurak urishisiz — qulagan
HEARTBEAT_EVERY = 5.0

_TASKS: dict[str, Callable[[dict], Any]] = {}


def mode() -> str:
    return (os.getenv("MEBELIX_COMPUTE", "inline") or "inline").strip().lower()


def queued() -> bool:
    return mode() == "queue"


def task(name: str):
    def deco(fn: Callable[[dict], Any]):
        _TASKS[name] = fn
        return fn
    return deco


def kinds() -> list[str]:
    return sorted(_TASKS)


def run_local(name: str, payload: dict) -> Any:
    """Vazifani shu jarayonda bajarish (JSON ko'rinishidagi natija — navbat orqali bilan bir xil)."""
    return jsonable_encoder(_TASKS[name](payload))


def call(name: str, payload: dict) -> Any:
    """Vazifani bajarish va natijani qaytarish (navbat yoqilgan bo'lsa — ishchi orqali)."""
    if name not in _TASKS:
        raise KeyError(name)
    if not queued():
        return run_local(name, payload)
    from ..db import JobRow, SessionLocal
    from ..i18n import lang_tag
    from . import notify
    jid = uuid.uuid4().hex[:16]
    now = time.time()
    with SessionLocal() as s:
        s.add(JobRow(id=jid, kind=name, project_id=str(payload.get("pid") or "")[:32] or None,
                     op_id=str(payload.get("oid") or "")[:32] or None, quality=str(payload.get("quality") or "")[:10],
                     state="queued", payload=payload, lang=lang_tag(), started=now, heartbeat=now))
        s.commit()
    notify.publish(notify.JOBS, name)
    try:
        return _wait(jid, name, payload, now)
    finally:
        _drop(jid)


def _drop(jid: str) -> None:
    from ..db import JobRow, SessionLocal
    try:
        with SessionLocal() as s:
            s.query(JobRow).filter(JobRow.id == jid).delete()
            s.commit()
    except Exception:  # noqa: BLE001 — eski yozuvlarni ishchi baribir tozalaydi
        log.exception("vazifa yozuvi o'chirilmadi")


def _take_back(jid: str) -> bool:
    """Hali olinmagan vazifani qaytarib olish (atomik: faqat `queued` holatda)."""
    from ..db import JobRow, SessionLocal
    with SessionLocal() as s:
        n = s.query(JobRow).filter(JobRow.id == jid, JobRow.state == "queued").update(
            {"state": "inline", "worker": f"web:{os.getpid()}"}, synchronize_session=False)
        s.commit()
    return n == 1


def _wait(jid: str, name: str, payload: dict, t0: float) -> Any:
    from sqlalchemy import select

    from ..db import JobRow, SessionLocal
    delay = 0.01
    while True:
        time.sleep(delay)
        delay = min(0.2, delay * 1.4)
        with SessionLocal() as s:
            r = s.execute(select(JobRow.state, JobRow.heartbeat).where(JobRow.id == jid)).first()
            if r is None:
                raise HTTPException(500, "job lost")
            state, hb = r
            if state in ("done", "error"):
                row = s.get(JobRow, jid)
                out = row.summary or {}
                if state == "done":
                    return out.get("value")
                raise HTTPException(row.code or 500, out.get("detail") or row.error or "error")
        now = time.time()
        if state == "queued" and now - t0 > CLAIM_WAIT:
            if _take_back(jid):
                log.warning("hisob ishchisi %s ni %.1f s ichida olmadi — veb-jarayonda bajariladi", name, now - t0)
                return run_local(name, payload)
        elif state == "running" and now - (hb or 0) > STALE_SECONDS:
            from ..i18n import _
            raise HTTPException(500, _("cn.job_failed", e="worker lost"))


# ───────────────────────── Ishchi tomoni (app/worker.py) ─────────────────────────
def claim(worker_id: str, kinds_: list[str]):
    """Eng eski kutilayotgan vazifani olish (barcha korxonalar; PostgreSQL da SKIP LOCKED). Qaytaradi: JobRow nusxasi yoki None."""
    from sqlalchemy import select

    from .. import tenant
    from ..db import IS_PG, JobRow, SessionLocal
    with tenant.system(), SessionLocal() as s:
        st = select(JobRow).where(JobRow.state == "queued", JobRow.kind.in_(kinds_)).order_by(JobRow.started).limit(1)
        if IS_PG:
            st = st.with_for_update(skip_locked=True)
        row = s.scalar(st)
        if row is None:
            return None
        n = s.query(JobRow).filter(JobRow.id == row.id, JobRow.state == "queued").update(
            {"state": "running", "worker": worker_id, "heartbeat": time.time()}, synchronize_session=False)
        s.commit()
        if n != 1:
            return None
        s.refresh(row)
        s.expunge(row)
        return row


def heartbeat(jid: str) -> bool:
    """Yurak urishi; qaytaradi: to'xtatish so'ralganmi."""
    from .. import tenant
    from ..db import JobRow, SessionLocal
    with tenant.system(), SessionLocal() as s:
        s.query(JobRow).filter(JobRow.id == jid, JobRow.state == "running").update(
            {"heartbeat": time.time()}, synchronize_session=False)
        s.commit()
        c = s.query(JobRow.cancel).filter(JobRow.id == jid).scalar()
    return bool(c)


def execute(row) -> None:
    """Olingan umumiy vazifani bajarish (korxona va til konteksti bilan) va natijani yozish."""
    from .. import tenant
    from ..db import JobRow, SessionLocal
    from ..i18n import _, set_lang
    set_lang(row.lang)
    code, value, detail = 200, None, None
    with tenant.use(row.company_id):
        try:
            value = run_local(row.kind, row.payload or {})
        except HTTPException as e:
            code, detail = e.status_code, e.detail
        except Exception as e:  # noqa: BLE001 — kutayotgan so'rovga matn sifatida
            log.exception("vazifa %s xatosi", row.kind)
            code, detail = 500, str(e) if isinstance(e, RuntimeError) else _("cn.job_failed", e=str(e)[:300])
        with SessionLocal() as s:
            s.query(JobRow).filter(JobRow.id == row.id).update(
                {"state": "done" if code == 200 else "error", "code": code, "finished": time.time(), "heartbeat": time.time(),
                 "summary": {"value": value} if code == 200 else {"detail": jsonable_encoder(detail)},
                 "error": "" if code == 200 else str(detail)[:2000]}, synchronize_session=False)
            s.commit()


def prune(keep_seconds: float = 15 * 60) -> int:
    """Eskirgan yozuvlar: tugagan (kutuvchi o'chirmagan) va hech kim olmagan / qulagan ishlar."""
    from .. import tenant
    from ..db import JobRow, SessionLocal
    cut = time.time() - keep_seconds
    with tenant.system(), SessionLocal() as s:
        n = s.query(JobRow).filter(JobRow.kind != "cn", JobRow.heartbeat < cut).delete(synchronize_session=False)
        s.commit()
    return n
