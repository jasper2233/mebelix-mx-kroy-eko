"""Scheer («Pa») — zip: `NAME.CUT` (dastur nomi), `soll.cut` (kartalar ro'yxati), `holz0000.rec` (ikkilik kesish rejasi),
`teile.lst` (detallar ro'yxati). Tavsif: docs/mebelix/postprocessors/scheer.md.

`holz0000.rec` (little-endian): 0x180 bayt o'zgarmas sarlavha, keyin 0x580 baytli bloklar — 0-blok stanokning standart
yozuvi (o'zgarmas), keyin har karta: 128 bayt karta sarlavhasi + 64 ta 20 baytli kesim yozuvi (`<hffh8s`): soni, 1-/3-daraja
o'lchami, 2-daraja o'lchami, 0, detal raqami (8 belgi; konteynerda bo'sh). 3-daraja yozuvida soni = 100 + dona.
Stanok faqat 3 kesim darajasini biladi. Etiketka fayli (`etikett.bin` — avvalgi dasturning ZPL etiketka dizayni)
chiqarilmaydi. Matnlar — lotin (transliteratsiya), katta harflar."""
from __future__ import annotations

from ...i18n import _
import struct

from . import Files, SawJob, register, safe_name, zip_files
from . import _saw_strips as S
from ._saw_common import job_title
from ._saw_giben import translit

MAX_LEVEL = 3                 # stanok kesim darajalari
MAX_CUTS = 64                 # bitta karta blokidagi kesim yozuvlari
BLOCK = 128 + 20 * MAX_CUTS   # 0x580
ENC = "ascii"
CRLF = "\r\n"


def _sparse(size: int, items: dict[int, str]) -> bytes:
    b = bytearray(size)
    for o, h in items.items():
        v = bytes.fromhex(h)
        b[o:o + len(v)] = v
    return bytes(b)


# Fayl sarlavhasi (0x180 bayt) — namunadagi o'zgarmas stanok yozuvlari (ma'nosi noma'lum: ikki yozuv 110 / 3000 / 3 /
# 110 / 6345 / 3, stanok papkasi `d:\scheer\`, 1000 / 2000 / 150 / 190); kroyga bog'liq emas deb olindi.
HEAD = _sparse(0x180, {
    0x00: "04000000dc4200803b45000040400000dc420048c64500004040",
    0x24: "013e22cd0000ae86a20d9770cf0900a07759dc34924ad74d01007c19db097748656c76004f087038dc341f5cdc34ca6427480100271527150002",
    0x6a: "01", 0x70: "16002d000000643a5c7363686565725c", 0xc8: "e803d0070000164300003e43",
    0x100: "02000000dc4200803b45000040400000dc420048c64500004040"})
# 0-blok: stanokning standart yozuvi (2500 × 2050 × 16, «DAMS1») — kesimsiz, o'zgarmas.
BLOCK0 = _sparse(BLOCK, {0x00: "010000401c450020004500008041000001000000030001",
                         0x1c: "204103010301000020410000fa430100000044414d5331202020202020202020202001"})
# Karta sarlavhasidagi o'zgarmas maydonlar (ofset → qiymat); o'lcham, qalinlik, raqam va material — kroydan.
SHEET_CONST = {0x00: "0b00", 0x14: "04000100281a00002041030103010000204100004843010000", 0x43: "04",
               0x4a: "0000fa430000fa430000c6c20000c6c2d7a3ee41"}


def _txt(s: str, n: int) -> str:
    """Lotin, katta harflar, `n` belgi (bo'sh joy bilan to'ldiriladi); vergul — maydon ajratuvchi, bo'sh joyga."""
    t = translit(s or "").upper().replace(",", " ").replace("\r", " ").replace("\n", " ").replace("?", "_")
    return t[:n].ljust(n)


def program_name(job: SawJob) -> str:
    """Dastur nomi — 8 belgi: «program_name» sozlamasi yoki loyiha nomi (lotin)."""
    forced = str(job.params.get("program_name") or "").strip()
    if forced:
        return safe_name(translit(forced), "kroy", 8).replace("?", "_")
    pn = (job.project_name or "").strip()
    order = (job.order or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order}_{pn}" if pn else order
    return safe_name(translit(pn), "kroy", 8).replace("?", "_")


def cuts(job: SawJob, mi: S.MapInfo, k: int) -> list[tuple[int, float, int, int]]:
    """Kesim yozuvlari (preorder): (daraja, o'lcham, takror, detal uid — konteynerda 0). Qoldiq / chiqindi yozilmaydi."""
    out: list[tuple[int, float, int, int]] = []

    def walk(p: S.Piece, lvl: int) -> None:
        for run in S.runs([c for c in p.children if c.kind != "R"]):
            c = run[0]
            if lvl > MAX_LEVEL or (c.kind == "C" and lvl == MAX_LEVEL):
                raise ValueError(_("pp_e_level_k", fmt="Scheer", k=k, m=MAX_LEVEL))
            out.append((lvl, c.size(p.axis), len(run), c.uid if c.kind == "P" else 0))
            if c.kind == "C":
                walk(c, lvl + 1)

    if mi.root is not None:
        walk(mi.root, 1)
    if len(out) > MAX_CUTS:
        raise ValueError(_("pp_e_cuts", fmt="Scheer", k=k, n=len(out), m=MAX_CUTS))
    return out


