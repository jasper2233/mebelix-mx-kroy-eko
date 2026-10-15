"""W18 / W3 «Qilinmadi» bandlari: Excel import — «Простые операции» (O), «Материалы» (katalog → CS/EL/SP/CL), qo'shimcha ustun
guruhlari (SP / GR / XNC shablon), погонаж («Ширина» bo'sh → CL). Fayllar sintetik `.xlsx` (openpyxl); mijoz ma'lumoti yo'q."""
from __future__ import annotations

import io
import json

import pytest
from openpyxl import Workbook

UZ = {"Accept-Language": "uz"}


def _xlsx(sheets) -> bytes:
    wb = Workbook()
    first = True
    if isinstance(sheets, list):
        sheets = {"Лист1": sheets}
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        ws.title = name
        first = False
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _project(client, name="W18 excel"):
    p = client.post("/api/projects", json={"name": name}).json()
    return p["id"]


def _imp(client, pid, data, cfg, name="d.xlsx", dry_run=False):
    return client.post(f"/api/projects/{pid}/import/excel", files={"file": (name, data)},
                       data={"config": json.dumps(cfg), "dry_run": "true" if dry_run else "false"})


def _ops(p, typ):
    return [o for o in p["operations"] if o["type"] == typ]


def _get(client, pid):
    return client.get(f"/api/projects/{pid}").json()


# ───────────────────────── «Простые операции» (O) ─────────────────────────
SIMPLE_ROWS = [["Код", "Наименование", "Ед.И", "Кол", "Цена", "Операция", "Изделие"],
               ["R-1", "Ручка", "шт", 4, 15000, "Фурнитура", "Шкаф"],
               ["R-2", "Петля", "шт", "6 шт", "1 200,5", "Фурнитура", "Шкаф"],
               ["P-1", "Плёнка", "м", 2.5, 8000, "Упаковка", ""],
               ["", "", "", "", "", "Упаковка", ""],                      # butunlay bo'sh (faqat operatsiya nomi) — «bo'sh qator» deb tashlanadi
               ["X", "", "", "abc", 5, "Упаковка", ""]]                   # yaroqsiz soni
SIMPLE_MAP = {"code": "A", "name": "B", "unit": "C", "qty": "D", "price": "E", "operation": "F", "product": "G"}


def test_simple_tab_creates_o_operations_grouped_by_operation_column(client):
    pid = _project(client)
    pr = client.post(f"/api/projects/{pid}/products", json={"name": "Шкаф", "qty": 3}).json()["products"][-1]["id"]
    r = _imp(client, pid, _xlsx(SIMPLE_ROWS), {"simple": {"enabled": True, "start_row": 2, "map": SIMPLE_MAP}},
             dry_run=False)
    assert r.status_code == 200, r.text
    d = r.json()
    o_ops = _ops(d, "O")
    assert [o["name"] for o in o_ops] == ["Фурнитура", "Упаковка"]
    assert d["imported"] == 0 and d["simple_rows"] == 3 and [x["rows"] for x in d["created_o"]] == [2, 1]
    furn = o_ops[0]["o"]
    assert furn["owner_product_id"] == pr                                       # «Изделие» ustuni → egasi mahsulot
    m = {x["code"]: x for x in furn["materials"]}
    assert (m["R-1"]["qty"], m["R-1"]["price"], m["R-1"]["unit"]) == (4, 15000, "шт")
    assert (m["R-2"]["qty"], m["R-2"]["price"], m["R-2"]["name"]) == (6, 1200.5, "Петля")      # «6 шт», «1 200,5» o'qiladi
    pack = o_ops[1]["o"]
    assert pack["owner_product_id"] is None and [x["code"] for x in pack["materials"]] == ["P-1"] and pack["materials"][0]["qty"] == 2.5
    # narx hisobi O mantig'i bilan: mahsulot soni 3 → (4×15000 + 6×1200.5) × 3
    assert o_ops[0]["cost_material"] == round((4 * 15000 + 6 * 1200.5) * 3, 2)
    # yaroqsiz qatorlar jim tashlanmaydi: sabab bilan
    sk = {s["row"]: s for s in d["skipped"]}
    assert set(sk) == {5, 6} and all(s["tab"] == "simple" for s in sk.values())
    assert "abc" in sk[6]["reason"]


