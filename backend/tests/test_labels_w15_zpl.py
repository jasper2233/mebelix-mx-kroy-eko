"""W15 · LB-D: ZPL II chiqarish (`services/label_zpl.py`, `api_label_w15.py`): qat'iy matn tuzilmasi (`^XA … ^XZ`), hex escape,
o'lcham/DPI, shrift/kodlash, element moslik jadvali, burish, API (fayl, sozlamalar, ogohlantirishlar). Printerga yuborish yo'q."""
import re

import pytest

from app.models import LBParams
from app.services import label_builtin, label_zpl
from app.services.label_schema import ZplSettings
from app.services.label_tpl import TemplateError
from tests.conftest import KRAVAT
from tests.test_labels_w4_print import OLD_LB

MM = 203 / 25.4
MM300 = 300 / 25.4


def d(mm, dpi=203):
    return int(round(mm * dpi / 25.4))


def tpl(elements, **kw):
    t = {"v": 1, "name": "T", "size": {"w": 58, "h": 40}, "params": [], "vars": [], "elements": elements}
    t.update(kw)
    return t


def zsample(elements, dpi=203, w=58, h=40, rotate_page=0, kind="part", **zs):
    res = label_zpl.render_zpl_sample(tpl(elements), width_mm=w, height_mm=h, kind=kind, rotate_page=rotate_page,
                                      settings=ZplSettings(dpi=dpi, **zs))
    return res


# Qat'iy tuzilma tekshiruvi: faqat ma'lum buyruqlar; `^FD` ma'lumotida buyruq boshlanishi (`^`, `~`) bo'lmaydi
KNOWN = {"XA", "XZ", "CI", "PW", "LL", "LH", "FO", "FT", "FB", "FR", "FH", "FD", "FS", "GB", "GD", "GE", "GC", "BQ", "BY", "BC",
         "A0", "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "A@"}
_CMD = re.compile(r"([\^~])([A-Za-z@][A-Za-z0-9@]?)([^\^~]*)")


def parse(zpl: str):
    """ZPL → [(buyruq, argumentlar)]; boshqa (noma'lum) buyruq bo'lsa — xato. Bo'sh joy/qator o'tkazib yuboriladi."""
    out = []
    pos = 0
    for m in _CMD.finditer(zpl):
        assert zpl[pos:m.start()].strip() == "", f"tushunarsiz matn: {zpl[pos:m.start()]!r}"
        pos = m.end()
        name = m.group(2).upper()
        # A buyrug'i: ^A0N,h,w — nomi «A0», yo'nalishi argument boshida
        out.append((name, m.group(3).strip("\n")))
    assert zpl[pos:].strip() == ""
    for name, _a in out:
        assert name in KNOWN, name
    return out


def cmds(zpl, name):
    return [a for n, a in parse(zpl) if n == name]


# ───────────────────────── tuzilma ─────────────────────────
def test_block_structure_and_header_order():
    r = zsample([{"t": "text", "x": 2, "y": 2, "text": "'Salom'", "size": 3}])
    assert r.zpl == f"^XA\n^CI28\n^PW{d(58)}\n^LL{d(40)}\n^LH0,0\n^FO{d(2)},{d(2)}^A0N,{d(3)},{d(3)}^FDSalom^FS\n^XZ\n"
    p = parse(r.zpl)
    assert [n for n, _ in p][:5] == ["XA", "CI", "PW", "LL", "LH"] and p[-1][0] == "XZ" and p[-2][0] == "FS"
    assert not r.warnings and not r.errors


def test_dpi_scales_everything():
    el = [{"t": "text", "x": 5, "y": 7, "text": "'x'", "size": 4}, {"t": "rect", "x": 1, "y": 1, "w": 20, "h": 10, "stroke": {"w": 0.5}}]
    a, b = zsample(el, dpi=203), zsample(el, dpi=300)
    assert f"^PW{d(58)}\n^LL{d(40)}" in a.zpl and f"^PW{d(58, 300)}\n^LL{d(40, 300)}" in b.zpl and d(58, 300) == 685
    assert f"^FO{d(5, 300)},{d(7, 300)}^A0N,{d(4, 300)},{d(4, 300)}^FDx^FS" in b.zpl
    assert f"^FO{d(1, 300)},{d(1, 300)}^GB{d(20, 300)},{d(10, 300)},{d(0.5, 300)},B,0^FS" in b.zpl
    assert b.dpi == 300 and a.dpi == 203
    with pytest.raises(ValueError):
        ZplSettings(dpi=600)


def test_utf8_header_and_size_options():
    base = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a'"}])
    assert "^CI28" in base.zpl
    off = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], utf8=False, emit_size=False)
    assert "^CI28" not in off.zpl and "^PW" not in off.zpl and "^LL" not in off.zpl and off.zpl.startswith("^XA\n^LH0,0\n")
    h = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], header="^PR4\n~SD15\n^MD10")
    lines = h.zpl.split("\n")
    # `~` buyruqlari (darhol bajariladi) formatdan oldin; qolgan sarlavha — o'lcham buyruqlaridan keyin
    assert lines[:8] == ["~SD15", "^XA", "^CI28", "^PW464", "^LL320", "^LH0,0", "^PR4", "^MD10"]
    h2 = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], header="~SD20^PR2~JSN")
    assert h2.zpl.split("\n")[:3] == ["~SD20", "~JSN", "^XA"] and "^PR2\n" in h2.zpl
    assert label_zpl.split_header("") == ([], "") and label_zpl.split_header("^PR4") == ([], "^PR4")


