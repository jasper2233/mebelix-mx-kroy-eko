"""OEE hisoblash yadrosi (W17) — toza funksiyalar, bazasiz. Vaqtlar — epoch soniya (UTC, float).

OEE = A × P × Q  (hammasi 0…1; hujjat: docs/mebelix/T_W17_OEE.md)

  A (Availability)  = ish vaqti / rejalashtirilgan vaqt
        rejalashtirilgan vaqt = smena oralig'i − tanaffuslar − rejalashtirilgan to'xtashlar (sabab `planned=True`)
        ish vaqti = rejalashtirilgan vaqt − rejalashtirilmagan to'xtashlar − `idle` (hodisasiz bo'shliq ≥ idle_gap_s)
  P (Performance)  = ideal vaqt / ish vaqti,   ≤ 1 (chegara; xomi `performance_raw`)
        ideal vaqt = Σ (ideal sikl × ishlab chiqarilgan soni);  ideal sikl — `ideal_cycle()`
  Q (Quality)      = yaroqli / jami ishlab chiqarilgan   (brak birligi — «part» yoki «sheet», sozlanadi)

Vaqt sinflash qoidalari (rejalashtirilgan vaqt ichida, ustuvorlik tartibida):
  1. rejalashtirilmagan to'xtash hodisasi (kesishsa — avval boshlangan g'olib, ikki marta hisoblanmaydi);
  2. `run` hodisasi oralig'i (boshlanishi ma'lum bo'lmasa — avvalgi hodisa oxiridan, lekin ko'pi bilan
     `run_cap_factor × ideal vaqt`; ideal ma'lum bo'lmasa — nol uzunlik);
  3. qolgan «bo'sh» bo'laklar: uzunligi < idle_gap_s — ish (karta almashtirish), ≥ idle_gap_s — `idle` to'xtash.
Hodisalar nuqtasi (karta tugagan vaqt) yarim ochiq (a, b] oraliqqa tegishli: soat 17:00:00 da tugagan karta 08–17 smenasiniki.
"""
from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Iterable, Optional, Sequence

# ───────────────────────── Konstantalar (hujjatda ham) ─────────────────────────
BAND_LOW = 0.60            # < 60 % — qizil
BAND_HIGH = 0.85           # ≥ 85 % — yashil (60…85 — sariq)
IDLE = "idle"              # hodisasiz bo'shliq uchun avtomatik sabab kodi
DEFAULT_CUT_SPEED_MM_S = 1000.0    # ideal kesish tezligi (60 m/min) — stanok profilida o'zgartiriladi
DEFAULT_CUT_CHANGE_S = 5.0         # bitta kesim almashinuvi (kesim tugadi → keyingisi boshlandi), s
DEFAULT_SHEET_LOAD_S = 25.0        # bitta list yuklash, s
MAX_RUN_S = 24 * 3600              # bitta `run` hodisasining eng uzun davomiyligi (tekshiruv)

Interval = tuple[float, float]


def band(v: Optional[float]) -> str:
    """Rang guruhi: low (<60 %), mid (60…85 %), high (≥85 %), none (qiymat yo'q)."""
    if v is None:
        return "none"
    if v < BAND_LOW - 1e-12:
        return "low"
    if v < BAND_HIGH - 1e-12:
        return "mid"
    return "high"


# ───────────────────────── Oraliqlar algebrasi ─────────────────────────
def merge(iv: Iterable[Interval]) -> list[Interval]:
    """Kesishgan/tegib turgan oraliqlarni birlashtiradi; bo'sh (b ≤ a) oraliqlar tashlanadi."""
    out: list[Interval] = []
    for a, b in sorted((a, b) for a, b in iv if b > a):
        if out and a <= out[-1][1]:
            if b > out[-1][1]:
                out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def clip_iv(iv: Iterable[Interval], lo: float, hi: float) -> list[Interval]:
    return [(max(a, lo), min(b, hi)) for a, b in iv if min(b, hi) > max(a, lo)]