def test_simple_tab_single_operation_default_name_header_and_target_append(client):
    pid = _project(client)
    rows = [["Код", "Наименование", "Ед.И", "Кол", "Цена"], ["A1", "Шуруп", "шт", 100, 50], ["A2", "Клей", "кг", 2, 9000]]
    cfg = {"simple": {"enabled": True, "start_row": 1, "map": {"code": "A", "name": "B", "unit": "C", "qty": "D", "price": "E"},
                      "op_name": "Мой набор"}}
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    op = _ops(d, "O")[0]
    assert op["name"] == "Мой набор" and len(op["o"]["materials"]) == 2                  # sarlavha qatori (start_row=1) ogohlantirish bilan o'tkazildi
    assert any("заголов" in w.lower() or "sarlavha" in w.lower() for w in d["warnings"])
    # mavjud O ga qo'shish
    cfg2 = {"simple": {"enabled": True, "start_row": 2, "map": cfg["simple"]["map"], "target_op": op["id"]}}
    d2 = _imp(client, pid, _xlsx(rows), cfg2).json()
    assert len(_ops(d2, "O")) == 1 and len(_ops(d2, "O")[0]["o"]["materials"]) == 4 and d2["created_o"] == []
    # nom berilmasa — standart nom
    d3 = _imp(client, pid, _xlsx(rows[1:]), {"simple": {"enabled": True, "start_row": 1, "map": cfg["simple"]["map"]}}, ).json()
    assert _ops(d3, "O")[-1]["name"] == "Комплектация"
    d4 = _imp(client, pid, _xlsx(rows[1:]), {"simple": {"enabled": True, "start_row": 1, "map": cfg["simple"]["map"]}},
              name="x.xlsx")
    assert d4.status_code == 200
    # nom bo'yicha uz tilida
    u = client.post(f"/api/projects/{pid}/import/excel", files={"file": ("d.xlsx", _xlsx(rows[1:]))},
                    data={"config": json.dumps({"simple": {"enabled": True, "start_row": 1, "map": cfg["simple"]["map"]}})}, headers=UZ).json()
    assert _ops(u, "O")[-1]["name"] == "Komplektatsiya"


def test_simple_tab_validation_errors(client):
    pid = _project(client)
    rows = [["A", "b"]]
    # na kod, na nom ustuni
    r = _imp(client, pid, _xlsx(rows), {"simple": {"enabled": True, "map": {"qty": "D"}}})
    assert r.status_code == 400 and "Код" in r.json()["detail"]
    # noma'lum maydon / ustun
    assert _imp(client, pid, _xlsx(rows), {"simple": {"enabled": True, "map": {"zzz": "A"}}}).status_code == 400
    assert _imp(client, pid, _xlsx(rows), {"simple": {"enabled": True, "map": {"code": "1"}}}).status_code == 400
    # target_op — O emas / yo'q
    el = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "k"}).json()["operations"][-1]["id"]
    assert _imp(client, pid, _xlsx(rows), {"simple": {"enabled": True, "map": {"code": "A"}, "target_op": el}}).status_code == 400
    assert _imp(client, pid, _xlsx(rows), {"simple": {"enabled": True, "map": {"code": "A"}, "target_op": "yo'q"}}).status_code == 400
    # hech narsa yoqilmagan
    r = _imp(client, pid, _xlsx(rows), {"parts": {"enabled": False}, "simple": {"enabled": False}})
    assert r.status_code == 400
    # xato hech narsani o'zgartirmagan
    assert _ops(_get(client, pid), "O") == []


