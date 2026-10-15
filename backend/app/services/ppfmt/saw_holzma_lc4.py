"""Holzma (CADmatic 4) — `.LC4`: binar, tegli (little-endian) kesish rejasi + detal ro'yxati.
Tavsif: docs/mebelix/postprocessors/holzma2-lc4.md.

Bitta CS operatsiyasi (material) = bitta fayl `<loyiha>_<material>.LC4`.
Namunalardagi `fme` satri oxiridagi etiketka blobi (boshqa dasturning ichki ma'lumoti) yozilmaydi — maydon bo'sh qoladi;
etiketka ma'lumoti `map` (AddInfo_*, Edge_*, PartFinished*) kalitlarida ochiq ko'rinishda bor."""
from __future__ import annotations

import struct
from typing import Optional

from . import SawJob, num, register
from ._saw_common import job_title
from ._saw_holzma import HNode, HPat, merge_reps, pattern

# ───────────────────────── past daraja: teg + qiymat ─────────────────────────
T_BOOL, T_I16, T_I32, T_I64, T_STR, T_BYTES, T_DEC = 0x01, 0x05, 0x06, 0x08, 0x0D, 0x0E, 0x0F
E_ROOT, E_KIND, E_SUB, E_GRAIN, E_INFO = 0x10, 0x11, 0x12, 0x13, 0x14

# tugun turlari (kind, sub)
K_ROOT, K_TRIM, K_KERF, K_STRIP, K_PART, K_REST = (1, 1), (4, 4), (2, 4), (0, 0), (11, 0), (10, 0)

# map kalitlari tartibi: namunalardagi tartib — Java HashMap iteratsiyasi (satr xeshi bo'yicha savat, savat ichida
# qo'shilish tartibi). Biz ham shunday tartiblaymiz: `_hash_order`. Qo'shilish tartibi (savatdosh kalitlar uchun muhim):
INSERT_ORDER = ("Edge_MaterialBack", "Edge_MaterialLeft", "Edge_MaterialRight", "Edge_MaterialFront", "PartFinishedWidth",
                "PartFinishedLength", "AddInfo_001", "AddInfo_002", "AddInfo_003", "AddInfo_004", "AddInfo_006",
                "AddInfo_007", "AddInfo_008", "AddInfo_009", "AddInfo_010", "AddInfo_011", "AddInfo_012", "AddInfo_013",
                "AddInfo_014", "AddInfo_015", "AddInfo_016")


def _jhash(s: str) -> int:
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    return h ^ (h >> 16)


def _hash_order(keys: list[str]) -> list[str]:
    n = 16
    while len(keys) > n * 3 // 4:            # yuklanish koeffitsienti 0.75
        n *= 2
    ins = {k: i for i, k in enumerate(INSERT_ORDER)}
    return sorted(keys, key=lambda k: (_jhash(k) & (n - 1), ins.get(k, len(ins)), k))


class _W:
    def __init__(self):
        self.b = bytearray()

    def tag(self, t: int):
        self.b += struct.pack("<H", t)

    def boolean(self, v: bool):
        self.tag(T_BOOL)
        self.b.append(1 if v else 0)

    def i16(self, v: int):
        self.tag(T_I16)
        self.b += struct.pack("<h", v)

    def i32(self, v: int):
        self.tag(T_I32)
        self.b += struct.pack("<i", int(v))

    def i64(self, v: int):
        self.tag(T_I64)
        self.b += struct.pack("<q", int(v))

    def obj(self, ver: int = 1):
        self.boolean(True)
        self.i16(ver)

    def string(self, s: str):
        e = (s or "").encode("utf-8")
        self.tag(T_STR)
        self.boolean(True)
        self.tag(T_BYTES)
        self.i32(len(e))
        self.b += e

    def dec(self, mm: float):             # fixed-point ×100 000
        self.tag(T_DEC)
        self.i16(1)
        self.i64(int(round(float(mm) * 100000)))
        self.boolean(False)

    def enum(self, t: int, v: int):
        self.tag(t)
        self.i32(v)

    def lst(self, items, fn):
        self.obj()
        self.i32(len(items))
        for x in items:
            fn(x)


