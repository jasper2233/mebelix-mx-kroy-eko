# -*- coding: utf-8 -*-
"""XNC frezalash chizmasi (2026-10-21): freza izi (asbob eni), boshlanish nuqtasi, skvoz kesim ajratadigan bo'lak (och rang).
«Подрезка на выходе» 2026-10-22 da foydalanuvchi qarori bilan olib tashlandi (onlayn tizimdagidek — stanok dasturiga qo'shimcha
kesim qo'shilmaydi)."""
import math
import re

from app.models import Operation, OpType, XncCommand as C, XNCParams
from app.services import xnc as X


def _xop(prog, dx=1500, dy=1400, dz=16):
    return Operation(type=OpType.XNC, name="stoleshnitsa", xnc=XNCParams(
        length=dx, width=dy, thickness=dz, by_part_size=False, program=prog))


# foydalanuvchi loyihasidagi stoleshnitsa: Mill4, (−30; 550) → (700; 550) → yoy (950; 800) → (950; 1430), skvoz, C=1
STOL = [C(cmd="MillStart", params={"X": -30, "Y": 550, "DP": "dz", "T": "Mill4", "D": 4, "C": 1}),
        C(cmd="MillLine", params={"X": 700, "Y": 550}),
        C(cmd="MillArcCenter", params={"X": 950, "Y": 800, "CX": 700, "CY": 800, "DIR": True}),
        C(cmd="MillLine", params={"X": 950, "Y": 1430})]


def test_machine_program_has_no_extra_precut():
    # yo'l detaldan chiqib tugasa ham stanok dasturida faqat dasturdagi yo'l: qo'shimcha teskari kesim yo'q
    ops = X.machine_program(_xop(STOL))["ops"]
    assert [o["kind"] for o in ops] == ["mill_start", "mill_line", "mill_arc", "mill_line"]
    assert (ops[0]["x"], ops[0]["y"]) == (-30, 550) and not any(o.get("precut") for o in ops)
    svg = X.xnc_drawing_svg(_xop(STOL), width_px=900)
    assert "xnc-precut" not in svg


def test_old_saved_precut_flag_is_ignored():
    # avval saqlangan loyihalardagi `exit_precut` maydoni o'qilganda xato bermaydi va hech narsaga ta'sir qilmaydi
    x = XNCParams.model_validate(dict(length=100, width=100, thickness=16, by_part_size=False, exit_precut=True))
    assert "exit_precut" not in x.model_dump()


def test_drawing_shows_band_start_and_cutoff():
    svg = X.xnc_drawing_svg(_xop(STOL), width_px=900)
    assert 'class="xnc-band"' in svg and 'class="xnc-mill-start"' in svg
    assert 'class="xnc-cutoff"' in svg
    # och bo'lak — korreksiya (o'ng) tomonidagi pastki-chap qism: (0;1400) burchagi kiradi, (1500;0) — yo'q
    d = svg.split('class="xnc-cutoff" d="')[1].split('"')[0]
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", d)]
    pts = list(zip(nums[::2], nums[1::2]))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    assert min(xs) == 0 and max(ys) == 1400 and max(xs) <= 952 and min(ys) >= 548


def test_not_through_mill_has_no_cutoff():
    prog = [dict(STOL[0].model_dump(), params={**STOL[0].params, "DP": 5})] + [c.model_dump() for c in STOL[1:]]
    svg = X.xnc_drawing_svg(_xop([C(**c) for c in prog]))
    assert 'class="xnc-cutoff"' not in svg and 'class="xnc-band"' in svg
    assert math.isfinite(1.0)
