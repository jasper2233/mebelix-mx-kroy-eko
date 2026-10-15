"""W9 · LB-D: shablonni `<program>` XML ga qaytarish (eksport) — moslik jadvali, ogohlantirishlar, round-trip (import → eksport →
import natijasi teng), API. Fikstura sintetik (w9_fixture.py)."""
import copy

import pytest
from w9_fixture import data_uri, el, png, program, sample_program, text

from app.services import label_builtin, label_tpl
from app.services import label_gl_common as C
from app.services import label_gl_export as GE
from app.services import label_gl_import as GI


def conv(xml):
    return GI.convert_program(xml, "T")


def export(tpl, layout=None):
    r = GE.export_program(tpl, layout)
    root = C.safe_fromstring(r.xml)                          # chiqish — xavfsiz parser o'qiy oladigan, DTD siz XML
    assert root.tag == "program" and r.xml.startswith('<?xml version="1.0" encoding="UTF-8"?><program ')
    return r, root


def wmap(r):
    return {(w["code"], w["key"]): w["count"] for w in r.warnings}


def tpl_of(elements, **kw):
    t = {"v": 1, "name": "T", "size": {"w": 60, "h": 40}, "params": [], "vars": [], "elements": elements}
    t.update(kw)
    return t


def kids(root, tag):
    return [e for e in root.iter(tag)]


# ───────────────────────── moslik jadvali ─────────────────────────
def test_every_element_type_is_written():
    els = [
        {"t": "text", "x": 2, "y": 3, "text": "'Salom'", "size": 3, "bold": True, "italic": True, "color": "#ff0000", "font": "mono"},
        {"t": "text", "x": "label.width/2.0", "y": 8, "text": "part.name", "size": 2.5, "maxw": "label.width", "align": "center"},
        {"t": "text", "x": 40, "y": 12, "text": "part.dims", "size": 2.5, "maxw": 20, "align": "right"},
        {"t": "text", "x": 2, "y": 16, "text": "part.title", "size": 2.5, "maxw": 30, "wrap": True, "lines": 3, "line_h": 3},
        {"t": "rect", "x": 1, "y": 1, "w": 10, "h": 5, "stroke": {"w": 0.4, "color": "#00f"}, "fill": "#eee"},
        {"t": "line", "x1": 2, "y1": 20, "x2": 32, "y2": 20, "stroke": {"w": 0.3}},
        {"t": "line", "x1": 5, "y1": 2, "x2": 5, "y2": 18},
        {"t": "image", "x": 40, "y": 20, "w": 8, "h": 8, "src": data_uri(png())},
        {"t": "barcode", "kind": "qr", "x": 40, "y": 2, "size": 15, "data": "label.code"},
        {"t": "part", "x": 30, "y": 5, "w": 20, "h": 14},
        {"t": "if", "cond": "edge.count > 0", "then": [{"t": "text", "x": 1, "y": 1, "text": "'yes'"}],
         "else": [{"t": "text", "x": 1, "y": 1, "text": "'no'"}]},
        {"t": "var", "name": "v1", "expr": "part.qty*2"},
    ]
    r, root = export(tpl_of(els, params=[{"name": "p", "type": "double", "default": 2, "title": "Param"}]))
    assert r.warnings and not {"barcode", "line"} & {w["code"] for w in r.warnings}
    # asosiy turlar: 4 text + if-ichidagi 2 text, 1 rect + 2 chiziq (rect), qrcode, part, image
    assert len(kids(root, "text")) == 6 and len(kids(root, "rect")) == 3 and len(kids(root, "qrcode")) == 1
    assert len(kids(root, "part")) == 1 and len(kids(root, "image")) == 1
    t0 = kids(root, "text")[0]
    assert (t0.get("x"), t0.get("y"), t0.get("fontName"), t0.get("fontBold"), t0.get("fontItalic"), t0.get("fillColor")) == \
        ("2", "5.46", "Courier New", "true", "true", "#FF0000")                      # y: yuqori chet 3 → asosiy chiziq 3 + 3·0.82
    assert t0.get("enable") == "true" and t0.get("w") is None and t0.get("ratio") == "false"
    c, rt, wr = kids(root, "text")[1:4]
    assert (c.get("x"), c.get("w"), c.get("align"), c.get("ratio")) == ("0", "dx", "center", "true")     # x = w/2 → qutining chap chetiga qaytdi
    assert (rt.get("x"), rt.get("w"), rt.get("align")) == ("20", "20", "right")                     # 40 - 20
    assert (wr.get("multiline"), wr.get("wordBreak"), wr.get("h"), wr.get("rowHeight")) == ("true", "true", "9", "3")
    rect = kids(root, "rect")[0]
    assert (rect.get("strokeColor"), rect.get("strokeWidth"), rect.get("fillColor")) == ("#0000FF", "0.4", "#EEEEEE")
    h_line, v_line = kids(root, "rect")[1:3]
    assert (h_line.get("x"), h_line.get("y"), h_line.get("w"), h_line.get("h")) == ("2", "20", "30", "0")
    assert (v_line.get("x"), v_line.get("y"), v_line.get("w"), v_line.get("h")) == ("5", "2", "0", "16")
    assert kids(root, "image")[0].get("imgdata").startswith("data:image/png;base64,")
    qr = kids(root, "qrcode")[0]
    assert (qr.get("sz"), qr.get("text")) == ("15", "label.code")                                    # MebeliX nomi (ogohlantirish bilan)
    iff = kids(root, "if")[0]
    els_ = [e for e in root if e.tag == "else"]
    assert iff.get("condition") == "edge.count > 0" and len(els_) == 1 and els_[0].get("expand") == "true"
    var = [v for v in kids(root, "var") if v.get("name") == "v1"][0]
    assert var.get("expr") == "count*2" and var.get("type") == "double"                              # part.qty → count
    par = [p for p in kids(root, "par") if p.get("name") == "p"][0]
    assert (par.get("type"), par.get("expr"), par.get("comment")) == ("double", "2", "Param")


