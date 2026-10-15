"""XNC muharriri sozlamalari (W8): «Инструменты» (asboblar jadvali) va «Палитра» (buyruq belgilari).

Sozlama doiralari (`settings_profiles`, standart profil — `settings.get_default / set_default`):
  xnc_tools    — XncToolsDoc: asboblar jadvali (tekislik, diametr, tuynuk (o'tuvchi), nom, chuqurlik, izoh)
  xnc_palette  — XncPalette: palitradagi buyruqlar tartibi va yoqilganligi

Asbob sozlamasi hisobda zaxira sifatida qatnashadi (`xnc.py`): drill/freza/paz buyrug'ida `T` nomi bo'yicha diametr (`D`) va
chuqurlik (`DP`) berilmagan bo'lsa shu jadvaldan olinadi. Ustuvorlik: buyruqdagi qiymat → dasturdagi `Tool` buyrug'i → sozlama
jadvali → standart (teshik 5 mm, paz 4 mm, chuqurlik = qalinlik). Jadval kesh bilan o'qiladi (`current_library`):
hisob ming martalab chaqirilishi mumkin; sozlama o'zgarganda `invalidate()` chaqiriladi (settings.py).
"""
from __future__ import annotations

import time
import typing
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ..i18n import _
from ..models import Base, XncCmd

PLANES = ("front", "left", "right", "top", "bottom")
Plane = Literal["front", "left", "right", "top", "bottom"]
PLANE_OF_CMD = {"DrillFront": "front", "DrillLeft": "left", "DrillRight": "right", "DrillTop": "top", "DrillBottom": "bottom"}
MAX_TOOLS = 500

# «Standart to'plam»: frontal tekislikda Bore<diametr>, yon tekisliklarda Bore8 va Bore4.5 (nom — diametrdan; o'zimiz yozdik)
DEFAULT_FRONT_D = (35, 26, 25, 20, 18, 15, 10, 8, 7, 5, 4.5, 3)
DEFAULT_SIDE_D = (8, 4.5)
DEFAULT_SIDE_PLANES = ("left", "right", "top", "bottom")


class XncTool(Base):
    """Asboblar jadvali qatori. `depth` — asbobning standart chuqurligi (bo'sh — buyruq o'zi beradi / qalinlik);
    `through` (faqat frontal) — o'tuvchi teshik asbobi: chuqurlik = qalinlik."""
    plane: Plane = "front"
    d: float = Field(8, gt=0, le=1000)
    through: bool = False
    name: str = Field("", max_length=40)
    depth: float | None = Field(None, ge=0, le=1000)
    comment: str = Field("", max_length=200)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError(_("xnc_tools_noname"))
        return v

    @model_validator(mode="after")
    def _plane_rules(self):
        if self.plane != "front":
            self.through = False            # o'tuvchi belgisi faqat frontal tekislik uchun
        return self


def default_tools() -> list[XncTool]:
    rows = [XncTool(plane="front", d=d, name=f"Bore{d:g}") for d in DEFAULT_FRONT_D]
    for pl in DEFAULT_SIDE_PLANES:
        rows += [XncTool(plane=pl, d=d, name=f"Bore{d:g}") for d in DEFAULT_SIDE_D]
    return rows


class XncToolsDoc(Base):
    tools: list[XncTool] = Field(default_factory=default_tools, max_length=MAX_TOOLS)

    @field_validator("tools")
    @classmethod
    def _unique(cls, v: list[XncTool]) -> list[XncTool]:
        seen: set[tuple[str, str]] = set()
        for t in v:
            k = (t.plane, t.name.casefold())
            if k in seen:
                raise ValueError(_("xnc_tools_dup", name=t.name, plane=t.plane))
            seen.add(k)
        return v


class ToolLib:
    """Hisob uchun asbob qidiruvi: (tekislik, nom) aniq; topilmasa — nom bo'yicha birinchisi."""

    def __init__(self, tools: list[XncTool]):
        self.tools = list(tools)
        self._exact = {(t.plane, t.name.casefold()): t for t in tools}
        self._by_name: dict[str, XncTool] = {}
        for t in tools:
            self._by_name.setdefault(t.name.casefold(), t)

    def __bool__(self) -> bool:
        return bool(self.tools)

    def find(self, name: str, plane: str | None = None) -> XncTool | None:
        key = (name or "").strip().casefold()
        if not key:
            return None
        if plane:
            t = self._exact.get((plane, key))
            if t is not None:
                return t
        return self._by_name.get(key)


def library_of(doc: XncToolsDoc | dict | None = None) -> ToolLib:
    """Hujjatdan (yoki standart to'plamdan) qidiruv jadvali."""
    if doc is None:
        doc = XncToolsDoc()
    elif isinstance(doc, dict):
        doc = XncToolsDoc.model_validate(doc)
    return ToolLib(doc.tools)


# ───────────────────────── Palitra ─────────────────────────
ALL_CMDS: tuple[str, ...] = typing.get_args(XncCmd)      # palitradagi buyruqlar (tartib — standart)


class PaletteItem(Base):
    cmd: str
    enabled: bool = True


class XncPalette(Base):
    """Palitra: har buyruq bir marta; noma'lum buyruq tashlanadi, yetishmaganlari oxiriga (yoqilgan holda) qo'shiladi —
    yangi buyruq paydo bo'lganda eski sozlama uni yashirib qo'ymaydi."""
    items: list[PaletteItem] = Field(default_factory=lambda: [PaletteItem(cmd=c) for c in ALL_CMDS])

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data):
        if not isinstance(data, dict):
            return {}
        raw = data.get("items")
        if raw is None:                                   # yo'q / null — standart palitra
            return {k: v for k, v in data.items() if k != "items"}
        out, seen = [], set()
        for it in raw if isinstance(raw, list) else []:
            if isinstance(it, str):
                it = {"cmd": it}
            if not isinstance(it, dict):
                continue
            cmd = it.get("cmd")
            if cmd in ALL_CMDS and cmd not in seen:
                seen.add(cmd)
                out.append({"cmd": cmd, "enabled": bool(it.get("enabled", True))})
        out += [{"cmd": c, "enabled": True} for c in ALL_CMDS if c not in seen]
        return {**data, "items": out}

    def enabled_cmds(self) -> list[str]:
        return [i.cmd for i in self.items if i.enabled]


# ───────────────────────── Hisob uchun joriy jadval (kesh) ─────────────────────────
LIB_TTL = 3.0                         # soniya: hisob tez-tez chaqiriladi, sozlama kamdan-kam o'zgaradi
_cache: dict = {"t": -1e9, "lib": None}


def invalidate() -> None:
    _cache["t"] = -1e9
    _cache["lib"] = None


def current_library() -> ToolLib | None:
    """Sozlamadagi (standart profil) asboblar jadvali; baza mavjud bo'lmasa / xato bo'lsa — None (sozlamasiz hisob)."""
    now = time.monotonic()
    if now - _cache["t"] < LIB_TTL:
        return _cache["lib"]
    try:
        from . import settings
        lib: ToolLib | None = ToolLib(XncToolsDoc.model_validate(settings.get_default("xnc_tools")).tools)
    except Exception:  # noqa: BLE001 — hisob sozlama xatosi tufayli yiqilmasin
        lib = None
    _cache["t"], _cache["lib"] = now, lib
    return lib


def current_palette() -> XncPalette:
    try:
        from . import settings
        return XncPalette.model_validate(settings.get_default("xnc_palette"))
    except Exception:  # noqa: BLE001
        return XncPalette()
