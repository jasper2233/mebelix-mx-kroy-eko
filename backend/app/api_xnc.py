"""XNC API (W1): shablonlar kutubxonasi (o'rnatilgan + foydalanuvchi), shablonni operatsiyaga qo'llash, Par parametrlari
holati, ishlov markazi postprotsessori (XNC operatsiyasi uchun)."""
from __future__ import annotations

import json
from typing import Any, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from . import store
from .i18n import _, LANG
from .models import OpType, Operation, PostprocessorProfile, Project, XncCommand
from .services import settings
from .services import xnc as xnc_svc
from .services import xnc_constraints as xcons
from .services import xnc_templates as tpl
from .services import xnc_tools

router = APIRouter()
# sozlamadagi asboblar jadvali hisobda zaxira (T nomi → D, DP): ilova ishga tushganda ulanadi (W8)
xnc_svc.set_tool_library_provider(xnc_tools.current_library)


# ───────────────────────── Shablonlar kutubxonasi ─────────────────────────
def _parse_id(tid: str) -> tuple[str, str | int]:
    if tid.startswith("lib:") and tid[4:] in tpl.LIBRARY:
        return "lib", tid[4:]
    if tid.startswith("u:") and tid[2:].isdigit():
        return "u", int(tid[2:])
    raise HTTPException(404, _("xnc_tpl_not_found"))


def _row_item(r: dict) -> dict:
    d = r.get("data") or {}
    prog = d.get("program") or []
    return dict(id=f"u:{r['id']}", name=r["name"], description=d.get("description", ""), category=d.get("category", ""),
                builtin=False, par_count=sum(1 for c in prog if c.get("cmd") == "Par"),
                commands=tpl.count_nodes(prog)[0] if prog else 0)


def load_template(tid: str, lang: Optional[str] = None) -> tuple[str, tpl.XncTemplate]:
    """(nom, shablon) — o'rnatilgan (til bo'yicha) yoki foydalanuvchi shabloni."""
    kind, key = _parse_id(tid)
    if kind == "lib":
        ru, uz, dru, duz, cat, _build = tpl.LIBRARY[key]
        uzb = (lang or "ru").lower().startswith("uz")
        return (uz if uzb else ru), tpl.XncTemplate(description=duz if uzb else dru, category=cat,
                                                    program=tpl.library_program(key, lang))
    r = settings.get_profile("xnc_template", key)
    if r is None:
        raise HTTPException(404, _("xnc_tpl_not_found"))
    return r["name"], tpl.XncTemplate.model_validate(r["data"])


@router.get("/xnc/templates", tags=["xnc"])
def templates_list(lang: Optional[str] = None):
    """Shablonlar ro'yxati: o'rnatilgan namunalar (`builtin=true`) + foydalanuvchi shablonlari."""
    return [*tpl.library_list(lang), *(_row_item(r) for r in settings.list_profiles("xnc_template"))]


@router.get("/xnc/templates/{tid}", tags=["xnc"])
def templates_get(tid: str, lang: Optional[str] = None):
    name, t = load_template(tid, lang)
    return dict(id=tid, name=name, builtin=tid.startswith("lib:"), **t.model_dump(mode="json"))


class TemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field("", max_length=2000)
    category: str = Field("", max_length=40)
    program: list[XncCommand] = []
    par_values: dict[str, float | str] = {}


def _save(name: str, t: tpl.XncTemplate, upsert: bool) -> dict:
    name = name.strip()
    if not name:
        raise HTTPException(400, _("profile_name_empty"))
    try:
        ex = settings.find_by_name("xnc_template", name) if upsert else None
        if ex is not None:
            return settings.update("xnc_template", ex["id"], None, t.model_dump(mode="json"))
        return settings.create("xnc_template", name, t.model_dump(mode="json"))
    except settings.SettingsError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/xnc/templates", tags=["xnc"])