def intersect(x: Sequence[Interval], y: Sequence[Interval]) -> list[Interval]:
    """Ikki birlashtirilgan ro'yxat kesishmasi."""
    out: list[Interval] = []
    i = j = 0
    while i < len(x) and j < len(y):
        a, b = max(x[i][0], y[j][0]), min(x[i][1], y[j][1])
        if b > a:
            out.append((a, b))
        if x[i][1] < y[j][1]:
            i += 1
        else:
            j += 1
    return out


def subtract(x: Sequence[Interval], y: Sequence[Interval]) -> list[Interval]:
    """x − y (ikkalasi ham birlashtirilgan)."""
    out: list[Interval] = []
    j = 0
    for a, b in x:
        cur = a
        while j < len(y) and y[j][1] <= cur:
            j += 1
        k = j
        while k < len(y) and y[k][0] < b:
            if y[k][0] > cur:
                out.append((cur, y[k][0]))
            cur = max(cur, y[k][1])
            if cur >= b:
                break
            k += 1
        if cur < b:
            out.append((cur, b))
    return out


def total(iv: Iterable[Interval]) -> float:
    return sum(b - a for a, b in iv)


class IvSet:
    """Birlashtirilgan oraliqlar to'plami: tez o'lchov (prefiks yig'indi + bisect) va nuqta tekshiruvi."""
    __slots__ = ("iv", "starts", "ends", "pref")

    def __init__(self, iv: Iterable[Interval] = ()):
        self.iv: list[Interval] = merge(iv)
        self.starts = [a for a, _ in self.iv]
        self.ends = [b for _, b in self.iv]
        self.pref = [0.0]
        for a, b in self.iv:
            self.pref.append(self.pref[-1] + (b - a))

    def cum(self, t: float) -> float:
        """To'plamning (−∞, t] dagi o'lchovi."""
        i = bisect_right(self.starts, t)
        if i == 0:
            return 0.0
        a, b = self.iv[i - 1]
        return self.pref[i - 1] + (min(t, b) - a)

    def measure(self, lo: float, hi: float) -> float:
        return max(0.0, self.cum(hi) - self.cum(lo)) if hi > lo else 0.0

    def contains_point(self, t: float) -> bool:
        """(a, b] yarim ochiq oraliq: a < t ≤ b."""
        i = bisect_left(self.ends, t)
        return i < len(self.iv) and self.iv[i][0] < t <= self.iv[i][1]

    def containing(self, t: float) -> Optional[Interval]:
        i = bisect_left(self.ends, t)
        if i < len(self.iv) and self.iv[i][0] < t <= self.iv[i][1]:
            return self.iv[i]
        return None

    def __bool__(self) -> bool:
        return bool(self.iv)


# ───────────────────────── Ideal sikl ─────────────────────────
@dataclass
class MachineProfile:
    """Stanokning ideal tezlik parametrlari (OEE stanoklari jadvalidan)."""
    key: str = ""
    cut_speed_mm_s: Optional[float] = DEFAULT_CUT_SPEED_MM_S
    cut_change_s: Optional[float] = DEFAULT_CUT_CHANGE_S
    sheet_load_s: Optional[float] = DEFAULT_SHEET_LOAD_S
    ideal_unit_s: Optional[float] = None       # geometriya yo'q hodisalar uchun: birlik sikli, s


def ideal_cycle(m: Any, prof: MachineProfile, sheets_per_pack: float = 1) -> Optional[float]:
    """Karta (CutMap yoki `cut_length_m` va `cuts_count` atributli obyekt) uchun BITTA list ideal sikli, soniya:

        (kesish uzunligi / ideal kesish tezligi + kesimlar soni × kesim almashinuvi) / paketdagi listlar + list yuklash

    `sheets_per_pack` > 1 bo'lsa (paket: bir necha list birga kesiladi) kesish vaqti shu listlar orasida bo'linadi, yuklash —
    har list uchun. Ma'lumot yetishmasa (uzunlik/kesimlar yo'q yoki tezlik ≤ 0) — None."""
    L = getattr(m, "cut_length_m", None)
    n = getattr(m, "cuts_count", None)
    v = prof.cut_speed_mm_s
    if L is None or n is None or v is None or not (v > 0) or L < 0 or n < 0:
        return None
    spp = sheets_per_pack if sheets_per_pack and sheets_per_pack >= 1 else 1
    cut = L * 1000.0 / v + n * (prof.cut_change_s or 0.0)
    return cut / spp + (prof.sheet_load_s or 0.0)


