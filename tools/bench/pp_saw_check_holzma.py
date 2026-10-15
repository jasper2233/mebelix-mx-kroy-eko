"""Arra postprotsessorlari (Holzma PTX / LC4 / SPL, HOMAG, HOMAG CHF, Shelling, Shelling MCS) — korxona namunalari bilan
tekshiruv.    cd tools/bench && python pp_saw_check_holzma.py [ptx lc4 spl homag chf shelling mcs] [--no-e2e] [--stress=N]
(--stress=N — tasodifiy N ta korxona loyihasining barcha kroylari: optimizator → fayl → qayta o'qish.)

(a) ANIQ: namuna faylni o'qib (parser) kesish daraxtlarini SawNode ga aylantiramiz, detallarni korxona loyihasidan BIZNING
    importer bilan olamiz, generatorni ishga tushirib namuna bilan bayt-bayt solishtiramiz (ataylab tashlab ketilgan
    avvalgi dasturning o'z etiketka ma'lumotlaridan tashqari).
(b) OXIRIDAN-OXIRIGACHA: loyihani import qilib BIZNING optimizator bilan kroy qilamiz, fayl yaratamiz, uni qayta o'qib
    tekshiramiz: har detal nomi/o'lchami/soni, listlar soni, daraxt o'lchamlari (propil bilan), «GibLab» so'zi yo'q.

Namunalar va loyihalar korxona fayllari — repoga kirmaydi (yo'llar quyida; bo'lmasa skript o'tkazib yuboradi).
"""
from __future__ import annotations

import collections
import functools
import glob
import io
import os
import re
import struct
import sys
import zipfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))

from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import SawMap, SawNode  # noqa: E402
from app.services.ppfmt._saw_common import leaves, part_totals, tree_errors  # noqa: E402
from app.services.ppfmt import _saw_shelling as SH  # noqa: E402
from app.services.ppfmt import saw_holzma_lc4 as LC4, saw_holzma_spl as SPL  # noqa: E402
from app.services.ppfmt._saw_homag import parse_pattern  # noqa: E402

SAMPLES = os.environ.get("PP_SAMPLES", r"D:/cloude giblab jasur/post prtsessorlar/PILNIY APPARAT")
PROJECTS = os.environ.get("PP_PROJECTS", r"D:/cloude giblab jasur/giblab project")
FORBIDDEN = b"giblab"
PROJ = PROJECTS
ppfmt.load_all()


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


def _norm(s):
    return re.sub(r"[^0-9a-z]+", "", (s or "").lower())


def find_op(p, hint: str):
    """Namuna fayl nomidagi material qismi (yoki material nomi) bo'yicha CS operatsiya."""
    h = _norm(hint)
    best = None
    for o in p.operations:
        if o.type != OpType.CS:
            continue
        n = _norm(o.name or o.code)
        if n and (n == h or h.endswith(n) or n in h):
            if best is None or len(n) > len(_norm(best.name)):
                best = o
    return best


norm = _norm


def cs_ops(p):
    return [o for o in p.operations if o.type == OpType.CS]


def job_for(p, op, maps=None, key=None):
    """SawJob: detallar — importdan; kartalar — berilgan (namuna) yoki op.result (optimizator)."""
    j = ppfmt.saw_job(p, op, key)
    if maps is not None:
        j.maps = maps
    return j


def run_opt(p, op):
    from app.services.calc import run_cutting
    run_cutting(p, op)
    return op


def no_forbidden(files) -> bool:
    for _, data in files:
        if FORBIDDEN in data.lower():
            return False
        if data[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(data))
            if any(FORBIDDEN in z.read(n).lower() or FORBIDDEN in n.lower().encode() for n in z.namelist()):
                return False
    return True


def first_diff(a: bytes, b: bytes, enc="cp1251", sep="\r\n") -> str:
    la, lb = a.decode(enc, "replace").split(sep), b.decode(enc, "replace").split(sep)
    nd = sum(x != y for x, y in zip(la, lb)) + abs(len(la) - len(lb))
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"{nd} qator farq; {i + 1}-qator: biz «{x[:110]}» | namuna «{y[:110]}»"
    return f"qatorlar soni {len(la)} vs {len(lb)}"


def common_e2e(job, files, parsed_maps, parsed_parts) -> list[str]:
    """parsed_maps: [(copies, SawNode)], parsed_parts: {uid: (name, l, w, qty)} — qayta o'qilgan fayldan."""
    errs: list[str] = []
    if not no_forbidden(files):
        errs.append("faylda taqiqlangan so'z")
    want = part_totals(job)
    got: dict[int, int] = {}
    for cp, t in parsed_maps:
        for lf in leaves(t):
            if lf.kind == "P" and lf.uid:
                got[lf.uid] = got.get(lf.uid, 0) + cp
                p = job.part(lf.uid)
                if p and sorted((round(lf.l, 1), round(lf.w, 1))) != sorted((round(p.length, 1), round(p.width, 1))):
                    errs.append(f"detal {p.name}: o'lcham {lf.l}x{lf.w} ≠ {p.length}x{p.width}")
                if p and p.grain and abs(lf.l - p.length) > 0.05:
                    errs.append(f"detal {p.name}: teksturali detal aylantirilgan")
        errs += tree_errors(t, job.kerf)
    if got != want:
        errs.append(f"detallar soni farqi: {sorted(set(got.items()) ^ set(want.items()))[:6]}")
    res = getattr(job.op, "result", None)
    if res is not None and not res.unplaced:      # hamma detal joylashgan bo'lsa — kartadagi soni = buyurtma soni
        short = [p.name for p in job.parts if want.get(p.uid, 0) != p.qty]
        if short:
            errs.append(f"kartadagi soni buyurtmaga teng emas: {short[:5]}")
    for p in job.parts:
        pp = parsed_parts.get(p.uid)
        if pp is None:
            errs.append(f"detal yo'q: {p.name}")
        elif (pp[0], round(pp[1], 1), round(pp[2], 1), pp[3]) != (p.name.replace(",", " "), round(p.length, 1),
                                                                 round(p.width, 1), p.qty):
            errs.append(f"detal ma'lumoti: {pp} ≠ {(p.name, p.length, p.width, p.qty)}")
    if sum(cp for cp, _ in parsed_maps) != sum(max(1, m.copies) for m in job.maps):
        errs.append("listlar soni farqi")
    return errs


def leaf_set(maps):
    """(nusxa, uid, x, y, l, w) — joylashuvni solishtirish uchun."""
    out = []
    for cp, t in maps:
        out.append((cp, tuple(sorted((lf.uid, round(lf.x, 1), round(lf.y, 1), round(lf.l, 1), round(lf.w, 1))
                                     for lf in leaves(t) if lf.kind == "P"))))
    return out


# ───────────────────────── Holzma PTX ─────────────────────────
def ptx_read(data: bytes) -> list[list[str]]:
    return [ln.split(",") for ln in data.decode("cp1251").split("\r\n") if ln]


def ptx_parse(data: bytes, uids: list[int]):
    """PTX → (maps [(copies, SawNode, SawMap meta)], parts {uid: (name, l, w, qty)}, kerf, meta).
    uids — PARTS_REQ indeksi (1..N) → detal uid (bizning ish tartibi)."""
    recs = ptx_read(data)
    req = [r for r in recs if r[0] == "PARTS_REQ"]
    parts = {uids[int(r[2]) - 1]: (r[3], float(r[5]), float(r[6]), int(r[7])) for r in req if int(r[2]) <= len(uids)}
    dims = {int(r[2]): (float(r[5]), float(r[6])) for r in req}
    mat = next(r for r in recs if r[0] == "MATERIALS")
    kerf = float(mat[7])
    ty, tx = float(mat[9]), float(mat[11])
    boards = {int(r[2]): (float(r[5]), float(r[6])) for r in recs if r[0] == "BOARDS"}
    offs = [r for r in recs if r[0] == "OFFCUTS"]
    pats = [r for r in recs if r[0] == "PATTERNS"]
    cuts = [r for r in recs if r[0] == "CUTS"]
    out = []
    for pi, pr in enumerate(pats):
        L, W = boards[int(pr[3])]
        typ = int(pr[4])
        rows = [(int(c[5]), float(c[6]), int(c[7]), int(c[8])) for c in cuts if c[2] == pr[2]]
        # daraxt: (level, dim, rpt, part, kids)
        root = dict(level=-1 if typ == 2 else 0, kids=[])
        stack = [root]
        for f, d, r, part in rows:
            if f >= 90:
                if f == 90:
                    tx = d
                elif f == 91:
                    ty = d
                else:
                    tx = d
                continue
            n = dict(level=f, dim=d, rpt=r, part=part, kids=[])
            while stack[-1]["level"] >= f:
                stack.pop()
            stack[-1]["kids"].append(n)
            stack.append(n)
        ax = "x" if typ == 2 else "y"
        rn = SawNode(x=tx, y=ty, l=L - 2 * tx, w=W - 2 * ty, kind="C", axis=ax)

        def build(node, row_kids, ax, lvl):
            pos = node.x if ax == "x" else node.y
            end = (node.x + node.l) if ax == "x" else (node.y + node.w)
            for k in row_kids:
                for _ in range(k["rpt"]):
                    if ax == "x":
                        c = SawNode(x=pos, y=node.y, l=k["dim"], w=node.w, kind="W", level=lvl)
                    else:
                        c = SawNode(x=node.x, y=pos, l=node.l, w=k["dim"], kind="W", level=lvl)
                    if k["kids"]:
                        c.kind, c.axis = "C", ("y" if ax == "x" else "x")
                        build(c, k["kids"], c.axis, lvl + 1)
                    elif k["part"]:
                        c.kind = "P"
                        c.uid = uids[k["part"] - 1] if k["part"] <= len(uids) else 0
                        pl, pw = dims.get(k["part"], (0, 0))
                        c.rotated = abs(c.l - pl) > 0.05 or abs(c.w - pw) > 0.05
                    node.children.append(c)
                    pos += k["dim"] + kerf
            if end - pos > 0.05:
                if ax == "x":
                    node.children.append(SawNode(x=pos, y=node.y, l=end - pos, w=node.w, kind="W", level=lvl))
                else:
                    node.children.append(SawNode(x=node.x, y=pos, l=node.l, w=end - pos, kind="W", level=lvl))

        build(rn, root["kids"], ax, 1)
        # qoldiq (OFFCUTS) — oxirgi ildiz chiqindisi yalpi o'lchami mos kelsa
        if rn.children and rn.children[-1].kind == "W":
            w = rn.children[-1]
            gl, gw = (L - w.x, W) if ax == "x" else (L, W - w.y)
            for o in offs:
                if abs(float(o[5]) - gl) < 0.05 and abs(float(o[6]) - gw) < 0.05 and pi == len(pats) - 1:
                    w.rem = 1
        sm = SawMap(index=pi + 1, copies=int(pr[5]), sheet_length=L, sheet_width=W, is_remnant=False, sheet_id="",
                    tree=rn, placements=[], offcuts=[], commands=[], trim_length=tx, trim_width=ty)
        out.append(sm)
    return out, parts, kerf


