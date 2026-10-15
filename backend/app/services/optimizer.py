"""MebeliX Kroy — ko'p darajali gilyotina (guillotine) listli kroy optimizatori.

Mustaqil yozilgan algoritm (GibLab yoki boshqa dastur kodidan foydalanilmagan).

Kesish DARAXTI:
  * ildiz — listning foydali zonasi (torsovkadan keyin);
  * 1-daraja kesishlar listni polosalarga bo'ladi (C1), 2-daraja polosani bo'laklarga (C2/P2),
    3-daraja bo'lakni kichikroq bo'laklarga (C3/P3) va h.k. «Максимальное количество вращений»
    daraxt chuqurligini cheklaydi;
  * barg — detal (P) yoki chiqindi/qoldiq (W).
Har tugun ichidagi bolalar bitta o'q bo'ylab ketma-ket joylashadi va propil bilan ajratiladi.
Shu tuzilmadan to'g'ridan-to'g'ri: joylashuvlar, qoldiqlar, buyruqlar jadvali (T/C/P/W + daraja),
kesish uzunligi (LT) va kesishlar soni (CT) olinadi.

Qidiruv (har bir list uchun, eng yaxshisi tanlanadi):
  1) daraxtni rekursiv to'ldirish: nomzodlar «aniq mos → ko'ndalang eng yaxshi moslik» tartibida,
     1–2-darajada «pilot» (nomzod tanlansa hududning qolgan qismi qanchalik to'lishini sinab ko'rish),
     «kompozit» polosalar (eni ichidagi detallar yig'indisiga teng, detal o'lchami bo'lishi shart emas);
  2) detalga yo'naltirilgan gilyotina (bo'sh to'rtburchakka eng mos detal, ikki kesim bilan bo'lish);
  3) eski 3 bosqichli algoritm — butun ish bo'yicha solishtiriladi, natija hech qachon yomonlashmaydi.
To'ldirish yuqori bo'lsa bir xil karta takrorlanadi (paket / kratnost, C: n). Vaqt byudjeti bor.

Guruhlash (blok): «Группировка по длине/ширине» belgilangan detallar k tadan blokka birlashtiriladi
(blok = k detal + (k−1) guruh propili), optimizator blokni bitta element sifatida joylaydi, natijada blok
detallarga ajratiladi (daraxtda alohida tugun, `g` — guruh propili). Blok daraxt chuqurligi cheklovini buzmaydi.

Koordinatalar: X — list uzunligi bo'ylab, Y — eni bo'ylab, (0,0) — chap-yuqori burchak.
GibLab bilan mos atamalar: «Торцовка по длине» — uzunlik bo'ylab (yuqori/pastki chetdan) kesish,
ya'ni ENni kamaytiradi; «Торцовка по ширине» — UZUNLIKni kamaytiradi.
"""
from __future__ import annotations

import copy
import math
import random
import time
from bisect import bisect_left
from collections import deque
from dataclasses import dataclass, field, replace as dataclass_replace
from typing import Iterable, Optional

from ..models import (CSCutParams, CSMaterialParams, CutCommand, CutMap, CuttingResult,
                      FirstCutDir, Offcut, Placement, StockSheet, StripSort)

EPS = 1e-6


# ───────────────────────── Kirish elementi (API o'zgarmagan) ─────────────────────────
@dataclass
class Item:
    part_id: str
    uid: int
    l: float            # X bo'yicha (aylantirilmagan)
    w: float            # Y bo'yicha
    can_rotate: bool
    k: int = 1          # blok: nechta detal (guruhlash); 1 — oddiy detal
    gl: bool = True     # blok detallari uzunlik (l) bo'ylab ketma-ket; False — en (w) bo'ylab
    ul: float = 0.0     # blokdagi bitta detal o'lchami
    uw: float = 0.0

    def orientations(self) -> list[tuple[float, float, bool]]:
        o = [(self.l, self.w, False)]
        if self.can_rotate and abs(self.l - self.w) > EPS:
            o.append((self.w, self.l, True))
        return o

    @property
    def area(self) -> float:
        return self.l * self.w


# ───────────────────────── Shakllar hovuzi ─────────────────────────
class _Shape:
    """Bir xil o'lcham va aylanish imkoniyatiga ega detallar guruhi (turli part_id bo'lishi mumkin)."""
    __slots__ = ("idx", "l", "w", "rot", "area", "pids", "k", "gl", "ul", "uw")

    def __init__(self, idx: int, l: float, w: float, rot: bool, k: int = 1, gl: bool = True,
                 ul: float = 0.0, uw: float = 0.0):
        self.idx, self.l, self.w, self.rot = idx, l, w, rot
        self.k, self.gl, self.ul, self.uw = k, gl, ul, uw     # blok (guruh) ma'lumoti
        self.area = l * w
        self.pids: list[tuple[str, int]] = []      # (part_id, uid) — har nusxa (blok) uchun


def _r3(v: float) -> float:
    return round(v, 3)


class _Pool:
    """Joylashtirish uchun oldindan tayyorlangan ma'lumotlar (o'zgarmas); sonlar alohida ro'yxatda."""

    def __init__(self, items: list[Item]):
        by_key: dict[tuple, _Shape] = {}
        for it in items:
            blk = (it.k, bool(it.gl), _r3(it.ul), _r3(it.uw)) if it.k > 1 else (1,)
            key = (_r3(it.l), _r3(it.w), bool(it.can_rotate)) + blk
            sh = by_key.get(key)
            if sh is None:
                sh = by_key[key] = _Shape(0, key[0], key[1], key[2], *(blk if it.k > 1 else ()))
            sh.pids.append((it.part_id, it.uid))
        shapes = sorted(by_key.values(), key=lambda s: (-s.area, -max(s.l, s.w)))
        for i, s in enumerate(shapes):
            s.idx = i
            s.pids.sort(key=lambda p: (p[1], p[0]))
        self.shapes = shapes
        self.counts0 = [len(s.pids) for s in shapes]
        self.has_blocks = any(s.k > 1 for s in shapes)
        self.gk: Optional[float] = None       # guruh propili (blok ichidagi kesim)
        self.gk_differs = False               # guruh propili asosiy propildan farq qiladimi
        # o'q bo'yicha yo'nalishlar: (a — o'q bo'yicha, b — ko'ndalang, shakl, aylantirilganmi)
        self.ori: dict[str, list[tuple[float, float, int, bool]]] = {}
        self.neg: dict[str, list[float]] = {}
        self.exact: dict[str, dict[tuple[float, float], list[tuple[int, bool]]]] = {}
        # ko'ndalang o'lcham bo'yicha indeks: {b: [(a, shakl, aylantirilgan), ...]} (a kamayish tartibida)
        self.cross: dict[str, dict[float, list[tuple[float, int, bool]]]] = {}
        for axis in ("x", "y"):
            lst = []
            ex: dict[tuple[float, float], list[tuple[int, bool]]] = {}
            cr: dict[float, list[tuple[float, int, bool]]] = {}
            for s in shapes:
                orients = [(s.l, s.w, False)]
                if s.rot and abs(s.l - s.w) > EPS:
                    orients.append((s.w, s.l, True))
                for (ox, oy, r) in orients:
                    a, b = (ox, oy) if axis == "x" else (oy, ox)
                    lst.append((a, b, s.idx, r))
                    ex.setdefault((a, b), []).append((s.idx, r))
                    cr.setdefault(b, []).append((a, s.idx, r))
            lst.sort(key=lambda t: (-t[0], -t[1]))
            for v in cr.values():
                v.sort(key=lambda t: (-t[0], t[1]))
            self.ori[axis] = lst
            self.neg[axis] = [-t[0] for t in lst]
            self.exact[axis] = ex
            self.cross[axis] = cr


# ───────────────────────── Kesish daraxti ─────────────────────────
class _N:
    """Daraxt tuguni. kind: 'C' — ichida bolalar bor, 'P' — detal, 'W' — chiqindi/qoldiq."""
    __slots__ = ("x", "y", "l", "w", "level", "kind", "axis", "children", "s", "rot", "rem", "pid", "gk")

    def __init__(self, x, y, l, w, level, kind, axis=None, children=None, s=-1, rot=False):
        self.x, self.y, self.l, self.w = x, y, l, w
        self.level, self.kind, self.axis = level, kind, axis
        self.children: list[_N] = children if children is not None else []
        self.s = s            # shakl indeksi (P uchun)
        self.rot = rot
        self.rem = 0          # qoldiq raqami (Д1, Д2 ...)
        self.pid = None       # (part_id, uid) — yakuniy taqsimotda
        self.gk = None        # guruh (blok) tuguni: bolalar orasidagi propil

    def shift(self, dx: float, dy: float) -> None:
        self.x += dx; self.y += dy
        for c in self.children:
            c.shift(dx, dy)

    def leaves(self):
        if self.kind == "C":
            for c in self.children:
                yield from c.leaves()
        else:
            yield self


@dataclass
class _Cfg:
    kerf: float
    min_trim: float
    max_level: int
    mode: str = "eff"             # 'eff' | 'area'
    look: tuple[int, ...] = (1,)  # har darajada sinab ko'riladigan nomzodlar soni
    rollout: int = 0              # nechanchi darajagacha «pilot» ishlatiladi
    composite: bool = True        # tarkibga moslashuvchi (kompozit) o'lchamli bolalar
    min_strip_w: float = 0
    max_strip_w: float = 0
    max_types: int = 0
    budget: list = field(default_factory=lambda: [0])
    cheap: Optional["_Cfg"] = None
    rng: Optional[random.Random] = None    # tasodifiy qayta urinishlar: nomzodlar tartibiga shovqin
    noise: float = 0.0                     # shovqin (o'rin bo'yicha standart og'ish)

    def fast(self) -> "_Cfg":
        """Pilot uchun tezkor (ochko'z) konfiguratsiya."""
        if self.cheap is None:
            self.cheap = _Cfg(kerf=self.kerf, min_trim=self.min_trim, max_level=self.max_level, mode="eff",
                              look=(1,), rollout=0, composite=False, min_strip_w=self.min_strip_w,
                              max_strip_w=self.max_strip_w, max_types=self.max_types, budget=self.budget)
        return self.cheap


def _other(axis: str) -> str:
    return "y" if axis == "x" else "x"


def _stack_axis(sh: "_Shape", rot: bool) -> str:
    """Blok detallari list koordinatasida qaysi o'q bo'ylab ketma-ket turadi."""
    ax = "x" if sh.gl else "y"
    return _other(ax) if rot else ax


def group_kerf(cut: CSCutParams) -> float:
    """Guruh (blok) ichidagi propil: «Толщина пилы для групповых деталей», bo'sh bo'lsa — asosiy propil."""
    return cut.kerf_group if cut.kerf_group is not None and cut.kerf_group > 0 else cut.kerf


def _depth_ok(root: "_N", pool: "_Pool", max_rotations: int) -> bool:
    """Daraxt «Макс. количество вращений» chegarasidan chuqur emasmi: buyruq darajasi = burilish raqami,
    ya'ni har detal max_rotations-darajadan chuqur kesilmaydi (polosa — 1, polosadagi bo'lak — 2, ...).
    Tuzilma bo'yicha hisoblanadi (oilalar daraja maydonini har xil to'ldiradi); bloklar detallarga
    ajratilganda qo'shiladigan daraja ham hisobga olinadi."""
    lim = max(1, max_rotations)          # 1 — faqat birinchi kesim (polosalar): detal ildizning bevosita bolasi bo'lishi shart
    blocks = pool.has_blocks

    def walk(n: "_N", lvl: int) -> bool:
        if n.kind != "C":
            return True
        for c in n.children:
            if c.kind == "P":
                extra = 0
                if blocks and 0 <= c.s < len(pool.shapes) and pool.shapes[c.s].k > 1:
                    splice = _stack_axis(pool.shapes[c.s], c.rot) == n.axis and not pool.gk_differs
                    extra = 0 if splice else 1
                if lvl + 1 + extra > lim:
                    return False
            elif c.kind == "C" and not walk(c, lvl + 1):
                return False
        return True
    return walk(root, 0)


def _expand_blocks(root: "_N", pool: "_Pool", queues: dict, kerf: float) -> "_N":
    """Daraxt nusxasida bloklarni detallarga ajratish: blok o'qi ota o'qiga teng va propil bir xil bo'lsa —
    detallar ota tugunga qo'shni bola bo'lib qo'shiladi, aks holda alohida guruh tuguni (gk) yaratiladi."""
    root = copy.deepcopy(root)
    gk = pool.gk if pool.gk is not None else kerf

    def units(leaf: "_N", sh: "_Shape", d: str, level: int) -> list["_N"]:
        ux, uy = (sh.uw, sh.ul) if leaf.rot else (sh.ul, sh.uw)
        pid = leaf.pid
        if pid is None:
            q = queues.get(leaf.s)
            pid = q.popleft() if q else ("?", 0)
        out, pos = [], (leaf.x if d == "x" else leaf.y)
        for _i in range(sh.k):
            if d == "x":
                u = _N(pos, leaf.y, ux, leaf.w, level, "P", s=-1, rot=leaf.rot)
                pos += ux + gk
            else:
                u = _N(leaf.x, pos, leaf.l, uy, level, "P", s=-1, rot=leaf.rot)
                pos += uy + gk
            u.pid = pid
            out.append(u)
        return out

    def walk(n: "_N") -> None:
        if n.kind != "C":
            return
        kids: list[_N] = []
        for c in n.children:
            if c.kind == "P" and 0 <= c.s < len(pool.shapes) and pool.shapes[c.s].k > 1:
                sh = pool.shapes[c.s]
                d = _stack_axis(sh, c.rot)
                if d == n.axis and not pool.gk_differs:
                    kids += units(c, sh, d, c.level)
                else:
                    g = _N(c.x, c.y, c.l, c.w, c.level, "C", axis=d, children=units(c, sh, d, c.level + 1))
                    g.gk = gk if pool.gk_differs else None
                    kids.append(g)
            else:
                walk(c)
                kids.append(c)
        n.children = kids
    walk(root)
    return root


def _partition(n: int, kmin: int, kmax: int) -> list[int]:
    """n ta detalni bloklarga bo'lish: har blok kmin..kmax; bo'lmasa qolgani yakka detal (1)."""
    kmin = max(2, kmin)
    kmax = n if kmax <= 0 else kmax
    if n < kmin or kmax < kmin:
        return [1] * n
    b = math.ceil(n / kmax)
    if n // b >= kmin:
        base, extra = divmod(n, b)
        return [base + 1] * extra + [base] * (b - extra)
    full = n // kmax
    return [kmax] * full + [1] * (n - full * kmax)


def group_items(items: list[Item], groups: dict[str, tuple[int, int, str]], stock: list[StockSheet],
                cut: CSCutParams) -> list[Item]:
    """«Группировка» — bir detalning nusxalarini bloklarga birlashtirish (blok listga sig'ishi kerak).
    groups: part_id → (min, max, 'l' | 'w')."""
    if not groups:
        return items
    gk = group_kerf(cut)
    zones = [z for z in (_zone(st, cut) for st in stock) if z.UL > 0 and z.UW > 0]
    plenty = [z for z in zones if z.stock.qty >= 10000]      # cheklanmagan listlar bo'lsa — blok ularga sig'sin
    if plenty:
        zones = plenty
    by_pid: dict[str, list[Item]] = {}
    out: list[Item] = []
    for it in items:
        if it.part_id in groups and it.k == 1:
            by_pid.setdefault(it.part_id, []).append(it)
        else:
            out.append(it)
    for pid, its in by_pid.items():
        kmin, kmax, ax = groups[pid]
        f = its[0]

        def dims(k: int) -> tuple[float, float]:
            return (k * f.l + (k - 1) * gk, f.w) if ax == "l" else (f.l, k * f.w + (k - 1) * gk)

        def fits(k: int) -> bool:
            bl, bw = dims(k)
            return any((bl <= z.UL + EPS and bw <= z.UW + EPS) or
                       (f.can_rotate and bw <= z.UL + EPS and bl <= z.UW + EPS) for z in zones)
        kfit = 1
        for k in range(2, len(its) + 1):
            if kmax and k > kmax:
                break
            if not fits(k):
                break
            kfit = k
        i = 0
        for k in _partition(len(its), kmin, kfit if kfit >= 2 else 1):
            if k == 1:
                out.append(its[i])
            else:
                bl, bw = dims(k)
                out.append(Item(pid, f.uid, bl, bw, f.can_rotate, k=k, gl=(ax == "l"), ul=f.l, uw=f.w))
            i += k
    return out


