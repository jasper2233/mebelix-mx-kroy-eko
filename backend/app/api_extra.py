"""Qo'shimcha API: qoldiqlar ombori, sozlamalar profillari, postprotsessorlar, MES integratsiyasi."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from . import store
from .db import CatalogItemRow, RemnantRow, SessionLocal
from .i18n import _
from .models import OpType, OrderStatus, PostprocessorProfile
from .services import labels, mes, settings, warehouse
from .services.calc import total_qty
from .services.render import part_edges

router = APIRouter()


# ───────────────────────── Qoldiqlar ombori ─────────────────────────
class RemnantIn(BaseModel):
    material_code: str
    material_name: str = ""
    length: float
    width: float
    thickness: float = 16
    qty: int = 1
    note: str = ""


@router.get("/remnants", tags=["qoldiqlar"])
def remnants_list(material_code: Optional[str] = None, thickness: Optional[float] = None, q: str = "",
                  include_empty: bool = False):
    with SessionLocal() as s:
        st = select(RemnantRow)
        if material_code:
            st = st.where(RemnantRow.material_code == material_code)
        if thickness is not None:
            st = st.where(RemnantRow.thickness == thickness)
        if q:
            like = f"%{q}%"
            st = st.where(RemnantRow.material_code.ilike(like) | RemnantRow.material_name.ilike(like)
                          | RemnantRow.note.ilike(like))
        if not include_empty:
            st = st.where(RemnantRow.qty > 0)
        rows = s.scalars(st.order_by(RemnantRow.material_code, RemnantRow.length.desc())).all()
        return [warehouse.row_dict(r) for r in rows]


@router.post("/remnants", tags=["qoldiqlar"])
def remnants_add(r: RemnantIn):
    if r.length <= 0 or r.width <= 0 or r.qty <= 0:
        raise HTTPException(400, _("remnant_positive"))
    with SessionLocal() as s:
        row = RemnantRow(**r.model_dump())
        s.add(row); s.commit()
        return warehouse.row_dict(row)


class RemnantPatch(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None
    thickness: Optional[float] = None
    qty: Optional[int] = None
    note: Optional[str] = None


@router.patch("/remnants/{rid}", tags=["qoldiqlar"])
def remnants_patch(rid: int, f: RemnantPatch):
    upd = f.model_dump(exclude_unset=True, exclude_none=True)
    if any(upd.get(k, 1) <= 0 for k in ("length", "width")) or upd.get("qty", 0) < 0 \
            or upd.get("thickness", 1) < 0:
        raise HTTPException(400, _("remnant_positive"))
    with SessionLocal() as s:
        row = s.get(RemnantRow, rid)
        if row is None:
            raise HTTPException(404, _("remnant_not_found"))
        for k, v in upd.items():
            setattr(row, k, v)
        s.commit()
        return warehouse.row_dict(row)


@router.delete("/remnants/{rid}", tags=["qoldiqlar"])
def remnants_delete(rid: int):
    with SessionLocal() as s:
        n = s.query(RemnantRow).filter(RemnantRow.id == rid).delete()
        s.commit()
    if not n:
        raise HTTPException(404, _("remnant_not_found"))
    return {"ok": True}


# ───────────────────────── Sozlamalar profillari ─────────────────────────
class ProfileIn(BaseModel):
    name: str
    data: Any = None
    is_default: bool = False


class ProfilePatch(BaseModel):
    name: Optional[str] = None
    data: Any = None
    is_default: Optional[bool] = None


def _scope(scope: str) -> str:
    if scope not in settings.SCOPES:
        raise HTTPException(404, _("unknown_scope", s=scope))
    return scope


@router.get("/settings", tags=["sozlamalar"])
def settings_scopes():
    return {s: settings.builtin(s) for s in settings.SCOPES}


@router.get("/settings/{scope}/default", tags=["sozlamalar"])
def settings_get_default(scope: str):
    return settings.get_default(_scope(scope))


@router.put("/settings/{scope}/default", tags=["sozlamalar"])
def settings_set_default(scope: str, data: Any = Body(...)):
    """«Joriy parametrlarni standart sifatida saqlash»."""
    return settings.set_default(_scope(scope), data)


@router.get("/settings/{scope}", tags=["sozlamalar"])
def settings_list(scope: str):
    return settings.list_profiles(_scope(scope))


@router.post("/settings/{scope}", tags=["sozlamalar"])
def settings_create(scope: str, inp: ProfileIn):
    return settings.create(_scope(scope), inp.name, inp.data if inp.data is not None else settings.builtin(scope),
                           inp.is_default)


@router.put("/settings/{scope}/{pid}", tags=["sozlamalar"])
def settings_update(scope: str, pid: int, inp: ProfilePatch):
    try:
        return settings.update(_scope(scope), pid, inp.name, inp.data, inp.is_default)
    except KeyError as e:
        raise HTTPException(404, _("profile_not_found")) from e


@router.delete("/settings/{scope}/{pid}", tags=["sozlamalar"])
def settings_delete(scope: str, pid: int):
    try:
        settings.delete(_scope(scope), pid)
    except KeyError as e:
        raise HTTPException(404, _("profile_not_found")) from e
    return {"ok": True}


# ───────────────────────── Postprotsessorlar ─────────────────────────
@router.get("/postprocessors", tags=["postprotsessor"])
def postprocessors_list():
    from .services.postprocessors import BUILTIN
    out = [dict(key=k, name=v["name"], extension=v["extension"], builtin=True) for k, v in BUILTIN.items()]
    for pr in settings.list_profiles("postprocessor"):
        d = pr["data"]
        out.append(dict(key=f"pp:{pr['id']}", profile_id=pr["id"], name=pr["name"] or d.get("name", ""),
                        extension=d.get("extension", "txt"), builtin=False))
    return out


class PreviewIn(BaseModel):
    project_id: str
    op_id: str
    profile: PostprocessorProfile
    max_chars: int = 20000


@router.post("/postprocessors/preview", tags=["postprotsessor"])
def postprocessor_preview(inp: PreviewIn):
    """Shablon muharririda jonli ko'rish: birinchi fayl matni (yoki xato)."""
    from .services.postprocessors import context, render_limited
    from .services.tpl_sandbox import TemplateFailed, TemplateLimit
    p = store.load(inp.project_id)
    op = store.op_of(p, inp.op_id)
    if op.type != OpType.CS or not op.result or not op.result.maps:
        raise HTTPException(400, _("pp_sample"))
    ctx = context(p, op)
    limit = max(1000, min(inp.max_chars, 200_000))
    try:
        text = render_limited(inp.profile.template, {**ctx, "map": ctx["maps"][0]} if inp.profile.per_map else ctx)
    except TemplateLimit as e:
        return {"ok": False, "error": _("template_limit", e=e)}
    except TemplateFailed as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:  # noqa: BLE001 — shablon xatosi foydalanuvchiga (sintaksis, sandbox)
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "text": text[:limit], "truncated": len(text) > limit,
            "files": len(ctx["maps"]) if inp.profile.per_map else 1}


