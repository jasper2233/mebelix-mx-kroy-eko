"""Felder F4Classic — har karta uchun bitta `.txt` (`PR_…` sarlavha + kesim daraxti), zip. Tavsif:
docs/mebelix/postprocessors/felder_f4classic.md.

`PR_DIMX` — list o'lchami 1-daraja (0) kesimlar o'qi bo'ylab, `PR_DIMY` — ikkinchi o'lcham; `PR_RIFX/Y` — torsovka + propil.
Daraxt qatori: `daraja, o'lcham` (konteyner) yoki `daraja, o'lcham, R<n>|bo'sh, bo'sh, detal[:detal…]` (detal; ketma-ket
bir xil detallar bitta qatorda, `R<n>` — soni). Chiqindi va qoldiq yozilmaydi. Nomlar — lotin (transliteratsiya).
"""
from __future__ import annotations

from . import SawJob, num, register
from . import _saw_strips as S
from ._saw_giben import translit

NOTE = ("Bitta namunadan o'rganilgan (3 karta). Etiketka fayllari (.ZPL) chiqarilmaydi — faqat kesim dasturi. "
        "PR_NPANN — karta nusxalari soni.")


def _lines(p: S.Piece, lvl: int, out: list[str]) -> None:
    for run in S.runs([c for c in p.children if c.kind != "R"]):
        c = run[0]
        d = num(c.size(p.axis))
        if c.kind == "P":
            rep = f"R{len(run)}" if len(run) > 1 else " "
            out.append(f"{lvl}, {d}, {rep},  , {':'.join(str(x.uid) for x in run)}")
        else:
            for x in run:                       # konteynerlar birlashtirilmaydi (namunadagi kabi)
                out.append(f"{lvl}, {d}")
                _lines(x, lvl + 1, out)


def txt(job: SawJob, mi: S.MapInfo, name: str) -> str:
    ax = mi.axis
    dimx, dimy = (mi.L, mi.W) if ax == "x" else (mi.W, mi.L)
    rifx, rify = (mi.tx, mi.ty) if ax == "x" else (mi.ty, mi.tx)
    head = [f"PR_VERSIONE = 12", f"PR_NOME = {name}", "PR_DESC = ", f"PR_CLI = {translit(S.project_title(job))}",
            f"PR_MATER = {translit(job.material_name)}", "PR_COMM = ", "PR_NORD = ",
            f"PR_DIMX = {num(dimx)}", f"PR_DIMY = {num(dimy)}", f"PR_RIFX = {num(rifx)}", f"PR_RIFY = {num(rify)}",
            f"PR_SPESS = {num(job.thickness)}", f"PR_NPANN = {mi.m.copies}", "PR_NPCAR = 1", "PR_TIPO = 0", "PR_TAGLI = "]
    body: list[str] = []
    if mi.root is not None:
        _lines(mi.root, 0, body)
    return "\r\n".join(head + body) + "\r\n"


@register("felder_f4classic", "Felder F4Classic (.txt)", "saw", ".zip", note=NOTE)
def generate(job: SawJob):
    stem = translit(S.file_stem(job))
    out = []
    for i, mi in enumerate(S.map_infos(job), 1):
        name = f"{stem}_{i:03d}"
        out.append((name + ".txt", txt(job, mi, name).encode("cp1251", "replace")))
    return out
