"""«Настройки → MES интеграция → XNC → MES» (2026-10-25, foydalanuvchi talabi): XNC ishini MES (ERP + moliya) ga yuborish
sozlamasi — yoqilgan / o'chiq, nima yuboriladi (parma teshiklari, freza metri, chuqurlik o'tishlari, arra pazi, har detal
bo'yicha batafsil) va har asbobning MES dagi kodi (moliya narxni o'z kodi bo'yicha bog'laydi — MX nomi farq qilsa ham).

Asbob kaliti: `kind|nom|diametr|tomon|teshib_o'tadi` (`xnc_tool_stats` dagi guruh bilan bir xil).
Sozlama: `settings` scope `xnc_mes` (standart profil).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class XncMesCode(BaseModel):
    kind: Literal["drill", "mill", "saw"]
    name: str = Field(max_length=60)
    d: float = Field(0, ge=0, le=1000)
    side: str = Field("", max_length=10)
    through: bool = False
    mes_code: str = Field("", max_length=60)
    comment: str = Field("", max_length=200)


class XncMesSettings(BaseModel):
    enabled: bool = True                # MES paketida `xnc_tools` bo'limi
    send_holes: bool = True             # parma: teshiklar soni
    send_mill: bool = True              # freza: kontur metri
    send_mill_passes: bool = True       # freza: chuqurlik qadamlari bilan metr
    send_saw: bool = True               # arra pazi: metr
    send_parts: bool = True             # har detal / operatsiya bo'yicha batafsil (`uses`)
    codes: list[XncMesCode] = Field(default_factory=list, max_length=2000)


def tool_key(kind: str, name: str, d: float, side: str = "", through: bool = False) -> str:
    return f"{kind}|{(name or '').strip().casefold()}|{float(d or 0):g}|{side or ''}|{int(bool(through))}"


def load() -> XncMesSettings:
    from . import settings
    try:
        return XncMesSettings.model_validate(settings.get_default("xnc_mes") or {})
    except Exception:  # noqa: BLE001
        return XncMesSettings()


def code_map(cfg: Optional[XncMesSettings] = None) -> dict[str, XncMesCode]:
    cfg = cfg or load()
    return {tool_key(c.kind, c.name, c.d, c.side, c.through): c for c in cfg.codes}


def with_codes(summary: dict, cfg: Optional[XncMesSettings] = None) -> dict:
    """Har asbobga `key` va `mes_code` (sozlamadan) qo'shiladi."""
    cm = code_map(cfg)
    for t in summary.get("tools", []):
        t["key"] = tool_key(t["kind"], t["name"], t["d"], t["side"], t["through"])
        c = cm.get(t["key"])
        t["mes_code"] = c.mes_code if c else ""
    return summary


def mes_view(summary: dict, cfg: Optional[XncMesSettings] = None) -> dict:
    """MES ga AYNAN ketadigan ko'rinish: sozlama bo'yicha keraksiz qiymatlar 0 / olib tashlanadi; o'chiq — bo'sh."""
    cfg = cfg or load()
    s = with_codes({**summary, "tools": [dict(t) for t in summary.get("tools", [])]}, cfg)
    if not cfg.enabled:
        return dict(enabled=False, xnc_ops=0, xnc_parts=0, tools=[], errors=[])
    tools = []
    for t in s["tools"]:
        if t["kind"] == "drill" and not cfg.send_holes:
            continue
        if t["kind"] == "mill" and not (cfg.send_mill or cfg.send_mill_passes):
            continue
        if t["kind"] == "saw" and not cfg.send_saw:
            continue
        t = dict(t)
        if not cfg.send_mill:
            t["mill_m"] = 0.0
        if not cfg.send_mill_passes:
            t["mill_pass_m"] = 0.0
        if not cfg.send_parts:
            t["uses"] = []
        tools.append(t)
    return dict(enabled=True, xnc_ops=s["xnc_ops"], xnc_parts=s["xnc_parts"], tools=tools, errors=s.get("errors", []))


def tool_rows(project_summary: Optional[dict] = None, cfg: Optional[XncMesSettings] = None) -> list[dict]:
    """Sozlama sahifasidagi asboblar jadvali: XNC asboblar jadvalidagi parmalar + sozlamada kodi bor asboblar + (berilsa)
    loyihada uchragan asboblar (frezalar, arralar). [{key, kind, name, d, side, through, mes_code, comment, in_project}]."""
    cfg = cfg or load()
    rows: dict[str, dict] = {}

    def add(kind, name, d, side="", through=False, **extra):
        k = tool_key(kind, name, d, side, through)
        r = rows.setdefault(k, dict(key=k, kind=kind, name=name, d=float(d or 0), side=side, through=bool(through),
                                    mes_code="", comment="", in_project=False))
        r.update({k2: v for k2, v in extra.items() if v is not None})
        return r

    try:
        from . import settings
        from .xnc_tools import XncToolsDoc
        for t in XncToolsDoc.model_validate(settings.get_default("xnc_tools")).tools:
            add("drill", t.name, t.d, "face" if t.plane == "front" else "side", t.through)
    except Exception:  # noqa: BLE001
        pass
    for c in cfg.codes:
        add(c.kind, c.name, c.d, c.side, c.through, mes_code=c.mes_code, comment=c.comment)
    for t in (project_summary or {}).get("tools", []):
        add(t["kind"], t["name"], t["d"], t["side"], t["through"], in_project=True)
    return sorted(rows.values(), key=lambda r: ({"drill": 0, "mill": 1, "saw": 2}[r["kind"]], r["name"].casefold(), r["d"], r["side"]))