def _fits(extent: float, size: float, min_trim: float, margin: float = 0.0) -> bool:
    """size shu extent ga sig'adimi: aynan teng yoki qolgan qism ≥ minimal obrezka.
    margin — hudud uzoq cheti list cheti bo'lsa, undan keyingi torsovka zapasi (jismoniy qirindiga qo'shiladi)."""
    rest = extent - size
    if rest < -EPS:
        return False
    return rest <= EPS or rest + margin >= min_trim - EPS


def _candidates(pool: _Pool, counts: list[int], R: float, C: float, axis: str, level: int,
                cfg: _Cfg, used: set, far_a: float = 0.0, far_c: float = 0.0) -> dict[float, list]:
    """Keyingi bola uchun o'lchamlar: {a: [aniq mos bormi, eng katta ko'ndalang b, eng katta maydon]}."""
    out: dict[float, list] = {}
    mt = cfg.min_trim - EPS
    lst = pool.ori[axis]
    i = bisect_left(pool.neg[axis], -R - EPS)
    limit = cfg.max_types and len(used) >= cfg.max_types
    shapes = pool.shapes
    mins, maxs = cfg.min_strip_w, cfg.max_strip_w
    for j in range(i, len(lst)):
        a, b, si, _r = lst[j]
        if counts[si] <= 0:
            continue
        ra = R - a
        if ra > EPS and ra + far_a < mt:
            continue
        rb = C - b
        if rb < -EPS or (rb > EPS and rb + far_c < mt):
            continue
        if limit and si not in used:
            continue
        if level == 1 and ((mins and a < mins - EPS) or (maxs and a > maxs + EPS)):
            continue
        e = out.get(a)
        exact = rb <= EPS
        if e is None:
            out[a] = [exact, b, shapes[si].area]
        else:
            if exact:
                e[0] = True
            if b > e[1]:
                e[1] = b
            ar = shapes[si].area
            if ar > e[2]:
                e[2] = ar
    return out


def _exact(pool: _Pool, counts, a, b, axis, cfg: _Cfg, used):
    lst = pool.exact[axis].get((_r3(a), _r3(b)))
    if not lst:
        return None
    limit = cfg.max_types and len(used) >= cfg.max_types
    for si, r in lst:
        if counts[si] > 0 and (not limit or si in used):
            return si, r
    return None


def _make_child(pool: _Pool, counts, used, cfg: _Cfg, x0, y0, pos, s, C, axis, level, allow_container=True,
                far_c: float = 0.0):
    """Ota tugunning `axis` o'qi bo'yicha pos nuqtasidan s o'lchamli bola yasaydi.
    allow_container=False — bola butun hududni egallaydi: faqat aniq detal bo'lishi mumkin."""
    if axis == "x":
        cx, cy, cl, cw = x0 + pos, y0, s, C
    else:
        cx, cy, cl, cw = x0, y0 + pos, C, s
    ex = _exact(pool, counts, s, C, axis, cfg, used)
    if ex is not None:
        si, r = ex
        counts[si] -= 1
        used.add(si)
        return _N(cx, cy, cl, cw, level, "P", s=si, rot=r), cl * cw
    if not allow_container or level > cfg.max_level:
        return None, 0.0          # level > max_level: konteyner (ichki kesim) kerak, lekin burilishlar chegarasi yetmaydi
    if level >= cfg.max_level:
        # oxirgi konteyner darajasi: ichidagi detallar (keyingi, eng oxirgi daraja) ko'ndalang bo'yicha aniq mos
        # bo'lishi shart — ularni chiqindidan ajratish uchun yana bir burilish kerak bo'lmasin
        kids, area = _fill_exact(pool, counts, used, cfg, cx, cy, cl, cw, _other(axis), level + 1, far_c)
    else:
        kids, area = _fill(pool, counts, used, cfg, cx, cy, cl, cw, _other(axis), level + 1, 0.0, far_c, 0.0)
    if not kids or area <= 0:
        return None, 0.0
    return _N(cx, cy, cl, cw, level, "C", axis=_other(axis), children=kids), area


def _fill_exact(pool: _Pool, counts, used, cfg: _Cfg, x0, y0, L, W, axis, level, far_a: float = 0.0):
    """Eng oxirgi daraja: hududni `axis` bo'ylab faqat ko'ndalang o'lchami hududga AYNAN teng detallar bilan
    to'ldirish (har biri bitta kesim bilan ajraladi). Ketma-ketlik — qolgan joyga sig'adigan eng kattasi
    (qolgan tilim minimal obrezka qoidasini buzmasin). Qaytaradi: (bolalar — oxirida chiqindi bilan, maydon)."""
    E, C = (L, W) if axis == "x" else (W, L)
    lst = pool.cross[axis].get(_r3(C))
    if not lst:
        return [], 0.0
    kerf, mt = cfg.kerf, cfg.min_trim - EPS
    blocks = pool.has_blocks
    kids: list[_N] = []
    area = 0.0
    pos = 0.0
    while True:
        R = E - pos
        if R <= EPS:
            break
        pick = None
        limit = cfg.max_types and len(used) >= cfg.max_types
        for (a, si, r) in lst:
            if a > R + EPS or counts[si] <= 0 or (limit and si not in used):
                continue
            if blocks and pool.shapes[si].k > 1 and (pool.gk_differs or _stack_axis(pool.shapes[si], r) != axis):
                continue          # blok shu o'q bo'ylab bo'linmasa — qo'shimcha daraja kerak bo'lardi
            ra = R - a
            if ra > EPS and ra + far_a < mt:
                continue          # ortidan minimal obrezkadan yupqa tilim qoladi
            pick = (a, si, r)
            break
        if pick is None:
            break
        a, si, r = pick
        counts[si] -= 1
        used.add(si)
        if axis == "x":
            kids.append(_N(x0 + pos, y0, a, W, level, "P", s=si, rot=r))
        else:
            kids.append(_N(x0, y0 + pos, L, a, level, "P", s=si, rot=r))
        area += a * C
        pos += a + kerf
    if kids and E - pos > EPS:
        if axis == "x":
            kids.append(_N(x0 + pos, y0, E - pos, W, level, "W"))
        else:
            kids.append(_N(x0, y0 + pos, L, E - pos, level, "W"))
    return kids, area


def _used_extent(node: _N, axis: str) -> float:
    start = node.x if axis == "x" else node.y
    far = start
    for lf in node.leaves():
        if lf.kind == "P":
            f = (lf.x + lf.l) if axis == "x" else (lf.y + lf.w)
            if f > far:
                far = f
    return far - start


def _shrink_size(node: _N, axis: str, R: float, min_trim: float) -> float:
    """Kompozit bolaning yangi o'lchami: ichidagi eng uzun qator (+ kerak bo'lsa minimal obrezka)."""
    u = _used_extent(node, axis)
    if u <= EPS:
        return 0.0
    ok = True
    for ch in node.children:
        if ch.kind == "W":
            continue
        rest = u - _used_extent(ch, axis)
        if EPS < rest < min_trim - EPS:
            ok = False
            break
    return min(u if ok else u + min_trim, R)


def _fill(pool: _Pool, counts, used, cfg: _Cfg, x0, y0, L, W, axis, level, start: float = 0.0,
          far_a: float = 0.0, far_c: float = 0.0):
    """(x0,y0,L,W) hududini `axis` bo'ylab bolalar bilan to'ldiradi (start nuqtadan).
    far_a / far_c — hudud uzoq cheti (o'q bo'yicha / ko'ndalang) list cheti bo'lsa torsovka zapasi.
    counts/used o'zgaradi. Qaytaradi: (bolalar — oxirida chiqindi bilan, detallar maydoni)."""
    E, C = (L, W) if axis == "x" else (W, L)
    kids: list[_N] = []
    area = 0.0
    pos = start
    k = cfg.look[level - 1] if level - 1 < len(cfg.look) else 1
    kerf = cfg.kerf
    while True:
        R = E - pos
        if R <= EPS:
            break
        cands = _candidates(pool, counts, R, C, axis, level, cfg, used, far_a, far_c)
        if not cands:
            break
        if level == 1 and cfg.mode == "area":
            order = sorted(cands.items(), key=lambda kv: (kv[1][0], kv[0], kv[1][2]), reverse=True)
        elif level == 1:
            order = sorted(cands.items(), key=lambda kv: (kv[1][0], kv[0], kv[1][2]), reverse=True)
            if len(order) > k >= 3:   # kichik o'lchamlarni ham sinaymiz
                q = k // 3
                order = order[: k - q] + order[-q:] + order[k - q: -q]
        else:
            order = sorted(cands.items(), key=lambda kv: (kv[1][0], round(kv[1][1] / C, 3), kv[0]), reverse=True)
        if cfg.rng is not None and cfg.noise > 0 and len(order) > 1:
            rng, nz = cfg.rng, cfg.noise
            order = [kv for _r, kv in sorted(((i + rng.gauss(0.0, nz), kv) for i, kv in enumerate(order)),
                                             key=lambda t: t[0])]
        if cfg.composite and level < cfg.max_level and k > 1:
            order.append((R, None))
        best = None
        ok = 0
        for s, info in order:
            if ok >= k and info is not None:
                break
            cfg.budget[0] += 1
            if info is None:
                # kompozit: avval butun qolgan joy bilan quriladi, so'ng eng uzun qatorga qisqartiriladi
                pc, pu = counts[:], set(used)
                node, a = _make_child(pool, pc, pu, cfg, x0, y0, pos, s, C, axis, level, True, far_c)
                if node is None or node.kind != "C":
                    continue
                s2 = _r3(_shrink_size(node, axis, R, cfg.min_trim))
                if s2 <= EPS or (pos <= EPS and abs(s2 - E) <= EPS) or not _fits(R, s2, cfg.min_trim, far_a):
                    continue
                if s2 in cands:
                    continue          # oddiy nomzod sifatida allaqachon sinalgan
                s = s2
                c2, u2 = counts[:], set(used)
                node, a = _make_child(pool, c2, u2, cfg, x0, y0, pos, s, C, axis, level, True, far_c)
                if node is None:
                    continue
            else:
                if k == 1:
                    c2, u2 = counts, used
                else:
                    c2, u2 = counts[:], set(used)
                full = pos <= EPS and abs(s - E) <= EPS
                node, a = _make_child(pool, c2, u2, cfg, x0, y0, pos, s, C, axis, level, not full, far_c)
                if node is None:
                    continue
            ok += 1
            if k == 1:
                best = (None, node, a, c2, u2, s)
                break
            if cfg.rollout >= level:
                c3, u3 = c2[:], set(u2)
                _k, rest = _fill(pool, c3, u3, cfg.fast(), x0, y0, L, W, axis, level, pos + s + kerf, far_a, far_c)
                sc = (round(a + rest, 0), round(a / (s * C), 4) if s * C > 0 else 0, s)
            elif cfg.mode == "area":
                sc = (round(a, 1), a / (s * C) if s * C > 0 else 0)
            else:
                sc = (round(a / (s * C), 4) if s * C > 0 else 0, a)
            if best is None or sc > best[0]:
                best = (sc, node, a, c2, u2, s)
        if best is None:
            break
        _, node, a, c2, u2, s = best
        if c2 is not counts:
            counts[:] = c2
            used.clear(); used.update(u2)
        kids.append(node)
        area += a
        pos += s + kerf
    if kids and E - pos > EPS:
        if axis == "x":
            kids.append(_N(x0 + pos, y0, E - pos, W, level, "W"))
        else:
            kids.append(_N(x0, y0 + pos, L, E - pos, level, "W"))
    return kids, area


# ───────────────────────── List zonasi ─────────────────────────
@dataclass
class _Zone:
    stock: StockSheet
    L: float; W: float            # to'liq list
    ox: float; oy: float          # foydali zona boshi
    UL: float; UW: float          # foydali zona o'lchami
    trim_x: float; trim_y: float  # T buyruqlaridagi torsovka qiymatlari
    far_raw_x: bool = True        # uzoq chet (X / Y bo'yicha) — list cheti (tor qirindiga ruxsat); polosaga
    far_raw_y: bool = True        # siqilgan zonada (qoldiq yig'ish) chet ichki kesim bo'ladi


def _zone(stock: StockSheet, p: CSCutParams) -> _Zone:
    """Foydali zona: «Торцовка по длине» — yuqori chetdan, «по ширине» — chap chetdan; qarama-qarshi chetlarda
    «Минимальный отступ в конце» (bo'sh — torsovka qiymati). Har qiymatga propil qo'shiladi (torsovka propilni
    o'z ichiga olmasa); 0 — kesim yo'q, propil ham yo'q. List qatoridagi qiymatlar operatsiyanikidan ustun."""
    t_len = stock.trim_length if stock.trim_length is not None else p.trim_length
    t_wid = stock.trim_width if stock.trim_width is not None else p.trim_width
    e_bot = stock.end_offset_bottom if stock.end_offset_bottom is not None else \
        (p.end_offset_bottom if p.end_offset_bottom is not None else t_len)
    e_rgt = stock.end_offset_right if stock.end_offset_right is not None else \
        (p.end_offset_right if p.end_offset_right is not None else t_wid)
    add = 0 if p.trim_includes_kerf else p.kerf
    oy = (t_len + add) if t_len > 0 else 0.0
    ox = (t_wid + add) if t_wid > 0 else 0.0
    far_y = (e_bot + add) if e_bot > 0 else 0.0
    far_x = (e_rgt + add) if e_rgt > 0 else 0.0
    return _Zone(stock, stock.length, stock.width, ox, oy,
                 stock.length - ox - far_x, stock.width - oy - far_y, t_wid, t_len)


@dataclass
class _Sheet:
    zone: _Zone
    root: _N
    area: float
    counts_after: list[int]
    how: str = ""
    used: Optional[list[int]] = None      # shu kartaga tushgan shakllar soni
    wval: float = 0.0                     # vaznli qiymat (SVC qidiruvida)


def _largest_waste(root: _N) -> float:
    return max((n.l * n.w for n in root.leaves() if n.kind == "W"), default=0.0)


def _tree_cut_len(root: _N, z: _Zone) -> float:
    """Kesish uzunligi bahosi (mm) — faqat nomzod listlarni saralash uchun (`_sheet_key`). Rasmiy LT `_build_map` da
    (onlayn qoida, X_1015 §12: har P/C qatori sanaladi). Bu yerda chuqur tugunda chegaraga tegib turgan oxirgi bola
    sanalmaydi (jismoniy kesim yo'q) — optimizator maqsadi o'zgarmasin deb ataylab shunday qoldirilgan."""
    total = 0.0

    def walk(node: _N, depth: int):
        nonlocal total
        ax = node.axis
        clen = (z.W if ax == "x" else z.L) if depth == 0 else (node.w if ax == "x" else node.l)
        if depth <= 1 and (z.trim_y if ax == "y" else z.trim_x) > 0:
            total += clen
        body = [c for c in node.children if not (c.kind == "W" and _extent(c, ax) <= EPS)]
        for i, ch in enumerate(body):
            if ch.kind == "W":
                continue
            if not (i == len(body) - 1 and depth >= 2):
                total += clen
            if ch.kind == "C":
                walk(ch, depth + 1)
    walk(root, 0)
    return total


