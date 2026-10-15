"""W9 · LB-D: tayyor shablon faylini (`<program>` XML) W4 JSON shabloniga o'giruvchi importyor — element turlari, ogohlantirishlar,
xavfsizlik, `.project` ichidan LB olish, API (`POST /api/labels/import-file`). Fikstura sintetik (w9_fixture.py)."""
import base64
import json

import pytest
from w9_fixture import data_uri, el, png, program, sample_program, text

from app.services import label_gl_common as C
from app.services import label_gl_import as GI
from app.services import label_tpl, label_vars

NS = {}                                                  # (bo'sh; xml nom maydoni kerak emas)


def conv(xml, name="T"):
    return GI.convert_program(xml, name)


def warn_map(res):
    return {(w["code"], w["key"]): w["count"] for w in res.warnings}


def by_t(els, t):
    return [e for _p, e in label_tpl.walk(els) if e.get("t") == t]


# ───────────────────────── element turlari ─────────────────────────
def test_header_size_layout_and_params():
    r = conv(sample_program())
    t = r.template
    assert t["name"] == "T" and t["size"] == {"w": 70, "h": 50}
    assert t["layout"] == {"mode": "sheet", "columns": 3, "rows": 5, "gap_mm": 2, "margin_mm": 6.0}
    # standart nomli par (part.code, part.id, waste, etn) — sinov qiymati: o'tkazib yuboriladi; boshqalari — parametr
    assert [(p["name"], p["type"], p["default"], p["title"]) for p in t["params"]] == [
        ("gap2", "double", 2.5, "Ichki oraliq"), ("show_logo", "boolean", True, "Logo"), ("tag", "string", "HELLO", ""),
        ("copies_n", "integer", 3, "")]
    assert r.info["std_pars"] == 4
    # standart qiymatdan farqli: ifodali par — o'zgaruvchiga aylanadi (ogohlantirish bilan)
    names = [v["name"] for v in t["vars"]]
    assert names == ["calc_par", "inner", "la2", "prefix"]
    v = {x["name"]: x for x in t["vars"]}
    assert v["inner"] == {"name": "inner", "expr": "label.width-gap2*2", "type": "double", "comment": "Ichki eni"}   # dx → label.width
    assert v["la2"]["expr"] == "label.width-4" and v["prefix"]["expr"] == "'P-'" and v["calc_par"]["expr"] == "label.width/2"
    assert warn_map(r)[("par_expr", "calc_par")] == 1


def test_par_named_like_our_alias_is_a_user_param():
    """`qty` — bizning taxallus (fayl formati nomi emas): foydalanuvchi parametri sifatida saqlanadi, qiymati chopda ustun turadi."""
    xml = program([el("par", name="qty", type="integer", expr="9"), el("par", name="part.qr", type="string", expr="z"),
                   el("par", name="count", type="integer", expr="1"), text("1", "5", "'n='+qty")])
    r = conv(xml)
    assert [(p["name"], p["default"]) for p in r.template["params"]] == [("qty", 9)] and r.info["std_pars"] == 2
    svg = label_tpl.Renderer(r.template, width_mm=58, height_mm=40, params={"qty": 5}).render(label_vars.sample_env("part"))
    assert "n=5" in svg


def test_xy_becomes_group_with_following_siblings():
    t = conv(sample_program()).template
    assert len(t["elements"]) == 1 and t["elements"][0]["t"] == "group" and t["elements"][0]["origin"] == [1, 2]
    top = t["elements"][0]["elements"]
    assert [e["t"] for e in top] == ["if"]                                     # if + (else — aka-uka) bitta `if` ga yig'ildi
    assert top[0]["cond"] == "not waste" and "else" in top[0] and len(top[0]["else"]) == 1


def test_zero_xy_is_dropped():
    t = conv(program([el("xy", enable="true", x="0", y="0"), text("1", "1", "'a'")])).template
    assert [e["t"] for e in t["elements"]] == ["text"]
    t = conv(program([el("xy", enable="false", x="9", y="9"), text("1", "1", "'a'")]))
    assert [e["t"] for e in t.template["elements"]] == ["text"] and warn_map(t)[("disabled", "xy")] == 1


