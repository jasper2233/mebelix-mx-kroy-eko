"""(O) Комплектация и другие действия — materiallar jadvali API (butun jadvalni almashtirish, buferdan qo'yish).

Parametrlar (egasi, ish narxi, izoh) — umumiy `PATCH /projects/{pid}/operations/{oid}` orqali (`{o: {...}, description}`);
operatsiya yaratish — `POST /projects/{pid}/operations {type: "O"}`; standart — `PUT /settings/o_defaults/default`.
Har so'rov — bitta tarix (undo/redo) qadami.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from . import store
from .i18n import _
from .models import O_MAX_ROWS, OMaterial, OParams, OpType, Operation
from .services import o_ops, settings

router = APIRouter(tags=["komplektatsiya (O)"])


def _need_o(op: Operation) -> OParams:
    if op.type != OpType.O:
        raise HTTPException(400, _("o_only"))
    if op.o is None:                       # eski JSON: parametrlar yo'q — bo'sh yaratiladi
        op.o = OParams()
    return op.o


@router.put("/projects/{pid}/operations/{oid}/o/materials")
def put_o_materials(pid: str, oid: str, rows: list[OMaterial] = Body(...)):
    """Butun materiallar jadvalini almashtirish (bitta undo qadami). Qatorlar ≤ 5000; qiymatlar chegarasi — 422."""
    if len(rows) > O_MAX_ROWS:
        raise HTTPException(422, _("o_rows_limit", n=O_MAX_ROWS))
    with store.editing(pid) as p:
        _need_o(store.op_of(p, oid)).materials = rows
    return p


class PasteIn(BaseModel):
    text: str = Field(max_length=o_ops.PASTE_MAX_CHARS)      # Excel / OpenOffice dan nusxa (TSV)
    mode: Literal["append", "replace"] = "append"            # append — oxiriga qo'shish; replace — jadvalni almashtirish


@router.post("/projects/{pid}/operations/{oid}/o/materials/paste")
def paste_o_materials(pid: str, oid: str, inp: PasteIn):
    """Buferdan (Excel) qo'yish: ustunlar `Код, Наименование, Ед.И, Кол, Цена`. Javob — loyiha + `added` (qo'shilgan qatorlar),
    `skipped` (`[{row, reason}]` — o'tkazib yuborilgan qatorlar) va `warnings`. Hech narsa qo'shilmasa tarixga yozilmaydi."""
    unit = o_ops.default_unit(settings.get_default("o_defaults"))
    with store.editing(pid, skip_unchanged=True) as p:
        prm = _need_o(store.op_of(p, oid))
        base = [] if inp.mode == "replace" else list(prm.materials)
        res = o_ops.parse_paste(inp.text, room=max(0, O_MAX_ROWS - len(base)), default_unit=unit)
        prm.materials = base + res.rows
    out = jsonable_encoder(p)
    out.update(added=len(res.rows), skipped=res.skipped, warnings=res.warnings)
    return out