def _sheet_key(sh: _Sheet):
    # ko'proq detal maydoni → kattaroq qoldiq → kamroq kesish uzunligi (arra vaqti)
    return (round(sh.area, 0), round(_largest_waste(sh.root), 0), -round(_tree_cut_len(sh.root, sh.zone), 0))


RAW_EDGE = 1e9   # list cheti: minimal obrezka qoidasi qo'llanmaydi (qirindi list chetidan tushadi)


def _margins(zone: _Zone, axis: str) -> tuple[float, float]:
    """Hududning uzoq cheti list cheti bo'lganda minimal obrezka cheklovi yo'q (GibLab ham shunday):
    masalan 2069 mm detal 2070 mm listga (torsovkasiz) sig'adi. Qaytaradi (o'q bo'yicha, ko'ndalang)."""
    rx = RAW_EDGE if zone.far_raw_x else 0.0
    ry = RAW_EDGE if zone.far_raw_y else 0.0
    return (rx, ry) if axis == "x" else (ry, rx)


def _pack_tree(pool: _Pool, counts, zone: _Zone, axis: str, cfg: _Cfg) -> Optional[_Sheet]:
    c = counts[:]
    used: set = set()
    fa, fc = _margins(zone, axis)
    kids, area = _fill(pool, c, used, cfg, 0.0, 0.0, zone.UL, zone.UW, axis, 1, 0.0, fa, fc)
    if not kids or area <= 0:
        return None
    root = _N(0.0, 0.0, zone.UL, zone.UW, 0, "C", axis=axis, children=kids)
    return _Sheet(zone, root, area, c)


# ───────────────────────── 2-oila: detalga yo'naltirilgan gilyotina ─────────────────────────
def _gfree_pack(pool: _Pool, counts, zone: _Zone, cfg: _Cfg, order_key: str, fit: str, split: str):
    """Har detal eng mos bo'sh to'rtburchakka; qolgan L-shakl ikki gilyotina kesimi bilan bo'linadi.
    Natija — ikkilik kesish daraxti, so'ng darajali daraxtga aylantiriladi."""
    kerf, mt = cfg.kerf, cfg.min_trim
    mx, my = _margins(zone, "x")
    c = counts[:]
    root = _N(0.0, 0.0, zone.UL, zone.UW, 0, "W")
    free: list[_N] = [root]
    keyf = {
        "area": lambda s: (s.area, max(s.l, s.w)),
        "long": lambda s: (max(s.l, s.w), s.area),
        "short": lambda s: (min(s.l, s.w), s.area),
        "perim": lambda s: (s.l + s.w, s.area),
    }[order_key]
    seq = []
    for s in sorted(pool.shapes, key=keyf, reverse=True):
        seq += [s] * c[s.idx]
    area = 0.0
    used: set = set()
    for s in seq:
        if cfg.max_types and len(used) >= cfg.max_types and s.idx not in used:
            continue
        orients = [(s.l, s.w, False)]
        if s.rot and abs(s.l - s.w) > EPS:
            orients.append((s.w, s.l, True))
        best = None
        for fi, f in enumerate(free):
            fmx = mx if f.x + f.l >= zone.UL - EPS else 0.0
            fmy = my if f.y + f.w >= zone.UW - EPS else 0.0
            for (ox, oy, r) in orients:
                if not (_fits(f.l, ox, mt, fmx) and _fits(f.w, oy, mt, fmy)):
                    continue
                dl, dw = f.l - ox, f.w - oy
                if fit == "bssf":
                    sc = (min(dl, dw), max(dl, dw))
                elif fit == "blsf":
                    sc = (max(dl, dw), min(dl, dw))
                else:
                    sc = (f.l * f.w - ox * oy, min(dl, dw))
                if best is None or sc < best[0]:
                    best = (sc, fi, ox, oy, r)
        if best is None:
            continue
        _sc, fi, ox, oy, r = best
        n = free.pop(fi)
        c[s.idx] -= 1
        used.add(s.idx)
        area += ox * oy
        dl, dw = n.l - ox, n.w - oy
        if split == "sas":
            vertical = dl < dw
        elif split == "las":
            vertical = dl >= dw
        elif split == "maxa":
            vertical = (dl * n.w) >= (dw * n.l)
        else:
            vertical = (dl * n.w) < (dw * n.l)
        part = _N(n.x, n.y, ox, oy, 0, "P", s=s.idx, rot=r)
        if vertical:
            n.kind, n.axis = "C", "x"
            sub = _N(n.x, n.y, ox, n.w, 0, "C", axis="y", children=[part])
            n.children = [sub]
            if dw - kerf > EPS:
                lw = _N(n.x, n.y + oy + kerf, ox, dw - kerf, 0, "W")
                sub.children.append(lw); free.append(lw)
            if dl - kerf > EPS:
                rw = _N(n.x + ox + kerf, n.y, dl - kerf, n.w, 0, "W")
                n.children.append(rw); free.append(rw)
        else:
            n.kind, n.axis = "C", "y"
            sub = _N(n.x, n.y, n.l, oy, 0, "C", axis="x", children=[part])
            n.children = [sub]
            if dl - kerf > EPS:
                tw = _N(n.x + ox + kerf, n.y, dl - kerf, oy, 0, "W")
                sub.children.append(tw); free.append(tw)
            if dw - kerf > EPS:
                bw = _N(n.x, n.y + oy + kerf, n.l, dw - kerf, 0, "W")
                n.children.append(bw); free.append(bw)
    if area <= 0:
        return None
    lroot = _normalize(root)
    if lroot is None or _depth(lroot) > cfg.max_level + 1:
        return None
    return _Sheet(zone, lroot, area, c)


def _normalize(n: _N) -> Optional[_N]:
    """Ikkilik gilyotina daraxtini darajali daraxtga aylantiradi."""
    def same(a: _N, b: _N) -> bool:
        return abs(a.x - b.x) <= EPS and abs(a.y - b.y) <= EPS and abs(a.l - b.l) <= EPS and abs(a.w - b.w) <= EPS

    def flat(node: _N) -> _N:
        if node.kind != "C":
            return node
        kids = []
        for ch in node.children:
            ch = flat(ch)
            # bitta bolali tugun faqat bola uni to'liq egallasa qisqartiriladi (aks holda torsovka kesimi yo'qoladi)
            if ch.kind == "C" and len(ch.children) == 1 and same(ch, ch.children[0]):
                ch = ch.children[0]
            if ch.kind == "C" and ch.axis == node.axis and ch.gk is None and node.gk is None:
                kids.extend(ch.children)
            else:
                kids.append(ch)
        node.children = [k for k in kids if not (k.kind == "W" and (k.l <= EPS or k.w <= EPS))]
        if len(node.children) == 1 and node.children[0].kind == "C" and same(node, node.children[0]):
            return node.children[0]
        return node
    r = flat(n)
    if r.kind != "C":
        r = _N(n.x, n.y, n.l, n.w, 0, "C", axis="y", children=[r])

    def fix(node: _N, level: int):
        node.level = level
        if node.kind == "C":
            merged: list[_N] = []
            for ch in sorted(node.children, key=lambda c: c.x if node.axis == "x" else c.y):
                if merged and ch.kind == "W" and merged[-1].kind == "W":
                    a = merged[-1]
                    if node.axis == "x":
                        a.l = ch.x + ch.l - a.x
                    else:
                        a.w = ch.y + ch.w - a.y
                    continue
                merged.append(ch)
            node.children = merged
            for ch in merged:
                fix(ch, level + 1)
    fix(r, 0)
    return r


def _depth(n: _N) -> int:
    if n.kind != "C":
        return n.level
    return max((_depth(c) for c in n.children), default=n.level)


GFREE = [(o, f, s) for o in ("area", "long", "perim") for f in ("bssf", "baf")
         for s in ("sas", "las", "maxa", "mina")]

# ───────────────────────── 3-oila: polosali 3 bosqichli (eski algoritm, daraxtga aylantiriladi) ─────────────────────────
def _legacy_sheet(pool: _Pool, counts, zone: _Zone, p: CSCutParams, axis: str) -> Optional[_Sheet]:
    """Boshlang'ich backenddagi 3 bosqichli polosa algoritmi (bir necha tartib × rejim) → kesish daraxti.
    Minimal obrezka buzilgan joylashuvlar rad etiladi."""
    from . import optimizer_legacy as lg
    transposed = axis == "x"          # lg polosalarni Y bo'ylab qo'yadi; x o'qi uchun transpozitsiya
    UL, UW = (zone.UW, zone.UL) if transposed else (zone.UL, zone.UW)
    items = []
    for sh in pool.shapes:
        n = counts[sh.idx]
        if n > 0:
            l, w = (sh.w, sh.l) if transposed else (sh.l, sh.w)
            items += [lg.Item(str(sh.idx), sh.idx, l, w, sh.rot)] * n
    if not items:
        return None
    best = None
    for mode in ("fill", "area", "ffd"):
        for key in lg.SORT_KEYS:
            trial = lg._sort_items(items, key)
            lay = lg._SheetLayout(zone.stock, UL, UW, 0.0, 0.0, UL, UW, False)
            lg._pack_sheet(lay, trial, p, mode)
            placed = sum(pc.l * pc.w for pc in lay.pieces)
            if placed > 0 and (best is None or placed > best[0] + 1e-6):
                best = (placed, lay)
    if best is None:
        return None
    lay = best[1]
    kerf, mt = p.kerf, p.min_trim_cut

    def tail(node: _N, extent_end: float) -> None:
        ax = node.axis
        end = 0.0
        for c in node.children:
            end = max(end, (c.x + c.l) if ax == "x" else (c.y + c.w))
        start = end + kerf
        if extent_end - start > EPS:
            if ax == "x":
                node.children.append(_N(start, node.y, extent_end - start, node.w, 0, "W"))
            else:
                node.children.append(_N(node.x, start, node.l, extent_end - start, 0, "W"))

    root = _N(0.0, 0.0, UL, UW, 0, "C", axis="y")
    c = counts[:]
    for st in lay.strips:
        strip = _N(0.0, st.y, UL, st.height, 1, "C", axis="x")
        for col in st.columns:
            if len(col.pieces) == 1 and abs(col.pieces[0].w - st.height) <= EPS and abs(col.pieces[0].l - col.width) <= EPS:
                pc = col.pieces[0]
                strip.children.append(_N(pc.x, pc.y, pc.l, pc.w, 2, "P", s=int(pc.item.part_id), rot=pc.rotated))
                continue
            cn = _N(col.x, st.y, col.width, st.height, 2, "C", axis="y")
            for pc in col.pieces:
                leaf = _N(pc.x, pc.y, pc.l, pc.w, 3, "P", s=int(pc.item.part_id), rot=pc.rotated)
                if pc.l < col.width - EPS:
                    wrap = _N(col.x, pc.y, col.width, pc.w, 3, "C", axis="x", children=[leaf])
                    tail(wrap, col.x + col.width)
                    cn.children.append(wrap)
                else:
                    cn.children.append(leaf)
            tail(cn, st.y + st.height)
            strip.children.append(cn)
        tail(strip, UL)
        root.children.append(strip)
    tail(root, UW)
    for lf in root.leaves():
        if lf.kind == "P":
            c[lf.s] -= 1
    if transposed:
        _transpose(root)
    root.x, root.y, root.l, root.w = 0.0, 0.0, zone.UL, zone.UW
    if _trim_violations(root, zone, mt):
        return None
    area = sum(lf.l * lf.w for lf in root.leaves() if lf.kind == "P")
    return _Sheet(zone, root, area, c)


# ───────────────────────── 4-oila: ustunli joylash (ustun ichi — aniq ryukzak) ─────────────────────────
def _col_packer(pool: _Pool, zone: _Zone, p: CSCutParams, axis: str, weights=None, stacks: bool = False):
    from .colpack import ColPacker
    return ColPacker(pool.shapes, zone.UL, zone.UW, p.kerf, p.min_trim_cut, p.max_rotations, axis == "y",
                     p.min_strip_width, p.max_strip_width, weights, stacks,
                     edge_ok=zone.far_raw_y if axis == "y" else zone.far_raw_x)


def _col_sheet(pool: _Pool, counts, zone: _Zone, p: CSCutParams, axis: str, look: int,
               mode: str = "greedy", weights=None, packer=None, deadline: Optional[float] = None) -> Optional[_Sheet]:
    """colpack.ColPacker natijasini kesish daraxtiga aylantirish. axis='x' — ustunlar X bo'ylab,
    axis='y' — polosalar Y bo'ylab (masala transpozitsiya qilinadi)."""
    tr = axis == "y"
    cp = packer if packer is not None else _col_packer(pool, zone, p, axis, weights)
    if mode == "dfs":
        end = time.monotonic() + look * 0.1
        out = cp.pack_dfs(counts, end if deadline is None else min(end, deadline))
    else:
        out = cp.pack(counts, look, mode, deadline)
    if out is None:
        return None
    cols, wval, c = out
    kerf, E, C = p.kerf, cp.E, cp.C
    root = _N(0.0, 0.0, E, C, 0, "C", axis="x")
    x_end = 0.0
    for (x, w, rows) in cols:
        col = _N(x, 0.0, w, C, 1, "C", axis="y")
        inst = []
        for r in rows:
            inst += [r] * r.t
        inst.sort(key=lambda r: (-r.h, -r.area))
        y = 0.0
        for r in inst:
            h = r.h
            cells = r.cells
            c0 = cells[0][0]
            if len(cells) == 1 and len(cells[0]) == 1 and abs(c0[2] - w) <= EPS and abs(c0[1] - h) <= EPS:
                col.children.append(_N(x, y, w, h, 2, "P", s=c0[0], rot=c0[3]))
            else:
                row = _N(x, y, w, h, 2, "C", axis="x")
                pos = x
                for cell in cells:
                    b = cell[0][2]
                    if len(cell) == 1 and abs(cell[0][1] - h) <= EPS:
                        row.children.append(_N(pos, y, b, h, 3, "P", s=cell[0][0], rot=cell[0][3]))
                    else:
                        # katakcha: detallar ustma-ust (yoki qatordan past bitta detal) — 4-daraja kesimlar
                        cnode = _N(pos, y, b, h, 3, "C", axis="y")
                        yy = y
                        for (si, a, _bb, rot) in cell:
                            cnode.children.append(_N(pos, yy, b, a, 4, "P", s=si, rot=rot))
                            yy += a + kerf
                        if y + h - yy > EPS:
                            cnode.children.append(_N(pos, yy, b, y + h - yy, 4, "W"))
                        row.children.append(cnode)
                    pos += b + kerf
                if x + w - pos > EPS:
                    row.children.append(_N(pos, y, x + w - pos, h, 3, "W"))
                col.children.append(row)
            y += h + kerf
        if C - y > EPS:
            col.children.append(_N(x, y, w, C - y, 2, "W"))
        root.children.append(col)
        x_end = x + w + kerf
    if E - x_end > EPS:
        root.children.append(_N(x_end, 0.0, E - x_end, C, 1, "W"))
    if tr:
        _transpose(root)
    root.x, root.y, root.l, root.w = 0.0, 0.0, zone.UL, zone.UW
    area = sum(lf.l * lf.w for lf in root.leaves() if lf.kind == "P")
    sh = _Sheet(zone, root, area, c)
    sh.wval = wval
    return sh


def _transpose(n: _N) -> None:
    n.x, n.y, n.l, n.w = n.y, n.x, n.w, n.l
    if n.axis:
        n.axis = _other(n.axis)
    # detal aylanishi o'zgarmaydi: qatlam fazosida element allaqachon transpozitsiya qilingan
    for c in n.children:
        _transpose(c)


