"""Biesse NC300 / OSI, SCM MaestroCut / WinCut, FELDER Format4 PC6 / PC7 — o'rnatilgan postprotsessorlarni korxona namunalari
bilan tekshirish.     cd tools/bench && python pp_saw_check_biesse.py [exact|e2e|all|chk] [nc300,osi,maestro,wincut,pc6,pc7]

(a) exact — serializator: namuna fayldan kesish kartalari (daraxt) o'qiladi va SawNode ga aylantiriladi, detallar —
    korxona `.project` faylidan BIZNING importer bilan; generatsiya qilib namuna bilan yozuvma-yozuv solishtiriladi.
    Ataylab yozilmaydigan qismlar (boshqa dasturning etiketka bloblari, nazorat summasi, vaqt/UUID) solishtirilmaydi.
(b) e2e — loyiha import → BIZNING optimizator → generatsiya → qayta o'qish: detallar soni/o'lchami/kromka, listlar soni,
    daraxt to'g'riligi (o'lchamlar + propil), faylda «GibLab» so'zi yo'qligi.

Namunalar: `post prtsessorlar/PILNIY APPARAT/<stanok>/`, loyihalar: `giblab project/**/NNNN_<mijoz>.project` (git'ga kirmaydi).
Chiqishda mijoz nomlari bosilmaydi (faqat buyurtma raqami).
"""
from __future__ import annotations

import base64
import collections
import copy
import functools
import glob
import io
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import SawMap, SawNode  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SAMPLES = os.environ.get("PP_SAMPLES") or os.path.join(ROOT, "post prtsessorlar", "PILNIY APPARAT")
PROJECTS = os.environ.get("PP_PROJECTS") or os.path.join(ROOT, "giblab project")
FORBIDDEN = b"giblab"


# ───────────────────────── loyiha ─────────────────────────
@functools.lru_cache(None)
def project_file(order: str):
    c = glob.glob(os.path.join(PROJECTS, "**", f"{order}_*.project"), recursive=True)
    c.sort(key=lambda f: (len(os.path.basename(f)), f))
    return c[0] if c else None


def load_project(order: str):
    f = project_file(order)
    p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
    return p


