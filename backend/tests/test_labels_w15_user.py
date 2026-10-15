"""W15 · LB-D: `source=user` — «Пользовательские данные»: maydonlar sxemasi (tur/standart/tekshiruv), qatorlar (qty), Excel dan
qo'yilgan matn qiymatlarini turga keltirish, chop (HTML/ZPL), chegaralar va eski JSON mosligi."""
import re

import pytest

from app.models import LEGACY_CTX, LBParams
from app.services import label_user, label_vars


def tpl(*exprs):
    return {"v": 1, "size": {"w": 58, "h": 40},
            "elements": [{"t": "text", "x": 2, "y": 2 + 5 * i, "text": e, "size": 3} for i, e in enumerate(exprs)]}


def _lb(client, pid, **lb):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()
    oid = p["operations"][-1]["id"]
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": lb})
    return oid, r


def _html(client, pid, oid):
    r = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels")
    assert r.status_code == 200, r.text
    return r.text


# ───────────────────────── maydonlar sxemasi ─────────────────────────
def test_normalize_fields_cleans_and_defaults():
    out = label_user.normalize_fields([{"name": "a"}, {"name": "b_2", "title": "B sarlavha", "type": "double", "width": 90, "default": 1.5},
                                       {"name": "c", "type": "boolean", "default": True, "width": -5}, {"name": "d", "width": 10.0, "default": "1"}])
    assert out == [{"name": "a", "title": "a", "type": "string", "default": None},
                   {"name": "b_2", "title": "B sarlavha", "type": "double", "width": 90, "default": 1.5},
                   {"name": "c", "title": "c", "type": "boolean", "default": True},                 # yaroqsiz width tashlanadi
                   {"name": "d", "title": "d", "type": "string", "width": 10.0, "default": "1"}]     # musbat width o'zgartirilmaydi (.project importi)


@pytest.mark.parametrize("bad", [
    [{"name": "1a"}], [{"name": "a b"}], [{"name": "ism"}, {"name": "Шкаф"}], [{"name": ""}], [{"name": "x" * 32}], [{"name": "a"}, {"name": "a"}],
    [{"name": "a", "type": "color"}], ["a"], [{"title": "x"}], [{"name": "a", "default": [1]}], [{"name": f"f{i}"} for i in range(51)],
])
def test_normalize_fields_rejects(bad):
    with pytest.raises(ValueError):
        label_user.normalize_fields(bad)


def test_api_cleans_bad_fields_and_old_json_still_loads(client, kravat):
    """Har PATCH butun operatsiyani qayta tekshiradi: eski/yaroqsiz maydon operatsiyani buzmasligi shart — yaroqsizlari tashlanadi."""
    pid = kravat[0]
    oid, ok = _lb(client, pid, source="user", fields=[{"name": "title", "type": "string"}])
    assert ok.status_code == 200
    lb_of = lambda: next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["lb"]
    assert lb_of()["fields"][0] == {"name": "title", "title": "title", "type": "string", "default": None}
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"fields": [
        {"name": "bad name"}, {"name": "a", "type": "x"}, {"name": "a"}, {"title": "nomsiz"}, {"name": "ok", "type": "integer", "default": [1]}]}})
    assert r.status_code == 200
    assert lb_of()["fields"] == [{"name": "a", "title": "a", "type": "string", "default": None},
                                 {"name": "ok", "title": "ok", "type": "integer", "default": None}]   # noma'lum tur → string, takror/yaroqsiz tashlandi
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"width_mm": 70}}).status_code == 200      # boshqa maydon PATCH i ishlayveradi
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"fields": "x"}}).status_code == 422
    # bazadan yuklash (eski JSON): noto'g'ri maydon rad etilmaydi
    old = LBParams.model_validate({"source": "user", "fields": [{"name": "Eski nom", "x": 1}, {"name": "a"}, {"name": "a"}]}, context=LEGACY_CTX)
    assert len(old.fields) == 3
    assert list(label_user.user_field_specs(old.fields)) == ["a"]                                      # chopda: yaroqsizlari tashlanadi


def test_project_import_fields_are_sanitised_for_strict_validation():
    """`.project` dagi LB maydonlari: takror nom tashlanadi, noma'lum tur «string» — LBParams(**kw) import paytida yiqilmasin."""
    import base64
    from app.services import label_import
    xml = ('<fields><field name="a" type="Int" width="12"/><field name="a" type="string"/><field name="b" type="weird" default="x"/>'
           '<field name="Шкаф"/><field name="c" type="bool"/></fields>')
    raw = "BASE64:" + base64.b64encode(xml.encode()).decode()
    fs = label_import._fields(raw)
    assert [(f["name"], f["type"]) for f in fs] == [("a", "integer"), ("b", "string"), ("c", "boolean")]
    lb = LBParams(source="user", fields=fs)                                                              # qat'iy tekshiruvdan o'tadi
    assert [f["name"] for f in lb.fields] == ["a", "b", "c"] and lb.fields[0]["width"] == 12.0