def test_text_variants():
    t = conv(sample_program()).template
    texts = [e for e in by_t(t["elements"], "text")]
    title, center, right, wrapped = texts[0], texts[1], texts[2], texts[3]
    assert title == {"t": "text", "x": 2, "y": 0.54, "text": "'Title'", "size": 3, "maxw": 30, "bold": True}   # y: asosiy chiziq 3 → yuqori chet 3 − 3·0.82
    # markazga tekislash: x = x + w/2 (w — ifoda: «inner»); matn qatori ifoda sifatida o'tadi; Courier → mono; rang; kursiv; izoh
    assert center["x"] == "inner/2.0" and center["maxw"] == "inner" and center["align"] == "center"
    assert center["font"] == "mono" and center["color"] == "#ff0000" and center["italic"] is True and center["comment"] == "centered"
    assert center["text"] == "ns(part.code)" and center["size"] == 2.5
    # o'ngga: x + w (sonlar — son); butun son 10 + 20 = 30
    assert right["x"] == 30 and right["maxw"] == 20 and right["align"] == "right"
    # ko'p qatorli: wrap, lines = h // rowHeight
    assert wrapped["wrap"] is True and wrapped["lines"] == 3 and wrapped["line_h"] == 3 and wrapped["maxw"] == 30


def test_text_y_is_baseline_not_top():
    """Faylda matn y si — asosiy chiziq: matn tagiga tortilgan chiziq (y+1) matnni kesib o'tmasligi uchun. Bizda y — yuqori chet."""
    xml = program([text("3", "30", "'Edge'", fontSize="2.5", w="25", align="right"),
                   el("rect", enable="true", x="3", y="31", w="25", h="0", strokeColor="#000000", strokeWidth="0.5", strokeDash="0",
                      fillColor="", fillHatch="1"),
                   text("1", "10 + k", "'v'", fontSize="fs"),
                   el("var", name="fs", type="double", expr="2"), el("var", name="k", type="double", expr="5")])
    els = conv(xml).template["elements"]
    t1, line, t2 = els
    assert t1["y"] == 27.95 and t1["size"] == 2.5
    assert t2["y"] == "(10 + k)-(fs*0.82)"                                      # ifodali o'lcham — ifoda shaklida
    svg = label_tpl.Renderer(label_tpl.normalize_template({"elements": els[:1]}), width_mm=58, height_mm=40).render(label_vars.sample_env("part"))
    assert 'y="30"' in svg                                                       # SVG da asosiy chiziq — faylning y si
    assert line["y1"] == 31 and 30 < line["y1"] < 30 + 2.5                       # chiziq asosiy chiziq tagida


def test_qrcode_rect_line_image_part():
    r = conv(sample_program())
    els = r.template["elements"][0]["elements"][0]["then"]
    qr = by_t(els, "barcode")[0]
    assert qr == {"t": "barcode", "kind": "qr", "x": 45, "y": 2, "size": 18, "data": "'ID-'+part.id"}
    line = by_t(els, "line")[0]                                              # h=0 → gorizontal chiziq
    assert (line["x1"], line["y1"], line["x2"], line["y2"]) == (2, 30, 32, 30)
    assert line["stroke"] == {"w": 0.3, "color": "#ff0000"}                  # rgb(...) → #hex
    rect = by_t(els, "rect")[0]
    assert rect == {"t": "rect", "x": 2, "y": 32, "w": 20, "h": 8, "stroke": {"w": 0.25, "color": "#000000"}, "fill": "#eeeeee"}
    img = by_t(els, "image")[0]
    assert img["src"].startswith("data:image/png;base64,") and (img["x"], img["y"], img["w"], img["h"]) == (50, 30, 8, 8)
    part = by_t(els, "part")[0]
    assert part == {"t": "part", "x": 40, "y": 22, "w": 18, "h": 24}
    w = warn_map(r)
    assert w[("part", "part")] == 1 and w[("dash", "rect")] == 1 and w[("hatch", "rect")] == 1 and w[("multiline", "text")] == 1


def test_converted_template_is_valid_and_renders():
    t = conv(sample_program()).template
    assert label_tpl.normalize_template(t) == t                              # normallashgan, qayta o'qiladi
    chk = label_tpl.check_template(t)
    assert chk["errors"] == [], chk["errors"]
    svg = label_tpl.Renderer(t, width_mm=70, height_mm=50).render(label_vars.sample_env("part"))
    assert "<text" in svg and "<image" in svg and "<line" in svg


def test_waste_rows_use_waste_dimensions_for_short_names():
    """Qoldiq qatorida length/width/indexInOperation — qoldiq o'lchami va raqami (W9 taxalluslari)."""
    env = label_vars.sample_env("waste")
    assert env["length"] == env["waste.length"] > 0 and env["width"] == env["waste.width"]
    assert env["indexInOperation"] == env["waste.number"]
    e2 = label_vars.sample_env("part")
    assert e2["indexInOperation"] == e2["part.index"] and "grtc" in e2 and "grtn" in e2


