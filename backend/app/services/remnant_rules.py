"""Qoldiqni olib qolish qoidalari (foydalanuvchi talabi, 2026-10-24).

Kroydan keyingi har bir qoldiq bo'lagi FOIZ bilan baholanadi: bo'lak maydoni (list chetigacha, xom o'lcham) / shu
materialning butun list maydoni × 100. Material uchun belgilangan foizdan kichik bo'lmasa — korxona olib qoladi (omborga
yoziladi), kichigi — mijozga beriladi (hisobotda ko'rinadi, omborga yozilmaydi). Faqat foiz hal qiladi (min. tomonlar emas).

Foiz MATERIAL TURI bo'yicha (LDSP, LMDF, AKRIL, HDF …) va kerak bo'lsa aniq material uchun (nom / kod) beriladi —
material qoidasi tur qoidasidan ustun. Qoida yo'q material — avvalgi xulq (деловой qoldiq: min. tomonlar va maydon).

Tur: MES kodi `M-LD-…` (guruh) bo'lsa — guruhdan, aks holda nomning birinchi so'zidan. Material nomlari katta-kichik
harf va bo'shliqlarsiz solishtiriladi («LDSP KASHMIR SHAGREN» = «ldsp  kashmir shagren»).

Sozlama: `settings` scope `remnant_rules` (standart profil).
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models import Operation, OpType

# MES katalog kodi `K-GG-MMM-VV`: materiallar guruhi → tur
MES_GROUP = {"LD": "LDSP", "LM": "LMDF", "HD": "HDF", "XD": "XDF", "MD": "MDF", "AK": "AKRIL", "DS": "DSP", "FN": "FANERA"}
# nomning birinchi so'zi (kirill / boshqa yozilish) → tur
TYPE_ALIAS = {"ЛДСП": "LDSP", "ЛМДФ": "LMDF", "МДФ": "MDF", "ХДФ": "HDF", "ДСП": "DSP", "АКРИЛ": "AKRIL", "AKRYL": "AKRIL",
              "ACRYL": "AKRIL", "ACRYLIC": "AKRIL", "ФАНЕРА": "FANERA", "DVP": "HDF", "ДВП": "HDF"}
# sozlamalar sahifasida doim ko'rinadigan turlar
COMMON_TYPES = ("LDSP", "LMDF", "MDF", "HDF", "XDF", "AKRIL")

_WORD = re.compile(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ]+")
_MES_CODE = re.compile(r"^\s*M-([A-Z]{2})-", re.IGNORECASE)


def norm(s: Optional[str]) -> str:
    """Material nomi / kodini solishtirish uchun: kichik harf, bitta bo'shliq, «ё» → «е»."""
    return " ".join((s or "").lower().replace("ё", "е").split())


def material_type(code: Optional[str], name: Optional[str]) -> str:
    m = _MES_CODE.match(code or "")
    if m and m.group(1).upper() in MES_GROUP:
        return MES_GROUP[m.group(1).upper()]
    for src in (name, code):
        w = _WORD.search(src or "")
        if w:
            t = w.group(0).upper()
            return TYPE_ALIAS.get(t, t)
    return ""


class TypeRule(BaseModel):
    type: str = Field(min_length=1, max_length=40)
    keep_percent: float = Field(gt=0, le=100, allow_inf_nan=False)

    @field_validator("type")
    @classmethod
    def _t(cls, v: str) -> str:
        v = v.strip().upper()
        return TYPE_ALIAS.get(v, v)