def _dims(mi: S.MapInfo) -> tuple[float, float]:
    """(1-daraja kesimlar o'qi bo'ylab list o'lchami, ikkinchi o'lcham)."""
    return (mi.L, mi.W) if mi.axis == "x" else (mi.W, mi.L)


def rec(job: SawJob, plans: list[tuple[S.MapInfo, list]]) -> bytes:
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    out = bytearray(HEAD + BLOCK0)
    for k, (mi, cs) in enumerate(plans, 1):
        h = bytearray(_sparse(128, SHEET_CONST))
        d1, d2 = _dims(mi)
        struct.pack_into("<fffh", h, 2, d1, d2, job.thickness, k)
        h[0x2e:0x3e] = _txt(job.material_name, 16).encode(ENC, "replace")
        out += h
        for lvl, size, n, uid in cs:
            name = (str(idx.get(uid, 0)) if uid else "").ljust(8)[:8].encode(ENC)
            a, b = (0.0, size) if lvl == 2 else (size, 0.0)
            out += struct.pack("<hffh8s", n + (100 if lvl == 3 else 0), a, b, 0, name)
        out += bytes(20 * (MAX_CUTS - len(cs)))
    return bytes(out)


def soll(job: SawJob, plans: list[tuple[S.MapInfo, list]]) -> str:
    mat, title = _txt(job.material_name, 16), _txt(S.project_title(job), 31)
    out = []
    for k, (mi, _cs) in enumerate(plans, 1):
        d1, d2 = _dims(mi)
        out.append(f"{k:4d},{d2:6.1f},{d1:6.1f},{job.thickness:6.1f},{mat},{max(1, mi.m.copies):4d},{0.0:6.1f}, ,{title}")
    return CRLF.join(out) + CRLF


def teile(job: SawJob, plans: list[tuple[S.MapInfo, list]], name: str) -> str:
    """Har detal kesim yozuvi uchun bitta qator: karta, material, detal raqami, jami soni, shu paytgacha kesilgani
    (o'sib boruvchi), loyiha o'lchami, tekstura belgisi."""
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    mat = _txt(job.material_name, 16)
    done: dict[int, int] = {}
    out = []
    for k, (mi, cs) in enumerate(plans, 1):
        mult = {0: max(1, mi.m.copies)}                  # daraja → ota konteynerlar takrori ko'paytmasi
        for lvl, _size, n, uid in cs:
            if not uid:
                mult[lvl] = mult[lvl - 1] * n
                continue
            p = job.part(uid)
            if p is None:
                continue
            done[uid] = done.get(uid, 0) + n * mult[lvl - 1]
            out.append(f"{name:<8},{name:<8},{k:3d},{k:3d},{mat},{job.thickness:4.1f},{str(idx.get(uid, 0)):<10},{p.qty:3d},"
                       f"{done[uid]:3d},{p.length:7.1f},{p.width:7.1f},{1 if p.grain else 0},{'':4},{'':4},{'':12},{'':30},{'':30}")
    return CRLF.join(out) + CRLF


NOTE = ("Zip: NAME.CUT, soll.cut, holz0000.rec, teile.lst. Stanok 3 kesim darajasini biladi («Макс. количество вращений» ≤ 3), "
        "bitta kartada ≤ 64 kesim yozuvi. Etiketka fayli (etikett.bin) chiqarilmaydi. Bitta namunadan o'rganilgan: "
        "holz0000.rec sarlavhasi va karta sarlavhasidagi bir nechta maydon namunadagi doimiylar (ma'nosi noma'lum); "
        "torsovka va propil faylda yo'q (stanok sozlamasidan). Dastur nomi — 8 belgi (sozlama «program_name» yoki loyiha nomi).")


@register("scheer", "Scheer (Pa) — NAME.CUT + soll.cut + holz0000.rec", "saw", "zip", note=NOTE)
def generate(job: SawJob) -> Files:
    name = program_name(job)
    plans = []
    for k, mi in enumerate(S.map_infos(job), 1):
        plans.append((mi, cuts(job, mi, k)))
    files = [("NAME.CUT", f"{name:<32}{CRLF}".encode(ENC, "replace")),
             ("soll.cut", soll(job, plans).encode(ENC, "replace")),
             ("holz0000.rec", rec(job, plans)),
             ("teile.lst", teile(job, plans, name).encode(ENC, "replace"))]
    return [(job_title(job) + ".zip", zip_files(files))]