# ───────────────────────── MES integratsiyasi ─────────────────────────
@router.post("/mes/orders", tags=["mes"])
def mes_order(order: mes.MesOrder, background: BackgroundTasks, folder_id: Optional[str] = None):
    """MES buyurtmasini qabul qilish: loyiha yaratiladi (yoki hali tasdiqlanmagan bo'lsa yangilanadi)."""
    with SessionLocal() as s:
        cat = {}
        codes = {pt.material_code for pr in order.products for pt in pr.parts} | \
                {c for pr in order.products for pt in pr.parts for c in pt.edges.values() if c}
        if codes:
            for r in s.scalars(select(CatalogItemRow).where(CatalogItemRow.code.in_(codes))).all():
                cat[r.code] = dict(id=r.id, name=r.name, price=r.price, thickness=r.thickness, length=r.length,
                                   width=r.width, params=r.params or {})
    cs_def = settings.get_default("cs_defaults")
    el_def = settings.get_default("el_defaults")
    old = store.find_by_mes_ref(order.mes_order_ref)
    if old is not None and old.status >= OrderStatus.APPROVED:
        raise HTTPException(409, _("order_approved", ref=order.mes_order_ref, n=old.number))
    p = mes.build_project(order, cat, old.number if old else store.next_number(), cs_def, el_def)
    if old is not None:
        for op in old.operations:
            if op.type == OpType.CS and op.result and op.result.remnants_saved:
                warehouse.rollback(op)
        p.id, p.folder_id, p.owner = old.id, old.folder_id, old.owner
        # operatsiyalar id si va mahalliy sozlamalar (kesish parametrlari, listlar) saqlanadi
        prev = {(o.type, o.code): o for o in old.operations}
        remap: dict[str, str] = {}
        for op in p.operations:
            o = prev.get((op.type, op.code))
            if o is None:
                continue
            remap[op.id] = o.id
            op.id = o.id
            if op.type == OpType.CS:
                op.cs_cut = o.cs_cut or op.cs_cut
                if o.sheets:
                    op.sheets = [sh.model_copy(update={"used_qty": 0}) for sh in o.sheets]
            elif op.type == OpType.EL and o.el:
                op.el.symbol, op.el.color, op.el.overhang = o.el.symbol, o.el.color, o.el.overhang
        for op in p.operations:
            for pt in op.parts:
                for side in ("top", "bottom", "left", "right"):
                    ref = getattr(pt, f"edge_{side}")
                    if ref.op_id in remap:
                        ref.op_id = remap[ref.op_id]
    else:
        p.folder_id = folder_id
        p.owner = "MES"
    if old is None:
        store.save_new(p)
    else:
        store.save(p)
    background.add_task(mes.send_webhook, "project.created" if old is None else "project.updated",
                        dict(project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref))
    return p


