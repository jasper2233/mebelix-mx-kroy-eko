"""(CL) Погонажный раскрой — kroy kartasi (1D, SVG) va chop (hisobot) bo'limi (W11).

Karta: polosa gorizontal; detallar — to'q sariq (raqam + uzunlik), otxod / деловой otxod — ko'k (Д№ + uzunlik), torsovka zonalari — kulrang,
propil — qora chiziq, kromka (ОВ/ОН — detal usti/osti, ОЛ/ОП — uchlari) — EL rangida. Polosa balandligi eniga mutanosib, lekin yozuvlar
o'qilishi uchun pastdan cheklangan: H = max(eni, L / 14, 3.4 × shrift) — frontend (`features/cl/StripMap.tsx`) bilan bir xil qoida.
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

from markupsafe import Markup, escape

from ..models import CLCostBase, CutMap, Operation, Part, PrintSettings, Project, SizeMode
from .calc import edge_map, op_part, total_qty
from .cl_calc import cl_cost, ensure_cl
from .render import (PART_FILL, PART_STROKE, REMNANT_FILL, REMNANT_SMALL, TRIM_FILL, WASTE_FILL, GroupRow, _edge_legend,
                     _edge_names_len, _qr_svg, _table, fmt, map_header, part_edges, safe_color)
from .sizes import compute_sizes

VIEW_RATIO = 14.0           # polosa balandligi kamida L / 14
MIN_FONT_PX = 10.0


def view_height(L: float, W: float, fs: float) -> float:
    return max(W, L / VIEW_RATIO, 3.4 * fs)


def map_trims(m: CutMap, op: Operation) -> tuple[float, float]:
    """(T_boshi, T_oxiri) mm: kartaga yozilgan (CLE da o'zgartirilgan bo'lishi mumkin), bo'lmasa operatsiya qiymati."""
    cl = ensure_cl(op)
    ts = m.trim_length if m.trim_length is not None else cl.trim
    te = m.end_offset_right if m.end_offset_right is not None else (cl.end_offset if cl.end_offset is not None else cl.trim)
    return float(ts), float(te)


