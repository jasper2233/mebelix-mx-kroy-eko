# -*- coding: utf-8 -*-
"""«Чёрно-белая печать» (2026-11-14, foydalanuvchi talabi): chop / PDF oq-qora — ekrandagi ranglardan qat'i nazar. Rangli zaliv
printerda qora dog' bo'lib chiqadi: detal / chiqindi / qoldiq — oq fon, qora chiziq; chiqindi shtrix, qoldiq punktir chegara.
Ekrandagi karta (`/map-svg`, style=None) rangli qoladi."""
import re

from app.models import PrintSettings
from app.services import render
from test_x1015b_print import _project

HEX = re.compile(r'(?:fill|stroke|color)="(#[0-9a-fA-F]{3,6})"|(?:background(?:-color)?|color)\s*:\s*(#[0-9a-fA-F]{3,6})')


def _colors(html: str) -> set[str]:
    return {(a or b).lower() for a, b in HEX.findall(html)}


def test_report_is_black_and_white_by_default():
    proj, cs, _el, _xnc, _m = _project()
    html = render.project_report_html(proj, PrintSettings(map_part_fill="#ff8800"), "ru")
    assert _colors(html) <= {"#000", "#fff"}, _colors(html) - {"#000", "#fff"}
    assert "<svg" in html and 'fill="url(#' in html                    # chiqindi — shtrix (zaliv emas)


def test_map_svg_mono_parts_white_edges_black():
    proj, cs, _el, _xnc, m = _project()
    ps = PrintSettings()
    svg = render.map_svg(m, 800, None, proj, cs, ps.map_part_label, True, True, False, style=ps)
    assert _colors(svg) <= {"#000", "#fff"}
    assert "#ff0000" not in svg.lower() and "#f2a541" not in svg.lower()


def test_color_option_and_screen_map_keep_colors():
    proj, cs, _el, _xnc, m = _project()
    html = render.project_report_html(proj, PrintSettings(map_mono=False), "ru")
    assert "#F2A541" in html                                           # o'chirilsa — avvalgidek rangli
    svg = render.map_svg(m, 800, None, proj, cs, "number_name", True, True, False)     # ekran (style yo'q)
    assert "#F2A541" in svg and "#ff0000" in svg.lower()


def test_mono_html_rules():
    s = '<rect fill="#F2A541" stroke="#5A3A0A"/><text fill="#241400">1</text><td style="background: #e9ecef; color:#0f5c9a">x</td>'
    out = render.mono_html(s)
    assert out == '<rect fill="#fff" stroke="#000"/><text fill="#000">1</text><td style="background: #fff; color: #000">x</td>'
    assert render.mono_html('fill="url(#a)" fill="none" stroke="#fff"') == 'fill="url(#a)" fill="none" stroke="#fff"'
