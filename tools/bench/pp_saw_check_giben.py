"""Arra postprotsessorlari (Giben G57 / GVisionXP / GDrive, KDT XML / KS33X / yangi versiya) — korxona namunalari bilan
tekshiruv.    cd tools/bench && python pp_saw_check_giben.py [g57 gvision gdrive xml ks33x new] [--no-e2e] [--stress=N]

(a) ANIQ: kesish daraxtlari NAMUNADAN o'qiladi (KDT XML namunasi — 10 buyurtmaning hammasida bor, to'liq chuqurlik va
    detal id lari bilan) va SawNode ga aylantiriladi; detallar korxona loyihasidan BIZNING importer bilan olinadi;
    generator natijasi namuna bilan bayt-bayt solishtiriladi (ataylab yozilmaydigan avvalgi dastur etiketka blobi va
    KDT XML ichki `id` / `O<n>` hisoblagichlaridan tashqari).
(b) OXIRIDAN-OXIRIGACHA: loyihani import qilib BIZNING optimizator bilan kroy qilamiz, fayl yaratamiz, uni mustaqil
    parser bilan qayta o'qiymiz: kesim daraxti, detallar (o'lcham / soni), listlar soni, geometriya (list ichida, propil
    bilan), «GibLab» so'zi yo'qligi.

Namunalar va loyihalar korxona fayllari — repoga kirmaydi (yo'llar quyida; bo'lmasa skript o'tkazib yuboradi).
"""
from __future__ import annotations

import functools
import glob
import io
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))

from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import SawMap, SawNode  # noqa: E402
from app.services.ppfmt._saw_common import job_title, leaves, part_totals  # noqa: E402
from app.services.ppfmt._saw_giben import GN, depth, layout, leaf_counts, merge, patterns  # noqa: E402

SAMPLES = os.environ.get("PP_SAMPLES", r"D:/cloude giblab jasur/post prtsessorlar/PILNIY APPARAT")
PROJECTS = os.environ.get("PP_PROJECTS", r"D:/cloude giblab jasur/giblab project")
FORBIDDEN = b"giblab"
DIRS = dict(g57="GIben G57", gvision="Giben GVisionXP", gdrive="Giben GDrive", xml="KDT XML", ks33x="KDT KS33X",
            new="KDT Новий версия")
KEYS = dict(g57="giben_g57", gvision="giben_gvisionxp", gdrive="giben_gdrive", xml="kdt_presize_xml",
            ks33x="kdt_ks33x", new="kdt_new")


# ───────────────────────── umumiy ─────────────────────────
@functools.lru_cache(None)
def project_file(order: str):
    c = glob.glob(os.path.join(PROJECTS, "**", f"{order}_*.project"), recursive=True)
    c.sort(key=lambda f: (len(os.path.basename(f)), f))
    return c[0] if c else None


def load(order: str):
    f = project_file(order)
    if not f:
        return None
    p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
    return p


def first_cs(p):
    return next((o for o in p.operations if o.type == OpType.CS and o.parts), None)


def run_opt(p, op):
    from app.services.calc import run_cutting
    run_cutting(p, op)
    return op


def samples(kind: str, ext: str) -> dict[str, str]:
    return {os.path.basename(f)[:4]: f for f in sorted(glob.glob(os.path.join(SAMPLES, DIRS[kind], "*." + ext)))}


def unzip(data: bytes) -> list[tuple[str, bytes]]:
    z = zipfile.ZipFile(io.BytesIO(data))
    return [(i.filename, z.read(i)) for i in z.infolist()]


def no_forbidden(files) -> bool:
    for name, data in files:
        if FORBIDDEN in data.lower() or FORBIDDEN in name.lower().encode():
            return False
        if data[:2] == b"PK":
            if not no_forbidden(unzip(data)):
                return False
    return True


def first_diff(a: bytes, b: bytes, enc="utf-8") -> str:
    la, lb = a.decode(enc, "replace").split("\n"), b.decode(enc, "replace").split("\n")
    nd = sum(x != y for x, y in zip(la, lb)) + abs(len(la) - len(lb))
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"{nd} qator farq; {i + 1}-qator: biz «{x[:100]}» | namuna «{y[:100]}»"
    return f"qatorlar soni {len(la)} vs {len(lb)}"


# ───────────────────────── parserlar (mustaqil o'qish) ─────────────────────────
class Pat:
    """Fayldan qayta o'qilgan karta: darajali daraxt (GN), nusxalar, o'lcham, siljishlar."""

    def __init__(self, kids, copies, dimx, dimy, off1=None, off2=None, rest=None):
        self.kids, self.copies, self.dimx, self.dimy, self.off1, self.off2, self.rest = (kids, copies, dimx, dimy, off1,
                                                                                       off2, rest)


def tree_from_cuts(cuts, base=3):
    """[(daraja, o'lcham, takror, uid)] pre-order → GN ro'yxati."""
    root = GN(0.0)
    stack = [(base - 1, root)]
    for lvl, q, n, uid in cuts:
        nd = GN(q, rep=n, uid=uid)
        while stack[-1][0] >= lvl:
            stack.pop()
        assert stack[-1][0] == lvl - 1, "daraja sakrashi"
        stack[-1][1].kids.append(nd)
        stack.append((lvl, nd))
    return root.kids