def norm(s: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", (s or "").lower())


def find_op(p, material: str):
    h = norm(material)
    best = None
    for o in p.operations:
        if o.type != OpType.CS:
            continue
        n = norm(o.name or o.code)
        if n and (n == h or n in h or h in n):
            if best is None or len(n) > len(norm(best.name)):
                best = o
    return best


# ───────────────────────── namuna daraxti → SawNode ─────────────────────────
class N:
    """Namuna kesish yozuvi: daraja, o'lcham, takror, bolalar; barg uchun detal uid / qoldiq."""

    def __init__(self, level, dim, rep=1, tag=None):
        self.level, self.dim, self.rep, self.tag = level, float(dim), int(rep), tag
        self.children: list[N] = []
        self.uid = 0
        self.rem = 0


def nest(items):
    """[(level, dim, rep, tag)] preorder → ildiz bolalari (N)."""
    roots: list[N] = []
    stack: list[N] = []
    for lv, dim, rep, tag in items:
        n = N(lv, dim, rep, tag)
        while stack and stack[-1].level >= lv:
            stack.pop()
        (stack[-1].children if stack else roots).append(n)
        stack.append(n)
    return roots


def other(a):
    return "y" if a == "x" else "x"


def expand(nodes: list[N]) -> list[N]:
    out = []
    for n in nodes:
        for _ in range(n.rep):
            c = copy.copy(n)
            c.rep = 1
            c.children = expand(n.children)
            out.append(c)
    return out


def to_sawnode(nodes: list[N], axis: str, x0: float, y0: float, ext_cross: float, kerf: float, partdim) -> list[SawNode]:
    """Ketma-ket (o'q `axis`) bolalar → SawNode lar (barg: P, uid bo'yicha burilish)."""
    out = []
    pos = x0 if axis == "x" else y0
    for n in nodes:
        x, y = (pos, y0) if axis == "x" else (x0, pos)
        lx, ly = (n.dim, ext_cross) if axis == "x" else (ext_cross, n.dim)
        if n.children:
            s = SawNode(x=x, y=y, l=lx, w=ly, kind="C", axis=other(axis))
            s.children = to_sawnode(n.children, other(axis), x, y, n.dim, kerf, partdim)
        elif n.rem:
            s = SawNode(x=x, y=y, l=lx, w=ly, kind="W", rem=n.rem)
        elif n.uid:
            cl = partdim(n.uid)
            s = SawNode(x=x, y=y, l=lx, w=ly, kind="P", uid=n.uid, rotated=bool(cl and abs(cl[0] - lx) > 0.01))
        else:
            s = SawNode(x=x, y=y, l=lx, w=ly, kind="W")
        out.append(s)
        pos += n.dim + kerf
    return out


def make_map(index, copies, L, W, first_axis, roots: list[N], kerf, trim_eff, trim_raw, partdim, offcuts=()):
    rl, rw = L - 2 * trim_eff, W - 2 * trim_eff
    root = SawNode(x=trim_eff, y=trim_eff, l=rl, w=rw, kind="C", axis=first_axis)
    root.children = to_sawnode(expand(roots), first_axis, trim_eff, trim_eff, rw if first_axis == "x" else rl, kerf, partdim)
    return SawMap(index=index, copies=copies, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id="s", tree=root,
                  placements=[], offcuts=list(offcuts), commands=[], trim_length=trim_raw, trim_width=trim_raw)


def leaves(nodes: list[N], mult=1):
    for n in nodes:
        m = mult * n.rep
        if n.children:
            yield from leaves(n.children, m)
        else:
            yield n, m


def leaf_sizes(nodes: list[N], first_axis: str, root_cross: float):
    """(barg, ko'paytma, sx, sy, oldingi aka-uka barg) — preorder."""
    def rec(ns, axis, cross, mult):
        prev = None
        for n in ns:
            m = mult * n.rep
            if n.children:
                yield from rec(n.children, other(axis), n.dim, m)
                prev = None
            else:
                sx, sy = (n.dim, cross) if axis == "x" else (cross, n.dim)
                yield n, m, sx, sy, prev
                prev = n
    yield from rec(nodes, first_axis, root_cross, 1)


class Stat:
    def __init__(self):
        self.c = collections.Counter()

    def add(self, k, ok, n=1):
        self.c[k + "_n"] += n
        if ok:
            self.c[k + "_ok"] += n

    def line(self):
        ks = sorted({k[:-2] for k in self.c if k.endswith("_n")})
        return ", ".join(f"{k} {self.c[k + '_ok']}/{self.c[k + '_n']}" for k in ks)


def base_job(p, op, key, maps, label_fields=None):
    j = ppfmt.saw_job(p, op, key)
    j.maps = maps
    j.params = dict(j.params)
    if label_fields is not None:
        j.params["_label_fields"] = label_fields
    return j


def tree_ok(m: SawMap, kerf: float) -> list[str]:
    """Daraxt: bolalar ota ichida, o'q bo'ylab ketma-ket (orada ≥ propil), ikkinchi o'qda ota ichida."""
    errs = []

    def rec(n):
        if n.kind != "C":
            return
        a = n.axis
        pos = None
        for ch in sorted(n.children, key=lambda c: c.x if a == "x" else c.y):
            s, e = (ch.x, ch.x + ch.l) if a == "x" else (ch.y, ch.y + ch.w)
            if pos is not None and s + 0.01 < pos + kerf:
                errs.append("kerf")
            pos = e
            if ch.x < n.x - 0.01 or ch.y < n.y - 0.01 or ch.x + ch.l > n.x + n.l + 0.01 or ch.y + ch.w > n.y + n.w + 0.01:
                errs.append("out")
            rec(ch)
    if m.tree is not None:
        rec(m.tree)
        t = m.tree
        if t.x + t.l > m.sheet_length + 0.01 or t.y + t.w > m.sheet_width + 0.01:
            errs.append("sheet")
    return errs


# ═════════════════════════ Biesse NC300 ═════════════════════════
def nc_unover(b: bytes) -> bytes:
    o = bytearray()
    i = 0
    while i < len(b):
        if b[i] == 0xC1:
            o.append(0x40 | (b[i + 1] & 0x3F))
            i += 2
        else:
            o.append(b[i])
            i += 1
    return bytes(o)


def nc_label(text: str):
    seg = text[text.index("B_LABEL\r\n") + 9:text.index("E_LABEL")]
    raw = base64.b64decode("".join(x.strip() for x in seg.split("\r\n")))
    p = 0

    def i32():
        nonlocal p
        v = struct.unpack(">i", raw[p:p + 4])[0]
        p += 4
        return v

    def rec():
        nonlocal p
        p += 1
        n = i32()
        s = raw[p:p + n]
        p += n
        return nc_unover(s).decode("utf-8").split(",")
    rests = []
    for _ in range(i32()):
        rests.append((rec(), i32()))
    dets = [rec() for _ in range(i32())]
    groups = []
    for _ in range(i32()):
        groups.append([(i32(), i32(), i32()) for _ in range(i32())])
    return rests, dets, groups


NC_LV = {"1": 1, "4": 1, "2": 2, "5": 2}


def nc_level(c):
    return NC_LV.get(c) or int(c[1:]) + 2


def nc_parse_tagli(t: str):
    d = dict(re.findall(r"^\t(\w+)=(.*?)\r$", t[:t.index("E_REF")], re.M))
    cuts = re.findall(r'\tCUT=\d+\r\n\t\tCOD="(\w+)"\r\n\t\tDIM=(\d+)\r\n\t\tQTA=(\d+)', t)
    return d, [(nc_level(c), int(dm) / 100, int(q), c) for c, dm, q in cuts]


def nc_unflip(nodes: list, axis: str) -> list:
    for n in nodes:
        n.children = nc_unflip(n.children, other(axis))
    return nodes[::-1] if axis == "y" else nodes


def nc_maps(z: zipfile.ZipFile, p, op):
    kerf = op.cs_cut.kerf
    trim_raw = op.cs_cut.trim_length
    idx = {i: pt.uid for i, pt in enumerate(op.parts, 1)}
    cl = {pt.uid: (pt.length, pt.width) for pt in op.parts}
    maps = []
    names = sorted(n for n in z.namelist() if n.startswith("tagli"))
    for k, n in enumerate(names, 1):
        t = z.read(n).decode("cp1251")
        d, items = nc_parse_tagli(t)
        L, W = int(d["X"]) / 100, int(d["Y"]) / 100
        te = int(d["ROL"]) / 100
        fa = "x" if items[0][3] == "1" else "y"
        # B_CUT da Y o'qi bo'ylab ro'yxatlar teskari (stanok Y o'qi ko'zguli) → geometrik tartibga qaytariladi
        roots = nc_unflip(expand(nest([(lv, dm, q, c) for lv, dm, q, c in items])), fa)
        rests, dets, groups = nc_label(t)
        # barg → detal: etiketka guruhlaridagi o'lchamlar bo'yicha
        pool = collections.defaultdict(list)          # (sx, sy) → [uid, …]
        for g in groups:
            for x, y, li in g:
                pool[(x, y)].append(idx.get(int(dets[li][3]), 0))
        for lf, m, sx, sy, prev in leaf_sizes(roots, fa, (W if fa == "x" else L) - 2 * te):
            key = (round(sx * 100), round(sy * 100))
            lst = pool.get(key) or []
            if lst:
                lf.uid = lst.pop(0)
        offc = []
        if rests:
            used = sum((n2.dim + kerf) * n2.rep for n2 in roots)
            ext = (L if fa == "x" else W) - 2 * te
            rn = N(1, ext - used, 1)
            rn.rem = 1
            roots.append(rn)
            f = rests[0][0]
            offc.append(dict(number=1, kind="remnant", business=True, length=float(f[4]), width=float(f[5]),
                             raw_length=float(f[4]), raw_width=float(f[5]), x=0, y=0))
        maps.append(make_map(k, int(d["QTA"]), L, W, fa, roots, kerf, te, trim_raw, lambda u: cl.get(u), offc))
    return maps


def nc_label_cmp(a: str, b: str, st: Stat):
    ra, da, ga = nc_label(a)
    rb, db, gb = nc_label(b)
    st.add("label_rest", sorted(tuple(r[0][:30]) for r in ra) == sorted(tuple(r[0][:30]) for r in rb))
    ma = collections.Counter(tuple(r[:30]) for r in da)
    mb = collections.Counter(tuple(r[:30]) for r in db)
    st.add("label_det", ma == mb, 1)
    st.add("label_det_rec", True, sum(ma.values()))
    st.c["label_det_rec_ok"] -= sum((ma - mb).values())

    def grp(d, g):
        return collections.Counter((tuple(d[i][:30]), tuple(sorted((x, y) for x, y, i in gg))) for gg in g for i in {gg[0][2]})
    st.add("label_groups", grp(da, ga) == grp(db, gb))


def check_nc300_exact():
    from app.services.ppfmt import biesse_nc300 as M
    st = Stat()
    rep = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Biesse Selco NC300", "*.zip"))):
        order = os.path.basename(f)[:4]
        z = zipfile.ZipFile(f)
        p = load_project(order)
        t1 = z.read(sorted(n for n in z.namelist() if n.startswith("tagli"))[0]).decode("cp1251")
        mat = re.search(r'MAT="(.*?)"', t1).group(1)
        op = find_op(p, mat)
        maps = nc_maps(z, p, op)
        job = base_job(p, op, M.KEY, maps)
        gen = M.files(job)
        sample = {n.replace("\\", "/"): z.read(n) for n in z.namelist()}
        st.add("files", sorted(gen) == sorted(sample))
        bad = []
        for n, b in sample.items():
            g = gen.get(n)
            if g is None:
                bad.append(n)
                continue
            if n.startswith("dist"):
                st.add("dist", g == b)
                if g != b:
                    bad.append(n)
                continue
            sa, sg = b.decode("cp1251"), g.decode("cp1251")
            ha, hg = sa[:sa.index("B_LABEL")], sg[:sg.index("B_LABEL")]
            st.add("tagli_cut", ha == hg)
            if ha != hg:
                bad.append(n)
                la, lg = ha.split("\r\n"), hg.split("\r\n")
                for i, (x, y) in enumerate(zip(la, lg)):
                    if x != y:
                        rep.append(f"   {order} {n}: qator {i}: namuna {x!r} / biz {y!r}")
                        break
            nc_label_cmp(sa, sg, st)
        st.add("orders", not bad)
    print("NC300 exact:", st.line())
    for r in rep[:15]:
        print(r)
    return st


# ═════════════════════════ Biesse OSI ═════════════════════════
OSI_LABELS = [  # namunadagi korxona sozlamasiga mos jadval (standartdan farqi: qMin = count, IIDesc = product.order)
    ("Код", "'P' + part.id"), ("Коорд min", "count"), ("Коорд max", "0"), ("Приоритет", "100"),
    ("Длина", "length"), ("Ширина", "width"), ("Текстура", "if(txt,1,0)"),
    ("Окончательная обработка / Finish", "'S'"), ("Данные отхода", "now('yyyy-MM-dd')"),
    ("Код подформата / PartNo", "indexInOperation"), ("Comment", "description"), ("Job", ""), ("Name", ""),
    ("Описание I", "name"), ("Описание II", "product.order")]
OSI_VOLATILE = {("Order", "Comment"), ("Job", "Comment"), ("WorkList", "Released"), ("Part", "EvDate"), ("Cut", "Chk")}


def osi_norm(e: ET.Element):
    a = {k: v for k, v in e.attrib.items() if (e.tag, k) not in OSI_VOLATILE}
    if e.tag == "WorkList":
        a["Due"] = a.get("Due", "")[:10]
    return a


def osi_maps(r: ET.Element, p, op):
    kerf = op.cs_cut.kerf
    trim_raw = op.cs_cut.trim_length
    cl = {pt.uid: (pt.length, pt.width) for pt in op.parts}
    pieces = {}
    for pc in r.iter("Piece"):
        for pid in pc.findall("Pid"):
            pieces[pid.get("id")] = (float(pc.get("L")), float(pc.get("W")))
    maps = []
    for k, job in enumerate(r.iter("Job"), 1):
        b = job.find("Board")
        L, W = float(b.get("L")), float(b.get("W"))
        te = int(job.find("TechnoParam[@ID='321']").get("Value")) / 100
        cuts = [(nc_level(c.get("Code")), float(c.get("L")), int(c.get("Rep")), c.get("Code")) for c in job.find("Program")]
        fa = "x" if cuts[0][3] == "1" else "y"
        roots = nest(cuts)
        q = int(job.get("QBoards"))
        need = collections.Counter()
        for sid in r.iter("Sid"):
            if sid.get("id") == job.get("Code"):
                for a, v in sid.attrib.items():
                    if a.startswith("qP"):
                        need[a[1:]] += int(v) // q
        for lf, m, sx, sy, prev in leaf_sizes(roots, fa, (W if fa == "x" else L) - 2 * te):
            cands = [pid for pid, c in need.items() if c >= m and pieces.get(pid) in ((sx, sy), (sy, sx))]
            if prev is not None and prev.uid and len(cands) > 1:
                alt = [c for c in cands if int(c[1:]) != prev.uid]
                cands = alt or cands
            cands.sort(key=lambda s: (need[s] != m, int(s[1:])))
            if cands:
                lf.uid = int(cands[0][1:])
                need[cands[0]] -= m
        maps.append(make_map(k, q, L, W, fa, roots, kerf, te, trim_raw, lambda u: cl.get(u)))
    return maps


def osi_strip(raw: bytes, op=None) -> ET.Element:
    """Namuna: tashlangan etiketka elementlarisiz; detal id lari bizning uid ga o'tkaziladi (importer avvalgi dastur
    id larini saqlamaydi — moslik `Code` = operatsiyadagi tartib raqami orqali)."""
    r = ET.fromstring(raw)
    wl = r.find("WorkList")
    for e in list(wl):
        if e.tag.startswith("GibLab"):
            wl.remove(e)
    if op is not None:
        tr = {}
        for e in wl.findall("Part"):
            i = int(e.get("Code"))
            if 1 <= i <= len(op.parts):
                tr[e.get("id")] = f"P{op.parts[i - 1].uid}"
        for e in wl.iter():
            if e.tag in ("Part", "Pid") and e.get("id") in tr:
                e.set("id", tr[e.get("id")])
            if e.tag == "Sid":
                q = {k: v for k, v in e.attrib.items() if k.startswith("qP")}
                for k in q:
                    del e.attrib[k]
                for k, v in q.items():
                    e.set("q" + tr.get(k[1:], k[1:]), v)
    return r


def osi_cmp(a: ET.Element, b: ET.Element, st: Stat, rep: list, order: str):
    st.add("order", osi_norm(a) == osi_norm(b))
    wa, wb = a.find("WorkList"), b.find("WorkList")
    st.add("worklist", osi_norm(wa) == osi_norm(wb))
    pa = {e.get("id"): osi_norm(e) for e in wa.findall("Part")}
    pb = {e.get("id"): osi_norm(e) for e in wb.findall("Part")}
    for k in pa:
        ok = pa[k] == pb.get(k)
        st.add("part", ok)
        if not ok and len(rep) < 30:
            d = {x: (pa[k].get(x), (pb.get(k) or {}).get(x)) for x in set(pa[k]) | set(pb.get(k) or {})
                 if pa[k].get(x) != (pb.get(k) or {}).get(x)}
            rep.append(f"   {order} Part {k}: {d}")
    ja, jb = wa.findall("Job"), wb.findall("Job")
    st.add("jobs_count", len(ja) == len(jb))
    for x, y in zip(ja, jb):
        st.add("job_attr", osi_norm(x) == osi_norm(y))
        st.add("technoparam", [t.attrib for t in x.findall("TechnoParam")] == [t.attrib for t in y.findall("TechnoParam")])
        st.add("board", x.find("Board").attrib == y.find("Board").attrib)
        ca = [osi_norm(c) for c in x.find("Program")]
        cb = [osi_norm(c) for c in y.find("Program")]
        st.add("program", ca == cb)
        if ca != cb and len(rep) < 30:
            rep.append(f"   {order} {x.get('Code')[-3:]} namuna {[(c['Code'], c['L'], c['Rep']) for c in ca]}\n"
                       f"        biz    {[(c['Code'], c['L'], c['Rep']) for c in cb]}")

        def flat(cs):
            return [(c["Code"], c["L"]) for c in cs for _ in range(int(c["Rep"]))]
        st.add("program_expanded", flat(ca) == flat(cb))

    def pcs(w):
        out = collections.Counter()
        for pc in w.findall("Piece"):
            a = {k: v for k, v in pc.attrib.items() if k != "N"}
            out[(tuple(sorted(a.items())), tuple(sorted((e.tag, tuple(sorted(e.attrib.items()))) for e in pc)))] += 1
        return out
    A, Bc = pcs(wa), pcs(wb)
    st.add("pieces", A == Bc)
    st.add("piece_rec", True, sum(A.values()))
    st.c["piece_rec_ok"] -= sum((A - Bc).values())
    if A != Bc and len(rep) < 12:
        rep.append(f"   {order} Piece: namunada bor, bizda yo'q {sum((A - Bc).values())} ta (L/W yo'nalishi yoki guruhlash)")


def check_osi_exact():
    from app.services.ppfmt import biesse_osi as M
    st = Stat()
    rep: list[str] = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Biesse Selco OSI", "*.xml"))):
        order = os.path.basename(f)[:4]
        raw = open(f, "rb").read()
        p = load_project(order)
        mat = ET.fromstring(raw).find(".//Board").get("MatCode")
        op = find_op(p, mat)
        r = osi_strip(raw, op)
        maps = osi_maps(r, p, op)
        job = base_job(p, op, M.KEY, maps, [dict(name=n, expr=e) for n, e in OSI_LABELS])
        g = M.build(job)
        gb = g.encode("utf-8")
        st.add("no_forbidden", FORBIDDEN not in gb.lower())
        osi_cmp(r, ET.fromstring(gb), st, rep, order)
        # bayt-bayt (o'zgaruvchan maydonlar va tashlangan elementlarsiz)
        st.add("bytes_masked_parts+jobs", osi_mask(osi_ser(r, False)) == osi_mask(osi_ser(ET.fromstring(gb), False)))
    print("OSI exact:", st.line())
    for x in rep[:25]:
        print(x)
    return st


def osi_ser(e: ET.Element, pieces=True) -> bytes:
    """Hujjat qoidasi bo'yicha qayta serializatsiya (namuna 14/14 bayt-bayt shu qoida bilan chiqadi)."""
    def ser(x):
        a = "".join(f' {k}="{v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(chr(34), "&quot;")}"'
                    for k, v in sorted(x.attrib.items()))
        ch = [c for c in x if pieces or c.tag != "Piece"]
        return f"<{x.tag}{a}/>" if not ch else f"<{x.tag}{a}>" + "".join(ser(c) for c in ch) + f"</{x.tag}>"
    return ser(e).encode("utf-8")


def osi_mask(b: bytes) -> bytes:
    b = re.sub(rb' Chk="\d+"', b"", b)
    b = re.sub(rb'(Comment|Released|EvDate)="[^"]*"', rb'\1=""', b)
    b = re.sub(rb'Due="(\d{4}-\d\d-\d\d)[^"]*"', rb'Due="\1"', b)
    return b


# ═════════════════════════ SCM MaestroCut / WinCut ═════════════════════════
SCM_LV = {"Y": 1, "X": 2, "U": 3, "V": 4, "W": 5, "Z": 6}
MAESTRO_LABELS = [  # korxona sozlamasiga mos (standartdan farqi: Codice/Job = product.order, Richiesti = count, bo'sh kromka — «»)
    ("Codice", "product.order"), ("Lunghezza", "format('0.00',length)"), ("Larghezza", "format('0.00',width)"),
    ("Richiesti", "count"), ("CodiceBordo1", "ets"), ("CodiceBordo2", "ebs"), ("CodiceBordo3", "els"),
    ("CodiceBordo4", "ers"), ("Job", "product.order")]


def scm_tree(rows, uid_of, rest_sz):
    """rows: [(tur, o'lcham, rip, eti)] → (ildiz N lar, offcut lar). Barg uid — eti dagi birinchi etiketka; qoldiq
    etiketkasi biriktirilgan kesimdan keyin (shu darajada) qoldiq tuguni qo'yiladi. rest_sz: {etiketka id: (L, W)}."""
    items = []
    for t, dim, rip, eti in rows:
        if t not in SCM_LV:
            continue
        items.append((SCM_LV[t], float(dim), int(rip), eti))
    roots = nest(items)
    offc = []

    def rec(ns):
        i = 0
        while i < len(ns):
            n = ns[i]
            ids = [int(x.split(",")[0]) for x in re.findall(r"\(([\d,]+)\)", n.tag or "")]
            rest = [j for j in ids if j in rest_sz]
            ids = [j for j in ids if j not in rest_sz]
            if not n.children and ids:
                n.uid = uid_of.get(ids[0], 0)
            rec(n.children)
            for j in rest:
                rn = N(n.level, 1.0, 1)
                rn.rem = len(offc) + 1
                ln, wd = rest_sz[j]
                offc.append(dict(number=rn.rem, kind="remnant", business=True, length=ln, width=wd, raw_length=ln,
                                 raw_width=wd, x=0, y=0))
                i += 1
                ns.insert(i, rn)
            i += 1
    rec(roots)
    return roots, offc


def maestro_parse(files: dict, op):
    """{nom: bytes} → (kartalar, fayl ID lari, sana, har karta {uid: dona})."""
    kerf_raw = op.cs_cut.trim_length
    cl = {pt.uid: (pt.length, pt.width) for pt in op.parts}
    xm = next(v for k, v in files.items() if k.endswith(".XMix")).decode("cp1251")
    mats = re.findall(r"<Material ([^>]*)/>", xm)
    reps = [int(x) for x in re.findall(r' Rep="(\d+)"', xm)]
    maps, ids = [], []
    names = sorted(k for k in files if k.endswith(".XPrg"))
    for k, n in enumerate(names):
        t = files[n].decode("cp1251")
        h = dict(re.findall(r'(\w+)="([^"]*)"', t[:t.index("/>")]))
        ma = dict(re.findall(r'(\w+)="([^"]*)"', mats[k]))
        L, W = float(ma["Lunghezza"]), float(ma["Larghezza"])
        kerf = float(h["SpessoreLama"])
        rows = re.findall(r'<Cut ID="\d+" T="([\w*]+)" Dim="([\d.]+)" Rip="(\d+)" EtiID="([^"]*)"/>', t)
        te = float(next(r[1] for r in rows if r[0] == "RY"))
        fa = "y" if abs(float(h["Lunghezza"]) - L) < 0.01 and abs(L - W) > 0.01 else ("x" if abs(L - W) > 0.01 else "y")
        uid_of, rest_sz = {}, {}
        for e in re.findall(r"<Etichetta ([^>]*)/>", t):
            a = dict(re.findall(r'(\w+)="([^"]*)"', e))
            if a["Resto"] == "1":
                rest_sz[int(a["Id"])] = (float(a["Lunghezza"]), float(a["Larghezza"]))
            else:
                i = int(a["Campo40"])
                uid_of[int(a["Id"])] = op.parts[i - 1].uid if 1 <= i <= len(op.parts) else 0
        roots, offc = scm_tree(rows, uid_of, rest_sz)
        maps.append(make_map(k + 1, reps[k], L, W, fa, roots, kerf, te, kerf_raw, lambda u: cl.get(u), offc))
        ids.append(h.get("GibLabID") or re.search(r'Campo64="([0-9a-f]*)#', t).group(1))
    d = re.search(r'Date="(\d\d)\.(\d\d)\.(\d{4})"', xm)
    return maps, ids, d.groups() if d else None


def maestro_norm_sample(name: str, b: bytes, op) -> bytes:
    t = b.decode("cp1251")
    if name.endswith(".XMix"):
        return t.replace("From GibLab", "From MebeliX Kroy").encode()
    t = re.sub(r' GibLabID="[^"]*"', "", t)
    i = t.find("<GibLabLabel>")
    if i >= 0:
        t = t[:i] + t[t.index("</GibLabLabel>") + len("</GibLabLabel>\r\n"):]

    def fix(m):
        e = m.group(0)
        if 'Resto="1"' in e:
            return re.sub(r'Campo3="[^"]*"', 'Campo3="*"', e)
        i = int(re.search(r'Campo40="(\d+)"', e).group(1))
        u = op.parts[i - 1].uid if 1 <= i <= len(op.parts) else 0
        return re.sub(r'Campo3="[^"]*"', f'Campo3="{u}"', e)
    return re.sub(r"<Etichetta [^>]*/>", fix, t).encode()


def maestro_norm_ours(name: str, b: bytes) -> bytes:
    t = b.decode("cp1251")
    return re.sub(r'(<Etichetta Id="\d+" Resto="1"[^>]*?)Campo3="[^"]*"', r'\1Campo3="*"', t).encode()


def check_maestro_exact():
    import datetime as dt
    from app.services.ppfmt import scm_maestrocut as M
    st = Stat()
    rep = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "SCM MaestroCut", "*.zip"))):
        order = os.path.basename(f)[:4]
        z = zipfile.ZipFile(f)
        sample = {n: z.read(n) for n in z.namelist()}
        p = load_project(order)
        t1 = next(v for k, v in sample.items() if k.endswith(".XPrg")).decode("cp1251")
        op = find_op(p, re.search(r'Descrizione="([^"]*)"', t1).group(1))
        maps, ids, d = maestro_parse(sample, op)
        job = base_job(p, op, M.KEY, maps, [dict(name=n, expr=e) for n, e in MAESTRO_LABELS])
        gen = M.files(job, when=dt.datetime(int(d[2]), int(d[1]), int(d[0])), ids=ids)
        st.add("names", sorted(gen) == sorted(sample))
        st.add("zipname", f"{ppfmt_stem(job)}.zip" == os.path.basename(f))
        for n, b in sample.items():
            g = gen.get(n)
            if g is None:
                continue
            a, o = maestro_norm_sample(n, b, op), maestro_norm_ours(n, g)
            st.add("no_forbidden", FORBIDDEN not in g.lower())
            if n.endswith(".XMix"):
                st.add("xmix", a == o)
                continue
            st.add("xprg", a == o)
            pa, po = a[:a.index(b"<DatiEtichetta>")], o[:o.index(b"<DatiEtichetta>")]
            st.add("xprg_cuts", pa == po)
            ea, eo = re.findall(rb"<Etichetta [^>]*/>", a), re.findall(rb"<Etichetta [^>]*/>", o)
            for x, y in zip(ea, eo):
                st.add("etichetta", x == y)
                dx, dy = dict(re.findall(rb'(\w+)="([^"]*)"', x)), dict(re.findall(rb'(\w+)="([^"]*)"', y))
                for k in dx:
                    st.add("etichetta_fields", dx[k] == dy.get(k))
                    if dx[k] != dy.get(k):
                        st.c["diff_" + k.decode()] += 1
                df = {k.decode(): (dx.get(k), dy.get(k)) for k in dx if dx.get(k) != dy.get(k) and k not in (b"Campo39", b"Campo60")}
                if df and len(rep) < 12:
                    rep.append(f"   {order} {n[-8:]} Etichetta: {df}")
            if pa != po and len(rep) < 12:
                la, lo = pa.split(b"\r\n"), po.split(b"\r\n")
                i = next((i for i, (x, y) in enumerate(zip(la, lo)) if x != y), min(len(la), len(lo)) - 1)
                rep.append(f"   {order} {n[-8:]} qator {i}: namuna {la[i][:160]!r} / biz {lo[i][:160]!r}")
    print("MaestroCut exact:", st.line(), "| farq qilgan maydonlar:", {k[5:]: v for k, v in st.c.items() if k.startswith("diff_")})
    for r in rep:
        print(r)
    return st


