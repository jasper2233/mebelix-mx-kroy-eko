"""MebeliX Kroy — REST API (FastAPI).

Ishga tushirish:  uvicorn app.main:app --reload --port 8000
Hujjat:           http://localhost:8000/docs
"""
from __future__ import annotations

import json
from typing import Literal, Optional
from uuid import uuid4

from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy import func, select

from .db import (CatalogItemRow, FolderRow, ProjectHistoryRow, ProjectRow, SessionLocal,
                 init_db)
from .models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, GRParams, OpType,
                     Operation, OrderStatus, Part, Product, Project, StockSheet, XNCParams)
from .services import calc, render
from .services.importers import import_parts
from .services.xnc import xnc_cost

app = FastAPI(title="MebeliX Kroy API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _startup():
    init_db()


# ───────────────────────── Yordamchilar ─────────────────────────
def _load(pid: str) -> Project:
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        if not row:
            raise HTTPException(404, "Loyiha topilmadi")
        return Project.model_validate(row.data)


def _save(p: Project, history: bool = True) -> Project:
    calc.recalc_project(p)
    data = json.loads(p.model_dump_json())
    cost = sum(o.cost_material + o.cost_operation for o in p.operations)
    with SessionLocal() as s:
        row = s.get(ProjectRow, p.id)
        if not row:
            row = ProjectRow(id=p.id); s.add(row)
        row.number = p.number; row.folder_id = p.folder_id; row.name = p.name
        row.owner = p.owner; row.status = int(p.status); row.order_date = str(p.order_date)
        row.cost = cost; row.mes_order_ref = p.mes_order_ref; row.data = data
        if history:
            last = s.scalar(select(func.max(ProjectHistoryRow.version))
                            .where(ProjectHistoryRow.project_id == p.id)) or 0
            # redo zanjirini kesish
            s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == p.id,
                                              ProjectHistoryRow.version > _cursor.get(p.id, last)).delete()
            v = _cursor.get(p.id, last) + 1
            s.add(ProjectHistoryRow(project_id=p.id, version=v, data=data))
            _cursor[p.id] = v
        s.commit()
    return p


_cursor: dict[str, int] = {}   # undo/redo ko'rsatkichi (prod: Redis yoki DB)


def _op(p: Project, op_id: str) -> Operation:
    for o in p.operations:
        if o.id == op_id:
            return o
    raise HTTPException(404, "Operatsiya topilmadi")


def _part(op: Operation, part_id: str) -> Part:
    for pt in op.parts:
        if pt.id == part_id:
            return pt
    raise HTTPException(404, "Detal topilmadi")


def _next_uid(p: Project) -> int:
    return max((pt.uid for o in p.operations for pt in o.parts), default=0) + 1


# ───────────────────────── Papkalar va loyihalar ─────────────────────────
class FolderIn(BaseModel):
    name: str
    parent_id: Optional[str] = None


@app.get("/api/folders")
def list_folders(parent_id: Optional[str] = None):
    with SessionLocal() as s:
        rows = s.scalars(select(FolderRow).where(FolderRow.parent_id == parent_id)).all()
        return [dict(id=r.id, name=r.name, parent_id=r.parent_id) for r in rows]


@app.post("/api/folders")
def create_folder(f: FolderIn):
    with SessionLocal() as s:
        r = FolderRow(id=uuid4().hex[:12], name=f.name, parent_id=f.parent_id)
        s.add(r); s.commit()
        return dict(id=r.id, name=r.name, parent_id=r.parent_id)


@app.patch("/api/folders/{fid}")
def rename_folder(fid: str, f: FolderIn):
    with SessionLocal() as s:
        r = s.get(FolderRow, fid)
        if not r:
            raise HTTPException(404)
        r.name = f.name; r.parent_id = f.parent_id; s.commit()
        return dict(id=r.id, name=r.name, parent_id=r.parent_id)


@app.get("/api/projects")
def list_projects(folder_id: Optional[str] = None, q: str = ""):
    """Проекты ro'yxati: ID, Egasi, Holati, Sana, Narx, Nomi."""
    with SessionLocal() as s:
        st = select(ProjectRow).where(ProjectRow.folder_id == folder_id)
        if q:
            st = st.where(ProjectRow.name.ilike(f"%{q}%"))
        rows = s.scalars(st.order_by(ProjectRow.number)).all()
        return [dict(id=r.id, number=r.number, owner=r.owner, status=r.status,
                     order_date=r.order_date, cost=r.cost, name=r.name) for r in rows]


class ProjectIn(BaseModel):
    name: str = "Nomsiz"
    folder_id: Optional[str] = None
    currency: str = "UZS"
    owner: str = ""
    mes_order_ref: Optional[str] = None


