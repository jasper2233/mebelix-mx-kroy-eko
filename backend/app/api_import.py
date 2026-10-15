"""Excel import v2 API (loyiha darajasida; CS siz ham ishlaydi) va fayl ko'rish.

  POST /api/projects/{pid}/import/excel   — `file` + `config` (JSON, `services/import_v2.ExcelImportConfig`);
                                             `dry_run=true` — hech narsa saqlanmaydi, faqat natija hisoboti
  POST /api/import/preview                — varaqlar va birinchi qatorlar (.xlsx / .xls / .csv)

Mijoz fayli faqat xotirada o'qiladi (hajm chegarasi `importers.MAX_FILE_BYTES`), serverda saqlanmaydi.
Mavjud `POST …/operations/{oid}/parts/import` (main.py) o'zgarmagan.
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from . import store
from .i18n import _, format_errors
from .models import Operation, OpType
from .services import catalog as catalog_svc
from .services import import_v2, importers

router = APIRouter()


def read_upload(file: UploadFile) -> bytes:
    """Yuklangan faylni xotiraga (chegara bilan) o'qish; katta bo'lsa — 413."""
    data = file.file.read(importers.MAX_FILE_BYTES + 1)
    if len(data) > importers.MAX_FILE_BYTES:
        raise HTTPException(413, _("imp_file_big", n=importers.MAX_FILE_BYTES // (1024 * 1024)))
    return data


def _make_cs(name: str) -> Operation:
    """Material nomi bo'yicha yangi CS: katalogda (nom yoki kod bilan aniq mos) bo'lsa — qalinlik/narx/list o'lchami
    undan; bo'lmasa — «Настройки» dagi standartlar. (`main._new_operation` — «+ CS» tugmasi bilan bir xil.)"""
    from .main import OpIn, _new_operation          # kechiktirilgan import (main bu modulni oxirida yuklaydi)
    item = catalog_svc.find_item("sheet", name)
    return _new_operation(OpIn(type=OpType.CS, name=name, material_id=item.id if item else None))


def _make_op(typ: str, name: str, code: str, item_id: Optional[str]) -> Operation:
    """W18 («Материалы» tabi, погонаж): tur (CS | CL | EL | SP) bo'yicha yangi operatsiya — katalog bo'lsa undan parametrlar
    (`main._new_operation`, «+ Operatsiya» tugmasi bilan bir xil)."""
    from .main import OpIn, _new_operation          # kechiktirilgan import
    return _new_operation(OpIn(type=OpType(typ), name=name, code=code, material_id=item_id))


def _parse_config(raw: str) -> import_v2.ExcelImportConfig:
    try:
        return import_v2.ExcelImportConfig.model_validate(json.loads(raw))
    except ValidationError as e:
        raise HTTPException(400, _("imp_bad_config", e=format_errors(e.errors()))) from e
    except ValueError as e:
        raise HTTPException(400, _("imp_bad_config", e=str(e)[:100])) from e


@router.post("/projects/{pid}/import/excel", tags=["import"])
def import_excel(pid: str, file: UploadFile = File(...), config: str = Form(...), dry_run: bool = Form(False)):
    """Excel/CSV → loyiha: «Детали» (guruhlash, o'lcham rejimi …) va «Изделия» tablari yoki «faqat mahsulot soni»
    (`config.mode = "products_qty"`). Javob: loyiha (avvalgidek) + `imported`, `skipped` (`[{row, reason, tab}]`),
    `warnings`, `created_edges`, `created_ops` (avto yaratilgan CS), `created_products`, `updated_products`,
    `zero_skipped`. `dry_run=true`: loyiha o'zgarmaydi, javob — faqat hisobot (`dry_run: true`)."""
    from .main import _invalidate, _products_qty_changed   # kechiktirilgan import
    data = read_upload(file)
    cfg = _parse_config(config)
    name = file.filename or ""

    def run(p):
        try:
            return import_v2.run_import(p, data, name, cfg, make_cs=_make_cs, make_op=_make_op)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001 — sozlama xatosi / buzuq fayl — foydalanuvchi xatosi (400)
            raise HTTPException(400, str(e) if isinstance(e, import_v2.ImportConfigError) else _("import_error", e=e)) from e

    if dry_run:
        rep = run(store.load(pid))
        return dict(rep.summary(), dry_run=True)
    with store.editing(pid) as p:
        rep = run(p)
        for op in rep.touched_ops:                       # detal qo'shilgan operatsiyalar kroyi eskiradi
            _invalidate(op)
        if rep.changed_products:
            _products_qty_changed(p, rep.changed_products)
    out = jsonable_encoder(p)
    out.update(rep.summary())
    return out


@router.post("/import/preview", tags=["katalog"])
def import_preview(file: UploadFile = File(...), sheet: int = Form(0), rows: int = Form(30), sheet_name: str = Form("")):
    """Excel/CSV faylning birinchi qatorlari (ustunlar xaritasini tanlash uchun). `sheet_name` — varaq nomi (berilsa
    `sheet` tartib raqamidan ustun). Javob: `sheets`, `columns`, `rows`, `sheet` (ko'rsatilgan varaq nomi), `format`."""
    data = read_upload(file)
    try:
        return importers.preview(data, file.filename or "", sheet_name.strip() or sheet, max(1, min(rows, 200)))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, _("file_unreadable", e=e)) from e