def test_simple_tab_unknown_product_warns_and_dry_run_changes_nothing(client):
    pid = _project(client)
    rows = [["R", "Ручка", "шт", 1, 10, "Оп", "Yo'q mahsulot"]]
    cfg = {"simple": {"enabled": True, "start_row": 1, "map": SIMPLE_MAP}}
    d = _imp(client, pid, _xlsx(rows), cfg, dry_run=True).json()
    assert d["dry_run"] is True and d["simple_rows"] == 1 and any("Yo'q mahsulot" in w for w in d["warnings"])
    assert _ops(_get(client, pid), "O") == []
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    assert _ops(d, "O")[0]["o"]["owner_product_id"] is None


# ───────────────────────── «Материалы» ─────────────────────────
@pytest.fixture(scope="module")
def mat_catalog(client):
    """Katalog: har tur uchun bittadan material (id/kod prefiksi `w18m-` — boshqa testlar bilan to'qnashmaydi)."""
    rows = [["id", "parent_id", "isfolder", "code", "name", "unit", "price", "thickness", "length", "width", "kind"],
            ["w18m-f", None, 1, "", "W18 папка", "", None, None, None, None, ""],
            ["w18m-1", "w18m-f", 0, "W18S1", "ЛДСП W18 18мм", "м2", 120000, 18, 2800, 2070, "sheet"],
            ["w18m-2", "w18m-f", 0, "W18E1", "ПВХ W18 2мм", "м", 1500, 2, None, 22, "edge"],
            ["w18m-3", "w18m-f", 0, "W18P1", "Лак W18", "м2", 30000, None, None, None, "surface"],
            ["w18m-4", "w18m-f", 0, "W18L1", "Плинтус W18", "м", 9000, 22, 3000, 60, "linear"]]
    cmap = {"id": "A", "parent_id": "B", "isfolder": "C", "code": "D", "name": "E", "unit": "F", "price": "G",
            "thickness": "H", "length": "I", "width": "J", "kind": "K"}
    r = client.post("/api/catalog/import", files={"file": ("g.xlsx", _xlsx(rows))},
                    data={"col_map": json.dumps(cmap), "start_row": 2, "roots": "{}"})
    assert r.status_code == 200, r.text
    return rows


MAT_MAP = {"code": "A", "name": "B", "kind": "C", "thickness": "D", "length": "E", "width": "F", "price": "G"}
MAT_CFG = {"materials": {"enabled": True, "start_row": 2, "map": MAT_MAP}}


def test_materials_tab_creates_cs_el_sp_cl_from_catalog_by_code_or_name(client, mat_catalog):
    pid = _project(client)
    rows = [["Код", "Наименование", "Тип", "Т", "Д", "Ш", "Цена"],
            ["W18S1", "", "", None, None, None, None],                       # kod bo'yicha → CS (qalinlik/list/narx katalogdan)
            ["", "ПВХ W18 2мм", "", None, None, None, None],                 # nom bo'yicha (katta-kichik harf farqsiz) → EL
            ["w18p1", "", None, None, None, None, None],                      # kod (kichik harf) → SP
            ["W18L1", "", "", None, None, None, None],                       # погонаж → CL
            ["W18S1", "", "", None, None, None, None]]                       # takror — bir marta
    d = _imp(client, pid, _xlsx({"Материалы": rows}), MAT_CFG).json()
    assert d["materials_added"] == 4 and d["materials_existing"] == 0 and d["skipped"] == [], d
    cs, el, sp, cl = (_ops(d, t)[0] for t in ("CS", "EL", "SP", "CL"))
    assert cs["name"] == "ЛДСП W18 18мм" and cs["code"] == "W18S1"
    assert cs["cs_material"]["thickness"] == 18 and cs["cs_material"]["price"] == 120000
    assert (cs["sheets"][0]["length"], cs["sheets"][0]["width"]) == (2800, 2070)
    assert el["code"] == "W18E1" and el["el"]["thickness"] == 2 and el["el"]["width"] == 22 and el["el"]["price"] == 1500
    assert el["el"]["symbol"] and el["el"]["color"]
    assert sp["code"] == "W18P1" and sp["sp"]["price"] == 30000
    assert cl["code"] == "W18L1" and cl["cl"]["width"] == 60 and cl["cl"]["thickness"] == 22 and cl["cl"]["price"] == 9000
    assert {x["type"] for x in d["created_ops"]} == {"CS", "SP", "CL"} and len(d["created_edges"]) == 1
    types = [o["type"] for o in d["operations"]]
    assert types.index("CS") < types.index("EL")                            # CS lar kromkadan oldin
    # qayta import: allaqachon bor — yaratilmaydi
    d2 = _imp(client, pid, _xlsx({"Материалы": rows}), MAT_CFG).json()
    assert d2["materials_added"] == 0 and d2["materials_existing"] == 4 and len(d2["operations"]) == len(d["operations"])


