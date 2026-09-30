"""MebeliX Kroy — REST API (FastAPI).

Ishga tushirish:  uvicorn app.main:app --reload --port 8000
Hujjat:           http://localhost:8000/docs
Frontend (build qilingan bo'lsa) shu server orqali ochiladi: http://localhost:8000/
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal, Optional
from uuid import uuid4

from fastapi import (APIRouter, BackgroundTasks, Body, Depends, FastAPI, File, Form, HTTPException, Query,
                     Request, UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select

from . import store
from .auth import current_user
from .i18n import _, set_lang
from .db import CatalogItemRow, FolderRow, ProjectRow, RemnantRow, SessionLocal, init_db
from .models import (CSCutParams, CSMaterialParams, CuttingResult, EdgeRef, ELParams, FirstCutDir, GRParams,
                     LabelSettings, OpType, Operation, OrderStatus, Part, PrintSettings, Product, Project,
                     StockSheet, XNCParams)
from .services import calc, editor, labels, mes, render, settings, warehouse
from .services.importers import import_parts
from .services.xnc import xnc_cost, xnc_drawing_svg

VERSION = "2.0.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    settings.seed()
    yield


app = FastAPI(title="MebeliX Kroy API", version=VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("MEBELIX_CORS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])
app.add_middleware(GZipMiddleware, minimum_size=2048)

api = APIRouter(prefix="/api", dependencies=[Depends(current_user)])


@app.middleware("http")
async def _lang_mw(request: Request, call_next):
    """Xabarlar tili: Accept-Language (frontend UI tilini yuboradi)."""
    set_lang(request.headers.get("accept-language"))
    return await call_next(request)


@app.exception_handler(editor.EditError)
async def _edit_error(_req: Request, e: editor.EditError):
    return JSONResponse(status_code=422, content={"detail": str(e), "details": e.details})


@app.exception_handler(settings.SettingsError)
async def _settings_error(_req: Request, e: settings.SettingsError):
    return JSONResponse(status_code=400, content={"detail": str(e)})


@app.get("/api/health", tags=["tizim"])
def health():
    return {"ok": True, "app": "MebeliX Kroy", "version": VERSION}


# ───────────────────────── Yordamchilar (eski nomlar saqlangan) ─────────────────────────
_load = store.load
_save = store.save
_op = store.op_of
_part = store.part_of
_next_uid = store.next_uid


def _invalidate(op: Operation) -> None:
    """Detallar/listlar o'zgardi — kroy natijasi eskirdi (omborga yozilgan qoldiqlar bekor qilinadi)."""
    if op.result is not None:
        warehouse.rollback(op)
    op.result = None
    for pt in op.parts:
        pt.used_qty = pt.left_qty = 0
    for sh in op.sheets:
        sh.used_qty = 0


def _replace_result(op: Operation) -> None:
    """Natija yangisi bilan almashtirilishidan oldin — omborga yozilgan qoldiqlarni bekor qilish."""
    if op.result is not None and op.result.remnants_saved:
        warehouse.rollback(op)


def _need_cs(op: Operation) -> None:
    if op.type != OpType.CS:
        raise HTTPException(400, _("cs_only"))


@api.get("/me", tags=["tizim"])
def me(user: dict = Depends(current_user)):
    return {k: v for k, v in user.items() if k != "claims"}


# ───────────────────────── Papkalar ─────────────────────────
class FolderIn(BaseModel):
    name: str
    parent_id: Optional[str] = None


