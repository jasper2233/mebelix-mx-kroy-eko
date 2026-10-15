"""Parity (W_PARITY_SPEC §5, §6): (LB) «Параметры» — «Границы» ro'yxati, «Выбранные детали» katakchasi; «Товары» importi —
«Родительский ID» (papka daraxti), «Единица измерения», «Размер»."""
import io
import json
from xml.etree import ElementTree as ET

from openpyxl import Workbook

from app.models import LBParams, Operation, OpType, Project
from app.services import catalog as cat
from app.services import label_import
from app.services.project_export import export_project
from tests.test_labels_w4_print import _count, _cut, _html, _new_lb


def _lb_of(client, pid, oid):
    return next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["lb"]


# ───────────────────────── (LB) «Границы» ─────────────────────────
def test_border_mode_model_and_legacy_flag():
    assert LBParams().border_kind == "perimeter" and LBParams().border_mode is None           # eski standart: ramka bor
    assert LBParams(border=False).border_kind == "none"                                       # eski bayroq (border_mode yo'q)
    lb = LBParams(border=True, border_mode="none")                                            # ro'yxat ustun, bayroq moslanadi
    assert lb.border_kind == "none" and lb.border is False
    lb = LBParams(border=False, border_mode="perimeter")
    assert lb.border_kind == "perimeter" and lb.border is True
    old = LBParams.model_validate({"border": False, "width_mm": 60}, context={"legacy": True})    # eski saqlangan JSON
    assert old.border_kind == "none" and old.border_mode is None


def test_border_mode_changes_print(client, kravat):
    pid, _cs, _el = _cut(client, kravat)
    oid = _new_lb(client, pid)
    assert ".lbl{box-sizing:border-box;border:.2mm solid #555" in _html(client, pid, oid)     # standart: perimetr bo'yicha
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"border_mode": "none"}})
    assert r.status_code == 200
    lb = _lb_of(client, pid, oid)
    assert lb["border_mode"] == "none" and lb["border"] is False
    h = _html(client, pid, oid)
    assert ".lbl{box-sizing:border-box;border:none" in h
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"border_mode": "perimeter"}})
    assert _lb_of(client, pid, oid)["border"] is True
    assert ".lbl{box-sizing:border-box;border:.2mm solid #555" in _html(client, pid, oid)
    # etiketka printeri rejimida ham
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"mode": "roll", "border_mode": "none"}})
    h = _html(client, pid, oid)
    assert "@page{size:58mm 40mm;margin:0}" in h and ".lbl{box-sizing:border-box;border:none" in h
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"border_mode": "dashed"}}).status_code == 422


# ───────────────────────── (LB) «Выбранные детали» ─────────────────────────
def test_selected_parts_checkbox(client, kravat):
    pid, _cs, _el = _cut(client, kravat)
    oid = _new_lb(client, pid)

    def total(**lb):
        assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": lb}).status_code == 200
        n = client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"]
        assert _count(_html(client, pid, oid)) == n                       # sanash va chop bir xil
        return n
    assert total() == 19
    assert total(part_selected=[2, 5]) == 4                               # eski xulq: katakcha berilmagan — ro'yxat ishlaydi
    assert total(part_selected_only=False) == 19                          # katakcha o'chiq — ro'yxat saqlanadi, lekin e'tiborsiz
    assert _lb_of(client, pid, oid)["part_selected"] == [2, 5]
    assert total(part_selected_only=True) == 4                            # yoqildi — faqat tanlanganlar
    assert total(part_selected=[]) == 0                                   # yoqiq, tanlov bo'sh — detal etiketkasi yo'q
    assert total(part_selected_only=False) == 19


def test_selected_parts_in_zpl(client, kravat):
    pid, _cs, _el = _cut(client, kravat)
    oid = _new_lb(client, pid, mode="roll", part_selected=[2, 5], part_selected_only=True)
    r = client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": _lb_of(client, pid, oid)})
    assert r.status_code == 200, r.text
    assert r.content.count(b"^XZ") == 4
    lb = dict(_lb_of(client, pid, oid), part_selected_only=False)
    assert client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": lb}).content.count(b"^XZ") == 19


def test_only_nonzero_and_each_flags_still_work(client, kravat):
    pid, _cs, _el = _cut(client, kravat)
    oid = _new_lb(client, pid, part_each=False, part_only_nonzero=False)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 14


def test_defaults_do_not_keep_selection_flag(client):
    before = client.get("/api/settings/lb_defaults/default").json()
    try:
        saved = client.put("/api/settings/lb_defaults/default",
                           json={"border_mode": "none", "part_selected": [1], "part_selected_only": True})
        assert saved.status_code == 200
        d = client.get("/api/settings/lb_defaults/default").json()
        assert d["border_mode"] == "none" and d["border"] is False
        assert d["part_selected"] == [] and d["part_selected_only"] is None
    finally:
        client.put("/api/settings/lb_defaults/default", json=before)      # boshqa testlar uchun avvalgi holat


