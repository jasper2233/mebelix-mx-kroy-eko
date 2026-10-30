"""Qo'shimcha API: qoldiqlar ombori, sozlamalar profillari, postprotsessorlar, MES integratsiyasi."""
from __future__ import annotations

import threading
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Query
from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from . import store
from .db import CatalogItemRow, RemnantMoveRow, RemnantRow, SessionLocal, text_search
from .i18n import _, cy
from .models import OpType, OrderStatus, PostprocessorProfile
from .services import labels, mes, remnant_rules, settings, warehouse
from .services.calc import total_qty
from .services.render import part_edges

router = APIRouter()


# ───────────────────────── Qoldiqlar ombori ─────────────────────────
_Size = Annotated[float, Field(allow_inf_nan=False, ge=0, le=100_000)]
_Qty = Annotated[int, Field(ge=0, le=1_000_000)]


class RemnantIn(BaseModel):
    material_code: str = Field(max_length=100)
    material_name: str = Field("", max_length=300)
    length: _Size
    width: _Size
    thickness: _Size = 16
    qty: _Qty = 1
    note: str = Field("", max_length=2000)
    linear: bool = False                 # (CL, W11) погонажный qoldiq: length — uzunlik, width — polosa eni
    # butun list o'lchami (foiz uchun; 2026-10-24) — qo'lda kiritilganda «% / m²» ko'rinadi
    sheet_length: Optional[_Size] = None
    sheet_width: Optional[_Size] = None


@router.get("/remnants", tags=["qoldiqlar"])
def remnants_list(material_code: Optional[str] = None, thickness: Optional[float] = None, q: str = "",
                  include_empty: bool = False, linear: Optional[bool] = None, status: Optional[str] = None):
    """`linear` — true: faqat погонажный (CL) qoldiqlar; false: faqat listli (CS); berilmasa — hammasi.
    `material_code` — katta-kichik harf va bo'shliqlarsiz solishtiriladi. Ro'yxatda «kutilmoqda» (arradan chiqmagan) qoldiqlar
    ham bor (`status` = pending, `qty` = 0) — ularni kroyga qo'shib bo'lmaydi. `status` — available | reserved | pending | empty.
    Ombor MES da bo'lsa (`remnant_rules.source = mes`) — ro'yxat MES bazasidan (faqat ko'rish)."""
    from .services import remnant_store
    if remnant_store.is_mes():
        out = remnant_store.list_all(material_code, linear)
        if not include_empty:
            out = [d for d in out if d["qty"] > 0 or d["qty_pending"] > 0]
        return [d for d in out if not status or d["status"] == status]
    with SessionLocal() as s:
        st = select(RemnantRow)
        if linear is not None:
            st = st.where(RemnantRow.linear == linear)
        if thickness is not None:
            st = st.where(RemnantRow.thickness == thickness)
        cond = text_search(q, RemnantRow.material_code, RemnantRow.material_name, RemnantRow.note)
        if cond is not None:             # Unicode katta-kichik harfga sezgirsiz (kirill ham), %/_ wildcard emas
            st = st.where(cond)
        if not include_empty:
            st = st.where(or_(RemnantRow.qty > 0, RemnantRow.qty_pending > 0))
        rows = s.scalars(st.order_by(RemnantRow.material_code, RemnantRow.length.desc())).all()
        if material_code:
            key = remnant_rules.norm(material_code)
            rows = [r for r in rows if remnant_rules.norm(r.material_code) == key]
        out = warehouse.annotate_reservations([warehouse.row_dict(r) for r in rows])   # + reserved_project / reserved_number
        if status:
            out = [d for d in out if d["status"] == status]
        return out


@router.post("/remnants", tags=["qoldiqlar"])
def remnants_add(r: RemnantIn):
    if r.length <= 0 or r.width <= 0 or r.qty <= 0:
        raise HTTPException(400, _("remnant_positive"))
    d = r.model_dump()
    sl, sw = d.pop("sheet_length", None), d.pop("sheet_width", None)
    with SessionLocal() as s:
        row = RemnantRow(**d, sheet_area_m2=round(sl * sw / 1e6, 4) if sl and sw else None, qty_released=r.qty)
        s.add(row)
        s.flush()
        warehouse.log_move(s, "qolda", row=row, qty=row.qty, note=_("rm_manual_add"))
        s.commit()
        out = warehouse.row_dict(row)
    warehouse.kick()
    return out


