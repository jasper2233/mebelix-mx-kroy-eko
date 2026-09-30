"""Kroy kartasini SVG ga chizish va chop etish uchun HTML hisobot (A4, brauzerda PDF).

Hisobot tuzilishi xodimlarga tanish tartibda (UI_SPEC §8): sarlavha → omborga talabnoma →
har operatsiya (CS: detallar, listlar, qoldiqlar, kartalar; EL: parametrlar + detallar; XNC: chizma).
Ranglar/shriftlar — MebeliX palitrasi.
"""
from __future__ import annotations

from html import escape
from typing import Optional

from ..models import (CutMap, CuttingResult, OpType, Operation, Part, PrintSettings, Project,
                      SizeMode)
from .calc import edge_map, edge_usage, total_qty, warehouse_request
from .sizes import compute_sizes

PART_FILL = "#F2A541"      # detal (to'q sariq)
PART_STROKE = "#5A3A0A"
WASTE_FILL = "#CBCED3"     # chiqindi (kulrang)
REMNANT_FILL = "#86B4E6"   # деловой qoldiq (ko'k)
REMNANT_SMALL = "#B9D3EF"  # oddiy qoldiq
TRIM_FILL = "#A9AEB6"      # torsovka zonasi

T = {
    "ru": {
        "project": "Проект", "author": "Автор", "order_id": "ID проекта", "order_date": "Дата заказа",
        "ready_date": "Дата готовности", "cost_mat": "Стоимость материалов", "cost_op": "Стоимость операций",
        "cost": "Стоимость", "warehouse": "Требование на склад", "type": "Тип", "code": "Код/Изделие",
        "name": "Наименование", "unit": "Ед.И", "qty": "Кол", "sheets_n": "Листы", "cut_len": "Длина реза",
        "edge_work": "Длина кромкования (работа)", "cs": "Листовой раскрой", "parts": "Детали",
        "size_blank": "Размер заготовки", "size_detail": "Размер детали (с кромкой)",
        "size_jointed": "Размер после прифуговки", "length": "Длина", "width": "Ширина",
        "edge_len": "О-ка по длине", "edge_wid": "О-ка по ширине", "used": "ИК", "left": "Ост",
        "sheets": "Листы", "area": "Площадь", "sheets_qty": "Кол. листов", "price": "Цена",
        "total_area": "Общ. площадь", "sum": "Сумма", "total": "Всего", "remnants": "Остатки",
        "unplaced": "Невместившиеся детали", "el": "Кромка", "mat_len": "Длина материала",
        "xnc": "Обработка", "drill": "Сверлений", "mill": "Фрезерование", "pcs": "шт", "m": "м",
        "remnant": "Деловой остаток", "commands": "Таблица команд", "milling": "Фрезерование",
        "drilling": "Сверление", "grooving": "Пазование", "detail": "Деталь", "product": "Изделие",
        "material": "Материал", "blank_size": "Рм. заготовки", "detail_size": "Рм. детали",
        "materials": "Материалы", "products": "Изделия", "code_short": "Код", "cost_mat_s": "Ст. м-ла",
        "cost_op_s": "Ст. оп-и", "saw": "Пиление", "customer": "Заказчик",
    },
    "uz": {
        "project": "Loyiha", "author": "Muallif", "order_id": "Loyiha ID", "order_date": "Buyurtma sanasi",
        "ready_date": "Tayyor bo'lish sanasi", "cost_mat": "Material narxi", "cost_op": "Ish narxi",
        "cost": "Jami narx", "warehouse": "Omborga talabnoma", "type": "Tur", "code": "Kod/Mahsulot",
        "name": "Nomi", "unit": "O'lch.", "qty": "Soni", "sheets_n": "Listlar", "cut_len": "Kesish uzunligi",
        "edge_work": "Kromkalash (ish)", "cs": "Listli kroy", "parts": "Detallar",
        "size_blank": "Zagotovka o'lchami", "size_detail": "Detal o'lchami (kromka bilan)",
        "size_jointed": "Prifugovkadan keyingi o'lcham", "length": "Uzunlik", "width": "En",
        "edge_len": "Kromka (uzunlik)", "edge_wid": "Kromka (en)", "used": "Ishlatildi", "left": "Qoldi",
        "sheets": "Listlar", "area": "Maydon", "sheets_qty": "List soni", "price": "Narx",
        "total_area": "Jami maydon", "sum": "Summa", "total": "Jami", "remnants": "Qoldiqlar",
        "unplaced": "Sig'magan detallar", "el": "Kromka", "mat_len": "Material uzunligi",
        "xnc": "Ishlov (XNC)", "drill": "Teshiklar", "mill": "Frezerlash", "pcs": "dona", "m": "m",
        "remnant": "Deloviy qoldiq", "commands": "Buyruqlar jadvali", "milling": "Frezerlash",
        "drilling": "Teshik", "grooving": "Pazlash", "detail": "Detal", "product": "Mahsulot",
        "material": "Material", "blank_size": "Zagotovka", "detail_size": "Detal",
        "materials": "Materiallar", "products": "Mahsulotlar", "code_short": "Kod", "cost_mat_s": "Material",
        "cost_op_s": "Ish", "saw": "Arralash", "customer": "Buyurtmachi",
    },
}


