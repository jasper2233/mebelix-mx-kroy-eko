"""Ustunli (polosali) list joylash: ustun/polosa ichi aniq 0/1 ryukzak (dinamik dasturlash) bilan to'ldiriladi.

Mebel detallarining ko'pchiligi umumiy o'lchamga ega (masalan, korpus chuqurligi) — bunday detallar bir xil
enli ustunga ustma-ust teriladi. Ochko'z (eng kattasi birinchi) terish ustunda 10–15 % bo'sh joy qoldiradi,
ryukzak esa ustun bo'yini deyarli to'liq to'ldiradigan to'plamni tanlaydi. Natija — optimizatorning qolgan
oilalari bilan bir xil kesish daraxti (_N), shuning uchun buyruqlar, tekshiruv, qo'lda tahrir o'zgarmaydi.

Tuzilma (ustunlar X bo'ylab; polosalar uchun masala transpozitsiya qilinadi):
  1-daraja — ustunlar (eni = biror detal o'lchami), butun list bo'yi bo'ylab;
  2-daraja — ustundagi «qatorlar»: bitta detal (ustun eniga teng) yoki bir nechta detal yonma-yon;
  3-daraja — qatordagi detallar (va o'ngdagi chiqindi);
  4-daraja — qator bo'yidan past detal ostidagi chiqindi (faqat max_rotations ≥ 4 bo'lsa).
Qator turlari: «one» — bitta detal; «row» — bir xil detallar (2–3 ta) yonma-yon; «mix» — turli detallar
(eng baland detal qator bo'yini belgilaydi, qolgan joy ochko'z to'ldiriladi).
"""
from __future__ import annotations

import math
import time
import os
from collections import Counter
from typing import Optional

import numpy as np

EPS = 1e-6
_ENV = os.environ.get
CP_PASSES = int(_ENV("MEBELIX_CP_PASSES", "0") or 0)        # 0 — avtomatik (tajriba uchun sozlamalar)
CP_STACKS = _ENV("MEBELIX_CP_STACKS", "0") != "0"     # standart: faqat chuqur qidiruvda (stacks=True)
CP_COMPOSITE = _ENV("MEBELIX_CP_COMPOSITE", "0") != "0"   # standart: faqat chuqur qidiruvda


def knapsack(entries: list[tuple[int, float, object]], cap: int) -> tuple[float, list]:
    """0/1 ryukzak: entries = [(og'irlik ≥ 1, qiymat, teg)]. Qaytaradi (eng katta qiymat, tanlangan teglar)."""
    if cap <= 0 or not entries:
        return 0.0, []
    dp = np.zeros(cap + 1)
    takes: list = []
    for (wt, v, _tag) in entries:
        if wt > cap or wt <= 0 or v <= 0:
            takes.append(None)
            continue
        cand = dp[: cap + 1 - wt] + v
        mask = cand > dp[wt:] + 1e-9
        if mask.any():
            nd = dp.copy()
            nd[wt:][mask] = cand[mask]
            dp = nd
            takes.append(mask)
        else:
            takes.append(None)
    c = int(np.argmax(dp))
    best = float(dp[c])
    chosen = []
    for i in range(len(entries) - 1, -1, -1):
        m = takes[i]
        if m is None:
            continue
        wt = entries[i][0]
        if c >= wt and m[c - wt]:
            chosen.append(entries[i][2])
            c -= wt
    return best, chosen


def _bundles(n: int) -> list[int]:
    """Cheklangan sonni ikkilik bo'laklarga ajratish (1, 2, 4, …, qoldiq) — 0/1 ryukzak uchun."""
    out, k = [], 1
    while n > 0:
        t = min(k, n)
        out.append(t)
        n -= t
        k *= 2
    return out


