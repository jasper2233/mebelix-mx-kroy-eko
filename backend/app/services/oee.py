"""OEE va ishlab chiqarish analitikasi (W17): ma'lumot modeli (DB), hodisalarni qabul qilish, hisoblash fasadi.

Hisoblash yadrosi — `oee_calc.py` (bazasiz, formulalar shu yerda tavsiflangan); bu modul:
  · sozlamalar (`oee_config`: tz_offset_min, idle_gap_s, run_cap_factor, unit, include_overtime) va boshlang'ich ma'lumot;
  · stanoklar (`oee_machines`), smena kalendari (`oee_shifts`), sabablar (`oee_reasons`) CRUD yordamchilari;
  · hodisalar (`oee_events`): tekshirish, `external_id` bo'yicha idempotent yozish (yaratish/yangilash), so'rov;
  · `compute(...)` — A, P, Q, OEE, qatorlar (soat/smena/kun/hafta), to'xtash Pareto;
  · sex rejimi: `record_sheet_done`, `start_downtime` / `stop_downtime`.
Hujjat (MES jamoasi uchun): docs/mebelix/T_W17_OEE.md. Vaqtlar — UTC; smena soatlari — zavod mahalliy vaqti (qat'iy siljish).
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from .. import tenant
from ..db import (OeeConfigRow, OeeEventRow, OeeMachineRow, OeeReasonRow, OeeShiftRow, SessionLocal)
from ..i18n import _, format_errors
from . import oee_calc as C

log = logging.getLogger("mebelix.oee")

MAX_BATCH = 500                      # bitta so'rovdagi hodisalar
MAX_RANGE_DAYS = 400                 # hisobot oralig'i
MAX_HOUR_DAYS = 31                   # soat bo'yicha guruhlash uchun eng uzun oraliq (kun)
LOOKBACK_S = 2 * 86400               # oyna oldidagi hodisalar (boshlanishi noma'lum `run` va bo'shliqlarni aniqlash uchun)
MAX_DOWN_S = 31 * 86400              # bitta to'xtashning eng uzun davomiyligi (tekshiruv)
FUTURE_SKEW_S = 86400                # kelajakdagi hodisa chegarasi (soat farqi uchun zaxira)
SCM_FEED_IS_M_MIN = True             # SCM `VelAvanz` birligi — m/min deb taxmin qilinadi (savol: U_OCHIQ_SAVOLLAR)
SOURCES_FREE = re.compile(r"^[a-z0-9_-]{1,20}$")
KEY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
CODE_RE = re.compile(r"^[a-z0-9_]{1,32}$")
HHMM_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
KINDS = ("saw", "edge", "cnc", "other")
GROUPS = ("hour", "shift", "day", "week")
PERIODS = ("today", "yesterday", "last7", "last14", "last30", "this_week", "this_month")
RESERVED_REASONS = {C.IDLE}

IDLE_NAMES = ("Простой без событий (причина не указана)", "Hodisasiz bo'shliq (sabab ko'rsatilmagan)")

# boshlang'ich sabablar: (kod, ru, uz, kind, planned, sort)
DEFAULT_REASONS: list[tuple[str, str, str, str, bool, int]] = [
    ("setup", "Наладка", "Sozlash", "downtime", False, 10),
    ("breakdown", "Поломка", "Nosozlik", "downtime", False, 20),
    ("material_wait", "Ожидание материала", "Material kutish", "downtime", False, 30),
    ("no_operator", "Нет оператора", "Operator yo'q", "downtime", False, 40),
    ("no_work", "Нет заказов", "Buyurtma (ish) yo'q", "downtime", False, 50),
    ("tool_change", "Замена пилы / инструмента", "Arra / asbob almashtirish", "downtime", False, 60),
    ("cleaning", "Уборка", "Tozalash", "downtime", False, 70),
    ("maintenance", "Плановое обслуживание", "Rejali texnik xizmat", "downtime", True, 80),
    ("break", "Перерыв", "Tanaffus", "downtime", True, 90),
    ("other", "Прочее", "Boshqa", "downtime", False, 100),
    ("chip", "Скол / выкрашивание", "Yorilish / chetning ko'chishi", "reject", False, 110),
    ("size", "Неверный размер", "O'lcham xato", "reject", False, 120),
    ("mat_defect", "Дефект материала", "Material nuqsoni", "reject", False, 130),
    ("damage", "Повреждение при обработке", "Ishlov paytida shikastlanish", "reject", False, 140),
    ("reject_other", "Прочее (брак)", "Boshqa (brak)", "reject", False, 150),
]
DEFAULT_SHIFT = dict(kind="shift", machine_key=None, name="Smena 1", weekdays=[0, 1, 2, 3, 4, 5], start_time="08:00",
                     end_time="17:00", breaks=[dict(start="12:00", end="13:00", name="Obed")], active=True)


class OeeError(ValueError):
    """Foydalanuvchiga ko'rsatiladigan xato (API da 400)."""


class OeeNotFound(KeyError):
    pass


class OeeConflict(ValueError):
    """Holat to'qnashuvi (API da 409)."""


# ───────────────────────── Vaqt yordamchilari ─────────────────────────
_UTC = timezone.utc


def epoch(dt: datetime) -> float:
    """datetime → epoch s (naive — UTC deb olinadi)."""
    return dt.replace(tzinfo=_UTC).timestamp() if dt.tzinfo is None else dt.timestamp()


def naive_utc(t: float) -> datetime:
    return datetime.fromtimestamp(t, _UTC).replace(tzinfo=None)


def utc_now() -> datetime:
    return datetime.now(_UTC).replace(tzinfo=None)


