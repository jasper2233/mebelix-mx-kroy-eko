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
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select

from . import store
from .auth import current_user
from .i18n import SCRIPT, _, error_text, format_errors, norm_lang, set_lang
from .db import CatalogItemRow, FolderRow, ProjectRow, RemnantRow, SessionLocal, ckey, init_db, text_search
from .models import (CSCutParams, CSMaterialParams, CuttingResult, EdgeRef, ELParams, FirstCutDir, GRParams,
                     LabelSettings, OpType, Operation, OrderStatus, Part, PrintSettings, Product, Project,
                     StockSheet, XNCParams)
from .services import calc, compute, editor, labels, mes, remnant_rules, remnant_store, render, settings, warehouse
from .services.importers import MAX_FILE_BYTES, import_parts_ex
from .services import o_ops
from .services import order_flow
from .services.xnc import xnc_cost, xnc_drawing_svg

VERSION = "2.0.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # bir nechta ilova jarayoni bir vaqtda ishga tushsa — boshlang'ich sozlamalar bir marta yozilsin (jarayonlararo qulf)
    from . import store as _store
    with _store._lock("startup-seed"):
        settings.seed()
    settings.listen()                      # boshqa jarayonlarda o'zgargan sozlamalar — keshlar tozalanadi (PostgreSQL NOTIFY)
    import threading as _th
    _th.Thread(target=_pack_history, name="mx-history-pack", daemon=True).start()
    yield


def _pack_history() -> None:
    """Eski siqilmagan tarix versiyalari (2-bosqichdan oldingi) — fonda siqiladi; bir jarayon bajaradi."""
    import logging as _lg
    from . import store as _store
    try:
        with _store._lock("history-pack"):
            n = _store.pack_history_backlog()
        if n:
            _lg.getLogger("mebelix.store").info("tarix: %d versiya siqildi", n)
    except Exception:  # noqa: BLE001
        _lg.getLogger("mebelix.store").exception("tarixni siqib bo'lmadi")


app = FastAPI(title="MebeliX Kroy API", version=VERSION, lifespan=lifespan)
# CORS: standart — o'chiq (frontend shu serverdan yoki nginx orqali bir manzildan ochiladi).
# Boshqa domendagi MES/ERP brauzerdan murojaat qilsa: MEBELIX_CORS=https://erp.korxona.uz,https://mes.korxona.uz
_cors = [o.strip() for o in os.getenv("MEBELIX_CORS", "").split(",") if o.strip()]
if _cors:
    app.add_middleware(CORSMiddleware, allow_origins=_cors, allow_methods=["*"], allow_headers=["*"],
                       expose_headers=["Content-Disposition", "X-PP-Refit", "X-PP-Refit-Mode", "X-Label-Warnings", "X-Total-Count"], allow_credentials="*" not in _cors)
app.add_middleware(GZipMiddleware, minimum_size=2048)

api = APIRouter(prefix="/api", dependencies=[Depends(current_user), Depends(order_flow.edit_guard)])


@app.middleware("http")
async def _lang_mw(request: Request, call_next):
    """Xabarlar tili: Accept-Language (frontend UI tilini yuboradi): ru | uz | uz-Cyrl.
    Hisobot / etiketka `?lang=uz-Cyrl` — yozuv kontekstda (SCRIPT=cyrl), parametr esa endpointlar uchun `uz` ga
    almashtiriladi (ular `Literal["ru", "uz"]` qabul qiladi; matnlar chiqishda kirillga o'giriladi)."""
    set_lang(request.headers.get("accept-language"))
    qs = request.scope.get("query_string") or b""
    if b"lang=" in qs:
        from urllib.parse import parse_qsl, urlencode
        pairs = parse_qsl(qs.decode("latin-1"), keep_blank_values=True)
        q = next((v for k, v in pairs if k == "lang"), None)
        if q is not None:
            v = norm_lang(q)
            SCRIPT.set("cyrl" if v == "uz-Cyrl" else "latn")
            if v == "uz-Cyrl":
                request.scope["query_string"] = urlencode([(k, "uz" if k == "lang" else x) for k, x in pairs]).encode("latin-1")
    # abonent (korxona): tokendagi `cid` — so'rovning hamma qismi (oqimlar, fon vazifalari) shu korxona nomidan ishlaydi;
    # PostgreSQL da RLS shu qiymat bo'yicha boshqa korxona qatorlarini yashiradi
    from . import tenant
    from .auth import request_company
    tok = tenant.set_current(request_company(request))
    try:
        return await call_next(request)
    finally:
        tenant.reset(tok)


@app.exception_handler(editor.EditError)
async def _edit_error(_req: Request, e: editor.EditError):
    return JSONResponse(status_code=422, content={"detail": str(e), "details": e.details, "code": getattr(e, "code", "")})


@app.exception_handler(settings.SettingsError)
async def _settings_error(_req: Request, e: settings.SettingsError):
    return JSONResponse(status_code=400, content={"detail": str(e)})


@app.exception_handler(remnant_store.StoreUnavailable)
async def _store_down(_req: Request, e: remnant_store.StoreUnavailable):
    return JSONResponse(status_code=503, content={"detail": str(e)})


@app.exception_handler(warehouse.WarehouseConflict)
async def _wh_conflict(_req: Request, e: warehouse.WarehouseConflict):
    return JSONResponse(status_code=409, content={"detail": str(e)})


def _safe_errors(errors: list) -> list:
    """Tekshiruv xatolari JSON ga: `msg` — foydalanuvchi tilida (ru/uz) qisqa sabab (xom inglizcha emas);
    kirish qiymati (masalan, cheksiz son) JSON ga sig'masa — matn sifatida."""
    out = []
    for er in errors:
        er = dict(er)
        er.pop("url", None)
        er["msg"] = error_text(er)
        if "ctx" in er:
            er["ctx"] = {k: str(v) for k, v in (er["ctx"] or {}).items()}
        if "input" in er:
            try:
                json.dumps(er["input"], allow_nan=False)
            except (TypeError, ValueError):
                er["input"] = str(er["input"])[:200]
        out.append(er)
    return out


def _validation_body(errors: list) -> dict:
    """422 javobi: `detail` — xatolar ro'yxati (avvalgi tuzilma), `message` — «maydon: sabab» ko'rinishida bitta matn,
    `messages` — har xato alohida qator (odam o'qiydigan maydon nomi bilan; UI xabarnomada ro'yxat qilib ko'rsatadi)."""
    return {"detail": _safe_errors(errors), "message": format_errors(errors),
            "messages": [format_errors([er], limit=1) for er in list(errors)[:10]]}


@app.exception_handler(RequestValidationError)
async def _request_validation_error(_req: Request, e: RequestValidationError):
    return JSONResponse(status_code=422, content=_validation_body(e.errors()))


@app.exception_handler(ValidationError)
async def _model_validation_error(_req: Request, e: ValidationError):
    """Endpoint ichida model tekshiruvi (masalan, PATCH da noto'g'ri tur) — 500 emas, 422."""
    return JSONResponse(status_code=422, content=_validation_body(e.errors()))


@app.get("/api/health", tags=["tizim"])
def health():
    return {"ok": True, "app": "MebeliX Kroy", "version": VERSION}


class LoginIn(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)


@app.get("/api/auth/config", tags=["tizim"])
def auth_config():
    """Kirish oynasi bormi (MEBELIX_USERS + MEBELIX_JWT_SECRET) — frontend 401 da shuni ko'rsatadi."""
    from .auth import login_enabled
    return {"login": login_enabled()}


@app.post("/api/auth/login", tags=["tizim"])
def auth_login(inp: LoginIn):
    """Login/parol → JWT (frontend uni `Authorization: Bearer` sifatida yuboradi)."""
    import time
    from .auth import issue_token, login_enabled
    if not login_enabled():
        raise HTTPException(404, _("login_off"))
    res = issue_token(inp.username.strip(), inp.password)
    if res is None:
        time.sleep(1)                                   # parolni tez-tez terib ko'rishni sekinlashtirish
        raise HTTPException(401, _("login_bad"))
    return res


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


def _invalidate_where(p: Project, pred) -> None:
    """Shartga mos detali bor CS operatsiyalarining kroyini eskirtirish."""
    for o in p.operations:
        if o.type in (OpType.CS, OpType.CL, OpType.CN) and any(pred(pt) for pt in o.parts):
            _invalidate(o)


def _products_qty_changed(p: Project, prids: set[str]) -> None:
    """Mahsulot soni o'zgardi → uning detallari soni (detal × mahsulot) o'zgardi → kroy eskirdi."""
    if prids:
        _invalidate_where(p, lambda pt: pt.product_id in prids)


# EL parametrlaridan detal zagotovka o'lchamiga ta'sir qiladiganlari
_EL_SIZE_FIELDS = ("thickness", "jointing_width")


def _uses_edge(pt: Part, oid: str) -> bool:
    """Detalning biror tomonida shu kromka (EL operatsiyasi) bormi."""
    return any(getattr(pt, f"edge_{sd}").op_id == oid for sd in ("top", "bottom", "left", "right"))


def _edge_affected_ops(p: Project, oid: str) -> list[Operation]:
    """Kromka o'lchami o'zgarsa natijasi o'chadigan kroy operatsiyalari (natijasi bor va shu kromkali detali bor)."""
    return [o for o in p.operations if o.type in (OpType.CS, OpType.CL, OpType.CN) and o.result is not None
            and o.result.maps and any(_uses_edge(pt, oid) for pt in o.parts)]


def _edge_size_changed(p: Project, old: Operation, new: Operation) -> None:
    """Kromka qalinligi/prifugovka o'zgarsa (yoki operatsiya EL bo'lib qolsa/bo'lmay qolsa) — shu kromkali
    detallar o'lchami o'zgaradi → kroy eskirdi."""
    if OpType.EL not in (old.type, new.type):
        return
    type_changed = old.type != new.type
    if type_changed or old.el is None or new.el is None or \
            any(getattr(old.el, f) != getattr(new.el, f) for f in _EL_SIZE_FIELDS):
        oid = new.id
        _invalidate_where(p, lambda pt: _uses_edge(pt, oid))


def _delete_project_rows(pid: str) -> None:
    """Loyihani o'chirish: omborga yozilgan qoldiqlari bekor qilinadi."""
    try:
        p = _load(pid)
    except HTTPException:
        return
    for op in p.operations:
        if op.type in (OpType.CS, OpType.CL, OpType.CN) and op.result and op.result.remnants_saved:
            warehouse.rollback(op)
    store.delete(pid)


def _need_cs(op: Operation) -> None:
    if op.type != OpType.CS:
        raise HTTPException(400, _("cs_only"))


def _need_cut(op: Operation) -> None:
    """Kroy / qoldiq endpointlari: listli (CS), pogonaj (CL) yoki nesting (CN, W16) kroy operatsiyasi."""
    if op.type not in (OpType.CS, OpType.CL, OpType.CN):
        raise HTTPException(400, _("cut_only"))


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
    parent = store.require_folder(f.parent_id)
    name = f.name.strip() or _("default_folder")
    if len(name) > 200:
        raise HTTPException(400, _("val_text_long", f="name", n=200))
    with SessionLocal() as s:
        r = FolderRow(id=uuid4().hex[:12], name=name, parent_id=parent, owner=user["name"])
        s.add(r); s.commit()
        return _folder(r)


@api.patch("/folders/{fid}", tags=["loyihalar"])
def rename_folder(fid: str, f: FolderPatch):
    with SessionLocal() as s:
        r = s.get(FolderRow, fid)
        if not r:
            raise HTTPException(404, _("folder_not_found"))
        if f.name is not None:
            if len(f.name.strip()) > 200:
                raise HTTPException(400, _("val_text_long", f="name", n=200))
            r.name = f.name.strip() or r.name
        if "parent_id" in f.model_fields_set:
            store.require_folder(f.parent_id)
            # papkani o'z ichiga ko'chirishning oldini olish
            cur = f.parent_id
            while cur:
                if cur == fid:
                    raise HTTPException(400, _("folder_into_itself"))
                row = s.get(FolderRow, cur)
                cur = row.parent_id if row else None
            r.parent_id = f.parent_id or None
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
        _delete_project_rows(pid)
    with SessionLocal() as s:
        for cur in reversed(ids):
            s.query(FolderRow).filter(FolderRow.id == cur).delete()
        s.commit()
    return {"ok": True, "deleted_projects": len(projects)}


# ───────────────────────── Loyihalar ─────────────────────────
@api.get("/projects", tags=["loyihalar"])
def list_projects(response: Response, folder_id: Optional[str] = None, q: str = "", status: Optional[int] = None,
                  all_folders: bool = False, limit: Optional[int] = Query(None, ge=1, le=5000), offset: int = Query(0, ge=0)):
    """Проекты ro'yxati: ID, Владелец, Состояние, Дата, Стоимость, Наименование.
    q berilsa — barcha papkalar bo'yicha qidiruv (nomi, raqami, buyurtmachi, MES raqami).
    Faqat ro'yxat ustunlari o'qiladi (loyiha JSON i emas). `limit`/`offset` — sahifalab; jami soni `X-Total-Count` sarlavhasida."""
    C = ProjectRow
    with SessionLocal() as s:
        st = select(C.id, C.number, C.owner, C.status, C.order_date, C.cost, C.name, C.folder_id, C.customer,
                    C.mes_order_ref, C.updated_at)
        q = q.strip()
        if q:
            # Unicode katta-kichik harfga sezgirsiz (kirill ham); `%` va `_` oddiy belgi (wildcard emas)
            cond = text_search(q, ProjectRow.name, ProjectRow.customer, ProjectRow.mes_order_ref)
            if q.isascii() and q.isdigit() and len(q) <= 12:
                cond = cond | (ProjectRow.number == int(q))
            st = st.where(cond)
        elif not all_folders:
            st = st.where(ProjectRow.folder_id == folder_id)
        if status is not None:
            st = st.where(ProjectRow.status == status)
        if limit is not None:
            response.headers["X-Total-Count"] = str(s.scalar(select(func.count()).select_from(st.subquery())))
            st = st.order_by(ProjectRow.number).limit(limit).offset(offset)
        else:
            st = st.order_by(ProjectRow.number)
        rows = s.execute(st).all()
        return [dict(id=r.id, number=r.number, owner=r.owner, status=r.status, order_date=r.order_date,
                     cost=r.cost, name=r.name, folder_id=r.folder_id, customer=r.customer or "",
                     mes_order_ref=r.mes_order_ref,
                     updated_at=r.updated_at.isoformat() + "Z" if r.updated_at else None) for r in rows]   # bazada UTC (naive)