def test_materials_tab_missing_in_catalog_uses_row_values_or_is_skipped(client, mat_catalog):
    pid = _project(client)
    rows = [["Код", "Наименование", "Тип", "Т", "Д", "Ш", "Цена"],
            ["NEW1", "Новый МДФ", "лист", 19, 2440, 1220, "95 000"],
            ["", "Кромка новая", "кромка", 1, None, 28, 700],
            ["", "Без типа", "", 10, None, None, 1],                          # tur yo'q → default_kind (sheet)
            ["", "Странный", "ттт", None, None, None, None],                  # tur tanilmadi
            ["", "", "", None, None, None, None],                             # butunlay bo'sh qator
            ["NEW2", "Плохая толщина", "", "abc", None, None, None]]
    d = _imp(client, pid, _xlsx(rows), MAT_CFG).json()
    cs = {o["name"]: o for o in _ops(d, "CS")}
    assert set(cs) == {"Новый МДФ", "Без типа"}
    mdf = cs["Новый МДФ"]
    assert mdf["code"] == "NEW1" and mdf["cs_material"]["thickness"] == 19 and mdf["cs_material"]["price"] == 95000
    assert (mdf["sheets"][0]["length"], mdf["sheets"][0]["width"]) == (2440, 1220)
    el = _ops(d, "EL")[0]
    assert el["name"] == "Кромка новая" and el["el"]["thickness"] == 1 and el["el"]["width"] == 28 and el["el"]["price"] == 700
    reasons = {s["row"]: s["reason"] for s in d["skipped"]}
    assert set(reasons) == {5, 7} and all(s["tab"] == "materials" for s in d["skipped"])
    assert "ттт" in reasons[5] and "abc" in reasons[7]
    assert sum("нет в каталоге" in w for w in d["warnings"]) == 3          # 3 ta qator katalogda yo'q → ogohlantirish
    # create_missing=false: katalogda yo'q qatorlar tashlanadi
    pid2 = _project(client)
    cfg = {"materials": {"enabled": True, "start_row": 2, "map": MAT_MAP, "create_missing": False}}
    d2 = _imp(client, pid2, _xlsx(rows[:2] + [["W18S1", "", "", None, None, None, None]]), cfg).json()
    assert [o["code"] for o in _ops(d2, "CS")] == ["W18S1"]
    assert d2["skipped"][0]["row"] == 2 and "каталог" in d2["skipped"][0]["reason"]
    # default_kind = edge
    pid3 = _project(client)
    cfg = {"materials": {"enabled": True, "start_row": 2, "map": {"name": "B"}, "default_kind": "edge"}}
    d3 = _imp(client, pid3, _xlsx(rows[:1] + [["", "Нет такой"]]), cfg).json()
    assert [o["name"] for o in _ops(d3, "EL")] == ["Нет такой"] and _ops(d3, "CS") == []


