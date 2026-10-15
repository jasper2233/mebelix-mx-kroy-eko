"""Biesse (NC300, OSI), SCM (MaestroCut, WinCut) va FELDER Format4 (PC6, PC7) arra formatlari uchun umumiy yordamchilar.

Modul nomi «_» bilan boshlanadi — `load_all()` uni format sifatida yuklamaydi. Faqat toza ma'lumot (SawJob) bilan ishlaydi.

Asosiy g'oya: optimizator daraxti (SawNode: C — guruh, P — detal, W — chixindi/qoldiq) **kesish darajalari daraxtiga**
(`Cut`) aylantiriladi: 1-daraja — polosa (list o'qlaridan biri bo'ylab), keyingi darajalar o'qni navbatma-navbat
almashtiradi; har yozuvda `dim` — ota o'qi bo'ylab o'lcham, barg — tayyor detal (yoki qoldiq). Chiqindi yozilmaydi
(stanok uni o'zi qoldiradi), trim va propil ham yozilmaydi — ular sozlamadan olinadi. Namunalardagi barcha formatlar
shu bitta daraxtni turli sintaksisda yozadi (docs/mebelix/postprocessors/*.md).

Etiketka maydonlari — faqat BIZNING stanok sozlamalaridagi jadvaldan (`pp_machine_ctx.get_label_fields`), qiymatlar
`services/expr.py` da hisoblanadi (CLAUDE.md 14-qoida). Boshqa dasturning ichki etiketka bloklari (zlib xarita, SVG eskiz)
bu yerda yaratilmaydi.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Any, Optional

from . import SawJob, SawMap, SawNode, safe_name
from . import order_text

PROGRAM = "MebeliX Kroy"          # yaratuvchi / dastur maydonlari (boshqa dastur nomi yozilmaydi)
EPS = 0.05


def other(a: str) -> str:
    return "y" if a == "x" else "x"


# ───────────────────────── kesish darajalari daraxti ─────────────────────────
@dataclass
class Cut:
    level: int                    # 1 — polosa, 2, 3, …
    axis: str                     # `dim` qaysi list o'qi bo'ylab: x | y
    dim: float                    # ota o'qi bo'ylab o'lcham (mm)
    cross: float                  # ikkinchi o'lcham (barg uchun — ota bo'lak o'lchami)
    uid: int = 0                  # barg-detal uid
    rem: int = 0                  # barg-qoldiq: offcut raqami (0 — qoldiq emas)
    rotated: bool = False
    rep: int = 1                  # ketma-ket bir xil yozuvlar soni (pastki daraxti bilan)
    rest: list[int] = field(default_factory=list)   # shu kesimdan keyin qolgan qoldiq(lar) raqami (SCM: etiketka shu kesimga)
    children: list["Cut"] = field(default_factory=list)

    @property
    def leaf(self) -> bool:
        return not self.children

    @property
    def sx(self) -> float:
        """Listning X o'qi bo'yicha o'lcham."""
        return self.dim if self.axis == "x" else self.cross

    @property
    def sy(self) -> float:
        return self.cross if self.axis == "x" else self.dim


def _along(n: SawNode, a: str) -> float:
    return n.l if a == "x" else n.w


def _pos(n: SawNode, a: str) -> float:
    return n.x if a == "x" else n.y


def _conv(children: list[SawNode], axis: str, cross: float, level: int) -> list[Cut]:
    """Bir ota ichidagi bolalar (o'q `axis` bo'ylab ketma-ket) → Cut ro'yxati. Chiqindi tashlanadi; xuddi shu o'qdagi
    ichki guruh ochiladi; barg ota bo'lakni ikkinchi o'qda to'liq egallamasa — qo'shimcha daraja (ajratish kesimi)."""
    out: list[Cut] = []
    for ch in sorted(children, key=lambda n: _pos(n, axis)):
        if ch.kind == "W" and not ch.rem:
            continue
        if ch.kind == "C" and ch.children and (ch.axis or other(axis)) == axis:
            out += _conv(ch.children, axis, cross, level)          # bir xil yo'nalish — ota ketma-ketligiga qo'shiladi
            continue
        dim, cr = _along(ch, axis), _along(ch, other(axis))
        if ch.kind == "C":
            if not ch.children:
                continue
            kids = _conv(ch.children, other(axis), dim, level + 1)
            if kids:
                out.append(Cut(level, axis, dim, cross, children=kids))
            continue
        leaf = Cut(level + 1, other(axis), cr, dim, uid=ch.uid if ch.kind == "P" else 0,
                   rem=ch.rem if ch.kind == "W" else 0, rotated=ch.rotated)
        if cr < cross - EPS:                                         # ikkinchi o'qda ham kesish kerak
            out.append(Cut(level, axis, dim, cross, children=[leaf]))
        else:
            leaf.level, leaf.axis, leaf.dim, leaf.cross = level, axis, dim, cross
            out.append(leaf)
    return out