@router.get("/mes/orders/{ref}", tags=["mes"])
def mes_order_get(ref: str):
    p = store.find_by_mes_ref(ref)
    if p is None:
        raise HTTPException(404, _("order_not_found"))
    return mes.export(p)


@router.get("/projects/{pid}/mes-export", tags=["mes"])
def mes_export(pid: str):
    return mes.export(store.load(pid))


def _scan(code: str) -> tuple[dict, Any]:
    info = labels.parse_qr(code)
    if info is None:
        raise HTTPException(400, _("qr_bad"))
    p = store.find_by_number(info["number"])
    if p is None:
        raise HTTPException(404, _("project_no_n", n=info["number"]))
    return info, p


@router.get("/mes/scan/{code:path}", tags=["mes"])
def mes_scan(code: str):
    """Etiketka yoki karta QR kodi bo'yicha ma'lumot (sex planshetlari / MES skaneri uchun)."""
    info, p = _scan(code)
    head = dict(project_id=p.id, number=p.number, name=p.name, customer=p.customer, mes_order_ref=p.mes_order_ref,
                status=int(p.status))
    if info["kind"] == "part":
        for op in p.operations:
            for pt in op.parts:
                if pt.uid == info["uid"]:
                    prod = next((x for x in p.products if x.id == pt.product_id), None)
                    maps = []
                    if op.result:
                        maps = [m.index for m in op.result.maps if any(pl.part_id == pt.id for pl in m.placements)]
                    return dict(kind="part", project=head, copy=info["copy"], total=info["total"],
                                part=dict(id=pt.id, uid=pt.uid, name=pt.name, code=pt.code, length=pt.length,
                                          width=pt.width, qty=total_qty(p, pt), grain=pt.grain,
                                          thickness=op.cs_material.thickness if op.cs_material else None,
                                          edges={k: v["name"] for k, v in part_edges(pt, p).items()},
                                          xnc=[o.code for o in p.operations if o.id in pt.xnc_op_ids]),
                                material=dict(op_id=op.id, name=op.name, code=op.code),
                                product=dict(id=prod.id, name=prod.name, code=prod.code) if prod else None,
                                maps=maps)
        raise HTTPException(404, _("part_uid_not_found", uid=info["uid"]))
    op = next((o for o in p.operations if o.id == info["op_id"]), None)
    if op is None or not op.result or not (1 <= info["map"] <= len(op.result.maps)):
        raise HTTPException(404, _("no_map"))
    m = op.result.maps[info["map"] - 1]
    parts = {pt.id: pt for pt in op.parts}
    return dict(kind="map", project=head, material=dict(op_id=op.id, name=op.name, code=op.code),
                map=dict(index=m.index, copies=m.copies, done=m.done_count, sheet=[m.sheet_length, m.sheet_width],
                         fill=m.fill_percent, cut_length_m=m.cut_length_m, comment=m.comment,
                         parts=[dict(uid=pl.part_uid, name=parts[pl.part_id].name if pl.part_id in parts else "",
                                     length=pl.length, width=pl.width) for pl in m.placements]))


@router.post("/mes/scan/{code:path}/done", tags=["mes"])
def mes_scan_done(code: str, background: BackgroundTasks, count: int = 1):
    """Karta QR kodi skanerlandi — shu kartadan kesilgan listlar soni +count (MES kuzatuvi)."""
    info, p = _scan(code)
    if info["kind"] != "map":
        raise HTTPException(400, _("scan_map_needed"))
    with store.editing(p.id, history=False) as pp:
        op = next((o for o in pp.operations if o.id == info["op_id"]), None)
        if op is None or not op.result or not (1 <= info["map"] <= len(op.result.maps)):
            raise HTTPException(404, _("no_map"))
        m = op.result.maps[info["map"] - 1]
        m.done_count = max(0, min(m.copies, m.done_count + count))
        done, copies = m.done_count, m.copies
    background.add_task(mes.send_webhook, "map.done", dict(project_id=pp.id, number=pp.number,
                                                           mes_order_ref=pp.mes_order_ref, op_id=info["op_id"],
                                                           map=info["map"], done=done, copies=copies))
    return dict(map=info["map"], done=done, copies=copies)


@router.post("/mes/webhook-test", tags=["mes"])
def mes_webhook_test():
    import os
    url = os.getenv("MES_WEBHOOK_URL")
    if not url:
        return {"sent": False, "reason": _("webhook_no_url")}
    mes.send_webhook("test", {"message": "MebeliX Kroy webhook sinovi"})
    return {"sent": True, "url": url}
