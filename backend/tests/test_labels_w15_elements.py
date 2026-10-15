"""W15 · LB-D: yangi chizma elementlari (polyline, arc, ellipse) — tuzilma, render, ifoda xatolari, W9 import/eksport moslik jadvali,
vizual redaktor uchun `design` API (har element `<g data-p>`), eski shablonlar mosligi."""
import copy
import json
import re
import xml.etree.ElementTree as ET

import pytest

from app.services import label_builtin, label_gl_common as C, label_gl_export as GE, label_gl_import as GI, label_tpl, label_vars
from app.services.label_tpl import Renderer, TemplateError, check_template, normalize_template

_TAGS = {"svg", "text", "tspan", "rect", "line", "g", "path", "image", "ellipse"}


def tpl(elements, **kw):
    t = {"v": 1, "name": "T", "size": {"w": 58, "h": 40}, "params": [], "vars": [], "elements": elements}
    t.update(kw)
    return t


def render(t, mark=False, kind="part", w=58, h=40):
    r = Renderer(normalize_template(t), width_mm=w, height_mm=h, mark=mark)
    svg = r.render(label_vars.sample_env(kind))
    root = ET.fromstring(svg)                                           # to'g'ri XML
    for el in root.iter():
        assert el.tag.split("}")[-1] in _TAGS, el.tag
        for k, v in el.attrib.items():
            assert not k.lower().startswith("on") and "javascript:" not in v.lower()
    return svg, r, root


def tags(root, name):
    return [e for e in root.iter() if e.tag.split("}")[-1] == name]


# ───────────────────────── tuzilma ─────────────────────────
def test_new_types_are_known_and_round_trip():
    els = [{"t": "polyline", "points": [[1, 1], [5, 5], ["label.width/2", 9]], "closed": True, "stroke": {"w": 0.3, "color": "#f00"}, "fill": "#eee"},
           {"t": "arc", "cx": 20, "cy": 20, "r": 8, "a1": 0, "a2": 180, "stroke": 0.4},
           {"t": "ellipse", "cx": 30, "cy": 10, "rx": 6, "ry": 3, "fill": "#000"}]
    t = normalize_template(tpl(els))
    assert normalize_template(json.loads(json.dumps(t))) == t                       # eksport → import: aynan o'sha
    assert {"polyline", "arc", "ellipse"} <= set(label_tpl.TYPES)


@pytest.mark.parametrize("bad", [
    {"t": "polyline"}, {"t": "polyline", "points": []}, {"t": "polyline", "points": [[1, 2]]},
    {"t": "polyline", "points": "x"}, {"t": "polyline", "points": [[1, 2], [3]]}, {"t": "polyline", "points": [[1, 2], [3, [4]]]},
    {"t": "polyline", "points": [[1, 2], [3, 4]], "fill": 5}, {"t": "polyline", "points": [[1, 2], [3, 4]], "stroke": {"color": 1}},
    {"t": "polyline", "points": [[1, 2], [3, 4]], "closed": {"a": 1}},
    {"t": "arc", "cx": [1]}, {"t": "ellipse", "rx": {"a": 1}}, {"t": "arc", "r": "x" * 1001},
])
def test_normalize_rejects_bad_new_elements(bad):
    with pytest.raises(TemplateError):
        normalize_template(tpl([bad]))


def test_polyline_point_limit():
    ok = {"t": "polyline", "points": [[i, i] for i in range(label_tpl.MAX_POINTS)]}
    normalize_template(tpl([ok]))
    with pytest.raises(TemplateError):
        normalize_template(tpl([{"t": "polyline", "points": [[i, i] for i in range(label_tpl.MAX_POINTS + 1)]}]))