def strip_map_svg(m: CutMap, width_px: int = 900, project: Optional[Project] = None, op: Optional[Operation] = None,
                  label: str = "number_name", show_edges: bool = True, mirror: bool = False,
                  style: Optional[PrintSettings] = None, uid: str = "m", remnant_numbers: bool = True) -> str:
    L, W = float(m.sheet_length), float(m.sheet_width)
    cl = ensure_cl(op) if op is not None else None
    k = cl.kerf if cl else 3.0
    ts, te = map_trims(m, op) if op is not None else (0.0, 0.0)
    scale = width_px / L if L > 0 else 1.0
    fs = max(MIN_FONT_PX / scale, 10.0)
    H = view_height(L, W, fs)
    st = style if style is not None else PrintSettings()
    part_fill = safe_color(st.map_part_fill, PART_FILL)
    waste_fill = safe_color(st.map_waste_fill, WASTE_FILL)
    parts = {p.id: p for p in op.parts} if op is not None else {}
    names = {p.id: p.name for p in op.parts} if op is not None else {}

    def RX(x: float, w: float) -> float:
        return L - x - w if mirror else x

    def X(x: float) -> float:
        return L - x if mirror else x

    sw = max(1.0, fs / 10)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(L)} {fmt(H)}" width="{width_px}" '
           f'height="{H * scale:.0f}" font-family="Arial, Helvetica, sans-serif">',
           f'<rect x="0" y="0" width="{fmt(L)}" height="{fmt(H)}" fill="{TRIM_FILL}" stroke="#222" stroke-width="{sw:.1f}"/>']
    # foydali zona (chiqindi fon): torsovka zonalari kulrang qoladi
    zx, zw = ts, max(0.0, L - ts - te)
    out.append(f'<rect x="{fmt(RX(zx, zw))}" y="0" width="{fmt(zw)}" height="{fmt(H)}" fill="{waste_fill}"/>')
    for o in m.offcuts:
        if o.kind != "remnant":
            continue
        out.append(f'<rect x="{fmt(RX(o.x, o.length))}" y="0" width="{fmt(o.length)}" height="{fmt(H)}" '
                   f'fill="{REMNANT_FILL if o.business else REMNANT_SMALL}" stroke="#3b6ea5" stroke-width="{sw:.1f}"/>')
        if remnant_numbers and o.length * scale > 34:
            out.append(f'<text x="{fmt(X(o.x + o.length / 2))}" y="{fmt(H * 0.28)}" font-size="{fs:.1f}" fill="#1f3f66" '
                       f'text-anchor="middle" dominant-baseline="middle">Д{int(o.number)}</text>'
                       f'<text x="{fmt(X(o.x + o.length / 2))}" y="{fmt(H * 0.56)}" font-size="{fs:.1f}" fill="#1f3f66" '
                       f'text-anchor="middle" dominant-baseline="middle">{fmt(o.length)}</text>')
    cut_w = max(k, fs / 8)
    cuts: list[float] = []
    if ts > 0:
        cuts.append(ts)
    for p in m.placements:
        cuts.append(p.x + p.length)
    for o in m.offcuts:
        if o.kind == "remnant" and cl is not None and cl.waste_incl_trim and te > 0:
            cuts.append(o.x + o.length)               # otxoddan keyingi alohida torsovka kesimi (Торцовка отходов ✓)
    for p in m.placements:
        part = parts.get(p.part_id)
        out.append(f'<rect x="{fmt(RX(p.x, p.length))}" y="0" width="{fmt(p.length)}" height="{fmt(H)}" fill="{part_fill}" '
                   f'stroke="{PART_STROKE}" stroke-width="{sw:.1f}"/>')
        if show_edges and part is not None and project is not None:
            ed = part_edges(part, project)
            ew = fs / 4
            segs = {"top": (p.x, ew / 2, p.x + p.length, ew / 2), "bottom": (p.x, H - ew / 2, p.x + p.length, H - ew / 2),
                    "left": (p.x + ew / 2, 0, p.x + ew / 2, H), "right": (p.x + p.length - ew / 2, 0, p.x + p.length - ew / 2, H)}
            for side, e in ed.items():
                if not e or e.get("lines", 1) <= 0:
                    continue
                x1, y1, x2, y2 = segs[side]
                out.append(f'<line x1="{fmt(X(x1))}" y1="{fmt(y1)}" x2="{fmt(X(x2))}" y2="{fmt(y2)}" '
                           f'stroke="{safe_color(e["color"])}" stroke-width="{ew:.1f}"/>')
        cx = p.x + p.length / 2
        uid_s = str(p.part_uid)
        room = p.length * scale
        if label in ("number", "number_name") and room > 6 * len(uid_s) + 4:
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(H * 0.28)}" font-size="{fs * 1.15:.1f}" font-weight="bold" fill="#241400" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(uid_s)}</text>')
        if room > 5.2 * len(fmt(p.length)) + 4:
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(H * 0.56)}" font-size="{fs:.1f}" fill="#241400" '
                       f'text-anchor="middle" dominant-baseline="middle">{fmt(p.length)}</text>')
        nm = (names.get(p.part_id) or "")
        if label in ("name", "number_name") and nm and room > 70:
            n = max(3, int(room / (fs * scale * 0.6 + 1)))
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(H * 0.82)}" font-size="{fs * 0.8:.1f}" fill="#3a2600" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(nm[:n])}</text>')
    for cx_ in cuts:                                  # propillar: qora chiziq (kesim kengligi, ko'rinish uchun kamida shrift / 8)
        out.append(f'<rect x="{fmt(RX(cx_, k))}" y="0" width="{fmt(cut_w)}" height="{fmt(H)}" fill="#111"/>')
    out.append("</svg>")
    return "".join(out)


# ───────────────────────── Hisobot bo'limi ─────────────────────────
def _kv(rows: list[tuple[str, str]]) -> str:
    return "<table class='kv'>" + "".join(f"<tr><td><b>{escape(a)}</b></td><td>{escape(str(b))}</td></tr>" for a, b in rows) + "</table>"


