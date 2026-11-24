"""Kroy kartasi yozuvlari bir-birining ustiga tushmaydi (xodim skrini 2026-11-24: tor tik detal 35×340 — en ustuni va
detal raqami bir joyda). Onlayn tizimda bunday detallarda yozuvlar ustma-ust; MX — `services/map_labels.py`."""
import itertools
import re

import pytest

from app.models import CutMap, Placement
from app.services import render
from app.services.map_labels import GAP_X, GAP_Y, label_box, part_label_layout

SIZES = [(35, 340), (30, 340), (45, 340), (60, 340), (80, 340), (340, 35), (390, 60), (390, 109), (40, 40), (60, 60),
         (100, 80), (770, 547), (2274, 382), (1450, 30), (300, 1450), (129, 390)]


def _check(items, x, y, l, w, fs):
    boxes = [label_box(i, fs) for i in items]
    for b in boxes:
        assert b[0] >= x - 1e-6 and b[2] <= x + l + 1e-6 and b[1] >= y - 1e-6 and b[3] <= y + w + 1e-6, (l, w, items)
    for (a, ia), (b, ib) in itertools.combinations(zip(boxes, items), 2):
        apart = a[2] + GAP_X * fs * 0.99 <= b[0] or b[2] + GAP_X * fs * 0.99 <= a[0] or \
            a[3] + GAP_Y * fs * 0.99 <= b[1] or b[3] + GAP_Y * fs * 0.99 <= a[1]
        assert apart, (l, w, ia, ib)


@pytest.mark.parametrize("fs", [16.0, 25.0, 40.0])
@pytest.mark.parametrize("l,w", SIZES)
def test_labels_never_overlap_and_stay_inside(l, w, fs):
    items = part_label_layout(100, 200, l, w, fs, num="44", len_s=str(l), wid_s=str(w), name="bok", min_fs=fs * 0.35)
    _check(items, 100, 200, l, w, fs)


def test_narrow_tall_part_keeps_number_and_dims_apart():
    """Xodim skrinidagi holat: 35×340, shrift ≈ 30 mm — raqam ham, o'lchamlar ham, ustma-ust emas."""
    items = part_label_layout(0, 0, 35, 340, 12.0, num="44", len_s="35", wid_s="340", min_fs=4)
    kinds = {i["kind"] for i in items}
    assert "num" in kinds
    _check(items, 0, 0, 35, 340, 12.0)


def test_ordinary_part_keeps_old_places():
    """Katta detal: raqam markazda, uzunlik pastki-chapda, en o'ng tomonda ustma-ust (avvalgi ko'rinish)."""
    items = {i["kind"]: i for i in part_label_layout(0, 0, 770, 547, 20.0, num="49", len_s="770", wid_s="547")}
    assert items["num"]["mode"] == "h" and items["num"]["x"] == 385
    assert items["len"]["mode"] == "h" and items["len"]["anchor"] == "start"
    assert items["wid"]["mode"] == "s" and items["wid"]["anchor"] == "end"


def test_print_map_every_narrow_part_has_number():
    pls = [Placement(part_id=f"p{i}", part_uid=i + 1, x=10 + i * 40, y=10, length=35, width=340, rotated=False)
           for i in range(6)]
    m = CutMap(index=0, sheet_id="s", sheet_length=2750, sheet_width=1830, placements=pls)
    svg = render.map_svg(m, 900, None, None, None, "number")
    nums = re.findall(r'class="pn"[^>]*>(.*?)</text>', svg)
    assert len(nums) == 6
