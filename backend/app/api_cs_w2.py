"""W2 — CS bo'shliqlari: kroygacha/keyin material va list miqdori, qoldiq «Исп. кол-во» (mijoz olib ketadigan bo'laklar),
qoldiq rezervi (REM-009). Yangi endpointlar shu modulda; `main.py` da `api.include_router(cs_w2_router)`."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import store
from .i18n import _
from .models import OpType
from .services import calc, warehouse

router = APIRouter()


def _cs(p, oid):
    op = store.op_of(p, oid)
    if op.type != OpType.CS:
        raise HTTPException(400, _("cs_only"))
    return op


def _cut(p, oid):
    """Qoldiq endpointlari: listli (CS), погонажный (CL, W11) yoki nesting (CN, W16) kroy operatsiyasi."""
    op = store.op_of(p, oid)
    if op.type not in (OpType.CS, OpType.CL, OpType.CN):
        raise HTTPException(400, _("cut_only"))
    return op


# ───────────────────────── Material va list miqdori (CS-036/037) ─────────────────────────
@router.get("/projects/{pid}/operations/{oid}/cs-quantities", tags=["kroy"])
def cs_quantities(pid: str, oid: str):
    """«Количество материала» va «Количество листов» (kroygacha — taxminiy, `estimated=true`; kroydan keyin — natijadan):
    estimated, sheets (yaxlitlangan yangi listlar — narx asosi), sheets_total (kroydagi listlar yoki taxminiy),
    material_qty_m2 (sarf − деловой qoldiqlar), sheet_area_m2, parts_area_m2 (pilniy o'lcham bo'yicha detallar maydoni).
    Hech narsa saqlanmaydi."""
    p = store.load(pid)
    return calc.cs_cost(p, _cs(p, oid))


# ───────────────────────── Qoldiq «Исп. кол-во» (REM-004 / CS-104) ─────────────────────────
@router.get("/projects/{pid}/operations/{oid}/remnant-groups", tags=["qoldiqlar"])
def remnant_groups(pid: str, oid: str):
    """Kroy natijasidagi qoldiqlar (foydali o'lcham va tur bo'yicha): key, business, length, width, qty, taken.
    `taken` — mijoz olib ketadigan («Исп. кол-во») bo'laklar; ular omborga yozilmaydi (standart 0)."""
    p = store.load(pid)
    op = _cut(p, oid)
    return dict(groups=warehouse.result_remnant_groups(op), saved=bool(op.result and op.result.remnants_saved))


class TakenIn(BaseModel):
    key: str = Field(max_length=60)
    qty: int = Field(ge=0, le=1_000_000)


@router.put("/projects/{pid}/operations/{oid}/result/taken", tags=["qoldiqlar"])
def set_taken(pid: str, oid: str, inp: TakenIn):
    """Qoldiq guruhi uchun «Исп. кол-во» (mijoz olib ketadigan bo'laklar soni; 0 — olib ketmaydi). Omborga yozilgandan
    keyin o'zgartirib bo'lmaydi (avval yozuvni bekor qiling)."""
    with store.editing(pid) as p:
        op = _cut(p, oid)
        res = op.result
        if not res or not res.maps:
            raise HTTPException(400, _("no_result"))
        if res.remnants_saved:
            raise HTTPException(409, _("remnant_taken_locked"))
        g = next((x for x in warehouse.result_remnant_groups(op) if x["key"] == inp.key), None)
        if g is None:
            raise HTTPException(404, _("remnant_taken_key", k=inp.key))
        if inp.qty > g["qty"]:
            raise HTTPException(400, _("remnant_taken_over", n=g["qty"]))
        taken = dict(res.taken_remnants or {})
        if inp.qty:
            taken[inp.key] = inp.qty
        else:
            taken.pop(inp.key, None)
        res.taken_remnants = taken
    return p


# ───────────────────────── Rezerv (REM-009) ─────────────────────────
class ReleaseIn(BaseModel):
    ids: list[int] = Field(max_length=500)


@router.post("/remnants/reservations/release", tags=["qoldiqlar"])
def release_reservations(inp: ReleaseIn):
    """Ombordagi qoldiqlar rezervini bo'shatish (qoldiqni band qilgan loyiha o'chib ketgan/unutilgan bo'lsa). Shu loyihaning
    listida qoldiq turaversa-da, endi u boshqa loyihalarga ochiq bo'ladi."""
    return dict(released=warehouse.release(inp.ids))
