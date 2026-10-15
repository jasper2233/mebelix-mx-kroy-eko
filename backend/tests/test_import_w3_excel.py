"""W3-A: Excel import v2 — loyiha darajasida, ko'p tabli («Детали» + «Изделия»), guruhlash, o'lcham rejimi,
«faqat mahsulot soni», `.xls`, xavfsizlik chegaralari. Fayllar testning o'zida `openpyxl` bilan yaratiladi."""
import importlib.util
import io
import json
import sys
from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook

from app.services import import_v2, importers

UZ = {"Accept-Language": "uz"}
FIX = Path(__file__).parent / "fixtures"

HEAD = ["Материал", "Длина", "Ширина", "Количество", "Текстура", "Наименование", "ОВ", "ОН", "ОЛ", "ОП", "Изделие", "№", "Описание"]
PMAP = {"material": "A", "length": "B", "width": "C", "qty": "D", "grain": "E", "name": "F", "edge_top": "G",
        "edge_bottom": "H", "edge_left": "I", "edge_right": "J", "product": "K"}


def _xlsx(sheets):
    """{varaq nomi: qatorlar} yoki qatorlar ro'yxati → .xlsx baytlari."""
    wb = Workbook()
    if isinstance(sheets, list):
        sheets = {"Лист1": sheets}
    first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        ws.title = name
        first = False
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _new_project(client, name="W3 import"):
    p = client.post("/api/projects", json={"name": name}).json()
    return p["id"], p


def _imp(client, pid, data, cfg, name="d.xlsx", dry_run=False, headers=None):
    return client.post(f"/api/projects/{pid}/import/excel", files={"file": (name, data)},
                       data={"config": json.dumps(cfg), "dry_run": "true" if dry_run else "false"}, headers=headers or {})


def _ops(p, typ):
    return [o for o in p["operations"] if o["type"] == typ]


def _cfg(**parts):
    return {"parts": {"start_row": 2, "map": dict(PMAP), **parts}}


ROWS = [HEAD,
        ["ЛДСП 16 Белый", 700, 550, 1, 1, "Основа", "ПВХ 0.4", "", "", "", "Шкаф А"],
        ["ЛДСП 16 Белый", 550, 165, 2, 1, "Крышка", "ПВХ 0.4", "ПВХ 0.4", "ПВХ 0.4", "ПВХ 0.4", "Шкаф А"],
        ["МДФ 18 Серый", 697, 184, 1, 0, "Фасад", "", "", "", "", "Шкаф Б"],
        ["лдсп  16 белый ", 100, 100, 3, 0, "Полка", "", "", "", "", "Шкаф А"]]


# ───────────────────────── guruhlash ─────────────────────────
def test_group_by_material_and_product_without_any_cs(client):
    pid, p0 = _new_project(client)
    assert not _ops(p0, "CS") and len(p0["products"]) == 1                 # yangi loyiha: CS yo'q, bitta standart mahsulot
    r = _imp(client, pid, _xlsx(ROWS), _cfg())
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["id"] == pid and d["imported"] == 4 and d["skipped"] == []
    cs = _ops(d, "CS")
    assert [o["name"] for o in cs] == ["ЛДСП 16 Белый", "МДФ 18 Серый"]    # «лдсп  16 белый » — o'sha CS (harf/bo'sh joy farqi yo'q)
    assert [len(o["parts"]) for o in cs] == [3, 1]
    assert [x["id"] for x in d["created_ops"]] == [o["id"] for o in cs]
    # tartib: CS lar birinchi, kromka (EL) — keyin
    types = [o["type"] for o in d["operations"]]
    assert types[:2] == ["CS", "CS"] and set(types[2:]) == {"EL"}
    assert [o["name"] for o in _ops(d, "EL")] == ["ПВХ 0.4"] and len(d["created_edges"]) == 1
    # mahsulotlar: bo'sh standart «Изделие 1» olib tashlanadi; «Шкаф А», «Шкаф Б»
    assert [x["name"] for x in d["products"]] == ["Шкаф А", "Шкаф Б"] and d["created_products"] == 2
    by_name = {x["name"]: x for x in d["products"]}
    parts = {x["name"]: x for x in cs[0]["parts"]}
    assert parts["Основа"]["product_id"] == by_name["Шкаф А"]["id"] == parts["Полка"]["product_id"]
    assert cs[1]["parts"][0]["product_id"] == by_name["Шкаф Б"]["id"]
    assert parts["Основа"]["grain"] is True and parts["Полка"]["grain"] is False and parts["Крышка"]["qty"] == 2
    assert parts["Крышка"]["edge_left"]["op_id"] == _ops(d, "EL")[0]["id"]
    allp = sorted(cs[0]["parts"] + cs[1]["parts"], key=lambda x: x["uid"])                  # uid — fayl tartibida, loyiha bo'yicha noyob
    assert [x["name"] for x in allp] == ["Основа", "Крышка", "Фасад", "Полка"] and len({x["uid"] for x in allp}) == 4


