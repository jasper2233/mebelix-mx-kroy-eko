"""OEE va ishlab chiqarish analitikasi API (W17). Hujjat (MES jamoasi uchun): docs/mebelix/T_W17_OEE.md.

Hodisalar (MES / sex rejimi / qo'lda):
  POST   /api/oee/events              bitta hodisa yoki `[...]` / `{"events": [...]}` (≤ 500); `external_id` bo'yicha idempotent
  GET    /api/oee/events              ro'yxat (machine, type, reason, from, to, limit, offset)
  GET/PATCH/DELETE /api/oee/events/{id}
  POST   /api/oee/downtime/start|stop, GET /api/oee/downtime/open     sex rejimi «To'xtash» (ochiq to'xtash)
Hisob-kitob:
  GET /api/oee/summary | /series | /downtime-pareto | /dashboard | /gaps     (machine, period | from+to, group_by)
  GET /api/oee/export.csv?kind=events|series|pareto
Sozlamalar (texnolog/administrator): /oee/config, /oee/machines (+ /catalog, /{key}/suggest), /oee/shifts (+ /preview), /oee/reasons.
Demo: POST/DELETE /api/oee/demo-seed — faqat `MEBELIX_DEMO=1` va ADMIN.
Rollar: yozish — «ko'ruvchi» emas hamma; sozlamalar — admin/texnolog (rolsiz token — to'liq huquq); demo — faqat admin.
"""
from __future__ import annotations

import csv
import io
from contextlib import contextmanager
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response

from .auth import canonical_roles, current_user
from .i18n import _
from .services import oee, oee_demo

router = APIRouter(prefix="/oee", tags=["oee"], dependencies=[Depends(lambda: oee.ensure_defaults())])


@contextmanager
def _errors():
    """OEE xatolarini HTTP ga o'giradi: topilmadi — 404, to'qnashuv — 409, noto'g'ri qiymat — 400."""
    try:
        yield
    except oee.OeeNotFound as e:
        raise HTTPException(404, str(e.args[0]) if e.args else _("oee_ev_not_found")) from e
    except oee.OeeConflict as e:
        raise HTTPException(409, str(e)) from e
    except oee.OeeError as e:
        raise HTTPException(400, str(e)) from e


def _writer(user: dict) -> None:
    if user.get("read_only"):
        raise HTTPException(403, _("forbidden_readonly"))


def _configurer(user: dict) -> None:
    """Sozlamalar (stanok, smena, sabab, konfiguratsiya): admin / texnolog; rolsiz (lokal yoki rolsiz token) — to'liq huquq."""
    _writer(user)
    roles = canonical_roles(user.get("roles") or [])
    if roles and not (roles & {"admin", "technologist"}):
        raise HTTPException(403, _("oee_forbidden_cfg"))


def _admin(user: dict) -> None:
    _writer(user)
    if "admin" not in canonical_roles(user.get("roles") or []):
        raise HTTPException(403, _("oee_forbidden_admin"))


def _name(user: dict) -> str:
    return str(user.get("name") or user.get("sub") or "")[:100]


def _range(frm: Optional[str], to: Optional[str], period: Optional[str]) -> tuple[float, float]:
    with _errors():
        return oee.resolve_range(frm, to, period, oee.get_config())


def _as_of(v: Optional[str]) -> Optional[float]:
    if not v:
        return None
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(v.strip())
    except ValueError as e:
        raise HTTPException(400, _("oee_range_bad")) from e
    if dt.tzinfo is None:
        raise HTTPException(400, _("oee_ev_naive"))
    return dt.timestamp()


# ───────────────────────── Sozlama ─────────────────────────
@router.get("/config")
def config_get():
    from .services import oee_calc as C
    return dict(config=oee.get_config().model_dump(), bands=dict(low=C.BAND_LOW, high=C.BAND_HIGH),
                groups=list(oee.GROUPS), periods=list(oee.PERIODS), kinds=list(oee.KINDS),
                demo_enabled=oee_demo.is_enabled(), max_batch=oee.MAX_BATCH)