def test_non_matching_elements_are_skipped_or_approximated_with_warnings():
    els = [
        {"t": "barcode", "kind": "code128", "x": 1, "y": 1, "w": 30, "h": 8, "data": "part.id"},
        {"t": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 10},                                         # qiyshiq
        {"t": "edges", "x": 30, "y": 5, "w": 14, "h": 9},
        {"t": "group", "rotate": 90, "origin": [5, 5], "elements": [{"t": "text", "x": 0, "y": 0, "text": "'r'"}]},
        {"t": "text", "x": 1, "y": 1, "text": "'t'", "rotate": 90},
        {"t": "rect", "x": 1, "y": 1, "w": 5, "h": 5, "radius": 2},
        {"t": "barcode", "kind": "qr", "x": 1, "y": 1, "size": 10, "data": "'a'", "rotate": 90},
        {"t": "text", "x": 1, "y": 1, "text": "'b'", "bold": "part.groove"},
    ]
    r, root = export(tpl_of(els))
    w = wmap(r)
    assert w[("barcode", "1")] == 1 and w[("line", "2")] == 1 and w[("edges", "3")] == 1 and w[("group_rot", "4")] == 1
    assert w[("rotate", "5")] == 1 and w[("radius", "6")] == 1 and w[("rotate", "7")] == 1 and w[("skipped", "bold (expr)")] == 1
    assert len(kids(root, "part")) == 1                                       # edges → part (eng yaqin element)
    assert len(kids(root, "qrcode")) == 1 and len(kids(root, "rect")) == 1    # code128, qiyshiq chiziq va burilgan guruh — yozilmadi
    assert all(isinstance(x["message"], str) and x["message"] for x in r.warnings)


def test_group_origin_becomes_xy_and_zero_origin_is_inlined():
    els = [{"t": "text", "x": 1, "y": 1, "text": "'a'"},
           {"t": "group", "origin": [4, "label.height/2.0"], "elements": [{"t": "text", "x": 0, "y": 0, "text": "'g'"}]}]
    r, root = export(tpl_of(els))
    tags = [e.tag for e in root]
    assert tags == ["text", "xy", "text"] and root[1].get("x") == "4" and root[1].get("y") == "dy/2.0"
    assert ("xy_scope", "2") not in wmap(r)                                  # guruh oxirgi — ogohlantirish yo'q
    r, root = export(tpl_of([{"t": "group", "origin": [4, 4], "elements": []}, {"t": "text", "x": 1, "y": 1, "text": "'z'"}]))
    assert ("xy_scope", "1") in wmap(r)                                      # keyingi aka-uka ham siljiydi — ogohlantirish
    r, root = export(tpl_of([{"t": "group", "origin": [0, 0], "elements": [{"t": "text", "x": 1, "y": 1, "text": "'z'"}]}]))
    assert [e.tag for e in root] == ["text"]


