"""Etiketka shabloni: «Кривая безье» (onlayn shablon buyruqlari ro'yxatidagi element, 2026-10-21) — tuzilma, SVG, ZPL."""
from app.services import label_tpl
from tests.test_labels_w15_elements import render, tags, tpl
from tests.test_labels_w15_zpl import cmds, zsample

BZ = {"t": "bezier", "x1": 4, "y1": 20, "c1x": 10, "c1y": 4, "c2x": 28, "c2y": 4, "x2": "label.width/2", "y2": 20, "stroke": {"w": 0.3}}


def test_bezier_type_known_and_renders_cubic_path():
    assert "bezier" in label_tpl.TYPES
    svg, r, root = render(tpl([BZ]), mark=True)
    paths = [p for p in tags(root, "path") if " C" in (p.get("d") or "")]
    assert len(paths) == 1 and paths[0].get("d").startswith("M4 20 C10 4 28 4 29 20")
    assert paths[0].get("data-v") == "4 20 10 4 28 4 29 20"            # muharrir tugunlari
    assert not r.errors


def test_bezier_zpl_is_polyline():
    res = zsample([BZ])
    zpl = res.zpl
    assert len(cmds(zpl, "GD")) + len(cmds(zpl, "GB")) >= 10           # egri chiziq — kesmalar ketma-ketligi
