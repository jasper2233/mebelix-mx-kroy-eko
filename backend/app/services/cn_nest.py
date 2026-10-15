"""(CN) Nesting optimizatori (W16): kontur detallarni listga zich joylash. Sof Python + numpy (shapely / scipy yo'q).

ALGORITM (T_W16_CN.md §4). «Pastki-chap» evristikasi, RASTER asosida:
  1. Foydali zona (list − `margin`) `c` mm li kataklarga bo'linadi. Har detal-burilish uchun KONSERVATIV niqob (`raster_rings`):
     detal bilan kesishgan har bir katak niqobga kiradi (ichki teshiklar — bo'sh). Detallar orasidagi talab etilgan masofa `spacing`
     katak-kvadratlari masofasi bilan o'lchanadigan yadro (`dilate`) orqali egallangan xaritaga qo'shiladi: ikki detalning niqoblari
     yadro bo'yicha kesishmasa — haqiqiy konturlar orasidagi masofa ≥ spacing (isbot: modul oxiridagi izoh). Shuning uchun joylash
     TO'G'RILIGI raster aniqligiga bog'liq emas (faqat zichligi); mustaqil tekshiruvchi — `cn_validate` (aniq poligon geometriyasi).
  2. Joylash: detal (kattadan kichikka) har ruxsat etilgan burchakda sinab ko'riladi; mumkin bo'lgan barcha o'rinlar xaritasi
     (to'rtburchak niqob — integral tasvir, umumiy niqob — FFT korrelyatsiyasi) hisoblanadi; eng «chap-yuqori» (yoki «yuqori-chap») o'rin
     tanlanadi: kalit = (o'rovchi to'rtburchak oxiri, ikkinchi koordinata). Ichki bo'shliqlarga (detal teshiklariga) kichik detallar
     o'zi tushadi — ular eng chapdagi mumkin bo'lgan o'rin bo'lgani uchun.
  3. Bir nechta urinish (tartib / yo'nalish / urug'li tasodifiy o'zgarishlar), eng yaxshisi tanlanadi. Hamma narsa deterministik:
     ish byudjeti sinovlar soni bilan beriladi, vaqt chegarasi (`time_limit`) faqat himoya (oshsa — shu paytgacha eng yaxshi natija).
  4. Bir xil sxemali ketma-ket listlar (bir xil sxema takrorlanadigan) `copies` bilan bitta kartaga birlashtiriladi — bu avtomatik hisobga teng.
  5. Qoldiqlar — `cn_free.free_rectangles` (bo'sh joydagi eng katta to'rtburchaklar, shu jumladan detal ichki kesimlarida).

CHEKLOVLAR (ochiq): raster — zichlik katak o'lchamiga bog'liq (odatda ≤ 1–2 % maydon yo'qotish); NFP yo'q — «sirpanish» yo'q;
ko'zgu aks ettirish yo'q; erkin burchak (`rot_step`) ko'p urinish vaqtini oshiradi; parallel jarayonlar yo'q.

IZOH (masofa isboti). Niqob M_i — detal i bilan kesishgan kataklar; Dil(M) — M ning har bir katagidan kvadratlar-masofasi < spacing bo'lgan
kataklar. Agar M_i ∩ Dil(M_j) = ∅ bo'lsa, i ning har bir katagi j ning har bir katagidan kvadratlar-masofasi bo'yicha ≥ spacing da; detal i
nuqtalari o'z kataklari ichida, j niki ham — demak ular orasidagi masofa ≥ spacing. Konturdagi yoy xatosi (`arc_tol`) alohida:
chaqiruvchi `spacing` ga arc_tol ni qo'shib beradi.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Optional

import numpy as np

from . import cn_geometry as G

UNLIMITED = 10000
CELL_CHOICES = (1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0)
QUALITY = {                      # ish byudjeti (deterministik): maqsadli kataklar soni, sinovlar, vaqt chegarasi (s)
    "fast": dict(cells=70_000, trials=3, time=3.0),
    "normal": dict(cells=220_000, trials=8, time=10.0),
    "max": dict(cells=600_000, trials=20, time=40.0),
}
FFT_CACHE_BYTES = 96 * 1024 * 1024
WINDOW_BUCKET = 32               # FFT oynasi shu kataklarga yaxlitlanadi (kesh kalitlari barqaror)


class NestCancelled(Exception):
    """Foydalanuvchi hisobni to'xtatdi."""