class FolderPatch(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None


def _folder(r: FolderRow) -> dict:
    return dict(id=r.id, name=r.name, parent_id=r.parent_id)


@api.get("/folders", tags=["loyihalar"])
def list_folders(parent_id: Optional[str] = None):
    with SessionLocal() as s:
        rows = s.scalars(select(FolderRow).where(FolderRow.parent_id == parent_id).order_by(FolderRow.name)).all()
        return [_folder(r) for r in rows]


@api.get("/folders/all", tags=["loyihalar"])
def all_folders():
    with SessionLocal() as s:
        return [_folder(r) for r in s.scalars(select(FolderRow).order_by(FolderRow.name)).all()]


@api.get("/folders/{fid}/path", tags=["loyihalar"])
def folder_path(fid: str):
    out = []
    with SessionLocal() as s:
        cur = s.get(FolderRow, fid)
        seen = set()
        while cur is not None and cur.id not in seen:
            seen.add(cur.id)
            out.append(_folder(cur))
            cur = s.get(FolderRow, cur.parent_id) if cur.parent_id else None
    return list(reversed(out))


@api.post("/folders", tags=["loyihalar"])
def create_folder(f: FolderIn, user: dict = Depends(current_user)):
    with SessionLocal() as s:
        r = FolderRow(id=uuid4().hex[:12], name=f.name.strip() or "Papka", parent_id=f.parent_id, owner=user["name"])
        s.add(r); s.commit()
        return _folder(r)


@api.patch("/folders/{fid}", tags=["loyihalar"])
def rename_folder(fid: str, f: FolderPatch):
    with SessionLocal() as s:
        r = s.get(FolderRow, fid)
        if not r:
            raise HTTPException(404, _("folder_not_found"))
        if f.name is not None:
            r.name = f.name.strip() or r.name
        if "parent_id" in f.model_fields_set:
            # papkani o'z ichiga ko'chirishning oldini olish
            cur = f.parent_id
            while cur:
                if cur == fid:
                    raise HTTPException(400, _("folder_into_itself"))
                row = s.get(FolderRow, cur)
                cur = row.parent_id if row else None
            r.parent_id = f.parent_id
        s.commit()
        return _folder(r)


@api.delete("/folders/{fid}", tags=["loyihalar"])
def delete_folder(fid: str, recursive: bool = False):
    with SessionLocal() as s:
        r = s.get(FolderRow, fid)
        if not r:
            raise HTTPException(404, _("folder_not_found"))
        ids, stack = [], [fid]
        while stack:
            cur = stack.pop()
            ids.append(cur)
            stack += [x.id for x in s.scalars(select(FolderRow).where(FolderRow.parent_id == cur)).all()]
        projects = s.scalars(select(ProjectRow.id).where(ProjectRow.folder_id.in_(ids))).all()
        if (projects or len(ids) > 1) and not recursive:
            raise HTTPException(409, _("folder_not_empty"))
    for pid in projects:
        store.delete(pid)
    with SessionLocal() as s:
        for cur in reversed(ids):
            s.query(FolderRow).filter(FolderRow.id == cur).delete()
        s.commit()
    return {"ok": True, "deleted_projects": len(projects)}


# ───────────────────────── Loyihalar ─────────────────────────
@api.get("/projects", tags=["loyihalar"])
def list_projects(folder_id: Optional[str] = None, q: str = "", status: Optional[int] = None,
                  all_folders: bool = False):
    """Проекты ro'yxati: ID, Владелец, Состояние, Дата, Стоимость, Наименование.
    q berilsa — barcha papkalar bo'yicha qidiruv (nomi, raqami, buyurtmachi, MES raqami)."""
    with SessionLocal() as s:
        st = select(ProjectRow)
        if q:
            like = f"%{q}%"
            cond = ProjectRow.name.ilike(like) | ProjectRow.customer.ilike(like) | ProjectRow.mes_order_ref.ilike(like)
            if q.strip().isdigit():
                cond = cond | (ProjectRow.number == int(q.strip()))
            st = st.where(cond)
        elif not all_folders:
            st = st.where(ProjectRow.folder_id == folder_id)
        if status is not None:
            st = st.where(ProjectRow.status == status)
        rows = s.scalars(st.order_by(ProjectRow.number)).all()
        return [dict(id=r.id, number=r.number, owner=r.owner, status=r.status, order_date=r.order_date,
                     cost=r.cost, name=r.name, folder_id=r.folder_id, customer=r.customer or "",
                     mes_order_ref=r.mes_order_ref,
                     updated_at=r.updated_at.isoformat() if r.updated_at else None) for r in rows]


class ProjectIn(BaseModel):
    name: str = "Nomsiz"
    folder_id: Optional[str] = None
    currency: Optional[str] = None
    owner: str = ""
    customer: str = ""
    mes_order_ref: Optional[str] = None


@api.post("/projects", tags=["loyihalar"])
def create_project(inp: ProjectIn, user: dict = Depends(current_user)):
    app_cfg = settings.get_default("app")
    data = inp.model_dump()
    data["currency"] = data["currency"] or app_cfg.get("currency", "UZS")
    data["owner"] = data["owner"] or user["name"]
    p = Project(number=store.next_number(), **data)
    p.products.append(Product(name="Изделие 1"))
    return _save(p)


@api.get("/projects/{pid}", tags=["loyihalar"])
def get_project(pid: str):
    return _load(pid)


class ProjectHeader(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    order_date: Optional[str] = None
    ready_date: Optional[str] = None
    note: Optional[str] = None
    status: Optional[OrderStatus] = None
    size_mode: Optional[str] = None
    folder_id: Optional[str] = None
    customer: Optional[str] = None
    owner: Optional[str] = None
    mes_order_ref: Optional[str] = None


NULLABLE_HEADER = {"folder_id", "mes_order_ref"}


@api.patch("/projects/{pid}", tags=["loyihalar"])
def update_project_header(pid: str, h: ProjectHeader, background: BackgroundTasks):
    with store.editing(pid) as p:
        old_status = p.status
        old_mode = p.size_mode
        upd = p.model_dump()
        for k, v in h.model_dump(exclude_unset=True).items():
            if v is None and k not in NULLABLE_HEADER:
                continue
            upd[k] = v
        new = Project.model_validate(upd)
        for k in upd:
            setattr(p, k, getattr(new, k))
        if p.size_mode != old_mode:
            # O'lcham kiritish rejimi o'zgardi — detallar jismoniy o'lchami saqlanadi (qiymatlar yangi rejimga o'giriladi)
            from .services.sizes import compute_sizes
            edges = calc.edge_map(p)
            for o in p.operations:
                for pt in o.parts:
                    s = compute_sizes(pt, old_mode, edges)
                    L, W = {"blank": s.blank, "detail": s.detail, "jointed": s.jointed}[p.size_mode.value]
                    pt.length, pt.width = round(L, 3), round(W, 3)
    if p.status != old_status:
        background.add_task(mes.send_webhook, "project.status", dict(
            project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, status=int(p.status),
            old_status=int(old_status)))
    return p


@api.delete("/projects/{pid}", tags=["loyihalar"])
def delete_project(pid: str):
    p = _load(pid)
    for op in p.operations:
        if op.type == OpType.CS and op.result and op.result.remnants_saved:
            warehouse.rollback(op)
    store.delete(pid)
    return {"ok": True}


class MoveProjects(BaseModel):
    ids: list[str]
    folder_id: Optional[str] = None


@api.post("/projects/move", tags=["loyihalar"])
def move_projects(m: MoveProjects):
    for pid in m.ids:
        with store.editing(pid, history=False) as p:
            p.folder_id = m.folder_id
    return {"ok": True, "count": len(m.ids)}


@api.post("/projects/{pid}/copy", tags=["loyihalar"])
def copy_project(pid: str, name: Optional[str] = None, folder_id: Optional[str] = None,
                 user: dict = Depends(current_user)):
    p = _load(pid)
    p.id = uuid4().hex[:12]
    p.number = store.next_number()
    p.name = name or (p.name + " (nusxa)")
    p.status = OrderStatus.NOT_ORDERED
    p.mes_order_ref = None
    p.owner = user["name"] or p.owner
    if folder_id is not None:
        p.folder_id = folder_id or None
    for op in p.operations:        # omborga bog'lanish nusxalanmaydi
        if op.result:
            op.result.remnants_saved = False
            op.result.saved_remnant_ids = []
            op.result.consumed_remnants = {}
            for m in op.result.maps:
                m.done_count = 0
    return _save(p)


@api.post("/projects/{pid}/save", tags=["loyihalar"])
def save_project(pid: str):
    """«Сохранить»: loyiha har o'zgarishda saqlanadi; bu amal hisob-kitobni yangilab, versiya yozadi."""
    with store.editing(pid) as p:
        pass
    return p


@api.post("/projects/{pid}/undo", tags=["loyihalar"])
def undo(pid: str):
    return store.step(pid, -1)


@api.post("/projects/{pid}/redo", tags=["loyihalar"])
def redo(pid: str):
    return store.step(pid, +1)


@api.get("/projects/{pid}/history", tags=["loyihalar"])
def history(pid: str):
    return store.history_info(pid)


@api.get("/projects/{pid}/export", tags=["loyihalar"])
def export_project(pid: str):
    p = _load(pid)
    return Response(p.model_dump_json(indent=2), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{p.number}.mxk.json"'})


def _import_bytes(data: bytes, filename: str) -> tuple[Project, list[str]]:
    from .plugins import find
    plug = find(filename)
    if plug is not None:
        try:
            return plug[1](data, filename)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    try:
        return Project.model_validate_json(data), []
    except ValueError as e:
        raise HTTPException(400, _("bad_project_file", e=e)) from e


def _store_imported(p: Project, folder_id: Optional[str], owner: str) -> Project:
    p.number = store.next_number()
    p.id = uuid4().hex[:12]
    p.folder_id = folder_id or None
    p.owner = p.owner or owner
    return _save(p)


@api.post("/projects/import", tags=["loyihalar"])
async def import_project(file: UploadFile = File(...), folder_id: Optional[str] = Form(None),
                         user: dict = Depends(current_user)):
    p, _w = _import_bytes(await file.read(), file.filename or "")
    return _store_imported(p, folder_id, user["name"])


@api.post("/projects/import-file", tags=["loyihalar"])
async def import_project_file(file: UploadFile = File(...), folder_id: Optional[str] = Form(None),
                              user: dict = Depends(current_user)):
    """Import (+ ogohlantirishlar): .mxk.json yoki plagin formatlari (.project)."""
    p, warnings = _import_bytes(await file.read(), file.filename or "")
    p = _store_imported(p, folder_id, user["name"])
    return {"project": p, "warnings": warnings}


@api.get("/import/formats", tags=["loyihalar"])
def import_formats():
    from .plugins import formats
    return [dict(ext=".mxk.json", title="MebeliX loyihasi (.mxk.json)")] + formats()


# ───────────────────────── Mahsulotlar (Изделия) ─────────────────────────
@api.post("/projects/{pid}/products", tags=["mahsulotlar"])
def add_product(pid: str, pr: Product, position: Optional[int] = None):
    with store.editing(pid) as p:
        if position is None or not (0 <= position <= len(p.products)):
            p.products.append(pr)
        else:
            p.products.insert(position, pr)
    return p


@api.put("/projects/{pid}/products/{prid}", tags=["mahsulotlar"])
def update_product(pid: str, prid: str, pr: Product):
    with store.editing(pid) as p:
        pr.id = prid
        p.products = [pr if x.id == prid else x for x in p.products]
    return p


@api.patch("/projects/{pid}/products/{prid}", tags=["mahsulotlar"])
def patch_product(pid: str, prid: str, fields: dict = Body(...)):
    with store.editing(pid) as p:
        for i, x in enumerate(p.products):
            if x.id == prid:
                d = x.model_dump(); d.update({k: v for k, v in fields.items() if k != "id"})
                p.products[i] = Product.model_validate(d)
                break
        else:
            raise HTTPException(404, _("product_not_found"))
    return p


@api.delete("/projects/{pid}/products/{prid}", tags=["mahsulotlar"])
def delete_product(pid: str, prid: str):
    with store.editing(pid) as p:
        p.products = [x for x in p.products if x.id != prid]
        for o in p.operations:
            n = len(o.parts)
            o.parts = [pt for pt in o.parts if pt.product_id != prid]
            if len(o.parts) != n:
                _invalidate(o)
    return p


@api.post("/projects/{pid}/products/zero-qty", tags=["mahsulotlar"])
def products_zero_qty(pid: str):
    with store.editing(pid) as p:
        for x in p.products:
            x.qty = 0
    return p


@api.post("/projects/{pid}/products/{prid}/move", tags=["mahsulotlar"])
def move_product(pid: str, prid: str, direction: Literal["up", "down"]):
    with store.editing(pid) as p:
        i = next((i for i, x in enumerate(p.products) if x.id == prid), None)
        if i is None:
            raise HTTPException(404, _("product_not_found"))
        j = i - 1 if direction == "up" else i + 1
        if 0 <= j < len(p.products):
            p.products[i], p.products[j] = p.products[j], p.products[i]
    return p


@api.post("/projects/{pid}/products/{prid}/clone", tags=["mahsulotlar"])
def clone_product(pid: str, prid: str):
    """Mahsulotni detallari bilan nusxalash (Ctrl+K)."""
    with store.editing(pid) as p:
        src = next((x for x in p.products if x.id == prid), None)
        if src is None:
            raise HTTPException(404, _("product_not_found"))
        cp = src.model_copy(update={"id": uuid4().hex[:12], "name": src.name + " (nusxa)"})
        p.products.insert(p.products.index(src) + 1, cp)
        uid = _next_uid(p)
        for o in p.operations:
            new = []
            for pt in o.parts:
                if pt.product_id == prid:
                    new.append(pt.model_copy(deep=True, update={"id": uuid4().hex[:12], "uid": uid,
                                                                "product_id": cp.id, "xnc_op_ids": [],
                                                                "used_qty": 0, "left_qty": 0}))
                    uid += 1
            if new:
                o.parts.extend(new)
                _invalidate(o)
    return p


@api.post("/projects/{pid}/products/sort", tags=["mahsulotlar"])
def sort_products(pid: str, by: Literal["code", "name", "qty", "cost"] = "name", desc: bool = False):
    with store.editing(pid) as p:
        key = {"code": lambda x: x.code, "name": lambda x: x.name.lower(), "qty": lambda x: x.qty,
               "cost": lambda x: x.cost_material + x.cost_operation}[by]
        p.products.sort(key=key, reverse=desc)
    return p


# ───────────────────────── Operatsiyalar ─────────────────────────
class OpIn(BaseModel):
    type: OpType
    code: str = ""
    name: str = ""
    material_id: Optional[str] = None


def _catalog_item(item_id: Optional[str]) -> Optional[CatalogItemRow]:
    if not item_id:
        return None
    with SessionLocal() as s:
        return s.get(CatalogItemRow, item_id)


def _new_operation(inp: OpIn) -> Operation:
    op = Operation(**inp.model_dump())
    item = _catalog_item(inp.material_id)
    prm = (item.params or {}) if item else {}
    if item:
        op.code = op.code or item.code or ""
        op.name = op.name or item.name or ""
    if op.type == OpType.CS:
        d = settings.get_default("cs_defaults")
        op.cs_material = CSMaterialParams.model_validate(d.get("material", {}))
        op.cs_cut = CSCutParams.model_validate(d.get("cut", {}))
        app_cfg = settings.get_default("app")
        L, W = app_cfg.get("default_sheet_length", 2750), app_cfg.get("default_sheet_width", 1830)
        if item:
            op.cs_material.thickness = item.thickness or op.cs_material.thickness
            op.cs_material.price = item.price or op.cs_material.price
            L, W = item.length or L, item.width or W
            for k in ("kerf", "trim_length", "trim_width"):
                if k in prm:
                    setattr(op.cs_cut, k, float(prm[k]))
            if "price_per_m2" in prm:
                op.cs_material.price_per_m2 = bool(prm["price_per_m2"])
        op.sheets = [StockSheet(length=L, width=W)]
    elif op.type == OpType.EL:
        op.el = ELParams.model_validate(settings.get_default("el_defaults"))
        if item:
            op.el.price = item.price or op.el.price
            op.el.thickness = float(prm.get("thickness", item.thickness or op.el.thickness) or 0)
            op.el.width = float(prm.get("width", item.width or op.el.width) or op.el.width)
    elif op.type == OpType.GR:
        op.gr = GRParams()
    elif op.type == OpType.XNC:
        op.xnc = XNCParams()
    return op


@api.post("/projects/{pid}/operations", tags=["operatsiyalar"])
def add_operation(pid: str, inp: OpIn, position: Optional[int] = None):
    with store.editing(pid) as p:
        op = _new_operation(inp)
        if op.type == OpType.EL and op.el:      # har yangi kromka — o'z belgisi va rangi
            n = sum(1 for o in p.operations if o.type == OpType.EL)
            if op.el.symbol == "A":
                op.el.symbol = chr(ord("A") + n % 26)
            if op.el.color == "#000000":
                op.el.color = mes.EDGE_COLORS[n % len(mes.EDGE_COLORS)]
        if position is None or not (0 <= position <= len(p.operations)):
            p.operations.append(op)
        else:
            p.operations.insert(position, op)
    return p


@api.put("/projects/{pid}/operations/{oid}", tags=["operatsiyalar"])
def update_operation(pid: str, oid: str, op: Operation):
    with store.editing(pid) as p:
        old = _op(p, oid)
        op.id = oid
        if op.parts == [] and old.parts:     # parametr yangilanishida detallar saqlanadi
            op.parts = old.parts
        if op.type == OpType.CS and op.result is None and old.result is not None:
            op.result = old.result
        p.operations = [op if o.id == oid else o for o in p.operations]
    return p


# kroy natijasini eskirtiradigan CS parametrlari (narx/ko'rinish maydonlari emas)
_CUT_AFFECTING_MAT = {"remnant_min_side1", "remnant_min_side2", "remnant_min_area", "remnant_size_incl_trim",
                      "min_part_size"}


@api.patch("/projects/{pid}/operations/{oid}", tags=["operatsiyalar"])
def patch_operation(pid: str, oid: str, fields: dict = Body(...)):
    """Qisman yangilash: {name, code, print, new_page, description, cs_material:{...}, cs_cut:{...}, el:{...}, xnc:{...}}.
    Kesish parametrlari o'zgarsa kroy natijasi o'chiriladi (qayta «Раскроить» kerak)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        d = op.model_dump()
        stale = False
        for k, v in fields.items():
            if k in ("id", "type", "parts", "result", "sheets"):
                continue
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                if k == "cs_cut" and any(d[k].get(kk) != vv for kk, vv in v.items()):
                    stale = True
                if k == "cs_material" and any(kk in _CUT_AFFECTING_MAT and d[k].get(kk) != vv for kk, vv in v.items()):
                    stale = True
                d[k].update(v)
            else:
                d[k] = v
        new = Operation.model_validate(d)
        new.parts, new.result, new.sheets = op.parts, op.result, op.sheets
        p.operations = [new if o.id == oid else o for o in p.operations]
        if stale and new.type == OpType.CS:
            _invalidate(new)
    return p


@api.delete("/projects/{pid}/operations/{oid}", tags=["operatsiyalar"])
def delete_operation(pid: str, oid: str):
    with store.editing(pid) as p:
        op = _op(p, oid)
        if op.type == OpType.CS and op.result:
            warehouse.rollback(op)
        p.operations = [o for o in p.operations if o.id != oid]
        for o in p.operations:        # shu operatsiyaga havolalarni tozalash
            for pt in o.parts:
                for side in ("top", "bottom", "left", "right"):
                    if getattr(pt, f"edge_{side}").op_id == oid:
                        setattr(pt, f"edge_{side}", EdgeRef())
                        _invalidate(o)
                    g = getattr(pt, f"groove_{side}")
                    if g.op_id == oid:
                        g.op_id = None
                if oid in pt.xnc_op_ids:
                    pt.xnc_op_ids = [x for x in pt.xnc_op_ids if x != oid]
    return p


@api.post("/projects/{pid}/operations/{oid}/move", tags=["operatsiyalar"])
def move_operation(pid: str, oid: str, direction: Literal["up", "down"]):
    with store.editing(pid) as p:
        i = next((i for i, o in enumerate(p.operations) if o.id == oid), None)
        if i is None:
            raise HTTPException(404, _("op_not_found"))
        j = i - 1 if direction == "up" else i + 1
        if 0 <= j < len(p.operations):
            p.operations[i], p.operations[j] = p.operations[j], p.operations[i]
    return p


@api.post("/projects/{pid}/operations/{oid}/clone", tags=["operatsiyalar"])
def clone_operation(pid: str, oid: str):
    with store.editing(pid) as p:
        src = _op(p, oid)
        cp = src.model_copy(deep=True)
        cp.id = uuid4().hex[:12]
        cp.result = None
        uid = _next_uid(p)
        for pt in cp.parts:
            pt.id = uuid4().hex[:12]; pt.uid = uid; uid += 1
            pt.used_qty = pt.left_qty = 0
        for sh in cp.sheets:
            sh.id = uuid4().hex[:12]; sh.used_qty = 0
        p.operations.insert(p.operations.index(src) + 1, cp)
    return p


@api.post("/projects/{pid}/operations/sort", tags=["operatsiyalar"])
def sort_operations(pid: str, by: Literal["type", "name", "code", "cost"] = "type"):
    order = {t: i for i, t in enumerate([OpType.O, OpType.CS, OpType.CN, OpType.CL, OpType.EL, OpType.SP,
                                          OpType.GR, OpType.XNC, OpType.LB])}
    with store.editing(pid) as p:
        key = {"type": lambda o: (order.get(o.type, 99), o.name.lower()), "name": lambda o: o.name.lower(),
               "code": lambda o: o.code, "cost": lambda o: -(o.cost_material + o.cost_operation)}[by]
        p.operations.sort(key=key)
    return p


@api.post("/projects/{pid}/actions/merge-same", tags=["operatsiyalar"])
def merge_same_operations(pid: str):
    """Общие действия → bir xil kod va nomli operatsiyalarni birlashtirish."""
    with store.editing(pid) as p:
        seen: dict[tuple, Operation] = {}
        remap: dict[str, str] = {}
        out = []
        for o in p.operations:
            k = (o.type, o.code, o.name)
            if o.type in (OpType.CS, OpType.CL, OpType.EL) and k in seen:
                tgt = seen[k]
                if o.type != OpType.EL:
                    tgt.parts.extend(o.parts)
                    _invalidate(tgt)
                remap[o.id] = tgt.id
                continue
            seen[k] = o
            out.append(o)
        for o in out:                      # olib tashlangan kromka operatsiyalariga havolalar
            for pt in o.parts:
                for side in ("top", "bottom", "left", "right"):
                    ref = getattr(pt, f"edge_{side}")
                    if ref.op_id in remap:
                        ref.op_id = remap[ref.op_id]
        p.operations = out
    return p


@api.post("/projects/{pid}/actions/split-edges", tags=["operatsiyalar"])
def split_edges_by_material(pid: str):
    """Общие действия → kromka operatsiyalarini kroy materiallari bo'yicha ajratish."""
    with store.editing(pid) as p:
        cs_ops = [o for o in p.operations if o.type == OpType.CS]
        new_ops: list[Operation] = []
        for el in [o for o in p.operations if o.type == OpType.EL]:
            users = [cs for cs in cs_ops if any(getattr(pt, f"edge_{s}").op_id == el.id
                                                for pt in cs.parts for s in ("top", "bottom", "left", "right"))]
            for cs in users[1:]:
                cp = el.model_copy(deep=True, update={"id": uuid4().hex[:12], "name": f"{el.name} ({cs.name})"})
                for pt in cs.parts:
                    for s in ("top", "bottom", "left", "right"):
                        ref = getattr(pt, f"edge_{s}")
                        if ref.op_id == el.id:
                            ref.op_id = cp.id
                new_ops.append((el, cp))
        for el, cp in new_ops:
            p.operations.insert(p.operations.index(el) + 1, cp)
    return p


@api.post("/projects/{pid}/actions/optimize-ops", tags=["operatsiyalar"])
def optimize_operations(pid: str):
    """Общие действия → operatsiyalarni optimallashtirish: bo'sh CS va ishlatilmagan kromka/XNC olib tashlanadi,
    bir xil kromkalar birlashtiriladi, tartib: CS → EL → GR → XNC."""
    merge_same_operations(pid)
    with store.editing(pid) as p:
        used_edges = {getattr(pt, f"edge_{s}").op_id for o in p.operations for pt in o.parts
                      for s in ("top", "bottom", "left", "right")}
        used_xnc = {x for o in p.operations for pt in o.parts for x in pt.xnc_op_ids}
        p.operations = [o for o in p.operations
                        if not ((o.type == OpType.CS and not o.parts) or (o.type == OpType.EL and o.id not in used_edges)
                                or (o.type == OpType.XNC and o.id not in used_xnc and o.xnc_part_id))]
    return sort_operations(pid, "type")


# ───────────────────────── Detallar ─────────────────────────
@api.post("/projects/{pid}/operations/{oid}/parts", tags=["detallar"])
def add_parts(pid: str, oid: str, parts: list[Part], position: Optional[int] = None):
    with store.editing(pid) as p:
        op = _op(p, oid)
        uid = _next_uid(p)
        for pt in parts:
            if not pt.uid:
                pt.uid = uid; uid += 1
            if not pt.product_id and p.products:
                pt.product_id = p.products[0].id
        if position is None or not (0 <= position <= len(op.parts)):
            op.parts.extend(parts)
        else:
            op.parts[position:position] = parts
        _invalidate(op)
    return p


@api.put("/projects/{pid}/operations/{oid}/parts/{ptid}", tags=["detallar"])
def update_part(pid: str, oid: str, ptid: str, part: Part):
    with store.editing(pid) as p:
        op = _op(p, oid); _part(op, ptid)
        part.id = ptid
        op.parts = [part if x.id == ptid else x for x in op.parts]
        _invalidate(op)
    return p


_PART_NON_CUT = {"name", "description", "code", "surface_face_op", "surface_back_op", "xnc_op_ids", "product_id"}


@api.patch("/projects/{pid}/operations/{oid}/parts/{ptid}", tags=["detallar"])
def patch_part(pid: str, oid: str, ptid: str, fields: dict = Body(...)):
    """Jadval katagini tahrirlash: faqat yuborilgan maydonlar o'zgaradi (nom/kod — kroy saqlanadi)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        for i, x in enumerate(op.parts):
            if x.id == ptid:
                d = x.model_dump()
                changed = {k for k, v in fields.items() if k not in ("id", "uid") and d.get(k) != v}
                d.update({k: v for k, v in fields.items() if k not in ("id",)})
                op.parts[i] = Part.model_validate(d)
                if changed - _PART_NON_CUT:
                    _invalidate(op)
                elif "product_id" in changed:
                    _invalidate(op)
                break
        else:
            raise HTTPException(404, _("part_not_found"))
    return p


class PartsSel(BaseModel):
    ids: list[str]


class PartPatchItem(BaseModel):
    id: str
    fields: dict


@api.post("/projects/{pid}/operations/{oid}/parts/batch-update", tags=["detallar"])
def parts_batch_update(pid: str, oid: str, items: list[PartPatchItem]):
    """Ko'p detalni turli qiymatlar bilan bir so'rovda yangilash (Excel dan Ctrl+V)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        idx = {pt.id: i for i, pt in enumerate(op.parts)}
        stale = False
        for it in items:
            i = idx.get(it.id)
            if i is None:
                continue
            d = op.parts[i].model_dump()
            if any(k not in _PART_NON_CUT and d.get(k) != v for k, v in it.fields.items()):
                stale = True
            d.update({k: v for k, v in it.fields.items() if k not in ("id", "uid")})
            op.parts[i] = Part.model_validate(d)
        if stale:
            _invalidate(op)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/delete", tags=["detallar"])
def delete_parts(pid: str, oid: str, sel: PartsSel):
    with store.editing(pid) as p:
        op = _op(p, oid)
        op.parts = [x for x in op.parts if x.id not in sel.ids]
        _invalidate(op)
    return p


class GroupUpdate(BaseModel):
    """Групповые действия: faqat berilgan maydonlar o'zgaradi."""
    ids: list[str]
    fields: dict


@api.post("/projects/{pid}/operations/{oid}/parts/group-update", tags=["detallar"])
def group_update(pid: str, oid: str, g: GroupUpdate):
    with store.editing(pid) as p:
        op = _op(p, oid)
        for i, pt in enumerate(op.parts):
            if pt.id in g.ids:
                d = pt.model_dump(); d.update({k: v for k, v in g.fields.items() if k not in ("id", "uid")})
                op.parts[i] = Part.model_validate(d)
        _invalidate(op)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/bulk/{action}", tags=["detallar"])
def parts_action(pid: str, oid: str, action: Literal["swap", "grain-on", "grain-off"], sel: PartsSel):
    """CTRL+W — o'lchamlarni almashtirish; CTRL+E/D — tekstura qo'yish/olish."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        for pt in op.parts:
            if pt.id not in sel.ids:
                continue
            if action == "swap":
                pt.length, pt.width = pt.width, pt.length
                pt.edge_top, pt.edge_bottom, pt.edge_left, pt.edge_right = \
                    pt.edge_left, pt.edge_right, pt.edge_top, pt.edge_bottom
                pt.groove_top, pt.groove_bottom, pt.groove_left, pt.groove_right = \
                    pt.groove_left, pt.groove_right, pt.groove_top, pt.groove_bottom
                pt.allow_top, pt.allow_bottom, pt.allow_left, pt.allow_right = \
                    pt.allow_left, pt.allow_right, pt.allow_top, pt.allow_bottom
            else:
                pt.grain = action == "grain-on"
        _invalidate(op)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/move-to/{target}", tags=["detallar"])
def move_parts(pid: str, oid: str, target: str, sel: PartsSel):
    """CTRL+M — boshqa operatsiyaga ko'chirish."""
    with store.editing(pid) as p:
        src = _op(p, oid); dst = _op(p, target)
        if dst.type not in (OpType.CS, OpType.CL):
            raise HTTPException(400, _("move_to_cut_only"))
        moving = [x for x in src.parts if x.id in sel.ids]
        src.parts = [x for x in src.parts if x.id not in sel.ids]
        dst.parts.extend(moving)
        _invalidate(src); _invalidate(dst)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/clone", tags=["detallar"])
def clone_parts(pid: str, oid: str, sel: PartsSel):
    """Ctrl+K — tanlangan detallar nusxasi (har biri o'zidan keyin)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        uid = _next_uid(p)
        out = []
        for pt in op.parts:
            out.append(pt)
            if pt.id in sel.ids:
                out.append(pt.model_copy(deep=True, update={"id": uuid4().hex[:12], "uid": uid, "xnc_op_ids": [],
                                                            "used_qty": 0, "left_qty": 0}))
                uid += 1
        op.parts = out
        _invalidate(op)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/move", tags=["detallar"])
def move_parts_updown(pid: str, oid: str, sel: PartsSel, direction: Literal["up", "down"]):
    """Ctrl+↑ / Ctrl+↓ — tanlangan detallarni bir qator yuqoriga/pastga."""
    with store.editing(pid, history=True) as p:
        op = _op(p, oid)
        arr = op.parts
        ids = set(sel.ids)
        rng = range(1, len(arr)) if direction == "up" else range(len(arr) - 2, -1, -1)
        for i in rng:
            j = i - 1 if direction == "up" else i + 1
            if arr[i].id in ids and arr[j].id not in ids:
                arr[i], arr[j] = arr[j], arr[i]
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/reorder", tags=["detallar"])
def reorder_parts(pid: str, oid: str, sel: PartsSel):
    with store.editing(pid) as p:
        op = _op(p, oid)
        pos = {i: n for n, i in enumerate(sel.ids)}
        op.parts.sort(key=lambda x: pos.get(x.id, len(pos)))
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/sort", tags=["detallar"])
def sort_parts(pid: str, oid: str, by: str = "uid", desc: bool = False):
    keys = {"uid": lambda x: x.uid, "name": lambda x: x.name.lower(), "length": lambda x: x.length,
            "width": lambda x: x.width, "qty": lambda x: x.qty, "code": lambda x: x.code,
            "area": lambda x: x.length * x.width, "product": lambda x: x.product_id or ""}
    if by not in keys:
        raise HTTPException(400, _("sort_fields", f=", ".join(keys)))
    with store.editing(pid) as p:
        op = _op(p, oid)
        op.parts.sort(key=keys[by], reverse=desc)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/import", tags=["detallar"])
async def import_parts_ep(pid: str, oid: str, file: UploadFile = File(...),
                          col_map: str = Form(...), sheet: int = Form(0), start_row: int = Form(2)):
    data = await file.read()
    with store.editing(pid) as p:
        op = _op(p, oid)
        try:
            parts = import_parts(p, data, file.filename or "", json.loads(col_map), sheet, start_row)
        except (ValueError, KeyError, IndexError) as e:
            raise HTTPException(400, _("import_error", e=e)) from e
        for pt in parts:
            pt.product_id = pt.product_id or (p.products[0].id if p.products else None)
        op.parts.extend(parts)
        _invalidate(op)
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/{ptid}/xnc", tags=["xnc"])
def add_xnc_for_part(pid: str, oid: str, ptid: str):
    """Detal xossalari → «(XNC) Обработка» qo'shish: detal o'lchamidagi bo'sh dastur."""
    from .services.sizes import compute_sizes
    with store.editing(pid) as p:
        op = _op(p, oid)
        pt = _part(op, ptid)
        s = compute_sizes(pt, p.size_mode, calc.edge_map(p))
        prod = next((x for x in p.products if x.id == pt.product_id), None)
        code = "_".join(x for x in ((prod.code if prod else ""), pt.code or str(pt.uid)) if x)
        x = XNCParams(length=s.detail[0], width=s.detail[1],
                      thickness=op.cs_material.thickness if op.cs_material else 16, qty=calc.total_qty(p, pt))
        xop = Operation(type=OpType.XNC, code=code, name=pt.name, xnc=x, xnc_part_id=pt.id)
        pt.xnc_op_ids.append(xop.id)
        p.operations.append(xop)
    return p


# ───────────────────────── Listlar va qoldiqlar ─────────────────────────
@api.put("/projects/{pid}/operations/{oid}/sheets", tags=["listlar"])
def set_sheets(pid: str, oid: str, sheets: list[StockSheet]):
    """Listlar ro'yxati. Kroyda ishlatilgan list o'zgarmasa (yangi list qo'shildi / soni oshdi) natija saqlanadi —
    «До кроить» uchun."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        old = {s.id: s for s in op.sheets}
        new = {s.id: s for s in sheets}
        stale = False
        if op.result:
            used: dict[str, int] = {}
            for m in op.result.maps:
                used[m.sheet_id] = used.get(m.sheet_id, 0) + m.copies
            for sid, n in used.items():
                a, b = old.get(sid), new.get(sid)
                if b is None or a is None or (a.length, a.width, a.trim_length, a.trim_width, a.is_remnant) != \
                        (b.length, b.width, b.trim_length, b.trim_width, b.is_remnant) or (b.qty < 10000 and b.qty < n):
                    stale = True
                    break
        op.sheets = sheets
        if stale:
            _invalidate(op)
        else:
            calc._account(p, op)
    return p


class IdsIn(BaseModel):
    ids: list[int]


@api.post("/projects/{pid}/operations/{oid}/sheets/from-remnants", tags=["listlar"])
def sheets_from_remnants(pid: str, oid: str, sel: IdsIn):
    """Листы и остатки → ombordagi qoldiqlarni qo'shish (kroyda birinchi navbatda ishlatiladi)."""
    with SessionLocal() as s:
        rows = [s.get(RemnantRow, i) for i in sel.ids]
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cs(op)
        have = {sh.source_remnant_id for sh in op.sheets if sh.source_remnant_id}
        for r in rows:
            if r is None or r.id in have or (r.qty or 0) <= 0:
                continue
            op.sheets.insert(0, StockSheet(length=r.length, width=r.width, qty=r.qty, is_remnant=True,
                                           source_remnant_id=r.id,
                                           description=f"Qoldiq #{r.id}" + (f" ({r.note})" if r.note else "")))
        _invalidate(op)
    return p


# ───────────────────────── Kroy ─────────────────────────
@api.post("/projects/{pid}/operations/{oid}/optimize", tags=["kroy"])
def optimize_op(pid: str, oid: str, background: BackgroundTasks,
                quality: Optional[Literal["fast", "normal", "max"]] = None,
                first_cut: Optional[FirstCutDir] = None, only_remaining: bool = False):
    """Раскроить (only_remaining=True — «До кроить»: faqat kroyga kirmagan detallar)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cs(op)
        if not op.parts:
            raise HTTPException(400, _("no_parts"))
        if not op.sheets:
            raise HTTPException(400, _("no_sheets"))
        _replace_result(op)
        calc.run_cutting(p, op, only_remaining=only_remaining, first_cut=first_cut, quality=quality)
    res = op.result
    background.add_task(mes.send_webhook, "cutting.done", dict(
        project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, op_id=op.id, op_name=op.name,
        sheets=res.total_sheets if res else 0, fill=res.total_fill_percent if res else 0))
    return res


@api.post("/projects/{pid}/operations/{oid}/variants", tags=["kroy"])
def cutting_variants(pid: str, oid: str):
    """Kroy variantlarini solishtirish (optimal / 1-kesish uzunlik bo'yicha / eni bo'yicha).
    Tanlangan variant `PUT .../result` bilan saqlanadi."""
    p = _load(pid)
    op = _op(p, oid)
    _need_cs(op)
    if not op.parts or not op.sheets:
        raise HTTPException(400, _("no_parts_or_sheets"))
    return calc.cutting_variants(p, op)


@api.delete("/projects/{pid}/operations/{oid}/result", tags=["kroy"])
def delete_result(pid: str, oid: str):
    with store.editing(pid) as p:
        _invalidate(_op(p, oid))
    return p


@api.put("/projects/{pid}/operations/{oid}/result", tags=["kroy"])
def save_edited_result(pid: str, oid: str, result: dict = Body(...)):
    """Tahrirlangan (yoki tanlangan variant) natijani saqlash — qayta quriladi va tekshiriladi."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cs(op)
        res = CuttingResult.model_validate(result)
        if res.maps and all(m.strips for m in res.maps):
            new = editor.rebuild(p, op, res)
            new.manual = res.manual
            new.variant = res.variant
        else:
            from .services.validate import validate
            errs = validate(res, calc._items_for(p, op, op.cs_cut), op.sheets, op.cs_cut)
            if errs:
                raise editor.EditError(errs[0], errs)
            new = res
        _replace_result(op)
        op.result = new
        calc._account(p, op)
        calc.cs_cost(p, op)
    return p


class EditIn(BaseModel):
    result: CuttingResult
    action: dict


@api.post("/projects/{pid}/operations/{oid}/edit", tags=["kroy"])
def edit_result(pid: str, oid: str, inp: EditIn):
    """Редактирование раскроя: qoralama + bitta amal → yangi qoralama (loyiha saqlanmaydi)."""
    p = _load(pid)
    op = _op(p, oid)
    _need_cs(op)
    return editor.apply(p, op, inp.result, inp.action)


class MapPatch(BaseModel):
    comment: Optional[str] = None
    done_count: Optional[int] = None


@api.patch("/projects/{pid}/operations/{oid}/maps/{idx}", tags=["kroy"])
def patch_map(pid: str, oid: str, idx: int, mp: MapPatch, background: BackgroundTasks):
    """Комментарий karta uchun; done_count — sexda kesib bo'lingan listlar (MES kuzatuvi)."""
    with store.editing(pid, history=mp.comment is not None) as p:
        op = _op(p, oid)
        if not op.result or not (1 <= idx <= len(op.result.maps)):
            raise HTTPException(404, _("no_map"))
        m = op.result.maps[idx - 1]
        if mp.comment is not None:
            m.comment = mp.comment
        if mp.done_count is not None:
            m.done_count = max(0, min(m.copies, mp.done_count))
            background.add_task(mes.send_webhook, "map.done", dict(
                project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, op_id=op.id, map=idx,
                done=m.done_count, copies=m.copies))
    return p


@api.get("/projects/{pid}/operations/{oid}/maps/{idx}.svg", tags=["kroy"])
def map_svg(pid: str, oid: str, idx: int, width: int = 900, label: str = "number_name", edges: bool = True,
            mirror: bool = False):
    p = _load(pid); op = _op(p, oid)
    if not op.result or not (1 <= idx <= len(op.result.maps)):
        raise HTTPException(404, _("no_map"))
    svg = render.map_svg(op.result.maps[idx - 1], max(100, min(width, 4000)), None, p, op, label, edges, True, mirror)
    return Response(svg, media_type="image/svg+xml")


# ───────────────────────── Qoldiqlarni omborga yozish ─────────────────────────
@api.get("/projects/{pid}/operations/{oid}/remnants", tags=["qoldiqlar"])
def op_remnants(pid: str, oid: str):
    p = _load(pid); op = _op(p, oid)
    _need_cs(op)
    res = op.result
    return dict(saved=bool(res and res.remnants_saved), remnants=warehouse.business_remnants(op),
                consumed=warehouse.consumed(op), material_code=warehouse.material_key(op))


@api.post("/projects/{pid}/operations/{oid}/remnants/commit", tags=["qoldiqlar"])
def op_remnants_commit(pid: str, oid: str):
    """Kroydan keyin (tasdiq bilan): деловой qoldiqlarni omborga yozish, ishlatilgan qoldiqlarni hisobdan chiqarish."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cs(op)
        try:
            out = warehouse.commit(p, op)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    return {**out, "project": p}


@api.post("/projects/{pid}/operations/{oid}/remnants/rollback", tags=["qoldiqlar"])
def op_remnants_rollback(pid: str, oid: str):
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cs(op)
        out = warehouse.rollback(op)
    return {**out, "project": p}


# ───────────────────────── Kromka / XNC ─────────────────────────
@api.get("/projects/{pid}/operations/{oid}/edge-usage", tags=["kromka"])
def edge_usage(pid: str, oid: str):
    p = _load(pid); return calc.edge_usage(p, _op(p, oid))


@api.get("/projects/{pid}/operations/{oid}/xnc-stats", tags=["xnc"])
def xnc_stats(pid: str, oid: str):
    p = _load(pid); op = _op(p, oid)
    if not op.xnc:
        raise HTTPException(400, _("not_xnc"))
    return xnc_cost(op)


@api.get("/projects/{pid}/operations/{oid}/xnc.svg", tags=["xnc"])
def xnc_svg(pid: str, oid: str, width: int = 560):
    p = _load(pid); op = _op(p, oid)
    if not op.xnc:
        raise HTTPException(400, _("not_xnc"))
    return Response(xnc_drawing_svg(op, p, max(100, min(width, 3000))), media_type="image/svg+xml")


# ───────────────────────── Postprotsessor ─────────────────────────
@api.get("/projects/{pid}/operations/{oid}/postprocess", tags=["postprotsessor"])
def postprocess(pid: str, oid: str, key: Optional[str] = None, profile_id: Optional[int] = None):
    """Kroy natijasini stanok/tizim formatida yuklab olish: key=csv|commands|dxf|json yoki profile_id (shablon)."""
    from .models import PostprocessorProfile
    from .services import postprocessors as pp
    p = _load(pid); op = _op(p, oid)
    _need_cs(op)
    if not op.result or not op.result.maps:
        raise HTTPException(400, _("cut_first"))
    if profile_id:
        pr = settings.get_profile("postprocessor", profile_id)
        if not pr:
            raise HTTPException(404, _("pp_not_found"))
        try:
            name, data, mime = pp.render_template(PostprocessorProfile.model_validate(pr["data"]), p, op)
        except Exception as e:  # noqa: BLE001 — shablon xatosi foydalanuvchiga
            raise HTTPException(400, _("template_error", e=e)) from e
    elif key in pp.BUILTIN:
        name, data, mime = pp.run_builtin(key, p, op)
    else:
        raise HTTPException(400, _("pp_not_selected"))
    from urllib.parse import quote
    return Response(data, media_type=mime,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


# ───────────────────────── Hisobot va etiketkalar ─────────────────────────
@api.get("/projects/{pid}/report", response_class=HTMLResponse, tags=["hisobot"])
def report(pid: str, lang: Literal["ru", "uz"] = "ru", profile_id: Optional[int] = None):
    ps = PrintSettings.model_validate(settings.resolve("print", profile_id))
    return render.project_report_html(_load(pid), ps, lang)


@api.post("/projects/{pid}/report", response_class=HTMLResponse, tags=["hisobot"])
def report_preview(pid: str, ps: PrintSettings, lang: Literal["ru", "uz"] = "ru"):
    """Saqlanmagan chop sozlamalari bilan ko'rish (Печать отчета → oldindan ko'rish)."""
    return render.project_report_html(_load(pid), ps, lang)


@api.get("/projects/{pid}/report.pdf", tags=["hisobot"])
def report_pdf(pid: str, lang: Literal["ru", "uz"] = "ru", profile_id: Optional[int] = None):
    try:
        from weasyprint import HTML  # type: ignore
    except ImportError as e:
        raise HTTPException(501, _("no_weasyprint")) from e
    p = _load(pid)
    ps = PrintSettings.model_validate(settings.resolve("print", profile_id))
    pdf = HTML(string=render.project_report_html(p, ps, lang)).write_pdf()
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{p.number}.pdf"'})


@api.get("/projects/{pid}/labels", response_class=HTMLResponse, tags=["hisobot"])
def labels_page(pid: str, op_id: Optional[str] = None, profile_id: Optional[int] = None,
                lang: Literal["ru", "uz"] = "ru"):
    ls = LabelSettings.model_validate(settings.resolve("labels", profile_id))
    return labels.labels_html(_load(pid), ls, op_id, lang)


@api.post("/projects/{pid}/labels", response_class=HTMLResponse, tags=["hisobot"])
def labels_preview(pid: str, ls: LabelSettings, op_id: Optional[str] = None, lang: Literal["ru", "uz"] = "ru"):
    """Saqlanmagan etiketka sozlamalari bilan ko'rish."""
    return labels.labels_html(_load(pid), ls, op_id, lang)


@api.get("/projects/{pid}/warehouse", tags=["hisobot"])
def warehouse_req(pid: str):
    return calc.warehouse_request(_load(pid))


# ───────────────────────── Tovarlar katalogi (MES) ─────────────────────────
def _cat(r: CatalogItemRow) -> dict:
    return dict(id=r.id, parent_id=r.parent_id, kind=r.kind, code=r.code, name=r.name, unit=r.unit,
                price=r.price, stock=r.stock, thickness=r.thickness, length=r.length, width=r.width,
                params=r.params or {})


@api.get("/catalog", tags=["katalog"])
def catalog(kind: Optional[str] = None, parent_id: Optional[str] = None, q: str = "", limit: int = 500):
    with SessionLocal() as s:
        st = select(CatalogItemRow)
        if kind:
            st = st.where(CatalogItemRow.kind == kind)
        if parent_id is not None:
            st = st.where(CatalogItemRow.parent_id == (parent_id or None))
        if q:
            st = st.where(CatalogItemRow.name.ilike(f"%{q}%") | CatalogItemRow.code.ilike(f"%{q}%"))
        return [_cat(r) for r in s.scalars(st.order_by(CatalogItemRow.name).limit(max(1, min(limit, 5000)))).all()]


class CatalogIn(BaseModel):
    id: str
    parent_id: Optional[str] = None
    kind: str
    code: str = ""
    name: str
    unit: str = ""
    price: float = 0
    stock: float = 0
    thickness: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    params: dict = {}


@api.post("/catalog/sync", tags=["katalog"])
def catalog_sync(items: list[CatalogIn]):
    """MES dan tovarlarni yuklash (upsert)."""
    with SessionLocal() as s:
        for it in items:
            s.merge(CatalogItemRow(**it.model_dump()))
        s.commit()
    return {"count": len(items)}


@api.delete("/catalog/{item_id}", tags=["katalog"])
def catalog_delete(item_id: str):
    with SessionLocal() as s:
        n = s.query(CatalogItemRow).filter(CatalogItemRow.id == item_id).delete()
        s.commit()
    if not n:
        raise HTTPException(404, _("catalog_item_not_found"))
    return {"ok": True}


@api.post("/catalog/import", tags=["katalog"])
async def catalog_import(file: UploadFile = File(...), col_map: str = Form(...), sheet: int = Form(0),
                         start_row: int = Form(2), kind: str = Form("sheet")):
    """Каталог товаров → Excel/CSV dan (ustunlar xaritasi: id, parent_id, code, name, unit, price, stock,
    thickness, length, width, kind)."""
    from .services.importers import import_catalog
    try:
        rows = import_catalog(await file.read(), file.filename or "", json.loads(col_map), sheet, start_row, kind)
    except (ValueError, KeyError, IndexError) as e:
        raise HTTPException(400, _("import_error", e=e)) from e
    with SessionLocal() as s:
        for r in rows:
            s.merge(CatalogItemRow(**r))
        s.commit()
    return {"count": len(rows)}


@api.post("/import/preview", tags=["katalog"])
async def import_preview(file: UploadFile = File(...), sheet: int = Form(0), rows: int = Form(30)):
    """Excel/CSV faylning birinchi qatorlari (ustunlar xaritasini tanlash uchun)."""
    from .services.importers import preview
    try:
        return preview(await file.read(), file.filename or "", sheet, max(1, min(rows, 200)))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, _("file_unreadable", e=e)) from e


# ───────────────────────── Qo'shimcha routerlar ─────────────────────────
from .api_extra import router as extra_router  # noqa: E402

api.include_router(extra_router)
app.include_router(api)


# ───────────────────────── Frontend (SPA) ─────────────────────────
WEB_DIR = Path(os.getenv("MEBELIX_WEB_DIR", str(Path(__file__).resolve().parents[2] / "frontend" / "dist")))

if WEB_DIR.is_dir() and (WEB_DIR / "index.html").is_file():
    from fastapi.staticfiles import StaticFiles
    if (WEB_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")
    _web_root = WEB_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> Any:
        if full_path.startswith("api/"):
            raise HTTPException(404)
        f = (WEB_DIR / full_path).resolve()
        if full_path and f.is_file() and _web_root in f.parents:
            return FileResponse(f)
        return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})