def test_old_templates_open_unchanged():
    """Eski (W4) shablonlar yangi maydonsiz ochiladi: normalizatsiya, render, tekshiruv, ZPL, XML eksport — hammasi xatosiz."""
    from app.services import label_zpl
    for key in label_builtin.BUILTIN:
        t = label_builtin.builtin_template(key, "ru")
        n = normalize_template(t)
        assert n["elements"] == t["elements"] and "points" not in json.dumps(n)       # yangi maydon qo'shilmadi
        chk = check_template(t)
        assert chk["ok"], (key, chk)
        svg, r, _ = render(t, kind="waste" if key == "waste" else "product" if key == "product" else "part", w=t["size"]["w"], h=t["size"]["h"])
        assert not r.errors and "data-p" not in svg                                  # mark o'chiq — chiqish avvalgidek
        z = label_zpl.render_zpl_sample(t, width_mm=t["size"]["w"], height_mm=t["size"]["h"], kind="part")
        assert z.zpl.startswith("^XA") and not z.errors
        assert GE.export_program(t).xml.startswith("<?xml")


# ───────────────────────── render ─────────────────────────
def test_polyline_renders_path_with_expression_points_and_closing():
    svg, r, root = render(tpl([{"t": "polyline", "points": [[1, 2], [10, 2], ["label.width/2", "label.height-1"]], "closed": True,
                                "stroke": {"w": 0.5, "color": "#c00"}, "fill": "#ddd"}]))
    (p,) = tags(root, "path")
    assert p.get("d") == "M1 2 L10 2 L29 39 Z" and p.get("stroke") == "#c00" and p.get("stroke-width") == "0.5" and p.get("fill") == "#ddd"
    assert not r.errors
    _, _, root2 = render(tpl([{"t": "polyline", "points": [[1, 2], [10, 2]], "closed": "label.width > 100"}]))
    assert tags(root2, "path")[0].get("d") == "M1 2 L10 2"                         # closed — ifoda; false → ochiq
    assert tags(root2, "path")[0].get("stroke") == "#000" and tags(root2, "path")[0].get("fill") == "none"     # standart: 0.2 mm qora chiziq


def test_arc_geometry_sweeps_and_pie_fill():
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 0, "a2": 90}]))
    assert tags(root, "path")[0].get("d") == "M30 20 A10 10 0 0 1 20 30"             # 0° → o'ngda, 90° → pastda (Y pastga: soat strelkasi bo'yicha)
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 0, "a2": 270}]))
    assert tags(root, "path")[0].get("d") == "M30 20 A10 10 0 1 1 20 10"             # katta yoy (|sweep| > 180)
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 90, "a2": 0}]))
    assert tags(root, "path")[0].get("d") == "M20 30 A10 10 0 0 0 30 20"             # teskari yo'nalish: sweep-flag 0
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 0, "a2": 90, "fill": "#abc"}]))
    d = tags(root, "path")[0].get("d")
    assert d.startswith("M20 20 L30 20 A10 10") and d.endswith("Z") and tags(root, "path")[0].get("stroke") is None   # sektor, konturisiz
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 0, "a2": 360}]))
    e = tags(root, "ellipse")[0]
    assert (e.get("rx"), e.get("ry")) == ("10", "10")                                 # to'liq aylana
    _, _, root = render(tpl([{"t": "arc", "cx": 20, "cy": 20, "r": 0, "a1": 0, "a2": 90}]))
    assert not tags(root, "path")                                                    # radius 0 — chizilmaydi


def test_ellipse_stroke_fill_defaults():
    _, _, root = render(tpl([{"t": "ellipse", "cx": 30, "cy": 10, "rx": 6, "ry": 3}]))
    e = tags(root, "ellipse")[0]
    assert (e.get("cx"), e.get("cy"), e.get("rx"), e.get("ry"), e.get("stroke"), e.get("fill")) == ("30", "10", "6", "3", "#000", "none")
    _, _, root = render(tpl([{"t": "ellipse", "cx": 30, "cy": 10, "rx": 6, "ry": 3, "fill": "#123456"}]))
    e = tags(root, "ellipse")[0]
    assert e.get("fill") == "#123456" and e.get("stroke") is None
    _, _, root = render(tpl([{"t": "ellipse", "cx": 30, "cy": 10, "rx": 0, "ry": 3}]))
    assert not tags(root, "ellipse")


def test_unsafe_color_is_neutralised_in_new_elements():
    _, _, root = render(tpl([{"t": "ellipse", "cx": 5, "cy": 5, "rx": 2, "ry": 2, "fill": "red\" onload=\"x", "stroke": {"w": 1, "color": "url(javascript:1)"}}]))
    e = tags(root, "ellipse")[0]
    assert e.get("fill") == "none" and e.get("stroke") == "#000"