class MaterialRule(BaseModel):
    material: str = Field("", max_length=300)          # nom (norm bilan solishtiriladi)
    code: str = Field("", max_length=100)              # kod (bo'lsa — avval kod bo'yicha)
    keep_percent: float = Field(gt=0, le=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def _any(self):
        if not self.material.strip() and not self.code.strip():
            raise ValueError("material / code")
        return self


class RemnantRules(BaseModel):
    types: list[TypeRule] = []
    materials: list[MaterialRule] = []
    # olib qolingan qoldiq MES «list arradan chiqdi» signaligacha «kutilmoqda» (boshqa buyurtmaga berilmaydi); MES integratsiyasi
    # yoqilmagan bo'lsa — darhol «mavjud»
    wait_mes: bool = True
    # kroydan keyin olib qolinadigan qoldiqlar omborga avtomatik yoziladi (tasdiqsiz)
    auto_commit: bool = False
    # ombor manbasi: local — MX jadvali (MES API tayyor bo'lguncha), mes — MES bazasi (`mes_url`, services/remnant_store.py)
    source: Literal["local", "mes"] = "local"
    mes_url: str = Field("", max_length=500)
    # bazadan topib qo'shish: nechta eng kichik nomzod sinaladi va qidiruv vaqti (kroydan keyin, s)
    find_limit: int = Field(5, ge=1, le=20)
    find_seconds: float = Field(8, ge=1, le=30)

    @model_validator(mode="after")
    def _dedupe(self):
        seen, ts = set(), []
        for r in self.types:
            if r.type not in seen:
                seen.add(r.type)
                ts.append(r)
        self.types = ts
        seen2, ms = set(), []
        for r in self.materials:
            k = (norm(r.code), norm(r.material))
            if k not in seen2:
                seen2.add(k)
                ms.append(r)
        self.materials = ms
        return self


def load() -> RemnantRules:
    from . import settings
    try:
        return RemnantRules.model_validate(settings.get_default("remnant_rules") or {})
    except Exception:  # noqa: BLE001 — buzilgan sozlama kroyni to'xtatmasin
        return RemnantRules()


def rule_for(code: Optional[str], name: Optional[str], rules: Optional[RemnantRules] = None) -> Optional[tuple[float, str]]:
    """(foiz, manba) — manba: «material» | «type»; qoida yo'q — None."""
    rules = rules or load()
    nc, nn = norm(code), norm(name)
    for r in rules.materials:
        if r.code.strip() and nc and norm(r.code) == nc:
            return r.keep_percent, "material"
    for r in rules.materials:
        if r.material.strip() and nn and norm(r.material) == nn:
            return r.keep_percent, "material"
    t = material_type(code, name)
    for r in rules.types:
        if t and r.type == t:
            return r.keep_percent, "type"
    return None


def op_rule(op: Operation, rules: Optional[RemnantRules] = None) -> Optional[tuple[float, str]]:
    if op.type != OpType.CS:
        return None
    return rule_for(op.code, op.name, rules)


def sheet_area_mm2(op: Operation) -> float:
    """Foiz uchun butun list maydoni (mm²): ro'yxatdagi eng katta qoldiq bo'lmagan list (odatda cheksiz), bo'lmasa natijadagi
    qoldiq bo'lmagan kartaning listi, bo'lmasa eng katta list."""
    full = [s for s in op.sheets if not s.is_remnant and not s.source_remnant_id]
    pool = [s for s in full if s.qty >= 10000] or full
    if pool:
        return max(s.length * s.width for s in pool)
    if op.result:
        ms = [m for m in op.result.maps if not m.is_remnant]
        if ms:
            return max(m.sheet_length * m.sheet_width for m in ms)
    return max((s.length * s.width for s in op.sheets), default=0.0)


def percent_of(length: float, width: float, sheet_mm2: float) -> float:
    return round(length * width / sheet_mm2 * 100, 1) if sheet_mm2 > 0 else 0.0


def classify(op: Operation, rules: Optional[RemnantRules] = None) -> Optional[dict]:
    """Natijadagi qoldiq bo'laklari foiz bo'yicha: {percent (qoida), source, sheet_m2, pieces: [{map, length, width, area_m2,
    percent, keep, copies, kind, business}]} (xom o'lcham — list chetigacha). Qoida yo'q yoki natija yo'q — None."""
    r = op_rule(op, rules)
    if r is None or not op.result:
        return None
    S = sheet_area_mm2(op)
    pieces = []
    for m in op.result.maps:
        for o in m.offcuts:
            if getattr(o, "in_part", False):
                continue
            L, W = (o.raw_length or o.length), (o.raw_width or o.width)
            if L <= 0 or W <= 0:
                continue
            p = percent_of(L, W, S)
            pieces.append(dict(map=m.index, length=round(max(L, W), 1), width=round(min(L, W), 1),
                               area_m2=round(L * W / 1e6, 3), percent=p, keep=p >= r[0] - 1e-9, copies=m.copies,
                               kind=o.kind, business=bool(o.business), ul=o.length, uw=o.width))
    return dict(percent=r[0], source=r[1], sheet_m2=round(S / 1e6, 3), pieces=pieces)
