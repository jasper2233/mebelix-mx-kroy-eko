"""MES integratsiyasi: buyurtma qabul qilish, natija eksporti, webhook, QR skanerlash.

1) MES → MebeliX:  POST /api/mes/orders   (MesOrder JSON)
   Har material kodi uchun (CS) operatsiya, har kromka kodi uchun (EL) operatsiya yaratiladi.
   Material/kromka parametrlari: so'rovdagi `materials` / `edges` ro'yxatidan, bo'lmasa katalogdan (catalog_items).
2) MebeliX → MES:  GET /api/projects/{id}/mes-export — sarf (list, m², kromka m), qoldiqlar, narxlar, kartalar.
3) Webhook: loyiha holati o'zgarsa yoki karta kesib bo'linsa MES_WEBHOOK_URL ga POST (JSON); xato bo'lsa
   (ulanish, timeout, HTTP ≥ 500/408/429) qisqa kutish bilan qayta uriniladi (fon vazifasida).
4) Skaner: GET /api/mes/scan/{qr} — etiketkadagi QR bo'yicha detal ma'lumoti.
5) Qayta yuborish (tasdiqlanmagan buyurtma): `merge_order` — MES ga tegishli maydonlar yangilanadi, kroychining
   lokal ishi (holat, o'lcham rejimi, izoh, XNC/GR/EL tahrirlari, boshqa operatsiyalar) saqlanadi.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from ..i18n import _
from ..models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, OpType, Operation, Part, Product,
                      Project, SizeMode, StockSheet)
from .calc import edge_usage, edge_map, product_qty, total_qty, warehouse_request

log = logging.getLogger("mebelix.mes")

MAX_DIM = 100_000            # mm
MAX_QTY = 100_000
PART_ID_PREFIX = "mx"        # MES dan kelgan detal id si: «mx» + hash (oddiy id lar hex — «m»/«x» bo'lmaydi)


class MesPart(BaseModel):
    name: str = ""
    code: str = ""
    material_code: str = Field(min_length=1, max_length=100)
    length: float = Field(gt=0, le=MAX_DIM, allow_inf_nan=False)
    width: float = Field(gt=0, le=MAX_DIM, allow_inf_nan=False)
    qty: int = Field(1, ge=0, le=MAX_QTY)
    grain: bool = False
    edges: dict[str, Optional[str]] = {}      # top/bottom/left/right → kromka kodi
    line_id: Optional[str] = Field(None, max_length=100)   # MES dagi qator ID si (ixtiyoriy): qayta yuborishda detalni aniq topadi


class MesProduct(BaseModel):
    code: str = ""
    name: str
    qty: int = Field(1, ge=0, le=MAX_QTY)
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
    mes_order_ref: str = Field(max_length=100)
    name: str = ""
    customer: str = ""
    currency: str = "UZS"
    order_date: Optional[date] = None
    ready_date: Optional[date] = None
    note: str = ""
    products: list[MesProduct] = []
    materials: list[MesMaterial] = []
    edges: list[MesEdge] = []

    @field_validator("mes_order_ref")
    @classmethod
    def _ref(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError(_("val_missing"))
        return v


def part_id(ref: str, key: str) -> str:
    """MES dagi detal qatori uchun turg'un id: qayta yuborilganda o'sha id (printerdan chiqqan etiketkalar buzilmaydi)."""
    return PART_ID_PREFIX + hashlib.sha1(f"{ref}\x00{key}".encode("utf-8")).hexdigest()[:10]


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
    keys: set[str] = set()
    for pr in order.products:
        prod = Product(code=pr.code, name=pr.name, qty=pr.qty)
        p.products.append(prod)
        for mp in pr.parts:
            uid += 1
            key = (mp.line_id or "").strip() or f"#{uid}"       # MES qator ID si yoki tartib raqami
            while key in keys:
                key += "'"
            keys.add(key)
            part = Part(id=part_id(order.mes_order_ref, key), uid=uid, product_id=prod.id, name=mp.name,
                        code=mp.code, length=mp.length, width=mp.width, qty=mp.qty, grain=mp.grain)
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
        elif op.type == OpType.CL:                 # (CL) pogonaj kroy: polosa eni, material uzunligi (m), qoldiqlar, kartalar
            from .cl_calc import mes_payload as cl_mes_payload
            d.update(cl_mes_payload(project, op))
        elif op.type == OpType.CN:                 # (CN) nesting: kontur detallar, kartalar (joylashuv + burchak), qoldiqlar (W16)
            from .cn_calc import mes_payload as cn_mes_payload
            d.update(cn_mes_payload(project, op))
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            d.update(material_m=u["material_m"], work_m=u["work_m"])
        elif op.type == OpType.SP:                 # sirt ishlovi (W12): ishlov maydoni va material sarfi, m²
            from .calc import surface_usage
            u = surface_usage(project, op)
            d.update(area_m2=u["area_m2"], material_m2=u["material_m2"])
        elif op.type == OpType.O:                  # komplektatsiya: egasi, ko'paytirgich, materiallar (furnitura)
            from .o_ops import mes_payload
            d.update(mes_payload(project, op))
        ops.append(d)
    return dict(project_id=project.id, number=project.number, mes_order_ref=project.mes_order_ref,
                name=project.name, customer=project.customer, status=int(project.status),
                cost_material=sum(o.cost_material for o in project.operations),
                cost_operation=sum(o.cost_operation for o in project.operations),
                warehouse=warehouse_request(project), operations=ops)


# ───────────────────────── Webhook ─────────────────────────
def _env_num(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _post_once(url: str, event: str, payload: dict, timeout: float) -> dict:
    """Bitta urinish. Natija: {sent, status, error, elapsed_ms}; HTTP ≥ 400 va istisnolar — sent=False."""
    t0 = time.monotonic()

    def ms() -> int:
        return int((time.monotonic() - t0) * 1000)
    try:
        import httpx
        headers = {"Content-Type": "application/json"}
        token = os.getenv("MES_WEBHOOK_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = httpx.post(url, json={"event": event, **payload}, headers=headers, timeout=timeout)
        status = getattr(r, "status_code", None)
        if isinstance(status, int) and status >= 400:
            return dict(sent=False, status=status, error=f"HTTP {status}", elapsed_ms=ms())
        return dict(sent=True, status=status if isinstance(status, int) else None, error=None, elapsed_ms=ms())
    except Exception as e:  # noqa: BLE001 — ulanish, timeout, DNS, TLS ...
        return dict(sent=False, status=None, error=f"{type(e).__name__}: {e}".rstrip(": ")[:300], elapsed_ms=ms())


def _retryable(res: dict) -> bool:
    st = res.get("status")
    return st is None or st >= 500 or st in (408, 429)       # ulanish xatosi, server xatosi, timeout, «ko'p so'rov»


def send_webhook(event: str, payload: dict, attempts: Optional[int] = None) -> dict:
    """MES_WEBHOOK_URL o'rnatilgan bo'lsa JSON yuboradi. Hodisalar fon vazifasida chaqiriladi (API ni bloklamaydi):
    vaqtinchalik xato bo'lsa qayta uriniladi (standart 3 urinish, kutish 1 s, 2 s — `MES_WEBHOOK_RETRIES`,
    `MES_WEBHOOK_RETRY_DELAY`); har urinish va yakuniy xato logga yoziladi. `MES_WEBHOOK_TIMEOUT` (standart 5 s).
    Qaytaradi: {sent, status, error, elapsed_ms, attempts} (URL yo'q bo'lsa: sent=False, attempts=0)."""
    url = os.getenv("MES_WEBHOOK_URL")
    if not url:
        return dict(sent=False, status=None, error=None, elapsed_ms=0, attempts=0)
    n = attempts if attempts is not None else max(1, int(_env_num("MES_WEBHOOK_RETRIES", 3)))
    delay = max(0.0, _env_num("MES_WEBHOOK_RETRY_DELAY", 1.0))
    timeout = max(0.1, _env_num("MES_WEBHOOK_TIMEOUT", 5.0))
    res: dict = {}
    for i in range(1, n + 1):
        res = _post_once(url, event, payload, timeout)
        res["attempts"] = i
        if res["sent"]:
            if i > 1:
                log.info("MES webhook (%s): %d-urinishda yuborildi", event, i)
            return res
        log.warning("MES webhook xatosi (%s), urinish %d/%d: %s", event, i, n, res["error"])
        if i < n and _retryable(res):
            if delay:
                time.sleep(delay * i)
            continue
        break
    log.error("MES webhook yuborilmadi (%s): %s (%d urinish)", event, res.get("error"), res.get("attempts", 0))
    return res


# ───────────────────────── Buyurtmani qayta yuborish: mavjud loyiha bilan birlashtirish ─────────────────────────
_SIDES = ("top", "bottom", "left", "right")


def _sig(project: Project, op: Operation) -> str:
    """CS operatsiyasining kroyga ta'sir qiluvchi holati: detallar (o'lcham/soni/kromka/mahsulot soni), kromka
    qalinligi, listlar. Kroy natijasi shu o'zgarmasa saqlanadi."""
    edges = {o.id: (o.el.thickness, o.el.jointing_width) for o in project.operations if o.type == OpType.EL and o.el}
    parts = [[pt.model_dump(mode="json", exclude={"used_qty", "left_qty"}), product_qty(project, pt),
              [edges.get(getattr(pt, f"edge_{s}").op_id) for s in _SIDES]] for pt in op.parts]
    sheets = [sh.model_dump(mode="json", exclude={"used_qty"}) for sh in op.sheets]
    return json.dumps([parts, sheets], sort_keys=True, default=str)