def test_variable_names_are_mapped_back_and_declared():
    els = [{"t": "text", "x": 1, "y": 1, "text": "part.thickness+edge.top.symbol+xnc1.code+waste.business+product.qty+part.uid",
            "size": "label.height/10.0"},
           {"t": "text", "x": 1, "y": 5, "text": "part.title+label.number"}]
    r, root = export(tpl_of(els, vars=[{"name": "k", "expr": "label.width*2", "type": "double"}]))
    t1 = kids(root, "text")[0]
    assert t1.get("text") == "thick+ets+XNC1+business+product.count+part.id" and t1.get("fontSize") == "dy/10.0"
    assert kids(root, "var")[0].get("expr") == "dx*2"
    pars = {p.get("name"): p.get("type") for p in kids(root, "par")}
    assert pars == {"thick": "double", "ets": "string", "XNC1": "string", "business": "boolean", "product.count": "integer",
                    "part.id": "integer"}                                 # ishlatilgan standart nomlar e'loni; dx/dy — e'lonsiz
    assert all(p.get("expr") in ("", "0", "false") for p in kids(root, "par"))      # sinov qiymati neytral (hech qanday namuna matni yo'q)
    w = wmap(r)
    assert w[("var", "part.title")] == 1 and w[("var", "label.number")] == 1       # faqat MebeliX da bor nomlar
    assert not any(k[0] == "var" and k[1] in ("thick", "dx") for k in w)


def test_user_names_params_and_vars_are_not_remapped():
    t = tpl_of([{"t": "text", "x": "margin", "y": 1, "text": "name+x"}],
               params=[{"name": "margin", "type": "double", "default": 1.5, "title": ""}, {"name": "name", "type": "string", "default": "A"}],
               vars=[{"name": "x", "expr": "margin*2"}])
    r, root = export(t)
    assert kids(root, "text")[0].get("text") == "name+x" and kids(root, "text")[0].get("x") == "margin"
    assert [p.get("name") for p in kids(root, "par")] == ["margin", "name"]        # `name` — foydalanuvchi parametri: e'lon takrorlanmaydi
    assert wmap(r)[("type", "")] == 1                                              # tur avtomatik aniqlandi (bitta umumiy ogohlantirish)


@pytest.mark.parametrize("expr_text,want", [
    ("5", "double"), ("'abc'", "string"), ("'P-'+part.id", "string"), ("a>1", "boolean"), ("not empty(etn)", "boolean"),
    ("empty(etn)", "boolean"), ("format('0',length)", "string"), ("if(waste,'a','b')", "string"), ("if(waste,1,2)", "double"),
    ("etn", "string"), ("business", "boolean"), ("length*2", "double"), ("true", "boolean"), ("1 $ 2", "string"),
])
def test_var_type_inference(expr_text, want):
    t = tpl_of([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], vars=[{"name": "v", "expr": expr_text}])
    r, root = export(t)
    assert kids(root, "var")[0].get("type") == want


def test_layout_attributes():
    t = tpl_of([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], size={"w": 58.5, "h": 40})
    _r, root = export(t)                                                           # layout yo'q — standart
    assert root.attrib == {"columns": "3", "dx": "58.5", "dy": "40", "gap": "2", "margin": "true", "printMode": "0", "rows": "0"}
    _r, root = export(t, {"mode": "roll", "columns": 2, "rows": 4, "gap_mm": 10.5, "margin_mm": None, "width_mm": 89, "height_mm": 60.25})
    assert root.attrib == {"columns": "2", "dx": "89", "dy": "60.25", "gap": "10.5", "margin": "false", "printMode": "1", "rows": "4"}
    t["layout"] = {"mode": "sheet", "columns": 4, "rows": 2, "gap_mm": 1, "margin_mm": 6.0}                  # shablon ichidagi maslahat
    _r, root = export(t)
    assert (root.get("columns"), root.get("rows"), root.get("gap"), root.get("margin")) == ("4", "2", "1", "true")


def test_output_is_wellformed_for_hostile_text():
    t = tpl_of([{"t": "text", "x": 1, "y": 1, "text": "'<&\">' + \"x'y\"", "comment": "a\x00b\x07<c>&Ж"},
                {"t": "text", "x": 1, "y": 2, "text": "'\x01ok'"}],
               params=[{"name": "p", "type": "string", "default": "q\x08<>&\"'", "title": "T\x0b"}])
    r, root = export(t)
    assert "\x00" not in r.xml and "\x07" not in r.xml and "<!DOCTYPE" not in r.xml and "<!ENTITY" not in r.xml
    assert kids(root, "text")[0].get("comment") == "ab<c>&Ж"


def test_invalid_template_is_a_clear_error():
    with pytest.raises(C.GLError):
        GE.export_program({"elements": [{"t": "nope"}]})
    with pytest.raises(C.GLError):
        GE.export_program([])