class ProjectIn(BaseModel):
    name: str = ""
    folder_id: Optional[str] = None
    currency: Optional[str] = None
    owner: str = ""
    customer: str = ""
    mes_order_ref: Optional[str] = None


# matn maydonlari uzunligi (DB ustunlari: PostgreSQL uzun qiymatni rad etadi) va sanalar oralig'i
_TEXT_LIMITS = {"name": 300, "customer": 200, "owner": 100, "mes_order_ref": 100, "currency": 10}
_YEAR_MIN, _YEAR_MAX = 1990, 2100
MAX_PRODUCT_QTY = 100_000


def _check_len(field: str, value: Optional[str]) -> None:
    lim = _TEXT_LIMITS.get(field)
    if value is not None and lim and len(value) > lim:
        raise HTTPException(400, _("val_text_long", f=field, n=lim))


def _check_date(field: str, v: str) -> str:
    """Sana matni → ISO (YYYY-MM-DD); noto'g'ri yoki 1990..2100 dan tashqari (masalan 0001-01-01) — 400."""
    from datetime import date as _date
    from pydantic import TypeAdapter
    try:
        d = TypeAdapter(_date).validate_python(v.strip() if isinstance(v, str) else v)
    except ValidationError as e:
        raise HTTPException(400, _("val_date_bad", f=field, v=str(v)[:30])) from e
    if not (_YEAR_MIN <= d.year <= _YEAR_MAX):
        raise HTTPException(400, _("val_date_range", f=field, a=_YEAR_MIN, b=_YEAR_MAX))
    return d.isoformat()


def _check_header(fields: dict) -> dict:
    """Loyiha sarlavhasi maydonlarini tekshirish/tozalash (PATCH): 400 + tushunarli matn (tilga mos)."""
    f = dict(fields)
    if f.get("name") is not None:
        f["name"] = f["name"].strip() or _("default_project")      # bo'sh nom — «Без названия» (yaratishdagidek)
    if f.get("currency") is not None:
        f["currency"] = f["currency"].strip()
        if not f["currency"]:
            raise HTTPException(400, _("val_currency_empty"))
    for k in ("name", "currency", "customer", "owner", "mes_order_ref"):
        _check_len(k, f.get(k))
    if f.get("mes_order_ref") is not None and not f["mes_order_ref"].strip():
        f["mes_order_ref"] = None
    for k in ("order_date", "ready_date"):
        if f.get(k) is not None:
            f[k] = _check_date(k, f[k])
    if f.get("size_mode") is not None:
        from .models import SizeMode
        try:
            SizeMode(f["size_mode"])
        except ValueError as e:
            raise HTTPException(400, _("val_size_mode", v=str(f["size_mode"])[:30])) from e
    if "folder_id" in f:
        f["folder_id"] = store.require_folder(f["folder_id"])
    return f


@api.post("/projects", tags=["loyihalar"])
def create_project(inp: ProjectIn, user: dict = Depends(current_user)):
    app_cfg = settings.get_default("app")
    data = inp.model_dump()
    data["currency"] = (data["currency"] or "").strip() or app_cfg.get("currency", "UZS")
    data["owner"] = data["owner"] or user["name"]
    data["name"] = (data["name"] or "").strip() or _("default_project")
    for k in ("name", "currency", "customer", "owner", "mes_order_ref"):
        _check_len(k, data.get(k))
    data["folder_id"] = store.require_folder(data["folder_id"])
    p = Project(number=store.next_number(), **data)
    p.products.append(Product(name=_("default_product")))
    return store.save_new(p)


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
def update_project_header(pid: str, h: ProjectHeader, background: BackgroundTasks, user: dict = Depends(current_user)):
    fields = _check_header(h.model_dump(exclude_unset=True))
    new_status = fields.pop("status", None)      # holat — order_flow qoidalari bilan (rol, orqaga qaytarish, tarix yozuvi)
    with store.editing(pid) as p:
        old_status = p.status
        old_mode = p.size_mode
        upd = p.model_dump()
        for k, v in fields.items():
            if v is None and k not in NULLABLE_HEADER:
                continue
            upd[k] = v
        try:
            new = Project.model_validate(upd)
        except ValidationError as e:
            raise HTTPException(400, format_errors(e.errors())) from e
        for k in upd:
            setattr(p, k, getattr(new, k))
        if new_status is not None and new_status != old_status:
            order_flow.check_transition(p, new_status, user, strict_ready=False)   # PATCH: «Утвержден» sanasiz ham (eski mijozlar)
            order_flow.apply_transition(p, new_status, user, via="patch")
        if p.size_mode != old_mode:
            # O'lcham kiritish rejimi o'zgardi — detallar jismoniy o'lchami saqlanadi (qiymatlar yangi rejimga o'giriladi)
            from .services.sizes import compute_sizes
            edges = calc.edge_map(p)
            for o in p.operations:
                for pt in o.parts:
                    s = compute_sizes(calc.op_part(o, pt), old_mode, edges)       # (CL) eni = polosa eni, detal eni 0 qoladi
                    L, W = {"blank": s.blank, "detail": s.detail, "jointed": s.jointed}[p.size_mode.value]
                    pt.length = round(L, 3)
                    if o.type != OpType.CL:
                        pt.width = round(W, 3)
    if p.status != old_status:
        background.add_task(mes.send_webhook, "project.status", dict(
            project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, status=int(p.status),
            old_status=int(old_status)))
    return p


@api.delete("/projects/{pid}", tags=["loyihalar"])
def delete_project(pid: str):
    _load(pid)
    _delete_project_rows(pid)
    return {"ok": True}


class MoveProjects(BaseModel):
    ids: list[str]
    folder_id: Optional[str] = None


@api.post("/projects/move", tags=["loyihalar"])
def move_projects(m: MoveProjects):
    folder = store.require_folder(m.folder_id)          # mavjud bo'lmagan papka — 400 (loyiha yo'qolib qolmasin)
    for pid in m.ids:
        _load(pid)                                      # hammasi mavjudligi oldindan tekshiriladi (yarim ko'chirish yo'q)
    for pid in m.ids:
        with store.editing(pid, history=False) as p:
            p.folder_id = folder
    return {"ok": True, "count": len(m.ids)}


@api.post("/projects/{pid}/copy", tags=["loyihalar"])
def copy_project(pid: str, name: Optional[str] = None, folder_id: Optional[str] = None,
                 user: dict = Depends(current_user)):
    p = _load(pid)
    p.id = uuid4().hex[:12]
    p.number = store.next_number()
    p.name = name or (p.name + _("copy_suffix"))
    p.status = OrderStatus.NOT_ORDERED
    p.order_log = []                # nusxa — yangi buyurtma: holat tarixi nusxalanmaydi
    p.mes_order_ref = None
    p.owner = user["name"] or p.owner
    if folder_id is not None:
        p.folder_id = store.require_folder(folder_id)
    for op in p.operations:        # omborga bog'lanish va sex holati nusxalanmaydi
        warehouse.detach(op)
        for sh in op.sheets:       # ombordagi qoldiqqa havola nusxaga o'tmaydi (import kabi) — rezerv va chiqim asl loyihaniki
            sh.source_remnant_id = None
        if op.result:
            for m in op.result.maps:
                m.done_count = 0
    return store.save_new(p)


@api.post("/projects/{pid}/save", tags=["loyihalar"])
def save_project(pid: str):
    """«Сохранить»: loyiha har o'zgarishda saqlanadi; bu amal hisob-kitobni yangilaydi. O'zgarish bo'lmasa
    tarixga bo'sh versiya yozilmaydi (Ctrl+Z oldingi haqiqiy amalni qaytaradi)."""
    with store.editing(pid, skip_unchanged=True) as p:
        pass
    return p


@api.post("/projects/{pid}/undo", tags=["loyihalar"])
def undo(pid: str, background: BackgroundTasks, user: dict = Depends(current_user)):
    return _step(pid, -1, background, user)


@api.post("/projects/{pid}/redo", tags=["loyihalar"])
def redo(pid: str, background: BackgroundTasks, user: dict = Depends(current_user)):
    return _step(pid, +1, background, user)


def _step(pid: str, d: int, background: BackgroundTasks, user: dict) -> Project:
    """Undo/redo; holat (status) o'zgarsa — MES ga xabar (xuddi qo'lda o'zgartirilgandek). Holatni pasaytiradigan qadam
    «orqaga qaytarish» qoidasiga bo'ysunadi (order_flow.check_step)."""
    order_flow.check_step(pid, d, user)
    old_status = _load(pid).status
    p = store.step(pid, d)
    if p.status != old_status:
        background.add_task(mes.send_webhook, "project.status", dict(
            project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, status=int(p.status),
            old_status=int(old_status)))
    return p


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
        except ValidationError as e:
            raise HTTPException(400, _("bad_project_file", e=format_errors(e.errors()))) from e
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    try:
        raw = json.loads(data)
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(400, _("bad_project_file", e=_("val_json"))) from e
    if not isinstance(raw, dict):
        raise HTTPException(400, _("bad_project_not_obj"))
    if not any(k in raw for k in ("operations", "products")):      # `{}` / `{"x":1}` — bo'sh loyiha yaratilmasin
        raise HTTPException(400, _("bad_project_empty"))
    try:
        p = Project.model_validate(raw)           # chegaradan chiqqan eski qiymatlar qisqartiriladi (models.LEGACY_CTX)
    except ValidationError as e:                  # xom pydantic matni emas — «maydon: sabab»
        raise HTTPException(400, _("bad_project_file", e=format_errors(e.errors()))) from e
    n = _clamped_count(raw, p)
    return p, ([_("imp_clamped", n=n)] if n else [])


def _clamped_count(raw: dict, p: Project) -> int:
    """Importda chegaraga qisqartirilgan (soni / o'lcham) qiymatlar soni — foydalanuvchi ogohlantiriladi."""
    def num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    n = 0
    for rp, pr in zip(raw.get("products") or [], p.products):
        if isinstance(rp, dict) and num(rp.get("qty")) and rp["qty"] != pr.qty:
            n += 1
    for ro, op in zip(raw.get("operations") or [], p.operations):
        for rpt, pt in zip((ro.get("parts") if isinstance(ro, dict) else None) or [], op.parts):
            if isinstance(rpt, dict):
                n += sum(1 for k in ("qty", "minus_qty", "length", "width") if num(rpt.get(k)) and rpt[k] != getattr(pt, k))
    return n


def _normalize_imported(p: Project) -> None:
    """Import qilingan loyiha: mahsulot soni chegarasi (400), matn uzunliklari (DB ustunlari) va sanalar tuzatiladi."""
    from datetime import date as _date
    for pr in p.products:
        if not (0 <= pr.qty <= MAX_PRODUCT_QTY):
            raise HTTPException(400, _("val_product_qty", n=MAX_PRODUCT_QTY))
    p.name = (p.name or "").strip()[:_TEXT_LIMITS["name"]]
    p.customer = (p.customer or "")[:_TEXT_LIMITS["customer"]]
    p.owner = (p.owner or "")[:_TEXT_LIMITS["owner"]]
    p.currency = (p.currency or "").strip()[:_TEXT_LIMITS["currency"]]
    for k in ("order_date", "ready_date"):
        if not (_YEAR_MIN <= getattr(p, k).year <= _YEAR_MAX):
            setattr(p, k, _date.today())


def _store_imported(p: Project, folder_id: Optional[str], owner: str) -> Project:
    folder_id = store.require_folder(folder_id)
    _normalize_imported(p)
    p.number = store.next_number()
    p.id = uuid4().hex[:12]
    p.folder_id = folder_id or None
    p.owner = p.owner or owner
    p.name = (p.name or "").strip() or _("default_project")
    p.currency = p.currency or settings.get_default("app").get("currency", "UZS")
    p.mes_order_ref = None
    for op in p.operations:        # fayldagi ombor/sex holati bu bazaga tegishli emas
        warehouse.detach(op)
        for sh in op.sheets:
            sh.source_remnant_id = None
        if op.result:
            for m in op.result.maps:
                m.done_count = 0
    return store.save_new(p)


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


@api.post("/projects/{pid}/import-merge", tags=["loyihalar"])
async def import_merge(pid: str, files: list[UploadFile] = File(...)):
    """«Проект → Импортировать»: bir yoki bir nechta loyiha fayli (.project / .mxk.json) **ochiq loyihaga** qo'shiladi
    (mahsulot va operatsiyalar oxiriga; `services/project_merge.py`). Xato bergan fayl o'tkazib yuboriladi va ro'yxatda
    ko'rsatiladi; qolganlari qo'shiladi. Bitta tarix yozuvi (Ctrl+Z bilan hammasi qaytadi)."""
    from .services.project_merge import append_project
    if not files:
        raise HTTPException(400, _("bad_project_empty"))
    if len(files) > 50:
        raise HTTPException(400, _("import_too_many", n=50))
    loaded: list[tuple[str, Project, list[str]]] = []
    report: list[dict] = []
    for f in files:
        name = f.filename or "file"
        try:
            np_, warns = _import_bytes(await f.read(), name)
            _normalize_imported(np_)
            for op in np_.operations:              # fayldagi ombor/sex holati bu bazaga tegishli emas
                warehouse.detach(op)
                for sh in op.sheets:
                    sh.source_remnant_id = None
            loaded.append((name, np_, warns))
        except HTTPException as e:
            report.append(dict(file=name, ok=False, error=str(e.detail)))
    with store.editing(pid) as p:
        for name, np_, warns in loaded:
            st = append_project(p, np_)
            report.append(dict(file=name, ok=True, warnings=warns, **st))
    return {"project": store.load(pid), "files": report}


