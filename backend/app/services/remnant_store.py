"""Ombor manbasi (2026-10-24, foydalanuvchi qarori: ombor ma'lumotlari MES bazasida; MX — kroy vazifasi, bazaga yuborish va
bazadan topib qo'shish qoidalari).

* `local` — MX ning o'z `remnants` jadvali (MES API tayyor bo'lguncha; hozirgi ish oqimi).
* `mes`   — MES bazasi HTTP orqali (`remnant_rules.mes_url`, token — `MES_API_TOKEN`, bo'lmasa `MES_WEBHOOK_TOKEN`):
    GET  {url}/remnants?material=&code=&type=&thickness=&status=available     → {items: [qoldiq]}
    GET  {url}/remnants?ids=1,2                                               → {items: [...]}
    POST {url}/remnants/reservations {order, ids, mode: add|remove|set}       → 200 | 409 {conflicts: [{id, order_number}]}
    POST {url}/remnants/intake {order, op, sheet_area_m2, keep_percent, pieces, client_pieces, consumed} → {intake_id, ids}
    POST {url}/remnants/intake/{intake_id}/cancel                             → 200
  «Kutilmoqda → list arradan chiqdi → mavjud» holati, kirim-chiqim jurnali va narxlar MES da yuritiladi.
Shartnoma: docs/mebelix/MES_QOLDIQ_V1.md.
"""
from __future__ import annotations

import os
from typing import Optional

from ..i18n import _
from ..models import Operation, OpType, Project
from . import remnant_rules


class StoreUnavailable(RuntimeError):
    """MES ombori bilan aloqa yo'q (503)."""


def source(rules: Optional[remnant_rules.RemnantRules] = None) -> str:
    rules = rules or remnant_rules.load()
    return "mes" if rules.source == "mes" and rules.mes_url.strip() else "local"


def is_mes() -> bool:
    return source() == "mes"


def order_info(p: Project) -> dict:
    return dict(project_id=p.id, number=p.number, name=p.name, mes_order_ref=p.mes_order_ref, customer=p.customer or "")


def op_info(op: Operation) -> dict:
    t = op.cs_material.thickness if op.cs_material else (op.cl.thickness if op.cl else None)
    return dict(id=op.id, name=op.name, code=op.code or "", type=remnant_rules.material_type(op.code, op.name), thickness=t,
                linear=op.type == OpType.CL)