def test_existing_cs_reused_by_name_or_code_and_target_for_empty_material(client):
    pid, _p = _new_project(client)
    client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "MDF18", "name": "Другой"})
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LD16", "name": "ЛДСП 16 Белый"}).json()
    ld = p["operations"][-1]["id"]
    rows = [HEAD, ["лдсп 16 белый", 100, 50, 1, "", "A", "", "", "", "", ""],
            ["mdf18", 200, 60, 1, "", "B", "", "", "", "", ""],          # kod bo'yicha
            ["", 300, 70, 2, "", "C", "", "", "", "", ""]]              # material yo'q → target_op
    d = _imp(client, pid, _xlsx(rows), _cfg(target_op=ld)).json()
    assert d["created_ops"] == [] and d["imported"] == 3
    ops = {o["name"]: o for o in _ops(d, "CS")}
    assert [x["name"] for x in ops["ЛДСП 16 Белый"]["parts"]] == ["A", "C"]
    assert [x["name"] for x in ops["Другой"]["parts"]] == ["B"]
    assert any("ЛДСП 16 Белый" in w and "1" in w for w in d["warnings"])      # «Строк без материала: 1 — добавлены в …»
    # target_op — CS emas → 400, hech narsa o'zgarmaydi
    el = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "k"}).json()["operations"][-1]["id"]
    n_before = len(client.get(f"/api/projects/{pid}").json()["operations"])
    assert _imp(client, pid, _xlsx(rows), _cfg(target_op=el)).status_code == 400
    assert len(client.get(f"/api/projects/{pid}").json()["operations"]) == n_before


def test_without_material_column_uses_first_cs_or_creates_default(client, kravat):
    pid, cs, _el = kravat
    cfg = {"parts": {"start_row": 2, "map": {"length": "B", "width": "C", "qty": "D", "name": "F"}}}
    n0 = len(next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == cs)["parts"])
    d = _imp(client, pid, _xlsx(ROWS), cfg).json()
    assert d["imported"] == 4 and len(_ops(d, "CS")) == 1 and d["created_ops"] == []
    assert len(_ops(d, "CS")[0]["parts"]) == n0 + 4
    pid2, _p = _new_project(client)                                       # CS yo'q → standart «Материал 1» yaratiladi
    d = _imp(client, pid2, _xlsx(ROWS), cfg).json()
    assert [o["name"] for o in _ops(d, "CS")] == ["Материал 1"] and len(_ops(d, "CS")[0]["parts"]) == 4


def test_new_cs_takes_catalog_params_by_exact_name_or_code(client):
    client.post("/api/catalog/sync", json=[{"id": "w3x-ld16", "kind": "sheet", "code": "W3-LD-16", "name": "W3 ЛДСП 16 Дуб",
                                            "price": 450000, "thickness": 16, "length": 2800, "width": 2070,
                                            "params": {"trim_length": 10}}])
    pid, _p = _new_project(client)
    rows = [HEAD, ["w3-ld-16", 100, 50, 1, "", "A", "", "", "", "", ""],      # kod bo'yicha (katta-kichik harfsiz)
            ["Нет в каталоге W3", 100, 50, 1, "", "B", "", "", "", "", ""]]
    d = _imp(client, pid, _xlsx(rows), _cfg()).json()
    a, b = _ops(d, "CS")
    assert a["name"] == "w3-ld-16" and a["code"] == "W3-LD-16" and a["cs_material"]["thickness"] == 16
    assert a["cs_material"]["price"] == 450000 and a["sheets"][0]["length"] == 2800 and a["cs_cut"]["trim_length"] == 10
    assert b["name"] == "Нет в каталоге W3" and b["sheets"][0]["length"] == 2750      # standart list o'lchami