def test_materials_then_parts_use_created_operations_and_reuse_existing_edge(client, mat_catalog):
    """«Материалы» va «Детали» bir importda: detalning material ustuni — shu importda katalogdan yaratilgan CS ni topadi."""
    pid = _project(client)
    wb = {"Материалы": [["Код"], ["W18S1"], ["W18E1"]],
          "Детали": [["Мат", "Длина", "Ширина", "Кол", "ОВ"], ["ЛДСП W18 18мм", 700, 500, 2, "ПВХ W18 2мм"]]}
    cfg = {"materials": {"enabled": True, "sheet_name": "Материалы", "start_row": 2, "map": {"code": "A"}},
           "parts": {"enabled": True, "sheet_name": "Детали", "start_row": 2,
                     "map": {"material": "A", "length": "B", "width": "C", "qty": "D", "edge_top": "E"}}}
    d = _imp(client, pid, _xlsx(wb), cfg).json()
    assert d["imported"] == 1 and d["materials_added"] == 2
    assert len(_ops(d, "CS")) == 1 and len(_ops(d, "EL")) == 1                   # ikkinchi CS / EL yaratilmadi
    cs, el = _ops(d, "CS")[0], _ops(d, "EL")[0]
    assert cs["code"] == "W18S1" and cs["parts"][0]["edge_top"]["op_id"] == el["id"]


def test_materials_tab_validation(client, mat_catalog):
    pid = _project(client)
    assert _imp(client, pid, _xlsx([["a"]]), {"materials": {"enabled": True, "map": {"price": "A"}}}).status_code == 400
    assert _imp(client, pid, _xlsx([["a"]]), {"materials": {"enabled": True, "map": {"name": "A"}, "default_kind": "bolt"}}).status_code == 400
    assert _imp(client, pid, _xlsx([["a"]]), {"materials": {"enabled": True, "map": {"foo": "A"}}}).status_code == 400


# ───────────────────────── (SP) / (GR) / (XNC) ustun guruhlari ─────────────────────────
@pytest.fixture()
def xnc_template(client):
    """Foydalanuvchi XNC shabloni («Teshik W18») — Excel ustunidagi kod shu nom bilan topiladi."""
    prog = [{"cmd": "DrillFront", "params": {"X": 50, "Y": 50, "D": 8, "DP": 12}}]
    r = client.post("/api/xnc/templates", json={"name": "Teshik W18", "program": prog}, params={"upsert": "true"})
    assert r.status_code == 200, r.text
    yield r.json()["id"]
    client.delete(f"/api/xnc/templates/{r.json()['id']}")


EXTRA_HEAD = ["Мат", "Длина", "Ширина", "Кол", "Название", "Код", "SP лиц", "SP обр", "ГР свер", "ГР слев", "XNC1", "XNC2"]
EXTRA_MAP = {"material": "A", "length": "B", "width": "C", "qty": "D", "name": "E", "code": "F", "sp_front": "G",
             "sp_back": "H", "gr_top": "I", "gr_left": "J", "xnc1": "K", "xnc2": "L"}