class RemnantPatch(BaseModel):
    material_code: Optional[str] = Field(None, max_length=100)
    material_name: Optional[str] = Field(None, max_length=300)
    length: Optional[_Size] = None
    width: Optional[_Size] = None
    thickness: Optional[_Size] = None
    qty: Optional[_Qty] = None
    note: Optional[str] = Field(None, max_length=2000)
    linear: Optional[bool] = None
    sheet_area_m2: Optional[float] = Field(None, ge=0, le=400)


@router.patch("/remnants/{rid}", tags=["qoldiqlar"])
def remnants_patch(rid: int, f: RemnantPatch):
    upd = f.model_dump(exclude_unset=True, exclude_none=True)
    if any(upd.get(k, 1) <= 0 for k in ("length", "width")) or upd.get("qty", 0) < 0 \
            or upd.get("thickness", 1) < 0:
        raise HTTPException(400, _("remnant_positive"))
    with SessionLocal() as s:
        row = s.get(RemnantRow, rid)
        if row is None:
            raise HTTPException(404, _("remnant_not_found"))
        before = {k: getattr(row, k) for k in upd}
        for k, v in upd.items():
            setattr(row, k, v)
        diff = ", ".join(f"{k}: {before[k]} → {v}" for k, v in upd.items() if before[k] != v)
        if diff:
            warehouse.log_move(s, "qolda", row=row, qty=row.qty or 0, note=f"{_('rm_manual_edit')}: {diff}")
        s.commit()
        out = warehouse.row_dict(row)
    if diff:
        warehouse.kick()
    return out


@router.delete("/remnants/{rid}", tags=["qoldiqlar"])
def remnants_delete(rid: int):
    with SessionLocal() as s:
        row = s.get(RemnantRow, rid)
        if row is None:
            raise HTTPException(404, _("remnant_not_found"))
        warehouse.log_move(s, "qolda", row=row, qty=(row.qty or 0) + (row.qty_pending or 0), note=_("rm_manual_del"))
        s.delete(row)
        s.commit()
    warehouse.kick()
    return {"ok": True}


@router.get("/remnants/moves", tags=["qoldiqlar"])
def remnants_moves(remnant_id: Optional[int] = None, project_id: Optional[str] = None, kind: Optional[str] = None,
                   limit: int = Query(300, ge=1, le=5000)):
    """Kirim-chiqim jurnali (yangisi birinchi). kind: kutish · kirim · chiqim · qaytish · bekor · rezerv · rezerv_bekor · mijozga · qolda."""
    with SessionLocal() as s:
        st = select(RemnantMoveRow)
        if remnant_id is not None:
            st = st.where(RemnantMoveRow.remnant_id == remnant_id)
        if project_id:
            st = st.where(RemnantMoveRow.project_id == project_id)
        if kind:
            st = st.where(RemnantMoveRow.kind == kind)
        rows = s.scalars(st.order_by(RemnantMoveRow.id.desc()).limit(limit)).all()
        return [warehouse.move_dict(m) for m in rows]


