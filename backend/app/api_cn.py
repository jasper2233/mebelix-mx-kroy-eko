"""W16 — (CN) Нестинговый раскрой: qo'shimcha endpointlar. Asosiy amallar umumiy yo'llarda (main.py: `optimize`, `edit`, `result`,
`remnants/*`, `sheets/from-remnants`, `maps/{i}.svg`, `postprocess`, `report`) operatsiya turiga qarab CN ga yo'naltiriladi.
Bu yerda: hisob miqdorlari, shakllar (konturlar), tahrir izi, tekshiruv va FON VAZIFASI (uzoq hisob — UI bloklanmaydi)."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException

from . import store
from .i18n import _
from .models import OpType
from .services import cn_calc, cn_editor, cn_jobs, cn_messages  # noqa: F401
from .services.cn_validate import validate_cn

router = APIRouter()


def _cn(p, oid):
    op = store.op_of(p, oid)
    if op.type != OpType.CN:
        raise HTTPException(400, _("cn.only"))
    return op


@router.get("/projects/{pid}/operations/{oid}/cn-quantities", tags=["kroy"])
def cn_quantities(pid: str, oid: str):
    """«Количество материала» (m²), listlar, kesim uzunligi, narx: kroygacha — taxminiy (`estimated=true`), kroydan keyin — natijadan."""
    p = store.load(pid)
    return cn_calc.cn_cost(p, _cn(p, oid))


@router.get("/projects/{pid}/operations/{oid}/cn-shapes", tags=["kroy"])
def cn_shapes(pid: str, oid: str):
    """Detal shakllari (kontur / to'rtburchak, ichki kesimlar, maydon, perimetr, ogohlantirishlar, etiketka o'rni). Hech narsa saqlanmaydi."""
    p = store.load(pid)
    return cn_calc.shapes_info(p, _cn(p, oid))


@router.get("/projects/{pid}/operations/{oid}/cn-edit/rev", tags=["kroy"])
def cn_edit_rev(pid: str, oid: str):
    """Natijaning joriy «izi» — muharrir ochilganda olinadi, saqlashda `PUT …/result?base=` bilan yuboriladi (parallel tahrir → 409)."""
    p = store.load(pid)
    return dict(rev=cn_editor.result_rev(_cn(p, oid).result))


@router.get("/projects/{pid}/operations/{oid}/cn-validate", tags=["kroy"])
def cn_validate_result(pid: str, oid: str):
    """Saqlangan natijani mustaqil tekshiruvdan o'tkazish: {ok, errors}."""
    p = store.load(pid)
    op = _cn(p, oid)
    if not op.result or not op.result.maps:
        raise HTTPException(400, _("cut_first"))
    ci = cn_calc.build_items(p, op)
    errs = validate_cn(op.result, ci.shapes, ci.need, ci.grains, op.sheets, cn_calc.ensure_cn(op))
    return dict(ok=not errs, errors=errs)


# ───────────────────────── Fon vazifasi ─────────────────────────
@router.post("/projects/{pid}/operations/{oid}/cn/jobs", tags=["kroy"])
def cn_job_start(pid: str, oid: str, quality: Optional[Literal["fast", "normal", "max"]] = None):
    """Nestingni fon vazifasi sifatida boshlash (UI bloklanmaydi). Natija tugagach loyihaga yoziladi (tarix qadami); so'rov:
    `GET …/cn/jobs/{job}` (state: running | done | error | cancelled, progress 0…1)."""
    return cn_jobs.start(pid, oid, quality).dump()


@router.get("/projects/{pid}/operations/{oid}/cn/jobs/current", tags=["kroy"])
def cn_job_current(pid: str, oid: str):
    """Shu operatsiya uchun ketayotgan vazifa yoki `null` (UI sahifa qayta yuklanganda progressni davom ettiradi). `{jid}` yo'lidan OLDIN turishi shart."""
    store.op_of(store.load(pid), oid)
    j = cn_jobs.current(pid, oid)
    return j.dump() if j else None


@router.get("/projects/{pid}/operations/{oid}/cn/jobs/{jid}", tags=["kroy"])
def cn_job_get(pid: str, oid: str, jid: str):
    return cn_jobs.get(jid, pid, oid).dump()


@router.delete("/projects/{pid}/operations/{oid}/cn/jobs/{jid}", tags=["kroy"])
def cn_job_cancel(pid: str, oid: str, jid: str):
    job = cn_jobs.get(jid, pid, oid)
    cn_jobs.cancel(job)
    return job.dump()