def ptx_exact(verbose=True):
    fmt = ppfmt.load_all()["holzma_ptx"]
    ok = tot = 0
    notes = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Holzma", "*.ptx"))):
        b = os.path.basename(f)
        order = b[:4]
        p = load(order)
        tot += 1
        if p is None:
            notes.append(f"{b}: loyiha topilmadi")
            continue
        data = open(f, "rb").read()
        mat = next(r for r in ptx_read(data) if r[0] == "MATERIALS")[4]
        op = find_op(p, mat)
        job = ppfmt.saw_job(p, op, "holzma_ptx")
        maps, _, _ = ptx_parse(data, [x.uid for x in job.parts])
        job.maps = maps
        files = fmt.fn(job)
        name, out = files[0]
        same = out == data and name == b
        ok += same
        if not same:
            notes.append(f"{b}: {'nom ' + name if name != b else first_diff(out, data)}")
    if verbose:
        print(f"Holzma PTX aniq: {ok}/{tot}")
        for n in notes:
            print("   ", n)
    return ok, tot, notes


def ptx_e2e(verbose=True):
    fmt = ppfmt.load_all()["holzma_ptx"]
    ok = tot = 0
    notes = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "Holzma", "*.ptx"))):
        b = os.path.basename(f)
        p = load(b[:4])
        if p is None:
            continue
        mat = next(r for r in ptx_read(open(f, "rb").read()) if r[0] == "MATERIALS")[4]
        op = find_op(p, mat)
        run_opt(p, op)
        job = ppfmt.saw_job(p, op, "holzma_ptx")
        files = fmt.fn(job)
        maps, parts, kerf = ptx_parse(files[0][1], [x.uid for x in job.parts])
        pm = [(m.copies, m.tree) for m in maps]
        errs = common_e2e(job, files, pm, parts)
        if leaf_set(pm) != leaf_set([(m.copies, m.tree) for m in job.maps]):
            errs.append("detallar joylashuvi optimizator daraxtidan farq qiladi")
        tot += 1
        ok += not errs
        sheets = sum(m.copies for m in job.maps)
        notes.append(f"{b}: listlar {sheets}, detallar {sum(x.qty for x in job.parts)}"
                     + (f" — XATO: {errs[:4]}" if errs else " — OK"))
    if verbose:
        print(f"Holzma PTX oxiridan-oxirigacha: {ok}/{tot}")
        for n in notes:
            print("   ", n)
    return ok, tot, notes


def ptx_reparse(job, files):
    maps, parts, _ = ptx_parse(files[0][1], [x.uid for x in job.parts])
    return [(m.copies, m.tree) for m in maps], parts


# ───────────────────────── korpus bo'yicha stress (faqat bizning optimizator) ─────────────────────────
def stress(key: str, reparse, n: int = 40, seed: int = 1, verbose=True):
    """Tasodifiy `n` ta loyihaning barcha CS operatsiyalari: optimizator → generator → qayta o'qish → tekshiruv."""
    import random
    fmt = ppfmt.load_all()[key]
    fs = sorted(glob.glob(os.path.join(PROJECTS, "**", "*_*.project"), recursive=True))
    random.seed(seed)
    fs = random.sample(fs, min(n, len(fs)))
    ok = tot = 0
    bad = []
    for f in fs:
        try:
            p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
        except Exception:      # noqa: BLE001
            continue
        for op in p.operations:
            if op.type != OpType.CS or not op.parts:
                continue
            run_opt(p, op)
            job = ppfmt.saw_job(p, op, key)
            try:
                files = fmt.fn(job)
                pm, parts = reparse(job, files)
                errs = common_e2e(job, files, pm, parts)
                if leaf_set(pm) != leaf_set([(m.copies, m.tree) for m in job.maps]):
                    errs.append("detallar joylashuvi optimizator daraxtidan farq qiladi")
            except Exception as e:      # noqa: BLE001
                errs = [f"istisno: {e!r}"]
            tot += 1
            ok += not errs
            if errs:
                bad.append(f"{os.path.basename(f)} / {op.name}: {errs[:3]}")
    if verbose:
        print(f"{key} korpus stress ({n} loyiha): {ok}/{tot} kroy")
        for x in bad[:15]:
            print("   ", x)
    return ok, tot, bad


# ═════════════════════════ Holzma LC4 / SPL ═════════════════════════
# ───────────────────────── LC4 o'quvchi ─────────────────────────
class _LcR:
    def __init__(s, b):
        s.b, s.i = b, 0

    def tag(s, t=None):
        v = struct.unpack_from('<H', s.b, s.i)[0]
        s.i += 2
        if t is not None and v != t:
            raise ValueError(f'teg {v:#x} != {t:#x} @ {s.i - 2}')
        return v

    def boolean(s):
        s.tag(1)
        s.i += 1
        return bool(s.b[s.i - 1])

    def _n(s, t, fmt, n):
        s.tag(t)
        v = struct.unpack_from(fmt, s.b, s.i)[0]
        s.i += n
        return v

    def i16(s): return s._n(5, '<h', 2)
    def i32(s): return s._n(6, '<i', 4)
    def i64(s): return s._n(8, '<q', 8)

    def obj(s, ver=1):
        assert s.boolean()
        assert s.i16() == ver

    def string(s):
        s.tag(0x0d)
        assert s.boolean()
        s.tag(0x0e)
        n = s.i32()
        s.i += n
        return s.b[s.i - n:s.i].decode('utf-8')

    def dec(s):
        s.tag(0x0f)
        assert s.i16() == 1
        v = s.i64() / 100000
        assert not s.boolean()
        return v

    def enum(s, t):
        s.tag(t)
        return s.i32()

    def lst(s, fn):
        s.obj()
        return [fn() for _ in range(s.i32())]

    def none(s):
        raise ValueError("bo'sh ro'yxat kutilgan")

    def item(s):
        s.obj()
        assert s.i16() == 2
        r = dict(id=s.string(), fme=s.string(), fme2=s.string(), L=s.dec(), W=s.dec(), T=s.dec(), q1=s.i32(), q2=s.i32(),
                 grain=s.enum(0x13), b1=s.boolean())
        r['map'] = s.lst(lambda: (s.obj(), s.string(), s.string())[1:])
        r['b2'] = s.boolean()
        return r

    def info(s):
        s.obj()
        return dict(a=s.i32(), rot=s.boolean(), label=s.string(), c=s.boolean(), e14=s.enum(0x14), ref=s.i32())

    def node(s, root=False):
        s.obj()
        if root:
            assert s.i16() == 1
        r = dict(name=s.string(), n2=s.string(), size=s.dec(), rep=s.i32(), kind=s.enum(0x11), sub=s.enum(0x12))
        assert s.i16() == 1
        r['info'] = s.info() if s.i32() else None
        s.lst(s.none)
        r['kids'] = s.lst(s.node)
        if root:
            r.update(W=s.dec(), x1=s.i32(), x2=s.i32(), mat=s.string())
            assert s.i16() == 1
            r.update(e10=s.enum(0x10), fb=s.boolean(), params=s.lst(lambda: (s.obj(2), s.string(), s.string(), s.boolean())[1:]))
        return r

    def file(s):
        s.obj()
        r = dict(job=s.string(), order=s.string(), parts=s.lst(s.item), boards=s.lst(s.item))
        s.lst(s.none)
        r['patterns'] = s.lst(lambda: s.node(True))
        assert s.i == len(s.b), 'ortiqcha bayt'
        return r


