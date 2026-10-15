"""Arra postprotsessorlari (Nanxing .CUT / .ncp, AES Alpha .ss, FastPanel .ocm) — korxona namunalari bilan tekshiruv.

    cd tools/bench && python pp_saw_check_nanxing.py [exact|e2e|all] [cut,ncp,aes,fp]

(a) exact — har namuna fayl uchun: namunadagi kesish kartalari (daraxt) → SawJob.maps, detallar esa korxona loyihasidan
    BIZNING importer (`plugins/legacy_project.py`) bilan; generator natijasi namuna bilan bayt-ma-bayt solishtiriladi
    (yaratilgan vaqt namunadan olinadi; AES `BSL3` dagi dastur nomi — «MebeliX Kroy», solishtirishda shu qator chetlanadi).
(b) e2e — loyiha importi → BIZNING optimizator (calc.run_cutting) → generator → faylni qayta o'qish: har detal soni/o'lchami/
    kromkasi, listlar soni, daraxt (o'lchamlar + propil), «GibLab» so'zi yo'qligi.

Papkalar: PP_SAMPLES (namunalar «PILNIY APPARAT»), PP_PROJECTS (korxona loyihalari). Korxona fayllari repoga kirmaydi.
"""
from __future__ import annotations

import collections
import glob
import io
import os
import re
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))

from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import SawMap, SawNode, saw_job  # noqa: E402
from app.services.ppfmt import _saw_strips as S  # noqa: E402

SAMPLES = os.environ.get("PP_SAMPLES") or r"D:/cloude giblab jasur/post prtsessorlar/PILNIY APPARAT"
PROJECTS = os.environ.get("PP_PROJECTS") or r"D:/cloude giblab jasur/giblab project"
FORBIDDEN = b"GibLab"

ppfmt.load_all()
from app.services.ppfmt import saw_nanxing_cut as CUT  # noqa: E402
from app.services.ppfmt import saw_nanxing_ncp as NCP  # noqa: E402
from app.services.ppfmt import saw_aes as AES  # noqa: E402
from app.services.ppfmt import saw_fastpanel as FP  # noqa: E402


# ───────────────────────── loyihalar ─────────────────────────
_ALLPROJ = None
_PCACHE: dict = {}


def all_projects():
    global _ALLPROJ
    if _ALLPROJ is None:
        _ALLPROJ = glob.glob(os.path.join(PROJECTS, "**", "*.project"), recursive=True)
    return _ALLPROJ


def load(path):
    if path not in _PCACHE:
        try:
            _PCACHE[path] = import_project(open(path, "rb").read(), os.path.basename(path))[0]
        except Exception as e:          # noqa: BLE001
            print("  import xato", path, e)
            _PCACHE[path] = None
    return _PCACHE[path]


def fresh(path):
    """Optimizator loyihani o'zgartiradi — har safar yangi nusxa."""
    return import_project(open(path, "rb").read(), os.path.basename(path))[0]


def candidates(order: str):
    out = []
    for p in all_projects():
        if os.path.basename(p).startswith(order) or os.path.basename(os.path.dirname(p)).startswith(order):
            out.append(p)
    return out


def find_op(order: str, names: list, dims: list, material: str = ""):
    """Namunadagi detallar ro'yxatiga eng mos loyiha + CS operatsiyasi. names/dims — namuna tartibida (bo'lishi mumkin None).
    Ball: tartib bo'yicha nom+o'lcham mosligi; teng bo'lsa — GibLab'da saqlangan («_» li) nusxa."""
    best = None
    for path in candidates(order):
        pr = load(path)
        if pr is None:
            continue
        for op in pr.operations:
            if op.type != OpType.CS or not op.parts:
                continue
            j = saw_job(pr, op)
            sc = 0
            for i, sp in enumerate(j.parts):
                if i < len(names) and names[i] is not None and names[i] == sp.name:
                    sc += 1
                if i < len(dims) and dims[i] is not None and tuple(dims[i]) == (sp.length, sp.width):
                    sc += 1
            if not any(n is not None for n in names):          # nomsiz (FastPanel) — o'lchamlar multimnojestvosi
                want = collections.Counter(tuple(sorted(d)) for d in dims)
                have = collections.Counter()
                for sp in j.parts:
                    have[tuple(sorted((sp.length, sp.width)))] += sp.qty
                sc = sum((want & have).values()) * 2 - sum((have - want).values())
            exact = len(j.parts) == max(len(names), len(dims)) and sc == 2 * len(j.parts)
            key = (sc, exact, op.name == material, "_" in os.path.basename(path))
            if best is None or key > best[0]:
                best = (key, path, pr, op, exact)
    return best


def node(x, y, l, w, k, **kw):
    return SawNode(x=float(x), y=float(y), l=float(l), w=float(w), kind=k, **kw)


def mk_map(i, copies, L, W, sid, tree):
    return SawMap(index=i + 1, copies=copies, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id=sid, tree=tree,
                  placements=[], offcuts=[], commands=[])


def other(a):
    return "y" if a == "x" else "x"


def span(n, a):
    return (n.x, n.l) if a == "x" else (n.y, n.w)


def setspan(n, a, s, z):
    if a == "x":
        n.x, n.l = s, z
    else:
        n.y, n.w = s, z


# ───────────────────────── .CUT ─────────────────────────
def cut_parse(path):
    r = ET.parse(path).getroot()
    pj = r.find("Project")
    d = pj.find("Data")
    return r, pj, d


