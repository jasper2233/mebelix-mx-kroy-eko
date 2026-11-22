# -*- coding: utf-8 -*-
"""Xodim videosi 2026-11-22 («0008» taroq pazlari): onlayn chizmadagidek paz yuzada to'q polosa (eni W), yon ko'rinishlarda —
kesim (eni W, chuqurligi DP, yuza tomonidan). Avval MX pazni yuzada och chiziq qilib chizar, yon ko'rinishda ko'rsatmasdi."""
import re

from app.models import Operation, OpType, XncCommand as C, XNCParams
from app.services import xnc as X


def _svg(prog, dz=16):
    op = Operation(type=OpType.XNC, name="op", xnc=XNCParams(length=600, width=300, thickness=dz, by_part_size=False, program=prog))
    return X.xnc_drawing_svg(op, None, 1200)


def _secs(svg):
    return [tuple(float(v) for v in m.groups())
            for m in re.finditer(r'<rect x="(-?[\d.e-]+)" y="(-?[\d.e-]+)" width="([\d.e-]+)" height="([\d.e-]+)" class="xnc-gsec"', svg)]


def test_vertical_groove_section_top_and_bottom_with_depth():
    svg = _svg([C(cmd="Groove", params={"X1": "500", "Y1": "0", "X2": "500", "Y2": "300", "DP": "14.8", "W": "4"})])
    g = re.search(r'<g class="xnc-groove".*?</g>', svg, re.S).group(0)
    assert 'class="xnc-gw"' in g and X.DRAW_GROOVE in g                 # yuzada to'q polosa
    secs = _secs(g)
    assert len(secs) == 2
    for x, y, w, h in secs:
        assert abs(x + w / 2 - 500) < 1e-6 and abs(w - 4) < 1e-6
        assert abs(h - 14.8) < 1e-6                                     # chuqurlik — haqiqiy (qalinlik 16 dan)
    assert min(s[1] for s in secs) < 0 < max(s[1] for s in secs)        # yuqori va pastki yon ko'rinish


def test_horizontal_groove_section_left_right_and_shallow_depth():
    svg = _svg([C(cmd="Groove", params={"X1": "0", "Y1": "100", "X2": "600", "Y2": "100", "DP": "6", "W": "8"})])
    secs = _secs(svg)
    assert len(secs) == 2
    for x, y, w, h in secs:
        assert abs(w - 6) < 1e-6 and abs(h - 8) < 1e-6
    assert min(s[0] for s in secs) < 0 < max(s[0] for s in secs)