def lc4_parse(data: bytes) -> dict:
    return _LcR(data).file()


def lc4_strip_blob(fme: str) -> str:
    """`detail.fme`/`rest.fme` satrining oxirgi (30-) maydoni — etiketka blobi — bo'shatiladi."""
    if fme.startswith(('detail.fme', 'rest.fme')):
        return fme[:fme.rfind(',') + 1]
    return fme


def lc4_write_parsed(r: dict) -> bytes:
    """Mustaqil qayta yozuvchi (o'qilgan dict → bayt), tahlil skripti uslubida: namunani blobsiz qayta yig'ish uchun."""
    b = bytearray()
    tag = lambda t: b.extend(struct.pack('<H', t))          # noqa: E731

    def bo(v): tag(1); b.append(1 if v else 0)
    def i16(v): tag(5); b.extend(struct.pack('<h', v))
    def i32(v): tag(6); b.extend(struct.pack('<i', v))
    def obj(v=1): bo(True); i16(v)

    def st(v):
        e = v.encode('utf-8'); tag(0x0d); bo(True); tag(0x0e); i32(len(e)); b.extend(e)

    def dec(v): tag(0x0f); i16(1); tag(8); b.extend(struct.pack('<q', int(round(v * 100000)))); bo(False)
    def en(t, v): tag(t); i32(v)

    def lst(xs, fn):
        obj(); i32(len(xs))
        for x in xs:
            fn(x)

    def item(it):
        obj(); i16(2); st(it['id']); st(it['fme']); st(it['fme2']); dec(it['L']); dec(it['W']); dec(it['T'])
        i32(it['q1']); i32(it['q2']); en(0x13, it['grain']); bo(it['b1'])
        lst(it['map'], lambda kv: (obj(), st(kv[0]), st(kv[1]))); bo(it['b2'])

    def node(n, root=False):
        obj()
        if root:
            i16(1)
        st(n['name']); st(n['n2']); dec(n['size']); i32(n['rep']); en(0x11, n['kind']); en(0x12, n['sub']); i16(1)
        i32(1 if n['info'] else 0)
        if n['info']:
            f = n['info']; obj(); i32(f['a']); bo(f['rot']); st(f['label']); bo(f['c']); en(0x14, f['e14']); i32(f['ref'])
        lst([], None); lst(n['kids'], node)
        if root:
            dec(n['W']); i32(n['x1']); i32(n['x2']); st(n['mat']); i16(1); en(0x10, n['e10']); bo(n['fb'])
            lst(n['params'], lambda p: (obj(2), st(p[0]), st(p[1]), bo(p[2])))
    obj(); st(r['job']); st(r['order']); lst(r['parts'], item); lst(r['boards'], item); lst([], None)
    lst(r['patterns'], lambda p: node(p, True))
    return bytes(b)


def lc4_maps(r: dict, job) -> list:
    """Namuna daraxtlari → SawMap (list koordinatalarida), detallar `ref` → bizning uid."""
    kerf = float(next(v for k, v, _ in r['patterns'][0]['params'] if k == 'SaegeblattStaerke')) if r['patterns'] else 0
    maps = []
    for k, (p, bd) in enumerate(zip(r['patterns'], r['boards'])):
        rot = p['info']['rot']
        L, W = p['size'], p['W']
        ax = 'y' if rot else 'x'
        oth = 'x' if rot else 'y'
        offcuts = []
        ext = {'x': L, 'y': W}

        def mk(start, size, a, ostart, osize):
            return dict(x=start, y=ostart, l=size, w=osize) if a == 'x' else dict(x=ostart, y=start, l=osize, w=size)

        def lead(kids):
            """Bolalar boshidagi trim + kerf (bo'lsa)."""
            return kids[0]['size'] + kerf if kids and kids[0]['kind'] == 4 else 0.0

        def build(kids, a, ostart, osize, end):
            """kids — `a` o'qi bo'ylab (birinchi bola joyi = ostart dan oldingi trim); ostart/osize — ikkinchi o'q."""
            out = []
            pos = None
            after_el = False
            for n in kids:
                if pos is None:
                    pos = 0.0
                if n['kind'] == 2 and after_el:          # element + kerf birga takrorlanadi (rep) — kerf hisoblangan
                    after_el = False
                    continue
                if n['kind'] in (2, 4):                  # kerf / trim — joy siljiydi
                    pos += n['size']
                    continue
                after_el = True
                for _ in range(max(1, n['rep'])):
                    g = mk(pos + base[0], n['size'], a, ostart, osize)
                    if n['kind'] == 11:
                        part = job.parts[n['info']['ref']]
                        out.append(SawNode(kind='P', uid=part.uid, rotated=n['info']['rot'] != rot, **g))
                    elif n['kind'] == 10:
                        it = r['parts'][n['info']['ref']]
                        num_ = len(offcuts) + 1
                        g = mk(pos + base[0], min(n['size'], end - pos - base[0]), a, ostart, osize)
                        offcuts.append(dict(number=num_, x=g['x'], y=g['y'], length=it['L'], width=it['W'],
                                            business=True, kind='remnant'))
                        out.append(SawNode(kind='W', rem=num_, **g))
                    else:
                        o = 'y' if a == 'x' else 'x'
                        c = SawNode(kind='C', axis=o, **g)
                        cs = (g['x'] if a == 'x' else g['y'])
                        lb = lead(n['kids'])
                        saved = base[0]
                        base[0] = (ostart - lb)
                        c.children = build(n['kids'], o, cs, n['size'], ostart + osize)
                        base[0] = saved
                        out.append(c)
                    pos += n['size'] + kerf
            return out
        t1 = p['kids'][0]['size'] if p['kids'] and p['kids'][0]['kind'] == 4 else 0
        t2 = next((n['size'] for c in p['kids'] if c['kind'] == 0 for n in c['kids'][:1] if n['kind'] == 4), 0)
        o0 = t2 + kerf
        osz = ext[oth] - 2 * o0
        base = [0.0]
        kids = build(p['kids'], ax, o0, osz, ext[ax] - t1 - kerf)
        root = SawNode(kind='C', axis=ax, children=kids, **mk(t1 + kerf, ext[ax] - 2 * (t1 + kerf), ax, o0, osz))
        maps.append(SawMap(index=k + 1, copies=bd['q1'], sheet_length=L, sheet_width=W, is_remnant=False, sheet_id='s',
                           tree=root, placements=[], offcuts=offcuts, commands=[]))
    return maps


def lc4_stripped(data: bytes) -> bytes:
    r = lc4_parse(data)
    assert lc4_write_parsed(r) == data, "mustaqil qayta yozuvchi namunani aynan tiklamadi"
    for it in r['parts']:
        it['fme'] = lc4_strip_blob(it['fme'])
        it['fme2'] = lc4_strip_blob(it['fme2'])
    return lc4_write_parsed(r)


def _lc_diff(a: bytes, b: bytes) -> str:
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    return f"farq @{i} (len {len(a)} vs {len(b)}): {a[max(0, i - 40):i + 40]!r} | {b[max(0, i - 40):i + 40]!r}"


def _lc_op_for(p, fname):
    s = os.path.splitext(os.path.basename(fname))[0]
    base = p.name
    hint = s[len(base) + 1:] if s.startswith(base) else s
    return find_op(p, hint)


def exact_lc4(verbose=True):
    files = sorted(glob.glob(os.path.join(SAMPLES, 'Holzma 2', '*.LC4')))
    ok, notes = 0, []
    for f in files:
        order = os.path.basename(f)[:4]
        data = open(f, 'rb').read()
        ref = lc4_stripped(data)
        r = lc4_parse(data)
        p = load(order)
        op = _lc_op_for(p, f)
        job = job_for(p, op, maps=[])
        job.maps = lc4_maps(r, job)
        out = LC4.build(job)
        # AddInfo_011 — detal ID: bizning importer ID larni 1.. qayta raqamlaydi (fayldagi `part@id` saqlanmaydi), qoldiqda —
        # boshqa dasturning ichki raqami. Solishtirishda: detal uchun bizning uid ↔ fayl ID moslik izchilligi tekshiriladi
        # va namunadagi qiymat qo'yiladi.
        o = lc4_parse(out)
        idmap = {}
        for a, b in zip(o['parts'], r['parts']):
            va, vb = dict(a['map']).get('AddInfo_011'), dict(b['map']).get('AddInfo_011')
            if a['fme'].startswith('detail.fme') and va is not None:
                if idmap.setdefault(va, vb) != vb:
                    notes.append(f"{order}: ID moslik buzildi {va}->{vb}")
            a['map'] = [(k, vb if k == 'AddInfo_011' and vb is not None else v) for k, v in a['map']]
        out2 = lc4_write_parsed(o)
        same = out2 == ref
        ok += same
        if not same:
            notes.append(f"{order}: {_lc_diff(out2, ref)}")
        if verbose:
            print('LC4', order, 'OK' if same else 'FARQ', '' if same else notes[-1][:300])
    return ok, len(files), notes