def cut_maps(d, uid_of):
    """.CUT → (stock, maps): SawNode daraxtlari optimizator ko'rinishida (ildiz = zona, 1-daraja perpendikulyar = zona)."""
    conds = d.findall("Condition/Shape")
    stock = [dict(id=f"s{i}", length=float(c.get("X")), width=float(c.get("Y")), qty=int(c.get("Count")), is_remnant=False)
             for i, c in enumerate(conds)]
    maps = []
    for i, lay in enumerate(d.findall("Solutions/Solution/Layouts/Layout")):
        c = conds[int(lay.get("SheetID"))]
        L, W, sx, sy = float(lay.get("X")), float(lay.get("Y")), float(c.get("Sx")), float(c.get("Sy"))
        ax = "x" if lay.get("Cut") == "true" else "y"
        root = node(sx, sy, L - 2 * sx, W - 2 * sy, "C", axis=ax)
        zone_end = {"x": L - sx, "y": W - sy}

        def conv(el, parent, a, lvl):
            """el — parent ichidagi bo'lak (parent bolalari a o'qi bo'ylab)."""
            px, py, X, Y = (float(el.get(k)) for k in ("Px", "Py", "X", "Y"))
            n = node(px, py, X, Y, "C")
            b = other(a)
            if el.get("Spare") == "True":
                s, z = span(n, a)
                end = min(s + z, zone_end[a])
                n = node(px, py, X, Y, "W", rem=int(el.get("UID")) + 1)
                setspan(n, a, s, end - s)
                setspan(n, b, *span(parent, b))
                return n
            if lvl == 1:
                setspan(n, b, *span(root, b))
            kids = el.findall("Part")
            if not kids:
                return node(px, py, X, Y, "P", uid=uid_of(int(el.get("UID"))), rotated=el.get("Angle") == "90")
            n.axis = b
            n.children = [conv(k, n, b, lvl + 1) for k in kids]
            return n

        root.children = [conv(el, root, ax, 1) for el in lay.findall("Part")]
        maps.append(mk_map(i, int(lay.get("Count")), L, W, f"s{int(lay.get('SheetID'))}", root))
    return stock, maps


def cut_objective(d):
    sh = d.findall("Objective/Shape")
    return [s.get("F1") for s in sh], [(float(s.get("X")), float(s.get("Y"))) for s in sh]


def setup_job(pr, op, name, mat, stock, maps):
    j = saw_job(pr, op)
    j.project_name = name
    j.order = ""
    j.material_name = mat
    j.stock = stock
    j.maps = maps
    return j


def fix_now(mod_now: str, fmt: str):
    t = datetime.strptime(mod_now, fmt)
    S.now = lambda: t


def cut_samples():
    return sorted(glob.glob(os.path.join(SAMPLES, "Nanxing (NXCutSaw)", "*", "*.CUT"))) + \
        sorted(glob.glob(os.path.join(SAMPLES, "Nanxing NXCutSAW", "*.CUT")))


def first_diff(a: bytes, b: bytes, ctx=60):
    n = min(len(a), len(b))
    i = next((i for i in range(n) if a[i] != b[i]), n)
    return f"@{i} len {len(a)}/{len(b)}\n      biz: {a[max(0, i - ctx):i + ctx]!r}\n   namuna: {b[max(0, i - ctx):i + ctx]!r}"


def synth_parts(shapes):
    """Namunadagi `Objective` dan SawPart ro'yxati (faqat serializatorni tekshirish uchun)."""
    from app.services.ppfmt import SawPart
    out = []
    for i, s in enumerate(shapes):
        ed = {}
        for f, side in (("F8", "top"), ("F9", "bottom"), ("F10", "left"), ("F11", "right")):
            v = s.get(f)
            if v:
                m = re.match(r"\((.*?)\) (.*)$", v)
                ed[side] = dict(symbol=m.group(1) if m else "", name=m.group(2) if m else v, thickness=1.0)
        out.append(SawPart(uid=10000 + i, name=s.get("F1") or "", code="", length=float(s.get("X")), width=float(s.get("Y")),
                           qty=int(s.get("Count")), grain=s.get("Turn") == "false", product=s.get("Order") or "",
                           edges=ed, xnc_face=s.get("F6") or "", xnc_back=s.get("F7") or "",
                           has_mill=s.get("F12") == "true", has_drill=s.get("F13") == "true", description=s.get("F2") or ""))
    return out


def attr_diff(ours: bytes, theirs: bytes) -> collections.Counter:
    """Objective/Shape atributlari bo'yicha farqlar (qaysi maydon necha detalda farq qiladi)."""
    a = ET.fromstring(ours).findall(".//Objective/Shape")
    b = ET.fromstring(theirs).findall(".//Objective/Shape")
    c = collections.Counter()
    if len(a) != len(b):
        c[f"detal qatorlari {len(a)}/{len(b)}"] += 1
    for x, y in zip(a, b):
        for k in set(x.attrib) | set(y.attrib):
            if x.get(k) != y.get(k):
                c[k] += 1
    return c


def exact_cut(verbose=False):
    ok = tot = ok_ser = ok_geo = 0
    bad = []
    fields = collections.Counter()
    for f in cut_samples():
        tot += 1
        raw = open(f, "rb").read()
        r, pj, d = cut_parse(f)
        names, dims = cut_objective(d)
        order = os.path.basename(f)[:4]
        best = find_op(order, names, dims, d.get("TypeName"))
        if not best:
            bad.append((f, "loyiha topilmadi"))
            continue
        _, path, pr, op, exact_proj = best
        fix_now(pj.get("Update"), "%d.%m.%Y %H:%M:%S")
        # 1) serializator: detallar ham namunadan (sof format tekshiruvi)
        sp = synth_parts(d.findall("Objective/Shape"))
        stock, maps = cut_maps(d, lambda i: sp[i].uid)
        j = setup_job(pr, op, pj.get("Name"), d.get("TypeName"), stock, maps)
        j.parts = sp
        j.material_code = d.get("Type") or ""
        ser = CUT.generate(j)[0][1]
        ok_ser += ser == raw
        # 2) detallar BIZNING importerdan
        j0 = saw_job(pr, op)
        uid_of = lambda i: j0.parts[i].uid if i < len(j0.parts) else -1   # noqa: E731
        stock, maps = cut_maps(d, uid_of)
        j = setup_job(pr, op, pj.get("Name"), d.get("TypeName"), stock, maps)
        j.material_code = d.get("Type") or ""
        name, data = CUT.generate(j)[0]
        if FORBIDDEN in data:
            bad.append((f, "GibLab so'zi"))
        if name != os.path.basename(f):
            bad.append((f, f"nom {name}"))
        geo = lambda b: b[b.index(b"<Spares"):b.index(b"<Objective")]   # noqa: E731
        ok_geo += geo(data) == geo(raw)
        if data == raw:
            ok += 1
        else:
            dif = attr_diff(data, raw)
            fields.update(dif)
            bad.append((f, ("" if exact_proj else "[loyiha versiyasi mos emas] ") + f"maydonlar: {dict(dif)} "
                        + ("" if ser == raw else "SERIALIZATOR FARQI ") + (first_diff(data, raw) if verbose else "")))
    print(f".CUT exact: serializator (detallar namunadan) {ok_ser}/{tot}; importer detallari bilan: to'liq {ok}/{tot}, "
          f"geometriya (Spares…Solutions) {ok_geo}/{tot}")
    for f, m in bad:
        print("  -", os.path.relpath(f, SAMPLES), m if verbose else m[:400])
    return dict(ser=ok_ser, full=ok, geo=ok_geo, tot=tot)


