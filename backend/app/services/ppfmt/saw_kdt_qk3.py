"""KDT PreSize V3.3.0P — zip ichida har karta uchun `NUM=<k>   PANELS( <n> x 1 = <n> ).qk` (o'zgaruvchan uzunlikdagi
ikkilik yozuvlar) va `.lbd` (KDT «yangi versiya» bilan bir xil). Tavsif: docs/mebelix/postprocessors/kdt-presize-qk-v3.md.

`.qk` (little-endian): sarlavha `kerf, dimy, dimx` (float32), keyin har **farzandli** bo'lak uchun 273 baytli yozuv
(preorder, ildizdan boshlab): bolalar blokining boshi (int32), bo'lak indeksi (int32), `siljish, ota o'lchami, o'lcham`
(3 × float32), 1 (int32), qalinlik (float32), 1 (bayt), 20 ta bola `(o'lcham float32, 0, takror int32)`, qoldiq (float32).
Indekslar KS33X jadvalidagi bilan bir xil (1 — ildiz, 11+, 101+, 1001+), faqat bo'sh yozuvlar yozilmaydi.
Bo'laklar tartibi: 1-daraja list uzunligi bo'ylab bo'lsa — KS33X dagi kabi (1-daraja teskari); list eni bo'ylab bo'lsa —
karta 90° burilgandek: 1-daraja o'z tartibida, 3-daraja (yana list eni bo'ylab) teskari."""
from __future__ import annotations

import struct

from . import Files, SawJob, register, zip_files
from . import saw_kdt_ks33x as K
from ._saw_common import job_title
from ._saw_giben import GPat, patterns

FAN = K.FAN                                   # bitta yozuvdagi bolalar soni
MAX_LEVEL = 4
IDX = {0: 1, 1: 11, 2: 101, 3: 1001}          # farzandli bo'lak darajasi (0 — ildiz) → indeks boshi
BASE = {0: 0, 1: 100, 2: 1000, 3: 10020}      # → bolalar blokining boshi (+ 20 × tartib raqami)


def tree(job: SawJob, P: GPat) -> list[dict]:
    """KS33X daraxti (`ks_tree`), V3.3.0P tartibida: list eni bo'ylab polosalangan kartada 1-daraja teskari qilinmaydi,
    toq chuqur darajalar (3-…) teskari; qoldiq — oxirida."""
    nodes = K.ks_tree(job, P)
    if P.axis != "y":
        return nodes

    def flip(ns: list[dict], lvl: int) -> list[dict]:
        out = [dict(n, ch=flip(n["ch"], lvl + 1)) if n["strip"] else n for n in ns]
        return out[::-1] if lvl % 2 == 1 and lvl > 1 else out

    return flip([n for n in nodes if not n.get("fl")][::-1], 1) + [n for n in nodes if n.get("fl")]


def qk(job: SawJob, P: GPat, nodes: list[dict]) -> bytes:
    kerf, thick = float(job.kerf), float(job.thickness)
    out = bytearray(struct.pack("<fff", kerf, P.dimy, P.dimx))

    def rec(ns: list[dict], lvl: int, rank: int, a: tuple[float, float, float], ext: float) -> None:
        if len(ns) > FAN:
            raise ValueError(f"KDT V3.3.0P: bitta bo'lakda {len(ns)} ta kesim — format chegarasi {FAN}")
        out.extend(struct.pack("<ii3fifB", BASE[lvl] + FAN * rank, IDX[lvl] + rank, *a, 1, thick, 1))
        for n in ns:
            out.extend(struct.pack("<fii", n["cut"], 0, n["rep"]))
        out.extend(bytes(12 * (FAN - len(ns))))
        used = a[0] + sum((n["cut"] + kerf) * n["rep"] for n in ns)
        out.extend(struct.pack("<f", max(0.0, ext - used)))
        for j, n in enumerate(ns):
            if not n["strip"]:
                continue
            if lvl + 2 > MAX_LEVEL:
                raise ValueError(f"KDT V3.3.0P: kesim {MAX_LEVEL} darajadan chuqur — stanok formati qo'llamaydi "
                                 "(«Макс. количество вращений» ni kamaytiring)")
            # qoldiq: 1-daraja bo'lak ichida list eni bo'yicha, chuqurroqda — ota o'lchami bo'yicha (namunadagi qoida)
            rec(n["ch"], lvl + 1, j if lvl == 0 else rank * FAN + j,
                (P.off1 if lvl == 0 else 0.0, P.dimx if lvl == 0 else a[2], n["cut"]),
                P.map.sheet_width if lvl == 0 else a[2])

    # ildiz qoldig'i list uzunligi bo'yicha hisoblanadi (namunadagi qoida); qoldiq bo'lagi .qk ga yozilmaydi
    rec([n for n in nodes if not n.get("fl")], 0, 0, (P.off1, P.dimy, P.dimx), P.map.sheet_length)
    return bytes(out)


NOTE = ("Zip: har karta uchun `.qk` (V3.3.0P — faqat to'ldirilgan yozuvlar) + `.lbd` (KDT yangi versiya bilan bir xil; "
        "etiketka blobi yozilmaydi). Chegaralar: ≤ 4 kesim darajasi, har bo'lakda ≤ 20 kesim. Bitta namunadan o'rganilgan "
        "(3 karta): yozuvdagi `1` (int32) va `1` (bayt) — doimiy deb olindi; list eni bo'ylab polosalangan kartada "
        "bo'laklar tartibi va qoldiq maydoni namunadagi qoida bo'yicha.")


@register("kdt_presize_qk", "KDT PreSize V3.3.0P (.qk + .lbd)", "saw", "zip", note=NOTE)
def kdt_presize_qk(job: SawJob) -> Files:
    title = job_title(job)
    files: Files = []
    for k, P in enumerate(patterns(job), 1):
        nodes = tree(job, P)
        base = f"NUM={k}   PANELS( {P.copies} x 1 = {P.copies} )"
        files.append((base + ".qk", qk(job, P, nodes)))
        files.append((base + ".lbd", K.lbd(job, P, nodes, title, True)))
    return [(title + ".zip", zip_files(files))]