# ───────────────────────── Hodisalar (yadro kirishi) ─────────────────────────
@dataclass(eq=False)
class RunEv:
    end: float
    start: Optional[float] = None
    qty: float = 1.0                       # kesilgan listlar
    reject_qty: float = 0.0                # shu hodisadagi brak (birligi — `unit`)
    unit: str = "part"
    parts: Optional[float] = None
    parts_per_sheet: Optional[float] = None
    cut_length_m: Optional[float] = None
    cuts: Optional[int] = None
    sheets_per_pack: float = 1.0
    ideal_cycle_s: Optional[float] = None  # MES bergan ideal sikl (bitta list), s
    sheet_area_m2: Optional[float] = None  # bitta list maydoni (material samaradorligi KPI)
    parts_area_m2: Optional[float] = None
    remnant_area_m2: Optional[float] = None
    id: int = 0


@dataclass(eq=False)
class DownEv:
    start: float
    reason: str
    end: Optional[float] = None            # None — hali davom etmoqda
    id: int = 0


@dataclass(eq=False)
class RejEv:
    ts: float
    qty: float = 1.0
    unit: str = "part"
    parts_per_sheet: Optional[float] = None
    reason: Optional[str] = None
    id: int = 0


@dataclass
class Cfg:
    """Hisob sozlamalari (DB dagi `oee_config.config`)."""
    idle_gap_s: float = 300.0              # hodisasiz bo'shliq shu uzunlikdan boshlab `idle` to'xtash
    run_cap_factor: float = 3.0            # boshlanishi noma'lum `run` uchun: ish oralig'i ≤ factor × ideal vaqt
    unit: str = "sheet"                    # ishlab chiqarilgan birlik: sheet | part
    include_overtime: bool = False         # smenadan tashqari ishlash rejalashtirilgan vaqtga qo'shilsinmi


def run_ideal_total(ev: RunEv, prof: MachineProfile) -> Optional[float]:
    """Hodisa uchun jami ideal vaqt (s): MES ideal sikli > karta geometriyasi (`ideal_cycle`) > stanokning `ideal_unit_s`."""
    qty = ev.qty if ev.qty and ev.qty > 0 else 0.0
    per: Optional[float] = None
    if ev.ideal_cycle_s and ev.ideal_cycle_s > 0:
        per = ev.ideal_cycle_s
    else:
        per = ideal_cycle(SimpleNamespace(cut_length_m=ev.cut_length_m, cuts_count=ev.cuts), prof, ev.sheets_per_pack or 1)
        if per is None and prof.ideal_unit_s and prof.ideal_unit_s > 0:
            per = prof.ideal_unit_s
    return None if per is None else per * qty


# ───────────────────────── Bitta stanok vaqt chizig'i ─────────────────────────
@dataclass(eq=False)
class Piece:
    ev: RunEv
    a: float                               # ish oralig'i boshi
    b: float                               # tugashi (a == b — nuqta)
    ideal: Optional[float]                 # jami ideal vaqt, s
    inferred: bool = False


@dataclass
class Timeline:
    key: str = ""
    lo: float = 0.0
    hi: float = 0.0
    p_eff: IvSet = field(default_factory=IvSet)        # rejalashtirilgan vaqt (tanaffus va rejalashtirilgan to'xtashsiz)
    ud_all: IvSet = field(default_factory=IvSet)       # rejalashtirilmagan to'xtashlar (barcha sabablar)
    idle: IvSet = field(default_factory=IvSet)
    valid: IvSet = field(default_factory=IvSet)        # p_eff − ud_all (ishlab chiqarish kredit oladigan vaqt)
    ud_by_reason: dict[str, IvSet] = field(default_factory=dict)
    ud_count: dict[str, int] = field(default_factory=dict)
    pd_by_reason: dict[str, IvSet] = field(default_factory=dict)       # rejalashtirilgan to'xtashlar (smena ichida)
    pd_count: dict[str, int] = field(default_factory=dict)
    pieces: list[Piece] = field(default_factory=list)
    piece_starts: list[float] = field(default_factory=list)
    max_dur: float = 0.0
    rejs: list[RejEv] = field(default_factory=list)    # p_eff ichidagi alohida brak hodisalari
    avg_pps: Optional[float] = None                    # o'rtacha detal/list (konvertatsiya uchun)
    no_ideal: int = 0                                  # ideal sikli noma'lum run hodisalari soni
    open_closed: int = 0                               # avtomatik yopilgan ochiq to'xtashlar
    idle_segments: list[Interval] = field(default_factory=list)
    raw_runs: int = 0
    raw_sheets: float = 0.0
    raw_rejects: float = 0.0
    raw_down: int = 0
    mat_sheets: float = 0.0                            # material: maydon ma'lumoti bor listlar (qty bo'yicha)
    mat_sheet_m2: float = 0.0
    mat_parts_m2: float = 0.0
    mat_remnant_m2: float = 0.0
    has_data: bool = False                             # oynada shu stanok uchun hodisa bor (aks holda «ma'lumot yo'q»)