def fmt(v: float) -> str:
    if v is None:
        return ""
    r = round(float(v), 2)
    return str(int(r)) if r == int(r) else f"{r:g}"


# ───────────────────────── Karta sarlavhasi ─────────────────────────
HEADER_FIELDS = ("N", "S", "C", "Cp", "LT", "CT", "F", "AP", "AM", "AW")


def map_header(m: CutMap, res: CuttingResult, fields: Optional[list[str]] = None) -> str:
    fields = fields or ["N", "S", "C", "Cp", "LT", "F"]
    parts = []
    for f in fields:
        if f == "N":
            parts.append(f"№:{m.index}/{len(res.maps)}")
        elif f == "S":
            parts.append(f"S:{fmt(m.sheet_length)}/{fmt(m.sheet_width)}")
        elif f == "C":
            parts.append(f"C:{m.copies}/{res.total_sheets}")
        elif f == "Cp":
            parts.append(f"Cp:{m.parts_count}/{res.total_parts}")
        elif f == "LT":
            parts.append(f"LT:{fmt(m.cut_length_m)}/{fmt(res.total_cut_length_m)}")
        elif f == "CT":
            parts.append(f"CT:{m.cuts_count}/{res.total_cuts}")
        elif f == "F":
            parts.append(f"F:{fmt(m.fill_percent)}%/{fmt(res.total_fill_percent)}%")
        elif f == "AP":
            parts.append(f"AP:{fmt(m.parts_area_m2)}")
        elif f == "AM":
            parts.append(f"AM:{fmt(m.sheet_area_m2)}")
        elif f == "AW":
            parts.append(f"AW:{fmt(m.remnant_area_m2)}")
    return "  ".join(parts)


# ───────────────────────── Kromka yordamchilari ─────────────────────────
def rotate_edges(edges: dict, rotated: bool) -> dict:
    """Detal kromkalari (top/bottom — uzunlik bo'ylab) joylashgan holatga: 90° soat yo'nalishida."""
    if not rotated:
        return edges
    return {"top": edges.get("left"), "bottom": edges.get("right"),
            "left": edges.get("bottom"), "right": edges.get("top")}


def part_edges(part: Part, project: Project) -> dict:
    out = {}
    ops = {o.id: o for o in project.operations if o.type == OpType.EL}
    for side in ("top", "bottom", "left", "right"):
        ref = getattr(part, f"edge_{side}")
        op = ops.get(ref.op_id) if ref and ref.op_id else None
        if op is not None:
            el = op.el
            out[side] = {"symbol": (el.symbol if el else "") or "?", "color": (el.color if el else "#000") or "#000",
                         "lines": (el.marker_lines if el else 1) or 1, "name": op.name}
    return out


def part_marks(part: Part, project: Project) -> str:
    """Nomga belgilar: '=' pazlash, '*' frezerlash, '%' teshik (UI_SPEC §5.2)."""
    marks = ""
    if any(getattr(part, f"groove_{s}").op_id for s in ("top", "bottom", "left", "right")):
        marks += "="
    xnc = [o for o in project.operations if o.type == OpType.XNC and o.id in part.xnc_op_ids and o.xnc]
    if xnc:
        cmds = [c.cmd for o in xnc for c in _flatten(o.xnc.program)]
        if any(c.startswith("Mill") for c in cmds):
            marks += "*"
        if any(c.startswith("Drill") for c in cmds):
            marks += "%"
        if any(c == "Groove" for c in cmds) and "=" not in marks:
            marks += "="
    return marks


