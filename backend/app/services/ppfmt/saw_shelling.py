"""Shelling (Schelling) arra markazi — `.l.zip` (`0000.ncl` + `NNNN.ncp`). Tavsif: docs/mebelix/postprocessors/shelling-zip.md."""
from __future__ import annotations

from . import SawJob, register
from ._saw_shelling import generate


@register("shelling", "Shelling (.l.zip)", "saw", ".l.zip",
          note="Har material — alohida zip: 0000.ncl (listlar, detallar, qoldiqlar) va har karta uchun NNNN.ncp. "
               "Arra qalinligi faylga yozilmaydi (stanok sozlamasi); trim = list chetidan birinchi bo'lakkacha. "
               "Etiketka ma'lumotlari fayli yozilmaydi. Detal qatoridagi sana — loyiha tayyorlik sanasi.")
def shelling(job: SawJob):
    return generate(job, mcs=False)