# ───────────────────────── qatorlar, varaq, qo'shimcha ustunlar ─────────────────────────
def test_sheet_by_name_row_range_zero_qty_extra_columns(client):
    pid, _p = _new_project(client)
    other = [["x"] * 3] * 3
    rows = [HEAD,
            ["M1", 100, 50, 1, "1", "Первая", "", "", "", "", "", 5, "заметка"],
            ["M1", 200, 60, 0, "", "Нулевая", "", "", "", "", "", 6, ""],
            ["M1", 300, 70, 2, "yes", "Третья", "", "", "", "", "", 7, ""],
            ["M1", 400, 80, 1, "", "За пределом", "", "", "", "", "", 8, ""]]
    data = _xlsx({"Прочее": other, "Детали": rows})
    cfg = _cfg(sheet_name="детали", start_row=2, end_row=4, skip_zero_qty=True,
               map={**PMAP, "number_in_name": "L", "description": "M", "code": "L"})
    d = _imp(client, pid, data, cfg).json()
    assert d["imported"] == 2 and d["zero_skipped"] == 1 and d["skipped"] == []
    ps = _ops(d, "CS")[0]["parts"]
    assert [x["name"] for x in ps] == ["5 Первая", "7 Третья"]                 # «Поместить номер в наименование»
    assert ps[0]["description"] == "заметка" and ps[0]["code"] == "5" and ps[0]["grain"] and ps[1]["grain"]
    assert any("нулев" in w for w in d["warnings"])
    # bir xil fayl, belgisiz: soni 0 detal ham qo'shiladi
    pid2, _p = _new_project(client)
    d = _imp(client, pid2, data, _cfg(sheet_name="Детали", end_row=4)).json()
    assert d["imported"] == 3 and d["zero_skipped"] == 0
    # varaq topilmadi → 400
    assert _imp(client, pid2, data, _cfg(sheet_name="yo'q")).status_code == 400
    assert _imp(client, pid2, data, _cfg(sheet=7)).status_code == 400


def test_empty_or_invalid_qty_length_rows_are_reported_not_silently_dropped(client):
    pid, _p = _new_project(client)
    rows = [HEAD, ["M", 100, 50, "", "", "Бос сони", "", "", "", "", ""],      # soni bo'sh — GibLab kabi qo'shilmaydi
            ["M", "abc", 50, 1, "", "Хато", "", "", "", "", ""],
            ["M", 100, 50, 1, "", "Яхши", "", "", "", "", ""], [None] * 13]
    d = _imp(client, pid, _xlsx(rows), _cfg()).json()
    assert d["imported"] == 1 and [s["row"] for s in d["skipped"]] == [2, 3] and all(s["tab"] == "parts" for s in d["skipped"])
    assert any("2" in w for w in d["warnings"])


# ───────────────────────── o'lcham rejimi ─────────────────────────
def _set_el(client, pid, el_id, **el):
    client.patch(f"/api/projects/{pid}/operations/{el_id}", json={"el": el})


def test_size_mode_conversion_into_project_mode(client, kravat):
    pid, cs, el = kravat                                      # kravat: detal bor, loyiha rejimi — detal
    _set_el(client, pid, el, thickness=1, jointing_width=0.5)
    rows = [HEAD, ["", 100, 50, 1, "", "Q", "KP-1/19", "KP-1/19", "KP-1/19", "KP-1/19", ""]]
    # fayl «prifugovkadan keyin»: detal = 100 + (1+1) × 50 + (1+1)
    d = _imp(client, pid, _xlsx(rows), _cfg(size_mode="jointed", target_op=cs)).json()
    q = next(x for o in d["operations"] if o["id"] == cs for x in o["parts"] if x["name"] == "Q")
    assert (q["length"], q["width"]) == (102, 52) and d["size_mode_changed"] is None
    # fayl «zagotovka»: zagotovka 100 → prifugovka 100 − (0.5+0.5) = 99 → detal 99 + 2 = 101 (en: 49 + 2 = 51)
    d = _imp(client, pid, _xlsx(rows), _cfg(size_mode="blank", target_op=cs)).json()
    q = [x for o in d["operations"] if o["id"] == cs for x in o["parts"] if x["name"] == "Q"][-1]
    assert (q["length"], q["width"]) == (101, 51)
    # loyiha rejimi bilan bir xil — o'zgarmaydi
    d = _imp(client, pid, _xlsx(rows), _cfg(size_mode="detail", target_op=cs)).json()
    q = [x for o in d["operations"] if o["id"] == cs for x in o["parts"] if x["name"] == "Q"][-1]
    assert (q["length"], q["width"]) == (100, 50)


