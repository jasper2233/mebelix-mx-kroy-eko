"""Nanxing CutSaw / CutSawFG — `.zip` → `001.ncp …` (ikkilik kesish kartasi). Tavsif: docs/mebelix/postprocessors/
nanxing-cutsawfg.md, nanxing-cutsaw.md (ikkalasi bir xil format).

Har noyob karta → bitta `.ncp` (little-endian tuzilma: sarlavha, tugunlar daraxti 0x208 baytdan, dum 0x68, etiketkalar
0x1000 baytdan UTF-16LE CSV). CutSawFG: loyihaning boshqa materiallari (CS) xuddi shu zip ichiga ichki zip bo'lib qo'yiladi.
"""
from __future__ import annotations

from ...i18n import _
import io
import struct
import zipfile

from . import SawJob, register, saw_job
from . import _saw_strips as S

CC = b"\xcc"
MAX_ENTS = 22                     # tugundagi kesim yozuvlari sig'imi (format cheklovi)
NOTE = ("Torsovka yozuvlari (0/1-daraja) = kroy zonasining boshi (namunalarda 5). Y bo'yicha boshlanadigan kartada "
        "Y koordinatalari propilga siljiydi (namunalardagi kabi). Bitta tugunda 22 tadan ortiq turli kesim bo'lsa — fayl "
        "yaratilmaydi (format cheklovi).")


def _wstr(s: str, nbytes: int) -> bytes:
    b = s.encode("utf-16le")
    b = b[: nbytes - 2 - (len(b[: nbytes - 2]) % 2)] + b"\0\0"
    return b + CC * (nbytes - len(b))


def _body(n: dict) -> bytes:
    b = struct.pack("<2i8d", n["parent"], n["nchild"], n["L"], n["W"], n["wL"], n["wW"], n["tx"], n["ty"], n["X"], n["Y"])
    ents = list(n["ents"]) + [(0, 0, 0.0)] * (MAX_ENTS - len(n["ents"]))
    for t, c, s in ents:
        b += struct.pack("<iid", t, c, float(s))
    return b + struct.pack("<i", len(n["ents"])) + CC * 4


def write_ncp(L: float, W: float, t: float, kerf: float, count: int, util: float, nodes: list[dict],
              labels: list[str], tail_trim: float = 5.0) -> bytes:
    """nodes — pre-order (ildiz birinchi); labels — barglar soniga teng slot ('' — bo'sh)."""
    out = bytearray(b"\x00ZBD" + struct.pack("<3d", L, W, t))
    out += struct.pack("<d2ifi", kerf, count, count, util, len(nodes))
    out += bytes.fromhex("00000000000045000000") + CC * 54 + _body(nodes[0])
    for n in nodes[1:]:
        out += struct.pack("<i", -1) + b"\0" * 16 + CC * 4 + _wstr(n["name"], 0x40) + _body(n)
    out += struct.pack("<i", -1) + b"\0" * 16 + CC * 4 + struct.pack("<d", tail_trim) + _wstr("MATERIAL NAME", 0x40) \
        + struct.pack("<2i", 1, count)
    for s in labels:
        out += _wstr(s, 0x1000)
    return bytes(out)


def _b(v: bool) -> str:
    return "true" if v else "false"


def _f2(v: float) -> str:
    return f"{v:.2f}"


def _clean(s: str) -> str:
    """CSV maydonida vergul ajratuvchi bilan to'qnashmasin (namunalarda qo'shtirnoq/ekranlash yo'q)."""
    return (s or "").replace(",", ";").replace("\r", " ").replace("\n", " ")


