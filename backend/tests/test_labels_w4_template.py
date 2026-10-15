"""W4 · LB: JSON shablon — tuzilma chegaralari, ifoda xatolari (jim 0 yo'q), elementlar, xavfsizlik (escape, rang, rasm)."""
import copy
import json
import re

import pytest

from app.services import label_builtin, label_tpl, label_vars
from app.services.label_tpl import Renderer, TemplateError, check_template, normalize_template


def tpl(elements, **kw):
    t = {"v": 1, "name": "T", "size": {"w": 58, "h": 40}, "params": [], "vars": [], "elements": elements}
    t.update(kw)
    return t


_ALLOWED_TAGS = {"svg", "text", "tspan", "rect", "line", "g", "path", "image"}


def assert_inert(svg: str) -> None:
    """Chiqish — to'g'ri tuzilgan XML; faqat ruxsat etilgan teglar; `on*` atributlari, `javascript:` va tashqi `href` yo'q."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg)
    for el in root.iter():
        assert el.tag.split("}")[-1] in _ALLOWED_TAGS, el.tag
        for k, v in el.attrib.items():
            assert not k.lower().startswith("on"), (el.tag, k)
            assert "javascript:" not in v.lower(), (el.tag, k, v)
            if k == "href":
                assert el.tag.endswith("image") and v.startswith("data:image/"), (el.tag, v[:30])


def render(t, env=None, w=58, h=40, params=None, kind="part"):
    r = Renderer(normalize_template(t), width_mm=w, height_mm=h, params=params)
    env = dict(env) if env is not None else label_vars.sample_env(kind)
    svg = r.render(env)
    assert_inert(svg)
    return svg, r


# ───────────────────────── tuzilma ─────────────────────────
def test_normalize_defaults_and_roundtrip():
    t = normalize_template({"elements": [{"t": "text", "x": 1, "y": 2, "text": "'a'"}]})
    assert t["v"] == 1 and t["size"] == {"w": 58, "h": 40} and t["params"] == [] and t["vars"] == []
    assert normalize_template(json.loads(json.dumps(t))) == t                         # eksport → import: aynan o'sha


@pytest.mark.parametrize("bad", [
    [], "x", {"size": {"w": 1, "h": 40}}, {"size": {"w": 58, "h": 9999}}, {"size": {"w": "a", "h": 5}},
    {"elements": "x"}, {"elements": [5]}, {"elements": [{"t": "nope"}]}, {"elements": [{"t": "text", "x": [1]}]},
    {"elements": [{"t": "text", "text": {"a": 1}}]}, {"elements": [{"t": "barcode", "kind": "pdf417", "data": "'1'"}]},
    {"elements": [{"t": "var", "name": "1bad", "expr": "1"}]}, {"elements": [{"t": "group", "origin": [1]}]},
    {"params": [{"name": "x", "type": "color"}]}, {"params": [{"type": "double"}]}, {"vars": [{"expr": "1"}]},
    {"elements": [{"t": "text", "text": "x" * 1001}]},
])
def test_normalize_rejects_bad_structure(bad):
    with pytest.raises(TemplateError):
        normalize_template(bad)


def test_normalize_limits():
    many = [{"t": "line", "x1": 0, "y1": 0, "x2": 1, "y2": 1} for _ in range(label_tpl.MAX_ELEMENTS)]
    normalize_template(tpl(many))
    with pytest.raises(TemplateError):
        normalize_template(tpl(many + [{"t": "line", "x1": 0, "y1": 0, "x2": 1, "y2": 1}]))
    deep = {"t": "text", "x": 0, "y": 0, "text": "'x'"}
    for _ in range(label_tpl.MAX_DEPTH):                                                # 8 daraja — mumkin, 9 — yo'q
        deep = {"t": "group", "elements": [deep]}
    with pytest.raises(TemplateError):
        normalize_template(tpl([deep]))
    ok = {"t": "text", "x": 0, "y": 0, "text": "'x'"}
    for _ in range(label_tpl.MAX_DEPTH - 1):
        ok = {"t": "group", "elements": [ok]}
    normalize_template(tpl([ok]))
    with pytest.raises(TemplateError):
        normalize_template(tpl([{"t": "text", "x": 0, "y": 0, "text": "'" + "a" * 1_100_000 + "'"}]))


def test_image_only_png_jpeg_data_uri():
    png = "data:image/png;base64,iVBORw0KGgo="
    normalize_template(tpl([{"t": "image", "x": 0, "y": 0, "w": 5, "h": 5, "src": png}]))
    for bad in ("data:image/svg+xml;base64,PHN2Zy8+", "http://evil/x.png", "javascript:alert(1)", "data:image/png;base64,AA\"onload=\"x",
                "data:image/png;base64," + "A" * 300_000, "data:text/html;base64,AAAA"):
        with pytest.raises(TemplateError):
            normalize_template(tpl([{"t": "image", "x": 0, "y": 0, "w": 5, "h": 5, "src": bad}]))


# ───────────────────────── ifoda xatolari: jim 0 yo'q ─────────────────────────
def test_check_reports_syntax_and_runtime_errors():
    t = tpl([
        {"t": "text", "x": "1", "y": "foo(", "text": "'a'"},                    # sintaksis
        {"t": "text", "x": "nope_var", "y": "2", "text": "'b'"},                # noma'lum o'zgaruvchi
        {"t": "text", "x": "1", "y": "1/0", "text": "'c'"},                     # nolga bo'lish
        {"t": "text", "x": "'abc'", "y": "2", "text": "'d'"},                   # son emas
        {"t": "text", "x": "1", "y": "2", "text": "unknown_fn(1)"},             # noma'lum funksiya
        {"t": "text", "x": "1", "y": "2", "text": "'ok'", "colour": "red"},     # noma'lum kalit — ogohlantirish
    ])
    r = check_template(t)
    assert not r["ok"]
    by = {(e["path"], e["field"]): e["message"] for e in r["errors"]}
    assert set(by) == {("1", "y"), ("2", "x"), ("3", "y"), ("4", "x"), ("5", "text")}
    assert all(m for m in by.values()) and "0" != by[("3", "y")]
    assert "nope_var" in by[("2", "x")]
    assert any(w["path"] == "6" and w["field"] == "colour" for w in r["warnings"])
    assert check_template(tpl([{"t": "text", "x": "1", "y": "2", "text": "'ok'"}]))["ok"]


def test_error_message_language():
    t = tpl([{"t": "text", "x": "nope_var", "y": "2", "text": "'b'"}])
    ru = check_template(t, lang="ru")["errors"][0]["message"]
    uz = check_template(t, lang="uz")["errors"][0]["message"]
    assert "переменная" in ru and "o'zgaruvchi" in uz


def test_render_marks_failed_element_instead_of_silent_zero():
    svg, r = render(tpl([{"t": "text", "x": "1", "y": "1/0", "text": "'zzz'"}, {"t": "text", "x": 1, "y": 5, "text": "'ok'"}]))
    assert "#ERR 1" in svg and ">ok<" in svg and "zzz" not in svg
    (e,) = r.errors.values()
    assert e["path"] == "1" and e["field"] == "y" and e["count"] == 1 and e["label"] == 1
    r.render(label_vars.sample_env("part"))
    assert list(r.errors.values())[0]["count"] == 2                                 # takrorlanmaydi — sanaladi


def test_failed_if_condition_is_error_and_false():
    svg, r = render(tpl([{"t": "if", "cond": "1/0", "then": [{"t": "text", "x": 1, "y": 1, "text": "'yes'"}],
                          "else": [{"t": "text", "x": 1, "y": 1, "text": "'no'"}]}]))
    assert ">no<" in svg and ">yes<" not in svg and r.errors


def test_var_error_is_reported_once_not_silently_zero():
    svg, r = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "bad"}], vars=[{"name": "bad", "expr": "1/0"}]))
    assert any(e["path"] == "vars.bad" for e in r.errors.values())
    assert ">bad<" not in svg


# ───────────────────────── elementlar ─────────────────────────
def test_if_else_inline_var_and_params():
    t = tpl([{"t": "var", "name": "n", "expr": "part.copies * 2"},
             {"t": "if", "cond": "show", "then": [{"t": "text", "x": 1, "y": 1, "text": "'ON '+n"}],
              "else": [{"t": "text", "x": 1, "y": 1, "text": "'OFF'"}]}],
            params=[{"name": "show", "type": "boolean", "default": True, "title": "x"}])
    svg, _ = render(t)
    assert ">ON 4<" in svg
    svg, _ = render(t, params={"show": False})
    assert ">OFF<" in svg and "ON" not in svg
    svg, _ = render(t, params={"show": "false"})
    assert ">OFF<" in svg


def test_static_vars_depend_only_on_size_and_params():
    t = tpl([{"t": "text", "x": "pad", "y": "dy", "text": "part.name"}],
            vars=[{"name": "pad", "expr": "label.width / 29"}, {"name": "dy", "expr": "pad * part.copy"}])
    r = Renderer(normalize_template(t), width_mm=58, height_mm=40)
    assert [v["name"] for v in r._static] == ["pad"] and [v["name"] for v in r._dynamic] == ["dy"]
    e1 = label_vars.sample_env("part"); e2 = dict(e1); e2["part.copy"] = 3
    s1, s2 = r.render(e1), r.render(e2)
    assert 'x="2" y="4.46"' in s1 and 'x="2" y="8.46"' in s2                       # y + 0.82·shrift (asos chizig'i)


def test_group_rotate_origin_and_nested_paths():
    t = tpl([{"t": "group", "rotate": 90, "origin": [50, 6], "elements": [
        {"t": "barcode", "kind": "code128", "x": 0, "y": 0, "w": 30, "h": 8, "data": "rspace(right(part.id,4),4,'0')", "caption": True}]}])
    svg, r = render(t)
    assert 'translate(50 6) rotate(90)' in svg and not r.errors
    assert ">0007<" in svg                                                           # caption — o'qiladigan matn
    t["elements"][0]["elements"][0]["data"] = "'кириллица'"
    svg, r = render(t)
    (e,) = r.errors.values()
    assert e["path"] == "1.elements.1" and "Code128" in e["message"] and "#ERR 1.elements.1" in svg


def test_barcode_rotate_and_qr_density_warning():
    svg, r = render(tpl([{"t": "barcode", "kind": "qr", "x": 2, "y": 2, "size": 5, "data": "part.qr", "rotate": 90}]))
    assert "rotate(90 2 2)" in svg
    assert any("мелк" in w["message"] for w in r.warnings.values())               # 5 mm da MXK QR — juda mayda
    svg, r = render(tpl([{"t": "barcode", "kind": "code128", "x": 1, "y": 1, "w": 20, "h": 8, "data": "'1000123000700001'"}]))
    assert r.warnings and not r.errors


def test_text_fit_shrink_then_truncate_and_wrap():
    long = "Juda uzun detal nomi " * 5
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "size": 3, "maxw": 20, "text": "'" + long + "'"}]))
    m = re.search(r'font-size="([\d.]+)"[^>]*>([^<]*)<', svg)
    assert float(m.group(1)) <= 3 * 0.6 + 1e-6 and m.group(2).endswith("…") and len(m.group(2)) < len(long)
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "size": 3, "maxw": 30, "text": "'Aaaaa Bbbbb Ccccc Ddddd Eeeee Fffff'"}]))
    assert svg.count("<tspan") == 0
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "size": 3, "maxw": 25, "wrap": True, "lines": 2,
                          "text": "'Aaaaa Bbbbb Ccccc Ddddd Eeeee Fffff Ggggg'"}]))
    assert svg.count("<tspan") == 2 and "…" in svg                                  # 2 qatorga sig'dirildi, oxirgisi kesildi
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "size": 3, "align": "right", "text": "'x\\ny'"}]))
    assert 'text-anchor="end"' in svg and svg.count("<tspan") == 2                  # \n — qatorlarga


def test_numbers_are_printed_without_java_double_suffix():
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "part.length"}, {"t": "text", "x": 1, "y": 5, "text": "1/4"},
                         {"t": "text", "x": 1, "y": 9, "text": "7.0/2"}, {"t": "text", "x": 1, "y": 13, "text": "7/2"}]))
    assert ">748<" in svg and ">0<" in svg and ">3.5<" in svg and ">3<" in svg      # butun ÷ butun — butun (til qoidasi)


def test_rect_line_image_part_edges_elements():
    png = "data:image/png;base64,iVBORw0KGgo="
    t = tpl([{"t": "rect", "x": 1, "y": 1, "w": 10, "h": 5, "stroke": {"w": 0.3, "color": "#f00"}, "fill": "#eee", "radius": 1},
             {"t": "rect", "x": 1, "y": 1, "w": 10, "h": 5},
             {"t": "line", "x1": 0, "y1": 0, "x2": 5, "y2": 5, "stroke": 0.5},
             {"t": "image", "x": 1, "y": 1, "w": 5, "h": 5, "src": png},
             {"t": "part", "x": 30, "y": 5, "w": 20, "h": 14}, {"t": "edges", "x": 30, "y": 22, "w": 14, "h": 9}])
    svg, r = render(t)
    assert not r.errors
    assert 'stroke="#f00"' in svg and 'rx="1"' in svg and '<image ' in svg and png in svg
    assert svg.count("<rect") >= 4 and "stroke-width=\"0.5\"" in svg
    assert ">748<" in svg and ">468<" in svg                                          # detal chizmasi: o'lchamlar
    assert ">A<" in svg and ">B<" in svg                                              # kromka belgilari
    # kromka yo'q qatorda chizma ham xatosiz
    env = label_vars.sample_env("product")
    svg, r = render(t, env=env)
    assert not r.errors


# ───────────────────────── xavfsizlik ─────────────────────────
def test_output_is_escaped_and_has_no_script_or_handlers():
    evil = '<script>alert(1)</script>"><img src=x onerror=alert(2)>&amp;'
    env = label_vars.sample_env("part")
    env["project.name"] = evil
    env["part.name"] = evil
    t = tpl([{"t": "text", "x": 1, "y": 1, "text": "project.name+part.name", "color": 'red" onload="alert(3)', "font": "x\" y=\""},
             {"t": "text", "x": 1, "y": 9, "text": "'</text><script>1</script>'"},
             {"t": "rect", "x": 1, "y": 1, "w": 2, "h": 2, "fill": 'red" onclick="x', "stroke": {"w": 1, "color": "javascript:alert(1)"}},
             {"t": "barcode", "kind": "qr", "x": 1, "y": 1, "size": 12, "data": "project.name", "color": 'red" onload="x'}])
    svg, r = render(t, env=env)                                      # render() ichida assert_inert: XML + teglar + atributlar
    assert "<script" not in svg and "<img" not in svg and "javascript:" not in svg
    assert "&lt;script&gt;" in svg and 'stroke="#000"' in svg and 'fill="none"' in svg      # rang — standartga qaytdi


def test_control_characters_removed_and_text_capped():
    env = label_vars.sample_env("part")
    env["part.name"] = "a\x00b\x07c\x1fd" + "z" * 5000
    svg, _ = render(tpl([{"t": "text", "x": 1, "y": 1, "text": "part.name"}]), env=env)
    assert "\x00" not in svg and "\x07" not in svg and "\x1f" not in svg
    assert max(len(m) for m in re.findall(r">([^<]*)<", svg)) <= label_tpl.MAX_TEXT


def test_numeric_fields_are_clamped():
    svg, _ = render(tpl([{"t": "rect", "x": 1e12, "y": -1e12, "w": 1e12, "h": 1e12}, {"t": "text", "x": 1, "y": 1, "size": 1e9, "text": "'x'"}]))
    assert "1e" not in svg and "1000000000" not in svg
    assert 'width="5000"' in svg and 'font-size="200"' in svg


# ───────────────────────── o'rnatilgan namunalar ─────────────────────────
_PAIRS = [(k, v[0]) for k, v in label_builtin.BUILTIN.items()] + [
    ("waste", "part"), ("product", "part"), ("detail", "waste"), ("detail", "product"), ("detail", "user")]     # standart — hamma tur


@pytest.mark.parametrize("key,kind", _PAIRS)
@pytest.mark.parametrize("size", [(58, 40), (40, 25), (100, 60)])
def test_builtin_templates_render_without_errors(key, kind, size):
    """Har namuna o'z qator turi bilan (va qoldiq/mahsulot shabloni detal qatori bilan ham) hamma o'lchamda xatosiz."""
    t = label_builtin.builtin_template(key)
    r = check_template(t, None, "ru", label_vars.sample_env(kind), size[0], size[1])
    assert r["ok"], r["errors"]
    svg, rr = render(t, env=label_vars.sample_env(kind), w=size[0], h=size[1])
    assert not rr.errors and "#ERR" not in svg and svg.count("<svg") >= 1


def test_builtin_detail_qr_is_the_mes_scanner_code():
    t = label_builtin.builtin_template("detail")
    env = label_vars.sample_env("part")
    svg, r = render(t, env=env)
    n, d = label_tpl.qr_cells(env["part.qr"], "m", False)
    assert env["part.qr"] == "MXK:1000123:7:1/2" and d in svg and "MXK:" not in svg
    assert 'font-size="4.2"' in svg and ">748 × 468 × 16<" in svg and "карта 3" in svg
    # QR o'chirilsa — yo'q; parametrlar qiymatlari bilan boshqariladi
    svg2, _ = render(t, env=env, params={"qr": False, "show_edges": False, "show_product": False, "show_map": False})
    assert d not in svg2 and "карта" not in svg2 and "Шкаф трёхдверный" not in svg2 and "<svg x=" not in svg2


def test_builtin_templates_are_independent_copies():
    a = label_builtin.builtin_template("detail")
    a["elements"].clear()
    assert label_builtin.builtin_template("detail")["elements"]
    assert label_builtin.builtin_template("detail", "uz")["name"] != label_builtin.builtin_template("detail", "ru")["name"]
    assert label_builtin.builtin_template("zzz") is None


def test_template_params_coercion():
    t = tpl([], params=[{"name": "d", "type": "double", "default": 2}, {"name": "i", "type": "integer", "default": 3},
                        {"name": "s", "type": "string", "default": "q"}, {"name": "b", "type": "boolean", "default": False}])
    r = Renderer(normalize_template(t), width_mm=58, height_mm=40, params={"d": "1,5x", "i": "7.9", "b": "yes"})
    assert r.values == {"d": 0.0, "i": 7, "s": "q", "b": True}


def test_deepcopy_safety_of_normalized_template():
    t = tpl([{"t": "text", "x": 1, "y": 1, "text": "'a'"}])
    n = normalize_template(t)
    n["elements"].append({"t": "nope"})
    assert len(t["elements"]) == 1                                                  # kirish obyekti o'zgarmaydi
    assert copy.deepcopy(n) == n
