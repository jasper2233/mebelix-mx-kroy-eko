"""LB (etiketkalar) API — W4: shablon kutubxonasi, tekshiruv, jonli ko'rinish, chop, A4 da kroy kartalari miniatyurasi.

Shablon kutubxonasi — sozlama profillari (`label_template` scope: `/api/settings/label_template` — yaratish/nomlash/o'chirish);
bu yerda: o'rnatilgan namunalar bilan umumiy ro'yxat, tekshiruv, jonli ko'rinish, import/eksport, o'zgaruvchilar ro'yxati.
Eski `GET/POST /projects/{pid}/labels` (qat'iy QR etiketka) — main.py da, o'zgarishsiz.
"""
from __future__ import annotations

import json
import re
from typing import Any, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from . import store
from .i18n import LANG, _
from .models import LB_MAX_LABELS, LBParams, OpType, PrintSettings
from .services import label_builtin, label_print, label_tpl, label_vars, render, settings
from .services.expr import FUNCTION_GROUPS

router = APIRouter()
SCOPE = "label_template"
Lang = Literal["ru", "uz"]


def _html(body: str) -> HTMLResponse:
    """Etiketka sahifasi: skript yo'q (CSP), boshqa saytga ulanmaydi."""
    return HTMLResponse(body, headers={"Content-Security-Policy": render.REPORT_CSP, "X-Content-Type-Options": "nosniff"})


def _op_lb(pid: str, oid: str) -> tuple[Any, LBParams]:
    project = store.load(pid)
    op = store.op_of(project, oid)
    if op.type != OpType.LB:
        raise HTTPException(400, _("lb.e_not_lb"))
    return project, op.lb or LBParams()


def _render(project, lb: LBParams, lang: str, **kw):
    try:
        return label_print.render_labels(project, lb, lang=lang, **kw)
    except label_print.LabelsLimit as e:
        raise HTTPException(422, str(e)) from e


# ───────────────────────── Shablonlar ─────────────────────────
def _profile_meta(pr: dict) -> dict:
    data = pr.get("data") or {}
    return {"id": f"profile:{pr['id']}", "profile_id": pr["id"], "key": None, "name": pr["name"], "builtin": False,
            "is_default": bool(pr.get("is_default")), "kind": "part", "size": data.get("size") or {"w": 58, "h": 40},
            "params": data.get("params") or []}


@router.get("/label-templates", tags=["etiketkalar"])
def templates_list(lang: Lang = "ru"):
    """O'rnatilgan namunalar + kutubxona (sozlama profillari)."""
    return label_builtin.builtin_list(lang) + [_profile_meta(p) for p in settings.list_profiles(SCOPE)]


def _find_template(tid: str, lang: str) -> tuple[dict, bool, str]:
    """tid → (shablon, o'rnatilgan?, nom)."""
    if tid.startswith("builtin:"):
        t = label_builtin.builtin_template(tid[8:], lang)
        if t is None:
            raise HTTPException(404, _("lb.tpl_not_found"))
        return t, True, t["name"]
    m = re.fullmatch(r"(?:profile:)?(\d+)", tid)
    pr = settings.get_profile(SCOPE, int(m.group(1))) if m else None
    if pr is None:
        raise HTTPException(404, _("lb.tpl_not_found"))
    t = dict(pr["data"])
    t["name"] = pr["name"]
    return t, False, pr["name"]


@router.get("/label-templates/{tid}", tags=["etiketkalar"])
def template_get(tid: str, lang: Lang = "ru"):
    t, builtin, name = _find_template(tid, lang)
    return {"id": tid, "name": name, "builtin": builtin, "template": t}


class CheckIn(BaseModel):
    template: Any
    params: dict[str, Any] = Field(default_factory=dict)
    width_mm: Optional[float] = Field(None, gt=0, le=500)
    height_mm: Optional[float] = Field(None, gt=0, le=500)
    kind: Literal["part", "waste", "product", "user"] = "part"