def cut_tree(m: SawMap) -> tuple[str, list[Cut]]:
    """(1-daraja o'qi, 1-daraja yozuvlari). O'q `x` — polosalar X bo'ylab ketma-ket (o'lchami X da, kesim chizig'i Y
    bo'ylab), `y` — polosalar Y bo'ylab (gorizontal polosalar)."""
    r = m.tree
    if r is None:
        return "y", []
    if r.kind != "C" or not r.children:
        return "y", _conv([r], "y", r.l, 1)
    ax = r.axis or "y"
    return ax, _conv(r.children, ax, _along(r, other(ax)), 1)


def walk_cuts(cuts: list[Cut]):
    for c in cuts:
        yield c
        yield from walk_cuts(c.children)


def drop_rem(cuts: list[Cut]) -> list[Cut]:
    """Qoldiq barglarini olib tashlaydi (qoldiq faqat chiqindi sifatida qoladi); bo'sh qolgan guruhlar ham."""
    out = []
    for c in cuts:
        if c.leaf:
            if not c.rem:
                out.append(c)
            continue
        k = drop_rem(c.children)
        if k:
            out.append(replace(c, children=k))
    return out


def _sig(c: Cut, by_part: bool) -> tuple:
    return (round(c.dim, 2), c.rem, (c.uid if by_part else bool(c.uid)), tuple((_sig(k, by_part), k.rep) for k in c.children))


def merge_runs(cuts: list[Cut], by_part: bool) -> list[Cut]:
    """Ketma-ket bir xil yozuvlarni (pastki daraxti bilan) `rep` ga yig'adi. `by_part=False` — faqat o'lchamlar bo'yicha
    (NC300), `True` — barglar bir xil detal bo'lsagina (OSI, SCM)."""
    out: list[Cut] = []
    for c in cuts:
        c2 = replace(c, children=merge_runs(c.children, by_part), rest=list(c.rest))
        if out and _sig(out[-1], by_part) == _sig(c2, by_part):
            out[-1].rep += c2.rep
        else:
            out.append(c2)
    return out


def merged_sources(merged: list[Cut], originals: list[list[Cut]]):
    """Yig'ilgan daraxt yozuvi ↔ asl (yig'ilmagan) yozuvlar: (yozuv, [asl yozuvlar]) preorder. `originals` — har
    takrorlanish uchun asl aka-uka ro'yxati (ildizda: [asl ro'yxat])."""
    ptr = [0] * len(originals)
    for mc in merged:
        taken: list[Cut] = []
        for k, ol in enumerate(originals):
            taken += ol[ptr[k]:ptr[k] + mc.rep]
            ptr[k] += mc.rep
        yield mc, taken
        if mc.children:
            yield from merged_sources(mc.children, [t.children for t in taken])


def only_rem(c: Cut) -> bool:
    return bool(c.rem) if c.leaf else all(only_rem(k) for k in c.children)


def rem_numbers(c: Cut) -> list[int]:
    return [c.rem] if c.leaf else [n for k in c.children for n in rem_numbers(k)]


def attach_rests(cuts: list[Cut], parent: Optional[Cut] = None) -> list[Cut]:
    """Qoldiq barglarini ro'yxatdan olib, raqamini oldingi aka-uka kesimga (`rest`) biriktiradi (birinchi bo'lsa — otaga).
    Namunalarda qoldiq — oxirgi polosadan keyingi qism va etiketkasi oxirgi polosa kesimiga yoziladi."""
    out: list[Cut] = []
    for c in cuts:
        if only_rem(c):
            tgt = out[-1] if out else parent
            if tgt is not None:
                tgt.rest += rem_numbers(c)
            continue
        if c.children:
            c.children = attach_rests(c.children, c)
        out.append(c)
    return out


