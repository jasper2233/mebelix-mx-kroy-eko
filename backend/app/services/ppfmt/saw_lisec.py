"""Lisec (XOpt) — shisha kesish liniyasi: har karta `PL<NNN>.DAT` (zip). Tavsif: docs/mebelix/postprocessors/lisec-xopt.md.

Onlayn tizim fayllaridan o'rganildi (2026-10-24, 10 karta): sarlavha `[LPL_*]` (list o'lchamlari, qalinlik, torsovka — sm),
keyin har 1-daraja polosa `[TRAVERE] <en>`, ichida 2-daraja `[Y_SCHNITT]`, 3-daraja `[Z_SCHNITT]`; detal bo'lsa qator
oxirida `[BOCK_CODE] <detalning operatsiyadagi tartib raqami>`. O'lchamlar sm da, bitta kasr (0.2 → «.2»); propil yozilmaydi;
oxirgi chiqindi yozilmaydi. BREITE — polosalar bo'ylab list o'lchami, HOEHE — polosalar terilgan o'q bo'yicha.
Faqat 3 kesish darajasi (stanok formati) — chuqurroq kroy eksportda 3 burilishga qayta bajariladi (`ROT_LIMIT`).
"""
from __future__ import annotations

from . import ROT_LIMIT, SawJob, SawNode, register

LEVELS = {1: "TRAVERE", 2: "Y_SCHNITT", 3: "Z_SCHNITT"}
ROT_LIMIT["lisec_xopt"] = 3


def cm(v: float) -> str:
    s = f"{float(v) / 10:.1f}"
    return s[1:] if s.startswith("0.") else s


def _ext(n: SawNode, ax: str) -> float:
    return n.l if ax == "x" else n.w


def map_text(job: SawJob, m, idx: dict[int, int]) -> str:
    root = m.tree
    ax = (root.axis if root is not None else "") or "x"
    breite, hoehe = (m.sheet_width, m.sheet_length) if ax == "x" else (m.sheet_length, m.sheet_width)
    P = job.params or {}
    out = [f"[LPL_REF] {P.get('ref') or 'MebeliX'}", f"[LPL_AUF] {job.project_name}", f"[LPL_AUFNR] {P.get('order_no') or 'Stroka?'}",
           f"[LPL_BREITE] {cm(breite)}", f"[LPL_HOEHE] {cm(hoehe)}", f"[LPL_DICKE] {cm(job.thickness)}", "[LPL_TYPE] 1",
           f"[LPL_BV] {cm(m.trim_length)}", f"[LPL_BU] {cm(m.trim_width)}"]

    def walk(n: SawNode, lvl: int) -> None:
        kids = list(n.children)
        while kids and kids[-1].kind == "W":
            kids.pop()
        for c in kids:
            if lvl > 3:
                raise ValueError("Lisec: 3 dan chuqur kesim darajasi")
            line = f"[{LEVELS[lvl]}] {cm(_ext(c, n.axis or 'x'))}"
            if c.kind == "P":
                line += f" [BOCK_CODE] {idx.get(c.uid, c.uid)}"
            if lvl == 1:
                out.append("")
            out.append(line)
            if c.kind == "C":
                walk(c, lvl + 1)

    if root is not None:
        walk(root, 1)
    return "\r\n".join(out) + "\r\n"


def generate(job: SawJob) -> list[tuple[str, bytes]]:
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    return [(f"PL{i:03d}.DAT", map_text(job, m, idx).encode("utf-8")) for i, m in enumerate(job.maps, 1)]


NOTE = "Har karta — PL<NNN>.DAT (zip). 3 kesish darajasi; o'lchamlar sm da."
register("lisec_xopt", "Lisec (XOpt) — .DAT", "saw", "zip", note=NOTE)(generate)