@router.get("/remnants/summary", tags=["qoldiqlar"])
def remnants_summary():
    """«Настройки → Правила остатков»: material turlari va materiallar — qoida foizi, ombordagi jami (soni, m², butun list
    foizida), kutilayotgani. Turlar: qoidalardagi + ombordagi + doimiy ro'yxat (LDSP, LMDF, MDF, HDF, XDF, AKRIL)."""
    rules = remnant_rules.load()
    with SessionLocal() as s:
        rows = s.scalars(select(RemnantRow).where(RemnantRow.linear == False,                       # noqa: E712
                                                  or_(RemnantRow.qty > 0, RemnantRow.qty_pending > 0))).all()
    types: dict[str, dict] = {}
    mats: dict[str, dict] = {}

    def tslot(t: str) -> dict:
        return types.setdefault(t, dict(type=t, keep_percent=None, count=0, pending=0, area_m2=0.0, sheets=0.0))

    for t in remnant_rules.COMMON_TYPES:
        tslot(t)
    for r in rules.types:
        tslot(r.type)["keep_percent"] = r.keep_percent
    for r in rows:
        t = remnant_rules.material_type(r.material_code, r.material_name)
        a = (r.length or 0) * (r.width or 0) / 1e6
        n, pnd = int(r.qty or 0), int(r.qty_pending or 0)
        sh = r.sheet_area_m2 or 0
        k = remnant_rules.norm(r.material_code)
        m = mats.setdefault(k, dict(material=r.material_name or r.material_code or "", code=r.material_code or "", type=t,
                                    count=0, pending=0, area_m2=0.0, sheets=0.0, sheet_m2=sh or None))
        for g in (tslot(t) if t else None, m):
            if g is None:
                continue
            g["count"] += n
            g["pending"] += pnd
            g["area_m2"] += a * n
            if sh:
                g["sheets"] += a * n / sh
    for m in mats.values():
        rr = remnant_rules.rule_for(m["code"], m["material"], rules)
        m["keep_percent"], m["rule_source"] = (rr if rr else (None, None))
    for g in list(types.values()) + list(mats.values()):
        g["area_m2"] = round(g["area_m2"], 3)
        g["percent_total"] = round(g["sheets"] * 100, 1)       # ombordagi jami — butun list foizida (230 % = 2.3 list)
        g.pop("sheets")
    return dict(types=sorted(types.values(), key=lambda g: (g["keep_percent"] is None, g["type"])),
                materials=sorted(mats.values(), key=lambda g: (g["type"], g["material"])),
                material_rules=[r.model_dump() for r in rules.materials], wait_mes=rules.wait_mes, auto_commit=rules.auto_commit)


@router.get("/mes/remnants", tags=["MES"])
def mes_remnants(status: Optional[str] = None, since_id: int = 0):
    """MES uchun: ombordagi listli va погонажный qoldiqlar holati bilan (available / reserved / pending / empty) va jurnal
    (`since_id` dan keyingi harakatlar) — MES o'z bazasini shu bilan sinxronlaydi (MES_QOLDIQ_V1.md)."""
    with SessionLocal() as s:
        rows = s.scalars(select(RemnantRow).order_by(RemnantRow.id)).all()
        moves = s.scalars(select(RemnantMoveRow).where(RemnantMoveRow.id > since_id).order_by(RemnantMoveRow.id).limit(5000)).all()
        out = [warehouse.row_dict(r) for r in rows]
        if status:
            out = [d for d in out if d["status"] == status]
        return dict(remnants=out, moves=[warehouse.move_dict(m) for m in moves])


@router.post("/mes/remnants/resend", tags=["MES"])
def mes_remnants_resend():
    """Yuborilmagan qoldiq harakatlarini MES ga hozir yuborish (navbat)."""
    from .services import remnant_outbox
    return remnant_outbox.flush()


# ───────────────────────── Sozlamalar profillari ─────────────────────────
class ProfileIn(BaseModel):
    name: str
    data: Any = None
    is_default: bool = False


class ProfilePatch(BaseModel):
    name: Optional[str] = None
    data: Any = None
    is_default: Optional[bool] = None


def _scope(scope: str) -> str:
    if scope not in settings.SCOPES:
        raise HTTPException(404, _("unknown_scope", s=scope))
    return scope


def _scope_w(scope: str) -> str:
    """Yozish uchun: «Раскроечные станки» faqat /saw-machines orqali (login paroli bilan)."""
    if scope == "saw_machines":
        raise HTTPException(403, _("password_wrong"))
    return _scope(scope)


@router.get("/settings", tags=["sozlamalar"])
def settings_scopes():
    return {s: settings.builtin(s) for s in settings.SCOPES}


@router.get("/settings/{scope}/default", tags=["sozlamalar"])
def settings_get_default(scope: str):
    return settings.get_default(_scope(scope))


@router.put("/settings/{scope}/default", tags=["sozlamalar"])
def settings_set_default(scope: str, data: Any = Body(...)):
    """«Joriy parametrlarni standart sifatida saqlash»."""
    return settings.set_default(_scope_w(scope), data)


@router.get("/settings/{scope}", tags=["sozlamalar"])
def settings_list(scope: str):
    return settings.list_profiles(_scope(scope))