# ───────────────────────── round-trip ─────────────────────────
def strip(t):
    t = copy.deepcopy(t)
    t.pop("name", None)
    return t


def rich_program():
    """Ifodali koordinatalar, o'ng/markaz tekislash (x, w — ifoda), ichma-ich if/else, ichidagi var, xy (ifoda), ko'p qatorli matn,
    turli tur par/var, printMode=1."""
    body = [
        text("la", "3", "'R'", w="la3", align="right", fontSize="2.2"),
        text("10", "5", "name", w="w2", align="center", fontBold="true"),
        text("l1-8", "9", "ucase(name)", w="12", align="center", fillColor="#00AA00"),
        text("2", "la-20", "'E'", fontSize="fs2"),                                   # o'lcham ham, y ham ifoda
        text("2", "w2+1", "'F'"),
        text("1", "12", "description", w="30", multiline="true", wordBreak="true", rowHeight="2.5", h="7.5", fontName="Courier New"),
        text("1", "20", "description", w="30", wordBreak="true"),
        el("rect", enable="true", x="1", y="la-3", w="la3", h="0", strokeColor="#112233", strokeWidth="0.5", strokeDash="0", fillColor="",
           fillHatch="1"),
        el("rect", enable="true", x="1", y="1", w="0", h="l1", strokeColor="#000000", strokeWidth="0.25", strokeDash="0", fillColor="",
           fillHatch="1"),
        el("rect", enable="true", x="30", y="30", w="la3/2", h="4", strokeColor="#000000", strokeWidth="0", strokeDash="0",
           fillColor="#FFFFFF", fillHatch="8"),
        el("image", enable="true", x="l1", y="1", w="6", h="6", imgdata=data_uri(png(3, 3)), ratio="true", expr=""),
        el("qrcode", enable="true", x="2", y="la/2", sz="12", text="'Q-'+part.id", fillColor="#223344"),
        el("if", [
            el("var", name="tmp", type="string", expr="'a'+part.id"),
            text("1", "40", "tmp", w="20"),
            el("if", [text("2", "41", "'deep'")], condition="empty(etn) and not waste"),
            el("else", [text("3", "41", "'deep-else'")]),
        ], condition="show_extra", comment="Qo'shimcha", expand="true"),
        el("else", [text("1", "42", "'plain'")], expand="true"),
    ]
    children = [
        el("par", name="show_extra", type="boolean", expr="true", comment="Qo'shimcha"),
        el("par", name="scale", type="double", expr="1.25"),
        el("par", name="count_n", type="integer", expr="4"),
        el("par", name="label_title", type="string", expr="Sarlavha"),
        el("par", name="etn", type="string", expr=""),
        el("var", name="la3", type="double", expr="dx-6", comment="Kenglik"),
        el("var", name="w2", type="double", expr="12"),
        el("var", name="fs2", type="double", expr="2.5"),
        el("var", name="l1", type="double", expr="la3/3"),
        el("var", name="la", type="double", expr="dx-2"),
        el("var", name="s", type="string", expr="'ab'+label_title"),
        el("var", name="flag", type="boolean", expr="scale>1"),
        el("xy", enable="true", x="0.5", y="la3/10"),
        *body,
    ]
    return program(children, columns="2", rows="4", gap="10", margin="false", printMode="1", dx="89", dy="60.25")


@pytest.mark.parametrize("xml", [sample_program(), rich_program()], ids=["sample", "rich"])
def test_round_trip_import_export_import_is_equal(xml):
    r1 = conv(xml)
    assert not [w for w in r1.warnings if w["code"] in ("tag", "unknown_var", "skipped", "orphan_else")], r1.warnings
    ex = GE.export_program(r1.template)
    r2 = conv(ex.xml)
    assert strip(r2.template) == strip(r1.template)
    ex2 = GE.export_program(r2.template)
    assert ex2.xml == ex.xml                                                       # eksport takrorlanuvchi (idempotent)
    assert r2.template["layout"] == r1.template["layout"] and r2.template["size"] == r1.template["size"]
    assert label_tpl.normalize_template(r2.template) == r2.template
    # qayta import yangi turdagi ogohlantirish chiqarmaydi (birinchi importda yo'qolgan narsa — dash, par_expr — endi yo'q)
    assert {w["code"] for w in r2.warnings} <= {w["code"] for w in r1.warnings}