# ───────────────────────── .ncp ─────────────────────────
def ncp_parse(d: bytes):
    def ws(b):
        return b.decode("utf-16le", errors="replace").split("\0")[0]
    L, W, t = struct.unpack_from("<3d", d, 4)
    kerf = struct.unpack_from("<d", d, 0x1C)[0]
    count = struct.unpack_from("<i", d, 0x24)[0]
    util = struct.unpack_from("<f", d, 0x2C)[0]
    nn = struct.unpack_from("<i", d, 0x30)[0]
    nodes = []
    for k in range(nn):
        st = 0x1C + k * 0x208
        B = st + 0x58
        n = dict(name="" if k == 0 else ws(d[st + 0x18:st + 0x58]))
        n["parent"], n["nchild"] = struct.unpack_from("<2i", d, B)
        n["L"], n["W"], n["wL"], n["wW"], n["tx"], n["ty"], n["X"], n["Y"] = struct.unpack_from("<8d", d, B + 8)
        cnt = struct.unpack_from("<i", d, st + 0x200)[0]
        n["ents"] = [struct.unpack_from("<iid", d, B + 0x48 + 16 * i) for i in range(cnt)]
        nodes.append(n)
    off = 0x1C + nn * 0x208 + 0x68
    labels = []
    while off + 0x1000 <= len(d):
        labels.append(ws(d[off:off + 0x1000]))
        off += 0x1000
    return dict(L=L, W=W, t=t, kerf=kerf, count=count, util=util, nodes=nodes, labels=labels)


def ncp_tree(f, part_of):
    """ncp → SawNode (optimizator ko'rinishi). part_of(n) → SawPart (Д<n>)."""
    nodes = f["nodes"]
    kids = collections.defaultdict(list)
    for i, n in enumerate(nodes):
        if i:
            kids[n["parent"]].append(i)
    r = nodes[0]
    ax = "x" if r["ents"] and r["ents"][0][0] % 2 == 0 else "y"
    trim = {"x": 0.0, "y": 0.0}
    trim[ax] = r["ents"][0][2] if r["ents"] and r["ents"][0][0] >= 2 else 0.0
    for c in kids[0]:
        e = nodes[c]["ents"]
        if e and e[0][0] >= 2:
            trim[other(ax)] = e[0][2]
            break
    dy = f["kerf"] if ax == "y" else 0.0
    L, W = f["L"], f["W"]
    root = node(trim["x"], trim["y"], L - 2 * trim["x"], W - 2 * trim["y"], "C", axis=ax)

    def conv(i, parent, a, lvl):
        n = nodes[i]
        x, y, l, w = n["X"], n["Y"] - dy, n["L"], n["W"]
        b = other(a)
        if n["name"].startswith("$"):
            sn = node(x, y, l, w, "W", rem=int(n["name"][1:]))
            setspan(sn, b, *span(parent, b))
            return sn
        if n["name"].startswith("Д"):
            sp = part_of(int(n["name"][1:]))
            rot = (l, w) != (sp.length, sp.width) and (l, w) == (sp.width, sp.length)
            return node(x, y, l, w, "P", uid=sp.uid, rotated=rot)
        sn = node(x, y, l, w, "C", axis=b)
        if lvl == 1:
            setspan(sn, b, *span(root, b))
        sn.children = [conv(k, sn, b, lvl + 1) for k in reversed(kids[i])]
        return sn

    root.children = [conv(k, root, ax, 1) for k in reversed(kids[0])]
    return root


def zip_members(data: bytes):
    z = zipfile.ZipFile(io.BytesIO(data))
    return [(i.filename, z.read(i.filename), i) for i in z.infolist()]


def ncp_materials(zpath):
    """Tashqi zip → [(material zip nomi, [(ncp nomi, bytes)], ichki zip nomlari, a'zolar)] (tashqi birinchi)."""
    out = []

    def rec(name, data):
        mem = zip_members(data)
        ncps = [(n, b) for n, b, _ in mem if n.lower().endswith(".ncp")]
        inner = [(n, b) for n, b, _ in mem if n.lower().endswith(".zip")]
        out.append((name, ncps, [n for n, _ in inner], mem))
        for n, b in inner:
            rec(n, b)

    rec(os.path.basename(zpath), open(zpath, "rb").read())
    return out


def _edge(s):
    if not s:
        return None
    m = re.match(r"\((.*?)\) (.*)$", s)
    return dict(symbol=m.group(1), name=m.group(2), thickness=1.0) if m else dict(symbol="", name=s, thickness=1.0)


def synth_from_labels(files):
    """Etiketkalardan SawPart'lar (Д<n> → n-1 indeks) — sof serializator tekshiruvi uchun."""
    from app.services.ppfmt import SawPart
    info = {}
    for f in files:
        for lb in f["labels"]:
            v = lb.split(",")
            if len(v) >= 21 and v[0].startswith("Д"):
                info[int(v[5])] = v
    n = max(info) if info else 0
    parts, groove = [], {}
    for i in range(1, n + 1):
        v = info.get(i)
        if v is None:
            parts.append(SawPart(uid=20000 + i, name="", code="", length=1, width=1, qty=0, grain=False))
            continue
        edges = {k: _edge(x) for k, x in zip(("top", "bottom", "left", "right"), v[10:14]) if x}
        parts.append(SawPart(uid=20000 + i, name=v[3], code="", length=float(v[6]), width=float(v[7]), qty=int(v[8]),
                             grain=False, product=v[20], edges=edges, xnc_face=v[17], xnc_back=v[18],
                             has_mill=v[15] == "true", has_drill=v[16] == "true", description=v[4]))
        groove[20000 + i] = v[14] == "true"
    return parts, groove


