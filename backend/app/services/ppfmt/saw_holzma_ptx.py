"""Holzma — `.ptx` (PTX 1.13 matn formati) arra postprotsessori.

Tavsif: `docs/mebelix/postprocessors/holzma-ptx.md`. Bitta CS operatsiya (material) → bitta `.ptx` fayl, `cp1251`, CRLF.
Yozuvlar: HEADER, JOBS, PARTS_REQ×N, PARTS_INF×N, BOARDS, MATERIALS, {PATTERNS, CUTS×k}×P, OFFCUTS.

Kesish daraxti (`SawNode`) → CUTS: juft daraja — X (uzunlik) bo'ylab, toq — Y (eni) bo'ylab. Ildiz o'qi `x` bo'lsa
karta TYPE=2 (avval listni uzunligi bo'yicha bo'laklarga bo'lish, 0-daraja), `y` bo'lsa TYPE=0 (1-darajadan — bo'ylama
polosalar). Ketma-ket bir xil bo'laklar QTY_RPT ga yig'iladi; oxirgi chiqindi yozilmaydi, o'rtadagi chiqindi — detalsiz
qator (joylashuv siljimasligi uchun). Listning asl chekkasidan boshlanadigan kesimlar seriyasi oldidan trim (90/91/92).
"""
from __future__ import annotations

from typing import Optional

from . import SawJob, SawMap, SawNode, register
from . import order_text
from ._saw_common import fmt_date, ival, job_title

EPS = 0.05


def _clean(s: str) -> str:
    """Vergul — ajratgich (qo'shtirnoq ishlatilmaydi), qator oxirlari olib tashlanadi."""
    return (s or "").replace(",", " ").replace("\r", " ").replace("\n", " ")


# ───────────────────────── daraxtni tayyorlash ─────────────────────────
def _size(n: SawNode, ax: str) -> float:
    return n.l if ax == "x" else n.w


def _pos(n: SawNode, ax: str) -> float:
    return n.x if ax == "x" else n.y


def _other(ax: str) -> str:
    return "y" if ax == "x" else "x"


def _norm(n: SawNode, ax: str) -> list[SawNode]:
    """`ax` o'qi bo'ylab ketma-ket bo'laklar ro'yxati (bir xil o'qli ichki C lar ochiladi)."""
    out: list[SawNode] = []
    for c in n.children:
        if c.kind == "C" and (c.axis or "x") == ax and c.children:
            out.extend(_norm(c, ax))
        else:
            out.append(c)
    return out


class _Row:
    """CUTS qatori (trimdan tashqari): daraja, o'lcham, detal indeksi, takror va bolalar."""
    __slots__ = ("level", "dim", "part", "rpt", "kids")

    def __init__(self, level: int, dim: float, part: int = 0, kids: Optional[list["_Row"]] = None):
        self.level, self.dim, self.part, self.rpt, self.kids = level, dim, part, 1, kids or []

    def sig(self):
        return (self.level, round(self.dim, 2), self.part, tuple(k.sig() + (k.rpt,) for k in self.kids))


def _rows(node: SawNode, ax: str, level: int, idx: dict[int, int]) -> list[_Row]:
    """C tugun bolalari → qatorlar (`ax` — shu darajadagi o'q)."""
    seq = [c for c in _norm(node, ax) if _size(c, ax) > EPS]
    # oxirgi chiqindi(lar) yozilmaydi
    while seq and not _useful(seq[-1]):
        seq.pop()
    rows: list[_Row] = []
    ext = _size(node, _other(ax))                 # bo'lakning boshqa o'qdagi o'lchami
    for c in seq:
        rows.append(_piece(c, ax, level, ext, idx))
    return _merge(rows)


def _useful(n: SawNode) -> bool:
    if n.kind == "P":
        return True
    if n.kind == "C":
        return any(x.kind == "P" for x in _iter(n))
    return False


def _iter(n: SawNode):
    yield n
    for c in n.children:
        yield from _iter(c)


def _piece(c: SawNode, ax: str, level: int, ext: float, idx: dict[int, int]) -> _Row:
    dim = _size(c, ax)
    oa = _other(ax)
    if c.kind == "P":
        row = _Row(level, dim, idx.get(c.uid, 0))
        if _size(c, oa) + EPS < ext:              # detal bo'lakni to'liq egallamaydi — yana bitta kesim
            inner = _Row(level + 1, _size(c, oa), row.part)
            row.part = 0
            row.kids = [inner]
        return row
    if c.kind == "C" and c.children:
        kids = _rows(c, oa, level + 1, idx)
        # bo'lak ichida bitta detal butun bo'lakni egallasa — detal shu qatorning o'zi
        if len(kids) == 1 and kids[0].part and not kids[0].kids and kids[0].rpt == 1 \
                and abs(kids[0].dim - _size(c, oa)) <= EPS and _full_single(c, oa):
            return _Row(level, dim, kids[0].part)
        return _Row(level, dim, 0, kids)
    return _Row(level, dim, 0)                    # o'rtadagi chiqindi bo'lagi