def iso(dt: Optional[datetime]) -> Optional[str]:
    """Naive UTC datetime → ISO 8601 matn (`...Z`)."""
    if dt is None:
        return None
    dt = dt.replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt.microsecond == 0 else dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _aware_utc(dt: datetime) -> datetime:
    """Soat poyasi majburiy (yo'q bo'lsa xato); UTC ga o'tkazilgan naive datetime qaytaradi."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(_("oee_ev_naive"))
    return dt.astimezone(_UTC).replace(tzinfo=None)


# ───────────────────────── Sozlamalar ─────────────────────────
class OeeConfig(BaseModel):
    """`oee_config.config`. Hamma qiymatlar hujjatlangan standartlar (T_W17_OEE.md)."""
    model_config = ConfigDict(extra="forbid")
    tz_offset_min: int = Field(300, ge=-720, le=840)          # zavod vaqti = UTC + shu daqiqa (O'zbekiston: +05:00 = 300)
    idle_gap_s: int = Field(300, ge=0, le=7200)               # hodisasiz bo'shliq shu uzunlikdan boshlab `idle` to'xtash
    run_cap_factor: float = Field(3.0, ge=1.0, le=20.0, allow_inf_nan=False)   # boshlanishi noma'lum run: ≤ factor × ideal
    unit: Literal["sheet", "part"] = "sheet"                  # ishlab chiqarilgan birlik
    include_overtime: bool = False                            # smenadan tashqari ishlash rejalashtirilgan vaqtga kirsinmi


def get_config() -> OeeConfig:
    with SessionLocal() as s:
        row = s.get(OeeConfigRow, (tenant.current(), "config"))
        data = row.value if row and isinstance(row.value, dict) else {}
    try:
        return OeeConfig.model_validate(data)
    except ValidationError:
        return OeeConfig()


def set_config(patch: dict) -> OeeConfig:
    cur = get_config().model_dump()
    cur.update(patch)
    try:
        new = OeeConfig.model_validate(cur)
    except ValidationError as e:
        raise OeeError(format_errors(e.errors())) from e
    with SessionLocal() as s:
        row = s.get(OeeConfigRow, (tenant.current(), "config"))
        if row is None:
            s.add(OeeConfigRow(key="config", value=new.model_dump()))
        else:
            row.value = new.model_dump()
        s.commit()
    return new


def _engine_cfg(cfg: OeeConfig) -> C.Cfg:
    return C.Cfg(idle_gap_s=float(cfg.idle_gap_s), run_cap_factor=float(cfg.run_cap_factor), unit=cfg.unit,
                 include_overtime=cfg.include_overtime)


def ensure_defaults() -> None:
    """Birinchi murojaatda: boshlang'ich sabablar, namunaviy smena (Du–Sha 08:00–17:00, tanaffus 12:00–13:00) va sozlama.
    Bir marta (`seeded` belgisi); keyin foydalanuvchi o'zgartirgan/o'chirganini qayta tiklamaydi."""
    with SessionLocal() as s:
        if s.get(OeeConfigRow, (tenant.current(), "seeded")) is not None:
            return
        have = set(s.scalars(select(OeeReasonRow.code)).all())
        for code, ru, uz, kind, planned, sort in DEFAULT_REASONS:
            if code not in have:
                s.add(OeeReasonRow(code=code, name_ru=ru, name_uz=uz, kind=kind, planned=planned, active=True, sort=sort,
                                   system=True))
        if not s.scalar(select(func.count(OeeShiftRow.id))):
            s.add(OeeShiftRow(**DEFAULT_SHIFT))
        if s.get(OeeConfigRow, (tenant.current(), "config")) is None:
            s.add(OeeConfigRow(key="config", value=OeeConfig().model_dump()))
        s.add(OeeConfigRow(key="seeded", value=True))
        try:
            s.commit()
        except IntegrityError:          # parallel birinchi murojaat — boshqasi allaqachon qo'ydi
            s.rollback()


# ───────────────────────── Stanoklar ─────────────────────────
class MachineIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=200)
    kind: Optional[Literal["saw", "edge", "cnc", "other"]] = None
    pp_key: Optional[str] = Field(None, max_length=64)
    cut_speed_mm_s: Optional[float] = Field(None, gt=0, le=100_000, allow_inf_nan=False)
    cut_change_s: Optional[float] = Field(None, ge=0, le=3600, allow_inf_nan=False)
    sheet_load_s: Optional[float] = Field(None, ge=0, le=3600, allow_inf_nan=False)
    ideal_unit_s: Optional[float] = Field(None, gt=0, le=86_400, allow_inf_nan=False)
    active: Optional[bool] = None
    note: Optional[str] = Field(None, max_length=2000)


def machine_dict(r: OeeMachineRow) -> dict:
    pp_name = None
    if r.pp_key:
        from .postprocessors import MACHINE_BY_KEY
        pp_name = (MACHINE_BY_KEY.get(r.pp_key) or (None,))[0]
    return dict(id=r.id, key=r.key, name=r.name, kind=r.kind or "saw", pp_key=r.pp_key, pp_name=pp_name,
                cut_speed_mm_s=r.cut_speed_mm_s, cut_change_s=r.cut_change_s, sheet_load_s=r.sheet_load_s,
                ideal_unit_s=r.ideal_unit_s, active=r.active is not False, note=r.note or "")


def profile_of(r: OeeMachineRow) -> C.MachineProfile:
    return C.MachineProfile(key=r.key, cut_speed_mm_s=r.cut_speed_mm_s, cut_change_s=r.cut_change_s,
                            sheet_load_s=r.sheet_load_s, ideal_unit_s=r.ideal_unit_s)


def list_machines(active_only: bool = False) -> list[dict]:
    with SessionLocal() as s:
        rows = s.scalars(select(OeeMachineRow).order_by(OeeMachineRow.id)).all()
        return [machine_dict(r) for r in rows if not active_only or r.active is not False]


def get_machine(key: str) -> dict:
    with SessionLocal() as s:
        r = s.scalar(select(OeeMachineRow).where(OeeMachineRow.key == key))
        if r is None:
            raise OeeNotFound(_("oee_machine_unknown", k=key[:64]))
        return machine_dict(r)


def create_machine(inp: MachineIn) -> dict:
    from .postprocessors import MACHINE_BY_KEY
    pp = (inp.pp_key or "").strip() or None
    if pp and pp not in MACHINE_BY_KEY:
        raise OeeError(_("oee_pp_unknown", k=pp[:64]))
    key = (inp.key or "").strip() or pp
    if not key or not KEY_RE.match(key):
        raise OeeError(_("oee_machine_key_bad"))
    name = (inp.name or "").strip() or (MACHINE_BY_KEY[pp][0] if pp else key)
    kind = inp.kind or ({"saw": "saw", "cnc": "cnc"}.get(MACHINE_BY_KEY[pp][1], "other") if pp else "saw")
    with SessionLocal() as s:
        if s.scalar(select(OeeMachineRow.id).where(OeeMachineRow.key == key)) is not None:
            raise OeeConflict(_("oee_machine_exists", k=key))
        r = OeeMachineRow(
            key=key, name=name, kind=kind, pp_key=pp, note=inp.note or "", active=True if inp.active is None else inp.active,
            cut_speed_mm_s=inp.cut_speed_mm_s if inp.cut_speed_mm_s is not None else C.DEFAULT_CUT_SPEED_MM_S,
            cut_change_s=inp.cut_change_s if inp.cut_change_s is not None else C.DEFAULT_CUT_CHANGE_S,
            sheet_load_s=inp.sheet_load_s if inp.sheet_load_s is not None else C.DEFAULT_SHEET_LOAD_S,
            ideal_unit_s=inp.ideal_unit_s)
        s.add(r)
        try:
            s.commit()
        except IntegrityError as e:
            s.rollback()
            raise OeeConflict(_("oee_machine_exists", k=key)) from e
        return machine_dict(r)


def update_machine(key: str, inp: MachineIn, fields: set[str]) -> dict:
    """`fields` — so'rovda berilgan maydonlar (null berilsa: tezlik parametrlari uchun «sozlanmagan» = standart)."""
    from .postprocessors import MACHINE_BY_KEY
    with SessionLocal() as s:
        r = s.scalar(select(OeeMachineRow).where(OeeMachineRow.key == key))
        if r is None:
            raise OeeNotFound(_("oee_machine_unknown", k=key[:64]))
        if "key" in fields and inp.key and inp.key != key:
            raise OeeError(_("oee_machine_key_fixed"))
        if "name" in fields and inp.name is not None:
            if not inp.name.strip():
                raise OeeError(_("val_str_short", v=1))
            r.name = inp.name.strip()
        if "kind" in fields and inp.kind:
            r.kind = inp.kind
        if "pp_key" in fields:
            pp = (inp.pp_key or "").strip() or None
            if pp and pp not in MACHINE_BY_KEY:
                raise OeeError(_("oee_pp_unknown", k=pp[:64]))
            r.pp_key = pp
        for f, dflt in (("cut_speed_mm_s", C.DEFAULT_CUT_SPEED_MM_S), ("cut_change_s", C.DEFAULT_CUT_CHANGE_S),
                        ("sheet_load_s", C.DEFAULT_SHEET_LOAD_S)):
            if f in fields:
                v = getattr(inp, f)
                setattr(r, f, dflt if v is None else v)
        if "ideal_unit_s" in fields:
            r.ideal_unit_s = inp.ideal_unit_s
        if "active" in fields and inp.active is not None:
            r.active = inp.active
        if "note" in fields:
            r.note = inp.note or ""
        s.commit()
        return machine_dict(r)


def delete_machine(key: str, force: bool = False) -> int:
    """Stanokni o'chiradi. Hodisalari bo'lsa — 409 (nofaol qiling), `force=True` — hodisalari bilan birga. O'chirilgan hodisalar soni."""
    with SessionLocal() as s:
        r = s.scalar(select(OeeMachineRow).where(OeeMachineRow.key == key))
        if r is None:
            raise OeeNotFound(_("oee_machine_unknown", k=key[:64]))
        n = s.scalar(select(func.count(OeeEventRow.id)).where(OeeEventRow.machine_key == key)) or 0
        if n and not force:
            raise OeeConflict(_("oee_machine_has_events", n=n))
        if n:
            s.query(OeeEventRow).filter(OeeEventRow.machine_key == key).delete(synchronize_session=False)
        s.query(OeeShiftRow).filter(OeeShiftRow.machine_key == key).delete(synchronize_session=False)
        s.delete(r)
        s.commit()
        return int(n)


def pp_catalog() -> list[dict]:
    """Postprotsessor stanoklari ro'yxati (OEE stanogi sifatida qo'shish uchun) — qo'shilganlari belgilanadi."""
    from .postprocessors import MACHINES
    with SessionLocal() as s:
        taken = {k for k in s.scalars(select(OeeMachineRow.key)).all()}
    return [dict(key=k, name=n, group=g, added=k in taken) for k, n, g in MACHINES]