@api.get("/import/formats", tags=["loyihalar"])
def import_formats():
    from .plugins import formats
    return [dict(ext=".mxk.json", title="MebeliX loyihasi (.mxk.json)")] + formats()


# ───────────────────────── Mahsulotlar (Изделия) ─────────────────────────
def _check_product(pr: Product) -> None:
    """Mahsulot: soni 0..100000; «Доп. параметры» kalitlari bo'sh yoki takroriy (chekka bo'sh joylardan tashqari bir
    xil) bo'lmasin."""
    if not (0 <= pr.qty <= MAX_PRODUCT_QTY):
        raise HTTPException(400, _("val_product_qty", n=MAX_PRODUCT_QTY))
    seen: set[str] = set()
    for k in pr.extra:
        key = k.strip()
        if not key:
            raise HTTPException(400, _("val_extra_empty"))
        if key in seen:
            raise HTTPException(400, _("val_extra_dup", k=key))
        seen.add(key)


@api.post("/projects/{pid}/products", tags=["mahsulotlar"])
def add_product(pid: str, pr: Product, position: Optional[int] = None):
    _check_product(pr)
    with store.editing(pid) as p:
        if position is None or not (0 <= position <= len(p.products)):
            p.products.append(pr)
        else:
            p.products.insert(position, pr)
    return p


@api.put("/projects/{pid}/products/{prid}", tags=["mahsulotlar"])
def update_product(pid: str, prid: str, pr: Product):
    _check_product(pr)
    with store.editing(pid) as p:
        old = next((x for x in p.products if x.id == prid), None)
        if old is None:
            raise HTTPException(404, _("product_not_found"))
        pr.id = prid
        p.products = [pr if x.id == prid else x for x in p.products]
        if old.qty != pr.qty:
            _products_qty_changed(p, {prid})
    return p


@api.patch("/projects/{pid}/products/{prid}", tags=["mahsulotlar"])
def patch_product(pid: str, prid: str, fields: dict = Body(...)):
    with store.editing(pid) as p:
        for i, x in enumerate(p.products):
            if x.id == prid:
                d = x.model_dump(); d.update({k: v for k, v in fields.items() if k != "id"})
                p.products[i] = Product.model_validate(d)
                _check_product(p.products[i])
                if p.products[i].qty != x.qty:
                    _products_qty_changed(p, {prid})
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
        changed = {x.id for x in p.products if x.qty != 0}
        for x in p.products:
            x.qty = 0
        _products_qty_changed(p, changed)
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
        cp = src.model_copy(update={"id": uuid4().hex[:12], "name": src.name + _("copy_suffix")})
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


class SortKey(BaseModel):
    """Umumiy «Сортировка» oynasi: ustun kaliti va yo'nalishi (Напр = kamayish); ro'yxat tartibi — ustuvorlik."""
    by: str
    desc: bool = False


def _multi_sort(items: list, keys: dict, specs) -> None:
    """Ko'p kalitli barqaror saralash: oxirgi kalitdan boshlab ketma-ket (Python sort barqaror).
    specs — SortKey/dict ro'yxati; boshqa shakl (masalan eski mijozning bo'sh `{}` tanasi) — 400."""
    try:
        specs = [s if isinstance(s, SortKey) else SortKey.model_validate(s) for s in specs]
    except Exception:  # noqa: BLE001 — ro'yxat emas / noto'g'ri element
        raise HTTPException(400, _("sort_fields", f=", ".join(keys))) from None
    bad = [s.by for s in specs if s.by not in keys]
    if bad:
        raise HTTPException(400, _("sort_fields", f=", ".join(keys)))
    for s in reversed(specs):
        items.sort(key=keys[s.by], reverse=s.desc)


@api.post("/projects/{pid}/products/sort", tags=["mahsulotlar"])
def sort_products(pid: str, by: str = "name", desc: bool = False, specs: Any = Body(None)):
    keys = {"code": lambda x: x.code, "name": lambda x: x.name.lower(), "qty": lambda x: x.qty,
            "cost_material": lambda x: x.cost_material, "cost_operation": lambda x: x.cost_operation,
            "cost": lambda x: x.cost_material + x.cost_operation}
    with store.editing(pid) as p:
        _multi_sort(p.products, keys, specs or [SortKey(by=by, desc=desc)])
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
        return s.get(CatalogItemRow, ckey(item_id))


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
            if "price_per_m2" in prm:          # katalog narxi m² uchun — hisob ham m² bo'yicha
                op.cs_material.cost_by_sheets = not bool(prm["price_per_m2"])
            for k in ("grain", "texture"):     # material teksturasi → «Учет текстуры» (va yangi detallarda Ткт)
                if k in prm:
                    op.cs_cut.use_grain = bool(prm[k])
                    break
        op.sheets = [StockSheet(length=L, width=W)]
    elif op.type == OpType.CL:       # (CL) Погонажный раскрой (W11): cl_defaults + katalogdagi погонажный tovar; bitta polosa (cheksiz)
        from .services import cl_calc
        op.cl = cl_calc.new_cl_params(settings.get_default("cl_defaults"), item)
        op.sheets = [StockSheet(length=cl_calc.default_strip_length(item), width=op.cl.width)]
    elif op.type == OpType.CN:       # (CN) Нестинговый раскрой (W16): cn_defaults + katalog materiali; bitta list (cheksiz)
        from .services import cn_calc
        op.cn = cn_calc.new_cn_params(settings.get_default("cn_defaults"), item)
        L, W = cn_calc.default_sheet(item, settings.get_default("app"))
        op.sheets = [StockSheet(length=L, width=W)]
    elif op.type == OpType.EL:
        op.el = ELParams.model_validate(settings.get_default("el_defaults"))
        if item:
            op.el.price = item.price or op.el.price
            op.el.thickness = float(prm.get("thickness", item.thickness or op.el.thickness) or 0)
            op.el.width = float(prm.get("width", item.width or op.el.width) or op.el.width)
    elif op.type == OpType.GR:
        op.gr = GRParams.model_validate(settings.get_default("gr_defaults"))      # «Сохранить параметры по умолчанию»
    elif op.type == OpType.SP:       # (SP) Обработка поверхности (W12): standart parametrlar (sp_defaults); katalog materiali narxi
        from .services import sp_ops
        op.sp = sp_ops.new_params(settings.get_default("sp_defaults"))
        if item:
            op.sp.price = float(item.price or op.sp.price)
    elif op.type == OpType.XNC:
        op.xnc = XNCParams(**settings.get_default("xnc_defaults"))      # narxlar — «Сохранить … по умолчанию»
    elif op.type == OpType.O:
        op.o = o_ops.new_params(settings.get_default("o_defaults"))
    elif op.type == OpType.LB:       # (LB) Этикетки (W4): standart parametrlar (lb_defaults) va nom
        from .models import LBParams
        op.lb = LBParams.model_validate(settings.get_default("lb_defaults"))
        op.name = op.name or _(f"lb.op_name_{op.lb.source}")      # «Этикетки: Детали и остатки» (manbaga qarab; faqat yaratishda)
    return op


@api.post("/projects/{pid}/operations", tags=["operatsiyalar"])
def add_operation(pid: str, inp: OpIn, position: Optional[int] = None):
    if inp.material_id and _catalog_item(inp.material_id) is None:     # katalogda yo'q tovar — jimgina saqlanmasin
        raise HTTPException(404, _("catalog_item_not_found"))
    with store.editing(pid) as p:
        op = _new_operation(inp)
        if op.type == OpType.EL and op.el:      # har yangi kromka — o'z belgisi va rangi (avto: A, B, C … — band bo'lmagani)
            els = [o.el for o in p.operations if o.type == OpType.EL and o.el]
            from .services import el_symbols       # jadval: «Настройка символов и цветов» (sozlama `el_symbols`)
            op.el.symbol, op.el.color = el_symbols.next_style((e.symbol for e in els), len(els))
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
        if not o_ops.owner_ok(p, op):        # (O) egasi — mavjud mahsulot
            raise HTTPException(422, _("o_owner_not_found"))
        if op.parts == [] and old.parts:     # parametr yangilanishida detallar saqlanadi
            op.parts = old.parts
        # natija faqat serverda yaratiladi (Раскроить / tahrir / variant) — mijozdan kelgani qabul qilinmaydi
        op.result = old.result if op.type in (OpType.CS, OpType.CL, OpType.CN) and op.type == old.type else None
        p.operations = [op if o.id == oid else o for o in p.operations]
        if op.type != old.type and old.result is not None:
            warehouse.rollback(old)
        if op.result is not None and (
                _params_stale(old, op)
                or [x.model_dump(exclude={"used_qty", "left_qty"}) for x in op.parts]
                != [x.model_dump(exclude={"used_qty", "left_qty"}) for x in old.parts]
                or [x.model_dump(exclude={"used_qty"}) for x in op.sheets]
                != [x.model_dump(exclude={"used_qty"}) for x in old.sheets]):
            _invalidate(op)
        _edge_size_changed(p, old, op)
    return p


# kroy natijasini eskirtiradigan CS parametrlari (narx/ko'rinish maydonlari emas)
_CUT_AFFECTING_MAT = {"remnant_min_side1", "remnant_min_side2", "remnant_min_area", "remnant_size_incl_trim",
                      "min_part_size"}
# keyingi «Раскроить» strategiyasi — mavjud natijani yaroqsiz qilmaydi (omborga yozilgan qoldiqlar saqlanadi)
_CUT_NON_CUT = {"quality", "save_drawings", "merge_parts", "prefer_big_pack", "strip_sort", "in_strip_sort", "fill_packet",
                "use_warehouse"}


def _cs_params_stale(old: Operation, new: Operation) -> bool:
    om, nm = old.cs_material, new.cs_material
    if (om is None) != (nm is None) or (om and any(getattr(om, f) != getattr(nm, f) for f in _CUT_AFFECTING_MAT)):
        return True
    oc, nc = old.cs_cut, new.cs_cut
    if (oc is None) != (nc is None):
        return True
    return bool(oc and any(getattr(oc, f) != getattr(nc, f) for f in CSCutParams.model_fields if f not in _CUT_NON_CUT))


def _params_stale(old: Operation, new: Operation) -> bool:
    """Parametr o'zgarishi kroy natijasini eskirtiradimi: CS — `_cs_params_stale`, CL — `cl_calc.cl_params_stale`."""
    if new.type == OpType.CL:
        from .services import cl_calc
        return cl_calc.cl_params_stale(old, new)
    if new.type == OpType.CN:                      # (CN, W16)
        from .services import cn_calc
        return cn_calc.cn_params_stale(old, new)
    return new.type == OpType.CS and _cs_params_stale(old, new)