def ncp_samples():
    return [("cutsawfg", f) for f in sorted(glob.glob(os.path.join(SAMPLES, "Nanxing (CutSawFG)", "*.zip")))] + \
        [("cutsaw", f) for f in sorted(glob.glob(os.path.join(SAMPLES, "Nanxing CutSaw", "*.zip")))]


def _ncp_cmp(b1: bytes, b2: bytes, acc: collections.Counter) -> None:
    a, b = ncp_parse(b1), ncp_parse(b2)
    if a["nodes"] != b["nodes"]:
        acc["tugunlar"] += 1
    for la, lb in zip(a["labels"], b["labels"]):
        for k, (x, y) in enumerate(zip(la.split(","), lb.split(","))):
            if x != y:
                acc[f"etiketka#{k}"] += 1
    if a["labels"] == b["labels"] and a["nodes"] == b["nodes"]:
        acc["sarlavha/util"] += 1


def exact_ncp(verbose=False):
    tot = ok_ser = ok_imp = 0
    mats = mats_ser = mats_imp = 0
    bad = []
    real_groove = S.part_groove
    for kind, zp in ncp_samples():
        order = os.path.basename(zp)[:4]
        for mname, ncps, inner_names, mem in ncp_materials(zp):
            files = [ncp_parse(b) for _, b in ncps]
            if not files:
                continue
            mats += 1
            lb0 = next((lb.split(",") for f in files for lb in f["labels"] if lb), None)
            proj, mat, mcode = lb0[1], lb0[2], lb0[19]
            t = datetime(*mem[0][2].date_time)
            S.now = lambda: t
            # 1) serializator — detallar etiketkalardan
            sp, groove = synth_from_labels(files)
            names = [p.name if p.qty else None for p in sp]
            dims = [(p.length, p.width) if p.qty else None for p in sp]
            best = find_op(order, names, dims, mat)
            if not best:
                bad.append((mname, "loyiha topilmadi"))
                continue
            _, path, pr, op, exact_proj = best
            S.part_groove = lambda job, uid: groove.get(uid, False)
            maps = [mk_map(i, f["count"], f["L"], f["W"], "s0", ncp_tree(f, lambda n: sp[n - 1])) for i, f in enumerate(files)]
            stock = [dict(id="s0", length=files[0]["L"], width=files[0]["W"], qty=10000, is_remnant=False)]
            j = setup_job(pr, op, proj, mat, stock, maps)
            j.parts = sp
            j.material_code = mcode
            j.kerf, j.thickness = files[0]["kerf"], files[0]["t"]
            ours = zip_members(NCP.op_zip(j))
            S.part_groove = real_groove
            ser_ok = 0
            ser_diff = collections.Counter()
            for (n1, b1, _), (n2, b2) in zip(ours, ncps):
                tot += 1
                same = n1 == n2 and b1 == b2
                ok_ser += same
                ser_ok += same
                if not same:
                    _ncp_cmp(b1, b2, ser_diff)
                    if verbose:
                        print("   SER", mname, n2, first_diff(b1, b2, 40))
            mats_ser += ser_ok == len(ncps) and len(ours) == len(ncps)
            # 2) detallar BIZNING importerdan
            j0 = saw_job(pr, op)
            maps = [mk_map(i, f["count"], f["L"], f["W"], "s0",
                           ncp_tree(f, lambda n: j0.parts[n - 1] if n - 1 < len(j0.parts) else sp[n - 1]))
                    for i, f in enumerate(files)]
            j = setup_job(pr, op, proj, mat, stock, maps)
            j.material_code = mcode
            ours = zip_members(NCP.op_zip(j))
            imp_ok = 0
            imp_diff = collections.Counter()
            for (n1, b1, _), (n2, b2) in zip(ours, ncps):
                same = n1 == n2 and b1 == b2
                ok_imp += same
                imp_ok += same
                if FORBIDDEN in b1:
                    bad.append((mname, "GibLab so'zi"))
                if not same:
                    _ncp_cmp(b1, b2, imp_diff)
            mats_imp += imp_ok == len(ncps)
            if imp_ok != len(ncps) or ser_ok != len(ncps):
                bad.append((f"{kind}:{mname}", ("" if exact_proj else "[loyiha versiyasi mos emas] ")
                            + f"serializator {ser_ok}/{len(ncps)} {dict(ser_diff)}, importer {imp_ok}/{len(ncps)} "
                            + f"{dict(imp_diff)}"))
    print(f".ncp exact: serializator (detallar etiketkadan) {ok_ser}/{tot} fayl ({mats_ser}/{mats} material); "
          f"importer detallari bilan {ok_imp}/{tot} fayl ({mats_imp}/{mats} material)")
    for f, m in bad:
        print("  -", f, m[:400])
    return dict(ser=ok_ser, full=ok_imp, tot=tot)


# ───────────────────────── AES .ss ─────────────────────────
def ss_parse(raw: bytes):
    rows = [r.split(",") for r in raw.decode("cp1251").split("\r\n") if r]
    ozl, urn, prt, pnl = [], [], [], []
    for r in rows:
        k = r[0]
        if k == "OZL1":
            ozl.append(dict(used=int(r[2]), w=float(r[4]), l=float(r[5]), trims=[float(x) for x in r[6:10]]))
        elif k == "URN1":
            urn.append(dict(qty=int(r[1]), l=float(r[3]), w=float(r[4])))
        elif k == "PRT1":
            prt.append(dict(name=r[8], pcode=r[10], pname=r[11]))
        elif k == "PRT3":
            prt[-1]["edges"] = [r[3], r[6], r[9], r[12]]           # chap, yuqori, o'ng, past
        elif k == "PRT4":
            prt[-1]["th"] = [float(x) for x in r[1:5]]
        elif k == "PNL1":
            pnl.append(dict(sheet=int(r[1]), dir=r[2], copies=int(r[3]), kes=[]))
        elif k == "KES1":
            pnl[-1]["kes"].append((int(r[1]), float(r[2]), r[3] == "1", int(r[4])))
    head = {r[0]: r for r in rows if r[0] in ("BSL1", "BSL2", "KON2", "LMT1")}
    return dict(rows=rows, ozl=ozl, urn=urn, prt=prt, pnl=pnl, head=head)