# ───────────────────────── yozuvlar ─────────────────────────
def _item(w: _W, r: dict):
    w.obj()
    w.i16(2)
    w.string(r["id"])
    w.string(r["fme"])
    w.string(r["fme"])                   # ikki marta (namunalarda aynan bir xil)
    w.dec(r["L"])
    w.dec(r["W"])
    w.dec(r["T"])
    w.i32(r["qty"])
    w.i32(r["qty"])
    w.enum(E_GRAIN, r["grain"])
    w.boolean(False)

    def pair(kv):
        w.obj()
        w.string(kv[0])
        w.string(kv[1])
    w.lst(r["map"], pair)
    w.boolean(False)


def _info(w: _W, a: int, rot: bool, label: str, e14: int, ref: int):
    w.obj()
    w.i32(a)
    w.boolean(rot)
    w.string(label)
    w.boolean(True)
    w.enum(E_INFO, e14)
    w.i32(ref)


def _node(w: _W, size: float, rep: int, kind: tuple[int, int], info: Optional[tuple] = None, kids=None):
    w.obj()
    w.string("")
    w.string("")
    w.dec(size)
    w.i32(rep)
    w.enum(E_KIND, kind[0])
    w.enum(E_SUB, kind[1])
    w.i16(1)
    w.i32(1 if info else 0)
    if info:
        _info(w, *info)
    w.lst([], None)
    kids = kids or []
    w.obj()
    w.i32(len(kids))
    for k in kids:
        k(w)


def _kerf(kerf: float):
    return lambda w: _node(w, kerf, 1, K_KERF)


def _trim(t: float):
    return lambda w: _node(w, t, 1, K_TRIM)


# ───────────────────────── ma'lumot ─────────────────────────
def _src_parts(job: SawJob) -> dict:
    return {p.uid: p for p in job.op.parts}


def _sizes(job: SawJob, uid: int):
    """(kesish L, W), (tayyor L, W) — loyiha detalidan (o'lcham rejimi, kromka, pripusk hisobga olinadi)."""
    sp = job.part(uid)
    try:
        from ..calc import edge_map
        from ..sizes import compute_sizes
        src = _src_parts(job).get(uid)
        if src is not None:
            cut = job.op.cs_cut
            s = compute_sizes(src, job.project.size_mode, edge_map(job.project), cut.machining_allowance if cut else 0)
            return (sp.length, sp.width), s.detail
    except Exception:          # noqa: BLE001 — sun'iy ishda loyiha detali bo'lmasligi mumkin
        pass
    return (sp.length, sp.width), (sp.length, sp.width)


def _flags(job: SawJob, uid: int, sp) -> tuple[bool, bool, bool]:
    """(paz, freza, присадка) — detalga bog'langan XNC dasturlar statistikasi bo'yicha (arra kesimi / freza metri /
    teshiklar soni > 0; namunalarda 358/358 mos). Paz — detal GR tomonlari ham. Loyiha detali bo'lmasa SawPart belgilari."""
    src = _src_parts(job).get(uid)
    if src is None:
        return False, bool(sp.has_mill), bool(sp.has_drill)
    groove = any(getattr(src, f"groove_{s}").op_id for s in ("top", "bottom", "left", "right"))
    mill = drill = False
    try:
        from ...models import OpType
        from .. import xnc as X
        xo = {o.id: o for o in job.project.operations if o.type == OpType.XNC}
        for xid in src.xnc_op_ids:
            o = xo.get(xid)
            if not o or not o.xnc:
                continue
            x = o.xnc
            st = X.program_stats(x.program, x.length, x.width, x.thickness, X.program_vars(x), x.par_values)
            groove = groove or st["saw_m"] > 0
            mill = mill or st["mill_m"] > 0
            drill = drill or st["drills"] > 0
    except Exception:          # noqa: BLE001 — hisoblab bo'lmasa SawPart belgilari
        return groove, bool(sp.has_mill), bool(sp.has_drill)
    return groove, mill, drill


def _order_text(job: SawJob) -> str:
    """Buyurtma matni: mahsulot «Данные заказа» (namunalarda `3161 mijoz`); bo'lmasa loyiha nomi."""
    prods = {p.id: p for p in getattr(job.project, "products", [])}
    for sp in job.op.parts:
        pr = prods.get(sp.product_id or "")
        if pr and pr.order_info:
            from . import order_text
            return order_text(job.project, pr.order_info)
    t = job.project_name or job.order
    return t.replace("_", " ")


def _f1(v: float) -> str:
    return f"{float(v):.1f}"


def _edge(e: Optional[dict]) -> str:
    return f"({e.get('symbol', '')}) {e.get('name', '')}" if e else ""


