"""Kroy kartasidagi detal yozuvlari (raqam, uzunlik, en, nom) joylashuvi — bir-birining ustiga tushmasin, detaldan chiqmasin.

Xodim skrini (2026-11-24): tor tik detallarda (35×340) en raqamlari ustuni va detal raqami bir joyga tushib o'qilmasdi.
Onlayn tizimda («test uchun», shunday detallar bilan jonli tekshirildi) ham yozuvlar ustma-ust — u yerda yechim yo'q.
Qoida (ekrandagi karta `frontend/src/features/cs/partLabels.ts` bilan bir xil): har yozuvning bir nechta joyi (afzal tartibda);
detal ichida, bir-biriga tegmaydigan eng yaxshi to'plam. Ustuvorlik: detal raqami → uzunlik / en → nom. Raqam sig'masa —
shu detalda shrift bosqichma-bosqich kichrayadi (`min_fs` gacha). Oddiy detalda birinchi variantlar — avvalgi ko'rinish.
"""
from __future__ import annotations

from typing import Optional

CW = 0.6        # monospace raqam eni (fs ulushi)
ASC = 0.74
DESC = 0.06
STEP = 0.95     # ustma-ust belgilar qadami
GAP_X = 0.5     # yonma-yon yozuvlar orasidagi bo'shliq
GAP_Y = 0.75    # ustma-ust (tik ustunda «10» va «45» bitta «1045» bo'lib o'qilmasin)
EDGE = 0.12


def _box(it: dict, fs: float) -> tuple[float, float, float, float]:
    f = fs * it.get("scale", 1.0)
    n = len(it["text"])
    if it["mode"] == "h":
        w = n * CW * f
        x0 = it["x"] if it["anchor"] == "start" else it["x"] - w if it["anchor"] == "end" else it["x"] - w / 2
        return x0, it["y"] - ASC * f, x0 + w, it["y"] + DESC * f
    if it["mode"] == "s":
        w = CW * f
        x0 = it["x"] if it["anchor"] == "start" else it["x"] - w if it["anchor"] == "end" else it["x"] - w / 2
        return x0, it["y"] - ASC * f, x0 + w, it["y"] + (n - 1) * STEP * f + DESC * f
    return it["x"] - DESC * f, it["y"], it["x"] + ASC * f, it["y"] + n * CW * f      # 90° burilgan: pastga o'sadi