@api.patch("/projects/{pid}/operations/{oid}", tags=["operatsiyalar"])
def patch_operation(pid: str, oid: str, fields: dict = Body(...)):
    """Qisman yangilash: {name, code, print, new_page, description, cs_material:{...}, cs_cut:{...}, el:{...}, xnc:{...}}.
    Kesish parametrlari o'zgarsa kroy natijasi o'chiriladi (qayta «Раскроить» kerak)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        d = op.model_dump()
        for k, v in fields.items():
            if k in ("id", "type", "parts", "result", "sheets"):
                continue
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                d[k].update(v)
            else:
                d[k] = v
        new = Operation.model_validate(d)
        if not o_ops.owner_ok(p, new):       # (O) egasi — mavjud mahsulot
            raise HTTPException(422, _("o_owner_not_found"))
        new.parts, new.result, new.sheets = op.parts, op.result, op.sheets
        p.operations = [new if o.id == oid else o for o in p.operations]
        if _params_stale(op, new):
            _invalidate(new)
        _edge_size_changed(p, op, new)
    return p


@api.get("/projects/{pid}/operations/{oid}/edge-affected", tags=["operatsiyalar"])
def edge_affected(pid: str, oid: str):
    """(EL) «Толщина» / «Ширина прифуговки» o'zgartirilsa qaysi kroy natijalari o'chadi — UI oldindan tasdiq so'raydi
    (`_edge_size_changed` bilan bir xil shart, hech narsani o'zgartirmaydi).
    {fields: [...], ops: [{id, type, code, name, manual, remnants_saved}]}"""
    p = _load(pid)
    op = _op(p, oid)
    ops = _edge_affected_ops(p, oid) if op.type == OpType.EL else []
    return dict(fields=list(_EL_SIZE_FIELDS), ops=[dict(id=o.id, type=o.type, code=o.code, name=o.name,
                                                       manual=o.result.manual, remnants_saved=o.result.remnants_saved)
                                                  for o in ops])


@api.delete("/projects/{pid}/operations/{oid}", tags=["operatsiyalar"])
def delete_operation(pid: str, oid: str):
    with store.editing(pid) as p:
        op = _op(p, oid)
        if op.type in (OpType.CS, OpType.CL, OpType.CN) and op.result:
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
                if pt.surface_face_op == oid:      # (SP) sirt ishlovi havolalari
                    pt.surface_face_op = None
                if pt.surface_back_op == oid:
                    pt.surface_back_op = None
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
            pt.xnc_op_ids = []             # asl detallarning XNC si ulashilmaydi (clone_parts / clone_product kabi)
        for sh in cp.sheets:
            sh.id = uuid4().hex[:12]; sh.used_qty = 0
        p.operations.insert(p.operations.index(src) + 1, cp)
    return p


def _sort_ops(p: Project, by: str, desc: bool, specs: Optional[list[SortKey]]) -> None:
    """Operatsiyalarni saralash (loyiha ustida, saqlamasdan) — bir nechta amalni bitta tarix qadamiga yig'ish uchun."""
    order = {t: i for i, t in enumerate([OpType.O, OpType.CS, OpType.CN, OpType.CL, OpType.EL, OpType.SP,
                                          OpType.GR, OpType.XNC, OpType.LB])}
    keys = {"type": lambda o: order.get(o.type, 99), "name": lambda o: o.name.lower(), "code": lambda o: o.code,
            "cost_material": lambda o: o.cost_material, "cost_operation": lambda o: o.cost_operation,
            "cost": lambda o: o.cost_material + o.cost_operation, "print": lambda o: not o.print,
            "new_page": lambda o: not o.new_page}
    if specs:
        _multi_sort(p.operations, keys, specs)
    elif by == "cost":                         # eski xatti-harakat: qimmatdan arzonga
        _multi_sort(p.operations, keys, [SortKey(by="cost", desc=True)])
    else:
        _multi_sort(p.operations, keys, [SortKey(by=by, desc=desc)] + ([SortKey(by="name")] if by == "type" else []))


@api.post("/projects/{pid}/operations/sort", tags=["operatsiyalar"])
def sort_operations(pid: str, by: str = "type", desc: bool = False, specs: Any = Body(None)):
    with store.editing(pid) as p:
        _sort_ops(p, by, desc, specs)
    return p


@api.post("/projects/{pid}/actions/merge-same", tags=["operatsiyalar"])
def merge_same_operations(pid: str):
    """Общие действия → bir xil kod va nomli operatsiyalarni birlashtirish."""
    with store.editing(pid) as p:
        _merge_same(p)
    return p


def _merge_key(o: Operation) -> tuple:
    """«Объединить операции с одинаковым кодом и наименованием материала»: bir xil operatsiya — tur, kod, nom VA material
    (qalinlik, asosiy list o'lchami; kromkada — qalinlik / eni / prifugovka). Onlayn tizim yozuvi faqat kod va nomni aytadi;
    korpusda «Devor» 100 va 200 mm li ikki CS bir xil nomda — faqat nom bo'yicha birlashtirish ularni bitta 100 mm
    operatsiyaga qo'shib yuborardi (material almashib ketadi), shuning uchun qalinlik / list o'lchami ham solishtiriladi.
    Kesish parametrlari (propil, torsovka) solishtirilmaydi — birinchi operatsiyaniki qoladi."""
    k: tuple = (o.type, o.code, o.name)
    if o.type == OpType.EL and o.el:           # qalinligi / prifugovkasi boshqa kromka — boshqa material: birlashtirilmaydi
        k += tuple(getattr(o.el, f) for f in _EL_SIZE_FIELDS)
    elif o.type == OpType.CS and o.cs_material is not None:
        base = next((s for s in o.sheets if not s.is_remnant), None)
        k += (o.cs_material.thickness, (base.length, base.width) if base is not None else None)
    elif o.type == OpType.CL and o.cl is not None:
        k += (o.cl.thickness, o.cl.width)
    elif o.type == OpType.CN and o.cn is not None:
        k += (o.cn.thickness,)
    return k


def _merge_sheets(tgt: Operation, src: Operation) -> None:
    """Birlashtirilgan operatsiyaning «Листы и остатки» qatorlari yo'qolmaydi: bir xil qator (o'lcham, torsovka, otstup,
    qoldiq belgisi, ombor havolasi) — soni qo'shiladi (cheksiz qoladi), boshqalari ro'yxat oxiriga qo'shiladi."""
    def key(s: StockSheet) -> tuple:
        return (s.length, s.width, s.trim_length, s.trim_width, s.end_offset_bottom, s.end_offset_right, s.is_remnant, s.source_remnant_id)
    have = {key(s): s for s in tgt.sheets}
    for s in src.sheets:
        k = key(s)
        if k in have:
            t = have[k]
            t.qty = 10000 if (t.qty >= 10000 or s.qty >= 10000) else min(10000, t.qty + s.qty)
        else:
            s.used_qty = 0
            tgt.sheets.append(s)
            have[k] = s


def _merge_same(p: Project) -> None:
    """Bir xil (tur, kod, nom, material parametrlari) li CS/CL/CN/EL operatsiyalarni birlashtirish (loyiha ustida, saqlamasdan)."""
    seen: dict[tuple, Operation] = {}
    remap: dict[str, str] = {}
    out = []
    for o in p.operations:
        k = _merge_key(o)
        if o.type in (OpType.CS, OpType.CL, OpType.CN, OpType.EL) and k in seen:
            tgt = seen[k]
            if o.type != OpType.EL:
                _invalidate(o)             # olib tashlanadigan natija omborga yozilgan bo'lsa — bekor
                tgt.parts.extend(o.parts)
                _merge_sheets(tgt, o)
                _invalidate(tgt)
            elif o.el and tgt.el and any(getattr(o.el, f) != getattr(tgt.el, f) for f in _EL_SIZE_FIELDS):
                oid = o.id                 # kromka qalinligi boshqa — shu kromkali detallar o'lchami o'zgaradi
                _invalidate_where(p, lambda pt, oid=oid: _uses_edge(pt, oid))
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


@api.post("/projects/{pid}/actions/split-edges", tags=["operatsiyalar"])
def split_edges_by_material(pid: str):
    """Общие действия → kromka operatsiyalarini kroy materiallari bo'yicha ajratish."""
    from .services import el_symbols
    with store.editing(pid) as p:
        cs_ops = [o for o in p.operations if o.type == OpType.CS]
        new_ops: list[Operation] = []
        symbols = [o.el.symbol for o in p.operations if o.type == OpType.EL and o.el]     # yangi kromka — o'z belgisi va rangi
        for el in [o for o in p.operations if o.type == OpType.EL]:
            users = [cs for cs in cs_ops if any(getattr(pt, f"edge_{s}").op_id == el.id
                                                for pt in cs.parts for s in ("top", "bottom", "left", "right"))]
            for cs in users[1:]:
                cp = el.model_copy(deep=True, update={"id": uuid4().hex[:12], "name": f"{el.name} ({cs.name})"})
                if cp.el is not None:
                    cp.el.symbol, cp.el.color = el_symbols.next_style(iter(symbols), len(symbols))
                    symbols.append(cp.el.symbol)
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
    bir xil kromkalar birlashtiriladi, tartib: CS → EL → GR → XNC. Hammasi bitta tarix qadami (bitta Ctrl+Z)."""
    with store.editing(pid) as p:
        _merge_same(p)
        used_edges = {getattr(pt, f"edge_{s}").op_id for o in p.operations for pt in o.parts
                      for s in ("top", "bottom", "left", "right")}
        used_xnc = {x for o in p.operations for pt in o.parts for x in pt.xnc_op_ids}
        p.operations = [o for o in p.operations
                        if not ((o.type in (OpType.CS, OpType.CL, OpType.CN) and not o.parts) or (o.type == OpType.EL and o.id not in used_edges)
                                or (o.type == OpType.XNC and o.id not in used_xnc and o.xnc_part_id))]
        _sort_ops(p, "type", False, None)
    return p


@api.post("/projects/{pid}/actions/optimize-all", tags=["kroy"])
def optimize_all(pid: str, background: BackgroundTasks,
                 quality: Optional[Literal["fast", "normal", "max"]] = None,
                 only_remaining: bool = False, skip_done: bool = False):
    """«Раскроить все операции»: loyihadagi barcha kroy operatsiyalari (CS, CL, CN) ketma-ket, bitta tarix qadami
    (bitta Ctrl+Z). Har operatsiya uchun natija yoki xato qaytadi; bittasining xatosi qolganlarini to'xtatmaydi.
    skip_done=true — natijasi bor operatsiyalar o'tkazib yuboriladi («До кроить» kabi faqat qolganlari)."""
    res = compute.call("cut_all", dict(pid=pid, quality=quality, only_remaining=only_remaining, skip_done=skip_done))
    p = res["project"]
    for r in res["results"]:
        if "sheets" in r:
            background.add_task(mes.send_webhook, "cutting.done", dict(
                project_id=p["id"], number=p["number"], mes_order_ref=p.get("mes_order_ref"), op_id=r["op_id"], op_name=r["name"],
                sheets=r["sheets"], fill=r["fill"], kind="sheet", material_len_m=0))
    return res


@compute.task("cut_all")
def _task_cut_all(a: dict) -> dict:
    pid, quality = a["pid"], a.get("quality")
    only_remaining, skip_done = bool(a.get("only_remaining")), bool(a.get("skip_done"))
    out: list[dict] = []
    with store.editing(pid) as p:
        for op in p.operations:
            if op.type not in (OpType.CS, OpType.CL, OpType.CN):
                continue
            row: dict = dict(op_id=op.id, type=op.type, name=op.name)
            if skip_done and op.result and op.result.maps:
                out.append(dict(row, skipped=True, reason=_("cut_all_already")))
                continue
            why = _cut_input_error(p, op, only_remaining)
            if why:                                     # detalsiz / listsiz — xato emas, o'tkazib yuboriladi (QA #6); sababi qatorda
                out.append(dict(row, skipped=True, reason=why))
                continue
            if op.type == OpType.CS and (op.cs_material is None or op.cs_material.thickness <= 0):
                # qalinligi 0 — list materiali emas («zamena material», alyumin profil va h.k. o'rinbosarlar): korxona
                # fayllarida bunday 211 ta CS operatsiyadan birortasi ham kesilmagan; «Раскроить все» ularni o'tkazib yuboradi
                # (alohida «Раскроить» bilan baribir kesish mumkin)
                out.append(dict(row, skipped=True, reason=_("cut_all_t0")))
                continue
            try:
                _check_cut_size(p, op)
                _replace_result(op)
                if op.type == OpType.CL:
                    calc.run_linear(p, op, quality=quality, only_remaining=only_remaining)
                elif op.type == OpType.CN:
                    from .services import cn_calc
                    cn_calc.run_nesting(p, op, quality=quality)
                else:
                    calc.run_cutting(p, op, only_remaining=only_remaining, quality=quality)
                r = op.result
                out.append(dict(row, sheets=r.total_sheets if r else 0, fill=r.total_fill_percent if r else 0,
                                cut_length_m=r.total_cut_length_m if r else 0, unplaced=len(r.unplaced) if r else 0,
                                warnings=list(r.warnings) if r else []))
            except HTTPException as e:
                out.append(dict(row, error=str(e.detail)))
            except Exception as e:  # noqa: BLE001 — bitta operatsiya xatosi qolganlarini to'xtatmaydi
                out.append(dict(row, error=str(e)))
    return dict(project=p, results=out, message=_("cut_all_done", n=sum(1 for r in out if "sheets" in r)))


@api.post("/projects/{pid}/actions/recode-xnc", tags=["operatsiyalar"])
def recode_xnc(pid: str):
    """Общие действия → bir xil kodli XNC dasturlarni noyob qilish (stanok fayl nomlari to'qnashmasin):
    takrorlari `kod-2`, `kod-3` … bo'ladi (band bo'lmagan birinchi raqam)."""
    with store.editing(pid) as p:
        used = {o.code for o in p.operations if o.type == OpType.XNC and o.code}
        seen: set[str] = set()
        for o in p.operations:
            if o.type != OpType.XNC or not o.code:
                continue
            if o.code in seen:
                n = 2
                while f"{o.code}-{n}" in used or f"{o.code}-{n}" in seen:
                    n += 1
                o.code = f"{o.code}-{n}"
                used.add(o.code)
            seen.add(o.code)
    return p


@api.post("/projects/{pid}/actions/xnc-coding", tags=["operatsiyalar"])
def xnc_coding(pid: str, body: Optional[dict] = None, preview: bool = False):
    """«Кодирование» (XNC Параметры): barcha XNC kodlari `xnc_coding` sozlamasi (yoki so'rovdagi qiymatlar) bo'yicha qayta
    yaratiladi. `preview=1` — saqlanmaydi, birinchi bog'langan XNC uchun namuna kod qaytadi («Кодирование Настройки» oynasi)."""
    from .services import xnc_coding as XC
    cfg = settings.validate_data("xnc_coding", {**settings.get_default("xnc_coding"), **(body or {})})
    if preview:
        p = store.load(pid)
        first = next(((c, e) for _o, c, e in XC.codes(p, cfg) if c is not None or e), (None, ""))
        return dict(sample=first[0], error=first[1])
    with store.editing(pid) as p:
        st = XC.apply(p, cfg)
    return dict(project=p, **st)


# ───────────────────────── Detallar ─────────────────────────
@api.post("/projects/{pid}/operations/{oid}/parts", tags=["detallar"])
def add_parts(pid: str, oid: str, parts: list[Part], position: Optional[int] = None):
    with store.editing(pid) as p:
        op = _op(p, oid)
        uid = _next_uid(p)
        # v2: Ткт berilmagan yangi detal — material teksturali bo'lsa ✓ («Учет текстуры» — material teksturasi)
        has_grain = op.cs_cut.use_grain if op.cs_cut is not None else (op.cn.use_grain if op.cn is not None else False)   # (CN, W16)
        # brauzer qatorni darhol ko'rsatish uchun id ni o'zi beradi (TAB bilan qo'shish); loyihada band bo'lsa — yangi id
        taken = {x.id for o in p.operations for x in o.parts}
        for pt in parts:
            if pt.id in taken:
                pt.id = Part.model_fields["id"].default_factory()
            taken.add(pt.id)
        for pt in parts:
            if op.type == OpType.CL:                 # (CL) detal eni — polosa eni: Part.width 0 saqlanadi, tekstura ma'nosiz
                pt.width = 0
                pt.grain = False
            elif "grain" not in pt.model_fields_set:
                pt.grain = has_grain
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


# kroyga ta'sir qilmaydigan detal maydonlari (product_id — ta'sir qiladi: soni = detal × mahsulot)
_PART_NON_CUT = {"name", "description", "code", "surface_face_op", "surface_back_op", "xnc_op_ids", "user_params"}


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
            fields = {k: v for k, v in it.fields.items() if not (op.type == OpType.CL and k in ("width", "grain"))}   # (CL) eni — polosa eni
            if any(k not in _PART_NON_CUT and k not in ("id", "uid") and d.get(k) != v for k, v in fields.items()):
                stale = True
            d.update({k: v for k, v in fields.items() if k not in ("id", "uid")})
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
        sp_ids = {o.id for o in p.operations if o.type == OpType.SP}
        for k in ("surface_face_op", "surface_back_op"):           # (SP) lits / orqa: faqat mavjud SP operatsiya (W18 «Групповые действия»)
            v = g.fields.get(k)
            if v and v not in sp_ids:
                raise HTTPException(400, _("sp_not_found"))
        changed = False
        for i, pt in enumerate(op.parts):
            if pt.id in g.ids:
                d = pt.model_dump(); upd = {k: v for k, v in g.fields.items() if k not in ("id", "uid")}
                if op.type == OpType.CL:                                  # (CL) detal eni — polosa eni; tekstura ma'nosiz
                    upd.pop("width", None); upd.pop("grain", None)
                if any(k not in _PART_NON_CUT and d.get(k) != v for k, v in upd.items()):
                    changed = True
                d.update(upd)
                op.parts[i] = Part.model_validate(d)
        if changed:
            _invalidate(op)                                               # nom / tavsif / SP bog'lash kroyni eskirtirmaydi
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
                # (CL) pogonaj detalida eni yo'q (polosa eni — operatsiyadan): uzunlik 0 ga aylanmasin — faqat tomonlar almashadi
                if op.type != OpType.CL:
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
        if dst.type not in (OpType.CS, OpType.CL, OpType.CN):
            raise HTTPException(400, _("move_to_cut_only"))
        moving = [x for x in src.parts if x.id in sel.ids]
        src.parts = [x for x in src.parts if x.id not in sel.ids]
        if dst.type == OpType.CL:                  # (CL) detal eni polosa eni: CS dan kelgan eni saqlanmaydi (0)
            for x in moving:
                x.width = 0
        elif src.type == OpType.CL and src.cl:     # CL → CS: eni = polosa eni
            for x in moving:
                x.width = src.cl.width
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
def sort_parts(pid: str, oid: str, by: str = "uid", desc: bool = False, specs: Any = Body(None)):
    keys = {"uid": lambda x: x.uid, "name": lambda x: x.name.lower(), "length": lambda x: x.length,
            "width": lambda x: x.width, "qty": lambda x: x.qty, "code": lambda x: x.code,
            "area": lambda x: x.length * x.width, "product": lambda x: x.product_id or "",
            "grain": lambda x: not x.grain, "description": lambda x: x.description.lower()}
    with store.editing(pid) as p:
        op = _op(p, oid)
        _multi_sort(op.parts, keys, specs or [SortKey(by=by, desc=desc)])
    return p


@api.post("/projects/{pid}/operations/{oid}/parts/import", tags=["detallar"])
async def import_parts_ep(pid: str, oid: str, file: UploadFile = File(...),
                          col_map: str = Form(...), sheet: int = Form(0), start_row: int = Form(2)):
    """Excel/CSV dan detallar. Javob — loyiha (avvalgidek) + `imported` (qo'shilgan detallar soni), `skipped`
    (`[{row, reason}]` — o'tkazib yuborilgan qatorlar: qator raqami va sabab), `warnings` (matnlar: yangi kromka,
    o'tkazib yuborilgan qatorlar soni) va `created_edges` (yangi yaratilgan EL operatsiyalari id/nomi)."""
    data = await file.read(MAX_FILE_BYTES + 1)                 # xotirada, hajm chegarasi bilan (importers.check_size)
    with store.editing(pid) as p:
        op = _op(p, oid)
        try:
            res = import_parts_ex(p, data, file.filename or "", json.loads(col_map), sheet, start_row)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001 — buzuq/noto'g'ri fayl (csv, xlsx, zip) — foydalanuvchi xatosi
            raise HTTPException(400, _("import_error", e=e)) from e
        for pt in res.parts:
            pt.product_id = pt.product_id or (p.products[0].id if p.products else None)
        op.parts.extend(res.parts)
        if res.parts:
            _invalidate(op)
    out = jsonable_encoder(p)
    out.update(imported=len(res.parts), skipped=res.skipped, warnings=res.warnings,
               created_edges=[dict(id=o.id, name=o.name, symbol=o.el.symbol if o.el else "")
                              for o in res.created_edges])
    return out


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
                      thickness=op.cs_material.thickness if op.cs_material else (op.cn.thickness if op.cn else 16),   # (CN, W16) nesting — CNParams
                      qty=calc.effective_qty(p, pt))
        # nomsiz detal (Bazis importida ko'p uchraydi) — ishlov nomi bo'sh qolmasin: kod / ID bilan
        xop = Operation(type=OpType.XNC, code=code, name=pt.name or code, xnc=x, xnc_part_id=pt.id)
        pt.xnc_op_ids.append(xop.id)
        p.operations.append(xop)
    return p


