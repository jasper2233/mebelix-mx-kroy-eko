"""CS kroy natijasini `.project` faylining `data` blokiga yozish (MES o'qiydigan kesish kartalari).

Foydalanuvchi qarori (2026-10-19): korxona MES tizimi `.project` faylidan kesish kartalarini `data` blokidan oladi va bloksiz faylni
«optimizatsiya qilinmagan» deb rad etadi; MX eksporti shu blokni o'z kroy natijasidan yozadi. Format tavsifi — korxona MES
dasturchilarining o'z dekoderi (`MebeliX-Mes-System/backend/app/services/giblab/csblob.py`) va foydalanuvchining o'z fayllaridagi
tuzilma; boshqa dastur kodi ishlatilmaydi.

Blok (base64, big-endian): u32 0, u32 1, u8 3, u32 N, so'ng N ta karta:
    u32 mult (shu kartadan listlar soni)
    f64 L, f64 W, u32 stock_part_id, u8 0, 4×f64 −1.0,
    u32 part_count (kataklar × mult), f64 waste_area (ro'yxatga olingan qoldiqlar, m²), u32 part_count, f64 part_area (m²),
    u32 0, f64 waste_area, u32 packets, f64 cut_length (m), u32 cut_count, f64 fill (part_area / list), u32 Nr,
    Nr × 15 bayt yozuv (birinchisi — «slot»): u8 teg (chuqurlik<<3 | tur), f64 o'lcham, u8 0, u8 soni, i32 detal id (−1 — tuzilma).
Turlar: 1 — torsovka/propil, 2 — ichki polosa (bolalari ko'ndalang o'qda), 3 — detal, 4 — ro'yxatga olingan qoldiq.
Yozuvlar — MX «Таблица команд»ining o'zi (T / C / P / W, daraja, o'lcham, soni) preorder tartibida. Birinchi kesimlar Y bo'ylab
(gorizontal polosalar) bo'lsa slot — bo'sh yozuv (0, tur 1, 0.0); X bo'ylab bo'lsa slot — birinchi yozuvning o'zi (odatda torsovka).
"""
from __future__ import annotations

import base64
import struct
from dataclasses import dataclass, field

from ..models import CutMap, CuttingResult

_REC = struct.Struct(">BdBBi")
_TYPE = {"T": 1, "C": 2, "P": 3, "W": 4}


@dataclass
class CutBlob:
    data: str
    stats: dict[str, str] = field(default_factory=dict)
    waste_parts: list[dict] = field(default_factory=list)      # list materiali ichidagi qoldiq qatorlari (id, l, w, business, sheet)


def _vertical(m: CutMap) -> bool:
    """Birinchi (ildiz) kesimlar X bo'ylabmi: ildiz polosasining bolalari X o'qida joylashgan."""
    root = m.strips[0] if m.strips else None
    return (root or {}).get("a", "x") == "x"


def _records(m: CutMap, part_id, waste_id) -> list[tuple[int, int, float, int, int]]:
    out: list[tuple[int, int, float, int, int]] = []
    for c in m.commands:
        t = _TYPE.get(c.code)
        if t is None:                                  # «R» (listni burish) — o'q slot bilan beriladi
            continue
        pid = -1
        if t == 3:
            pid = part_id(c.ref)
        elif t == 4:
            pid = waste_id(m, c.ref)
        out.append((max(1, c.level), t, float(c.size), max(1, c.count) if t != 1 else 0, pid))
    return out


