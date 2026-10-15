"""W16 (CN) — nesting algoritmi: to'g'rilik (200 ta tasodifiy instans: kesishish 0, hamma detal list ichida, masofa), ichki kesimlarga
joylash, determinizm, vaqt, ruxsat etilgan burchaklar / tekstura, cheklangan listlar, takrorlanuvchi sxemalar."""
from __future__ import annotations

import math
import random
import time

import pytest

from app.services import cn_geometry as G
from app.services import cn_nest as N
from app.services import cn_validate as V
from cn_w16_util import (check_sheet, circle_ring, point_in_ring, shape_circle, shape_L, shape_ring, shape_round_hole)


def _parts(specs, rot90=True, rot_step=0.0, use_grain=True):
    """specs: [(shape, qty, grain)]."""
    return [N.NestPart(f"p{i}", i + 1, sh, q, N.allowed_angles(g, rot90, rot_step, use_grain)) for i, (sh, q, g) in enumerate(specs)]


def _polys(out, parts, sheets, li):
    ly = out.layouts[li]
    res = []
    for it in ly.items:
        outer, holes, _bw, _bh = G.place_shape(parts[it.part].shape, it.angle, it.x, it.y)
        res.append((outer, holes))
    return res


def _assert_valid(out, parts, sheets, spacing, margin, rot90=True, rot_step=0.0, use_grain=True, grains=None):
    placed = [0] * len(parts)
    for li, ly in enumerate(out.layouts):
        sh = sheets[ly.sheet]
        polys = _polys(out, parts, sheets, li)
        assert check_sheet(polys, sh.length, sh.width, margin, spacing) == [], f"layout {li}"          # mustaqil (skalyar) tekshiruv
        vp = [V.Poly(parts[it.part].uid, o, h) for it, (o, h) in zip(ly.items, polys)]
        assert V.check_polys(vp, sh.length, sh.width, margin, spacing) == []                             # cn_validate bilan bir xil xulosa
        for it in ly.items:
            placed[it.part] += ly.copies
            g = bool(grains[it.part]) if grains else False
            ok = (it.angle % 180 == 0) if (g and use_grain) else True
            assert ok, f"tekstura buzildi: burchak {it.angle}"
            assert it.angle in parts[it.part].angles
        assert ly.copies >= 1
    for pi, p in enumerate(parts):
        n_un = sum(1 for u in out.unplaced if u == pi)
        assert placed[pi] + n_un == p.qty, f"detal {p.uid}: {placed[pi]} + {n_un} != {p.qty}"


def _rand_shape(rnd: random.Random, sheet_w: float):
    k = rnd.choice(("rect", "rect", "circle", "L", "ring", "roundhole", "rect"))
    lim = sheet_w * 0.6
    if k == "rect":
        return G.rect_shape(rnd.uniform(40, lim), rnd.uniform(40, lim))
    if k == "circle":
        return shape_circle(rnd.uniform(20, lim / 2), rnd.choice((16, 24, 32)))
    if k == "L":
        a, b = rnd.uniform(120, lim), rnd.uniform(120, lim)
        return shape_L(a, b, rnd.uniform(30, min(a, b) * 0.6))
    if k == "ring":
        L, W = rnd.uniform(150, lim), rnd.uniform(150, lim)
        return shape_ring(L, W, rnd.uniform(30, L * 0.6), rnd.uniform(30, W * 0.6))
    L, W = rnd.uniform(150, lim), rnd.uniform(150, lim)
    return shape_round_hole(L, W, rnd.uniform(15, min(L, W) * 0.35), 20)