def fdt_parse(data: bytes):
    """→ dict(parts [(uid, l, w)], sheets, pats [Pat], leaves [[(uid, x0, y0, x1, y1)]], kerf)."""
    txt = data.decode("cp1251")
    assert "\r" not in txt and txt.endswith("\n")
    parts, pats, lvs, sheets = [], [], [], []
    cur = None
    sect = ""
    rec: dict = {}
    kerf = 0.0
    for ln in txt.split("\n")[:-1]:
        m = re.match(r"^\[(Start|End)([A-Za-z_]+?)(\d*)\]$", ln)
        if m:
            st, nm = m.group(1) == "Start", m.group(2)
            if st:
                sect = nm
                if nm in ("DatiElementoFDT", "DatiPannelloFDT", "DatiPannelloFDS", "DatiElementoFDS", "Tg_Ed"):
                    rec = {}
            else:
                if nm == "DatiElementoFDT":
                    parts.append((int(rec["IDP"]), int(rec["XBA"]) / 1000, int(rec["YAL"]) / 1000))
                elif nm == "DatiPannelloFDT":
                    sheets.append((rec["IDL"], int(rec["XBA"]) / 1000, int(rec["YAL"]) / 1000, int(rec["QTA"])))
                elif nm == "DatiPannelloFDS":
                    cur = dict(rec=rec, cuts=[], leaves=[])
                    pats.append(cur)
                elif nm == "DatiElementoFDS":
                    cur["leaves"].append((int(rec["IDP"]),) + tuple(int(rec[k]) / 1000 for k in
                                                                    ("XANGINF", "YANGINF", "XANGSUP", "YANGSUP")))
                elif nm == "Tg_Ed":
                    cur["cuts"].append((int(rec["TIPOTG"]), int(rec["QUOTATG"]) / 1000, int(rec["QTARIP"]), 0))
                sect = ""
            continue
        k, _, v = ln.partition(" = ")
        assert _ == " = ", f"g'alati qator: {ln!r}"
        if k == "SPESSORELAMA":
            kerf = int(v) / 1000
        rec[k] = v
    out = []
    for c in pats:
        r = c["rec"]
        kids = tree_from_cuts(c["cuts"])
        it = iter(c["leaves"])

        def fill(nodes, live=True):          # barg uid lari FDS dan (takrorlarning birinchisi)
            for n in nodes:
                if n.kids:
                    fill(n.kids, live)
                    for _ in range(n.rep - 1):
                        fill(n.kids, False)
                else:
                    ids = [next(it)[0] for _ in range(n.rep)]
                    if live:
                        assert len(set(ids)) == 1, "takrorlangan bargda turli detal"
                        n.uid = ids[0]
        if c["leaves"]:
            fill(kids)
        p = Pat(kids, int(r["RIPETIZIONI"]), int(r["DIMX"]) / 1000, int(r["DIMY"]) / 1000)
        p.trims = (int(r["RIFILO3"]) / 1000, int(r["RIFILO4"]) / 1000)
        out.append(p)
        assert r["FOGLIPACCO"] == r["RIPETIZIONI"]
    return dict(parts=parts, sheets=sheets, pats=out, leaves=[c["leaves"] for c in pats], kerf=kerf)


class _Rd:
    def __init__(self, b):
        self.b, self.i = b, 0

    def raw(self, n):
        v = self.b[self.i:self.i + n]
        assert len(v) == n
        self.i += n
        return v

    def zfield(self, size):
        out = bytearray()
        while len(out) < size:
            c = self.b[self.i]
            self.i += 1
            if c == 0xFC:
                n = self.b[self.i]
                self.i += 1
                assert n > 0, "maydon o'rtasida yozuv oxiri"
                out += bytes(n)
            else:
                out.append(c)
        assert len(out) == size
        return bytes(out)

    def end(self):
        assert self.raw(2) == b"\xfc\x00", "yozuv oxiri belgisi yo'q"


def dax_parse(b: bytes):
    """→ (qalinlik×1000, [yozuv dict(idx, l, w, qty, name, kind)])."""
    r = _Rd(b)
    assert r.raw(2) == b"\x04\x00"
    a = r.zfield(160) + r.zfield(1) + r.zfield(40)
    r.end()
    thick = struct.unpack_from("<i", a, 55)[0]
    bb = r.raw(2) + r.zfield(70) + r.zfield(1) + r.zfield(128)
    r.end()
    assert bb[:2] == b"\xff\xff" and len(a) == len(bb) == 201
    recs = []
    while r.i < len(b):
        idx, l, w, q = struct.unpack("<4i", r.raw(16))
        r.zfield(24)
        name = r.zfield(40).rstrip(b"\0").decode("cp1251")
        kind, q2, q3 = struct.unpack("<3i", r.raw(12))
        tail = r.zfield(68) + r.zfield(1) + r.zfield(40)
        r.end()
        assert q == q2 == q3 and not any(tail)
        recs.append(dict(idx=idx, l=l / 1000, w=w / 1000, qty=q, name=name, kind=kind))
    return thick, recs


def cpx_parse(b: bytes):
    """→ [dict(copies, dimx, dimy, sheet, cuts [(daraja, o'lcham, takror, detal indeksi)])]."""
    r = _Rd(b)
    assert r.raw(2) == b"\x04\x00"
    cards = []
    while r.i < len(b):
        if b[r.i:r.i + 2] == b"\xff\xff":
            r.raw(2)
            k, sh, cp, dx, dy = struct.unpack("<h4i", r.raw(18))
            assert r.zfield(76) == b"\x01" + bytes(75) and k == len(cards) + 1
            r.end()
            cards.append(dict(copies=cp, dimx=dx / 1000, dimy=dy / 1000, sheet=sh, cuts=[]))
            continue
        lvl, part, size, rep = struct.unpack("<hhih", r.raw(10))
        assert not any(r.zfield(38))
        r.end()
        if lvl == 2:
            assert part == 0 and rep == 1 and abs(size / 1000 - cards[-1]["dimx"]) < 1e-6 and not cards[-1]["cuts"]
            continue
        cards[-1]["cuts"].append((lvl, size / 1000, rep, part))
    return cards


def xml_parse(txt: str):
    """KDT XML → dict(panels [dict(attrs, nodes {id: dict(attrs, parts)})], parts [(code, l, w, sq, uc, rc)])."""
    def attrs(s):
        return dict(re.findall(r'([a-z]+)="([^"]*)"', s))
    lines = txt.split("\n")
    assert lines[0] == '<?xml version="1.0" encoding="UTF-8"?>' and lines[1] == "<project>" and lines[-1] == "</project>"
    panels, plist = [], []
    cur = node = None
    in_parts = False
    nos = []
    for ln in lines[2:-1]:
        if ln.startswith("<panel"):
            cur = dict(a=attrs(ln), nodes={})
            panels.append(cur)
        elif ln.startswith("<no."):
            a = attrs(ln)
            nos.append(int(re.match(r"<no\.(\d+) ", ln).group(1)))
            node = dict(a=a, parts=[])
            assert a["id"] not in cur["nodes"], "takror id"
            cur["nodes"][a["id"]] = node
        elif ln.startswith("<part "):
            a = attrs(ln)
            if in_parts:
                plist.append((a["code"], float(a["l"]), float(a["w"]), int(a["sq"]), int(a["uc"]), int(a["rc"])))
            else:
                node["parts"].append(a)
        elif ln == "<parts>":
            in_parts = True
        else:
            assert ln == "" or ln.startswith("</"), f"g'alati qator {ln!r}"
    assert nos == list(range(1, len(nos) + 1)), "no.N uzluksiz emas"
    return dict(panels=panels, parts=plist)