# ───────────────────────── Listlar va qoldiqlar ─────────────────────────
@api.put("/projects/{pid}/operations/{oid}/sheets", tags=["listlar"])
def set_sheets(pid: str, oid: str, sheets: list[StockSheet]):
    """Listlar ro'yxati. Kroyda ishlatilgan list o'zgarmasa (yangi list qo'shildi / soni oshdi) natija saqlanadi —
    «До кроить» uchun."""
    ids = [s.id for s in sheets]
    if len(set(ids)) != len(ids):                 # bir xil id li ikki qator — kroy kartalari qaysi qatorga tegishli ekani noaniq bo'ladi
        raise HTTPException(422, _("sheets_dup_id"))
    rids = [s.source_remnant_id for s in sheets if s.source_remnant_id]
    if rids:
        with SessionLocal() as s_:
            missing = [rid for rid in rids if s_.get(RemnantRow, rid) is None]
        if missing:                               # omborda yo'q qoldiqqa havola — keyin «не хватает остатков» emas, darhol 404
            raise HTTPException(404, _("remnant_row_missing", ids=", ".join(str(x) for x in missing)))
    try:       # boshqa loyiha band qilgan ombor qoldig'ini qo'shib bo'lmaydi (REM-009)
        warehouse.check_sheets(pid, rids)
    except warehouse.WarehouseConflict as e:
        raise HTTPException(409, str(e)) from e
    for s in sheets:
        s.description = (s.description or "")[:500]
    with store.editing(pid) as p:
        op = _op(p, oid)
        old = {s.id: s for s in op.sheets}
        new = {s.id: s for s in sheets}
        stale = False
        if op.result:
            used: dict[str, int] = {}
            for m in op.result.maps:
                used[m.sheet_id] = used.get(m.sheet_id, 0) + m.copies
            # Kroyda ishlatilgan listning foydali zonasiga ta'sir qiluvchi hamma maydon (o'lcham, torsovka, chekkadagi otstup, qoldiq belgisi)
            zone = lambda s: (s.length, s.width, s.trim_length, s.trim_width, s.end_offset_bottom, s.end_offset_right, s.is_remnant)   # noqa: E731
            for sid, n in used.items():
                a, b = old.get(sid), new.get(sid)
                if b is None or a is None or zone(a) != zone(b) or (b.qty < 10000 and b.qty < n):
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


@api.get("/projects/{pid}/operations/{oid}/remnant-offer", tags=["listlar"])
def remnant_offer(pid: str, oid: str):
    """Kroydan keyingi taklif (eng kichik tejaydigan qoldiq) — `_remnant_offer`."""
    return _remnant_offer(pid, oid, 1)


def _remnant_offer(pid: str, oid: str, max_ok: int = 1):
    """Kroydan KEYIN (2026-10-24, foydalanuvchi qoidasi: kesish doim butun listlardan boshlanadi, faqat ularga sig'may qolgan
    detallar uchun qoldiq omboriga murojaat qilinadi): omborda shu materialdan (kalit `warehouse.material_key`, listli,
    qalinlik ±0.01) bor, butun listdan kichik qoldiq qo'shilsa umumiy material KAMAYADIMI — butun operatsiya tez rejimda qayta
    hisoblanadi (eng kichik qoldiqdan, ≤ 5 nomzod, ≤ 8 s); kamaytiradigan eng kichigi taklif qilinadi.
    Qoldiq boshqa loyihada band yoki operatsiyaga allaqachon qo'shilgan bo'lsa — taklif qilinmaydi.
    Javob: {rows: [qoldiq + fit_parts + saving_m2], tail: {map, parts, area_m2, fill} | null, flagged}."""
    p = _load(pid)
    op = _op(p, oid)
    flagged = sum(1 for pt in op.parts if pt.from_remnant)
    if op.type != OpType.CS or not op.result or not op.result.maps:
        return dict(rows=[], tail=None, flagged=flagged)
    unl = {sh.id for sh in op.sheets if sh.qty >= 10000}
    tail_map = next((m for m in reversed(op.result.maps) if m.sheet_id in unl), None)
    if tail_map is None or not tail_map.placements:
        return dict(rows=[], tail=None, flagged=flagged)
    cut = op.cs_cut or CSCutParams()
    off = 2 * ((cut.trim_length or 0) + (cut.kerf or 0))
    grain_on = bool(cut.use_grain)
    pmap = {pt.id: pt for pt in op.parts}
    parts_all = [(pt.length, pt.width, bool(pt.grain) and grain_on) for pt in op.parts if pt.qty > 0]
    tail = [(pl.length, pl.width, bool(pmap[pl.part_id].grain) and grain_on if pl.part_id in pmap else True)
            for pl in tail_map.placements]
    need = sum(l * w for l, w, _g in tail)
    key = warehouse.material_key(op)
    t_op = op.cs_material.thickness if op.cs_material else None
    have = {sh.source_remnant_id for sh in op.sheets if sh.source_remnant_id}
    full_area = tail_map.sheet_length * tail_map.sheet_width
    rules = remnant_rules.load()
    out = remnant_store.candidates(op)      # lokal yoki MES bazasi; nom «LDSP KASHMIR SHAGREN» = «ldsp  kashmir shagren»
    del key
    res = []
    for r in out:
        if r["id"] in have or (r.get("reserved_project") and r.get("reserved_project") != pid):
            continue
        if t_op and r.get("thickness") and abs(float(r["thickness"]) - float(t_op)) > 0.01:
            continue
        L, W = float(r["length"]) - off, float(r["width"]) - off
        if float(r["length"]) * float(r["width"]) >= full_area:
            continue                      # butun listdan kichik qoldiqlar
        if not any((l <= L and w <= W) or (not g and w <= L and l <= W) for l, w, g in parts_all):
            continue                      # hech bir detal sig'maydi
        res.append(r)
    res.sort(key=lambda r: float(r["length"]) * float(r["width"]))
    # haqiqiy mezon: shu qoldiq qo'shilsa umumiy MATERIAL kamayadimi (butun operatsiya tez rejimda qayta hisoblanadi; qoldiqqa
    # oxirgi list detallari emas, boshqa detallar ham tushishi mumkin — «4421»: 2385×449 + planka qoldiqqa, qolgani 1 listga)
    import time as _time
    from .services.optimizer import optimize as _opt
    fast = cut.model_copy(update={"quality": "fast"})
    items = calc._items_for(p, op, fast)
    base = sum(m.sheet_length * m.sheet_width * m.copies for m in op.result.maps) / 1e6
    t_end = _time.monotonic() + rules.find_seconds
    ok = []
    for r in res[:rules.find_limit]:
        if _time.monotonic() > t_end:
            break
        st = [sh.model_copy() for sh in op.sheets] + [StockSheet(id="offer", length=float(r["length"]), width=float(r["width"]),
                                                                   qty=1, is_remnant=True)]
        rr = _opt(items, st, fast, op.cs_material or CSMaterialParams())
        area = sum(m.sheet_length * m.sheet_width * m.copies for m in rr.maps) / 1e6
        if not rr.unplaced and area < base - 0.01 and any(m.sheet_id == "offer" for m in rr.maps):
            # mijozga sotish: qoldiq BUTUNLIGICHA, narxi = qoldiq m² / list m² × list narxi (= m² narxi × qoldiq m²)
            pr = calc.material_prices(op)
            ok.append({**r, "fit_parts": sum(len(m.placements) for m in rr.maps if m.sheet_id == "offer"),
                       "saving_m2": round(base - area, 3),
                       "percent": remnant_rules.percent_of(float(r["length"]), float(r["width"]), full_area),
                       "sale_price": round(float(r["area_m2"]) * pr["m2"], 2), "sheet_price": round(pr["sheet"], 2)})
            if len(ok) >= max_ok:
                break                     # taklif oynasi uchun eng kichik foydali qoldiq yetarli
    return dict(rows=ok, flagged=flagged,
                tail=dict(map=tail_map.index, parts=len(tail), area_m2=round(need / 1e6, 3), fill=tail_map.fill_percent))


class KeepIn(BaseModel):
    key: str = Field(max_length=100)
    keep: Optional[bool] = None          # None — qoida bo'yicha (tanlov bekor)