# ───────────────────────── 200 ta tasodifiy instans ─────────────────────────
@pytest.mark.parametrize("batch", range(4))
def test_random_instances_are_valid(batch):
    """200 instans (4 × 50): to'rtburchak / doira / L / teshikli kontur aralash; kesishish 0, hamma detal list ichida, masofa qoidasi,
    hisob-kitob (joylangan + sig'magan = soni). Mustaqil skalyar tekshiruvchi va cn_validate ikkalasi xato topmaydi."""
    n_placed = 0
    for k in range(50):
        seed = 1000 * batch + k
        rnd = random.Random(seed)
        L, W = rnd.choice(((1200, 800), (1500, 1000), (900, 600), (2000, 1000), (700, 500)))
        spacing = rnd.choice((0.0, 2.0, 6.25, 10.0))
        margin = rnd.choice((0.0, 5.0, 12.0))
        rot90 = rnd.random() < 0.8
        step = 45.0 if rnd.random() < 0.15 else 0.0
        specs = [(_rand_shape(rnd, W), rnd.randint(1, 4), rnd.random() < 0.25) for _ in range(rnd.randint(3, 9))]
        parts = _parts(specs, rot90, step)
        stock = [N.NestSheet("s", L, W, N.UNLIMITED)]
        out = N.nest(parts, stock, N.NestParams(spacing=spacing, margin=margin, quality="fast"))
        _assert_valid(out, parts, stock, spacing, margin, rot90, step, True, [g for _s, _q, g in specs])
        n_placed += sum(len(ly.items) * ly.copies for ly in out.layouts)
    assert n_placed > 100


@pytest.mark.parametrize("batch", range(2))
def test_random_instances_all_trial_kinds_are_valid(batch):
    """Barcha sinov turlari (to'ldirish o'qi «qisqa» ham, burilish afzalligi tik / yotiq ham, urug'li tasodifiy tartiblar): 12 sinov."""
    for k in range(25):
        rnd = random.Random(777 + 100 * batch + k)
        L, W = rnd.choice(((1200, 800), (700, 1100), (900, 600), (600, 1500)))                 # tik listlar ham (axis «y» ga o'tadi)
        spacing = rnd.choice((0.0, 3.0, 6.25))
        margin = rnd.choice((0.0, 5.0))
        specs = [(_rand_shape(rnd, min(L, W)), rnd.randint(1, 4), rnd.random() < 0.2) for _ in range(rnd.randint(4, 9))]
        parts = _parts(specs)
        stock = [N.NestSheet("s", L, W, N.UNLIMITED)]
        out = N.nest(parts, stock, N.NestParams(spacing=spacing, margin=margin, quality="fast", max_trials=12, stop_at_bound=False))
        assert out.info["trials"] >= 6
        _assert_valid(out, parts, stock, spacing, margin, True, 0.0, True, [g for _s, _q, g in specs])

def test_dense_rect_instance_with_two_stock_types_and_limited_qty():
    rnd = random.Random(7)
    specs = [(G.rect_shape(rnd.randint(60, 400), rnd.randint(60, 300)), rnd.randint(1, 3), False) for _ in range(25)]
    parts = _parts(specs)
    stock = [N.NestSheet("rem", 800, 600, 2), N.NestSheet("new", 1500, 1000, N.UNLIMITED)]       # avval qoldiq (≤ 2 dona), keyin yangi list
    out = N.nest(parts, stock, N.NestParams(spacing=6.25, margin=5.0, quality="normal"))
    _assert_valid(out, parts, stock, 6.25, 5.0)
    used_rem = sum(ly.copies for ly in out.layouts if ly.sheet == 0)
    assert 1 <= used_rem <= 2                                                                    # ro'yxat tartibi va soni cheklovi
    assert out.layouts[0].sheet == 0


def test_unplaceable_part_goes_to_unplaced_and_rest_is_placed():
    parts = _parts([(G.rect_shape(3000, 100), 1, False), (G.rect_shape(200, 100), 3, False)])
    stock = [N.NestSheet("s", 1200, 800, N.UNLIMITED)]
    out = N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="fast"))
    assert out.unplaced == [0]
    assert sum(len(ly.items) * ly.copies for ly in out.layouts) == 3
    _assert_valid(out, parts, stock, 6, 5)
    # list chetidan masofa hisobga olinadi: 1190 × 790 detal 1200 × 800 listga margin 5 da sig'maydi, margin 0 da sig'adi
    big = _parts([(G.rect_shape(1190, 790), 1, False)])
    assert N.nest(big, stock, N.NestParams(spacing=6, margin=5, quality="fast")).unplaced == [0]
    ok = N.nest(big, stock, N.NestParams(spacing=6, margin=0, quality="fast"))
    assert ok.unplaced == [] and len(ok.layouts) == 1