# ───────────────────────── Kirish / chiqish ─────────────────────────
@dataclass
class NestPart:
    """Detal turi: shakl, soni, ruxsat etilgan burchaklar."""
    key: str
    uid: int
    shape: G.Shape
    qty: int
    angles: list[float]


@dataclass
class NestSheet:
    key: str
    length: float
    width: float
    qty: int = UNLIMITED


@dataclass
class NestParams:
    spacing: float                       # detallar orasidagi eng kam masofa (asbob + masofa + yoy xatosi)
    margin: float = 5.0                  # kontur — list chetigacha
    quality: str = "normal"
    time_limit: float = 0.0              # 0 — darajaga mos
    seed: int = 20240601
    max_trials: int = 0                  # 0 — darajaga mos
    stop_at_bound: bool = True           # listlar soni quyi chegaraga yetsa sinovlarni to'xtatish (test: False — hamma sinov turlari)
    order: str = "auto"                  # "auto" — tartiblar optimizator tanlaydi; "list" — detallar ro'yxati tartibida (foydalanuvchi saralagan)


@dataclass
class PlacedItem:
    part: int                            # NestPart indeksi
    angle: float
    x: float                             # aylantirilgan shakl o'rovchi to'rtburchagining chap-yuqori burchagi (list koordinatalari)
    y: float
    w: float = 0.0                       # o'rovchi to'rtburchak o'lchami (aylantirilgan)
    h: float = 0.0


@dataclass
class Layout:
    sheet: int                           # NestSheet indeksi
    copies: int
    items: list[PlacedItem]


@dataclass
class NestOutcome:
    layouts: list[Layout]
    unplaced: list[int]                  # NestPart indekslari (har nusxa uchun bitta)
    info: dict


def allowed_angles(grain: bool, rot90: bool, rot_step: float, use_grain: bool) -> list[float]:
    """Detal uchun ruxsat etilgan burchaklar (gradus, soat mili bo'yicha). Ткт ✓ (va `use_grain`) — faqat 0° va 180° (rot90 bo'lsa)."""
    angs = {0.0}
    if rot90:
        angs |= {90.0, 180.0, 270.0}
    if rot_step and rot_step > 0:
        k = 1
        while k * rot_step < 360.0 - 1e-9:
            angs.add(round(k * rot_step, 6))
            k += 1
    if grain and use_grain:
        angs = {a for a in angs if abs(a) < 1e-9 or abs(a - 180.0) < 1e-9}
    return sorted(angs)


