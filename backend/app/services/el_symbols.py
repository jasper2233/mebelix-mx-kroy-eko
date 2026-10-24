"""(EL) «Настройка символов и цветов»: kromka belgilari va ranglari jadvali (ilova sozlamasi, doira `el_symbols`).

Yangi kromka operatsiyasiga navbatdagi **band bo'lmagan** belgi va uning rangi shu jadvaldan beriladi (`next_style`); eski
fayllar importida belgi / rang yozilmagan kromkalarga — tartib bo'yicha (`style_at`). Jadval bo'sh bo'lsa yoki baza mavjud
bo'lmasa — o'rnatilgan standart (A … Z, har biriga o'z rangi).
"""
from __future__ import annotations

import re
import string
import time
from typing import Iterable

from pydantic import Field, field_validator

from ..i18n import _
from ..models import Base

MAX_ROWS = 200
TTL = 2.0                     # s — jadval keshi (import bir necha kromka uchun bazaga qayta-qayta murojaat qilmasin)
_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")
# standart jadvalning davomi (birinchi ranglar — importdagi `_EL_COLORS` va yangi kromka ranglari `mes.EDGE_COLORS`)
_EXTRA_COLORS = ["#8b4513", "#2e8b57", "#4b0082", "#ff1493", "#708090", "#808000", "#00ced1", "#dc143c", "#9acd32", "#ff8c00",
                 "#4169e1", "#a0522d", "#3cb371"]


class ElSymbolRow(Base):
    symbol: str
    color: str

    @field_validator("symbol")
    @classmethod
    def _symbol(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) != 1:
            raise ValueError(_("val_el_symbol"))
        return v

    @field_validator("color")
    @classmethod
    def _color(cls, v: str) -> str:
        v = (v or "").strip()
        if not _COLOR_RE.fullmatch(v):
            raise ValueError(_("val_el_color"))
        return v


def default_rows() -> list[ElSymbolRow]:
    """A … Z, har biriga alohida rang: importdagi standart ranglar, so'ng qolganlari (takrorlarsiz)."""
    from ..plugins.legacy_project import _EL_COLORS
    from .mes import EDGE_COLORS
    colors: list[str] = []
    for c in [*_EL_COLORS, *EDGE_COLORS, *_EXTRA_COLORS]:
        if c.lower() not in {x.lower() for x in colors}:
            colors.append(c)
    return [ElSymbolRow(symbol=s, color=colors[i % len(colors)]) for i, s in enumerate(string.ascii_uppercase)]


class ElSymbolsDoc(Base):
    rows: list[ElSymbolRow] = Field(default_factory=default_rows, max_length=MAX_ROWS)


_cache: dict = {}            # korxona → {"t", "rows"} (har korxonaning o'z sozlamasi)


def invalidate() -> None:
    _cache.clear()


def table() -> list[ElSymbolRow]:
    """Joriy jadval (standart profil); bo'sh / o'qib bo'lmasa — o'rnatilgan standart."""
    from .. import tenant
    now = time.monotonic()
    c = _cache.setdefault(tenant.current(), {"t": -1e9, "rows": None})
    if c["rows"] is not None and now - c["t"] < TTL:
        return c["rows"]
    rows: list[ElSymbolRow] = []
    try:
        from . import settings
        rows = ElSymbolsDoc.model_validate(settings.get_default("el_symbols")).rows
    except Exception:  # noqa: BLE001 — sozlama xatosi yangi kromka qo'shishni buzmasin
        rows = []
    rows = rows or default_rows()
    c["t"], c["rows"] = now, rows
    return rows


def next_style(used_symbols: Iterable[str], n: int = 0) -> tuple[str, str]:
    """Yangi kromka uchun (belgi, rang): jadvaldagi birinchi band bo'lmagan belgi; hammasi band bo'lsa — `n`-qator (aylanib)."""
    rows = table()
    used = {(s or "").strip() for s in used_symbols}
    r = next((r for r in rows if r.symbol not in used), None) or rows[n % len(rows)]
    return r.symbol, r.color


def style_at(i: int) -> tuple[str, str]:
    """Tartib bo'yicha `i`-kromkaning (belgi, rang) i (import: faylda belgi / rang yozilmagan)."""
    rows = table()
    r = rows[i % len(rows)]
    return r.symbol, r.color