def leaves_mult(cuts: list[Cut], mult: int = 1):
    """(barg, umumiy takror) — `rep` lar ko'paytmasi bilan (bitta list uchun)."""
    for c in cuts:
        m = mult * c.rep
        if c.leaf:
            yield c, m
        else:
            yield from leaves_mult(c.children, m)


# ───────────────────────── detal ma'lumotlari ─────────────────────────
class Parts:
    """uid → loyiha detali (l/w, mahsulot, kromka kodi) va SawPart (kesish o'lchami, kromka belgisi)."""

    def __init__(self, job: SawJob):
        self.job = job
        op = job.op
        self.model = {p.uid: p for p in op.parts}
        self.index = {p.uid: i for i, p in enumerate(op.parts, 1)}
        self.saw = {p.uid: p for p in job.parts}
        self.prod = {p.id: p for p in job.project.products}
        self.prod_index = {p.id: i for i, p in enumerate(job.project.products, 1)}
        self.ops = {o.id: o for o in job.project.operations}

    def product(self, uid: int):
        p = self.model.get(uid)
        return self.prod.get(p.product_id or "") if p else None

    def edge(self, uid: int, side: str) -> dict:
        """{symbol, name, thickness, code} yoki {} (side: top | bottom | left | right)."""
        sp = self.saw.get(uid)
        e = dict((sp.edges or {}).get(side) or {}) if sp else {}
        if e:
            p = self.model.get(uid)
            ref = getattr(p, f"edge_{side}", None) if p else None
            o = self.ops.get(getattr(ref, "op_id", None) or "")
            e["code"] = (o.code if o else "") or ""
        return e

    def lw(self, uid: int) -> tuple[float, float]:
        """Loyiha o'lchami (l, w)."""
        p = self.model.get(uid)
        return (float(p.length), float(p.width)) if p else (0.0, 0.0)

    def cut_lw(self, uid: int) -> tuple[float, float]:
        sp = self.saw.get(uid)
        return (float(sp.length), float(sp.width)) if sp else self.lw(uid)


def order_name(job: SawJob) -> str:
    """Buyurtma nomi (mahsulotning «Заказ» maydoni, masalan «3161 mijoz»); bo'lmasa loyiha nomi."""
    ids = {p.product_id for p in job.op.parts if p.product_id}
    for pr in job.project.products:
        if pr.id in ids and (pr.order_info or "").strip():
            return order_text(job.project, pr.order_info)
    for pr in job.project.products:
        if (pr.order_info or "").strip():
            return order_text(job.project, pr.order_info)
    return job.project_name or job.order


def file_stem(job: SawJob) -> str:
    """`<loyiha nomi>_<material>` (bo'shliq va maxsus belgilar → «_», ketma-ketlari bitta)."""
    return safe_name(f"{job.project_name}_{job.material_name}", "kroy", 120)


def project_date(job: SawJob) -> date:
    for s in (job.order_date, str(getattr(job.project, "order_date", "") or "")):
        try:
            return date.fromisoformat(str(s)[:10])
        except ValueError:
            continue
    return date.today()


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def remnants(m: SawMap) -> dict[int, dict]:
    """Karta qoldiqlari: offcut raqami → {length, width, raw_length, raw_width} (faqat ishbop qoldiqlar)."""
    out = {}
    for o in m.offcuts or []:
        if o.get("kind") == "remnant" and o.get("number"):
            out[int(o["number"])] = o
    return out


