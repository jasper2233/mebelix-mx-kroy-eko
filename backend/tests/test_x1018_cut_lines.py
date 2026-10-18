"""Karta: arra kesish chiziqlari ota hudud bo'ylab to'liq chiziladi (chiqindi ustidan ham), detal chetida to'xtamaydi."""
from app.services.render import cut_lines


def _tree():
    # list 1000×500, torsovka 10; ildiz — X bo'yicha 2 polosa; 1-polosa Y bo'yicha: detal 300 + chiqindi (oxiriga yetmaydi)
    strip1 = {"k": "C", "a": "y", "x": 10, "y": 10, "l": 400, "w": 480,
              "c": [{"k": "P", "x": 10, "y": 10, "l": 400, "w": 300}]}
    strip2 = {"k": "C", "a": "y", "x": 414, "y": 10, "l": 576, "w": 480,
              "c": [{"k": "P", "x": 414, "y": 10, "l": 576, "w": 200}, {"k": "P", "x": 414, "y": 214, "l": 576, "w": 276}]}
    return [{"k": "C", "a": "x", "x": 10, "y": 10, "l": 980, "w": 480, "c": [strip1, strip2]}]


def test_cut_lines_span_parent_and_cross_waste():
    ls = cut_lines(_tree(), 1000, 500, kerf2=2)
    # torsovka — butun list bo'ylab
    assert (10, 0, 10, 500) in ls and (990, 0, 990, 500) in ls
    # polosalar orasidagi vertikal kesish — ildiz bo'yi bo'ylab, propil o'rtasida (410 + 2)
    assert (412, 10, 412, 490) in ls
    # 1-polosada detal ostidagi kesish — chiqindini ajratadi va polosa eni bo'ylab to'liq (detal chetida to'xtamaydi)
    assert (10, 312, 410, 312) in ls
    # 2-polosa: oxirgi detal ota oxirigacha yetadi — undan keyin chiziq yo'q
    assert not any(y1 == y2 and y1 > 490 for x1, y1, x2, y2 in ls)


def test_cut_lines_in_report_svg():
    from app.models import CutMap
    m = CutMap(index=1, sheet_id="s", sheet_length=1000, sheet_width=500, strips=_tree())
    from app.services.render import map_svg
    svg = map_svg(m)
    assert svg.count('class="cut"') == len(cut_lines(_tree(), 1000, 500))
