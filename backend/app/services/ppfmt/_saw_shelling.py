"""Shelling (Schelling) arra markazi: `.l.zip` ichida `0000.ncl` (listlar + detallar) va `NNNN.ncp` (har karta).

Format korxona namunalaridan o'rganilgan (docs/mebelix/postprocessors/shelling-zip.md, shelling-mcs-zip.md):
qat'iy kenglikdagi ASCII qatorlar, CRLF, o'lchamlar mikronda (mm × 1000, 8 xona). Ikkala variant (oddiy va MCS)
bir xil yozuvlardan iborat; farq faqat detal qatoridagi sana manbasida (buyurtma / tayyorlik sanasi).

Namunalardagi yorliq (etiketka) fayli boshqa dasturning ichki ma'lumoti — u yozilmaydi (faqat `.ncl` / `.ncp`).
"""
from __future__ import annotations

import io
import random
import re
import time
import zipfile
from datetime import datetime
from typing import Optional

from . import SawJob, SawNode, num
from ._saw_common import fmt_date

ENC = "cp1251"           # namunalarda faqat ASCII; kirill uchun cp1251 (taxmin — ochiq savol)
LETTERS = "XabcdefghijklmnopqrstuvwyzXX"   # 1-daraja polosa — X, keyin a, b, c, d …


def mm(v: float) -> str:
    """mm → mikron, 8 xona (00584000 = 584 mm)."""
    return "%08d" % max(0, round(float(v) * 1000))


def fx(s: str, n: int) -> str:
    """Qat'iy kenglikdagi matn: kesiladi va o'ngdan bo'sh joy bilan to'ldiriladi."""
    return (s or "")[:n].ljust(n)


def zip_title(job: SawJob) -> str:
    """`<loyiha>_<material>`: bo'sh joylar «_», «(» olib tashlanadi, «)» → «_» (namunalardagi nomlash);
    loyiha nomi buyurtma raqami bilan boshlanmasa — oldiga raqam qo'shiladi."""
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order}_{pn}" if pn else order
    s = f"{pn}_{job.material_name}" if pn else (job.material_name or "kroy")
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", s).replace("(", "").replace(")", "_")
    s = re.sub(r"\s+", "_", s)
    return s[:120] or "kroy"


def make_id(ms: Optional[int] = None) -> str:
    """Eksport ID (20 hex): 4 tasodifiy + `0000` + eksport vaqti (Unix ms, 12 hex) — namunalardagi shakl."""
    ms = int(time.time() * 1000) if ms is None else int(ms)
    return "%04x" % random.randrange(0x10000) + "0000" + "%012x" % (ms & 0xFFFFFFFFFFFF)


# ───────────────────────── 0000.ncl ─────────────────────────
def _edge(e: Optional[dict]) -> str:
    if not e:
        return ""
    return f"({e.get('symbol') or '?'}) {num(e.get('thickness') or 0, 2)}"


def _f01_part(idx, p, job: SawJob, gid: str, date: str) -> str:
    progs = fx(p.xnc_face, 20) + " " + fx(p.xnc_back, 20) + " " + " " * 41
    return ("F 01 %04d %04d 0 %06d %06d %s %s %s %s %s %s %s %s 9 9 0 00 000000 000 000000 000 1 0 %s1 0 %s %s %09d %s 0 0 000"
            % (idx, idx, p.qty, p.qty, fx(job.material_name, 20), mm(job.thickness), mm(p.length), mm(p.width),
               mm(p.length), mm(p.width), fx(p.name, 20), "0" if p.grain else "1", progs, gid, fx(p.product, 20),
               p.uid, date))


def _f01_rem(idx, qty, job: SawJob, L: float, W: float) -> str:
    return ("F 01 %04d %04d 1 %06d %06d %s %s %s %s 00000000 00000000 %s 0 9 9 0 00 000000 000 000000 000 0 0"
            % (idx, idx, qty, qty, fx(job.material_name, 20), mm(job.thickness), mm(L), mm(W), fx("Ostatok", 20)))