def test_extra_column_groups_link_sp_gr_xnc_to_parts(client, xnc_template):
    pid = _project(client)
    rows = [EXTRA_HEAD,
            ["ЛДСП", 700, 500, 2, "Бок", "B1", "Лак", "Морилка", "Паз 1", "", "Teshik W18", "pocket_rect"],
            ["ЛДСП", 600, 400, 1, "Полка", "P1", "лак", "", "-", "паз 1", "teshik w18", ""]]
    cfg = {"parts": {"start_row": 2, "map": EXTRA_MAP}}
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    assert d["imported"] == 2 and d["linked"]["sp"] == 3 and d["linked"]["gr"] == 2 and d["linked"]["xnc"] == 3
    sps = {o["name"]: o for o in _ops(d, "SP")}
    assert set(sps) == {"Лак", "Морилка"}                                          # «лак» — katta-kichik harfsiz o'sha operatsiya
    grs = _ops(d, "GR")
    assert [o["name"] for o in grs] == ["Паз 1"]
    cs = _ops(d, "CS")[0]
    a, b = cs["parts"]
    assert a["surface_face_op"] == sps["Лак"]["id"] and a["surface_back_op"] == sps["Морилка"]["id"]
    assert b["surface_face_op"] == sps["Лак"]["id"] and b["surface_back_op"] is None
    assert a["groove_top"]["op_id"] == grs[0]["id"] and a["groove_top"]["back_side"] is False and a["groove_left"]["op_id"] is None
    assert b["groove_top"]["op_id"] is None and b["groove_left"]["op_id"] == grs[0]["id"]          # «-» = yo'q
    xops = _ops(d, "XNC")
    assert len(xops) == 3 and all(x["xnc_part_id"] in (a["id"], b["id"]) for x in xops)
    assert len(a["xnc_op_ids"]) == 2 and len(b["xnc_op_ids"]) == 1
    by_part = {x["id"]: x for x in xops}
    first = by_part[a["xnc_op_ids"][0]]
    assert first["xnc"]["program"][0]["cmd"] == "DrillFront" and first["name"] == "Бок"
    assert first["code"] == "B1" and by_part[a["xnc_op_ids"][1]]["code"] == "B1-2"             # Обработка 2 — «-2» qo'shimchasi
    assert by_part[a["xnc_op_ids"][1]]["xnc"]["program"]                                       # o'rnatilgan shablon (pocket_rect) dasturi
    assert first["xnc"]["length"] == 700 and first["xnc"]["width"] == 500                       # sync_xnc detal o'lchamini oldi
    # XNC kodlari loyihada noyob
    codes = [x["code"] for x in xops]
    assert len(set(codes)) == len(codes)
    # ogohlantirishlar: yangi SP / GR yaratildi
    assert sum("поверхности" in w for w in d["warnings"]) == 2 and any("пазования" in w for w in d["warnings"])


def test_xnc_template_not_found_warns_once_and_links_nothing(client):
    pid = _project(client)
    rows = [EXTRA_HEAD,
            ["ЛДСП", 700, 500, 1, "A", "c1", "", "", "", "", "Нет_такого", ""],
            ["ЛДСП", 710, 500, 1, "B", "c2", "", "", "", "", "нет_такого", ""]]
    d = _imp(client, pid, _xlsx(rows), {"parts": {"start_row": 2, "map": EXTRA_MAP}}).json()
    assert d["imported"] == 2 and d["linked"]["xnc"] == 0 and _ops(d, "XNC") == []
    miss = [w for w in d["warnings"] if "Нет_такого" in w or "нет_такого" in w]
    assert len(miss) == 1 and "2" in miss[0]                                                  # bir marta, birinchi qator raqami bilan
    u = client.post(f"/api/projects/{pid}/import/excel", files={"file": ("d.xlsx", _xlsx(rows))}, headers=UZ,
                    data={"config": json.dumps({"parts": {"start_row": 2, "map": EXTRA_MAP}})}).json()
    assert any("topilmadi" in w for w in u["warnings"])


def test_xnc_codes_unique_against_existing_and_lib_key_lookup(client):
    pid = _project(client)
    client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": "S1", "name": "bor"})
    rows = [EXTRA_HEAD, ["ЛДСП", 700, 500, 1, "A", "S1", "", "", "", "", "lib:row32", ""],
            ["ЛДСП", 710, 500, 1, "B", "S1", "", "", "", "", "row32", ""]]
    d = _imp(client, pid, _xlsx(rows), {"parts": {"start_row": 2, "map": EXTRA_MAP}}).json()
    codes = sorted(o["code"] for o in _ops(d, "XNC"))
    assert codes == ["S1", "S1-2", "S1-3"] and d["linked"]["xnc"] == 2