def suggest_from_pp(pp_key: str) -> dict:
    """Postprotsessor stanok sozlamasidan ideal tezlik taklifi (faqat foydalanuvchi so'raganda qo'llanadi).
    SCM WinCut `vel_avanz` (VelAvanz): birligi hujjatda yo'q — m/min deb taxmin qilinadi (`SCM_FEED_IS_M_MIN`)."""
    from .postprocessors import MACHINE_BY_KEY
    from . import pp_machine_ctx as PC
    if pp_key not in MACHINE_BY_KEY:
        raise OeeError(_("oee_pp_unknown", k=pp_key[:64]))
    params = PC.get_params(pp_key)
    out: dict[str, float] = {}
    src: dict[str, Any] = {}
    if "vel_avanz" in params and isinstance(params["vel_avanz"], (int, float)) and params["vel_avanz"] > 0:
        v = float(params["vel_avanz"])
        src["vel_avanz"] = v
        out["cut_speed_mm_s"] = round(v * 1000.0 / 60.0 if SCM_FEED_IS_M_MIN else v, 3)
    return dict(pp_key=pp_key, source=src, suggested=out, assumption="vel_avanz = m/min" if SCM_FEED_IS_M_MIN else "vel_avanz = mm/s")


# ───────────────────────── Sabablar ─────────────────────────
class ReasonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Optional[str] = Field(None, max_length=32)
    name_ru: Optional[str] = Field(None, max_length=120)
    name_uz: Optional[str] = Field(None, max_length=120)
    kind: Optional[Literal["downtime", "reject"]] = None
    planned: Optional[bool] = None
    active: Optional[bool] = None
    sort: Optional[int] = Field(None, ge=0, le=100_000)


def reason_dict(r: OeeReasonRow) -> dict:
    return dict(id=r.id, code=r.code, name_ru=r.name_ru or r.code, name_uz=r.name_uz or r.name_ru or r.code,
                kind=r.kind or "downtime", planned=bool(r.planned), active=r.active is not False, sort=r.sort or 0,
                system=bool(r.system))


def list_reasons(kind: Optional[str] = None, active_only: bool = False) -> list[dict]:
    with SessionLocal() as s:
        st = select(OeeReasonRow).order_by(OeeReasonRow.sort, OeeReasonRow.id)
        out = [reason_dict(r) for r in s.scalars(st).all()]
    return [r for r in out if (not kind or r["kind"] == kind) and (not active_only or r["active"])]


def create_reason(inp: ReasonIn) -> dict:
    code = (inp.code or "").strip()
    if not CODE_RE.match(code):
        raise OeeError(_("oee_reason_code_bad"))
    if code in RESERVED_REASONS:
        raise OeeError(_("oee_reason_reserved", c=code))
    name_ru = (inp.name_ru or inp.name_uz or code).strip()
    name_uz = (inp.name_uz or inp.name_ru or code).strip()
    with SessionLocal() as s:
        if s.scalar(select(OeeReasonRow.id).where(OeeReasonRow.code == code)) is not None:
            raise OeeConflict(_("oee_reason_exists", c=code))
        mx = s.scalar(select(func.max(OeeReasonRow.sort))) or 0
        r = OeeReasonRow(code=code, name_ru=name_ru, name_uz=name_uz, kind=inp.kind or "downtime",
                         planned=bool(inp.planned), active=True if inp.active is None else inp.active,
                         sort=inp.sort if inp.sort is not None else mx + 10, system=False)
        s.add(r)
        s.commit()
        return reason_dict(r)


def update_reason(code: str, inp: ReasonIn, fields: set[str]) -> dict:
    with SessionLocal() as s:
        r = s.scalar(select(OeeReasonRow).where(OeeReasonRow.code == code))
        if r is None:
            raise OeeNotFound(_("oee_reason_unknown", c=code[:32]))
        if "code" in fields and inp.code and inp.code != code:
            raise OeeError(_("oee_reason_code_fixed"))
        if "kind" in fields and inp.kind and inp.kind != (r.kind or "downtime"):
            used = s.scalar(select(func.count(OeeEventRow.id)).where(OeeEventRow.reason == code)) or 0
            if used:
                raise OeeConflict(_("oee_reason_used", c=code, n=used))
            r.kind = inp.kind
        for f in ("name_ru", "name_uz"):
            if f in fields and getattr(inp, f) is not None:
                v = getattr(inp, f).strip()
                if not v:
                    raise OeeError(_("val_str_short", v=1))
                setattr(r, f, v)
        if "planned" in fields and inp.planned is not None:
            r.planned = inp.planned
        if "active" in fields and inp.active is not None:
            r.active = inp.active
        if "sort" in fields and inp.sort is not None:
            r.sort = inp.sort
        s.commit()
        return reason_dict(r)


def delete_reason(code: str) -> None:
    with SessionLocal() as s:
        r = s.scalar(select(OeeReasonRow).where(OeeReasonRow.code == code))
        if r is None:
            raise OeeNotFound(_("oee_reason_unknown", c=code[:32]))
        if r.system:
            raise OeeConflict(_("oee_reason_system", c=code))
        used = s.scalar(select(func.count(OeeEventRow.id)).where(OeeEventRow.reason == code)) or 0
        if used:
            raise OeeConflict(_("oee_reason_used", c=code, n=used))
        s.delete(r)
        s.commit()


# ───────────────────────── Smena kalendari ─────────────────────────
class BreakIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: str
    end: str
    name: str = Field("", max_length=60)


class ShiftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["shift", "off"] = "shift"
    machine: Optional[str] = Field(None, max_length=64)        # bo'sh — hamma stanoklar
    name: str = Field("", max_length=100)
    weekdays: list[int] = [0, 1, 2, 3, 4, 5]                   # 0 = dushanba … 6 = yakshanba
    start: Optional[str] = None                                # «HH:MM» (zavod vaqti)
    end: Optional[str] = None                                  # ≤ start bo'lsa — yarim tundan o'tadi
    breaks: list[BreakIn] = Field([], max_length=20)
    valid_from: Optional[date] = None                          # mahalliy sana (shu kun ham kiradi)
    valid_to: Optional[date] = None
    active: bool = True


def _hhmm(v: Optional[str]) -> str:
    m = HHMM_RE.match((v or "").strip())
    if not m:
        raise OeeError(_("oee_shift_bad_time"))
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def _mins(v: str) -> int:
    return int(v[:2]) * 60 + int(v[3:])


def shift_row_values(m: ShiftIn) -> dict:
    """ShiftIn → ustun qiymatlari (tekshirilgan)."""
    if m.valid_from and m.valid_to and m.valid_to < m.valid_from:
        raise OeeError(_("oee_shift_range"))
    mk = (m.machine or "").strip() or None
    if m.kind == "off":
        if not (m.valid_from and m.valid_to):
            raise OeeError(_("oee_off_range"))
        return dict(kind="off", machine_key=mk, name=m.name.strip(), weekdays=None, start_time=None, end_time=None,
                    breaks=None, valid_from=m.valid_from.isoformat(), valid_to=m.valid_to.isoformat(), active=m.active)
    wd = sorted(set(m.weekdays))
    if not wd or any(d < 0 or d > 6 for d in wd):
        raise OeeError(_("oee_shift_weekdays"))
    st, en = _hhmm(m.start), _hhmm(m.end)
    s0, e0 = _mins(st), _mins(en)
    if s0 == e0:
        raise OeeError(_("oee_shift_len"))
    length = (e0 - s0) % 1440
    brs = []
    for b in m.breaks:
        bs, be = _hhmm(b.start), _hhmm(b.end)
        off_s = (_mins(bs) - s0) % 1440
        off_e = off_s + ((_mins(be) - _mins(bs)) % 1440)
        if _mins(bs) == _mins(be) or off_e > length:
            raise OeeError(_("oee_break_outside", b=f"{bs}–{be}"))
        brs.append(dict(start=bs, end=be, name=b.name.strip()))
    return dict(kind="shift", machine_key=mk, name=m.name.strip() or f"{st}–{en}", weekdays=wd, start_time=st, end_time=en,
                breaks=brs, valid_from=m.valid_from.isoformat() if m.valid_from else None,
                valid_to=m.valid_to.isoformat() if m.valid_to else None, active=m.active)


def shift_dict(r: OeeShiftRow) -> dict:
    return dict(id=r.id, kind=r.kind or "shift", machine=r.machine_key, name=r.name or "", weekdays=list(r.weekdays or []),
                start=r.start_time, end=r.end_time, breaks=list(r.breaks or []), valid_from=r.valid_from,
                valid_to=r.valid_to, active=r.active is not False)


def list_shifts() -> list[dict]:
    with SessionLocal() as s:
        return [shift_dict(r) for r in s.scalars(select(OeeShiftRow).order_by(OeeShiftRow.kind.desc(), OeeShiftRow.id)).all()]