def xml_pats(x, strict=True):
    """XML panellar → [Pat] (takrorlar birlashtirilgan); strict — geometriya (x, y, l, w, trim) ham tekshiriladi."""
    out = []
    for pn in x["panels"]:
        a = pn["a"]
        kerf = float(a["saw"])
        root = pn["nodes"]["0"]
        rest = None
        seen = {"0"}

        def conv(nd, layer):
            nonlocal rest
            res = []
            pos = float(nd["a"]["trim"])
            na = nd["a"]
            assert int(na["layer"]) == layer
            for p in nd["parts"]:
                ch = pn["nodes"][p["id"]]
                seen.add(p["id"])
                ca = ch["a"]
                cut = float(p["cut"])
                if strict:
                    ex, ey = ((float(na["x"]), float(na["y"]) + pos) if layer % 2 else
                              (float(na["x"]) + pos, float(na["y"])))
                    assert (abs(float(ca["x"]) - ex) < 1e-6 and abs(float(ca["y"]) - ey) < 1e-6
                            and abs(float(ca["l"]) - float(na["w"])) < 1e-6 and abs(float(ca["w"]) - cut) < 1e-6), \
                        "bo'lak geometriyasi qoidaga mos emas"
                    assert pos + cut <= float(na["l"]) + 1e-6, "bo'lak otasidan chiqdi"
                pos += cut + kerf
                if p["type"] == "3":
                    assert layer == 1 and p is nd["parts"][-1] and not ch["parts"]
                    rest = (p["code"], cut)
                elif p["type"] == "1":
                    assert not ch["parts"] and float(ca["trim"]) == 0
                    res.append(GN(cut, uid=int(p["code"])))
                else:
                    assert p["type"] == "2" and ch["parts"]
                    res.append(GN(cut, kids=merge(conv(ch, layer + 1)),
                                  lead=float(ca["trim"]) if layer + 1 >= 3 else 0.0))
            return res

        kids = merge(conv(root, 1))
        assert seen == set(pn["nodes"]), "bog'lanmagan tugun"
        off2 = None
        for p in root["parts"]:
            ch = pn["nodes"][p["id"]]
            if ch["parts"]:
                off2 = float(ch["a"]["trim"])
        out.append(Pat(kids, int(a["num"]), float(a["w"]), float(a["l"]), float(root["a"]["trim"]), off2, rest))
    return out


class _JR:
    def __init__(self, b):
        self.b, self.i = b, 0

    def int(self):
        v = struct.unpack_from(">i", self.b, self.i)[0]
        self.i += 4
        return v

    def bool(self):
        v = self.b[self.i]
        self.i += 1
        assert v in (0, 1)
        return v

    def dbl(self):
        v = struct.unpack_from(">d", self.b, self.i)[0]
        self.i += 8
        return v

    def utf(self):
        n = struct.unpack_from(">H", self.b, self.i)[0]
        v = self.b[self.i + 2:self.i + 2 + n].decode("utf-8")
        self.i += 2 + n
        return v


def lbd_parse(b: bytes):
    """→ (tugunlar, [(kalit, csv)], qolgan baytlar)."""
    r = _JR(b)

    def node():
        st, typ, cut, rep = r.bool(), r.utf(), r.dbl(), r.int()
        if st:
            n = r.int()
            return dict(strip=1, typ=typ, cut=cut, rep=rep, ch=[node() for _ in range(n)])
        return dict(strip=0, typ=typ, cut=cut, rep=rep, idx=r.int(), code=r.utf(), l=r.dbl(), w=r.dbl(), fl=r.bool())

    nodes = [node() for _ in range(r.int())]
    labels = [(r.int(), r.utf()) for _ in range(r.int())]
    return nodes, labels, b[r.i:]


def qk_parse(b: bytes, new: bool):
    """.qk → dict(kerf, off, l, w, tree [(cut, rep, kids)]); jadvaldagi hamma nol bo'lmagan yozuv daraxtga kirishi shart."""
    ea = 13 if new else 12
    assert len(b) == (2920032 if new else 2720032)
    bs = 4 + ea * 20000 + (1 if new else 0)
    left = bytearray(b)

    def mark(o, n):
        left[o:o + n] = bytes(n)

    def ga(i):
        o = 4 + ea * i
        mark(o, ea)
        v = struct.unpack_from("<fff", b, o)
        if new:
            assert b[o + 12] == 1
        return v

    def gb(i):
        o = bs + 12 * i
        v = struct.unpack_from("<fii", b, o)
        return v

    kerf = struct.unpack_from("<f", b, 0)[0]
    off, l, w = ga(1)
    bl, bw, z = struct.unpack_from("<ffi", b, bs + 12)
    assert (bl, bw, z) == (l, w, 0)
    mark(0, 4)
    mark(bs + 12, 12)
    abase = {1: 11, 2: 101, 3: 1001}
    bbase = {1: 2, 2: 102, 3: 1002, 4: 10022}

    def kids(lvl, prank, pdim):
        res = []
        for j in range(90 if lvl == 1 else 20):
            r = j if lvl == 1 else prank * 20 + j
            o = bs + 12 * (bbase[lvl] + r)
            if o + 12 > len(b) or (lvl < 4 and bbase[lvl] + r >= bbase[lvl + 1]):
                break
            cut, z, rep = gb(bbase[lvl] + r)
            if rep == 0:
                break
            assert z == 0
            mark(o, 12)
            if lvl in abase:
                f0, f1, f2 = ga(abase[lvl] + r)
                assert f2 == cut and f1 == pdim and f0 == (off if lvl == 1 else 0.0), "A jadvali B ga mos emas"
            res.append((cut, rep, kids(lvl + 1, r, cut) if lvl < 4 else []))
        return res

    tree = kids(1, 0, w)
    assert left.count(0) == len(left), "daraxtga kirmagan nol bo'lmagan baytlar bor"
    return dict(kerf=kerf, off=off, l=l, w=w, tree=tree)


