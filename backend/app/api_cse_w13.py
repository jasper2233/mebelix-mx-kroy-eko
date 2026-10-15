"""W13 — CSE (Редактирование раскроя): paket amallari, parallel tahrirni aniqlash izi, qoralamani tekshirish.

Alohida tahrir amallari (`remove/move/clone/rotate` + `paths`, `place_multi`, `expand_block`, `flip`, `replace`, `swap`,
`move_map`, `map_trim`, `comment`) — mavjud `POST …/edit` endpointida (`services/editor.py`, `services/editor_w13.py`);
bu modul unga qo'shimcha endpointlar. `main.py` da `api.include_router(cse_w13_router)`."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import store
from .i18n import _
from .models import CuttingResult, OpType
from .services import editor, editor_w13

router = APIRouter()

MAX_BATCH = 200


def _cs(p, oid):
    op = store.op_of(p, oid)
    if op.type != OpType.CS:
        raise HTTPException(400, _("cs_only"))
    return op


class BatchIn(BaseModel):
    result: CuttingResult
    actions: list[dict]


@router.post("/projects/{pid}/operations/{oid}/edit/batch", tags=["kroy"])
def edit_batch(pid: str, oid: str, inp: BatchIn):
    """Bir nechta tahrir amalini ketma-ket qo'llash (hammasi yoki hech biri): qoralama + amallar → yangi qoralama.
    Biror amal xato bersa — 422, xabarda amal tartib raqami (loyiha o'zgarmaydi)."""
    if len(inp.actions) > MAX_BATCH:
        raise editor.EditError(_("ed.batch_long", n=MAX_BATCH))
    p = store.load(pid)
    op = _cs(p, oid)
    res = inp.result
    for i, action in enumerate(inp.actions, 1):
        try:
            res = editor.apply(p, op, res, action)
        except editor.EditError as e:
            kind = str(action.get("type"))[:30] if isinstance(action, dict) else "?"
            raise editor.EditError(_("ed.batch_fail", i=i, t=kind, e=str(e)), e.details) from None
    return res


@router.get("/projects/{pid}/operations/{oid}/edit/rev", tags=["kroy"])
def edit_rev(pid: str, oid: str):
    """Natijaning joriy «izi» — muharrir ochilganda olinadi, saqlashda `PUT …/result?base=` bilan yuboriladi."""
    p = store.load(pid)
    op = _cs(p, oid)
    return dict(rev=editor_w13.result_rev(op.result))


@router.post("/projects/{pid}/operations/{oid}/edit/check", tags=["kroy"])
def edit_check(pid: str, oid: str, result: CuttingResult):
    """Qoralamani saqlamasdan tekshirish: karta kesib bo'ladimi (daraja, propil, minimal obrezka, detallar soni).
    Qaytaradi: ok, errors (bo'sh bo'lsa — yaroqli), maps (har karta: daraja, detallar soni)."""
    p = store.load(pid)
    op = _cs(p, oid)
    try:
        rebuilt = editor.rebuild(p, op, result)
    except editor.EditError as e:
        return dict(ok=False, errors=e.details or [str(e)], maps=[])
    return dict(ok=True, errors=[], maps=[dict(index=m.index, parts=m.parts_count, copies=m.copies,
                                              fill=m.fill_percent) for m in rebuilt.maps])