def _resume_point(r: RunEv, ideal: Optional[float]) -> float:
    return r.start if r.start is not None else r.end - (ideal or 0.0)


def build_timeline(prof: MachineProfile, planned: Sequence[Interval], planned_codes: set[str],
                   runs: Sequence[RunEv], downs: Sequence[DownEv], rejs: Sequence[RejEv], cfg: Cfg,
                   lo: float, hi: float, as_of: float, key: str = "") -> Timeline:
    """Bitta stanok uchun [lo, min(hi, as_of)] oynasida vaqt chizig'ini quradi (hodisalar oynadan oldin/keyin ham berilishi mumkin)."""
    tl = Timeline(key=key, lo=lo, hi=min(hi, as_of))
    hi = tl.hi
    if hi <= lo:
        return tl
    P0 = merge(clip_iv(planned, lo, hi))
    ideal = {id(r): run_ideal_total(r, prof) for r in runs}
    tl.no_ideal = sum(1 for r in runs if ideal[id(r)] is None and lo < r.end <= hi)

    # xom sanoqlar (kalendardan qat'i nazar): oyna ichidagi hodisalar
    for r in runs:
        if lo < r.end <= hi:
            tl.raw_runs += 1
            tl.raw_sheets += r.qty
            if r.sheet_area_m2 and r.parts_area_m2 is not None:        # material samaradorligi (OEE ga kirmaydi)
                tl.mat_sheets += r.qty
                tl.mat_sheet_m2 += r.qty * r.sheet_area_m2
                tl.mat_parts_m2 += r.qty * r.parts_area_m2
                tl.mat_remnant_m2 += r.qty * (r.remnant_area_m2 or 0.0)
    for j in rejs:
        if lo < j.ts <= hi:
            tl.raw_rejects += j.qty
    tl.raw_down = sum(1 for d in downs if d.start < hi and (d.end is None or d.end > lo))

    # 1) to'xtashlarni yopish (ochiq to'xtash: keyingi to'xtash boshlanishi, as_of yoki ish qayta boshlangan joyda)
    dsorted = sorted(downs, key=lambda d: (d.start, d.id))
    dn: list[tuple[float, float, str]] = []
    for k, d in enumerate(dsorted):
        if d.end is not None:
            e = d.end
        else:
            e = as_of
            if k + 1 < len(dsorted):
                e = min(e, dsorted[k + 1].start)
            for r in runs:
                if r.end > d.start:
                    e = min(e, max(d.start, _resume_point(r, ideal[id(r)])))
            tl.open_closed += 1
        if e > d.start:
            dn.append((d.start, e, d.reason))

    # 2) boshlanishi noma'lum `run` — avvalgi hodisa oxiridan chiqarib olinadi
    p_eff0 = IvSet(subtract(P0, merge(clip_iv([(s, e) for s, e, rs in dn if rs in planned_codes], lo, hi))))
    items: list[tuple[float, int, int, Any]] = []
    for i, r in enumerate(runs):
        items.append((r.end, 0, i, r))
    for i, (s, e, rs) in enumerate(dn):
        items.append((e, 1, i, None))
    items.sort(key=lambda x: (x[0], x[1], x[2]))
    last_end: Optional[float] = None
    pieces: list[Piece] = []
    for end, kind, _i, r in items:
        if kind == 0:
            idl = ideal[id(r)]
            if r.start is not None:
                a, inferred = min(r.start, r.end), False
            else:
                inferred = True
                if idl is None:
                    a = r.end                                          # davomiylik noma'lum — nuqta
                else:
                    gap = (r.end - last_end) if last_end is not None else math.inf
                    a = r.end - max(0.0, min(gap, cfg.run_cap_factor * idl))
                    if not cfg.include_overtime:
                        seg = p_eff0.containing(r.end)
                        if seg is not None and a < seg[0]:
                            a = seg[0]                                  # smena boshidan oldingi qismi kesiladi
            pieces.append(Piece(r, a, r.end, idl, inferred))
        last_end = end if last_end is None else max(last_end, end)

    # 3) rejalashtirilgan vaqt
    run_iv = merge((p.a, p.b) for p in pieces)
    runc = merge(clip_iv(run_iv, lo, hi))
    pd_all = merge(clip_iv([(s, e) for s, e, rs in dn if rs in planned_codes], lo, hi))
    base = merge(list(P0) + runc) if cfg.include_overtime else P0
    p_eff = subtract(base, pd_all)
    tl.p_eff = IvSet(p_eff)

    # 4) to'xtashlar: har soniya bitta sababga tegishli (avval boshlangan g'olib); rejalashtirilgan — alohida
    claimed: list[Interval] = []
    pclaimed: list[Interval] = []
    ud_parts: dict[str, list[Interval]] = {}
    pd_parts: dict[str, list[Interval]] = {}
    for s, e, rs in sorted(dn, key=lambda x: (x[0], x[1])):
        if rs in planned_codes:
            piece = subtract(intersect([(max(s, lo), min(e, hi))], P0), pclaimed) if min(e, hi) > max(s, lo) else []
            if piece:
                pd_parts.setdefault(rs, []).extend(piece)
                pclaimed = merge(pclaimed + piece)
                tl.pd_count[rs] = tl.pd_count.get(rs, 0) + 1
        else:
            piece = subtract(intersect([(max(s, lo), min(e, hi))], p_eff), claimed) if min(e, hi) > max(s, lo) else []
            if piece:
                ud_parts.setdefault(rs, []).extend(piece)
                claimed = merge(claimed + piece)
                tl.ud_count[rs] = tl.ud_count.get(rs, 0) + 1
    tl.ud_by_reason = {rs: IvSet(v) for rs, v in ud_parts.items()}
    tl.pd_by_reason = {rs: IvSet(v) for rs, v in pd_parts.items()}
    tl.ud_all = IvSet(claimed)

    # 5) qolgan vaqt: ish (run oralig'i) / bo'sh bo'lak (< idle_gap_s — ish, ≥ — idle)
    valid = subtract(p_eff, claimed)
    tl.valid = IvSet(valid)
    runset = intersect(runc, valid)
    rest = subtract(valid, runset)
    idle = [seg for seg in rest if seg[1] - seg[0] >= cfg.idle_gap_s - 1e-9]
    tl.idle = IvSet(idle)
    tl.idle_segments = idle

    # 6) ish hodisalari bo'laklari, alohida brak
    pieces.sort(key=lambda p: (p.a, p.b))
    tl.pieces = pieces
    tl.piece_starts = [p.a for p in pieces]
    tl.max_dur = max((p.b - p.a for p in pieces), default=0.0)
    tl.rejs = [j for j in rejs if tl.p_eff.contains_point(j.ts)]
    tot_sheets = sum(p.ev.qty for p in pieces if p.ev.parts_per_sheet or p.ev.parts)
    tot_parts = sum((p.ev.parts if p.ev.parts is not None else p.ev.qty * p.ev.parts_per_sheet)
                    for p in pieces if p.ev.parts is not None or p.ev.parts_per_sheet)
    tl.avg_pps = (tot_parts / tot_sheets) if tot_sheets > 0 and tot_parts > 0 else None
    return tl


