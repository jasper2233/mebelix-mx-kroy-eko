"""MES paketi v1 API (shartnoma — docs/mebelix/MES_PAKET_V1.md; quruvchi — services/mes_package.py).

  GET /api/projects/{pid}/mes-package?version=1[&pp=enabled|all|none|<kalit,...>][&files=inline|meta]
      [&mes_order_id=<int>][&mes_order_number=B-YYYY-NNN]
      Paketni quradi va qaytaradi (hech qayerga yubormaydi, loyiha o'zgarmaydi). Yopiq postprotsessor aniq so'ralsa yoki paketning o'zi
      (`mx:mes_package`) admin tomonidan yopilgan bo'lsa — 403.
  GET /api/mes-package/schema?version=1 — paketning JSON sxemasi (MES dasturchilari uchun).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from . import store
from .i18n import _
from .services import mes_package

router = APIRouter(tags=["mes"])


def _version(v: int) -> None:
    if v != mes_package.VERSION:
        raise HTTPException(400, _("mes_pkg_version"))


@router.get("/projects/{pid}/mes-package")
def mes_package_get(pid: str, version: int = 1, pp: str = Query("enabled", max_length=2000),
                    files: str = "inline", mes_order_id: Optional[int] = Query(None, ge=1),
                    mes_order_number: Optional[str] = Query(None, max_length=60)):
    _version(version)
    from .services import pp_access
    pp_access.require_extra("mx:mes_package")         # admin yopgan bo'lsa 403 (sxema ochiq qoladi)
    p = store.load(pid)
    pkg = mes_package.build(p, mes_order_id=mes_order_id, mes_order_number=mes_order_number, pp=pp, files=files)
    return pkg.model_dump(mode="json")


@router.get("/mes-package/schema")
def mes_package_schema(version: int = 1):
    _version(version)
    return mes_package.json_schema()