def cl_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    cl = ensure_cl(op)
    info = cl_cost(project, op)
    cur = project.currency
    mm_, m_ = t["mm"], t["m"]
    s = [f"<h2{cls}>{sec}. (CL) {t['cl']}: {('(' + escape(op.code) + ') ') if op.code else ''}{escape(op.name)}</h2>"]
    n = 0
    if ps.cl_header:
        n += 1
        end = cl.end_offset if cl.end_offset is not None else cl.trim
        price_unit = t["cl_price_strip"] if cl.price_by_strip else t["cl_price_m"]
        left = [(t["cl_width"], f"{fmt(cl.width)} {mm_}"), (t["cl_thick"], f"{fmt(cl.thickness)} {mm_}"),
                (t["cl_kerf"], f"{fmt(cl.kerf)} {mm_}"), (t["cl_trim"], f"{fmt(cl.trim)} {mm_}"),
                (t["cl_end_offset"], f"{fmt(end)} {mm_}"), (t["cl_pack"], f"{fmt(cl.pack_height)} {mm_}"),
                (t["cl_mult"], f"{cl.multiplicity} {t['pcs']}"), (t["cl_waste_min"], f"{fmt(cl.waste_min)} {mm_}"),
                (t["cl_business_min"], f"{fmt(cl.business_min)} {mm_}"),
                (t["cl_trim_waste"], t["cl_yes"] if cl.waste_incl_trim else t["cl_no"])]
        base_names = {CLCostBase.CUT_WITH_TRIM: "cl_base0", CLCostBase.CUT_NO_TRIM: "cl_base1",
                      CLCostBase.MATERIAL_LEN: "cl_base2", CLCostBase.PARTS_LEN: "cl_base3"}
        approx = "≈ " if info.get("estimated") else ""
        right = [(t["cl_price"], f"{fmt(cl.price)} {cur} ({price_unit})"), (t["cl_est_fill"], f"{fmt(cl.est_fill_percent)}%"),
                 (t["cl_usage"], f"{approx}{fmt(info['material_qty_m'])} {m_}"),
                 (t["cl_cost_mat"], f"{fmt(op.cost_material)} {cur}"), (t["cl_op_base"], t[base_names[cl.op_cost_base]]),
                 (t["cl_op_price"], f"{fmt(cl.op_price)} {cur}"), (t["cl_cost_op"], f"{fmt(op.cost_operation)} {cur}")]
        s.append(f"<h3>{n}. {t['cl_params']}</h3>")
        s.append(f"<table class='kv'><tr><td>{_kv(left)}</td><td>{_kv(right)}</td></tr></table>")
    edges = edge_map(project)
    mode = SizeMode(project.size_mode)
    mode_title = {SizeMode.BLANK: t["size_blank"], SizeMode.DETAIL: t["size_detail"], SizeMode.JOINTED: t["size_jointed"]}[mode]
    if ps.cl_parts:
        n += 1

        def part_row(p: Part) -> list:
            sz = compute_sizes(op_part(op, p), mode, edges, 0)
            L = sz.blank[0] if mode == SizeMode.BLANK else (sz.jointed[0] if mode == SizeMode.JOINTED else sz.detail[0])
            return [p.uid, fmt(L), fmt(cl.width), _edge_names_len(p, project, ("top", "bottom")),
                    _edge_names_len(p, project, ("left", "right")), total_qty(project, p), p.used_qty, p.left_qty,
                    escape(p.name)]

        if ps.cl_group_by_product:
            by_prod: dict[Optional[str], list[Part]] = {}
            known = {pr.id for pr in project.products}
            for p in op.parts:
                by_prod.setdefault(p.product_id if p.product_id in known else None, []).append(p)
            rows: list = []
            for pr in [*project.products, None]:
                grp = by_prod.get(pr.id if pr else None)
                if not grp:
                    continue
                rows.append(GroupRow(f"{t['product']}: {pr.name} × {pr.qty} {t['pcs']}" if pr else t["no_product"]))
                rows += [part_row(p) for p in grp]
        else:
            rows = [part_row(p) for p in op.parts]
        s.append(f"<h3>{n}. {t['parts']} ({mode_title})</h3>")
        s.append(_table(["№", t["length"], t["width"], t["edge_len"], t["cl_edge_end"], t["qty"], t["used"], t["left"], t["name"]], rows))
    res = op.result
    if res and ps.cl_unplaced and res.unplaced:
        n += 1
        cnt = Counter(res.unplaced)
        rows = [[p.uid, fmt(p.length), fmt(cl.width), cnt[p.id], escape(p.name)] for p in op.parts if p.id in cnt]
        s.append(f"<h3>{n}. {t['unplaced']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["qty"], t["name"]], rows))
    if res and ps.cl_strips:
        n += 1
        rows = []
        tot_len = 0.0
        for i, sh in enumerate(op.sheets, 1):
            if not sh.used_qty:
                continue
            ln = sh.length * sh.used_qty / 1000
            tot_len += ln
            rows.append([i, t["cl_k_strip"] if not (sh.is_remnant or sh.source_remnant_id) else t["remnant"], fmt(sh.length),
                         fmt(cl.width), sh.used_qty, fmt(round(ln, 3))])
        rows.append(["", "", "", "", Markup("<b>{}:</b>").format(t["total"]), Markup("<b>{}</b>").format(fmt(round(tot_len, 3)))])
        s.append(f"<h3>{n}. {t['cl_strips']}</h3>")
        s.append(_table(["№", t["cl_kind"], t["length"], t["width"], t["cl_used"], f"{t['cl_mat_len']}, {m_}"], rows))
    if res and ps.cl_remnants and res.remnants:
        n += 1
        cnt2 = Counter((o.length, o.raw_length, o.business) for o in res.remnants)
        rows = [[i, fmt(ln), fmt(raw), fmt(cl.width), c, t["cl_k_business"] if b else t["cl_k_waste"]]
                for i, ((ln, raw, b), c) in enumerate(sorted(cnt2.items(), key=lambda kv: -kv[0][1]), 1)]
        s.append(f"<h3>{n}. {t['cl_remnants']}</h3>")
        s.append(_table(["№", t["length"], f"{t['length']} ({t['remnants']})", t["width"], t["qty"], t["cl_kind"]], rows))
    if res and ps.cl_maps:
        names = {p.id: p.name for p in op.parts}
        parts_by_id = {p.id: p for p in op.parts}
        legend = _edge_legend(project, op, t)
        cards: list[str] = []
        for m in res.maps:
            head = f"<div class='maphdr'>{escape(op.name)} &nbsp; {escape(map_header(m, res, ps.map_header_fields))}</div>"
            svg = strip_map_svg(m, 700, project, op, ps.map_part_label, ps.map_edges, ps.map_mirror, style=ps,
                                uid=f"c{sec}m{m.index}", remnant_numbers=ps.map_remnant_number)
            side = ""
            if ps.map_parts_list:
                cnt3 = Counter(pl.part_id for pl in m.placements)
                rows = []
                for pid, c in sorted(cnt3.items(), key=lambda kv: parts_by_id[kv[0]].uid if kv[0] in parts_by_id else 0):
                    p = parts_by_id.get(pid)
                    if p is not None:
                        sz = next((pl.length for pl in m.placements if pl.part_id == pid), p.length)
                        rows.append([p.uid, fmt(sz), c, escape(names.get(pid, ""))])
                side += _table(["№", t["s_len"], t["s_qty"], t["name"]], rows)
                if legend:
                    side += f"<div class='legend'>{legend}</div>"
            if ps.cl_commands:
                side += _table([t["c_code"], t["c_size"], t["c_count"], t["c_ref"]],
                               [[f"{c.code}{c.level}", fmt(c.size), c.count, c.ref] for c in m.commands])
            if ps.map_qr:
                qr = _qr_svg(f"MXK:{project.number}:{op.id}:{m.index}")
                if qr:
                    side += f"<div class='qr'>{qr}</div>"
            comment = f"<div class='muted'>{escape(m.comment)}</div>" if m.comment else ""
            cards.append(f"<div class='mapcard'>{head}<div class='mapwrap'><div>{svg}{comment}</div>"
                         f"<div class='side'>{side}</div></div></div>")
        s.append("".join(cards))
    return "".join(s)
