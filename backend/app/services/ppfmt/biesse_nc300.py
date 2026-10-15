"""Biesse Selco NC300 — zip: `dist/<NOME>` (buyurtma ro'yxati) + `tagli/<NOME>.NNN` (har kesish kartasi).

Tavsif: docs/mebelix/postprocessors/biesse-selco-nc300.md. Qisqacha:
  * NOME — loyiha nomining birinchi 8 belgisi (DOS 8.3); o'lchamlar butun son, 1/100 mm; qatorlar CRLF, chekinish TAB.
  * B_CUT — kesish daraxtining preorder ro'yxati: kod `1`/`4` (1-daraja: X / Y bo'ylab), `2`/`5` (2-daraja), `Z1`, `Z2`, …;
    ketma-ket bir xil pastki daraxtlar har doim `QTA` ga yig'iladi (faqat o'lcham bo'yicha). List Y o'qi bo'ylab
    ketma-ket bo'laklar teskari tartibda yoziladi (stanok Y o'qi ko'zguli), X bo'ylab — o'z tartibida.
  * B_REF — trim (torsovka + propil), 1/100 mm.
  * B_LABEL — etiketkalar bloki: qoldiq yozuvlari, detal yozuvlari (31 maydonli CSV) va listdagi joylashuv guruhlari.
    Detal yozuvlari — detal raqami bo'yicha xesh-jadval tartibida, guruhlar — listdagi (geometrik) tartibda. CSV ning 0–14 maydonlari — detal ma'lumoti (format qoidasi), 15–29 — BIZNING etiketka maydonlari jadvali (NC300 uchun
    jadval yo'q → bo'sh), 30-maydon (boshqa dasturning ichki o'zgaruvchilar xaritasi + eskiz) **yozilmaydi** (bo'sh).
"""
from __future__ import annotations

import base64
import struct
from dataclasses import replace

from . import SawJob, register, safe_name
from . import _saw_bsf as B
from ._saw_giben import translit

KEY = "biesse_nc300"
ENC = "cp1251"                   # namunalarda faqat ASCII; kirill uchun cp1251 (tasdiqlanmagan)
CRLF = "\r\n"


def nome(job: SawJob) -> str:
    """Dastur nomi — 8 belgi, lotin (kirill transliteratsiya qilinadi: «Без имени» → `Bez_imen`)."""
    return safe_name(translit(job.project_name or job.order), "kroy", 200)[:8]


def code(level: int, first_axis: str) -> str:
    if level == 1:
        return "1" if first_axis == "x" else "4"
    if level == 2:
        return "2" if first_axis == "x" else "5"
    return f"Z{level - 2}"


def trims(job: SawJob, m) -> tuple[float, float]:
    """(uzunlik bo'yicha, en bo'yicha) trim: torsovka + propil (sozlamada «propil hisobga olingan» bo'lmasa)."""
    inc = bool(getattr(job.op.cs_cut, "trim_includes_kerf", False)) if job.op.cs_cut else False
    k = 0.0 if inc else float(job.kerf or 0)
    return float(m.trim_length or 0) + k, float(m.trim_width or 0) + k


# ───────────────────────── B_LABEL ─────────────────────────
def _over(b: bytes) -> bytes:
    """0x50…0x7F baytlar 2 baytli «overlong» ko'rinishda (0xC1, 0x80|b&0x3F) — blok kodlash qoidasi (namunalar)."""
    o = bytearray()
    for x in b:
        if 0x50 <= x <= 0x7F:
            o += bytes((0xC1, 0x80 | (x & 0x3F)))
        else:
            o.append(x)
    return bytes(o)


def _rec(fields: list[str]) -> bytes:
    b = _over(",".join(fields).encode("utf-8"))
    return b"\x01" + struct.pack(">I", len(b)) + b


def _csv(v) -> str:
    return B.text(v).replace(",", " ").replace("\r", " ").replace("\n", " ")


def label_block(rests: list[list[str]], dets: list[list[str]], groups: list[list[tuple[int, int, int]]]) -> list[str]:
    o = bytearray(struct.pack(">I", len(rests)))
    for f in rests:
        o += _rec(f) + struct.pack(">I", 1)
    o += struct.pack(">I", len(dets))
    for f in dets:
        o += _rec(f)
    o += struct.pack(">I", len(groups))
    for g in groups:
        o += struct.pack(">I", len(g))
        for x, y, i in g:
            o += struct.pack(">III", x, y, i)
    s = base64.b64encode(bytes(o)).decode("ascii")
    return ["\t" + s[i:i + 80] for i in range(0, len(s), 80)]


def flip_y(cuts: list[B.Cut]) -> list[B.Cut]:
    """Y o'qi bo'ylab ketma-ket yozuvlar teskari tartibda (stanok Y o'qi ko'zguli); X bo'ylab — o'zgarmaydi."""
    out = [replace(c, children=flip_y(c.children), rest=list(c.rest)) for c in cuts]
    return out[::-1] if out and out[0].axis == "y" else out


def hash_order(keys: list[int]) -> list[int]:
    """Xesh-jadval tartibi (savat = kalit & (sig'im − 1), savat ichida kiritish tartibi) — namunadagi detal yozuvlari
    tartibi (KDT `.lbd` dagi kabi)."""
    cap = 16
    while len(keys) > cap * 3 // 4:
        cap *= 2
    return sorted(keys, key=lambda k: ((k ^ (k >> 16)) & (cap - 1), keys.index(k)))