# ───────────────────────── Ichki kesimlarga joylash ─────────────────────────
def test_small_parts_fall_into_holes_of_larger_part():
    ring = shape_ring(700, 600, 500, 400)                   # 500×400 teshikli panel
    small = G.rect_shape(120, 80)
    parts = _parts([(ring, 1, False), (small, 4, False)])
    stock = [N.NestSheet("s", 760, 660, 1)]                 # list panelning o'zidan arang katta: kichiklar faqat teshikka sig'adi
    out = N.nest(parts, stock, N.NestParams(spacing=6.25, margin=5, quality="normal"))
    _assert_valid(out, parts, stock, 6.25, 5)
    assert out.unplaced == [] and len(out.layouts) == 1
    ring_it = next(it for it in out.layouts[0].items if it.part == 0)
    outer, holes, _w, _h = G.place_shape(ring, ring_it.angle, ring_it.x, ring_it.y)
    inside = 0
    for it in out.layouts[0].items:
        if it.part != 1:
            continue
        o2, _h2, _a, _b = G.place_shape(small, it.angle, it.x, it.y)
        assert all(point_in_ring(p, holes[0]) for p in o2)  # to'liq teshik ichida
        inside += 1
    assert inside == 4


def test_circle_in_round_hole_and_L_interlock_are_valid():
    parts = _parts([(shape_round_hole(500, 500, 190, 36), 2, False), (shape_circle(80, 24), 6, False), (shape_L(300, 250, 70), 6, False)])
    stock = [N.NestSheet("s", 2000, 1000, N.UNLIMITED)]
    out = N.nest(parts, stock, N.NestParams(spacing=6.25, margin=5, quality="normal"))
    _assert_valid(out, parts, stock, 6.25, 5)
    assert out.unplaced == []
    area = sum(p.shape.area * p.qty for p in parts)
    used = sum(ly.copies for ly in out.layouts)
    assert area / (used * 2000 * 1000) > 0.15                # mantiqiy zichlik (teshikka tushgan doiralar bilan)