def _trim_violations(root: _N, zone: _Zone, mt: float) -> int:
    """Ichki kesimlarda minimal obrezkadan kichik qirindi qolgan joylar soni (list chetlari hisobga olinmaydi)."""
    bad = 0

    def walk(n: _N):
        nonlocal bad
        if n.kind != "C":
            return
        ax = n.axis
        end = (n.x + n.l) if ax == "x" else (n.y + n.w)
        raw = end >= ((zone.UL if ax == "x" else zone.UW) - EPS) and (zone.far_raw_x if ax == "x" else zone.far_raw_y)
        body = [c for c in n.children if c.kind != "W"]
        if body and not raw:
            last = max(((c.x + c.l) if ax == "x" else (c.y + c.w)) for c in body)
            rest = end - last
            if EPS < rest < mt - EPS:
                bad += 1
        for c in n.children:
            walk(c)
    walk(root)
    return bad


LEGACY_MAX_ITEMS = 200
RANDOM_MAX_PARTS = 40       # «hammasi bitta listga sig'sin» tasodifiy qidiruvi — kichik to'plamlar uchun
RANDOM_TRIES = 400

# (rejim, har darajadagi nomzodlar soni, pilot chuqurligi, kompozit) — arzonidan qimmatiga
STRATEGIES = (
    ("eff", (4, 1, 1), 0, True),
    ("eff", (8, 3, 1), 1, True),
    ("eff", (6, 4, 2), 2, True),
    ("area", (6, 3, 2), 0, True),
)
# vaqt yetsa (kichik buyurtmalar, oxirgi listlar) qo'shimcha sinaladigan chuqurroq qidiruv
INTENSIVE = (
    ("eff", (8, 4, 2), 0, True),
    ("eff", (6, 3, 1), 2, True),
    ("eff", (8, 4, 2), 1, True),
    ("eff", (10, 5, 3), 2, True),
    ("eff", (6, 4, 2), 2, False),
    ("area", (8, 4, 2), 1, True),
    ("eff", (12, 6, 3, 2), 1, True),
    ("eff", (10, 5, 3), 0, False),
    ("area", (10, 5, 3), 2, True),
    ("eff", (16, 8, 4, 2), 2, True),
)
GFREE_ALL = [(o, f, s) for o in ("area", "long", "short", "perim") for f in ("bssf", "baf", "blsf")
             for s in ("sas", "las", "maxa", "mina")]
GFREE_TOP = [("area", "bssf", "las"), ("area", "bssf", "sas"), ("area", "bssf", "maxa"), ("long", "bssf", "las")]


def _axes_for(p: CSCutParams) -> list[str]:
    # 'y' — polosalar Y bo'ylab (1-kesishlar uzunlik bo'ylab), 'x' — polosalar X bo'ylab
    return {
        FirstCutDir.ANY: ["y", "x"],
        FirstCutDir.LENGTH: ["y"],
        FirstCutDir.WIDTH: ["x"],
        FirstCutDir.LENGTH_PREF: ["y", "x"],
        FirstCutDir.WIDTH_PREF: ["x", "y"],
    }[p.first_cut]


def _best_sheet(pool: _Pool, counts, zone: _Zone, p: CSCutParams, axes: list[str], deadline: float,
                cheap_only: bool = False, intensive: bool = False, target_all: bool = False,
                collect: Optional[list] = None, deep: bool = False) -> Optional[_Sheet]:
    """Bitta list uchun eng yaxshi joylashuv. Strategiyalar arzonidan qimmatiga, vaqt tugaguncha.
    target_all — hammasi sig'ishi kerak (topilishi bilan to'xtaydi)."""
    best: Optional[_Sheet] = None
    # max_level — oxirgi KONTEYNER darajasi (detallar undan bir daraja pastda, ya'ni ≤ max_rotations)
    base = dict(kerf=p.kerf, min_trim=p.min_trim_cut, max_level=max(1, p.max_rotations) - 1,
                min_strip_w=p.min_strip_width, max_strip_w=p.max_strip_width, max_types=p.max_part_types_per_map)
    need = sum(counts)
    # Qat'iy muddat: «hammasi sig'sin» (target_all) qidiruvi muddatdan biroz oshishi mumkin, lekin cheksiz emas;
    # kamida bitta nomzod (birinchi strategiya) har doim quriladi.
    t_start = time.monotonic()
    hard = deadline + (min(1.0, max(0.1, 0.5 * (deadline - t_start))) if target_all else 0.0)

    def late() -> bool:
        return best is not None and time.monotonic() > hard

    def consider(sh: Optional[_Sheet], how: str) -> bool:
        nonlocal best
        if sh is None or sh.area <= 0:
            return False
        if not _depth_ok(sh.root, pool, p.max_rotations):
            return False
        sh.how = how
        if collect is not None:
            collect.append(sh)
        if best is None or _sheet_key(sh) > _sheet_key(best):
            best = sh
        return target_all and sum(sh.counts_after) == 0

    def tree(cfgs) -> bool:
        for n, (mode, look, roll, comp) in enumerate(cfgs):
            if best is not None and (cheap_only or time.monotonic() > deadline):
                return False
            for axis in axes:
                if p.max_strip_length:
                    cross = zone.UL if axis == "y" else zone.UW
                    if cross > p.max_strip_length + EPS and len(axes) > 1:
                        continue
                cfg = _Cfg(mode=mode, look=look, rollout=roll, composite=comp and p.complex_strips, **base)
                if consider(_pack_tree(pool, counts, zone, axis, cfg), f"tree:{mode}{look}{roll}{'c' if comp else ''}{axis}"):
                    return True
        return False

    def gfree(variants) -> bool:
        cfg = _Cfg(**base)
        for (o, f, sp) in variants:
            if late() or (best is not None and time.monotonic() > deadline and not target_all):
                return False
            sh = _gfree_pack(pool, counts, zone, cfg, o, f, sp)
            if sh is not None and (sh.root.axis in axes or len(axes) > 1):
                if consider(sh, f"gfree:{o}-{f}-{sp}"):
                    return True
        return False

    def legacy() -> bool:
        if need > LEGACY_MAX_ITEMS or (cheap_only and best is not None) or p.max_rotations < 2:
            return False               # O(n²) — katta hovuzda juda sekin; hovuz kichrayganda ishlaydi
                                       # (burilish 1 da: polosa → bo'lak daraxti baribir chuqurroq — rad etilardi)
        for axis in axes:
            if late():
                return False
            try:
                sh = _legacy_sheet(pool, counts, zone, p, axis)
            except Exception:  # noqa: BLE001
                sh = None
            if consider(sh, f"strip3:{axis}"):
                return True
        return False

    def col(looks) -> bool:
        if p.max_part_types_per_map or not p.complex_strips or p.max_rotations < 2:
            return False                   # ustunli oila turlar sonini / oddiy polosalarni cheklamaydi; burilish 1 da chuqurroq
        for axis in axes:
            if p.max_strip_length:
                cross = zone.UL if axis == "y" else zone.UW
                if cross > p.max_strip_length + EPS and len(axes) > 1:
                    continue
            for look in looks:
                if late() or (best is not None and time.monotonic() > deadline and not target_all):
                    return False
                mode = "knap" if look == 0 else "greedy"
                if consider(_col_sheet(pool, counts, zone, p, axis, look, mode, deadline=hard), f"col:{axis}{look}"):
                    return True
        return False

    def col_weighted(iters: int) -> bool:
        """Sig'may qolgan detallar vaznini oshirib ustunli joylashni takrorlash (bitta list uchun «qiymat
        tuzatish»): uzun / noqulay detallar keng ustunlarga oldinroq olinadi."""
        if p.max_part_types_per_map or not p.complex_strips or p.max_rotations < 2:
            return False
        wts = [1.0] * len(pool.shapes)
        packers = None
        for _it in range(iters):
            if time.monotonic() > deadline:
                return False
            packers = {axis: _col_packer(pool, zone, p, axis, wts, stacks=True) for axis in axes}
            left = None
            for axis in axes:
                for look, mode in ((3, "greedy"), (0, "knap")):
                    if time.monotonic() > deadline:
                        return False
                    sh = _col_sheet(pool, counts, zone, p, axis, look, mode, wts, packers[axis], deadline=deadline)
                    if consider(sh, f"colw:{axis}{mode}"):
                        return True
                    if sh is not None and (left is None or sum(sh.counts_after) < sum(left)):
                        left = sh.counts_after
            if left is None or sum(left) == 0:
                return False
            for i, k in enumerate(left):
                if k > 0:
                    wts[i] *= 1.6
        return False

    def col_dfs() -> bool:
        """Ustunli qidiruv (chuqurlik bo'yicha) — hammasi bitta listga sig'adigan ustunlar ketma-ketligi."""
        if p.max_part_types_per_map or not p.complex_strips or p.max_rotations < 2:
            return False
        for axis in axes:
            left = deadline - time.monotonic()
            if left <= 0:
                return False
            sh = _col_sheet(pool, counts, zone, p, axis, max(1, int(left * 10 / max(1, len(axes)))), "dfs",
                            packer=_col_packer(pool, zone, p, axis, stacks=True), deadline=deadline)
            if consider(sh, f"coldfs:{axis}"):
                return True
        return False

    def randomized() -> bool:
        """Kichik to'plamni bitta listga sig'dirish: daraxt usuli tasodifiy nomzod tartibi bilan qayta-qayta
        (takrorlanuvchi urug'), vaqt tugaguncha yoki hammasi sig'guncha."""
        rng = random.Random(1000003 * need + len(pool.shapes))
        tries = 0
        while time.monotonic() < deadline and tries < RANDOM_TRIES:
            tries += 1
            axis = rng.choice(axes)
            cfg = _Cfg(mode=rng.choice(("eff", "eff", "area")),
                       look=(rng.choice((2, 3, 4, 6)), rng.choice((1, 2, 3)), rng.choice((1, 2))),
                       rollout=rng.choice((0, 0, 1)), composite=p.complex_strips, rng=rng,
                       noise=rng.uniform(0.3, 1.5), **base)
            if consider(_pack_tree(pool, counts, zone, axis, cfg), f"rand:{axis}{tries}"):
                return True
        return False

    if tree(STRATEGIES[:1]) or col((3, 0)) or gfree(GFREE_TOP if cheap_only else GFREE) or legacy() \
            or tree(STRATEGIES[1:]):
        return best
    if (intensive or target_all) and need > 0:
        if col((1, 8)) or tree(INTENSIVE) or gfree([v for v in GFREE_ALL if v not in GFREE]):
            return best
        # chuqur qidiruv (vaqt tugaguncha) — faqat bir martalik joylarda (oxirgi list, «tail» tuzatish);
        # ko'p marta chaqiriladigan qidiruvlar (bin completion, SVC) uni ishlatmaydi
        if deep and target_all and need <= RANDOM_MAX_PARTS and (col_weighted(12) or col_dfs() or randomized()):
            return best
    return best


# ───────────────────────── Polosalarni saralash ─────────────────────────
def _extent(n: _N, axis: str) -> float:
    return n.l if axis == "x" else n.w


def _reorder(node: _N, mode: StripSort, kerf: float) -> None:
    """Tugun bolalarini (oxirgi chiqindidan tashqari) o'q bo'yicha qayta tartiblaydi."""
    if mode == StripSort.NONE or node.kind != "C" or len(node.children) < 2:
        return
    ax = node.axis
    body = [c for c in node.children if c.kind != "W"]
    tail = [c for c in node.children if c.kind == "W"]
    if len(body) < 2 or len(tail) > 1:
        return
    if mode == StripSort.DESC:
        body.sort(key=lambda c: -_extent(c, ax))
    elif mode == StripSort.ASC:
        body.sort(key=lambda c: _extent(c, ax))
    elif mode == StripSort.NARROW_CENTER:
        srt = sorted(body, key=lambda c: -_extent(c, ax))
        left, right = [], []
        for i, c in enumerate(srt):
            (left if i % 2 == 0 else right).append(c)
        body = left + right[::-1]
    pos = node.x if ax == "x" else node.y
    for c in body:
        cur = c.x if ax == "x" else c.y
        if ax == "x":
            c.shift(pos - cur, 0)
        else:
            c.shift(0, pos - cur)
        pos += _extent(c, ax) + kerf
    for c in tail:
        end = (node.x + node.l) if ax == "x" else (node.y + node.w)
        cur = c.x if ax == "x" else c.y
        if ax == "x":
            c.shift(pos - cur, 0); c.l = end - pos
        else:
            c.shift(0, pos - cur); c.w = end - pos
    node.children = body + [t for t in tail if _extent(t, ax) > EPS]


def _snapshot(n: _N):
    return [(c, c.x, c.y, c.l, c.w) for c in n.children], list(n.children)


def _restore(n: _N, snap) -> None:
    items, order = snap
    for (c, x, y, l, w) in items:
        c.shift(x - c.x, y - c.y)
        c.l, c.w = l, w
    n.children = order


def _safe_reorder(node: _N, mode: StripSort, cut: CSCutParams, zone: _Zone, root: Optional[_N] = None) -> None:
    if mode == StripSort.NONE or node.kind != "C":
        return
    snap = _snapshot(node)
    before = _trim_violations(root or node, zone, cut.min_trim_cut)
    _reorder(node, mode, cut.kerf)
    if _trim_violations(root or node, zone, cut.min_trim_cut) > before:
        _restore(node, snap)


# ───────────────────────── Asosiy funksiya ─────────────────────────
QUALITY_BUDGET = {
    # sifat: (asosiy soniya, har detalga qo'shimcha, maksimum)
    "fast": (0.4, 0.004, 1.5),
    "normal": (1.0, 0.02, 4.0),
    "max": (3.0, 0.05, 15.0),
}
# Qo'shimcha qidiruv (listlar soni maydon bo'yicha pastki chegaradan ko'p bo'lsa — aynan K listga joylash):
# faqat natija yaxshilanishi mumkin bo'lgan murakkab buyurtmalarda sarflanadi.
IMPROVE_BUDGET = {
    "fast": (0.5, 0.0, 1.0),
    "normal": (7.0, 0.02, 9.0),
    "max": (8.0, 0.08, 25.0),
}


# Oxirgi listdagi qoldiqni yig'ish (bitta katta деловой bo'lak) uchun vaqt
COMPACT_BUDGET = {"fast": 0.25, "normal": 0.8, "max": 2.0}
# Деловой qoldiq bahosi: list bo'yi/eni bo'ylab butun bo'lmagan («burchak») bo'lak maydoni shu koeffitsient bilan
REMNANT_CORNER_WEIGHT = 0.75
# List tejash qidiruvi yechimga juda yaqin bo'lsa uzaytiriladi — lekin kroy umumiy vaqti shu chegaradan oshmaydi
# (spetsifikatsiya: standart byudjet ≤ 20 s); «Максимальное» rejimda chegara yo'q
TOTAL_CAP = {"fast": 4.0, "normal": 17.0}


def time_budget(n_parts: int, quality: str = "normal") -> float:
    a, b, mx = QUALITY_BUDGET.get(quality, QUALITY_BUDGET["normal"])
    return min(mx, a + b * n_parts)


def improve_budget(n_parts: int, quality: str = "normal") -> float:
    a, b, mx = IMPROVE_BUDGET.get(quality, IMPROVE_BUDGET["normal"])
    return min(mx, a + b * n_parts)