def ppfmt_stem(job):
    from app.services.ppfmt import _saw_bsf as B
    return B.file_stem(job)


def wincut_parse(files: dict, op):
    kerf = op.cs_cut.kerf
    trim_raw = op.cs_cut.trim_length
    cl = {pt.uid: (pt.length, pt.width) for pt in op.parts}
    SL = op.sheets[0].length if op.sheets else 2750.0
    maps = []
    for k, n in enumerate(sorted(files), 1):
        t = files[n].decode("cp1251")
        sec = {}
        cur = None
        for ln in t.split("\r\n"):
            if ln.startswith("["):
                cur = ln
                sec[cur] = []
            elif ln and cur:
                sec[cur].append(ln.split("=", 1))
        h = dict(sec["[Intestazione]"])
        lung, larg, thk = float(h["Lunghezza"]), float(h["Larghezza"]), float(h["Spessore"])
        fa = "y" if abs(lung - SL) < 0.01 or lung > larg else "x"
        L, W = (lung, larg) if fa == "y" else (larg, lung)
        uid_of, rest_sz = {}, {}
        for key, v in sec["[Dati]"]:
            if key == "NumeroDati":
                continue
            f = v.split(",")
            if f[28] == "REST":
                rest_sz[int(key)] = (float(f[6]), float(f[7]))
            else:
                i = int(f[29])
                uid_of[int(key)] = op.parts[i - 1].uid if 1 <= i <= len(op.parts) else 0
        refs = dict(sec["[Riferimenti]"])
        rows = []
        for key, v in sec["[Righe]"]:
            if key == "NumeroRighe":
                continue
            f = v.split(",")
            rows.append((f[0], f[1], f[2], refs.get(key, "")))
        te = float(next(r[1] for r in rows if r[0] == "RY"))
        roots, offc = scm_tree(rows, uid_of, rest_sz)
        maps.append(make_map(k, max(1, int(round(float(h["AltPacco"]) / thk))), L, W, fa, roots, kerf, te, trim_raw,
                             lambda u: cl.get(u), offc))
    return maps