# ───────────────────────── qiymatlarni turga keltirish ─────────────────────────
@pytest.mark.parametrize("v,tp,dv,want", [
    ("12", "integer", None, 12), (" 1 234 ", "integer", None, 1234), ("1 234,5", "double", None, 1234.5), ("3.0", "integer", None, 3),
    ("abc", "integer", None, 0), (None, "integer", 7, 7), ("", "double", "2,5", 2.5), ("x", "double", None, 0.0), (True, "integer", None, 1),
    ("да", "boolean", None, True), ("Yes", "boolean", None, True), ("1", "boolean", None, True), ("0", "boolean", None, False),
    ("нет", "boolean", None, False), (2, "boolean", None, True), (0, "boolean", None, False), (None, "boolean", True, True),
    (5, "string", None, "5"), (None, "string", None, ""), (None, "string", "std", "std"), (1.5, "string", None, "1.5"),
    (5, "any", None, 5), ("a", "any", None, "a"), (None, "any", None, ""), ([1], "any", None, "[1]"), ("a" * 2000, "string", None, "a" * 1000),
])
def test_coerce_user_value(v, tp, dv, want):
    assert label_user.coerce_user_value(v, tp, dv) == want
    assert type(label_user.coerce_user_value(v, tp, dv)) is type(want)


def test_excel_pasted_strings_work_in_arithmetic_and_conditions(client, kravat):
    """Excel dan qo'yilgan hamma qiymat matn: ifodada son/mantiqiy sifatida ishlashi uchun tur bo'yicha o'giriladi."""
    pid = kravat[0]
    oid, r = _lb(client, pid, source="user", border=False,
                 fields=[{"name": "nom", "type": "string"}, {"name": "narx", "type": "double"}, {"name": "soni", "type": "integer"},
                         {"name": "bor", "type": "boolean", "default": True}, {"name": "izoh", "type": "string", "default": "—"}],
                 data=[{"qty": "2", "nom": "Stol", "narx": "1 250,5", "soni": "3", "bor": "нет"}, {"qty": 1, "nom": "Stul", "narx": "100", "soni": 2}],
                 template=tpl("user.nom", "format('0.00', user.narx*user.soni)", "if(user.bor,'BOR','YOQ')", "user.izoh"))
    assert r.status_code == 200, r.text
    h = _html(client, pid, oid)
    assert h.count("class='lbl'") == 3                                                                   # qty: "2" (matn) → 2 nusxa + 1
    assert h.count(">Stol<") == 2 and h.count(">3751.50<") == 2 and h.count(">YOQ<") == 2               # 1250.5 × 3
    assert h.count(">Stul<") == 1 and h.count(">200.00<") == 1 and h.count(">BOR<") == 1               # bo'sh «bor» → standart (true)
    assert h.count(">—<") == 3                                                                          # bo'sh «izoh» → standart matn
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["user"] == 3
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()
    assert rows["total"] == 3 and [x["copy"] for x in rows["rows"]] == [1, 2, 1] and [x["copies"] for x in rows["rows"]] == [2, 2, 1]


def test_untyped_legacy_fields_pass_values_through(client, kravat):
    """Tur ko'rsatilmagan (eski) maydon: qiymat o'zgarmaydi — son soni qoladi (avvalgi xulq)."""
    pid = kravat[0]
    fields = [{"name": "n"}]
    specs = label_user.user_field_specs(fields)
    assert specs == {"n": ("any", None)}
    p = LBParams.model_validate({"source": "user", "fields": fields, "data": [{"n": 5}, {"n": "x"}]}, context=LEGACY_CTX)
    from app import store
    eb = label_vars.EnvBuilder(store.load(pid), p, 2)
    items = list(label_vars.iter_items(eb.project, p))
    assert [eb.env(it)["user.n"] for it in items] == [5, "x"]


def test_missing_values_use_defaults_or_typed_zero():
    p = LBParams.model_validate({"source": "user", "fields": [{"name": "a", "type": "integer"}, {"name": "b", "type": "string", "default": "std"},
                                                              {"name": "c", "type": "boolean"}, {"name": "d", "type": "double"}], "data": [{}]})
    project, _cs = label_vars.sample_project()
    eb = label_vars.EnvBuilder(project, p, 1)
    e = eb.env(next(label_vars.iter_items(project, p)))
    assert (e["user.a"], e["user.b"], e["user.c"], e["user.d"]) == (0, "std", False, 0.0)
    assert e["label.kind"] == "user" and e["part.copy"] == 1 and e["part.copies"] == 1