def test_size_mode_empty_project_adopts_file_mode(client):
    pid, p0 = _new_project(client)
    assert p0["size_mode"] == "detail"
    rows = [HEAD, ["M", 100, 50, 1, "", "Q", "", "", "", "", ""]]
    d = _imp(client, pid, _xlsx(rows), _cfg(size_mode="blank")).json()
    assert d["size_mode_changed"] == "blank" and client.get(f"/api/projects/{pid}").json()["size_mode"] == "blank"
    assert _ops(d, "CS")[0]["parts"][0]["length"] == 100                        # fayldagi raqam o'zgarmadi


# ───────────────────────── «Изделия» tabi ─────────────────────────
PROD_ROWS = [["Код", "Наименование", "Количество", "Описание", "Телефон 1", "Телефон 2", "Дата"],
             ["SA", "Шкаф А", 2, "для А", "+998901112233", "+998907778899", date(2026, 10, 15)],
             ["SB", "Шкаф Б", 0, "", "", "", None],
             ["SC", "Шкаф В", 1, "пустой", "", "", "2026-11-01"]]
PRMAP = {"code": "A", "name": "B", "qty": "C", "description": "D", "phone1": "E", "phone2": "F", "date": "G"}


def _two_tabs(**prod):
    return {"parts": {"sheet_name": "Детали", "start_row": 2, "map": {**PMAP, "product": "K"}},
            "products": {"enabled": True, "sheet_name": "Изделия", "start_row": 2, "map": dict(PRMAP), **prod}}


def test_products_tab_link_by_name_fields_and_empty_products(client):
    pid, _p = _new_project(client)
    parts_rows = [HEAD, ["M", 100, 50, 1, "", "A", "", "", "", "", "Шкаф А"],
                  ["M", 200, 60, 1, "", "B", "", "", "", "", "Шкаф Б"],
                  ["M", 300, 70, 1, "", "C", "", "", "", "", "Неизвестный"]]
    data = _xlsx({"Детали": parts_rows, "Изделия": PROD_ROWS})
    d = _imp(client, pid, data, _two_tabs(link="name")).json()
    pr = {x["name"]: x for x in d["products"]}
    assert list(pr) == ["Шкаф А", "Шкаф Б", "Неизвестный"]                      # «Шкаф В» — bo'sh (add_empty o'chiq), tartib — varaq bo'yicha
    a = pr["Шкаф А"]
    assert (a["code"], a["qty"], a["description"], a["phone1"], a["phone2"], a["ready_date"]) == \
        ("SA", 2, "для А", "+998901112233", "+998907778899", "2026-10-15")
    assert pr["Шкаф Б"]["qty"] == 0 and pr["Неизвестный"]["qty"] == 1           # varaqda yo'q — qiymatdan, soni 1
    cs = _ops(d, "CS")[0]
    assert {x["name"]: x["product_id"] for x in cs["parts"]} == {"A": a["id"], "B": pr["Шкаф Б"]["id"], "C": pr["Неизвестный"]["id"]}
    # add_empty — bo'sh «Шкаф В» ham qo'shiladi
    pid2, _p = _new_project(client)
    d = _imp(client, pid2, data, _two_tabs(link="name", add_empty=True)).json()
    assert [x["name"] for x in d["products"]] == ["Шкаф А", "Шкаф Б", "Шкаф В", "Неизвестный"]
    assert next(x for x in d["products"] if x["name"] == "Шкаф В")["ready_date"] == "2026-11-01"


