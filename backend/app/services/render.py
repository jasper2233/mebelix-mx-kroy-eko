"""Kroy kartasini SVG ga chizish va chop etish uchun HTML hisobot."""
from __future__ import annotations

from html import escape

from ..models import CutMap, CuttingResult, OpType, Project
from .calc import edge_usage, total_qty, warehouse_request

PART_FILL = "#FFA500"      # detal (to'q sariq)
WASTE_FILL = "#C8C8C8"     # chiqindi (kulrang)
REMNANT_FILL = "#7FB2F0"   # qoldiq (ko'k)


def map_header(m: CutMap, res: CuttingResult) -> str:
    return (f"№:{m.index}/{len(res.maps)}  S:{m.sheet_length:g}/{m.sheet_width:g}  "
            f"C:{m.copies}/{res.total_sheets}  Cp:{m.parts_count}/{res.total_parts}  "
            f"LT:{m.cut_length_m:g}/{res.total_cut_length_m:g}  "
            f"F:{m.fill_percent:g}%/{res.total_fill_percent:g}%")


def map_svg(m: CutMap, width_px: int = 900, part_names: dict[str, str] | None = None) -> str:
    L, W = m.sheet_length, m.sheet_width
    k = width_px / L
    h_px = W * k
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {W}" '
           f'width="{width_px}" height="{h_px:.0f}" font-family="monospace">',
           f'<rect x="0" y="0" width="{L}" height="{W}" fill="{WASTE_FILL}" stroke="#000" stroke-width="2"/>']
    fs = max(18, min(L, W) / 40)
    for o in m.offcuts:
        fill = REMNANT_FILL if o.kind == "remnant" else WASTE_FILL
        out.append(f'<rect x="{o.x}" y="{o.y}" width="{o.length}" height="{o.width}" '
                   f'fill="{fill}" stroke="#666" stroke-width="1"/>')
        if o.kind == "remnant":
            out.append(f'<text x="{o.x + o.length / 2}" y="{o.y + o.width / 2}" font-size="{fs}" '
                       f'text-anchor="middle">Д{o.number} {o.length:g}×{o.width:g}</text>')
    for p in m.placements:
        out.append(f'<rect x="{p.x}" y="{p.y}" width="{p.length}" height="{p.width}" '
                   f'fill="{PART_FILL}" stroke="#000" stroke-width="1.5"/>')
        cx, cy = p.x + p.length / 2, p.y + p.width / 2
        label = str(p.part_uid)
        if part_names and p.part_id in part_names:
            label += " " + part_names[p.part_id]
        out.append(f'<text x="{cx}" y="{cy}" font-size="{fs * 1.3}" font-weight="bold" '
                   f'text-anchor="middle" dominant-baseline="middle">{escape(label)}</text>')
        # o'lchamlar: pastda uzunlik, o'ngda en (vertikal)
        out.append(f'<text x="{p.x + 4}" y="{p.y + p.width - 6}" font-size="{fs}">{p.length:g}</text>')
        out.append(f'<text x="{p.x + p.length - 6}" y="{p.y + 4}" font-size="{fs}" '
                   f'transform="rotate(90 {p.x + p.length - 6} {p.y + 4})">{p.width:g}</text>')
    out.append("</svg>")
    return "".join(out)


def _table(headers: list[str], rows: list[list]) -> str:
    h = "".join(f"<th>{escape(str(x))}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def project_report_html(project: Project) -> str:
    css = """body{font-family:Arial,sans-serif;font-size:12px;margin:16px}
    table{border-collapse:collapse;margin:6px 0 14px}td,th{border:1px solid #333;padding:2px 6px}
    th{background:#eee}.pb{page-break-before:always}h2{font-size:16px}h3{font-size:14px}
    .hdr{font-weight:bold;text-align:center;margin:10px 0 4px}"""
    s = [f"<html><head><meta charset='utf-8'><title>{escape(project.name)}</title>"
         f"<style>{css}</style></head><body>"]
    total_m = sum(o.cost_material for o in project.operations)
    total_o = sum(o.cost_operation for o in project.operations)
    s.append(f"<h2>Loyiha: {escape(project.name)}</h2>")
    s.append(_table(["Buyurtma №", "Buyurtma sanasi", "Tayyor sanasi", "Material narxi",
                     "Operatsiya narxi", "Jami"],
                    [[project.number, project.order_date, project.ready_date,
                      f"{total_m:g} {project.currency}", f"{total_o:g} {project.currency}",
                      f"{total_m + total_o:g} {project.currency}"]]))
    s.append("<h3>1. Omborga talabnoma</h3>")
    s.append(_table(["№", "Tur", "Kod", "Nomi", "Birlik", "Soni", "Izoh"],
                    [[i + 1, r["type"], r["code"], r["name"], r["unit"], r["qty"], r["note"]]
                     for i, r in enumerate(warehouse_request(project))]))
    n = 1
    for op in project.operations:
        if not op.print:
            continue
        n += 1
        cls = ' class="pb"' if op.new_page else ""
        if op.type == OpType.CS:
            s.append(f"<h3{cls}>{n}. (CS) Listli kroy: {escape(op.name)}</h3>")
            rows = []
            for p in op.parts:
                rows.append([p.uid, p.length, p.width, total_qty(project, p), p.used_qty,
                             p.left_qty, p.name])
            s.append(_table(["№", "Uzunlik", "En", "Soni", "ИК", "Qoldi", "Nomi"], rows))
            res = op.result
            if res:
                s.append(_table(["№", "Uzunlik", "En", "Maydon", "List soni"],
                                [[i + 1, sh.length, sh.width,
                                  round(sh.length * sh.width / 1e6, 3), sh.used_qty]
                                 for i, sh in enumerate(op.sheets) if sh.used_qty]))
                names = {p.id: p.name for p in op.parts}
                for m in res.maps:
                    s.append(f"<div class='hdr'>{escape(op.name)} &nbsp; {escape(map_header(m, res))}</div>")
                    s.append(map_svg(m, 700, None))
                    s.append(_table(["Kod", "Daraja", "O'lcham", "Soni", "Ref"],
                                    [[c.code, c.level, c.size, c.count, c.ref] for c in m.commands]))
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            s.append(f"<h3{cls}>{n}. (EL) Kromka: {escape(op.code)} {escape(op.name)}</h3>")
            s.append(f"<p>Material: {u['material_m']} m &nbsp; Ish: {u['work_m']} m</p>")
            s.append(_table(["Material", "Uzunlik", "O.uz", "En", "O.en", "Soni", "Kromka m", "Nomi"],
                            [[r["material"], r["length"], r["edges_len"], r["width"], r["edges_wid"],
                              r["qty"], r["edge_m"], r["name"]] for r in u["rows"]]))
        elif op.type == OpType.XNC:
            s.append(f"<h3{cls}>{n}. (XNC) Ishlov: {escape(op.code)} {escape(op.name)}</h3>")
    s.append("</body></html>")
    return "".join(s)
