"""LB W15: vizual redaktor uchun jonli ko'rinish (`design`) va ZPL chiqarish.

  POST /api/label-templates/design                  — shablon + namuna (yoki loyiha qatori) → SVG (har element `<g data-p>` ichida) + xatolar
                                                      + o'zgaruvchilar qiymatlari (redaktor: tanlash/ko'chirish, «Переменные» paneli)
  GET  /api/projects/{pid}/operations/{oid}/lb/labels/zpl   — LB operatsiyasi bo'yicha `.zpl` fayl (query: dpi, header, utf8, font)
  POST /api/projects/{pid}/lb/labels/zpl            — saqlanmagan LBParams bilan `.zpl` fayl ({lb, zpl})
  POST /api/projects/{pid}/lb/labels/zpl/preview    — birinchi etiketkalar ZPL matni + ogohlantirishlar (JSON)
  POST /api/label-templates/zpl                     — shablonning bitta etiketkasi (namuna ma'lumot) ZPL matni

ZPL sozlamalari — `label_zpl` scope ining standart profili (`/api/settings/label_zpl/default`), so'rovdagi qiymatlar uni bosadi.
Printerga to'g'ridan yuborish yo'q (drayver/tarmoq bu paketda yo'q): faqat fayl.
"""
from __future__ import annotations

import re
from typing import Any, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError

from . import store
from .api_labels import _op_lb
from .i18n import LANG, _, format_errors
from .models import LB_MAX_LABELS, LBParams
from .services import label_print, label_tpl, label_vars, label_zpl, settings
from .services.label_schema import ZplSettings
from .services.label_user import normalize_fields

router = APIRouter()
Lang = Literal["ru", "uz"]
Kind = Literal["part", "waste", "product", "user"]


# ───────────────────────── Vizual redaktor: jonli ko'rinish ─────────────────────────
class DesignIn(BaseModel):
    template: Any
    params: dict[str, Any] = Field(default_factory=dict)
    width_mm: Optional[float] = Field(None, gt=0, le=500)
    height_mm: Optional[float] = Field(None, gt=0, le=500)
    kind: Kind = "part"
    fields: list[dict] = Field(default_factory=list, max_length=50)       # kind=user: maydonlar sxemasi
    row: Optional[dict] = None                                            # kind=user: namuna qator
    project_id: Optional[str] = None                                      # berilsa: shu loyihaning `index`-chi etiketka qatori
    lb: Optional[LBParams] = None
    index: int = Field(0, ge=0, le=1_000_000)
    values: bool = True                                                   # o'zgaruvchilar qiymatlarini ham qaytarish


def _plain(v: Any) -> Any:
    """JSON ga mos qiymat (ifoda dvigateli turlari)."""
    if isinstance(v, str):
        return label_tpl._CTRL_RE.sub(" ", v)[:500]          # yakka surrogat/boshqaruv belgilari JSON/UTF-8 ni buzmasin; panel uchun qisqartirilgan
    if v is None or isinstance(v, (bool, int)):
        return v
    if isinstance(v, float):
        return v if v == v and abs(v) != float("inf") else None
    return str(v)


def _design_env(inp: DesignIn, lang: str, w: float, h: float) -> tuple[dict, dict]:
    """(env, meta): loyiha qatori (project_id + lb) yoki namuna ma'lumot."""
    if inp.project_id and inp.lb is not None:
        project = store.load(inp.project_id)
        lb = inp.lb
        counts = label_vars.count_items(project, lb)
        total = counts["total"]
        if total > 0:
            idx = min(inp.index, total - 1)
            it = None
            for i, cur in enumerate(label_vars.iter_items(project, lb)):
                if i >= idx:
                    it = cur
                    break
            if it is not None:
                eb = label_vars.EnvBuilder(project, lb, total, lang)
                eb.number = idx
                return eb.env(it), {"source": "project", "total": total, "index": idx, "kind": it.kind}
    lb = LBParams(mode="roll", width_mm=w, height_mm=h)
    if inp.kind == "user" and inp.fields:
        try:
            lb = LBParams(mode="roll", width_mm=w, height_mm=h, fields=normalize_fields(inp.fields), source="user")
        except (ValueError, ValidationError):
            pass
    return label_vars.sample_env(inp.kind, lang, lb, inp.row), {"source": "sample", "total": 1, "index": 0, "kind": inp.kind}