def _layout(x: float, y: float, l: float, w: float, fs: float, num: Optional[str], len_s: str, wid_s: str,
            name: Optional[str], num_scale: float, name_scale: float, rotate_first: bool, mirror: bool,
            allow_rot: bool) -> list[dict]:
    cx, cy, R, B = x + l / 2, y + w / 2, x + l, y + w
    pad = 0.3 * fs

    def mid(sc=1.0):
        return cy + (ASC - DESC) / 2 * fs * sc

    def it(kind, text, mode, xx, yy, anchor, scale=1.0):
        return dict(kind=kind, text=text, mode=mode, x=xx, y=yy, anchor=anchor, scale=scale)

    cand: dict[str, list[dict]] = {"num": [], "len": [], "wid": [], "name": []}
    if num:
        n, ns = len(num), num_scale
        stack_mid = cy - ((n - 1) * STEP - ASC + DESC) / 2 * fs * ns
        cand["num"] = [
            it("num", num, "h", cx, mid(ns), "middle", ns),
            it("num", num, "s", cx, stack_mid, "middle", ns),
            it("num", num, "h", cx, y + w * 0.3 + (ASC - DESC) / 2 * fs * ns, "middle", ns),
            it("num", num, "h", cx, y + w * 0.7 + (ASC - DESC) / 2 * fs * ns, "middle", ns),
            it("num", num, "h", x + l * 0.6, mid(ns), "middle", ns),
            it("num", num, "h", x + l * 0.6, y + w * 0.3 + (ASC - DESC) / 2 * fs * ns, "middle", ns),
            it("num", num, "h", x + l * 0.35, mid(ns), "middle", ns),
            it("num", num, "s", cx, y + w * 0.3 - (n - 1) * STEP * fs * ns / 2 + ASC * fs * ns / 2, "middle", ns),
            it("num", num, "s", cx, y + w * 0.62 - (n - 1) * STEP * fs * ns / 2 + ASC * fs * ns / 2, "middle", ns),
        ]
    ln = len(len_s)
    cand["len"] = [
        it("len", len_s, "h", x + 0.35 * fs, B - 0.35 * fs, "start"),
        it("len", len_s, "h", x + pad, mid(), "start"),                              # ingichka polosa: bitta qatorda
        it("len", len_s, "s", x + pad, B - 0.35 * fs - (ln - 1) * STEP * fs, "start"),
        it("len", len_s, "s", cx, B - 0.35 * fs - (ln - 1) * STEP * fs, "middle"),
    ]
    rot = [it("wid", wid_s, "r", R - 1.25 * fs, y + 0.35 * fs, "start")] if allow_rot else []
    cand["wid"] = (rot if rotate_first else []) + [
        it("wid", wid_s, "s", R - pad, y + 1.05 * fs, "end"),
        it("wid", wid_s, "h", R - 0.3 * fs, y + 0.95 * fs, "end"),                  # ingichka uzun detal
        it("wid", wid_s, "h", R - pad, mid(), "end"),                               # ingichka polosa
        it("wid", wid_s, "s", cx, y + 1.05 * fs, "middle"),                         # tor tik detal
    ] + ([] if rotate_first else rot)
    if name:
        below = it("name", name, "h", cx, mid() + 1.1 * fs, "middle", name_scale)
        center = it("name", name, "h", cx, mid(), "middle", name_scale)
        cand["name"] = [below, center] if num else [center, below]
    if mirror:          # ko'zgu: uzunlik / en teskari burchaklarda (matn o'qiladigan holda)
        for k in ("len", "wid"):
            for c in cand[k]:
                if c["mode"] == "r":
                    c["x"] = x + 0.5 * fs
                    continue
                c["x"] = 2 * cx - c["x"]
                c["anchor"] = {"start": "end", "end": "start"}.get(c["anchor"], c["anchor"])

    def inside(b):
        e = EDGE * fs
        return b[0] >= x + e and b[2] <= R - e and b[1] >= y + e and b[3] <= B - e

    def sep(a, b):
        gx, gy = GAP_X * fs, GAP_Y * fs
        return not (a[0] < b[2] + gx and b[0] < a[2] + gx and a[1] < b[3] + gy and b[1] < a[3] + gy)

    ok = {k: [(c, _box(c, fs)) for c in v if inside(_box(c, fs))] for k, v in cand.items()}

    def opt(a):
        return [(v, i) for i, v in enumerate(a)] + [(None, 0)]
    best_s, best = -1.0, []
    for nv, ni in opt(ok["num"]):
        for lv, li in opt(ok["len"]):
            for wv, wi in opt(ok["wid"]):
                ch = [v for v in (nv, lv, wv) if v]
                if any(not sep(ch[i][1], ch[j][1]) for i in range(len(ch)) for j in range(i + 1, len(ch))):
                    continue
                s = (1000 - ni * 3 if nv else 0) + (100 - li * 2 if lv else 0) + (100 - wi * 2 if wv else 0)
                nm = None
                for mv, mi in opt(ok["name"]):
                    if mv is None:
                        break
                    if all(sep(v[1], mv[1]) for v in ch):
                        s += 10 - mi
                        nm = mv[0]
                        break
                if s > best_s:
                    best_s, best = s, [v[0] for v in ch] + ([nm] if nm else [])
    return best


def part_label_layout(x: float, y: float, l: float, w: float, fs: float, *, num: Optional[str], len_s: str, wid_s: str,
                      name: Optional[str] = None, num_scale: float = 1.0, name_scale: float = 0.85,
                      rotate_first: bool = False, mirror: bool = False, min_fs: Optional[float] = None) -> list[dict]:
    """Yozuvlar ro'yxati: {kind: num|len|wid|name, text, mode: h|s|r, x, y (asos chizig'i / burish nuqtasi), anchor, scale}.
    Shrift o'lchami = fs × scale. h — gorizontal, s — belgilar ustma-ust, r — 90° burilgan."""
    allow_rot = rotate_first
    first = _layout(x, y, l, w, fs, num, len_s, wid_s, name, num_scale, name_scale, rotate_first, mirror, allow_rot)
    if not num or any(i["kind"] == "num" for i in first):
        return first
    lo = min_fs if min_fs is not None else fs * 0.5
    for k in (0.85, 0.7, 0.55, 0.45, 0.35):
        if fs * k < lo:
            break
        items = _layout(x, y, l, w, fs * k, num, len_s, wid_s, name, num_scale, name_scale, rotate_first, mirror, allow_rot)
        if any(i["kind"] == "num" for i in items):
            for i in items:
                i["scale"] *= k
            return items
    return first


def label_box(item: dict, fs: float) -> tuple[float, float, float, float]:
    """Yozuv egallaydigan to'rtburchak (x0, y0, x1, y1) — testlar uchun."""
    return _box(item, fs)