# ───────────────────────── Ko'rsatkichlar ─────────────────────────
@dataclass
class Comp:
    """Qo'shiladigan komponentlar (bucket → oyna → stanoklar yig'indisi): nisbatlar shulardan hisoblanadi."""
    ppt: float = 0.0           # rejalashtirilgan vaqt, s
    stop: float = 0.0          # rejalashtirilmagan to'xtash + idle, s
    run: float = 0.0           # ish vaqti, s
    idle: float = 0.0          # shundan hodisasiz bo'shliq, s
    ideal: float = 0.0         # ideal vaqt (ideal sikli ma'lum hodisalar), s
    sheets_all: float = 0.0    # kredit olgan listlar
    sheets_known: float = 0.0  # shundan ideal sikli ma'lumlari
    units_known: float = 0.0   # shunisi — `unit` birligida
    produced: float = 0.0      # ishlab chiqarilgan (`unit` birligida)
    parts: float = 0.0         # ishlab chiqarilgan detallar (ma'lum bo'lganlari)
    rejects: float = 0.0       # brak (`unit` birligida)
    events: int = 0
    fallback: int = 0          # birlik konvertatsiyasi uchun ma'lumot yo'q (1:1 olindi)
    outside_sheets: float = 0.0  # rejalashtirilgan vaqtdan tashqarida ishlab chiqarilgan (hisobga kirmadi)

    def add(self, o: "Comp") -> "Comp":
        for f in self.__dataclass_fields__:
            setattr(self, f, getattr(self, f) + getattr(o, f))
        return self