def wincut_norm(b: bytes, op=None) -> bytes:
    out = []
    in_dati = False
    for ln in b.decode("cp1251").split("\r\n"):
        if ln.startswith("["):
            in_dati = ln == "[Dati]"
        elif in_dati and not ln.startswith("NumeroDati") and ln:
            k, v = ln.split("=", 1)
            f = v.split(",")
            f[30] = ""
            if f[28] == "REST":
                f[5] = "*"
            elif op is not None:
                i = int(f[29])
                f[5] = str(op.parts[i - 1].uid) if 1 <= i <= len(op.parts) else f[5]
            ln = k + "=" + ",".join(f)
        out.append(ln)
    return "\r\n".join(out).encode()


def check_wincut_exact():
    from app.services.ppfmt import scm_wincut as M
    st = Stat()
    rep = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "SCM WinCut", "*.zip"))):
        order = os.path.basename(f)[:4]
        z = zipfile.ZipFile(f)
        sample = {n.replace("\\", "/"): z.read(n) for n in z.namelist()}
        p = load_project(order)
        t1 = next(iter(sample.values())).decode("cp1251")
        op = find_op(p, re.search(r"Descrizione=(.*?)\r", t1).group(1))
        job = base_job(p, op, M.KEY, wincut_parse(sample, op))
        gen = M.files(job)
        st.add("names", sorted(gen) == sorted(sample))
        for n, b in sample.items():
            g = gen.get(n)
            if g is None:
                continue
            a, o = wincut_norm(b, op), wincut_norm(g)
            st.add("file", a == o)
            st.add("no_forbidden", FORBIDDEN not in g.lower())
            if a != o and len(rep) < 12:
                la, lo = a.split(b"\r\n"), o.split(b"\r\n")
                i = next((i for i, (x, y) in enumerate(zip(la, lo)) if x != y), min(len(la), len(lo)) - 1)
                rep.append(f"   {order} {n[-3:]} qator {i}: namuna {la[i][:120]!r} / biz {lo[i][:120]!r}")
    print("WinCut exact:", st.line())
    for r in rep:
        print(r)
    return st