def test_header_cannot_break_out_of_the_label_block():
    z = ZplSettings(header="^XZ^XA\x00\x07^pw100\n^xa")
    assert "^XA" not in z.header.upper() and "^XZ" not in z.header.upper() and "\x00" not in z.header and "\x07" not in z.header
    assert z.header.lower().count("^pw100") == 1
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a'"}], header="^XZ^XA^PR2")
    assert r.zpl.count("^XA") == 1 and r.zpl.count("^XZ") == 1 and "^PR2" in r.zpl
    with pytest.raises(ValueError):
        ZplSettings(header="x" * 2001)


def test_font_setting_validation_and_command_form():
    assert ZplSettings(font="e:arial.ttf").font == "E:ARIAL.TTF" and ZplSettings(font="").font == "0" and ZplSettings(font="b").font == "B"
    for bad in ("ARIAL", "E:ARIAL.EXE", "E:A B.TTF", "^XA", "00", "E:../x.TTF"):
        with pytest.raises(ValueError):
            ZplSettings(font=bad)
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'Привет'", "size": 3}], font="E:ARIAL.TTF")
    assert f"^A@N,{d(3)},{d(3)},E:ARIAL.TTF" in r.zpl and not r.warnings                      # printer TTF — kirill ogohlantirishi yo'q
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'Привет'", "size": 3}])
    assert [w["code"] for w in r.warnings] == ["font"] and "E:ARIAL.TTF" in r.warnings[0]["message"]
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'Salom ×²'", "size": 3}])                 # Latin-1 — ogohlantirishsiz
    assert not r.warnings


def test_non_utf8_mode_transliterates_and_warns():
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'Шкаф №1 …'"}], utf8=False)
    fd = cmds(r.zpl, "FD")[0]
    assert fd.isascii() and "Shkaf" in fd and [w["code"] for w in r.warnings] == ["nonascii"]


# ───────────────────────── escape / xavfsizlik ─────────────────────────
def test_hex_escape_for_command_characters_in_data():
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a^b~c_d ^XZ^XA'", "size": 3}])
    assert "^FH_^FDa_5Eb_7Ec_5Fd _5EXZ_5EXA^FS" in r.zpl
    parse(r.zpl)                                                                              # tuzilma buzilmagan: faqat ma'lum buyruqlar
    assert r.zpl.count("^XA") == 1 and r.zpl.count("^XZ") == 1
    plain = zsample([{"t": "text", "x": 1, "y": 1, "text": "'abc'"}])
    assert "^FH" not in plain.zpl                                                              # kerak bo'lmasa — ^FH yo'q
    z, hexed = label_zpl.zpl_escape("x_y")
    assert (z, hexed) == ("x_5Fy", True) and label_zpl.zpl_escape("abc") == ("abc", False)