def test_new_elements_report_expression_errors_with_field_names():
    t = tpl([{"t": "polyline", "points": [[1, 2], ["nope_var", 3], [4, "1/0"]]}, {"t": "arc", "cx": "foo(", "cy": 1, "r": 2},
             {"t": "ellipse", "cx": 1, "cy": 1, "rx": "'a'", "ry": 2}])
    chk = check_template(t)
    by = {(e["path"], e["field"]) for e in chk["errors"]}
    assert ("1", "points[2][1]") in by and ("2", "cx") in by and ("3", "rx") in by         # element boshiga birinchi xato (boshqa elementlar kabi)
    chk2 = check_template(tpl([{"t": "polyline", "points": [[1, 2], [3, "foo("], [4, "1+"]]}]))
    assert {(e["path"], e["field"]) for e in chk2["errors"]} == {("1", "points[2][2]"), ("1", "points[3][2]")}      # sintaksis — hammasi
    svg, r, _ = render(t)
    assert "#ERR 1" in svg and "#ERR 2" in svg and "#ERR 3" in svg                    # jim bo'sh emas


def test_unknown_keys_warn_only_for_the_right_type():
    chk = check_template(tpl([{"t": "polyline", "points": [[1, 2], [3, 4]], "colour": "red"}, {"t": "text", "x": 1, "y": 1, "text": "'a'", "points": []}]))
    ws = {(w["path"], w["field"]) for w in chk["warnings"]}
    assert ("1", "colour") in ws and ("2", "points") in ws and ("1", "points") not in ws


def test_nested_new_elements_inside_group_and_if():
    t = tpl([{"t": "group", "origin": [10, 5], "rotate": 90, "elements": [{"t": "polyline", "points": [[0, 0], [5, 0]]}]},
             {"t": "if", "cond": "true", "then": [{"t": "ellipse", "cx": 3, "cy": 3, "rx": 1, "ry": 1}]}])
    svg, r, root = render(t, mark=True)
    assert [g.get("data-p") for g in tags(root, "g") if g.get("data-p")] == ["1", "1.elements.1", "2", "2.then.1"]
    assert 'transform="translate(10 5) rotate(90)"' in svg


# ───────────────────────── mark (redaktor) ─────────────────────────
def test_mark_wraps_every_element_with_its_path_and_type():
    svg, r, root = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "'a'"}, {"t": "line", "x1": 0, "y1": 0, "x2": 5, "y2": 5},
                               {"t": "var", "name": "v", "expr": "1"}, {"t": "text", "x": 1, "y": "1/0", "text": "'zz'"}]), mark=True)
    ws = [(g.get("data-p"), g.get("data-t")) for g in tags(root, "g")]
    assert ws == [("1", "text"), ("2", "line"), ("3", "var"), ("4", "text")]
    assert "#ERR 4" in svg and svg.index("#ERR 4") < svg.rindex("</g>")                # xato belgisi ham o'z o'rovchi ichida
    plain, _, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "'a'"}]))
    marked, _, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "'a'"}]), mark=True)
    assert re.sub(r'<g data-p="1" data-t="text">|</g>', "", marked) == plain            # mark faqat o'rovchi qo'shadi


# ───────────────────────── W9 import/eksport moslik jadvali ─────────────────────────
def wmap(r):
    return {(w["code"], w["key"]): w["count"] for w in r.warnings}


def test_export_axis_aligned_polyline_becomes_line_rects_others_warn():
    r = GE.export_program(tpl([
        {"t": "polyline", "points": [[2, 2], [20, 2], [20, 10]], "stroke": {"w": 0.4, "color": "#00f"}},
        {"t": "polyline", "points": [[2, 20], [10, 20], [10, 30], [2, 30]], "closed": True},
        {"t": "polyline", "points": [[2, 2], [20, 8]]},                                  # qiyshiq — butunlay o'tkazib yuboriladi
        {"t": "polyline", "points": [[30, 2], [40, 2]], "fill": "#ccc"},                  # to'ldirish yozilmaydi
        {"t": "arc", "cx": 20, "cy": 20, "r": 5, "a1": 0, "a2": 90}, {"t": "ellipse", "cx": 20, "cy": 20, "rx": 5, "ry": 3}]))
    root = C.safe_fromstring(r.xml)
    rects = [e for e in root.iter("rect")]
    assert len(rects) == 2 + 4 + 1                                                       # 2 + 4 (yopiq: 4 kesma) + 1 (to'ldirishli)
    first = rects[0]
    assert (first.get("x"), first.get("y"), first.get("w"), first.get("h"), first.get("strokeColor")) == ("2", "2", "18", "0", "#0000FF")
    codes = wmap(r)
    assert ("polyline", "3") in codes and ("poly_fill", "4") in codes and ("arc", "5") in codes and ("ellipse", "6") in codes
    assert all(w["message"] for w in r.warnings)