# ───────────────────────── Tekstura va burilishlar ─────────────────────────
def test_grain_and_rotation_rules():
    assert N.allowed_angles(False, True, 0, True) == [0.0, 90.0, 180.0, 270.0]
    assert N.allowed_angles(True, True, 0, True) == [0.0, 180.0]
    assert N.allowed_angles(True, True, 0, False) == [0.0, 90.0, 180.0, 270.0]        # use_grain o'chiq — Ткт e'tiborsiz
    assert N.allowed_angles(False, False, 0, True) == [0.0]
    assert N.allowed_angles(False, False, 45, True) == [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    assert N.allowed_angles(True, True, 45, True) == [0.0, 180.0]
    # 1000 × 300 × 2 detal 700 × 1200 listda faqat burilgandagina sig'adi (yonma-yon, 90°): tekstura ✓ — sig'maydi, ✗ — sig'adi
    stock = [N.NestSheet("s", 700, 1200, 1)]
    prm = N.NestParams(spacing=6, margin=5, quality="fast")
    grain = N.nest(_parts([(G.rect_shape(1000, 300), 2, True)]), stock, prm)
    free = N.nest(_parts([(G.rect_shape(1000, 300), 2, False)]), stock, prm)
    assert len(grain.unplaced) == 2 and free.unplaced == []
    assert {it.angle for ly in free.layouts for it in ly.items} <= {90.0, 270.0}


def test_free_angle_part_is_rotated_to_fit_and_valid():
    # uzun ingichka detal diagonal bo'ylab: 0 / 90 da sig'maydi, 45° da sig'adi
    stock = [N.NestSheet("s", 800, 800, 1)]
    bar = G.rect_shape(900, 60)
    prm = N.NestParams(spacing=6, margin=5, quality="normal")
    assert N.nest(_parts([(bar, 1, False)], True, 0), stock, prm).unplaced == [0]
    out = N.nest(_parts([(bar, 1, False)], True, 45), stock, prm)
    assert out.unplaced == []
    assert out.layouts[0].items[0].angle in (45.0, 135.0, 225.0, 315.0)
    _assert_valid(out, _parts([(bar, 1, False)], True, 45), stock, 6, 5, True, 45)


# ───────────────────────── Determinizm, vaqt, takrorlanuvchi sxema ─────────────────────────
def _sig(out):
    return [(ly.sheet, ly.copies, [(it.part, it.angle, round(it.x, 6), round(it.y, 6)) for it in ly.items]) for ly in out.layouts], out.unplaced


@pytest.mark.parametrize("quality", ["fast", "normal"])
def test_deterministic(quality):
    rnd = random.Random(11)
    specs = [(_rand_shape(rnd, 1000), rnd.randint(1, 3), rnd.random() < 0.3) for _ in range(12)]
    prm = N.NestParams(spacing=6.25, margin=5, quality=quality)
    stock = [N.NestSheet("s", 1500, 1000, N.UNLIMITED)]
    a = N.nest(_parts(specs), stock, prm)
    b = N.nest(_parts(specs), stock, prm)
    assert _sig(a) == _sig(b)


def test_50_random_rects_within_budget_and_valid():
    """Qabul: 50 ta tasodifiy to'rtburchak, «normal» ≤ 10 s; to'g'rilik 100 %."""
    rnd = random.Random(5)
    specs = [(G.rect_shape(rnd.randint(100, 800), rnd.randint(100, 600)), rnd.randint(1, 3), False) for _ in range(50)]
    parts = _parts(specs)
    stock = [N.NestSheet("s", 2750, 1830, N.UNLIMITED)]
    t = time.monotonic()
    out = N.nest(parts, stock, N.NestParams(spacing=6.25, margin=5, quality="normal"))
    assert time.monotonic() - t < 10.0
    _assert_valid(out, parts, stock, 6.25, 5)
    assert out.unplaced == []
    area = sum(p.shape.area * p.qty for p in parts)
    used_area = sum(2750 * 1830 * ly.copies for ly in out.layouts)
    assert area / used_area > 0.60                         # CS (gilyotina) 4 list/ ~71 % umumiy; nesting kamida shunday sinfda


def test_identical_layouts_are_merged_into_copies():
    parts = _parts([(G.rect_shape(600, 400), 20, False)])
    stock = [N.NestSheet("s", 1250, 850, N.UNLIMITED)]      # har listga 2×2 = 4 ta sig'adi → 20 ta = 5 list = 1 karta × 5
    out = N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="fast"))
    assert len(out.layouts) == 1 and out.layouts[0].copies == 5 and len(out.layouts[0].items) == 4
    _assert_valid(out, parts, stock, 6, 5)


def test_cancel_raises_and_time_limit_returns_best():
    rnd = random.Random(2)
    specs = [(G.rect_shape(rnd.randint(100, 500), rnd.randint(100, 400)), 3, False) for _ in range(40)]
    parts = _parts(specs)
    stock = [N.NestSheet("s", 2750, 1830, N.UNLIMITED)]
    with pytest.raises(N.NestCancelled):
        N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="normal"), cancel=lambda: True)
    prog = []
    out = N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="normal", time_limit=0.05),
                 progress=lambda f, m: prog.append(f))
    assert out.layouts and prog and prog[-1] == 1.0 and all(0 <= p <= 1 for p in prog)
    assert prog == sorted(prog) or max(prog) <= 1.0


def test_spacing_zero_allows_touching_but_never_crossing():
    parts = _parts([(G.rect_shape(300, 200), 8, False)])
    stock = [N.NestSheet("s", 1210, 410, 1)]                # 4 × 2 = 8 ta, bir-biriga tegib (masofa 0)
    out = N.nest(parts, stock, N.NestParams(spacing=0.0, margin=5, quality="normal"))
    assert out.unplaced == [] and len(out.layouts) == 1 and len(out.layouts[0].items) == 8
    _assert_valid(out, parts, stock, 0.0, 5)