def _full_single(c: SawNode, oa: str) -> bool:
    seq = [x for x in _norm(c, oa) if _size(x, oa) > EPS]
    return len(seq) == 1


def _merge(rows: list[_Row]) -> list[_Row]:
    out: list[_Row] = []
    for r in rows:
        if out and out[-1].sig() == r.sig():
            out[-1].rpt += r.rpt
        else:
            out.append(r)
    return out


# ───────────────────────── yozish ─────────────────────────
def _cuts(m: SawMap, idx: dict[int, int]) -> tuple[int, list[tuple]]:
    """(TYPE, [(function, dim, rpt, part, qty)])."""
    root = m.tree
    if root is None:
        return 0, []
    ax = root.axis or "x"
    tx, ty = root.x, root.y                       # trim (list chetidan zonagacha)
    typ = 2 if ax == "x" else 0
    top = _rows(root, ax, 0 if ax == "x" else 1, idx)
    out: list[tuple] = []

    def emit(r: _Row):
        out.append((r.level, r.dim, r.rpt, r.part, r.rpt if r.part else 0))
        if r.kids:
            # asl chekkadan boshlanadigan seriya: TYPE=2 da 0-daraja ichida (Y chekka), TYPE=0 da 1-daraja ichida (X)
            if typ == 2 and r.level == 0:
                out.append((91, ty, 0, 0, 0))
            elif typ == 0 and r.level == 1:
                out.append((92, tx, 0, 0, 0))
            for k in r.kids:
                emit(k)

    out.append((90, tx, 0, 0, 0) if typ == 2 else (91, ty, 0, 0, 0))
    for r in top:
        emit(r)
    return typ, out


def _offcuts(m: SawMap) -> list[tuple]:
    """Ildiz darajasidagi oxirgi qoldiq (rem>0): (matn L, matn W, yalpi L, yalpi W)."""
    root = m.tree
    if root is None or not root.children:
        return []
    ax = root.axis or "x"
    seq = _norm(root, ax)
    if not seq or seq[-1].kind != "W" or not seq[-1].rem:
        return []
    w = seq[-1]
    tx, ty = root.x, root.y
    if ax == "x":
        gl, gw = m.sheet_length - w.x, m.sheet_width
        return [(gl - tx, gw - 2 * ty, gl, gw)]
    gl, gw = m.sheet_length, m.sheet_width - w.y
    return [(gl - 2 * tx, gw - ty, gl, gw)]


def _part_extra(job: SawJob) -> dict[int, dict]:
    """Detal uid → buyurtma ma'lumoti (mahsulot «Данные заказа») va XNC kodlari (bog'lanish tartibida)."""
    out: dict[int, dict] = {}
    try:
        from ...models import OpType
        pr = job.project
        prods = {p.id: p for p in pr.products}
        xcode = {o.id: (o.code or "") for o in pr.operations if o.type == OpType.XNC}
        for p in job.op.parts:
            prod = prods.get(p.product_id or "")
            out[p.uid] = dict(order=order_text(pr, getattr(prod, "order_info", "") or "") if prod else "",
                              xnc=[xcode[x] for x in p.xnc_op_ids if x in xcode])
    except Exception:          # noqa: BLE001 — sun'iy ish (test) bo'lsa
        pass
    return out


@register("holzma_ptx", "Holzma (PTX) .ptx", "saw", "ptx",
          note="PTX 1.13 matn formati (cp1251). Kesish rejasi PATTERNS/CUTS daraxti sifatida; qoldiq OFFCUTS da "
               "(faqat ildiz darajasidagi деловой qoldiq). BOARDS info maydoni namunalardagi kabi «L x L».")