def test_export_import_round_trip_keeps_supported_part_and_drops_new_elements_with_warning():
    base = [{"t": "text", "x": 2, "y": 3, "text": "part.name", "size": 3}, {"t": "rect", "x": 1, "y": 1, "w": 20, "h": 8, "stroke": {"w": 0.3}}]
    full = tpl(base + [{"t": "arc", "cx": 20, "cy": 20, "r": 5}, {"t": "ellipse", "cx": 20, "cy": 20, "rx": 5, "ry": 3}])
    ex = GE.export_program(full)
    back = GI.convert_program(ex.xml, "T").template
    only_base = GI.convert_program(GE.export_program(tpl(base)).xml, "T").template
    assert back["elements"] == only_base["elements"]                                     # qo'llab-quvvatlanadigan qism teng
    assert {w["code"] for w in ex.warnings} >= {"arc", "ellipse"}
    # eksport takrorlansa — bir xil matn
    assert GE.export_program(full).xml == ex.xml


def test_import_never_creates_new_element_types():
    """`<program>` fayl formatida chizma teglari yo'q: noma'lum tegni import «tag» ogohlantirishi bilan o'tkazib yuboradi."""
    xml = ('<program columns="3" dx="58" dy="40" gap="2" margin="true" printMode="0" rows="0">'
           '<text enable="true" x="1" y="5" text="\'a\'" fontSize="3"/><polyline x="1" y="2"/><ellipse cx="1"/></program>')
    r = GI.convert_program(xml, "T")
    assert [e["t"] for e in r.template["elements"]] == ["text"]
    assert {w["key"] for w in r.warnings if w["code"] == "tag"} == {"polyline", "ellipse"}


# ───────────────────────── API: vizual redaktor ─────────────────────────
def test_check_and_library_accept_new_elements(client):
    t = tpl([{"t": "polyline", "points": [[1, 1], [9, 9]]}, {"t": "arc", "cx": 5, "cy": 5, "r": 3, "a1": 0, "a2": 90}])
    assert client.post("/api/label-templates/check", json={"template": t}).json()["ok"]
    r = client.post("/api/settings/label_template", json={"name": "W15 chizma", "data": t})
    assert r.status_code == 200
    got = client.get(f"/api/label-templates/profile:{r.json()['id']}").json()["template"]
    assert [e["t"] for e in got["elements"]] == ["polyline", "arc"] and got["elements"][0]["points"] == [[1, 1], [9, 9]]
    exp = client.get(f"/api/label-templates/profile:{r.json()['id']}/export-xml")
    assert exp.status_code == 200 and "<program" in exp.text
    # JSON eksport → import: yangi elementlar aynan o'sha holda qaytadi
    js = client.get(f"/api/label-templates/profile:{r.json()['id']}/export")
    assert js.status_code == 200
    back = client.post("/api/label-templates/import", json=js.json(), params={"name": "W15 qaytgan"})
    assert back.status_code == 200 and not back.json()["errors"]
    got2 = client.get(f"/api/label-templates/{back.json()['id']}").json()["template"]
    assert got2["elements"] == got["elements"]
    client.delete(f"/api/settings/label_template/{back.json()['profile']['id']}")
    bad = client.post("/api/settings/label_template", json={"name": "bad", "data": tpl([{"t": "polyline", "points": [[1, 1]]}])})
    assert bad.status_code == 400
    client.delete(f"/api/settings/label_template/{r.json()['id']}")