def test_rich_round_trip_keeps_semantics_in_render():
    """Eksport/importdan keyin ham shablon bir xil SVG beradi (namuna ma'lumot bilan)."""
    from app.services import label_vars
    r1 = conv(rich_program())
    r2 = conv(GE.export_program(r1.template).xml)
    env = label_vars.sample_env("part")
    a = label_tpl.Renderer(r1.template, width_mm=89, height_mm=60.25, params={"scale": 2}).render(dict(env))
    b = label_tpl.Renderer(r2.template, width_mm=89, height_mm=60.25, params={"scale": 2}).render(dict(env))
    assert a == b and "#ERR" not in a


def test_builtin_templates_export_and_reimport():
    for key in ("detail", "detail_c128", "waste", "product"):
        t = label_builtin.builtin_template(key, "ru")
        r = GE.export_program(t)
        assert "label.width" not in r.xml and "label.height" not in r.xml          # o'lcham o'zgaruvchilari dx/dy ga qaytarilgan
        again = conv(r.xml)                                                        # eksport fayli qayta o'qiladi
        assert again.info["elements"] >= 5 and again.template["size"] == t["size"]
        w = {c: k for c, k in ((x["code"], x["key"]) for x in r.warnings)}
        assert ("edges" in w) == (key == "detail") and ("barcode" in w) == (key == "detail_c128")
        if key == "detail_c128":
            assert wmap(r)[("barcode", "10")] == 1                                 # Code128 — o'tkazib yuborildi
        if key == "detail":
            assert wmap(r)[("edges", "3.then.8.then.1")] == 1                      # kromka sxemasi → part (eng yaqin element)


# ───────────────────────── API ─────────────────────────
def test_api_export_xml_with_layout_and_reimport(client):
    t = conv(sample_program()).template
    r = client.post("/api/labels/export-xml", json={"template": t, "layout": {"mode": "sheet", "columns": 2, "rows": 3, "gap_mm": 4,
                                                                                "margin_mm": 5, "width_mm": 70, "height_mm": 50}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["filename"] == "T.xml" and d["xml"].startswith("<?xml") and isinstance(d["warnings"], list)
    root = C.safe_fromstring(d["xml"])
    assert (root.get("columns"), root.get("rows"), root.get("gap"), root.get("dx"), root.get("dy")) == ("2", "3", "4", "70", "50")
    # fayl sifatida qayta yuklash — shu tizimning o'zida o'qiladi va teng
    up = client.post("/api/labels/import-file", files={"file": ("chiqish.xml", d["xml"].encode("utf-8"))})
    assert up.status_code == 200, up.text
    it = up.json()["items"][0]
    assert strip(it["template"]) == strip({**t, "layout": {"mode": "sheet", "columns": 2, "rows": 3, "gap_mm": 4.0, "margin_mm": 6.0}})
    assert it["layout"]["columns"] == 2 and it["layout"]["rows"] == 3


def test_api_export_xml_rejects_bad_input(client):
    assert client.post("/api/labels/export-xml", json={"template": {"elements": [{"t": "zzz"}]}}).status_code == 422
    assert client.post("/api/labels/export-xml", json={"template": [1, 2]}).status_code == 422
    assert client.post("/api/labels/export-xml", json={"template": {"elements": []}, "layout": {"columns": 99}}).status_code == 422


def test_api_export_xml_of_library_and_builtin(client):
    r = client.get("/api/label-templates/builtin:detail/export-xml")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert "attachment" in r.headers["content-disposition"] and r.headers["content-disposition"].endswith(".xml")
    assert int(r.headers["x-export-warnings"]) >= 1
    assert C.safe_fromstring(r.text).tag == "program"
    # kutubxona profili (kirill nom) — sarlavha ASCII (RFC 5987)
    save = client.post("/api/settings/label_template", json={"name": "Деталь №1", "data": conv(sample_program()).template}).json()
    r2 = client.get(f"/api/label-templates/profile:{save['id']}/export-xml")
    assert r2.status_code == 200 and "UTF-8''" in r2.headers["content-disposition"]
    assert C.safe_fromstring(r2.text).get("dx") == "70"
    assert client.get("/api/label-templates/builtin:nope/export-xml").status_code == 404


def test_api_export_warnings_follow_language(client):
    t = {"elements": [{"t": "barcode", "kind": "code128", "x": 1, "y": 1, "w": 30, "h": 8, "data": "'1'"}]}
    uz = client.post("/api/labels/export-xml", json={"template": t}, headers={"Accept-Language": "uz"}).json()["warnings"][0]["message"]
    ru = client.post("/api/labels/export-xml", json={"template": t}, headers={"Accept-Language": "ru"}).json()["warnings"][0]["message"]
    assert "o'tkazib yuborildi" in uz and "пропущен" in ru

