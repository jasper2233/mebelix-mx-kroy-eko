"""MES integratsiyasi: buyurtma qabul qilish, natija eksporti, webhook, QR skanerlash.

1) MES → MebeliX:  POST /api/mes/orders   (MesOrder JSON)
   Har material kodi uchun (CS) operatsiya, har kromka kodi uchun (EL) operatsiya yaratiladi.
   Material/kromka parametrlari: so'rovdagi `materials` / `edges` ro'yxatidan, bo'lmasa katalogdan (catalog_items).
2) MebeliX → MES:  GET /api/projects/{id}/mes-export — sarf (list, m², kromka m), qoldiqlar, narxlar, kartalar.
3) Webhook: loyiha holati o'zgarsa yoki karta kesib bo'linsa MES_WEBHOOK_URL ga POST (JSON).
4) Skaner: GET /api/mes/scan/{qr} — etiketkadagi QR bo'yicha detal ma'lumoti.
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Optional

from pydantic import BaseModel

from ..models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, OpType, Operation, Part, Product,
                      Project, StockSheet)
from .calc import edge_usage, total_qty, warehouse_request

log = logging.getLogger("mebelix.mes")


class MesPart(BaseModel):
    name: str = ""
    code: str = ""
    material_code: str
    length: float
    width: float
    qty: int = 1
    grain: bool = False
    edges: dict[str, Optional[str]] = {}      # top/bottom/left/right → kromka kodi


class MesProduct(BaseModel):
    code: str = ""
    name: str
    qty: int = 1
    parts: list[MesPart] = []


class MesMaterial(BaseModel):
    code: str
    name: str = ""
    thickness: float = 16
    length: float = 2750
    width: float = 1830
    price: float = 0
    price_per_m2: bool = False
    grain: bool = False


class MesEdge(BaseModel):
    code: str
    name: str = ""
    thickness: float = 0
    width: float = 19
    price: float = 0
    symbol: str = ""
    color: str = ""


class MesOrder(BaseModel):
    mes_order_ref: str
    name: str = ""
    customer: str = ""
    currency: str = "UZS"
    order_date: Optional[date] = None
    ready_date: Optional[date] = None
    note: str = ""
    products: list[MesProduct] = []
    materials: list[MesMaterial] = []
    edges: list[MesEdge] = []


EDGE_COLORS = ["#1f6feb", "#c9761a", "#1f9d57", "#c0392b", "#7d3cc9", "#0e7d78", "#b3861a", "#c2508f"]


def build_project(order: MesOrder, catalog: dict[str, dict], number: int,
                  cs_defaults: Optional[dict] = None, el_defaults: Optional[dict] = None) -> Project:
    """MES buyurtmasidan MebeliX loyihasini yasaydi (katalog — code → catalog_items qatori)."""
    p = Project(number=number, name=order.name or order.mes_order_ref, customer=order.customer,
                currency=order.currency, note=order.note, mes_order_ref=order.mes_order_ref)
    if order.order_date:
        p.order_date = order.order_date
    if order.ready_date:
        p.ready_date = order.ready_date
    mats = {m.code: m for m in order.materials}
    edges = {e.code: e for e in order.edges}
    cs_ops: dict[str, Operation] = {}
    el_ops: dict[str, Operation] = {}

    def el_op(code: str) -> Operation:
        if code in el_ops:
            return el_ops[code]
        e = edges.get(code)
        cat = catalog.get(code, {})
        params = ELParams(**(el_defaults or {}))
        params.thickness = e.thickness if e else float(cat.get("thickness") or 0)
        params.width = e.width if e else float((cat.get("params") or {}).get("width", cat.get("width") or 19))
        params.price = e.price if e else float(cat.get("price") or 0)
        params.symbol = (e.symbol if e and e.symbol else chr(ord("A") + len(el_ops) % 26))
        params.color = (e.color if e and e.color else EDGE_COLORS[len(el_ops) % len(EDGE_COLORS)])
        op = Operation(type=OpType.EL, code=code, name=(e.name if e and e.name else cat.get("name", code)),
                       material_id=cat.get("id"), el=params)
        el_ops[code] = op
        return op

    def cs_op(code: str) -> Operation:
        if code in cs_ops:
            return cs_ops[code]
        m = mats.get(code)
        cat = catalog.get(code, {})
        mp = CSMaterialParams(**{k: v for k, v in (cs_defaults or {}).get("material", {}).items()})
        cp = CSCutParams(**{k: v for k, v in (cs_defaults or {}).get("cut", {}).items()})
        mp.thickness = m.thickness if m else float(cat.get("thickness") or 16)
        mp.price = m.price if m else float(cat.get("price") or 0)
        mp.cost_by_sheets = not (m.price_per_m2 if m else False)    # m² narxi — m² bo'yicha hisob
        L = m.length if m else float(cat.get("length") or 2750)
        W = m.width if m else float(cat.get("width") or 1830)
        op = Operation(type=OpType.CS, code=code, name=(m.name if m and m.name else cat.get("name", code)),
                       material_id=cat.get("id"), cs_material=mp, cs_cut=cp, sheets=[StockSheet(length=L, width=W)])
        cs_ops[code] = op
        return op

    uid = 0
    for pr in order.products:
        prod = Product(code=pr.code, name=pr.name, qty=pr.qty)
        p.products.append(prod)
        for mp in pr.parts:
            uid += 1
            part = Part(uid=uid, product_id=prod.id, name=mp.name, code=mp.code, length=mp.length,
                        width=mp.width, qty=mp.qty, grain=mp.grain)
            for side in ("top", "bottom", "left", "right"):
                ec = mp.edges.get(side)
                if ec:
                    setattr(part, f"edge_{side}", EdgeRef(op_id=el_op(ec).id))
            cs_op(mp.material_code).parts.append(part)
    p.operations = list(cs_ops.values()) + list(el_ops.values())
    return p


def export(project: Project) -> dict:
    """MES uchun natija: sarf, qoldiqlar, narx, kartalar (qisqa)."""
    ops = []
    for op in project.operations:
        d = dict(id=op.id, type=op.type.value, code=op.code, name=op.name,
                 cost_material=op.cost_material, cost_operation=op.cost_operation)
        if op.type == OpType.CS:
            res = op.result
            d.update(parts=[dict(uid=pt.uid, code=pt.code, name=pt.name, length=pt.length, width=pt.width,
                                 qty=total_qty(project, pt), used=pt.used_qty, left=pt.left_qty) for pt in op.parts])
            if res:
                d.update(sheets=res.total_sheets, material_m2=res.material_area_m2, parts_m2=res.parts_area_m2,
                         remnant_m2=res.remnant_area_m2, fill_percent=res.total_fill_percent,
                         cut_length_m=res.total_cut_length_m, cuts=res.total_cuts,
                         remnants=[dict(length=o.raw_length or o.length, width=o.raw_width or o.width,
                                        business=o.business) for o in res.remnants],
                         maps=[dict(index=m.index, copies=m.copies, done=m.done_count, sheet=[m.sheet_length, m.sheet_width],
                                    fill=m.fill_percent, parts=m.parts_count) for m in res.maps])
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            d.update(material_m=u["material_m"], work_m=u["work_m"])
        ops.append(d)
    return dict(project_id=project.id, number=project.number, mes_order_ref=project.mes_order_ref,
                name=project.name, customer=project.customer, status=int(project.status),
                cost_material=sum(o.cost_material for o in project.operations),
                cost_operation=sum(o.cost_operation for o in project.operations),
                warehouse=warehouse_request(project), operations=ops)


def send_webhook(event: str, payload: dict) -> None:
    """MES_WEBHOOK_URL o'rnatilgan bo'lsa JSON yuboradi (fon vazifasi, xatoda faqat log)."""
    url = os.getenv("MES_WEBHOOK_URL")
    if not url:
        return
    try:
        import httpx
        headers = {"Content-Type": "application/json"}
        token = os.getenv("MES_WEBHOOK_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        httpx.post(url, json={"event": event, **payload}, headers=headers, timeout=5.0)
    except Exception as e:  # noqa: BLE001
        log.warning("MES webhook xatosi (%s): %s", event, e)