@api.get("/projects/{pid}/operations/{oid}/remnant-intake", tags=["qoldiqlar"])
def remnant_intake(pid: str, oid: str):
    """«Остатки: приход» (2026-10-24): shu operatsiya kroyidan bazaga kirim — har qoldiq bo'lagi foizi, qoida bo'yicha
    va texnolog tanlovi bo'yicha «omborga» / «mijozga»; ishlatilgan (sotiladigan) ombor qoldiqlari; yozilganmi."""
    p = _load(pid)
    op = _op(p, oid)
    _need_cut(op)
    res = op.result
    rules = remnant_rules.load()
    cls = remnant_rules.classify(op, rules, require_rule=False) if op.type == OpType.CS else None
    pieces = []
    if cls:
        agg: dict[str, dict] = {}
        for pc in cls["pieces"]:
            if pc["kind"] != "remnant" and not pc["keep"]:
                continue                  # mayda chiqindi ro'yxatda ko'rsatilmaydi
            g = agg.setdefault(pc["key"], {k: pc[k] for k in ("key", "map", "length", "width", "area_m2", "percent", "keep",
                                                               "auto_keep", "manual")} | dict(qty=0))
            g["qty"] += pc["copies"]
        pieces = sorted(agg.values(), key=lambda g: (-g["area_m2"], g["map"]))
    pr = calc.material_prices(op) if op.type == OpType.CS else dict(m2=0.0, sheet=0.0)
    by_id = {sh.source_remnant_id: sh for sh in op.sheets if sh.source_remnant_id}
    consumed = [dict(id=rid, qty=n, length=by_id[rid].length, width=by_id[rid].width,
                     area_m2=round(by_id[rid].length * by_id[rid].width / 1e6, 3),
                     sale_price=round(by_id[rid].length * by_id[rid].width / 1e6 * pr["m2"] * n, 2))
                for rid, n in warehouse.consumed(op).items() if rid in by_id]
    return dict(saved=bool(res and res.remnants_saved), keep_percent=cls["percent"] if cls else None,
                rule_source=cls["source"] if cls else None, sheet_m2=cls["sheet_m2"] if cls else None,
                material=op.name, code=op.code or "", type=remnant_rules.material_type(op.code, op.name),
                pieces=pieces, consumed=consumed, source=remnant_store.source(rules),
                pending=bool(op.type == OpType.CS and warehouse._mes_wait(rules)), has_result=bool(res and res.maps))


@api.put("/projects/{pid}/operations/{oid}/remnant-intake", tags=["qoldiqlar"])
def remnant_intake_set(pid: str, oid: str, f: KeepIn):
    """Texnolog tanlovi: bo'lak omborga (true) / mijozga (false) / qoida bo'yicha (null). Bazaga yozilgandan keyin — avval bekor qiling."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
        if not op.result or not op.result.maps:
            raise HTTPException(400, _("no_result"))
        if op.result.remnants_saved:
            raise HTTPException(409, _("remnants_already"))
        if f.keep is None:
            op.result.remnant_keep.pop(f.key, None)
        else:
            op.result.remnant_keep[f.key] = f.keep
    return remnant_intake(pid, oid)


@api.get("/projects/{pid}/operations/{oid}/remnant-match", tags=["qoldiqlar"])
def remnant_match(pid: str, oid: str):
    """«Остатки: расход» (2026-10-24): bazadagi aynan shu material (kod / nom) qoldiqlari — yuqorida material sarfini
    KAMAYTIRADIGANLARI (tejash m², mijozga narxi; kroydan keyin), pastda detallari sig'adigan barcha qoldiqlar (qaysi detallar)."""
    p = _load(pid)
    op = _op(p, oid)
    _need_cut(op)
    if op.type != OpType.CS:
        return dict(saving=[], fitting=[], cut=False)
    has_cut = bool(op.result and op.result.maps)
    saving = _remnant_offer(pid, oid, 3)["rows"] if has_cut else []
    cut = op.cs_cut or CSCutParams()
    off = 2 * ((cut.trim_length or 0) + (cut.kerf or 0))
    grain_on = bool(cut.use_grain)
    t_op = op.cs_material.thickness if op.cs_material else None
    have = {sh.source_remnant_id for sh in op.sheets if sh.source_remnant_id}
    full = remnant_rules.sheet_area_mm2(op)
    pr = calc.material_prices(op)
    parts = [pt for pt in op.parts if pt.qty > 0]
    fitting = []
    for r in remnant_store.candidates(op):
        if r.get("reserved_project") and r["reserved_project"] != pid:
            continue
        if t_op and r.get("thickness") and abs(float(r["thickness"]) - float(t_op)) > 0.01:
            continue
        L, W = float(r["length"]) - off, float(r["width"]) - off
        fits = [dict(id=pt.id, name=pt.name, length=pt.length, width=pt.width, qty=pt.qty) for pt in parts
                if (pt.length <= L and pt.width <= W) or (not (pt.grain and grain_on) and pt.width <= L and pt.length <= W)]
        if not fits:
            continue
        fitting.append({**r, "in_sheets": r["id"] in have, "fit_parts": fits, "fit_count": sum(f["qty"] for f in fits),
                        "percent": remnant_rules.percent_of(float(r["length"]), float(r["width"]), full) if full else None,
                        "sale_price": round(float(r["area_m2"]) * pr["m2"], 2)})
    fitting.sort(key=lambda r: (r["in_sheets"], float(r["area_m2"])))
    return dict(saving=saving, fitting=fitting[:50], cut=has_cut, material=op.name, code=op.code or "",
                type=remnant_rules.material_type(op.code, op.name))


@api.post("/projects/{pid}/operations/{oid}/sheets/from-remnants", tags=["listlar"])
def sheets_from_remnants(pid: str, oid: str, sel: IdsIn, force: bool = False):
    """Листы и остатки → ombordagi qoldiqlarni qo'shish (kroyda birinchi navbatda ishlatiladi).
    Qalinligi operatsiya materialidan farq qilgan qoldiq — 400 («Показать все материалы» rejimida `force=true` bilan ruxsat)."""
    rows = remnant_store.get_many(sel.ids)          # lokal yoki MES bazasidan
    missing = [i for i, r in zip(sel.ids, rows) if r is None]
    if missing:
        raise HTTPException(404, _("remnant_row_missing", ids=", ".join(str(x) for x in missing)))
    op0 = _op(_load(pid), oid)            # tur va qoldiq turi (listli / погонажный) mosligi rezervdan OLDIN tekshiriladi
    _need_cut(op0)
    want_linear = op0.type == OpType.CL
    if any(r is not None and bool(r.get("linear", False)) != want_linear for r in rows):
        raise HTTPException(400, _("cl_linear_only" if want_linear else "cl_sheet_only"))
    if not force:                         # qalinlik mos kelmasa — boshqa material (masalan 16 va 18 mm) adashib qo'shilmasin
        t_op = (op0.cs_material.thickness if op0.cs_material else None) if op0.type == OpType.CS else \
            (op0.cl.thickness if op0.cl else None) if op0.type == OpType.CL else (op0.cn.thickness if op0.cn else None)
        for r in rows:
            if r is not None and t_op and r["thickness"] and abs(float(r["thickness"]) - float(t_op)) > 0.01:
                raise HTTPException(400, _("remnant_thickness", id=r["id"], t=f"{float(r['thickness']):g}", t2=f"{float(t_op):g}"))
    try:       # rezerv: tanlangan qoldiqlar shu loyiha uchun band qilinadi; boshqa loyiha band qilgan bo'lsa — 409
        warehouse.reserve(pid, [r["id"] for r in rows if r is not None and (r["qty"] or 0) > 0], atomic=True)
    except warehouse.WarehouseConflict as e:
        raise HTTPException(409, str(e)) from e
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
        have = {sh.source_remnant_id for sh in op.sheets if sh.source_remnant_id}
        for r in rows:
            if r is None or r["id"] in have or (r["qty"] or 0) <= 0:
                continue
            note = r.get("note") or ""
            op.sheets.insert(0, StockSheet(length=r["length"], width=(op.cl.width if op.type == OpType.CL and op.cl else r["width"]),
                                           qty=r["qty"], is_remnant=True,
                                           source_remnant_id=r["id"],
                                           description=_("remnant_sheet", id=r["id"]).capitalize() + (f" ({note})" if note else "")))
        _invalidate(op)
    return p


# ───────────────────────── Kroy ─────────────────────────
def _max_cut_items() -> int:
    try:
        return max(1, int(os.getenv("MEBELIX_MAX_CUT_ITEMS", "20000")))
    except ValueError:
        return 20000


def _check_cut_size(p: Project, op: Operation) -> None:
    """Bitta kroyga kiradigan detal nusxalari soni chegarasi (standart 20000, `MEBELIX_MAX_CUT_ITEMS`): juda katta
    hajm loyiha qulfini daqiqalab band qilmasin (optimizator o'zgarmaydi) — 400 + tushunarli matn."""
    n = sum(calc.effective_qty(p, pt) for pt in op.parts)
    if n > _max_cut_items():
        raise HTTPException(400, _("cut_too_many", n=n, max=_max_cut_items()))


def _cut_input_error(p, op, only_remaining: bool = False) -> Optional[str]:
    """Kroy uchun kirish ma'lumoti yo'q bo'lsa — foydalanuvchi tilidagi sabab (aks holda None). Detal qatorlari yo'q yoki hammasining
    kroyga kiradigan soni (ОК − МК) 0; list (CL da — polosa) qatorlari yo'q yoki hammasining soni 0 (qoldiqlar ham shu ro'yxatda).
    Avval bunday holatda kroy baribir ishga tushib, «0 list, sig'madi: N» natija berardi. «До кроить» da list soni tekshirilmaydi
    (bo'sh listlar hisobini kroyning o'zi qiladi)."""
    bars = op.type == OpType.CL
    if not op.parts:
        return _("no_parts")
    if not only_remaining and sum(calc.effective_qty(p, pt) for pt in op.parts) <= 0:
        return _("no_parts_qty")
    if not op.sheets:
        return _("no_bars" if bars else "no_sheets")
    if not only_remaining and all((sh.qty or 0) <= 0 for sh in op.sheets):
        return _("no_bars_qty" if bars else "no_sheets_qty")
    return None


@api.post("/projects/{pid}/operations/{oid}/optimize", tags=["kroy"])
def optimize_op(pid: str, oid: str, background: BackgroundTasks,
                quality: Optional[Literal["fast", "normal", "max"]] = None,
                first_cut: Optional[FirstCutDir] = None, only_remaining: bool = False, fill_free: bool = True):
    """Раскроить (only_remaining=True — «До кроить»: faqat kroyga kirmagan detallar; fill_free — avval mavjud kartalarning
    bo'sh joylariga (onlayn tizimdagidek, standart), False — faqat yangi listlarga; operator «До кроить» oynasida tanlaydi).
    Hisob — `compute` navbati orqali (2-bosqich: alohida ishchi jarayonda)."""
    out = compute.call("cut", dict(pid=pid, oid=oid, quality=quality, first_cut=None if first_cut is None else int(first_cut),
                                   only_remaining=only_remaining, fill_free=fill_free))
    background.add_task(mes.send_webhook, "cutting.done", out["hook"])
    return out["result"]


def _auto_commit_remnants(p: Project, op: Operation) -> None:
    """«Правила остатков → записывать автоматически» (2026-10-24): kroydan keyin olib qolinadigan qoldiqlar omborga
    (MES kutishi bilan «kutilmoqda») va ishlatilgan ombor qoldiqlari chiqimga tasdiqsiz yoziladi. Ombor to'qnashuvi bo'lsa —
    yozilmaydi (xodim «Деловые остатки → склад» oynasida ko'radi)."""
    from .services import remnant_rules
    res = op.result
    if op.type != OpType.CS or not res or not res.maps or res.remnants_saved or res.unplaced:
        return
    if not remnant_rules.load().auto_commit:
        return
    try:
        warehouse.commit(p, op)
    except (warehouse.WarehouseConflict, ValueError) as e:
        import logging as _lg
        _lg.getLogger("mebelix.warehouse").warning("qoldiqlar omborga avtomatik yozilmadi (%s / %s): %s", p.number, op.id, e)


@compute.task("cut")
def _task_cut(a: dict) -> dict:
    pid, oid, quality, only_remaining = a["pid"], a["oid"], a.get("quality"), bool(a.get("only_remaining"))
    first_cut = None if a.get("first_cut") is None else FirstCutDir(a["first_cut"])
    fill_free = a.get("fill_free", True)
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
        why = _cut_input_error(p, op, only_remaining)
        if why:
            raise HTTPException(400, why)
        _check_cut_size(p, op)
        _replace_result(op)
        if op.type == OpType.CL:                   # (CL) pogonaj kroy: 1D optimizator (cl_optimizer); «До кроить» — W18 (cl_calc._run_remaining)
            calc.run_linear(p, op, quality=quality, only_remaining=only_remaining)
        elif op.type == OpType.CN:                 # (CN, W16) nesting (sinxron; UI uchun fon vazifasi: `api_cn.py` → `cn/jobs`)
            from .services import cn_calc
            n_items = sum(calc.effective_qty(p, pt) for pt in op.parts)
            if n_items > cn_calc.max_items():
                raise HTTPException(400, _("cn.too_many", n=n_items, max=cn_calc.max_items()))
            try:
                cn_calc.run_nesting(p, op, quality=quality)
            except RuntimeError as e:             # mustaqil tekshiruv (validate_cn) rad etdi — nesting xatosi
                raise HTTPException(500, str(e)) from e
        else:
            calc.run_cutting(p, op, only_remaining=only_remaining, first_cut=first_cut, quality=quality, fill_free=fill_free)
            _auto_commit_remnants(p, op)
    res = op.result
    return dict(result=res, hook=dict(
        project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, op_id=op.id, op_name=op.name,
        sheets=res.total_sheets if res else 0, fill=res.total_fill_percent if res else 0,
        kind=res.kind if res else "sheet", material_len_m=res.material_len_m if res else 0))


@api.post("/projects/{pid}/operations/{oid}/variants", tags=["kroy"])
def cutting_variants(pid: str, oid: str):
    """Kroy variantlarini solishtirish (CS: optimal / 1-kesish uzunlik bo'yicha / eni bo'yicha; CL (W18): kam material /
    kam sarf / kam kesim / maksimal sifat — 1D da «uzunlik / eni bo'yicha» ma'nosiz). Tanlangan variant `PUT .../result` bilan saqlanadi."""
    return compute.call("variants", dict(pid=pid, oid=oid))