# ═════════════════════════ FELDER PC6 / PC7 ═════════════════════════
# Headdata.text: namunada buyurtma nomi (standart: project.name); Part.text0: namunada har tomon 2 belgi («1 » yoki 2 bo'shliq;
# standart ifodada bo'sh tomon — 1 bo'shliq)
PC6_LABELS_FIX = {1: "product.order",
                  5: "+".join(f"if(empty({x}),'  ',if({t}>1,2,1)+' ')" for x, t in
                              (("ets", "ett"), ("ebs", "ebt"), ("els", "elt"), ("ers", "ert")))}
PC7_LABELS_FIX = {1: "product.order"}


def felder_rows(key, fix):
    from app.services import pp_machine_schema as S
    rows = S.default_label_rows(key)
    for i, e in fix.items():
        rows[i] = dict(name=rows[i]["name"], expr=e)
    return rows


def felder_maps(recs, op, uid_of, pc7: bool, rest_net=None):
    """recs: [(tur, maydonlar)] MA200 dan boshlab → kartalar. Barg: (uid | 'R', X, Y)."""
    trim_raw = op.cs_cut.trim_length
    cl = {pt.uid: (pt.length, pt.width) for pt in op.parts}
    maps = []
    cur = None

    def flush():
        if cur is None:
            return

        def fix(n):                               # yashirin bo'lak o'lchami — ichidagilarning eng katta cheti
            for c in n.children:
                fix(c)
            if n.tag == "implicit":
                n.dim = max([sum(g.dim for g in c.children) + cur["kerf"] * (len(c.children) - 1)
                             for c in n.children if c.children] or [n.dim])
        for r in cur["roots"]:
            fix(r)
        maps.append(make_map(len(maps) + 1, cur["copies"], cur["L"], cur["W"], cur["fa"] or "y", cur["roots"], cur["kerf"],
                             cur["te"], trim_raw, lambda u: cl.get(u), cur["rest"]))
    stack = {}
    for typ, f in recs:
        if typ == "MA200":
            flush()
            if pc7:
                cur = dict(L=float(f[5]), W=float(f[6]), copies=int(f[7]), te=float(f[10]), kerf=float(f[14]))
            else:
                cur = dict(L=float(f[5]), W=float(f[6]), copies=int(f[7]), te=float(f[10]), kerf=float(f[14]))
            cur.update(roots=[], fa=None, rest=[])
            continue
        if cur is None or not typ.startswith("MA") or typ == "MA999":
            continue
        fam, k = typ[2], int(typ[3])
        fa = "y" if fam == "3" else "x"
        cur["fa"] = fa
        if k == 0:
            s = N(1, float(f[1]), 1)
            s.tag = "rest" if (pc7 and len(f) > 2) else None      # qoldiq polosasi: xom o'lcham (uzoq trim bilan)
            if s.tag:
                s.dim -= cur["te"]
            cur["roots"].append(s)
            stack = {1: s}
            continue
        name = f[1].strip()
        X, Y = float(f[2]), float(f[3])
        Lv = (k + 3) // 2 if k % 2 else (k + 4) // 2

        def ax(level):
            return fa if level % 2 else other(fa)

        def size(level):
            return X if ax(level) == "x" else Y
        is_rem = name.startswith("R")
        if is_rem:
            net = rest_net(f) if rest_net else (X, Y)
            cur["rest"].append(dict(number=len(cur["rest"]) + 1, kind="remnant", business=True, length=net[0], width=net[1],
                                    raw_length=X, raw_width=Y, x=0, y=0))
            if stack[1].tag == "rest" and k == 1:
                stack[1].rem = len(cur["rest"])
                continue
        new_parent = k % 2 == 0
        if new_parent:
            for lv in [x for x in stack if x >= Lv - 1]:
                del stack[lv]
        for lv in range(2, Lv):                   # yo'q oraliq bo'laklar (yashirin) — o'lchami barg bo'yicha
            if lv not in stack:
                pn = N(lv, size(lv), 1)
                pn.tag = "implicit" if lv < Lv - 1 else None
                stack[lv - 1].children.append(pn)
                stack[lv] = pn
                for hi in [x for x in stack if x > lv]:
                    del stack[hi]
            else:
                stack[lv].dim = max(stack[lv].dim, size(lv)) if lv < Lv - 1 else stack[lv].dim
        leaf = N(Lv, size(Lv), 1)
        if is_rem:
            leaf.rem = len(cur["rest"])
        else:
            leaf.uid = uid_of(name)
        stack[Lv - 1].children.append(leaf)
        for hi in [x for x in stack if x >= Lv]:
            del stack[hi]
        if Lv == 2:
            for hi in [x for x in stack if x >= 2]:
                del stack[hi]
    flush()
    return maps