def _f80(p) -> str:
    e = p.edges or {}
    return ("F 80 00000000 00000000 00000000 00000000 0000 "
            + "".join(fx(_edge(e.get(s)), 21) for s in ("bottom", "top", "left", "right"))
            + "00 00 00 00 00000000 00000000")


# ───────────────────────── kesish daraxti → C qatorlari ─────────────────────────
def _along(n: SawNode, axis: str) -> float:
    return n.l if axis == "x" else n.w


def _norm_kids(n: SawNode) -> list[SawNode]:
    """Ota bilan bir o'qdagi ichki C guruhlar ochiladi (format o'qni har darajada almashtiradi)."""
    out: list[SawNode] = []
    for c in n.children:
        if c.kind == "C" and c.children and (c.axis or "x") == (n.axis or "x"):
            out.extend(_norm_kids(c))
        else:
            out.append(c)
    return out


def _sig(n: SawNode, axis: str):
    """Takrorlarni yig'ish uchun imzo (qoldiq raqami hisobga olinmaydi)."""
    s = round(_along(n, axis), 2)
    if n.kind == "P":
        return ("P", s, n.uid)
    if n.kind == "W":
        return ("W", s, bool(n.rem))
    ax = n.axis or "x"
    return ("C", s, round(n.l if ax != "x" else n.w, 2), ax, tuple(_sig(c, ax) for c in _norm_kids(n)))


class _Ncp:
    def __init__(self, job: SawJob, findex: dict[int, int], rems: list):
        self.job, self.findex, self.rems = job, findex, rems
        self.lines: list[str] = []
        self.strip_trim = 0.0        # 1-daraja polosalar boshidagi trim (list chetidan)
        self.runs = 1                # shu karta bo'yicha listlar soni

    def C(self, par: str, ch: str, size: float, cnt: int, ref: Optional[int] = None):
        s = "C %s %s %s %03d" % (par, fx(ch, 3), mm(size), cnt)
        self.lines.append(s + (" 0 %04d" % ref if ref is not None else ""))

    def node(self, n: SawNode, label: str, depth: int, mult: int, trim: Optional[float]):
        ax = n.axis or "x"
        kids = _norm_kids(n)
        if trim and trim > 0:
            self.C(label, "T", trim, 1)
        # oxirgi «haqiqiy» bo'lakdan keyingi oddiy chiqindi yozilmaydi
        last = max((i for i, c in enumerate(kids) if not (c.kind == "W" and not c.rem)), default=-1)
        groups: list[list] = []
        for c in kids[:last + 1]:
            sg = _sig(c, ax)
            if groups and groups[-1][0] == sg and c.kind != "W":
                groups[-1][2] += 1
            else:
                groups.append([sg, c, 1])
        k = 0
        for _sg, c, cnt in groups:
            size = _along(c, ax)
            if c.kind == "P":
                ref = self.findex.get(c.uid)
                if ref is None:
                    continue
                self.C(label, "", size, cnt, ref)
            elif c.kind == "W" and c.rem:
                # qoldiq: L — list uzunligi (x) bo'ylab; bir xil o'lchamli qoldiqlar bitta yozuv (soni yig'iladi)
                key = (round(c.l, 2), round(c.w, 2))
                i = next((j for j, r in enumerate(self.rems) if (r[0], r[1]) == key), None)
                if i is None:
                    self.rems.append([key[0], key[1], 0])
                    i = len(self.rems) - 1
                self.rems[i][2] += mult * self.runs
                self.C(label, "R", 0, 0, i + 1)
            else:                              # polosa (C) yoki o'rtadagi chiqindi — bo'sh polosa
                k += 1
                name = f"{LETTERS[min(depth, len(LETTERS) - 1)]}{k:02d}"
                self.C(label, name, size, cnt)
                if c.kind == "C":
                    self.node(c, name, depth + 1, mult * cnt, self.strip_trim if depth == 0 else None)


def _books(runs: int, per_max: int) -> tuple[int, int]:
    """Paketlar soni × paketdagi listlar = runs (paketdagi listlar ≤ paket balandligi / qalinlik)."""
    per_max = max(1, per_max)
    for per in range(min(per_max, runs), 0, -1):
        if runs % per == 0:
            return runs // per, per
    return runs, 1