def _stale(op: Operation) -> None:
    """Kroy natijasi eskirdi (omborga yozilgan qoldiqlar bekor qilinadi)."""
    from . import warehouse
    if op.result is not None:
        warehouse.rollback(op)
    op.result = None
    for pt in op.parts:
        pt.used_qty = pt.left_qty = 0
    for sh in op.sheets:
        sh.used_qty = 0


def _drop_op(project: Project, op: Operation) -> None:
    from . import warehouse
    if op.type == OpType.CS and op.result is not None:
        warehouse.rollback(op)
    project.operations = [x for x in project.operations if x.id != op.id]


def _rename_part(project: Project, pt: Part, new_id: str) -> None:
    """Detal id sini almashtirish (eski loyihalar: tasodifiy id → MES id) — havolalar va natija yangilanadi."""
    old = pt.id
    pt.id = new_id
    for o in project.operations:
        if o.xnc_part_id == old:
            o.xnc_part_id = new_id
        if o.result is not None:
            o.result.unplaced = [new_id if x == old else x for x in o.result.unplaced]
            for m in o.result.maps:
                for pl in m.placements:
                    if pl.part_id == old:
                        pl.part_id = new_id


def merge_order(cur: Project, new: Project, order: MesOrder, catalog: Optional[dict] = None) -> dict:
    """Tasdiqlanmagan loyihaga (`cur`) MES buyurtmasini (`new` — buyurtmadan yangidan qurilgan loyiha) qo'shish.

    MES ga tegishli (payloadda berilgan bo'lsa yangilanadi): mahsulotlar (kod/nom/soni), detallar (nom, kod, o'lcham,
    soni, tekstura, kromka), material va kromka parametrlari (qalinlik/narx/list o'lchami — MES yoki katalog bergan
    bo'lsa), loyiha nomi, buyurtmachi, valyuta, sanalar. Detal `Part.id` bo'yicha topiladi (MES qator ID si yoki
    tartib raqami): id/uid turg'un, yangilari qo'shiladi, MES da yo'q bo'lganlari o'chiriladi.
    Lokal (saqlanadi): holat, o'lcham rejimi, izoh, papka, egasi, raqami, MES ga tegishli bo'lmagan operatsiyalar
    (XNC/GR/EL, CS parametrlari, listlar), detalning MES bermagan maydonlari (paz, pripusk, guruh, XNC ...) va
    lokal qo'shilgan detallar. Kroy natijasi faqat kroyga ta'sir qiladigan narsa o'zgarsa bekor qilinadi."""
    catalog = catalog or {}
    given = order.model_fields_set
    stats = dict(parts_added=0, parts_updated=0, parts_removed=0)
    cs_before = {o.id: o for o in cur.operations if o.type == OpType.CS}
    before = {oid: _sig(cur, o) for oid, o in cs_before.items()}
    count_before = {oid: len(o.parts) for oid, o in cs_before.items()}
    new_op_parts = {o.id: list(o.parts) for o in new.operations if o.type == OpType.CS}

    # 1) sarlavha
    if "name" in given and order.name.strip():
        cur.name = order.name.strip()
    elif not cur.name.strip():
        cur.name = new.name
    if "customer" in given and order.customer.strip():
        cur.customer = order.customer.strip()
    if "currency" in given and order.currency.strip():
        cur.currency = order.currency.strip()
    if order.order_date:
        cur.order_date = order.order_date
    if order.ready_date:
        cur.ready_date = order.ready_date
    if not cur.note.strip() and order.note.strip():          # lokal izoh bor bo'lsa — saqlanadi
        cur.note = order.note

    # 2) mahsulotlar
    had_parts = {pt.product_id for o in cur.operations for pt in o.parts if pt.product_id}
    used_prod: set[str] = set()
    prod_map: dict[str, str] = {}                # yangi mahsulot id → yakuniy mahsulot id
    for npr in new.products:
        cands = [x for x in cur.products if x.id not in used_prod]
        hit = next((x for x in cands if npr.code and x.code == npr.code and x.name == npr.name), None) \
            or next((x for x in cands if npr.code and x.code == npr.code), None) \
            or next((x for x in cands if x.name == npr.name and not (npr.code and x.code and x.code != npr.code)), None)
        if hit is None:
            cur.products.append(npr)
            hit = npr
        else:
            hit.code, hit.name, hit.qty = npr.code, npr.name, npr.qty
        prod_map[npr.id] = hit.id
        used_prod.add(hit.id)

    # 3) operatsiyalar: (tur, kod) bo'yicha
    by_key: dict[tuple, Operation] = {}
    for o in cur.operations:
        if o.type in (OpType.CS, OpType.EL):
            by_key.setdefault((o.type, o.code), o)
    mat_known = {m.code for m in order.materials} | set(catalog)
    edge_known = {e.code for e in order.edges} | set(catalog)
    edge_given = {e.code: e for e in order.edges}
    op_map: dict[str, Operation] = {}            # yangi operatsiya id → yakuniy operatsiya
    appended: list[Operation] = []
    for nop in new.operations:
        o = by_key.get((nop.type, nop.code))
        if o is None:                            # MES da bor, loyihada yo'q — yangi operatsiya (detallar pastda)
            nop.parts = []
            op_map[nop.id] = nop
            appended.append(nop)
            continue
        op_map[nop.id] = o
        if nop.type == OpType.EL and o.el is not None and nop.el is not None and nop.code in edge_known:
            o.name = nop.name or o.name
            o.material_id = nop.material_id or o.material_id
            o.el.thickness, o.el.width, o.el.price = nop.el.thickness, nop.el.width, nop.el.price
            e = edge_given.get(nop.code)
            if e is not None and e.symbol:
                o.el.symbol = nop.el.symbol
            if e is not None and e.color:
                o.el.color = nop.el.color
        elif nop.type == OpType.CS and o.cs_material is not None and nop.cs_material is not None \
                and nop.code in mat_known:
            o.name = nop.name or o.name
            o.material_id = nop.material_id or o.material_id
            o.cs_material.thickness = nop.cs_material.thickness
            o.cs_material.price = nop.cs_material.price
            o.cs_material.cost_by_sheets = nop.cs_material.cost_by_sheets
            ns = nop.sheets[0] if nop.sheets else None
            if ns is not None and len(o.sheets) == 1 and not o.sheets[0].is_remnant and o.sheets[0].qty >= 10000 \
                    and (o.sheets[0].length, o.sheets[0].width) != (ns.length, ns.width):
                o.sheets = [o.sheets[0].model_copy(update={"length": ns.length, "width": ns.width})]
    for nop in appended:                         # yangi CS — oxirgi CS dan keyin, yangi EL — oxirgi EL dan keyin
        idx = max((i for i, o in enumerate(cur.operations) if o.type == nop.type), default=-1)
        if idx < 0 and nop.type == OpType.EL:
            idx = max((i for i, o in enumerate(cur.operations) if o.type == OpType.CS), default=-1)
        cur.operations.insert(idx + 1, nop)

    # 4) detallar
    mes_parts: dict[int, MesPart] = {}
    u = 0
    for pr in order.products:
        for mp in pr.parts:
            u += 1
            mes_parts[u] = mp
    old_parts: dict[str, tuple[Operation, Part]] = {}
    by_uid: dict[int, tuple[Operation, Part]] = {}
    for o in cs_before.values():
        for pt in o.parts:
            old_parts.setdefault(pt.id, (o, pt))
            by_uid.setdefault(pt.uid, (o, pt))
    legacy = not any(pid.startswith(PART_ID_PREFIX) for pid in old_parts)    # eski loyiha: id lar tasodifiy

    def edge_ref(ref: EdgeRef) -> EdgeRef:
        tgt = op_map.get(ref.op_id) if ref.op_id else None
        return EdgeRef(op_id=tgt.id if tgt else None)

    matched: dict[str, Operation] = {}           # topilgan detal id → joylashishi kerak bo'lgan operatsiya
    synced: list[Part] = []                      # MES dan yangilangan/yaratilgan detallar
    fresh: set[str] = set()                      # yangi yaratilgan detallar id si
    to_add: dict[str, list[Part]] = {}           # operatsiya id → yangi detallar
    moved_in: dict[str, list[Part]] = {}         # operatsiya id → boshqa operatsiyadan kelgan detallar
    for nop in new.operations:
        if nop.type != OpType.CS:
            continue
        tgt = op_map[nop.id]
        for npt in new_op_parts[nop.id]:
            mp = mes_parts.get(npt.uid)
            hit = old_parts.get(npt.id) or (by_uid.get(npt.uid) if legacy else None)
            if hit is not None and hit[1].id in matched:
                hit = None
            if hit is None:
                npt.product_id = prod_map.get(npt.product_id or "", npt.product_id)
                for s in _SIDES:
                    setattr(npt, f"edge_{s}", edge_ref(getattr(npt, f"edge_{s}")))
                to_add.setdefault(tgt.id, []).append(npt)
                fresh.add(npt.id)
                synced.append(npt)
                stats["parts_added"] += 1
                continue
            src_op, pt = hit
            if pt.id != npt.id:                  # eski loyiha — id MES id siga o'tkaziladi (havolalar yangilanadi)
                _rename_part(cur, pt, npt.id)
            matched[pt.id] = tgt
            f = mp.model_fields_set if mp is not None else set()
            if "name" in f:
                pt.name = npt.name
            if "code" in f:
                pt.code = npt.code
            if "qty" in f:
                pt.qty = npt.qty
            if "grain" in f:
                pt.grain = npt.grain
            pt.length, pt.width = npt.length, npt.width
            pt.product_id = prod_map.get(npt.product_id or "", npt.product_id)
            if "edges" in f:
                for s in _SIDES:
                    setattr(pt, f"edge_{s}", edge_ref(getattr(npt, f"edge_{s}")))
            if src_op.id != tgt.id:
                moved_in.setdefault(tgt.id, []).append(pt)
            synced.append(pt)
            stats["parts_updated"] += 1
    removed_ids: set[str] = set()
    for o in cs_before.values():
        kept = []
        for pt in o.parts:
            tgt = matched.get(pt.id)
            if tgt is not None:
                if tgt.id == o.id:
                    kept.append(pt)              # joyida qoladi (tartib saqlanadi)
            elif legacy or pt.id.startswith(PART_ID_PREFIX):
                removed_ids.add(pt.id)           # MES da endi yo'q
                stats["parts_removed"] += 1
            else:
                kept.append(pt)                  # lokal qo'shilgan detal
        o.parts = kept
    # yangi / ko'chirilgan detallar operatsiya oxiriga; yangi detal tartib raqamini (uid) oladi, band bo'lsa — keyingisini
    used_uid = {pt.uid for o in cur.operations for pt in o.parts} | {pt.uid for v in moved_in.values() for pt in v}
    for o in cur.operations:
        if o.type != OpType.CS:
            continue
        add = moved_in.get(o.id, []) + to_add.get(o.id, [])
        for pt in add:
            if pt.id in fresh:
                if pt.uid <= 0 or pt.uid in used_uid:
                    pt.uid = max(used_uid, default=0) + 1
                used_uid.add(pt.uid)
        o.parts = o.parts + add

    # 5) bo'shab qolgan MES operatsiyalari, o'chirilgan detallarning XNC lari, detalsiz qolgan mahsulotlar
    target_ids = {x.id for x in op_map.values()}
    for oid, o in cs_before.items():
        if oid not in target_ids and not o.parts and count_before[oid] > 0:
            _drop_op(cur, o)
    for o in list(cur.operations):
        if o.type == OpType.XNC and o.xnc_part_id in removed_ids:
            _drop_op(cur, o)
    live = {o.id for o in cur.operations}
    for o in cur.operations:
        for pt in o.parts:
            if any(x not in live for x in pt.xnc_op_ids):
                pt.xnc_op_ids = [x for x in pt.xnc_op_ids if x in live]
    have_prod = {pt.product_id for o in cur.operations for pt in o.parts}
    cur.products = [x for x in cur.products if x.id in used_prod or x.id not in had_parts or x.id in have_prod]

    # 6) lokal o'lcham rejimi: MES o'lchamlari — «detal o'lchami»; loyiha rejimiga o'giriladi (jismoniy o'lcham saqlanadi)
    if cur.size_mode != SizeMode.DETAIL and synced:
        from .sizes import compute_sizes
        em = edge_map(cur)
        for pt in synced:
            s = compute_sizes(pt, SizeMode.DETAIL, em)
            L, W = {"blank": s.blank, "detail": s.detail, "jointed": s.jointed}[cur.size_mode.value]
            pt.length, pt.width = round(L, 3), round(W, 3)

    # 7) kroy natijasi: faqat kroyga ta'sir qiluvchi narsa o'zgargan bo'lsa bekor qilinadi
    for o in cur.operations:
        if o.type == OpType.CS and o.id in before and _sig(cur, o) != before[o.id]:
            _stale(o)
    return stats