def _flatten(cmds):
    for c in cmds:
        yield c
        yield from _flatten(c.children)


# ───────────────────────── Karta SVG ─────────────────────────
def map_svg(m: CutMap, width_px: int = 900, part_names: Optional[dict[str, str]] = None,
            project: Optional[Project] = None, op: Optional[Operation] = None,
            label: str = "number_name", show_edges: bool = True, remnant_numbers: bool = True,
            mirror: bool = False) -> str:
    """Karta: detallar — to'q sariq (raqam + o'lchamlar: pastda uzunlik, o'ngda en), chiqindi — kulrang,
    деловой qoldiq — ko'k (Д№ o'lcham bilan). Kromkali tomonlar — rangli qalin chiziq va belgi."""
    L, W = m.sheet_length, m.sheet_width
    k = width_px / L
    h_px = W * k
    fs = max(16.0, min(L, W) / 42)
    parts_by_id = {p.id: p for p in op.parts} if op else {}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(L)} {fmt(W)}" '
           f'width="{width_px}" height="{h_px:.0f}" font-family="Arial, Helvetica, sans-serif"'
           + (' transform="scale(-1,1)"' if mirror else '') + '>',
           f'<rect x="0" y="0" width="{fmt(L)}" height="{fmt(W)}" fill="{TRIM_FILL}" stroke="#222" stroke-width="{fs / 5:.1f}"/>']
    # foydali zona (chiqindi fon) — daraxt ildizidan
    if m.strips:
        r = m.strips[0]
        out.append(f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["l"]}" height="{r["w"]}" fill="{WASTE_FILL}"/>')
    for o in m.offcuts:
        if o.kind != "remnant":
            continue
        fill = REMNANT_FILL if o.business else REMNANT_SMALL
        out.append(f'<rect x="{fmt(o.x)}" y="{fmt(o.y)}" width="{fmt(o.length)}" height="{fmt(o.width)}" '
                   f'fill="{fill}" stroke="#3b6ea5" stroke-width="{fs / 8:.1f}"/>')
        if remnant_numbers and o.length > fs * 4 and o.width > fs * 1.6:
            out.append(f'<text x="{fmt(o.x + o.length / 2)}" y="{fmt(o.y + o.width / 2)}" font-size="{fs * 1.1:.1f}" '
                       f'fill="#1f3f66" text-anchor="middle" dominant-baseline="middle">Д{o.number} '
                       f'{fmt(o.length)}×{fmt(o.width)}</text>')
    for p in m.placements:
        out.append(f'<rect x="{fmt(p.x)}" y="{fmt(p.y)}" width="{fmt(p.length)}" height="{fmt(p.width)}" '
                   f'fill="{PART_FILL}" stroke="{PART_STROKE}" stroke-width="{fs / 7:.1f}"/>')
        part = parts_by_id.get(p.part_id)
        if show_edges and part is not None and project is not None:
            ed = rotate_edges(part_edges(part, project), p.rotated)
            sw = fs / 3
            ins = sw / 2 + fs / 10
            seg = {
                "top": (p.x + ins, p.y + ins, p.x + p.length - ins, p.y + ins),
                "bottom": (p.x + ins, p.y + p.width - ins, p.x + p.length - ins, p.y + p.width - ins),
                "left": (p.x + ins, p.y + ins, p.x + ins, p.y + p.width - ins),
                "right": (p.x + p.length - ins, p.y + ins, p.x + p.length - ins, p.y + p.width - ins),
            }
            for side, e in ed.items():
                if not e:
                    continue
                x1, y1, x2, y2 = seg[side]
                out.append(f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" '
                           f'stroke="{escape(e["color"])}" stroke-width="{sw:.1f}"/>')
        cx, cy = p.x + p.length / 2, p.y + p.width / 2
        name = (part_names or {}).get(p.part_id) or (part.name if part else "")
        num = str(p.part_uid)
        big = min(fs * 2.0, p.width * 0.45, p.length / max(1, len(num)) * 0.9)
        if label in ("number", "number_name"):
            out.append(f'<text x="{fmt(cx)}" y="{fmt(cy)}" font-size="{big:.1f}" font-weight="bold" fill="#241400" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(num)}</text>')
        if label in ("name", "number_name") and name and p.width > fs * 3.2 and p.length > fs * 6:
            dy = big * 0.9 if label == "number_name" else 0
            max_chars = max(3, int(p.length / (fs * 0.62)))
            out.append(f'<text x="{fmt(cx)}" y="{fmt(cy + dy)}" font-size="{fs * 0.85:.1f}" fill="#3a2600" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(name[:max_chars])}</text>')
        # o'lchamlar: pastki-chap burchakda uzunlik, o'ng tomonda en (vertikal)
        if p.length > fs * 3 and p.width > fs * 1.4:
            out.append(f'<text x="{fmt(p.x + fs * 0.35)}" y="{fmt(p.y + p.width - fs * 0.35)}" font-size="{fs:.1f}" '
                       f'fill="#241400">{fmt(p.length)}</text>')
        if p.width > fs * 3 and p.length > fs * 1.4:
            tx, ty = p.x + p.length - fs * 0.4, p.y + fs * 0.35
            out.append(f'<text x="{fmt(tx)}" y="{fmt(ty)}" font-size="{fs:.1f}" fill="#241400" '
                       f'transform="rotate(90 {fmt(tx)} {fmt(ty)})">{fmt(p.width)}</text>')
    out.append("</svg>")
    return "".join(out)