# ───────────────────────── Raster ─────────────────────────
def raster_rings(rings: list[G.Ring], c: float, ox: float = 0.0, oy: float = 0.0, split: bool = False):
    """Konservativ niqob: halqalar (tashqi + ichki; juft-toq qoidasi) bilan kesishgan kataklar. Katak (i, j) = [ox + i·c, ox + (i+1)·c] ×
    [oy + j·c, oy + (j+1)·c]. Qaytaradi: (niqob (h, w) bool, i0, j0) — niqobning chap-yuqori katagi (i0, j0).
    split=True: (markazi ichkarida bo'lgan kataklar, chegara tegadigan kataklar, i0, j0)."""
    pts = [np.asarray(r, dtype=float) for r in rings if len(r) >= 3]
    allp = np.vstack(pts)
    minx, miny = allp[:, 0].min() - ox, allp[:, 1].min() - oy
    maxx, maxy = allp[:, 0].max() - ox, allp[:, 1].max() - oy
    i0, j0 = int(math.floor(minx / c + 1e-12)), int(math.floor(miny / c + 1e-12))
    i1, j1 = int(math.ceil(maxx / c - 1e-12)), int(math.ceil(maxy / c - 1e-12))
    w, h = max(1, i1 - i0), max(1, j1 - j0)
    parity = np.zeros(h * (w + 1), dtype=np.int32)
    touch = np.zeros((h, w), dtype=bool)
    step = c / 4.0
    delta = step / 2.0 + 1e-9
    for p in pts:
        x1 = p[:, 0] - ox - i0 * c
        y1 = p[:, 1] - oy - j0 * c
        x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
        # --- ichki qism: skanlash chiziqlari (katak markazlari) bilan kesishish parityi ---
        ymin, ymax = np.minimum(y1, y2), np.maximum(y1, y2)
        r0 = np.clip(np.ceil(ymin / c - 0.5 - 1e-12).astype(np.int64), 0, h)
        r1 = np.clip(np.ceil(ymax / c - 0.5 - 1e-12).astype(np.int64), 0, h)
        cnt = np.maximum(r1 - r0, 0)
        tot = int(cnt.sum())
        if tot:
            eidx = np.repeat(np.arange(len(x1)), cnt)
            rows = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt) + r0[eidx]
            yc = (rows + 0.5) * c
            dy = (y2 - y1)[eidx]
            xc = x1[eidx] + (yc - y1[eidx]) * (x2 - x1)[eidx] / dy
            k = np.clip(np.ceil(xc / c - 0.5 - 1e-12).astype(np.int64), 0, w)
            np.add.at(parity, rows * (w + 1) + k, 1)
        # --- chegara: konturga yaqin kataklar (konservativ) ---
        seg = np.hypot(x2 - x1, y2 - y1)
        ns = np.maximum(1, np.ceil(seg / step)).astype(np.int64)
        tot2 = int(ns.sum())
        eidx = np.repeat(np.arange(len(x1)), ns)
        within = np.arange(tot2) - np.repeat(np.cumsum(ns) - ns, ns)
        t = within / ns[eidx]
        px = x1[eidx] + t * (x2 - x1)[eidx]
        py = y1[eidx] + t * (y2 - y1)[eidx]
        ia = np.floor((px - delta) / c).astype(np.int64)
        ib = np.floor((px + delta) / c).astype(np.int64)
        ja = np.floor((py - delta) / c).astype(np.int64)
        jb = np.floor((py + delta) / c).astype(np.int64)
        for ii in (ia, ib):
            for jj in (ja, jb):
                ok = (ii >= 0) & (ii < w) & (jj >= 0) & (jj < h)
                touch[jj[ok], ii[ok]] = True
    par = parity.reshape(h, w + 1) & 1
    inside = (np.cumsum(par, axis=1)[:, :w] & 1).astype(bool)
    if split:
        return inside, touch, i0, j0
    return inside | touch, i0, j0


def kernel_halfwidths(rho: float) -> dict[int, int]:
    """Kvadratlar-masofasi yadrosi: har qator siljishi dy uchun gorizontal yarim-kenglik hx (|dx| ≤ hx). rho = spacing / katak."""
    out: dict[int, int] = {0: 0}
    if rho <= 0:
        return out
    ry = int(math.ceil(rho)) + 1
    for dy in range(-ry, ry + 1):
        b = max(abs(dy) - 1, 0)
        rem = rho * rho - b * b
        if rem > 1e-12:
            out[dy] = max(1, int(math.ceil(math.sqrt(rem) - 1e-12)))
    return out


def dilate(mask: np.ndarray, rho: float) -> tuple[np.ndarray, int]:
    """Niqobni kvadratlar-masofasi yadrosi bilan kengaytiradi. Qaytaradi: (natija (h + 2R, w + 2R), R); niqob natijada (R, R) dan boshlanadi."""
    kh = kernel_halfwidths(rho)
    h, w = mask.shape
    R = max(max(abs(dy) for dy in kh), max(kh.values()))
    out = np.zeros((h + 2 * R, w + 2 * R), dtype=bool)
    if R == 0:
        out[:, :] = mask
        return out, 0
    Wp = w + 2 * R
    padded = np.zeros((h, Wp), dtype=np.int32)
    padded[:, R:R + w] = mask
    cs = np.zeros((h, Wp + 1), dtype=np.int32)
    np.cumsum(padded, axis=1, out=cs[:, 1:])
    idx = np.arange(Wp)
    cache: dict[int, np.ndarray] = {}
    for dy, hx in kh.items():
        d = cache.get(hx)
        if d is None:
            lo = np.clip(idx - hx, 0, Wp)
            hi = np.clip(idx + hx + 1, 0, Wp)
            d = (cs[:, hi] - cs[:, lo]) > 0
            cache[hx] = d
        out[R + dy:R + dy + h, :] |= d
    return out, R


@lru_cache(maxsize=4096)
def fast_len(n: int) -> int:
    """n dan katta yoki teng eng kichik 2^a·3^b·5^c (FFT uchun qulay uzunlik)."""
    n = max(1, int(n))
    best = None
    p5 = 1
    while p5 < 2 * n:
        p3 = p5
        while p3 < 2 * n:
            x = p3
            while x < n:
                x *= 2
            if best is None or x < best:
                best = x
            p3 *= 3
        p5 *= 5
    return best or n


