"""HOMAG CHF 41.44..44 (NPS400) pil markazi — `<loyiha>_<material>.zip`, ichida har **fizik list** uchun `pattern.NNN`
(docs/mebelix/postprocessors/homag-chf-nps400.md). Format oddiy HOMAG bilan bir xil, faqat kitob yo'q va daraxt
4 darajagacha (kodlar 1,2,3,7)."""
from __future__ import annotations

from . import SawJob, register
from ._saw_homag import pattern, zip_patterns


@register("homag_chf", "HOMAG CHF 41.44..44 (NPS400)", "saw", "zip",
          note="Har list — alohida pattern fayl (bir xil kartali listlar ham). Kesish daraxti 4 darajagacha "
               "(kodlar 1,2,3,7). Oxirgi qoldiq/chiqindi yozilmaydi.")
def generate(job: SawJob):
    pats = []
    for m in job.maps:
        data = pattern(job, m, 4)
        pats += [data] * max(1, m.copies)
    return zip_patterns(job, pats)
