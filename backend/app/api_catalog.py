"""«Товары» (material katalogi) API: ro'yxat, daraxt, rasm, MES sinxroni (`/catalog/sync`), Excel/CSV importi.

  GET    /api/catalog                 — tekis ro'yxat: kind, parent_id (""=ildiz), q, limit, recursive, unfiled, folders;
                                        `tree=true` — daraxt (papkalar + materiallar `children` ichida)
  GET    /api/catalog/tree            — faqat papkalar daraxti `{nodes, total, unfiled}` (kind, q, items, root)
  GET    /api/catalog/{id}            — bitta qator + `image` (data: URI yoki havola)
  PUT    /api/catalog/{id}/image      — rasm yuklash (`file` yoki `url`); DELETE — o'chirish
  POST   /api/catalog/sync            — MES dan upsert (avvalgidek; `image` ixtiyoriy)
  POST   /api/catalog/import          — Excel/CSV (goods.xls ustunlari: id, parent_id, isfolder, code, name, unit, price,
                                        stock, image, params, thickness, length, width, kind) + ildiz kategoriyalar
  DELETE /api/catalog/{id}            — qatorni o'chirish (`recursive=true` — papka bilan ichidagilar)
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from .api_import import read_upload
from .db import CatalogImageRow, CatalogItemRow, SessionLocal
from .i18n import _
from .services import catalog as cat
from .services import import_settings

router = APIRouter()


@router.get("/catalog", tags=["katalog"])
def catalog(kind: Optional[str] = None, parent_id: Optional[str] = None, q: str = "", limit: int = 500,
            recursive: bool = False, unfiled: bool = False, folders: bool = True, tree: bool = False):
    if tree:
        return cat.folder_tree(kind, q, True, limit)["nodes"]
    return cat.query_items(kind, parent_id, q, limit, recursive=recursive, unfiled=unfiled, folders=folders)


@router.get("/catalog/tree", tags=["katalog"])
def catalog_tree(kind: Optional[str] = None, q: str = "", items: bool = False, root: Optional[str] = None,
                 limit: int = 2000):
    return cat.folder_tree(kind, q, items, limit, root)


@router.get("/catalog/{item_id}", tags=["katalog"])
def catalog_get(item_id: str):
    with SessionLocal() as s:
        row = s.get(CatalogItemRow, item_id)
        if row is None:
            raise HTTPException(404, _("catalog_item_not_found"))
        out = cat.item_dict(row)
        img = s.get(CatalogImageRow, item_id) if row.has_image else None
    out["image"] = img.data if img is not None else None
    return out


class CatalogIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    parent_id: Optional[str] = Field(None, max_length=64)
    kind: str = Field(pattern=r"^(sheet|linear|edge|surface|folder)$")      # services/catalog.KINDS + papka
    code: str = Field("", max_length=100)
    name: str = Field(max_length=300)
    unit: str = Field("", max_length=20)
    price: float = Field(0, ge=0)
    stock: float = Field(0, ge=0)
    thickness: Optional[float] = Field(None, ge=0)
    length: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, ge=0)
    params: dict = {}
    image: Optional[str] = Field(None, max_length=cat.MAX_IMAGE_BYTES * 2)    # ixtiyoriy: berilmasa mavjud rasm saqlanadi


@router.post("/catalog/sync", tags=["katalog"])
def catalog_sync(items: list[CatalogIn]):
    """MES dan tovarlarni yuklash (upsert). Mavjud tovarda faqat yuborilgan maydonlar o'zgaradi (qisman yangilash:
    masalan faqat `price`/`stock` — `params`, `unit`, rasm belgisi saqlanadi); yangi tovar to'liq yoziladi. Rasm (`image`)
    berilmasa — mavjud rasm o'zgarmaydi; yaroqsiz rasm butun sinxronni to'xtatmaydi (`image_errors` soni).
    O'chirish — alohida `DELETE /catalog/{id}`."""
    bad = 0
    images: dict[str, str] = {}
    with SessionLocal() as s:
        for it in items:
            row = s.get(CatalogItemRow, it.id)
            if row is None:
                s.add(CatalogItemRow(**it.model_dump(exclude={"image"})))
            else:
                for k, v in it.model_dump(exclude={"image"}, exclude_unset=True).items():
                    setattr(row, k, v)
            if it.image is not None and it.image.strip():
                try:
                    images[it.id] = cat.normalize_image(it.image)
                except ValueError:
                    bad += 1
        s.commit()
    cat.store_images(images)
    return {"count": len(items), "image_errors": bad}