def choose_cell(Lu: float, Wu: float, target_cells: int, min_dim: float) -> float:
    """Katak o'lchami: maqsadli kataklar sonidan oshmaydigan eng kichik (1…16 mm); mayda detallar bo'lsa maqsad ikki barobar."""
    tgt = target_cells * (2 if min_dim < 60 else 1)
    for c in CELL_CHOICES:
        if (Lu / c) * (Wu / c) <= tgt:
            return c
    return CELL_CHOICES[-1]


# ───────────────────────── Detal-burilish niqoblari ─────────────────────────
@dataclass
class _Ori:
    angle: float
    h: int
    w: int
    bw: float
    bh: float
    mask: np.ndarray
    full: bool
    area: int
    uid: int = 0
    dil: Optional[np.ndarray] = None
    R: int = 0


class _FftCache:
    def __init__(self, cap: int = FFT_CACHE_BYTES):
        self.cap, self.size = cap, 0
        self.d: dict = {}

    def get(self, k):
        v = self.d.get(k)
        if v is not None:
            self.d[k] = self.d.pop(k)           # LRU
        return v

    def put(self, k, v):
        if v.nbytes > self.cap // 4:
            return
        while self.size + v.nbytes > self.cap and self.d:
            kk = next(iter(self.d))
            self.size -= self.d.pop(kk).nbytes
        self.d[k] = v
        self.size += v.nbytes


class _Grid:
    """Bitta list nusxasi: egallangan xarita (dilatatsiyalangan), oldinga qaragan «chegara» (front)."""

    def __init__(self, nx: int, ny: int, axis: str):
        self.nx, self.ny, self.axis = nx, ny, axis
        self.O = np.zeros((ny, nx), dtype=bool)
        self.free = nx * ny
        self.front = 0                    # axis x: egallangan ustunlar o'ng chegarasi (kataklarda); axis y: qatorlarniki
        self.S: Optional[np.ndarray] = None
        self.S_lim = -1
        self.of: Optional[np.ndarray] = None
        self.of_key = None

    def invalidate(self):
        self.S, self.S_lim, self.of, self.of_key = None, -1, None, None