def ss_tree(ss, pn, part_of, kerf):
    """PNL (KES1 qatorlari) → SawNode daraxti (optimizator ko'rinishi)."""
    oz = ss["ozl"][pn["sheet"] - 1]
    L, W = oz["l"], oz["w"]
    tx, ty = oz["trims"][0] + kerf, oz["trims"][2] + kerf
    ax = "x" if pn["dir"] == "S" else "y"
    root = node(tx, ty, L - 2 * tx, W - 2 * ty, "C", axis=ax)
    stack = [root]                      # stack[i] — i-daraja konteyner
    for lvl, size, is_part, urn in pn["kes"]:
        if size < 0:
            continue
        del stack[lvl:]
        par = stack[lvl - 1]
        a, b = par.axis, other(par.axis)
        sibs = par.children
        start = span(par, a)[0] if not sibs else span(sibs[-1], a)[0] + span(sibs[-1], a)[1] + kerf
        n = node(0, 0, 0, 0, "C")
        setspan(n, a, start, size)
        setspan(n, b, *span(par, b))
        if is_part:
            sp = part_of(urn)
            n.kind, n.uid = "P", sp.uid
            n.rotated = (n.l, n.w) != (sp.length, sp.width) and (n.l, n.w) == (sp.width, sp.length)
        else:
            n.axis = b
            stack.append(n)
        sibs.append(n)
    return root, L, W


def ss_synth(ss):
    from app.services.ppfmt import SawPart
    out = []
    for i, (u, p) in enumerate(zip(ss["urn"], ss["prt"])):
        ed = {}
        for side, nm, th in zip(("left", "top", "right", "bottom"), p["edges"], p["th"]):
            if nm:
                ed[side] = dict(symbol="A", name=nm, thickness=th)
        out.append(SawPart(uid=30000 + i, name=p["name"], code="", length=u["l"], width=u["w"], qty=u["qty"], grain=False,
                           product=p["pname"], product_code=p["pcode"], edges=ed))
    return out


def ss_samples():
    return sorted(glob.glob(os.path.join(SAMPLES, "AES Alpha", "*.ss"))) + \
        sorted(glob.glob(os.path.join(SAMPLES, "AESS Alpha (SS)", "*", "*.ss")))


def ss_norm(b: bytes) -> bytes:
    """BSL3 (dastur nomi maydoni) solishtirishdan chetlanadi."""
    return re.sub(rb"BSL3,[^\r]*\r\n", b"BSL3\r\n", b)


def exact_aes(verbose=False):
    tot = ok_ser = ok_imp = 0
    bad = []
    for f in ss_samples():
        tot += 1
        raw = open(f, "rb").read()
        ss = ss_parse(raw)
        h = ss["head"]
        kerf = float(h["KON2"][1])
        t = datetime.strptime(h["BSL2"][1] + " " + h["BSL2"][2], "%d.%m.%Y %H:%M")
        S.now = lambda: t
        proj = h["BSL1"][2]
        mat = next(r[1] for r in ss["rows"] if r[0] == "OZL2")
        names = [p["name"] for p in ss["prt"]]
        dims = [(u["l"], u["w"]) for u in ss["urn"]]
        best = find_op(os.path.basename(f)[:4], names, dims, mat)
        if not best:
            bad.append((f, "loyiha topilmadi"))
            continue
        _, path, pr, op, exact_proj = best
        stock = [dict(id=f"s{i}", length=o["l"], width=o["w"], qty=10000, is_remnant=False) for i, o in enumerate(ss["ozl"])]

        def build(part_of):
            maps = []
            for i, pn in enumerate(ss["pnl"]):
                root, L, W = ss_tree(ss, pn, part_of, kerf)
                maps.append(mk_map(i, pn["copies"], L, W, f"s{pn['sheet'] - 1}", root))
            return maps

        sp = ss_synth(ss)
        j = setup_job(pr, op, proj, mat, stock, build(lambda u: sp[u - 1]))
        j.parts = sp
        j.kerf = kerf
        j.thickness = float(h["LMT1"][1])
        j.pack_height = float(h["LMT1"][2])
        j.trim_length, j.trim_width = ss["ozl"][0]["trims"][0], ss["ozl"][0]["trims"][2]
        ser = AES.generate(j)[0][1]
        ser_ok = ss_norm(ser) == ss_norm(raw)
        ok_ser += ser_ok
        j0 = saw_job(pr, op)
        j = setup_job(pr, op, proj, mat, stock, build(lambda u: j0.parts[u - 1] if u - 1 < len(j0.parts) else sp[u - 1]))
        name, data = AES.generate(j)[0]
        if FORBIDDEN in data:
            bad.append((f, "GibLab so'zi"))
        if name != os.path.basename(f):
            bad.append((f, f"nom {name}"))
        imp_ok = ss_norm(data) == ss_norm(raw)
        ok_imp += imp_ok
        if not (ser_ok and imp_ok):
            rk = collections.Counter()
            a = ss_norm(data).split(b"\r\n")
            b = ss_norm(raw).split(b"\r\n")
            for x, y in zip(a, b):
                if x != y:
                    rk[x[:4].decode()] += 1
            if len(a) != len(b):
                rk[f"qatorlar {len(a)}/{len(b)}"] += 1
            bad.append((f, ("" if exact_proj else "[loyiha versiyasi mos emas] ")
                        + f"serializator {'OK' if ser_ok else 'FARQ ' + first_diff(ss_norm(ser), ss_norm(raw), 50)}; "
                        + f"importer farqli qatorlar: {dict(rk)}"))
    print(f"AES .ss exact (BSL3 dan tashqari): serializator {ok_ser}/{tot}; importer detallari bilan {ok_imp}/{tot}")
    for f, m in bad:
        print("  -", os.path.relpath(f, SAMPLES), m[:500])
    return dict(ser=ok_ser, full=ok_imp, tot=tot)