def test_products_tab_link_by_code_and_skip_zero_qty(client):
    pid, _p = _new_project(client)
    parts_rows = [HEAD, ["M", 100, 50, 1, "", "A", "", "", "", "", "SA"], ["M", 200, 60, 1, "", "B", "", "", "", "", "SB"],
                  ["M", 300, 70, 1, "", "C", "", "", "", "", "SC"]]
    data = _xlsx({"Детали": parts_rows, "Изделия": PROD_ROWS})
    d = _imp(client, pid, data, _two_tabs(link="code", skip_zero_qty=True)).json()
    assert [x["code"] for x in d["products"]] == ["SA", "SC"] and d["zero_skipped"] >= 1
    # «SB» (soni 0) mahsulot qo'shilmadi — uning detali ham tashlandi
    assert sorted(x["name"] for x in _ops(d, "CS")[0]["parts"]) == ["A", "C"] and d["imported"] == 2


def test_only_products_tab_adds_all_products_and_reuses_existing(client):
    pid, p0 = _new_project(client)
    client.post(f"/api/projects/{pid}/products", json={"name": "Шкаф А", "code": "SA", "qty": 7})
    data = _xlsx({"Изделия": PROD_ROWS})
    cfg = {"parts": {"enabled": False}, "products": {"enabled": True, "start_row": 2, "map": dict(PRMAP), "link": "code"}}
    d = _imp(client, pid, data, cfg).json()
    names = [x["name"] for x in d["products"]]
    assert names == ["Шкаф А", "Шкаф Б", "Шкаф В"]                              # mavjud «SA» qayta ishlatildi; standart bo'sh olib tashlandi
    assert next(x for x in d["products"] if x["code"] == "SA")["qty"] == 7        # oddiy rejimda mavjud mahsulot o'zgarmaydi
    assert d["created_products"] == 2


def test_products_qty_only_mode_updates_existing_and_invalidates_cut(client, kravat):
    pid, cs, _el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    prod = p["products"][0]
    client.post(f"/api/projects/{pid}/products", json={"name": "Шкаф Б", "code": "SB", "qty": 1})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == cs)["result"]
    rows = [["Наименование", "Количество"], [prod["name"], 3], ["Шкаф Б", 5], ["Нет такого", 2], ["Шкаф Б", 9]]
    cfg = {"mode": "products_qty", "products": {"start_row": 2, "link": "name", "map": {"name": "A", "qty": "B"}}}
    n_ops = len(p["operations"])
    d = _imp(client, pid, _xlsx(rows), cfg).json()
    pr = {x["name"]: x["qty"] for x in d["products"]}
    assert pr[prod["name"]] == 3 and pr["Шкаф Б"] == 5 and len(d["products"]) == 2         # yangi mahsulot qo'shilmadi
    assert d["updated_products"] == 2 and d["imported"] == 0 and len(d["operations"]) == n_ops
    assert [s["reason"] for s in d["skipped"]] and "Нет такого" in d["skipped"][0]["reason"]
    assert next(o for o in d["operations"] if o["id"] == cs)["result"] is None            # mahsulot soni o'zgardi → kroy eskirdi
    # kod bo'yicha; soni 0 + belgi — o'zgartirilmaydi
    cfg = {"mode": "products_qty", "products": {"start_row": 2, "link": "code", "skip_zero_qty": True,
                                                "map": {"code": "A", "qty": "B"}}}
    d = _imp(client, pid, _xlsx([["Код", "Сони"], ["SB", 0]]), cfg).json()
    assert {x["name"]: x["qty"] for x in d["products"]}["Шкаф Б"] == 5 and d["zero_skipped"] == 1
    # ustunlar yo'q → 400
    assert _imp(client, pid, _xlsx(rows), {"mode": "products_qty", "products": {"map": {"name": "A"}}}).status_code == 400


def test_dry_run_changes_nothing(client):
    pid, p0 = _new_project(client)
    r = _imp(client, pid, _xlsx(ROWS), _cfg(), dry_run=True)
    assert r.status_code == 200
    d = r.json()
    assert d["dry_run"] is True and d["imported"] == 4 and len(d["created_ops"]) == 2 and "operations" not in d
    after = client.get(f"/api/projects/{pid}").json()
    assert after["operations"] == [] and [x["name"] for x in after["products"]] == [x["name"] for x in p0["products"]]