class Row:
    """Ustundagi bitta qator turi. cells — chapdan o'ngga katakchalar; har katakcha — ustma-ust terilgan
    detallar [(si, a, b, r)] (bir xil en b; bitta detal — oddiy katakcha). h — qator bo'yi,
    t — nusxalar soni (ryukzak bo'lagi)."""
    __slots__ = ("kind", "h", "cells", "t", "need", "area", "value", "wused")

    def __init__(self, kind: str, h: float, cells: tuple, wt: list[float], kerf: float, t: int = 1):
        self.kind, self.h, self.cells, self.t = kind, h, cells, t
        need: dict[int, int] = {}
        area = value = 0.0
        wused = 0.0
        for k, cell in enumerate(cells):
            wused += cell[0][2] + (kerf if k else 0.0)
            for p in cell:
                need[p[0]] = need.get(p[0], 0) + 1
                ab = p[1] * p[2]
                area += ab
                value += ab * wt[p[0]]
        self.need, self.area, self.value, self.wused = need, area, value, wused

    def with_t(self, t: int) -> "Row":
        r = Row.__new__(Row)
        r.kind, r.h, r.cells, r.t, r.need, r.area, r.value, r.wused = self.kind, self.h, self.cells, t, self.need, \
            self.area, self.value, self.wused
        return r