# ───────────────────────── SPL ─────────────────────────
def spl_parse(data: bytes) -> dict:
    i = 0
    recs = []
    while i < len(data):
        L, lv = struct.unpack_from('>HH', data, i)
        t = chr(data[i + 11])
        assert data[i + 6:i + 11] == b'\x30\x21\x00\x00\x00'
        p = data[i + 12:i + 12 + L]
        i += 12 + L
        link = None
        if t in 'cfx' and i < len(data) and not (t == 'x' and i + 4 > len(data)):
            link = struct.unpack_from('>I', data, i)[0]
            i += 4
        recs.append(dict(t=t, lv=lv, p=p, link=link))
    be = lambda b, o: struct.unpack_from('>I', b, o)[0]  # noqa: E731
    pats = []
    for r in recs:
        if r['t'] == 'd':
            d = r['p']
            pats.append(dict(name=d[18:24].split(b'\0')[0].decode(), rot=be(d, 24), qty=be(d, 28), L=be(d, 36) / 1e4,
                             W=be(d, 40) / 1e4, T=be(d, 44) / 1e4, nodes=[]))
        elif r['t'] == 'e':
            pats[-1]['e'] = r['p']
        elif r['t'] == 'f':
            pats[-1]['f'] = [be(r['p'], o) for o in range(0, 32, 4)]
        elif r['t'] == 'n':
            q = r['p']
            pats[-1]['nodes'].append((r['lv'], int.from_bytes(q[3:8], 'big'), be(q, 8) / 1e4))
    return dict(recs=recs, patterns=pats)


def spl_tree(nodes):
    root = dict(lv=0, kids=[])
    st = [root]
    for lv, pid, size in nodes:
        n = dict(lv=lv, pid=pid, size=size, kids=[])
        while st[-1]['lv'] >= lv:
            st.pop()
        st[-1]['kids'].append(n)
        st.append(n)
    return root['kids'][0]


def spl_maps(r: dict, job) -> list:
    kerf = job.kerf
    tl = struct.unpack_from('>I', r['patterns'][0]['e'], 32)[0] / 1e4 if r['patterns'] else 0
    by_idx = {i: p for i, p in enumerate(job.parts, 1)}
    maps = []
    for k, p in enumerate(r['patterns']):
        rot = bool(p['rot'])
        L, W = p['L'], p['W']
        ax, oth = ('y', 'x') if rot else ('x', 'y')
        ext = {'x': L, 'y': W}
        off = tl + kerf

        def mk(start, size, a, ostart, osize):
            return dict(x=start, y=ostart, l=size, w=osize) if a == 'x' else dict(x=ostart, y=start, l=osize, w=size)

        def build(kids, a, start, ostart, osize):
            out = []
            pos = start
            for n in kids:
                g = mk(pos, n['size'], a, ostart, osize)
                if n['pid']:
                    part = by_idx[n['pid']]
                    rotated = abs(g['l'] - part.length) > 0.5 or abs(g['w'] - part.width) > 0.5
                    out.append(SawNode(kind='P', uid=part.uid, rotated=rotated, **g))
                elif n['kids']:
                    o = 'y' if a == 'x' else 'x'
                    c = SawNode(kind='C', axis=o, **g)
                    c.children = build(n['kids'], o, ostart, pos, n['size'])
                    out.append(c)
                else:
                    out.append(SawNode(kind='W', **g))
                pos += n['size'] + kerf
            return out
        t = spl_tree(p['nodes'])
        osz = ext[oth] - 2 * off
        root = SawNode(kind='C', axis=ax, **mk(off, ext[ax] - 2 * off, ax, off, osz))
        root.children = build(t['kids'], ax, off, off, osz)
        maps.append(SawMap(index=k + 1, copies=p['qty'], sheet_length=L, sheet_width=W, is_remnant=False, sheet_id='s',
                           tree=root, placements=[], offcuts=[], commands=[]))
    return maps


def exact_spl(verbose=True):
    files = sorted(glob.glob(os.path.join(SAMPLES, 'Holzma 3', '*.SPL')))
    ok, notes = 0, []
    for f in files:
        order = os.path.basename(f)[:4]
        data = open(f, 'rb').read()
        p = load(order)
        # material: Holzma (.ptx) papkasidagi shu buyurtma fayli bo'yicha
        ptx = glob.glob(os.path.join(SAMPLES, 'Holzma', f'{order}_*.ptx'))
        op = _lc_op_for(p, ptx[0]) if ptx else cs_ops(p)[0]
        job = job_for(p, op, maps=[])
        r = spl_parse(data)
        job.maps = spl_maps(r, job)
        out = SPL.build(job)
        name = SPL.generate(job)[0][0]
        same = out == data
        ok += same
        if not same:
            notes.append(f"{order}: {_lc_diff(out, data)}")
        if name != os.path.basename(f):
            notes.append(f"{order}: nom {name} != {os.path.basename(f)}")
        if verbose:
            print('SPL', order, 'OK' if same else 'FARQ', name, '' if same else notes[-1][:300])
    return ok, len(files), notes


# ───────────────────────── oxirigacha (bizning optimizator) ─────────────────────────
def _lc_check(job, maps_back, gen_bytes, label):
    errs = []
    if b'GibLab' in gen_bytes or 'GibLab'.encode('utf-16-le') in gen_bytes:
        errs.append('GibLab so\'zi bor')
    want = {p.uid: p.qty for p in job.parts}
    got = {}
    for m in maps_back:
        for lf in leaves(m.tree):
            if lf.kind == 'P':
                got[lf.uid] = got.get(lf.uid, 0) + m.copies
                p = job.part(lf.uid)
                if sorted((round(lf.l, 1), round(lf.w, 1))) != sorted((round(p.length, 1), round(p.width, 1))):
                    errs.append(f'o\'lcham {p.name}: {lf.l}x{lf.w} vs {p.length}x{p.width}')
        errs += [f'daraxt: {e}' for e in tree_errors(m.tree, job.kerf)]
    ours = part_totals(job)
    # joylashuv: qayta o'qilgan detallar o'rni/o'lchami bizning kartadagi bilan bir xil bo'lishi kerak
    rect = lambda t: sorted((lf.uid, round(lf.x, 1), round(lf.y, 1), round(lf.l, 1), round(lf.w, 1))  # noqa: E731
                            for lf in leaves(t) if lf.kind == 'P')
    for a, b in zip(job.maps, maps_back):
        if rect(a.tree) != rect(b.tree):
            ra, rb = rect(a.tree), rect(b.tree)
            d = [x for x in ra if x not in rb][:2]
            errs.append(f"karta {a.index}: joylashuv farqi {d} / {[x for x in rb if x not in ra][:2]}")
    if got != ours:
        errs.append(f'soni: fayl {sum(got.values())} vs kroy {sum(ours.values())}')
    unpl = {u: q for u, q in want.items() if got.get(u, 0) != q}
    if sum(m.copies for m in maps_back) != sum(m.copies for m in job.maps):
        errs.append(f"listlar soni {sum(m.copies for m in maps_back)} != {sum(m.copies for m in job.maps)}")
    return errs, unpl


def lc_e2e(kind='lc4', orders=None, verbose=True):
    folder = 'Holzma 2' if kind == 'lc4' else 'Holzma 3'
    files = sorted(glob.glob(os.path.join(SAMPLES, folder, '*.LC4' if kind == 'lc4' else '*.SPL')))
    res = []
    for f in files:
        order = os.path.basename(f)[:4]
        if orders and order not in orders:
            continue
        p = load(order)
        src = f if kind == 'lc4' else (glob.glob(os.path.join(SAMPLES, 'Holzma', f'{order}_*.ptx')) or [f])[0]
        op = _lc_op_for(p, src) or cs_ops(p)[0]
        run_opt(p, op)
        job = job_for(p, op, key='holzma_cadmatic4' if kind == 'lc4' else 'holzma_cadmatic3')
        try:
            files_out = (LC4 if kind == 'lc4' else SPL).generate(job)
        except ValueError as e:
            # SPL: chuqurlik > 4 — loyiha «Макс. количество вращений» = 6; 4 bilan qayta kroy qilib tekshiramiz
            if verbose:
                print(kind.upper(), 'e2e', order, 'chuqur:', e, '→ max_rotations=4 bilan qayta')
            op.cs_cut.max_rotations = 4
            run_opt(p, op)
            job = job_for(p, op, key='holzma_cadmatic3')
            try:
                files_out = SPL.generate(job)
            except ValueError as e2:
                res.append((order, 'SKIP', str(e2)))
                continue
        name, data = files_out[0]
        if kind == 'lc4':
            r = lc4_parse(data)
            back = lc4_maps(r, job)
            names_ok = all(dict(it['map']).get('AddInfo_009') == jp.name and it['q1'] == jp.qty
                           for it, jp in zip(r['parts'], job.parts))
        else:
            r = spl_parse(data)
            back = spl_maps(r, job)
            names_ok = True
        errs, unpl = _lc_check(job, back, data, kind)
        if not names_ok:
            errs.append('nom/soni maydonlari mos emas')
        res.append((order, 'OK' if not errs else 'XATO', errs[:5], len(job.maps), sum(m.copies for m in job.maps),
                    len(unpl)))
        if verbose:
            print(kind.upper(), 'e2e', order, name, 'kartalar', len(job.maps), 'listlar', sum(m.copies for m in job.maps),
                  'OK' if not errs else errs[:5], '(kroyga sig\'maganlar: %d)' % len(unpl) if unpl else '')
    return res


