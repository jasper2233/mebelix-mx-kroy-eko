"""Hisob ishchilari (2-bosqich): `jobs` navbatidagi og'ir vazifalarni alohida jarayonlarda bajaradi.

    python -m app.worker -n 6          # 6 ta ishchi jarayon (standart: MEBELIX_WORKERS yoki CPU yadrolari / 2)

Veb-server `MEBELIX_COMPUTE=queue` bilan ishga tushirilishi kerak (aks holda navbatga hech narsa yozilmaydi). Ishchilar bazaga
`MEBELIX_DB_URL` orqali ulanadi — boshqa kompyuterda ham ishlatish mumkin (4-bosqich). Har ishchi bir vaqtda bitta vazifa;
yangi vazifa kelganda PostgreSQL NOTIFY bilan darhol uyg'onadi (bo'lmasa har `POLL` soniyada tekshiradi). Bosh jarayon qulagan
ishchini qayta ishga tushiradi; bitta kompyuterda bitta bosh jarayon (advisory lock), PID — `worker.pid`.
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import os
import sys
import threading
import time
from pathlib import Path

log = logging.getLogger("mebelix.worker")

POLL = 1.0
PID_FILE = Path(__file__).resolve().parent.parent / "worker.pid"


def _setup() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(name)s: %(message)s")
    from . import main  # noqa: F401 — vazifalar (`@compute.task`) ro'yxatdan o'tadi
    from .db import init_db
    init_db()
    from .services import settings
    settings.listen()


def _waiter():
    """Yangi vazifa xabarini kutish: NOTIFY (PostgreSQL) yoki oddiy pauza."""
    from .services import notify
    ev = threading.Event()
    notify.on(notify.JOBS, lambda _p: ev.set())
    notify.start()

    def wait(t: float) -> None:
        ev.wait(t)
        ev.clear()
    return wait


def _beat(jid: str, stop: threading.Event) -> None:
    from .services import compute
    while not stop.wait(compute.HEARTBEAT_EVERY):
        try:
            compute.heartbeat(jid)
        except Exception:  # noqa: BLE001
            log.warning("yurak urishi yozilmadi", exc_info=True)


def child(idx: int) -> None:
    """Bitta ishchi jarayon: navbatdan olish → bajarish → keyingisi."""
    _setup()
    from .services import cn_jobs, compute
    wid = f"{os.uname().nodename if hasattr(os, 'uname') else os.getenv('COMPUTERNAME', 'pc')}:{os.getpid()}"
    kinds = compute.kinds() + ["cn"]
    wait = _waiter()
    last_prune = 0.0
    log.info("ishchi %d tayyor (%s), vazifalar: %s", idx, wid, ", ".join(kinds))
    while True:
        try:
            if time.time() - last_prune > 60:
                last_prune = time.time()
                compute.prune()
            row = compute.claim(wid, kinds)
        except Exception:  # noqa: BLE001 — baza vaqtincha yo'q: kutib qayta urinadi
            log.warning("navbatni o'qib bo'lmadi", exc_info=True)
            time.sleep(2.0)
            continue
        if row is None:
            wait(POLL)
            continue
        t0 = time.time()
        stop = threading.Event()
        threading.Thread(target=_beat, args=(row.id, stop), daemon=True).start()
        try:
            if row.kind == "cn":
                cn_jobs.run_claimed(row)          # to'xtatish bayrog'ini CN o'zi o'qiydi (progress yozuvida)
            else:
                compute.execute(row)
        finally:
            stop.set()
        log.info("%s (%s, korxona %s) — %.2f s", row.kind, row.project_id, row.company_id, time.time() - t0)


def _single_instance():
    """Bitta kompyuterda bitta bosh jarayon (PostgreSQL advisory lock — ulanish ochiq turguncha)."""
    from sqlalchemy import text

    from .db import IS_PG, engine
    if not IS_PG:
        return None
    conn = engine.connect()
    host = os.getenv("COMPUTERNAME", "pc")
    got = conn.execute(text("SELECT pg_try_advisory_lock(hashtextextended(:k, 0))"), {"k": f"mx:worker:{host}"}).scalar()
    conn.commit()                    # sessiya qulfi saqlanadi; ochiq tranzaksiya VACUUM ni to'smasin
    if not got:
        conn.close()
        log.error("bu kompyuterda hisob ishchilari allaqachon ishlayapti")
        sys.exit(2)
    return conn


def main() -> None:
    ap = argparse.ArgumentParser(description="MebeliX Kroy hisob ishchilari")
    ap.add_argument("-n", "--procs", type=int, default=int(os.getenv("MEBELIX_WORKERS", "0")) or max(1, (os.cpu_count() or 2) // 2))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(name)s: %(message)s")
    _lock = _single_instance()  # noqa: F841 — jarayon tugaguncha ushlab turiladi
    PID_FILE.write_text(str(os.getpid()), encoding="ascii")
    ctx = mp.get_context("spawn")
    procs: dict[int, mp.Process] = {}
    log.info("hisob ishchilari: %d jarayon", a.procs)
    try:
        while True:
            for i in range(a.procs):
                p = procs.get(i)
                if p is None or not p.is_alive():
                    if p is not None:
                        log.warning("ishchi %d to'xtadi (kod %s) — qayta ishga tushiriladi", i, p.exitcode)
                    p = ctx.Process(target=child, args=(i,), name=f"mx-worker-{i}", daemon=True)
                    p.start()
                    procs[i] = p
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs.values():
            p.terminate()
        try:
            PID_FILE.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