@router.delete("/catalog/{item_id}", tags=["katalog"])
def catalog_delete(item_id: str, recursive: bool = False):
    with SessionLocal() as s:
        row = s.get(CatalogItemRow, item_id)
        if row is None:
            raise HTTPException(404, _("catalog_item_not_found"))
        ids = [item_id]
        if recursive and row.kind == cat.FOLDER:
            fids = cat.descendant_folders(s, item_id)
            ids = list(dict.fromkeys(fids))
            for i in range(0, len(fids), 500):
                ids += [r for r in s.scalars(select(CatalogItemRow.id).where(CatalogItemRow.parent_id.in_(fids[i:i + 500])))]
            ids = list(dict.fromkeys(ids))
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            s.query(CatalogImageRow).filter(CatalogImageRow.item_id.in_(chunk)).delete(synchronize_session=False)
            s.query(CatalogItemRow).filter(CatalogItemRow.id.in_(chunk)).delete(synchronize_session=False)
        s.commit()
    return {"ok": True, "deleted": len(ids)}


@router.put("/catalog/{item_id}/image", tags=["katalog"])
def catalog_image_put(item_id: str, file: Optional[UploadFile] = File(None), url: str = Form("")):
    """Material rasmi: fayl (PNG/JPEG/GIF/WebP, ≤ 256 KB, tomonlari ≤ 8192 px) yoki `http(s)://` havola. Tur mazmundan
    aniqlanadi (SVG va boshqalar rad etiladi); rasm bazada `data:` URI sifatida saqlanadi."""
    try:
        if file is not None and file.filename:
            value = cat.image_from_bytes(file.file.read(cat.MAX_IMAGE_BYTES + 1))
        elif url.strip():
            value = cat.normalize_image(url)
        else:
            raise ValueError(_("cat_image_type"))
        cat.set_image(item_id, value)
    except KeyError as e:
        raise HTTPException(404, _("catalog_item_not_found")) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.delete("/catalog/{item_id}/image", tags=["katalog"])
def catalog_image_delete(item_id: str):
    try:
        cat.set_image(item_id, None)
    except KeyError as e:
        raise HTTPException(404, _("catalog_item_not_found")) from e
    return {"ok": True}


def _upsert(s, rows: list[dict]) -> None:
    """Qatorlarni ommaviy yozish (mavjud id — yangilanadi, yangisi — qo'shiladi); `has_image` o'zgarmaydi."""
    existing: set[str] = set()
    ids = [r["id"] for r in rows]
    for i in range(0, len(ids), 500):
        existing.update(s.scalars(select(CatalogItemRow.id).where(CatalogItemRow.id.in_(ids[i:i + 500]))))
    s.bulk_insert_mappings(CatalogItemRow, [dict(r, has_image=False) for r in rows if r["id"] not in existing])
    s.bulk_update_mappings(CatalogItemRow, [r for r in rows if r["id"] in existing])


@router.post("/catalog/import", tags=["katalog"])
def catalog_import(file: UploadFile = File(...), col_map: str = Form(...), sheet: int = Form(0), start_row: int = Form(2),
                   kind: str = Form("sheet"), end_row: int = Form(0), sheet_name: str = Form(""),
                   roots: str = Form(""), id_prefix: str = Form("")):
    """Каталог товаров → Excel/CSV dan. `col_map` — {maydon: ustun harfi}: id, parent_id, isfolder, code, name, unit,
    price, stock, image, params, size, thickness, length, width, kind. `roots` — {"sheet": "0", "edge": "5", …}: tur uchun
    ildiz kategoriya ID si (qator turi shu ildiz ostida bo'lishidan); `kind` — ildizsiz qatorlar uchun standart tur;
    `id_prefix` — barcha ID larga old qo'shimcha. Javob: `count`, `folders`, `items`, `images`, `warnings`, `skipped`."""
    data = read_upload(file)
    try:
        rt = json.loads(roots) if roots.strip() else import_settings.saved_roots()      # berilmasa — serverda saqlangan (W18)
        if not isinstance(rt, dict):
            raise ValueError(_("set_json_object"))
        res = cat.import_catalog_ex(data, file.filename or "", json.loads(col_map), sheet_name.strip() or sheet,
                                    max(1, start_row), kind, end_row=max(0, end_row), roots=rt, id_prefix=id_prefix)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001 — buzuq/noto'g'ri fayl — foydalanuvchi xatosi
        raise HTTPException(400, _("import_error", e=e)) from e
    with SessionLocal() as s:
        _upsert(s, res.rows)
        s.commit()
    cat.store_images(res.images)
    return dict(count=len(res.rows), folders=res.folders, items=res.items, images=len(res.images),
                warnings=res.warnings, skipped=res.skipped)