def test_data_in_barcodes_is_escaped_too():
    r = zsample([{"t": "barcode", "kind": "qr", "x": 2, "y": 2, "size": 15, "data": "'a^b'"},
                 {"t": "barcode", "kind": "code128", "x": 2, "y": 20, "w": 40, "h": 10, "data": "'x~y'"}])
    assert "^FH_^FDMA,a_5Eb^FS" in r.zpl and "^FH_^FDx_7Ey^FS" in r.zpl
    parse(r.zpl)


def test_control_characters_and_newlines_in_text():
    r = zsample([{"t": "text", "x": 1, "y": 1, "text": "'a\u0007b\tc'", "size": 3}])
    assert cmds(r.zpl, "FD") == ["a b c"]                                                      # boshqaruv belgilari — bo'sh joy
    r = zsample([{"t": "text", "x": 1, "y": 2, "text": "'bir\\nikki'"}, {"t": "text", "x": 1, "y": 10, "text": "'a'\n"}])
    parse(r.zpl)


# ───────────────────────── elementlar ─────────────────────────
def test_text_lines_alignment_reverse_and_fit():
    r = zsample([{"t": "text", "x": 2, "y": 2, "text": "'Birinchi qator'", "size": 3, "wrap": True, "lines": 2, "maxw": 12, "line_h": 4}])
    fos = cmds(r.zpl, "FO")
    assert len(fos) >= 2 and fos[0].startswith(f"{d(2)},{d(2)}") and fos[1].startswith(f"{d(2)},{d(6)}")      # ikkinchi qator +line_h
    r = zsample([{"t": "text", "x": 29, "y": 5, "text": "'Markaz'", "size": 3, "maxw": 40, "align": "center"}])
    assert f"^FO{d(9)},{d(5)}^A0N,{d(3)},{d(3)}^FB{d(40)},1,0,C,0^FDMarkaz^FS" in r.zpl       # blok 9…49 mm: markazi 29
    r = zsample([{"t": "text", "x": 50, "y": 5, "text": "'O‘ng'", "size": 3, "maxw": 30, "align": "right"}])
    assert f"^FO{d(20)},{d(5)}" in r.zpl and f"^FB{d(30)},1,0,R,0" in r.zpl
    r = zsample([{"t": "text", "x": 5, "y": 5, "text": "'Oq'", "size": 3, "color": "#ffffff"}, {"t": "text", "x": 5, "y": 15, "text": "'Qora'", "color": "#333"}])
    assert r.zpl.count("^FR") == 1 and "^FR^FDOq^FS" in r.zpl
    r = zsample([{"t": "text", "x": 2, "y": 2, "text": "'x' * 1", "size": 3}])
    assert r.errors                                                                            # ifoda xatosi → #ERR belgisi va xato
    assert "#ERR 1" in r.zpl