class Engine:
    """Bitta kirish (detallar, listlar, parametrlar) uchun hamma sinovlar umumiy niqob / FFT keshi bilan ishlaydi."""

    def __init__(self, parts: list[NestPart], sheets: list[NestSheet], prm: NestParams,
                 progress: Optional[Callable[[float, str], None]] = None, cancel: Optional[Callable[[], bool]] = None):
        self.parts, self.sheets, self.prm = parts, sheets, prm
        self.progress, self.cancel = progress, cancel
        self.q = QUALITY.get(prm.quality, QUALITY["normal"])
        self.time_limit = prm.time_limit or self.q["time"]
        self.max_trials = prm.max_trials or self.q["trials"]
        self.t0 = time.monotonic()
        self.fft = _FftCache()
        self._ori: dict = {}
        self.cells: dict[int, float] = {}
        self.stats = dict(fft=0, integral=0, placed=0)
        dims = [min(p.shape.bbox_size) for p in parts if p.qty > 0] or [100.0]
        self.min_dim = min(dims)
        self.rect_only = all(p.shape.is_rect and p.angles and all(abs(a % 90.0) < 1e-9 for a in p.angles) for p in parts)
        self.total = sum(p.qty for p in parts)
        self._trial_no, self._n_trials = 0, 1
        self.hard_limit = self.time_limit * 4
        self.timed_out = False

    # --- vaqt / to'xtatish ---
    def elapsed(self) -> float:
        return time.monotonic() - self.t0

    def _check(self):
        if self.cancel is not None and self.cancel():
            raise NestCancelled()

    # --- katak va niqoblar ---
    def cell_of(self, si: int) -> float:
        c = self.cells.get(si)
        if c is None:
            s, m = self.sheets[si], self.prm.margin
            tgt = self.q["cells"] * (2 if self.rect_only else 1)
            c = choose_cell(s.length - 2 * m, s.width - 2 * m, tgt, self.min_dim)
            self.cells[si] = c
        return c

    def orientations(self, pi: int, c: float) -> list[_Ori]:
        key = (pi, c)
        got = self._ori.get(key)
        if got is not None:
            return got
        part = self.parts[pi]
        out: list[_Ori] = []
        seen: set = set()
        simple_rect = part.shape.is_rect
        for ang in part.angles:
            o = G.orient_shape(part.shape, ang)
            if simple_rect and abs(ang % 90.0) < 1e-9:
                h = max(1, int(math.ceil(o.bh / c - 1e-9)))
                w = max(1, int(math.ceil(o.bw / c - 1e-9)))
                mask = np.ones((h, w), dtype=bool)
                full = True
            else:
                mask, _i0, _j0 = raster_rings([o.outer, *o.holes], c)
                h, w = mask.shape
                full = bool(mask.all())
            sig = (mask.shape, hash(mask.tobytes()))
            if sig in seen:
                continue
            seen.add(sig)
            out.append(_Ori(ang, h, w, o.bw, o.bh, mask, full, int(mask.sum()), uid=len(out), R=self._kernel_r(c)))
        self._ori[key] = out
        return out

    def _kernel_r(self, c: float) -> int:
        kh = kernel_halfwidths(self.prm.spacing / c)
        return max(max(abs(dy) for dy in kh), max(kh.values()))

    def dil(self, o: _Ori, c: float) -> tuple[np.ndarray, int]:
        if o.dil is None:
            o.dil, o.R = dilate(o.mask, self.prm.spacing / c)
        return o.dil, o.R

    # --- mumkin bo'lgan o'rinlar ---
    @staticmethod
    def _limits(g: _Grid, o: _Ori) -> tuple[int, int]:
        """(gx_max, gy_max): izlash oynasi (front dan keyin hammasi bo'sh — u yerga izlash shart emas)."""
        if g.axis == "x":
            return min(g.nx - o.w, g.front), g.ny - o.h
        return g.nx - o.w, min(g.ny - o.h, g.front)

    def _integral(self, g: _Grid, lim: int) -> np.ndarray:
        if g.S is not None and g.S_lim >= lim:
            return g.S
        O = g.O[:, :lim] if g.axis == "x" else g.O[:lim, :]
        S = np.zeros((O.shape[0] + 1, O.shape[1] + 1), dtype=np.int32)
        np.cumsum(np.cumsum(O, axis=0, dtype=np.int32), axis=1, out=S[1:, 1:])
        g.S, g.S_lim = S, lim
        self.stats["integral"] += 1
        return S

    def best_position(self, g: _Grid, oris: list[_Ori], pref: str = "auto") -> Optional[tuple[tuple, _Ori, int, int]]:
        """Eng yaxshi (kalit, burilish, gx, gy) yoki None. Kalit — (o'rovchi to'rtburchak oxiri, ikkinchi koordinata, burilish tartibi).
        `pref` — burilish afzalligi: "auto" — faqat kalit; "flat" — uzun tomon to'ldirish o'qi bo'ylab, "tall" — ko'ndalang (faqat oldinga
        — chegarani kengaytiradigan joylarda; ichki bo'shliqqa tushish afzallikka bog'liq emas)."""
        cand: list[tuple[_Ori, int, int]] = []
        for o in oris:
            if o.h > g.ny or o.w > g.nx or o.area > g.free:
                continue
            gx_max, gy_max = self._limits(g, o)
            if gx_max >= 0 and gy_max >= 0:
                cand.append((o, gx_max, gy_max))
        if not cand:
            return None
        # umumiy oyna: barcha to'rtburchak niqoblar uchun bitta integral tasvir; umumiy niqoblar uchun bitta FFT oyna
        full = [c for c in cand if c[0].full]
        gen = [c for c in cand if not c[0].full]
        S = None
        if full:
            lim = max((gx + o.w) if g.axis == "x" else (gy + o.h) for o, gx, gy in full)
            S = self._integral(g, lim)
        fy = fx = 0
        if gen:
            Wn = max(gx + o.w for o, gx, gy in gen)
            Hn = max(gy + o.h for o, gx, gy in gen)
            bw = WINDOW_BUCKET
            Wn = min(g.nx, ((Wn + bw - 1) // bw) * bw)
            Hn = min(g.ny, ((Hn + bw - 1) // bw) * bw)
            fx, fy = fast_len(Wn), fast_len(Hn)
            if g.of is None or g.of_key != (fy, fx):
                Oc = np.zeros((fy, fx), dtype=np.float32)
                Oc[:Hn, :Wn] = g.O[:Hn, :Wn]
                g.of = np.fft.rfft2(Oc)
                g.of_key = (fy, fx)
                self.stats["fft"] += 1
        results: list[tuple[tuple, _Ori, int, int]] = []
        for o, gx_max, gy_max in cand:
            h, w = o.h, o.w
            if o.full:
                F = (S[h:gy_max + h + 1, w:gx_max + w + 1] - S[:gy_max + 1, w:gx_max + w + 1]
                     - S[h:gy_max + h + 1, :gx_max + 1] + S[:gy_max + 1, :gx_max + 1]) == 0
            else:
                mk = (id(o), fy, fx)
                Mf = self.fft.get(mk)
                if Mf is None:
                    Mc = np.zeros((fy, fx), dtype=np.float32)
                    Mc[:h, :w] = o.mask
                    Mf = np.conj(np.fft.rfft2(Mc))
                    self.fft.put(mk, Mf)
                    self.stats["fft"] += 1
                corr = np.fft.irfft2(g.of * Mf, s=(fy, fx))
                self.stats["fft"] += 1
                F = corr[:gy_max + 1, :gx_max + 1] < 0.5
            while True:
                ys, xs = np.nonzero(F)
                if ys.size == 0:
                    break
                if g.axis == "x":
                    kk = (xs + w).astype(np.int64) * (g.ny + 1) + ys
                else:
                    kk = (ys + h).astype(np.int64) * (g.nx + 1) + xs
                i = int(np.argmin(kk))
                gx, gy = int(xs[i]), int(ys[i])
                if o.full or not (g.O[gy:gy + h, gx:gx + w] & o.mask).any():      # FFT yaxlitlash xatosiga qarshi aniq tekshiruv
                    results.append(((int(kk[i]), o.uid), o, gx, gy))
                    break
                F[gy, gx] = False
        if not results:
            return None
        best = min(results, key=lambda r: r[0])
        if pref != "auto" and len(results) > 1:
            along_x = g.axis == "x"

            def aligned(o: _Ori) -> bool:
                flat = (o.bw >= o.bh) if along_x else (o.bh >= o.bw)
                return flat if pref == "flat" else (not flat or o.bw == o.bh)
            prim = best[0][0] // ((g.ny + 1) if along_x else (g.nx + 1))
            if prim + best[1].R > g.front:                           # yangi detal chegarani kengaytiradi — burilishni afzallik bo'yicha tanlash
                sub = [r for r in results if aligned(r[1])]
                if sub:
                    best = min(sub, key=lambda r: r[0])
        return best

    def commit(self, g: _Grid, o: _Ori, gx: int, gy: int, c: float) -> None:
        D, R = self.dil(o, c)
        y0, x0 = gy - R, gx - R
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(g.ny, y0 + D.shape[0]), min(g.nx, x0 + D.shape[1])
        sub = g.O[ya:yb, xa:xb]
        add = D[ya - y0:yb - y0, xa - x0:xb - x0]
        g.free -= int((add & ~sub).sum())
        sub |= add
        g.front = max(g.front, (gx + o.w + R) if g.axis == "x" else (gy + o.h + R))
        g.front = min(g.front, g.nx if g.axis == "x" else g.ny)
        g.invalidate()

    # --- bitta list nusxasini to'ldirish ---
    def fill_sheet(self, si: int, remaining: list[int], order: list[int], axis: str, pref: str = "auto") -> list[PlacedItem]:
        sh = self.sheets[si]
        m = self.prm.margin
        c = self.cell_of(si)
        nx = int(math.floor((sh.length - 2 * m) / c + 1e-9))
        ny = int(math.floor((sh.width - 2 * m) / c + 1e-9))
        if nx < 1 or ny < 1:
            return []
        g = _Grid(nx, ny, axis)
        left = list(remaining)
        items: list[PlacedItem] = []
        for pi in order:
            if left[pi] <= 0:
                continue
            oris = self.orientations(pi, c)
            while left[pi] > 0:
                self._check()
                if self.elapsed() > self.hard_limit:
                    self.timed_out = True
                    return items
                got = self.best_position(g, oris, pref)
                if got is None:
                    break
                _key, o, gx, gy = got
                self.commit(g, o, gx, gy, c)
                items.append(PlacedItem(pi, o.angle, m + gx * c, m + gy * c, o.bw, o.bh))
                left[pi] -= 1
                self.stats["placed"] += 1
        return items

    # --- bitta sinov ---
    def trial(self, order: list[int], axis_pref: str, pref: str = "auto") -> tuple[list[Layout], list[int]]:
        remaining = [p.qty for p in self.parts]
        layouts: list[Layout] = []
        for si, sh in enumerate(self.sheets):
            avail = sh.qty
            if min(sh.length, sh.width) - 2 * self.prm.margin <= 0:
                continue
            axis = "x" if (axis_pref == "long") == (sh.length >= sh.width) else "y"
            while avail > 0 and any(r > 0 for r in remaining):
                items = self.fill_sheet(si, remaining, order, axis, pref)
                if not items:
                    break
                cnt: dict[int, int] = {}
                for it in items:
                    cnt[it.part] = cnt.get(it.part, 0) + 1
                reps = max(1, min(avail, min(remaining[pi] // n for pi, n in cnt.items())))
                for pi, n in cnt.items():
                    remaining[pi] -= n * reps
                layouts.append(Layout(si, reps, items))
                avail -= reps
                if self.progress is not None and self.total:
                    done = 1.0 - sum(remaining) / self.total
                    self.progress(min(0.99, (self._trial_no + done) / max(1, self._n_trials)), "")
                if self.elapsed() > self.hard_limit:
                    break
        unplaced = [pi for pi, r in enumerate(remaining) for _k in range(max(0, r))]
        return layouts, unplaced

    # --- baholash ---
    def score(self, layouts: list[Layout], unplaced: list[int]) -> tuple:
        area = sum(self.sheets[ly.sheet].length * self.sheets[ly.sheet].width * ly.copies for ly in layouts)
        tail = 0.0
        if layouts:
            ly = layouts[-1]
            sh = self.sheets[ly.sheet]
            along_x = sh.length >= sh.width
            ext = max((it.x + it.w) if along_x else (it.y + it.h) for it in ly.items)
            tail = ext / max(sh.length if along_x else sh.width, 1.0)
        return (len(unplaced), round(area, 3), round(tail, 4))

    # --- tartiblar ---
    def orders(self) -> list[tuple[list[int], str, str]]:
        """Sinovlar ketma-ketligi: (detallar tartibi, to'ldirish o'qi, burilish afzalligi). Birinchilari eng ko'p foyda beradiganlar —
        «fast» faqat shu boshlang'ich to'plamdan oladi (arzon: har biri bir necha ms)."""
        idx = [i for i, p in enumerate(self.parts) if p.qty > 0]
        area = lambda i: self.parts[i].shape.area
        maxs = lambda i: max(self.parts[i].shape.bbox_size)
        per = lambda i: self.parts[i].shape.perimeter
        bbox_a = lambda i: self.parts[i].shape.bbox_size[0] * self.parts[i].shape.bbox_size[1]
        if self.prm.order == "list":                       # saralash: ro'yxat tartibi saqlanadi (faqat burilish afzalligi o'zgaradi)
            return [(list(idx), "long", "auto"), (list(idx), "long", "flat"), (list(idx), "long", "tall")][:max(self.max_trials, 1)]
        by_area = sorted(idx, key=lambda i: (-area(i), i))
        by_max = sorted(idx, key=lambda i: (-maxs(i), -area(i), i))
        by_bbox = sorted(idx, key=lambda i: (-bbox_a(i), i))
        by_per = sorted(idx, key=lambda i: (-per(i), i))
        cand = [
            (by_area, "long", "auto"), (by_area, "long", "flat"), (by_area, "long", "tall"),
            (by_max, "long", "flat"), (by_max, "long", "auto"), (by_bbox, "long", "flat"),
            (by_area, "short", "auto"), (by_per, "long", "flat"), (by_max, "long", "tall"), (by_bbox, "long", "auto"),
            (by_area, "short", "flat"), (by_per, "long", "auto"),
        ]
        rnd = random.Random(self.prm.seed)
        n = max(self.max_trials, 1)
        while len(cand) < n:
            o = list(by_area)
            for _k in range(max(2, len(o) // 4)):          # qo'shni juftliklarni almashtirish (urug'li)
                a = rnd.randrange(0, max(1, len(o) - 1))
                if a + 1 < len(o):
                    o[a], o[a + 1] = o[a + 1], o[a]
            cand.append((o, "long" if rnd.random() < 0.7 else "short", rnd.choice(("auto", "flat", "tall"))))
        return cand[:n]

    def run(self) -> NestOutcome:
        cands = self.orders()
        self._n_trials = len(cands)
        best = None
        best_s = None
        done_trials = 0
        lb = None                              # bitta turdagi list bo'lsa: listlar sonining quyi chegarasi ⌈Σ sof maydon / foydali maydon⌉
        if len(self.sheets) == 1 and self.prm.stop_at_bound:
            sh = self.sheets[0]
            usable = max(1.0, (sh.length - 2 * self.prm.margin) * (sh.width - 2 * self.prm.margin))
            lb = max(1, int(math.ceil(sum(p.shape.area * p.qty for p in self.parts) / usable - 1e-9)))
        for tn, (order, axis, pref) in enumerate(cands):
            self._trial_no = tn
            if tn > 0:
                if self.elapsed() > self.time_limit:
                    break                      # qolgan sinovlar vaqt chegarasi tufayli o'tkazilmadi (natija baribir to'liq)
                self.hard_limit = self.time_limit
            layouts, unplaced = self.trial(order, axis, pref)
            s = self.score(layouts, unplaced)
            done_trials += 1
            if best_s is None or s < best_s:
                best, best_s = (layouts, unplaced), s
            if not unplaced and lb is not None and sum(ly.copies for ly in layouts) <= lb:
                break                          # listlar soni quyi chegaraga yetdi — yaxshilab bo'lmaydi
        layouts, unplaced = best if best else ([], [pi for pi, p in enumerate(self.parts) for _k in range(p.qty)])
        info = dict(trials=done_trials, cells={str(si): c for si, c in self.cells.items()}, elapsed_s=round(self.elapsed(), 3),
                    fft=self.stats["fft"], integral=self.stats["integral"], placed=self.stats["placed"],
                    quality=self.prm.quality, seed=self.prm.seed, timed_out=self.timed_out)
        if self.progress is not None:
            self.progress(1.0, "done")
        return NestOutcome(layouts, unplaced, info)


def nest(parts: list[NestPart], sheets: list[NestSheet], prm: NestParams,
         progress: Optional[Callable[[float, str], None]] = None, cancel: Optional[Callable[[], bool]] = None) -> NestOutcome:
    """Asosiy kirish nuqtasi."""
    return Engine(parts, sheets, prm, progress, cancel).run()


def place_in_layout(shape: G.Shape, angles: list[float], length: float, width: float,
                    existing: list[tuple[G.Ring, list[G.Ring]]], prm: NestParams) -> Optional[tuple[float, float, float]]:
    """Mavjud joylashuvga (list koordinatalaridagi poligonlar) bitta detalni eng chap-yuqori mumkin bo'lgan o'ringa qo'yish
    (qo'lda tahrir: «авто-расстановка»). Qaytaradi: (burchak, x, y) yoki None. Raster aniqligi — `choose_cell` (qo'lda tahrir uchun «max»)."""
    eng = Engine([NestPart("x", 0, shape, 1, angles)], [NestSheet("s", length, width, 1)], prm)
    c = eng.cell_of(0)
    m = prm.margin
    nx, ny = int(math.floor((length - 2 * m) / c + 1e-9)), int(math.floor((width - 2 * m) / c + 1e-9))
    if nx < 1 or ny < 1:
        return None
    axis = "x" if length >= width else "y"
    g = _Grid(nx, ny, axis)
    rho = prm.spacing / c
    for outer, holes in existing:
        mask, i0, j0 = raster_rings([outer, *holes], c, m, m)
        D, R = dilate(mask, rho)
        y0, x0 = j0 - R, i0 - R
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(ny, y0 + D.shape[0]), min(nx, x0 + D.shape[1])
        if ya < yb and xa < xb:
            g.O[ya:yb, xa:xb] |= D[ya - y0:yb - y0, xa - x0:xb - x0]
    g.free = int((~g.O).sum())
    g.front = nx if axis == "x" else ny                  # butun list bo'ylab izlash (joylashuvlar xohlagan joyda bo'lishi mumkin)
    got = eng.best_position(g, eng.orientations(0, c))
    if got is None:
        return None
    _key, o, gx, gy = got
    return o.angle, m + gx * c, m + gy * c