# ───────────────────────── etiketka maydonlari (bizning jadval) ─────────────────────────
def label_rows(job: SawJob, key: str) -> list[dict]:
    """Stanok etiketka maydonlari jadvali (Настройки → Постпроцессоры). `params['_label_fields']` — tekshiruv/test uchun
    berilgan jadval; aks holda saqlangan sozlama, u ham bo'lmasa — sxema standarti."""
    rows = job.params.get("_label_fields") if isinstance(job.params, dict) else None
    if isinstance(rows, list):
        return [dict(name=str(r.get("name", "")), expr=str(r.get("expr", ""))) for r in rows]
    try:
        from ..pp_machine_ctx import get_label_fields
        return get_label_fields(key)
    except Exception:          # noqa: BLE001 — sozlamalar bazasi bo'lmasa (test) — sxema standarti
        try:
            from ..pp_machine_schema import default_label_rows
            return default_label_rows(key)
        except Exception:      # noqa: BLE001
            return []


class Labels:
    """Har detal uchun etiketka maydonlari qiymatlari (nom → qiymat; tartib — jadval tartibi)."""

    def __init__(self, job: SawJob, key: str, rows: Optional[list[dict]] = None):
        self.rows = rows if rows is not None else label_rows(job, key)
        self.job = job
        self._calc = None
        self._cache: dict[int, list[tuple[str, Any]]] = {}
        if self.rows:
            try:
                from ..pp_machine_ctx import LabelCalc
                self._calc = LabelCalc(job.project, job.op, self.rows)
            except Exception:  # noqa: BLE001
                self._calc = None
        self._by_uid = {p.uid: p for p in job.op.parts}

    def values(self, uid: int) -> list[tuple[str, Any]]:
        """[(maydon nomi, qiymat)] — jadval bo'sh bo'lsa []."""
        if uid in self._cache:
            return self._cache[uid]
        out: list[tuple[str, Any]] = []
        p = self._by_uid.get(uid)
        if self._calc is not None and p is not None:
            out = [(r["name"], r["value"]) for r in self._calc.values(p, None)]
        elif self.rows:
            out = [(r["name"], "") for r in self.rows]
        self._cache[uid] = out
        return out

    def by_index(self, uid: int, i: int, dflt: Any = "") -> Any:
        v = self.values(uid)
        return v[i][1] if i < len(v) else dflt

    def by_name(self, uid: int) -> dict[str, Any]:
        return {n: v for n, v in self.values(uid)}

    def first_uid(self) -> int:
        return self.job.op.parts[0].uid if self.job.op.parts else 0

    def warnings(self) -> list[dict]:
        return self._calc.warnings() if self._calc is not None else []


def text(v: Any) -> str:
    """Etiketka qiymati → matn (`expr.to_text`: 1400.0, true/false; bo'sh — «»)."""
    from .. import expr
    return expr.to_text(v)


# ───────────────────────── matn / son ─────────────────────────
def n2(v: float) -> str:
    return f"{float(v):.2f}"


def n1(v: float) -> str:
    return f"{float(v):.1f}"


def ival(v: float) -> str:
    """Butun bo'lsa butun, aks holda kerakli kasr (nuqta bilan, ortiqcha nolsiz)."""
    r = round(float(v), 3)
    if r == int(r):
        return str(int(r))
    return f"{r:.3f}".rstrip("0").rstrip(".")


def cents(v: float) -> int:
    """mm → 1/100 mm (butun)."""
    return int(round(float(v) * 100))


def fit(s: Any, w: int) -> str:
    """Qat'iy kenglik: chapga tekislab bo'shliq bilan to'ldiriladi, uzunrog'i kesiladi."""
    s = "" if s is None else str(s)
    return s[:w].ljust(w)


def zero(v: float, w: int, nd: int = 1) -> str:
    """Chapdan nol bilan to'ldirilgan son: zero(16, 5) → «016.0», zero(1900, 8) → «001900.0»."""
    s = f"{abs(float(v)):.{nd}f}" if nd else str(int(round(abs(float(v)))))
    s = s.rjust(w, "0")[-w:] if len(s) <= w else s
    return ("-" + s[1:]) if float(v) < 0 else s


def make_zip(files: list[tuple[str, bytes]], when: Optional[datetime] = None) -> bytes:
    """Zip (Deflate); barcha yozuvlar bir xil vaqt belgisi bilan."""
    t = (when or now()).timetuple()[:6]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            zi = zipfile.ZipInfo(name, date_time=t)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0
            z.writestr(zi, data)
    return buf.getvalue()


def esc_xml(s: Any) -> str:
    s = "" if s is None else str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
