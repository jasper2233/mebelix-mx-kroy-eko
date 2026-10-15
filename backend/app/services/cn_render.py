"""(CN) Нестинговый раскрой — kroy kartasi (SVG, haqiqiy kontur) va chop (hisobot) bo'limi (W16).

Karta: list (kulrang), foydali zona chegarasi (punktir), detallar — to'q sariq poligonlar (ichki kesimlar `evenodd` bilan bo'sh), raqam
(detal №) kontur markazida; qoldiqlar — ko'k to'rtburchaklar (Д№ + o'lcham; detal ichki kesimidagisi — `Д№ ⌂`); etiketka o'rni —
ingichka punktir to'rtburchak. Frontend (`features/cn/NestMap.tsx`) bilan bir xil ranglar.
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

from markupsafe import Markup, escape

from ..models import CutMap, Operation, OpCostBase, PrintSettings, Project
from .cn_calc import cn_cost, ensure_cn
from .render import (PART_FILL, PART_STROKE, REMNANT_FILL, REMNANT_SMALL, WASTE_FILL, _qr_svg, _table, fmt, map_header, safe_color)


def _path(ring: list, mirror: bool, L: float) -> str:
    pts = [(L - x if mirror else x, y) for x, y in ring]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


def nest_map_svg(m: CutMap, width_px: int = 900, project: Optional[Project] = None, op: Optional[Operation] = None,
                 label: str = "number_name", show_edges: bool = True, mirror: bool = False, style: Optional[PrintSettings] = None,
                 uid: str = "m", remnant_numbers: bool = True, show_label_spots: bool = False) -> str:
    L, W = float(m.sheet_length), float(m.sheet_width)
    cn = ensure_cn(op) if op is not None else None
    st = style if style is not None else PrintSettings()
    part_fill = safe_color(st.map_part_fill, PART_FILL)
    waste_fill = safe_color(st.map_waste_fill, WASTE_FILL)
    names = {p.id: p.name for p in op.parts} if op is not None else {}
    scale = width_px / L if L > 0 else 1.0
    fs = max(10.0 / scale, 8.0)
    sw = max(0.8, fs / 12)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(L)} {fmt(W)}" width="{width_px}" height="{W * scale:.0f}" '
           f'font-family="Arial, Helvetica, sans-serif">',
           f'<rect x="0" y="0" width="{fmt(L)}" height="{fmt(W)}" fill="{waste_fill}" stroke="#222" stroke-width="{sw:.1f}"/>']
    if cn is not None and cn.margin > 0:
        out.append(f'<rect x="{fmt(cn.margin)}" y="{fmt(cn.margin)}" width="{fmt(L - 2 * cn.margin)}" height="{fmt(W - 2 * cn.margin)}" '
                   f'fill="none" stroke="#7a7f88" stroke-width="{sw / 2:.2f}" stroke-dasharray="{fs:.1f} {fs / 2:.1f}"/>')
    for o in m.offcuts:
        if o.kind != "remnant":
            continue
        x = L - o.x - o.length if mirror else o.x
        out.append(f'<rect x="{fmt(x)}" y="{fmt(o.y)}" width="{fmt(o.length)}" height="{fmt(o.width)}" '
                   f'fill="{REMNANT_FILL if o.business else REMNANT_SMALL}" stroke="#3b6ea5" stroke-width="{sw:.1f}"/>')
        if remnant_numbers and min(o.length, o.width) * scale > 26:
            cx, cy = x + o.length / 2, o.y + o.width / 2
            txt = f'Д{int(o.number)}{" ⌂" if o.in_part else ""} {fmt(o.length)}×{fmt(o.width)}'
            need = len(txt) * fs * 0.58 * scale                       # taxminiy yozuv eni (piksel)
            rot = need > o.length * scale and o.width > o.length      # tor va baland qoldiq: yozuv vertikal
            tr = f' transform="rotate(-90 {fmt(cx)} {fmt(cy)})"' if rot else ""
            if need > max(o.length, o.width) * scale:
                txt = f'Д{int(o.number)}{" ⌂" if o.in_part else ""}'
            out.append(f'<text x="{fmt(cx)}" y="{fmt(cy)}" font-size="{fs:.1f}" fill="#1f3f66" text-anchor="middle" '
                       f'dominant-baseline="middle"{tr}>{txt}</text>')
    for p in m.placements:
        rings = [p.outline, *p.holes]
        d = " ".join(_path(r, mirror, L) for r in rings if r)
        out.append(f'<path d="{d}" fill="{part_fill}" fill-rule="evenodd" stroke="{PART_STROKE}" stroke-width="{sw:.1f}"/>')
        bx = L - p.x - p.length if mirror else p.x
        cx, cy = bx + p.length / 2, p.y + p.width / 2
        if p.label and not show_label_spots:
            lx = L - p.label[0] if mirror else p.label[0]
            cx, cy = lx, p.label[1]
        room = min(p.length, p.width) * scale
        uid_s = str(p.part_uid)
        if label in ("number", "number_name") and room > 6 * len(uid_s) + 6:
            out.append(f'<text x="{fmt(cx)}" y="{fmt(cy)}" font-size="{fs * 1.2:.1f}" font-weight="bold" fill="#241400" text-anchor="middle" '
                       f'dominant-baseline="middle">{escape(uid_s)}</text>')
        nm = names.get(p.part_id) or ""
        if label in ("name", "number_name") and nm and room > 60:
            n = max(3, int(p.length * scale / (fs * scale * 0.6 + 1)))
            out.append(f'<text x="{fmt(cx)}" y="{fmt(cy + fs * 1.3)}" font-size="{fs * 0.8:.1f}" fill="#3a2600" text-anchor="middle" '
                       f'dominant-baseline="middle">{escape(nm[:n])}</text>')
        if show_label_spots and p.label:
            lx, ly, lw, lh, la = p.label
            lx = L - lx if mirror else lx
            out.append(f'<rect x="{fmt(lx - lw / 2)}" y="{fmt(ly - lh / 2)}" width="{fmt(lw)}" height="{fmt(lh)}" fill="none" stroke="#1f6feb" '
                       f'stroke-width="{sw / 2:.2f}" stroke-dasharray="{fs / 3:.1f} {fs / 3:.1f}" transform="rotate({la:.1f} {fmt(lx)} {fmt(ly)})"/>')
    out.append("</svg>")
    return "".join(out)


# ───────────────────────── Hisobot bo'limi ─────────────────────────
def _kv(rows: list[tuple[str, str]]) -> str:
    return "<table class='kv'>" + "".join(f"<tr><td><b>{escape(a)}</b></td><td>{escape(str(b))}</td></tr>" for a, b in rows) + "</table>"


def cn_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    cn = ensure_cn(op)
    info = cn_cost(project, op)
    cur = project.currency
    mm_ = t["mm"]
    s = [f"<h2{cls}>{sec}. (CN) {t['cn']}: {('(' + escape(op.code) + ') ') if op.code else ''}{escape(op.name)}</h2>"]
    n = 0
    if ps.cn_params:
        n += 1
        rot = t["cn_rot_none"] if not cn.rot90 and not cn.rot_step else (
            t["cn_rot_90"] + (f", {t['cn_rot_free'].format(s=fmt(cn.rot_step))}" if cn.rot_step else ""))
        left = [(t["cn_thick"], f"{fmt(cn.thickness)} {mm_}"), (t["cn_tool"], f"{fmt(cn.tool_diameter)} {mm_}"),
                (t["cn_offset"], f"{fmt(cn.offset)} {mm_}"), (t["cn_gap"], f"{fmt(cn.part_gap)} {mm_}"),
                (t["cn_spacing"], f"{fmt(cn.spacing)} {mm_}"), (t["cn_margin"], f"{fmt(cn.margin)} {mm_}"), (t["cn_rot"], rot),
                (t["cn_grain"], t["cn_yes"] if cn.use_grain else t["cn_no"]), (t["cn_xnc"], t["cn_yes"] if cn.use_xnc_contours else t["cn_no"])]
        unit = t["cn_price_sheet"] if cn.cost_by_sheets else t["cn_price_m2"]
        approx = "≈ " if info.get("estimated") else ""
        base = {OpCostBase.CUT_LENGTH: "cn_base0", OpCostBase.PART_PERIMETER: "cn_base1", OpCostBase.PART_AREA: "cn_base2",
                OpCostBase.MATERIAL_AREA: "cn_base3"}[cn.op_cost_base]
        right = [(t["cn_price"], f"{fmt(cn.price)} {cur} ({unit})"), (t["cn_est_fill"], f"{fmt(cn.est_fill_percent)}%"),
                 (t["cn_usage"], f"{approx}{fmt(info['material_qty_m2'])} {t['u_m2']}"), (t["cn_cost_mat"], f"{fmt(op.cost_material)} {cur}"),
                 (t["cn_op_base"], t[base]), (t["cn_op_price"], f"{fmt(cn.op_price)} {cur}"), (t["cn_cost_op"], f"{fmt(op.cost_operation)} {cur}")]
        s.append(f"<h3>{n}. {t['cn_params']}</h3>")
        s.append(f"<table class='kv'><tr><td>{_kv(left)}</td><td>{_kv(right)}</td></tr></table>")
    res = op.result
    if ps.cn_parts:
        n += 1
        from .cn_calc import build_items
        ci = build_items(project, op)
        rows = []
        for p in op.parts:
            sh = ci.shapes.get(p.id)
            L, W = ci.sizes.get(p.id, (p.length, p.width))
            kind = t["cn_shape_rect"] if (sh is None or sh.is_rect) else t["cn_shape_contour"]
            rows.append([p.uid, fmt(L), fmt(W), kind, len(sh.holes) if sh else 0, fmt(round((sh.area if sh else L * W) / 1e6, 4)),
                         fmt(round((sh.perimeter if sh else 2 * (L + W)) / 1000, 3)), p.qty, p.used_qty, p.left_qty, escape(p.name)])
        s.append(f"<h3>{n}. {t['cn_parts_t']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["cn_shape"], t["cn_holes"], t["cn_area"], t["cn_perim"], t["qty"], t["used"], t["left"],
                         t["name"]], rows))
    if res and ps.cn_unplaced and res.unplaced:
        n += 1
        cnt = Counter(res.unplaced)
        rows = [[p.uid, fmt(p.length), fmt(p.width), cnt[p.id], escape(p.name)] for p in op.parts if p.id in cnt]
        s.append(f"<h3>{n}. {t['unplaced']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["qty"], t["name"]], rows))
    if res and ps.cn_sheets:
        n += 1
        rows = []
        tot_area = 0.0
        for i, sh in enumerate(op.sheets, 1):
            if not sh.used_qty:
                continue
            area = sh.length * sh.width / 1e6
            tot_area += area * sh.used_qty
            rows.append([i, fmt(sh.length), fmt(sh.width), fmt(round(area, 3)), sh.used_qty, fmt(round(area * sh.used_qty, 3))])
        rows.append(["", "", "", Markup("<b>{}:</b>").format(t["total"]), "", Markup("<b>{}</b>").format(fmt(round(tot_area, 3)))])
        s.append(f"<h3>{n}. {t['cn_sheets']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["area"], t["sheets_qty"], t["total_area"]], rows))
    if res and ps.cn_remnants and res.remnants:
        n += 1
        cnt2 = Counter((o.length, o.width, o.business, o.in_part) for o in res.remnants)
        rows = [[i, fmt(l), fmt(w), fmt(round(l * w / 1e6, 3)), c, t["cn_business"] if b else t["cn_plain"], (f"{t['cn_in_part']}{ip}" if ip else t["cn_free"])]
                for i, ((l, w, b, ip), c) in enumerate(sorted(cnt2.items(), key=lambda kv: -kv[0][0] * kv[0][1]), 1)]
        s.append(f"<h3>{n}. {t['cn_remnants']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["area"], t["qty"], t["cn_kind"], ""], rows))
    if res and ps.cn_maps:
        parts_by_id = {p.id: p for p in op.parts}
        cards: list[str] = []
        for m in res.maps:
            head = f"<div class='maphdr'>{escape(op.name)} &nbsp; {escape(map_header(m, res, ps.map_header_fields))}</div>"
            svg = nest_map_svg(m, 700, project, op, ps.map_part_label, ps.map_edges, ps.map_mirror, style=ps, uid=f"n{sec}m{m.index}",
                               remnant_numbers=ps.map_remnant_number)
            side = ""
            if ps.map_parts_list:
                cnt3 = Counter(pl.part_id for pl in m.placements)
                rows = []
                for pid, c in sorted(cnt3.items(), key=lambda kv: parts_by_id[kv[0]].uid if kv[0] in parts_by_id else 0):
                    p = parts_by_id.get(pid)
                    if p is not None:
                        pl = next(x for x in m.placements if x.part_id == pid)
                        rows.append([p.uid, fmt(p.length), fmt(p.width), c, fmt(pl.angle)])
                side += _table(["№", t["s_len"], t["s_wid"], t["s_qty"], "°"], rows)
            if ps.map_qr:
                qr = _qr_svg(f"MXK:{project.number}:{op.id}:{m.index}")
                if qr:
                    side += f"<div class='qr'>{qr}</div>"
            comment = f"<div class='muted'>{escape(m.comment)}</div>" if m.comment else ""
            cards.append(f"<div class='mapcard'>{head}<div class='mapwrap'><div>{svg}{comment}</div><div class='side'>{side}</div></div></div>")
        s.append("".join(cards))
    return "".join(s)