def _profile_name(name: str) -> str:
    """Profil nomi: bo'sh bo'lmasin (ro'yxatda ko'rinmas element), ≤ 100 belgi."""
    name = (name or "").strip()
    if not name:
        raise HTTPException(400, _("profile_name_empty"))
    if len(name) > 100:
        raise HTTPException(400, _("val_text_long", f="name", n=100))
    return name


@router.post("/settings/{scope}", tags=["sozlamalar"])
def settings_create(scope: str, inp: ProfileIn, upsert: bool = False):
    """Profil yaratish. `upsert=true` — shu `scope` da bir xil nomli profil bor bo'lsa yangi qator yaratilmaydi,
    mavjudi yangilanadi (zaxirani qayta import qilish dublikat bermasin)."""
    scope = _scope_w(scope)
    name = _profile_name(inp.name)
    data = inp.data if inp.data is not None else settings.builtin(scope)
    if upsert:
        ex = settings.find_by_name(scope, name)
        if ex is not None:
            return settings.update(scope, ex["id"], None, data, True if inp.is_default else None)
    return settings.create(scope, name, data, inp.is_default)


@router.put("/settings/{scope}/{pid}", tags=["sozlamalar"])
def settings_update(scope: str, pid: int, inp: ProfilePatch):
    name = _profile_name(inp.name) if inp.name is not None else None
    try:
        return settings.update(_scope_w(scope), pid, name, inp.data, inp.is_default)
    except KeyError as e:
        raise HTTPException(404, _("profile_not_found")) from e


@router.delete("/settings/{scope}/{pid}", tags=["sozlamalar"])
def settings_delete(scope: str, pid: int):
    try:
        settings.delete(_scope_w(scope), pid)
    except KeyError as e:
        raise HTTPException(404, _("profile_not_found")) from e
    return {"ok": True}


# Profillar zaxirasi: `{app, version, profiles: {scope: [{name, data, is_default}]}}`
@router.get("/backup/settings", tags=["sozlamalar"])
def backup_export():
    return {"app": "MebeliX Kroy", "version": 1, "profiles": {s: settings.list_profiles(s) for s in settings.SCOPES}}


@router.post("/backup/settings/import", tags=["sozlamalar"])
def backup_import(body: Any = Body(...), mode: str = "update"):
    """Zaxira faylidan profillarni tiklash. Bir xil `scope` + `name` — dublikat yaratilmaydi: `mode=update` (standart)
    mavjudini yangilaydi, `mode=skip` o'tkazib yuboradi. Fayl noto'g'ri (profillar yo'q) bo'lsa — 400.
    Javob: {created, updated, skipped, invalid: [{scope, name, error}], total}."""
    profs = body.get("profiles") if isinstance(body, dict) else None
    if not isinstance(profs, dict) or not any(isinstance(profs.get(s), list) for s in settings.SCOPES):
        raise HTTPException(400, _("backup_bad"))
    if mode not in ("update", "skip"):
        raise HTTPException(400, _("val_choice") + " (mode: update | skip)")
    out = dict(created=0, updated=0, skipped=0, invalid=[], total=0)
    for scope in settings.SCOPES:
        items = profs.get(scope)
        if not isinstance(items, list):
            continue
        for it in items:
            out["total"] += 1
            nm = str(it.get("name") or "").strip()[:100] if isinstance(it, dict) else ""
            if not isinstance(it, dict) or not nm:
                out["invalid"].append(dict(scope=scope, name=nm, error=_("profile_name_empty")))
                continue
            try:
                ex = settings.find_by_name(scope, nm)
                data = it.get("data") if it.get("data") is not None else settings.builtin(scope)
                if ex is None:
                    settings.create(scope, nm, data, bool(it.get("is_default")))
                    out["created"] += 1
                elif mode == "skip":
                    out["skipped"] += 1
                else:
                    settings.update(scope, ex["id"], None, data, True if it.get("is_default") else None)
                    out["updated"] += 1
            except settings.SettingsError as e:
                out["invalid"].append(dict(scope=scope, name=nm, error=str(e)))
    return out


# ───────────────────────── Postprotsessorlar ─────────────────────────
def _machine_cfg() -> dict:
    """Stanoklar sozlamasi: yoqilgan stanoklar, ularga biriktirilgan shablon profillari, fayl nomi prefiksi."""
    d = settings.get_default("pp_machines") or {}
    return dict(enabled={k: bool(v) for k, v in (d.get("enabled") or {}).items() if v},
                profile={k: v for k, v in (d.get("profile") or {}).items() if v is not None},
                prefix=bool(d.get("prefix", False)))


