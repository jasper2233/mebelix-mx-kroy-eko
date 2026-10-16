"""2026-10-16 (X_1015 §16): (LB) «Параметры» kuzatilgan tizimdagi kabi — A4 rejimida etiketka o'lchami sahifa va to'rdan hisoblanadi,
yangi operatsiya standarti, nom manbaga qarab, `.project` atributlari 1:1 (import / eksport)."""
from xml.etree import ElementTree as ET

from app.models import LBParams, Operation, OpType, Project
from app.services import label_import, label_zpl
from app.services.project_export import export_project
from tests.test_labels_w4_print import _cut, _html, _new_lb

REAL = ('<operation printMode="0" printParts="true" partEach="false" partONZ="false" partSelected="false" printWastes="true" '
        'wasteEach="false" productEach="false" productONZ="false" columns="2" rows="4" gap="10" margin="true" source="2" '
        'printable="true" startNewPage="true" typeId="LB" id="6"/>')


def test_label_size_derived_in_sheet_mode():
    assert LBParams().label_size() == (210.0, 297.0)                                     # 1×1 maydonsiz
    lb = LBParams(columns=2, rows=4, gap_mm=10, margin_mm=6)
    assert lb.auto_size and lb.label_size() == (94.0, 63.75)
    assert LBParams(columns=2, rows=2, rotate_page=90).label_size() == (148.5, 105.0)    # albom
    assert LBParams(columns=3, rows=7, gap_mm=0).label_size() == (70.0, 42.42)           # pastga yaxlitlanadi (sig'adi)
    roll = LBParams(mode="roll", width_mm=58, height_mm=40, columns=2, rows=4)
    assert not roll.auto_size and roll.label_size() == (58.0, 40.0)
    legacy = LBParams(columns=3, rows=0, width_mm=60, height_mm=30)                      # eski ma'lumot: qo'lda o'lcham
    assert not legacy.auto_size and legacy.label_size() == (60.0, 30.0) and legacy.effective() is legacy
    eff = lb.effective()
    assert (eff.width_mm, eff.height_mm) == (94.0, 63.75) and lb.width_mm == 58          # asl nusxa o'zgarmaydi


def test_new_op_defaults_and_name(client, kravat):
    pid = kravat[0]
    op = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()["operations"][-1]
    assert op["name"] == "Этикетки: Детали и остатки"
    lb = op["lb"]
    assert (lb["mode"], lb["source"], lb["columns"], lb["rows"], lb["gap_mm"], lb["margin_mm"]) == ("sheet", "parts", 1, 1, 0, None)
    assert lb["border"] is False and (lb["border_mode"] in (None, "none"))
    assert lb["print_parts"] and not lb["part_each"] and not lb["part_only_nonzero"] and lb["part_selected_only"] in (None, False)
    assert lb["print_wastes"] and not lb["waste_each"]
    # nom manbaga qarab (lb_defaults dagi manba) — faqat yaratishda
    assert client.put("/api/settings/lb_defaults/default", json={**lb, "source": "products"}).status_code == 200
    try:
        op2 = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()["operations"][-1]
        assert op2["name"] == "Этикетки: Изделия" and op2["lb"]["source"] == "products"
        client.patch(f"/api/projects/{pid}/operations/{op2['id']}", json={"lb": {"source": "user"}})
        assert next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == op2["id"])["name"] == "Этикетки: Изделия"
    finally:
        client.put("/api/settings/lb_defaults/default", json=lb)


def test_print_uses_derived_size(client, kravat):
    pid, _cs, _el = _cut(client, kravat)
    oid = _new_lb(client, pid, columns=2, rows=4, gap_mm=10, margin_mm=6)
    h = _html(client, pid, oid)
    assert "grid-template-columns:repeat(2,94mm);grid-auto-rows:63.75mm;gap:10mm" in h and ".lbl{width:94mm;height:63.75mm}" in h
    assert "@page{size:210mm 297mm;margin:6mm}" in h
    # jonli ko'rish ham
    lb = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["lb"]
    pv = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": lb}).json()
    assert ".lbl{width:94mm;height:63.75mm}" in pv["html"] and not any("помещается" in w for w in pv["warnings"])
    # rulon — qo'lda o'lcham
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"mode": "roll"}})
    assert "@page{size:58mm 40mm;margin:0}" in _html(client, pid, oid)
    # eski A4 (rows=0) — qo'lda o'lcham, avvalgidek
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"mode": "sheet", "rows": 0, "columns": 3, "width_mm": 60, "height_mm": 30}})
    assert ".lbl{width:60mm;height:30mm}" in _html(client, pid, oid)


def test_zpl_and_vars_use_derived_size(client, kravat):
    from app import store
    pid, _cs, _el = _cut(client, kravat)
    lb = LBParams(columns=2, rows=4, gap_mm=10, margin_mm=6,
                  template={"name": "t", "size": {"w": 58, "h": 40},
                            "elements": [{"t": "text", "x": 1, "y": 1, "text": "label.width+'x'+label.height", "size": 3}]})
    res = label_zpl.render_zpl(store.load(pid), lb, limit=1)
    assert "^PW" in res.zpl and "94.0x63.75" in res.zpl
    dots = int(res.zpl.split("^PW")[1].split("^")[0])
    assert abs(dots - round(94 / 25.4 * res.dpi)) <= 1


def test_import_real_attributes_and_export_roundtrip():
    warns: list[str] = []
    lb, name = label_import.from_project_xml(ET.fromstring(REAL), warns)
    assert name == "Этикетки: Детали и остатки"
    assert (lb.mode, lb.source, lb.columns, lb.rows, lb.gap_mm, lb.margin_mm) == ("sheet", "parts", 2, 4, 10, 6.0)
    assert lb.print_parts and not lb.part_each and not lb.part_only_nonzero and lb.print_wastes and not lb.waste_each
    assert not lb.product_each and not lb.product_only_nonzero
    assert lb.label_size() == (94.0, 63.75)
    # atributlar yo'q — yangi standart
    lb0, _n = label_import.from_project_xml(ET.fromstring('<operation typeId="LB" id="1"/>'), [])
    d = LBParams()
    assert (lb0.columns, lb0.rows, lb0.gap_mm, lb0.margin_mm, lb0.part_each, lb0.print_wastes, lb0.waste_each) == \
        (d.columns, d.rows, d.gap_mm, d.margin_mm, d.part_each, d.print_wastes, d.waste_each)
    # eksport — o'sha atributlar
    pr = Project(name="T", operations=[Operation(type=OpType.LB, name="Этикетки", lb=lb)])
    txt = export_project(pr).xml.decode("utf-8")
    for k, v in {"printMode": "0", "printParts": "true", "partEach": "false", "partONZ": "false", "partSelected": "false",
                 "printWastes": "true", "wasteEach": "false", "productEach": "false", "productONZ": "false",
                 "columns": "2", "rows": "4", "gap": "10", "margin": "true", "source": "2"}.items():
        assert f'{k}="{v}"' in txt, k