# ───────────────────────── ogohlantirishlar ─────────────────────────
def test_unsupported_tags_attrs_disabled_and_skipped_are_counted():
    xml = program([
        text("1", "1", "'a'", bogus="1"),
        el("ellipse", cx="1"), el("ellipse", cx="2"), el("set", [el("ellipse")], name="a"),
        text("1", "2", "'off'", enable="false"),
        text("1", "3", "'cond'", enable="show"),
        el("text", enable="true", x="1", text="'no y'"),                       # y yo'q → o'tkazib yuboriladi
        el("par", name="show", type="boolean", expr="true"),
        el("else", [text("1", "1", "'x'")]),                                   # if siz else
        el("rect", enable="true", x="1", y="1", w="5", h="5", strokeWidth="1", color="red"),
        text("1", "9", "'z'", fontName="Times New Roman", valign="center", align="middle"),
    ], extra="1")
    r = conv(xml)
    w = warn_map(r)
    assert w[("tag", "ellipse")] == 3 and w[("tag", "set")] == 1                   # joylashgan teg ham sanaladi
    assert w[("attr", "text.bogus")] == 1 and w[("attr", "rect.color")] == 1 and w[("attr", "program.extra")] == 1
    assert w[("disabled", "text")] == 1 and w[("skipped", "text")] == 1 and w[("orphan_else", "else")] == 1
    assert w[("font", "Times New Roman")] == 1 and w[("valign", "center")] == 1 and w[("align", "middle")] == 1
    els = r.template["elements"]
    cond = [e for e in els if e["t"] == "if"]
    assert len(cond) == 1 and cond[0]["cond"] == "show" and cond[0]["then"][0]["text"] == "'cond'"      # enable=ifoda → if
    assert all(isinstance(x["message"], str) and x["message"] and x["count"] >= 1 for x in r.warnings)


def test_unknown_and_nodata_variables_are_warned_not_silent():
    xml = program([text("1", "1", "badname+good+etn+waste+grtc"), el("if", [text("1", "2", "'x'")], condition="grtoi or fullName")])
    w = warn_map(conv(xml))
    assert w[("unknown_var", "badname")] == 1
    nodata = sorted(set(C.GL_STD) - label_vars.VAR_NAMES)                              # formatga ma'lum, bizda ma'lumot yo'q
    assert {"good", "grtoi", "fullName"} <= set(nodata)
    assert w[("var_nodata", "good")] == 1 and w[("var_nodata", "grtoi")] == 1 and w[("var_nodata", "fullName")] == 1
    assert ("unknown_var", "etn") not in w and ("var_nodata", "waste") not in w and ("var_nodata", "grtc") not in w
    # ma'lumot bor standart nomlar (qisqa nomlar ham) — ogohlantirishsiz
    ok = warn_map(conv(program([text("1", "1", "etn+ebs+elt+XNC1+xncSide2+grtc+grbw+grld+indexInOperation+thick+totalCount")])))
    assert not [k for k in ok if k[0] in ("unknown_var", "var_nodata")]


def test_image_validation():
    ok, big = png(), png(400, 400) + b"\0" * 300_000
    xml = program([
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata=data_uri(ok), ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata=data_uri(b"<svg/>", "svg+xml"), ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata=data_uri(big), ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata="data:image/png;base64,AAAAA", ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata=data_uri(b"not a png"), ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata="", ratio="true"),
        el("image", enable="true", x="1", y="1", w="5", h="5", imgdata=data_uri(ok), ratio="false", expr="pic"),
    ])
    r = conv(xml)
    assert len(by_t(r.template["elements"], "image")) == 2                     # 1-chi va 7-chi (static rasm bilan)
    w = warn_map(r)
    assert w[("image_type", "image")] == 1 and w[("image_size", "image")] == 1 and w[("image_invalid", "image")] == 2
    assert w[("image_none", "image")] == 1 and w[("image_expr", "image")] == 1 and w[("image_ratio", "image")] == 1
    assert r.info["images"] == 2