@router.post("/label-templates/check", tags=["etiketkalar"])
def template_check(inp: CheckIn, lang: Lang = "ru"):
    """Muharrir: tuzilma, ifoda sintaksisi, namuna qatorida hisoblash → {ok, errors[], warnings[]}."""
    env = label_vars.sample_env(inp.kind, lang)
    return label_tpl.check_template(inp.template, inp.params, lang, env, inp.width_mm, inp.height_mm)


class SampleIn(CheckIn):
    rotate_page: Literal[0, 90] = 0
    border: bool = True


@router.post("/label-templates/preview", tags=["etiketkalar"])
def template_preview(inp: SampleIn, lang: Lang = "ru"):
    """Saqlamasdan ko'rish: namuna ma'lumot bilan bitta etiketka (HTML + xatolar)."""
    token = LANG.set(lang)
    try:
        try:
            tpl = label_tpl.normalize_template(inp.template)
        except label_tpl.TemplateError as e:
            err = {"path": "", "field": "", "expr": "", "message": str(e), "count": 1}
            return {"html": "", "errors": [err], "warnings": []}
        w = inp.width_mm or float(tpl["size"]["w"])
        h = inp.height_mm or float(tpl["size"]["h"])
        lb = LBParams(mode="roll", width_mm=w, height_mm=h, rotate_page=inp.rotate_page, border=inp.border)
        env = label_vars.sample_env(inp.kind, lang, lb)
        r = label_tpl.Renderer(tpl, width_mm=w, height_mm=h, params=inp.params, lang=lang)
        svg = r.render(env)
        res = label_print.LabelsResult(total=1, rendered=1, pages=1, errors=list(r.errors.values()), banner=False,
                                       warnings=[x["message"] for x in r.warnings.values()])
        return {"html": label_print._page(lb, [svg], res, lang), "errors": res.errors, "warnings": res.warnings}
    finally:
        LANG.reset(token)


@router.get("/label-templates/{tid}/export", tags=["etiketkalar"])
def template_export(tid: str, lang: Lang = "ru"):
    t, _builtin, name = _find_template(tid, lang)
    fname = re.sub(r"[^\w.-]+", "_", name, flags=re.UNICODE).strip("_") or "label"
    # sarlavha qiymati faqat ASCII bo'lishi shart (kirill nomlar — RFC 5987 foiz kodlash bilan)
    return Response(json.dumps(t, ensure_ascii=False, indent=1), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}.label.json"})


@router.post("/label-templates/import", tags=["etiketkalar"])
def template_import(body: Any = Body(...), name: Optional[str] = None):
    """Eksport qilingan shablon JSON ini kutubxonaga qo'shish (tuzilma tekshiriladi; ifoda xatolari — `check` javobida)."""
    try:
        tpl = label_tpl.normalize_template(body)
    except label_tpl.TemplateError as e:
        raise HTTPException(422, str(e)) from e
    nm = (name or tpl.get("name") or "Label").strip()[:100] or "Label"
    pr = settings.create(SCOPE, nm, tpl)
    chk = label_tpl.check_template(tpl, None, "uz" if LANG.get() == "uz" else "ru")
    return {"profile": pr, "id": f"profile:{pr['id']}", "errors": chk["errors"], "warnings": chk["warnings"]}


@router.get("/label-variables", tags=["etiketkalar"])
def variables(lang: Lang = "ru"):
    """Muharrir uchun: o'zgaruvchilar (guruhlar bo'yicha) va ifoda funksiyalari."""
    funcs = [{"group": g, "name": n, "sig": s} for g, items in FUNCTION_GROUPS.items() for n, s in items]
    return {"groups": label_vars.variable_catalog(lang), "functions": funcs,
            "aliases": sorted(label_vars.ALIASES), "max_labels": LB_MAX_LABELS}


# ───────────────────────── Loyiha: sanash, ko'rish, chop ─────────────────────────
@router.get("/projects/{pid}/operations/{oid}/lb/count", tags=["etiketkalar"])
def lb_count(pid: str, oid: str):
    project, lb = _op_lb(pid, oid)
    return label_vars.count_items(project, lb)