def encode(result: CuttingResult, *, stock_id, part_id, new_id) -> CutBlob:
    """`stock_id(sheet_id)` — list qatorining eksport id si; `part_id(ref)` — detal uid → eksport id; `new_id()` — yangi id."""
    blob = CutBlob(data="")
    waste_ids: dict[tuple[int, str], int] = {}

    def waste_id(m: CutMap, ref: str) -> int:
        key = (m.index, ref)
        if key not in waste_ids:
            num = int(ref[1:]) if ref[1:].isdigit() else 0
            off = next((o for o in m.offcuts if o.kind == "remnant" and o.number == num), None)
            wid = int(new_id())
            waste_ids[key] = wid
            blob.waste_parts.append(dict(id=wid, l=off.length if off else 0.0, w=off.width if off else 0.0,
                                         business=bool(off and off.business), sheet=stock_id(m.sheet_id), count=m.copies))
        return waste_ids[key]

    maps = [m for m in result.maps if m.copies > 0]
    raw = bytearray(struct.pack(">IIBI", 0, 1, 3, len(maps)))
    tot = dict(mult=0, parts=0, packets=0, waste=0.0, part_a=0.0, mat_a=0.0, cut_l=0.0, cut_lm=0.0, cut_n=0, waste_n=0, biz=0.0)
    for m in maps:
        recs = _records(m, lambda r: int(part_id(r)), waste_id)
        if _vertical(m):
            slot, rest = (recs[0], recs[1:]) if recs else ((0, 1, 0.0, 0, -1), [])
        else:
            slot, rest = (0, 1, 0.0, 0, -1), recs
        cells = sum(r[3] for r in recs if r[1] == 3)
        wastes = [o for o in m.offcuts if o.kind == "remnant"]
        waste_a = sum(o.length * o.width for o in wastes) / 1e6
        part_a = sum(p.length * p.width for p in m.placements) / 1e6
        sheet_a = m.sheet_length * m.sheet_width / 1e6
        part_count = cells * m.copies
        packets = max(1, m.packs or 1)
        raw += struct.pack(">I", m.copies)
        raw += struct.pack(">ddIB", m.sheet_length, m.sheet_width, int(stock_id(m.sheet_id)), 0)
        raw += struct.pack(">dddd", -1.0, -1.0, -1.0, -1.0)
        raw += struct.pack(">IdIdIdIdIdI", part_count, waste_a, part_count, part_a, 0, waste_a, packets, m.cut_length_m,
                           m.cuts_count, (part_a / sheet_a) if sheet_a else 0.0, len(rest) + 1)
        for depth, t, v, q, pid in [slot, *rest]:
            raw += _REC.pack((depth << 3) | t, v, 0, q, pid)
        tot["mult"] += m.copies; tot["parts"] += part_count; tot["packets"] += packets
        tot["waste"] += waste_a * m.copies; tot["part_a"] += part_a * m.copies; tot["mat_a"] += sheet_a * m.copies
        tot["cut_l"] += m.cut_length_m; tot["cut_lm"] += m.cut_length_m * m.copies; tot["cut_n"] += m.cuts_count
        tot["waste_n"] += len(wastes) * m.copies
        tot["biz"] += sum(o.length * o.width for o in wastes if o.business) / 1e6 * m.copies
    blob.data = base64.b64encode(bytes(raw)).decode("ascii")
    f = lambda v, n=5: f"{round(v, n):g}" if v else "0"            # noqa: E731
    cut_n = sum(m.cuts_count * m.copies for m in maps)
    blob.stats = {
        "cTrimLengthP": "0", "cTrimCountP": "0", "cPartCountP": "0", "cPartsAmountP": "0", "cWasteAmountP": "0",
        "cMaterialAmountP": "0", "costMaterial": "0", "costOperation": "0", "costTotal": "0",
        "cutLength": f"0={f(tot['cut_lm'], 3)};1={f(tot['cut_lm'], 3)};", "cutCount": f"0={cut_n};1={cut_n};",
        "cCountPackets": str(tot["packets"]), "cTrimLength": f(tot["cut_l"], 3), "cTrimCount": str(tot["cut_n"]),
        "cFilling": f(tot["part_a"] / tot["mat_a"]) if tot["mat_a"] else "0", "cBusinessWasteAmount": f(tot["biz"]),
        "cPartCount": str(tot["parts"]), "cPartAmount": f(tot["part_a"]), "cMaterialCount": str(tot["mult"]),
        "cMaterialAmount": f(tot["mat_a"]), "cWasteCount": str(tot["waste_n"]), "cWasteAmount": f(tot["waste"]),
    }
    return blob
