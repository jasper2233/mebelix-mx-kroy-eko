"""Postprotsessorlar: kroy natijasini stanok / boshqa tizim formatiga o'girish.

O'rnatilgan formatlar (hamma uchun ochiq, mustaqil yozilgan):
  csv       — kesish ro'yxati (Excel/1C/MES uchun)
  commands  — kesish buyruqlari matni (arra operatori uchun, T/C/P/W + daraja)
  dxf       — kroy kartalari DXF (R12, CAD/CAM uchun)
  json      — to'liq natija (MES integratsiyasi)

Foydalanuvchi postprotsessori — «Настройки → Постпроцессоры» da shablon yoziladi (Jinja2, xavfsiz sandbox).
Korxonangiz arra stanogining formatini shu yerda kod o'zgartirmasdan tasvirlaysiz. Shablonga beriladigan
ma'lumotlar (kontekst):
  project  — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
  op       — {name, code, thickness, kerf, trim_length, trim_width}
  maps     — [{index, copies, sheet_length, sheet_width, is_remnant, fill, cut_length_m, cuts,
               placements:[{n, uid, name, code, x, y, length, width, rotated, edges}],
               commands:[{n, code, level, size, count, ref}],
               remnants:[{number, x, y, length, width, business}]}]
  parts    — [{uid, name, code, length, width, qty, used, left, grain, edges}]
  map      — (per_map=True bo'lsa) joriy karta
  f(v, n=1) — sonni formatlash (nuqta bilan), now — sana-vaqt
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime

from ..models import Operation, OpType, PostprocessorProfile, Project
from .calc import total_qty
from .render import part_edges, rotate_edges
from .tpl_sandbox import fnum, render as render_limited

BUILTIN = {
    "csv": dict(name="MebeliX CSV — kesish ro'yxati", extension="csv"),
    "commands": dict(name="Kesish buyruqlari (operator uchun, TXT)", extension="txt"),
    "dxf": dict(name="DXF — kroy kartalari (CAD/CAM)", extension="dxf"),
    "json": dict(name="MES JSON — to'liq natija", extension="json"),
}

EXAMPLE_TEMPLATE = """{#- Namuna: har karta alohida fayl. O'zingizning stanok formatingizga moslang. -#}
SHEET;{{ f(map.sheet_length) }};{{ f(map.sheet_width) }};{{ f(op.thickness) }};{{ map.copies }}
{% for c in map.commands -%}
CUT;{{ c.n }};{{ c.code }};{{ c.level }};{{ f(c.size) }};{{ c.count }};{{ c.ref }}
{% endfor -%}
{% for p in map.placements -%}
PART;{{ p.uid }};{{ f(p.x) }};{{ f(p.y) }};{{ f(p.length) }};{{ f(p.width) }};{{ 1 if p.rotated else 0 }};{{ p.name }}
{% endfor -%}
END
"""


_f = fnum          # o'rnatilgan formatlar ham shablondagi f() bilan bir xil formatlaydi


def context(project: Project, op: Operation) -> dict:
    parts = {p.id: p for p in op.parts}
    res = op.result
    cut = op.cs_cut
    ctx_parts = []
    for p in op.parts:
        ed = part_edges(p, project)
        ctx_parts.append(dict(uid=p.uid, name=p.name, code=p.code, length=p.length, width=p.width,
                              qty=total_qty(project, p), used=p.used_qty, left=p.left_qty, grain=p.grain,
                              edges={k: v["symbol"] for k, v in ed.items()}))
    maps = []
    for m in (res.maps if res else []):
        pls = []
        for i, pl in enumerate(m.placements, 1):
            p = parts.get(pl.part_id)
            ed = rotate_edges(part_edges(p, project), pl.rotated) if p else {}
            pls.append(dict(n=i, uid=pl.part_uid, name=p.name if p else "", code=p.code if p else "",
                            x=pl.x, y=pl.y, length=pl.length, width=pl.width, rotated=pl.rotated,
                            edges={k: v["symbol"] for k, v in ed.items() if v}))
        cmds = [dict(n=i, code=c.code, level=c.level, size=c.size, count=c.count, ref=c.ref)
                for i, c in enumerate(m.commands, 1)]
        rem = [dict(number=o.number, x=o.x, y=o.y, length=o.length, width=o.width, business=o.business)
               for o in m.offcuts if o.kind == "remnant"]
        maps.append(dict(index=m.index, copies=m.copies, sheet_length=m.sheet_length, sheet_width=m.sheet_width,
                         is_remnant=m.is_remnant, fill=m.fill_percent, cut_length_m=m.cut_length_m,
                         cuts=m.cuts_count, placements=pls, commands=cmds, remnants=rem))
    return dict(
        project=dict(name=project.name, number=project.number, customer=project.customer,
                     order_date=str(project.order_date), ready_date=str(project.ready_date),
                     currency=project.currency, mes_order_ref=project.mes_order_ref or ""),
        op=dict(name=op.name, code=op.code, thickness=op.cs_material.thickness if op.cs_material else 0,
                kerf=cut.kerf if cut else 0, trim_length=cut.trim_length if cut else 0,
                trim_width=cut.trim_width if cut else 0),
        maps=maps, parts=ctx_parts, f=fnum, now=datetime.now().strftime("%Y-%m-%d %H:%M"))


def _csv(ctx: dict) -> str:
    rows = ["karta;nusxa;list_uzunlik;list_en;detal;nomi;kod;x;y;uzunlik;en;aylantirilgan;kromka"]
    for m in ctx["maps"]:
        for p in m["placements"]:
            ed = "".join(f"{k[0].upper()}{v}" for k, v in sorted(p["edges"].items()))
            rows.append(";".join(str(v) for v in (m["index"], m["copies"], _f(m["sheet_length"]), _f(m["sheet_width"]),
                                                  p["uid"], p["name"].replace(";", ","), p["code"], _f(p["x"]), _f(p["y"]),
                                                  _f(p["length"]), _f(p["width"]), 1 if p["rotated"] else 0, ed)))
    return "\n".join(rows) + "\n"


def _commands(ctx: dict) -> str:
    out = [f"MebeliX Kroy — {ctx['project']['name']} (№{ctx['project']['number']})",
           f"Material: {ctx['op']['name']}  qalinlik {ctx['op']['thickness']} mm, arra {ctx['op']['kerf']} mm", ""]
    for m in ctx["maps"]:
        out.append(f"=== Karta {m['index']}/{len(ctx['maps'])}  list {_f(m['sheet_length'])}×{_f(m['sheet_width'])}"
                   f"  × {m['copies']} ta  F {m['fill']}%  LT {m['cut_length_m']} m")
        out.append(f"{'№':>3}  {'Кд':<4}{'Р':>9}{'К':>4}  Д")
        for c in m["commands"]:
            out.append(f"{c['n']:>3}  {c['code'] + str(c['level']):<4}{_f(c['size']):>9}{c['count']:>4}  {c['ref']}")
        out.append("")
    return "\n".join(out)


def _dxf(ctx: dict) -> str:
    def line(x1, y1, x2, y2, layer):
        return f"0\nLINE\n8\n{layer}\n10\n{x1:.2f}\n20\n{y1:.2f}\n30\n0\n11\n{x2:.2f}\n21\n{y2:.2f}\n31\n0\n"

    def rect(x, y, w, h, layer):
        return line(x, y, x + w, y, layer) + line(x + w, y, x + w, y + h, layer) + \
            line(x + w, y + h, x, y + h, layer) + line(x, y + h, x, y, layer)

    def text(x, y, h, s, layer):
        return f"0\nTEXT\n8\n{layer}\n10\n{x:.2f}\n20\n{y:.2f}\n30\n0\n40\n{h:.2f}\n1\n{s}\n"
    layers = ("SHEET", "PARTS", "REMNANT", "TEXT")
    head = "0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n4\n" + "".join(
        f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in zip(layers, (7, 3, 5, 2))) + \
        "0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"
    body = []
    oy = 0.0
    for m in ctx["maps"]:
        W = m["sheet_width"]
        body.append(text(0, oy + W + 60, 60, f"{ctx['op']['name']} karta {m['index']} x{m['copies']}", "TEXT"))
        body.append(rect(0, oy, m["sheet_length"], W, "SHEET"))
        for p in m["placements"]:
            y = oy + W - p["y"] - p["width"]           # DXF Y yuqoriga
            body.append(rect(p["x"], y, p["length"], p["width"], "PARTS"))
            th = max(10.0, min(60.0, min(p["length"], p["width"]) / 5))
            body.append(text(p["x"] + th / 2, y + p["width"] / 2 - th / 2, th,
                             f"{p['uid']} {_f(p['length'])}x{_f(p['width'])}", "TEXT"))
        for r in m["remnants"]:
            y = oy + W - r["y"] - r["width"]
            body.append(rect(r["x"], y, r["length"], r["width"], "REMNANT"))
        oy += W + 300
    return head + "".join(body) + "0\nENDSEC\n0\nEOF\n"


def run_builtin(key: str, project: Project, op: Operation) -> tuple[str, bytes, str]:
    ctx = context(project, op)
    base = f"{project.number}_{(op.code or op.name or 'kroy').replace(' ', '_')[:30]}"
    if key == "csv":
        return f"{base}.csv", ("﻿" + _csv(ctx)).encode("utf-8"), "text/csv"
    if key == "commands":
        return f"{base}_buyruqlar.txt", _commands(ctx).encode("utf-8"), "text/plain"
    if key == "dxf":
        return f"{base}.dxf", _dxf(ctx).encode("ascii", errors="replace"), "application/dxf"
    if key == "json":
        data = dict(project=ctx["project"], op=ctx["op"], maps=ctx["maps"], parts=ctx["parts"])
        return f"{base}.json", json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    raise KeyError(key)


def render_template(pp: PostprocessorProfile, project: Project, op: Operation) -> tuple[str, bytes, str]:
    """Foydalanuvchi shabloni. per_map=True — har karta alohida fayl (zip)."""
    ctx = context(project, op)
    nl = "\r\n" if pp.newline == "crlf" else "\n"
    base = f"{project.number}_{(op.code or op.name or 'kroy').replace(' ', '_')[:30]}"

    def enc(text: str) -> bytes:
        text = text.replace("\r\n", "\n").replace("\n", nl)
        return text.encode(pp.encoding or "utf-8", errors="replace")
    if pp.per_map:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for m in ctx["maps"]:
                z.writestr(f"{base}_{m['index']:02d}.{pp.extension}", enc(render_limited(pp.template, {**ctx, "map": m})))
        return f"{base}_{pp.name.replace(' ', '_')}.zip", buf.getvalue(), "application/zip"
    return f"{base}.{pp.extension}", enc(render_limited(pp.template, ctx)), "text/plain"


def is_cs(op: Operation) -> bool:
    return op.type == OpType.CS