@router.post("/label-templates/design", tags=["etiketkalar"])
def template_design(inp: DesignIn, lang: Lang = "ru"):
    """Redaktor: shablonni namuna ma'lumot bilan chizadi. Javob: `svg` (viewBox mm; har element `<g data-p="yo'l" data-t="tur">`),
    `errors` (ifoda xatolari: path/field/message), `warnings`, `values` (o'zgaruvchi → qiymat), `tpl_values` (shablon parametr/vars)."""
    token = LANG.set(lang)
    try:
        try:
            tpl = label_tpl.normalize_template(inp.template)
        except label_tpl.TemplateError as e:
            return {"svg": "", "width": inp.width_mm or 58, "height": inp.height_mm or 40,
                    "errors": [{"path": "", "field": "", "expr": "", "message": str(e), "count": 1}], "warnings": [],
                    "values": {}, "tpl_values": {}, "meta": {"source": "sample", "total": 1, "index": 0, "kind": inp.kind}}
        w = inp.width_mm or float(tpl["size"]["w"])
        h = inp.height_mm or float(tpl["size"]["h"])
        env, meta = _design_env(inp, lang, w, h)
        r = label_tpl.Renderer(tpl, width_mm=w, height_mm=h, params=inp.params, lang=lang, mark=True)
        svg = r.render(env)
        out: dict = {"svg": svg, "width": w, "height": h, "errors": list(r.errors.values()),
                     "warnings": [x["message"] for x in r.warnings.values()], "meta": meta, "values": {}, "tpl_values": {}}
        if inp.values:
            vals = {n: _plain(env[n]) for n, *_r in label_vars.VARS if n in env}
            vals.update({k: _plain(v) for k, v in env.items() if k.startswith("user.")})
            out["values"] = vals
            names = [p["name"] for p in tpl["params"]] + [v["name"] for v in tpl["vars"]]
            names += [el["name"] for _p, el in label_tpl.walk(tpl["elements"]) if el.get("t") == "var" and el.get("name")]
            out["tpl_values"] = {n: _plain(env.get(n)) for n in names}
        return out
    finally:
        LANG.reset(token)


# ───────────────────────── ZPL ─────────────────────────
def _zpl_settings(over: dict[str, Any]) -> ZplSettings:
    """Standart profil (`label_zpl` scope) + so'rovdagi qiymatlar."""
    base = settings.get_default("label_zpl")
    merged = {**base, **{k: v for k, v in over.items() if v is not None}}
    try:
        return ZplSettings.model_validate(merged)
    except ValidationError as e:
        raise HTTPException(422, format_errors(e.errors())) from e


def _file_stem(*parts: str) -> str:
    s = re.sub(r"[^\w.-]+", "_", "_".join(p for p in parts if p), flags=re.UNICODE).strip("_")
    return s[:80] or "labels"


def _zpl_response(project, lb: LBParams, zs: ZplSettings, lang: str, name: str) -> Response:
    try:
        res = label_zpl.render_zpl(project, lb, zs, lang=lang)
    except label_print.LabelsLimit as e:
        raise HTTPException(422, str(e)) from e
    if res.errors and not res.zpl:
        raise HTTPException(422, "; ".join(str(e.get("message", "")) for e in res.errors[:3]))
    if res.rendered == 0:
        raise HTTPException(422, _("lb.empty"))
    stem = _file_stem(project.name, name)
    return Response(res.zpl.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(stem)}.zpl",
                             "X-ZPL-Warnings": str(len(res.warnings)), "X-ZPL-Labels": str(res.rendered),
                             "X-Content-Type-Options": "nosniff"})