# ───────────────────────── Hisobot ─────────────────────────
def _table(headers: list[str], rows: list[list], cls: str = "") -> str:
    h = "".join(f"<th>{escape(str(x))}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c if str(c).startswith('<') else escape(str(c))}</td>" for c in r) + "</tr>"
                for r in rows)
    return f"<table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def _qr_svg(data: str, scale: int = 2) -> str:
    try:
        import segno
        return segno.make(data, error="m").svg_inline(scale=scale, border=1)
    except Exception:  # noqa: BLE001 — segno o'rnatilmagan bo'lsa QR chiqmaydi
        return ""


CSS = """
@page { size: A4; margin: 10mm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #1b1f24; margin: 0; }
h1 { font-size: 18px; margin: 0 0 6px; }
h2 { font-size: 15px; margin: 14px 0 6px; }
h3 { font-size: 13px; margin: 10px 0 4px; }
table { border-collapse: collapse; margin: 4px 0 10px; }
td, th { border: 1px solid #333; padding: 2px 5px; vertical-align: top; }
th { background: #e9ecef; font-weight: bold; }
td.num { text-align: right; }
.pb { page-break-before: always; }
.kv td { border: none; padding: 1px 12px 1px 0; }
.maphdr { font-weight: bold; text-align: center; margin: 8px 0 3px; font-size: 12px; }
.mapwrap { display: flex; gap: 8px; align-items: flex-start; page-break-inside: avoid; }
.mapwrap svg { max-width: 100%; height: auto; }
.side { min-width: 170px; font-size: 10px; }
.side table { margin-top: 0; }
.legend { font-size: 10px; margin-top: 4px; }
.qr svg { width: 70px; height: 70px; }
.brand { color: #0f5c9a; font-weight: bold; letter-spacing: .5px; }
.muted { color: #666; }
"""


