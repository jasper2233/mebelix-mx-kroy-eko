"""`.project` eksporti (W10): loyiha → ochiq tavsiflangan `.project` (XML) fayli.

  GET  /api/projects/{pid}/export/project          — faylni yuklab olish (Content-Disposition: attachment, UTF-8 XML)
  GET  /api/projects/{pid}/export/project/report   — fayl nomi, o'lchami, hisoblagichlar va ogohlantirishlar (nima o'tkazib yuborildi)
  POST /api/projects/export/project-zip            — bir nechta loyiha: `{ids: [...]}` → ZIP (har loyiha — alohida `.project`)

Kroy natijasi (kartalar) eksport qilinmaydi — qabul qiluvchi dastur kroyni qayta hisoblaydi. Batafsil: `docs/mebelix/T_W10_PROJECT_EKSPORT.md`.
"""
from __future__ import annotations

import io
import re
import zipfile
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import store
from .i18n import _
from .services import project_export as pe

router = APIRouter(tags=["eksport"])

MAX_ZIP_PROJECTS = 200


def _run(pid: str) -> pe.ExportResult:
    p = store.load(pid)
    try:
        return pe.export_project(p)
    except pe.ExportError as e:                      # o'z sxemamizdan o'tmadi: dastur xatosi — buzuq fayl berilmaydi
        raise HTTPException(500, _("exp_invalid", e="; ".join(e.errors[:3]))) from e


def _disposition(filename: str) -> str:
    ascii_name = re.sub(r'[^A-Za-z0-9._ \-]+', "_", filename).strip() or "project.project"
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename, safe="")}'


@router.get("/projects/{pid}/export/project")
def export_project_file(pid: str):
    res = _run(pid)
    return Response(res.xml, media_type="application/xml; charset=utf-8",
                    headers={"Content-Disposition": _disposition(res.filename),
                             "X-Export-Warnings": str(sum(1 for w in res.warnings if w["level"] == "warn"))})


@router.get("/projects/{pid}/export/project/report")
def export_project_report(pid: str):
    res = _run(pid)
    return dict(filename=res.filename, bytes=len(res.xml), counts=res.counts, warnings=res.warnings,
                format_version=pe.FORMAT_VERSION)


class ZipIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=MAX_ZIP_PROJECTS)


@router.post("/projects/export/project-zip")
def export_project_zip(body: ZipIn):
    buf = io.BytesIO()
    used: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for pid in dict.fromkeys(body.ids):
            res = _run(pid)
            name, n = res.filename, 1
            while name.lower() in used:                      # bir xil nomli loyihalar — «(2)», «(3)»
                n += 1
                name = re.sub(r"\.project$", f"_({n}).project", res.filename)
            used.add(name.lower())
            z.writestr(name, res.xml)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": _disposition("projects.zip")})
