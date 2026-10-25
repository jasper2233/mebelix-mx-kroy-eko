"""«Настройки → MES интеграция → XNC → MES» (2026-10-25, foydalanuvchi talabi): XNC ishini MES (ERP + moliya) ga yuborish
sozlamasi — yoqilgan / o'chiq, nima yuboriladi (parma teshiklari, freza metri, chuqurlik o'tishlari, arra pazi, har detal
bo'yicha batafsil) va har asbobning MES dagi kodi (moliya narxni o'z kodi bo'yicha bog'laydi — MX nomi farq qilsa ham).

Asbob kaliti: `kind|nom|diametr|tomon|teshib_o'tadi` (`xnc_tool_stats` dagi guruh bilan bir xil).
Sozlama: `settings` scope `xnc_mes` (standart profil).
"""
from __future__ import annotations

import re
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
    # (2026-10-25) «bizning asboblar» ro'yxati: faqat korxona ishlatadigan asboblar; o'chirilgani (active=False) —
    # buyurtmada uchrasa «noma'lum asbob» ogohlantirishi; usage — nechta loyihada uchragani (oxirgi yig'ishda)
    active: bool = True
    usage: int = Field(0, ge=0)


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


_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s*$")


def mismatch(name: str, d: float) -> bool:
    """Asbob nomidagi raqam (Bore35, Mill8, BoreTh4.5) uning diametriga mos emas — dasturda adashib yozilgan bo'lishi mumkin."""
    m = _NUM.search((name or "").strip())
    if not m or not d:
        return False
    try:
        return abs(float(m.group(1).replace(",", ".")) - float(d)) > 0.01
    except ValueError:
        return False


def with_codes(summary: dict, cfg: Optional[XncMesSettings] = None) -> dict:
    """Har asbobga `key`, `mes_code`, `known` (bizning ro'yxatda va faol; ro'yxat bo'sh bo'lsa — hammasi ma'lum) va
    `mismatch` (nom — diametr mos emas) qo'shiladi."""
    cfg = cfg or load()
    cm = code_map(cfg)
    listed = bool(cfg.codes)
    for t in summary.get("tools", []):
        t["key"] = tool_key(t["kind"], t["name"], t["d"], t["side"], t["through"])
        c = cm.get(t["key"])
        t["mes_code"] = c.mes_code if c else ""
        t["known"] = (c is not None and c.active) if listed else True
        t["mismatch"] = mismatch(t["name"], t["d"])
    return summary


def mes_view(summary: dict, cfg: Optional[XncMesSettings] = None) -> dict:
    """MES ga AYNAN ketadigan ko'rinish: sozlama bo'yicha keraksiz qiymatlar 0 / olib tashlanadi; o'chiq — bo'sh."""
    cfg = cfg or load()
    s = with_codes({**summary, "tools": [dict(t) for t in summary.get("tools", [])]}, cfg)
    if not cfg.enabled:
        return dict(enabled=False, xnc_ops=0, xnc_parts=0, tools=[], errors=[], warnings=[])
    warnings = [f"unknown_tool:{t['name']} D{t['d']:g}" for t in s["tools"] if not t["known"]]
    warnings += [f"name_diameter_mismatch:{t['name']} D{t['d']:g}" for t in s["tools"] if t["mismatch"]]
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
    return dict(enabled=True, xnc_ops=s["xnc_ops"], xnc_parts=s["xnc_parts"], tools=tools, errors=s.get("errors", []),
                warnings=warnings)


def tool_rows(project_summary: Optional[dict] = None, cfg: Optional[XncMesSettings] = None) -> list[dict]:
    """«Bizning asboblar» jadvali: FAQAT korxona ro'yxati (sozlama); loyiha berilsa — undagi ro'yxatda yo'q asboblar ham
    (`unknown`, qo'shish uchun). [{key, kind, name, d, side, through, mes_code, comment, active, usage, mismatch, in_project, unknown}]."""
    cfg = cfg or load()
    rows: dict[str, dict] = {}
    for c in cfg.codes:
        k = tool_key(c.kind, c.name, c.d, c.side, c.through)
        rows[k] = dict(key=k, kind=c.kind, name=c.name, d=c.d, side=c.side, through=c.through, mes_code=c.mes_code,
                       comment=c.comment, active=c.active, usage=c.usage, mismatch=mismatch(c.name, c.d), in_project=False,
                       unknown=False)
    for t in (project_summary or {}).get("tools", []):
        k = tool_key(t["kind"], t["name"], t["d"], t["side"], t["through"])
        r = rows.get(k)
        if r is None:
            rows[k] = dict(key=k, kind=t["kind"], name=t["name"], d=t["d"], side=t["side"], through=t["through"], mes_code="",
                           comment="", active=False, usage=0, mismatch=mismatch(t["name"], t["d"]), in_project=True, unknown=True)
        else:
            r["in_project"] = True
    return sorted(rows.values(), key=lambda r: (r["unknown"], {"drill": 0, "mill": 1, "saw": 2}[r["kind"]], -r["usage"],
                                               r["name"].casefold(), r["d"], r["side"]))


def scan_projects(limit: int = 20000) -> dict:
    """Korxonaning barcha loyihalaridan haqiqatan ishlatilgan asboblar (nechta loyihada) — «Собрать из проектов»."""
    import json
    from sqlalchemy import select
    from ..db import ProjectRow, SessionLocal
    from ..models import Project
    from .xnc_tool_stats import project_tool_summary
    found: dict[str, dict] = {}
    n = 0
    with SessionLocal() as s:
        for (data,) in s.execute(select(ProjectRow.data).limit(limit)):
            try:
                d = data if isinstance(data, dict) else json.loads(data)
                p = Project.model_validate(d)
            except Exception:  # noqa: BLE001 — o'qib bo'lmaydigan loyiha o'tkazib yuboriladi
                continue
            sm = project_tool_summary(p)
            if not sm["xnc_ops"]:
                continue
            n += 1
            for t in sm["tools"]:
                k = tool_key(t["kind"], t["name"], t["d"], t["side"], t["through"])
                f = found.setdefault(k, dict(kind=t["kind"], name=t["name"], d=t["d"], side=t["side"], through=t["through"], usage=0))
                f["usage"] += 1
    return dict(projects=n, tools=list(found.values()))


def merge_scan(cfg: XncMesSettings, scan: dict) -> XncMesSettings:
    """Yig'ilgan asboblar ro'yxatga qo'shiladi (yangilari — faol), bor asboblarning `usage` i yangilanadi; MES kodi, izoh va
    «Используется» belgisi o'zgarmaydi."""
    have = {tool_key(c.kind, c.name, c.d, c.side, c.through): c for c in cfg.codes}
    out = list(cfg.codes)
    for t in scan["tools"]:
        k = tool_key(t["kind"], t["name"], t["d"], t["side"], t["through"])
        if k in have:
            have[k].usage = t["usage"]
        else:
            c = XncMesCode(kind=t["kind"], name=t["name"], d=t["d"], side=t["side"], through=t["through"], usage=t["usage"])
            out.append(c)
            have[k] = c
    return cfg.model_copy(update={"codes": out})