# ───────────────────────── xavfsizlik va xatolar ─────────────────────────
def test_config_validation_errors_are_400_and_localized(client):
    pid, _p = _new_project(client)
    data = _xlsx(ROWS)
    bad = [{"parts": {"map": {**PMAP, "length": "1"}}},                      # ustun harfi emas
           {"parts": {"map": {**PMAP, "zzz": "A"}}},                         # noma'lum maydon
           {"parts": {"map": {**PMAP, "length": "ZZZ"}}},                    # chegaradan tashqari ustun
           {"parts": {"map": {"name": "A"}}},                                # uzunlik/en yo'q
           {"parts": {"enabled": False}, "products": {"enabled": False}},    # hech narsa yoqilmagan
           {"parts": {"start_row": 0, "map": PMAP}},
           {"mode": "boshqa"}]
    for cfg in bad:
        r = _imp(client, pid, data, cfg)
        assert r.status_code == 400, (cfg, r.text)
    r = client.post(f"/api/projects/{pid}/import/excel", files={"file": ("d.xlsx", data)}, data={"config": "{buzuq"})
    assert r.status_code == 400
    r = _imp(client, pid, data, {"parts": {"map": {"name": "A"}}}, headers=UZ)
    assert "ustunlari" in r.json()["detail"]
    assert _imp(client, "yoq", data, _cfg()).status_code == 404
    assert client.get(f"/api/projects/{pid}").json()["operations"] == []     # xatoda hech narsa saqlanmadi


def test_limits_file_size_rows_materials_and_formulas(client, monkeypatch):
    pid, _p = _new_project(client)
    data = _xlsx(ROWS)
    # fayl hajmi
    monkeypatch.setattr(importers, "MAX_FILE_BYTES", 500)
    assert _imp(client, pid, data, _cfg()).status_code == 413
    monkeypatch.setattr(importers, "MAX_FILE_BYTES", 10 * 1024 * 1024)
    # zip ochilgandan keyingi hajm (zip-bomba)
    monkeypatch.setattr(importers, "MAX_UNZIPPED_BYTES", 100)
    assert _imp(client, pid, data, _cfg()).status_code == 400
    monkeypatch.setattr(importers, "MAX_UNZIPPED_BYTES", 150 * 1024 * 1024)
    # o'qiladigan qatorlar chegarasi: 3-qatordan keyingisi o'qilmaydi
    monkeypatch.setattr(importers, "MAX_ROW_NO", 3)
    d = _imp(client, pid, data, _cfg(), dry_run=True).json()
    assert d["imported"] == 2
    monkeypatch.setattr(importers, "MAX_ROW_NO", 50_000)
    # bir importda yaratiladigan yangi CS soni
    monkeypatch.setattr(import_v2, "MAX_NEW_OPS", 1)
    r = _imp(client, pid, data, _cfg())
    assert r.status_code == 400 and client.get(f"/api/projects/{pid}").json()["operations"] == []
    monkeypatch.setattr(import_v2, "MAX_NEW_OPS", 100)
    # detallar soni chegarasi
    monkeypatch.setattr(import_v2, "MAX_IMPORT_PARTS", 2)
    assert _imp(client, pid, data, _cfg()).status_code == 400
    monkeypatch.setattr(import_v2, "MAX_IMPORT_PARTS", 20_000)
    # formula: hisoblanmaydi (saqlangan qiymat yo'q → bo'sh katak), qator sababi bilan tashlanadi
    wb = Workbook()
    ws = wb.active
    ws.append(HEAD)
    ws.append(["M", "=100+100", 50, 1, "", "Ф", "", "", "", "", ""])
    ws.append(["M", 120, 50, 1, "", "Нормал", "", "", "", "", ""])
    buf = io.BytesIO(); wb.save(buf)
    d = _imp(client, pid, buf.getvalue(), _cfg()).json()
    assert d["imported"] == 1 and d["skipped"][0]["row"] == 2


