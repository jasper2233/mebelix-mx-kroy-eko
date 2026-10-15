"""(CN) Postprotsessor ma'lumoti (W16): nesting natijasi uchun toza kontekst + o'rnatilgan formatlar (json, csv, dxf, commands).

STANOK G-CODE FORMATI BU YERDA YO'Q: u korxona dasturchilari tomonidan Jinja shablonda yoziladi (`render_template` → `context_cn`). Biz faqat
toza ma'lumot beramiz: joylashuvlar, burchaklar, list koordinatalaridagi poligonlar, asbob va asbob yo'li (kontur ofseti).

Kontekst (`context_cn`; shablonda `maps`, `parts`, `op`, `tool`, `project`, `f`, `now`):
  project — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
  op      — {name, code, kind="nest", thickness, spacing, margin, arc_tol, sheets_per_pack}
  tool    — {diameter, radius, offset}   (offset — asbob markazining detal konturidan masofasi, mm)
  maps    — [{index, copies, sheet_length, sheet_width, is_remnant, fill, cut_length_m, cuts, comment,
              placements:[{n, uid, name, code, x, y, length, width, angle, rotated, outline:[[x, y]…], holes:[[[x, y]…]…],
                           tool_path:{outer:[[[x, y]…]…], holes:[[[x, y]…]…]}, label:[cx, cy, w, h, burchak] | null}],
              remnants:[{number, x, y, length, width, business, in_part, raw_length, raw_width}]}]
  parts   — [{uid, name, code, length, width, qty, used, left, grain, shape: "rect" | "contour"}]
Koordinatalar: list chap-yuqori burchagidan, X o'ngga, Y pastga, mm; burchak — soat mili bo'yicha (ekranda), gradus. `outline` — tashqi
kontur (yoylar `arc_tol` xatosi bilan siniq chiziq); `tool_path.outer` — outline ni `offset` ga TASHQARIGA, `holes` — ichki konturlarni
`offset` ga teshik ichiga (material tashqarisiga) siljitish: asbob markazi yurishi kerak bo'lgan yo'l.
"""
from __future__ import annotations

import json
from datetime import datetime

from ..models import Operation, Project
from . import cn_geometry as G
from .calc import total_qty
from .cn_calc import ensure_cn, spacing_of
from .tpl_sandbox import fnum


def _tool_path(outline, holes, offset: float, tol: float) -> dict:
    def conv(r):
        return [(p[0], p[1]) for p in r]
    outer = []
    inner = []
    if offset > 0:
        o_ring = G.orient_ring(conv(outline), True)
        outer = [[[round(x, 3), round(y, 3)] for x, y in r] for r in G.offset_ring(o_ring, offset, tol)]
        for h in holes:
            h_ring = G.orient_ring(conv(h), False)
            inner += [[[round(x, 3), round(y, 3)] for x, y in r] for r in G.offset_ring(h_ring, offset, tol)]
    else:
        outer = [[list(p) for p in outline]]
        inner = [[list(p) for p in h] for h in holes]
    return dict(outer=outer, holes=inner)


def context_cn(project: Project, op: Operation, machine_key: str | None = None) -> dict:
    """CN operatsiyasi uchun postprotsessor konteksti (stanok formati yo'q — toza ma'lumot)."""
    cn = ensure_cn(op)
    res = op.result
    parts = {p.id: p for p in op.parts}
    tol = max(0.05, cn.arc_tol / 2)
    ctx_parts = [dict(uid=p.uid, name=p.name, code=p.code, length=p.length, width=p.width, qty=total_qty(project, p), used=p.used_qty,
                      left=p.left_qty, grain=p.grain) for p in op.parts]
    maps = []
    for m in (res.maps if res else []):
        pls = []
        for i, pl in enumerate(m.placements, 1):
            p = parts.get(pl.part_id)
            pls.append(dict(n=i, uid=pl.part_uid, name=p.name if p else "", code=p.code if p else "", x=pl.x, y=pl.y, length=pl.length,
                            width=pl.width, angle=pl.angle, rotated=pl.rotated, outline=pl.outline, holes=pl.holes,
                            tool_path=_tool_path(pl.outline, pl.holes, cn.offset, tol), label=pl.label))
        rem = [dict(number=o.number, x=o.x, y=o.y, length=o.length, width=o.width, business=o.business, in_part=o.in_part,
                    raw_length=o.raw_length, raw_width=o.raw_width) for o in m.offcuts if o.kind == "remnant"]
        maps.append(dict(index=m.index, copies=m.copies, sheet_length=m.sheet_length, sheet_width=m.sheet_width, is_remnant=m.is_remnant,
                         fill=m.fill_percent, cut_length_m=m.cut_length_m, cuts=m.cuts_count, comment=m.comment, packs=m.packs,
                         placements=pls, remnants=rem))
    ctx = dict(
        project=dict(name=project.name, number=project.number, customer=project.customer, order_date=str(project.order_date),
                     ready_date=str(project.ready_date), currency=project.currency, mes_order_ref=project.mes_order_ref or ""),
        op=dict(name=op.name, code=op.code, kind="nest", thickness=cn.thickness, spacing=round(spacing_of(cn), 4), margin=cn.margin,
                arc_tol=cn.arc_tol, sheets_per_pack=res.sheets_per_pack if res else 1),
        tool=dict(diameter=cn.tool_diameter, radius=cn.tool_diameter / 2, offset=cn.offset),
        maps=maps, parts=ctx_parts, f=fnum, now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        machine=None, label={}, label_text={}, label_warnings=[])
    return ctx


