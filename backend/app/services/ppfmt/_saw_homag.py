"""HOMAG «pattern.NNN» formati (oddiy HOMAG va HOMAG CHF / NPS400 uchun umumiy) — korxona namunalaridan o'rganilgan
(docs/mebelix/postprocessors/homag-zip.md, homag-chf-nps400.md).

Fayl: `#REMARK`, `#DIMENSION`, `#SPEEDS`, `#TRIMS` sarlavhalari va kesish daraxtining pre-order ro'yxati (`#CUT`).
Har `#CUT` — bitta bo'lak: daraja kodi, bo'lak o'lchami (shu daraja o'qi bo'ylab), takror soni. Bolasi yo'q bo'lak —
tayyor detal; bo'laklar ota boshidan zich (propil bilan) joylashadi, oxiridagi qoldiq/chiqindi yozilmaydi.
Detal nomi, etiketka, kromka faylga chiqmaydi — stanok faqat o'lchamlar bo'yicha kesadi.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Optional

from . import SawJob, SawMap, SawNode, num

# Mantiqiy daraja → fayldagi kod (namunalarda 1,2,3,7,9; 4/5/6/8 kodlari uchramagan)
LEVEL_CODE = {1: 1, 2: 2, 3: 3, 4: 7, 5: 9}
CODE_LEVEL = {v: k for k, v in LEVEL_CODE.items()}
EPS = 0.01


@dataclass
class Piece:
    """Format bo'lagi: `size` — ota bo'lakni kesish o'qi bo'ylab o'lcham; `rep` — ketma-ket takror."""
    size: float
    rep: int = 1
    uid: int = 0
    waste: bool = False
    children: list["Piece"] = field(default_factory=list)
    other: float = 0.0          # barg uchun: ikkinchi o'q bo'ylab o'lcham (1-daraja bargini o'rash uchun)

    def sig(self) -> tuple:
        return (round(self.size, 3), self.uid, self.waste, tuple((c.sig(), c.rep) for c in self.children))


def _other(axis: str) -> str:
    return "y" if axis == "x" else "x"


def _ext(n: SawNode, axis: str) -> float:
    return n.l if axis == "x" else n.w


def _strip_tail(items: list[Piece]) -> list[Piece]:
    """Oxiridagi chiqindi/qoldiq bo'laklar yozilmaydi (bo'laklar boshidan zich, qolgani — avtomatik chiqindi)."""
    while items and items[-1].waste:
        items.pop()
    return items


def _seq(n: SawNode, axis: str) -> list[Piece]:
    """`n` sohasi `axis` bo'ylab kesilganda hosil bo'ladigan bo'laklar ro'yxati."""
    if n.kind == "C" and (n.axis or "x") == axis:
        items: list[Piece] = []
        for c in n.children:
            items += _as_pieces(c, axis)
        return _strip_tail(items)
    return _strip_tail(_as_pieces(n, axis))


def _as_pieces(n: SawNode, axis: str) -> list[Piece]:
    size = _ext(n, axis)
    if size <= EPS:
        return []
    if n.kind == "P":
        return [Piece(size, uid=n.uid, other=_ext(n, _other(axis)))]
    if n.kind != "C" or not n.children:
        return [Piece(size, waste=True)]
    if (n.axis or "x") == axis:          # bir xil o'qli ichma-ich guruh — ota ro'yxatiga yoyiladi
        out: list[Piece] = []
        for c in n.children:
            out += _as_pieces(c, axis)
        return out
    kids = _seq(n, _other(axis))
    if not kids:
        return [Piece(size, waste=True)]
    if len(kids) == 1 and not kids[0].children and abs(kids[0].size - _ext(n, _other(axis))) < EPS:
        k = kids[0]                       # bo'lakni to'liq egallagan bitta detal — bo'lakning o'zi detal
        return [Piece(size, uid=k.uid, waste=k.waste, other=k.size)]
    return [Piece(size, children=kids)]


def _merge(items: list[Piece]) -> list[Piece]:
    """Ketma-ket bir xil bo'laklar (o'lcham, detal, ichki daraxt bir xil) → bitta qator, `rep` bilan."""
    out: list[Piece] = []
    for p in items:
        p.children = _merge(p.children)
        if out and out[-1].sig() == p.sig():
            out[-1].rep += p.rep
        else:
            out.append(p)
    return out


def map_pieces(m: SawMap) -> tuple[str, list[Piece]]:
    """Karta daraxti → (1-daraja o'qi, 1-daraja bo'laklari)."""
    root = m.tree
    if root is None:
        return "x", []
    axis = (root.axis or "x") if root.kind == "C" else "x"
    items = _seq(root, axis)
    for p in items:
        # 1-daraja bo'lagining o'zi detal bo'lsa — 2-daraja kesimi bilan yoziladi (namunalarda 1-darajali barg yo'q;
        # stanok trimi bilan bizning trim farq qilsa ham detalning ikkinchi o'lchami aniq bo'lsin)
        if not p.children and not p.waste and p.other > EPS:
            p.children = [Piece(p.other, uid=p.uid)]
            p.uid = 0
    return axis, _merge(items)


def depth(items: list[Piece], lvl: int = 1) -> int:
    return max((depth(p.children, lvl + 1) if p.children else lvl for p in items), default=0)


def leaf_count(items: list[Piece], mult: int = 1) -> int:
    n = 0
    for p in items:
        if p.children:
            n += leaf_count(p.children, mult * p.rep)
        elif not p.waste:
            n += mult * p.rep
    return n


def _txt(s: str) -> str:
    return (s or "").replace(",", " ").replace("\r", " ").replace("\n", " ")


