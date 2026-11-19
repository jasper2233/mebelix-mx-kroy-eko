"""Kroy qidiruvining «ish soati» — yuklama ostida ham bir xil hajmdagi qidiruv.

Muammo (2026-11-19): optimizator vaqt byudjeti bilan ishlaydi; serverda bir vaqtda bir nechta kroy ketsa (yoki noutbuk
qizib, chastota tushsa) har jarayon tezligi ~2 baravargacha kamayadi → shu soniyalarda kamroq variant ko'riladi va ba'zi
buyurtmalar +1 list bilan chiqadi (yolg'iz kesilganda — yo'q).

Yechim: `optimize()` ichida soat devor vaqti emas, «bajarilgan ish» bo'yicha yuradi: har ~0.1 s da kichik
mikro-o'lchov (≈0.05 ms) bilan joriy tezlik o'lchanadi va soat `tezlik / REF_SPEED` nisbatida sekinlashtiriladi
(nisbat [MIN_RATE, 1] oralig'ida — tez mashinada qidiruv qisqarmaydi, yuklamada kroy ko'pi bilan 1/MIN_RATE marta uzayadi).
`REF_SPEED` (`MEBELIX_REF_SPEED`) — shu kompyuterda kroy YOLG'IZ ishlaganda mikro-o'lchov tezligining medianasi
(kroy jarayonining o'zi keshni band qilgani uchun bo'sh holatdagidan past). `MEBELIX_VCLOCK=0` — o'chirish.
Soat faqat `scope()` ichida farq qiladi; tashqarida (`editor`, `cut_rest` muddatlari) — oddiy `time.monotonic()`.
"""
from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager

MIN_RATE = 0.5
PERIOD = 0.1                     # mikro-o'lchov oralig'i (devor vaqti, s)
# mikro-o'lchov/s: yolg'iz kroy paytidagi mediana (2026-11-19 — 15.2–15.6 ming)
REF_SPEED = float(os.environ.get("MEBELIX_REF_SPEED", "15000") or 0)
if os.environ.get("MEBELIX_VCLOCK", "1") == "0" or REF_SPEED <= 0:
    MIN_RATE = 1.0               # o'chirilgan: oddiy devor vaqti

_tl = threading.local()


def _probe() -> float:
    """Kichik sof-Python ish (lug'at, ro'yxat, arifmetika) — optimizator yuklamasiga o'xshash; tezlik = 1/vaqt."""
    t = time.perf_counter()
    x, d, a = 1, {}, []
    for i in range(400):
        x = (x * 31 + i) % 1000003
        d[x & 63] = i
        a.append(x)
    a.sort()
    dt = time.perf_counter() - t
    return 1.0 / dt if dt > 0 else 0.0


def _rate(st) -> float:
    sp = _probe()
    st.speed = sp if st.speed is None else 0.7 * st.speed + 0.3 * sp
    return min(1.0, max(MIN_RATE, st.speed / REF_SPEED))


def now() -> float:
    st = getattr(_tl, "st", None)
    w = time.monotonic()
    if st is None or MIN_RATE >= 1.0:
        return w
    dw = w - st.wall
    if dw >= PERIOD:
        st.virt += dw * st.rate
        st.wall = w
        st.rate = _rate(st)
        return st.virt
    return st.virt + dw * st.rate


class _State:
    __slots__ = ("wall", "virt", "rate", "speed", "depth")


@contextmanager
def scope():
    """Ichma-ich chaqiruvlar bitta soatni ishlatadi; tashqi `scope` dan chiqilganda soat devor vaqtiga qaytadi."""
    st = getattr(_tl, "st", None)
    if st is not None:
        st.depth += 1
        try:
            yield
        finally:
            st.depth -= 1
        return
    st = _State()
    st.wall = st.virt = time.monotonic()
    st.speed = None
    st.depth = 1
    st.rate = 1.0
    if MIN_RATE < 1.0:
        st.rate = _rate(st)
    _tl.st = st
    try:
        yield
    finally:
        _tl.st = None