def build(job: SawJob, mcs: bool = False, gid: Optional[str] = None, export: Optional[datetime] = None,
          stamp: Optional[datetime] = None) -> tuple[str, list[tuple[str, bytes]]]:
    """→ (zip nomi kengaytmasiz, [(a'zo nomi, bayt)])."""
    export = export or datetime.now()
    gid = gid or make_id(int(export.timestamp() * 1000))
    title = zip_title(job)
    date = fmt_date(job.order_date if mcs else job.ready_date, "%Y.%m.%d")
    findex = {p.uid: i for i, p in enumerate(job.parts, 1)}

    # listlar (B 01): ombordagi barcha o'lchamlar; karta → list indeksi
    boards: list[tuple[float, float]] = []
    bidx: dict[str, int] = {}
    for s in job.stock:
        key = (float(s["length"]), float(s["width"]))
        if key not in boards:
            boards.append(key)
        bidx[str(s.get("id"))] = boards.index(key) + 1
    for m in job.maps:
        key = (float(m.sheet_length), float(m.sheet_width))
        if str(m.sheet_id) not in bidx:
            if key not in boards:
                boards.append(key)
            bidx[str(m.sheet_id)] = boards.index(key) + 1

    per_max = int((job.pack_height or 0) // job.thickness) if job.thickness > 0 and job.pack_height else 1
    rems: list = []
    ncps: list[tuple[str, bytes]] = []
    pno = 0
    for m in job.maps:
        if m.tree is None:
            continue
        pno += 1
        root = m.tree
        ax = root.axis or "x"
        head = "K01" if ax == "x" else "L01"
        d1, d2 = (m.sheet_length, m.sheet_width) if ax == "x" else (m.sheet_width, m.sheet_length)
        runs = max(1, m.copies)
        books, per = _books(runs, per_max)
        w = _Ncp(job, findex, rems)
        w.strip_trim = root.y if ax == "x" else root.x       # polosa boshidagi trim (list chetidan)
        w.lines += ["P 01 %04d %04d %06d 0 0 0000 0" % (pno, bidx.get(str(m.sheet_id), 1), runs),
                    "P 02 01 %04d %04d 00000000 001" % (books, per),
                    "P 03 00 0 00 00000000 %s %s %s %s" % (mm(d1), mm(d2), mm(d1), mm(d2)),
                    "P 98 0 0 0"]
        w.runs = runs
        w.node(root, head, 0, 1, root.x if ax == "x" else root.y)
        w.lines.append("P$")
        ncps.append(("%04d.ncp" % pno, ("\r\n".join(w.lines) + "\r\n").encode(ENC, "replace")))

    ncl = ["S 01 001 001 %s %s 0 %s" % (fx(title, 20), export.strftime("%Y-%m-%d"), gid),
           "S 46 " + fx(title, 70)]
    for i, (L, W) in enumerate(boards, 1):
        ncl.append("B 01 %04d 0 %s %s %s %s 0 %s 0 0 0000000001 0"
                   % (i, fx(job.material_name, 20), mm(job.thickness), mm(L), mm(W), fx(job.material_name, 20)))
    for i, p in enumerate(job.parts, 1):
        ncl += [_f01_part(i, p, job, gid, date), "P 09 00000000 00000000 00000000 00000000 XXXX", _f80(p)]
    for i, (L, W, q) in enumerate(rems, 1):
        ncl.append(_f01_rem(i, q, job, L, W))
    ncl.append("S$")
    files = [("0000.ncl", ("\r\n".join(ncl) + "\r\n").encode(ENC, "replace"))] + ncps
    return title, files


def zip_bytes(files: list[tuple[str, bytes]], stamp: Optional[datetime] = None) -> bytes:
    t = (stamp or datetime.now()).timetuple()[:6]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            zi = zipfile.ZipInfo(name, date_time=t)
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
    return buf.getvalue()


def generate(job: SawJob, mcs: bool = False) -> list[tuple[str, bytes]]:
    title, files = build(job, mcs=mcs)
    return [(f"{title}.l.zip", zip_bytes(files))]