def e2e_lc4(**kw):
    return lc_e2e('lc4', **kw)


def e2e_spl(**kw):
    return lc_e2e('spl', **kw)


# ═════════════════════════ HOMAG / HOMAG CHF (NPS400) ═════════════════════════
HM_BEST = os.environ.get('BEST', '1') == '1'
HOMAG_DIR = os.path.join(SAMPLES, "HOMAG")
CHF_DIR = os.path.join(SAMPLES, "HOMAG CHF 41.44..44 (NPS400)")


def hm_read_zip(src):
    z = zipfile.ZipFile(io.BytesIO(src) if isinstance(src, bytes) else src)
    return [(i.filename, z.read(i)) for i in z.infolist()]


def hm_rows_tree(data, kerf, trims=None):
    """parse_pattern + har bargga namunadagi qator raqami (`_row`) — uid biriktirish uchun."""
    d = parse_pattern(data, kerf, trims)
    rows = d["rows"]

    def expand(i):
        lvl = rows[i][0]
        j = i + 1
        kids = []
        while j < len(rows) and rows[j][0] > lvl:
            sub, j = expand(j)
            kids += sub
        return (kids if kids else [i]) * rows[i][2], j

    seq = []
    i = 0
    while i < len(rows):
        sub, i = expand(i)
        seq += sub
    lf = [n for n in leaves(d["tree"]) if n.kind == "P"]
    assert len(lf) == len(seq), (len(lf), len(seq))
    for n, ri in zip(lf, seq):
        n._row = ri
    return d


def _hm_row_tree(rows):
    """Namuna qatorlari → qatorlar daraxti [{i, size, rep, ch}] (uid biriktirish uchun)."""
    root = {"i": -1, "lv": 0, "size": 0, "rep": 1, "ch": []}
    st = [root]
    for i, (lv, s, r) in enumerate(rows):
        n = {"i": i, "lv": lv, "size": s, "rep": r, "ch": []}
        while st[-1]["lv"] >= lv:
            st.pop()
        n["up"] = st[-1]
        st[-1]["ch"].append(n)
        st.append(n)
    return root


def _hm_shape(n):
    return (n["size"], tuple((_hm_shape(c), c["rep"]) for c in n["ch"]))


def hm_assign(job, pats, limit=300000):
    """Namuna barglariga detal uid (generator kirishi uchun). Shartlar: bitta namuna qatori (rep bilan) — bitta detal;
    namunada alohida yozilgan qo'shni bir xil bo'laklarda kamida bitta mos barg — boshqa detal (aks holda generator
    ularni birlashtirgan bo'lardi); detal soni oshmasin. Orqaga qaytishli qidiruv, topilmasa — ochko'z."""
    items = []                       # (geo barglar, need, kandidatlar)
    cons = {}                        # item indeksi → [(juftlar ro'yxati)] — shu item tanlanganda tekshiriladi
    for rows, tree in pats:
        rt = _hm_row_tree(rows)
        geo = {}
        for n in leaves(tree):
            if n.kind == "P":
                geo.setdefault(n._row, []).append(n)
        idx = {}

        def leaf_rows(n):
            if not n["ch"]:
                yield n
            for c in n["ch"]:
                yield from leaf_rows(c)

        def walk_rows(n):
            yield n
            for c in n["ch"]:
                yield from walk_rows(c)

        for L in leaf_rows(rt):
            if L["i"] < 0 or L["i"] not in geo:
                continue
            need, x = 1, L
            while x["i"] >= 0:
                need *= x["rep"]
                x = x["up"]
            ns = geo[L["i"]]
            l, w = ns[0].l, ns[0].w
            straight = [p for p in job.parts if abs(p.length - l) < .01 and abs(p.width - w) < .01]
            rot = [p for p in job.parts if abs(p.width - l) < .01 and abs(p.length - w) < .01]
            cand = straight + [p for p in rot if not p.grain] + [p for p in rot if p.grain]
            idx[L["i"]] = len(items)
            items.append((ns, len(ns), cand))
        for X in walk_rows(rt):
            if X["i"] < 0:
                continue
            sib = X["up"]["ch"]
            k = sib.index(X)
            if k == 0 or _hm_shape(sib[k - 1]) != _hm_shape(X):
                continue
            pairs = [(idx[a["i"]], idx[b["i"]]) for a, b in zip(leaf_rows(X), leaf_rows(sib[k - 1]))
                     if a["i"] in idx and b["i"] in idx]
            if pairs:
                cons.setdefault(max(max(p) for p in pairs), []).append(pairs)
    rem = {p.uid: p.qty for p in job.parts}
    choice = [None] * len(items)
    steps = [0]

    def ok(i):
        for pairs in cons.get(i, []):
            if all(choice[a] is not None and choice[b] is not None and choice[a].uid == choice[b].uid for a, b in pairs):
                return False
        return True

    def dfs(i):
        if i == len(items):
            return True
        steps[0] += 1
        if steps[0] > limit:
            return False
        ns, need, cand = items[i]
        if not cand:
            return dfs(i + 1)
        for p in cand:
            if rem[p.uid] >= need:
                rem[p.uid] -= need
                choice[i] = p
                if ok(i) and dfs(i + 1):
                    return True
                rem[p.uid] += need
                choice[i] = None
        return False

    import sys as _s
    _s.setrecursionlimit(20000)
    if not dfs(0):                  # ochko'z: birinchi sig'adigan
        rem = {p.uid: p.qty for p in job.parts}
        for i, (ns, need, cand) in enumerate(items):
            choice[i] = next((p for p in cand if rem[p.uid] >= need), None) or (cand[0] if cand else None)
            if choice[i] is not None:
                rem[choice[i].uid] -= need
    bad = 0
    for (ns, need, cand), p in zip(items, choice):
        if p is None:
            bad += need
            continue
        for n in ns:
            n.uid = p.uid
            n.rotated = abs(p.length - n.l) > .01
    return bad


def _hm_exact_one(key, sample_zip, job):
    files = hm_read_zip(sample_zip)
    trees, maps = [], []
    for i, (nm, data) in enumerate(files, 1):
        d = hm_rows_tree(data, job.kerf, (job.trim_length, job.trim_width))
        trees.append((d["rows"], d["tree"]))
        maps.append(SawMap(index=i, copies=1, sheet_length=d["sheet"][0], sheet_width=d["sheet"][1], is_remnant=False,
                           sheet_id="", tree=d["tree"], placements=[], offcuts=[], commands=[],
                           trim_length=job.trim_length, trim_width=job.trim_width))
    bad = hm_assign(job, trees)
    job.maps = maps
    out = ppfmt.REGISTRY[key].fn(job)
    assert len(out) == 1 and out[0][0].endswith(".zip")
    gen = hm_read_zip(out[0][1])
    notes = []
    if [n for n, _ in gen] != [n for n, _ in files]:
        notes.append(f"fayllar: {[n for n, _ in gen]} != {[n for n, _ in files]}")
    nf = sum(1 for (a, x), (b, y) in zip(gen, files) if a == b and x == y)
    for (a, x), (b, y) in zip(gen, files):
        if x != y:
            xl, yl = x.split(b"\r\n"), y.split(b"\r\n")
            k = next(i for i in range(max(len(xl), len(yl))) if xl[i:i + 1] != yl[i:i + 1])
            notes.append(f"{a}: qator {k}: biz {xl[k:k + 1]} != namuna {yl[k:k + 1]}")
    if out[0][0] != os.path.basename(sample_zip):
        notes.append(f"zip nomi {out[0][0]} != {os.path.basename(sample_zip)}")
    if bad:
        notes.append(f"{bad} barg detalga mos kelmadi")
    return nf, len(files), notes


def exact_homag():
    ok = tot = 0
    notes = []
    for z in sorted(glob.glob(os.path.join(HOMAG_DIR, "*.zip"))):
        order = os.path.basename(z)[:4]
        rem = hm_read_zip(z)[0][1].split(b"\r\n")[0].decode("cp1251").split(",")
        p = load(order)
        op = next((o for o in cs_ops(p) if o.name == rem[2]), None) or find_op(p, rem[2])
        a, b, nt = _hm_exact_one("homag", z, job_for(p, op))
        ok += a
        tot += b
        notes.append(f"{order}: {a}/{b} " + "; ".join(nt))
    return ok, tot, notes


