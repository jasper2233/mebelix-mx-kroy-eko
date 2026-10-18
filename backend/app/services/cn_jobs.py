"""(CN) Uzoq hisobni fon vazifasi sifatida bajarish (W16): UI bloklanmaydi — progress so'raladi, to'xtatish mumkin.

Oqim: `start` loyihani o'qiydi, kirish izini (`cn_calc.input_rev`) eslab qoladi va alohida oqimda `run_nesting` ni ishga tushiradi (loyiha qulfi
hisob davomida band qilinmaydi). Tugagach natija `store.editing` ostida qo'llanadi — agar loyiha shu orada o'zgargan bo'lsa (kirish izi
farq qilsa) natija QO'LLANMAYDI (`cn.job_stale`). Vazifalar jarayon xotirasida (bir jarayonli o'rnatish; ko'p jarayonli o'rnatishda
bir foydalanuvchining so'rovlari bir jarayonga yo'naltirilishi kerak). Tugagan vazifalar 15 daqiqadan keyin tozalanadi.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException

from .. import store
from ..i18n import _
from ..models import OpType
from . import cn_calc, cn_messages  # noqa: F401
from . import warehouse
from .calc import _account, effective_qty
from .cn_nest import NestCancelled

KEEP_SECONDS = 15 * 60


@dataclass
class Job:
    id: str
    pid: str
    oid: str
    quality: str
    state: str = "running"                 # running | done | error | cancelled
    progress: float = 0.0
    message: str = ""
    started: float = field(default_factory=time.monotonic)
    finished: float = 0.0
    error: str = ""
    summary: Optional[dict] = None
    input_rev: str = ""
    cancel: threading.Event = field(default_factory=threading.Event)
    lang: str = "ru"

    def dump(self) -> dict:
        end = self.finished or time.monotonic()
        return dict(id=self.id, state=self.state, progress=round(self.progress, 4), message=self.message,
                    elapsed_s=round(end - self.started, 2), error=self.error, quality=self.quality, result=self.summary)


_JOBS: dict[str, Job] = {}
_LOCK = threading.Lock()


def _prune() -> None:
    now = time.monotonic()
    for k in [k for k, j in _JOBS.items() if j.finished and now - j.finished > KEEP_SECONDS]:
        _JOBS.pop(k, None)


def get(jid: str, pid: str, oid: str) -> Job:
    with _LOCK:
        j = _JOBS.get(jid)
    if j is None or j.pid != pid or j.oid != oid:
        raise HTTPException(404, _("cn.job_not_found"))
    return j


def current(pid: str, oid: str) -> Optional[Job]:
    """Shu operatsiya uchun ketayotgan vazifa (sahifa qayta yuklansa ham UI uni qayta topadi) yoki None."""
    with _LOCK:
        return next((j for j in _JOBS.values() if j.pid == pid and j.oid == oid and j.state == "running"), None)


def start(pid: str, oid: str, quality: Optional[str]) -> Job:
    """Hisobni boshlash. Xatolar (detallar / listlar yo'q, katta hajm, band) — HTTPException; aks holda ishlayotgan Job."""
    p = store.load(pid)
    op = store.op_of(p, oid)
    if op.type != OpType.CN:
        raise HTTPException(400, _("cn.only"))
    if not op.parts:
        raise HTTPException(400, _("no_parts"))
    if sum(effective_qty(p, pt) for pt in op.parts) <= 0:         # hamma detal soni 0 — kroy uchun hech narsa yo'q
        raise HTTPException(400, _("no_parts_qty"))
    if not op.sheets:
        raise HTTPException(400, _("no_sheets"))
    if all((sh.qty or 0) <= 0 for sh in op.sheets):
        raise HTTPException(400, _("no_sheets_qty"))
    n = sum(effective_qty(p, pt) for pt in op.parts)
    if n > cn_calc.max_items():
        raise HTTPException(400, _("cn.too_many", n=n, max=cn_calc.max_items()))
    cn = cn_calc.ensure_cn(op)
    q = quality or cn.quality
    with _LOCK:
        _prune()
        if any(j.pid == pid and j.oid == oid and j.state == "running" for j in _JOBS.values()):
            raise HTTPException(409, _("cn.job_busy"))
        job = Job(uuid.uuid4().hex[:12], pid, oid, q, input_rev=cn_calc.input_rev(p, op))
        from ..i18n import lang_tag
        job.lang = lang_tag()                        # ru | uz | uz-Cyrl (fon oqimida xabarlar shu tilda)
        _JOBS[job.id] = job
    threading.Thread(target=_run, args=(job,), name=f"cn-job-{job.id}", daemon=True).start()
    return job


def cancel(job: Job) -> None:
    job.cancel.set()


def _run(job: Job) -> None:
    from ..i18n import set_lang
    set_lang(job.lang)
    try:
        p = store.load(job.pid)
        op = store.op_of(p, job.oid)

        def progress(frac: float, msg: str) -> None:
            job.progress = max(job.progress, min(0.99, float(frac)))
            if msg:
                job.message = msg
        cn_calc.run_nesting(p, op, quality=job.quality, progress=progress, cancel=job.cancel.is_set)
        res = op.result
        if job.cancel.is_set():
            raise NestCancelled()
        with store.editing(job.pid) as p2:
            op2 = store.op_of(p2, job.oid)
            if cn_calc.input_rev(p2, op2) != job.input_rev:
                raise RuntimeError(_("cn.job_stale"))
            if op2.result is not None and op2.result.remnants_saved:     # eski natija omborga yozilgan bo'lsa — bekor qilinadi
                warehouse.rollback(op2)
            op2.result = res
            _account(p2, op2)
            cn_calc.cn_cost(p2, op2)
        job.summary = dict(sheets=res.total_sheets, fill=res.total_fill_percent, unplaced=len(res.unplaced),
                           elapsed_s=res.elapsed_s, maps=len(res.maps), warnings=len(res.warnings))
        job.progress = 1.0
        job.state = "done"
    except NestCancelled:
        job.state = "cancelled"
        job.error = _("cn.job_cancelled")
    except HTTPException as e:
        job.state, job.error = "error", str(e.detail)
    except Exception as e:  # noqa: BLE001 — hisob xatosi foydalanuvchiga matn sifatida
        job.state, job.error = "error", str(e) if isinstance(e, RuntimeError) else _("cn.job_failed", e=str(e)[:300])
    finally:
        job.finished = time.monotonic()