# ───────────────────────── FastPanel .ocm ─────────────────────────
def ocm_panels(raw: bytes):
    r = ET.fromstring(raw)
    out = []
    kids = list(r)
    for pi, pat in zip(kids[0::2], kids[1::2]):
        out.append((pi.attrib, pat))
    return r.get("JobName"), out


def ocm_tree(pi, pat, sheet, pick):
    """PanelInfo + Pattern → SawNode. sheet=(L, W) — list (X, Y); pick(entry, dims, prev) → uid."""
    L, W = sheet
    T = float(pi["TrimSize"])
    kerf = float(pi["BladeThickness"])
    ax = "x" if (float(pi["Length"]), float(pi["Width"])) == (L, W) else "y"
    root = node(T, T, L - 2 * T, W - 2 * T, "C", axis=ax)
    cache = {}                       # Entry → uid (takrorlangan konteyner nusxalarida bir xil detal)

    def fill(par, entries):
        a, b = par.axis, other(par.axis)
        prev = None
        for e in entries:
            d, q = float(e.get("Distance")), int(e.get("Quantity"))
            sub = list(e)
            uid = cache.get(id(e))
            for _ in range(q):
                sibs = par.children
                start = span(par, a)[0] if not sibs else span(sibs[-1], a)[0] + span(sibs[-1], a)[1] + kerf
                n = node(0, 0, 0, 0, "C")
                setspan(n, a, start, d)
                setspan(n, b, *span(par, b))
                if sub or par is root:
                    n.axis = b
                    fill(n, sub)
                else:
                    if uid is None:
                        uid = cache[id(e)] = pick(e, (n.l, n.w), prev, q)
                    n.kind, n.uid = "P", uid
                sibs.append(n)
            prev = (e, uid)

    fill(root, list(pat))
    return root


def exact_fp(verbose=False):
    tot = ok_ser = ok_imp = 0
    bad = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "FastPanel", "*", "*.ocm"))):
        tot += 1
        raw = open(f, "rb").read()
        stem, panels = ocm_panels(raw)
        order = os.path.basename(f)[:4]
        # loyiha/material: fayl nomi oxiri = material nomi (sanitizatsiya), o'lchamlar multimnojestvosi
        best = None
        for path in candidates(order):
            pr = load(path)
            if pr is None:
                continue
            for op in pr.operations:
                if op.type != OpType.CS or not op.parts:
                    continue
                ms = re.sub(r"[\s()]+", "_", op.name or "")
                if stem.endswith("_" + ms):
                    key = (op.result is None, "_" in os.path.basename(path), len(op.parts))
                    if best is None or key > best[0]:
                        best = (key, path, pr, op, ms)
        if not best:
            bad.append((f, "loyiha topilmadi"))
            continue
        _, path, pr, op, ms = best
        proj = stem[:-len(ms) - 1]
        j0 = saw_job(pr, op)
        sheets = [(s.length, s.width) for s in op.sheets]

        def sheet_of(pi):
            a, b = float(pi["Length"]), float(pi["Width"])
            for L, W in sheets:
                if (L, W) == (a, b) or (L, W) == (b, a):
                    return L, W
            return (a, b) if a >= b else (b, a)

        # 1) serializator: har Entry — alohida (soxta) detal
        from app.services.ppfmt import SawPart
        fake: list = []

        def pick_fake(e, dims, prev, q):
            fake.append(SawPart(uid=40000 + len(fake), name="", code="", length=dims[0], width=dims[1], qty=q, grain=False))
            return fake[-1].uid

        stock, maps = [], []
        for i, (pi, pat) in enumerate(panels):
            L, W = sheet_of(pi)
            sid = f"s{L:g}x{W:g}"
            if not any(s["id"] == sid for s in stock):
                stock.append(dict(id=sid, length=L, width=W, qty=10000, is_remnant=False))
            maps.append(mk_map(i, int(pi["Quantity"]), L, W, sid, ocm_tree(pi, pat, (L, W), pick_fake)))
        j = setup_job(pr, op, proj, op.name, stock, maps)
        j.parts = fake
        j.kerf, j.thickness = float(panels[0][0]["BladeThickness"]), float(panels[0][0]["Thickness"])
        ser = FP.generate(j)[0][1]
        ser_ok = ser == raw
        ok_ser += ser_ok
        # 2) BIZNING importer detallari (o'lcham bo'yicha detal tanlash; ketma-ket alohida yozuvlar — boshqa detal)
        left = {p.uid: p.qty for p in j0.parts}

        def pick(e, dims, prev, q, mult=1):
            cands = [p for p in j0.parts if tuple(sorted((p.length, p.width))) == tuple(sorted(dims))]
            if prev is not None and prev[0].get("Distance") == e.get("Distance") and not list(prev[0]):
                alt = [p for p in cands if p.uid != prev[1]]
                cands = alt or cands
            if not cands:
                return -1
            p = max(cands, key=lambda p: left.get(p.uid, 0))
            left[p.uid] = left.get(p.uid, 0) - q
            return p.uid

        maps = []
        for i, (pi, pat) in enumerate(panels):
            L, W = sheet_of(pi)
            maps.append(mk_map(i, int(pi["Quantity"]), L, W, f"s{L:g}x{W:g}", ocm_tree(pi, pat, (L, W), pick)))
        j = setup_job(pr, op, proj, op.name, stock, maps)
        name, data = FP.generate(j)[0]
        if FORBIDDEN in data:
            bad.append((f, "GibLab so'zi"))
        if name != os.path.basename(f):
            bad.append((f, f"nom {name}"))
        imp_ok = data == raw
        ok_imp += imp_ok
        if not (ser_ok and imp_ok):
            bad.append((f, f"serializator {'OK' if ser_ok else 'FARQ ' + first_diff(ser, raw, 50)}; importer "
                        + ("OK" if imp_ok else "FARQ " + first_diff(data, raw, 50))))
    print(f"FastPanel .ocm exact: serializator {ok_ser}/{tot}; importer detallari bilan {ok_imp}/{tot}")
    for f, m in bad:
        print("  -", os.path.relpath(f, SAMPLES), m[:500])
    return dict(ser=ok_ser, full=ok_imp, tot=tot)