def labels_for_map(job: SawJob, m, cuts: list[B.Cut], P: B.Parts, L: B.Labels, order: str):
    """(qoldiq yozuvlari, detal yozuvlari, joylashuv guruhlari). Guruh — listdagi tartibda ketma-ket kelgan bir xil detal
    bo'laklari (bitta list uchun); detal yozuvlari — xesh-jadval tartibida (`hash_order`)."""
    rems = B.remnants(m)
    rests: list[list[str]] = []
    for lf, mult in B.leaves_mult(cuts):
        if lf.rem:
            o = rems.get(lf.rem) or {}
            ln, wd = float(o.get("length") or lf.sx), float(o.get("width") or lf.sy)
            for _ in range(mult):
                rests.append(["rest.fme", "", "1", "1", B.ival(ln), B.ival(wd), B.ival(round(ln * wd / 1e6, 3)), _csv(order)]
                             + [""] * 23)
    uids: list[int] = []
    groups_u: list[tuple[int, list[tuple[int, int]]]] = []
    for lf, mult in B.leaves_mult(B.merge_runs(B.drop_rem(cuts), by_part=True)):
        if not lf.uid:
            continue
        if lf.uid not in uids:
            uids.append(lf.uid)
        groups_u.append((lf.uid, [(B.cents(lf.sx), B.cents(lf.sy))] * mult))
    uids = hash_order(uids)
    dets: list[list[str]] = []
    for u in uids:
        sp = P.saw.get(u)
        l, w = P.lw(u)
        e = {s: P.edge(u, s) for s in ("left", "right", "top", "bottom")}
        extra = [_csv(v) for _n, v in L.values(u)][:15]
        dets.append(["detail.fme", "", str(sp.qty if sp else 0), str(P.index.get(u, 0)), "1", _csv(order), B.ival(l), B.ival(w),
                     _csv(sp.name if sp else ""), str(sp.qty if sp else 0),
                     *[_csv(e[s].get("symbol", "")) for s in ("left", "right", "top", "bottom")],
                     "true" if (sp and sp.grain) else "false"]
                    + extra + [""] * (15 - len(extra)) + [""])
    li = {u: i for i, u in enumerate(uids)}
    groups = [[(x, y, li[u]) for x, y in lst] for u, lst in groups_u]
    return rests, dets, groups


# ───────────────────────── fayllar ─────────────────────────
def tagli(job: SawJob, m, idx: int, name: str, P: B.Parts, L: B.Labels, order: str) -> str:
    ax, cuts = B.cut_tree(m)
    prog = flip_y(B.merge_runs(B.drop_rem(cuts), by_part=False))
    tl, tw = trims(job, m)
    out = ["B_SCH", "B_DAT", f'\tNM="{name}.{idx:03d}"', '\tCMM=""', f'\tMAT="{job.material_name}"', '\tDAY=""', '\tOPZ=""',
           f"\tX={B.cents(m.sheet_length)}", f"\tY={B.cents(m.sheet_width)}", f"\tZ={B.cents(job.thickness)}",
           f"\tHP={B.cents(job.pack_height)}", "\tVL=0", "\tVT=0", f"\tQTA={max(1, m.copies)}", "E_DAT", "B_REF",
           "\tFORZ=0", f"\tROL={B.cents(tl)}", f"\tRMADL={B.cents(tl)}", f"\tRMIDL={B.cents(tl)}", f"\tROT={B.cents(tw)}",
           f"\tRMADT={B.cents(tw)}", f"\tRMIDT={B.cents(tw)}", f"\tRMIP={B.cents(tl)}", "E_REF", "B_CUT"]
    n = 0
    for c in B.walk_cuts(prog):
        n += 1
        out += [f"\tCUT={n}", f'\t\tCOD="{code(c.level, ax)}"', f"\t\tDIM={B.cents(c.dim)}", f"\t\tQTA={c.rep}"]
    out += ["E_CUT", "E_SCH", "B_LABEL"]
    out += label_block(*labels_for_map(job, m, cuts, P, L, order))
    out += ["E_LABEL"]
    return CRLF.join(out) + CRLF


def dist(job: SawJob, name: str, order: str) -> str:
    out = [str(len(job.maps)), "B_FDIS", "\tDAT", f'\t\tNOME="{name}"', '\t\tPROX=""', "\t\tCPI=0", f'\t\tCOMM="{translit(order)}"', "B_DIS"]
    for i, m in enumerate(job.maps, 1):
        com = f"{B.ival(m.sheet_length)}x{B.ival(m.sheet_width)}x{B.ival(job.thickness)}: {job.material_name}"[:40]
        out += ["\tDIS", f"\t\tNM={i}", f'\t\tNPG="{name}.{i:03d}"', f"\t\tQTA={max(1, m.copies)}", "\t\tESE=0", '\t\tOPZ=""',
                f'\t\tCOM="{com}"']
    out += ["E_DIS", "E_FDIS"]
    return CRLF.join(out) + CRLF


def files(job: SawJob) -> dict[str, bytes]:
    """Zip ichidagi fayllar: {`dist/NOME`: …, `tagli/NOME.001`: …} (tekshiruv uchun ham)."""
    name = nome(job)
    order = B.order_name(job)
    P, L = B.Parts(job), B.Labels(job, KEY)
    out = {f"dist/{name}": dist(job, name, order).encode(ENC, "replace")}
    for i, m in enumerate(job.maps, 1):
        out[f"tagli/{name}.{i:03d}"] = tagli(job, m, i, name, P, L, order).encode(ENC, "replace")
    return out


@register(KEY, "Biesse Selco NC300", "saw", "zip",
          note="Etiketka bloki (B_LABEL): detal maydonlari va joylashuv guruhlari yoziladi; boshqa dasturning ichki o'zgaruvchilar "
               "xaritasi va eskizi (CSV 30-maydon) yozilmaydi. Kirill matn — cp1251 (tasdiqlanmagan).")
def gen(job: SawJob):
    f = files(job)
    return [(f"{nome(job)}.zip", B.make_zip(list(f.items())))]