# ───────────────────────── namuna → SawJob ─────────────────────────
def sample_maps(order: str, op):
    """KDT XML namunasidan kesish daraxtlari → SawMap (list koordinatalarida, G57 qoidasi bo'yicha geometriya)."""
    zf = samples("xml", "zip").get(order)
    if not zf:
        return None, None
    name, data = next((n, d) for n, d in unzip(open(zf, "rb").read()) if n.endswith(".xml"))
    x = xml_parse(data.decode("utf-8"))
    pats = xml_pats(x)
    sheet = op.sheets[-1]
    L, W = sheet.length, sheet.width
    maps = []
    meta = dict(sheet_id=x["panels"][0]["a"]["code"], kerf=float(x["panels"][0]["a"]["saw"]))
    kerf = meta["kerf"]
    for i, P in enumerate(pats):
        axis = "x" if abs(P.dimy - L) < 0.01 and abs(P.dimx - W) < 0.01 else "y"
        off = P.off1

        def to_sheet(cx, cy, cw, ch):
            return (cy, cx, ch, cw) if axis == "x" else (cx, cy, cw, ch)

        def build(nodes, lvl, cx0, cy0, cw, ch, endpos, lead=0.0):
            """bolalar (SawNode ro'yxati) — karta koordinatasida (cx0, cy0, cw × ch) bo'lak ichida."""
            along_y = lvl % 2 == 1
            pos = (cy0 if along_y else cx0) + lead
            res = []
            for n in nodes:
                for _ in range(n.rep):
                    rect = (cx0, pos, cw, n.size) if along_y else (pos, cy0, n.size, ch)
                    sx, sy, sl, sw = to_sheet(*rect)
                    if n.kids:
                        ax = ("y" if axis == "x" else "x") if along_y else axis
                        c = SawNode(x=sx, y=sy, l=sl, w=sw, kind="C", axis=ax, level=lvl)
                        c.children = build(n.kids, lvl + 1, rect[0], rect[1], rect[2], rect[3], None, n.lead)
                    else:
                        c = SawNode(x=sx, y=sy, l=sl, w=sw, kind="P", uid=n.uid, level=lvl)
                    res.append(c)
                    pos += n.size + kerf
            if endpos is not None and P.rest is not None:
                rect = (cx0, pos, cw, endpos - pos)
                sx, sy, sl, sw = to_sheet(*rect)
                res.append(SawNode(x=sx, y=sy, l=sl, w=sw, kind="W", rem=1, level=lvl))
            return res

        root = SawNode(x=off, y=off, l=L - 2 * off, w=W - 2 * off, kind="C", axis=axis)
        root.children = build(P.kids, 1, off, off, P.dimx - 2 * off, P.dimy - 2 * off, P.dimy - off)
        offcuts = []
        if P.rest is not None:
            w = root.children[-1]
            offcuts.append(dict(x=w.x, y=w.y, length=w.l, width=w.w, kind="remnant", number=1, business=True,
                                raw_length=w.l, raw_width=w.w, in_part=0))
        maps.append(SawMap(index=i + 1, copies=P.copies, sheet_length=L, sheet_width=W, is_remnant=False,
                           sheet_id=sheet.id, tree=root, placements=[], offcuts=offcuts, commands=[],
                           trim_length=off - kerf, trim_width=off - kerf))
    return maps, meta


@functools.lru_cache(None)
def sample_job(order: str, key: str):
    p = load(order)
    if p is None:
        return None
    op = first_cs(p)
    maps, meta = sample_maps(order, op)
    if maps is None:
        return None
    job = ppfmt.saw_job(p, op, key)
    job.maps = maps
    job.params = dict(job.params or {}, sheet_id=meta["sheet_id"])
    # Namunalarda detal raqami — loyiha faylidagi `part/@id`; bizning importer detallarni qayta raqamlaydi (uid 1..N,
    # operatsiya tartibida). Solishtirish uchun shu operatsiya detallariga fayldagi raqamlarni qo'yamiz.
    ids = legacy_ids(order)
    if len(ids) != len(job.parts) or any((round(l, 3), round(w, 3)) != (round(sp.length, 3), round(sp.width, 3))
                                         for (_, l, w), sp in zip(ids, job.parts)):
        return None
    for (i, _, _), sp in zip(ids, job.parts):
        sp.uid = i
    return job


def legacy_ids(order: str):
    """Loyiha faylidagi birinchi CS operatsiyasi detallari: [(id, l, w)] (operatsiyadagi tartibda)."""
    import xml.etree.ElementTree as ET
    r = ET.parse(project_file(order)).getroot()
    parts = {}
    for g in r.iter("good"):
        if g.get("typeId") == "product":
            for pe in g.findall("part"):
                parts[pe.get("id")] = (float(pe.get("l") or 0), float(pe.get("w") or 0))
    for o in r.findall("operation"):
        if o.get("typeId") == "CS":
            return [(int(pe.get("id")),) + parts[pe.get("id")] for pe in o.findall("part") if pe.get("id") in parts]
    return []


# ───────────────────────── (a) aniq solishtirish ─────────────────────────
def report(title, ok, tot, notes, verbose):
    if verbose:
        print(f"{title}: {ok}/{tot}")
        for n in notes:
            print("   ", n)
    return ok, tot, notes


def exact_fdt(kind, verbose=True):
    fmt = ppfmt.load_all()[KEYS[kind]]
    ok = tot = 0
    notes = []
    for order, f in samples(kind, "fdt").items():
        tot += 1
        job = sample_job(order, KEYS[kind])
        if job is None:
            notes.append(f"{order}: loyiha yoki daraxt manbai topilmadi")
            continue
        name, out = fmt.fn(job)[0]
        data = open(f, "rb").read()
        same = out == data and name == os.path.basename(f)
        ok += same
        if not same:
            notes.append(f"{order}: " + (f"nom {name}" if name != os.path.basename(f) else first_diff(out, data, "cp1251")))
    return report(f"{fmt.name} aniq (bayt-bayt)", ok, tot, notes, verbose)