def _check_machine_key(s, key: Optional[str]) -> None:
    if key and s.scalar(select(OeeMachineRow.id).where(OeeMachineRow.key == key)) is None:
        raise OeeError(_("oee_machine_unknown", k=key[:64]))


def create_shift(inp: ShiftIn) -> dict:
    vals = shift_row_values(inp)
    with SessionLocal() as s:
        _check_machine_key(s, vals["machine_key"])
        r = OeeShiftRow(**vals)
        s.add(r)
        s.commit()
        return shift_dict(r)


def update_shift(sid: int, inp: ShiftIn) -> dict:
    vals = shift_row_values(inp)
    with SessionLocal() as s:
        r = s.get(OeeShiftRow, sid)
        if r is None:
            raise OeeNotFound(_("oee_shift_unknown"))
        _check_machine_key(s, vals["machine_key"])
        for k, v in vals.items():
            setattr(r, k, v)
        s.commit()
        return shift_dict(r)


def delete_shift(sid: int) -> None:
    with SessionLocal() as s:
        r = s.get(OeeShiftRow, sid)
        if r is None:
            raise OeeNotFound(_("oee_shift_unknown"))
        s.delete(r)
        s.commit()


def _parse_d(v: Optional[str]) -> Optional[date]:
    return date.fromisoformat(v) if v else None


def _date_of(idx: int) -> date:
    return date(1970, 1, 1) + timedelta(days=idx)


def expand_shifts(rows: list[dict], machine_key: Optional[str], lo: float, hi: float, off_min: int) -> list[dict]:
    """Kalendar → smena nusxalari [lo, hi] oralig'ida. Stanokka alohida smenalar bo'lsa — faqat shular (umumiylar o'rniga);
    dam olish (`off`) — umumiy va shu stanokniki. Nusxa: {name, date, start, end, breaks:[(s, e, nom)]} (epoch s)."""
    shifts = [r for r in rows if r["kind"] == "shift" and r["active"]]
    own = [r for r in shifts if machine_key and r["machine"] == machine_key]
    use = own or [r for r in shifts if r["machine"] is None]
    offs = [(_parse_d(r["valid_from"]), _parse_d(r["valid_to"])) for r in rows
            if r["kind"] == "off" and r["active"] and (r["machine"] is None or r["machine"] == machine_key)]
    out: list[dict] = []
    d0, d1 = C.local_day_index(lo, off_min) - 1, C.local_day_index(hi, off_min) + 1
    for di in range(d0, d1 + 1):
        d = _date_of(di)
        if any(a and b and a <= d <= b for a, b in offs):
            continue
        base = C.day_start(di, off_min)
        for r in use:
            if d.weekday() not in r["weekdays"]:
                continue
            vf, vt = _parse_d(r["valid_from"]), _parse_d(r["valid_to"])
            if (vf and d < vf) or (vt and d > vt):
                continue
            s0, e0 = _mins(r["start"]), _mins(r["end"])
            start = base + s0 * 60
            end = base + (e0 if e0 > s0 else e0 + 1440) * 60
            if end <= lo or start >= hi:
                continue
            brs = []
            for b in r["breaks"] or []:
                bs, be = _mins(b["start"]), _mins(b["end"])
                bs_abs = bs if bs >= s0 else bs + 1440
                be_abs = bs_abs + ((be - bs) % 1440)
                brs.append((base + bs_abs * 60, base + be_abs * 60, b.get("name", "")))
            out.append(dict(name=r["name"], date=d.isoformat(), start=start, end=end, breaks=brs, id=r["id"]))
    out.sort(key=lambda x: (x["start"], x["end"]))
    return out


def planned_intervals(insts: list[dict]) -> list[C.Interval]:
    """Smena nusxalari − tanaffuslar."""
    iv: list[C.Interval] = []
    for i in insts:
        iv.extend(C.subtract([(i["start"], i["end"])], C.merge((s, e) for s, e, _n in i["breaks"])))
    return C.merge(iv)


def preview_shifts(machine: Optional[str], lo: float, hi: float) -> list[dict]:
    cfg = get_config()
    rows = list_shifts()
    out = []
    for i in expand_shifts(rows, machine, lo, hi, cfg.tz_offset_min):
        pl = planned_intervals([i])
        out.append(dict(name=i["name"], date=i["date"], start=C.iso_utc(i["start"]), end=C.iso_utc(i["end"]),
                        planned_min=round(C.total(pl) / 60.0, 2),
                        breaks=[dict(start=C.iso_utc(s), end=C.iso_utc(e), name=n) for s, e, n in i["breaks"]]))
    return out