def test_extras_absent_columns_leave_import_unchanged_and_dry_run_reports(client):
    pid = _project(client)
    rows = [["Длина", "Ширина", "Кол"], [700, 500, 2]]
    d = _imp(client, pid, _xlsx(rows), {"parts": {"start_row": 2, "map": {"length": "A", "width": "B", "qty": "C"}}}).json()
    assert d["imported"] == 1 and d["linked"] == {"sp": 0, "gr": 0, "xnc": 0, "xnc_new": 0} and _ops(d, "XNC") == []
    rows = [EXTRA_HEAD, ["ЛДСП", 700, 500, 1, "A", "c1", "Лак", "", "", "", "", ""]]
    dry = _imp(client, pid, _xlsx(rows), {"parts": {"start_row": 2, "map": EXTRA_MAP}}, dry_run=True).json()
    assert dry["dry_run"] is True and dry["linked"]["sp"] == 1
    assert _ops(_get(client, pid), "SP") == []                                               # dry-run saqlamadi


# ───────────────────────── погонаж: «Ширина» bo'sh → CL ─────────────────────────
LIN_ROWS = [["Мат", "Длина", "Ширина", "Кол", "Название", "ОВ"],
            ["ЛДСП", 700, 500, 2, "Панель", ""],
            ["Плинтус 60", 1200, "", 3, "Плинтус A", "ПВХ 1"],
            ["Плинтус 60", 800, "", 2, "Плинтус B", ""],
            ["", 500, "", 1, "Без материала", ""],
            ["ЛДСП", "", "", 1, "Нет длины", ""]]
LIN_MAP = {"material": "A", "length": "B", "width": "C", "qty": "D", "name": "E", "edge_top": "F"}


def test_empty_width_goes_to_cl_when_flag_set_else_skipped_as_before(client):
    pid = _project(client)
    d0 = _imp(client, pid, _xlsx(LIN_ROWS), {"parts": {"start_row": 2, "map": LIN_MAP}}).json()
    assert d0["imported"] == 1 and len(d0["skipped"]) == 4 and _ops(d0, "CL") == [] and d0["linear_imported"] == 0   # eski xulq
    pid = _project(client)
    d = _imp(client, pid, _xlsx(LIN_ROWS), {"parts": {"start_row": 2, "map": LIN_MAP, "linear_no_width": True}}).json()
    assert d["imported"] == 4 and d["linear_imported"] == 3 and [s["row"] for s in d["skipped"]] == [6]       # uzunlik yo'q — tashlandi
    cls = {o["name"]: o for o in _ops(d, "CL")}
    assert set(cls) == {"Плинтус 60", "Погонаж"}                                  # material nomi / standart nom
    pl = cls["Плинтус 60"]
    assert [(p["name"], p["length"], p["width"], p["qty"]) for p in pl["parts"]] == [("Плинтус A", 1200, 0, 3), ("Плинтус B", 800, 0, 2)]
    assert pl["parts"][0]["edge_top"]["op_id"] == _ops(d, "EL")[0]["id"]           # kromka CL detaliga ham
    assert cls["Погонаж"]["parts"][0]["name"] == "Без материала"
    cs = _ops(d, "CS")[0]
    assert len(cs["parts"]) == 1 and cs["parts"][0]["width"] == 500
    assert sum("погонаж" in w.lower() for w in d["warnings"]) == 2
    # CL kroyga yaroqli
    op = pl["id"]
    r = client.post(f"/api/projects/{pid}/operations/{op}/optimize", json={"quality": "fast"})
    assert r.status_code == 200 and r.json()["total_parts"] == 5


def test_linear_target_cl_and_existing_cl_reuse(client):
    pid = _project(client)
    cl = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": "Plintus 60"}).json()["operations"][-1]["id"]
    cl2 = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": "Boshqa"}).json()["operations"][-1]["id"]
    rows = [["Мат", "Длина", "Ширина", "Кол"], ["plintus 60", 1000, "", 1], ["", 900, "", 2]]
    cfg = {"parts": {"start_row": 2, "map": {"material": "A", "length": "B", "width": "C", "qty": "D"},
                     "linear_no_width": True, "target_cl": cl2}}
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    cls = {o["id"]: o for o in _ops(d, "CL")}
    assert len(cls) == 2 and d["created_ops"] == []
    assert [p["length"] for p in cls[cl]["parts"]] == [1000] and [p["length"] for p in cls[cl2]["parts"]] == [900]      # nom → mavjud CL; bo'sh → target_cl
    # target_cl CL emas → 400
    el = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "k"}).json()["operations"][-1]["id"]
    cfg["parts"]["target_cl"] = el
    assert _imp(client, pid, _xlsx(rows), cfg).status_code == 400