def pc6_parse(b: bytes, op):
    lines = b.decode("cp1251").split("\r\n")
    recs = []
    for ln in lines:
        if ln.startswith("###"):
            break
        if ln.startswith("MA"):
            f = ln.split("/")
            recs.append((f[0], f))
    i0 = next(i for i, r in enumerate(recs) if r[0] == "MA200")

    def uid_of(name):
        i = int(name)
        return op.parts[i - 1].uid if 1 <= i <= len(op.parts) else 0
    return felder_maps(recs[i0:], op, uid_of, False)


def pc6_norm(b: bytes, ours: bool) -> list[str]:
    out = []
    for ln in b.decode("cp1251").split("\r\n"):
        if ln.startswith("###"):
            break
        if not ours:
            ln = ln.replace("/GibLab  /", "/MebeliX /").replace("/GibLab/", "/Mebeli/")
        ln = re.sub(r"#N\(\d+\)", "#N(*)", ln)
        ln = re.sub(r"#P\(\d+\) *", "#P(*)", ln)
        if ln[:5] in ("MA005", "MA010", "MA015", "MA050", "MA200"):
            f = ln.split("/")
            f[1], f[2] = "<code>", "<op>"
            ln = "/".join(f)
        out.append(ln)
    while out and not out[-1]:
        out.pop()
    return out


def check_pc6_exact():
    import datetime as dt
    from app.services.ppfmt import felder_format4 as M
    st = Stat()
    rep = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Felder PC6", "*.may"))):
        order = os.path.basename(f)[:4]
        raw = open(f, "rb").read()
        p = load_project(order)
        t = raw.decode("cp1251")
        op = find_op(p, t.split("\r\n")[1].split("/")[4])
        job = base_job(p, op, M.KEY6, pc6_parse(raw, op), felder_rows(M.KEY6, PC6_LABELS_FIX))
        d = t[6:12]
        g = M.pc6(job, when=dt.datetime(2000 + int(d[4:6]), int(d[2:4]), int(d[0:2]))).encode("cp1251")
        st.add("no_forbidden", FORBIDDEN not in g.lower())
        st.add("filename", f"{ppfmt_stem(job)}.may" == os.path.basename(f))
        a, o = pc6_norm(raw, False), pc6_norm(g, True)
        st.add("file", a == o)
        st.add("material_code+op_id (importda saqlanmaydi)", raw.split(b"/", 3)[:0] == [] and t.splitlines()[1].split("/")[1:3] == g.decode("cp1251").splitlines()[1].split("/")[1:3])
        st.add("lines_count", len(a) == len(o))
        for x, y in zip(a, o):
            st.add("rec_" + x[:5].replace("MA31", "MA3k").replace("MA32", "MA3k").replace("MA33", "MA3k")
                   .replace("MA34", "MA3k").replace("MA35", "MA3k").replace("MA41", "MA4k").replace("MA42", "MA4k")
                   .replace("MA43", "MA4k").replace("MA44", "MA4k").replace("MA45", "MA4k"), x == y)
            if x != y and len(rep) < 12:
                rep.append(f"   {order}: namuna {x[:230]!r}\n            biz {y[:230]!r}")
    print("Felder PC6 exact:", st.line())
    for r in rep:
        print(r)
    return st


