"""MebeliX Kroy — (CL) Погонажный раскрой: bir o'lchovli (1D) kroy optimizatori (W11).

Mustaqil yozilgan algoritm (GibLab yoki boshqa dastur kodidan foydalanilmagan). Masala: polosa (xlom) — profil, plintus, bruss —
kerakli uzunlikdagi bo'laklarga kesiladi; detal bo'linmaydi, aylantirilmaydi, faqat 90° ko'ndalang kesim.

Geometriya (birlik — 0.01 mm, hamma hisob butun sonlarda; k — propil, T_s / T_e — boshidagi / oxiridagi torsovka):

    a_s = T_s > 0 ? T_s + k : 0         a_e = T_e > 0 ? T_e + k : 0
    U   = L − a_s − a_e                  (foydali uzunlik; masalan 1600, T 20, k 10 → 1540)
    R   = U − Σp − (n−1)·k  ≥ 0          (sig'ish sharti ⇔ Σ(p + k) ≤ U + k: «og'irlik p + k, sig'im U + k» — to'plam-sumka)

Oxirgi detaldan keyin: R = 0 — oxirgi kesim = oxirgi torsovka kesimi; 0 < R ≤ k — otxod bo'lagi yo'q (qoldiq torsovkaga qo'shiladi);
R > k — otxod bo'lagi `W = R − k` (T_e > 0 bo'lsa «xom» uzunligi W + k + T_e = R + T_e). `waste_incl_trim` (Торцовка отходов): ✓ — otxod
uzunligi W (80), ☐ — R + T_e (110) va oxirgi torsovka kesimi qilinmaydi. W_hisob < `waste_min` — oddiy chiqindi (ajratuvchi kesim yo'q),
≥ `waste_min` — otxod, ≥ `business_min` — деловой otxod (sarfga kirmaydi, omborga yoziladi).
Kesimlar soni: [T_s>0] + (n−1) + (T_e>0 ? 1 + [otxod ∧ ✓] : [R>0]) — LT = kesimlar × polosa eni.

Maqsad funksiyasi (leksikografik; «material» rejimi — foydalanuvchi talabi): 1) hamma detal joylansin; 2) kam material (Σ polosa
uzunligi); 3) ko'proq деловой otxod; 4) kam xil karta (bir xil sxema — C nusxa); 5) kam kesim. `OBJECTIVE = "consumption"` — hujjat
§3.4 tartibi (sarf = material − деловой otxod, so'ng polosalar soni).

Algoritm (deterministik — vaqtga bog'liq tasodif yo'q, byudjet — tugun / iteratsiya soni):
  1) quyi chegara LB = ⌈Σ(p + k) / (U + k)⌉ (eng uzun polosa bo'yicha);
  2) nomzodlar: SHP — ketma-ket «eng zich sxema» (chegaralangan to'plam-sumka DP, Python int bitset: reach |= reach << w) va bir xil
     sxema c marta takrorlanadi; «eng katta detal majburiy» varianti (minimal-slack); FFD — pastki kafolat (natija FFD dan yomon emas);
  3) yaxshilash: eng bo'sh polosalar detallarini bin-completion / DFS bilan bitta kam polosaga qayta joylash (kichik to'plamlar uchun
     aniq yechim); cheksiz turlar orasida qisqaroq polosaga «tushirish»;
  4) eng yaxshisi `_score` bo'yicha tanlanadi.
Polosalar tartibi — ro'yxat tartibi (ustuvorlik): cheklangan sonli (qoldiq) turlar ro'yxat tartibida birinchi ishlatiladi, ketma-ket kelgan
cheksiz (10000) turlar orasidan eng zich sxema beradigani tanlanadi.
"""
from __future__ import annotations

import time
from collections import Counter, deque
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from math import gcd
from typing import Optional, Sequence

from ..i18n import _
from ..models import CLParams, CutCommand, CutMap, CuttingResult, Offcut, Placement, StockSheet

UNIT = 100                 # 1 birlik = 0.01 mm
UNLIMITED = 10000          # StockSheet.qty: 10000 — cheklanmagan
TOL = 0.011                # tekshiruv bag'ishlashi, mm
OBJECTIVE = "material"     # "material" (foydalanuvchi talabi) | "consumption" (hujjat §3.4)
# «Варианты» (W18): xodim solishtirib tanlaydigan maqsadlar. "cuts" — kam kesim (LT): 1) hamma detal joylansin, 2) kam kesim, 3) kam material
OBJECTIVES = ("material", "consumption", "cuts")
F_NET_OF_BUSINESS = False  # F = Σp / L (R4 hisobi); True — Σp / (L − деловой otxod) (CS usuli)

# sifat rejimlari: byudjetlar tugun / iteratsiya sonida (deterministik; 1000 detal uchun fast ≈ 0.2 s, normal ≈ 1 s, max ≈ 4 s)
CFG = {
    "fast": dict(tail_r=3, tail_items=24, nodes=3000, rounds=4, variants=2, conc=20000, shake=20),
    "normal": dict(tail_r=6, tail_items=48, nodes=30000, rounds=12, variants=3, conc=200000, shake=300),
    "max": dict(tail_r=8, tail_items=64, nodes=250000, rounds=40, variants=3, conc=1000000, shake=3000),
}


def u(v: float) -> int:
    """mm → birlik (0.01 mm)."""
    return int(round(float(v) * UNIT))


def mm(x: int) -> float:
    return round(x / UNIT, 3)