@compute.task("variants")
def _task_variants(a: dict):
    pid, oid = a["pid"], a["oid"]
    p = _load(pid)
    op = _op(p, oid)
    if op.type != OpType.CL:
        _need_cs(op)
    why = _cut_input_error(p, op)
    if why:
        raise HTTPException(400, why)
    _check_cut_size(p, op)
    if op.type == OpType.CL:
        return calc.cl_variants(p, op)
    return calc.cutting_variants(p, op)


@api.delete("/projects/{pid}/operations/{oid}/result", tags=["kroy"])
def delete_result(pid: str, oid: str):
    with store.editing(pid) as p:
        _invalidate(_op(p, oid))
    return p


@api.put("/projects/{pid}/operations/{oid}/result", tags=["kroy"])
def save_edited_result(pid: str, oid: str, result: dict = Body(...), base: Optional[str] = None):
    """Tahrirlangan (yoki tanlangan variant) natijani saqlash — qayta quriladi va tekshiriladi.
    `base` (ixtiyoriy, `GET .../edit/rev`) — muharrir ochilgandagi natija izi: shu orada natija boshqa oynada o'zgargan
    bo'lsa — 409 (parallel tahrirda yangi natija jimgina ustidan yozilmaydi)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
        if base:
            from .services import cl_editor, cn_editor, editor_w13
            rev_fn = cl_editor.result_rev if op.type == OpType.CL else (cn_editor.result_rev if op.type == OpType.CN else editor_w13.result_rev)
            if base != rev_fn(op.result):
                raise HTTPException(409, _("ed.conflict"))
        res = CuttingResult.model_validate(result)
        if op.type == OpType.CN:                   # (CN, W16) CNE: qoralama qayta quriladi (poligonlar serverda) va validate_cn dan o'tadi
            from .services import cn_calc, cn_editor
            new = cn_editor.rebuild(p, op, res, final=True)
            new.manual = res.manual
            new.variant = res.variant
            new.nest = dict(res.nest or {})
            _replace_result(op)
            op.result = new
            calc._account(p, op)
            cn_calc.cn_cost(p, op)
            return p
        if op.type == OpType.CL:                   # (CL) CLE: qoralama qayta quriladi va validate_cl dan o'tadi
            from .services import cl_editor
            new = cl_editor.rebuild(p, op, res, final=True)
            new.manual = res.manual
            new.variant = res.variant
            _replace_result(op)
            op.result = new
            calc._account(p, op)
            calc.cl_cost(p, op)
            return p
        if res.maps and all(m.strips for m in res.maps):
            new = editor.rebuild(p, op, res)
            new.manual = res.manual
            new.variant = res.variant
        else:
            from .services.validate import validate
            for m in res.maps:            # daraxtsiz (eski) natija: mijoz daraxti qabul qilinmaydi
                m.strips = []
            errs = validate(res, calc._items_for(p, op, op.cs_cut), op.sheets, op.cs_cut)
            if errs:
                raise editor.EditError(errs[0], errs)
            new = res
            warehouse.detach_result(new)       # ombor bog'lanishi faqat server amallarida
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
    _need_cut(op)
    if op.type == OpType.CL:                       # (CL) CLE amallari: services/cl_editor.py
        from .services import cl_editor
        return cl_editor.apply(p, op, inp.result, inp.action)
    if op.type == OpType.CN:                       # (CN, W16) CNE amallari: services/cn_editor.py
        from .services import cn_editor
        return cn_editor.apply(p, op, inp.result, inp.action)
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
            m.comment = mp.comment[:2000]            # muharrir (`editor.COMMENT_MAX`) bilan bir xil chegara
        if mp.done_count is not None:
            m.done_count = max(0, min(m.copies, mp.done_count))
            background.add_task(mes.send_webhook, "map.done", dict(
                project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, op_id=op.id, map=idx,
                done=m.done_count, copies=m.copies))
    if mp.done_count is not None:        # list arradan chiqdi — shu kartaning olib qolingan qoldiqlari «mavjud» (2026-10-24)
        warehouse.on_map_done(p, op, idx, m.done_count)
    return p


@api.get("/projects/{pid}/operations/{oid}/maps/{idx}.svg", tags=["kroy"])
def map_svg(pid: str, oid: str, idx: int, width: int = 900, label: str = "number_name", edges: bool = True,
            mirror: bool = False):
    p = _load(pid); op = _op(p, oid)
    if not op.result or not (1 <= idx <= len(op.result.maps)):
        raise HTTPException(404, _("no_map"))
    if op.type == OpType.CL:                       # (CL) 1D karta: polosa (services/cl_render.py)
        from .services import cl_render
        return Response(cl_render.strip_map_svg(op.result.maps[idx - 1], max(100, min(width, 4000)), p, op, label, edges, mirror),
                        media_type="image/svg+xml")
    if op.type == OpType.CN:                       # (CN, W16) nesting kartasi: haqiqiy kontur (services/cn_render.py)
        from .services import cn_render
        return Response(cn_render.nest_map_svg(op.result.maps[idx - 1], max(100, min(width, 4000)), p, op, label, edges, mirror),
                        media_type="image/svg+xml")
    svg = render.map_svg(op.result.maps[idx - 1], max(100, min(width, 4000)), None, p, op, label, edges, True, mirror)
    return Response(svg, media_type="image/svg+xml")


# ───────────────────────── Qoldiqlarni omborga yozish ─────────────────────────
@api.get("/projects/{pid}/operations/{oid}/remnants", tags=["qoldiqlar"])
def op_remnants(pid: str, oid: str):
    p = _load(pid); op = _op(p, oid)
    _need_cut(op)
    res = op.result
    rules = remnant_rules.load()
    rr = remnant_rules.op_rule(op, rules)
    sheet_mm2 = remnant_rules.sheet_area_mm2(op) if op.type == OpType.CS else 0
    rem = warehouse.business_remnants(op)
    for g in rem:
        g["percent"] = remnant_rules.percent_of(g["length"], g["width"], sheet_mm2) if sheet_mm2 else None
    return dict(saved=bool(res and res.remnants_saved), remnants=rem,
                consumed=warehouse.consumed(op), material_code=warehouse.material_key(op),
                keep_percent=rr[0] if rr else None, rule_source=rr[1] if rr else None,
                client=warehouse.client_pieces(op, rules), source=remnant_store.source(rules),
                pending=bool(op.type == OpType.CS and warehouse._mes_wait(rules)))


@api.post("/projects/{pid}/operations/{oid}/remnants/commit", tags=["qoldiqlar"])
def op_remnants_commit(pid: str, oid: str):
    """Kroydan keyin (tasdiq bilan): деловой qoldiqlarni omborga yozish, ishlatilgan qoldiqlarni hisobdan chiqarish."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
        try:
            out = warehouse.commit(p, op)
        except warehouse.WarehouseConflict as e:
            raise HTTPException(409, str(e)) from e
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    return {**out, "project": p}


@api.post("/projects/{pid}/operations/{oid}/remnants/rollback", tags=["qoldiqlar"])
def op_remnants_rollback(pid: str, oid: str):
    with store.editing(pid) as p:
        op = _op(p, oid)
        _need_cut(op)
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
    from .services import xnc_constraints
    return {**xnc_cost(op), **xnc_constraints.stats_fields(op, p)}       # + stanok cheklovlari xabarlari (W8)


@api.get("/projects/{pid}/operations/{oid}/xnc-sheet", response_class=HTMLResponse, tags=["xnc"])
def xnc_sheet(pid: str, oid: str, lang: Literal["ru", "uz"] = "ru"):
    """«Чертеж» (detal «XNC Редактор» oynasi): o'lchamli chizma + teshiklar jadvali + shtamp."""
    p = _load(pid); op = _op(p, oid)
    if not op.xnc:
        raise HTTPException(400, _("not_xnc"))
    return _html(render.xnc_sheet_html(p, op, lang))


@api.get("/projects/{pid}/operations/{oid}/xnc.svg", tags=["xnc"])
def xnc_svg(pid: str, oid: str, width: int = 560, machine: bool = False, height: int = 0, dims: bool = False):
    """Detal chizmasi. Stanok cheklovlari (Настройки → XNC → Ограничения) qo'shimcha burish bersa — chizmada yozuv chiqadi;
    `machine=true` — chizma stanokdagi (burilgan) holatda; `height` — ko'rsatiladigan maydon balandligi (px, minimal ko'rinadigan
    o'lchamlar uchun masshtab); `dims=true` — eni / bo'yi yozuvlari (standart yo'q, onlayn ko'rinishdagi kabi)."""
    p = _load(pid); op = _op(p, oid)
    if not op.xnc:
        raise HTTPException(400, _("not_xnc"))
    from .services import xnc_constraints
    turn = xnc_constraints.analyze(op, p)["extra_turn"]            # rejim off — 0
    return Response(xnc_drawing_svg(op, p, max(100, min(width, 3000)), turn=turn, turned=machine,
                                    height_px=max(0, min(height, 3000)), dims=dims), media_type="image/svg+xml")


# ───────────────────────── Postprotsessor ─────────────────────────
def _refit_rotations(pid: str, oid: str, rotations: int):
    """Stanok formati kesim darajasini cheklasa: «Макс. количество вращений» = `rotations` qilib, kroyni qayta bajaradi va
    loyihani saqlaydi. Qaytaradi: (loyiha, operatsiya, yangi burilishlar soni)."""
    with store.editing(pid) as p:
        op = _op(p, oid)
        if op.result is not None and op.result.remnants_saved:   # omborga yozilgan qoldiqlar — jimgina bekor qilinmaydi
            raise HTTPException(400, _("pp_refit_remnants", n=rotations))
        op.cs_cut = (op.cs_cut or CSCutParams()).model_copy(update={"max_rotations": rotations})
        _replace_result(op)
        calc.run_cutting(p, op)
    p = _load(pid)
    return p, _op(p, oid), rotations


def _refit_copy(p: Project, op: Operation, rotations: int):
    """Vaqtinchalik nusxada qayta kroy (QA #3): saqlanmaydi — loyihadagi natija (qo'lda tahrir, izohlar, omborga yozilgan
    qoldiqlar) o'zgarmaydi; fayl shu nusxadan chiqariladi. Qaytaradi: (nusxa loyiha, nusxa operatsiya, burilishlar soni)."""
    p2 = p.model_copy(deep=True)
    op2 = _op(p2, op.id)
    op2.cs_cut = (op2.cs_cut or CSCutParams()).model_copy(update={"max_rotations": rotations})
    op2.result = None
    calc.run_cutting(p2, op2)
    return p2, op2, rotations


def _refit_check(mk: str, p: Project, op: Operation, lim: Optional[int]) -> Optional[dict]:
    """Stanok formati uchun qayta kroy kerakmi (hech narsani o'zgartirmaydi): kerak bo'lsa — {limit, current, manual,
    remnants_saved}, aks holda None. UI shu javob bilan tasdiq so'raydi (almashtirish / nusxadan eksport / bekor)."""
    from .services import ppfmt
    if op.type != OpType.CS or not op.cs_cut:
        return None
    cur = op.cs_cut.max_rotations
    need: Optional[int] = None
    if lim and cur > lim:
        need = lim
    else:
        try:
            ppfmt.run_saw(mk, p, op)
        except ppfmt.FormatError:
            if lim and cur > 2:
                need = cur - 1
    if need is None:
        return None
    r = op.result
    return dict(limit=need, current=cur, manual=bool(r and r.manual), remnants_saved=bool(r and r.remnants_saved))


