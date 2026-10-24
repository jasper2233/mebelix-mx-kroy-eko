"""XNC shablonlar oynasi (onlayn «Открыть шаблоны обработки», 2026-10-23): standart papkalar («Типовые фрезеровки» 14,
«Фасады МДФ» 9 — bizning parametrli dasturlar), har biri xatosiz hisoblanadi va chiqindi bo'lagi to'g'ri tomonda; foydalanuvchi
papkalari (qo'shish / nomini o'zgartirish / bo'sh papkani o'chirish), shablonni ko'chirish, eskiz SVG, «Открыть» — oxiriga qo'shish."""
import re

import pytest

from app.models import Operation, OpType, XNCParams
from app.services import xnc as X
from app.services import xnc_templates as T
from app.services.xnc_templates_std import STD

RU = lambda ru, uz: ru  # noqa: E731


@pytest.mark.parametrize("key", list(STD))
def test_std_template_computes_without_errors(key):
    ru, _uz, _fold, (dx, dy), build = STD[key]
    for size in ((dx, dy), (dx * 2, dy * 1.5)):                    # boshqa o'lchamda ham (parametrli)
        x = XNCParams(length=size[0], width=size[1], thickness=16, by_part_size=False, program=build(RU))
        st = X.xnc_stats(x)
        assert st["errors"] == 0 and st["warnings"] == [], (key, size, st["warnings"])
        assert st["mill_m"] > 0
        svg = X.xnc_drawing_svg(Operation(type=OpType.XNC, name=ru, xnc=x), None, 300, height_px=300)
        assert "xnc-error" not in svg


def test_edge_cut_waste_is_small_piece():
    """Chetni shakllantiruvchi shablonlarda ajratilgan (och) bo'lak — kichik bo'lak, butun detal emas."""
    for key in ("m_radius1", "m_notch", "m_notch_r", "m_outer2", "m_step", "m_step_f", "m_step_r", "m_corner_ir"):
        ru, _uz, _f, (dx, dy), build = STD[key]
        x = XNCParams(length=dx, width=dy, thickness=16, by_part_size=False, program=build(RU))
        svg = X.xnc_drawing_svg(Operation(type=OpType.XNC, name=ru, xnc=x), None, 600, height_px=400)
        polys = re.findall(r'class="xnc-cutoff" d="([^"]+)"', svg)
        for d in polys:
            nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
            xs, ys = nums[0::2], nums[1::2]
            area = abs(sum(xs[i] * ys[(i + 1) % len(xs)] - xs[(i + 1) % len(xs)] * ys[i] for i in range(len(xs)))) / 2
            assert area < dx * dy * 0.5, (key, area)


def test_library_lists_folders():
    items = T.library_list("ru")
    by_folder: dict[str, int] = {}
    for it in items:
        by_folder[it["folder"]] = by_folder.get(it["folder"], 0) + 1
    assert by_folder["Типовые фрезеровки"] == 14 and by_folder["Фасады МДФ"] == 9
    assert by_folder["Образцы MebeliX"] == 7


def test_folders_move_rename_delete_and_thumb(client):
    r = client.get("/api/xnc/template-folders").json()
    assert "Типовые фрезеровки" in r["builtin"] and r["user"] == []
    assert client.post("/api/xnc/template-folders", json={"path": "Кухни"}).status_code == 200
    t = client.post("/api/xnc/templates", json={"name": "Мой паз", "program": [
        {"cmd": "Groove", "params": {"X1": 0, "Y1": 50, "X2": "dx", "Y2": 50, "DP": 8, "W": 4}, "comment": "", "children": []}]}).json()
    assert t["folder"] == ""
    t = client.patch(f"/api/xnc/templates/{t['id']}", json={"folder": "Кухни"}).json()
    assert t["folder"] == "Кухни"
    assert client.delete("/api/xnc/template-folders", params={"path": "Кухни"}).status_code == 400   # ichida shablon bor
    r = client.patch("/api/xnc/template-folders", json={"path": "Кухни", "new_path": "Кухни 2026"}).json()
    assert r["user"] == ["Кухни 2026"]
    lst = {x["id"]: x for x in client.get("/api/xnc/templates").json()}
    assert lst[t["id"]]["folder"] == "Кухни 2026"
    assert client.patch(f"/api/xnc/templates/{t['id']}", json={"folder": "", "name": "Паз 2"}).json()["name"] == "Паз 2"
    assert client.delete("/api/xnc/template-folders", params={"path": "Кухни 2026"}).status_code == 200
    assert client.patch("/api/xnc/templates/lib:f_arch", json={"folder": "x"}).status_code == 400  # o'rnatilgan — faqat o'qish
    svg = client.get("/api/xnc/templates/lib:f_arch/thumb.svg")
    assert svg.status_code == 200 and svg.headers["content-type"].startswith("image/svg") and "<svg" in svg.text
    assert client.get(f"/api/xnc/templates/{t['id']}/thumb.svg").status_code == 200