def optimize(items: list[Item], stock: list[StockSheet], cut: CSCutParams,
             mat: CSMaterialParams, time_limit: Optional[float] = None,
             groups: Optional[dict[str, tuple[int, int, str]]] = None) -> CuttingResult:
    """Раскроить: detallarni listlarga joylaydi. time_limit — vaqt byudjeti (soniya); berilmasa
    cut.quality va detallar soniga qarab tanlanadi (500 detal ≤ 5 s).
    Har karta kesish daraxti bilan qaytadi (buyruqlar jadvali, qo'lda tahrir, tekshiruv uchun)."""
    if not items or not stock:
        return CuttingResult(unplaced=[i.part_id for i in items])
    src = items
    if groups:
        items = group_items(items, groups, stock, cut)
    quality = getattr(cut, "quality", "normal")
    extra = improve_budget(len(items), quality)
    explicit = time_limit is not None
    if time_limit is None:
        time_limit = time_budget(len(items), quality)
    else:
        extra = min(extra, time_limit * 0.5)
    t0 = time.monotonic()
    grouped = groups and len(items) != len(src)
    compact = COMPACT_BUDGET.get(quality, 1.0)
    if explicit:
        compact = min(compact, time_limit * 0.2)
    res = _optimize_tree(items, stock, cut, mat, t0 + time_limit * (0.6 if grouped else 0.9),
                         improve_s=extra * (0.6 if grouped else 1.0), compact_s=compact)
    if grouped and any(pid in groups for pid in res.unplaced):
        # bloklar cheklangan listlarga sig'madi — sig'maganlari guruhsiz (yakka detal) bilan qayta
        rest = {pid: g for pid, g in groups.items() if pid not in set(res.unplaced)}
        alt = _optimize_tree(group_items(src, rest, stock, cut), stock, cut, mat, t0 + time_limit * 0.95,
                             compact_s=compact * 0.5)
        if (len(alt.unplaced), alt.total_sheets) < (len(res.unplaced), res.total_sheets):
            res = alt
    res.variant = res.variant or "optimal"
    return res