@router.get("/postprocessors", tags=["postprotsessor"])
def postprocessors_list():
    from .services.postprocessors import BUILTIN, MACHINES, pp_label, pp_order
    from .i18n import LANG
    from .services import pp_access
    shut = pp_access.closed_extras()                # admin yopgan MebeliX formatlari / shablonlar — opened=false (xira)
    out = [dict(key=k, name=_(f"pp_builtin_{k}"), extension=v["extension"], builtin=True, opened=f"mx:{k}" not in shut)
           for k, v in BUILTIN.items()]
    for pr in settings.list_profiles("postprocessor"):
        d = pr["data"]
        out.append(dict(key=f"pp:{pr['id']}", profile_id=pr["id"], name=pr["name"] or d.get("name", ""),
                        extension=d.get("extension", "txt"), builtin=False, opened=f"pp:{pr['id']}" not in shut))
    # yoqilgan saw-stanoklar: shablon biriktirilgan bo'lsa ishlaydi, aks holda ro'yxatda xira (available=false)
    cfg = _machine_cfg()
    profiles = {p["id"]: p for p in settings.list_profiles("postprocessor")}
    from .services import ppfmt, pp_access
    native = ppfmt.load_all()
    opened = pp_access.open_keys()
    for key, name, grp in MACHINES:
        if grp not in ("saw", "nest"):              # nest — (CN) nesting ishlov markazlari (faqat o'rnatilgan formatlar)
            continue
        nat = native.get(key)
        has_native = nat is not None and nat.group == grp
        is_open = key in opened
        # (2026-10-18) guruhdagi hamma stanok nomi bilan ro'yxatda: mijoz uchun ochilmagani — opened=false (xira, bosilmaydi);
        # ochilgan: o'rnatilgan format (namunalardan) yoki yoqilgan stanok + shablon — ishlaydi, aks holda available=false
        bound = cfg["profile"].get(key)
        pr = profiles.get(bound) if bound is not None else None
        works = bool(pr) and bool(cfg["enabled"].get(key)) if bound is not None else has_native   # main.postprocess qoidasi
        ext = pr["data"].get("extension", "txt") if pr else (nat.ext if has_native else "")
        out.append(dict(key=f"machine:{key}", name=name, extension=ext, builtin=False, machine=True, group=grp,
                        available=is_open and works, native=has_native and not pr, opened=is_open,
                        note=nat.note if has_native and not pr else "",
                        label=pp_label(key, LANG.get()), order=pp_order(key)))
    head = [x for x in out if not x.get("machine")]
    return head + sorted((x for x in out if x.get("machine")), key=lambda x: x["order"])


@router.get("/postprocessors/machines", tags=["postprotsessor"])
def machines_get():
    """«Настройки → Постпроцессоры → Станки»: stanok nomlari ro'yxati (pil markazlari va ishlov markazlari), har biri
    uchun yoqilganligi va biriktirilgan format shabloni (profil). Formatning o'zi korxona dasturchilari tomonidan yoziladi."""
    from .services.postprocessors import MACHINES
    cfg = _machine_cfg()
    profiles = {p["id"]: p for p in settings.list_profiles("postprocessor")}
    from .services import ppfmt, pp_access
    native = ppfmt.load_all()
    opened = pp_access.open_keys()
    groups: dict[str, list] = {"saw": [], "cnc": [], "nest": []}
    for key, name, grp in MACHINES:
        pid = cfg["profile"].get(key)
        pr = profiles.get(pid) if pid is not None else None
        nat = native.get(key)
        groups[grp].append(dict(key=key, name=name, group=grp, enabled=bool(cfg["enabled"].get(key)),
                                opened=key in opened,          # mijoz uchun ochilgan (admin; services/pp_access.py)
                                profile_id=pr["id"] if pr else None, profile_name=pr["name"] if pr else None,
                                bound=bool(pr), native=bool(nat and nat.group == grp),
                                native_ext=nat.ext if nat else "", native_note=cy(nat.note) if nat else ""))
    return dict(prefix=cfg["prefix"], groups=[dict(key=g, machines=m) for g, m in groups.items()])