def exact_gdrive(verbose=True):
    fmt = ppfmt.load_all()["giben_gdrive"]
    okd = okc = tot = 0
    notes = []
    for order, f in samples("gdrive", "zip").items():
        tot += 1
        job = sample_job(order, "giben_gdrive")
        if job is None:
            notes.append(f"{order}: loyiha yoki daraxt manbai topilmadi")
            continue
        ours = dict(unzip(fmt.fn(job)[0][1]))
        theirs = dict(unzip(open(f, "rb").read()))
        if sorted(ours) != sorted(theirs):
            notes.append(f"{order}: ichki nomlar {sorted(ours)} ≠ {sorted(theirs)}")
            continue
        for ext in ("DAX", "CPX"):
            n = next(k for k in ours if k.endswith(ext))
            same = ours[n] == theirs[n]
            if ext == "DAX":
                okd += same
            else:
                okc += same
            if not same:
                i = next((i for i, (x, y) in enumerate(zip(ours[n], theirs[n])) if x != y), -1)
                notes.append(f"{order} {ext}: uzunlik {len(ours[n])} vs {len(theirs[n])}, birinchi farq @{i}")
    if verbose:
        print(f"{fmt.name} aniq (bayt-bayt): DAX {okd}/{tot}, CPX {okc}/{tot}")
        for n in notes:
            print("   ", n)
    return okd + okc, 2 * tot, notes


_XML_NORM = (re.compile(r'id="\d+"'), re.compile(r'code="O\d+"'))


def xml_norm(s: str) -> str:
    return _XML_NORM[1].sub('code="O"', _XML_NORM[0].sub('id=""', s))


def exact_xml(verbose=True):
    fmt = ppfmt.load_all()["kdt_presize_xml"]
    ok = tot = full = 0
    notes = []
    img = 0
    for order, f in samples("xml", "zip").items():
        tot += 1
        job = sample_job(order, "kdt_presize_xml")
        if job is None:
            notes.append(f"{order}: loyiha topilmadi")
            continue
        zname, zdata = fmt.fn(job)[0]
        ours = unzip(zdata)
        theirs = unzip(open(f, "rb").read())
        a, b = ours[0][1].decode("utf-8"), theirs[0][1].decode("utf-8")
        same = xml_norm(a) == xml_norm(b) and ours[0][0] == theirs[0][0] and zname == os.path.basename(f)
        ok += same
        full += a == b
        img += len(ours) - 1
        want = [f"{p.uid}.emf" for p in job.parts]
        if [n for n, _ in theirs[1:] if not n.startswith("O")] != want:      # O<n>.emf — qoldiq etiketkasi
            notes.append(f"{order}: namunadagi rasm nomlari tartibi kutilgandan farq qiladi")
        if not same:
            notes.append(f"{order}: " + first_diff(xml_norm(a).encode(), xml_norm(b).encode()))
    notes.append(f"`id`/`O<n>` bilan birga to'liq bir xil: {full}/{tot}; biz yozgan etiketka rasmlari: {img} "
                 f"({'Pillow bor' if img else 'Pillow yo`q — rasmlar tashlab ketildi'})")
    return report(f"{fmt.name} aniq (id / O<n> hisoblagichlaridan tashqari)", ok, tot, notes, verbose)


def _strip_rest_idx(nodes, idx=0):
    return [dict(n, idx=idx) if (not n["strip"] and n["fl"]) else n for n in nodes]


def exact_ks(kind, verbose=True):
    import app.services.ppfmt.saw_kdt_ks33x as K
    new = kind == "new"
    fmt = ppfmt.load_all()[KEYS[kind]]
    okq = okt = okl = okn = tot = 0
    notes = []
    for order, f in samples(kind, "zip").items():
        job = sample_job(order, KEYS[kind])
        theirs = unzip(open(f, "rb").read())
        if job is None:
            tot += len(theirs) // 2
            notes.append(f"{order}: loyiha topilmadi")
            continue
        title = job_title(job)
        if title + ".zip" != os.path.basename(f):
            notes.append(f"{order}: zip nomi {title}.zip")
        pats = patterns(job)
        tq = [(n, d) for n, d in theirs if n.endswith(".qk")]
        tl = dict((n, d) for n, d in theirs if n.endswith(".lbd"))
        for k, P in enumerate(pats, 1):
            tot += 1
            if k > len(tq):
                notes.append(f"{order}: karta {k} namunada yo'q")
                continue
            qn, qd = tq[k - 1]
            ln = qn[:-3] + ".lbd"
            rn, rl, rrest = lbd_parse(tl[ln])
            ridx = next((n["idx"] for n in rn if not n["strip"] and n["fl"]), None)
            job.params["rest_id"] = ridx
            nodes = K.ks_tree(job, P)
            base = f"NUM={k}   PANELS( {P.copies} x 1 = {P.copies} )"
            okn += base + ".qk" == qn
            q = K.qk(job, P, nodes, new) == qd
            okq += q
            t = nodes == rn
            okt += t
            ours_l = K.labels(job, P, nodes, title, new)
            cut = lambda s: s.split(",")[:30]          # noqa: E731 — oxirgi maydon (blob) solishtirilmaydi
            ll = ([k2 for k2, _ in ours_l] == [k2 for k2, _ in rl]
                  and all(cut(a) == cut(b) and len(a.split(",")) == len(b.split(",")) == 31
                          for (_, a), (_, b) in zip(ours_l, rl)) and rrest == (b"\x00" if new else b""))
            okl += ll
            if not q:
                notes.append(f"{order} karta {k}: .qk farq qiladi")
            if not t:
                notes.append(f"{order} karta {k}: .lbd daraxti farq qiladi")
            if not ll:
                bad = [(a, b) for (_, a), (_, b) in zip(ours_l, rl) if cut(a) != cut(b)]
                notes.append(f"{order} karta {k}: etiketka qatorlari farq qiladi: kalitlar "
                             f"{[k2 for k2, _ in ours_l] == [k2 for k2, _ in rl]}"
                             + (f"; biz {cut(bad[0][0])[:15]} | namuna {cut(bad[0][1])[:15]}" if bad else ""))
        job.params.pop("rest_id", None)
    if verbose:
        print(f"{fmt.name} aniq: .qk bayt-bayt {okq}/{tot}, .lbd daraxti {okt}/{tot}, etiketka qatorlari (blobsiz) "
              f"{okl}/{tot}, fayl nomlari {okn}/{tot}")
        for n in notes:
            print("   ", n)
    return okq + okt + okl + okn, 4 * tot, notes


