"""(CN) Uzoq hisobni fon vazifasi sifatida bajarish (W16): UI bloklanmaydi — progress so'raladi, to'xtatish mumkin.

Oqim: `start` loyihani o'qiydi, kirish izini (`cn_calc.input_rev`) eslab qoladi va alohida oqimda `run_nesting` ni ishga tushiradi (loyiha qulfi
hisob davomida band qilinmaydi). Tugagach natija `store.editing` ostida qo'llanadi — agar loyiha shu orada o'zgargan bo'lsa (kirish izi
farq qilsa) natija QO'LLANMAYDI (`cn.job_stale`). Holat `jobs` jadvalida (2026-10-22, ko'p jarayonli server): ishni boshlagan
jarayon uni bajaradi va holatini yozib boradi; holatni / to'xtatishni istalgan jarayon bazadan o'qiydi va yozadi. Ishchi
`STALE_SECONDS` davomida yangilanmasa (jarayon qulagan) — ish band hisoblanmaydi. Tugaganlar 15 daqiqadan keyin tozalanadi.
2-bosqich: `MEBELIX_COMPUTE=queue` bo'lsa ish `queued` holatda yoziladi va hisob ishchisi (`app.worker` → `run_claimed`) bajaradi;
ishchi `compute.CLAIM_WAIT` ichida olmasa — boshlagan veb-jarayon o'zi bajaradi.
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
STALE_SECONDS = 120          # ishchi shuncha vaqt holat yozmasa — qulagan deb hisoblanadi
SAVE_EVERY = 0.5             # progressni bazaga yozish oralig'i, s


@dataclass
class Job:
    id: str
    pid: str
    oid: str
    quality: str
    state: str = "running"                 # running | done | error | cancelled
    progress: float = 0.0
    message: str = ""
    started: float = field(default_factory=time.time)
    finished: float = 0.0
    error: str = ""
    summary: Optional[dict] = None
    input_rev: str = ""
    cancel: threading.Event = field(default_factory=threading.Event)
    lang: str = "ru"
    saved: float = 0.0                     # oxirgi bazaga yozilgan vaqt (faqat ishchi jarayonda)

    def dump(self) -> dict:
        end = self.finished or time.time()
        return dict(id=self.id, state="running" if self.state == "queued" else self.state, progress=round(self.progress, 4), message=self.message,
                    elapsed_s=round(end - self.started, 2), error=self.error, quality=self.quality, result=self.summary)


_JOBS: dict[str, Job] = {}                 # shu jarayonda bajarilayotgan ishlar (to'xtatish hodisasi uchun)
_LOCK = threading.Lock()


def _save(job: Job, force: bool = False) -> None:
    """Holatni bazaga yozish (ishchi jarayon). Progress — `SAVE_EVERY` dan siyrak emas; holat o'zgarishi — doim."""
    now = time.time()
    if not force and now - job.saved < SAVE_EVERY:
        return
    from ..db import JobRow, SessionLocal
    with SessionLocal() as s:
        r = s.get(JobRow, job.id)
        if r is None:
            r = JobRow(id=job.id, kind="cn", project_id=job.pid, op_id=job.oid, quality=job.quality, started=job.started,
                       heartbeat=now, lang=job.lang, payload=dict(input_rev=job.input_rev))
            s.add(r)
        r.state, r.progress, r.message, r.error = job.state, job.progress, job.message, job.error
        r.summary, r.finished, r.heartbeat = job.summary, job.finished, now
        if r.cancel:                                              # boshqa jarayon to'xtatishni so'ragan
            job.cancel.set()
        s.commit()
    job.saved = now


def _from_row(r) -> Job:
    j = Job(r.id, r.project_id, r.op_id, r.quality or "", state=r.state, progress=r.progress or 0.0, message=r.message or "",
            started=r.started, finished=r.finished or 0.0, error=r.error or "", summary=r.summary)
    if r.state in ("running", "queued") and time.time() - (r.heartbeat or 0) > STALE_SECONDS:   # ishchi jarayon qulagan
        j.state, j.error, j.finished = "error", _("cn.job_failed", e="worker lost"), r.heartbeat
    return j


def _prune() -> None:
    from ..db import JobRow, SessionLocal
    cut = time.time() - KEEP_SECONDS
    with SessionLocal() as s:
        s.query(JobRow).filter(JobRow.state != "running", JobRow.finished > 0, JobRow.finished < cut).delete()
        s.commit()
    with _LOCK:
        for k in [k for k, j in _JOBS.items() if j.finished and j.finished < cut]:
            _JOBS.pop(k, None)


def get(jid: str, pid: str, oid: str) -> Job:
    with _LOCK:
        j = _JOBS.get(jid)                 # shu jarayonda bajarilayotgan — eng yangi holat
    if j is None:
        from ..db import JobRow, SessionLocal
        with SessionLocal() as s:
            r = s.get(JobRow, jid)
            j = _from_row(r) if r is not None else None
    if j is None or j.pid != pid or j.oid != oid:
        raise HTTPException(404, _("cn.job_not_found"))
    return j