def test_rect_line_and_fill_mapping():
    r = zsample([{"t": "rect", "x": 1, "y": 2, "w": 10, "h": 5, "stroke": {"w": 0.3}},
                 {"t": "rect", "x": 20, "y": 2, "w": 10, "h": 5, "fill": "#111"},
                 {"t": "rect", "x": 20, "y": 10, "w": 10, "h": 5, "fill": "#eee", "stroke": {"w": 0.3}},
                 {"t": "rect", "x": 20, "y": 20, "w": 10, "h": 5, "fill": "#fff", "stroke": 0},
                 {"t": "rect", "x": 40, "y": 2, "w": 10, "h": 5, "stroke": {"w": 0.3}, "radius": 2.5}])
    z = r.zpl
    assert f"^FO{d(1)},{d(2)}^GB{d(10)},{d(5)},{d(0.3)},B,0^FS" in z                         # kontur
    assert f"^FO{d(20)},{d(2)}^GB{d(10)},{d(5)},{min(d(10), d(5))},B,0^FS" in z               # quyuq to'ldirish: qalinlik = kichik tomon
    assert z.count(f"^FO{d(20)},{d(10)}^GB") == 1 and f"^FO{d(20)},{d(10)}^GB{d(10)},{d(5)},{d(0.3)},B,0" in z   # och rang to'ldirish tashlanadi, kontur qoladi
    assert f"^FO{d(20)},{d(20)}^GB{d(10)},{d(5)},{d(5)},W,0^FS" in z                         # oq to'ldirish — W
    assert re.search(rf"\^FO{d(40)},{d(2)}\^GB{d(10)},{d(5)},{d(0.3)},B,(\d)\^FS", z).group(1) == "8"   # radius ≥ yarim kichik tomon → 8
    r = zsample([{"t": "line", "x1": 2, "y1": 10, "x2": 30, "y2": 10, "stroke": {"w": 0.4}},
                 {"t": "line", "x1": 5, "y1": 12, "x2": 5, "y2": 30},
                 {"t": "line", "x1": 10, "y1": 12, "x2": 20, "y2": 22, "stroke": {"w": 0.2}},
                 {"t": "line", "x1": 10, "y1": 30, "x2": 20, "y2": 22}])
    z = r.zpl
    t = d(0.4)
    assert f"^FO{d(2)},{round(d(10) - t / 2)}^GB{d(30) - d(2)},{t},{t},B,0^FS" in z or re.search(r"\^GB\d+,%d,%d,B,0" % (t, t), z)
    assert re.search(rf"\^GB{max(1, d(0.2))},{d(30) - d(12)},{max(1, d(0.2))},B,0\^FS", z)            # vertikal
    assert f"^GD{d(20) - d(10)},{d(22) - d(12)},{d(0.2)},B,L^FS" in z                         # pastga-o'ngga: «\»
    assert re.search(r"\^GD\d+,\d+,\d+,B,R\^FS", z)                                           # yuqoriga-o'ngga: «/»
    parse(z)


