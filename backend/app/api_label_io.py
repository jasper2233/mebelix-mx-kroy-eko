"""LB shablon fayllari: import va eksport (W9 · LB-D).

  POST /api/labels/import-file        — multipart: `file` (.lbl / .xml — ildizi `<program>`; .project — undagi LB operatsiyalar),
                                         `name` (ixtiyoriy), `save` (true — kutubxonaga saqlash), `select` (saqlanadigan indekslar, vergul bilan)
  POST /api/labels/export-xml         — `{template, layout?}` → `{xml, warnings, filename}` (muharrirdagi joriy shablon)
  GET  /api/label-templates/{id}/export-xml — kutubxona/o'rnatilgan shablonni `<program>` XML fayli sifatida yuklab olish

Mijoz fayli faqat xotirada o'qiladi (≤ 5 MB, XML xavfsiz parser bilan), serverda saqlanmaydi; natija — kutubxona profili
(`label_template` scope) va ogohlantirishlar ro'yxati. Tayyor shablon bilan ishlash qoidalari — services/label_gl_*.py.
"""
from __future__ import annotations

import re
from pathlib import PurePath
from typing import Any, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from .i18n import LANG, _
from .services import label_gl_common as C
from .services import label_gl_export, label_gl_import, label_tpl, settings

router = APIRouter()
SCOPE = "label_template"
Lang = Literal["ru", "uz"]
EXTS = (".lbl", ".xml", ".project")


class LayoutIn(BaseModel):
    """Sahifa joylashuvi (`LBParams` maydonlari) — XML ildiz atributlariga yoziladi."""
    mode: Literal["sheet", "roll"] = "sheet"
    columns: int = Field(3, ge=1, le=20)
    rows: int = Field(0, ge=0, le=50)
    gap_mm: float = Field(2, ge=0, le=50)
    margin_mm: Optional[float] = Field(6, ge=0, le=50)
    width_mm: Optional[float] = Field(None, ge=label_tpl.SIZE_MIN, le=label_tpl.SIZE_MAX)
    height_mm: Optional[float] = Field(None, ge=label_tpl.SIZE_MIN, le=label_tpl.SIZE_MAX)


class ExportXmlIn(BaseModel):
    template: Any
    layout: Optional[LayoutIn] = None


def _safe_name(name: str, default: str = "label") -> str:
    return re.sub(r"[^\w.-]+", "_", name or "", flags=re.UNICODE).strip("_")[:80] or default


def _lang() -> str:
    return "uz" if LANG.get() == "uz" else "ru"


def _item(i: int, source: str, name: str, ops: int, res: label_gl_import.GLResult) -> dict:
    tpl = res.template
    tpl["name"] = name[:100]
    chk = label_tpl.check_template(tpl, None, _lang())
    return {"index": i, "source": source, "name": name[:100], "ops": ops, "template": tpl, "size": tpl["size"],
            "layout": tpl.get("layout"), "warnings": res.warnings, "info": res.info, "errors": chk["errors"][:30], "saved": None}


@router.post("/labels/import-file", tags=["etiketkalar"])
def import_file(file: UploadFile = File(...), name: str = Form(""), save: bool = Form(False), select: str = Form("")):
    """Tayyor shablon faylini o'qiydi → shablon(lar) + ogohlantirishlar; `save=true` — kutubxonaga ham saqlaydi."""
    fname = file.filename or ""
    ext = PurePath(fname).suffix.lower()
    if ext not in EXTS:
        raise HTTPException(400, _("lbx.e_ext"))
    data = file.file.read(C.MAX_FILE_BYTES + 1)
    if len(data) > C.MAX_FILE_BYTES:
        raise HTTPException(413, _("lbx.e_big", n=C.MAX_FILE_BYTES // (1024 * 1024)))
    stem = PurePath(fname).stem[:80] or "label"
    base = (name or "").strip()[:100]
    items: list[dict] = []
    skipped: list[dict] = []
    extra = 0
    try:
        if ext == ".project":
            progs, extra = label_gl_import.programs_from_project(data)
            used: set[str] = set()
            for i, pg in enumerate(progs):
                nm = pg["name"]
                while nm in used:
                    nm = f"{pg['name'][:90]} ({len(used) + 1})"
                used.add(nm)
                try:
                    items.append(_item(len(items), pg["name"], nm, pg["ops"], label_gl_import.convert_program(pg["program"], nm)))
                except C.GLError as e:
                    skipped.append({"source": pg["name"], "error": str(e)})
            if not items:
                raise C.GLError(skipped[0]["error"] if skipped else _("lbx.e_no_lb"))
        else:
            items.append(_item(0, stem, base or stem, 1, label_gl_import.convert_program(data, base or stem)))
    except C.GLError as e:
        raise HTTPException(400, str(e)) from e
    if save:
        want = {int(x) for x in re.findall(r"\d+", select)} if select.strip() else None
        chosen = [it for it in items if want is None or it["index"] in want]
        for it in chosen:
            nm = (f"{base} {it['index'] + 1}" if base and len(chosen) > 1 else (base or it["name"]))[:100]
            tpl = dict(it["template"])
            tpl["name"] = nm
            pr = settings.create(SCOPE, nm, tpl)
            it["saved"] = {"id": f"profile:{pr['id']}", "profile_id": pr["id"], "name": pr["name"]}
    return {"filename": fname, "kind": "project" if ext == ".project" else "program", "items": items, "skipped": skipped,
            "more": extra}


@router.post("/labels/export-xml", tags=["etiketkalar"])
def export_xml(inp: ExportXmlIn):
    """Joriy shablon (muharrirdagi nusxa ham bo'lishi mumkin) → `<program>` XML matni + ogohlantirishlar."""
    try:
        res = label_gl_export.export_program(inp.template, inp.layout.model_dump() if inp.layout else None)
    except C.GLError as e:
        raise HTTPException(422, str(e)) from e
    nm = inp.template.get("name") if isinstance(inp.template, dict) else ""
    return {"xml": res.xml, "warnings": res.warnings, "filename": f"{_safe_name(str(nm or ''))}.xml"}


@router.get("/label-templates/{tid}/export-xml", tags=["etiketkalar"])
def template_export_xml(tid: str, lang: Lang = "ru"):
    from .api_labels import _find_template
    t, _builtin, name = _find_template(tid, lang)
    try:
        res = label_gl_export.export_program(t)
    except C.GLError as e:
        raise HTTPException(422, str(e)) from e
    return Response(res.xml, media_type="application/xml; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(_safe_name(name))}.xml",
                             "X-Export-Warnings": str(len(res.warnings))})
