"""W4 · LB: `.project` importi LB operatsiyasini o'qiydi (parametrlar saqlanadi, eski shablon matni — o'qilmasdan saqlanadi)."""
import base64
from pathlib import Path
from xml.sax.saxutils import quoteattr

import pytest

from app.models import Project
from app.plugins.legacy_project import import_project

# real fayllardagi LB operatsiyasi tuzilmasi (qiymatlar umumiy; mijoz ma'lumoti yo'q)
PROGRAM = ('<?xml version="1.0" encoding="UTF-8"?><program columns="2" dx="89" dy="60.25" gap="10" margin="true" printMode="0" rows="4">'
           '<par comment="Деталь - Код" name="part.code" type="string" expr="01_017"/>'
           '<var comment="Длина без полей" name="la" type="double" expr="dx-margin*2"/></program>')
FIELDS = "BASE64:" + base64.b64encode(
    b'<fields><field id="1" name="qty" type="integer" width="10" default="1"/></fields>').decode()


def lb_xml(**attrs) -> bytes:
    base = dict(printMode="0", printParts="true", partEach="false", partONZ="false", partSelected="false", printWastes="true",
                wasteEach="false", productEach="false", productONZ="false", columns="2", rows="4", gap="10", margin="true",
                source="2", fields=FIELDS, printable="true", startNewPage="true", data="AQAAAAA=", program=PROGRAM, typeId="LB", id="6")
    base.update(attrs)
    a = " ".join(f"{k}={quoteattr(v)}" for k, v in base.items() if v is not None)
    return f'<?xml version="1.0" encoding="UTF-8"?><project name="Demo"><operation {a}/></project>'.encode("utf-8")


def test_lb_operation_is_imported_with_all_parameters():
    p, warnings = import_project(lb_xml(), "demo.project")
    assert [o.type.value for o in p.operations] == ["LB"]
    op = p.operations[0]
    lb = op.lb
    assert op.name == "Этикетки: Детали и остатки" and op.print and op.new_page
    assert (lb.source, lb.mode, lb.columns, lb.rows, lb.gap_mm, lb.margin_mm) == ("parts", "sheet", 2, 4, 10, 6)
    assert (lb.width_mm, lb.height_mm) == (89, 60.25)                         # program ildiz elementining dx/dy si (rulon uchun saqlanadi)
    assert lb.label_size() == (94, 63.75)                                     # A4 2×4: chopda sahifa va to'rdan hisoblanadi
    assert lb.print_parts and not lb.part_each and not lb.part_only_nonzero and lb.print_wastes and not lb.waste_each
    assert not lb.product_each and not lb.product_only_nonzero and lb.part_selected == []
    assert lb.fields == [{"name": "qty", "title": "qty", "type": "integer", "width": 10.0, "default": "1"}]
    assert lb.legacy_program == PROGRAM                                       # ma'lumot yo'qolmaydi
    assert lb.template is None and lb.template_id is None                     # shablon o'qilmaydi — standart ishlatiladi
    assert any("шаблон" in w and "не читается" in w for w in warnings)
    assert not any("Пропущена операция" in w for w in warnings)               # endi «o'tkazib yuborildi» emas


def test_lb_import_variants_and_clamping():
    p, w = import_project(lb_xml(printMode="1", source="1", columns="99", rows="-3", gap="900", margin="false", program=None,
                                 fields="BASE64:@@bu-base64-emas@@", partEach="true", partONZ="true"), "x.project")
    lb = p.operations[0].lb
    assert lb.mode == "roll" and lb.source == "products" and lb.columns == 20 and lb.rows == 0 and lb.gap_mm == 50
    assert lb.margin_mm is None and lb.fields == [] and lb.legacy_program == "" and lb.part_each and lb.part_only_nonzero
    assert (lb.width_mm, lb.height_mm) == (58, 40) and not w                  # program yo'q — standart o'lcham, ogohlantirish yo'q
    p, _ = import_project(lb_xml(source="0"), "x.project")
    assert p.operations[0].lb.source == "user"
    p, _ = import_project(lb_xml(program=PROGRAM.replace('dx="89"', 'dx="99999"')), "x.project")
    assert p.operations[0].lb.width_mm == 500                                  # o'lcham chegaralanadi
    big = "<program dx=\"50\" dy=\"30\">" + "x" * 400_000 + "</program>"
    p, _ = import_project(lb_xml(program=big), "x.project")
    assert len(p.operations[0].lb.legacy_program) == 300_000 and p.operations[0].lb.width_mm == 50


def test_lb_fields_schema_is_filtered():
    raw = base64.b64encode(b'<fields><field name="ok_1" type="string" width="12" default="a"/><field name="1bad"/>'
                           b'<field name="a b"/><field name="x" description="Sarlavha" type="double" width="0"/></fields>').decode()
    p, _ = import_project(lb_xml(fields="BASE64:" + raw), "x.project")
    f = p.operations[0].lb.fields
    assert [x["name"] for x in f] == ["ok_1", "x"] and f[1]["title"] == "Sarlavha" and f[1]["width"] == 1.0
    p, _ = import_project(lb_xml(fields="BASE64:" + base64.b64encode(b"<!DOCTYPE x [<!ENTITY e 'v'>]><fields/>").decode()), "x.project")
    assert p.operations[0].lb.fields == []                                    # XML hujum — rad etiladi, loyiha ochiladi


def test_imported_lb_survives_save_and_reload():
    p, _ = import_project(lb_xml(), "demo.project")
    again = Project.model_validate_json(p.model_dump_json())                  # bazadan yuklash yo'li (legacy kontekst)
    assert again.operations[0].lb == p.operations[0].lb


def test_imported_lb_prints_with_default_template(client):
    r = client.post("/api/projects/import-file", files={"file": ("demo.project", lb_xml())})
    assert r.status_code == 200, r.text
    d = r.json()
    proj = d["project"]
    assert any("шаблон" in w for w in d["warnings"])                           # foydalanuvchi ogohlantiriladi
    pid = proj["id"]
    oid = proj["operations"][0]["id"]
    pv = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": proj["operations"][0]["lb"]}).json()
    assert pv["template"] == "builtin:detail" and pv["total"] == 0 and not pv["errors"]
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 0


_CORPUS = Path(__file__).resolve().parents[2] / "tools" / "bench" / "projects"


@pytest.mark.skipif(not _CORPUS.exists(), reason="korxona korpusi yo'q (git'ga kirmaydi)")
def test_corpus_lb_operations_import_without_loss():
    """Korxonaning real loyihalaridagi LB operatsiyalari (hisoblar — umumiy, mijoz ismlarisiz)."""
    n_xml = n_imp = 0
    for f in _CORPUS.rglob("*.project"):
        raw = f.read_bytes()
        k = raw.count(b'typeId="LB"')
        if not k:
            continue
        n_xml += k
        p, warnings = import_project(raw, "corpus.project")
        lbs = [o for o in p.operations if o.type.value == "LB"]
        assert len(lbs) == k
        for o in lbs:
            assert o.lb.columns >= 1 and o.lb.legacy_program.startswith("<?xml") and o.lb.width_mm > 5
        n_imp += len(lbs)
    assert n_xml == n_imp