# ───────────────────────── (b) oxiridan-oxirigacha ─────────────────────────
def sig(nodes, with_uid=True, maxlvl=None, lvl=1):
    out = []
    for n in nodes:
        if n.kids and maxlvl is not None and lvl >= maxlvl:
            out.append((round(n.size, 3), n.rep, 999, ()))
        else:
            out.append((round(n.size, 3), n.rep, (n.uid if with_uid and not n.kids else 0),
                        tuple(sig(n.kids, with_uid, maxlvl, lvl + 1))))
    return out


def geometry_errors(job, pats) -> list[str]:
    """Format qoidasi bo'yicha geometriya: list ichida, detal o'lchami mos, optimizator joylashuvi bilan bir xil."""
    errs = []
    kerf = job.kerf
    for P in pats:
        m = P.map
        lv = layout(P, kerf)
        want = sorted((lf.uid, round(lf.x, 2), round(lf.y, 2), round(lf.x + lf.l, 2), round(lf.y + lf.w, 2))
                      for lf in leaves(m.tree) if lf.kind == "P")
        got = []
        for uid, x0, y0, x1, y1 in lv:
            sx0, sy0, sx1, sy1 = (y0, x0, y1, x1) if P.axis == "x" else (x0, y0, x1, y1)
            got.append((uid, round(sx0, 2), round(sy0, 2), round(sx1, 2), round(sy1, 2)))
            p = job.part(uid)
            if p is None:
                errs.append(f"karta {m.index}: noma'lum detal {uid}")
                continue
            if sorted((round(x1 - x0, 1), round(y1 - y0, 1))) != sorted((round(p.length, 1), round(p.width, 1))):
                errs.append(f"karta {m.index}: detal {p.name} o'lchami {x1 - x0:g}x{y1 - y0:g} ≠ {p.length:g}x{p.width:g}")
            if p.grain and abs((sx1 - sx0) - p.length) > 0.05:
                errs.append(f"karta {m.index}: teksturali detal {p.name} aylantirilgan")
            if sx1 > m.sheet_length + 0.01 or sy1 > m.sheet_width + 0.01 or min(sx0, sy0) < -0.01:
                errs.append(f"karta {m.index}: detal listdan chiqdi")
        g = sorted(got)
        for i in range(len(g)):                       # kesishmaslik (propil bilan)
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                if a[1] < b[3] + kerf - 0.01 and b[1] < a[3] + kerf - 0.01 and a[2] < b[4] + kerf - 0.01 \
                        and b[2] < a[4] + kerf - 0.01:
                    errs.append(f"karta {m.index}: detallar orasida propil yo'q {a} {b}")
                    break
        if not P.dropped and g != want:
            errs.append(f"karta {m.index}: joylashuv optimizator daraxtidan farq qiladi")
        elif P.dropped and sorted(x[0] for x in g) != sorted(x[0] for x in want):
            errs.append(f"karta {m.index}: detallar to'plami farq qiladi")
    return errs


def count_errors(job, pats) -> list[str]:
    errs = []
    want = part_totals(job)
    got: dict[int, int] = {}
    for P in pats:
        for uid, n in leaf_counts(P.kids).items():
            got[uid] = got.get(uid, 0) + n * P.copies
    if got != want:
        errs.append(f"detallar soni farqi: {sorted(set(got.items()) ^ set(want.items()))[:6]}")
    res = getattr(job.op, "result", None)
    if res is not None and not res.unplaced:
        short = [p.name for p in job.parts if want.get(p.uid, 0) != p.qty]
        if short:
            errs.append(f"kartadagi soni buyurtmaga teng emas: {short[:5]}")
    if len(pats) != len(job.maps):
        errs.append("kartalar soni farqi")
    return errs


def head_errors(parsed, pats, what) -> list[str]:
    """Qayta o'qilgan kartalar sarlavhasi: nusxalar, o'lcham."""
    errs = []
    if len(parsed) != len(pats):
        return [f"{what}: kartalar soni {len(parsed)} ≠ {len(pats)}"]
    for i, (a, P) in enumerate(zip(parsed, pats), 1):
        if a.copies != P.copies or abs(a.dimx - P.dimx) > 1e-6 or abs(a.dimy - P.dimy) > 1e-6:
            errs.append(f"{what} karta {i}: sarlavha farqi")
    return errs


def reparse_g57(job, files, pats, gvision=False):
    errs = []
    name, data = files[0]
    d = fdt_parse(data)
    errs += head_errors(d["pats"], pats, "fdt")
    for i, (a, P) in enumerate(zip(d["pats"], pats), 1):
        if sig(a.kids, not gvision) != sig(P.kids, not gvision):
            errs.append(f"karta {i}: Tagli_Ed daraxti farq qiladi")
    if gvision:
        if d["parts"] or any(d["leaves"]):
            errs.append("GVisionXP da detallar bo'lmasligi kerak")
        return errs
    if d["parts"] != [(p.uid, p.length, p.width) for p in job.parts]:
        errs.append("ElementiFDT detallari farq qiladi")
    if abs(d["kerf"] - job.kerf) > 1e-9:
        errs.append("propil farqi")
    if sum(s[3] for s in d["sheets"]) != sum(P.copies for P in pats):
        errs.append("listlar soni (QTA) farqi")
    for i, (lv, a, P) in enumerate(zip(d["leaves"], d["pats"], pats), 1):
        a.off1, a.off2 = P.off1, P.off2            # siljish faylda alohida yozilmaydi (torsovka + propil)
        if a.trims != (P.map.trim_length, P.map.trim_width):
            errs.append(f"karta {i}: RIFILO farqi")
        exp = [(u, round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)) for u, x0, y0, x1, y1 in layout(a, d["kerf"])]
        if exp != [(u, round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)) for u, x0, y0, x1, y1 in lv]:
            errs.append(f"karta {i}: ElementiFDS koordinatalari Tagli_Ed dan kelib chiqmaydi")
    return errs


