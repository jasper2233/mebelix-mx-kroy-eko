"""Giben GDrive — zip ichida `.DAX` (list + detallar) va `.CPX` (kesish kartalari), ikkilik (little-endian).
Tavsif: docs/mebelix/postprocessors/giben-gdrive.md.

Yozuvlar qat'iy uzunlikda (DAX 201 bayt, CPX kesimi 48, karta sarlavhasi 96); sonli maydonlar xom yoziladi, bayt-massiv
(matn / zahira) maydonlarining nol qismi `FC nn` (nn ta nol) bilan siqiladi, `FC 00` — yozuv oxiri.
Stanok faqat 3 kesim darajasini (3, 4, 5) biladi: chuqurroq kesiladigan bo'lak 999-detal («DOREZAT!!!») deb belgilanadi
va uning ichki kesimlari yozilmaydi (operator qo'lda kesadi)."""
from __future__ import annotations

import struct

from . import Files, SawJob, safe_name, register, zip_files
from ._saw_common import job_title
from ._saw_giben import GN, patterns, translit, um

END = b"\xfc\x00"
REC_TAIL = b"\xfc\x44\xfc\x01\xfc\x28" + END          # 68 + 1 + 40 nol, yozuv oxiri
CUT_END = b"\xfc\x26" + END                           # 38 nol, yozuv oxiri
REDO = 999                                            # «qo'lda qayta kesish» soxta detali
MAX_LEVEL = 5


def _i32(v: int) -> bytes:
    return struct.pack("<i", int(v))


def _i16(v: int) -> bytes:
    return struct.pack("<h", int(v))


def _zfield(content: bytes, size: int) -> bytes:
    """Bayt-massiv maydoni: mazmun (oxirgi nollarsiz) + `FC n` (qolgan n ta nol)."""
    content = content[:size].rstrip(b"\0")
    out = b""
    pad = size - len(content)
    while pad > 0:                                    # n bir bayt (1..255)
        k = min(pad, 255)
        out += bytes([0xFC, k])
        pad -= k
    return content + out


def _text(s: str, size: int) -> bytes:
    """Matn: transliteratsiya, faqat ASCII (0xFC bayti — siqish belgisi — matnda uchramasligi uchun)."""
    return translit(s).encode("ascii", "replace")[:size]


def short_name(job: SawJob) -> str:
    """DOS 8.3 nom: loyiha nomining birinchi 8 belgisi."""
    pn = (job.project_name or "").strip()
    order = (job.order or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order}_{pn}" if pn else order
    return safe_name(translit(pn), "kroy", 8).replace("?", "_")


def _record(idx: int, l: float, w: float, qty: int, name: bytes, kind: int) -> bytes:
    return (_i32(idx) + _i32(um(l)) + _i32(um(w)) + _i32(qty) + b"\xfc\x18" + _zfield(name, 40) + _i32(kind)
            + _i32(qty) + _i32(qty) + REC_TAIL)


def _sheet_rows(pats) -> tuple[list[list], dict[int, int]]:
    ids: dict[tuple, int] = {}
    rows: list[list] = []
    of: dict[int, int] = {}
    for p in pats:
        k = (round(p.map.sheet_length, 3), round(p.map.sheet_width, 3))
        if k not in ids:
            ids[k] = len(rows)
            rows.append([p.map.sheet_length, p.map.sheet_width, 0])
        rows[ids[k]][2] += p.copies
        of[id(p)] = ids[k] + 1
    return rows, of


def dax(job: SawJob, pats) -> bytes:
    out = b"\x04\x00"
    # A yozuvi: 55 nol + qalinlik×1000 (namunalarda 16000; boshqa qalinlikda tasdiqlanmagan) + nollar
    out += b"\xfc\x37" + _zfield(_i32(um(job.thickness)), 105) + b"\xfc\x01\xfc\x28" + END
    out += b"\xff\xff\xfc\x32" + b"\x01\xfc\x13" + b"\xfc\x01\xfc\x80" + END          # B yozuvi (doimiy)
    rows, _ = _sheet_rows(pats)
    for i, (l, w, n) in enumerate(rows):
        out += _record(5001 + i, l, w, n, b"", 4)
    for i, p in enumerate(job.parts, 1):
        out += _record(i, p.length, p.width, p.qty, _text(p.name, 40), 1)
    out += _record(REDO, 1000, 1000, 1000, b"DOREZAT!!!", 1)
    return out


def cpx(job: SawJob, pats) -> bytes:
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    _, sheet_of = _sheet_rows(pats)

    def walk(nodes: list[GN], lvl: int) -> bytes:
        r = b""
        for c in nodes:
            if not c.kids:
                pi = idx.get(c.uid, 0)
            elif lvl >= MAX_LEVEL:
                pi = REDO
            else:
                pi = 0
            r += _i16(lvl) + _i16(pi) + _i32(um(c.size)) + _i16(c.rep) + CUT_END
            if c.kids and lvl < MAX_LEVEL:
                r += walk(c.kids, lvl + 1)
        return r

    out = b"\x04\x00"
    for k, P in enumerate(pats, 1):
        out += (b"\xff\xff" + _i16(k) + _i32(sheet_of[id(P)]) + _i32(P.copies) + _i32(um(P.dimx)) + _i32(um(P.dimy))
                + b"\x01" + b"\xfc\x4b" + END)
        out += _i16(2) + _i16(0) + _i32(um(P.dimx)) + _i16(1) + CUT_END             # 2-daraja: butun karta
        out += walk(P.kids, 3)
    return out


@register("giben_gdrive", "Giben GDrive (.DAX + .CPX)", "saw", "zip",
          note="Zip ichida 8 belgili nom bilan `.DAX` + `.CPX`. Namunalarda faqat birinchi material chiqarilgan va "
               "material nomi faylda yo'q; bizda har CS operatsiyasi alohida zip (`<loyiha>_<material>.zip`). "
               "Stanok 3 kesim darajasini biladi: chuqurroq bo'laklar 999 «DOREZAT!!!» (qo'lda kesiladi) — kroyda "
               "«Макс. количество вращений» = 3 tavsiya. Ochiq savol: son maydonida 0xFC bayti (masalan 720 mm = "
               "80 FC 0A 00) — xom yoziladi (sonlar siqilmaydi deb hisoblandi; namunalarda uchramagan, stanokda "
               "sinash kerak); matnlar lotinga o'giriladi (0xFC uchramaydi), 40 baytgacha. A yozuvidagi 16000 — "
               "qalinlik×1000 deb olindi (faqat 16 mm namunalar).")
def giben_gdrive(job: SawJob) -> Files:
    pats = patterns(job)
    nm = short_name(job)
    return [(job_title(job) + ".zip", zip_files([(nm + ".DAX", dax(job, pats)), (nm + ".CPX", cpx(job, pats))]))]