def test_limits_and_empty_program():
    with pytest.raises(GI.GLError):
        conv(program([]))                                                      # element yo'q
    with pytest.raises(GI.GLError):
        conv(program([el("ellipse", cx="1")]))                                 # faqat qo'llab-quvvatlanmaydigan teglar
    many = [text("1", "1", "'a'") for _ in range(label_tpl.MAX_ELEMENTS + 1)]
    with pytest.raises(GI.GLError):
        conv(program(many))                                                    # ≤ 500 element
    deep = text("1", "1", "'a'")
    for _ in range(9):
        deep = el("if", [deep], condition="true")
    with pytest.raises(GI.GLError):
        conv(program([deep]))                                                  # ≤ 8 daraja
    r = conv(program([text("1", "1", "'" + "x" * 1001 + "'"), text("1", "2", "'ok'")]))
    assert warn_map(r)[("skipped", "text")] == 1 and len(r.template["elements"]) == 1     # ifoda ≤ 1000 belgi
    r = conv(program([text("1", "1", "'a'")], dx="9999", dy="1"))
    assert r.template["size"] == {"w": 500, "h": 5} and warn_map(r)[("size", "9999×1")] == 1


def test_every_warning_and_error_code_has_ru_and_uz_text():
    """Kod ichida ishlatilgan har bir ogohlantirish/xato kodi uchun i18n da ikki tilda matn bor (kalitning o'zi chiqib qolmasin)."""
    import re
    from pathlib import Path

    from app.i18n import MSG
    src = Path(GI.__file__).parent
    for fname, prefix in (("label_gl_import.py", "lbx.w_"), ("label_gl_export.py", "lbx.x_")):
        text_ = (src / fname).read_text(encoding="utf-8")
        codes = set(re.findall(r"\.w\.add\(\"(\w+)\"", text_))
        assert codes, fname
        for c in codes:
            ru, uz = MSG[prefix + c]
            assert ru.strip() and uz.strip() and ru != uz, prefix + c
    for fname in ("label_gl_import.py", "label_gl_common.py", "label_gl_export.py"):
        for c in set(re.findall(r"_\(\"(lbx\.e_\w+)\"", (src / fname).read_text(encoding="utf-8"))):
            assert c in MSG, c
    assert "imp_lb_converted" in MSG and MSG["imp_lb_converted"][0] != MSG["imp_lb_converted"][1]


# ───────────────────────── xavfsizlik ─────────────────────────
def test_root_must_be_program():
    with pytest.raises(GI.GLError, match="program"):
        GI.parse_program('<?xml version="1.0"?><label><text/></label>')
    with pytest.raises(GI.GLError):
        GI.parse_program("bu xml emas")
    with pytest.raises(GI.GLError):
        GI.parse_program(b"")
    with pytest.raises(GI.GLError):
        GI.parse_program(b"\x00\x01\x02")


BOMB = ('<?xml version="1.0"?><!DOCTYPE program [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">'
        '<!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">]><program dx="50" dy="30"><text x="1" y="1" text="&c;"/></program>')
XXE = ('<?xml version="1.0"?><!DOCTYPE program [<!ENTITY x SYSTEM "file:///etc/passwd">]><program dx="50" dy="30">'
       '<text x="1" y="1" text="&x;"/></program>')


UTF16_DTD = ("<?xml version='1.0' encoding='UTF-16'?><!DOCTYPE program [<!ENTITY a 'b'>]><program dx='5' dy='5'/>").encode("utf-16")


@pytest.mark.parametrize("bad", [BOMB, XXE, BOMB.encode(), XXE.encode(), '<!DOCTYPE program><program dx="5" dy="5"/>',
                                 '<!doctype program><program dx="5" dy="5"/>', UTF16_DTD])
def test_dtd_and_entities_are_rejected(bad):
    with pytest.raises(GI.GLError, match="DTD"):
        GI.parse_program(bad)
    with pytest.raises(GI.GLError):
        conv(bad)


def test_leading_whitespace_and_bom_are_tolerated():
    xml = program([text("1", "5", "'a'")])
    for data in ("\n  " + xml, ("\n" + xml).encode(), b"\xef\xbb\xbf" + xml.encode()):
        assert GI.parse_program(data).tag == "program"
    cp = '<?xml version="1.0" encoding="windows-1251"?><program dx="40" dy="30">' + el("text", x="1", y="5", text="'Привет'") + "</program>"
    assert conv(cp.encode("cp1251")).template["elements"][0]["text"] == "'Привет'"