def gen(job: SawJob) -> list[tuple[str, bytes]]:
    P = job.params or {}
    title = job_title(job)
    dt = fmt_date(job.ready_date or job.order_date)
    mat = _clean(job.material_name)
    code = _clean(job.material_code if P.get("board_code", True) else "")
    idx = {p.uid: i for i, p in enumerate(job.parts, 1)}
    extra = _part_extra(job)
    lines: list[str] = [f"HEADER,1.13,{_clean(title)[:25]},0,0,1",
                        f"JOBS,1,{_clean(title).replace('_', ' ')},,{dt},{dt},,1,,"]
    for i, p in enumerate(job.parts, 1):
        q = int(p.qty)
        lines.append(f"PARTS_REQ,1,{i},{_clean(p.name)},1,{ival(p.length)},{ival(p.width)},{q},0,0,"
                     f"{1 if p.grain else 0},{q},0,0,0")
    for i, p in enumerate(job.parts, 1):
        e = p.edges or {}
        sides = ("bottom", "top", "left", "right")
        names = [_clean((e.get(s) or {}).get("name", "")) for s in sides]
        syms = [_clean((e.get(s) or {}).get("symbol", "")) for s in sides]
        ex = extra.get(p.uid, {})
        xn = ex.get("xnc") or [c for c in (p.xnc_face, p.xnc_back) if c]
        xn = (xn + ["", ""])[:2]
        lines.append(",".join(["PARTS_INF", "1", str(i), "", "1", ival(p.length), ival(p.width),
                               _clean(ex.get("order", ""))] + names + syms +
                              ["", "", mat, "", "", _clean(p.product), "", _clean(p.product_code), "", "", "1", "1",
                               _clean(xn[0]), _clean(xn[1]), f"(CS) {mat}"]))
    # listlar (har xil o'lcham — alohida BOARDS)
    boards: list[tuple[float, float]] = []
    bidx: list[int] = []
    for m in job.maps:
        key = (m.sheet_length, m.sheet_width)
        if key not in boards:
            boards.append(key)
        bidx.append(boards.index(key) + 1)
    if not boards and job.stock:
        boards.append((job.stock[0]["length"], job.stock[0]["width"]))
    book = int(job.pack_height // job.thickness) if job.thickness > 0 and job.pack_height > 0 else 1
    book = max(1, book)
    for b, (L, W) in enumerate(boards, 1):
        used = sum(max(1, m.copies) for m, bi in zip(job.maps, bidx) if bi == b)
        stq = next((int(s["qty"]) for s in job.stock if abs(s["length"] - L) < EPS and abs(s["width"] - W) < EPS), 10000)
        info = f"{ival(L)} x {ival(L)}" if P.get("board_info_ll", True) else f"{ival(L)} x {ival(W)}"
        lines.append(f"BOARDS,1,{b},{code},1,{ival(L)},{ival(W)},{stq},{used},0,0,{info},{mat},1")
    root0 = next((m.tree for m in job.maps if m.tree is not None), None)
    if root0 is not None:
        tr_y, tr_x = root0.y, root0.x
    else:
        inc = bool(getattr(getattr(job.op, "cs_cut", None), "trim_includes_kerf", False))
        tr_x = job.trim_length + (0 if inc else job.kerf)
        tr_y = job.trim_width + (0 if inc else job.kerf)
    k = ival(job.kerf)
    lines.append(f"MATERIALS,1,1,{code},{mat},{ival(job.thickness)},{book},{k},{k},{ival(tr_y)},{ival(tr_y)},"
                 f"{ival(tr_x)},{ival(tr_x)},0,0,0,1,1,1,1,,1")
    offs: list[tuple] = []
    for pi, (m, bi) in enumerate(zip(job.maps, bidx), 1):
        typ, cuts = _cuts(m, idx)
        run = max(1, m.copies)
        # QTY_CYCLES — paketlar (arra sikllari) soni: ⌈listlar / paketdagi listlar⌉ (PTX tavsifi; namunalarda run ≤ book → 1)
        cycles = -(-run // book)
        lines.append(f"PATTERNS,1,{pi},{bi},{typ},{run},{cycles},{min(run, book)},,0,0")
        for ci, (f, d, r, part, qp) in enumerate(cuts, 1):
            lines.append(f"CUTS,1,{pi},{ci},0,{f},{ival(d)},{r},{part},{qp}")
        for o in _offcuts(m):
            offs.append(o + (bi, run))
    for oi, (nl, nw, gl, gw, bi, run) in enumerate(offs, 1):
        lines.append(f"OFFCUTS,1,{oi},Остаток {ival(nl)} x {ival(nw)},{bi},{ival(gl)},{ival(gw)},{run}")
    data = ("\r\n".join(lines) + "\r\n").encode("cp1251", errors="replace")
    return [(f"{title}.ptx", data)]
