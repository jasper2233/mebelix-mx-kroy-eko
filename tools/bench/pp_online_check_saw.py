"""Arra postprotsessorlari — onlayn tizimda bitta loyihadan chiqarilgan fayllar bilan bayt-ma-bayt tekshiruv.
    cd tools/bench && python pp_online_check_saw.py [scheer qk3 kdt spl gdrive nc300 fastpanel e2e]

Namuna papkasi (`ONLINE_2026-10-04`): bitta loyiha (`loyiha.project`, 35 detal, 3 list) ikki xil kroy bilan:
  * A kroy (burilishlar 4) — `arra/*` va `yangi_formatlar/{holzma_cadmatic3.SPL, giben_gdrive, biesse_nc300, kdt_v*}`;
    daraxt manbai — `arra/felder_f4classic/*.txt` (daraja, o'lcham, detal raqamlari);
  * B kroy (burilishlar 3) — `yangi_formatlar/{scheer.zip, fastpanel_215.ocm}`; daraxt manbai — `.ocm` (o'lchamlar) +
    `teile.lst` (detal raqamlari, barglar tartibida).
Bizning optimizator boshqa joylashuv beradi, shuning uchun daraxtlar namunadan qo'lda quriladi (SawNode), detallar esa
loyihadan BIZNING importer bilan olinadi; generator natijasi namuna bilan solishtiriladi. Avvalgi dasturning etiketka
bloblari ataylab yozilmaydi (solishtirishdan chiqariladi).

Namunalar korxona fayllari — repoga kirmaydi (yo'l: PP_ONLINE; papka bo'lmasa skript o'tkazib yuboradi).
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, HERE)

from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import SawMap, SawNode  # noqa: E402

ONLINE = os.environ.get("PP_ONLINE", r"D:/cloude giblab jasur/post prtsessorlar/ONLINE_2026-10-04")
PROJECT_NAME = "Без имени"            # onlayn tizimdagi loyiha nomi (fayl nomlari shundan)
FORBIDDEN = b"giblab"


def path(*a) -> str:
    return os.path.join(ONLINE, *a)


def unzip(data: bytes) -> dict[str, bytes]:
    z = zipfile.ZipFile(io.BytesIO(data))
    return {i.filename.replace("\\", "/"): z.read(i) for i in z.infolist()}


def read_zip(*a) -> dict[str, bytes]:
    return unzip(open(path(*a), "rb").read())


def no_forbidden(files: dict[str, bytes]) -> bool:
    for name, data in files.items():
        if FORBIDDEN in data.lower() or FORBIDDEN in name.lower().encode():
            return False
        if data[:2] == b"PK" and not no_forbidden(unzip(data)):
            return False
    return True


# ───────────────────────── loyiha va daraxtlar ─────────────────────────
def load():
    p, _ = import_project(open(path("loyiha.project"), "rb").read(), "loyiha.project")
    op = next(o for o in p.operations if o.type == OpType.CS and o.parts)
    return p, op


class N:
    """Namunadan o'qilgan bo'lak: o'lcham (ota o'qi bo'ylab), detal raqami (barg) yoki ichki bo'laklar."""

    def __init__(self, size, uid=0, kids=None):
        self.size, self.uid, self.kids = float(size), uid, kids or []


def f4_parse(text: str):
    """F4Classic `.txt` → (1-daraja o'qi bo'ylab list o'lchami, [N])."""
    dimx = 0.0
    root: list[N] = []
    stack: list[tuple[int, list[N]]] = [(-1, root)]
    for ln in text.splitlines():
        if ln.startswith("PR_DIMX"):
            dimx = float(ln.split("=")[1])
        if not re.match(r"^\d+,", ln):
            continue
        f = [x.strip() for x in ln.split(",")]
        lvl, size = int(f[0]), float(f[1])
        while stack[-1][0] >= lvl:
            stack.pop()
        if len(f) >= 5:
            for u in f[4].split(":"):
                stack[-1][1].append(N(size, uid=int(u)))
        else:
            n = N(size)
            stack[-1][1].append(n)
            stack.append((lvl, n.kids))
    return dimx, root


def ocm_parse(text: str, ids: list[int]):
    """FastPanel `.ocm` → [(Length, [N])]; barg `Entry` larning detal raqami — `ids` dan (hujjat tartibida)."""
    import xml.etree.ElementTree as ET
    r = ET.fromstring(text)
    it = iter(ids)

    def conv(e) -> list[N]:
        out = []
        for c in e.findall("Entry"):
            q, d = int(c.get("Quantity")), float(c.get("Distance"))
            if len(c):
                kids = conv(c)
                out += [N(d, kids=kids) for _ in range(q)]
            else:
                u = next(it)
                out += [N(d, uid=u) for _ in range(q)]
        return out

    pats = []
    infos = r.findall("PanelInfo")
    for pi, pt in zip(infos, r.findall("Pattern")):
        pats.append((float(pi.get("Length")), conv(pt)))
    return pats


def make_map(job, index: int, dim1: float, nodes: list[N]) -> SawMap:
    """[N] → SawMap (list koordinatalarida): bo'laklar zona boshidan (torsovka + propil) propil bilan ketma-ket."""
    st = job.stock[0]
    L, W = float(st["length"]), float(st["width"])
    axis = "x" if abs(dim1 - L) < 0.01 else "y"
    kerf = job.kerf
    off = job.trim_length + kerf
    dims = {p.uid: (p.length, p.width) for p in job.parts}

    def build(ns: list[N], a: str, x0: float, y0: float, l: float, w: float, lvl: int) -> list[SawNode]:
        out = []
        pos = x0 if a == "x" else y0
        for n in ns:
            x, y, cl, cw = (pos, y0, n.size, w) if a == "x" else (x0, pos, l, n.size)
            if n.kids:
                b = "y" if a == "x" else "x"
                c = SawNode(x=x, y=y, l=cl, w=cw, kind="C", axis=b, level=lvl)
                c.children = build(n.kids, b, x, y, cl, cw, lvl + 1)
            else:
                pl, pw = dims[n.uid]
                rot = not (abs(cl - pl) < 0.01 and abs(cw - pw) < 0.01)
                c = SawNode(x=x, y=y, l=cl, w=cw, kind="P", uid=n.uid, rotated=rot, level=lvl)
            out.append(c)
            pos += n.size + kerf
        return out

    root = SawNode(x=off, y=off, l=L - 2 * off, w=W - 2 * off, kind="C", axis=axis)
    root.children = build(nodes, axis, off, off, root.l, root.w, 1)
    return SawMap(index=index, copies=1, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id=st["id"], tree=root,
                  placements=[], offcuts=[], commands=[], trim_length=job.trim_length, trim_width=job.trim_width)


def base_job(key: str, rot: int):
    p, op = load()
    p.name = PROJECT_NAME
    job = ppfmt.saw_job(p, op, None)
    job.params = {}
    job.max_rotations = rot
    return job


def job_a(key: str):
    """A kroy (F4Classic `.txt` dan)."""
    job = base_job(key, 4)
    for i, f in enumerate(sorted(glob.glob(path("arra", "felder_f4classic", "*.txt"))), 1):
        dim1, nodes = f4_parse(open(f, encoding="cp1251").read())
        job.maps.append(make_map(job, i, dim1, nodes))
    return job


def job_b(key: str):
    """B kroy (`.ocm` + `teile.lst` dan)."""
    job = base_job(key, 3)
    ids = [int(ln.split(b",")[6]) for ln in read_zip("yangi_formatlar", "scheer.zip")["teile.lst"].split(b"\r\n")
           if ln.count(b",") > 10]
    pats = ocm_parse(open(path("yangi_formatlar", "fastpanel_215.ocm"), encoding="utf-8").read(), ids)
    for i, (dim1, nodes) in enumerate(pats, 1):
        job.maps.append(make_map(job, i, dim1, nodes))
    return job


def run(key: str, job) -> dict[str, bytes]:
    """Generator natijasi: {nom: bayt} (zip ochilgan holda)."""
    out: dict[str, bytes] = {}
    for name, data in ppfmt.load_all()[key].fn(job):
        if data[:2] == b"PK":
            out.update(unzip(data))
            out["<zip>"] = name.encode()
        else:
            out[name] = data
    return out


def diff_at(a: bytes, b: bytes) -> str:
    i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"uzunlik {len(a)} vs {len(b)}, birinchi farq @{i}: biz {a[i:i + 16].hex()} | namuna {b[i:i + 16].hex()}"


class Res:
    def __init__(self, title: str):
        self.title, self.ok, self.tot, self.notes = title, 0, 0, []

    def eq(self, what: str, ours, theirs, note: str = "") -> bool:
        self.tot += 1
        same = ours == theirs
        self.ok += same
        if not same:
            if isinstance(ours, bytes) and isinstance(theirs, bytes):
                note = note or diff_at(ours, theirs)
            self.notes.append(f"{what}: {note or f'biz {ours!r} | namuna {theirs!r}'}")
        return same

    def show(self) -> bool:
        print(f"{self.title}: {self.ok}/{self.tot}")
        for n in self.notes:
            print("    " + n)
        return self.ok == self.tot


def file_ids(job) -> dict[int, int]:
    """Bizning detal uid (operatsiyadagi tartib raqami) → loyiha faylidagi `part/@id`. Onlayn tizim xesh-jadval kaliti
    va KDT `.lbd` indeksi sifatida fayldagi id ni ishlatadi; bizning importer detallarni 1..N qayta raqamlaydi."""
    import xml.etree.ElementTree as ET
    r = ET.parse(path("loyiha.project")).getroot()
    dims = {}
    for g in r.iter("good"):
        if g.get("typeId") == "product":
            for pe in g.findall("part"):
                dims[pe.get("id")] = (float(pe.get("l") or 0), float(pe.get("w") or 0), int(float(pe.get("count") or 0)))
    cs = next(o for o in r.findall("operation") if o.get("typeId") == "CS")
    ids = [pe.get("id") for pe in cs.findall("part") if dims.get(pe.get("id"), (0, 0, 0))[2] > 0]
    assert len(ids) == len(job.parts), (len(ids), len(job.parts))
    for i, sp in zip(ids, job.parts):
        assert dims[i][:2] == (sp.length, sp.width), (i, dims[i], sp.length, sp.width)
    return {sp.uid: int(i) for i, sp in zip(ids, job.parts)}


def remap_ids(job):
    """Detal uid larini fayldagi id ga almashtiradi (SawPart, operatsiya detallari, daraxt tugunlari)."""
    ids = file_ids(job)
    for sp in job.parts:
        sp.uid = ids[sp.uid]
    for p in job.op.parts:
        p.uid = ids.get(p.uid, p.uid)

    def walk(n):
        if n.uid:
            n.uid = ids[n.uid]
        for c in n.children:
            walk(c)
    for m in job.maps:
        walk(m.tree)
    return job


# ───────────────────────── tekshiruvlar ─────────────────────────
def check_scheer() -> Res:
    """Scheer (B kroy): NAME.CUT, soll.cut, holz0000.rec, teile.lst — bayt-ma-bayt; etikett.bin chiqarilmaydi."""
    r = Res("Scheer (B kroy, bayt-ma-bayt)")
    ours = run("scheer", job_b("scheer"))
    theirs = read_zip("yangi_formatlar", "scheer.zip")
    ours.pop("<zip>", None)
    r.eq("fayllar", sorted(ours), sorted(n for n in theirs if n != "etikett.bin"))
    for n in sorted(theirs):
        if n != "etikett.bin":
            r.eq(n, ours.get(n, b""), theirs[n])
    r.eq("begona nom yo'q", no_forbidden(ours), True)
    try:                                              # A kroy (4 daraja) — stanok formati qo'llamaydi → xato
        run("scheer", job_a("scheer"))
        r.eq("4 daraja → ValueError", False, True)
    except ValueError:
        r.eq("4 daraja → ValueError", True, True)
    return r


def _lbd_eq(r: Res, what: str, ours: bytes, theirs: bytes) -> None:
    """`.lbd`: daraxt, etiketka kalitlari tartibi, CSV ning 30 maydoni (31- — avvalgi dastur blobi — yozilmaydi)."""
    import pp_saw_check_giben as G
    a, b = G.lbd_parse(ours), G.lbd_parse(theirs)
    r.eq(what + " daraxt", a[0], b[0], "daraxt farq qiladi")
    r.eq(what + " etiketka qatorlari", [(k, s.split(",")[:30], len(s.split(","))) for k, s in a[1]],
         [(k, s.split(",")[:30], len(s.split(","))) for k, s in b[1]], "qatorlar farq qiladi")
    r.eq(what + " oxiri", a[2], b[2])


def _check_kdt(key: str, sample: str, title: str) -> Res:
    r = Res(title)
    ours = run(key, remap_ids(job_a(key)))
    theirs = read_zip("yangi_formatlar", sample)
    ours.pop("<zip>", None)
    r.eq("fayllar", sorted(ours), sorted(theirs))
    for n in sorted(theirs):
        if n not in ours:
            continue
        if n.endswith(".qk"):
            r.eq(n, ours[n], theirs[n])
        else:
            _lbd_eq(r, n, ours[n], theirs[n])
    r.eq("begona nom yo'q", no_forbidden(ours), True)
    return r


def check_qk3() -> Res:
    return _check_kdt("kdt_presize_qk", "kdt_v330.zip", "KDT PreSize V3.3.0P (A kroy; .qk bayt-ma-bayt, .lbd blobsiz)")


def check_kdt() -> Res:
    """V6.3.2P namunasi = V1.4.0P (`kdt_new`), V4.x (eski) namunasi = `kdt_ks33x` — namunalar o'zaro va bizning natija."""
    r = _check_kdt("kdt_new", "kdt_v632.zip", "KDT V6.3.2P = kdt_new, V4.x = kdt_ks33x (A kroy)")
    r2 = _check_kdt("kdt_ks33x", "kdt_v4x.zip", "")
    r.ok, r.tot, r.notes = r.ok + r2.ok, r.tot + r2.tot, r.notes + r2.notes
    for z, d in (("kdt_v632.zip", "kdt_new"), ("kdt_v4x.zip", "kdt_ks33x")):      # namunalar o'zaro bayt-ma-bayt
        a = read_zip("yangi_formatlar", z)
        b = {os.path.basename(f): open(f, "rb").read() for f in glob.glob(path("arra", d, "*"))}
        r.eq(f"{z} = arra/{d}", a, b, "namunalar farq qiladi")
    return r


def check_spl() -> Res:
    r = Res("Holzma CADmatic 3 .SPL (A kroy, bayt-ma-bayt)")
    ours = run("holzma_cadmatic3", job_a("holzma_cadmatic3"))
    r.eq("fayl nomi (8 belgi, lotin)", sorted(ours), ["Bez_imen.SPL"])
    r.eq("SPL", next(iter(ours.values())), open(path("yangi_formatlar", "holzma_cadmatic3.SPL"), "rb").read())
    r.eq("begona nom yo'q", no_forbidden(ours), True)
    return r


def check_gdrive() -> Res:
    r = Res("Giben GDrive .DAX/.CPX (A kroy, bayt-ma-bayt)")
    ours = run("giben_gdrive", job_a("giben_gdrive"))
    theirs = read_zip("yangi_formatlar", "giben_gdrive.zip")
    ours.pop("<zip>", None)
    r.eq("fayllar", sorted(ours), sorted(theirs))
    for n in sorted(theirs):
        r.eq(n, ours.get(n, b""), theirs[n])
    r.eq("begona nom yo'q", no_forbidden(ours), True)
    return r


def check_nc300() -> Res:
    """NC300: `dist` va `tagli` bayt-ma-bayt; namunadagi etiketka yozuvlarining 30-maydoni (avvalgi dastur blobi)
    bo'shatilib qayta kodlanadi (biz uni yozmaymiz)."""
    import pp_saw_check_biesse as B
    from app.services.ppfmt import biesse_nc300 as M
    r = Res("Biesse Selco NC300 (A kroy, bayt-ma-bayt, etiketka blobisiz)")
    ours = run("biesse_nc300", remap_ids(job_a("biesse_nc300")))
    theirs = read_zip("yangi_formatlar", "biesse_nc300.zip")
    ours.pop("<zip>", None)
    r.eq("fayllar", sorted(ours), sorted(theirs))
    for n in sorted(theirs):
        t = theirs[n]
        if n.startswith("tagli"):
            s = t.decode("cp1251")
            rests, dets, groups = B.nc_label(s)
            blk = M.label_block([f[:30] + [""] for f, _n in rests], [d[:30] + [""] for d in dets], groups)
            t = (s[:s.index("B_LABEL\r\n") + 9] + "\r\n".join(blk) + "\r\n" + s[s.index("E_LABEL"):]).encode("cp1251")
        r.eq(n, ours.get(n, b""), t)
    r.eq("begona nom yo'q", no_forbidden(ours), True)
    return r


def check_fastpanel() -> Res:
    """B kroy daraxti (`.ocm` + `teile.lst` dan qurilgan) bizning FastPanel generatoridan aynan shu `.ocm` ni beradi."""
    r = Res("FastPanel 2.1.5 .ocm (B kroy, bayt-ma-bayt)")
    ours = run("fastpanel", job_b("fastpanel"))
    r.eq("ocm", next(iter(ours.values())), open(path("yangi_formatlar", "fastpanel_215.ocm"), "rb").read())
    return r


def check_e2e() -> Res:
    """Oxiridan-oxirigacha: loyiha BIZNING optimizator bilan (burilishlar 3) kroy qilinadi va `run_saw` orqali fayl
    chiqariladi — xatosiz, begona nomsiz; Scheer `.rec` va V3.3.0P `.qk` hajmi yozuvlar soniga mos."""
    from app.services.calc import run_cutting
    r = Res("Oxiridan-oxirigacha (bizning kroy, burilishlar 3)")
    p, op = load()
    p.name = PROJECT_NAME
    op.cs_cut.max_rotations = 3
    run_cutting(p, op)
    n = len(op.result.maps)
    for key in ("scheer", "kdt_presize_qk", "holzma_cadmatic3", "giben_gdrive", "biesse_nc300"):
        try:
            name, data, _mime = ppfmt.run_saw(key, p, op)
        except ValueError as e:
            r.eq(key, str(e), "")
            continue
        files = unzip(data) if data[:2] == b"PK" else {name: data}
        r.eq(f"{key}: begona nom yo'q", no_forbidden({name: data}), True)
        if key == "scheer":
            r.eq("scheer: .rec hajmi", len(files["holz0000.rec"]), 0x180 + 0x580 * (n + 1))
            r.eq("scheer: soll.cut qatorlari", files["soll.cut"].count(b"\r\n"), n)
        if key == "kdt_presize_qk":
            r.eq("qk3: fayllar soni", len(files), 2 * n)
            r.eq("qk3: yozuvlar butun", all((len(d) - 12) % 273 == 0 for f, d in files.items() if f.endswith(".qk")), True)
    return r


CHECKS = dict(scheer=check_scheer, qk3=check_qk3, kdt=check_kdt, spl=check_spl, gdrive=check_gdrive, nc300=check_nc300,
              fastpanel=check_fastpanel, e2e=check_e2e)


def main() -> int:
    if not os.path.isfile(path("loyiha.project")):
        print(f"namuna papkasi topilmadi ({ONLINE}) — o'tkazib yuborildi")
        return 0
    sel = [a for a in sys.argv[1:] if not a.startswith("-")] or list(CHECKS)
    ok = True
    for k in sel:
        ok = CHECKS[k]().show() and ok
    print("HAMMASI MOS" if ok else "FARQLAR BOR")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