def templates_save(inp: TemplateIn, upsert: bool = False):
    """Dasturni nom bilan shablon sifatida saqlash (`upsert=true` — shu nomli shablon bo'lsa yangilanadi)."""
    t = tpl.XncTemplate(description=inp.description, category=inp.category, program=inp.program, par_values=inp.par_values)
    return _row_item(_save(inp.name, t, upsert))


@router.delete("/xnc/templates/{tid}", tags=["xnc"])
def templates_delete(tid: str):
    kind, key = _parse_id(tid)
    if kind == "lib":
        raise HTTPException(400, _("xnc_tpl_builtin_ro"))
    try:
        settings.delete("xnc_template", int(key))
    except KeyError as e:
        raise HTTPException(404, _("xnc_tpl_not_found")) from e
    return {"ok": True}


@router.get("/xnc/templates/{tid}/export", tags=["xnc"])
def templates_export(tid: str, lang: Optional[str] = None):
    """Shablonni JSON faylga eksport qilish (yuklab olinadi)."""
    name, t = load_template(tid, lang)
    data = json.dumps(tpl.to_file(name, t), ensure_ascii=False, indent=2).encode("utf-8")
    fname = quote(f"{name}.xnc.json")
    return Response(data, media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{fname}"})


@router.post("/xnc/templates/import", tags=["xnc"])
def templates_import(body: Any = Body(...), upsert: bool = False):
    """JSON fayldan (eksport formati) shablon qo'shish. Format noto'g'ri — 400."""
    try:
        name, t = tpl.from_file(body)
    except tpl.TemplateError as e:
        raise HTTPException(400, str(e)) from e
    return _row_item(_save(name, t, upsert))


# ───────────────────────── Shablonni operatsiyaga qo'llash ─────────────────────────
class ApplyIn(BaseModel):
    template: str                                   # lib:<kalit> | u:<id>
    mode: Literal["replace", "append"] = "replace"  # mavjud dastur o'rniga yoki oxiriga
    lang: Optional[str] = None


def _xnc_op(p: Project, oid: str) -> Operation:
    op = store.op_of(p, oid)
    if op.type != OpType.XNC or op.xnc is None:
        raise HTTPException(400, _("not_xnc"))
    return op


@router.post("/projects/{pid}/operations/{oid}/xnc/apply-template", tags=["xnc"])
def apply_template(pid: str, oid: str, inp: ApplyIn):
    """Shablon dasturini operatsiyaga qo'yish. replace — dastur va Par qiymatlari shablondagidek; append — oxiriga
    qo'shiladi (mavjud dasturdagi bilan bir nomli Par qayta e'lon qilinmaydi). Javob — yangilangan loyiha."""
    _name, t = load_template(inp.template, inp.lang)
    with store.editing(pid) as p:
        x = _xnc_op(p, oid).xnc
        x.program, _skipped = tpl.merge_program(x.program, t.program, inp.mode)
        if inp.mode != "append":
            x.par_values = dict(t.par_values)
        else:
            x.par_values = {**t.par_values, **x.par_values}
    return p


# ───────────────────────── DXF import (ixtiyoriy) ─────────────────────────
@router.post("/projects/{pid}/operations/{oid}/xnc/import-dxf", tags=["xnc"])
async def import_dxf(pid: str, oid: str, file: UploadFile = File(...), mode: str = Form("append"),
                     origin: str = Form("bbox"), flip_y: bool = Form(True), depth: str = Form("dz"),
                     tool_d: float = Form(6.0), correction: int = Form(0), drill_max_d: Optional[float] = Form(None),
                     drill_depth: str = Form("dz")):
    """ASCII DXF (LINE, ARC, LWPOLYLINE, POLYLINE, CIRCLE) → kontur frezalash buyruqlari (services/xnc_dxf.py qoidalari).
    mode=append — mavjud dastur oxiriga, replace — o'rniga. Javob: {project, warnings, stats}."""
    from .services import xnc_dxf
    if mode not in ("append", "replace"):
        raise HTTPException(400, _("xnc_tpl_mode"))
    if origin not in ("bbox", "zero") or not (0 < tool_d <= 1000) or correction not in (0, 1, 2, 3) \
            or len(depth) > 200 or len(drill_depth) > 200 or (drill_max_d is not None and not (0 < drill_max_d <= 1000)):
        raise HTTPException(400, _("val_choice"))
    data = await file.read(xnc_dxf.MAX_BYTES + 1)
    p = store.load(pid)
    x0 = _xnc_op(p, oid).xnc
    try:
        prog, warnings, stats = xnc_dxf.to_program(data, origin=origin, flip_y=flip_y, height=x0.width, depth=depth,
                                                   tool_d=tool_d, correction=correction, drill_max_d=drill_max_d,
                                                   drill_depth=drill_depth)
    except xnc_dxf.DxfError as e:
        raise HTTPException(400, str(e)) from e
    with store.editing(pid) as p:
        x = _xnc_op(p, oid).xnc
        x.program = prog if mode == "replace" else [*x.program, *prog]
    return {"project": p, "warnings": warnings, "stats": stats}


# ───────────────────────── Par parametrlari holati ─────────────────────────
@router.get("/projects/{pid}/operations/{oid}/xnc-params", tags=["xnc"])
def xnc_params(pid: str, oid: str):
    """Dasturdagi Par parametrlari: nom, yorliq, tur, standart qiymat, joriy qiymat, ko'rinish (visible) va faqat o'qish
    (readonly) — ifodalar operatsiyadagi hozirgi qiymatlar bilan hisoblangan. UI «Параметры» yorlig'idagi forma shundan."""
    p = store.load(pid)
    op = _xnc_op(p, oid)
    x = op.xnc
    ops = xnc_svc.evaluate(x.program, x.length, x.width, x.thickness, xnc_svc.program_vars(x), x.par_values)
    return dict(params=xnc_svc.unique_params(ops.params), errors=ops.problems, warnings=list(ops.messages),
                warning_src=list(ops.msg_src))


@router.get("/projects/{pid}/operations/{oid}/xnc-vars", tags=["xnc"])
def xnc_vars(pid: str, oid: str):
    """«Переменные» oynasi: tizim o'zgaruvchilari (allowanceB … xncSide) va dasturning o'z Par / Var lari joriy hisoblangan
    qiymatlari bilan — {rows: [{name, kind, type, value, description}]} (faqat o'qish)."""
    p = store.load(pid)
    return dict(rows=xnc_svc.variable_table(_xnc_op(p, oid).xnc))


# ───────────────────────── Stanok cheklovlari (W8) ─────────────────────────
@router.get("/projects/{pid}/operations/{oid}/xnc-constraints", tags=["xnc"])
def xnc_constraints_check(pid: str, oid: str, long_side: str = "any"):
    """Dasturning stanok cheklovlariga mosligi (sozlama «Настройки → XNC → Ограничения»): {mode, issues[{level, code, text,
    text_ru, text_uz, command_path, count}], extra_turn, rotation}. Rejim off — issues bo'sh."""
    if long_side not in ("any", "horizontal", "vertical"):
        raise HTTPException(400, _("pp_long_side"))
    p = store.load(pid)
    return xcons.analyze(_xnc_op(p, oid), p, None, long_side)


# ───────────────────────── Ishlov markazi postprotsessori ─────────────────────────
@router.get("/xnc/postprocessors", tags=["xnc", "postprotsessor"])
def xnc_postprocessors():
    """XNC operatsiyasi uchun mavjud chiqishlar: o'rnatilgan JSON, foydalanuvchi shablonlari va yoqilgan ishlov markazlari
    (`cnc` guruhi; shablon biriktirilgan bo'lsa ishlaydi)."""
    from .api_extra import _machine_cfg
    from .services import postprocessors as pp
    out = [dict(key=k, name=_(f"pp_builtin_xnc_{k}"), extension=v["extension"], builtin=True)
           for k, v in pp.XNC_BUILTIN.items()]
    profiles = {r["id"]: r for r in settings.list_profiles("postprocessor")}
    for pr in profiles.values():
        d = pr["data"]
        kind = pp.template_kind(d.get("template", ""))
        if kind == "saw":                      # pil markazi shabloni (map/maps) — XNC uchun ko'rsatilmaydi (QA #14)
            continue
        out.append(dict(key=f"pp:{pr['id']}", profile_id=pr["id"], name=pr["name"] or d.get("name", ""),
                        extension=d.get("extension", "txt"), builtin=False, kind=kind))
    cfg = _machine_cfg()
    from .services import ppfmt
    native = ppfmt.load_all()
    for key, name, grp in pp.MACHINES:
        nat = native.get(key)
        has_native = nat is not None and nat.group == "cnc"
        if grp == "cnc" and (cfg["enabled"].get(key) or has_native):     # o'rnatilgan format — doim ro'yxatda
            pr = profiles.get(cfg["profile"].get(key))
            ext = pr["data"].get("extension", "txt") if pr else (nat.ext if has_native else "")
            out.append(dict(key=f"machine:{key}", name=name, extension=ext, builtin=False, machine=True,
                            available=bool(pr) or has_native, native=has_native and not pr,
                            note=nat.note if has_native and not pr else "",
                            label=pp.pp_label(key, LANG.get()), order=pp.pp_order(key)))
    head = [x for x in out if not x.get("machine")]
    return head + sorted((x for x in out if x.get("machine")), key=lambda x: x["order"])


def postprocess_xnc(p: Project, op: Operation, key: Optional[str], profile_id: Optional[int], long_side: str) -> Response:
    """`GET /projects/{pid}/operations/{oid}/postprocess` XNC operatsiyasi uchun (main.py shuni chaqiradi)."""
    from .api_extra import _machine_cfg
    from .services import postprocessors as pp
    from .services.tpl_sandbox import TemplateLimit
    if not pp.is_xnc(op):
        raise HTTPException(400, _("not_xnc"))
    if long_side not in ("any", "horizontal", "vertical"):
        raise HTTPException(400, _("pp_long_side"))
    cons = xcons.load()                       # stanok cheklovlari (W8): rejim off bo'lsa e'tiborsiz
    machine = None
    mk: Optional[str] = None
    if key and key.startswith("machine:"):
        mk = key.split(":", 1)[1]
        if mk not in pp.MACHINE_BY_KEY:
            raise HTTPException(400, _("pp_machine_unknown", k=mk))
        machine, grp = pp.MACHINE_BY_KEY[mk]
        cfg = _machine_cfg()
        if grp != "cnc":
            raise HTTPException(400, _("pp_machine_not_cnc", n=machine))
        from .services import ppfmt
        profile_id = cfg["profile"].get(mk)
        if not profile_id and ppfmt.available(mk) and ppfmt.REGISTRY[mk].group == "cnc":
            try:
                name, data, mime = ppfmt.run_cnc(mk, p, op, long_side)   # o'rnatilgan format (namunalardan)
            except ppfmt.FormatError as e:
                raise HTTPException(400, str(e)) from e
            if cfg["prefix"]:
                name = f"{pp._safe_name(machine, 'machine', 30)}_{name}"
            return Response(data, media_type=mime,
                            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})
        if not cfg["enabled"].get(mk):
            raise HTTPException(400, _("pp_machine_off", n=machine))
        if not profile_id:
            raise HTTPException(400, _("pp_machine_unbound", n=machine))
    if profile_id:
        pr = settings.get_profile("postprocessor", profile_id)
        if not pr:
            raise HTTPException(404, _("pp_not_found"))
        if pp.template_kind(pr["data"].get("template", "")) == "saw":     # «'map' is undefined» o'rniga tushunarli xabar
            raise HTTPException(400, _("pp_profile_saw", n=pr["name"] or pr["data"].get("name", "")))
        try:
            name, data, mime = pp.render_template_xnc(PostprocessorProfile.model_validate(pr["data"]), p, op, long_side, mk,
                                                      constraints=cons)
        except TemplateLimit as e:
            raise HTTPException(400, _("template_limit", e=e)) from e
        except Exception as e:  # noqa: BLE001 — shablon xatosi foydalanuvchiga
            raise HTTPException(400, _("template_error", e=e)) from e
        if machine and _machine_cfg()["prefix"]:
            name = f"{pp._safe_name(machine, 'machine', 30)}_{name}"
    elif key in pp.XNC_BUILTIN:
        name, data, mime = pp.run_builtin_xnc(key, p, op, long_side, constraints=cons)
    else:
        raise HTTPException(400, _("pp_not_selected"))
    return Response(data, media_type=mime,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


# ───────────────────────── O'rnatilgan stanok formatlari (v2.5, services/ppfmt) ─────────────────────────
@router.get("/postprocessors/native", tags=["postprotsessor"])
def native_formats():
    """Namunalardan o'rganilgan o'rnatilgan formatlar: {key, name, group (saw|cnc), ext, note}."""
    from .services import ppfmt
    return [dict(key=f.key, name=f.name, group=f.group, ext=f.ext, note=f.note) for f in ppfmt.load_all().values()]


@router.get("/projects/{pid}/postprocess-xnc", tags=["postprotsessor"])
def postprocess_xnc_project(pid: str, key: str, long_side: str = "any", ops: Optional[str] = None) -> Response:
    """Loyihaning XNC dasturlari bitta zip da (ishlov markazi formati: key=machine:<kalit>). `ops` — vergul bilan ajratilgan
    operatsiya id lari (faqat belgilanganlar); berilmasa — hammasi."""
    from .services import ppfmt
    if long_side not in ("any", "horizontal", "vertical"):
        raise HTTPException(400, _("pp_long_side"))
    mk = key.split(":", 1)[1] if key.startswith("machine:") else key
    if not ppfmt.available(mk) or ppfmt.REGISTRY[mk].group != "cnc":
        raise HTTPException(400, _("pp_machine_unknown", k=mk))
    p = store.load(pid)
    if not any(o.type == OpType.XNC for o in p.operations):
        raise HTTPException(400, _("not_xnc"))
    try:
        only = {x for x in (ops or "").split(",") if x} or None
        name, data, mime = ppfmt.run_cnc_project(mk, p, long_side, only)
    except ppfmt.FormatError as e:
        raise HTTPException(400, str(e)) from e
    return Response(data, media_type=mime,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


class XncLinkIn(BaseModel):
    part_id: Optional[str] = None            # None — bog'lanishni bekor qilish («Отменить деталь»)


@router.post("/projects/{pid}/operations/{oid}/xnc/link", tags=["xnc"])
def xnc_link_part(pid: str, oid: str, body: XncLinkIn):
    """«Выбрать деталь» / «Отменить деталь»: XNC dasturini kroy detaliga bog'lash yoki ajratish. Bog'langanda
    «По размеру детали» yoqilgan bo'lsa o'lcham va soni detaldan olinadi."""
    from .services import calc
    from .services.sizes import compute_sizes
    with store.editing(pid) as p:
        op = next((o for o in p.operations if o.id == oid), None)
        if op is None or op.type != OpType.XNC or op.xnc is None:
            raise HTTPException(400, _("not_xnc"))
        for o in p.operations:                         # eski bog'lanishlar
            for pt in o.parts:
                if oid in pt.xnc_op_ids:
                    pt.xnc_op_ids = [x for x in pt.xnc_op_ids if x != oid]
        op.xnc_part_id = None
        if body.part_id:
            hit = next(((o, pt) for o in p.operations for pt in o.parts if pt.id == body.part_id), None)
            if hit is None:
                raise HTTPException(404, _("part_not_found"))
            src, pt = hit
            pt.xnc_op_ids.append(oid)
            op.xnc_part_id = pt.id
            if op.xnc.by_part_size:
                s = compute_sizes(pt, p.size_mode, calc.edge_map(p))
                op.xnc.length, op.xnc.width = s.detail[0], s.detail[1]
                if src.cs_material:
                    op.xnc.thickness = src.cs_material.thickness
                op.xnc.qty = max(1, calc.effective_qty(p, pt))
            if not op.name:
                op.name = pt.name
    return p