def reparse_gdrive(job, files, pats):
    errs = []
    inner = dict(unzip(files[0][1]))
    names = sorted(inner)
    if len(names) != 2 or not names[0].endswith(".CPX") or not names[1].endswith(".DAX") or len(names[0]) > 12:
        errs.append(f"ichki nomlar: {names}")
    thick, recs = dax_parse(inner[names[1]])
    if thick != round(job.thickness * 1000):
        errs.append("qalinlik farqi")
    sheets = [r for r in recs if r["kind"] == 4]
    prt = [r for r in recs if r["kind"] == 1]
    if sum(r["qty"] for r in sheets) != sum(P.copies for P in pats):
        errs.append("listlar soni farqi")
    if prt[-1]["idx"] != 999 or [r["idx"] for r in prt[:-1]] != list(range(1, len(job.parts) + 1)):
        errs.append("detal indekslari")
    from app.services.ppfmt._saw_giben import translit
    for r, p in zip(prt, job.parts):
        if (r["l"], r["w"], r["qty"]) != (p.length, p.width, p.qty) or r["name"] != translit(p.name)[:40].rstrip("\0"):
            errs.append(f"detal yozuvi: {r} ≠ {p.name}")
            break
    cards = cpx_parse(inner[names[0]])
    uid_of = {i: p.uid for i, p in enumerate(job.parts, 1)}
    parsed = []
    redo = 0
    for c in cards:
        cuts = [(lvl, q, n, part) for lvl, q, n, part in c["cuts"]]
        if any(lvl > 5 for lvl, *_ in cuts):
            errs.append("5 dan chuqur daraja")
        kids = tree_from_cuts(cuts)

        def fix(nodes):
            nonlocal redo
            for n in nodes:
                if n.kids:
                    if n.uid != 0:
                        errs.append("farzandli bo'lakda detal raqami")
                    fix(n.kids)
                elif n.uid == 999:
                    redo += n.rep
                else:
                    n.uid = uid_of.get(n.uid, -1)
        fix(kids)
        parsed.append(Pat(kids, c["copies"], c["dimx"], c["dimy"]))
    errs += head_errors(parsed, pats, "cpx")
    for i, (a, P) in enumerate(zip(parsed, pats), 1):
        if sig(a.kids) != sig(P.kids, maxlvl=3):
            errs.append(f"karta {i}: CPX daraxti farq qiladi")
    job._redo = redo
    return errs


def reparse_xml(job, files, pats):
    errs = []
    inner = unzip(files[0][1])
    if not inner[0][0].endswith(".xml"):
        errs.append("birinchi fayl xml emas")
    for n, d in inner[1:]:
        if not n.endswith(".emf") or d[:4] != b"\x89PNG":
            errs.append(f"rasm {n} PNG emas")
    x = xml_parse(inner[0][1].decode("utf-8"))
    parsed = xml_pats(x)
    errs += head_errors(parsed, pats, "xml")
    for i, (a, P) in enumerate(zip(parsed, pats), 1):
        if [(k.sig(), k.rep) for k in a.kids] != [(k.sig(), k.rep) for k in P.kids]:
            errs.append(f"karta {i}: XML daraxti farq qiladi")
        if (a.rest is None) != (P.rest is None):
            errs.append(f"karta {i}: qoldiq belgisi farq qiladi")
        pa = x["panels"][i - 1]["a"]
        if float(pa["saw"]) != job.kerf or float(pa["thickness"]) != job.thickness or pa["material"] != job.material_name:
            errs.append(f"karta {i}: panel atributlari")
    want = part_totals(job)
    pl = [r for r in x["parts"] if not r[0].startswith("O")]
    if [(int(c), l, w, sq) for c, l, w, sq, uc, rc in pl] != [(p.uid, p.length, p.width, p.qty) for p in job.parts]:
        errs.append("<parts> ro'yxati farq qiladi")
    for c, l, w, sq, uc, rc in pl:
        if uc != min(sq, want.get(int(c), 0)) or rc != sq - uc:
            errs.append(f"<parts> uc/rc: {c}")
            break
    return errs


def f32(v: float) -> float:
    """.qk float32 saqlaydi — solishtirish uchun shu aniqlikka keltiramiz (masalan 602.11 mm)."""
    return struct.unpack("<f", struct.pack("<f", v))[0]


def reparse_ks(job, files, pats, new=False):
    errs = []
    inner = unzip(files[0][1])
    if len(inner) != 2 * len(pats):
        return [f"fayllar soni {len(inner)} ≠ {2 * len(pats)}"]
    title = job_title(job)
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    for k, P in enumerate(pats, 1):
        (qn, qd), (ln, ld) = inner[2 * k - 2], inner[2 * k - 1]
        base = f"NUM={k}   PANELS( {P.copies} x 1 = {P.copies} )"
        if qn != base + ".qk" or ln != base + ".lbd":
            errs.append(f"karta {k}: fayl nomi {qn}")
        q = qk_parse(qd, new)
        if (q["kerf"], q["off"], q["l"], q["w"]) != (f32(job.kerf), f32(P.off1), f32(P.dimy), f32(P.dimx)):
            errs.append(f"karta {k}: .qk sarlavhasi")
        nodes, labels, rest = lbd_parse(ld)
        if rest != (b"\x00" if new else b""):
            errs.append(f"karta {k}: .lbd oxiri")

        def shape(ns):
            return [(f32(n["cut"]), n["rep"], shape(n["ch"]) if n["strip"] else []) for n in ns
                    if n["strip"] or not n["fl"]]
        if shape(nodes) != q["tree"]:
            errs.append(f"karta {k}: .qk va .lbd daraxtlari farq qiladi")

        def back(ns):                        # .lbd → GN (bo'lingan takrorlar qayta birlashtiriladi)
            out = []
            for n in ns:
                if n["strip"]:
                    assert n["typ"] == "Полоса"
                    out.append(GN(n["cut"], rep=n["rep"], kids=back(n["ch"])))
                elif not n["fl"]:
                    p = job.part(n["idx"])
                    assert n["typ"] == "Деталь" and p is not None and n["code"] == str(idx[p.uid]) \
                        and (n["l"], n["w"]) == (p.length, p.width)
                    out.append(GN(n["cut"], rep=n["rep"], uid=n["idx"]))
            return merge(out)
        top = [n for n in nodes if n["strip"] or not n["fl"]]
        kids = back(top[::-1])
        # 1-daraja teskari tartibda birlashtirilgani uchun: takrorlar soni bir xil bo'lishi kifoya
        if sig(kids) != sig(P.kids):
            errs.append(f"karta {k}: .lbd daraxti farq qiladi")
        rests = [n for n in nodes if not n["strip"] and n["fl"]]
        if (len(rests) == 1) != (P.rest is not None) or (rests and nodes[-1] is not rests[0]):
            errs.append(f"karta {k}: qoldiq tuguni")
        on_sheet = leaf_counts(P.kids)
        keys = [kk for kk, _ in labels]
        if sorted(keys) != sorted(list(on_sheet) + [r["idx"] for r in rests]) or len(set(keys)) != len(keys):
            errs.append(f"karta {k}: etiketka kalitlari")
        for kk, s in labels:
            f = s.split(",")
            if len(f) != 31 or f[30] != "":
                errs.append(f"karta {k}: etiketka maydonlari soni / blob bo'sh emas")
                break
            p = job.part(kk)
            if f[0] == "detail.fme":
                if p is None or (f[3], f[5], f[6], f[7], f[9]) != (str(idx[kk]), title, ppfmt.num(p.length),
                                                                 ppfmt.num(p.width), str(p.qty)) \
                        or f[8] != p.name.replace(",", " ") or f[2] != str(on_sheet[kk] if new else p.qty) \
                        or f[14] != ("true" if p.grain else "false"):
                    errs.append(f"karta {k}: etiketka qatori {f[:10]}")
                    break
            elif f[0] != "rest.fme":
                errs.append(f"karta {k}: noma'lum etiketka turi")
    return errs