def test_linear_rows_skip_size_mode_conversion(client):
    pid = _project(client)
    rows = [["Мат", "Длина", "Ширина", "Кол"], ["ЛДСП", 700, 500, 1], ["П", 1000, "", 1]]
    cfg = {"parts": {"start_row": 2, "map": {"material": "A", "length": "B", "width": "C", "qty": "D"}, "linear_no_width": True,
                     "size_mode": "blank"}}
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    assert d["imported"] == 2 and d["skipped"] == []
    assert _ops(d, "CL")[0]["parts"][0]["length"] == 1000


# ───────────────────────── profil va 4-tab birga ─────────────────────────
def test_excel_profile_accepts_new_tabs_and_all_tabs_in_one_import(client, mat_catalog):
    prof = {"mode": "full", "parts": {"enabled": True, "map": {"length": "A"}, "linear_no_width": True},
            "simple": {"enabled": True, "map": {"code": "A"}}, "materials": {"enabled": True, "map": {"code": "A"}, "create_missing": False}}
    r = client.post("/api/settings/excel_import", json={"name": "W18 profil", "data": prof})
    assert r.status_code == 200 and r.json()["data"]["simple"]["map"] == {"code": "A"}
    client.delete(f"/api/settings/excel_import/{r.json()['id']}")
    pid = _project(client)
    wb = {"Детали": [["Мат", "Длина", "Ширина", "Кол"], ["ЛДСП", 700, 500, 2]],
          "Простые операции": [["Код", "Наименование", "Ед.И", "Кол", "Цена"], ["K1", "Ручка", "шт", 2, 100]],
          "Материалы": [["Код"], ["W18S1"]]}
    cfg = {"parts": {"enabled": True, "sheet_name": "Детали", "start_row": 2,
                     "map": {"material": "A", "length": "B", "width": "C", "qty": "D"}},
           "simple": {"enabled": True, "sheet_name": "Простые операции", "start_row": 2,
                      "map": {"code": "A", "name": "B", "unit": "C", "qty": "D", "price": "E"}},
           "materials": {"enabled": True, "sheet_name": "Материалы", "start_row": 2, "map": {"code": "A"}}}
    d = _imp(client, pid, _xlsx(wb), cfg).json()
    assert d["imported"] == 1 and d["simple_rows"] == 1 and d["materials_added"] == 1
    assert {o["type"] for o in d["operations"]} == {"CS", "O"}
    assert sorted(o["name"] for o in _ops(d, "CS")) == ["ЛДСП", "ЛДСП W18 18мм"]          # katalogdan (Материалы) + detal materialidan
    assert sorted(len(o["parts"]) for o in _ops(d, "CS")) == [0, 1]
    assert _ops(d, "O")[0]["o"]["materials"][0]["code"] == "K1"


def test_products_qty_mode_ignores_new_tabs(client):
    pid = _project(client)
    p = client.post(f"/api/projects/{pid}/products", json={"name": "Шкаф", "qty": 1}).json()
    rows = [["Наим", "Кол"], ["Шкаф", 5]]
    cfg = {"mode": "products_qty", "products": {"enabled": True, "link": "name", "start_row": 2, "map": {"name": "A", "qty": "B"}},
           "simple": {"enabled": True, "map": {"code": "A"}}}
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    assert d["updated_products"] == 1 and _ops(d, "O") == [] and d["simple_rows"] == 0