# ───────────────────────── Hodisalar ─────────────────────────
class EventIn(BaseModel):
    """Hodisa (MES / sex rejimi / qo'lda). Vaqtlar — soat poyasi bilan (ISO 8601: `...Z` yoki `+05:00`)."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["run", "downtime", "reject"]
    machine: str = Field(min_length=1, max_length=64)
    external_id: Optional[str] = Field(None, max_length=100)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    qty: Optional[int] = Field(None, ge=0, le=1_000_000)
    reject_qty: Optional[int] = Field(None, ge=0, le=1_000_000)
    unit: Optional[Literal["part", "sheet"]] = None
    parts: Optional[int] = Field(None, ge=0, le=10_000_000)
    parts_per_sheet: Optional[int] = Field(None, ge=0, le=100_000)
    cut_length_m: Optional[float] = Field(None, ge=0, le=100_000, allow_inf_nan=False)
    cuts: Optional[int] = Field(None, ge=0, le=100_000)
    sheets_per_pack: Optional[int] = Field(None, ge=1, le=1000)
    ideal_cycle_s: Optional[float] = Field(None, gt=0, le=86_400, allow_inf_nan=False)
    sheet_area_m2: Optional[float] = Field(None, gt=0, le=1000, allow_inf_nan=False)
    parts_area_m2: Optional[float] = Field(None, ge=0, le=1000, allow_inf_nan=False)
    remnant_area_m2: Optional[float] = Field(None, ge=0, le=1000, allow_inf_nan=False)
    reason: Optional[str] = Field(None, max_length=32)
    note: Optional[str] = Field(None, max_length=2000)
    project_number: Optional[int] = Field(None, ge=0, le=2_000_000_000)
    project_id: Optional[str] = Field(None, max_length=32)
    op_id: Optional[str] = Field(None, max_length=32)
    map_index: Optional[int] = Field(None, ge=0, le=100_000)
    source: Optional[str] = Field(None, max_length=20)

    @field_validator("start", "end")
    @classmethod
    def _tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        out = _aware_utc(v)
        if not (datetime(2000, 1, 1) <= out < datetime(2100, 1, 1)):
            raise ValueError(_("oee_ev_range"))
        return out

    @field_validator("source")
    @classmethod
    def _src(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not SOURCES_FREE.match(v):
            raise ValueError(_("oee_ev_source"))
        return v

    @model_validator(mode="after")
    def _by_type(self) -> "EventIn":
        t = self.type
        now = utc_now() + timedelta(seconds=FUTURE_SKEW_S)
        if t == "run":
            if self.end is None:
                raise ValueError(_("oee_ev_need", f="end", t=t))
            if self.start is not None:
                if self.start >= self.end:
                    raise ValueError(_("oee_ev_order"))
                if (self.end - self.start).total_seconds() > C.MAX_RUN_S:
                    raise ValueError(_("oee_ev_long", h=round((self.end - self.start).total_seconds() / 3600, 1), m=C.MAX_RUN_S // 3600))
            if self.qty is not None and self.qty < 1:
                raise ValueError(_("val_ge", v=1))
            if self.end > now:
                raise ValueError(_("oee_ev_future"))
        elif t == "downtime":
            if self.start is None:
                raise ValueError(_("oee_ev_need", f="start", t=t))
            if not (self.reason or "").strip():
                raise ValueError(_("oee_ev_need", f="reason", t=t))
            if self.end is not None:
                if self.end <= self.start:
                    raise ValueError(_("oee_ev_order"))
                if (self.end - self.start).total_seconds() > MAX_DOWN_S:
                    raise ValueError(_("oee_ev_long", h=round((self.end - self.start).total_seconds() / 3600, 1), m=MAX_DOWN_S // 3600))
            if self.start > now or (self.end is not None and self.end > now):
                raise ValueError(_("oee_ev_future"))
        else:   # reject
            if self.end is None:
                if self.start is None:
                    raise ValueError(_("oee_ev_need", f="end", t=t))
                self.end = self.start            # faqat `start` berilgan bo'lsa ham qabul qilinadi (bitta vaqt nuqtasi)
            if self.qty is not None and self.qty < 1:
                raise ValueError(_("val_ge", v=1))
            if self.end > now:
                raise ValueError(_("oee_ev_future"))
        return self


def event_values(e: EventIn) -> dict:
    """EventIn → ustun qiymatlari (turga xos standartlar bilan)."""
    t = e.type
    v: dict[str, Any] = dict(type=t, machine_key=e.machine.strip(), external_id=(e.external_id or "").strip() or None,
                             start_ts=e.start, end_ts=e.end, reason=(e.reason or "").strip() or None,
                             note=(e.note or "").strip() or None, source=e.source,
                             project_number=e.project_number, project_id=e.project_id, op_id=e.op_id, map_index=e.map_index,
                             qty=None, reject_qty=None, unit=None, parts=None, parts_per_sheet=None, cut_length_m=None,
                             cuts=None, sheets_per_pack=None, ideal_cycle_s=None, sheet_area_m2=None, parts_area_m2=None,
                             remnant_area_m2=None)
    if t == "run":
        v.update(qty=e.qty if e.qty is not None else 1, reject_qty=e.reject_qty or 0, unit=e.unit or "part", parts=e.parts,
                 parts_per_sheet=e.parts_per_sheet, cut_length_m=e.cut_length_m, cuts=e.cuts,
                 sheets_per_pack=e.sheets_per_pack or 1, ideal_cycle_s=e.ideal_cycle_s, reason=None,
                 sheet_area_m2=e.sheet_area_m2, parts_area_m2=e.parts_area_m2, remnant_area_m2=e.remnant_area_m2)
        if e.start is None:
            v["start_ts"] = None
    elif t == "reject":
        v.update(qty=e.qty if e.qty is not None else 1, unit=e.unit or "part", parts_per_sheet=e.parts_per_sheet, start_ts=None)
    else:
        v.update(end_ts=e.end)
    return v


def event_dict(r: OeeEventRow) -> dict:
    return dict(id=r.id, type=r.type, machine=r.machine_key, start=iso(r.start_ts), end=iso(r.end_ts), qty=r.qty,
                reject_qty=r.reject_qty, unit=r.unit, parts=r.parts, parts_per_sheet=r.parts_per_sheet,
                cut_length_m=r.cut_length_m, cuts=r.cuts, sheets_per_pack=r.sheets_per_pack, ideal_cycle_s=r.ideal_cycle_s,
                sheet_area_m2=r.sheet_area_m2, parts_area_m2=r.parts_area_m2, remnant_area_m2=r.remnant_area_m2, reason=r.reason, note=r.note, project_number=r.project_number, project_id=r.project_id, op_id=r.op_id,
                map_index=r.map_index, source=r.source, external_id=r.external_id, created_by=r.created_by,
                created_at=iso(r.created_at), updated_at=iso(r.updated_at),
                open=bool(r.type == "downtime" and r.end_ts is None))


def _lookup_card(number: Optional[int], op_id: Optional[str], idx: Optional[int], cache: dict) -> Optional[dict]:
    """Loyiha kartasidan geometriya (best effort; xato — None): cut_length_m, cuts, parts_per_sheet, sheets_per_pack."""
    if number is None or not op_id or idx is None:
        return None
    if number not in cache:
        try:
            from .. import store
            cache[number] = store.find_by_number(number)
        except Exception:  # noqa: BLE001 — loyiha yo'q / o'qib bo'lmadi: hodisa baribir yoziladi
            cache[number] = None
    p = cache[number]
    if p is None:
        return None
    op = next((o for o in p.operations if o.id == op_id), None)
    if op is None or op.result is None or not (1 <= idx <= len(op.result.maps)):
        return None
    m = op.result.maps[idx - 1]
    return dict(cut_length_m=m.cut_length_m, cuts=m.cuts_count, parts_per_sheet=m.parts_count,
                sheets_per_pack=op.result.sheets_per_pack or 1, sheet_area_m2=m.sheet_area_m2 or None,
                parts_area_m2=m.parts_area_m2, remnant_area_m2=m.remnant_area_m2)


def _semantic(vals: dict, machines: set[str], reasons: dict[str, dict]) -> None:
    if vals["machine_key"] not in machines:
        raise OeeError(_("oee_machine_unknown", k=vals["machine_key"][:64]))
    rs = vals["reason"]
    if vals["type"] == "downtime":
        info = reasons.get(rs or "")
        if info is None or info["kind"] != "downtime":
            raise OeeError(_("oee_reason_unknown", c=(rs or "")[:32]))
        if not info["active"]:
            raise OeeError(_("oee_reason_inactive", c=rs))
    elif vals["type"] == "reject" and rs:
        info = reasons.get(rs)
        if info is None or info["kind"] != "reject":
            raise OeeError(_("oee_reason_unknown", c=rs[:32]))
        if not info["active"]:
            raise OeeError(_("oee_reason_inactive", c=rs))


_FIELDS = ("type", "machine_key", "external_id", "start_ts", "end_ts", "qty", "reject_qty", "unit", "parts", "parts_per_sheet",
           "cut_length_m", "cuts", "sheets_per_pack", "ideal_cycle_s", "sheet_area_m2", "parts_area_m2", "remnant_area_m2", "reason",
           "note", "project_number", "project_id",
           "op_id", "map_index", "source")


def _same(row: OeeEventRow, vals: dict) -> bool:
    for k in _FIELDS:
        a, b = getattr(row, k), vals.get(k)
        if k == "source" and b is None:
            continue                        # manba berilmagan yangilash mavjud manbani o'zgartirmaydi
        if a != b:
            return False
    return True


def ingest(items: list[Any], user: str = "", default_source: str = "api") -> list[dict]:
    """Hodisalarni qabul qiladi. Har element uchun natija: {index, status: created|updated|unchanged|error, id?, error?}.
    `external_id` bo'yicha idempotent: bir xil kalit — mavjud hodisa to'liq yangilanadi (o'zgarmasa `unchanged`)."""
    n = len(items)
    results: list[Optional[dict]] = [None] * n
    parsed: list[tuple[int, dict]] = []
    machines = {m["key"] for m in list_machines()}
    reasons = {r["code"]: r for r in list_reasons()}
    cache: dict = {}
    for i, it in enumerate(items):
        try:
            if not isinstance(it, dict):
                raise OeeError(_("val_dict"))
            e = EventIn.model_validate(it)
            vals = event_values(e)
            if vals["source"] is None:
                vals["source"] = default_source
            _semantic(vals, machines, reasons)
            if vals["type"] == "run" and (vals["cut_length_m"] is None or vals["cuts"] is None or vals["sheet_area_m2"] is None):
                card = _lookup_card(vals["project_number"], vals["op_id"], vals["map_index"], cache)
                if card:
                    for k, v in card.items():
                        if vals.get(k) is None or (k == "sheets_per_pack" and not e.sheets_per_pack):
                            vals[k] = v
            parsed.append((i, vals))
        except ValidationError as ex:
            results[i] = dict(index=i, status="error", error=format_errors(ex.errors()))
        except OeeError as ex:
            results[i] = dict(index=i, status="error", error=str(ex))
    for attempt in (1, 2):
        out = _apply(parsed, user)
        if out is not None:
            for i, r in out.items():
                results[i] = r
            break
    else:                                    # ikki urinishda ham poyga — oxirgi chora
        for i, _v in parsed:
            results[i] = dict(index=i, status="error", error="conflict")
    return [r for r in results if r is not None]


def _apply(parsed: list[tuple[int, dict]], user: str) -> Optional[dict[int, dict]]:
    """Bitta tranzaksiyada yozadi. Poyga (unique external_id) — None (qayta urinish)."""
    res: dict[int, dict] = {}
    if not parsed:
        return res
    now = utc_now()
    with SessionLocal() as s:
        ext = [v["external_id"] for _i, v in parsed if v["external_id"]]
        existing: dict[str, OeeEventRow] = {}
        if ext:
            for chunk in range(0, len(ext), 400):
                for r in s.scalars(select(OeeEventRow).where(OeeEventRow.external_id.in_(ext[chunk:chunk + 400]))).all():
                    existing[r.external_id] = r
        pending: list[tuple[int, str, OeeEventRow]] = []
        for i, vals in parsed:
            row = existing.get(vals["external_id"]) if vals["external_id"] else None
            if row is not None:
                if row.type != vals["type"] or row.machine_key != vals["machine_key"]:
                    res[i] = dict(index=i, status="error", id=row.id, error=_("oee_ev_dup_type", x=vals["external_id"][:100]))
                    continue
                if _same(row, vals):
                    pending.append((i, "unchanged", row))
                    continue
                for k in _FIELDS:
                    if k == "source" and vals.get(k) is None:
                        continue
                    setattr(row, k, vals.get(k))
                row.updated_at = now
                pending.append((i, "updated", row))
                continue
            row = OeeEventRow(**vals, created_by=user or None, created_at=now, updated_at=now)
            s.add(row)
            if vals["external_id"]:
                existing[vals["external_id"]] = row
            pending.append((i, "created", row))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            return None
        for i, status, row in pending:          # id lar commitdan keyin ma'lum
            res[i] = dict(index=i, status=status, id=row.id)
    return res


def get_event(eid: int) -> dict:
    with SessionLocal() as s:
        r = s.get(OeeEventRow, eid)
        if r is None:
            raise OeeNotFound(_("oee_ev_not_found"))
        return event_dict(r)


def patch_event(eid: int, patch: dict, user: str = "") -> dict:
    """Hodisani qisman o'zgartirish (qo'lda tuzatish): joriy qiymatlar ustiga `patch`; turi o'zgarmaydi."""
    with SessionLocal() as s:
        r = s.get(OeeEventRow, eid)
        if r is None:
            raise OeeNotFound(_("oee_ev_not_found"))
        cur = event_dict(r)
        body = {k: v for k, v in cur.items() if k in EventIn.model_fields and v is not None}
        body["machine"] = cur["machine"]
        if "type" in patch and patch["type"] != r.type:
            raise OeeError(_("oee_ev_type_fixed"))
        body.update({k: v for k, v in patch.items() if k in EventIn.model_fields})
        for k, v in patch.items():
            if k in EventIn.model_fields and v is None:
                body.pop(k, None)
        try:
            e = EventIn.model_validate(body)
        except ValidationError as ex:
            raise OeeError(format_errors(ex.errors())) from ex
        vals = event_values(e)
        machines = {m["key"] for m in list_machines()}
        reasons = {x["code"]: x for x in list_reasons()}
        _semantic(vals, machines, reasons)
        if vals["external_id"] and vals["external_id"] != r.external_id:
            if s.scalar(select(OeeEventRow.id).where(OeeEventRow.external_id == vals["external_id"])) is not None:
                raise OeeConflict(_("oee_ev_dup_type", x=vals["external_id"][:100]))
        for k in _FIELDS:
            if k == "source" and vals.get(k) is None:
                continue
            setattr(r, k, vals.get(k))
        r.updated_at = utc_now()
        try:
            s.commit()
        except IntegrityError as ex:
            s.rollback()
            raise OeeConflict(_("oee_ev_dup_type", x=str(vals["external_id"])[:100])) from ex
        return event_dict(r)


def delete_event(eid: int) -> None:
    with SessionLocal() as s:
        r = s.get(OeeEventRow, eid)
        if r is None:
            raise OeeNotFound(_("oee_ev_not_found"))
        s.delete(r)
        s.commit()


def _time_col():
    return func.coalesce(OeeEventRow.end_ts, OeeEventRow.start_ts)


def list_events(machine: Optional[str] = None, type_: Optional[str] = None, lo: Optional[float] = None,
                hi: Optional[float] = None, reason: Optional[str] = None, limit: int = 200, offset: int = 0,
                source: Optional[str] = None) -> dict:
    with SessionLocal() as s:
        st = select(OeeEventRow)
        cnt = select(func.count(OeeEventRow.id))
        conds = []
        if machine:
            conds.append(OeeEventRow.machine_key == machine)
        if type_:
            conds.append(OeeEventRow.type == type_)
        if reason:
            conds.append(OeeEventRow.reason == reason)
        if source:
            conds.append(OeeEventRow.source == source)
        if lo is not None:
            conds.append(or_(_time_col() >= naive_utc(lo), OeeEventRow.end_ts.is_(None)))
        if hi is not None:
            conds.append(or_(OeeEventRow.start_ts < naive_utc(hi), (OeeEventRow.start_ts.is_(None)) & (OeeEventRow.end_ts < naive_utc(hi))))
        for c in conds:
            st, cnt = st.where(c), cnt.where(c)
        total = s.scalar(cnt) or 0
        rows = s.scalars(st.order_by(_time_col().desc(), OeeEventRow.id.desc()).limit(limit).offset(offset)).all()
        return dict(total=total, items=[event_dict(r) for r in rows])


# ───────────────────────── Sex rejimi: kesildi / to'xtash ─────────────────────────
def workshop_machine(key: Optional[str]) -> Optional[str]:
    """Sex «bajarildi» belgisi uchun stanok: berilgan faol kalit; berilmasa — yagona faol «saw» stanogi; aks holda None."""
    with SessionLocal() as s:
        if key:
            r = s.scalar(select(OeeMachineRow).where(OeeMachineRow.key == key))
            return r.key if r is not None and r.active is not False else None
        rows = [r for r in s.scalars(select(OeeMachineRow)).all() if r.active is not False and (r.kind or "saw") == "saw"]
        return rows[0].key if len(rows) == 1 else None


def record_sheet_done(machine: Optional[str], delta: int, geo: dict, user: str = "") -> Optional[dict]:
    """Sexda karta «bajarildi» (+delta list): `run` hodisasi (tugash = hozir, boshlanish — hisobda avvalgi hodisadan).
    Stanok aniqlanmasa — None (hodisa yozilmaydi). Chaqiruvchi xatolarni yutadi (skaner buzilmasin)."""
    key = workshop_machine(machine)
    if not key or delta < 1:
        return None
    vals = dict(type="run", machine_key=key, external_id=None, start_ts=None, end_ts=utc_now().replace(microsecond=0),
                qty=int(delta), reject_qty=0, unit="part", parts=None, parts_per_sheet=geo.get("parts_per_sheet"),
                cut_length_m=geo.get("cut_length_m"), cuts=geo.get("cuts"), sheets_per_pack=geo.get("sheets_per_pack") or 1,
                ideal_cycle_s=None, sheet_area_m2=geo.get("sheet_area_m2"), parts_area_m2=geo.get("parts_area_m2"),
                remnant_area_m2=geo.get("remnant_area_m2"), reason=None, note=None, project_number=geo.get("project_number"),
                project_id=geo.get("project_id"), op_id=geo.get("op_id"), map_index=geo.get("map_index"),
                source="workshop")
    with SessionLocal() as s:
        row = OeeEventRow(**vals, created_by=user or None, created_at=utc_now(), updated_at=utc_now())
        s.add(row)
        s.commit()
        return event_dict(row)


def open_downtime(machine: str) -> Optional[dict]:
    with SessionLocal() as s:
        r = s.scalar(select(OeeEventRow).where(OeeEventRow.machine_key == machine, OeeEventRow.type == "downtime",
                                               OeeEventRow.end_ts.is_(None)).order_by(OeeEventRow.start_ts.desc()))
        return event_dict(r) if r is not None else None


def start_downtime(machine: str, reason: str, note: str = "", user: str = "") -> dict:
    machines = {m["key"] for m in list_machines()}
    reasons = {r["code"]: r for r in list_reasons()}
    vals = dict(type="downtime", machine_key=machine, reason=reason)
    _semantic(vals, machines, reasons)
    if open_downtime(machine) is not None:
        raise OeeConflict(_("oee_downtime_open"))
    now = utc_now().replace(microsecond=0)
    with SessionLocal() as s:
        row = OeeEventRow(type="downtime", machine_key=machine, start_ts=now, end_ts=None, reason=reason,
                          note=(note or "").strip()[:2000] or None, source="workshop", created_by=user or None,
                          created_at=now, updated_at=now)
        s.add(row)
        s.commit()
        return event_dict(row)


def stop_downtime(machine: str) -> dict:
    now = utc_now().replace(microsecond=0)
    with SessionLocal() as s:
        r = s.scalar(select(OeeEventRow).where(OeeEventRow.machine_key == machine, OeeEventRow.type == "downtime",
                                               OeeEventRow.end_ts.is_(None)).order_by(OeeEventRow.start_ts.desc()))
        if r is None:
            raise OeeNotFound(_("oee_downtime_none"))
        r.end_ts = now if now > r.start_ts else r.start_ts + timedelta(seconds=1)
        r.updated_at = now
        s.commit()
        return event_dict(r)


# ───────────────────────── Davr va hisoblash ─────────────────────────
def resolve_range(frm: Optional[str], to: Optional[str], period: Optional[str], cfg: OeeConfig,
                  now: Optional[float] = None) -> tuple[float, float]:
    """Davr → (lo, hi) epoch s. `period` (today, yesterday, last7, last14, last30, this_week, this_month) yoki `from`/`to`:
    `YYYY-MM-DD` (zavod kuni; `to` kuni ham kiradi) yoki soat poyasi bilan ISO vaqt ([from, to)). Standart — last7."""
    off = cfg.tz_offset_min
    now = utc_now().replace(tzinfo=_UTC).timestamp() if now is None else now
    today = C.local_day_index(now, off)

    def dstart(i: int) -> float:
        return C.day_start(i, off)
    if period and not (frm or to):
        if period not in PERIODS:
            raise OeeError(_("oee_range_bad"))
        if period == "today":
            return dstart(today), dstart(today + 1)
        if period == "yesterday":
            return dstart(today - 1), dstart(today)
        if period in ("last7", "last14", "last30"):
            n = int(period[4:])
            return dstart(today - n + 1), dstart(today + 1)
        if period == "this_week":
            wd = _date_of(today).weekday()
            return dstart(today - wd), dstart(today - wd + 7)
        d = _date_of(today)
        first = d.replace(day=1)
        nxt = (first + timedelta(days=32)).replace(day=1)
        return dstart((first - date(1970, 1, 1)).days), dstart((nxt - date(1970, 1, 1)).days)

    def parse(v: str, is_to: bool) -> float:
        v = v.strip()
        try:
            if len(v) == 10:
                di = (date.fromisoformat(v) - date(1970, 1, 1)).days
                return dstart(di + 1) if is_to else dstart(di)
            dt = datetime.fromisoformat(v)
        except ValueError as e:
            raise OeeError(_("oee_range_bad")) from e
        if dt.tzinfo is None:
            raise OeeError(_("oee_ev_naive"))
        return dt.timestamp()
    if not frm and not to:
        return dstart(today - 6), dstart(today + 1)
    hi = parse(to, True) if to else dstart(today + 1)
    lo = parse(frm, False) if frm else hi - 7 * 86400
    if hi <= lo:
        raise OeeError(_("oee_range_bad"))
    if hi - lo > MAX_RANGE_DAYS * 86400:
        raise OeeError(_("oee_range_big", n=MAX_RANGE_DAYS))
    return lo, hi


def _load(keys: list[str], lo: float, hi: float) -> dict[str, tuple[list, list, list]]:
    """Stanoklar bo'yicha (runs, downs, rejs) — engine obyektlari."""
    out: dict[str, tuple[list, list, list]] = {k: ([], [], []) for k in keys}
    if not keys:
        return out
    lb, ub = naive_utc(lo - LOOKBACK_S), naive_utc(hi + LOOKBACK_S)
    with SessionLocal() as s:
        rows = s.scalars(select(OeeEventRow).where(
            OeeEventRow.machine_key.in_(keys),
            or_(
                (OeeEventRow.type.in_(("run", "reject"))) & (OeeEventRow.end_ts >= lb) & (OeeEventRow.end_ts < ub),
                (OeeEventRow.type == "downtime") & (OeeEventRow.start_ts < naive_utc(hi))
                & (or_(OeeEventRow.end_ts.is_(None), OeeEventRow.end_ts > lb)),
            ))).all()
        for r in rows:
            runs, downs, rejs = out[r.machine_key]
            if r.type == "run" and r.end_ts is not None:
                runs.append(C.RunEv(id=r.id, end=epoch(r.end_ts), start=epoch(r.start_ts) if r.start_ts else None,
                                    qty=float(r.qty or 1), reject_qty=float(r.reject_qty or 0), unit=r.unit or "part",
                                    parts=float(r.parts) if r.parts is not None else None,
                                    parts_per_sheet=float(r.parts_per_sheet) if r.parts_per_sheet else None,
                                    cut_length_m=r.cut_length_m, cuts=r.cuts, sheets_per_pack=float(r.sheets_per_pack or 1),
                                    ideal_cycle_s=r.ideal_cycle_s, sheet_area_m2=r.sheet_area_m2, parts_area_m2=r.parts_area_m2,
                                    remnant_area_m2=r.remnant_area_m2))
            elif r.type == "downtime" and r.start_ts is not None:
                downs.append(C.DownEv(id=r.id, start=epoch(r.start_ts), reason=r.reason or "other",
                                      end=epoch(r.end_ts) if r.end_ts else None))
            elif r.type == "reject" and r.end_ts is not None:
                rejs.append(C.RejEv(id=r.id, ts=epoch(r.end_ts), qty=float(r.qty or 1), unit=r.unit or "part",
                                    parts_per_sheet=float(r.parts_per_sheet) if r.parts_per_sheet else None, reason=r.reason))
    return out


def _r(v: Optional[float], nd: int = 4) -> Optional[float]:
    return None if v is None else round(v, nd)


def _metrics(c: C.Comp) -> dict:
    x = C.ratios(c)
    out = dict(
        availability=_r(x["availability"]), performance=_r(x["performance"]), performance_raw=_r(x["performance_raw"]),
        quality=_r(x["quality"]), oee=_r(x["oee"]), planned_min=_r(x["planned_min"], 2), run_min=_r(x["run_min"], 2),
        stop_min=_r(x["stop_min"], 2), idle_min=_r(x["idle_min"], 2), ideal_min=_r(x["ideal_min"], 2),
        produced=_r(x["produced"], 2), rejected=_r(x["rejected"], 2), good=_r(x["good"], 2), sheets=_r(x["sheets"], 2),
        parts=_r(x["parts"], 2), avg_cycle_s=_r(x["avg_cycle_s"], 1), ideal_cycle_s=_r(x["ideal_cycle_s"], 1),
        events=x["events"], capped=x["capped"], outside=_r(x["outside_sheets"], 2))
    out["band"] = {k: C.band(x[k]) for k in ("oee", "availability", "performance", "quality")}
    return out


def _material(tls: list) -> dict:
    """Material samaradorligi (OEE ga KIRMAYDI — qo'shimcha KPI): oynada kesilgan, maydon ma'lumoti bor kartalar bo'yicha.
    fill = detallar maydoni / list maydoni (F); waste = (list − detallar − деловой qoldiq) / list — qayta ishlatiladigan qoldiq otxod emas."""
    sh = sum(t.mat_sheets for t in tls)
    sm = sum(t.mat_sheet_m2 for t in tls)
    pm = sum(t.mat_parts_m2 for t in tls)
    rm = sum(t.mat_remnant_m2 for t in tls)
    if sm <= 0:
        return dict(sheets=0, sheet_m2=0, parts_m2=0, remnant_m2=0, fill=None, waste=None)
    return dict(sheets=_r(sh, 2), sheet_m2=_r(sm, 2), parts_m2=_r(pm, 2), remnant_m2=_r(rm, 2), fill=_r(min(1.0, pm / sm)),
                waste=_r(max(0.0, sm - pm - rm) / sm))


def compute(machine: Optional[str] = None, lo: Optional[float] = None, hi: Optional[float] = None, group_by: str = "day",
            as_of: Optional[float] = None, period: Optional[str] = None, also: tuple[str, ...] = ()) -> dict:
    """OEE hisobi: summary (A, P, Q, OEE, miqdorlar), machines (har stanok), series (soat/smena/kun/hafta), pareto (to'xtash
    sabablari, daqiqa), warnings. `machine=None` — hamma faol stanoklar (komponentlar yig'indisi: vaqt bo'yicha vaznli).
    `also` — qo'shimcha guruhlashlar (`extra_series[guruh]`): panel bir so'rovda kun trendi va smenalar jadvalini oladi."""
    if group_by not in GROUPS:
        raise OeeError(_("oee_group_bad"))
    cfg = get_config()
    ecfg = _engine_cfg(cfg)
    now = utc_now().replace(tzinfo=_UTC).timestamp()
    as_of = now if as_of is None else as_of
    if lo is None or hi is None:
        lo, hi = resolve_range(None, None, period, cfg, now)
    if group_by == "hour" and hi - lo > MAX_HOUR_DAYS * 86400:
        raise OeeError(_("oee_hour_range", n=MAX_HOUR_DAYS))
    with SessionLocal() as s:
        if machine:
            rows = s.scalars(select(OeeMachineRow).where(OeeMachineRow.key == machine)).all()
            if not rows:
                raise OeeNotFound(_("oee_machine_unknown", k=machine[:64]))
        else:
            rows = [r for r in s.scalars(select(OeeMachineRow).order_by(OeeMachineRow.id)).all() if r.active is not False]
        profs = [(r.key, r.name, r.kind or "saw", profile_of(r)) for r in rows]
    reasons = {r["code"]: r for r in list_reasons()}
    planned_codes = {c for c, r in reasons.items() if r["planned"]}
    shift_rows = list_shifts()
    data = _load([p[0] for p in profs], lo, hi)
    tls: list[tuple[str, str, str, C.Timeline, list]] = []
    for key, name, kind, prof in profs:
        runs, downs, rejs = data[key]
        insts = expand_shifts(shift_rows, key, lo - 86400, hi + 86400, cfg.tz_offset_min)
        tl = C.build_timeline(prof, planned_intervals(insts), planned_codes, runs, downs, rejs, ecfg, lo, hi, as_of, key)
        has = any(lo < r.end <= tl.hi or (r.start is not None and r.start < tl.hi and r.end > lo) for r in runs) \
            or any(d.start < tl.hi and (d.end is None or d.end > lo) for d in downs) \
            or any(lo < j.ts <= tl.hi for j in rejs)
        tl.has_data = has
        tls.append((key, name, kind, tl, insts if has else []))
    live = [t for t in tls if t[3].has_data]

    # summary + stanoklar (ma'lumoti yo'q stanok yig'indiga kirmaydi: 0 % emas, «ma'lumot yo'q»)
    machines_out = []
    total = C.Comp()
    for key, name, kind, tl, _insts in tls:
        c = C.components(tl, lo, hi, ecfg)
        d = dict(machine=key, name=name, kind=kind, has_data=tl.has_data)
        d.update(_metrics(c) if tl.has_data else {})
        if tl.has_data:
            total.add(c)
        machines_out.append(d)
    summary = _metrics(total)
    summary["machines"] = len(live)
    material = _material([t[3] for t in live])
    for mo, t in zip(machines_out, tls):
        if mo["has_data"]:
            mo["material"] = _material([t[3]])

    # qatorlar (soat / smena / kun / hafta): har bo'lak uchun komponentlar yig'indisi (bo'laklar yig'indisi = butun oyna)
    def build_series(g: str) -> list[dict]:
        buckets: list[tuple[float, float, str, dict]] = []
        if g == "shift":
            seen: set[tuple[float, float, str]] = set()
            for _k, _n, _kd, _tl, insts in live:
                for i in insts:
                    kk = (i["start"], i["end"], i["name"])
                    if kk in seen or i["end"] <= lo or i["start"] >= hi:
                        continue
                    seen.add(kk)
                    buckets.append((max(i["start"], lo), min(i["end"], hi), f"{i['date']} {i['name']}",
                                    dict(name=i["name"], date=i["date"])))
            buckets.sort(key=lambda b: (b[0], b[1]))
        else:
            for a, b, s0 in C.bucket_edges(lo, hi, g, cfg.tz_offset_min):
                buckets.append((a, b, C.local_label(s0, cfg.tz_offset_min, g), {}))
        out = []
        for a, b, label, extra in buckets:
            c = C.Comp()
            for _k, _n, _kd, tl, _i in live:
                c.add(C.components(tl, a, b, ecfg))
            out.append(dict(start=C.iso_utc(a), end=C.iso_utc(b), label=label, **extra, **_metrics(c)))
        return out
    series = build_series(group_by)
    extra_series = {g: build_series(g) for g in also if g in GROUPS and g != group_by}

    # Pareto (rejalashtirilmagan to'xtashlar, daqiqa) + rejalashtirilgan to'xtashlar
    secs: dict[str, float] = {}
    cnts: dict[str, int] = {}
    psecs: dict[str, float] = {}
    pcnts: dict[str, int] = {}
    for _k, _n, _kd, tl, _i in live:
        for rs, st in tl.ud_by_reason.items():
            secs[rs] = secs.get(rs, 0.0) + st.measure(lo, hi)
            cnts[rs] = cnts.get(rs, 0) + tl.ud_count.get(rs, 0)
        isec = tl.idle.measure(lo, hi)
        if isec > 0:
            secs[C.IDLE] = secs.get(C.IDLE, 0.0) + isec
            cnts[C.IDLE] = cnts.get(C.IDLE, 0) + sum(1 for a, b in tl.idle_segments if b > lo and a < hi)
        for rs, st in tl.pd_by_reason.items():
            psecs[rs] = psecs.get(rs, 0.0) + st.measure(lo, hi)
            pcnts[rs] = pcnts.get(rs, 0) + tl.pd_count.get(rs, 0)

    def item(rs: str, sec: float, cnt: int, planned: bool) -> dict:
        info = reasons.get(rs)
        ru = IDLE_NAMES[0] if rs == C.IDLE else (info["name_ru"] if info else rs)
        uz = IDLE_NAMES[1] if rs == C.IDLE else (info["name_uz"] if info else rs)
        return dict(reason=rs, name_ru=ru, name_uz=uz, minutes=round(sec / 60.0, 2), count=cnt, planned=planned)
    pareto = sorted((item(rs, v, cnts.get(rs, 0), False) for rs, v in secs.items() if v > 0),
                    key=lambda x: (-x["minutes"], x["reason"]))          # teng bo'lsa — kod bo'yicha (barqaror tartib)
    tot_min = sum(p["minutes"] for p in pareto)
    cum = 0.0
    for p in pareto:
        p["share"] = round(p["minutes"] / tot_min, 4) if tot_min > 0 else 0.0
        cum += p["share"]
        p["cumulative"] = round(min(1.0, cum), 4)
    planned_list = sorted((item(rs, v, pcnts.get(rs, 0), True) for rs, v in psecs.items() if v > 0),
                          key=lambda x: (-x["minutes"], x["reason"]))

    # ogohlantirishlar
    warns: list[dict] = []
    if any(t[3].has_data and t[3].raw_runs and not t[3].p_eff.iv for t in tls):
        warns.append(dict(code="no_calendar"))
    ni = sum(t[3].no_ideal for t in live)
    if ni:
        warns.append(dict(code="no_ideal", count=ni))
    if summary.get("capped"):
        warns.append(dict(code="p_capped"))
    if total.fallback:
        warns.append(dict(code="unit_fallback", count=int(total.fallback)))
    if total.outside_sheets > 0:
        warns.append(dict(code="outside_shift", count=round(total.outside_sheets, 2)))
    nd = [t[0] for t in tls if not t[3].has_data]
    if nd:
        warns.append(dict(code="no_data", machines=nd))
    opened = sum(t[3].open_closed for t in live)
    if opened:
        warns.append(dict(code="open_downtime", count=opened))
    return dict(machine=machine, **{"from": C.iso_utc(lo), "to": C.iso_utc(hi)}, as_of=C.iso_utc(as_of), group_by=group_by,
                config=cfg.model_dump(), bands=dict(low=C.BAND_LOW, high=C.BAND_HIGH), summary=summary,
                machines=machines_out, material=material, series=series, extra_series=extra_series, pareto=pareto,
                pareto_total_min=round(tot_min, 2), planned_losses=planned_list, warnings=warns)


def idle_gaps(machine: str, lo: float, hi: float, as_of: Optional[float] = None, limit: int = 100) -> list[dict]:
    """Hodisasiz (`idle`) bo'shliqlar — foydalanuvchi sabab belgilashi uchun (to'xtash hodisasiga aylantiriladi)."""
    cfg = get_config()
    ecfg = _engine_cfg(cfg)
    now = utc_now().replace(tzinfo=_UTC).timestamp()
    as_of = now if as_of is None else as_of
    with SessionLocal() as s:
        r = s.scalar(select(OeeMachineRow).where(OeeMachineRow.key == machine))
        if r is None:
            raise OeeNotFound(_("oee_machine_unknown", k=machine[:64]))
        prof = profile_of(r)
    reasons = {x["code"]: x for x in list_reasons()}
    planned_codes = {c for c, x in reasons.items() if x["planned"]}
    runs, downs, rejs = _load([machine], lo, hi)[machine]
    insts = expand_shifts(list_shifts(), machine, lo - 86400, hi + 86400, cfg.tz_offset_min)
    tl = C.build_timeline(prof, planned_intervals(insts), planned_codes, runs, downs, rejs, ecfg, lo, hi, as_of, machine)
    out = [dict(start=C.iso_utc(a), end=C.iso_utc(b), minutes=round((b - a) / 60.0, 2)) for a, b in tl.idle_segments]
    return out[-limit:][::-1]