def project_report_html(project: Project, ps: Optional[PrintSettings] = None, lang: str = "ru") -> str:
    ps = ps or PrintSettings()
    t = T.get(lang, T["ru"])
    cur = project.currency
    s = [f"<!DOCTYPE html><html lang='{lang}'><head><meta charset='utf-8'><title>{escape(project.name)}</title>"
         f"<style>{CSS}</style></head><body>"]
    total_m = sum(o.cost_material for o in project.operations)
    total_o = sum(o.cost_operation for o in project.operations)
    sec = 0
    if ps.header:
        s.append(f"<div class='brand'>MebeliX Kroy</div><h1>{t['project']}: {escape(project.name)}</h1>")
        rows = [(t["author"], project.owner or "—"), (t["order_id"], project.number),
                (t["order_date"], project.order_date), (t["ready_date"], project.ready_date),
                (t["cost_mat"], f"{fmt(total_m)} {cur}"), (t["cost_op"], f"{fmt(total_o)} {cur}"),
                (t["cost"], f"{fmt(total_m + total_o)} {cur}")]
        if project.customer:
            rows.insert(1, (t["customer"], project.customer))
        if project.mes_order_ref:
            rows.insert(2, ("MES", project.mes_order_ref))
        s.append("<table class='kv'>" + "".join(f"<tr><td><b>{escape(str(a))}</b></td><td>{escape(str(b))}</td></tr>"
                                               for a, b in rows) + "</table>")
    if ps.warehouse:
        sec += 1
        s.append(f"<h2>{sec}. {t['warehouse']}</h2>")
        rows = []
        for i, r in enumerate(warehouse_request(project), 1):
            name = r["name"]
            if r["type"] == "CS" and ps.warehouse_cut_work:
                name += f" ({t['sheets_n']}: {r['qty']} {t['pcs']}  {t['cut_len']}: {r.get('cut_m', 0)} {t['m']})"
            elif r["type"] == "EL" and ps.warehouse_edge_work:
                name += f" ({t['edge_work']}: {r.get('work_m', 0)} {t['m']})"
            rows.append([i, r["type"], r["code"], name, r["unit"], fmt(r["qty"])])
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"]], rows))
    if ps.materials_list:
        sec += 1
        s.append(f"<h2>{sec}. {t['materials']}</h2>")
        rows = []
        for i, r in enumerate(warehouse_request(project), 1):
            op = next((o for o in project.operations if o.id == r["op_id"]), None)
            price = (op.cs_material.price if op and op.cs_material else (op.el.price if op and op.el else 0))
            rows.append([i, r["type"], r["code"], r["name"], r["unit"], fmt(r["qty"]), fmt(price),
                         fmt(op.cost_material if op else 0)])
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"], t["price"], t["sum"]], rows))
    if ps.products_list and project.products:
        sec += 1
        s.append(f"<h2>{sec}. {t['products']}</h2>")
        rows = [[i, p.code, p.name, p.qty, fmt(p.cost_material), fmt(p.cost_operation),
                 fmt(round(p.cost_material + p.cost_operation, 2))] for i, p in enumerate(project.products, 1)]
        s.append(_table(["№", t["code_short"], t["name"], t["qty"], t["cost_mat_s"], t["cost_op_s"], t["cost"]], rows))
    if ps.xnc_stats:
        from .xnc import program_stats
        xs = [o for o in project.operations if o.type == OpType.XNC and o.xnc]
        if xs:
            sec += 1
            s.append(f"<h2>{sec}. {t['xnc']}</h2>")
            rows = []
            for i, o in enumerate(xs, 1):
                st = program_stats(o.xnc.program, o.xnc.length, o.xnc.width, o.xnc.thickness)
                rows.append([i, o.code, o.name, o.xnc.qty, st["drills"], fmt(st["mill_m"]), fmt(st["saw_m"]),
                             fmt(o.cost_operation)])
            s.append(_table(["№", t["code_short"], t["name"], t["qty"], t["drill"], t["mill"] + ", " + t["m"],
                             t["saw"] + ", " + t["m"], t["cost"]], rows))
    if ps.operations:
        for op in project.operations:
            if not op.print:
                continue
            sec += 1
            cls = " class='pb'" if op.new_page else ""
            if op.type == OpType.CS:
                s.append(_cs_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.EL:
                s.append(_el_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.XNC and ps.xnc_drawing:
                s.append(_xnc_section(project, op, t, sec, cls))
    s.append("</body></html>")
    return "".join(s)


def _edge_names_len(part: Part, project: Project, sides: tuple[str, str]) -> str:
    names: dict[str, int] = {}
    ops = {o.id: o for o in project.operations if o.type == OpType.EL}
    for sd in sides:
        ref = getattr(part, f"edge_{sd}")
        if ref.op_id and ref.op_id in ops:
            nm = ops[ref.op_id].name or ops[ref.op_id].code
            names[nm] = names.get(nm, 0) + 1
    return "<br>".join(f"({n}) {escape(k)}" for k, n in names.items()) or ""


def _cs_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    s = [f"<h2{cls}>{sec}. (CS) {t['cs']}: {escape(op.name)}</h2>"]
    mode = ps.cs_size_mode or project.size_mode
    mode_title = {SizeMode.BLANK: t["size_blank"], SizeMode.DETAIL: t["size_detail"],
                  SizeMode.JOINTED: t["size_jointed"]}[SizeMode(mode)]
    edges = edge_map(project)
    cut = op.cs_cut
    n = 0
    if ps.cs_parts:
        n += 1
        rows = []
        for p in op.parts:
            sz = compute_sizes(p, SizeMode(mode), edges, cut.machining_allowance if cut else 0)
            L, W = sz.blank if mode == SizeMode.BLANK else (sz.jointed if mode == SizeMode.JOINTED else sz.detail)
            marks = part_marks(p, project)
            rows.append([p.uid, fmt(L), _edge_names_len(p, project, ("top", "bottom")), fmt(W),
                         _edge_names_len(p, project, ("left", "right")), total_qty(project, p), p.used_qty,
                         p.left_qty, escape((marks + " " if marks else "") + p.name)])
        s.append(f"<h3>{n}. {t['parts']} ({mode_title})</h3>")
        s.append(_table(["№", t["length"], t["edge_len"], t["width"], t["edge_wid"], t["qty"], t["used"],
                         t["left"], t["name"]], rows))
    res = op.result
    if res and ps.cs_unplaced and res.unplaced:
        n += 1
        from collections import Counter
        cnt = Counter(res.unplaced)
        rows = [[p.uid, fmt(p.length), fmt(p.width), cnt[p.id], escape(p.name)] for p in op.parts if p.id in cnt]
        s.append(f"<h3>{n}. {t['unplaced']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["qty"], t["name"]], rows))
    if res and ps.cs_sheets:
        n += 1
        mat = op.cs_material
        rows = []
        tot_area = tot_sum = 0.0
        for i, sh in enumerate(op.sheets, 1):
            if not sh.used_qty:
                continue
            area = sh.length * sh.width / 1e6
            if mat and mat.price_per_m2:
                price = mat.price; summ = price * area * sh.used_qty
            else:
                price = mat.price if mat else 0; summ = price * sh.used_qty
            tot_area += area * sh.used_qty; tot_sum += summ
            rows.append([i, fmt(sh.length), fmt(sh.width), fmt(round(area, 3)), sh.used_qty, fmt(price),
                         fmt(round(area * sh.used_qty, 3)), fmt(round(summ, 2))])
        rows.append(["", "", "", "", "", f"<b>{t['total']}:</b>", f"<b>{fmt(round(tot_area, 3))}</b>",
                     f"<b>{fmt(round(tot_sum, 2))}</b>"])
        s.append(f"<h3>{n}. {t['sheets']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["area"], t["sheets_qty"], t["price"], t["total_area"],
                         t["sum"]], rows))
    if res and ps.cs_remnants and res.remnants:
        n += 1
        from collections import Counter
        cnt = Counter((o.length, o.width, o.business) for o in res.remnants)
        rows = [[i, fmt(l), fmt(w), fmt(round(l * w / 1e6, 3)), c, t["remnant"] if b else "—"]
                for i, ((l, w, b), c) in enumerate(sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1]), 1)]
        s.append(f"<h3>{n}. {t['remnants']}</h3>")
        s.append(_table(["№", t["length"], t["width"], t["area"], t["qty"], ""], rows))
    if res and ps.cs_maps:
        names = {p.id: p.name for p in op.parts}
        parts_by_id = {p.id: p for p in op.parts}
        legend = _edge_legend(project, op)
        for m in res.maps:
            s.append(f"<div class='maphdr'>{escape(op.name)} &nbsp; {escape(map_header(m, res, ps.map_header_fields))}</div>")
            svg = map_svg(m, 620, names, project, op, ps.map_part_label, ps.map_edges, ps.map_remnant_number,
                          ps.map_mirror)
            side = ""
            if ps.map_parts_list:
                from collections import Counter
                cnt = Counter(pl.part_id for pl in m.placements)
                rows = []
                for pid, c in sorted(cnt.items(), key=lambda kv: parts_by_id[kv[0]].uid if kv[0] in parts_by_id else 0):
                    p = parts_by_id.get(pid)
                    if p is None:
                        continue
                    rows.append([p.uid, fmt(p.length), fmt(p.width), c, part_marks(p, project)])
                side += _table(["№", "Дл", "Шр", "Кл", "Мт"], rows)
                if legend:
                    side += f"<div class='legend'>{legend}</div>"
            if ps.cs_commands:
                side += _table(["Кд", "Р", "К", "Д"], [[f"{c.code}{c.level}", fmt(c.size), c.count, c.ref]
                                                      for c in m.commands])
            if ps.map_qr:
                qr = _qr_svg(f"MXK:{project.number}:{op.id}:{m.index}")
                if qr:
                    side += f"<div class='qr'>{qr}</div>"
            s.append(f"<div class='mapwrap'><div>{svg}</div><div class='side'>{side}</div></div>")
    return "".join(s)