def test_design_api_returns_marked_svg_values_and_errors(client):
    t = tpl([{"t": "text", "x": 2, "y": 2, "text": "part.name", "size": 3},
             {"t": "rect", "x": "pad", "y": 10, "w": 10, "h": 5}, {"t": "text", "x": 1, "y": "1/0", "text": "'bad'"},
             {"t": "ellipse", "cx": 40, "cy": 20, "rx": 5, "ry": 3}], vars=[{"name": "pad", "expr": "1.5*2"}],
            params=[{"name": "k", "type": "double", "default": 2}])
    r = client.post("/api/label-templates/design", json={"template": t, "params": {"k": 3}}).json()
    root = ET.fromstring(r["svg"])
    assert [g.get("data-p") for g in tags(root, "g")] == ["1", "2", "3", "4"]
    assert (r["width"], r["height"]) == (58, 40)
    assert [(e["path"], e["field"]) for e in r["errors"]] == [("3", "y")]
    assert r["values"]["part.name"] and r["values"]["label.width"] == 58 and r["tpl_values"] == {"pad": 3.0, "k": 3.0}
    assert r["meta"] == {"source": "sample", "total": 1, "index": 0, "kind": "part"}
    # o'lcham va tur
    r2 = client.post("/api/label-templates/design", json={"template": t, "width_mm": 80, "height_mm": 30, "kind": "product"}).json()
    assert (r2["width"], r2["height"]) == (80, 30) and 'viewBox="0 0 80 30"' in r2["svg"] and r2["meta"]["kind"] == "product"
    assert r2["values"]["product.name"]
    # tuzilma xatosi — svg bo'sh, xato ro'yxatda
    r3 = client.post("/api/label-templates/design", json={"template": {"elements": [{"t": "nope"}]}}).json()
    assert r3["svg"] == "" and r3["errors"] and "nope" in r3["errors"][0]["message"]
    assert client.post("/api/label-templates/design", json={"template": t, "values": False}).json()["values"] == {}
    assert client.post("/api/label-templates/design", json={"template": t, "width_mm": 9999}).status_code == 422


def test_design_api_uses_real_project_rows(client, kravat):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    t = tpl([{"t": "text", "x": 2, "y": 2, "text": "part.name+' #'+label.number", "size": 3}])
    lb = {"mode": "roll", "width_mm": 58, "height_mm": 40}
    a = client.post("/api/label-templates/design", json={"template": t, "project_id": pid, "lb": lb, "index": 0}).json()
    b = client.post("/api/label-templates/design", json={"template": t, "project_id": pid, "lb": lb, "index": 5}).json()
    assert a["meta"]["source"] == "project" and a["meta"]["total"] == 19 and a["meta"]["index"] == 0
    assert "#1<" in a["svg"] and "#6<" in b["svg"] and b["meta"]["index"] == 5          # label.number — qator tartibi
    c = client.post("/api/label-templates/design", json={"template": t, "project_id": pid, "lb": lb, "index": 999}).json()
    assert c["meta"]["index"] == 18                                                      # oxirgisiga qisqartiriladi
    empty = client.post("/api/label-templates/design", json={"template": t, "project_id": pid, "lb": {**lb, "source": "products", "product_only_nonzero": True}}).json()
    assert empty["meta"]["source"] in ("sample", "project")                              # qator bo'lmasa — namunaga qaytadi (xato yo'q)
    assert client.post("/api/label-templates/design", json={"template": t, "project_id": "nope", "lb": lb}).status_code in (404, 400)


def test_design_api_user_kind_uses_fields_and_row(client):
    t = tpl([{"t": "text", "x": 2, "y": 2, "text": "user.title+'/'+user.n", "size": 3}])
    fields = [{"name": "title", "title": "Nom", "type": "string"}, {"name": "n", "type": "integer"}]
    r = client.post("/api/label-templates/design", json={"template": t, "kind": "user", "fields": fields, "row": {"title": "AB", "n": "7"}}).json()
    assert ">AB/7<" in r["svg"] and not r["errors"]
    r = client.post("/api/label-templates/design", json={"template": t, "kind": "user", "fields": fields}).json()
    assert ">Nom/1<" in r["svg"]                                                         # qator yo'q — sarlavha va 1 (namuna)