def _hm_chf_candidates(order):
    return sorted(set(glob.glob(os.path.join(PROJ, "**", f"{order}_*.project"), recursive=True) +
                      glob.glob(os.path.join(PROJ, "**", f"{order} *.project"), recursive=True)))


def _hm_key(l, w):
    return tuple(sorted((round(l, 2), round(w, 2))))


def hm_chf_match(z):
    """Namuna zip → (loyiha, op, fayl) — detallar multiset'i aynan mos keladigan CS operatsiya."""
    order = os.path.basename(z)[:4]
    ls = collections.Counter()
    for _, d in hm_read_zip(z):
        for n in leaves(parse_pattern(d)["tree"]):
            ls[_hm_key(n.l, n.w)] += 1
    for f in _hm_chf_candidates(order):
        try:
            p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
        except Exception:      # noqa: BLE001
            continue
        for op in cs_ops(p):
            c = collections.Counter()
            for sp in job_for(p, op).parts:
                c[_hm_key(sp.length, sp.width)] += sp.qty
            if c == ls:
                return p, op, f
    return None, None, None


def exact_chf():
    ok = tot = 0
    notes = []
    for z in sorted(glob.glob(os.path.join(CHF_DIR, "*.zip"))):
        order = os.path.basename(z)[:4]
        p, op, f = hm_chf_match(z)
        if p is None:
            notes.append(f"{order}: mos loyiha/operatsiya topilmadi (o'tkazib yuborildi)")
            continue
        job = job_for(p, op)
        smat = hm_read_zip(z)[0][1].split(b"\r\n")[0].decode("cp1251").split(",")[2]
        pre = []
        if job.material_name != smat:      # loyiha keyin tahrirlangan (material nomi o'zgargan) — namuna nomi bilan
            pre.append(f"loyihada material nomi o'zgargan ({job.material_name!r} → namuna {smat!r}); namuna nomi bilan")
            job.material_name = smat
        a, b, nt = _hm_exact_one("homag_chf", z, job)
        nt = pre + nt
        ok += a
        tot += b
        notes.append(f"{order} ({os.path.basename(f)}): {a}/{b} " + "; ".join(nt))
    return ok, tot, notes


# ───────────────────────── oxirigacha (bizning optimizator) ─────────────────────────
HM_LEVELS = {"homag": 5, "homag_chf": 4}       # format daraja chegarasi → optimizator «Макс. количество вращений»


def hm_e2e_job(key, p, op):
    if op.cs_cut is not None and op.cs_cut.max_rotations > HM_LEVELS[key]:
        op.cs_cut.max_rotations = HM_LEVELS[key]      # stanok profili: daraxt chuqurligi format chegarasidan oshmasin
    run_opt(p, op)
    job = job_for(p, op)
    if not job.maps:
        return 0, 0, ["(karta yo'q)"]
    errs = []
    out = ppfmt.REGISTRY[key].fn(job)
    if b"giblab" in b"".join(d for _, d in out).lower():
        errs.append("GibLab so'zi bor")
    files = hm_read_zip(out[0][1])
    if key == "homag":
        from app.services.ppfmt.saw_homag import books
        mult = [n for _, n in books(job)]
    else:
        mult = [1] * len(files)
    if len(mult) != len(files):
        errs.append(f"fayl soni {len(files)} != {len(mult)}")
    sheets = sum(m.copies for m in job.maps)
    if sum(mult) != sheets:
        errs.append(f"listlar {sum(mult)} != {sheets}")
    got = collections.Counter()
    grain_bad = 0
    gl = {(round(sp.length, 2), round(sp.width, 2)) for sp in job.parts if sp.grain}
    for (nm, data), k in zip(files, mult):
        if b"giblab" in data.lower():
            errs.append("GibLab")
        d = parse_pattern(data, job.kerf)
        e = tree_errors(d["tree"], job.kerf)
        if e:
            errs.append(f"{nm}: {e[:2]}")
        r = d["tree"]
        sl, sw = d["sheet"]
        if r.children:            # 1-daraja: oxirgi bo'lak oxiri ≤ D1 − trim
            last = r.children[-1]
            end = (last.x + last.l) if r.axis == "x" else (last.y + last.w)
            lim = (sl - job.trim_length) if r.axis == "x" else (sw - job.trim_width)
            if end > lim + 0.51:
                errs.append(f"{nm}: 1-daraja sig'maydi {end} > {lim}")
        for n in leaves(r):
            if n.kind == "P":
                got[_hm_key(n.l, n.w)] += k
                if (round(n.w, 2), round(n.l, 2)) in gl and (round(n.l, 2), round(n.w, 2)) not in gl:
                    grain_bad += k
    want = collections.Counter()
    pt = part_totals(job)
    for sp in job.parts:
        if pt.get(sp.uid):
            want[_hm_key(sp.length, sp.width)] += pt[sp.uid]
    if got != want:
        errs.append(f"detallar farqi: ortiq {dict(got - want)} kam {dict(want - got)}")
    unpl = sum(sp.qty for sp in job.parts) - sum(pt.values())
    if unpl:
        errs.append(f"(optimizator joylashtirmagan {unpl} dona)")
    if grain_bad:
        errs.append(f"teksturali detal burilgan {grain_bad}")
    return len(files), sheets, errs


def _hm_e2e(key, projects):
    res = []
    for label, p in projects:
        for op in cs_ops(p):
            if not op.parts:
                continue
            try:
                nf, sh, errs = hm_e2e_job(key, p, op)
            except Exception as e:      # noqa: BLE001
                nf, sh, errs = 0, 0, [f"XATO {type(e).__name__}: {e}"]
            res.append((label, op.name, nf, sh, errs))
    return res


def e2e_homag():
    ps = [(os.path.basename(z)[:4], load(os.path.basename(z)[:4]))
          for z in sorted(glob.glob(os.path.join(HOMAG_DIR, "*.zip")))]
    return _hm_e2e("homag", ps)


def e2e_chf():
    ps = []
    for z in sorted(glob.glob(os.path.join(CHF_DIR, "*.zip"))):
        p, op, f = hm_chf_match(z)
        if p is None:
            fs = _hm_chf_candidates(os.path.basename(z)[:4])
            if not fs:
                continue
            p, _ = import_project(open(fs[0], "rb").read(), os.path.basename(fs[0]))
        ps.append((os.path.basename(z)[:4], p))
    return _hm_e2e("homag_chf", ps)


def hm_show_e2e(name, res):
    good = sum(1 for r in res if not [e for e in r[4] if not e.startswith("(")])
    print(f"{name} e2e: {good}/{len(res)} operatsiya xatosiz")
    for lab, mat, nf, sh, errs in res:
        print(f"   {lab} {mat}: fayl {nf}, list {sh} {'OK' if not errs else errs}")


# ═════════════════════════ Shelling / Shelling (MCS) ═════════════════════════
def sh_um(s):
    return int(s) / 1000.0


# ───────────────────────── o'quvchi (parser) ─────────────────────────
def sh_parse_ncl(data: bytes):
    lines = data.decode("cp1251").split("\r\n")
    head = dict(title20=lines[0][13:33].rstrip(), date=lines[0][34:44], gid=lines[0][47:67], title=lines[1][5:].rstrip())
    B, F, R = [], [], []
    cur = None
    for l in lines:
        t = l[:4]
        if t == "B 01":
            B.append(dict(idx=int(l[5:9]), mat=l[12:32].rstrip(), t=sh_um(l[33:41]), L=sh_um(l[42:50]), W=sh_um(l[51:59])))
        elif t == "F 01":
            if l[15] == "1":
                R.append(dict(idx=int(l[5:9]), qty=int(l[17:23]), L=sh_um(l[61:69]), W=sh_um(l[70:78])))
                cur = None
                continue
            cur = dict(idx=int(l[5:9]), qty=int(l[17:23]), L=sh_um(l[61:69]), W=sh_um(l[70:78]), name=l[97:117].rstrip(),
                       rot=l[118], p1=l[155:175].strip(), p2=l[176:196].strip(), prod=l[263:283].rstrip(),
                       label=int(l[284:293]), fdate=l[294:304], edges=[])
            F.append(cur)
        elif t == "F 80" and cur is not None:
            cur["edges"] = [l[46 + 21 * i:67 + 21 * i].strip() for i in range(4)]
    return head, B, F, R


def sh_parse_ncp(data: bytes):
    L = [l for l in data.decode("cp1251").split("\r\n") if l]
    p01, p02, p03 = L[0].split(), L[1].split(), L[2].split()
    pat = dict(no=int(p01[2]), board=int(p01[3]), runs=int(p01[4]), books=int(p02[2]), per=int(p02[3]),
               D1=sh_um(p03[6]), D2=sh_um(p03[7]))
    C = []
    for l in L[4:]:
        if l.startswith("C "):
            C.append(dict(par=l[2:5], ch=l[6:9].strip(), size=sh_um(l[10:18]), cnt=int(l[19:22]),
                          ref=int(l[25:29]) if len(l) > 22 else None))
    pat["C"] = C
    return pat