def test_project_file_selection_flag_and_border_attr():
    op = Operation(type=OpType.LB, name="Этикетки", lb=LBParams(part_selected=[3], part_selected_only=True))
    op2 = Operation(type=OpType.LB, name="Этикетки 2", lb=LBParams(part_selected=[3], part_selected_only=False))
    xml = export_project(Project(name="p", operations=[op, op2])).xml.decode("utf-8")
    assert xml.count('partSelected="true"') == 1 and xml.count('partSelected="false"') == 1
    assert "border=" not in xml                       # korxona fayllarida bu atribut yo'q — eksport lug'ati kengaymaydi
    # importda atribut uchrasa — o'qiladi: 0 — chegara yo'q, boshqasi — perimetr; bo'lmasa — eski standart
    warns: list[str] = []
    got = [label_import.from_project_xml(ET.fromstring(f'<operation typeId="LB" {a}/>'), warns)[0]
           for a in ('border="0"', 'border="1"', "")]
    assert [x.border_kind for x in got] == ["none", "perimeter", "perimeter"] and got[2].border_mode is None


# ───────────────────────── «Товары» importi ─────────────────────────
def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _import(client, rows, cmap, **form):
    data = {"col_map": json.dumps(cmap), "start_row": 2, **{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in form.items()}}
    return client.post("/api/catalog/import", files={"file": ("g.xlsx", _xlsx(rows))}, data=data)


def test_parse_size():
    assert cat.parse_size("2750x1830") == (2750, 1830, None)
    assert cat.parse_size("2800 × 2070 × 16") == (2800, 2070, 16)
    assert cat.parse_size("2750х1830") == (2750, 1830, None)              # kirill «х»
    assert cat.parse_size("3050*1220") == (3050, 1220, None)
    assert cat.parse_size(2440) == (2440, None, None)
    assert cat.parse_size("abc") == (None, None, None) and cat.parse_size(None) == (None, None, None)


def test_parent_id_builds_tree_unit_and_size(client):
    """Papka belgisi ustunisiz: «Родительский ID» ning o'zi daraxtni quradi; birlik va «Размер» qatorga yoziladi."""
    rows = [["ID", "Родительский ID", "Код", "Наименование", "Единица измерения", "Цена", "Размер", "Толщина", "Длина"],
            [1, None, "", "Плиты", "", None, None, None, None],
            [2, 1, "", "ЛДСП 16", "", None, None, None, None],
            [10, 2, "PL1", "ЛДСП Белый", "м2", 100, "2750x1830", 16, None],
            [11, 2, "PL2", "ЛДСП Дуб", "лист", 120, "2800 × 2070 × 18", None, None],
            [12, 2, "PL3", "ЛДСП Серый", "шт", 90, "2440x1220", None, 3000],
            [13, None, "PL4", "Без папки", "м2", 50, None, None, None]]
    cmap = {"id": "A", "parent_id": "B", "code": "C", "name": "D", "unit": "E", "price": "F", "size": "G", "thickness": "H", "length": "I"}
    r = _import(client, rows, cmap, id_prefix="plb-", kind="linear")
    assert r.status_code == 200, r.text
    d = r.json()
    assert (d["count"], d["folders"], d["items"]) == (6, 2, 4)
    it = {x["id"]: x for x in client.get("/api/catalog", params={"limit": 5000}).json() if x["id"].startswith("plb-")}
    assert it["plb-1"]["kind"] == "folder" and it["plb-2"]["kind"] == "folder" and it["plb-2"]["parent_id"] == "plb-1"
    assert it["plb-10"]["parent_id"] == "plb-2" and it["plb-13"]["parent_id"] is None
    assert [it[f"plb-{i}"]["unit"] for i in (10, 11, 12, 13)] == ["м2", "лист", "шт", "м2"]
    assert (it["plb-10"]["length"], it["plb-10"]["width"], it["plb-10"]["thickness"]) == (2750, 1830, 16)
    assert (it["plb-11"]["length"], it["plb-11"]["width"], it["plb-11"]["thickness"]) == (2800, 2070, 18)
    assert (it["plb-12"]["length"], it["plb-12"]["width"]) == (3000, 1220)          # alohida «Длина» ustuni ustun
    assert all(it[f"plb-{i}"]["kind"] == "linear" for i in (10, 11, 12, 13))        # «Корневая категория» — tanlangan tur
    tree = client.get("/api/catalog/tree").json()
    root = next(n for n in tree["nodes"] if n["id"] == "plb-1")
    assert root["count"] == 3 and [c["id"] for c in root["children"]] == ["plb-2"]
    assert tree["unfiled"] >= 1
    # qayta import (boshqa ildiz kategoriya): mavjud qatorlar yangilanadi, ko'paymaydi
    r = _import(client, rows, cmap, id_prefix="plb-", kind="edge")
    assert r.status_code == 200
    it = {x["id"]: x for x in client.get("/api/catalog", params={"limit": 5000}).json() if x["id"].startswith("plb-")}
    assert it["plb-10"]["kind"] == "edge" and len(it) == 6


def test_unknown_field_rejected(client):
    r = _import(client, [["a"], ["x"]], {"name": "A", "sort": "B"})
    assert r.status_code == 400