@router.post("/projects/{pid}/lb/count", tags=["etiketkalar"])
def lb_count_draft(pid: str, lb: LBParams):
    """Saqlanmagan LB parametrlari bo'yicha etiketkalar soni (Печать → Этикетки)."""
    return label_vars.count_items(store.load(pid), lb)


class PreviewIn(BaseModel):
    lb: LBParams = Field(default_factory=LBParams)
    shown: int = Field(label_print.PREVIEW_SHOWN, ge=1, le=60)
    scan: int = Field(label_print.PREVIEW_SCAN, ge=0, le=2000)


@router.post("/projects/{pid}/lb/preview", tags=["etiketkalar"])
def lb_preview(pid: str, inp: PreviewIn, lang: Lang = "ru"):
    """Jonli ko'rinish: birinchi etiketkalar HTML + xatolar (birinchi `scan` ta etiketka hisoblanadi) + jami soni."""
    res = _render(store.load(pid), inp.lb, lang, limit=inp.shown, scan=inp.scan, banner=False)
    return {"html": res.html, "total": res.total, "rendered": res.rendered, "pages": res.pages, "counts": res.counts,
            "errors": res.errors, "warnings": res.warnings, "template": res.template, "template_name": res.template_name,
            "truncated": res.truncated, "max_labels": LB_MAX_LABELS}


@router.get("/projects/{pid}/operations/{oid}/lb/labels", response_class=HTMLResponse, tags=["etiketkalar"])
def lb_labels(pid: str, oid: str, lang: Lang = "ru"):
    """LB operatsiyasi bo'yicha chop sahifasi (hamma etiketkalar, ≤ 10 000)."""
    project, lb = _op_lb(pid, oid)
    return _html(_render(project, lb, lang).html)


@router.post("/projects/{pid}/lb/labels", response_class=HTMLResponse, tags=["etiketkalar"])
def lb_labels_draft(pid: str, lb: LBParams, lang: Lang = "ru"):
    """Saqlanmagan LB parametrlari bilan chop sahifasi."""
    return _html(_render(store.load(pid), lb, lang).html)


@router.get("/projects/{pid}/operations/{oid}/lb/rows", tags=["etiketkalar"])
def lb_rows(pid: str, oid: str, limit: int = Query(200, ge=1, le=2000), lang: Lang = "ru"):
    """Hal qilingan qatorlar (tashqi printer / MES uchun): tartib raqami, tur, shtrixkod kodi va asosiy qiymatlar."""
    project, lb = _op_lb(pid, oid)
    counts = label_vars.count_items(project, lb)
    eb = label_vars.EnvBuilder(project, lb, counts["total"], lang)
    rows = []
    for it in label_vars.iter_items(project, lb):
        if len(rows) >= limit:
            break
        e = eb.env(it)
        rows.append({"number": e["label.number"], "kind": it.kind, "code": e["label.code"], "part_uid": e["part.id"],
                     "name": e["part.name"] or e["product.name"], "copy": e["part.copy"], "copies": e["part.copies"],
                     "map": e["map.index"], "material": e["material.name"], "length": e["part.length"],
                     "width": e["part.width"], "label_index": e["label.index"], "label_count": e["label.count"]})
    return {"total": counts["total"], "rows": rows}


# ───────────────────────── Kroy kartalari miniatyurasi (A4 da 4 / 6) ─────────────────────────
@router.get("/projects/{pid}/map-sheets", response_class=HTMLResponse, tags=["hisobot"])
def map_sheets(pid: str, per_page: int = Query(4), op_id: Optional[str] = None, profile_id: Optional[int] = None,
               lang: Lang = "ru"):
    """Kroy kartalari miniatyurasi: A4 varaqda 4 yoki 6 karta (chop sozlamalari profilidan kromka/ko'zgu/QR olinadi)."""
    if per_page not in label_print.MAP_SHEET_COUNTS:
        raise HTTPException(422, _("lb.e_per_page"))
    ps = PrintSettings.model_validate(settings.resolve("print", profile_id))
    html, _n = label_print.map_sheets_html(store.load(pid), per_page=per_page, op_id=op_id, lang=lang, ps=ps)
    return _html(html)