def _running_row(pid: str, oid: str, skip: tuple = ()):
    from ..db import JobRow, SessionLocal
    with SessionLocal() as s:
        r = (s.query(JobRow).filter(JobRow.kind == "cn", JobRow.project_id == pid, JobRow.op_id == oid, JobRow.id.notin_(skip),
                                    JobRow.state.in_(("running", "queued")),
                                    JobRow.heartbeat > time.time() - STALE_SECONDS)
             .order_by(JobRow.started.desc()).first())
        return _from_row(r) if r is not None else None


def current(pid: str, oid: str) -> Optional[Job]:
    """Shu operatsiya uchun ketayotgan vazifa (sahifa qayta yuklansa ham UI uni qayta topadi) yoki None."""
    with _LOCK:
        mine = [j for j in _JOBS.values() if j.pid == pid and j.oid == oid]
    j = next((j for j in mine if j.state in ("running", "queued")), None)
    # shu jarayondagi tugagan ish bazada hali «running» bo'lishi mumkin (yakuniy yozuv bir lahza keyin) — xotiradagisi ustun
    return j or _running_row(pid, oid, tuple(j.id for j in mine))


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
    _prune()
    # band tekshiruvi va yozuv — operatsiya qulfi ostida (boshqa jarayon bir vaqtda boshlasa ham bitta ish)
    with store._lock(f"cn-job:{pid}:{oid}"):
        if current(pid, oid) is not None:
            raise HTTPException(409, _("cn.job_busy"))
        job = Job(uuid.uuid4().hex[:12], pid, oid, q, input_rev=cn_calc.input_rev(p, op))
        from ..i18n import lang_tag
        job.lang = lang_tag()                        # ru | uz | uz-Cyrl (fon oqimida xabarlar shu tilda)
        from . import compute
        if compute.queued():
            job.state = "queued"
        _save(job, force=True)
        if job.state == "queued":
            from . import notify
            notify.publish(notify.JOBS, "cn")
        else:
            with _LOCK:
                _JOBS[job.id] = job
    # korxona konteksti fon oqimiga ham o'tadi (Thread uni o'zi ko'chirmaydi) — saqlash shu korxona nomidan, RLS bilan
    from .. import tenant
    target = _fallback if job.state == "queued" else _run
    threading.Thread(target=tenant.bind(target, job), name=f"cn-job-{job.id}", daemon=True).start()
    return job


def _fallback(job: Job) -> None:
    """Navbat rejimi: ishchi `CLAIM_WAIT` ichida olmasa — ishni qaytarib olib shu jarayonda bajarish."""
    from ..db import JobRow, SessionLocal
    from . import compute
    time.sleep(compute.CLAIM_WAIT)
    with SessionLocal() as s:
        n = s.query(JobRow).filter(JobRow.id == job.id, JobRow.state == "queued").update(
            {"state": "running", "worker": "web", "heartbeat": time.time()}, synchronize_session=False)
        s.commit()
    if n != 1:
        return                                            # ishchi olgan (yoki to'xtatilgan)
    job.state = "running"
    with _LOCK:
        _JOBS[job.id] = job
    _run(job)


def run_claimed(row) -> None:
    """Hisob ishchisi olgan CN ishi (app.worker): holat bazadagi yozuv orqali davom etadi."""
    from .. import tenant
    job = Job(row.id, row.project_id, row.op_id, row.quality or "", started=row.started,
              input_rev=str((row.payload or {}).get("input_rev") or ""))
    job.lang = row.lang or "ru"
    with _LOCK:
        _JOBS[job.id] = job
    try:
        with tenant.use(row.company_id):
            _run(job)
    finally:
        with _LOCK:
            _JOBS.pop(job.id, None)


def cancel(job: Job) -> None:
    """To'xtatish: shu jarayonda bo'lsa — darhol; boshqa jarayonda bajarilayotgan bo'lsa — bazadagi bayroq orqali."""
    job.cancel.set()
    from ..db import JobRow, SessionLocal
    with SessionLocal() as s:
        r = s.get(JobRow, job.id)
        if r is not None and r.state == "queued":           # hali hech kim olmagan — darhol bekor
            r.state, r.error, r.finished, r.cancel = "cancelled", _("cn.job_cancelled"), time.time(), True
            s.commit()
        elif r is not None and r.state == "running":
            r.cancel = True
            s.commit()


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
            _save(job)                                   # siyrak yozuv; boshqa jarayondan kelgan to'xtatishni ham o'qiydi
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
        job.finished = time.time()
        try:
            _save(job, force=True)
        except Exception:  # noqa: BLE001 — holat yozilmasa ham ish natijasi loyihada
            pass