def map_ncp(job: SawJob, mi: S.MapInfo, uid_idx: dict[int, int]) -> bytes:
    root = mi.root
    kerf = job.kerf
    dy = kerf if mi.axis == "y" else 0.0
    trim = {"x": mi.tx, "y": mi.ty}
    nodes: list[dict] = []
    leaves: list[tuple[S.Piece, dict]] = []

    def rect_of(p: S.Piece, parent_rect: dict, parent: S.Piece) -> dict:
        if p is root:
            return {"x": (0.0, mi.L), "y": (0.0, mi.W)}
        if p.kind == "R":
            a, b = parent.axis, S.other(parent.axis)
            return {a: (p.pos(a) + (dy if a == "y" else 0.0), p.size(a)), b: parent_rect[b]}
        x, y, l, w = p.cr
        return {"x": (x, l), "y": (y + dy, w)}

    def add(p: S.Piece, parent_idx: int, parent_rect: dict, parent: S.Piece) -> None:
        r = rect_of(p, parent_rect, parent)
        n = dict(parent=parent_idx, nchild=0, L=r["x"][1], W=r["y"][1], wL=r["x"][1], wW=r["y"][1], tx=0.0, ty=0.0,
                 X=r["x"][0], Y=r["y"][0], ents=[], name="")
        idx = len(nodes)
        nodes.append(n)
        if p.kind == "P":
            n["name"] = f"Д{uid_idx.get(p.uid, 0) + 1}"
            leaves.append((p, n))
            return
        if p.kind == "R":
            n["name"] = f"${p.k}"
            leaves.append((p, n))
            return
        n["name"] = "NONE"
        a = p.axis
        ta = 0 if a == "x" else 1
        n["tx" if a == "x" else "ty"] = trim[a]
        used = 0.0
        if p.level <= 1:
            n["ents"].append((ta + 2, 1, trim[a]))
            used += trim[a]
        for run in S.runs([c for c in p.children if c.kind != "R"]):
            sz = run[0].size(a)
            n["ents"].append((ta, len(run), sz))
            n["nchild"] += len(run)
            used += len(run) * (sz + kerf)
        if len(n["ents"]) > MAX_ENTS:
            raise ValueError(_("pp_e_node", fmt="NCP", n=len(n["ents"]), m=MAX_ENTS))
        if a == "x":
            n["wL"] = n["L"] - used
        else:
            n["wW"] = n["W"] - used
        for c in reversed(p.children):              # teskari kesish tartibi (eng uzoq bo'lak birinchi)
            add(c, idx, r, p)

    add(root, -1, {}, root)
    nodes[0]["name"] = ""
    # etiketkalar: noyob detallar (tugun tartibida), keyin qoldiqlar, qolgani bo'sh
    proj = _clean(S.project_title(job))
    mat = _clean(job.material_name)
    code = _clean(job.material_code)
    labels: list[str] = []
    seen: set[int] = set()
    part_area = 0.0
    for p, n in leaves:
        if p.kind != "P":
            continue
        part_area += n["L"] * n["W"]
        if p.uid in seen:
            continue
        seen.add(p.uid)
        i = uid_idx.get(p.uid, 0)
        sp = job.parts[i]
        e = sp.edges
        labels.append(",".join([
            f"Д{i + 1}", proj, mat, _clean(sp.name), _clean(sp.description), str(i + 1), _f2(sp.length), _f2(sp.width),
            str(sp.qty), "false", _clean(S.edge_text(e.get("top"))), _clean(S.edge_text(e.get("bottom"))),
            _clean(S.edge_text(e.get("left"))), _clean(S.edge_text(e.get("right"))), _b(S.part_groove(job, sp.uid)),
            _b(sp.has_mill), _b(sp.has_drill), _clean(sp.xnc_face), _clean(sp.xnc_back), code, _clean(sp.product)]))
    rem_area = 0.0
    for p, n in leaves:
        if p.kind != "R":
            continue
        rem_area += p.l * p.w
        labels.append(",".join([f"${p.k}", proj, mat, "", "", str(p.k), _f2(p.l), _f2(p.w), "0", "true", "", "", "", "",
                                "false", "false", "false", "", "", code, ""]))
    labels += [""] * (len(leaves) - len(labels))
    labels = [s[:2047] for s in labels]
    den = mi.L * mi.W - rem_area
    util = part_area / den if den > 0 else 0.0
    return write_ncp(mi.L, mi.W, job.thickness, kerf, mi.m.copies, util, nodes, labels, trim[mi.axis])


def _zinfo(name: str, dt: tuple, deflate: bool) -> zipfile.ZipInfo:
    zi = zipfile.ZipInfo(name, date_time=dt)
    zi.compress_type = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
    zi.create_system = 0
    return zi


def op_zip(job: SawJob, inner: list[tuple[str, bytes]] = ()) -> bytes:
    """Bitta material zip'i: `001.ncp …` (deflate) + ichki zip'lar (stored)."""
    infos = S.map_infos(job)
    uid_idx = {p.uid: i for i, p in enumerate(job.parts)}
    t = S.now()
    dt = (max(1980, t.year), t.month, t.day, t.hour, t.minute, t.second)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        k = 0
        for mi in infos:
            if mi.root is None:
                continue
            k += 1
            z.writestr(_zinfo(f"{k:03d}.ncp", dt, True), map_ncp(job, mi, uid_idx))
        for name, data in inner:
            z.writestr(_zinfo(name, dt, False), data)
    return buf.getvalue()


def ncp_files(job: SawJob, nested: bool) -> list[tuple[str, bytes]]:
    inner: list[tuple[str, bytes]] = []
    if nested:                                       # CutSawFG: boshqa materiallar — ichki zip
        from ...models import OpType
        for o in job.project.operations:
            if o.type != OpType.CS or o.id == job.op.id or not (o.result and o.result.maps):
                continue
            sj = saw_job(job.project, o)
            inner.append((S.file_stem(sj) + ".zip", op_zip(sj)))
    return [(S.file_stem(job) + ".zip", op_zip(job, inner))]


@register("nanxing_cutsaw", "Nanxing CutSaw (.ncp)", "saw", ".zip", note=NOTE)
def generate_cutsaw(job: SawJob):
    return ncp_files(job, nested=False)


@register("nanxing_cutsawfg", "Nanxing CutSawFG (.ncp)", "saw", ".zip",
          note=NOTE + " Loyihaning boshqa kroy qilingan materiallari shu zip ichida ichki zip bo'lib keladi.")
def generate_cutsawfg(job: SawJob):
    return ncp_files(job, nested=True)

