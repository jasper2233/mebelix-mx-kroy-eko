"""Раскроечные станки — har stanokning o'z standarti (2026-10-30, foydalanuvchi qarori, xodim loyihasi «1275»).

Sabab: «oxirgi qo'yilgan qoladi» qoidasi bilan bitta operator bitta loyihada pilani 3 → 6 qilgan, u korxona standartiga yozilib,
keyingi import qilingan loyihalarning hammasiga 6 mm bo'lib kelgan (1274, 1275). Onlayn tizimdagidek (`.project`: `good
typeId="tool.cutting"` — Толщина пилы, Высота пакета, вращения, polosalar; operatsiya `tool1` bilan unga havola qiladi):
  • stanok parametrlari (`MACHINE_FIELDS`) operatsiyada o'zgartirilsa — FAQAT o'sha loyihada; standart o'zgarmaydi;
  • yangi CS operatsiya / import (faylda yo'q qiymatlar) — stanok standartidan; foydalanuvchi o'z stanogini tanlashi mumkin
    (`user_machine`: login → stanok), aks holda korxonaning asosiy stanogi;
  • standartni o'zgartirish — ataylab: yozuv huquqi bor login + o'sha loginning paroli; kim / qachon yoziladi.
Sozlama korxonaga tegishli (`settings_profiles`, RLS): har abonentning o'z stanoklari.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# onlayn `tool.cutting` maydonlari + торцовка / отступ (stanok arra tishi va qisqichlariga bog'liq)
MACHINE_FIELDS = ("kerf", "kerf_group", "trim_length", "trim_width", "trim_includes_kerf", "end_offset_bottom",
                  "end_offset_right", "max_rotations", "pack_height", "complex_strips", "strip_sort", "in_strip_sort",
                  "min_strip_width", "max_strip_width", "max_strip_length", "min_trim_cut")
DEFAULT_ID = "main"


class SawMachine(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = Field("", max_length=100)
    cut: dict = Field(default_factory=dict)          # MACHINE_FIELDS qiymatlari (CSCutParams bilan tekshiriladi)
    updated_by: str = ""
    updated_at: str = ""


class SawMachines(BaseModel):
    machines: list[SawMachine] = Field(default_factory=list)
    default_id: Optional[str] = None
    user_machine: dict[str, str] = Field(default_factory=dict)      # login (kichik harf) → stanok id


def clean_cut(cut: dict) -> dict:
    """Faqat stanok maydonlari, CSCutParams qoidalari bilan (noto'g'ri qiymat — ValueError)."""
    from ..models import CSCutParams
    full = CSCutParams.model_validate({k: v for k, v in (cut or {}).items() if k in MACHINE_FIELDS})
    return full.model_dump(mode="json", include=set(MACHINE_FIELDS))


def _seed() -> SawMachines:
    """Hali stanok yozilmagan korxona: bitta asosiy stanok — hozirgi CS standartidan (oldingi xulq saqlanadi)."""
    from . import settings
    from ..models import CSCutParams
    cut = (settings.get_default("cs_defaults") or {}).get("cut") or {}
    try:
        c = clean_cut(cut)
    except ValueError:
        c = clean_cut(CSCutParams().model_dump(mode="json"))
    return SawMachines(machines=[SawMachine(id=DEFAULT_ID, name="", cut=c)], default_id=DEFAULT_ID)


def load() -> SawMachines:
    from . import settings
    d = settings.get_default("saw_machines") or {}
    try:
        sm = SawMachines.model_validate(d)
    except ValueError:
        sm = SawMachines()
    if not sm.machines:
        return _seed()
    if sm.default_id not in {m.id for m in sm.machines}:
        sm.default_id = sm.machines[0].id
    return sm


def save(sm: SawMachines) -> SawMachines:
    from . import settings
    settings.set_default("saw_machines", sm.model_dump(mode="json"))
    return sm


def norm_login(login: Optional[str]) -> str:
    return (login or "").strip().lower()


def machine_for(login: Optional[str] = None, sm: Optional[SawMachines] = None) -> SawMachine:
    """Loginning stanogi (tanlagan bo'lsa), aks holda korxonaning asosiy stanogi."""
    sm = sm or load()
    by = {m.id: m for m in sm.machines}
    mid = sm.user_machine.get(norm_login(login)) if login else None
    return by.get(mid or "") or by.get(sm.default_id or "") or sm.machines[0]


def effective_cs_defaults(login: Optional[str] = None) -> dict:
    """Yangi CS operatsiya / import uchun standart: `cs_defaults` (material va boshqa parametrlar) + stanok parametrlari."""
    from . import settings
    from ..tenant import current_login
    d = settings.get_default("cs_defaults") or {}
    m = machine_for(login if login is not None else (current_login() or "local"))     # tokensiz rejim — «local»
    cut = {**(d.get("cut") or {}), **m.cut, "machine_id": m.id}
    return {**d, "cut": cut}


def stamp(m: SawMachine, login: str) -> None:
    m.updated_by = login or ""
    m.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
