"""Stanok asboblari jadvali («Инструменты»): parma / o'tuvchi parma / freza / paz arrasi → stanokdagi raqami yoki nomi.

Qoidalar (manba: docs/mebelix/postprocessors/WEB_tooling.md): teshik ko'p formatlarda diametr bilan beriladi — shpindelni stanok
o'zi tanlaydi; freza va paz arrasi (ayrim formatlarda parmalar ham) aniq asbob raqami / nomini talab qiladi. Bu qiymatlar
stanokka bog'liq — «Настройки → Постпроцессоры → <stanok> → Инструменты» jadvalida saqlanadi (`pp_machine_ctx.get_tools`).

Kalit: `<tur>:<tekislik>:<diametr>`; tur — drill | through | mill | saw; tekislik — front (yuza) | left | right | top | bottom
| back (orqa yuza). Generator: `tool_ref(job, "mill", "front", 8)` → "" bo'lsa asbob ko'rsatilmagan.
"""
from __future__ import annotations

from typing import Any, Optional

KINDS = ("drill", "through", "mill", "saw")
PLANES = ("front", "left", "right", "top", "bottom", "back")

# Jadvalning standart qatorlari (mebel sexining odatiy to'plami; diametrlar — taklif, foydalanuvchi o'zgartiradi)
STD_ROWS: tuple[tuple[str, str, float], ...] = (
    ("drill", "front", 3), ("drill", "front", 5), ("through", "front", 5), ("drill", "front", 8), ("through", "front", 8),
    ("drill", "front", 10), ("drill", "front", 15), ("drill", "front", 20), ("drill", "front", 35),
    ("drill", "left", 4.5), ("drill", "left", 8), ("drill", "right", 4.5), ("drill", "right", 8),
    ("drill", "top", 4.5), ("drill", "top", 8), ("drill", "bottom", 4.5), ("drill", "bottom", 8),
    ("mill", "front", 8), ("saw", "front", 4),
)

# Stanok bo'yicha standart qiymatlar (bo'sh — diametr bo'yicha avtomatik / ko'rsatilmagan)
DEFAULTS: dict[str, dict[str, str]] = {}


def _n(d: float) -> str:
    r = round(float(d), 3)
    return str(int(r)) if r == int(r) else f"{r:.3f}".rstrip("0").rstrip(".")


def tool_key(kind: str, plane: str, d: float) -> str:
    return f"{kind}:{plane}:{_n(d)}"


def std_rows(machine: str) -> list[dict[str, Any]]:
    """Jadval qatorlari (standart + stanok standart qiymati)."""
    dflt = DEFAULTS.get(machine, {})
    return [dict(key=tool_key(k, p, d), kind=k, plane=p, d=d, ref=dflt.get(tool_key(k, p, d), "")) for k, p, d in STD_ROWS]


def tool_ref(job: Any, kind: str, plane: str, d: float, default: str = "") -> str:
    """Asbobning stanokdagi raqami / nomi: foydalanuvchi jadvali → stanok standarti → `default`."""
    key = tool_key(kind, plane, d)
    tools = (getattr(job, "params", None) or {}).get("tools") or {}
    v = str(tools.get(key, "") or "").strip()
    if v:
        return v
    v = DEFAULTS.get(getattr(job, "machine", "") or "", {}).get(key, "")
    return v or default


def need_tool(job: Any, kind: str, plane: str, d: float, what: str = "") -> str:
    """Majburiy asbob: ko'rsatilmagan bo'lsa — tushunarli xato (FormatError ga aylanadi)."""
    v = tool_ref(job, kind, plane, d)
    if not v:
        ru = {"drill": "сверло", "through": "сквозное сверло", "mill": "фреза", "saw": "пазовая пила"}[kind]
        raise ValueError(f"не указан инструмент станка: {ru} Ø{_n(d)} ({plane}){' — ' + what if what else ''}. "
                         f"Настройки → Постпроцессоры → станок → Инструменты")
    return v


def ref_int(v: str, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default