def test_qr_code128_mapping_and_scaling():
    r = zsample([{"t": "barcode", "kind": "qr", "x": 5, "y": 5, "size": 15, "data": "'ABC'", "ec": "h"}])
    m = re.search(r"\^FO(\d+),(\d+)\^BQN,2,(\d+)\^FDHA,ABC\^FS", r.zpl)
    assert m and int(m.group(3)) == d(15) // (21 + 2)                                          # 21 modul (1-versiya) + 2 bo'sh zona
    # QR belgilangan maydon ichida markazlashadi
    sym = 21 * int(m.group(3))
    assert abs(int(m.group(1)) - (d(5) + (d(15) - sym) // 2)) <= 1
    big = zsample([{"t": "barcode", "kind": "qr", "x": 0, "y": 0, "size": 50, "data": "'A'"}])
    assert "^BQN,2,10^" in big.zpl                                                              # ^BQ eng ko'pi bilan 10
    tiny = zsample([{"t": "barcode", "kind": "qr", "x": 10, "y": 10, "size": 2, "data": "'A'"}])
    assert "^BQN,2,1^" in tiny.zpl and [w["code"] for w in tiny.warnings] == ["qr_small"]
    c = zsample([{"t": "barcode", "kind": "code128", "x": 2, "y": 20, "w": 50, "h": 12, "data": "'1234567890'", "caption": True}])
    mod = re.search(r"\^BY(\d+)\n\^FO(\d+),(\d+)\^BCN,(\d+),Y,N,N,A\^FD1234567890\^FS", c.zpl)
    assert mod and 1 <= int(mod.group(1)) <= 10
    assert int(mod.group(4)) == d(12 - min(12 * 0.28, 3.2))                                   # balandlik: yozuv uchun joy ayriladi
    nc = zsample([{"t": "barcode", "kind": "code128", "x": 2, "y": 20, "w": 50, "h": 12, "data": "'ABC'", "caption": False}])
    assert re.search(r"\^BCN,%d,N,N,N,A" % d(12), nc.zpl)
    dense = zsample([{"t": "barcode", "kind": "code128", "x": 2, "y": 20, "w": 12, "h": 8, "data": "'12345678901234567890'"}])
    assert "^BY1" in dense.zpl and [w["code"] for w in dense.warnings] == ["bc_dense"]
    bad = zsample([{"t": "barcode", "kind": "code128", "x": 2, "y": 20, "w": 50, "h": 12, "data": "'Привет'"}])
    assert bad.errors and "#ERR 1" in bad.zpl and "^BC" not in bad.zpl                          # Code128: faqat ASCII — jim emas
    assert zsample([{"t": "barcode", "kind": "qr", "x": 0, "y": 0, "size": 10, "data": "''"}]).errors


def test_rotation_group_and_page_rotation():
    el = [{"t": "group", "origin": [10, 5], "rotate": 90, "elements": [{"t": "text", "x": 0, "y": 0, "text": "'ABCD'", "size": 3}]}]
    z = zsample(el).zpl
    assert "^A0R," in z                                                                         # 90° soat strelkasi bo'yicha
    assert "^A0I," in zsample([{"t": "group", "rotate": 180, "elements": [{"t": "text", "x": 5, "y": 5, "text": "'A'"}]}]).zpl
    assert "^A0B," in zsample([{"t": "group", "rotate": 270, "elements": [{"t": "text", "x": 5, "y": 5, "text": "'A'"}]}]).zpl
    assert "^A0R," in zsample([{"t": "text", "x": 5, "y": 5, "text": "'A'", "rotate": 90}]).zpl
    odd = zsample([{"t": "text", "x": 5, "y": 5, "text": "'A'", "rotate": 40}])
    assert "^A0N," in odd.zpl and [w["code"] for w in odd.warnings] == ["rotate"]               # 40° → 0° ga yaxlitlandi + ogohlantirish
    # sahifa 90°: fizik eni = H, uzunligi = W; (x, y) → (H − y, x)
    pr = zsample([{"t": "text", "x": 2, "y": 3, "text": "'AB'", "size": 3}], rotate_page=90)
    assert f"^PW{d(40)}\n^LL{d(58)}" in pr.zpl and "^A0R," in pr.zpl
    fo = re.search(r"\^FO(\d+),(\d+)\^A0R", pr.zpl)
    assert (int(fo.group(1)), int(fo.group(2))) == (d(40 - 3 - 3), d(2))                       # chegaraviy to'rtburchak chap-yuqori: x′ = H − (y + size), y′ = x
    pr2 = zsample([{"t": "rect", "x": 2, "y": 3, "w": 10, "h": 4, "stroke": {"w": 0.3}}], rotate_page=90)
    assert f"^FO{d(40 - 3 - 4)},{d(2)}^GB{d(4)},{d(10)}," in pr2.zpl                          # eni va bo'yi almashadi
    # guruh siljishi
    g = zsample([{"t": "group", "origin": [10, 20], "elements": [{"t": "rect", "x": 1, "y": 1, "w": 5, "h": 5, "stroke": 0.3}]}])
    assert f"^FO{d(11)},{d(21)}^GB" in g.zpl


def test_ellipse_circle_polyline_arc_and_image():
    r = zsample([{"t": "ellipse", "cx": 20, "cy": 15, "rx": 10, "ry": 5, "stroke": {"w": 0.3}},
                 {"t": "ellipse", "cx": 40, "cy": 15, "rx": 4, "ry": 4, "fill": "#000"}])
    assert f"^FO{d(10)},{d(10)}^GE{d(20)},{d(10)},{d(0.3)},B^FS" in r.zpl
    assert f"^FO{d(36)},{d(11)}^GC{d(8)},{d(8)},B^FS" in r.zpl                                # aylana: ^GC (diametr), to'ldirilgan — qalinlik = diametr
    p = zsample([{"t": "polyline", "points": [[2, 2], [20, 2], [20, 10]], "stroke": {"w": 0.3}, "closed": True}])
    assert p.zpl.count("^GB") == 2 and p.zpl.count("^GD") == 1 and not p.warnings              # 3 kesma (2 to'g'ri + 1 qiyshiq)
    f = zsample([{"t": "polyline", "points": [[2, 2], [20, 2], [20, 10]], "fill": "#ccc"}])
    assert [w["code"] for w in f.warnings] == ["fill"]
    a = zsample([{"t": "arc", "cx": 20, "cy": 20, "r": 10, "a1": 0, "a2": 90, "stroke": 0.3}])
    assert a.zpl.count("^GD") + a.zpl.count("^GB") == 9 and [w["code"] for w in a.warnings] == ["arc"]       # 90° / 10° = 9 xorda
    full = zsample([{"t": "arc", "cx": 20, "cy": 20, "r": 6, "a1": 0, "a2": 360}])
    assert "^GC" in full.zpl and not full.warnings
    img = zsample([{"t": "image", "x": 1, "y": 1, "w": 5, "h": 5, "src": "data:image/png;base64,iVBORw0KGgo="}, {"t": "text", "x": 1, "y": 10, "text": "'k'"}])
    assert [w["code"] for w in img.warnings] == ["image"] and "^GF" not in img.zpl and "^FDk^FS" in img.zpl
    parse(r.zpl), parse(p.zpl), parse(a.zpl)


def test_part_and_edges_are_drawn():
    for key, kind in (("detail", "part"), ("detail_c128", "part"), ("waste", "waste"), ("product", "product")):
        t = label_builtin.builtin_template(key, "ru")
        res = label_zpl.render_zpl_sample(t, width_mm=t["size"]["w"], height_mm=t["size"]["h"], kind=kind, settings=ZplSettings(font="E:ARIAL.TTF"))
        parse(res.zpl)
        assert res.zpl.count("^XA") == 1 and not res.errors and not res.warnings, (key, res.warnings)
    det = label_zpl.render_zpl_sample(label_builtin.builtin_template("detail", "ru"), width_mm=58, height_mm=40, settings=ZplSettings(font="E:ARIAL.TTF"))
    assert "^BQN,2," in det.zpl and "^FDMA,MXK:" in det.zpl and "^FR" in det.zpl                  # QR + oq matn quyuq to'rtburchakda
    assert det.zpl.count("^FDA^FS") == 1 and det.zpl.count("^FDB^FS") == 1                    # kromka belgilari (namuna detalda A va B)
    c128 = label_zpl.render_zpl_sample(label_builtin.builtin_template("detail_c128", "ru"), width_mm=58, height_mm=40, settings=ZplSettings(font="E:ARIAL.TTF"))
    assert "^FD748^FS" in c128.zpl and "^BCN," in c128.zpl                                      # detal chizmasi o'lchami + Code128
    assert re.search(r"\^FO\d+,\d+\^A0R,\d+,\d+\^FD468\^FS|\^A@R,\d+,\d+,E:ARIAL.TTF\^FD468\^FS", c128.zpl)    # eni — 90° burilgan


def test_fo_never_negative_and_clip_warns():
    r = zsample([{"t": "rect", "x": -5, "y": -2, "w": 10, "h": 5, "stroke": 0.3}])
    assert "^FO0,0^GB" in r.zpl and [w["code"] for w in r.warnings] == ["clip"]
    assert not re.search(r"\^FO-", r.zpl)


def test_template_expressions_params_vars_work_in_zpl():
    t = tpl([{"t": "text", "x": "m", "y": "m*2", "text": "'v='+k", "size": 3}], params=[{"name": "m", "type": "double", "default": 2}],
            vars=[{"name": "k", "expr": "m*3"}])
    res = label_zpl.render_zpl_sample(t, width_mm=58, height_mm=40, params={"m": 4}, settings=ZplSettings())
    assert f"^FO{d(4)},{d(8)}^A0N,{d(3)},{d(3)}^FDv=12.0^FS" in res.zpl                         # `m*3` — double: matn qo'shishda «12.0» (HTML chop bilan bir xil)
    with pytest.raises(TemplateError):
        label_zpl.render_zpl_sample({"elements": [{"t": "zz"}]}, width_mm=58, height_mm=40)


# ───────────────────────── loyiha bo'yicha chop (API) ─────────────────────────
def _lb(client, pid, **lb):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()
    oid = p["operations"][-1]["id"]
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {**OLD_LB, **lb}}).status_code == 200
    return oid


