"""FastPanel — `.ocm` (ManualPattern XML, bitta qator, ASCII, deklaratsiyasiz). Tavsif: docs/mebelix/postprocessors/fastpanel.md.

Bitta CS operatsiyasi → bitta fayl; har noyob karta — `PanelInfo` + `Pattern`. `Entry` daraxti: 1-daraja polosalar
(`Length` o'qi bo'ylab), 2-daraja — polosa ichida, 3-daraja — qayta kesish …; `Distance` — bo'lak eni (propilsiz),
`Quantity` — ketma-ket bir xil bo'laklar soni. Chiqindi, qoldiq, detal nomlari yozilmaydi.
"""
from __future__ import annotations

from . import SawJob, num, register
from . import _saw_strips as S

NOTE = ("TrimSize = kroy zonasining boshi (torsovka + propil; namunalarda 5). Detal nomi/kromka faylda yo'q — faqat "
        "geometriya. Namunalarda chuqurlik ≤ 3 daraja; chuqurroq daraxt ham shu qoida bilan yoziladi.")


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _entries(p: S.Piece) -> str:
    out = []
    for run in S.runs([c for c in p.children if c.kind != "R"]):
        c = run[0]
        at = f'<Entry Distance="{num(c.size(p.axis))}" Quantity="{len(run)}"'
        inner = _entries(c) if c.kind == "C" else ""
        out.append(f"{at}>{inner}</Entry>" if inner else f"{at}/>")
    return "".join(out)


def ocm_text(job: SawJob) -> str:
    stem = S.file_stem(job)
    parts = [f'<ManualPattern JobName="{_esc(stem)}">']
    for mi in S.map_infos(job):
        if mi.root is None:
            continue
        ax = mi.axis
        length, width = (mi.L, mi.W) if ax == "x" else (mi.W, mi.L)
        trim = mi.tx if ax == "x" else mi.ty
        parts.append(f'<PanelInfo BladeThickness="{num(job.kerf)}" Length="{num(length)}" Quantity="{mi.m.copies}" '
                     f'Thickness="{num(job.thickness)}" TrimSize="{num(trim)}" Width="{num(width)}"/>')
        inner = _entries(mi.root)
        parts.append(f"<Pattern>{inner}</Pattern>" if inner else "<Pattern/>")
    parts.append("</ManualPattern>")
    return "".join(parts)


@register("fastpanel", "FastPanel (.ocm)", "saw", ".ocm", note=NOTE)
def generate(job: SawJob):
    return [(S.file_stem(job) + ".ocm", ocm_text(job).encode("utf-8"))]
