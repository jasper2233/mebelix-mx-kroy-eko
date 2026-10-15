"""KDT KS33X va KDT «yangi versiya» — zip ichida har karta uchun `NUM=<k>   PANELS( <n> x 1 = <n> ).qk` (ikkilik
float32/int32 massiv, kesish rejasi) va `.lbd` (big-endian, UTF matnlar: kesish daraxti + etiketka qatorlari).
Tavsif: docs/mebelix/postprocessors/kdt-ks33x.md, kdt-novaya-versiya.md.

Etiketka qatorining oxirgi maydoni (avvalgi dasturning ichki etiketka blobi) yozilmaydi — bo'sh qoladi; qolgan
maydonlar (soni, tartib raqami, o'lcham, nom, kromka belgilari, tekstura) ochiq CSV ko'rinishida yoziladi."""
from __future__ import annotations

import struct

from . import Files, SawJob, num, register, zip_files
from ._saw_common import job_title
from ._saw_giben import GN, GPat, leaf_counts, patterns

T_STRIP, T_PART, T_REST = "Полоса", "Деталь", "Остаток"      # stanok dasturi kutadigan tur nomlari
REST_CODE = "Д"
FAN = 20                      # har tugunda farzandlar uchun ajratilgan joy
A_COUNT = 20000               # A jadvali yozuvlari soni
SIZE_OLD, SIZE_NEW = 2720032, 2920032
A_BASE = {1: 11, 2: 101, 3: 1001}                 # daraja → A jadvalidagi boshlang'ich indeks
A_LIMIT = {1: 101, 2: 1001, 3: A_COUNT}
B_BASE = {1: 2, 2: 102, 3: 1002, 4: 10022}
B_LIMIT = {1: 102, 2: 1002, 3: 10022}


def _utf(s: str) -> bytes:
    b = s.encode("utf-8")
    if len(b) > 65535:
        b = b[:65535]
    return struct.pack(">H", len(b)) + b


