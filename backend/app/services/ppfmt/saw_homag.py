"""HOMAG pil markazi — `<loyiha>_<material>.zip`, ichida `pattern.001…` (docs/mebelix/postprocessors/homag-zip.md).

Har material (CS operatsiyasi) — bitta zip; har fayl — bitta **kitob (paket)**: bir xil kartali listlar
paket balandligi / qalinlik (namunalarda 40/16 → 2 list) bo'yicha guruhlanadi, kartaning qolgan listlari keyingi faylda.
Kitobdagi listlar soni faylga yozilmaydi (namunalardagi kabi) — operator stanokda kiritadi.
"""
from __future__ import annotations

import math

from . import SawJob, register
from ._saw_homag import pattern, zip_patterns


def book_size(job: SawJob) -> int:
    """Bitta faylga (paketga) tushadigan listlar soni: sozlama `book` yoki ⌊paket balandligi / qalinlik⌋."""
    try:
        b = int(job.params.get("book") or 0)
    except (TypeError, ValueError):
        b = 0
    if b <= 0 and job.pack_height and job.thickness:
        b = int(math.floor(job.pack_height / job.thickness + 1e-9))
    return max(1, b)


def books(job: SawJob) -> list[tuple[int, int]]:
    """(karta indeksi ro'yxatda, shu fayldagi listlar soni) — har karta nusxalari paketlarga bo'linadi."""
    b = book_size(job)
    out: list[tuple[int, int]] = []
    for i, m in enumerate(job.maps):
        left = max(1, m.copies)
        while left > 0:
            n = min(b, left)
            out.append((i, n))
            left -= n
    return out


@register("homag", "HOMAG (pattern, zip)", "saw", "zip",
          note="Har paket (bir xil kartali listlar, paket balandligi/qalinlik) — alohida pattern fayl; paketdagi listlar "
               "soni faylga yozilmaydi. Kesish daraxti 5 darajagacha (kodlar 1,2,3,7,9). Oxirgi qoldiq/chiqindi yozilmaydi.")
def generate(job: SawJob):
    cache: dict[int, bytes] = {}
    pats = []
    for i, _n in books(job):
        if i not in cache:
            cache[i] = pattern(job, job.maps[i], 5)
        pats.append(cache[i])
    return zip_patterns(job, pats)
