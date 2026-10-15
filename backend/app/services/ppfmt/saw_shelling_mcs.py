"""Shelling (MCS) arra markazi — `.l.zip` (`0000.ncl` + `NNNN.ncp`). Tavsif: docs/mebelix/postprocessors/shelling-mcs-zip.md.
Yozuvlar oddiy Shelling bilan bir xil; detal qatoridagi sana — buyurtma sanasi."""
from __future__ import annotations

from . import SawJob, register
from ._saw_shelling import generate


@register("shelling_mcs", "Shelling MCS (.l.zip)", "saw", ".l.zip",
          note="Har material — alohida zip (namunalarda boshqa materiallar tashqi zip ichiga keyinroq qo'shilgan; "
               "biz har materialni alohida beramiz). Etiketka ma'lumotlari fayli yozilmaydi. "
               "Detal qatoridagi sana — buyurtma sanasi.")
def shelling_mcs(job: SawJob):
    return generate(job, mcs=True)