# ───────────────────────── (b) end-to-end ─────────────────────────
def e2e_targets():
    """Namunalarga mos (loyiha, CS operatsiya) juftlari — takrorsiz."""
    seen = {}
    for f in cut_samples():
        r, pj, d = cut_parse(f)
        names, dims = cut_objective(d)
        b = find_op(os.path.basename(f)[:4], names, dims, d.get("TypeName"))
        if b:
            seen.setdefault((b[1], b[2].operations.index(b[3])), b[3].name)
    for f in ss_samples():
        ss = ss_parse(open(f, "rb").read())
        mat = next(r[1] for r in ss["rows"] if r[0] == "OZL2")
        b = find_op(os.path.basename(f)[:4], [p["name"] for p in ss["prt"]], [(u["l"], u["w"]) for u in ss["urn"]], mat)
        if b:
            seen.setdefault((b[1], b[2].operations.index(b[3])), b[3].name)
    return sorted(seen)


def tree_check(root, kerf, L, W, eps=0.01):
    """Qayta o'qilgan daraxt: bolalar ota ichida, o'q bo'ylab ketma-ket, orasida ≥ propil; chuqurlik."""
    errs = []
    depth = [0]

    def rec(n, lvl):
        depth[0] = max(depth[0], lvl)
        if n.x < -eps or n.y < -eps or n.x + n.l > L + eps or n.y + n.w > W + eps:
            errs.append(f"list chegarasidan tashqari {n.x},{n.y},{n.l},{n.w}")
        if n.kind != "C":
            return
        a, b = n.axis, other(n.axis)
        kids = sorted(n.children, key=lambda c: span(c, a)[0])
        prev_end = None
        for c in kids:
            s, z = span(c, a)
            ps, pz = span(n, a)
            if s < ps - eps or s + z > ps + pz + eps:
                errs.append(f"bola ota tashqarisida ({a}) {s}+{z} / {ps}+{pz}")
            qs, qz = span(c, b)
            rs, rz = span(n, b)
            if qs < rs - eps or qs + qz > rs + rz + eps:
                errs.append(f"bola ota tashqarisida ({b})")
            if prev_end is not None and s < prev_end + kerf - eps:
                errs.append(f"propil yetmaydi {prev_end}→{s}")
            prev_end = s + z
            rec(c, lvl + 1)

    rec(root, 0)
    return errs, depth[0]


def leaves_of(root):
    out = []

    def rec(n):
        if n.kind == "P":
            out.append(n)
        for c in n.children:
            rec(c)
    rec(root)
    return out