def test_xml_node_and_depth_limits():
    wide = "<program dx='50' dy='30'>" + "<text x='1' y='1' text='1'/>" * (C.MAX_XML_NODES + 5) + "</program>"
    with pytest.raises(GI.GLError):
        GI.parse_program(wide)
    deep = "<program dx='50' dy='30'>" + "<if condition='true'>" * (C.MAX_XML_DEPTH + 2) + "</if>" * (C.MAX_XML_DEPTH + 2) + "</program>"
    with pytest.raises(GI.GLError):
        GI.parse_program(deep)
    with pytest.raises(GI.GLError):
        GI.parse_program(b"<program dx='50' dy='30'>" + b" " * (C.MAX_FILE_BYTES + 1) + b"</program>")


# ───────────────────────── .project ichidan LB olish ─────────────────────────
def project_xml(programs, other_ops=True):
    ops = []
    for i, (nm, pr) in enumerate(programs):
        ops.append(el("operation", typeId="LB", typeName=nm, id=str(i + 1), program=pr, columns="2", rows="4"))
    if other_ops:
        ops.append(el("operation", typeId="CS", typeName="Material", id="9"))
        ops.append(el("operation", typeId="LB", typeName="Bo'sh", id="10", program=""))
    return ('<?xml version="1.0" encoding="UTF-8"?>' + el("project", [el("operations", ops)], name="Demo")).encode("utf-8")


def test_programs_from_project_dedupes_and_skips_non_lb():
    a, b = sample_program(), program([text("1", "1", "'b'")], dx="40", dy="30")
    progs, extra = GI.programs_from_project(project_xml([("Bir", a), ("Ikki", a), ("Uch", b)]))
    assert [(p["name"], p["ops"]) for p in progs] == [("Bir", 2), ("Uch", 1)] and extra == 0
    assert all(p["program"].startswith("<?xml") for p in progs)
    with pytest.raises(GI.GLError):
        GI.programs_from_project(project_xml([], other_ops=True))              # shablonli LB yo'q
    with pytest.raises(GI.GLError, match="project"):
        GI.programs_from_project(b"<program dx='5' dy='5'/>")
    many = [(f"n{i}", program([text("1", "1", f"'{i}'")])) for i in range(C.MAX_PROGRAMS + 3)]
    progs, extra = GI.programs_from_project(project_xml(many, other_ops=False))
    assert len(progs) == C.MAX_PROGRAMS and extra == 3
    with pytest.raises(GI.GLError, match="DTD"):
        GI.programs_from_project(b'<?xml version="1.0"?><!DOCTYPE project [<!ENTITY a "b">]><project/>')


def test_project_import_converts_lb_program_to_template():
    """`.project` importi: LB operatsiyasi shablonga o'giriladi (operatsiya shuni ishlatadi); asl matn ham saqlanadi."""
    from app.plugins.legacy_project import import_project
    pr = sample_program()
    raw = ('<?xml version="1.0" encoding="UTF-8"?><project name="Demo">' + el("operation", typeId="LB", typeName="Etik", id="3",
           printMode="0", columns="2", rows="4", gap="10", margin="true", source="2", program=pr) + "</project>").encode()
    p, warnings = import_project(raw, "demo.project")
    lb = p.operations[0].lb
    assert lb.template is not None and lb.template["elements"] and lb.template["size"] == {"w": 70, "h": 50}
    assert lb.template_id is None and lb.legacy_program == pr and (lb.width_mm, lb.height_mm) == (70, 50)
    assert any("Etik" in w and ("преобразован" in w) for w in warnings)
    assert not any("не читается" in w for w in warnings)
    # bazadan qayta yuklash (legacy kontekst) shablonni saqlab qoladi
    from app.models import Project
    assert Project.model_validate_json(p.model_dump_json()).operations[0].lb.template == lb.template


def test_project_import_falls_back_when_program_is_not_convertible():
    from app.plugins.legacy_project import import_project
    for bad in ('<program dx="50" dy="30"><ellipse/></program>', "bu xml emas", "<label/>"):
        raw = ('<?xml version="1.0"?><project name="D">' + el("operation", typeId="LB", id="3", program=bad) + "</project>").encode()
        p, warnings = import_project(raw, "d.project")
        lb = p.operations[0].lb
        assert lb.template is None and lb.legacy_program == bad                 # eskicha: saqlanadi, standart shablon ishlatiladi
        assert any("не читается" in w for w in warnings)


# ───────────────────────── API ─────────────────────────
def up(client, filename, data, **form):
    return client.post("/api/labels/import-file", files={"file": (filename, data)}, data=form)