def round_half_up(v: float, nd: int = 2) -> float:
    try:
        return float(Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
    except Exception:  # noqa: BLE001
        return round(v, nd)


# ───────────────────────── Kirish / geometriya ─────────────────────────
@dataclass
class LItem:
    """Kroy elementi: detalning bitta nusxasi (`length` — pilniy uzunlik, mm)."""
    part_id: str
    uid: int
    length: float


@dataclass(frozen=True)
class Geom:
    """Bitta polosa turining geometriyasi (birlik 0.01 mm)."""
    L: int
    k: int
    ts: int
    te: int

    @property
    def a_s(self) -> int:
        return self.ts + self.k if self.ts > 0 else 0

    @property
    def a_e(self) -> int:
        return self.te + self.k if self.te > 0 else 0

    @property
    def U(self) -> int:
        return self.L - self.a_s - self.a_e

    @property
    def cap(self) -> int:
        """Sig'im (og'irlik = p + k): U + k."""
        return self.U + self.k


@dataclass(frozen=True)
class Rules:
    waste_min: int
    business_min: int
    incl_trim: bool            # «Торцовка отходов» ✓ — otxod toza uzunligi


def trims_of(cl: CLParams) -> tuple[int, int]:
    """(T_boshi, T_oxiri) birlikda: oxiri — «Минимальный отступ в конце» (berilmasa torsovka qiymati)."""
    ts = u(cl.trim)
    te = u(cl.end_offset) if cl.end_offset is not None else ts
    return ts, te


def rules_of(cl: CLParams) -> Rules:
    return Rules(u(cl.waste_min), u(cl.business_min), bool(cl.waste_incl_trim))


def usable_length(length: float, trim: float, kerf: float, end_offset: Optional[float] = None) -> float:
    """Foydali uzunlik U = L − (T_boshi + k) − (T_oxiri + k); torsovka 0 bo'lgan tomonda `T + k` qo'shilmaydi.
    Tekshiruv: usable_length(1600, 20, 10) = 1540."""
    te = trim if end_offset is None else end_offset
    a_s = trim + kerf if trim > 0 else 0.0
    a_e = te + kerf if te > 0 else 0.0
    return round(length - a_s - a_e, 3)


# ───────────────────────── Bitta polosa tartibi ─────────────────────────
@dataclass(frozen=True)
class Layout:
    xs: tuple[int, ...]        # detallarning boshlanish koordinatalari
    R: int                     # U − Σp − (n−1)k
    sum_p: int
    cuts: int
    off_x: int                 # kesimdan keyingi koordinata (otxod / chiqindi boshlanishi)
    off_kind: str              # "remnant" | "waste" | ""
    off_len: int               # Offcut.length: otxod (W_hisob) yoki chiqindi uzunligi
    off_raw: int               # xom uzunlik (polosa oxirigacha) — omborga shu yoziladi
    business: bool
    end_trim_cut: bool         # otxoddan keyin alohida torsovka kesimi (Торцовка отходов ✓)

    @property
    def business_len(self) -> int:
        return self.off_len if (self.off_kind == "remnant" and self.business) else 0


def layout(g: Geom, pieces: Sequence[int], r: Rules) -> Optional[Layout]:
    """Detallar (berilgan tartibda, birlikda) polosaga joylashadimi? Joylashsa — tartib; aks holda None."""
    n = len(pieces)
    if n == 0:
        return None
    sum_p = sum(pieces)
    R = g.U - sum_p - (n - 1) * g.k
    if R < 0:
        return None
    xs = []
    x = g.a_s
    for p in pieces:
        xs.append(x)
        x += p + g.k
    cuts = (1 if g.ts > 0 else 0) + (n - 1)
    off_kind, off_len, off_raw, business, end_cut = "", 0, 0, False, False
    if g.te > 0:
        cuts += 1                                  # oxirgi detaldan keyingi kesim (R = 0 yoki otxod yo'q bo'lsa — u torsovka kesimi)
        if R > g.k:
            w_net, w_raw = R - g.k, R + g.te
            w = w_net if r.incl_trim else w_raw
            if w >= r.waste_min and w > 0:
                off_kind, off_len, off_raw = "remnant", w, w_raw
                business = w >= r.business_min
                if r.incl_trim:                    # otxod toza uzunlikda: undan keyin alohida torsovka kesimi
                    cuts += 1
                    end_cut = True
        if not off_kind and R > 0:
            off_kind, off_len, off_raw = "waste", R + g.te, R + g.te
    elif R > 0:
        cuts += 1                                  # oxirgi detalni ajratuvchi kesim
        if R > g.k:
            w = R - g.k
            if w >= r.waste_min and w > 0:
                off_kind, off_len, off_raw = "remnant", w, w
                business = w >= r.business_min
            else:
                off_kind, off_len, off_raw = "waste", w, w
    return Layout(tuple(xs), R, sum_p, cuts, x, off_kind, off_len, off_raw, business, end_cut)


# ───────────────────────── Polosa turlari ─────────────────────────
@dataclass
class StripType:
    idx: int                   # kirish ro'yxatidagi (stock) o'rni
    stock: StockSheet
    geom: Geom
    avail: Optional[int]       # None — cheksiz

    @property
    def cap(self) -> int:
        return self.geom.cap


def build_types(stock: Sequence[StockSheet], cl: CLParams) -> list[StripType]:
    ts, te = trims_of(cl)
    k = u(cl.kerf)
    out: list[StripType] = []
    for i, sh in enumerate(stock):
        if sh.qty <= 0 or sh.length <= 0:
            continue
        g = Geom(u(sh.length), k, ts, te)
        if g.U <= 0:
            continue
        out.append(StripType(i, sh, g, None if sh.qty >= UNLIMITED else int(sh.qty)))
    return out


# ───────────────────────── Eng zich sxema (chegaralangan to'plam-sumka) ─────────────────────────
def _shift_union(x: int, w: int, n: int, mask: int) -> int:
    """⋃ i=1..n (x << w·i) & mask — bir xil detaldan 1..n dona qo'shish (O(log n) siljitish)."""
    res, done = 0, 0
    if n <= 0 or not x:
        return 0
    for bit in bin(n)[2:]:
        res = (res | (res << (w * done))) & mask
        done *= 2
        if bit == "1":
            done += 1
            res = (res | (x << (w * done))) & mask
    return res


def _best_pattern_limited(cap: int, dem: dict[int, int], k: int, must: Optional[int], max_types: int) -> tuple[int, dict[int, int]]:
    """`_best_pattern` — «Максимальное количество разновидностей деталей на карте кроя» cheklovi bilan: sxemada ko'pi bilan
    `max_types` xil uzunlik. DP qatlamlari: reach[t] — ko'pi bilan t xil detal bilan erishiladigan yig'indilar (bitset)."""
    base = 0
    chosen: dict[int, int] = {}
    avail = dem
    free = None                                            # `must` uzunligi: turi allaqachon hisoblangan (byudjet sarflamaydi)
    T = max_types
    if must is not None:
        w0 = must + k
        if w0 > cap or dem.get(must, 0) <= 0:
            return 0, {}
        base = w0
        cap -= w0
        chosen[must] = 1
        avail = dict(dem)
        avail[must] -= 1
        free = must
        T -= 1
    groups = sorted((p, c) for p, c in avail.items() if c > 0 and p + k <= cap and (T > 0 or p == free))
    if not groups:
        return base, chosen
    g = cap
    for p, _c in groups:
        g = gcd(g, p + k)
        if g == 1:
            break
    cap_s = cap // g
    mask = (1 << (cap_s + 1)) - 1
    reach = [1] * (T + 1)
    before: list[list[int]] = []
    dims: list[tuple[int, int]] = []
    for p, c in groups:
        w = (p + k) // g
        cc = min(c, cap_s // w)
        dims.append((w, cc))
        before.append(reach)
        if p == free:
            reach = [r | _shift_union(r, w, cc, mask) for r in reach]
        else:
            reach = [reach[0]] + [reach[t] | _shift_union(reach[t - 1], w, cc, mask) for t in range(1, T + 1)]
    best = reach[T].bit_length() - 1
    s, t = best, T
    for gi in range(len(groups) - 1, -1, -1):              # katta detallar afzal (guruhlar o'sish tartibida)
        p, _c = groups[gi]
        w, cc = dims[gi]
        if p == free:
            src, dt = before[gi][t], 0
        elif t > 0:
            src, dt = before[gi][t - 1], 1
        else:
            continue
        for i in range(min(cc, s // w), 0, -1):
            if (src >> (s - w * i)) & 1:
                chosen[p] = chosen.get(p, 0) + i
                s -= w * i
                t -= dt
                break
    return base + best * g, chosen


def _best_pattern(cap: int, dem: dict[int, int], k: int, must: Optional[int] = None, max_types: int = 0) -> tuple[int, dict[int, int]]:
    """`dem` — {detal uzunligi (birlik): qolgan soni}. `cap` — sig'im (U + k). Σ(p + k) ≤ cap bo'lgan, yig'indisi eng katta (qoldiq
    R minimal) to'plam: (yig'indi, {uzunlik: soni}). Teng bo'lsa — kattaroq detallar afzal (kamroq detal = kamroq kesim).
    `must` berilsa — shu uzunlikdagi bitta detal majburiy kiritiladi. Python int bitset: reach |= reach << w.
    `max_types` > 0 — sxemada ko'pi bilan shuncha xil uzunlik (`_best_pattern_limited`)."""
    if max_types > 0:
        return _best_pattern_limited(cap, dem, k, must, max_types)
    base = 0
    chosen: dict[int, int] = {}
    avail = dem
    if must is not None:
        w0 = must + k
        if w0 > cap or dem.get(must, 0) <= 0:
            return 0, {}
        base = w0
        cap -= w0
        chosen[must] = 1
        avail = dict(dem)
        avail[must] -= 1
    groups = sorted((p, c) for p, c in avail.items() if c > 0 and p + k <= cap)
    if not groups:
        return base, chosen
    g = cap
    for p, _c in groups:
        g = gcd(g, p + k)
        if g == 1:
            break
    cap_s = cap // g
    mask = (1 << (cap_s + 1)) - 1
    reach = 1
    layers: list[tuple[int, int, int, int]] = []          # (guruh, take, og'irlik, reach_oldin)
    for gi, (p, c) in enumerate(groups):
        w = (p + k) // g
        cc = min(c, cap_s // w)
        take = 1
        while cc > 0:
            t = min(take, cc)
            wt = w * t
            layers.append((gi, t, wt, reach))
            reach = (reach | (reach << wt)) & mask
            cc -= t
            take <<= 1
    best = reach.bit_length() - 1
    s = best
    cnt = [0] * len(groups)
    for gi, t, wt, before in reversed(layers):             # katta detallarni afzal ko'radi (qatlamlar o'sish tartibida)
        if s >= wt and (before >> (s - wt)) & 1:
            cnt[gi] += t
            s -= wt
    for gi, (p, _c) in enumerate(groups):
        if cnt[gi]:
            chosen[p] = chosen.get(p, 0) + cnt[gi]
    return base + best * g, chosen


def _pattern_for(cap: int, dem: dict[int, int], k: int, largest_first: bool, max_types: int = 0) -> tuple[int, dict[int, int]]:
    if largest_first and dem:
        big = max(dem)
        if big + k <= cap:
            return _best_pattern(cap, dem, k, must=big, max_types=max_types)
        # eng katta detal bu turga sig'maydi — oddiy eng zich sxema
    return _best_pattern(cap, dem, k, max_types=max_types)


def _kinds_ok(pieces: Sequence[int], max_types: int) -> bool:
    """Polosadagi xil uzunliklar soni cheklovdan oshmaydimi (0 — cheklov yo'q)."""
    return max_types <= 0 or len(set(pieces)) <= max_types


# ───────────────────────── Yechim ─────────────────────────
Strip = tuple[int, tuple[int, ...]]            # (tur indeksi — types ro'yxatida, detal uzunliklari kamayish tartibida)


def _norm(pieces: Sequence[int]) -> tuple[int, ...]:
    return tuple(sorted(pieces, reverse=True))


def _shp(types: list[StripType], dem0: dict[int, int], k: int, largest_first: bool,
         max_types: int = 0) -> tuple[list[Strip], dict[int, int]]:
    """Ketma-ket evristika: har qadamda ro'yxat tartibidagi birinchi (cheklanganlar — oxirigacha) turga eng zich sxema tanlanadi va
    detallar tugaguncha C marta takrorlanadi. Qaytaradi: (polosalar, joylanmay qolgan {uzunlik: soni})."""
    dem = {p: c for p, c in dem0.items() if c > 0}
    avail = [t.avail for t in types]
    dead = [False] * len(types)
    out: list[Strip] = []
    while dem:
        step = None
        j = 0
        while j < len(types):
            if dead[j] or avail[j] == 0:
                j += 1
                continue
            if avail[j] is None:                           # ketma-ket kelgan cheksiz turlar: eng zich sxemasini tanlash
                pool = []
                jj = j
                while jj < len(types) and avail[jj] is None:
                    if not dead[jj]:
                        pool.append(jj)
                    jj += 1
                best = None
                for q in pool:
                    s, pat = _pattern_for(types[q].cap, dem, k, largest_first, max_types)
                    if not pat:
                        dead[q] = True
                        continue
                    if best is None or s * types[best[0]].cap > best[1] * types[q].cap:
                        best = (q, s, pat)
                if best is None:
                    j = jj
                    continue
                step = (best[0], best[2])
                break
            s, pat = _pattern_for(types[j].cap, dem, k, largest_first, max_types)
            if not pat:
                dead[j] = True
                j += 1
                continue
            step = (j, pat)
            break
        if step is None:
            break
        j, pat = step
        c = min(dem[p] // n for p, n in pat.items())
        if avail[j] is not None:
            c = min(c, avail[j])
            avail[j] -= c
        c = max(1, c)
        strip = (j, _norm([p for p, n in pat.items() for _ in range(n)]))
        out.extend([strip] * c)
        for p, n in pat.items():
            dem[p] -= n * c
            if dem[p] <= 0:
                del dem[p]
    return out, dem


def _ffd(types: list[StripType], pieces: Sequence[int], k: int) -> tuple[list[Strip], dict[int, int]]:
    """First-Fit-Decreasing (pastki kafolat): detal — birinchi sig'adigan polosaga (segment daraxti: har detal O(log n)); yangi polosa —
    ro'yxat tartibidagi birinchi mos tur."""
    avail = [t.avail for t in types]
    n = len(pieces)
    size = 1
    while size < max(1, n):
        size <<= 1
    tree = [0] * (2 * size)                        # barglar — polosalarning bo'sh joyi (qolgan sig'im), ichki tugunlar — maksimum
    strips: list[list] = []                        # [tur, [detallar], og'irlik yig'indisi]
    left: Counter = Counter()

    def set_leaf(i: int, v: int) -> None:
        i += size
        tree[i] = v
        i >>= 1
        while i:
            tree[i] = max(tree[2 * i], tree[2 * i + 1])
            i >>= 1

    for p in sorted(pieces, reverse=True):
        w = p + k
        if tree[1] >= w:                           # eng chapdagi mos polosa
            i = 1
            while i < size:
                i = 2 * i if tree[2 * i] >= w else 2 * i + 1
            sid = i - size
            s = strips[sid]
            s[1].append(p)
            s[2] += w
            set_leaf(sid, types[s[0]].cap - s[2])
            continue
        for j, t in enumerate(types):
            if (avail[j] is None or avail[j] > 0) and w <= t.cap:
                if avail[j] is not None:
                    avail[j] -= 1
                strips.append([j, [p], w])
                set_leaf(len(strips) - 1, t.cap - w)
                break
        else:
            left[p] += 1
    return [(s[0], _norm(s[1])) for s in strips], dict(left)


def _ffd_limited(types: list[StripType], pieces: Sequence[int], k: int, max_types: int) -> tuple[list[Strip], dict[int, int]]:
    """FFD — xillar soni cheklovi bilan: detal birinchi sig'adigan VA (shu uzunlik allaqachon bor yoki xillar soni < cheklov)
    polosaga qo'yiladi; yangi polosa — ro'yxat tartibidagi birinchi mos tur."""
    avail = [t.avail for t in types]
    strips: list[list] = []                        # [tur, [detallar], og'irlik yig'indisi, {xil uzunliklar}]
    left: Counter = Counter()
    for p in sorted(pieces, reverse=True):
        w = p + k
        for s in strips:
            if types[s[0]].cap - s[2] >= w and (p in s[3] or len(s[3]) < max_types):
                s[1].append(p)
                s[2] += w
                s[3].add(p)
                break
        else:
            for j, t in enumerate(types):
                if (avail[j] is None or avail[j] > 0) and w <= t.cap:
                    if avail[j] is not None:
                        avail[j] -= 1
                    strips.append([j, [p], w, {p}])
                    break
            else:
                left[p] += 1
    return [(s[0], _norm(s[1])) for s in strips], dict(left)


def _downsize(strips: list[Strip], types: list[StripType], k: int) -> list[Strip]:
    """Cheksiz turlar ichida detallar sig'adigan eng qisqa polosa tanlanadi (material tejash)."""
    unl = [j for j, t in enumerate(types) if t.avail is None]
    if len(unl) < 2:
        return strips
    out: list[Strip] = []
    for j, ps in strips:
        if types[j].avail is None:
            sumw = sum(p + k for p in ps)
            best = j
            for q in unl:
                if types[q].cap >= sumw and types[q].geom.L < types[best].geom.L:
                    best = q
            j = best
        out.append((j, ps))
    return out


# ───────────────────────── Aniq yechim (kichik to'plam) ─────────────────────────
class _Budget(Exception):
    pass


def _exact_pack(ws: Sequence[int], cap: int, max_bins: int, budget: list[int]) -> Optional[list[list[int]]]:
    """Og'irliklarni `max_bins` ta `cap` sig'imli savatga joylash (DFS: eng kattasidan boshlab, simmetriya va «aniq mos» dominantligi,
    bo'sh joy chegarasi). Topilsa — savatlar ro'yxati; topilmasa yoki umumiy byudjet (`budget[0]` — tugunlar) tugasa — None."""
    ws = sorted(ws, reverse=True)
    n = len(ws)
    if n == 0:
        return []
    if ws[0] > cap or sum(ws) > cap * max_bins:
        return None
    rem = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        rem[i] = rem[i + 1] + ws[i]
    bins: list[int] = []                           # qolgan sig'imlar
    assign = [0] * n
    smallest = ws[-1]

    def dfs(i: int) -> bool:
        if i == n:
            return True
        budget[0] -= 1
        if budget[0] < 0:
            raise _Budget
        waste = 0
        free = (max_bins - len(bins)) * cap
        for r in bins:                              # hech narsa sig'maydigan savatlarning qoldig'i behuda ketadi
            if r < smallest:
                waste += r
            free += r
        if free - waste < rem[i]:
            return False
        w = ws[i]
        exact = next((b for b, r in enumerate(bins) if r == w), -1)
        if exact >= 0:                              # aniq mos kelish hukmron: faqat shu savat sinaladi
            bins[exact] = 0
            assign[i] = exact
            if dfs(i + 1):
                return True
            bins[exact] = w
            return False
        tried: set[int] = set()
        for b in range(len(bins)):
            r = bins[b]
            if r > w and r not in tried:
                tried.add(r)
                bins[b] -= w
                assign[i] = b
                if dfs(i + 1):
                    return True
                bins[b] += w
        if len(bins) < max_bins:
            bins.append(cap - w)
            assign[i] = len(bins) - 1
            if dfs(i + 1):
                return True
            bins.pop()
        return False

    try:
        ok = dfs(0)
    except _Budget:
        return None
    if not ok:
        return None
    out: list[list[int]] = [[] for _ in bins]
    for i, b in enumerate(assign):
        out[b].append(ws[i])
    return out


def _improve(strips: list[Strip], types: list[StripType], k: int, cfg: dict, lb: int, max_types: int = 0) -> list[Strip]:
    """Eng bo'sh polosalar detallarini bitta kam polosaga qayta joylash (aniq qidiruv; byudjet — umumiy tugunlar soni)."""
    cur = list(strips)
    budget = [cfg["nodes"]]
    for _round in range(cfg["rounds"]):
        if len(cur) <= lb or budget[0] <= 0:
            break
        by_type: dict[int, list[int]] = {}
        for i, (j, _ps) in enumerate(cur):
            by_type.setdefault(j, []).append(i)
        done = False
        for j in sorted(by_type, key=lambda q: (-len(by_type[q]), q)):
            idxs = by_type[j]
            if len(idxs) < 2:
                continue
            cap = types[j].cap
            idxs = sorted(idxs, key=lambda i: (sum(p + k for p in cur[i][1]), i))      # eng bo'sh — birinchi
            for r in range(2, min(cfg["tail_r"], len(idxs)) + 1):
                cand = idxs[:r]
                ws = [p + k for i in cand for p in cur[i][1]]
                if len(ws) > cfg["tail_items"]:
                    break
                if sum(ws) > cap * (r - 1):
                    continue
                packed = _exact_pack(ws, cap, r - 1, budget)
                if packed is not None and max_types and not all(_kinds_ok(b, max_types) for b in packed):
                    packed = None                               # xillar soni cheklovi buziladi — bu qayta joylash olinmaydi
                if packed is not None:
                    drop = set(cand)
                    rest = [s for i, s in enumerate(cur) if i not in drop]
                    new = [(j, _norm([w - k for w in b])) for b in sorted(packed, key=lambda b: -sum(b))]
                    cur = rest + new
                    done = True
                    break
                if budget[0] <= 0:
                    break
            if done or budget[0] <= 0:
                break
        if not done:
            break
    return cur


def _shake(strips: list[Strip], types: list[StripType], k: int, cfg: dict, lb: int, max_types: int = 0) -> list[Strip]:
    """Tasodifiy (deterministik urug'li) r ta bir turdagi polosa detallarini bitta kam polosaga aniq qidiruv bilan qayta joylash —
    `_improve` faqat eng bo'shlarini ko'radi, bu esa turli kombinatsiyalarni sinaydi. Byudjet: `cfg["shake"]` urinish."""
    import random
    rng = random.Random(97531)
    cur = list(strips)
    budget = [cfg["nodes"] * 2]
    for _it in range(cfg["shake"]):
        if len(cur) <= lb or budget[0] <= 0:
            break
        j = cur[rng.randrange(len(cur))][0]
        idxs = [i for i, (jj, _ps) in enumerate(cur) if jj == j]
        if len(idxs) < 3:
            continue
        r = rng.randint(3, min(cfg["tail_r"] + 1, len(idxs)))
        by_slack = sorted(idxs, key=lambda i: (sum(p + k for p in cur[i][1]), i))
        head = by_slack[:max(r, len(by_slack) * 2 // 5)]
        pick = set(rng.sample(head, min(len(head), max(2, r - 1))))
        rest = [i for i in idxs if i not in pick]
        while len(pick) < r and rest:
            pick.add(rest.pop(rng.randrange(len(rest))))
        ws = [p + k for i in pick for p in cur[i][1]]
        cap = types[j].cap
        if len(ws) > cfg["tail_items"] or sum(ws) > cap * (len(pick) - 1):
            continue
        allow = min(4000, budget[0])
        sub = [allow]
        packed = _exact_pack(ws, cap, len(pick) - 1, sub)
        budget[0] -= allow - max(0, sub[0])
        if packed is not None and max_types and not all(_kinds_ok(b, max_types) for b in packed):
            packed = None
        if packed is not None:
            keep = [s for i, s in enumerate(cur) if i not in pick]
            cur = keep + [(j, _norm([w - k for w in b])) for b in sorted(packed, key=lambda b: -sum(b))]
    return cur


def _concentrate(strips: list[Strip], types: list[StripType], k: int, budget: int, max_types: int = 0) -> list[Strip]:
    """Bo'sh joyni jamlash (Fleszar–Hindi usuli): eng bo'sh polosadagi detalni boshqa polosaga ko'chirish (1–0) yoki undan kichigiga
    almashtirish (1–1, boshqa polosa sig'sa) — Σ(to'ldirish²) qat'iy o'sadi (to'xtash kafolati). Bo'shab qolgan polosa olib tashlanadi.
    Qo'shimcha: detalni uzunligi yig'indisi teng ikkita kichigiga almashtirishdan farqli ravishda hech qachon detal soni o'zgarmaydi."""
    bins = [[j, sorted((p + k for p in ps), reverse=True)] for j, ps in strips]
    n = len(bins)
    if n < 2:
        return strips
    fill = [sum(ws) for _j, ws in bins]
    cap = [types[j].cap for j, _ws in bins]
    ops = budget
    changed = True
    while changed and ops > 0:
        changed = False
        order = sorted(range(n), key=lambda i: (cap[i] - fill[i], i), reverse=True)        # eng bo'sh — birinchi
        top = min(n, 80)
        for a in order[:top]:
            if not bins[a][1] or ops <= 0:
                continue
            progressed = True
            while progressed and bins[a][1] and ops > 0:
                progressed = False
                for x in sorted(set(bins[a][1]), reverse=True):
                    best = None                                  # (kamayish, b, y): y = None — ko'chirish
                    for b in range(n):
                        if b == a or not bins[b][1] or fill[b] < fill[a]:
                            continue
                        ops -= 1
                        slack_b = cap[b] - fill[b]
                        if slack_b >= x:
                            cand = (x, -slack_b + x, b, None)    # ko'chirish: A dan x chiqadi (eng zich bin afzal)
                            if max_types and x not in bins[b][1] and len(set(bins[b][1])) >= max_types:
                                cand = None                       # B da yangi xil — cheklovdan oshadi
                        else:
                            cand = None
                            for y in bins[b][1]:
                                if y < x and slack_b + y >= x:
                                    if max_types:                 # almashtirishdan keyin ikkala polosa ham cheklovda qolsin
                                        nb = list(bins[b][1])
                                        nb.remove(y)
                                        na = list(bins[a][1])
                                        na.remove(x)
                                        if len(set(nb + [x])) > max_types or len(set(na + [y])) > max_types:
                                            continue
                                    cand = (x - y, -(slack_b + y - x), b, y)
                                    break                         # y — bin ichida kamayish tartibida: birinchi mos eng katta y
                        if cand is not None and (best is None or cand[:2] > best[:2]):
                            best = cand
                    if best is None:
                        continue
                    _d, _s, b, y = best
                    bins[a][1].remove(x)
                    fill[a] -= x
                    bins[b][1].append(x)
                    fill[b] += x
                    if y is not None:
                        bins[b][1].remove(y)
                        fill[b] -= y
                        bins[a][1].append(y)
                        fill[a] += y
                    bins[b][1].sort(reverse=True)
                    bins[a][1].sort(reverse=True)
                    progressed = changed = True
                    break
    return [(j, _norm([w - k for w in ws])) for j, ws in bins if ws]


# ───────────────────────── Baholash ─────────────────────────
def _score(strips: list[Strip], types: list[StripType], rules: Rules, left: int, objective: Optional[str] = None) -> tuple:
    objective = objective or OBJECTIVE
    mat = bus = cuts = 0
    seen = set()
    for j, ps in strips:
        t = types[j]
        lay = layout(t.geom, ps, rules)
        if lay is None:                              # kutilmagan: sig'maydi — eng yomon baho
            return (1 << 60,)
        mat += t.geom.L
        bus += lay.business_len
        cuts += lay.cuts
        seen.add((j, ps))
    placed = sum(len(ps) for _j, ps in strips)
    if objective == "consumption":
        return (left, mat - bus, mat, len(seen), cuts, len(strips), -placed)
    if objective == "cuts":
        return (left, cuts, mat, -bus, len(seen), len(strips), -placed)
    return (left, mat, -bus, len(seen), cuts, len(strips), -placed)


def lower_bound(piece_lengths: Sequence[float], stock: Sequence[StockSheet], cl: CLParams) -> int:
    """Quyi chegara: LB = ⌈Σ(p + k) / (U + k)⌉ (eng uzun polosa bo'yicha; sig'maydigan detallar hisobga olinmaydi)."""
    types = build_types(stock, cl)
    if not types:
        return 0
    k = u(cl.kerf)
    cap = max(t.cap for t in types)
    tot = sum(u(p) + k for p in piece_lengths if u(p) + k <= cap)
    return -(-tot // cap) if tot else 0


def ffd_strips(piece_lengths: Sequence[float], stock: Sequence[StockSheet], cl: CLParams) -> int:
    """Taqqoslash uchun: FFD yechimidagi polosalar soni (testlar)."""
    types = build_types(stock, cl)
    k = u(cl.kerf)
    s, _left = _ffd(types, [u(p) for p in piece_lengths], k)
    return len(s)


# ───────────────────────── Natija ─────────────────────────
def _collapse(cmds: Sequence[CutCommand]) -> list[CutCommand]:
    out: list[CutCommand] = []
    for c in cmds:
        if out and c.code == "P" and (out[-1].code, out[-1].level, out[-1].size, out[-1].ref) == (c.code, c.level, c.size, c.ref):
            out[-1].count += 1
        else:
            out.append(c.model_copy())
    return out


def make_map(index: int, stock: StockSheet, g: Geom, r: Rules, pieces: Sequence[tuple[int, str, int]], width_mm: float,
             counter: list[int], is_remnant: Optional[bool] = None) -> Optional[CutMap]:
    """Bitta polosa kartasi. `pieces` — [(uzunlik birlikda, part_id, uid)] polosadagi tartibda. Sig'masa — None.
    Torsovkalar kartaga aniq yoziladi: `trim_length` = T_boshi, `end_offset_right` = T_oxiri (mm)."""
    lay = layout(g, [p for p, _pid, _uid in pieces], r)
    if lay is None:
        return None
    m = CutMap(index=index, sheet_id=stock.id, sheet_length=mm(g.L), sheet_width=width_mm,
               is_remnant=stock.is_remnant if is_remnant is None else is_remnant, copies=1)
    m.trim_length = mm(g.ts)
    m.end_offset_right = mm(g.te)
    for (p, pid, uid), x in zip(pieces, lay.xs):
        m.placements.append(Placement(part_id=pid, part_uid=uid, x=mm(x), y=0, length=mm(p), width=width_mm, rotated=False))
    cmds: list[CutCommand] = []
    if g.ts > 0:
        cmds.append(CutCommand(code="T", level=1, size=mm(g.ts)))
    for p, _pid, uid in pieces:
        cmds.append(CutCommand(code="P", level=1, size=mm(p), ref=str(uid)))
    if lay.off_kind == "remnant":
        counter[0] += 1
        m.offcuts.append(Offcut(x=mm(lay.off_x), y=0, length=mm(lay.off_len), width=width_mm, kind="remnant",
                                number=counter[0], business=lay.business, raw_length=mm(lay.off_raw), raw_width=width_mm))
        cmds.append(CutCommand(code="W", level=1, size=mm(lay.off_len), ref=f"Д{counter[0]}"))
        if lay.end_trim_cut:
            cmds.append(CutCommand(code="T", level=1, size=mm(g.te)))
    elif lay.off_kind == "waste":
        m.offcuts.append(Offcut(x=mm(lay.off_x), y=0, length=mm(lay.off_len), width=width_mm, kind="waste", number=0,
                                business=False, raw_length=mm(lay.off_raw), raw_width=width_mm))
    m.commands = _collapse(cmds)
    m.parts_count = len(pieces)
    m.cuts_count = lay.cuts
    m.cut_length_m = round(lay.cuts * width_mm / 1000, 3)
    m.parts_area_m2 = round(lay.sum_p / UNIT * width_mm / 1e6, 4)
    m.sheet_area_m2 = round(g.L / UNIT * width_mm / 1e6, 4)
    m.remnant_area_m2 = round(lay.business_len / UNIT * width_mm / 1e6, 4)
    m.fill_percent = fill_of(lay.sum_p, g.L, lay.business_len)
    m.strips = []
    return m


def fill_of(sum_p: int, L: int, business: int) -> float:
    """F = Σ detal uzunligi ÷ polosa uzunligi (R4: 3100 / 3200 = 96.875 → 96.88 %)."""
    den = L - business if F_NET_OF_BUSINESS else L
    return round_half_up(100 * sum_p / den, 2) if den > 0 else 0.0


def finish_cl(res: CuttingResult, width_mm: float) -> CuttingResult:
    """Umumiy ko'rsatkichlar (karta raqamlari, jami, qoldiqlar)."""
    for i, m in enumerate(res.maps, 1):
        m.index = i
    res.kind = "linear"
    res.total_sheets = sum(m.copies for m in res.maps)
    res.total_parts = sum(m.parts_count * m.copies for m in res.maps)
    res.total_cut_length_m = round(sum(m.cut_length_m * m.copies for m in res.maps), 3)
    res.total_cuts = sum(m.cuts_count * m.copies for m in res.maps)
    res.parts_area_m2 = round(sum(m.parts_area_m2 * m.copies for m in res.maps), 4)
    res.material_area_m2 = round(sum(m.sheet_area_m2 * m.copies for m in res.maps), 4)
    res.remnant_area_m2 = round(sum(m.remnant_area_m2 * m.copies for m in res.maps), 4)
    res.material_qty_m2 = round(res.material_area_m2 - res.remnant_area_m2, 4)
    parts_len = sum(sum(p.length for p in m.placements) * m.copies for m in res.maps)
    mat_len = sum(m.sheet_length * m.copies for m in res.maps)
    bus_len = sum(sum(o.length for o in m.offcuts if o.kind == "remnant" and o.business) * m.copies for m in res.maps)
    res.material_len_m = round(mat_len / 1000, 4)
    res.business_len_m = round(bus_len / 1000, 4)
    den = mat_len - bus_len if F_NET_OF_BUSINESS else mat_len
    res.total_fill_percent = round_half_up(100 * parts_len / den, 2) if den > 0 else 0
    res.remnants = [o for m in res.maps for o in m.offcuts if o.kind == "remnant" for _ in range(m.copies)]
    return res


# ───────────────────────── Asosiy kirish nuqtasi ─────────────────────────
def optimize_linear(items: Sequence[LItem], stock: Sequence[StockSheet], cl: CLParams, *, time_limit: Optional[float] = None,
                    quality: Optional[str] = None, objective: Optional[str] = None) -> CuttingResult:
    """Kroy + «МЗап» (polosa qatorining minimal to'ldirish foizi): shu polosadagi kartalar to'ldirishi chegaradan past bo'lsa,
    polosa soni mos kartalar soniga tushiriladi va kroy qayta bajariladi (ko'pi bilan 3 marta)."""
    res = _optimize_linear_once(items, stock, cl, time_limit=time_limit, quality=quality, objective=objective)
    cur = list(stock)
    for _ in range(3):
        lim = {s.id: s.min_fill_percent for s in cur if getattr(s, "min_fill_percent", None)}
        if not lim:
            return res
        bad = {sid for sid in lim for m in res.maps if m.sheet_id == sid and m.fill_percent + 1e-9 < lim[sid]}
        if not bad:
            return res
        ok_cnt = {sid: sum(m.copies for m in res.maps if m.sheet_id == sid and m.fill_percent + 1e-9 >= lim[sid]) for sid in bad}
        cur = [s.model_copy(update={"qty": min(s.qty, ok_cnt[s.id])}) if s.id in bad else s for s in cur]
        res = _optimize_linear_once(items, [s for s in cur if s.qty > 0], cl, time_limit=time_limit, quality=quality,
                                    objective=objective)
    return res


def _optimize_linear_once(items: Sequence[LItem], stock: Sequence[StockSheet], cl: CLParams, *, time_limit: Optional[float] = None,
                          quality: Optional[str] = None, objective: Optional[str] = None) -> CuttingResult:
    """Kroy. `items` — detal nusxalari (pilniy uzunlik); `stock` — polosalar ro'yxat tartibida (ustuvorlik). `time_limit` —
    soniya: berilsa va u tugasa — qo'shimcha yaxshilash to'xtatiladi (natija shundan keyin deterministik EMAS; standart — None).
    `objective` (W18 «Варианты») — `OBJECTIVES` dan biri: nomzodlarni baholash tartibi. Berilmasa — `OBJECTIVE` va faqat
    yaxshilangan nomzodlar (oddiy «Раскроить» xulqi o'zgarmaydi); berilsa — yaxshilanmagan nomzodlar ham tanlovga qo'shiladi."""
    t0 = time.monotonic()
    cfg = CFG.get(quality or cl.quality, CFG["normal"])
    types = build_types(stock, cl)
    k = u(cl.kerf)
    rules = rules_of(cl)
    width = float(cl.width)
    # «Максимальное количество разновидностей деталей на карте кроя»: xil = pilniy uzunlik (CS da — o'lcham); 0 — cheklanmagan
    mt = max(0, int(getattr(cl, "max_part_types_per_map", 0) or 0))
    res = CuttingResult(kind="linear")
    if not items:
        return finish_cl(res, width)
    # detallar: uzunlik → [(part_id, uid)] (kirish tartibida; bir xil detal nusxalari ketma-ket — «run»lar)
    runs: dict[int, list[list]] = {}
    for it in items:
        run = runs.setdefault(u(it.length), [])
        if run and run[-1][0] == it.part_id and run[-1][1] == it.uid:
            run[-1][2] += 1
        else:
            run.append([it.part_id, it.uid, 1])
    cap_max = max((t.cap for t in types), default=0)
    dem: dict[int, int] = {}
    for p, run in runs.items():
        if p > 0 and p + k <= cap_max:
            dem[p] = sum(r[2] for r in run)
    strips: list[Strip] = []
    if dem and types:
        cands: list[tuple[list[Strip], dict[int, int]]] = [_shp(types, dem, k, False, mt)]
        if cfg["variants"] >= 2:
            cands.append(_shp(types, dem, k, True, mt))
        flat = [p for p, c in dem.items() for _ in range(c)]
        cands.append(_ffd_limited(types, flat, k, mt) if mt else _ffd(types, flat, k))
        lb = lower_bound([p / UNIT for p in flat], stock, cl)
        best = None
        for s, lo in cands:
            s = _downsize(s, types, k)
            pool = [list(s)] if objective is not None else []          # «Варианты»: yaxshilanmagan nomzod ham tanlovda
            if cfg["rounds"] and (time_limit is None or time.monotonic() - t0 < time_limit):
                s = _improve(s, types, k, cfg, lb, mt)
                if len(s) > lb and cfg["conc"]:
                    s = _improve(_concentrate(s, types, k, cfg["conc"], mt), types, k, cfg, lb, mt)
                if len(s) > lb and cfg["shake"]:
                    s = _shake(s, types, k, cfg, lb, mt)
            s = _downsize(s, types, k)
            pool.append(s)
            for cand in pool:
                if mt and not all(_kinds_ok(ps, mt) for _j, ps in cand):
                    continue                                    # himoya: cheklovni buzgan nomzod tanlanmaydi
                sc = _score(cand, types, rules, sum(lo.values()), objective)
                if best is None or sc < best[0]:
                    best = (sc, cand)
        strips = best[1] if best is not None else []
    # bir xil (tur, sxema) polosalar — C nusxa, birinchi uchragan tartibda; kartalar tartibi — polosa ro'yxati tartibi (ustuvorlik:
    # cheklanganlar / qoldiqlar birinchi), bir tur ichida — hosil bo'lish tartibi
    order: list[Strip] = []
    count: dict[Strip, int] = {}
    for s in strips:
        if s not in count:
            count[s] = 0
            order.append(s)
        count[s] += 1
    order.sort(key=lambda s: s[0])

    def take(p: int, n: int) -> list[tuple[str, int]]:
        out: list[tuple[str, int]] = []
        run = runs[p]
        while n > 0 and run:
            head = run[0]
            m = min(n, head[2])
            out.extend([(head[0], head[1])] * m)
            head[2] -= m
            n -= m
            if head[2] == 0:
                run.pop(0)
        return out

    counter = [0]
    maps: list[CutMap] = []
    prev_sig = None
    for s in order:
        j, ps = s
        t = types[j]
        for _c in range(count[s]):
            ids: list[tuple[int, str, int]] = []
            for p in sorted(set(ps), reverse=True):
                ids.extend((p, pid, uid) for pid, uid in take(p, ps.count(p)))
            sig = (j, tuple(uid for _p, _pid, uid in ids))
            if maps and sig == prev_sig:
                maps[-1].copies += 1
                continue
            m = make_map(len(maps) + 1, t.stock, t.geom, rules, ids, width, counter,
                         is_remnant=bool(t.stock.is_remnant or t.stock.source_remnant_id))
            assert m is not None
            maps.append(m)
            prev_sig = sig
    res.maps = maps
    # joylanmagan detallar: navbatlarda qolganlari (sig'maydiganlar ham)
    res.unplaced = [pid for p in sorted(runs) for pid, _uid, n in runs[p] for _ in range(n)]
    finish_cl(res, width)
    res.elapsed_s = round(time.monotonic() - t0, 2)
    return res


# ───────────────────────── Tekshiruv ─────────────────────────
def validate_cl(res: CuttingResult, items: Sequence[LItem], stock: Sequence[StockSheet], cl: CLParams,
                allow_empty: bool = False) -> list[str]:
    """Natijani mustaqil tekshirish: sig'ish (R ≥ 0), propil, torsovka, koordinatalar, otxod tasnifi, statistika, detallar soni,
    polosa miqdori. Xatolar ro'yxati (bo'sh — to'g'ri)."""
    errs: list[str] = []
    sheets = {s.id: s for s in stock}
    k = u(cl.kerf)
    rules = rules_of(cl)
    want_len: dict[str, set[int]] = {}
    for it in items:
        want_len.setdefault(it.part_id, set()).add(u(it.length))
    need = Counter(it.part_id for it in items)
    placed: Counter = Counter()
    used: Counter = Counter()
    ts_def, te_def = trims_of(cl)
    for m in res.maps:
        st = sheets.get(m.sheet_id)
        if st is None:
            errs.append(_("vcl.unknown_sheet", map=m.index, id=m.sheet_id))
            continue
        if abs(m.sheet_length - st.length) > TOL:
            errs.append(_("vcl.sheet_len", map=m.index, a=m.sheet_length, b=st.length))
        if abs(m.sheet_width - cl.width) > TOL:
            errs.append(_("vcl.sheet_width", map=m.index, a=m.sheet_width, b=cl.width))
        used[m.sheet_id] += m.copies
        if not m.placements:
            if not allow_empty:
                errs.append(_("vcl.empty_map", map=m.index))
            continue
        ts = u(m.trim_length) if m.trim_length is not None else ts_def
        te = u(m.end_offset_right) if m.end_offset_right is not None else te_def
        g = Geom(u(m.sheet_length), k, ts, te)
        pls = sorted(m.placements, key=lambda p: p.x)
        pieces: list[int] = []
        for p in pls:
            if abs(p.y) > TOL or abs(p.width - cl.width) > TOL or p.rotated:
                errs.append(_("vcl.bad_place", map=m.index, uid=p.part_uid))
            up = u(p.length)
            if up not in want_len.get(p.part_id, set()):
                errs.append(_("vcl.bad_size", map=m.index, uid=p.part_uid, l=p.length))
            pieces.append(up)
            placed[p.part_id] += m.copies
        lay = layout(g, pieces, rules)
        if lay is None:
            errs.append(_("vcl.no_fit", map=m.index, need=mm(sum(pieces) + (len(pieces) - 1) * k), have=mm(g.U)))
            continue
        for p, x in zip(pls, lay.xs):
            if abs(p.x - x / UNIT) > TOL:
                errs.append(_("vcl.bad_x", map=m.index, uid=p.part_uid, x=p.x, exp=mm(x)))
        rem = [o for o in m.offcuts if o.kind == "remnant"]
        if lay.off_kind == "remnant":
            if len(rem) != 1 or abs(rem[0].length - lay.off_len / UNIT) > TOL or rem[0].business != lay.business \
                    or abs(rem[0].raw_length - lay.off_raw / UNIT) > TOL:
                errs.append(_("vcl.bad_offcut", map=m.index))
        elif rem:
            errs.append(_("vcl.bad_offcut", map=m.index))
        if lay.cuts != m.cuts_count or m.parts_count != len(pieces) \
                or abs(fill_of(lay.sum_p, g.L, lay.business_len) - m.fill_percent) > 0.011 \
                or abs(round(lay.cuts * cl.width / 1000, 3) - m.cut_length_m) > 0.0011:
            errs.append(_("vcl.bad_stats", map=m.index))
    got = placed + Counter(res.unplaced)
    if need != got:
        diff = (need - got) + (got - need)
        errs.append(_("vcl.count", d=dict(list(diff.items())[:5])))
    for sid, n in used.items():
        st = sheets.get(sid)
        if st is not None and st.qty < UNLIMITED and n > st.qty:
            errs.append(_("vcl.sheets_exceeded", size=f"{st.length:g}", n=n, q=st.qty))
    return errs