def _convert(qty: float, from_unit: str, to_unit: str, pps: Optional[float], fallback_pps: Optional[float]) -> tuple[float, bool]:
    """Brak sonini `to_unit` birligiga o'tkazadi. (qiymat, 1:1 zaxira ishlatildimi)."""
    if from_unit == to_unit or qty == 0:
        return qty, False
    k = pps if pps and pps > 0 else fallback_pps
    if not k or k <= 0:
        return qty, True
    return (qty * k, False) if to_unit == "part" else (qty / k, False)


def components(tl: Timeline, blo: float, bhi: float, cfg: Cfg) -> Comp:
    """[blo, bhi] oralig'idagi komponentlar (blo, bhi tl oynasi ichida bo'lishi shart emas — kesiladi)."""
    c = Comp()
    blo, bhi = max(blo, tl.lo), min(bhi, tl.hi)
    if bhi <= blo:
        return c
    c.ppt = tl.p_eff.measure(blo, bhi)
    ud = tl.ud_all.measure(blo, bhi)
    c.idle = tl.idle.measure(blo, bhi)
    c.stop = ud + c.idle
    c.run = max(0.0, c.ppt - c.stop)
    lo_i = bisect_left(tl.piece_starts, blo - tl.max_dur - 1e-9)
    hi_i = bisect_right(tl.piece_starts, bhi)
    for p in tl.pieces[lo_i:hi_i]:
        ev = p.ev
        if p.b > p.a:
            s0, s1 = max(p.a, blo), min(p.b, bhi)
            if s1 <= s0:
                continue
            length = p.b - p.a
            c.outside_sheets += ev.qty * max(0.0, (s1 - s0) - tl.p_eff.measure(s0, s1)) / length   # smenadan tashqarida
            share = tl.valid.measure(s0, s1) / length
            if share <= 0:
                continue
        else:
            if not (blo < p.a <= bhi):
                continue
            if not tl.valid.contains_point(p.a):
                if not tl.p_eff.contains_point(p.a):
                    c.outside_sheets += ev.qty
                continue
            share = 1.0
        sheets = ev.qty * share
        c.events += 1
        c.sheets_all += sheets
        # ishlab chiqarilgan soni (`unit` birligida)
        pps = ev.parts_per_sheet
        parts_ev: Optional[float] = ev.parts if ev.parts is not None else (ev.qty * pps if pps else None)
        if parts_ev is not None:
            c.parts += parts_ev * share
        if cfg.unit == "part":
            if parts_ev is not None:
                units = parts_ev * share
            else:
                units, c.fallback = sheets, c.fallback + 1
        else:
            units = sheets
        c.produced += units
        if p.ideal is not None:
            c.ideal += p.ideal * share
            c.sheets_known += sheets
            c.units_known += units
        if ev.reject_qty:
            q, fb = _convert(ev.reject_qty * share, ev.unit, cfg.unit, (parts_ev / ev.qty) if parts_ev and ev.qty else pps, tl.avg_pps)
            c.rejects += q
            c.fallback += int(fb)
    for j in tl.rejs:
        if blo < j.ts <= bhi:
            q, fb = _convert(j.qty, j.unit, cfg.unit, j.parts_per_sheet, tl.avg_pps)
            c.rejects += q
            c.fallback += int(fb)
            c.events += 1
    return c


