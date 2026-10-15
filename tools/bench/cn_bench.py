"""(CN) nesting optimizatori benchmarki (W16): sintetik instanslar (korxona fayllari ishlatilmaydi).

  python cn_bench.py            — to'rtburchaklar (50 / 120 xil) va aralash konturlar (doira, L, teshikli) — fast / normal

Har natija mustaqil skalyar tekshiruvdan o'tkaziladi (`backend/tests/cn_w16_util.check_sheet`): kesishish, masofa, list chetidan masofa.
CS optimizatoriga (`optimizer.py`, `colpack.py`) bu skript TEGMAYDI. Raqamlar — `docs/mebelix/T_W16_CN.md` §3.
"""
from __future__ import annotations

import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend", "tests"))

from app.services import cn_geometry as G  # noqa: E402
from app.services import cn_nest as N  # noqa: E402
from cn_w16_util import check_sheet, shape_circle, shape_L, shape_ring, shape_round_hole  # noqa: E402


def parts_of(specs):
    return [N.NestPart(f"p{i}", i + 1, sh, q, N.allowed_angles(g, True, 0, True)) for i, (sh, q, g) in enumerate(specs)]


def bench(name, specs, quality, sheet=(2750, 1830), spacing=6.25, margin=5.0):
    parts = parts_of(specs)
    t = time.time()
    out = N.nest(parts, [N.NestSheet("s", *sheet, N.UNLIMITED)], N.NestParams(spacing=spacing, margin=margin, quality=quality))
    dt = time.time() - t
    used = sum(ly.copies for ly in out.layouts)
    area = sum(p.shape.area * p.qty for p in parts)
    bad = 0
    for ly in out.layouts:
        polys = [G.place_shape(parts[it.part].shape, it.angle, it.x, it.y)[:2] for it in ly.items]
        bad += len(check_sheet(polys, sheet[0], sheet[1], margin, spacing))
    print(f"{name:30s} {quality:6s} dona={sum(p.qty for p in parts):4d} list={used:3d} F={area / (used * sheet[0] * sheet[1]) * 100 if used else 0:5.1f}% "
          f"sig'magan={len(out.unplaced)} xato={bad} vaqt={dt:5.2f}s sinov={out.info['trials']} katak={list(out.info['cells'].values())}")


def mixed(rnd, n):
    out = []
    for _ in range(n):
        k = rnd.choice(("c", "L", "ring", "rect", "rh"))
        if k == "c":
            s = shape_circle(rnd.uniform(40, 220), 32)
        elif k == "L":
            s = shape_L(rnd.uniform(200, 700), rnd.uniform(200, 600), rnd.uniform(60, 150))
        elif k == "ring":
            s = shape_ring(rnd.uniform(300, 800), rnd.uniform(300, 600), rnd.uniform(100, 250), rnd.uniform(80, 200))
        elif k == "rh":
            s = shape_round_hole(rnd.uniform(300, 700), rnd.uniform(300, 600), rnd.uniform(50, 130), 28)
        else:
            s = G.rect_shape(rnd.randint(60, 500), rnd.randint(60, 400))
        out.append((s, rnd.randint(1, 3), False))
    return out


def main() -> None:
    rnd = random.Random(5)
    rects50 = [(G.rect_shape(rnd.randint(100, 800), rnd.randint(100, 600)), rnd.randint(1, 3), False) for _ in range(50)]
    rnd = random.Random(8)
    rects120 = [(G.rect_shape(rnd.randint(60, 700), rnd.randint(60, 500)), rnd.randint(1, 6), rnd.random() < .3) for _ in range(120)]
    rnd = random.Random(9)
    mix40 = mixed(rnd, 40)
    for q in ("fast", "normal"):
        bench("50 xil to'rtburchak", rects50, q)
        bench("120 xil to'rtburchak", rects120, q)
        bench("40 aralash kontur", mix40, q)


if __name__ == "__main__":
    main()