@api.get("/projects/{pid}/operations/{oid}/postprocess", tags=["postprotsessor"])
def postprocess(pid: str, oid: str, key: Optional[str] = None, profile_id: Optional[int] = None,
                long_side: str = "any", refit: Optional[Literal["check", "replace", "copy"]] = None):
    """Kroy natijasini stanok/tizim formatida yuklab olish: key=csv|commands|dxf|json yoki profile_id (shablon).
    XNC operatsiyasi uchun — ishlov markazi konteksti (key=json yoki shablon; long_side=horizontal|vertical|any).
    `refit` — stanok formati burilishlarni cheklasa (o'rnatilgan arra formatlari): check — faylsiz, qayta kroy kerakmi
    ({refit: null | {limit, current, manual, remnants_saved}}); replace (standart, eski xulq) — loyihadagi natija qayta kroy
    bilan almashtiriladi (X-PP-Refit); copy — vaqtinchalik nusxadan eksport, loyiha o'zgarmaydi (X-PP-Refit-Mode: copy)."""
    from .models import PostprocessorProfile
    from .services import postprocessors as pp
    p = _load(pid); op = _op(p, oid)
    if key and key.startswith("machine:") and key.split(":", 1)[1] in pp.MACHINE_BY_KEY:
        from .services import pp_access               # mijoz uchun ochilmagan postprotsessor — 403 (UI da xira, API ham rad etadi)
        pp_access.require_open(key.split(":", 1)[1])
    if op.type == OpType.XNC:                         # ishlov markazi: XNC dasturi (W1)
        from .api_xnc import postprocess_xnc
        return postprocess_xnc(p, op, key, profile_id, long_side)
    if op.type == OpType.CN and key and key.startswith("machine:"):    # (CN) nesting → ishlov markazi formati (2026-10-24)
        from .services import ppfmt
        mk = key.split(":", 1)[1]
        if not (ppfmt.available(mk) and ppfmt.REGISTRY[mk].group == "nest"):
            raise HTTPException(400, _("pp_machine_unknown", k=mk))
        if not op.result or not op.result.maps:
            raise HTTPException(400, _("cut_first"))
        try:
            name, data, mime = ppfmt.run_nest(mk, p, op)
        except ppfmt.FormatError as e:
            raise HTTPException(400, str(e)) from e
        from urllib.parse import quote as _q
        return Response(data, media_type=mime, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{_q(name)}"})
    if not (key and key.startswith("machine:")):     # MebeliX formati / stanoksiz shablon — admin yopgan bo'lsa 403
        from .services import pp_access
        if profile_id:
            pp_access.require_extra(f"pp:{profile_id}")
        elif key in pp.BUILTIN:
            pp_access.require_extra(f"mx:{key}")
    _need_cut(op)                                    # CS yoki CL (CL: o'rnatilgan csv/commands/json/dxf; stanok shabloni — Q19)
    if not op.result or not op.result.maps:
        raise HTTPException(400, _("cut_first"))
    machine = None
    mk = None
    label_warns: list = []                           # etiketka maydon ifodalari xatolari (W7): sarlavha X-Label-Warnings
    if key and key.startswith("machine:"):           # stanok nomi bo'yicha: unga biriktirilgan shablon profili
        from .api_extra import _machine_cfg
        mk = key.split(":", 1)[1]
        if mk not in pp.MACHINE_BY_KEY:
            raise HTTPException(400, _("pp_machine_unknown", k=mk))
        machine = pp.MACHINE_BY_KEY[mk][0]
        cfg = _machine_cfg()
        from .services import ppfmt
        profile_id = cfg["profile"].get(mk)
        if not profile_id and ppfmt.available(mk) and ppfmt.REGISTRY[mk].group == "saw":
            # o'rnatilgan format (shablon biriktirilmagan): namunalardan o'rganilgan generator
            from urllib.parse import quote as _q
            refit_n = 0                               # stanok chegarasiga moslab qayta kroy qilingan burilishlar soni
            from .services.pp_machine_ctx import get_params as _gp
            lim = ppfmt.rot_limit(mk, _gp(mk))
            if refit == "check":                      # faqat tekshiruv: fayl ham, o'zgarish ham yo'q (QA #3)
                return dict(refit=_refit_check(mk, p, op, lim), machine=machine)
            mode = refit or "replace"
            do_refit = _refit_rotations if mode == "replace" else (lambda _pid, _oid, n: _refit_copy(p, op, n))
            if op.type == OpType.CS and lim and op.cs_cut and op.cs_cut.max_rotations > lim:
                p, op, refit_n = do_refit(pid, oid, lim)
            while True:
                try:
                    name, data, mime = ppfmt.run_saw(mk, p, op)
                    break
                except ppfmt.FormatError as e:        # format cheklovi (kesim darajasi): burilishni kamaytirib qayta kroy
                    cur = op.cs_cut.max_rotations if op.type == OpType.CS and op.cs_cut else 0
                    if not lim or cur <= 2:
                        raise HTTPException(400, str(e)) from e
                    p, op, refit_n = do_refit(pid, oid, cur - 1)
            if cfg["prefix"]:
                name = f"{pp._safe_name(machine, 'machine', 30)}_{name}"
            hdr = {"Content-Disposition": f"attachment; filename*=UTF-8''{_q(name)}"}
            if refit_n:
                hdr["X-PP-Refit"] = str(refit_n)      # UI: «kroy stanokka moslab qayta bajarildi» xabari + loyihani yangilash
                hdr["X-PP-Refit-Mode"] = mode         # copy — loyihadagi natija o'zgarmadi
            return Response(data, media_type=mime, headers=hdr)
        if not cfg["enabled"].get(mk):
            raise HTTPException(400, _("pp_machine_off", n=machine))
        if not profile_id:
            raise HTTPException(400, _("pp_machine_unbound", n=machine))
    if profile_id:
        pr = settings.get_profile("postprocessor", profile_id)
        if not pr:
            raise HTTPException(404, _("pp_not_found"))
        if pp.template_kind(pr["data"].get("template", "")) == "xnc":     # ishlov markazi shabloni — kroy uchun emas
            raise HTTPException(400, _("pp_profile_xnc", n=pr["name"] or pr["data"].get("name", "")))
        from .services.tpl_sandbox import TemplateLimit
        try:
            name, data, mime = pp.render_template(PostprocessorProfile.model_validate(pr["data"]), p, op, mk, label_warns)
        except TemplateLimit as e:
            raise HTTPException(400, _("template_limit", e=e)) from e
        except Exception as e:  # noqa: BLE001 — shablon xatosi foydalanuvchiga
            raise HTTPException(400, _("template_error", e=e)) from e
        if machine:                                   # «Добавлять префикс имени станка к названию файла»
            from .api_extra import _machine_cfg as _mc
            if _mc()["prefix"]:
                name = f"{pp._safe_name(machine, 'machine', 30)}_{name}"
    elif key in pp.BUILTIN:
        name, data, mime = pp.run_builtin(key, p, op)
    else:
        raise HTTPException(400, _("pp_not_selected"))
    from urllib.parse import quote
    hdr = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"}
    if label_warns:
        hdr["X-Label-Warnings"] = str(len(label_warns))
    return Response(data, media_type=mime, headers=hdr)


# ───────────────────────── Hisobot va etiketkalar ─────────────────────────
def _html(body: str) -> HTMLResponse:
    """Hisobot/etiketka sahifasi: skriptlar taqiqlangan (CSP), boshqa saytga ulanmaydi."""
    return HTMLResponse(body, headers={"Content-Security-Policy": render.REPORT_CSP,
                                       "X-Content-Type-Options": "nosniff"})


@api.get("/projects/{pid}/report", response_class=HTMLResponse, tags=["hisobot"])
def report(pid: str, lang: Literal["ru", "uz"] = "ru", profile_id: Optional[int] = None):
    ps = PrintSettings.model_validate(settings.resolve("print", profile_id))
    return _html(render.project_report_html(_load(pid), ps, lang))


@api.post("/projects/{pid}/report", response_class=HTMLResponse, tags=["hisobot"])
def report_preview(pid: str, ps: PrintSettings, lang: Literal["ru", "uz"] = "ru"):
    """Saqlanmagan chop sozlamalari bilan ko'rish (Печать отчета → oldindan ko'rish)."""
    return _html(render.project_report_html(_load(pid), ps, lang))


@compute.task("report_pdf")
def _task_report_pdf(a: dict) -> dict:
    """Hisobot HTML + PDF (Chrome / WeasyPrint) — ishchi jarayonda; PDF baytlari base64 da."""
    import base64

    from .services.pdf_render import html_to_pdf
    p = _load(a["pid"])
    ps = PrintSettings.model_validate(a["ps"]) if a.get("ps") is not None else \
        PrintSettings.model_validate(settings.resolve("print", a.get("profile_id")))
    pdf = html_to_pdf(render.project_report_html(p, ps, a.get("lang") or "ru"))
    if pdf is None:
        raise HTTPException(501, _("no_weasyprint"))
    return dict(number=p.number, pdf=base64.b64encode(pdf).decode("ascii"))


def _pdf_response(out: dict, inline: bool) -> Response:
    import base64
    disp = "inline" if inline else "attachment"
    return Response(base64.b64decode(out["pdf"]), media_type="application/pdf",
                    headers={"Content-Disposition": f'{disp}; filename="{out["number"]}.pdf"'})


@api.get("/projects/{pid}/report.pdf", tags=["hisobot"])
def report_pdf(pid: str, lang: Literal["ru", "uz"] = "ru", profile_id: Optional[int] = None, inline: bool = False):
    """Hisobot A4 PDF (sahifalar, kolontitul) — WeasyPrint yoki shu kompyuterdagi Chrome / Edge (`services/pdf_render.py`)."""
    return _pdf_response(compute.call("report_pdf", dict(pid=pid, lang=lang, profile_id=profile_id)), inline)


@api.post("/projects/{pid}/report.pdf", tags=["hisobot"])
def report_pdf_preview(pid: str, ps: PrintSettings, lang: Literal["ru", "uz"] = "ru"):
    """«Печать отчета» oynasi: saqlanmagan sozlamalar bilan A4 PDF (brauzerning PDF ko'rgichida — to'g'ridan-to'g'ri chop)."""
    return _pdf_response(compute.call("report_pdf", dict(pid=pid, lang=lang, ps=ps.model_dump(mode="json"))), True)


@api.get("/projects/{pid}/labels", response_class=HTMLResponse, tags=["hisobot"])
def labels_page(pid: str, op_id: Optional[str] = None, profile_id: Optional[int] = None,
                lang: Literal["ru", "uz"] = "ru"):
    ls = LabelSettings.model_validate(settings.resolve("labels", profile_id))
    return _html(labels.labels_html(_load(pid), ls, op_id, lang))


@api.post("/projects/{pid}/labels", response_class=HTMLResponse, tags=["hisobot"])
def labels_preview(pid: str, ls: LabelSettings, op_id: Optional[str] = None, lang: Literal["ru", "uz"] = "ru"):
    """Saqlanmagan etiketka sozlamalari bilan ko'rish."""
    return _html(labels.labels_html(_load(pid), ls, op_id, lang))


@api.get("/projects/{pid}/warehouse", tags=["hisobot"])
def warehouse_req(pid: str):
    return calc.warehouse_request(_load(pid))


# ───────────────────────── Tovarlar katalogi va fayl ko'rish (W3) ─────────────────────────
# `/catalog` (ro'yxat, daraxt, rasm, sync, import, delete) — api_catalog.py; `/import/preview`, `/projects/{id}/import/excel` —
# api_import.py (quyida `include_router`). `/catalog/sync` (MES) yo'li va javobi avvalgidek (+ `image_errors`).

# ───────────────────────── Qo'shimcha routerlar ─────────────────────────
from .api_extra import router as extra_router  # noqa: E402

api.include_router(extra_router)
from .api_oee import router as oee_router  # noqa: E402  (W17: OEE va ishlab chiqarish analitikasi)
api.include_router(oee_router)
from .api_order import router as order_router  # noqa: E402  (W14: «Заказать» oqimi, «Очистить проект»)
api.include_router(order_router)
from .api_queue import router as queue_router  # noqa: E402  (2026-10-15: buyurtmalar navbati, material bazasi tekshiruvi)
api.include_router(queue_router)
from .api_pp_machines import router as pp_machines_router  # noqa: E402  (W7: stanok sozlamalari sxemasi, etiketka maydonlari)
api.include_router(pp_machines_router)
from .api_xnc import router as xnc_router  # noqa: E402  (W1: XNC shablonlar, Par, ishlov markazi postprotsessori)
api.include_router(xnc_router)
from .api_import import router as import_router  # noqa: E402  (W3: Excel import v2, fayl ko'rish)
from .api_catalog import router as catalog_router  # noqa: E402  (W3: «Товары» daraxti, rasm, import, MES sync)
api.include_router(import_router)
api.include_router(catalog_router)
from .api_expr import router as expr_router  # noqa: E402  (W6: ifoda API)
from .api_gr import router as gr_router  # noqa: E402  (W6: GR paz hisobi)

api.include_router(expr_router)
api.include_router(gr_router)
from .api_o import router as o_router  # noqa: E402  (W5: O Комплектация)
api.include_router(o_router)
from .api_cs_w2 import router as cs_w2_router  # noqa: E402  (W2: CS bo'shliqlari — miqdorlar, «Исп. кол-во», rezerv)
api.include_router(cs_w2_router)
from .api_cl import router as cl_router  # noqa: E402  (W11: CL pogonaj kroy — miqdorlar, CLE tahrir izi)
api.include_router(cl_router)
from .api_cn import router as cn_router  # noqa: E402  (W16: CN nesting — miqdorlar, shakllar, tahrir izi, fon vazifasi)
api.include_router(cn_router)
from .api_labels import router as labels_router  # noqa: E402  (W4: LB etiketkalar — shablon, ko'rish, chop, A4 da karta miniatyurasi)
api.include_router(labels_router)
from .api_label_io import router as label_io_router  # noqa: E402  (W9: LB shablon fayllarini import/eksport)
api.include_router(label_io_router)
from .api_label_w15 import router as label_w15_router  # noqa: E402  (W15: etiketka vizual redaktori — jonli ko'rinish; ZPL chiqarish)
api.include_router(label_w15_router)
from .api_sp import router as sp_router  # noqa: E402  (W12: SP sirt ishlovi hisobi)
from .api_pprog import router as pprog_router  # noqa: E402  (W12: mahsulot «Программа», «Пересчитать параметричность»)
api.include_router(sp_router)
api.include_router(pprog_router)
from .api_export import router as export_router  # noqa: E402  (W10: `.project` eksporti)
api.include_router(export_router)
from .api_cse_w13 import router as cse_w13_router  # noqa: E402  (W13: CSE tahrir paketi, parallel tahrir izi, tekshirish)
api.include_router(cse_w13_router)
from .api_import_w18 import router as import_w18_router  # noqa: E402  (W18: «Импорт из других программ» — katalog, parametrlar, profillar)
api.include_router(import_w18_router)
from .api_ops_x1018 import router as ops_x1018_router  # noqa: E402  (2026-10-18: «Объединить» tanlov bilan, CS → CN)
api.include_router(ops_x1018_router)
from .api_pp_access import router as pp_access_router  # noqa: E402  (2026-10-18: postprotsessorlarga kirish — admin ochadi/yopadi)
api.include_router(pp_access_router)
from .api_mes_package import router as mes_package_router  # noqa: E402  (2026-10-18: MES paketi v1 — faqat quriladi, yuborilmaydi)
api.include_router(mes_package_router)
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
            raise HTTPException(404, _("api_not_found"))
        try:
            f = (WEB_DIR / full_path).resolve()
            ok = bool(full_path) and "\x00" not in full_path and f.is_file() and _web_root in f.parents
        except (OSError, ValueError):          # /%00, juda uzun yo'l va h.k.
            ok = False
        if ok:
            return FileResponse(f)
        return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})