def pc7_parse(b: bytes, op):
    recs = []
    idx = {}
    rest = {}
    for ln in b.decode("utf-8").split("\r\n"):
        if ln.startswith("MA"):
            f = ln.split("§§")
            recs.append((f[0], f))
            if f[0] == "MA010":
                if f[4] == "REST":
                    rest[f[1]] = (float(f[5]), float(f[6]))
                else:
                    idx[f[1]] = int(f[17])
    i0 = next(i for i, r in enumerate(recs) if r[0] == "MA200")

    def uid_of(name):
        i = idx.get(name[1:], 0)
        return op.parts[i - 1].uid if 1 <= i <= len(op.parts) else 0
    return felder_maps(recs[i0:], op, uid_of, True, lambda f: rest.get(f[4], (float(f[2]), float(f[3]))))


def pc7_norm(b: bytes, ours: bool) -> list[str]:
    lines = [ln.split("§§") for ln in b.decode("utf-8").split("\r\n")]
    idx = {f[1]: f[17] for f in lines if f[0] == "MA010" and f[4] != "REST"}
    out = []
    for f in lines:
        f = list(f)
        if f[0] == "MA000" and not ours:
            f[2] = "MebeliX Kroy" if f[2] == "GibLab" else f[2]
        elif f[0] == "MA010":
            if f[4] == "REST":
                f[1], f[-1] = "*", "#P(*)"
            else:
                f[1], f[27] = f[17], "#P(*)"
        elif f[0] == "MA200":
            f[4] = "#N(*)"
        elif re.fullmatch(r"MA[34][1-9]0", f[0]):
            if f[1].startswith("R"):
                f[4] = "*"
            else:
                f[1] = "D" + idx.get(f[1][1:], "?")
                f[4] = idx.get(f[4], "?")
        out.append("§§".join(f))
    return out


def check_pc7_exact():
    import datetime as dt
    from app.services.ppfmt import felder_format4 as M
    st = Stat()
    rep = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Felder PC7", "*.may"))):
        order = os.path.basename(f)[:4]
        raw = open(f, "rb").read()
        p = load_project(order)
        first = raw.decode("utf-8").split("\r\n")
        op = find_op(p, next(x.split("§§")[18] for x in first if x.startswith("MA010")))
        job = base_job(p, op, M.KEY7, pc7_parse(raw, op), felder_rows(M.KEY7, PC7_LABELS_FIX))
        d = first[0].split("§§")[1]
        g = M.pc7(job, when=dt.datetime(int(d[6:10]), int(d[3:5]), int(d[0:2]))).encode("utf-8")
        st.add("no_forbidden", FORBIDDEN not in g.lower())
        a, o = pc7_norm(raw, False), pc7_norm(g, True)
        st.add("file", a == o)
        st.add("lines_count", len(a) == len(o))
        for x, y in zip(a, o):
            k = x[:5]
            k = "MA010R" if (k == "MA010" and "§§REST§§" in x) else ("MAxk0" if re.match(r"MA[34][1-9]", k) else k)
            st.add("rec_" + k, x == y)
            if x != y and len(rep) < 12:
                rep.append(f"   {order}: namuna {x[:230]!r}\n            biz {y[:230]!r}")
    print("Felder PC7 exact:", st.line())
    for r in rep:
        print(r)
    return st


# ═════════════════════════ (b) END-TO-END ═════════════════════════
def unzip(b: bytes) -> dict:
    z = zipfile.ZipFile(io.BytesIO(b))
    return {n: z.read(n) for n in z.namelist()}


def e2e_reparse(key: str, name: str, data: bytes, op):
    """Generatsiya qilingan fayl(lar)ni qayta o'qish → (kartalar, barcha baytlar, kromka belgilari {uid: (t, b, l, r)} | None)."""
    edges = None
    by_idx = {i: pt.uid for i, pt in enumerate(op.parts, 1)}
    if key == "biesse_nc300":
        fl = unzip(data)
        maps = nc_maps(zipfile.ZipFile(io.BytesIO(data)), None, op)
        edges = {}
        for n, b in fl.items():
            if n.startswith("tagli"):
                for d in nc_label(b.decode("cp1251"))[1]:
                    edges[by_idx.get(int(d[3]), 0)] = (d[12], d[13], d[10], d[11])
        blob = b"".join(fl.values()) + "".join(fl).encode()
    elif key == "biesse_osi":
        r = ET.fromstring(data)
        maps = osi_maps(r, None, op)
        edges = {int(e.get("id")[1:]): tuple(e.get(f"TypEdge{s}", "") for s in ("Up", "Lo", "L", "R")) for e in r.iter("Part")}
        blob = data
    elif key == "scm_maestrocut":
        fl = unzip(data)
        maps = maestro_parse(fl, op)[0]
        edges = {}
        for n, b in fl.items():
            for e in re.findall(r"<Etichetta ([^>]*)/>", b.decode("cp1251")):
                a = dict(re.findall(r'(\w+)="([^"]*)"', e))
                if a["Resto"] == "0":
                    edges[int(a["Campo3"])] = tuple(a[f"CodiceBordo{i}"].strip() for i in range(1, 5))
        blob = b"".join(fl.values()) + "".join(fl).encode()
    elif key == "scm_wincut":
        fl = unzip(data)
        maps = wincut_parse(fl, op)
        blob = b"".join(fl.values()) + "".join(fl).encode("utf-8")
    elif key == "felder_format4_pc6":
        maps = pc6_parse(data, op)
        edges = {}
        k = 0
        for ln in data.decode("cp1251").split("\r\n"):
            if ln.startswith("MA010"):
                k += 1
                f = ln.split("/")
                edges[by_idx.get(k, 0)] = tuple((re.match(r"\((.*?)\)", f[15 + i].strip()) or [None, ""])[1] for i in range(4))
        blob = data
    else:
        maps = pc7_parse(data, op)
        edges = {}
        for ln in data.decode("utf-8").split("\r\n"):
            f = ln.split("§§")
            if f[0] == "MA010" and f[4] != "REST":
                edges[int(f[1])] = tuple((re.match(r"\((.*?)\)", f[9 + i]) or [None, ""])[1] for i in range(4))
        blob = data
    return maps, blob + name.encode("utf-8"), edges


def walk_nodes(n):
    yield n
    for c in n.children:
        yield from walk_nodes(c)