def ks_tree(job: SawJob, P: GPat) -> list[dict]:
    """KDT daraxti: 1-daraja teskari tartibda; farzandli bo'lak takrori «kitob» sig'imi bo'yicha bo'linadi
    (⌊paket balandligi / (qalinlik × listlar)⌋); qoldiq — 1-daraja oxirida."""
    t, pkg = job.thickness, job.pack_height
    maxrep = max(1, int(pkg // (t * P.copies))) if pkg > 0 and t > 0 else 10 ** 9
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}

    def conv(nodes: list[GN]) -> list[dict]:
        out = []
        for c in nodes:
            if not c.kids:
                p = job.part(c.uid)
                out.append(dict(strip=0, typ=T_PART, cut=float(c.size), rep=c.rep, idx=int(c.uid),
                                code=str(idx.get(c.uid, 0)), l=float(p.length) if p else 0.0,
                                w=float(p.width) if p else 0.0, fl=0))
            else:
                n = c.rep
                kids = conv(c.kids)
                while n > 0:
                    k = min(maxrep, n)
                    n -= k
                    out.append(dict(strip=1, typ=T_STRIP, cut=float(c.size), rep=k, ch=kids))
        return out

    nodes = conv(P.kids[::-1])
    if P.rest is not None:
        r = P.rest
        cut = r.l if P.axis == "x" else r.w
        nodes.append(dict(strip=0, typ=T_REST, cut=float(cut), rep=1, idx=rest_id(job, P), code=f"{REST_CODE}{r.number}",
                          l=float(r.l), w=float(r.w), fl=1))
    return nodes


def rest_id(job: SawJob, P: GPat) -> int:
    """Qoldiq yozuvi kaliti: detal id lari bilan to'qnashmaydigan son (yoki «rest_id» sozlamasi)."""
    forced = job.params.get("rest_id")
    if forced:
        return int(forced)
    return max([p.uid for p in job.parts] or [0]) + max(1, P.rest.number if P.rest else 1)


def qk(job: SawJob, P: GPat, nodes: list[dict], new: bool = False) -> bytes:
    ea = 13 if new else 12
    b = bytearray(SIZE_NEW if new else SIZE_OLD)
    kerf = job.kerf
    bstart = 4 + ea * A_COUNT + (1 if new else 0)
    struct.pack_into("<f", b, 0, kerf)

    def put_a(i: int, f0: float, f1: float, f2: float):
        o = 4 + ea * i
        struct.pack_into("<fff", b, o, f0, f1, f2)
        if new:
            b[o + 12] = 1

    def put_b(i: int, cut: float, rep: int):
        struct.pack_into("<fii", b, bstart + 12 * i, cut, 0, rep)

    put_a(1, P.off1, P.dimy, P.dimx)
    struct.pack_into("<ffi", b, bstart + 12, P.dimy, P.dimx, 0)

    def walk(ns: list[dict], lvl: int, prank: int, pdim: float):
        if lvl > 4:
            raise ValueError("KDT KS33X: kesim 4 darajadan chuqur — stanok formati qo'llamaydi "
                             "(«Макс. количество вращений» ni kamaytiring)")
        if len(ns) > (90 if lvl == 1 else FAN):
            raise ValueError(f"KDT KS33X: bitta bo'lakda {len(ns)} ta kesim — format chegarasi "
                             f"{90 if lvl == 1 else FAN}")
        for j, n in enumerate(ns):
            r = j if lvl == 1 else prank * FAN + j
            if lvl in A_BASE:
                if A_BASE[lvl] + r >= A_LIMIT[lvl] or B_BASE[lvl] + r >= B_LIMIT[lvl]:
                    raise ValueError("KDT KS33X: kesimlar soni format jadvaliga sig'maydi (polosalar juda ko'p)")
                put_a(A_BASE[lvl] + r, P.off1 if lvl == 1 else 0.0, pdim, n["cut"])
            elif bstart + 12 * (B_BASE[lvl] + r) + 12 > len(b):
                raise ValueError("KDT KS33X: kesimlar soni format jadvaliga sig'maydi")
            put_b(B_BASE[lvl] + r, n["cut"], n["rep"])
            if n["strip"]:
                walk(n["ch"], lvl + 1, r, n["cut"])

    walk([n for n in nodes if not n.get("fl")], 1, 0, P.dimx)      # qoldiq .qk ga yozilmaydi
    return bytes(b)


def _node(n: dict) -> bytes:
    out = bytes([n["strip"]]) + _utf(n["typ"]) + struct.pack(">d", n["cut"]) + struct.pack(">i", n["rep"])
    if n["strip"]:
        out += struct.pack(">i", len(n["ch"])) + b"".join(_node(c) for c in n["ch"])
    else:
        out += struct.pack(">i", n["idx"]) + _utf(n["code"]) + struct.pack(">dd", n["l"], n["w"]) + bytes([n["fl"]])
    return out


def _csv(v) -> str:
    return str(v).replace(",", " ").replace("\r", " ").replace("\n", " ")


def labels(job: SawJob, P: GPat, nodes: list[dict], title: str, new: bool) -> list[tuple[int, str]]:
    """Etiketka qatorlari (kalit, CSV) — Java HashMap tartibida (savat = kalit & (sig'im−1), savat ichida kiritish
    tartibi)."""
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    on_sheet = leaf_counts(P.kids)
    order: list[int] = []
    rest = None

    def seen(ns: list[dict]):
        nonlocal rest
        for n in ns:
            if n["strip"]:
                seen(n["ch"])
            elif n["fl"]:
                rest = n
                if n["idx"] not in order:
                    order.append(n["idx"])
            elif n["idx"] not in order:
                order.append(n["idx"])

    seen(nodes)
    rows: dict[int, str] = {}
    for uid in order:
        if rest is not None and uid == rest["idx"]:
            f = ["rest.fme", "", "1", "1", num(rest["l"]), num(rest["w"]), f"{rest['l'] * rest['w'] / 1e6:.3f}", title]
        else:
            p = job.part(uid)
            if p is None:
                continue

            def sym(side: str) -> str:
                return (p.edges.get(side) or {}).get("symbol", "") or ""
            cnt = on_sheet.get(uid, 0) if new else p.qty
            f = ["detail.fme", "", str(cnt), str(idx.get(uid, 0)), "1", title, num(p.length), num(p.width), _csv(p.name),
                 str(p.qty), sym("left"), sym("right"), sym("top"), sym("bottom"), "true" if p.grain else "false"]
        f += [""] * (31 - len(f))                  # oxirgi (31-) maydon — etiketka blobi: yozilmaydi
        rows[uid] = ",".join(_csv(x) for x in f)
    cap = 16
    while len(rows) > cap * 3 // 4:
        cap *= 2
    keys = sorted(rows, key=lambda k: ((k ^ (k >> 16)) & (cap - 1), order.index(k)))
    return [(k, rows[k]) for k in keys]


def lbd(job: SawJob, P: GPat, nodes: list[dict], title: str, new: bool = False) -> bytes:
    out = struct.pack(">i", len(nodes)) + b"".join(_node(n) for n in nodes)
    lb = labels(job, P, nodes, title, new)
    out += struct.pack(">i", len(lb)) + b"".join(struct.pack(">i", k) + _utf(s) for k, s in lb)
    return out + (b"\x00" if new else b"")


def _files(job: SawJob, new: bool) -> Files:
    title = job_title(job)
    files: Files = []
    for k, P in enumerate(patterns(job), 1):
        nodes = ks_tree(job, P)
        base = f"NUM={k}   PANELS( {P.copies} x 1 = {P.copies} )"
        files.append((base + ".qk", qk(job, P, nodes, new)))
        files.append((base + ".lbd", lbd(job, P, nodes, title, new)))
    return [(title + ".zip", zip_files(files))]


_NOTE = ("Zip: har karta uchun `.qk` + `.lbd`. Namunalarda faqat birinchi material chiqarilgan; bizda har CS "
         "operatsiyasi alohida zip. Etiketka blobi (avvalgi dasturning ichki ma'lumoti: o'zgaruvchilar + chizma) "
         "yozilmaydi — CSV ning oxirgi maydoni bo'sh; stanok etiketkasi uni talab qilsa, aniqlash kerak. Format "
         "chegaralari: ≤ 4 kesim darajasi, har bo'lakda ≤ 20 kesim. Farzandli bo'lak takrori ⌊paket balandligi / "
         "(qalinlik × listlar)⌋ bo'yicha bo'linadi (faqat 16 mm / 40 mm bilan tasdiqlangan). ")


@register("kdt_ks33x", "KDT KS33X (.qk + .lbd)", "saw", "zip", note=_NOTE)
def kdt_ks33x(job: SawJob) -> Files:
    return _files(job, False)


@register("kdt_new", "KDT yangi versiya (.qk + .lbd)", "saw", "zip",
          note=_NOTE + "Yangi versiya: `.qk` 2 920 032 bayt (A yozuvi 13 bayt), etiketkada soni — kartadagi dona.")
def kdt_new(job: SawJob) -> Files:
    return _files(job, True)