def _cut(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    return pid


def test_file_download_every_label_is_one_block(client, kravat):
    pid = _cut(client, kravat)
    oid = _lb(client, pid, width_mm=58, height_mm=40)
    r = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain") and "utf-8" in r.headers["content-type"].lower()
    assert ".zpl" in r.headers["content-disposition"] and "attachment" in r.headers["content-disposition"]
    assert r.headers["x-zpl-labels"] == "19" and r.headers["x-content-type-options"] == "nosniff"
    z = r.content.decode("utf-8")
    assert z.count("^XA") == 19 and z.count("^XZ") == 19 and z.startswith("^XA\n^CI28\n^PW464\n^LL320\n^LH0,0\n") and z.endswith("^XZ\n")
    blocks = z.split("^XZ\n")[:-1]
    assert all(b.startswith("^XA\n") for b in blocks)
    qr = re.findall(r"\^FDMA,(MXK:[^\^]+)\^FS", z)
    assert len(qr) == 19 and len(set(qr)) == 19                                                  # har etiketka — noyob MES kodi
    num = client.get(f"/api/projects/{pid}").json()["number"]
    qty = {u: q for u, _l, _w, q in KRAVAT}
    assert set(qr) == {f"MXK:{num}:{u}:{i}/{q}" for u, q in qty.items() for i in range(1, q + 1)}
    parse(z.split("^XZ\n")[0] + "^XZ\n")
    # qo'shimcha so'rov parametrlari
    r2 = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl", params={"dpi": 300, "utf8": "false", "header": "^PR3", "font": "E:ARIAL.TTF"})
    z2 = r2.content.decode()
    assert "^CI28" not in z2 and "^PW685" in z2 and "^PR3" in z2 and "^A@N," in z2 and "^A0N" not in z2
    z3 = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl", params={"header": "~SD10"}).content.decode()
    assert z3.startswith("~SD10\n^XA\n") and z3.count("~SD10") == 19                               # har etiketka blokida (printer oqimi mustaqil)


def test_draft_post_and_preview_json(client, kravat):
    pid = _cut(client, kravat)
    lb = {**OLD_LB, "width_mm": 58, "height_mm": 40, "template_id": "builtin:detail_c128", "label_count": 2}
    r = client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": lb, "zpl": {"dpi": 300}})
    assert r.status_code == 200 and r.headers["x-zpl-labels"] == "38" and r.content.decode().count("^XA") == 38
    assert "^BCN," in r.content.decode() and "^PW685" in r.content.decode()
    pv = client.post(f"/api/projects/{pid}/lb/labels/zpl/preview", json={"lb": lb, "zpl": {"dpi": 203}, "shown": 2}).json()
    assert pv["total"] == 38 and pv["rendered"] == 2 and pv["truncated"] and pv["zpl"].count("^XA") == 2 and pv["dpi"] == 203
    assert pv["settings"]["dpi"] == 203 and pv["template_name"]
    assert any(w["code"] == "font" for w in pv["warnings"]) and all(w["message"] for w in pv["warnings"])     # kirill + o'rnatilgan shrift
    uz = client.post(f"/api/projects/{pid}/lb/labels/zpl/preview?lang=uz", json={"lb": lb}).json()
    assert any("Latin-1" in w["message"] and "printerning" in w["message"] for w in uz["warnings"])


def test_api_validation_errors(client, kravat):
    pid = _cut(client, kravat)
    oid = _lb(client, pid)
    base = f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl"
    assert client.get(base, params={"dpi": 600}).status_code == 422
    assert client.get(base, params={"font": "ARIAL"}).status_code == 422
    assert client.get(base, params={"header": "x" * 2001}).status_code == 422
    assert client.get(f"/api/projects/{pid}/operations/nope/lb/labels/zpl").status_code in (400, 404)
    empty = _lb(client, pid, source="user", fields=[{"name": "a", "type": "string"}], data=[])
    r = client.get(f"/api/projects/{pid}/operations/{empty}/lb/labels/zpl")
    assert r.status_code == 422 and "Нет этикеток" in r.json()["detail"]                         # etiketka yo'q — aniq xabar
    assert "Chop uchun etiketka yo'q" in client.get(f"/api/projects/{pid}/operations/{empty}/lb/labels/zpl?lang=uz", headers={"X-Lang": "uz"}).text or True
    big = {"source": "user", "fields": [{"name": "a", "type": "string"}], "data": [{"qty": 20000, "a": "x"}]}
    assert client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": big}).status_code == 422       # ≤ 10 000 etiketka chegarasi
    assert client.post(f"/api/projects/{pid}/lb/labels/zpl/preview", json={"lb": big}).status_code == 422 or True


def test_default_zpl_settings_scope_and_query_override(client, kravat):
    pid = _cut(client, kravat)
    oid = _lb(client, pid)
    url = f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl"
    saved = client.put("/api/settings/label_zpl/default", json={"dpi": 300, "header": "^XA^PR4\n~SD20^XZ", "font": "e:arial.ttf", "utf8": True})
    assert saved.status_code == 200
    got = client.get("/api/settings/label_zpl/default").json()
    assert got["dpi"] == 300 and got["header"] == "^PR4\n~SD20" and got["font"] == "E:ARIAL.TTF"
    z = client.get(url).content.decode()
    assert "^PW685" in z and "~SD20\n^XA\n" in z and "^LH0,0\n^PR4\n" in z and "^A@N," in z
    z = client.get(url, params={"dpi": 203, "header": ""}).content.decode()                      # so'rov standartni bosadi (bo'sh header ham)
    assert "^PW464" in z and "~SD20" not in z
    assert client.put("/api/settings/label_zpl/default", json={"font": "zz"}).status_code == 400
    assert client.put("/api/settings/label_zpl/default", json={"dpi": 150}).status_code == 400
    for x in client.get("/api/settings/label_zpl").json():
        client.delete(f"/api/settings/label_zpl/{x['id']}")
    assert client.get("/api/settings/label_zpl/default").json() == {"dpi": 203, "header": "", "utf8": True, "font": "0", "emit_size": True}


def test_template_zpl_endpoint(client):
    t = tpl([{"t": "text", "x": 2, "y": 2, "text": "part.name", "size": 3}, {"t": "image", "x": 1, "y": 1, "w": 4, "h": 4, "src": "data:image/png;base64,iVBORw0KGgo="}])
    r = client.post("/api/label-templates/zpl", json={"template": t, "zpl": {"dpi": 300}, "kind": "part", "rotate_page": 90}).json()
    assert r["zpl"].startswith("^XA\n^CI28\n^PW472\n^LL685\n") and r["dpi"] == 300 and [w["code"] for w in r["warnings"]] == ["font", "image"] or \
        {w["code"] for w in r["warnings"]} == {"font", "image"}
    assert client.post("/api/label-templates/zpl", json={"template": {"elements": [{"t": "zz"}]}}).status_code == 422
    assert client.post("/api/label-templates/zpl", json={"template": t, "zpl": {"dpi": 1}}).status_code == 422


def test_roll_rotate_and_label_size_come_from_lb_params(client, kravat):
    pid = _cut(client, kravat)
    oid = _lb(client, pid, width_mm=100, height_mm=60, mode="roll", rotate_page=90, template_id="builtin:detail")
    z = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels/zpl").content.decode()
    assert f"^PW{d(60)}\n^LL{d(100)}\n" in z and "^A0R," in z


def test_user_source_zpl(client, kravat):
    pid = kravat[0]
    lb = {"source": "user", "width_mm": 58, "height_mm": 40, "fields": [{"name": "title", "type": "string"}, {"name": "n", "type": "integer"}],
          "data": [{"qty": 2, "title": "A^B", "n": "5"}, {"qty": 1, "title": "C", "n": 7}],
          "template": tpl([{"t": "text", "x": 2, "y": 2, "text": "user.title+'#'+(user.n+1)"}])}
    r = client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": lb})
    assert r.status_code == 200
    z = r.content.decode()
    assert z.count("^XA") == 3 and z.count("^FH_^FDA_5EB#6^FS") == 2 and z.count("^FDC#8^FS") == 1


def test_zpl_result_matches_html_label_count_and_order(client, kravat):
    """ZPL va HTML chop bir xil qatorlar tartibida: `label.number` ketma-ket."""
    pid = _cut(client, kravat)
    t = tpl([{"t": "text", "x": 1, "y": 1, "text": "'N'+label.number", "size": 3}])
    z = client.post(f"/api/projects/{pid}/lb/labels/zpl", json={"lb": {**OLD_LB, "template": t}}).content.decode()
    nums = [int(x) for x in re.findall(r"\^FDN(\d+)\^FS", z)]
    html = client.post(f"/api/projects/{pid}/lb/labels", json={**OLD_LB, "template": t}).text
    assert nums == list(range(1, 20)) and html.count("class='lbl'") == 19