def sh_label_tree(C):
    root = dict(label=C[0]["par"], kids=[])
    latest = {root["label"]: root}
    for c in C:
        par = latest[c["par"]]
        n = dict(c, kids=[], label=c["ch"])
        par["kids"].append(n)
        if c["ch"] not in ("T", "R", ""):
            latest[c["ch"]] = n
    return root


def sh_pattern_tree(pat, kerf: float) -> SawNode:
    """Karta → SawNode daraxti (list koordinatalari; x — list uzunligi)."""
    lt = sh_label_tree(pat["C"])
    k = lt["label"][0] == "K"
    D1, D2 = pat["D1"], pat["D2"]
    t0 = next((c["size"] for c in lt["kids"] if c["label"] == "T"), 0.0)
    t1 = t0
    for c in lt["kids"]:
        if c["label"] not in ("T", "R", "") and c["kids"]:
            t1 = next((g["size"] for g in c["kids"] if g["label"] == "T"), 0.0)
            break
    # along/across → x/y
    def mk(a0, b0, la, lb, ax, kind="C"):
        x, y, l, w = (a0, b0, la, lb) if ax_is_x(ax) else (b0, a0, lb, la)
        return SawNode(x=x, y=y, l=l, w=w, kind=kind, axis=ax if kind == "C" else "")

    def ax_is_x(ax):
        return ax == "x"

    root_ax = "x" if k else "y"
    root = mk(t0, t1, D1 - 2 * t0, D2 - 2 * t1, root_ax)

    def fill(node: SawNode, lab, ax):
        a0 = node.x if ax == "x" else node.y
        b0 = node.y if ax == "x" else node.x
        la = node.l if ax == "x" else node.w
        lb = node.w if ax == "x" else node.l
        pos = a0
        other = "y" if ax == "x" else "x"
        for c in lab["kids"]:
            if c["label"] == "T":
                continue
            if c["label"] == "R":
                n = mk(pos, b0, a0 + la - pos, lb, ax, "W")
                n.rem = c["ref"]
                node.children.append(n)
                pos = a0 + la + kerf
                continue
            for _ in range(max(1, c["cnt"])):
                if c["label"] == "":
                    n = mk(pos, b0, c["size"], lb, ax, "P")
                    n.uid = c["ref"]          # vaqtincha: F indeksi (keyin uid ga almashtiriladi)
                else:
                    n = mk(pos, b0, c["size"], lb, ax, "C")
                    n.axis = other
                    fill(n, c, other)
                node.children.append(n)
                pos += c["size"] + kerf
        # oxirgi chiqindi
        end = a0 + la
        if end - pos > 0.01:
            node.children.append(mk(pos, b0, end - pos, lb, ax, "W"))

    fill(root, lt, root_ax)
    return root


def sh_read_zip(path_or_bytes):
    z = zipfile.ZipFile(path_or_bytes if not isinstance(path_or_bytes, bytes) else io.BytesIO(path_or_bytes))
    return {n: z.read(n) for n in z.namelist()}


# ───────────────────────── loyiha va operatsiya ─────────────────────────
# MCS namunalari uchun eng mos loyiha fayllari (tahlil natijasi)
SH_MCS_BEST = {'2027': '2027 Donogul.project', '2031': '2031 Diyor.project', '2032': '2032 Axror.project'}


def sh_find_project(order):
    if order in SH_MCS_BEST:
        c = glob.glob(os.path.join(PROJ, "**", SH_MCS_BEST[order]), recursive=True)
        if c:
            return c[0]
    c = glob.glob(os.path.join(PROJ, "**", f"{order}_*.project"), recursive=True)
    c = [f for f in c if re.match(rf"{order}_", os.path.basename(f))]
    if not c:
        c = glob.glob(os.path.join(PROJ, "**", f"{order} *.project"), recursive=True)
    c.sort(key=lambda f: (len(os.path.basename(f)), f))
    return c[0] if c else None


_sh_cache = {}


def sh_project(order):
    if order not in _sh_cache:
        f = sh_find_project(order)
        p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
        _sh_cache[order] = p
    return _sh_cache[order]


def sh_op_for(p, title):
    t = norm(title)
    best = None
    for o in cs_ops(p):
        n = norm(o.name or o.code)
        if n and t.endswith(n) and (best is None or len(n) > len(norm(best.name))):
            best = o
    return best


def sh_sample_sets(mcs: bool):
    folder = os.path.join(SAMPLES, "Shelling (MCS)" if mcs else "Shelling")
    for f in sorted(glob.glob(os.path.join(folder, "*.l.zip"))):
        members = sh_read_zip(f)
        order = os.path.basename(f)[:4]
        yield order, os.path.basename(f)[:-6], {k: v for k, v in members.items() if not k.endswith(".zip")}
        for k, v in members.items():
            if k.endswith(".l.zip"):
                yield order, k[:-6], sh_read_zip(v)


def sh_parts_from_sample(F):
    """Faqat serializatorni tekshirish uchun: detallar namunaning o'zidan (loyiha versiyasi farqini chetlab)."""
    from app.services.ppfmt import SawPart
    out = []
    for f in F:
        ed = {}
        for side, e in zip(("bottom", "top", "left", "right"), f["edges"]):
            m = re.match(r"\((.*)\) (.*)", e)
            if m:
                ed[side] = dict(symbol=m.group(1), name="", thickness=float(m.group(2)))
        out.append(SawPart(uid=f["label"], name=f["name"], code="", length=f["L"], width=f["W"], qty=f["qty"],
                           grain=f["rot"] == "0", product=f["prod"], edges=ed, xnc_face=f["p1"], xnc_back=f["p2"]))
    return out


def sh_job_from_sample(p, op, members, mcs, self_parts=False):
    head, B, F, R = sh_parse_ncl(members["0000.ncl"])
    job = ppfmt.saw_job(p, op)
    if self_parts:
        job.parts = sh_parts_from_sample(F)
        if F:
            d = F[0]["fdate"].replace(".", "-")
            job.order_date = job.ready_date = d
        if job.material_name[:20].rstrip() != B[0]["mat"]:
            if not head["title"].startswith(job.project_name + "_"):     # loyiha fayli boshqa nomli versiya
                job.project_name = "_".join(head["title"].split("_")[:2])
            pre = job.project_name + "_"
            mat = head["title"][len(pre):].replace("_", " ") if head["title"].startswith(pre) else B[0]["mat"]
            job.material_name = mat if mat[:20].rstrip() == B[0]["mat"] else B[0]["mat"]
    findex_to_uid = {}
    # F indeks → bizning detal (tartib bo'yicha). Yorliq raqami: avvalgi dastur — part@id, biz — uid (importer
    # ketma-ket raqamlaydi), shuning uchun nomi mos detalga namunadagi raqam beriladi (faqat serializatorni tekshirish).
    for i, part in enumerate(job.parts, 1):
        if i <= len(F) and F[i - 1]["name"] == part.name[:20]:
            part.uid = F[i - 1]["label"]
        findex_to_uid[i] = part.uid
    maps = []
    for name in sorted(k for k in members if k.endswith(".ncp")):
        pat = sh_parse_ncp(members[name])
        tree = sh_pattern_tree(pat, job.kerf)
        for n in leaves(tree):
            if n.kind == "P":
                n.uid = findex_to_uid.get(n.uid, -n.uid)
        k = pat["C"][0]["par"][0] == "K"
        L, W = (pat["D1"], pat["D2"]) if k else (pat["D2"], pat["D1"])
        maps.append(SawMap(index=pat["no"], copies=pat["runs"], sheet_length=L, sheet_width=W, is_remnant=False,
                           sheet_id=f"b{pat['board']}", tree=tree, placements=[], offcuts=[], commands=[]))
    job.maps = maps
    job.stock = [dict(id=f"b{b['idx']}", length=b["L"], width=b["W"], qty=1, is_remnant=False) for b in B]
    return job, head


def sh_exact(mcs: bool, verbose=False, self_parts=False):
    ok = tot = mok = mtot = 0
    notes = []
    for order, title, members in sh_sample_sets(mcs):
        tot += 1
        try:
            p = sh_project(order)
        except Exception as e:  # noqa: BLE001
            notes.append(f"{title}: loyiha yo'q ({e})")
            continue
        op = sh_op_for(p, title)
        if op is None and self_parts:
            op = cs_ops(p)[0]
        if op is None:
            notes.append(f"{title}: CS operatsiya topilmadi")
            continue
        job, head = sh_job_from_sample(p, op, members, mcs, self_parts)
        ex = datetime.strptime(head["date"], "%Y-%m-%d")
        t, files = SH.build(job, mcs=mcs, gid=head["gid"], export=ex)
        ours = dict(files)
        good = True
        bad = []
        for k, v in members.items():
            if k.startswith("GibLabData"):
                continue
            mtot += 1
            if ours.get(k) == v:
                mok += 1
            else:
                good = False
                bad.append(k)
                if verbose:
                    a = v.decode("cp1251").split("\r\n")
                    b = (ours.get(k) or b"").decode("cp1251").split("\r\n")
                    for i, (x, y) in enumerate(zip(a, b)):
                        if x != y:
                            print(f"   {title} {k} L{i}\n     S:{x!r}\n     M:{y!r}")
                            break
                    if len(a) != len(b):
                        print(f"   {title} {k} qatorlar {len(a)} vs {len(b)}")
        extra = [k for k in ours if k not in members]
        if extra:
            good = False
            bad.append("ortiqcha:" + ",".join(extra))
        if t != title and not self_parts:
            bad.append(f"nom {t!r}≠{title!r}")
        ok += good
        if bad:
            notes.append(f"{title}: {bad[:6]}")
    return ok, tot, mok, mtot, notes