class ColPacker:
    """Bitta list (foydali zona) uchun ustunli joylash.
    transposed=False: ustunlar X bo'ylab (ildiz o'qi 'x'); transposed=True: polosalar Y bo'ylab (ildiz o'qi 'y').
    weights — detal turlari vazni (qiymat = maydon × vazn); berilmasa hammasi 1."""

    MIX_HEIGHTS = 24          # aralash qator uchun sinaladigan eng ko'p qator bo'ylari

    def __init__(self, shapes, UL: float, UW: float, kerf: float, min_trim: float, levels: int,
                 transposed: bool, min_w: float = 0.0, max_w: float = 0.0, weights=None, stacks: bool = False,
                 edge_ok: bool = True):
        self.shapes = shapes
        self.wt = list(weights) if weights is not None else [1.0] * len(shapes)
        self.kerf, self.mt, self.levels, self.tr = kerf, min_trim, max(2, levels), transposed
        self.E = UW if transposed else UL          # ustunlar shu o'q bo'ylab teriladi
        self.C = UL if transposed else UW          # ustun bo'yi
        self.min_w, self.max_w = min_w or 0.0, max_w or 0.0
        self.edge_ok = edge_ok                     # zona oxiri list cheti (tor qirindi propilga ketishi mumkin)
        self.dl: Optional[float] = None            # joriy pack() chaqiruvining muddati (o'tsa — to'xtaydi)
        self.opts = []
        for sh in shapes:
            # (b — ustun eni bo'ylab, a — ustun bo'yi bo'ylab, haqiqiy aylantirish belgisi)
            o = [(sh.l, sh.w, False)] if not transposed else [(sh.w, sh.l, False)]
            if sh.rot and abs(sh.l - sh.w) > EPS:
                o.append((sh.w, sh.l, True) if not transposed else (sh.l, sh.w, True))
            self.opts.append(o)
        self._cache: dict = {}
        # ustma-ust katakchali qatorlar: sekinroq, shuning uchun faqat chuqur (bir listga sig'dirish) qidiruvda
        self.stacks = (stacks or CP_STACKS) and len(shapes) <= 60
        self.composite = stacks or CP_COMPOSITE          # mazmuniga qarab toraytiriladigan ustunlar (chuqur qidiruv)

    def _gap_ok(self, gap: float, edge: bool) -> bool:
        return gap <= EPS or edge or gap >= self.mt - EPS

    # ── qatorlar ──
    def _rows(self, w: float, counts: list[int], edge: bool) -> list[Row]:
        C, kerf, wt = self.C, self.kerf, self.wt
        three, four = self.levels >= 3, self.levels >= 4
        rows: list[Row] = []
        fit: list[tuple[int, float, float, bool]] = []          # (si, a, b, r) — ustunga sig'adigan yo'nalishlar
        for si, n in enumerate(counts):
            if n <= 0:
                continue
            best = None
            for (b, a, r) in self.opts[si]:
                if b > w + EPS or a > C + EPS:
                    continue
                fit.append((si, a, b, r))
                gap = w - b
                if gap > EPS and not (three and self._gap_ok(gap, edge)):
                    continue
                if best is None or b > best[1] + EPS:
                    best = (a, b, r)
            if best is None:
                continue
            a, b, r = best
            for t in _bundles(n):
                rows.append(Row("one", a, (((si, a, b, r),),), wt, kerf, t))
            if three:
                for m in (2, 3):
                    tot = m * b + (m - 1) * kerf
                    if n < m or tot > w + EPS or not self._gap_ok(w - tot, edge):
                        continue
                    for t in _bundles(n // m):
                        rows.append(Row("row", a, (((si, a, b, r),),) * m, wt, kerf, t))
        if three and len(fit) >= 2:
            rows += self._mixed(w, counts, edge, fit, four)
            if four and self.stacks:
                rows += self._stacked(w, counts, edge, fit)
        return rows

    def _mixed(self, w: float, counts: list[int], edge: bool, fit, four: bool) -> list[Row]:
        """Aralash qatorlar: har qator bo'yi h uchun — eng keng h-baland detal (yetakchi) + qolgan joyga
        bo'yi ≤ h (4-daraja bo'lmasa — aynan h) detallar, balanddan pastga, keng birinchi."""
        kerf = self.kerf
        nh = max(6, min(self.MIX_HEIGHTS, 600 // max(1, len(fit))))
        heights = sorted({round(a, 3) for (_si, a, _b, _r) in fit}, reverse=True)[:nh]
        order = sorted(fit, key=lambda f: (-f[1], -f[2]))
        out: list[Row] = []
        seen: set = set()
        for h in heights:
            lead = None
            for f in order:
                if abs(f[1] - h) <= EPS and (lead is None or f[2] > lead[2]):
                    lead = f
            if lead is None:
                continue
            left = {lead[0]: counts[lead[0]] - 1}
            parts = [lead]
            used = lead[2]
            for f in order:
                si, a, b, r = f
                if a > h + EPS or (not four and a < h - EPS):
                    continue
                if EPS < h - a < self.mt - EPS:
                    continue                 # detal ostida minimal obrezkadan yupqa tilim qolardi
                avail = left.get(si, counts[si])
                while avail > 0 and used + kerf + b <= w + EPS:
                    parts.append(f)
                    used += kerf + b
                    avail -= 1
                left[si] = avail
            while len(parts) > 1 and not self._gap_ok(w - used, edge):
                used -= parts[-1][2] + kerf
                parts.pop()
            if len(parts) < 2 or not self._gap_ok(w - used, edge):
                continue
            if len({(p[0], p[3]) for p in parts}) < 2:
                continue                     # bir xil detallar — «row» turi bilan qoplangan
            key = tuple(sorted((p[0], p[3]) for p in parts))
            if key in seen:
                continue
            seen.add(key)
            out.append(Row("mix", h, tuple((p,) for p in parts), self.wt, kerf, 1))
        return out

    def _stacked(self, w: float, counts: list[int], edge: bool, fit) -> list[Row]:
        """Ustunli qatorlar (4–5-daraja): qator bo'yini belgilovchi yetakchi detal + yonida bir xil enli
        detallar ustma-ust terilgan katakchalar (masalan 154 enli ikki detal 400 + 400 bitta 900 li qatorda).
        Har katakcha — qator bo'yiga sig'adigan eng zich ustun; katakchalar zichlik bo'yicha ochko'z tanlanadi."""
        kerf, mt = self.kerf, self.mt
        nh = max(4, min(12, 400 // max(1, len(fit))))
        heights = sorted({round(a, 3) for (_si, a, _b, _r) in fit}, reverse=True)[:nh]
        by_b: dict[float, list] = {}
        for f in fit:
            by_b.setdefault(round(f[2], 3), []).append(f)
        for lst in by_b.values():
            lst.sort(key=lambda f: -f[1])
        out: list[Row] = []
        seen: set = set()
        for h in heights:
            lead = None
            for f in fit:
                if abs(f[1] - h) <= EPS and (lead is None or f[2] > lead[2]):
                    lead = f
            if lead is None:
                continue
            left = counts[:]
            left[lead[0]] -= 1
            cells: list[tuple] = [(lead,)]
            used = lead[2]
            while True:
                R = w - used - kerf
                best = None
                for b, group in by_b.items():
                    if b > R + EPS:
                        continue
                    stack: list = []
                    hu = 0.0
                    for f in group:
                        n = left[f[0]] - sum(1 for q in stack if q[0] == f[0])
                        while n > 0 and hu + (kerf if stack else 0.0) + f[1] <= h + EPS:
                            hu += (kerf if stack else 0.0) + f[1]
                            stack.append(f)
                            n -= 1
                    while stack and EPS < h - hu < mt - EPS:
                        q = stack.pop()
                        hu -= q[1] + (kerf if stack else 0.0)
                    if not stack:
                        continue
                    val = sum(q[1] * q[2] * self.wt[q[0]] for q in stack)
                    dens = val / (b * h)
                    if best is None or (dens, val) > best[0]:
                        best = ((dens, val), b, tuple(stack))
                if best is None:
                    break
                _k, b, stack = best
                cells.append(stack)
                used += kerf + b
                for q in stack:
                    left[q[0]] -= 1
            while len(cells) > 1 and not self._gap_ok(w - used, edge):
                used -= cells[-1][0][2] + kerf
                cells.pop()
            if len(cells) < 2 or not self._gap_ok(w - used, edge) or all(len(c) == 1 for c in cells):
                continue                     # ustma-ust katakcha yo'q — «mix» turi bilan qoplangan
            key = tuple(sorted((q[0], q[3]) for c in cells for q in c))
            if key in seen:
                continue
            seen.add(key)
            out.append(Row("stack", h, tuple(cells), self.wt, kerf, 1))
        return out

    def column(self, w: float, counts: list[int], edge: bool) -> tuple[float, list[Row]]:
        """w enli ustunni ryukzak bilan to'ldirish. edge — ustun list chetiga tegadi (tor qirindiga ruxsat).
        Qaytaradi (vaznli qiymat, qatorlar)."""
        key = (round(w, 3), edge, tuple(counts))
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        kerf, C = self.kerf, self.C
        cap = int(math.floor(C + kerf + 1e-6))
        # Takroriy ryukzak: tanlangan qatorlar bir detalni talashsa, yo'qotilgan joy qolgan sonlar bilan
        # qayta yaratilgan qatorlar bilan to'ldiriladi (masalan, ikkinchi qatorning yetakchisi band bo'lsa).
        left = counts[:]
        kept_all: list[Row] = []
        total = 0.0
        for _pass in range(CP_PASSES or (2 if self.stacks else 1)):
            rows = self._rows(w, left, edge)
            if not rows or cap <= 0:
                break
            entries = [(int(math.ceil(r.h + kerf - 1e-6)) * r.t, r.value * r.t, r) for r in rows]
            _v, chosen = knapsack(entries, cap)
            val, kept = self._realize(chosen, left)
            if not kept:
                break
            kept_all += kept
            total += val
            for r in kept:
                for si, k in r.need.items():
                    left[si] -= k * r.t
                cap -= int(math.ceil(r.h + kerf - 1e-6)) * r.t
            if len(kept) == len(chosen) and all(a.t == b.t for a, b in zip(sorted(kept, key=id), sorted(chosen, key=id))):
                break                        # ziddiyat yo'q — qayta urinish shart emas
        out: tuple[float, list[Row]] = (total, kept_all)
        self._cache[key] = out
        return out

    @staticmethod
    def _realize(chosen: list[Row], counts: list[int]) -> tuple[float, list[Row]]:
        """Tanlangan qatorlar birgalikda mavjud sonlardan oshmasin (turli qator turlari bir detalni talashishi
        mumkin): qimmatlisidan boshlab, sig'adigan nusxalar soni bilan."""
        left = counts[:]
        keep: list[Row] = []
        val = 0.0
        for r in sorted(chosen, key=lambda r: -r.value):
            t = r.t
            for si, k in r.need.items():
                t = min(t, left[si] // k)
            if t <= 0:
                continue
            for si, k in r.need.items():
                left[si] -= k * t
            keep.append(r if t == r.t else r.with_t(t))
            val += r.value * t
        return val, keep

    @staticmethod
    def consume(counts: list[int], rows: list[Row]) -> None:
        for r in rows:
            for si, k in r.need.items():
                counts[si] -= k * r.t

    @staticmethod
    def area_of(rows: list[Row]) -> float:
        return sum(r.area * r.t for r in rows)

    MAX_WIDTHS = 20           # bir qadamda sinaladigan eng ko'p ustun eni (maydon salohiyati bo'yicha)

    def _widths(self, counts, R: float, first: bool) -> list[float]:
        pot: dict[float, float] = {}
        for si, n in enumerate(counts):
            if n <= 0:
                continue
            for (b, a, _r) in self.opts[si]:
                if b <= R + EPS and a <= self.C + EPS:
                    if first and ((self.min_w and b < self.min_w - EPS) or (self.max_w and b > self.max_w + EPS)):
                        continue
                    k = round(b, 3)
                    pot[k] = pot.get(k, 0.0) + n * a * b * self.wt[si]
        if len(pot) > self.MAX_WIDTHS:
            top = sorted(pot.items(), key=lambda kv: -kv[1])[: self.MAX_WIDTHS]
            return sorted((k for k, _v in top), reverse=True)
        return sorted(pot, reverse=True)

    # ── list ──
    def _late(self) -> bool:
        return self.dl is not None and time.monotonic() > self.dl

    def pack(self, counts: list[int], look: int = 3, mode: str = "greedy", deadline: Optional[float] = None):
        """Qaytaradi (ustunlar [(x, en, qatorlar)], vaznli qiymat, qolgan sonlar) yoki None.
        mode: greedy — samaradorlik bo'yicha ketma-ket (look — oldindan ko'rish nomzodlari);
        knap — ustunlar to'plami ham ryukzak bilan (list uzunligi aniq to'lishi uchun).
        deadline o'tsa — oldindan ko'rish to'xtaydi, list o'sha joyida yakunlanadi (to'liq bo'lmagan natija)."""
        c = counts[:]
        self.dl = deadline
        try:
            if mode == "knap":
                cols, val = self._fill_knap(c, 0.0)
            else:
                cols, val = self._fill(c, 0.0, look, True)
        finally:
            self.dl = None
        if not cols:
            return None
        return cols, val, c

    def pack_dfs(self, counts: list[int], deadline: float, beam: int = 4):
        """Ustunlar ketma-ketligini chuqurlik bo'yicha qidirish (har qadamda samaradorligi eng yuqori `beam` ta
        ustun eni), maydon chegarasi bilan kesib. Hammasi sig'sa — darhol to'xtaydi. Natija pack() kabi."""
        import time as _t
        kerf, C, E = self.kerf, self.C, self.E
        areas = [sh.l * sh.w for sh in self.shapes]
        total = sum(a * n for a, n in zip(areas, counts))
        best = [0.0, None, None]                 # maydon, ustunlar, qolgan sonlar
        seen: dict = {}

        def dfs(x: float, c: list[int], area: float, cols: list) -> bool:
            if area > best[0] + 1e-6:
                best[0], best[1], best[2] = area, list(cols), c[:]
            if area >= total - 1e-6:
                return True
            R = E - x
            if R <= EPS or _t.monotonic() > deadline:
                return False
            if area + min(total - area, R * C) <= best[0] + 1e-6:
                return False
            key = (round(x, 1), tuple(c))
            if seen.get(key, -1.0) >= area - 1e-6:
                return False
            seen[key] = area
            scored = []
            for w in self._widths(c, R, True):
                edge = self.edge_ok and R - w <= kerf + EPS
                val, rows = self.column(w, c, edge)
                if val > 0:
                    scored.append((val / (w * C), val, w, rows, edge))
            scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
            for eff, val, w, rows, edge in scored[:beam]:
                c2 = c[:]
                self.consume(c2, rows)
                cols.append((x, (R if (edge and self.levels >= 3) else w), rows))
                if dfs(x + w + kerf, c2, area + self.area_of(rows), cols):
                    return True
                cols.pop()
            return False

        dfs(0.0, counts[:], 0.0, [])
        if not best[1]:
            return None
        return best[1], best[0], best[2]

    def _fill(self, c: list[int], x0: float, look: int, top: bool):
        kerf = self.kerf
        cols: list = []
        total = 0.0
        x = x0
        while True:
            R = self.E - x
            if R <= EPS or self._late():
                break
            scored = []
            for w in self._widths(c, R, True):
                val, rows = self.column(w, c, self.edge_ok and R - w <= kerf + EPS)
                if val <= 0:
                    continue
                scored.append((val / (w * self.C), val, w, rows))
            comp = self._composite(c, R) if self.composite else None
            if comp is not None:
                scored.append(comp)
            if not scored:
                break
            scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
            pick = scored[0]
            if top and look > 1 and len(scored) > 1:
                best_tot = -1.0
                for cand in scored[:look]:
                    if self._late():
                        break
                    c2 = c[:]
                    self.consume(c2, cand[3])
                    _k, rest = self._fill(c2, x + cand[2] + kerf, 1, False)
                    tot = cand[1] + rest
                    if tot > best_tot + 1e-6:
                        best_tot, pick = tot, cand
            _e, val, w, rows = pick
            self.consume(c, rows)
            # list chetiga propildan yaqin qolgan ustun chetgacha cho'ziladi (oraliq qirindi propilga ketadi)
            cols.append((x, R if (self.edge_ok and R - w <= kerf + EPS and self.levels >= 3) else w, rows))
            total += val
            x += w + kerf
        return cols, total

    def _composite(self, c: list[int], R: float):
        """«Сложная полоса»: ustun butun qolgan joy bilan to'ldiriladi, so'ng eng keng qatorgacha toraytiriladi
        (eni biror detal o'lchami emas, mazmuniga qarab). Qaytaradi (samaradorlik, qiymat, en, qatorlar) yoki None."""
        if self.levels < 3 or R <= EPS or (self.min_w and R < self.min_w - EPS):
            return None
        val, rows = self.column(R, c, True)
        if val <= 0 or not rows:
            return None
        u = max(r.wused for r in rows)
        if u >= R - EPS:
            return None                      # torayish yo'q — oddiy nomzodlar orasida bor
        ok = all(u - r.wused <= EPS or u - r.wused >= self.mt - EPS for r in rows)
        wc = u if ok else min(R, u + self.mt)
        if R - wc <= self.kerf + EPS:
            return None
        if self.max_w and wc > self.max_w + EPS:
            return None
        return (val / (wc * self.C), val, wc, rows)

    def _fill_knap(self, c: list[int], x0: float):
        kerf, E = self.kerf, self.E
        R = E - x0
        cands = []
        for w in self._widths(c, R, True):
            val, rows = self.column(w, c, False)
            if val <= 0:
                continue
            need: Counter = Counter()
            for r in rows:
                for si, k in r.need.items():
                    need[si] += k * r.t
            m = min((c[si] // n for si, n in need.items() if n > 0), default=0)
            m = min(m, int((R + kerf + EPS) // (w + kerf)))
            if m > 0:
                cands.append((w, val, m))
        if not cands:
            return [], 0.0
        entries = []
        for i, (w, val, m) in enumerate(cands):
            wt = int(math.ceil(w + kerf - 1e-6))
            for t in _bundles(m):
                entries.append((wt * t, val * t, (i, t)))
        _v, chosen = knapsack(entries, int(math.floor(R + kerf + 1e-6)))
        plan: list[int] = []
        for (i, t) in chosen:
            plan += [i] * t
        plan.sort(key=lambda i: (-cands[i][1] / cands[i][0], -cands[i][0]))
        cols, total, x = [], 0.0, x0
        for i in plan:
            w = cands[i][0]
            if x + w > E + EPS:
                continue
            edge = self.edge_ok and (E - x - w) <= kerf + EPS
            val, rows = self.column(w, c, edge)
            if val <= 0:
                continue
            self.consume(c, rows)
            cols.append((x, E - x if (edge and self.levels >= 3) else w, rows))
            total += val
            x += w + kerf
        more, v2 = self._fill(c, x, 1, False)
        return cols + more, total + v2