@router.get("/projects/{pid}/operations/{oid}/lb/labels/zpl", tags=["etiketkalar"])
def lb_zpl_get(pid: str, oid: str, dpi: Optional[int] = None, header: Optional[str] = None,
               utf8: Optional[bool] = None, font: Optional[str] = None, emit_size: Optional[bool] = None, lang: Lang = "ru"):
    """LB operatsiyasi bo'yicha hamma etiketkalar — `.zpl` fayl (≤ 10 000 etiketka)."""
    project, lb = _op_lb(pid, oid)
    zs = _zpl_settings(dict(dpi=dpi, header=header, utf8=utf8, font=font, emit_size=emit_size))
    op = store.op_of(project, oid)
    return _zpl_response(project, lb, zs, lang, op.name or "LB")


class ZplDraftIn(BaseModel):
    lb: LBParams = Field(default_factory=LBParams)
    zpl: dict[str, Any] = Field(default_factory=dict)         # ZplSettings maydonlari (berilmaganlari — standart profil)
    shown: int = Field(label_zpl.PREVIEW_LABELS, ge=1, le=20)
    scan: int = Field(label_zpl.PREVIEW_SCAN, ge=0, le=2000)


@router.post("/projects/{pid}/lb/labels/zpl", tags=["etiketkalar"])
def lb_zpl_draft(pid: str, inp: ZplDraftIn, lang: Lang = "ru"):
    """Saqlanmagan LB parametrlari bilan `.zpl` fayl."""
    return _zpl_response(store.load(pid), inp.lb, _zpl_settings(inp.zpl), lang, "labels")


@router.post("/projects/{pid}/lb/labels/zpl/preview", tags=["etiketkalar"])
def lb_zpl_preview(pid: str, inp: ZplDraftIn, lang: Lang = "ru"):
    """Oldindan ko'rish: birinchi etiketkalar ZPL matni, ogohlantirishlar (birinchi `scan` ta etiketka bo'yicha) va jami soni."""
    zs = _zpl_settings(inp.zpl)
    try:
        res = label_zpl.render_zpl(store.load(pid), inp.lb, zs, lang=lang, limit=inp.shown, scan=inp.scan)
    except label_print.LabelsLimit as e:
        raise HTTPException(422, str(e)) from e
    return {"zpl": res.zpl, "total": res.total, "rendered": res.rendered, "truncated": res.truncated, "warnings": res.warnings,
            "errors": res.errors, "dpi": zs.dpi, "template_name": res.template_name, "max_labels": LB_MAX_LABELS,
            "settings": zs.model_dump()}


class ZplSampleIn(BaseModel):
    template: Any
    params: dict[str, Any] = Field(default_factory=dict)
    width_mm: Optional[float] = Field(None, gt=0, le=500)
    height_mm: Optional[float] = Field(None, gt=0, le=500)
    kind: Kind = "part"
    rotate_page: Literal[0, 90] = 0
    zpl: dict[str, Any] = Field(default_factory=dict)


@router.post("/label-templates/zpl", tags=["etiketkalar"])
def template_zpl(inp: ZplSampleIn, lang: Lang = "ru"):
    """Shablon + namuna ma'lumot → bitta etiketka ZPL matni (loyihasiz; redaktor va tekshiruv uchun)."""
    try:
        tpl = label_tpl.normalize_template(inp.template)
    except label_tpl.TemplateError as e:
        raise HTTPException(422, str(e)) from e
    w = inp.width_mm or float(tpl["size"]["w"])
    h = inp.height_mm or float(tpl["size"]["h"])
    res = label_zpl.render_zpl_sample(tpl, width_mm=w, height_mm=h, params=inp.params, kind=inp.kind, lang=lang,
                                      settings=_zpl_settings(inp.zpl), rotate_page=inp.rotate_page)
    return {"zpl": res.zpl, "warnings": res.warnings, "errors": res.errors, "dpi": res.dpi}