def _ordered(m: dict) -> list[tuple[str, str]]:
    return [(k, m[k]) for k in _hash_order(list(m))]


def _part_items(job: SawJob, title: str, order: str) -> list[dict]:
    items = []
    for i, p in enumerate(job.parts, 1):
        (cl, cw), (dl, dw) = _sizes(job, p.uid)
        ed = p.edges or {}
        sym = [(ed.get(s) or {}).get("symbol", "") for s in ("left", "right", "top", "bottom")]
        groove, mill, drill = _flags(job, p.uid, p)
        fme = ["detail.fme", "", str(p.qty), str(i), "1", title, num(cl), num(cw), p.name, str(p.qty), *sym,
               "true" if p.grain else "false"] + [""] * 16          # 15–29 bo'sh, 30 — etiketka blobi (yozilmaydi)
        m = {
            "AddInfo_001": job.material_name, "AddInfo_003": p.product, "AddInfo_004": p.product_code,
            "AddInfo_006": "1", "AddInfo_007": "1", "AddInfo_008": order, "AddInfo_009": p.name, "AddInfo_010": p.code,
            "AddInfo_011": str(p.uid), "AddInfo_012": "true" if groove else "false",
            "AddInfo_013": "true" if mill else "false", "AddInfo_014": "true" if drill else "false",
            "PartFinishedLength": _f1(dl), "PartFinishedWidth": _f1(dw),
        }
        if job.material_code:
            m["AddInfo_002"] = job.material_code
        if p.xnc_face or p.xnc_back:                  # 1-tomon (lits) XNC dasturi; ikkala tomon bo'lsa 016 — orqa
            m["AddInfo_015"] = p.xnc_face or p.xnc_back
        if p.xnc_face and p.xnc_back:
            m["AddInfo_016"] = p.xnc_back
        for side, key in (("bottom", "Edge_MaterialFront"), ("top", "Edge_MaterialBack"), ("left", "Edge_MaterialLeft"),
                          ("right", "Edge_MaterialRight")):
            if ed.get(side):
                m[key] = _edge(ed[side])
        items.append(dict(id=f"Д{i}", fme=",".join(fme), L=cl, W=cw, T=job.thickness, qty=p.qty,
                          grain=2 if p.grain else 0, map=_ordered(m)))
    return items


def _rest_item(job: SawJob, n: HNode, pat: HPat, k: int, title: str, order: str) -> dict:
    """Biznes-qoldiq yozuvi: o'lcham — kartaning qoldiqlar ro'yxatidan (trimdan keyingi), bo'lmasa daraxtdan."""
    L = W = 0.0
    for o in pat.map.offcuts:
        if o.get("number") == n.rem or (n.src is not None and abs(o.get("x", -1) - n.src.x) < 0.6
                                        and abs(o.get("y", -1) - n.src.y) < 0.6):
            L, W = float(o.get("length", 0)), float(o.get("width", 0))
            break
    if not (L and W) and n.src is not None:
        L, W = n.src.l, n.src.w
    area = L * W / 1e6
    fme = ["rest.fme", "", "1", "1", num(L), num(W), f"{area:.3f}", title] + [""] * 23
    m = {"PartFinishedWidth": _f1(W), "PartFinishedLength": _f1(L), "AddInfo_011": str(n.rem),
         "AddInfo_001": job.material_name, "AddInfo_012": "false", "AddInfo_013": "false", "AddInfo_014": "false",
         "AddInfo_008": order}
    if job.material_code:
        m["AddInfo_002"] = job.material_code
    return dict(id=f"Д{k}", fme=",".join(fme), L=L, W=W, T=job.thickness, qty=0, grain=0, map=_ordered(m))


def _anschnitt(job: SawJob, t: float) -> str:
    cut = job.op.cs_cut
    inc = bool(getattr(cut, "trim_includes_kerf", False)) if cut else False
    return _f1(t + (0 if inc else job.kerf))