def test_html_disguised_as_xls_and_garbage_are_rejected_clearly(client):
    pid, _p = _new_project(client)
    html = "<html><table><tr><td>a</td></tr></table></html>".encode()
    r = _imp(client, pid, html, _cfg(), name="d.xls")
    assert r.status_code == 400 and ".xlsx" in r.json()["detail"]
    r = _imp(client, pid, html, _cfg(), name="d.xls", headers=UZ)
    assert "Fayl formati" in r.json()["detail"]
    assert _imp(client, pid, b"PK\x03\x04garbage", _cfg(), name="d.xlsx").status_code == 400
    # kengaytma xlsx, mazmun — OLE2 (shifrlangan/buzuq .xls): xabar bilan 400
    assert _imp(client, pid, importers._OLE2 + b"x" * 600, _cfg(), name="d.xlsx").status_code == 400


def test_csv_and_old_endpoint_still_work(client, kravat):
    pid, cs, _el = kravat
    text = "Материал;Длина;Ширина;Количество;Наименование\nЛДСП Тест;764;300;2;Полка\nЛДСП Тест;500;200;1;Стенка\n"
    cfg = {"parts": {"start_row": 2, "map": {"material": "A", "length": "B", "width": "C", "qty": "D", "name": "E"}}}
    d = _imp(client, pid, text.encode("cp1251"), cfg, name="d.csv").json()
    assert d["imported"] == 2 and [x["name"] for x in d["created_ops"]] == ["ЛДСП Тест"]
    # eski endpoint — avvalgi shakl
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("d.csv", text.encode("utf-8-sig"))},
                    data={"col_map": json.dumps({"name": "E", "length": "B", "width": "C", "qty": "D"})})
    assert r.status_code == 200 and r.json()["imported"] == 2 and r.json()["skipped"] == []


def test_preview_returns_sheet_name_format_and_selects_sheet_by_name(client):
    data = _xlsx({"Первый": [["a", "b"]], "Второй": [["x", "y", "z"], ["1", "2", "3"]]})
    pv = client.post("/api/import/preview", files={"file": ("d.xlsx", data)}, data={"sheet": 0}).json()
    assert pv["sheets"] == ["Первый", "Второй"] and pv["sheet"] == "Первый" and pv["format"] == "xlsx" and pv["columns"] == ["A", "B"]
    pv = client.post("/api/import/preview", files={"file": ("d.xlsx", data)}, data={"sheet_name": "второй"}).json()
    assert pv["sheet"] == "Второй" and pv["columns"] == ["A", "B", "C"] and pv["rows"][1] == ["1", "2", "3"]
    assert client.post("/api/import/preview", files={"file": ("d.xlsx", data)}, data={"sheet_name": "yoq"}).status_code == 400


# ───────────────────────── .xls (xlrd) ─────────────────────────
needs_xlrd = pytest.mark.skipif(importlib.util.find_spec("xlrd") is None, reason=".xls o'qish uchun xlrd kerak (pip install xlrd)")


def test_xls_without_xlrd_gives_clear_message(client, monkeypatch):
    """xlrd o'rnatilmagan bo'lsa — aniq xabar: .xlsx / .csv talab qilinadi (import va ko'rish)."""
    monkeypatch.setitem(sys.modules, "xlrd", None)                       # `import xlrd` → ImportError
    data = (FIX / "w3_sample.xls").read_bytes()
    pid, _p = _new_project(client)
    r = _imp(client, pid, data, _cfg(), name="s.xls")
    assert r.status_code == 400 and "xlrd" in r.json()["detail"] and ".xlsx" in r.json()["detail"]
    r = client.post("/api/import/preview", files={"file": ("s.xls", data)}, data={"sheet": 0}, headers=UZ)
    assert r.status_code == 400 and "xlrd" in r.json()["detail"]
    assert client.get(f"/api/projects/{pid}").json()["operations"] == []