@app.post("/api/projects")
def create_project(inp: ProjectIn):
    with SessionLocal() as s:
        num = (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1
    p = Project(number=num, **inp.model_dump())
    p.products.append(Product(name="Mahsulot1"))
    return _save(p)


@app.get("/api/projects/{pid}")
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


@app.patch("/api/projects/{pid}")
def update_project_header(pid: str, h: ProjectHeader):
    p = _load(pid)
    upd = p.model_dump()
    upd.update({k: v for k, v in h.model_dump().items() if v is not None})
    return _save(Project.model_validate(upd))


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    with SessionLocal() as s:
        s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid).delete()
        s.query(ProjectRow).filter(ProjectRow.id == pid).delete()
        s.commit()
    return {"ok": True}


@app.post("/api/projects/{pid}/copy")
def copy_project(pid: str, name: Optional[str] = None):
    p = _load(pid)
    with SessionLocal() as s:
        num = (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1
    p.id = uuid4().hex[:12]; p.number = num; p.name = name or (p.name + " (nusxa)")
    return _save(p)


@app.post("/api/projects/{pid}/undo")
def undo(pid: str):
    return _step(pid, -1)


@app.post("/api/projects/{pid}/redo")
def redo(pid: str):
    return _step(pid, +1)


def _step(pid: str, d: int):
    with SessionLocal() as s:
        last = s.scalar(select(func.max(ProjectHistoryRow.version))
                        .where(ProjectHistoryRow.project_id == pid)) or 0
        cur = _cursor.get(pid, last) + d
        row = s.scalar(select(ProjectHistoryRow).where(ProjectHistoryRow.project_id == pid,
                                                       ProjectHistoryRow.version == cur))
        if not row:
            raise HTTPException(400, "Qaytarib bo'lmaydi")
        _cursor[pid] = cur
        p = Project.model_validate(row.data)
    return _save(p, history=False)


@app.get("/api/projects/{pid}/export")
def export_project(pid: str):
    p = _load(pid)
    return Response(p.model_dump_json(indent=2), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{p.number}.mxk.json"'})


@app.post("/api/projects/import")
async def import_project(file: UploadFile = File(...), folder_id: Optional[str] = Form(None)):
    p = Project.model_validate_json(await file.read())
    with SessionLocal() as s:
        p.number = (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1
    p.id = uuid4().hex[:12]; p.folder_id = folder_id
    return _save(p)


# ───────────────────────── Mahsulotlar (Изделия) ─────────────────────────
@app.post("/api/projects/{pid}/products")
def add_product(pid: str, pr: Product):
    p = _load(pid); p.products.append(pr); return _save(p)


@app.put("/api/projects/{pid}/products/{prid}")
def update_product(pid: str, prid: str, pr: Product):
    p = _load(pid)
    p.products = [pr if x.id == prid else x for x in p.products]
    return _save(p)


@app.delete("/api/projects/{pid}/products/{prid}")
def delete_product(pid: str, prid: str):
    p = _load(pid)
    p.products = [x for x in p.products if x.id != prid]
    for o in p.operations:
        o.parts = [pt for pt in o.parts if pt.product_id != prid]
    return _save(p)


@app.post("/api/projects/{pid}/products/zero-qty")
def products_zero_qty(pid: str):
    p = _load(pid)
    for x in p.products:
        x.qty = 0
    return _save(p)


# ───────────────────────── Operatsiyalar ─────────────────────────
class OpIn(BaseModel):
    type: OpType
    code: str = ""
    name: str = ""
    material_id: Optional[str] = None


@app.post("/api/projects/{pid}/operations")
def add_operation(pid: str, inp: OpIn):
    p = _load(pid)
    op = Operation(**inp.model_dump())
    if op.type == OpType.CS:
        op.cs_material = CSMaterialParams(); op.cs_cut = CSCutParams()
        op.sheets = [StockSheet(length=2750, width=1830)]
    elif op.type == OpType.EL:
        op.el = ELParams()
    elif op.type == OpType.GR:
        op.gr = GRParams()
    elif op.type == OpType.XNC:
        op.xnc = XNCParams()
    p.operations.append(op)
    return _save(p)


@app.put("/api/projects/{pid}/operations/{oid}")
def update_operation(pid: str, oid: str, op: Operation):
    p = _load(pid)
    old = _op(p, oid)
    op.id = oid
    if op.parts == [] and old.parts:     # parametr yangilanishida detallar saqlanadi
        op.parts = old.parts
    p.operations = [op if o.id == oid else o for o in p.operations]
    return _save(p)


@app.delete("/api/projects/{pid}/operations/{oid}")
def delete_operation(pid: str, oid: str):
    p = _load(pid)
    p.operations = [o for o in p.operations if o.id != oid]
    for o in p.operations:        # shu kromkaga havolalarni tozalash
        for pt in o.parts:
            for side in ("top", "bottom", "left", "right"):
                if getattr(pt, f"edge_{side}").op_id == oid:
                    setattr(pt, f"edge_{side}", EdgeRef())
    return _save(p)


@app.post("/api/projects/{pid}/operations/{oid}/move")
def move_operation(pid: str, oid: str, direction: Literal["up", "down"]):
    p = _load(pid)
    i = next(i for i, o in enumerate(p.operations) if o.id == oid)
    j = i - 1 if direction == "up" else i + 1
    if 0 <= j < len(p.operations):
        p.operations[i], p.operations[j] = p.operations[j], p.operations[i]
    return _save(p)


@app.post("/api/projects/{pid}/operations/{oid}/clone")
def clone_operation(pid: str, oid: str):
    p = _load(pid)
    src = _op(p, oid)
    cp = src.model_copy(deep=True)
    cp.id = uuid4().hex[:12]; cp.result = None
    uid = _next_uid(p)
    for pt in cp.parts:
        pt.id = uuid4().hex[:12]; pt.uid = uid; uid += 1
    p.operations.insert(p.operations.index(src) + 1, cp)
    return _save(p)


@app.post("/api/projects/{pid}/actions/merge-same")
def merge_same_operations(pid: str):
    """Общие действия → bir xil kod va nomli operatsiyalarni birlashtirish."""
    p = _load(pid)
    seen: dict[tuple, Operation] = {}
    out = []
    for o in p.operations:
        k = (o.type, o.code, o.name)
        if o.type in (OpType.CS, OpType.CL) and k in seen:
            seen[k].parts.extend(o.parts); seen[k].result = None
            continue
        seen[k] = o; out.append(o)
    p.operations = out
    return _save(p)


# ───────────────────────── Detallar ─────────────────────────
@app.post("/api/projects/{pid}/operations/{oid}/parts")
def add_parts(pid: str, oid: str, parts: list[Part]):
    p = _load(pid); op = _op(p, oid)
    uid = _next_uid(p)
    for pt in parts:
        if not pt.uid:
            pt.uid = uid; uid += 1
        if not pt.product_id and p.products:
            pt.product_id = p.products[0].id
        op.parts.append(pt)
    op.result = None
    return _save(p)


@app.put("/api/projects/{pid}/operations/{oid}/parts/{ptid}")
def update_part(pid: str, oid: str, ptid: str, part: Part):
    p = _load(pid); op = _op(p, oid); _part(op, ptid)
    part.id = ptid
    op.parts = [part if x.id == ptid else x for x in op.parts]
    op.result = None
    return _save(p)


class PartsSel(BaseModel):
    ids: list[str]


@app.post("/api/projects/{pid}/operations/{oid}/parts/delete")
def delete_parts(pid: str, oid: str, sel: PartsSel):
    p = _load(pid); op = _op(p, oid)
    op.parts = [x for x in op.parts if x.id not in sel.ids]; op.result = None
    return _save(p)


class GroupUpdate(BaseModel):
    """Групповые действия: faqat berilgan maydonlar o'zgaradi."""
    ids: list[str]
    fields: dict


@app.post("/api/projects/{pid}/operations/{oid}/parts/group-update")
def group_update(pid: str, oid: str, g: GroupUpdate):
    p = _load(pid); op = _op(p, oid)
    for i, pt in enumerate(op.parts):
        if pt.id in g.ids:
            d = pt.model_dump(); d.update(g.fields)
            op.parts[i] = Part.model_validate(d)
    op.result = None
    return _save(p)


@app.post("/api/projects/{pid}/operations/{oid}/parts/bulk/{action}")
def parts_action(pid: str, oid: str, action: Literal["swap", "grain-on", "grain-off"], sel: PartsSel):
    """CTRL+W — o'lchamlarni almashtirish; CTRL+E/D — tekstura qo'yish/olish."""
    p = _load(pid); op = _op(p, oid)
    for pt in op.parts:
        if pt.id not in sel.ids:
            continue
        if action == "swap":
            pt.length, pt.width = pt.width, pt.length
            pt.edge_top, pt.edge_bottom, pt.edge_left, pt.edge_right = \
                pt.edge_left, pt.edge_right, pt.edge_top, pt.edge_bottom
        else:
            pt.grain = action == "grain-on"
    op.result = None
    return _save(p)


@app.post("/api/projects/{pid}/operations/{oid}/parts/move-to/{target}")
def move_parts(pid: str, oid: str, target: str, sel: PartsSel):
    """CTRL+M — boshqa operatsiyaga ko'chirish."""
    p = _load(pid); src = _op(p, oid); dst = _op(p, target)
    moving = [x for x in src.parts if x.id in sel.ids]
    src.parts = [x for x in src.parts if x.id not in sel.ids]
    dst.parts.extend(moving); src.result = None; dst.result = None
    return _save(p)


@app.post("/api/projects/{pid}/operations/{oid}/parts/import")
async def import_parts_ep(pid: str, oid: str, file: UploadFile = File(...),
                          col_map: str = Form(...), sheet: int = Form(0), start_row: int = Form(2)):
    p = _load(pid); op = _op(p, oid)
    parts = import_parts(p, await file.read(), file.filename or "", json.loads(col_map), sheet, start_row)
    for pt in parts:
        pt.product_id = pt.product_id or (p.products[0].id if p.products else None)
    op.parts.extend(parts); op.result = None
    return _save(p)


# ───────────────────────── Listlar va qoldiqlar ─────────────────────────
@app.put("/api/projects/{pid}/operations/{oid}/sheets")
def set_sheets(pid: str, oid: str, sheets: list[StockSheet]):
    p = _load(pid); op = _op(p, oid)
    op.sheets = sheets; op.result = None
    return _save(p)


# ───────────────────────── Kroy ─────────────────────────
@app.post("/api/projects/{pid}/operations/{oid}/optimize")
def optimize_op(pid: str, oid: str):
    """Раскроить."""
    p = _load(pid); op = _op(p, oid)
    if op.type != OpType.CS:
        raise HTTPException(400, "Faqat CS operatsiyasi uchun")
    calc.run_cutting(p, op)
    _save(p)
    return op.result


@app.delete("/api/projects/{pid}/operations/{oid}/result")
def delete_result(pid: str, oid: str):
    p = _load(pid); op = _op(p, oid); op.result = None
    for pt in op.parts:
        pt.used_qty = pt.left_qty = 0
    return _save(p)


@app.put("/api/projects/{pid}/operations/{oid}/result")
def save_edited_result(pid: str, oid: str, result: dict = Body(...)):
    """Редактирование раскроя: frontend tahrirlangan kartani yuboradi."""
    from .models import CuttingResult
    p = _load(pid); op = _op(p, oid)
    op.result = CuttingResult.model_validate(result)
    calc.cs_cost(p, op)
    return _save(p)


@app.get("/api/projects/{pid}/operations/{oid}/maps/{idx}.svg")
def map_svg(pid: str, oid: str, idx: int, width: int = 900):
    p = _load(pid); op = _op(p, oid)
    if not op.result or not (1 <= idx <= len(op.result.maps)):
        raise HTTPException(404, "Karta yo'q")
    return Response(render.map_svg(op.result.maps[idx - 1], width), media_type="image/svg+xml")


# ───────────────────────── Kromka / XNC ─────────────────────────
@app.get("/api/projects/{pid}/operations/{oid}/edge-usage")
def edge_usage(pid: str, oid: str):
    p = _load(pid); return calc.edge_usage(p, _op(p, oid))


@app.get("/api/projects/{pid}/operations/{oid}/xnc-stats")
def xnc_stats(pid: str, oid: str):
    p = _load(pid); op = _op(p, oid)
    if not op.xnc:
        raise HTTPException(400, "XNC emas")
    return xnc_cost(op)


# ───────────────────────── Hisobot ─────────────────────────
@app.get("/api/projects/{pid}/report", response_class=HTMLResponse)
def report(pid: str):
    return render.project_report_html(_load(pid))


@app.get("/api/projects/{pid}/warehouse")
def warehouse(pid: str):
    return calc.warehouse_request(_load(pid))


# ───────────────────────── Tovarlar katalogi (MES) ─────────────────────────
@app.get("/api/catalog")
def catalog(kind: Optional[str] = None, parent_id: Optional[str] = None, q: str = ""):
    with SessionLocal() as s:
        st = select(CatalogItemRow)
        if kind:
            st = st.where(CatalogItemRow.kind == kind)
        if parent_id is not None:
            st = st.where(CatalogItemRow.parent_id == parent_id)
        if q:
            st = st.where(CatalogItemRow.name.ilike(f"%{q}%") | CatalogItemRow.code.ilike(f"%{q}%"))
        return [dict(id=r.id, parent_id=r.parent_id, kind=r.kind, code=r.code, name=r.name,
                     unit=r.unit, price=r.price, stock=r.stock, thickness=r.thickness,
                     length=r.length, width=r.width, params=r.params) for r in s.scalars(st).all()]


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


@app.post("/api/catalog/sync")
def catalog_sync(items: list[CatalogIn]):
    """MES dan tovarlarni yuklash (upsert)."""
    with SessionLocal() as s:
        for it in items:
            s.merge(CatalogItemRow(**it.model_dump()))
        s.commit()
    return {"count": len(items)}
