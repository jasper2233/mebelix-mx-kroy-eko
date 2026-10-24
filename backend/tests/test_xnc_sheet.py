"""Detal «XNC Редактор» oynasi «Чертеж» — onlayn varaq tartibida (2026-10-22, jonli solishtirildi): ramkali oq varaq, raqamlangan
teshiklar, umumiy va ordinata o'lchamlari (qirraga yaqin X — pastda), teshiklar jadvali (Ø / DP guruhlari), «Лицевая сторона»,
«Кромкооблицовка», shtamp."""
import re

from app.models import Operation, OpType, XncCommand as C, XNCParams
from app.services import xnc as X


def _drill(x, y, d=8, dp=12):
    return {"cmd": "DrillFront", "params": {"X": x, "Y": y, "DP": dp, "D": d, "T": f"Bore{d}"}, "comment": "", "enabled": True,
            "children": []}


def test_xnc_sheet(client, kravat):
    pid, cs, _el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = next(o for o in p["operations"] if o["id"] == cs)["parts"][0]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}/xnc").json()
    xop = p["operations"][-1]["id"]
    prog = [_drill(50, 37), _drill(200, 37, 35, 13)]
    assert client.patch(f"/api/projects/{pid}/operations/{xop}", json={"xnc": {"program": prog}}).status_code == 200
    r = client.get(f"/api/projects/{pid}/operations/{xop}/xnc-sheet")
    assert r.status_code == 200 and "<svg" in r.text
    t = r.text
    assert "data-testid='xnc-sheet'" in t and "xnc-sheet-dims" in t       # varaq va o'lchamlar
    assert "Ø=8" in t and "DP=12" in t and "Ø=35" in t and "DP=13" in t   # teshiklar jadvali guruhlari
    assert ">50<" in t and ">37<" in t                                     # X / Y qiymatlari
    assert 'class="xnc-num"' in t                                          # teshik raqamlari
    for label in ("Лицевая сторона", "Кромкооблицовка", "Рм. заготовки", "Рм. детали", "По размеру", "Количество", "Код"):
        assert label in t, label
    assert "#FFA500" not in t                                              # detal oq (to'q sariq emas)
    assert client.get(f"/api/projects/{pid}/operations/{cs}/xnc-sheet").status_code == 400


def _xop(prog, dx=1950, dy=600):
    return Operation(type=OpType.XNC, name="tom", code="T1", xnc=XNCParams(length=dx, width=dy, thickness=16, by_part_size=False,
                                                                         program=prog))


def test_sheet_dims_like_online_varaq():
    # onlayn «5000 kupe / tom»: 975 tepada, chetdagi 8 va 1942 — pastda; Y: 70, 430, 530 o'ngda
    prog = [C(cmd="DrillFront", params={"X": 975, "Y": 70, "DP": 19, "D": 7, "T": "BoreTh7"}),
            C(cmd="DrillFront", params={"X": 975, "Y": 430, "DP": 19, "D": 7, "T": "BoreTh7"}),
            C(cmd="DrillFront", params={"X": 8, "Y": 70, "DP": 19, "D": 8, "T": "BoreTh8"}),
            C(cmd="DrillFront", params={"X": 8, "Y": 530, "DP": 19, "D": 8, "T": "BoreTh8"}),
            C(cmd="DrillFront", params={"X": 1942, "Y": 70, "DP": 19, "D": 8, "T": "BoreTh8"}),
            C(cmd="DrillFront", params={"X": 1942, "Y": 530, "DP": 19, "D": 8, "T": "BoreTh8"})]
    svg = X.xnc_drawing_svg(_xop(prog), None, 1100, height_px=520, sheet=True)
    dims = svg.split('class="xnc-sheet-dims"')[1]
    texts = re.findall(r">([\d.]+)</text>", dims)
    for v in ("1950", "600", "975", "8", "1942", "70", "430", "530"):
        assert v in texts, v
    assert texts.count("975") == 1 and texts.count("70") == 1                # noyob qiymatlar bir marta
    # pastki / yuqori asos: «8» va «1942» yozuvlari detaldan pastda (y > 600), «975» — tepada (y < 0)
    def y_of(v):
        m = re.search(r'<text x="[^"]+" y="([-\d.e]+)"[^>]*>' + re.escape(v) + "</text>", dims)
        return float(m.group(1))
    assert y_of("8") > 600 and y_of("1942") > 600 and y_of("975") < 0
    assert [int(n) for n in re.findall(r'class="xnc-num"[^>]*>(\d+)<', svg)] == [1, 2, 3, 4, 5, 6]
    assert "xnc-origin" not in svg and "xnc-face" not in svg                  # varaqda koordinata o'qlari / lits belgisi yo'q


def test_regular_drawing_unchanged_by_sheet_mode():
    prog = [C(cmd="DrillFront", params={"X": 100, "Y": 22, "DP": 13, "D": 35, "T": "Bore35"})]
    svg = X.xnc_drawing_svg(_xop(prog, 650, 330), None, 560)
    assert "#FFA500" in svg and "xnc-origin" in svg and "xnc-sheet-dims" not in svg and "xnc-num" not in svg