def e2e_one(path, opid, quality, stat, problems, verbose):
    """Bitta (loyiha, CS): import → optimizator → 4 format → qayta o'qish va tekshiruv."""
    from app.services.calc import run_cutting
    pr = fresh(path)
    op = pr.operations[opid]
    run_cutting(pr, op, quality=quality)
    res = op.result
    job = saw_job(pr, op)
    tag = f"{os.path.basename(path)}:{op.name}"
    exp_maps = []                      # optimizator joylashuvi: [(nusxa, Counter((uid,x,y,l,w)))]
    for m in res.maps:
        exp_maps.append((m.copies, collections.Counter(
            (p.part_uid, round(p.x, 2), round(p.y, 2), round(p.length, 2), round(p.width, 2)) for p in m.placements)))
    by_uid = {p.uid: p for p in job.parts}
    placed = collections.Counter()
    for c, cnt in exp_maps:
        for k, v in cnt.items():
            placed[k[0]] += v * c
    unplaced = sum(max(0, p.qty - placed[p.uid]) for p in job.parts)
    if unplaced:
        stat["joylashmagan detal (optimizator)"] += unplaced
    maxrot = job.max_rotations
    part_of = lambda n: job.parts[n - 1]   # noqa: E731

    def check_maps(fmt, got, with_uid=True):
        """got: [(nusxa, L, W, SawNode)] — qayta o'qilgan kartalar."""
        stat[f"{fmt} kroy"] += 1
        errs = []
        if len(got) != len(exp_maps):
            errs.append(f"kartalar soni {len(got)}/{len(exp_maps)}")
        if sum(g[0] for g in got) != res.total_sheets:
            errs.append(f"listlar {sum(g[0] for g in got)}/{res.total_sheets}")
        tot = collections.Counter()
        for (c, L, W, root), (ec, ecnt) in zip(got, exp_maps):
            te, dep = tree_check(root, job.kerf, L, W)
            errs += te[:3]
            if dep - 1 > maxrot:
                stat[f"{fmt}: chuqurlik > burilishlar ({dep - 1} > {maxrot})"] += 1
            lv = collections.Counter()
            for n in leaves_of(root):
                k = (n.uid if with_uid else 0, round(n.x, 2), round(n.y, 2), round(n.l, 2), round(n.w, 2))
                lv[k] += 1
                tot[n.uid] += c
                sp = by_uid.get(n.uid)
                if with_uid and sp is not None:
                    if sorted((n.l, n.w)) != sorted((sp.length, sp.width)):
                        errs.append(f"o'lcham {sp.name} {n.l}x{n.w}")
                    elif (n.l, n.w) != (sp.length, sp.width) and not S.can_turn(job, sp):
                        errs.append(f"teksturali detal burilgan {sp.name}")
            want = ecnt if with_uid else collections.Counter((0,) + k[1:] for k in ecnt.elements())
            if lv != want:
                errs.append(f"joylashuv farqi: {sum((lv - want).values())} ortiqcha, {sum((want - lv).values())} yetishmaydi")
            if c != ec:
                errs.append(f"nusxa {c}/{ec}")
        if with_uid:
            for p in job.parts:
                if tot[p.uid] != placed[p.uid]:
                    errs.append(f"soni {p.name}: {tot[p.uid]}/{placed[p.uid]}")
        if errs:
            stat[f"{fmt} XATO"] += 1
            problems[fmt].append((tag, errs[:5]))
        return errs

    # .CUT
    name, data = CUT.generate(job)[0]
    if FORBIDDEN in data:
        problems["GibLab"].append((tag, "cut"))
    d = ET.fromstring(data).find("Project/Data")
    stock, maps = cut_maps(d, lambda i: job.parts[i].uid)
    check_maps("cut", [(m.copies, m.sheet_length, m.sheet_width, m.tree) for m in maps])
    fe = []
    for p, s in zip(job.parts, d.findall("Objective/Shape")):
        if (s.get("F1"), int(s.get("Count")), float(s.get("X")), float(s.get("Y"))) != (p.name, p.qty, p.length, p.width):
            fe.append(f"Objective {p.name}")
        for fk, side in (("F8", "top"), ("F9", "bottom"), ("F10", "left"), ("F11", "right")):
            if (s.get(fk) or "") != S.edge_text(p.edges.get(side)):
                fe.append(f"kromka {p.name} {side}")
    if fe:
        problems["cut maydonlar"].append((tag, fe[:5]))
    # .ncp (CutSaw va CutSawFG)
    for key, gen in (("cutsaw", NCP.generate_cutsaw), ("cutsawfg", NCP.generate_cutsawfg)):
        name, data = gen(job)[0]
        mats = ncp_materials_bytes(name, data)
        if any(FORBIDDEN in b for _, ncps, _, _ in mats for _, b in ncps):
            problems["GibLab"].append((tag, key))
        files = [ncp_parse(b) for _, b in mats[0][1]]
        got = [(f["count"], f["L"], f["W"], ncp_tree(f, part_of)) for f in files]
        check_maps(key, got)
        le = []
        for f in files:
            for lb in f["labels"]:
                v = lb.split(",")
                if v[0].startswith("Д"):
                    p = job.parts[int(v[5]) - 1]
                    if (v[3], float(v[6]), float(v[7]), int(v[8])) != (p.name.replace(",", ";"), p.length, p.width, p.qty):
                        le.append(f"etiketka {p.name}")
                    if v[10:14] != [S.edge_text(p.edges.get(s)).replace(",", ";") for s in ("top", "bottom", "left", "right")]:
                        le.append(f"etiketka kromka {p.name}")
            if abs(f["util"]) > 1.0001:
                le.append(f"util {f['util']}")
        if le:
            problems[key + " etiketka"].append((tag, le[:5]))
    # AES .ss
    name, data = AES.generate(job)[0]
    if FORBIDDEN in data:
        problems["GibLab"].append((tag, "aes"))
    ss = ss_parse(data)
    got = []
    for pn in ss["pnl"]:
        root, L, W = ss_tree(ss, pn, part_of, job.kerf)
        got.append((pn["copies"], L, W, root))
    check_maps("aes", got)
    ae = []
    for p, u, pt in zip(job.parts, ss["urn"], ss["prt"]):
        if (u["qty"], u["l"], u["w"], pt["name"]) != (p.qty, p.length, p.width, p.name.replace(",", ";")):
            ae.append(f"URN/PRT {p.name}")
        if pt["edges"] != [(p.edges.get(s) or {}).get("name", "").strip() for s in ("left", "top", "right", "bottom")]:
            ae.append(f"PRT3 {p.name}")
    if [o["used"] for o in ss["ozl"]] != [sum(m.copies for m in res.maps if m.sheet_id == s["id"]) for s in job.stock]:
        ae.append("OZL1 ishlatilgan listlar")
    if ae:
        problems["aes maydonlar"].append((tag, ae[:5]))
    # FastPanel .ocm
    name, data = FP.generate(job)[0]
    if FORBIDDEN in data:
        problems["GibLab"].append((tag, "fp"))
    _, panels = ocm_panels(data)
    got = []
    for (pi, pat), m in zip(panels, [m for m in job.maps if m.tree is not None]):
        got.append((int(pi["Quantity"]), m.sheet_length, m.sheet_width,
                    ocm_tree(pi, pat, (m.sheet_length, m.sheet_width), lambda e, dims, prev, q: 0)))
    check_maps("fp", got, with_uid=False)
    stat["listlar"] += res.total_sheets
    if verbose:
        print("  ", tag, "listlar", res.total_sheets)


def e2e_targets_extra(n):
    """Qo'shimcha: korpusdagi boshqa loyihalarning CS operatsiyalari (birinchi n ta)."""
    out = []
    for path in sorted(all_projects()):
        if len(out) >= n:
            break
        pr = load(path)
        if pr is None:
            continue
        for i, o in enumerate(pr.operations):
            if o.type == OpType.CS and o.parts and o.sheets and len(out) < n:
                out.append((path, i))
    return out


def e2e(verbose=False, quality="fast"):
    targets = e2e_targets()
    extra = int(os.environ.get("PP_E2E_EXTRA", "0") or 0)
    if extra:
        have = set(targets)
        targets += [t for t in e2e_targets_extra(extra + len(targets)) if t not in have][:extra]
    print(f"E2E: {len(targets)} ta (loyiha, material); optimizator rejimi «{quality}»")
    stat = collections.Counter()
    problems = collections.defaultdict(list)
    for path, opid in targets:
        try:
            e2e_one(path, opid, quality, stat, problems, verbose)
        except Exception as e:          # noqa: BLE001
            stat["istisno"] += 1
            problems["istisno"].append((os.path.basename(path), [repr(e)[:200]]))
    print("E2E natija:", dict(stat))
    for k, v in problems.items():
        print(f"  [{k}] {len(v)} ta")
        for tag, e in v[:8]:
            print("     ", tag, e)
    return stat, problems


def ncp_materials_bytes(name, data):
    out = []

    def rec(nm, b):
        mem = zip_members(b)
        out.append((nm, [(n, x) for n, x, _ in mem if n.endswith(".ncp")], [n for n, _, _ in mem if n.endswith(".zip")], mem))
        for n, x, _ in mem:
            if n.endswith(".zip"):
                rec(n, x)
    rec(name, data)
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    which = (sys.argv[2] if len(sys.argv) > 2 else "cut,ncp,aes,fp").split(",")
    v = "-v" in sys.argv
    if mode in ("exact", "all"):
        if "cut" in which:
            exact_cut(v)
        if "ncp" in which:
            exact_ncp(v)
        if "aes" in which:
            exact_aes(v)
        if "fp" in which:
            exact_fp(v)
    if mode in ("e2e", "all"):
        e2e(v, os.environ.get("PP_QUALITY", "fast"))