# ───────────────────────── O'rnatilgan formatlar ─────────────────────────
def _json(ctx: dict) -> str:
    data = dict(project=ctx["project"], op=ctx["op"], tool=ctx["tool"], maps=ctx["maps"], parts=ctx["parts"])
    return json.dumps(data, ensure_ascii=False, indent=2)


def _csv(ctx: dict) -> str:
    rows = ["karta;nusxa;list_uzunlik;list_en;detal;nomi;kod;x;y;burchak;uzunlik;en;konturlar"]
    for m in ctx["maps"]:
        for p in m["placements"]:
            rows.append(";".join(str(v) for v in (m["index"], m["copies"], fnum(m["sheet_length"]), fnum(m["sheet_width"]), p["uid"],
                                                   p["name"].replace(";", ","), p["code"], fnum(p["x"]), fnum(p["y"]), fnum(p["angle"]),
                                                   fnum(p["length"]), fnum(p["width"]), 1 + len(p["holes"]))))
    return "\n".join(rows) + "\n"


def _commands(ctx: dict) -> str:
    out = [f"MebeliX Kroy — {ctx['project']['name']} (№{ctx['project']['number']})",
           f"{ctx['op']['name']}: t={fnum(ctx['op']['thickness'])}  D={fnum(ctx['tool']['diameter'])}  spacing={fnum(ctx['op']['spacing'])}", ""]
    for m in ctx["maps"]:
        out.append(f"=== {m['index']}/{len(ctx['maps'])}  {fnum(m['sheet_length'])}x{fnum(m['sheet_width'])}  x{m['copies']}  F {m['fill']}%  LT {m['cut_length_m']} m")
        out.append(f"{'№':>3} {'uid':>5} {'x':>9} {'y':>9} {'angle':>7} {'L':>8} {'W':>8}  name")
        for p in m["placements"]:
            out.append(f"{p['n']:>3} {p['uid']:>5} {fnum(p['x']):>9} {fnum(p['y']):>9} {fnum(p['angle']):>7} {fnum(p['length']):>8} "
                       f"{fnum(p['width']):>8}  {p['name']}")
        out.append("")
    return "\n".join(out)


def _dxf(ctx: dict) -> str:
    """DXF (R12, POLYLINE): list, detal konturlari, ichki kesimlar, asbob yo'li, qoldiqlar — alohida qatlamlarda (CAD / CAM uchun)."""
    layers = (("SHEET", 7), ("PARTS", 3), ("HOLES", 1), ("TOOLPATH", 5), ("REMNANT", 4), ("TEXT", 2))
    head = "0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n%d\n" % len(layers) + "".join(
        f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in layers) + "0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"

    def poly(pts, layer, oy, W):
        s = f"0\nPOLYLINE\n8\n{layer}\n66\n1\n70\n1\n"
        for x, y in pts:
            s += f"0\nVERTEX\n8\n{layer}\n10\n{x:.3f}\n20\n{oy + W - y:.3f}\n30\n0\n"
        return s + "0\nSEQEND\n8\n" + layer + "\n"

    def text(x, y, h, s, layer):
        return f"0\nTEXT\n8\n{layer}\n10\n{x:.2f}\n20\n{y:.2f}\n30\n0\n40\n{h:.2f}\n1\n{s}\n"
    body = []
    oy = 0.0
    for m in ctx["maps"]:
        W, L = m["sheet_width"], m["sheet_length"]
        body.append(text(0, oy + W + 60, 60, f"{ctx['op']['name']} #{m['index']} x{m['copies']}", "TEXT"))
        body.append(poly([(0, 0), (L, 0), (L, W), (0, W)], "SHEET", oy, W))
        for p in m["placements"]:
            body.append(poly([tuple(q) for q in p["outline"]], "PARTS", oy, W))
            for h in p["holes"]:
                body.append(poly([tuple(q) for q in h], "HOLES", oy, W))
            for r in p["tool_path"]["outer"] + p["tool_path"]["holes"]:
                body.append(poly([tuple(q) for q in r], "TOOLPATH", oy, W))
            th = max(8.0, min(40.0, min(p["length"], p["width"]) / 6))
            body.append(text(p["x"] + p["length"] / 2 - th, oy + W - p["y"] - p["width"] / 2 - th / 2, th, str(p["uid"]), "TEXT"))
        for r in m["remnants"]:
            body.append(poly([(r["x"], r["y"]), (r["x"] + r["length"], r["y"]), (r["x"] + r["length"], r["y"] + r["width"]),
                              (r["x"], r["y"] + r["width"])], "REMNANT", oy, W))
        oy += W + 300
    return head + "".join(body) + "0\nENDSEC\n0\nEOF\n"


def run_builtin_cn(key: str, project: Project, op: Operation, safe_name) -> tuple[str, bytes, str]:
    ctx = context_cn(project, op)
    base = f"{project.number}_{safe_name(op.code or op.name, 'nesting', 30)}"
    if key == "json":
        return f"{base}.json", _json(ctx).encode("utf-8"), "application/json"
    if key == "csv":
        return f"{base}.csv", ("﻿" + _csv(ctx)).encode("utf-8"), "text/csv"
    if key == "commands":
        return f"{base}_buyruqlar.txt", _commands(ctx).encode("utf-8"), "text/plain"
    if key == "dxf":
        return f"{base}.dxf", _dxf(ctx).encode("ascii", errors="replace"), "application/dxf"
    raise KeyError(key)