def exact_shelling(verbose=False, self_parts=False):
    return sh_exact(False, verbose, self_parts)


def exact_mcs(verbose=False, self_parts=False):
    return sh_exact(True, verbose, self_parts)


# ───────────────────────── uchidan-uchiga ─────────────────────────
def sh_verify(job, zbytes: bytes, fname: str):
    errs = []
    if b"giblab" in zbytes.lower():
        errs.append("GibLab so'zi zipda")
    members = sh_read_zip(zbytes)
    for k, v in members.items():
        if b"giblab" in v.lower() or "giblab" in k.lower():
            errs.append(f"GibLab so'zi: {k}")
    head, B, F, R = sh_parse_ncl(members["0000.ncl"])
    if len(F) != len(job.parts):
        errs.append(f"detallar {len(F)} ≠ {len(job.parts)}")
    for f, p in zip(F, job.parts):
        if f["name"] != p.name[:20] or (f["L"], f["W"]) != (round(p.length, 3), round(p.width, 3)) or f["qty"] != p.qty:
            errs.append(f"detal {f['idx']} mos emas")
    produced = {}
    sheets = 0
    nmaps = 0
    remq = {}
    for name in sorted(k for k in members if k.endswith(".ncp")):
        nmaps += 1
        pat = sh_parse_ncp(members[name])
        sheets += pat["runs"]
        if pat["books"] * pat["per"] != pat["runs"]:
            errs.append(f"{name}: paket")
        tree = sh_pattern_tree(pat, job.kerf)
        b = next((x for x in B if x["idx"] == pat["board"]), None)
        if b is None or sorted([b["L"], b["W"]]) != sorted([pat["D1"], pat["D2"]]):
            errs.append(f"{name}: list o'lchami")
        for e in tree_errors(tree, job.kerf):
            errs.append(f"{name}: {e}")
        for n in leaves(tree):
            if n.kind == "P":
                produced[n.uid] = produced.get(n.uid, 0) + pat["runs"]
                f = F[n.uid - 1]
                dims = sorted([round(n.l, 2), round(n.w, 2)])
                if dims != sorted([f["L"], f["W"]]):
                    errs.append(f"{name}: detal {n.uid} o'lchami {dims} ≠ {f['L']}x{f['W']}")
                if f["rot"] == "0" and abs(n.l - f["L"]) > 0.01:
                    errs.append(f"{name}: tekstura buzildi ({f['name']})")
            elif n.kind == "W" and n.rem:
                remq[n.rem] = remq.get(n.rem, 0) + pat["runs"]
                r = R[n.rem - 1]
                if (round(n.l, 2), round(n.w, 2)) != (r["L"], r["W"]):
                    errs.append(f"{name}: qoldiq {n.rem} o'lchami")
    placed = {}
    for m in job.maps:
        for n in leaves(m.tree):
            if n.kind == "P":
                placed[n.uid] = placed.get(n.uid, 0) + m.copies
    for f, p in zip(F, job.parts):
        if produced.get(f["idx"], 0) != placed.get(p.uid, 0):
            errs.append(f"detal {p.name}: faylda {produced.get(f['idx'], 0)}, kroyda {placed.get(p.uid, 0)}")
    exp_sheets = sum(m.copies for m in job.maps if m.tree is not None)
    if sheets != exp_sheets:
        errs.append(f"listlar {sheets} ≠ {exp_sheets}")
    for r in R:
        if remq.get(r["idx"], 0) != r["qty"]:
            errs.append(f"qoldiq {r['idx']} soni {r['qty']} ≠ {remq.get(r['idx'], 0)}")
    return errs, sheets, sum(placed.values())


def sh_e2e(mcs: bool, verbose=False):
    key = "shelling_mcs" if mcs else "shelling"
    fmt = ppfmt.load_all()[key]
    ok = tot = 0
    notes = []
    seen = set()
    for order, title, members in sh_sample_sets(mcs):
        if (order, title) in seen:
            continue
        seen.add((order, title))
        try:
            p = sh_load_fresh(order)
        except Exception as e:  # noqa: BLE001
            notes.append(f"{title}: loyiha yo'q ({e})")
            continue
        op = sh_op_for(p, title)
        if op is None or not op.parts:
            continue
        tot += 1
        run_opt(p, op)
        job = ppfmt.saw_job(p, op, key)
        files = fmt.fn(job)
        fname, data = files[0]
        errs, sheets, nparts = sh_verify(job, data, fname)
        if not errs:
            ok += 1
        else:
            notes.append(f"{title}: {errs[:4]}")
        if verbose:
            print(f"   {title}: listlar {sheets} (natija {op.result.total_sheets}), detal {nparts}, xato {len(errs)}")
    return ok, tot, notes


def sh_load_fresh(order):
    f = sh_find_project(order)
    p, _ = import_project(open(f, "rb").read(), os.path.basename(f))
    return p


def e2e_shelling(verbose=False):
    return sh_e2e(False, verbose)


def e2e_mcs(verbose=False):
    return sh_e2e(True, verbose)


# ═════════════════════════ ishga tushirish ═════════════════════════
def _show(title, ok, tot, notes):
    print(f"{title}: {ok}/{tot}")
    for n in notes:
        print("   ", n)


def lc4_exact():
    ok, tot, notes = exact_lc4(verbose=False)
    _show("Holzma 2 LC4 aniq (etiketka blobisiz)", ok, tot, notes)


def spl_exact():
    ok, tot, notes = exact_spl(verbose=False)
    _show("Holzma 3 SPL aniq", ok, tot, notes)


def _lc_show(title, res):
    good = sum(1 for r in res if r[1] == "OK")
    _show(title, good, len(res), [f"{r[0]}: {r[1]} {r[2] if r[1] != 'OK' else ''}"
                                  + (f" kartalar {r[3]}, listlar {r[4]}" if len(r) > 4 else "") for r in res])


def homag_exact():
    _show("HOMAG aniq (pattern fayllar)", *exact_homag())


def chf_exact():
    _show("HOMAG CHF aniq (pattern fayllar)", *exact_chf())


def shelling_exact():
    ok, tot, mok, mtot, notes = exact_shelling(False)
    _show(f"Shelling aniq: fayllar {mok}/{mtot}, zip", ok, tot, notes)
    ok, tot, mok, mtot, notes = exact_shelling(False, True)
    _show(f"Shelling aniq (detallar namunadan — faqat serializator): fayllar {mok}/{mtot}, zip", ok, tot, notes)


def mcs_exact():
    ok, tot, mok, mtot, notes = exact_mcs(False)
    _show(f"Shelling MCS aniq: fayllar {mok}/{mtot}, zip", ok, tot, notes)
    ok, tot, mok, mtot, notes = exact_mcs(False, True)
    _show(f"Shelling MCS aniq (detallar namunadan — faqat serializator): fayllar {mok}/{mtot}, zip", ok, tot, notes)


# kalit → (aniq, oxiridan-oxirigacha, ppfmt kaliti, stress uchun qayta o'quvchi yoki None)
CHECKS = {
    "ptx": (ptx_exact, ptx_e2e, "holzma_ptx", ptx_reparse),
    "lc4": (lc4_exact, lambda: _lc_show("Holzma 2 LC4 oxiridan-oxirigacha", e2e_lc4(verbose=False)), "holzma_cadmatic4", None),
    "spl": (spl_exact, lambda: _lc_show("Holzma 3 SPL oxiridan-oxirigacha", e2e_spl(verbose=False)), "holzma_cadmatic3", None),
    "homag": (homag_exact, lambda: hm_show_e2e("HOMAG", e2e_homag()), "homag", None),
    "chf": (chf_exact, lambda: hm_show_e2e("HOMAG CHF", e2e_chf()), "homag_chf", None),
    "shelling": (shelling_exact, lambda: _show("Shelling oxiridan-oxirigacha", *e2e_shelling(False)), "shelling", None),
    "mcs": (mcs_exact, lambda: _show("Shelling MCS oxiridan-oxirigacha", *e2e_mcs(False)), "shelling_mcs", None),
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keys = args or list(CHECKS)
    many = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--stress=")), 0)
    for k in keys:
        ex, e2e, key, reparse = CHECKS[k]
        ex()
        if "--no-e2e" not in sys.argv:
            e2e()
        if many and reparse:
            stress(key, reparse, many)


if __name__ == "__main__":
    main()
