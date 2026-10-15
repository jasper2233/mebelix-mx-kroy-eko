"""(CL) pogonaj kroy optimizatori benchmarki (W11): sintetik instanslar (korxona fayllari ishlatilmaydi).

  python cl_bench.py            — 3 ta sinf: realistik (detal polosaning 3–30 %), qiyin (3–45 %), katta (1000 detal)

Ko'rsatkichlar: polosalar soni LB (⌈Σ(p + k)/(U + k)⌉) ga nisbatan, FFD ga nisbatan, vaqt (normal / fast / max). LB zaif bo'lgan
(detal polosa yarmidan katta) instanslarda LB + 1 dan oshish optimizator kamchiligi emas — `_exact_pack` bilan tekshiriladi (qarang T_W11_CL.md §6).
"""
from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend"))

from app.models import CLParams, StockSheet  # noqa: E402
from app.services import cl_optimizer as co  # noqa: E402
from app.services.cl_optimizer import LItem  # noqa: E402


def instance(rnd: random.Random, lo: float, hi: float, n_max: int = 400):
    L = rnd.choice([3000, 6000])
    cl = CLParams(width=100, kerf=rnd.choice([3, 4.4]), trim=rnd.choice([0, 10]), waste_min=100, business_min=1000,
                  waste_incl_trim=rnd.random() < 0.7)
    pieces: list[float] = []
    for _k in range(rnd.randint(2, 30)):
        pieces += [float(rnd.randint(int(L * lo), int(L * hi)))] * rnd.randint(1, 20)
    return L, cl, pieces[:n_max]


def run(name: str, lo: float, hi: float, N: int = 200, seed: int = 2026, quality: str = "normal") -> None:
    rnd = random.Random(seed)
    eq = p1 = p2 = worse_ffd = 0
    tot_t = max_t = 0.0
    for _i in range(N):
        L, cl, pieces = instance(rnd, lo, hi)
        cl = cl.model_copy(update={"quality": quality})
        items = [LItem(f"p{i}", i, p) for i, p in enumerate(pieces)]
        st = [StockSheet(id="s", length=L, width=100)]
        t = time.time()
        res = co.optimize_linear(items, st, cl)
        dt = time.time() - t
        tot_t += dt
        max_t = max(max_t, dt)
        assert not co.validate_cl(res, items, st, cl)
        lb = co.lower_bound(pieces, st, cl)
        d = res.total_sheets - lb
        eq += d == 0
        p1 += d == 1
        p2 += d >= 2
        worse_ffd += res.total_sheets > co.ffd_strips(pieces, st, cl)
    print(f"{name:34s} [{quality:6s}] N={N}: =LB {eq}  +1 {p1}  ≥+2 {p2}  | ≤LB+1 {100 * (eq + p1) / N:.1f}%  FFD dan yomon {worse_ffd}"
          f"  | vaqt o'rtacha {1000 * tot_t / N:.0f} ms, max {1000 * max_t:.0f} ms")


def big(quality: str) -> None:
    rnd = random.Random(1000)
    lens = [rnd.randint(200, 2800) for _ in range(300)]
    pieces = [float(lens[i % 300]) for i in range(1000)]
    cl = CLParams(width=100, kerf=3, trim=10, quality=quality)
    items = [LItem(f"p{i}", i, p) for i, p in enumerate(pieces)]
    st = [StockSheet(id="s", length=6000, width=100)]
    t = time.time()
    res = co.optimize_linear(items, st, cl)
    print(f"1000 detal (300 xil uzunlik) [{quality:6s}]: {res.total_sheets} polosa, LB {co.lower_bound(pieces, st, cl)}, "
          f"{len(res.maps)} karta, {time.time() - t:.2f} s")


if __name__ == "__main__":
    for q in ("normal", "fast"):
        run("realistik (3–30 %)", 0.03, 0.30, quality=q)
        run("qiyin (3–45 %)", 0.03, 0.45, quality=q)
    run("juda qiyin (3–80 %, LB zaif)", 0.03, 0.80, quality="normal")
    for q in ("fast", "normal", "max"):
        big(q)