def _edge_legend(project: Project, op: Operation) -> str:
    used = set()
    for p in op.parts:
        for sd in ("top", "bottom", "left", "right"):
            ref = getattr(p, f"edge_{sd}")
            if ref.op_id:
                used.add(ref.op_id)
    out = []
    for o in project.operations:
        if o.type == OpType.EL and o.id in used:
            sym = (o.el.symbol if o.el else "?") or "?"
            lines = (o.el.marker_lines if o.el else 1) or 1
            out.append(f"<span style='color:{escape(o.el.color if o.el else '#000')}'>■</span> "
                       f"{escape(sym)}-{lines}: {escape(o.name)}")
    marks = {m for p in op.parts for m in part_marks(p, project)}
    if "*" in marks:
        out.append("[*] Фрезерование")
    if "%" in marks:
        out.append("[%] Сверление")
    if "=" in marks:
        out.append("[=] Пазование")
    return "<br>".join(out)


def _el_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    u = edge_usage(project, op)
    el = op.el
    cur = project.currency
    s = [f"<h2{cls}>{sec}. (EL) {t['el']}: {('(' + escape(op.code) + ') ') if op.code else ''}{escape(op.name)}</h2>"]
    if ps.el_params and el:
        left = [("Ширина", f"{fmt(el.width)} мм"), ("Толщина", f"{fmt(el.thickness)} мм"),
                ("Ширина прифуговки", f"{fmt(el.jointing_width)} мм"), ("Процент отхода", f"{fmt(el.waste_percent)}%"),
                ("Длина остатка по краям", f"{fmt(el.overhang)} мм"), ("Мин. оклеиваемая длина", f"{fmt(el.min_glue_length)} мм"),
                ("Символ", el.symbol), ("Линии маркировки", el.marker_lines)]
        right = [(t["mat_len"], f"{u['material_m']} м"), ("Цена материала", f"{fmt(el.price)} {cur}"),
                 ("Стоимость материала", f"{fmt(op.cost_material)} {cur}"), ("Цена операции (м)", f"{fmt(el.op_price)} {cur}"),
                 (t["edge_work"], f"{u['work_m']} м"), ("Стоимость операции", f"{fmt(op.cost_operation)} {cur}"),
                 (t["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        rows = "".join(f"<tr><td>{escape(str(a[0]))}</td><td>{escape(str(a[1]))}</td><td style='width:30px'></td>"
                       f"<td>{escape(str(b[0]))}</td><td>{escape(str(b[1]))}</td></tr>"
                       for a, b in zip(left + [("", "")] * (len(right) - len(left)), right + [("", "")] * (len(left) - len(right))))
        s.append(f"<table class='kv'>{rows}</table>")
    if ps.el_parts:
        s.append(f"<h3>1. {t['parts']}</h3>")
        s.append(_table(["№", "Товар", t["length"], "О. дл.", t["width"], "О. шр.", t["qty"], "Дл. кр-ки", t["name"]],
                        [[i, escape(r["material"]), fmt(r["length"]), r["edges_len"], fmt(r["width"]), r["edges_wid"],
                          r["qty"], fmt(r["edge_m"]), escape(r["name"])] for i, r in enumerate(u["rows"], 1)]))
    return "".join(s)


def _xnc_section(project: Project, op: Operation, t: dict, sec: int, cls: str) -> str:
    from .xnc import xnc_drawing_svg, xnc_holes_table
    x = op.xnc
    if not x:
        return ""
    part = None
    for o in project.operations:
        for p in o.parts:
            if op.id in p.xnc_op_ids:
                part = (p, o)
    s = [f"<h2{cls}>{sec}. (XNC) {t['xnc']}: {escape(op.code)} {escape(op.name)}</h2>"]
    s.append("<div class='mapwrap'>" + xnc_drawing_svg(op, project, 560) + "<div class='side'>")
    rows = xnc_holes_table(op)
    if rows:
        s.append(_table(["№", "X", "Y", "Ø", "DP", "T"], rows))
    stamp = [(t["name"], op.name), (t["product"], ""), (t["detail"], part[0].name if part else ""),
             (t["material"], part[1].name if part else ""),
             (t["blank_size"], f"{fmt(x.length)} × {fmt(x.width)} × {fmt(x.thickness)}"),
             (t["code"], op.code), (t["qty"], x.qty)]
    s.append("<table>" + "".join(f"<tr><th>{escape(str(a))}</th><td>{escape(str(b))}</td></tr>" for a, b in stamp) + "</table>")
    s.append("</div></div>")
    return "".join(s)
