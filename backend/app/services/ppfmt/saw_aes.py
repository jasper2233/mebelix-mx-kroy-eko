"""AES Alpha / AESS Alpha (SS) — `.ss` (qat'iy kenglikli CSV yozuvlari BSL/KON/LMT/OZL/URN/PRT/PNL/KES, CRLF).
Tavsif: docs/mebelix/postprocessors/aes-alpha.md (+ aess-alpha-ss.md — aynan bir xil format).

Bitta CS operatsiyasi → bitta fayl. Kesish daraxti pre-order `KES1` qatorlari: daraja, bo'lak eni, detal belgisi, detal
raqami; 3- va undan chuqur daraja guruhlari boshida `-0.50` qatori; chiqindi va qoldiqlar yozilmaydi.
"""
from __future__ import annotations

from . import SawJob, register
from . import _saw_strips as S

NOTE = ("BSL3 dastur maydoniga «MebeliX Kroy» yoziladi. Konstantalar (KON1 M,M,N; OZL1 *****/9.860; PNL2) namunalardagi "
        "kabi. Lotin bo'lmagan harflar cp1251 da (namunalarda uchramagan — tasdiqlash kerak).")
ENC = "cp1251"


def f92(v: float) -> str:
    return f"{float(v):9.2f}"


def _txt(s: str) -> str:
    return (s or "").replace(",", ";").replace("\r", " ").replace("\n", " ")


def ss_text(job: SawJob) -> str:
    infos = S.map_infos(job)
    uid_idx = {p.uid: i for i, p in enumerate(job.parts)}
    t = S.now()
    rows = [f"BSL1,001,{_txt(S.project_title(job))}",
            f"BSL2,{t:%d.%m.%Y},{t:%H:%M},",
            f"BSL3,From {S.PROGRAM},1.0,,",
            "KON1,M,M,N,   1,0",
            f"KON2,{f92(job.kerf)},{f92(job.kerf)}, 0.00,     0.00,     0.00,     0.00",
            "KON3,     0.00",
            f"LMT1,{f92(job.thickness)},{f92(job.pack_height)}",
            "ASP1,      ,      ,      ",
            "ASP2,           ,           ,           "]
    used: dict[str, int] = {}
    for mi in infos:
        used[mi.m.sheet_id] = used.get(mi.m.sheet_id, 0) + mi.m.copies
    sheet_no: dict[str, int] = {}
    tl, tw = job.trim_length, job.trim_width
    for i, s in enumerate(job.stock, 1):
        sheet_no[s["id"]] = i
        rows += [f"OZL1,*****,{used.get(s['id'], 0):5d},   9.860,{f92(s['width'])},{f92(s['length'])},"
                 f"{f92(tl)},{f92(tl)},{f92(tw)},{f92(tw)}",
                 f"OZL2,{_txt(job.material_name)}",
                 f"OZL3,1                ,{f92(tl)},{f92(tw)}"]
    for i, p in enumerate(job.parts, 1):
        rows += [f"URN1,{p.qty:5d},{p.qty:5d},{f92(p.length)},{f92(p.width)}, ,N",
                 f"URN2,        ,{f92(p.length)},{f92(p.width)}",
                 f"URN3, 1, {i}"]
    for i, p in enumerate(job.parts):
        e = p.edges
        sides = ("left", "top", "right", "bottom")
        nm = [_txt((e.get(s) or {}).get("name", "")) for s in sides]
        th = [float((e.get(s) or {}).get("thickness", 0) or 0) if e.get(s) else 0.0 for s in sides]
        pad = " " * 8
        rows += [f"PRT1,{p.qty:5d}, {i},{f92(p.length)},{f92(p.width)}, 1,{' ' * 24},,{_txt(p.name)},,"
                 f"{_txt(p.product_code)},{_txt(p.product)},{' ' * 16}",
                 f"PRT2, 0, ,{f92(job.thickness)},",
                 f"PRT3,0000,{pad},{nm[0]},{pad},{pad},{nm[1]},{pad},{pad},{nm[2]},{pad},{pad},{nm[3]},{pad}",
                 f"PRT4,{','.join(f92(x) for x in th)},1,{' ' * 20}",
                 "PRT5, ,N,     ,     "]
    for mi in infos:
        if mi.root is None:
            continue
        rows += [f"PNL1,{sheet_no.get(mi.m.sheet_id, 1):02d},{'S' if mi.axis == 'x' else 'L'},{mi.m.copies},0",
                 "PNL2, 0.0000,        0.0000,        0.0000,        0.0000,       1.000",
                 "PNL3,     ,     ,     ,     ",
                 "PNL4,           ,           ,           ",
                 "PNL5,      ,      ,            ,            ",
                 "BASLA"]

        def kes(p: S.Piece) -> None:
            kids = [c for c in p.children if c.kind != "R"]
            for j, c in enumerate(kids):
                lvl = c.level
                if j == 0 and lvl >= 3:
                    rows.append(f"KES1,{lvl:02d},{f92(-0.5)},0,000")
                if c.kind == "P":
                    rows.append(f"KES1,{lvl:02d},{f92(c.size(p.axis))},1,{uid_idx.get(c.uid, 0) + 1:03d}")
                else:
                    rows.append(f"KES1,{lvl:02d},{f92(c.size(p.axis))},0,000")
                    kes(c)

        kes(mi.root)
    rows.append("BITIR")
    return "".join(r + "\r\n" for r in rows)


def generate(job: SawJob):
    return [(S.file_stem(job) + ".ss", ss_text(job).encode(ENC, errors="replace"))]


register("aes_alpha", "AES Alpha (.ss)", "saw", ".ss", note=NOTE)(generate)
register("aess_alpha", "AESS Alpha (SS) (.ss)", "saw", ".ss", note=NOTE)(generate)