# ───────────────────────── MES HTTP ─────────────────────────
def _req(method: str, path: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    import httpx
    rules = remnant_rules.load()
    url = rules.mes_url.rstrip("/") + path
    headers = {"Content-Type": "application/json"}
    token = os.getenv("MES_API_TOKEN") or os.getenv("MES_WEBHOOK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = httpx.request(method, url, json=json, params=params, headers=headers, timeout=float(os.getenv("MES_API_TIMEOUT", "10")))
    except Exception as e:  # noqa: BLE001 — ulanish, timeout, DNS
        raise StoreUnavailable(_("mes_store_down", e=f"{type(e).__name__}")) from e
    if r.status_code == 409:
        from .warehouse import WarehouseConflict
        body = _json(r)
        items = body.get("conflicts") or []
        raise WarehouseConflict("; ".join(_("remnant_reserved_other", id=c.get("id"), n=c.get("order_number", "?")) for c in items)
                                or body.get("detail") or "409")
    if r.status_code >= 400:
        raise StoreUnavailable(_("mes_store_error", s=r.status_code, d=str(_json(r).get("detail", ""))[:200]))
    return _json(r)


def _json(r) -> dict:
    try:
        v = r.json()
        return v if isinstance(v, dict) else {"items": v}
    except Exception:  # noqa: BLE001
        return {}


def _norm_item(d: dict) -> dict:
    """MES qoldig'i → MX qoldiq ko'rinishi (`warehouse.row_dict` maydonlari)."""
    L, W = float(d.get("length") or 0), float(d.get("width") or 0)
    sheet = float(d.get("sheet_area_m2") or 0) or None
    return dict(id=int(d["id"]), material_code=d.get("material_code") or "", material_name=d.get("material_name") or "",
                length=L, width=W, thickness=float(d.get("thickness") or 0), qty=int(d.get("qty") or 0),
                area_m2=round(L * W / 1e6, 3), note=d.get("note") or "", source_project=d.get("source_project"),
                source_number=d.get("source_number"), source_op=None, created_at=d.get("created_at"),
                reserved_project=d.get("reserved_project"), reserved_number=d.get("reserved_number"),
                linear=bool(d.get("linear", False)), qty_pending=int(d.get("qty_pending") or 0), source_map=d.get("source_map"),
                sheet_area_m2=sheet, percent=round(L * W / 1e6 / sheet * 100, 1) if sheet else None,
                mat_type=d.get("type") or remnant_rules.material_type(d.get("material_code"), d.get("material_name")),
                status=d.get("status") or ("available" if int(d.get("qty") or 0) > 0 else "empty"), external=True)


# ───────────────────────── Umumiy amallar ─────────────────────────
def candidates(op: Operation, linear: bool = False) -> list[dict]:
    """Operatsiya materialidan (nom/kod — katta-kichik harf va bo'shliqlarsiz) mavjud (`qty` > 0) qoldiqlar."""
    if is_mes():
        info = op_info(op)
        items = _req("GET", "/remnants", params=dict(material=op.name or "", code=op.code or "", type=info["type"],
                                                     thickness=info["thickness"] or "", status="available",
                                                     linear=str(linear).lower())).get("items") or []
        return [d for d in (_norm_item(x) for x in items) if d["qty"] > 0 and d["linear"] == linear]
    from sqlalchemy import select
    from ..db import RemnantRow, SessionLocal
    from . import warehouse
    key = remnant_rules.norm(warehouse.material_key(op))
    with SessionLocal() as s:
        rows = s.scalars(select(RemnantRow).where(RemnantRow.linear == linear, RemnantRow.qty > 0)).all()
        rows = [r for r in rows if remnant_rules.norm(r.material_code) == key]
        return warehouse.annotate_reservations([warehouse.row_dict(r) for r in rows])


def list_all(material_code: Optional[str] = None, linear: Optional[bool] = None) -> list[dict]:
    """MES rejimida «Склад остатков» ro'yxati (faqat ko'rish)."""
    params = dict(material=material_code or "")
    if linear is not None:
        params["linear"] = str(linear).lower()
    return [_norm_item(x) for x in (_req("GET", "/remnants", params=params).get("items") or [])]


def get_many(ids: list[int]) -> list[Optional[dict]]:
    if is_mes():
        got = {d["id"]: d for d in (_norm_item(x) for x in
                                    (_req("GET", "/remnants", params=dict(ids=",".join(str(i) for i in ids))).get("items") or []))}
        return [got.get(int(i)) for i in ids]
    from ..db import RemnantRow, SessionLocal
    from . import warehouse
    with SessionLocal() as s:
        return [warehouse.row_dict(r) if r is not None else None for r in (s.get(RemnantRow, i) for i in ids)]


def mes_reservations(p: Project, ids: list[int], mode: str) -> None:
    _req("POST", "/remnants/reservations", json=dict(order=order_info(p), ids=[int(i) for i in ids], mode=mode))


def mes_commit(p: Project, op: Operation) -> dict:
    """Kroydan keyin MES ga: olib qolinadigan qoldiqlar (har karta — MES list arradan chiqqanda «mavjud» qiladi), mijozga
    beriladigan bo'laklar va buyurtmada ishlatilgan (sotilgan) ombor qoldiqlari."""
    from . import calc, warehouse
    res = op.result
    rules = remnant_rules.load()
    rr = remnant_rules.op_rule(op, rules)
    sheet_m2 = round(remnant_rules.sheet_area_mm2(op) / 1e6, 4) if op.type == OpType.CS else None
    pr = calc.material_prices(op) if op.type == OpType.CS else dict(m2=0.0, sheet=0.0)
    used = warehouse.consumed(op)
    by_id = {sh.source_remnant_id: sh for sh in op.sheets if sh.source_remnant_id}
    consumed = [dict(id=rid, qty=n, length=by_id[rid].length, width=by_id[rid].width,
                     area_m2=round(by_id[rid].length * by_id[rid].width / 1e6, 4),
                     sale_price=round(by_id[rid].length * by_id[rid].width / 1e6 * pr["m2"] * n, 2)) for rid, n in used.items()]
    pieces = [dict(map=g["map"], length=g["length"], width=g["width"], qty=g["qty"], copies=g["copies"],
                   percent=remnant_rules.percent_of(g["length"], g["width"], sheet_m2 * 1e6) if sheet_m2 else None)
              for g in warehouse.kept_pieces(op, rules)]
    body = dict(order=order_info(p), op=op_info(op), sheet_area_m2=sheet_m2, keep_percent=rr[0] if rr else None,
                rule_source=rr[1] if rr else None, sheet_price=round(pr["sheet"], 2), m2_price=round(pr["m2"], 4),
                pieces=pieces, client_pieces=warehouse.client_pieces(op, rules), consumed=consumed)
    out = _req("POST", "/remnants/intake", json=body)
    res.remnants_saved = True
    res.saved_remnant_ids = [int(i) for i in out.get("ids") or []]
    res.saved_remnant_qty = {}
    res.consumed_remnants = {str(k): v for k, v in used.items()}
    res.remnant_intake_id = str(out.get("intake_id") or "") or None
    return dict(added=[dict(id=i) for i in res.saved_remnant_ids], consumed=res.consumed_remnants, intake_id=res.remnant_intake_id)


def mes_rollback(op: Operation) -> dict:
    from . import warehouse
    res = op.result
    if res and res.remnants_saved and res.remnant_intake_id:
        _req("POST", f"/remnants/intake/{res.remnant_intake_id}/cancel", json={})
    removed = list(res.saved_remnant_ids) if res else []
    warehouse.detach(op)
    return dict(removed=removed, restored={}, kept=[], orphaned=[])