def test_qty_variants_and_limits(client, kravat):
    pid = kravat[0]
    base = dict(source="user", fields=[{"name": "a", "type": "string"}], template=tpl("user.a"))
    cases = [([{"a": "x"}], 1), ([{"a": "x", "qty": 0}], 0), ([{"a": "x", "qty": "abc"}], 1), ([{"a": "x", "qty": 2.9}], 2), ([{"a": "x", "qty": 3}, {"a": "y", "qty": 4}], 7)]
    for data, n in cases:
        oid, r = _lb(client, pid, data=data, **base)
        assert r.status_code == 200
        assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == n, data
    oid, _ = _lb(client, pid, data=[{"a": "x", "qty": 10000}], **base)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels").status_code == 200           # 10 000 — chegara
    oid, _ = _lb(client, pid, data=[{"a": "x", "qty": 10001}], **base)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels").status_code == 422             # 10 001 — rad etiladi
    pv = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {**base, "data": [{"a": "x", "qty": 10001}]}}).json()
    assert pv["total"] == 10001 and pv["rendered"] == 6 and pv["truncated"]                              # ko'rish ishlayveradi
    big = [{"a": str(i)} for i in range(10000)]
    oid, r = _lb(client, pid, data=big, **base)
    assert r.status_code == 200
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"data": big + [{"a": "x"}]}}).status_code == 422     # ≤ 10 000 qator


def test_user_text_is_escaped_in_html(client, kravat):
    pid = kravat[0]
    oid, _ = _lb(client, pid, source="user", fields=[{"name": "a", "type": "string"}], data=[{"a": "<b>x</b>\"'&"}], template=tpl("user.a"))
    h = _html(client, pid, oid)
    assert "<b>x</b>" not in h and "&lt;b&gt;x&lt;/b&gt;" in h


def test_xml_invalid_characters_in_user_data_do_not_break_svg_html_or_zpl(client, kravat):
    """Yakka surrogat (JSON «\\ud800») va U+FFFE — XML/UTF-8 uchun yaroqsiz: chop/ko'rinish/ZPL yiqilmasligi shart (bo'sh joyga almashtiriladi)."""
    import json
    import xml.etree.ElementTree as ET
    pid = kravat[0]
    hdr = {"Content-Type": "application/json"}
    lb = {"source": "user", "fields": [{"name": "a", "type": "string"}], "data": [{"a": "x\ud800y￾z"}], "template": tpl("user.a")}
    r = client.post(f"/api/projects/{pid}/lb/labels", content=json.dumps(lb), headers=hdr)            # json.dumps: lone surrogate → «\ud800» escape
    assert r.status_code == 200 and "x y z" in r.text
    body = {"template": tpl("user.a"), "kind": "user", "fields": lb["fields"], "row": lb["data"][0]}
    d = client.post("/api/label-templates/design", content=json.dumps(body), headers=hdr)
    assert d.status_code == 200
    ET.fromstring(d.json()["svg"])                                                                    # to'g'ri XML (redaktor DOMParser i yiqilmaydi)
    z = client.post(f"/api/projects/{pid}/lb/labels/zpl", content=json.dumps({"lb": lb}), headers=hdr)
    assert z.status_code == 200 and "^FDx y z^FS" in z.content.decode("utf-8")


def test_unknown_user_variable_is_an_error_not_silent(client, kravat):
    pid = kravat[0]
    oid, _ = _lb(client, pid, source="user", fields=[{"name": "a", "type": "string"}], data=[{"a": "x"}], template=tpl("user.zzz"))
    pv = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"source": "user", "fields": [{"name": "a"}], "data": [{"a": "x"}], "template": tpl("user.zzz")}}).json()
    assert pv["errors"] and "user.zzz" in pv["errors"][0]["message"] and "#ERR" in pv["html"]


def test_sample_env_user_uses_field_titles_and_types():
    lb = LBParams(source="user", fields=label_user.normalize_fields([{"name": "t", "title": "Sarlavha", "type": "string"}, {"name": "n", "type": "integer"},
                                                                    {"name": "b", "type": "boolean"}, {"name": "d", "type": "string", "default": "std"}]))
    e = label_vars.sample_env("user", "ru", lb)
    assert (e["user.t"], e["user.n"], e["user.b"], e["user.d"]) == ("Sarlavha", 1, True, "std")
    e = label_vars.sample_env("user", "ru", lb, {"t": "Q", "n": "9"})
    assert (e["user.t"], e["user.n"], e["user.b"]) == ("Q", 9, False)
    e = label_vars.sample_env("user", "ru", LBParams(source="user", data=[{"x": 1}]))
    assert e["label.kind"] == "user"


def test_user_source_works_with_every_print_mode_and_zpl(client, kravat):
    pid = kravat[0]
    lb = dict(source="user", fields=[{"name": "a", "type": "string"}], data=[{"a": "1", "qty": 3}], template=tpl("user.a"))
    oid, _ = _lb(client, pid, mode="roll", **lb)
    assert _html(client, pid, oid).count("class='pg'") == 3
    oid, _ = _lb(client, pid, mode="sheet", columns=2, rows=1, **lb)
    assert _html(client, pid, oid).count("class='pg'") == 2                                                # 3 etiketka / (2 × 1) = 2 sahifa
    z = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl").content.decode()
    assert z.count("^XA") == 3 and len(re.findall(r"\^FD1\^FS", z)) == 3