@router.put("/config")
def config_put(body: dict = Body(...), user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return dict(config=oee.set_config(body).model_dump())


# ───────────────────────── Stanoklar ─────────────────────────
@router.get("/machines")
def machines_list(active_only: bool = False):
    return oee.list_machines(active_only)


@router.get("/machines/catalog")
def machines_catalog():
    """Postprotsessor stanoklari ro'yxati — OEE stanogi sifatida bog'lash uchun."""
    return oee.pp_catalog()


@router.post("/machines", status_code=201)
def machines_create(inp: oee.MachineIn, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return oee.create_machine(inp)


@router.get("/machines/{key}")
def machines_get(key: str):
    with _errors():
        return oee.get_machine(key)


@router.put("/machines/{key}")
@router.patch("/machines/{key}")
def machines_update(key: str, inp: oee.MachineIn, user: dict = Depends(current_user)):
    """Qisman yangilash (berilgan maydonlar). Tezlik maydonlariga `null` — standart qiymat; `ideal_unit_s: null` — o'chiriladi."""
    _configurer(user)
    with _errors():
        return oee.update_machine(key, inp, set(inp.model_fields_set))


@router.delete("/machines/{key}")
def machines_delete(key: str, force: bool = False, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return dict(ok=True, events_deleted=oee.delete_machine(key, force))


@router.get("/machines/{key}/suggest")
def machines_suggest(key: str):
    """Ideal tezlik taklifi: bog'langan postprotsessor stanogi sozlamasidan (masalan SCM `VelAvanz`)."""
    with _errors():
        m = oee.get_machine(key)
        if not m["pp_key"]:
            raise oee.OeeError(_("oee_pp_unknown", k="—"))
        return oee.suggest_from_pp(m["pp_key"])


# ───────────────────────── Smenalar ─────────────────────────
@router.get("/shifts")
def shifts_list():
    return oee.list_shifts()


@router.get("/shifts/preview")
def shifts_preview(machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
                   period: Optional[str] = None):
    """Kalendar nusxalari (smena boshi/oxiri UTC da, tanaffuslar, rejalashtirilgan daqiqa) — tanlangan davr uchun."""
    lo, hi = _range(frm, to, period or ("this_week" if not frm and not to else None))
    with _errors():
        return oee.preview_shifts(machine or None, lo, hi)


@router.post("/shifts", status_code=201)
def shifts_create(inp: oee.ShiftIn, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return oee.create_shift(inp)


@router.put("/shifts/{sid}")
def shifts_update(sid: int, inp: oee.ShiftIn, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return oee.update_shift(sid, inp)


@router.delete("/shifts/{sid}")
def shifts_delete(sid: int, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        oee.delete_shift(sid)
    return dict(ok=True)


# ───────────────────────── Sabablar ─────────────────────────
@router.get("/reasons")
def reasons_list(kind: Optional[str] = None, active_only: bool = False):
    return oee.list_reasons(kind, active_only)


@router.post("/reasons", status_code=201)
def reasons_create(inp: oee.ReasonIn, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return oee.create_reason(inp)


@router.put("/reasons/{code}")
@router.patch("/reasons/{code}")
def reasons_update(code: str, inp: oee.ReasonIn, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        return oee.update_reason(code, inp, set(inp.model_fields_set))


@router.delete("/reasons/{code}")
def reasons_delete(code: str, user: dict = Depends(current_user)):
    _configurer(user)
    with _errors():
        oee.delete_reason(code)
    return dict(ok=True)


# ───────────────────────── Hodisalar ─────────────────────────
def _items(body: Any) -> tuple[list[Any], bool]:
    """So'rov tanasi → (elementlar, bittami)."""
    if isinstance(body, list):
        return body, False
    if isinstance(body, dict) and isinstance(body.get("events"), list) and "type" not in body:
        return body["events"], False
    if isinstance(body, dict):
        return [body], True
    raise HTTPException(422, _("val_dict"))


@router.post("/events")
def events_post(response: Response, body: Any = Body(...), user: dict = Depends(current_user)):
    """Bitta hodisa (`{...}`) yoki ommaviy (`[...]` / `{"events": [...]}`, ≤ 500). Bitta hodisa: 201 (yaratildi) / 200
    (yangilandi, o'zgarmadi) + `{status, id, event}`; xato — 400. Ommaviy: `{created, updated, unchanged, errors, results[]}` —
    to'g'ri elementlar yoziladi, xatolari `results[i].error` da; hammasi xato bo'lsa — 422."""
    _writer(user)
    items, single = _items(body)
    if len(items) > oee.MAX_BATCH:
        raise HTTPException(400, _("oee_batch_limit", n=oee.MAX_BATCH))
    res = oee.ingest(items, _name(user), default_source="api")
    if single:
        r = res[0]
        if r["status"] == "error":
            raise HTTPException(409 if "external_id" in r.get("error", "") else 400, r["error"])
        response.status_code = 201 if r["status"] == "created" else 200
        return dict(status=r["status"], id=r["id"], event=oee.get_event(r["id"]))
    cnt = {k: sum(1 for r in res if r["status"] == k) for k in ("created", "updated", "unchanged", "error")}
    out = dict(created=cnt["created"], updated=cnt["updated"], unchanged=cnt["unchanged"], errors=cnt["error"], results=res)
    if items and cnt["error"] == len(items):
        response.status_code = 422
    return out


@router.get("/events")
def events_list(machine: Optional[str] = None, type: Optional[str] = None, reason: Optional[str] = None,
                source: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
                period: Optional[str] = None, limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
    lo = hi = None
    if frm or to or period:
        lo, hi = _range(frm, to, period)
    if type and type not in ("run", "downtime", "reject"):
        raise HTTPException(400, _("val_choice") + " (type: run | downtime | reject)")
    return oee.list_events(machine, type, lo, hi, reason, limit, offset, source)


@router.get("/events/{eid}")
def events_get(eid: int):
    with _errors():
        return oee.get_event(eid)


@router.patch("/events/{eid}")
def events_patch(eid: int, body: dict = Body(...), user: dict = Depends(current_user)):
    _writer(user)
    with _errors():
        return oee.patch_event(eid, body, _name(user))


@router.delete("/events/{eid}")
def events_delete(eid: int, user: dict = Depends(current_user)):
    _writer(user)
    with _errors():
        oee.delete_event(eid)
    return dict(ok=True)


# ───────────────────────── Sex rejimi: To'xtash ─────────────────────────
@router.get("/downtime/open")
def downtime_open(machine: str):
    return dict(machine=machine, open=oee.open_downtime(machine))


@router.post("/downtime/start", status_code=201)
def downtime_start(body: dict = Body(...), user: dict = Depends(current_user)):
    """Sex rejimi: ochiq to'xtash boshlash {machine, reason, note?}. Keyingi `stop` yoki ishlab chiqarish hodisasi yopadi."""
    _writer(user)
    with _errors():
        return oee.start_downtime(str(body.get("machine") or ""), str(body.get("reason") or ""), str(body.get("note") or ""),
                                  _name(user))


@router.post("/downtime/stop")
def downtime_stop(body: dict = Body(...), user: dict = Depends(current_user)):
    _writer(user)
    with _errors():
        return oee.stop_downtime(str(body.get("machine") or ""))


# ───────────────────────── Hisob-kitob ─────────────────────────
def _compute(machine, frm, to, period, group_by, as_of, also=()):
    lo, hi = _range(frm, to, period)
    with _errors():
        return oee.compute(machine or None, lo, hi, group_by, _as_of(as_of), also=tuple(also))


@router.get("/summary")
def summary(machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
            period: Optional[str] = None, as_of: Optional[str] = None):
    """A, P, Q, OEE, miqdorlar (ishlab chiqarilgan, brak, o'rtacha/ideal sikl), har stanok bo'yicha; `warnings`."""
    r = _compute(machine, frm, to, period, "day", as_of)
    return {k: r[k] for k in ("machine", "from", "to", "as_of", "config", "bands", "summary", "machines", "warnings")}


@router.get("/series")
def series(machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
           period: Optional[str] = None, group_by: str = "day", as_of: Optional[str] = None):
    """Trend: `group_by` = hour | shift | day | week; har bo'lakda A, P, Q, OEE va vaqt/miqdorlar."""
    r = _compute(machine, frm, to, period, group_by, as_of)
    return {k: r[k] for k in ("machine", "from", "to", "group_by", "bands", "series", "warnings")}


@router.get("/downtime-pareto")
def downtime_pareto(machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
                    period: Optional[str] = None, as_of: Optional[str] = None):
    """To'xtash sabablari bo'yicha daqiqa (kamayish tartibida, ulush va kumulyativ ulush); `idle` — hodisasiz bo'shliq."""
    r = _compute(machine, frm, to, period, "day", as_of)
    return {k: r[k] for k in ("machine", "from", "to", "pareto", "pareto_total_min", "planned_losses")}


@router.get("/dashboard")
def dashboard(machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None,
              period: Optional[str] = None, group_by: str = "day", as_of: Optional[str] = None):
    """Panel uchun hammasi bir so'rovda: summary + machines + series (group_by) + extra_series.shift + pareto + warnings."""
    return _compute(machine, frm, to, period, group_by, as_of, also=("shift",))


@router.get("/gaps")
def gaps(machine: str, frm: Optional[str] = Query(None, alias="from"), to: Optional[str] = None, period: Optional[str] = None,
         as_of: Optional[str] = None):
    """Hodisasiz bo'shliqlar (idle) — sabab belgilash uchun (to'xtash hodisasini yaratish)."""
    lo, hi = _range(frm, to, period)
    with _errors():
        return dict(machine=machine, items=oee.idle_gaps(machine, lo, hi, _as_of(as_of)))


# ───────────────────────── CSV ─────────────────────────
def _cell(v: Any) -> Any:
    """CSV in'ektsiyadan himoya (Excel formulasi): =, +, -, @ bilan boshlangan matn oldiga `'` qo'yiladi."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return "" if v is None else v


@router.get("/export.csv")
def export_csv(kind: str = "events", machine: Optional[str] = None, frm: Optional[str] = Query(None, alias="from"),
               to: Optional[str] = None, period: Optional[str] = None, group_by: str = "day", sep: str = ";",
               as_of: Optional[str] = None):
    """CSV (UTF-8 BOM, Excel uchun; ajratgich `sep` — `;` yoki `,`): kind = events | series | pareto."""
    if sep not in (";", ","):
        raise HTTPException(400, _("val_choice") + " (sep: ; ,)")
    lo, hi = _range(frm, to, period)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=sep, lineterminator="\r\n")
    if kind == "events":
        cols = ["id", "type", "machine", "start", "end", "qty", "reject_qty", "unit", "parts", "parts_per_sheet", "cut_length_m",
                "cuts", "sheets_per_pack", "ideal_cycle_s", "reason", "note", "project_number", "op_id", "map_index", "source",
                "external_id"]
        w.writerow(cols)
        got = oee.list_events(machine or None, None, lo, hi, None, 1000, 0)
        off = 0
        while True:
            for e in got["items"]:
                w.writerow([_cell(e[c]) for c in cols])
            off += len(got["items"])
            if off >= got["total"] or off >= 100_000 or not got["items"]:
                break
            got = oee.list_events(machine or None, None, lo, hi, None, 1000, off)
    elif kind in ("series", "pareto"):
        with _errors():
            r = oee.compute(machine or None, lo, hi, group_by, _as_of(as_of))
        if kind == "series":
            cols = ["label", "start", "end", "planned_min", "run_min", "stop_min", "availability", "performance", "quality",
                    "oee", "produced", "rejected", "avg_cycle_s", "ideal_cycle_s"]
            w.writerow(cols)
            for s in r["series"]:
                w.writerow([_cell(s.get(c)) for c in cols])
        else:
            cols = ["reason", "name_ru", "name_uz", "minutes", "count", "share", "cumulative"]
            w.writerow(cols)
            for p in r["pareto"]:
                w.writerow([_cell(p.get(c)) for c in cols])
    else:
        raise HTTPException(400, _("val_choice") + " (kind: events | series | pareto)")
    name = f"oee_{kind}_{(machine or 'all')}.csv"
    return Response(content="﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ───────────────────────── Demo ─────────────────────────
@router.post("/demo-seed")
def demo_seed(days: int = Query(14, ge=1, le=60), user: dict = Depends(current_user)):
    """2 sintetik stanok × `days` kun demo-hodisalar (ko'rsatish/test). Faqat `MEBELIX_DEMO=1` muhitida va ADMIN rolida;
    haqiqiy hodisalarga tegmaydi (faqat `source=demo` almashtiriladi)."""
    if not oee_demo.is_enabled():
        raise HTTPException(403, _("oee_demo_off"))
    _admin(user)
    return oee_demo.seed(days)


@router.delete("/demo-seed")
def demo_clear(user: dict = Depends(current_user)):
    if not oee_demo.is_enabled():
        raise HTTPException(403, _("oee_demo_off"))
    _admin(user)
    return oee_demo.clear()