class MachinesIn(BaseModel):
    enabled: dict[str, bool] = {}
    profile: dict[str, Optional[int]] = {}
    prefix: bool = False


@router.put("/postprocessors/machines", tags=["postprotsessor"])
def machines_put(inp: MachinesIn):
    from .services.postprocessors import MACHINE_BY_KEY
    bad = [k for k in list(inp.enabled) + list(inp.profile) if k not in MACHINE_BY_KEY]
    if bad:
        raise HTTPException(400, _("pp_machine_unknown", k=", ".join(bad)))
    ids = {p["id"] for p in settings.list_profiles("postprocessor")}
    if any(v is not None and v not in ids for v in inp.profile.values()):
        raise HTTPException(404, _("pp_not_found"))
    cur = settings.get_default("pp_machines") or {}
    keep = {k: cur[k] for k in ("params", "label_fields") if k in cur}      # W7: stanok sozlamalari/etiketka maydonlari saqlansin
    settings.set_default("pp_machines", dict(enabled={k: v for k, v in inp.enabled.items() if v},
                                            profile={k: v for k, v in inp.profile.items() if v is not None},
                                            prefix=inp.prefix, **keep))
    return machines_get()


class PreviewIn(BaseModel):
    project_id: str
    op_id: str
    profile: PostprocessorProfile
    max_chars: int = 20000
    machine: Optional[str] = None          # W7: stanok kaliti — kontekstga `machine` va hisoblangan `label` lar qo'shiladi


@router.post("/postprocessors/preview", tags=["postprotsessor"])
def postprocessor_preview(inp: PreviewIn):
    """Shablon muharririda jonli ko'rish: birinchi fayl matni (yoki xato)."""
    from .services.postprocessors import context, render_limited
    from .services.tpl_sandbox import TemplateFailed, TemplateLimit
    p = store.load(inp.project_id)
    op = store.op_of(p, inp.op_id)
    if op.type != OpType.CS or not op.result or not op.result.maps:
        raise HTTPException(400, _("pp_sample"))
    if inp.machine:
        from .services.postprocessors import MACHINE_BY_KEY
        if inp.machine not in MACHINE_BY_KEY:
            raise HTTPException(400, _("pp_machine_unknown", k=inp.machine[:60]))
    ctx = context(p, op, inp.machine or None)
    limit = max(1000, min(inp.max_chars, 200_000))
    try:
        text = render_limited(inp.profile.template, {**ctx, "map": ctx["maps"][0]} if inp.profile.per_map else ctx)
    except TemplateLimit as e:
        return {"ok": False, "error": _("template_limit", e=e)}
    except TemplateFailed as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:  # noqa: BLE001 — shablon xatosi foydalanuvchiga (sintaksis, sandbox)
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "text": text[:limit], "truncated": len(text) > limit,
            "files": len(ctx["maps"]) if inp.profile.per_map else 1}


# ───────────────────────── MES integratsiyasi ─────────────────────────
_mes_lock = threading.Lock()


@router.post("/mes/orders", tags=["mes"])
def mes_order(order: mes.MesOrder, background: BackgroundTasks, folder_id: Optional[str] = None):
    """MES buyurtmasini qabul qilish: loyiha yaratiladi (yoki hali tasdiqlanmagan bo'lsa yangilanadi)."""
    # bir xil buyurtma parallel kelsa (hatto boshqa ilova jarayoniga) — ikki loyiha yaratilmasin: jarayonlararo qulf
    from . import store as _store, tenant as _tenant
    with _mes_lock, _store._lock(f"mes-intake:{_tenant.current()}"):
        return _mes_order(order, background, folder_id)


