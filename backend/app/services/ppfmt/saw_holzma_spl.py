"""Holzma (CADmatic 3) — `.SPL`: binar (big-endian) kesish rejasi. Tavsif: docs/mebelix/postprocessors/holzma3-spl.md.

Fayl: `c` sarlavha, keyin har karta uchun blok `d` (karta) + `e` (stanok parametrlari) + `f` (statistika) + `n`… (daraxt
tugunlari, pre-order) + `x`. O'lchamlar 0.0001 mm birlikda. Detal faqat indeks bilan (CS dagi detal tartibi, 1 dan) —
nom/kromka yo'q. Daraxt chuqurligi ≤ 5 (list + 4 kesish darajasi). Fayl nomi — DOS 8.3 uslubida (8 belgi)."""
from __future__ import annotations

import math
import struct

from . import SawJob, register
from ._saw_common import job_title
from ._saw_giben import translit
from ._saw_holzma import HNode, depth, part_area, pattern

MAX_LEVELS = 5
SIG = b"\x30\x21\x00\x00\x00"

# `e` yozuvi (460 bayt): namunalarda o'zgarmas stanok parametrlari (ofset → qiymat, ×0.0001 mm yoki son).
# Ma'nosi aniq bo'lganlari: 32..44 — trimlar, 60 — minimal tilim, 228/288/380/384 — arra qalinligi.
E_CONST = {16: 43000000, 20: 43000000, 24: 1000000, 28: 1000000, 72: 10000000, 76: 10000000, 80: 1000, 84: 1, 104: 1,
           120: 1, 124: 1, 128: 1, 132: 1, 140: 1, 204: 80000, 208: 100000, 212: 500000, 216: 200000, 240: 4500000,
           252: 1240000, 264: 1000000, 268: 50000, 284: 13000000, 292: 1000000, 296: 1000000, 312: 1000000,
           316: 10000000, 320: 10000000, 328: 13000000, 332: 99999000, 340: 100, 344: 99999000, 348: 99999000,
           388: 5000, 392: 50000, 448: 99999000, 452: 1500000}


def _be32(v: int) -> bytes:
    return struct.pack(">I", int(v) & 0xFFFFFFFF)


def _um(mm: float) -> int:
    return int(round(float(mm) * 10000))


def _rec(t: str, payload: bytes, lv: int = 0, link=None) -> bytes:
    h = struct.pack(">HHH", len(payload), lv, 0) + SIG + t.encode("ascii")
    return h + payload + (_be32(link) if link is not None else b"")


def _e(job: SawJob) -> bytes:
    e = bytearray(460)
    for o, v in E_CONST.items():
        e[o:o + 4] = _be32(v)
    for o, v in ((32, job.trim_length), (36, job.trim_length), (40, job.trim_width), (44, job.trim_width)):
        e[o:o + 4] = _be32(_um(v))
    cut = job.op.cs_cut
    mt = getattr(cut, "min_trim_cut", 5.0) if cut else 5.0
    e[60:64] = _be32(_um(mt))
    for o in (228, 288, 380, 384):
        e[o:o + 4] = _be32(_um(job.kerf))
    return bytes(e)


def _nodes(job: SawJob, nodes: list[HNode], lv: int, idx: dict[int, int], out: list):
    """Pre-order: (daraja, detal indeksi, o'lcham). Qoldiq va oxirgi chiqindi yozilmaydi (implisit)."""
    nodes = [n for n in nodes if n.kind != "rest"]
    while nodes and nodes[-1].kind == "waste":
        nodes.pop()
    for n in nodes:
        if n.kind == "part":
            out.append((lv, idx.get(n.uid, 0), n.size))
        else:
            out.append((lv, 0, n.size))
            _nodes(job, n.kids, lv + 1, idx, out)


def build(job: SawJob) -> bytes:
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    pats = [p for p in (pattern(job, m) for m in job.maps) if p is not None]
    E = _e(job)
    blocks = []
    for k, p in enumerate(pats, 1):
        if depth(p.kids) + 1 > MAX_LEVELS:
            raise ValueError(f"SPL: {k}-karta kesish chuqurligi {depth(p.kids)} > {MAX_LEVELS - 1} "
                             f"(«Макс. количество вращений» ni kamaytiring)")
        d = bytearray(131)
        d[0:4] = _be32(0x02CF28BF)
        d[4:8] = _be32(104)
        d[8:12] = _be32(101)
        nm = f"{k:03d}".encode("ascii")[:6]
        d[18:18 + len(nm)] = nm
        d[24:28] = _be32(1 if p.rot else 0)
        d[28:32] = _be32(p.copies)
        d[32:36] = _be32(p.copies)
        d[36:40] = _be32(_um(p.sheet_l))
        d[40:44] = _be32(_um(p.sheet_w))
        d[44:48] = _be32(_um(job.thickness))
        d[74:76] = struct.pack(">H", min(p.copies, 0xFFFF))
        d[76:78] = struct.pack(">H", 1)
        rows = [(1, 0, p.sheet_w if p.rot else p.sheet_l)]
        _nodes(job, p.kids, 2, idx, rows)
        nb = b""
        leaves = 0
        for lv, pid, size in rows:
            q = bytearray(29)
            q[0:2] = b"\x00\x80"
            q[2] = lv - 1
            q[3:8] = int(pid).to_bytes(5, "big")
            q[8:12] = _be32(_um(size))
            q[12] = 4
            if pid:
                q[19] = 99
                leaves += 1
            nb += _rec("n", bytes(q), lv)
        xh = _rec("x", b"")
        # f[16]/f[28]: namunalarda f[28] = ⌊listdagi bo'sh (detalsiz) maydon, m²⌋ (30/30), f[16] = 4 − f[28]
        free = (p.sheet_l * p.sheet_w - part_area(job, p.kids, 0)) / 1e6
        f28 = max(0, min(4, int(math.floor(free + 1e-9))))
        f = bytearray(32)
        f[12:16] = _be32(MAX_LEVELS)
        f[16:20] = _be32(4 - f28)
        f[20:24] = _be32(leaves * p.copies)
        f[28:32] = _be32(f28)
        blocks.append(_rec("d", bytes(d)) + _rec("e", E) + _rec("f", bytes(f), link=len(nb) + len(xh)) + nb + xh)
    c = bytearray(52)
    c[0:4] = _be32(0x02CF28C0)
    c[4:8] = _be32(104)
    c[8:12] = _be32(len(blocks))
    c[12:16] = _be32(MAX_LEVELS)
    out = _rec("c", bytes(c), link=len(blocks[0]) if blocks else 0)
    for i, b in enumerate(blocks):
        out += b + (_be32(len(blocks[i + 1])) if i + 1 < len(blocks) else b"")
    return out


def short_name(job: SawJob) -> str:
    """Dastur nomi — 8 belgi, lotin (kirill transliteratsiya qilinadi: «Без имени» → `Bez_imen`)."""
    return translit(job_title(job)).replace("?", "_")[:8]


@register("holzma_cadmatic3", "Holzma (CADmatic 3) .SPL", "saw", "SPL",
          note="Binar kesish rejasi (Holzma 3 namunalaridan): faqat detal indekslari (nom/kromka yo'q), fayl nomi 8 belgi. "
               "Kesish chuqurligi ≤ 4 daraja bo'lishi shart (aks holda xato). `e` yozuvidagi stanok parametrlari "
               "namunalardagi doimiylar (trim, arra, min. tilim — kroy parametrlaridan).")
def generate(job: SawJob):
    return [(f"{short_name(job)}.SPL", build(job))]