REPARSE = dict(g57=reparse_g57, gvision=lambda j, f, p: reparse_g57(j, f, p, True), gdrive=reparse_gdrive,
               xml=reparse_xml, ks33x=reparse_ks, new=lambda j, f, p: reparse_ks(j, f, p, True))


def check_job(kind, job) -> tuple[list[str], dict]:
    fmt = ppfmt.load_all()[KEYS[kind]]
    pats = patterns(job)
    info = dict(sheets=sum(P.copies for P in pats), cards=len(pats), dropped=sum(P.dropped for P in pats), redo=0,
                unsupported="", deep=sum(depth(P.kids) > 4 for P in pats))
    try:
        files = fmt.fn(job)
    except ValueError as e:                  # format chegarasi (KS33X: daraja / farzandlar soni)
        info["unsupported"] = str(e)
        return [], info
    errs = []
    if not no_forbidden(files):
        errs.append("faylda taqiqlangan so'z")
    try:
        errs += REPARSE[kind](job, files, pats)
    except AssertionError as e:
        errs.append(f"qayta o'qish: {e}")
    errs += count_errors(job, pats) + geometry_errors(job, pats)
    info["redo"] = getattr(job, "_redo", 0)
    return errs, info


def e2e(kind, verbose=True):
    ok = tot = 0
    notes = []
    orders = sorted(samples("xml", "zip"))
    for order in orders:
        p = cut_project(order)
        if p is None:
            continue
        for op in [o for o in p.operations if o.type == OpType.CS and o.parts]:
            job = ppfmt.saw_job(p, op, KEYS[kind])
            errs, info = check_job(kind, job)
            tot += 1
            ok += not errs and not info["unsupported"]
            extra = (f", surilgan chiqindi {info['dropped']}" if info["dropped"] else "") + \
                    (f", 4 darajadan chuqur kartalar {info['deep']}" if info["deep"] else "") + \
                    (f", 999-bo'laklar {info['redo']}" if info["redo"] else "")
            notes.append(f"{order} / {op.name}: kartalar {info['cards']}, listlar {info['sheets']}, detallar "
                         f"{sum(x.qty for x in job.parts)}{extra}"
                         + (f" — FORMAT CHEGARASI: {info['unsupported']}" if info["unsupported"] else
                            f" — XATO: {errs[:4]}" if errs else " — OK"))
    return report(f"{KEYS[kind]} oxiridan-oxirigacha", ok, tot, notes, verbose)


@functools.lru_cache(None)
def cut_project(order: str):
    """Loyiha + BIZNING optimizator natijasi (hamma CS operatsiyalari) — formatlar orasida qayta ishlatiladi."""
    p = load(order)
    if p is not None:
        for op in p.operations:
            if op.type == OpType.CS and op.parts:
                run_opt(p, op)
    return p


def stress(kinds, n=40, seed=1, verbose=True):
    """Tasodifiy `n` ta loyihaning barcha CS operatsiyalari: optimizator (bir marta) → har format → qayta o'qish."""
    import random
    fs = sorted(glob.glob(os.path.join(PROJECTS, "**", "*_*.project"), recursive=True))
    random.seed(seed)
    fs = random.sample(fs, min(n, len(fs)))
    res = {k: [0, 0, 0, [], 0, 0, 0] for k in kinds}
    for f in fs:
        try:
            p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
        except Exception:      # noqa: BLE001
            continue
        for op in p.operations:
            if op.type != OpType.CS or not op.parts:
                continue
            run_opt(p, op)
            for k in kinds:
                job = ppfmt.saw_job(p, op, KEYS[k])
                try:
                    errs, info = check_job(k, job)
                except Exception as e:      # noqa: BLE001
                    errs, info = [f"istisno: {e!r}"], dict(unsupported="")
                r = res[k]
                r[1] += 1
                r[4] += info.get("dropped", 0)
                r[5] += info.get("redo", 0)
                r[6] += info.get("deep", 0)
                if info["unsupported"]:
                    r[2] += 1
                elif not errs:
                    r[0] += 1
                else:
                    r[3].append(f"{os.path.basename(f)} / {op.name}: {errs[:3]}")
    if verbose:
        for k, (ok, tot, uns, bad, drop, redo, deep) in res.items():
            print(f"{KEYS[k]} korpus stress ({len(fs)} loyiha): {ok}/{tot} kroy OK, format chegarasi {uns}; "
                  f"surilgan chiqindi {drop}, 999-bo'laklar {redo}, 4 darajadan chuqur kartalar {deep}")
            for x in bad[:10]:
                print("   ", x)
    return res


EXACT = dict(g57=lambda v=True: exact_fdt("g57", v), gvision=lambda v=True: exact_fdt("gvision", v),
             gdrive=exact_gdrive, xml=exact_xml, ks33x=lambda v=True: exact_ks("ks33x", v),
             new=lambda v=True: exact_ks("new", v))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    kinds = args or list(EXACT)
    many = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--stress=")), 0)
    if not os.path.isdir(SAMPLES):
        print("namunalar papkasi topilmadi:", SAMPLES)
        return
    if "--no-exact" not in sys.argv:
        for k in kinds:
            EXACT[k]()
    if "--no-e2e" not in sys.argv:
        for k in kinds:
            e2e(k)
    if many:
        stress(kinds, many)


if __name__ == "__main__":
    main()