def _run_job(pool: _Pool, stock_sorted: list[StockSheet], cut: CSCutParams, axes: list[str], deadline: float,
             family: Optional[tuple[str, str]] = None,
             counts0: Optional[list[int]] = None) -> tuple[list[_Sheet], list[int]]:
    """Butun ishni listma-list joylash. family=None — barcha oilalar (eng yaxshisi har listda),
    aks holda bitta oila (masalan ('strip3','x')) — ish darajasidagi xilma-xillik uchun."""
    counts = (counts0 if counts0 is not None else pool.counts0)[:]
    sheets: list[_Sheet] = []
    remaining = {s.id: s.qty for s in stock_sorted}
    t_begin = time.monotonic()
    main_deadline = t_begin + (deadline - t_begin) * 0.6
    small = sum(counts) <= 120
    for st in stock_sorted:
        zone = _zone(st, cut)
        if zone.UL <= 0 or zone.UW <= 0:
            continue
        usable = zone.UL * zone.UW
        while remaining[st.id] > 0 and sum(counts) > 0:
            now = time.monotonic()
            if family is not None:
                sh = _legacy_sheet(pool, counts, zone, cut, family[1]) if family[0] == "strip3" else None
                if sh is not None and not _depth_ok(sh.root, pool, cut.max_rotations):
                    sh = None
                if sh is not None:
                    sh.how = f"{family[0]}:{family[1]}"
            else:
                left_area = sum(s.area * c for s, c in zip(pool.shapes, counts))
                est = max(1.0, left_area / (usable * 0.85))
                sheet_deadline = now + max(0.0, (main_deadline - now)) / est
                last_one = left_area <= usable * 0.995
                sh = _best_sheet(pool, counts, zone, cut, axes, sheet_deadline, cheap_only=now > deadline,
                                 intensive=small or last_one, target_all=last_one, deep=last_one)
                if sh is not None and cut.first_cut in (FirstCutDir.LENGTH_PREF, FirstCutDir.WIDTH_PREF) \
                        and sh.root.axis != axes[0] and 100 * sh.area / usable < cut.fill_packet:
                    alt = _best_sheet(pool, counts, zone, cut, [axes[0]], sheet_deadline)
                    if alt is not None and alt.area >= sh.area - EPS:
                        sh = alt
            if sh is None:
                break
            sh.used = [a - b for a, b in zip(counts, sh.counts_after)]
            counts[:] = sh.counts_after
            sheets.append(sh)
            remaining[st.id] -= 1
            # Paket / kratnost: to'ldirish yuqori bo'lsa aynan shu karta takrorlanadi
            if 100 * sh.area / usable >= cut.fill_packet - EPS:
                reps = min((counts[i] // u for i, u in enumerate(sh.used) if u > 0), default=0)
                reps = min(reps, remaining[st.id])
                for _ in range(reps):
                    for i, u in enumerate(sh.used):
                        counts[i] -= u
                    sheets.append(sh)
                    remaining[st.id] -= 1
    if family is None:
        sheets = _repair_tail(pool, sheets, counts, cut, axes, deadline)
    return sheets, counts


def _stock_orders(ss: list[StockSheet]) -> list[list[StockSheet]]:
    """Listlarni ishlatish tartibi variantlari. Soni cheklangan (< 10000) listlar bo'lmasa — bitta tartib."""
    lim = [s for s in ss if s.qty < 10000]
    unl = [s for s in ss if s.qty >= 10000]
    if len(ss) < 2 or not lim:
        return [ss]
    out = [ss]

    def add(o: list[StockSheet]) -> None:
        if [id(s) for s in o] not in [[id(s) for s in x] for x in out]:
            out.append(o)

    rem = [s for s in lim if s.is_remnant]                  # ombor qoldiqlari — doim birinchi (kichigidan)
    oth = [s for s in lim if not s.is_remnant]
    add(rem + sorted(oth, key=lambda s: -s.length * s.width) + unl)
    add(rem + sorted(oth, key=lambda s: s.length * s.width) + unl)
    if oth and (rem or unl):
        add(rem + unl)                                      # cheklangan oddiy listlarsiz
    return out


def _composition_search(pool: _Pool, stock: list[StockSheet], cut: CSCutParams, axes: list[str],
                        area_best: float, deadline: float) -> Optional[list[_Sheet]]:
    """Ishlatiladigan listlar TO'PLAMINI (qaysi qoldiq listlar + nechta butun list) maydon bo'yicha o'sish tartibida
    sinash: har to'plam uchun hammasini shu listlarga sig'dirish («bin completion», turli o'lchamli zonalar).
    Joriy eng yaxshi maydondan (area_best, m²) kichik birinchi muvaffaqiyatli to'plam qaytadi."""
    lim: list[StockSheet] = []
    for s in sorted((s for s in stock if s.qty < 10000), key=lambda s: s.length * s.width):
        lim += [s] * min(s.qty, 4)
    lim = lim[:8]
    unl = [s for s in stock if s.qty >= 10000]
    if not lim or not unl:
        return None
    total = sum(sh.area * c for sh, c in zip(pool.shapes, pool.counts0))
    zone_of: dict[str, _Zone] = {s.id: _zone(s, cut) for s in lim + unl}
    full = lambda s: s.length * s.width / 1e6                      # noqa: E731
    comps: list[tuple[float, int, list[StockSheet]]] = []
    for new in unl:
        zn = zone_of[new.id]
        if zn.UL <= 0 or zn.UW <= 0:
            continue
        for mask in range(1 << len(lim)):
            sel = [lim[i] for i in range(len(lim)) if mask >> i & 1]
            if any(zone_of[s.id].UL <= 0 or zone_of[s.id].UW <= 0 for s in sel):
                continue
            cap = sum(zone_of[s.id].UL * zone_of[s.id].UW for s in sel)
            need = max(0, math.ceil((total - cap) / (zn.UL * zn.UW) - 1e-9))
            for n_new in (need, need + 1):
                if n_new == 0 and not sel:
                    continue
                area = sum(full(s) for s in sel) + n_new * full(new)
                if area < area_best - 0.01:
                    comps.append((area, len(sel) + n_new, sel + [new] * n_new))
    comps.sort(key=lambda c: (round(c[0], 2), c[1]))
    seen: set = set()
    tried = 0
    for area, _n, seq in comps:
        key = tuple(s.id for s in seq)
        if key in seen:
            continue
        seen.add(key)
        now = time.monotonic()
        if now > deadline or tried >= 10:
            break
        tried += 1
        zones = [zone_of[s.id] for s in seq]
        r = _bin_completion_zones(pool, pool.counts0[:], zones, cut, axes, min(deadline, now + max(0.4, (deadline - now) / 4)))
        if r is not None:
            return r
    return None


def _limited_first(pool: _Pool, stock: list[StockSheet], cut: CSCutParams, axes: list[str],
                   deadline: float) -> Optional[tuple[list[_Sheet], list[int]]]:
    """Eng katta cheklangan (qoldiq/qirqim) listga bir nechta muqobil detallar to'plamini joylab, qolganini
    ochko'zlik bilan yechish: «ochko'z» to'plam qolganini bitta butun listga sig'dirmasa ham boshqasi sig'adi."""
    lim = sorted((s for s in stock if s.qty < 10000 and not s.is_remnant), key=lambda s: -s.length * s.width)
    if not lim:
        return None
    st = lim[0]
    zone = _zone(st, cut)
    if zone.UL <= 0 or zone.UW <= 0:
        return None
    t0 = time.monotonic()
    cands = _sheet_cands(pool, pool.counts0[:], zone, cut, axes, t0 + max(0.2, (deadline - t0) * 0.3), 8)
    rest_stock = [s.model_copy(update={"qty": s.qty - 1}) if s.id == st.id else s for s in stock]
    rest_stock = [s for s in rest_stock if s.qty > 0]
    best: Optional[tuple[list[_Sheet], list[int]]] = None
    best_key = None
    for i, cand in enumerate(cands):
        now = time.monotonic()
        if now > deadline and best is not None:
            break
        cand.used = [a - b for a, b in zip(pool.counts0, cand.counts_after)]
        share = max(0.3, (deadline - now) / max(1, len(cands) - i))
        rest, left = _run_job(pool, rest_stock, cut, axes, now + share, counts0=cand.counts_after)
        job = [cand] + rest
        k = _job_key(pool, job, left, cut.prefer_big_pack)
        if best_key is None or k < best_key:
            best, best_key = (job, left), k
    return best


def _refill_limited(pool: _Pool, sheets: list[_Sheet], stock: list[StockSheet], cut: CSCutParams,
                    axes: list[str], deadline: float) -> list[_Sheet]:
    """Oxirgi butun («cheksiz») listdagi detallarni hali ishlatilmagan qoldiq/qirqim listlarga ko'chirishga urinish:
    hammasi sig'sa — butun list tejaladi (material ham ketmaydi)."""
    free: dict[str, int] = {}
    for st in stock:
        if st.qty < 10000:
            free[st.id] = st.qty
    for s in sheets:
        if s.zone.stock.id in free:
            free[s.zone.stock.id] -= 1
    cands = [st for st in stock if free.get(st.id, 0) > 0]
    cands.sort(key=lambda st: -st.length * st.width)
    out = list(sheets)
    while cands and time.monotonic() < deadline:
        idx = max((i for i, s in enumerate(out) if s.zone.stock.qty >= 10000), default=None)
        if idx is None:
            break
        tail = out[idx]
        c = tail.used[:] if tail.used is not None else _shape_counts(pool, tail.root)
        add: list[_Sheet] = []
        pool_free = {st.id: free[st.id] for st in cands}
        for st in cands:
            zone = _zone(st, cut)
            if zone.UL <= 0 or zone.UW <= 0:
                continue
            while pool_free[st.id] > 0 and sum(c) > 0:
                sh = _best_sheet(pool, c, zone, cut, axes, min(deadline, time.monotonic() + 1.0),
                                 intensive=True, target_all=True)
                if sh is None or sum(sh.counts_after) >= sum(c):
                    break
                sh.used = [a - b for a, b in zip(c, sh.counts_after)]
                c = sh.counts_after[:]
                add.append(sh)
                pool_free[st.id] -= 1
        if sum(c) > 0 or not add:
            break
        out = out[:idx] + out[idx + 1:] + add
        for sh in add:
            free[sh.zone.stock.id] -= 1
        cands = [st for st in cands if free.get(st.id, 0) > 0]
    return out


def _job_key(pool: _Pool, sheets: list[_Sheet], counts: list[int], big_pack: bool = False):
    left = sum(counts)
    remn = _largest_waste(sheets[-1].root) if sheets else 0.0
    # Ishlatilgan material maydoni (m²): turli o'lchamli listlar (qoldiq/qirqim + butun list) bo'lganda katta qoldiq
    # evaziga ortiqcha butun list olinmasin; bir xil o'lchamli listlarda list soniga mutanosib (tartib o'zgarmaydi).
    area = round(sum(s.zone.L * s.zone.W for s in sheets) / 1e6, 2)
    if big_pack:        # «Большой пакет»: teng listlarda — kamroq turli karta (ko'proq nusxa, paketda kesish)
        return (left, area, len(sheets), len({_sheet_sig(s) for s in sheets}), -round(remn / 1e6, 3))
    return (left, area, len(sheets), -round(remn / 1e6, 3))


def _sheet_cands(pool: _Pool, counts: list[int], zone: _Zone, cut: CSCutParams, axes: list[str],
                 deadline: float, limit: int) -> list[_Sheet]:
    """Bitta list uchun turli (detallar to'plami bo'yicha farqli) yaxshi joylashuvlar — maydon kamayishi tartibida."""
    cands: list[_Sheet] = []
    _best_sheet(pool, counts, zone, cut, axes, deadline, intensive=True, collect=cands)
    uniq: dict[tuple, _Sheet] = {}
    for c in sorted(cands, key=lambda x: (-round(x.area, 0), -_largest_waste(x.root))):
        key = tuple(c.counts_after)
        if key not in uniq:
            uniq[key] = c
        if len(uniq) >= limit:
            break
    return list(uniq.values())


FIT_LIMITED_MAX_SHEETS = 12


def _fit_limited(pool: _Pool, stock: list[StockSheet], cut: CSCutParams, axes: list[str],
                 deadline: float) -> Optional[list[_Sheet]]:
    """Barcha listlar soni cheklangan va oddiy qidiruv detallarni sig'dira olmagan holat: mavjud listlarning hammasiga
    (turli tartiblarda) to'liq joylashga urinish. Maydon yetmasa yoki listlar ko'p bo'lsa — None."""
    if any(s.qty >= 10000 for s in stock):
        return None
    seq: list[StockSheet] = []
    for s in stock:
        seq += [s] * max(0, s.qty)
    if not seq or len(seq) > FIT_LIMITED_MAX_SHEETS:
        return None
    zone_of = {s.id: _zone(s, cut) for s in stock}
    seq = [s for s in seq if zone_of[s.id].UL > 0 and zone_of[s.id].UW > 0]
    total = sum(sh.area * c for sh, c in zip(pool.shapes, pool.counts0))
    if total > sum(zone_of[s.id].UL * zone_of[s.id].UW for s in seq) + EPS:
        return None
    area = lambda s: s.length * s.width                                  # noqa: E731
    orders = [sorted(seq, key=lambda s: -area(s)), sorted(seq, key=area), list(seq)]
    seen: set = set()
    uniq = []
    for o in orders:
        k = tuple(s.id for s in o)
        if k not in seen:
            seen.add(k)
            uniq.append(o)
    for i, o in enumerate(uniq):
        now = time.monotonic()
        if now > deadline:
            break
        r = _bin_completion_zones(pool, pool.counts0[:], [zone_of[s.id] for s in o], cut, axes,
                                  now + (deadline - now) / (len(uniq) - i))
        if r is not None:
            return r
    return None


def _bin_completion(pool: _Pool, counts: list[int], zone: _Zone, cut: CSCutParams, axes: list[str],
                    K: int, deadline: float, width: int = 8) -> Optional[list[_Sheet]]:
    """Detallarni aynan K ta (bir xil) listga joylashga urinish — `_bin_completion_zones` ning xususiy holi."""
    return _bin_completion_zones(pool, counts, [zone] * K, cut, axes, deadline, width)


def _bin_completion_zones(pool: _Pool, counts: list[int], zones: list[_Zone], cut: CSCutParams, axes: list[str],
                          deadline: float, width: int = 8) -> Optional[list[_Sheet]]:
    """Detallarni berilgan listlar ketma-ketligiga (zones[0], zones[1], …; o'lchamlari turlicha bo'lishi mumkin)
    joylashga urinish («bin completion» qidiruvi): har list uchun bir nechta nomzod joylashuv; jami chiqindi
    Σ foydali − detallar maydonidan oshsa — shox kesiladi; muvaffaqiyatsiz holatlar eslab qolinadi.
    Topilmasa (yoki vaqt tugasa) — None."""
    K = len(zones)
    Us = [z.UL * z.UW for z in zones]
    total = sum(pool.shapes[i].area * c for i, c in enumerate(counts))
    slack0 = sum(Us) - total
    if K == 0 or slack0 < -EPS:
        return None
    failed: set = set()
    calls = [0]

    def dfs(c: list[int], k_left: int, slack: float) -> Optional[list[_Sheet]]:
        if sum(c) == 0:
            return []
        if k_left <= 0 or time.monotonic() > deadline:
            return None
        key = (tuple(c), k_left)
        if key in failed:
            return None
        zone = zones[K - k_left]
        U = Us[K - k_left]
        if k_left == 1:
            sh = _best_sheet(pool, c, zone, cut, axes, min(deadline, time.monotonic() + 0.6),
                             intensive=True, target_all=True)
            if sh is not None and sum(sh.counts_after) == 0:
                sh.used = [a - b for a, b in zip(c, sh.counts_after)]
                return [sh]
            failed.add(key)
            return None
        calls[0] += 1
        cands = _sheet_cands(pool, c, zone, cut, axes, min(deadline, time.monotonic() + 0.5), width)
        for sh in cands:
            waste = U - sh.area
            if waste > slack + 1.0:
                break                         # maydon kamayishi tartibida — keyingilari ham sig'maydi
            if sum(sh.counts_after) == sum(c):
                continue
            r = dfs(sh.counts_after, k_left - 1, slack - waste)
            if r is not None:
                sh.used = [a - b for a, b in zip(c, sh.counts_after)]
                return [sh] + r
            if time.monotonic() > deadline:
                return None
        failed.add(key)
        return None

    return dfs(counts[:], K, slack0)


SVC_ALPHA = float(__import__("os").environ.get("MEBELIX_SVC_ALPHA", "0") or 0)
SVC_MODES = tuple((int(m.split(":")[0]), m.split(":")[1]) for m in
                  __import__("os").environ.get("MEBELIX_SVC_MODES", "0:knap,1:greedy,2:greedy").split(","))


SVC_FINAL_MAX = float(__import__("os").environ.get("MEBELIX_SVC_FINAL_MAX", "0.96") or 0.96)
SVC_CLOSE = float(__import__("os").environ.get("MEBELIX_SVC_CLOSE", "0.06") or 0.06)


def _svc_search(pool: _Pool, zone: _Zone, cut: CSCutParams, axes: list[str], deadline: float,
                target: int, lb: int, extend_to: Optional[float] = None,
                stats: Optional[dict] = None) -> Optional[list[_Sheet]]:
    """Ketma-ket qiymat tuzatish (Sequential Value Correction): ish bir necha marta qayta quriladi; har safar
    yomon to'lgan listlarga tushgan detallar «qimmatroq» bo'ladi (vazn = to'ldirish ulushining teskarisi,
    iteratsiyalar bo'yicha o'rtacha) va keyingi qurishda oldinroq joylanadi. target dan kam listli eng yaxshi
    yechim (yoki None) qaytadi; pastki chegaraga yetsa — darhol.
    extend_to — muddat tugaganda yechimga juda yaqin bo'lsa (ortiqcha listga tushgan maydon ≤ SVC_CLOSE · list),
    qidiruv bir marta shu vaqtgacha uzaytiriladi (list tejash bir necha soniyadan qimmat)."""
    n = len(pool.shapes)
    U = zone.UL * zone.UW
    if U <= 0 or cut.max_part_types_per_map or not cut.complex_strips:
        return None                       # ustunli oila bu cheklovlarni qo'llab-quvvatlamaydi
    w = [1.0] * n
    best: Optional[list[_Sheet]] = None
    dl = [deadline]                       # joriy muddat (uzaytirilishi mumkin)
    best_over = float("inf")              # eng yaqin urinish: maqsaddan ortib qolgan detallar maydoni
    # tez rejimlar (oldindan ko'rishsiz) — iteratsiyalar soni muhimroq; oxirgi list uchun to'liq to'plam
    modes = [(axis, look, mode) for axis in axes for (look, mode) in SVC_MODES]
    final_modes = [(axis, look, mode) for axis in axes for (look, mode) in ((3, "greedy"), (0, "knap"), (1, "greedy"))]
    finals: dict[tuple, Optional[_Sheet]] = {}       # oxirgi list: qolgan detallar to'plami → joylashuv (yoki None)
    plain = {axis: _col_packer(pool, zone, cut, axis) for axis in axes}

    def final(c: list[int]) -> Optional[_Sheet]:
        key = tuple(c)
        if key in finals:
            return finals[key]
        fin = None
        for (axis, look, mode) in final_modes:
            if time.monotonic() > dl[0]:
                break
            s2 = _col_sheet(pool, c, zone, cut, axis, look, mode, None, plain[axis], deadline=dl[0])
            if s2 is not None and sum(s2.counts_after) == 0 and _depth_ok(s2.root, pool, cut.max_rotations):
                fin = s2
                break
        # ustunli usullar sig'dira olmadi — intensiv qidiruv faqat real imkoniyat bo'lsa (juda zich qoldiq
        # deyarli hech qachon sig'maydi; har urinish ~0.3 s — iteratsiyalar soni muhimroq)
        ratio = sum(s.area * k for s, k in zip(pool.shapes, c)) / U
        if fin is None and ratio <= SVC_FINAL_MAX:
            s2 = _best_sheet(pool, c, zone, cut, axes, min(dl[0], time.monotonic() + (0.4 if ratio <= 0.9 else 0.25)),
                             intensive=True, target_all=True)
            if s2 is not None and sum(s2.counts_after) == 0:
                fin = s2
        finals[key] = fin
        return fin

    rng = random.Random(7919 * len(pool.shapes) + sum(pool.counts0))
    it = 0
    t_begin = time.monotonic()
    while True:
        now = time.monotonic()
        # uzaytirish qarori keyingi iteratsiya muddatga sig'maydigan bo'lganda (o'rtacha iteratsiya vaqti bo'yicha) —
        # iteratsiya muddat bilan uzilib, vaznlarni buzmasin
        avg_it = (now - t_begin) / it if it else 0.0
        if extend_to is not None and extend_to > dl[0] and now + 1.2 * avg_it >= dl[0] \
                and best_over <= SVC_CLOSE * U:
            dl[0] = extend_to                 # yechimga juda yaqin — bir marta uzaytiriladi
            extend_to = None
            if stats is not None:
                stats["extended"] = True
        if now >= dl[0]:
            break
        it += 1
        c = pool.counts0[:]
        sheets: list[_Sheet] = []
        packers = {axis: _col_packer(pool, zone, cut, axis, w) for axis in axes}   # ustun keshi — iteratsiya ichida
        while sum(c) > 0 and len(sheets) < target and time.monotonic() < dl[0]:
            left_area = sum(s.area * k for s, k in zip(pool.shapes, c))
            if left_area <= U * 0.999:
                fin = final(c)
                if fin is not None:
                    fin.used = [a - b for a, b in zip(c, fin.counts_after)]
                    sheets.append(fin)
                    c = fin.counts_after
                    break
            cand = None
            for (axis, look, mode) in modes:
                if cand is not None and time.monotonic() > dl[0]:
                    break
                s2 = _col_sheet(pool, c, zone, cut, axis, look, mode, w, packers[axis], deadline=dl[0])
                if s2 is None or s2.area <= 0 or not _depth_ok(s2.root, pool, cut.max_rotations):
                    continue
                if cand is None or s2.wval > cand.wval + EPS:
                    cand = s2
            if cand is None:
                break
            cand.used = [a - b for a, b in zip(c, cand.counts_after)]
            sheets.append(cand)
            c = cand.counts_after
        if sum(c) == 0 and len(sheets) < target:
            best, target = sheets, len(sheets)
            best_over = float("inf")
            if target <= lb:
                return best
        elif len(sheets) >= target - 1 and time.monotonic() < dl[0]:
            # maqsaddan (target − 1 list) ortib qolgan maydon: oxirgi list(lar) + joylanmaganlar
            over = sum(sh.area for sh in sheets[target - 1:]) + sum(s.area * k for s, k in zip(pool.shapes, c))
            best_over = min(best_over, over)
            if stats is not None:
                stats["best_over"] = best_over / U
        if time.monotonic() >= dl[0]:
            break                             # muddat bilan uzilgan (to'liq bo'lmagan) iteratsiya vaznlarga ta'sir qilmaydi
        # qiymat tuzatish: har tur uchun o'z listining to'ldirish ulushi teskarisi (joylanmagan — 2);
        # yangilash qadami tasodifiy (takrorlanuvchi urug') — sikllardan chiqish uchun
        alpha = SVC_ALPHA if SVC_ALPHA > 0 else rng.uniform(0.35, 0.85)
        acc = [0.0] * n
        cnt = [0] * n
        for sh in sheets:
            f = max(0.05, sh.area / U)
            for i, u in enumerate(sh.used or []):
                if u:
                    acc[i] += u / f
                    cnt[i] += u
        for i in range(n):
            if pool.counts0[i] <= 0:
                continue
            y = acc[i] / cnt[i] if cnt[i] else 2.0
            if cnt[i] < pool.counts0[i]:
                y = (acc[i] + 2.0 * (pool.counts0[i] - cnt[i])) / pool.counts0[i]
            w[i] = (1 - alpha) * w[i] + alpha * y
    return best


def _optimize_tree(items: list[Item], stock: list[StockSheet], cut: CSCutParams,
                   mat: CSMaterialParams, deadline: float, improve_s: float = 0.0,
                   compact_s: float = 0.0) -> CuttingResult:
    pool = _Pool(items)
    pool.gk = group_kerf(cut)
    pool.gk_differs = abs(pool.gk - cut.kerf) > EPS
    stock_sorted = sorted(stock, key=lambda s: (not s.is_remnant, s.length * s.width if s.is_remnant else 0))
    axes = _axes_for(cut)
    t0 = time.monotonic()
    budget = deadline - t0
    # Turli list tartiblari (qoldiq/qirqim + butun list): ro'yxat tartibi, cheklanganlar yuza bo'yicha, faqat butun
    # listlar — eng kam material sarflagani tanlanadi (bir xil o'lchamli listlarda bitta tartib, hech narsa o'zgarmaydi).
    # «Порядок листов: по списку» (standart) — faqat ro'yxat tartibi: ombor qoldiqlari va soni cheklangan listlar
    # sig'gan detal bo'lsa avval ishlatiladi (xodimlar o'rgangan tizim xulqi); «economy» — tartiblar sinaladi.
    orders = _stock_orders(stock_sorted) if getattr(cut, "stock_order", "list") == "economy" else [stock_sorted]
    stock_all = stock_sorted
    best_sheets = best_counts = best_key = None
    for i, order in enumerate(orders):
        share = budget * 0.85 if len(orders) == 1 else (budget * 0.85 * 0.4 if i == 0 else budget * 0.85 * 0.6 / (len(orders) - 1))
        sh0, cn0 = _run_job(pool, order, cut, axes, time.monotonic() + share)
        if len(orders) > 1 and sum(cn0) == 0:
            sh0 = _refill_limited(pool, sh0, stock_all, cut, axes, time.monotonic() + share * 0.5)
        k0 = _job_key(pool, sh0, cn0, cut.prefer_big_pack)
        if best_key is None or k0 < best_key:
            best_sheets, best_counts, best_key, stock_sorted = sh0, cn0, k0, order
    if len(orders) > 1 and sum(pool.counts0) <= 250:
        lf = _limited_first(pool, stock_all, cut, axes, time.monotonic() + budget * 0.25)
        if lf is not None and sum(lf[1]) == 0:
            k1 = _job_key(pool, lf[0], lf[1], cut.prefer_big_pack)
            if k1 < best_key:
                best_sheets, best_counts, best_key, stock_sorted = lf[0], lf[1], k1, stock_all
        if best_key[0] == 0 and time.monotonic() < t0 + budget:
            cs = _composition_search(pool, stock_all, cut, axes, best_key[1], time.monotonic() + budget * 0.3)
            if cs:
                zero = [0] * len(pool.shapes)
                k2 = _job_key(pool, cs, zero, cut.prefer_big_pack)
                if k2 < best_key:
                    best_sheets, best_counts, best_key, stock_sorted = cs, zero, k2, stock_all
    variant = "optimal"
    cands = [(best_key, best_sheets, best_counts, variant)]
    # Ish darajasidagi muqobil: 3 bosqichli polosa algoritmi (har yo'nalish uchun alohida)
    for axis in axes:
        if time.monotonic() > deadline or sum(pool.counts0) > LEGACY_MAX_ITEMS:
            break
        try:
            sh2, c2 = _run_job(pool, stock_sorted, cut, axes, deadline, family=("strip3", axis))
        except Exception:  # noqa: BLE001
            continue
        k2 = _job_key(pool, sh2, c2, cut.prefer_big_pack)
        cands.append((k2, sh2, c2, f"strip3-{axis}"))
        if k2 < best_key:
            best_sheets, best_counts, best_key, variant = sh2, c2, k2, f"strip3-{axis}"
    # Cheklangan listlar (qoldiq / soni kam list) va detal SIG'MAY QOLDI: maydon bo'yicha sig'ishi mumkin bo'lsa —
    # mavjud listlarning hammasiga «bin completion» bilan to'liq joylashga urinish (bir nechta list tartibida).
    if best_sheets is not None and sum(best_counts) > 0 and time.monotonic() < t0 + budget + improve_s:
        fit_end = max(deadline, time.monotonic() + max(improve_s, 1.0))
        _cap = TOTAL_CAP.get(getattr(cut, "quality", "normal"))
        if _cap is not None:                      # rejimning umumiy vaqt chegarasi (Быстро ≤ 4 s, Стандарт ≤ 17 s)
            fit_end = min(fit_end, t0 + _cap - 0.5)
        fit = _fit_limited(pool, stock_all, cut, axes, fit_end)
        if fit is not None:
            zero = [0] * len(pool.shapes)
            best_sheets, best_counts, variant = fit, zero, "optimal"
            best_key = _job_key(pool, fit, zero, cut.prefer_big_pack)
            cands = [(best_key, fit, zero, variant)]
    # Listlar soni maydon bo'yicha pastki chegaradan ko'p bo'lsa — aynan K ta listga joylash qidiruvi
    stock_ids = {s.id for s in stock_sorted if s.qty > 0}
    if best_sheets and sum(best_counts) == 0 and len(stock_ids) == 1:
        zone = best_sheets[0].zone
        U = zone.UL * zone.UW
        total = sum(s.area * c for s, c in zip(pool.shapes, pool.counts0))
        lb = max(1, math.ceil(total / U - 1e-9)) if U > 0 else len(best_sheets)
        if lb < len(best_sheets):
            # 1) «bin completion» (kichik buyurtmalarda tez yechadi yoki tez tugaydi), 2) qiymat tuzatish (SVC).
            # Bitta listga juda zich (> 94 %) sig'dirish — asosiy qidiruvda chuqur urinilgan; qo'shimcha vaqt cheklanadi.
            if lb == 1 and total > U * 0.94:
                improve_s = min(improve_s, 2.0)
            imp_deadline = max(deadline, time.monotonic() + improve_s)
            now = time.monotonic()
            bc = _bin_completion(pool, pool.counts0, zone, cut, axes, lb, now + (imp_deadline - now) * 0.35)
            if bc is not None and len(bc) < len(best_sheets):
                best_sheets, best_counts = bc, [0] * len(pool.shapes)
                cands = [(_job_key(pool, bc, best_counts, cut.prefer_big_pack), bc, best_counts, variant)]
            if lb < len(best_sheets) and time.monotonic() < imp_deadline:
                # yechimga juda yaqin bo'lsa — qo'shimcha vaqt (list tejash bir necha soniyadan qimmat)
                ext = imp_deadline + improve_s * 0.6
                cap = TOTAL_CAP.get(getattr(cut, "quality", "normal"))
                if cap is not None:
                    ext = min(ext, t0 + cap)
                sv = _svc_search(pool, zone, cut, axes, imp_deadline, len(best_sheets), lb, extend_to=ext)
                if sv is not None and len(sv) < len(best_sheets):
                    best_sheets, best_counts = sv, [0] * len(pool.shapes)
                    cands = [(_job_key(pool, sv, best_counts, cut.prefer_big_pack), sv, best_counts, variant)]
    # Yakuniy: oxirgi listdagi bo'sh joyni BITTA katta (деловой) qoldiqqa yig'ish. Listlar soni teng nomzodlar
    # (asosiy qidiruv / polosa algoritmi) ichidan yig'ilgan qoldig'i eng yaxshisi tanlanadi.
    if compact_s > 0 and best_sheets:
        head = _job_key(pool, best_sheets, best_counts, cut.prefer_big_pack)[:-1]
        tied = sorted((c for c in cands if c[0][:-1] == head), key=lambda c: c[0]) or \
            [(best_key, best_sheets, best_counts, variant)]
        # oxirgi listdagi detallar to'plami bir xil nomzodlar — bitta qidiruv (natija deyarli bir xil bo'ladi)
        uniq, seen = [], set()
        for c in tied:
            sig = tuple(_shape_counts(pool, c[1][-1].root)) if c[1] else ()
            if sig not in seen:
                seen.add(sig)
                uniq.append(c)
        tied = uniq[:3]
        c_end = time.monotonic() + compact_s
        best_val = None
        for i, (_k, shs, cnts, var) in enumerate(tied):
            now = time.monotonic()
            new, val = _compact_tail(pool, shs, cut, axes, mat, now + max(0.0, c_end - now) / (len(tied) - i))
            # butun ish bo'yicha деловой maydon → oxirgi list qoldig'i → oldingi listlar zichroq (oxirgida kam detal);
            # teng bo'lsa — dastlabki (yaxshiroq kalitli) nomzod qoladi
            val = (_job_business(new, mat), val[1], val[2], -round(new[-1].area / 1e4))
            if best_val is None or val > best_val:
                best_val, best_sheets, best_counts, variant = val, new, cnts, var
        # qolgan listlar (vaqt qolsa): chiqindisi yetarli listlarda ham деловой qoldiq
        best_sheets = _compact_others(pool, best_sheets, cut, axes, mat, time.monotonic() + compact_s * 0.6)
    sheets = best_sheets
    # polosalarni saralash (har daraxt bir marta); list chetiga tayangan qirindi ichkariga o'tib qolsa — bekor
    for sh in {id(x): x for x in sheets}.values():
        _safe_reorder(sh.root, cut.strip_sort, cut, sh.zone)
        if cut.in_strip_sort != StripSort.NONE:
            for ch in sh.root.children:
                _safe_reorder(ch, cut.in_strip_sort, cut, sh.zone, root=sh.root)
    # part_id larni taqsimlash: har shakl uchun navbat
    queues = {s.idx: deque(s.pids) for s in pool.shapes}
    res = _build_result(sheets, queues, cut, mat, pool)
    res.unplaced = [pid for s in pool.shapes for (pid, _u) in list(queues[s.idx]) for _k in range(s.k)]
    res.variant = variant
    return _finish(res, mat)


def _repair_tail(pool: _Pool, sheets: list[_Sheet], counts: list[int], cut: CSCutParams,
                 axes: list[str], deadline: float) -> list[_Sheet]:
    """Oxirgi r ta listning detallarini birlashtirib, r−1 ta listga intensiv qidiruv bilan sig'dirishga urinish.
    (Ko'p hollarda oxirgi listda 1–2 detal qoladi — shu list tejaladi.)"""
    improved = True
    while improved and time.monotonic() < deadline:
        improved = False
        n = len(sheets)
        for r in (2, 3):
            if n < r or time.monotonic() > deadline:
                break
            tail = sheets[n - r:]
            zone = tail[-1].zone
            if any(t.zone.stock.id != zone.stock.id for t in tail):
                continue
            U = counts[:]
            for t in tail:
                for i, u in enumerate(t.used or []):
                    U[i] += u
            area = sum(pool.shapes[i].area * c for i, c in enumerate(U))
            usable = zone.UL * zone.UW
            if area > (r - 1) * usable * 0.995:
                continue
            c = U[:]
            new: list[_Sheet] = []
            ok = True
            for k in range(r - 1):
                last = k == r - 2
                sh = _best_sheet(pool, c, zone, cut, axes, min(deadline, time.monotonic() + (1.0 if last else 9e9)),
                                 intensive=True, target_all=last, deep=last)
                if sh is None:
                    ok = False
                    break
                sh.used = [a - b for a, b in zip(c, sh.counts_after)]
                c = sh.counts_after
                new.append(sh)
            if ok and sum(c) <= sum(counts):
                if sum(c) < sum(counts) or len(new) < r:
                    sheets = sheets[: n - r] + new
                    counts[:] = c
                    improved = True
                    break
    return _improve_remnant(pool, sheets, counts, cut, axes, deadline)


def _leaf_remnant(leaf: _N, z: _Zone, mat: CSMaterialParams) -> tuple[str, bool, float, float, float]:
    """Chiqindi bargi — kartadagi bilan bir xil qoida: (tur, деловой, hisob maydoni mm², xom uzunlik, xom en).
    Xom o'lcham — list chetiga tegsa torsovka bilan birga («Размер остатка с учетом торцовки» ☐ bo'lsa shu
    o'lcham bilan tasniflanadi va hisoblanadi)."""
    X, Y = leaf.x + z.ox, leaf.y + z.oy
    rx0 = 0.0 if leaf.x <= EPS else X
    ry0 = 0.0 if leaf.y <= EPS else Y
    rx1 = z.L if leaf.x + leaf.l >= z.UL - EPS else X + leaf.l
    ry1 = z.W if leaf.y + leaf.w >= z.UW - EPS else Y + leaf.w
    raw_l, raw_w = rx1 - rx0, ry1 - ry0
    if mat.remnant_size_incl_trim:
        cl_l, cl_w = leaf.l, leaf.w
    else:
        cl_l, cl_w = raw_l, raw_w
    kind, business = _classify(cl_l, cl_w, mat)
    return kind, business, cl_l * cl_w, raw_l, raw_w


def _remnant_score(root: _N, zone: _Zone, mat: Optional[CSMaterialParams]) -> tuple:
    """List qoldig'i bahosi (kattasi yaxshi): (деловой qoldiqlar jami maydoni, eng yaxshi bo'lak turi
    [деловой 2 / qoldiq 1 / chiqindi 0], o'sha bo'lak maydoni) — 1 sm² gacha yaxlitlangan."""
    tot, best = 0.0, (0, 0.0)
    for lf in root.leaves():
        if lf.kind != "W" or lf.l <= EPS or lf.w <= EPS:
            continue
        if mat is None:
            best = max(best, (0, lf.l * lf.w))
            continue
        kind, biz, area, rl, rw = _leaf_remnant(lf, zone, mat)
        if biz:
            # list bo'yi yoki eni bo'ylab butun polosa qoldiq qayta ishlatishga qulay; «burchak» (kvadratga yaqin)
            # bo'lak 25 % kam baholanadi — u faqat polosadan ancha katta bo'lsagina tanlanadi (foydalanuvchi talabi)
            full = rl >= zone.L - 1.0 or rw >= zone.W - 1.0
            tot += area if full else area * REMNANT_CORNER_WEIGHT
        best = max(best, (2 if biz else 1 if kind == "remnant" else 0, area))
    return (round(tot / 1e4), best[0], round(best[1] / 1e4))


def _sheet_sig(sh: "_Sheet") -> tuple:
    """Karta joylashuvi imzosi (bir xil kartalar — paket nusxalari)."""
    return (sh.zone.stock.id, tuple(sorted((round(lf.x, 1), round(lf.y, 1), lf.s, lf.rot)
                                           for lf in sh.root.leaves() if lf.kind == "P")))


def _shape_counts(pool: _Pool, root: _N) -> list[int]:
    U = [0] * len(pool.shapes)
    for lf in root.leaves():
        if lf.kind == "P" and lf.s >= 0:
            U[lf.s] += 1
    return U


def _band_root(small: _N, zone: _Zone, axis: str, kerf: float) -> Optional[_N]:
    """Tor zonada (polosada) qurilgan daraxtni butun listga kengaytirish: polosalar o'z joyida,
    qolgan qism — bitta katta qoldiq (W)."""
    kids = list(small.children)
    while kids and kids[-1].kind == "W":
        kids.pop()
    if not kids:
        return None
    e = max(((c.x + c.l) if axis == "x" else (c.y + c.w)) for c in kids)
    Ua = zone.UL if axis == "x" else zone.UW
    start = e + kerf
    if Ua - start > EPS:
        kids.append(_N(start, 0.0, Ua - start, zone.UW, 1, "W") if axis == "x"
                    else _N(0.0, start, zone.UL, Ua - start, 1, "W"))
    return _N(0.0, 0.0, zone.UL, zone.UW, 0, "C", axis=axis, children=kids)


def _min_band(pool: _Pool, U: list[int], zone: _Zone, cut: CSCutParams, axis: str, lo: float, hi: float,
              t_end: float) -> Optional[_N]:
    """U detallarni `axis` bo'yicha iloji boricha tor polosaga joylash (ildiz o'qi = axis): polosa eni ikkilik
    qidiruv bilan kamaytiriladi, har qadamda «hammasi sig'adimi». Qaytaradi tor zonadagi daraxt yoki None."""
    found: Optional[_N] = None
    steps = 0
    while hi - lo > 3.0 and steps < 9 and time.monotonic() < t_end:
        steps += 1
        mid = lo + (hi - lo) * (0.75 if found is None and steps == 1 else 0.5)
        z2 = dataclass_replace(zone, UL=mid, far_raw_x=False) if axis == "x" else \
            dataclass_replace(zone, UW=mid, far_raw_y=False)
        now = time.monotonic()
        cand = _best_sheet(pool, U, z2, cut, [axis], min(t_end, now + max(0.03, (t_end - now) / 3)), target_all=True)
        if cand is not None and sum(cand.counts_after) == 0 and cand.root.axis == axis:
            found = cand.root
            hi = _used_extent(found, axis) - 1.0
        else:
            lo = mid + 1.0
    return found


def _shift_levels(n: _N, d: int) -> None:
    n.level += d
    for c in n.children:
        _shift_levels(c, d)


def _corner_variants(pool: _Pool, band: _N, zone: _Zone, cut: CSCutParams, a: str, t_end: float) -> list[_N]:
    """Polosali yechimdan «burchak» qoldiqli variantlar: oxirgi j ta polosa detallari bitta polosaga (S) ko'ndalang
    yo'nalishda zich joylanadi — S ning qolgan qismi va undan keyingi joy bitta to'rtburchak qoldiq bo'ladi."""
    if cut.max_rotations < 3 or cut.min_strip_width or cut.max_strip_width or not cut.complex_strips:
        return []                 # oddiy polosalar / polosa eni cheklovlari — S polosaning ixtiyoriy eni mos emas
    strips = [c for c in band.children if c.kind != "W"]
    if len(strips) < 2:
        return []
    cross = _other(a)
    Ua = zone.UL if a == "x" else zone.UW
    Uo = zone.UW if a == "x" else zone.UL
    k = cut.kerf
    # ikki tartib: asl va «ko'ndalang yo'nalishda to'la polosalar oldinda» (ular joyida qoladi, qisqalari S ga)
    orders = [strips]
    srt = sorted(strips, key=lambda c: -_used_extent(c, cross))
    if srt != strips:
        laid, pos = [], 0.0
        for c in srt:
            c2 = copy.deepcopy(c)
            cur = c2.x if a == "x" else c2.y
            c2.shift(pos - cur, 0.0) if a == "x" else c2.shift(0.0, pos - cur)
            laid.append(c2)
            pos += _extent(c2, a) + k
        orders.insert(0, laid)
    sub_cut = cut.model_copy(update={"max_rotations": cut.max_rotations - 1})
    out: list[_N] = []
    tasks = [(st, j) for st in orders for j in range(len(st) - 1, 0, -1)]
    for t_i, (strips, j) in enumerate(tasks):
        if time.monotonic() > t_end:
            break
        prev = strips[j - 1]
        start = ((prev.x + prev.l) if a == "x" else (prev.y + prev.w)) + k
        S_ext = Ua - start
        if S_ext <= EPS:
            continue
        U = [0] * len(pool.shapes)
        for st in strips[j:]:
            for lf in st.leaves():
                if lf.kind == "P" and lf.s >= 0:
                    U[lf.s] += 1
        area = sum(pool.shapes[i].area * c for i, c in enumerate(U))
        if area <= 0:
            continue
        zS = dataclass_replace(zone, UL=S_ext) if a == "x" else dataclass_replace(zone, UW=S_ext)
        now = time.monotonic()
        sub = _min_band(pool, U, zS, sub_cut, cross, area / S_ext, Uo - 1.0, now + (t_end - now) / (len(tasks) - t_i))
        if sub is None:
            continue
        kids = [copy.deepcopy(c) for c in sub.children]
        while kids and kids[-1].kind == "W":
            kids.pop()
        if not kids:
            continue
        e_c = max(((c.x + c.l) if cross == "x" else (c.y + c.w)) for c in kids)
        for c in kids:
            c.shift(start, 0.0) if a == "x" else c.shift(0.0, start)
            _shift_levels(c, 1)
        rest = Uo - e_c - k
        if a == "x":
            if rest > EPS:
                kids.append(_N(start, e_c + k, S_ext, rest, 2, "W"))
            S = _N(start, 0.0, S_ext, Uo, 1, "C", axis=cross, children=kids)
        else:
            if rest > EPS:
                kids.append(_N(e_c + k, start, rest, S_ext, 2, "W"))
            S = _N(0.0, start, Uo, S_ext, 1, "C", axis=cross, children=kids)
        out.append(_N(0.0, 0.0, zone.UL, zone.UW, 0, "C", axis=a, children=list(strips[:j]) + [S]))
    return out


def _compact_sheet(pool: _Pool, sh: _Sheet, cut: CSCutParams, axes: list[str],
                   mat: Optional[CSMaterialParams], deadline: float) -> tuple[_Sheet, tuple]:
    """Oxirgi (to'liq bo'lmagan) list: shu detallarni iloji boricha tor polosaga (list bo'ylab yoki eni bo'ylab)
    joylab, qolgan joyni BITTA katta (деловой) qoldiqqa aylantirish; so'ng «burchak» variantlari — oxirgi
    polosalar detallari ko'ndalang zich joylanadi (qoldiq — list burchagidagi katta to'rtburchak).
    Qaytaradi: (list, qoldiq qiymati)."""
    zone = sh.zone
    cur_val = _remnant_score(sh.root, zone, mat)
    U = _shape_counts(pool, sh.root)
    area = sum(pool.shapes[i].area * c for i, c in enumerate(U))
    waste = zone.UL * zone.UW - area
    need = max(mat.remnant_min_area * 1e6, mat.remnant_min_side1 * mat.remnant_min_side2) if mat else 0.0
    if not area or waste < max(need, zone.UL * zone.UW * 0.05) or time.monotonic() > deadline:
        return sh, cur_val
    best_sh, best_val = sh, cur_val
    base_viol = _trim_violations(sh.root, zone, cut.min_trim_cut)
    # «По длине/ширине предпочтительно»: to'liq bo'lmagan list afzal yo'nalishda qoladi (C2)
    axes = list(axes[:1]) if cut.first_cut in (FirstCutDir.LENGTH_PREF, FirstCutDir.WIDTH_PREF) else list(axes)
    for n, a in enumerate(axes):
        now = time.monotonic()
        t_end = now + max(0.0, deadline - now) / (len(axes) - n)
        Ua = zone.UL if a == "x" else zone.UW
        Uo = zone.UW if a == "x" else zone.UL
        hi = (_used_extent(sh.root, a) if sh.root.axis == a else Ua) - 1.0
        found = _min_band(pool, U, zone, cut, a, area / Uo, hi, now + (t_end - now) * 0.55)
        if found is None and sh.root.axis == a:
            found = sh.root                    # joriy joylashuv o'zi eng tor polosa — burchak variantlari undan
        if found is None:
            continue
        band = _band_root(found, zone, a, cut.kerf)
        if band is None:
            continue
        for root in [band] + _corner_variants(pool, band, zone, cut, a, t_end):
            if not _depth_ok(root, pool, cut.max_rotations) \
                    or _trim_violations(root, zone, cut.min_trim_cut) > base_viol:
                continue
            val = _remnant_score(root, zone, mat)
            if val > best_val:
                best_val = val
                best_sh = _Sheet(zone, root, sh.area, sh.counts_after,
                                 (sh.how or "") + ("+band" if root is band else "+corner"), sh.used)
    return best_sh, best_val


def _replace_same(sheets: list[_Sheet], old: _Sheet, new: _Sheet) -> list[_Sheet]:
    """old bilan bir xil joylashuvli barcha listlar (paket nusxalari, alohida obyekt bo'lsa ham) — new bilan."""
    sig = _sheet_sig(old)
    return [new if (s is old or _sheet_sig(s) == sig) else s for s in sheets]


def _compact_others(pool: _Pool, sheets: list[_Sheet], cut: CSCutParams, axes: list[str],
                    mat: Optional[CSMaterialParams], deadline: float) -> list[_Sheet]:
    """Oxirgidan boshqa listlar: chiqindisi деловой qoldiq bo'lishga yetadigan, lekin hozir деловой qoldig'i
    yo'q listlarda ham bo'sh joy bitta bo'lakka yig'iladi (eng ko'p chiqindili listlardan boshlab).
    Bir xil kartalar (nusxalar) birga o'zgaradi — kartalar soni o'zgarmaydi."""
    if len(sheets) < 2 or mat is None:
        return sheets
    last_sig = _sheet_sig(sheets[-1])
    groups: dict[tuple, _Sheet] = {}
    for sh in sheets:
        sig = _sheet_sig(sh)
        if sig != last_sig and sig not in groups:
            groups[sig] = sh
    order = sorted(groups.values(), key=lambda x: x.area)
    for i, sh in enumerate(order):
        now = time.monotonic()
        if now > deadline:
            break
        if _remnant_score(sh.root, sh.zone, mat)[1] == 2:
            continue
        new, val = _compact_sheet(pool, sh, cut, axes, mat, now + (deadline - now) / (len(order) - i))
        if new is not sh:
            sheets = _replace_same(sheets, sh, new)
    return sheets


def _compact_tail(pool: _Pool, sheets: list[_Sheet], cut: CSCutParams, axes: list[str],
                  mat: Optional[CSMaterialParams], deadline: float) -> tuple[list[_Sheet], tuple]:
    if not sheets:
        return sheets, (0, 0, 0)
    last = sheets[-1]
    new, val = _compact_sheet(pool, last, cut, axes, mat, deadline)
    if new is last:
        return sheets, val
    return _replace_same(sheets, last, new), val


def _job_business(sheets: list[_Sheet], mat: Optional[CSMaterialParams]) -> int:
    """Ish bo'yicha деловой qoldiqlar jami maydoni (sm², har list nusxasi bilan)."""
    memo: dict[int, int] = {}
    tot = 0
    for sh in sheets:
        v = memo.get(id(sh))
        if v is None:
            v = memo[id(sh)] = _remnant_score(sh.root, sh.zone, mat)[0]
        tot += v
    return tot


def _improve_remnant(pool: _Pool, sheets: list[_Sheet], counts: list[int], cut: CSCutParams,
                     axes: list[str], deadline: float) -> list[_Sheet]:
    """Listlar soni o'zgarmagan holda oxirgi ikki listni qayta taqsimlash: oxirgi listda eng katta
    (деловой) qoldiq qolsin — ingichka/kichik detallar oxirgi listga, kattalari oldingisiga."""
    if len(sheets) < 2 or sum(counts) > 0 or time.monotonic() > deadline:
        return sheets
    a, b = sheets[-2], sheets[-1]
    if a is b or a.zone.stock.id != b.zone.stock.id:
        return sheets
    zone = b.zone
    U = [0] * len(pool.shapes)
    for t in (a, b):
        for i, u in enumerate(t.used or []):
            U[i] += u
    cands: list[_Sheet] = []
    _best_sheet(pool, U, zone, cut, axes, deadline, intensive=True, collect=cands)
    uniq = {}
    for c in sorted(cands, key=lambda x: -x.area):
        key = tuple(c.counts_after)
        if key not in uniq:
            uniq[key] = c
    best_pair = (b.root and _largest_waste(b.root), a, b)
    for first in list(uniq.values())[:12]:
        if time.monotonic() > deadline:
            break
        rest = first.counts_after
        if sum(rest) == 0:
            continue
        last = _best_sheet(pool, rest, zone, cut, axes, min(deadline, time.monotonic() + 0.5), intensive=True,
                           target_all=True)
        if last is None or sum(last.counts_after) > 0:
            continue
        rem = _largest_waste(last.root)
        if rem > best_pair[0] + 1.0:
            first.used = [x - y for x, y in zip(U, first.counts_after)]
            last.used = [x - y for x, y in zip(rest, last.counts_after)]
            best_pair = (rem, first, last)
    if best_pair[1] is not a:
        return sheets[:-2] + [best_pair[1], best_pair[2]]
    return sheets


# ───────────────────────── Natijani yig'ish ─────────────────────────
def _classify(l: float, w: float, mat: CSMaterialParams) -> tuple[str, bool]:
    """(tur, деловой): qoldiq — ikkala tomon chegaradan katta; деловой — maydon ham yetarli."""
    a, b = max(l, w), min(l, w)
    if a >= mat.remnant_min_side1 - EPS and b >= mat.remnant_min_side2 - EPS:
        return "remnant", (a * b) / 1e6 >= mat.remnant_min_area - 1e-9
    return "waste", False


def _build_map(sh: _Sheet, idx: int, p: CSCutParams, mat: CSMaterialParams, counter: list[int],
               queues: dict[int, deque]) -> CutMap:
    z = sh.zone
    m = CutMap(index=idx, sheet_id=z.stock.id, sheet_length=z.L, sheet_width=z.W, is_remnant=z.stock.is_remnant)
    cmds: list[CutCommand] = []
    stats = {"len": 0.0, "cuts": 0}

    # joylashuvlar, qoldiqlar
    for leaf in sh.root.leaves():
        X, Y = leaf.x + z.ox, leaf.y + z.oy
        if leaf.kind == "P":
            if leaf.pid is None:            # optimizator: shakl navbatidan; qo'lda tahrir: oldindan berilgan
                q = queues.get(leaf.s)
                leaf.pid = q.popleft() if q else ("?", 0)
            pid, uid = leaf.pid
            m.placements.append(Placement(part_id=pid, part_uid=uid, x=round(X, 3), y=round(Y, 3),
                                          length=round(leaf.l, 3), width=round(leaf.w, 3), rotated=leaf.rot))
        elif leaf.l > EPS and leaf.w > EPS:
            kind, business, _area, raw_l, raw_w = _leaf_remnant(leaf, z, mat)
            leaf.rem = 0
            if kind == "remnant":
                counter[0] += 1
                leaf.rem = counter[0]
            m.offcuts.append(Offcut(x=round(X, 3), y=round(Y, 3), length=round(leaf.l, 3), width=round(leaf.w, 3),
                                    kind=kind, number=leaf.rem, business=business,
                                    raw_length=round(raw_l, 3), raw_width=round(raw_w, 3)))

    def walk(node: _N, depth: int) -> None:
        ax = node.axis
        lvl = depth + 1
        if depth == 0:
            clen = z.W if ax == "x" else z.L   # 1-daraja kesishlar xom list bo'ylab
        else:
            clen = node.w if ax == "x" else node.l
        # Torsovka: ildizda (T1) va har 1-daraja polosasida (T2)
        if depth <= 1:
            trim = z.trim_y if ax == "y" else z.trim_x
            if trim > 0:
                cmds.append(CutCommand(code="T", level=lvl, size=round(trim, 2)))
                stats["len"] += clen; stats["cuts"] += 1
        body = [c for c in node.children if not (c.kind == "W" and _extent(c, ax) <= EPS)]
        for i, ch in enumerate(body):
            if ch.kind == "W":
                if ch.rem:
                    cmds.append(CutCommand(code="W", level=lvl, size=round(_extent(ch, ax), 2), ref=f"Д{ch.rem}"))
                if i < len(body) - 1:          # o'rtadagi chiqindi: keyingi bo'lakni undan ajratadigan kesim (W — chiqindi kesimi)
                    stats["len"] += clen; stats["cuts"] += 1
                continue
            # LT/CT qoidasi — onlayn tizim bilan bir xil (X_1015_ONLAYN_AUDIT_MCP.md §12): jadvalning har P/C qatori — bitta
            # arra yurishi (bo'lakning uzoq tomonini ajratadigan kesim), uzunligi — kesilayotgan bo'lakning ko'ndalang o'lchami
            # (clen); propil qo'shilmaydi. Chuqur tugunda chegaraga tegib turgan oxirgi bola ham sanaladi (onlayn geometriyada
            # har stack oxirida ≥ «отступ в конце» qoldiq bo'lib, bu kesim doim bor) — shunda LT = jadval qatorlari yig'indisi.
            stats["len"] += clen; stats["cuts"] += 1
            size = round(_extent(ch, ax), 2)
            if ch.kind == "P":
                cmds.append(CutCommand(code="P", level=lvl, size=size, ref=str(ch.pid[1] if ch.pid else "")))
            else:
                cmds.append(CutCommand(code="C", level=lvl, size=size))
                walk(ch, depth + 1)

    walk(sh.root, 0)
    m.commands = _collapse(cmds)
    m.parts_count = len(m.placements)
    m.cut_length_m = round(stats["len"] / 1000, 3)
    m.cuts_count = stats["cuts"]
    m.parts_area_m2 = round(sum(pl.length * pl.width for pl in m.placements) / 1e6, 4)
    m.sheet_area_m2 = round(z.L * z.W / 1e6, 4)
    m.remnant_area_m2 = round(sum(_off_area(o, mat) for o in m.offcuts if o.business) / 1e6, 4)
    m.strips = [_ser(sh.root, z)]
    m.comment = ""
    return m


def _off_area(o: Offcut, mat: CSMaterialParams) -> float:
    return (o.length * o.width) if mat.remnant_size_incl_trim else (o.raw_length * o.raw_width)


def _ser(n: _N, z: _Zone) -> dict:
    """Daraxtning ixcham JSON ko'rinishi (list koordinatalarida) — chizish va qo'lda tahrir uchun."""
    d = {"x": round(n.x + z.ox, 2), "y": round(n.y + z.oy, 2), "l": round(n.l, 2), "w": round(n.w, 2), "k": n.kind}
    if n.kind == "C":
        d["a"] = n.axis
        if n.gk is not None:
            d["g"] = round(n.gk, 3)
        d["c"] = [_ser(c, z) for c in n.children]
    elif n.kind == "P" and n.pid:
        d["u"] = n.pid[1]
        if n.rot:
            d["o"] = 1
    elif n.kind == "W" and n.rem:
        d["r"] = n.rem
    return d


def _collapse(cmds: Iterable[CutCommand]) -> list[CutCommand]:
    out: list[CutCommand] = []
    for c in cmds:
        if out and (out[-1].code, out[-1].level, out[-1].size, out[-1].ref) == \
                (c.code, c.level, c.size, c.ref) and c.code in ("P", "C"):
            out[-1].count += 1
        else:
            out.append(c.model_copy())
    return out


def _signature(m: CutMap):
    return (m.sheet_id, tuple(sorted((p.part_id, p.x, p.y, p.length, p.width) for p in m.placements)))


def _build_result(sheets: list[_Sheet], queues, p: CSCutParams, mat: CSMaterialParams,
                  pool: Optional[_Pool] = None) -> CuttingResult:
    maps: list[CutMap] = []
    counter = [0]
    for sh in sheets:
        before = counter[0]
        for leaf in sh.root.leaves():      # bir daraxt bir necha list uchun ishlatilishi mumkin — navbatdan qayta
            if leaf.kind == "P":
                leaf.pid = None
        if pool is not None and pool.has_blocks:     # bloklar → detallar (nusxa daraxtda)
            sh = _Sheet(sh.zone, _expand_blocks(sh.root, pool, queues, p.kerf), sh.area, sh.counts_after,
                        sh.how, sh.used)
        m = _build_map(sh, len(maps) + 1, p, mat, counter, queues)
        if maps and _signature(maps[-1]) == _signature(m):
            maps[-1].copies += 1
            counter[0] = before
            continue
        maps.append(m)
    return CuttingResult(maps=maps)


def _finish(res: CuttingResult, mat: CSMaterialParams) -> CuttingResult:
    """Umumiy ko'rsatkichlar. F GibLab usulida: detallar maydoni ÷ (list − деловой qoldiqlar)."""
    for i, m in enumerate(res.maps, 1):
        m.index = i
        if not m.remnant_area_m2 and m.offcuts:
            m.remnant_area_m2 = round(sum(_off_area(o, mat) for o in m.offcuts if o.business) / 1e6, 4)
        denom = m.sheet_area_m2 - m.remnant_area_m2
        m.fill_percent = round(100 * m.parts_area_m2 / denom, 2) if denom > 0 else 0
    res.total_sheets = sum(m.copies for m in res.maps)
    res.total_parts = sum(m.parts_count * m.copies for m in res.maps)
    res.total_cut_length_m = round(sum(m.cut_length_m * m.copies for m in res.maps), 3)
    res.total_cuts = sum(m.cuts_count * m.copies for m in res.maps)
    res.parts_area_m2 = round(sum(m.parts_area_m2 * m.copies for m in res.maps), 4)
    res.material_area_m2 = round(sum(m.sheet_area_m2 * m.copies for m in res.maps), 4)
    res.remnant_area_m2 = round(sum(m.remnant_area_m2 * m.copies for m in res.maps), 4)
    res.material_qty_m2 = round(res.material_area_m2 - res.remnant_area_m2, 4)
    denom = res.material_area_m2 - res.remnant_area_m2
    res.total_fill_percent = round(100 * res.parts_area_m2 / denom, 2) if denom > 0 else 0
    res.remnants = [o for m in res.maps for o in m.offcuts if o.kind == "remnant" for _ in range(m.copies)]
    return res
