# «Ish soati» (2026-11-19): optimize() ichida soat yuklama ostida sekinlashadi, tashqarida — oddiy monotonic.
import time

from app.services import vclock


def test_outside_scope_is_wall_clock():
    a = time.monotonic()
    b = vclock.now()
    assert abs(b - a) < 0.05


def test_scope_never_runs_ahead_and_resets(monkeypatch):
    monkeypatch.setattr(vclock, "MIN_RATE", 0.5)
    monkeypatch.setattr(vclock, "REF_SPEED", 1e12)          # «sekin mashina» — nisbat MIN_RATE gacha tushadi
    with vclock.scope():
        w0, v0 = time.monotonic(), vclock.now()
        t = time.monotonic()
        while time.monotonic() - t < 0.35:
            vclock.now()
        dw, dv = time.monotonic() - w0, vclock.now() - v0
        assert dv <= dw + 1e-6
        assert dv >= dw * 0.45
        assert dv < dw * 0.8
        with vclock.scope():                                 # ichma-ich — o'sha soat
            assert vclock.now() >= v0
    assert abs(vclock.now() - time.monotonic()) < 0.05