def build(job: SawJob) -> bytes:
    title = job_title(job)
    order = _order_text(job)
    kerf = job.kerf
    pats = [p for p in (pattern(job, m) for m in job.maps) if p is not None]
    parts = _part_items(job, title, order)
    ref = {p.uid: i for i, p in enumerate(job.parts)}
    rests: list[dict] = []

    def emit_list(nodes: list[HNode], pat: HPat, level: int, trim: float):
        out = []
        if trim >= 0:
            out += [_trim(trim), _kerf(kerf)]
        for n, rep in merge_reps(nodes):
            out.append(emit(n, rep, pat, level))
            out.append(_kerf(kerf))
        return out

    def emit(n: HNode, rep: int, pat: HPat, level: int):
        if n.kind == "part":
            info = (1, pat.rot != n.rot, "Part", 1, ref.get(n.uid, 0))
            return lambda w: _node(w, n.size, rep, K_PART, info)
        if n.kind == "rest":
            rests.append(_rest_item(job, n, pat, len(rests) + 1, title, order))
            info = (1, False, "Rest", 1, len(parts) + len(rests) - 1)
            return lambda w: _node(w, n.size, 0, K_REST, info)
        if not n.kids:                                # o'rtadagi chiqindi bo'lagi — ichida kesim yo'q
            return lambda w: _node(w, n.size, rep, K_STRIP)
        kids = emit_list(n.kids, pat, level + 1, pat.trim2 if level == 1 else -1)
        return lambda w: _node(w, n.size, rep, K_STRIP, None, kids)

    # 1) kesish daraxtlari alohida yoziladi (qoldiq yozuvlari shu paytda yig'iladi), 2) keyin butun fayl
    rw = _W()
    for i, pat in enumerate(pats):
        _root(rw, job, i, pat, emit_list(pat.kids, pat, 1, pat.trim1))
    boards = [dict(id=str(i + 1), fme=job.material_name, L=p.sheet_l, W=p.sheet_w, T=job.thickness, qty=p.copies,
                   grain=0, map=[]) for i, p in enumerate(pats)]
    w = _W()
    w.obj()
    w.string(title)
    w.string(order)
    w.lst(parts + rests, lambda r: _item(w, r))
    w.lst(boards, lambda r: _item(w, r))
    w.lst([], None)
    w.obj()
    w.i32(len(pats))
    w.b += rw.b
    return bytes(w.b)


def _root(w: _W, job: SawJob, i: int, pat: HPat, kids: list):
    """Ildiz (list): nomi `00001`…, o'lchami — list uzunligi; dumida eni, listlar soni, material va parametrlar."""
    w.obj()
    w.i16(1)
    w.string(f"{i + 1:05d}")
    w.string("")
    w.dec(pat.sheet_l)
    w.i32(1)
    w.enum(E_KIND, K_ROOT[0])
    w.enum(E_SUB, K_ROOT[1])
    w.i16(1)
    w.i32(1)
    _info(w, 0, pat.rot, "", 3, i)
    w.lst([], None)
    w.obj()
    w.i32(len(kids))
    for k in kids:
        k(w)
    w.dec(pat.sheet_w)
    w.i32(pat.copies)
    w.i32(pat.copies)
    w.string(job.material_name)
    w.i16(1)
    w.enum(E_ROOT, 0)
    w.boolean(False)
    tx, ty = (pat.trim2, pat.trim1) if pat.rot else (pat.trim1, pat.trim2)      # X (uzunlik) va Y (eni) chetlari
    ax, ay = _anschnitt(job, max(tx, 0)), _anschnitt(job, max(ty, 0))
    params = [("AnschnittHintenOptimal", "0"), ("AnschnittKopf", "0.0"), ("AnschnittLinks", ax),
              ("AnschnittOben", ay), ("AnschnittRechts", ax), ("AnschnittUnten", ay),
              ("AnschnittNachschnittHinten", "0.0"), ("AnschnittNachschnittVorne", "0.0"),
              ("AnschnittNullVorneNichtSchneiden", "1"), ("NutTiefe", "0"), ("SaegeblattStaerke", num(job.kerf))]

    def p2(kv):
        w.obj(2)
        w.string(kv[0])
        w.string(kv[1])
        w.boolean(True)
    w.lst(params, p2)


@register("holzma_cadmatic4", "Holzma (CADmatic 4) .LC4", "saw", "LC4",
          note="Binar kesish rejasi (Holzma 2 namunalaridan). Detal etiketkasi ma'lumoti AddInfo_*/Edge_* maydonlarida; "
               "namunalardagi ichki etiketka blobi yozilmaydi. Qoldiq yozuvidagi AddInfo_011 — bizning qoldiq raqami.")
def generate(job: SawJob):
    return [(f"{job_title(job)}.LC4", build(job))]