def order_text(job: SawJob) -> str:
    """`#REMARK` 1-maydon: buyurtma — loyiha nomi («_» → probel; nom raqam bilan boshlanmasa oldiga buyurtma raqami).
    Namunalarda `3161_mijoz` loyihasi → `3161 mijoz` (mahsulot «Данные заказа» boshqacha bo'lgan holatda ham)."""
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order} {pn}".strip()
    return pn.replace("_", " ")


def pattern(job: SawJob, m: SawMap, max_level: int) -> bytes:
    axis, items = map_pieces(m)
    d = depth(items)
    if d > max_level:
        raise ValueError(f"karta {m.index}: kesish daraxti {d} darajali — format {max_level} darajagacha "
                         f"(«Макс. количество вращений» ni kamaytiring)")
    d1, d2 = (m.sheet_length, m.sheet_width) if axis == "x" else (m.sheet_width, m.sheet_length)
    rows = [f"#REMARK,{_txt(order_text(job))},{_txt(job.material_name)},",
            f"#DIMENSION,{num(d1, 2)},{num(d2, 2)},{num(job.thickness, 2)},0,",
            "#SPEEDS,0.00,0.00,0.00,0.00,",
            f"#TRIMS,{m.trim_length:.1f},{m.trim_width:.1f},0.0,0.0,0,"]

    def emit(ps: list[Piece], lvl: int) -> None:
        for p in ps:
            rows.append(f"#CUT,{LEVEL_CODE[lvl]},{num(p.size, 2)},{p.rep},0,0,0,0,0,0.00000,0,0,0,0,")
            emit(p.children, lvl + 1)

    emit(items, 1)
    return ("\r\n".join(rows) + "\r\n").encode("cp1251", errors="replace")


def zip_patterns(job: SawJob, patterns: list[bytes]) -> list[tuple[str, bytes]]:
    """Bitta zip (namunalardagi kabi, 1 ta pattern bo'lsa ham): ichida `pattern.001`, `pattern.002`, …"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, data in enumerate(patterns, 1):
            z.writestr(f"pattern.{i:03d}", data)
    return [(f"{zip_name(job)}.zip", buf.getvalue())]


def zip_name(job: SawJob) -> str:
    """`<loyiha>_<material>`: probel va qavslar ketma-ketligi → «_» (oxiridagi probel ham: `LDSP UD ` → `LDSP_UD_`),
    loyiha nomi buyurtma raqami bilan boshlanmasa — oldiga raqam."""
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order}_{pn}" if pn else order
    s = f"{pn}_{job.material_name}" if pn else (job.material_name or "kroy")
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", s)
    s = re.sub(r"[\s()]+", "_", s).lstrip("_")
    return s[:100] or "kroy"


# ───────────────────────── o'qish (tekshiruv va testlar uchun) ─────────────────────────
def parse_pattern(data: bytes, kerf: float = 0.0, trim: Optional[tuple[float, float]] = None) -> dict:
    """`pattern.NNN` → {remark, dim, thickness, trims, axis, tree (SawNode, list koordinatalarida), rows}.
    Daraxt: ildiz — trimdan keyingi soha (1-daraja o'qi bo'ylab C); `rep` ketma-ket nusxalarga yoyiladi;
    bo'laklar orasida `kerf`; bolasi yo'q bo'lak — detal (uid=0, chaqiruvchi o'zi biriktiradi)."""
    lines = [ln for ln in data.decode("cp1251").split("\r\n") if ln]
    hdr: dict[str, list[str]] = {}
    rows: list[tuple[int, float, int]] = []
    for ln in lines:
        f = ln.split(",")
        if f[0] == "#CUT":
            rows.append((CODE_LEVEL[int(f[1])], float(f[2]), int(f[3])))
        else:
            hdr[f[0]] = f[1:]
    d1, d2 = float(hdr["#DIMENSION"][0]), float(hdr["#DIMENSION"][1])
    tl, tw = (float(hdr["#TRIMS"][0]), float(hdr["#TRIMS"][1])) if trim is None else trim
    # pre-order → ichki daraxt
    root: dict = {"lv": 0, "size": None, "rep": 1, "ch": []}
    st = [root]
    for lv, s, r in rows:
        node = {"lv": lv, "size": s, "rep": r, "ch": []}
        while st[-1]["lv"] >= lv:
            st.pop()
        if st[-1]["lv"] != lv - 1:
            raise ValueError("daraja sakradi")
        st[-1]["ch"].append(node)
        st.append(node)
    # D1 ≥ D2 bo'lsa 1-daraja o'qi x (list uzunligi), aks holda y
    axis = "x" if d1 >= d2 else "y"
    sl, sw = (d1, d2) if axis == "x" else (d2, d1)

    def build(nd: dict, x: float, y: float, l: float, w: float, ax: str) -> SawNode:
        c = SawNode(x=x, y=y, l=l, w=w, kind="C", axis=ax)
        pos = x if ax == "x" else y
        for ch in nd["ch"]:
            for _ in range(ch["rep"]):
                if ax == "x":
                    cx, cy, cl, cw = pos, y, ch["size"], w
                else:
                    cx, cy, cl, cw = x, pos, l, ch["size"]
                if ch["ch"]:
                    c.children.append(build(ch, cx, cy, cl, cw, _other(ax)))
                else:
                    c.children.append(SawNode(x=cx, y=cy, l=cl, w=cw, kind="P"))
                pos += ch["size"] + kerf
        return c

    tree = build(root, tl, tw, sl - 2 * tl, sw - 2 * tw, axis)
    return dict(remark=hdr.get("#REMARK", []), dim=(d1, d2), thickness=float(hdr["#DIMENSION"][2]),
                trims=(tl, tw), axis=axis, tree=tree, rows=rows, sheet=(sl, sw))