# ───────────────────────── Raster yordamchilari ─────────────────────────
def test_raster_mask_is_conservative_cover_of_polygon():
    """Niqob kataklari poligon bilan kesishgan HAR BIR katakni qamrashi shart (konservativ)."""
    sh = shape_circle(100, 40)
    mask, i0, j0 = N.raster_rings([sh.outer], 5.0)
    assert (i0, j0) == (0, 0)
    h, w = mask.shape
    assert (w, h) == (40, 40)
    rnd = random.Random(1)
    for _ in range(3000):                                   # poligon ichidagi har tasodifiy nuqta niqobda bo'lishi shart
        x, y = rnd.uniform(0, 200), rnd.uniform(0, 200)
        if point_in_ring((x, y), sh.outer):
            assert mask[int(y // 5), int(x // 5)]


def test_dilation_kernel_gives_required_clearance():
    """Dilatatsiya yadrosi: niqoblari kesishmaydigan ikki detal orasida haqiqiy masofa ≥ spacing (konservativ)."""
    rho = 6.25 / 2.0
    m = N.np.ones((10, 10), dtype=bool)
    D, R = N.dilate(m, rho)
    assert D.shape == (10 + 2 * R, 10 + 2 * R) and R >= math.ceil(rho)
    # to'rtburchak blok: yon tomondagi egallangan katak soni = ceil(rho) (kvadratlar masofasi < rho ⇒ egallangan); keyingi katakkacha
    # bo'sh masofa shuncha katak: katak 2 mm ⇒ ≥ spacing, lekin ortiqcha konservativ emas (bir katakdan ko'p emas)
    row = D[R + 5]
    blocked_right = int(row[R + 10:].sum())
    assert blocked_right == R == math.ceil(rho)
    assert blocked_right * 2.0 >= 6.25 - 1e-9 and (blocked_right - 1) * 2.0 < 6.25
    assert D[R + 5, :R].all() and D[:R, R + 5].all() and D[R + 10:, R + 5].all()          # to'rt tomonda ham bir xil


def test_sort_mode_list_keeps_user_order():
    """«Сортировка»: order="list" — detallar ro'yxat tartibida joylanadi (avto rejimda katta detal birinchi bo'lardi)."""
    small, big = G.rect_shape(100, 80), G.rect_shape(700, 500)
    parts = _parts([(small, 2, False), (big, 1, False)])
    stock = [N.NestSheet("s", 1500, 900, N.UNLIMITED)]
    auto = N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="fast"))
    lst = N.nest(parts, stock, N.NestParams(spacing=6, margin=5, quality="fast", order="list"))
    assert auto.layouts[0].items[0].part == 1                  # avto: eng katta birinchi
    assert lst.layouts[0].items[0].part == 0 and lst.layouts[0].items[0].x == 5 and lst.layouts[0].items[0].y == 5
    _assert_valid(lst, parts, stock, 6, 5)



def test_independent_checker_itself_detects_violations():
    """Mustaqil skalyar tekshiruvchi bo'sh (vacuous) o'tmasligi uchun: ataylab buzilgan joylashuvlarni topishi shart."""
    r = G.rect_ring(100, 100)
    sh = lambda dx, dy: ([(p[0] + dx, p[1] + dy) for p in r], [])
    assert check_sheet([sh(10, 10), sh(120, 10)], 500, 500, 5, 10) == []
    assert any(e.startswith("cross") for e in check_sheet([sh(10, 10), sh(60, 60)], 500, 500, 5, 10))
    assert any(e.startswith("gap") for e in check_sheet([sh(10, 10), sh(115, 10)], 500, 500, 5, 10))
    assert any(e.startswith("outside") for e in check_sheet([sh(2, 10)], 500, 500, 5, 10))
    small = ([(p[0] + 30, p[1] + 30) for p in G.rect_ring(20, 20)], [])
    assert any(e.startswith("inside") for e in check_sheet([sh(10, 10), small], 500, 500, 5, 10))      # to'liq ichkarida
    ring_o = [(p[0], p[1]) for p in G.rect_ring(300, 300)]
    ring_h = [G.orient_ring([(100, 100), (200, 100), (200, 200), (100, 200)], False)]
    inner = ([(p[0] + 130, p[1] + 130) for p in G.rect_ring(40, 40)], [])
    assert check_sheet([(ring_o, ring_h), inner], 500, 500, 0, 10) == []                              # teshik ichida — to'g'ri
    assert any(e.startswith("gap") for e in check_sheet([(ring_o, ring_h), ([(p[0] + 104, p[1] + 130) for p in G.rect_ring(40, 40)], [])],
                                                      500, 500, 0, 10))