@needs_xlrd
def test_xls_preview_and_full_import_both_tabs(client):
    data = (FIX / "w3_sample.xls").read_bytes()
    pv = client.post("/api/import/preview", files={"file": ("sample.xls", data)}, data={"sheet": 0}).json()
    assert pv["format"] == "xls" and pv["sheets"] == ["детали", "изделия"] and pv["rows"][0][:3] == ["Материал", "Длина", "Ширина"]
    assert pv["rows"][1][1] == "700"                                          # float 700.0 → «700»
    pid, _p = _new_project(client)
    cfg = {"parts": {"sheet_name": "детали", "start_row": 2, "map": {**PMAP, "product": "K"}},
           "products": {"enabled": True, "sheet_name": "изделия", "start_row": 2, "link": "name", "map": dict(PRMAP),
                        "add_empty": True}}
    d = _imp(client, pid, data, cfg, name="sample.xls").json()
    assert d["imported"] == 3 and [o["name"] for o in _ops(d, "CS")] == ["ЛДСП 16 Белый", "МДФ 18 Серый"]
    assert all(p["grain"] for p in _ops(d, "CS")[0]["parts"]) and not _ops(d, "CS")[1]["parts"][0]["grain"]   # 1.0 / 0.0
    pr = {x["name"]: x for x in d["products"]}
    assert pr["Шкаф А"]["qty"] == 2 and pr["Шкаф А"]["ready_date"] == "2026-10-15" and "Шкаф В" in pr
    assert [o["name"] for o in _ops(d, "EL")] == ["ПВХ 0.4"]
    # kengaytma xlsx deb yolg'on aytsa ham mazmundan tanib olinadi
    d = _imp(client, _new_project(client)[0], data, cfg, name="sample.xlsx").json()
    assert d["imported"] == 3


@needs_xlrd
def test_xls_qty_only_mode_and_old_endpoint(client, kravat):
    data = (FIX / "w3_sample.xls").read_bytes()
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/products", json={"name": "Шкаф А", "code": "SA", "qty": 1})
    cfg = {"mode": "products_qty", "products": {"sheet": 1, "start_row": 2, "link": "code", "map": {"code": "A", "qty": "C"}}}
    d = _imp(client, pid, data, cfg, name="s.xls").json()
    assert {x["name"]: x["qty"] for x in d["products"]}["Шкаф А"] == 2 and d["updated_products"] == 1
    assert [s["row"] for s in d["skipped"]] == [3, 4]                          # SB, SC — loyihada yo'q
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("s.xls", data)},
                    data={"col_map": json.dumps({"name": "F", "length": "B", "width": "C", "qty": "D", "grain": "E"}), "sheet": 0})
    assert r.status_code == 200 and r.json()["imported"] == 3


def test_excel_import_profile_scope_accepts_v2_shape_and_old_shape(client):
    """Kengaytirilgan profil (`parts` / `products` / `mode`) saqlanadi; eski `{map, start}` profillari ham o'qiladi."""
    old = client.post("/api/settings/excel_import", json={"name": "W3 eski", "data": {"map": {"length": "B", "width": "C"}, "start": 3}}).json()
    new = client.post("/api/settings/excel_import", json={"name": "W3 yangi", "data": {
        "mode": "full", "parts": {"sheet_name": "Детали", "start_row": 2, "end_row": 500, "size_mode": "blank", "skip_zero_qty": True,
                                  "map": {**PMAP, "number_in_name": "L"}},
        "products": {"enabled": True, "sheet_name": "Изделия", "link": "code", "map": PRMAP, "add_empty": True}}}).json()
    got = {p["name"]: p for p in client.get("/api/settings/excel_import").json()}
    assert got["W3 eski"]["data"] == {"map": {"length": "B", "width": "C"}, "start": 3}
    d = got["W3 yangi"]["data"]
    assert d["parts"]["size_mode"] == "blank" and d["products"]["link"] == "code" and d["parts"]["map"]["number_in_name"] == "L"
    # saqlangan sozlama bilan import ishlaydi (profil ma'lumoti to'g'ridan-to'g'ri `config`)
    pid, _p = _new_project(client)
    data = _xlsx({"Детали": ROWS, "Изделия": PROD_ROWS})
    cfg = {k: v for k, v in d.items()}
    cfg["parts"] = {**cfg["parts"], "end_row": 0}
    assert _imp(client, pid, data, cfg).status_code == 200
    for p in (old, new):
        assert client.delete(f"/api/settings/excel_import/{p['id']}").status_code == 200