def e2e_one(key: str, p, op, st: Stat, rep: list, tag: str):
    from app.services.ppfmt import _saw_bsf as B
    fmt = ppfmt.load_all()[key]
    job = ppfmt.saw_job(p, op, key)
    files = fmt.fn(job)
    name, data = files[0]
    try:
        maps, blob, edges = e2e_reparse(key, name, data, op)
    except Exception as e:  # noqa: BLE001
        st.add("reparse", False)
        rep.append(f"   {tag} {key}: qayta o'qishda xato {type(e).__name__}: {e}")
        return
    st.add("reparse", True)
    st.add("no_forbidden", FORBIDDEN not in blob.lower())
    res = op.result
    st.add("sheets", sum(m.copies for m in maps) == sum(m.copies for m in res.maps) and len(maps) == len(res.maps))
    saw = {sp.uid: sp for sp in job.parts}
    # detallar soni: optimizator joylashtirganlari bilan teng
    want = collections.Counter()
    for m in res.maps:
        for pl in m.placements:
            want[pl.part_uid] += m.copies
    got = collections.Counter()
    size_ok = True
    for m in maps:
        for n in walk_nodes(m.tree):
            if n.kind == "P":
                got[n.uid] += m.copies
                sp = saw.get(n.uid)
                if sp is None:
                    size_ok = False
                    continue
                straight = abs(n.l - sp.length) < 0.06 and abs(n.w - sp.width) < 0.06
                turned = abs(n.l - sp.width) < 0.06 and abs(n.w - sp.length) < 0.06
                if not (straight or (turned and not (sp.grain and op.cs_cut.use_grain))):
                    size_ok = False
    ok = got == want
    st.add("parts_qty", ok)
    if not ok and len(rep) < 20:
        rep.append(f"   {tag} {key}: detallar soni farq: yetishmaydi {dict((want - got).most_common(4))}, ortiqcha {dict((got - want).most_common(4))}")
    st.add("parts_size", size_ok)
    placed_all = all(want[sp.uid] == sp.qty for sp in job.parts) or bool(res.unplaced)
    st.add("all_placed_or_reported", placed_all)
    te = [tree_ok(m, job.kerf) for m in maps]
    st.add("tree_valid", not any(te))
    if any(te) and len(rep) < 20:
        rep.append(f"   {tag} {key}: daraxt xatosi {[e[:3] for e in te if e][:2]}")
    if edges is not None:
        P = B.Parts(job)
        eo = all(tuple(P.edge(u, s).get("symbol", "") for s in ("top", "bottom", "left", "right")) == edges.get(u)
                 for u in got)
        st.add("edges", eo)
    # qoldiqlar (format qoldiq yozsa): soni
    if key in ("scm_maestrocut", "scm_wincut", "felder_format4_pc7", "biesse_nc300"):
        nr = sum(1 for m in maps for n in walk_nodes(m.tree) if n.kind == "W" and n.rem)
        st.c["remnants_written"] += nr


def check_e2e(sel=None, quality=None):
    from app.services.calc import run_cutting
    keys = {"nc300": "biesse_nc300", "osi": "biesse_osi", "maestro": "scm_maestrocut", "wincut": "scm_wincut",
            "pc6": "felder_format4_pc6", "pc7": "felder_format4_pc7"}
    orders = sorted({os.path.basename(f)[:4] for d in ("Biesse Selco NC300", "Biesse Selco OSI", "SCM MaestroCut", "SCM WinCut",
                                                        "Felder PC6", "Felder PC7")
                     for f in glob.glob(os.path.join(SAMPLES, d, "*"))})
    if os.environ.get("PP_ORDERS"):
        orders = os.environ["PP_ORDERS"].split(",")
    stats = {k: Stat() for k in keys.values() if sel is None or any(keys[s] == k for s in sel if s in keys)}
    rep: list[str] = []
    nops = 0
    for order in orders:
        if not project_file(order):
            continue
        p = load_project(order)
        for oi, op in enumerate([o for o in p.operations if o.type == OpType.CS], 1):
            if not op.parts:
                continue
            run_cutting(p, op, quality=quality or os.environ.get("PP_QUALITY") or "fast")
            if not op.result or not op.result.maps:
                continue
            nops += 1
            for key, st in stats.items():
                try:
                    e2e_one(key, p, op, st, rep, f"{order}/op{oi}")
                except Exception as e:  # noqa: BLE001
                    st.add("generate", False)
                    rep.append(f"   {order}/op{oi} {key}: xato {type(e).__name__}: {e}")
    print(f"END-TO-END: {len(orders)} loyiha, {nops} CS kroy (bizning optimizator)")
    for key, st in stats.items():
        print(f"  {key}: {st.line()}; yozilgan qoldiqlar {st.c['remnants_written']}")
    for r in rep[:25]:
        print(r)
    return stats


# ═════════════════════════ OSI `Chk` izlanishi ═════════════════════════
def chk_research():
    """OSI oxirgi kesimidagi nazorat summasi: 14 namunadagi 80 qiymat bo'yicha oddiy gipotezalarni sinaydi (bayt
    oraliqlari × algoritmlar). Hozircha birortasi mos kelmagan; qiymat kesimlar soniga deyarli chiziqli (≈ 2400 / kesim)."""
    import binascii
    import zlib

    def fletcher16(b):
        s1 = s2 = 0
        for x in b:
            s1 = (s1 + x) % 255
            s2 = (s2 + s1) % 255
        return s2 << 8 | s1

    def algos(b):
        a, c = zlib.adler32(b), zlib.crc32(b)
        return {"sum": sum(b), "crc32": c, "crc32&1FFFF": c & 0x1FFFF, "adler": a, "adler_lo": a & 0xFFFF, "adler_hi": a >> 16,
                "fletcher16": fletcher16(b), "crc16": binascii.crc_hqx(b, 0), "crc16_ffff": binascii.crc_hqx(b, 0xFFFF),
                "sum16le": sum(int.from_bytes(b[i:i + 2], "little") for i in range(0, len(b), 2)),
                "sum16be": sum(int.from_bytes(b[i:i + 2], "big") for i in range(0, len(b), 2))}
    hits = collections.Counter()
    total = 0
    ratio = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Biesse Selco OSI", "*.xml"))):
        raw = open(f, "rb").read()
        for m in re.finditer(rb'<Job Code="[^"]*"', raw):
            js = m.start()
            job = raw[js:raw.find(b"</Job>", js) + 6]
            cm = re.search(rb' Chk="(\d+)"', job)
            chk = int(cm.group(1))
            nochk = job[:cm.start()] + job[cm.end():]
            prog = nochk[nochk.find(b"<Program>"):nochk.find(b"</Program>") + 10]
            cuts = re.findall(rb"<Cut [^>]*/>", prog)
            vals = [(c[0], c[1], c[2]) for c in re.findall(rb'Code="(\w+)" L="([\d.]+)" Rep="(\d+)"', prog)]
            total += 1
            ratio.append(chk / len(cuts))
            ranges = {"job": nochk, "program": prog, "cuts": b"".join(cuts), "file_to_chk": raw[:js + cm.start()],
                      "values": b"".join(a + b + c for a, b, c in vals),
                      "cents": b"".join(a + str(int(round(float(b) * 100))).encode() + c for a, b, c in vals)}
            nums = {"sum_L": sum(float(b) for _a, b, _c in vals), "sum_LxRep": sum(float(b) * int(c) for _a, b, c in vals),
                    "sum_cents": sum(round(float(b) * 100) for _a, b, _c in vals)}
            for rn, b in ranges.items():
                for an, v in algos(b).items():
                    for mod in (None, 65536, 131072, 100000, 1000000):
                        if (v % mod if mod else v) == chk:
                            hits[(rn, an, mod)] += 1
            for nn, v in nums.items():
                for mod in (None, 65536, 131072, 100000, 1000000):
                    if int(v) % (mod or 10 ** 12) == chk:
                        hits[(nn, "num", mod)] += 1
    print(f"OSI Chk: {total} ta qiymat; mos kelgan gipotezalar: {dict(hits) or 'yo`q'}; Chk / kesimlar soni: "
          f"{min(ratio):.0f}…{max(ratio):.0f}")


# ═════════════════════════ ishga tushirish ═════════════════════════
EXACT = {"nc300": check_nc300_exact, "osi": check_osi_exact, "maestro": check_maestro_exact, "wincut": check_wincut_exact,
         "pc6": check_pc6_exact, "pc7": check_pc7_exact}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    sel = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    if mode in ("exact", "all"):
        for k, fn in EXACT.items():
            if sel is None or k in sel:
                fn()
    if mode in ("e2e", "all"):
        check_e2e(sel)
    if mode == "chk":
        chk_research()


if __name__ == "__main__":
    main()