@pytest.mark.parametrize("ext", [".lbl", ".xml", ".LBL"])
def test_api_import_program_file(client, ext):
    r = up(client, "mening shablonim" + ext, sample_program().encode("utf-8"))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "program" and len(d["items"]) == 1 and d["skipped"] == []
    it = d["items"][0]
    assert it["name"] == "mening shablonim" and it["template"]["size"] == {"w": 70, "h": 50} and it["saved"] is None
    assert it["layout"]["columns"] == 3 and it["info"]["elements"] > 10 and it["errors"] == []
    assert {w["code"] for w in it["warnings"]} >= {"part", "dash", "hatch"}
    assert all(w["message"] for w in it["warnings"])
    assert client.get("/api/label-templates").json() and not any(t["name"] == "mening shablonim" for t in client.get("/api/label-templates").json())


def test_api_import_saves_to_library_with_chosen_name(client):
    r = up(client, "x.lbl", sample_program().encode(), name="Ombor 70x50", save="true")
    assert r.status_code == 200, r.text
    saved = r.json()["items"][0]["saved"]
    assert saved["name"] == "Ombor 70x50" and saved["id"].startswith("profile:")
    lst = {t["id"]: t for t in client.get("/api/label-templates").json()}
    assert lst[saved["id"]]["name"] == "Ombor 70x50" and lst[saved["id"]]["size"] == {"w": 70, "h": 50}
    g = client.get(f"/api/label-templates/{saved['id']}").json()["template"]
    assert g["layout"]["rows"] == 5 and g["elements"]
    # kutubxonadagi shablon chop uchun ishlaydi (ko'rish)
    pv = client.post("/api/label-templates/preview", json={"template": g}).json()
    assert pv["errors"] == [] and "<svg" in pv["html"]


def test_api_import_project_offers_each_program_separately(client):
    a, b = sample_program(), program([text("1", "1", "'b'")], dx="40", dy="30")
    raw = project_xml([("Katta", a), ("Kichik", b), ("Katta nusxa", a), ("Buzuq", "<program dx='5'><ellipse/></program>")])
    r = up(client, "loyiha.project", raw)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "project" and [i["name"] for i in d["items"]] == ["Katta", "Kichik"] and d["items"][0]["ops"] == 2
    assert [s["source"] for s in d["skipped"]] == ["Buzuq"] and d["skipped"][0]["error"]
    assert [i["size"] for i in d["items"]] == [{"w": 70, "h": 50}, {"w": 40, "h": 30}]
    # faqat tanlangani saqlanadi
    r = up(client, "loyiha.project", raw, save="true", select="1", name="Kichik shablon")
    items = r.json()["items"]
    assert items[0]["saved"] is None and items[1]["saved"]["name"] == "Kichik shablon"


def test_api_import_rejects_bad_files(client):
    assert up(client, "x.txt", b"<program/>").status_code == 400                                 # kengaytma
    assert up(client, "x.lbl", b"<label><text/></label>").status_code == 400                     # ildiz program emas
    assert "program" in up(client, "x.xml", b"<label/>").json()["detail"]
    assert up(client, "x.lbl", b"").status_code == 400
    assert up(client, "x.lbl", BOMB.encode()).status_code == 400
    assert up(client, "x.lbl", XXE.encode()).status_code == 400
    r = up(client, "x.lbl", b"<program dx='5' dy='5'>" + b" " * (C.MAX_FILE_BYTES + 10) + b"</program>")
    assert r.status_code == 413                                                                   # > 5 MB
    assert up(client, "x.project", b"<project name='x'><operation typeId='CS'/></project>").status_code == 400   # LB yo'q
    assert up(client, "x.project", b"<program dx='5' dy='5'/>").status_code == 400                 # .project ildizi project emas
    assert up(client, "x.lbl", program([el("ellipse", cx="1")]).encode()).status_code == 400      # qo'llab-quvvatlanadigan element yo'q
    assert up(client, "x.lbl", sample_program().replace('x="2" y="3"', 'x="2"', 1).encode()).status_code == 200   # bitta element tushadi, qolgani o'tadi


def test_api_import_messages_follow_language(client):
    r = client.post("/api/labels/import-file", files={"file": ("x.lbl", b"<label/>")}, headers={"Accept-Language": "uz"})
    assert "Ildiz teg" in r.json()["detail"]
    r = client.post("/api/labels/import-file", files={"file": ("x.lbl", b"<label/>")}, headers={"Accept-Language": "ru"})
    assert "Корневой тег" in r.json()["detail"]