def _mes_order(order: mes.MesOrder, background: BackgroundTasks, folder_id: Optional[str]):
    with SessionLocal() as s:
        cat = {}
        codes = {pt.material_code for pr in order.products for pt in pr.parts} | \
                {c for pr in order.products for pt in pr.parts for c in pt.edges.values() if c}
        if codes:
            for r in s.scalars(select(CatalogItemRow).where(CatalogItemRow.code.in_(codes))).all():
                cat[r.code] = dict(id=r.id, name=r.name, price=r.price, thickness=r.thickness, length=r.length,
                                   width=r.width, params=r.params or {})
    from .services.saw_machines import effective_cs_defaults
    cs_def = effective_cs_defaults()               # material standarti + stanok parametrlari
    el_def = settings.get_default("el_defaults")
    old = store.find_by_mes_ref(order.mes_order_ref)
    if old is not None and old.status >= OrderStatus.APPROVED:
        raise HTTPException(409, _("order_approved", ref=order.mes_order_ref, n=old.number))
    if old is None:
        store.require_folder(folder_id)
        p = mes.build_project(order, cat, store.next_number(), cs_def, el_def)
        p.folder_id = folder_id or None
        p.owner = "MES"
        store.save_new(p)
        event = "project.created"
    else:
        # qayta yuborish: lokal ish (holat, o'lcham rejimi, izoh, XNC/GR/EL tahrirlari, id/raqam) saqlanadi,
        # MES ga tegishli maydonlar yangilanadi — bitta tarix qadami
        new = mes.build_project(order, cat, old.number, cs_def, el_def)
        with store.editing(old.id) as p:
            if p.status >= OrderStatus.APPROVED:                  # poyga: shu orada tasdiqlangan
                raise HTTPException(409, _("order_approved", ref=order.mes_order_ref, n=p.number))
            mes.merge_order(p, new, order, cat)
        event = "project.updated"
    background.add_task(mes.send_webhook, event,
                        dict(project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref))
    return p


@router.get("/mes/orders/{ref:path}", tags=["mes"])
def mes_order_get(ref: str):
    from .services import pp_access
    pp_access.require_extra("mx:mes_export")        # MES natijasi (JSON) — admin yopgan bo'lsa 403
    p = store.find_by_mes_ref(ref)
    if p is None:
        raise HTTPException(404, _("order_not_found"))
    return mes.export(p)


@router.get("/projects/{pid}/mes-export", tags=["mes"])
def mes_export(pid: str):
    from .services import pp_access
    pp_access.require_extra("mx:mes_export")        # MES natijasi (JSON) — admin yopgan bo'lsa 403
    return mes.export(store.load(pid))


def _scan(code: str) -> tuple[dict, Any]:
    info = labels.parse_qr(code)
    if info is None:
        raise HTTPException(400, _("qr_bad"))
    p = store.find_by_number(info["number"])
    if p is None:
        raise HTTPException(404, _("project_no_n", n=info["number"]))
    return info, p


@router.get("/mes/scan/{code:path}", tags=["mes"])
def mes_scan(code: str):
    """Etiketka yoki karta QR kodi bo'yicha ma'lumot (sex planshetlari / MES skaneri uchun)."""
    info, p = _scan(code)
    head = dict(project_id=p.id, number=p.number, name=p.name, customer=p.customer, mes_order_ref=p.mes_order_ref,
                status=int(p.status))
    if info["kind"] == "part":
        for op in p.operations:
            for pt in op.parts:
                if pt.uid == info["uid"]:
                    prod = next((x for x in p.products if x.id == pt.product_id), None)
                    maps = []
                    if op.result:
                        maps = [m.index for m in op.result.maps if any(pl.part_id == pt.id for pl in m.placements)]
                    return dict(kind="part", project=head, copy=info["copy"], total=info["total"],
                                part=dict(id=pt.id, uid=pt.uid, name=pt.name, code=pt.code, length=pt.length,
                                          width=op.cl.width if (op.type == OpType.CL and op.cl) else pt.width,     # CL: eni = polosa eni
                                          qty=total_qty(p, pt), grain=pt.grain,
                                          thickness=(op.cs_material.thickness if op.cs_material
                                                     else (op.cl.thickness if (op.type == OpType.CL and op.cl) else None)),
                                          edges={k: v["name"] for k, v in part_edges(pt, p).items()},
                                          xnc=[o.code for o in p.operations if o.id in pt.xnc_op_ids]),
                                material=dict(op_id=op.id, name=op.name, code=op.code),
                                product=dict(id=prod.id, name=prod.name, code=prod.code) if prod else None,
                                maps=maps)
        raise HTTPException(404, _("part_uid_not_found", uid=info["uid"]))
    op = next((o for o in p.operations if o.id == info["op_id"]), None)
    if op is None or not op.result or not (1 <= info["map"] <= len(op.result.maps)):
        raise HTTPException(404, _("no_map"))
    m = op.result.maps[info["map"] - 1]
    parts = {pt.id: pt for pt in op.parts}
    return dict(kind="map", project=head, material=dict(op_id=op.id, name=op.name, code=op.code),
                map=dict(index=m.index, copies=m.copies, done=m.done_count, sheet=[m.sheet_length, m.sheet_width],
                         fill=m.fill_percent, cut_length_m=m.cut_length_m, comment=m.comment,
                         parts=[dict(uid=pl.part_uid, name=parts[pl.part_id].name if pl.part_id in parts else "",
                                     length=pl.length, width=pl.width) for pl in m.placements]))