def ratios(c: Comp) -> dict:
    """Komponentlardan A, P, Q, OEE (0…1 yoki None) va yordamchi ko'rsatkichlar."""
    A = min(1.0, c.run / c.ppt) if c.ppt > 0 else None
    share = (c.sheets_known / c.sheets_all) if c.sheets_all > 0 else None
    run_eff = c.run * share if share is not None else None
    p_raw: Optional[float] = None
    if run_eff is not None and run_eff > 0 and c.sheets_known > 0:
        p_raw = c.ideal / run_eff
    P = min(1.0, p_raw) if p_raw is not None else None
    Q: Optional[float] = None
    if c.produced > 0:
        Q = max(0.0, min(1.0, (c.produced - c.rejects) / c.produced))
    if A is not None and A <= 0:
        oee: Optional[float] = 0.0
    elif A is not None and P is not None and Q is not None:
        oee = A * P * Q
    else:
        oee = None
    avg_cycle = (run_eff / c.units_known) if run_eff and c.units_known > 0 else None
    ideal_cycle_unit = (c.ideal / c.units_known) if c.units_known > 0 else None
    return dict(availability=A, performance=P, performance_raw=p_raw, quality=Q, oee=oee,
                planned_min=c.ppt / 60.0, run_min=c.run / 60.0, stop_min=c.stop / 60.0, idle_min=c.idle / 60.0,
                ideal_min=c.ideal / 60.0, produced=c.produced, rejected=c.rejects,
                good=max(0.0, c.produced - c.rejects), sheets=c.sheets_all, parts=c.parts or None,
                avg_cycle_s=avg_cycle, ideal_cycle_s=ideal_cycle_unit, events=c.events,
                capped=bool(p_raw is not None and p_raw > 1.0 + 1e-12),
                outside_sheets=c.outside_sheets, fallback=c.fallback)


# ───────────────────────── Vaqt oralig'i va guruhlash (zavod mahalliy vaqti: qat'iy siljish) ─────────────────────────
def local_day_index(t: float, off_min: int) -> int:
    """Mahalliy sana raqami (1970-01-01 dan kunlar)."""
    return math.floor((t + off_min * 60) / 86400.0)


def day_start(idx: int, off_min: int) -> float:
    return idx * 86400.0 - off_min * 60


def bucket_edges(lo: float, hi: float, group: str, off_min: int) -> list[tuple[float, float, float]]:
    """[lo, hi] ni soat/kun/hafta (Dushanba) bo'yicha bo'laklaydi; (boshi, oxiri, kesilmagan boshlang'ich UTC) — chekkalar kesiladi."""
    if hi <= lo:
        return []
    off = off_min * 60
    if group == "hour":
        step, origin = 3600.0, 0.0
    elif group == "day":
        step, origin = 86400.0, 0.0
    else:                                    # week: Dushanba (1970-01-05) dan
        step, origin = 7 * 86400.0, 4 * 86400.0
    out: list[tuple[float, float, float]] = []
    k = math.floor((lo + off - origin) / step)
    while True:
        s = origin + k * step - off
        e = s + step
        if s >= hi:
            break
        out.append((max(s, lo), min(e, hi), s))
        k += 1
        if len(out) > 5000:
            break
    return out


def iso_utc(t: Optional[float]) -> Optional[str]:
    if t is None:
        return None
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_label(t: float, off_min: int, group: str) -> str:
    d = datetime.fromtimestamp(t + off_min * 60, tz=timezone.utc)
    if group == "hour":
        return d.strftime("%Y-%m-%d %H:00")
    if group == "week":
        iso = d.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    return d.strftime("%Y-%m-%d")
