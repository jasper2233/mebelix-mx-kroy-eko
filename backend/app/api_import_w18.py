"""«Импорт из других программ» API si (W18, WP-C): formatlar katalogi, parametrlar sxemasi, profillar, import.

  GET  /api/import/catalog                          formatlar ro'yxati: nom, kengaytmalar, ikonka, holat (`ready` | `no_module`)
  GET  /api/import/formats/{key}/schema             parametrlar jadvali (ParamGrid sxemasi: guruhlar, tur, standart, «Справка»);
                                                     `?profile_id=` — shu profil qiymatlari bilan
  POST /api/import/run                              multipart: `file`, `format`, `profile_id?`, `params?` (JSON), `folder_id?` → yangi loyiha
  GET  /api/import/profiles?format=                 import profillari ({id, name, format, params})
  GET  /api/import/profiles/export?as=json|xml      profillar fayli (`format=`, `ids=1,2` bilan toraytiriladi) — IMP-006
  POST /api/import/profiles/import                  multipart: `file` (JSON yoki XML), `on_conflict=replace|rename|skip`
Profil yaratish / o'zgartirish / o'chirish — umumiy `/api/settings/import_profile` (data = {format, params}).

Importerlar (plaginlar) bu yerda emas: `plugins/<nom>.py` (`@register(..., key=)`). Importeri yo'q format — `no_module` (400).
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError

from . import plugins
from .auth import current_user
from .i18n import _, format_errors, pick
from .services import import_formats as F
from .services import settings

router = APIRouter(prefix="/import", tags=["import"])

SCOPE = "import_profile"
RUN_MAX_BYTES = 64 * 1024 * 1024         # bitta import fayli (.project ichida ikkilik kroy natijasi ham bo'ladi)


def _fmt(key: str) -> F.ImportFormat:
    f = F.format_of(key)
    if f is None:
        raise HTTPException(404, _("imp_fmt_unknown", k=key[:40]))
    return f


def _row(r: dict) -> dict:
    d = r.get("data") or {}
    return dict(id=r["id"], name=r["name"], format=d.get("format", "project"), params=d.get("params") or {},
                is_default=bool(r.get("is_default")))


def _profiles(fmt: Optional[str] = None) -> list[dict]:
    rows = [_row(r) for r in settings.list_profiles(SCOPE)]
    return [r for r in rows if fmt is None or r["format"] == fmt]


# ───────────────────────── Katalog va sxema ─────────────────────────
@router.get("/catalog")
def catalog():
    return F.catalog_payload()


@router.get("/formats/{key}/schema")
def schema(key: str, profile_id: Optional[int] = None):
    _fmt(key)
    saved = None
    if profile_id is not None:
        pr = settings.get_profile(SCOPE, profile_id)
        if pr is None or (pr["data"] or {}).get("format") != key:
            raise HTTPException(404, _("profile_not_found"))
        saved = (pr["data"] or {}).get("params") or {}
    return F.schema_payload(key, saved)


# ───────────────────────── Import ─────────────────────────
@router.post("/run")
def run(file: UploadFile = File(...), format: str = Form("project"), profile_id: Optional[int] = Form(None),
        params: str = Form(""), folder_id: Optional[str] = Form(None), user: dict = Depends(current_user)):
    """Tanlangan format importeri bilan faylni yangi loyiha sifatida yuklash. Parametrlar: standart ← profil ← `params`
    (JSON obyekt; tur qat'iy tekshiriladi). Javob: `{project, warnings, format, options}`."""
    from .main import _store_imported         # kechiktirilgan import (main bu modulni oxirida yuklaydi)
    fmt = _fmt(format)
    entry = plugins.by_key(format)
    if entry is None:
        raise HTTPException(400, _("imp_no_module"))
    name = file.filename or ""
    low = name.lower()
    if fmt.exts and not any(low.endswith(e) for e in fmt.exts):
        raise HTTPException(400, _("imp_ext_mismatch", f=name[:80], n=pick(fmt.name_ru, fmt.name_uz),
                                   x=", ".join(fmt.exts)))
    saved = None
    if profile_id is not None:
        pr = settings.get_profile(SCOPE, profile_id)
        if pr is None or (pr["data"] or {}).get("format") != format:
            raise HTTPException(404, _("profile_not_found"))
        saved = (pr["data"] or {}).get("params") or {}
    overrides: Any = None
    if params.strip():
        try:
            overrides = json.loads(params)
        except ValueError as e:
            raise HTTPException(400, _("imp_params_invalid", e=_("val_json"))) from e
        if not isinstance(overrides, dict):
            raise HTTPException(400, _("imp_params_invalid", e=_("val_dict")))
    try:
        values = F.resolve_values(format, saved, overrides)
    except ValueError as e:
        raise HTTPException(400, _("imp_params_invalid", e=str(e))) from e
    data = file.file.read(RUN_MAX_BYTES + 1)
    if len(data) > RUN_MAX_BYTES:
        raise HTTPException(413, _("imp_file_big", n=RUN_MAX_BYTES // (1024 * 1024)))
    with F.use_options(values):
        try:
            p, warnings = entry[1](data, name)
        except ValidationError as e:
            raise HTTPException(400, _("bad_project_file", e=format_errors(e.errors()))) from e
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    p = _store_imported(p, folder_id, user["name"])
    return dict(project=p, warnings=warnings, format=format, options=values)


# ───────────────────────── Profillar ─────────────────────────
@router.get("/profiles")
def profiles_list(format: Optional[str] = None):
    return _profiles(format)


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40] or "profiles"


@router.get("/profiles/export")
def profiles_export(fmt: str = Query("json", alias="as"), format: Optional[str] = None, ids: str = ""):
    """Profillar fayli: `as=json` (standart) yoki `as=xml`. `format=` — faqat shu format; `ids=1,2` — faqat shular.
    Faylda hamma parametr qiymati aniq yoziladi (ikkinchi korxonada ham xuddi shu sozlama chiqsin)."""
    if fmt not in ("json", "xml"):
        raise HTTPException(400, _("val_choice") + " (as: json | xml)")
    want: Optional[set[int]] = None
    if ids.strip():
        try:
            want = {int(x) for x in ids.split(",") if x.strip()}
        except ValueError as e:
            raise HTTPException(400, _("val_int")) from e
    rows = [r for r in settings.list_profiles(SCOPE)
            if (want is None or r["id"] in want) and (format is None or (r["data"] or {}).get("format") == format)]
    stem = "import_profiles" + (f"_{_slug(format)}" if format else "")
    if fmt == "xml":
        body, mime = F.export_xml(rows), "application/xml"
    else:
        body, mime = json.dumps(F.export_json(rows), ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    return Response(body, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{stem}.{fmt}"'})


def _find(fmt: str, name: str) -> Optional[dict]:
    key = name.strip().casefold()
    for r in settings.list_profiles(SCOPE):
        if (r["data"] or {}).get("format") == fmt and (r["name"] or "").strip().casefold() == key:
            return r
    return None


def _free_name(fmt: str, name: str) -> str:
    n = 2
    while True:
        cand = f"{name[:F.MAX_PROFILE_NAME - 6]} ({n})"
        if _find(fmt, cand) is None:
            return cand
        n += 1


@router.post("/profiles/import")
def profiles_import(file: UploadFile = File(...), on_conflict: str = Form("replace")):
    """Profillar faylidan (JSON yoki XML) yuklash. Bir xil nom + format: `replace` (standart) — almashtiriladi, `rename` — yangi nom
    («nom (2)»), `skip` — tegilmaydi. Yaroqsiz profil `invalid` ga yoziladi (qolganlari yuklanadi).
    Javob: `{created, replaced, renamed, skipped, invalid: [{name, format, error}], total}`."""
    if on_conflict not in ("replace", "rename", "skip"):
        raise HTTPException(400, _("imp_conflict_mode"))
    data = file.file.read(F.MAX_PROFILE_FILE + 1)
    try:
        items = F.parse_file(data)
    except F.ProfileFileError as e:
        raise HTTPException(400, str(e)) from e
    out: dict[str, Any] = dict(created=0, replaced=0, renamed=0, skipped=0, invalid=[], total=len(items))
    for it in items:
        name, fmt = it["name"][:F.MAX_PROFILE_NAME], it["format"]

        def bad(msg: str) -> None:
            out["invalid"].append(dict(name=name, format=fmt, error=msg))
        if not name:
            bad(_("profile_name_empty"))
            continue
        if F.format_of(fmt) is None:
            bad(_("imp_profile_format", name=name, f=fmt[:40]))
            continue
        if it.get("error"):
            bad(it["error"])
            continue
        try:
            doc = F.ImportProfile.model_validate(dict(format=fmt, params=it["params"])).model_dump(mode="json")
        except ValidationError as e:
            bad(format_errors(e.errors()))
            continue
        ex = _find(fmt, name)
        try:
            if ex is None:
                settings.create(SCOPE, name, doc)
                out["created"] += 1
            elif on_conflict == "skip":
                out["skipped"] += 1
            elif on_conflict == "rename":
                settings.create(SCOPE, _free_name(fmt, name), doc)
                out["renamed"] += 1
            else:
                settings.update(SCOPE, ex["id"], None, doc)
                out["replaced"] += 1
        except settings.SettingsError as e:
            bad(str(e))
    return out