@router.post("/mes/scan/{code:path}/done", tags=["mes"])
def mes_scan_done(code: str, background: BackgroundTasks, count: int = 1, machine: Optional[str] = None):
    """Karta QR kodi skanerlandi — shu kartadan kesilgan listlar soni +count (MES kuzatuvi). `machine` — OEE stanogi kaliti
    (ixtiyoriy; berilmasa yagona faol «saw» stanogi): shunda OEE `run` hodisasi yoziladi (W17)."""
    info, p = _scan(code)
    if info["kind"] != "map":
        raise HTTPException(400, _("scan_map_needed"))
    with store.editing(p.id, history=False) as pp:
        op = next((o for o in pp.operations if o.id == info["op_id"]), None)
        if op is None or not op.result or not (1 <= info["map"] <= len(op.result.maps)):
            raise HTTPException(404, _("no_map"))
        m = op.result.maps[info["map"] - 1]
        before = m.done_count
        m.done_count = max(0, min(m.copies, m.done_count + count))
        done, copies = m.done_count, m.copies
        oee_geo = dict(project_number=pp.number, project_id=pp.id, op_id=op.id, map_index=m.index,
                       cut_length_m=m.cut_length_m, cuts=m.cuts_count, parts_per_sheet=m.parts_count,
                       sheets_per_pack=op.result.sheets_per_pack or 1, sheet_area_m2=m.sheet_area_m2 or None,
                       parts_area_m2=m.parts_area_m2, remnant_area_m2=m.remnant_area_m2)
        oee_delta = m.done_count - before
    try:                                    # OEE (W17): kesilgan list hodisasi — ixtiyoriy; xatosi skanerni buzmaydi
        from .services import oee
        oee.record_sheet_done(machine, oee_delta, oee_geo, "workshop")
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger("mebelix.oee").exception("OEE hodisasi yozilmadi")
    background.add_task(mes.send_webhook, "map.done", dict(project_id=pp.id, number=pp.number,
                                                           mes_order_ref=pp.mes_order_ref, op_id=info["op_id"],
                                                           map=info["map"], done=done, copies=copies))
    released = warehouse.on_map_done(pp, op, info["map"], done)     # olib qolingan qoldiqlar «mavjud» (2026-10-24)
    return dict(map=info["map"], done=done, copies=copies, remnants_released=released)


def _mask_url(url: str) -> str:
    """URL dagi `login:parol@` qismini yashiradi (javobda ko'rinmasin)."""
    import re
    return re.sub(r"//[^/@]*@", "//***@", url)


@router.post("/mes/webhook-test", tags=["mes"])
def mes_webhook_test():
    """Webhookni sinash (bitta urinish). `sent` — faqat server 2xx/3xx javob bersa true; xatoda `status` (HTTP kodi),
    `error` (matn), `reason` (foydalanuvchi tilida sabab) va `elapsed_ms` qaytadi."""
    import os
    url = os.getenv("MES_WEBHOOK_URL")
    if not url:
        return {"sent": False, "url": None, "status": None, "error": None, "elapsed_ms": 0, "attempts": 0,
                "reason": _("webhook_no_url")}
    res = mes.send_webhook("test", {"message": "MebeliX Kroy webhook sinovi"}, attempts=1)
    reason = None
    if not res["sent"]:
        reason = _("webhook_http_error", status=res["status"]) if res.get("status") \
            else _("webhook_conn_error", e=res.get("error"))
    return {"sent": res["sent"], "url": _mask_url(url), "status": res.get("status"), "error": res.get("error"),
            "elapsed_ms": res.get("elapsed_ms", 0), "attempts": res.get("attempts", 1), "reason": reason}
