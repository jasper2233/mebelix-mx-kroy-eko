"""Kroy kartasini SVG ga chizish va chop etish uchun HTML hisobot (A4, brauzerda PDF).

Hisobot tuzilishi xodimlarga tanish tartibda (UI_SPEC §8): sarlavha → omborga talabnoma →
har operatsiya (CS: detallar, listlar, qoldiqlar, kartalar; EL: parametrlar + detallar; XNC: chizma).
Ranglar/shriftlar — MebeliX palitrasi.
"""
from __future__ import annotations

import re
from typing import Optional

from markupsafe import Markup, escape

from ..models import (CutMap, CuttingResult, OpType, Operation, Part, PrintSettings, Project,
                      SizeMode)
from .calc import (edge_map, edge_usage, effective_qty, groove_usage, material_prices, product_qty, total_qty,
                   warehouse_request)
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
        "cost_unit": "Стоимость (1 шт)", "cost_all": "Всего",
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
        "el_width": "Ширина", "el_thick": "Толщина", "el_joint": "Ширина прифуговки", "el_waste": "Процент отхода",
        "el_overhang": "Длина остатка по краям", "el_min_glue": "Мин. оклеиваемая длина", "el_symbol": "Символ",
        "el_lines": "Линии маркировки", "el_mat_price": "Цена материала", "el_mat_cost": "Стоимость материала",
        "el_op_price": "Цена операции (м)", "el_op_cost": "Стоимость операции", "mm": "мм",
        "el_goods": "Товар", "el_e_len": "О. дл.", "el_e_wid": "О. шр.", "el_edge_len": "Дл. кр-ки",
        "s_len": "Дл", "s_wid": "Шр", "s_qty": "Кл", "s_marks": "Мт", "c_code": "Кд", "c_size": "Р", "c_count": "К",
        "c_ref": "Д", "lg_mill": "Фрезерование", "lg_drill": "Сверление", "lg_groove": "Пазование",
        "u_sheets": "Листы", "u_m": "м", "u_pcs": "шт",
        "el_narrow": "сторона, перпендикулярная кромке, меньше ограничения",
        "gr": "Пазование", "gr_width": "Ширина паза", "gr_depth": "Глубина паза", "gr_offset": "Отступ",
        "gr_incl": "включительно", "gr_saw": "Толщина пилы", "gr_price": "Цена метра паза",
        "gr_usage": "Длина пазования", "gr_passes": "Проходов пилы", "gr_cut": "Длина пропила",
        "gr_pv": "ПВ", "gr_pn": "ПН", "gr_pl": "ПЛ", "gr_pp": "ПП", "gr_len": "Д-на паза", "gr_back": "обр.",
        "by_part_size": "По размеру детали", "yes": "Да", "no": "Нет",
    },
    "uz": {
        "project": "Loyiha", "author": "Muallif", "order_id": "Loyiha ID", "order_date": "Buyurtma sanasi",
        "ready_date": "Tayyor bo'lish sanasi", "cost_mat": "Material narxi", "cost_op": "Ish narxi",
        "cost_unit": "Narx (1 dona)", "cost_all": "Jami",
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
        "el_width": "Eni", "el_thick": "Qalinligi", "el_joint": "Prifugovka eni", "el_waste": "Chiqindi foizi",
        "el_overhang": "Chetlardagi qoldiq uzunligi", "el_min_glue": "Min. yopishtiriladigan uzunlik", "el_symbol": "Belgi",
        "el_lines": "Belgilash chiziqlari", "el_mat_price": "Material narxi", "el_mat_cost": "Material qiymati",
        "el_op_price": "Ish narxi (m)", "el_op_cost": "Ish qiymati", "mm": "mm",
        "el_goods": "Tovar", "el_e_len": "Kr. uz.", "el_e_wid": "Kr. en", "el_edge_len": "Kromka uz.",
        "s_len": "Uz", "s_wid": "En", "s_qty": "Son", "s_marks": "Bel", "c_code": "Kd", "c_size": "O'l", "c_count": "Son",
        "c_ref": "D", "lg_mill": "Frezerlash", "lg_drill": "Teshik", "lg_groove": "Pazlash",
        "u_sheets": "List", "u_m": "m", "u_pcs": "dona",
        "el_narrow": "kromkaga perpendikulyar tomon chegaradan kichik",
        "gr": "Pazlash", "gr_width": "Paz eni", "gr_depth": "Paz chuqurligi", "gr_offset": "Chetdan masofa",
        "gr_incl": "qo'shilgan holda", "gr_saw": "Arra qalinligi", "gr_price": "1 m paz narxi",
        "gr_usage": "Pazlash uzunligi", "gr_passes": "Arra o'tishlari", "gr_cut": "Kesish uzunligi",
        "gr_pv": "Yu", "gr_pn": "Pa", "gr_pl": "Ch", "gr_pp": "O'", "gr_len": "Paz uz.", "gr_back": "orqa",
        "by_part_size": "Detal o'lchami bo'yicha", "yes": "Ha", "no": "Yo'q",
    },
}


def fmt(v: float) -> str:
    if v is None:
        return ""
    r = round(float(v), 2)
    # `:g` 6 ta raqamdan keyin «1.13283e+06» beradi (pul/narxlar uchun yaramaydi) — qat'iy ≤ 2 xona
    return str(int(r)) if r == int(r) else f"{r:.2f}".rstrip("0").rstrip(".")


def num(v, default: str = "0") -> str:
    """Tashqaridan kelgan (JSON) son — faqat son sifatida chiqadi (SVG atributiga matn tushmaydi)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return fmt(f) if f == f and abs(f) != float("inf") else default


_COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20}|rgba?\([0-9.,\s%]{5,40}\))$")


def safe_color(c, default: str = "#000") -> str:
    """Rang faqat #hex / nom / rgb() ko'rinishida (style/stroke atributiga boshqa narsa tushmaydi)."""
    c = (c or "").strip() if isinstance(c, str) else ""
    return c if _COLOR_RE.match(c) else default


# Hisobot va etiketkalarda skript bo'lmaydi: brauzer har qanday <script>/on*= ni bajarmaydi.
REPORT_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:"
CSP_META = f'<meta http-equiv="Content-Security-Policy" content="{REPORT_CSP}">'


# ───────────────────────── Karta sarlavhasi ─────────────────────────
HEADER_FIELDS = ("N", "S", "C", "Cp", "LT", "CT", "F", "AP", "AM", "AW", "PK")


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
        elif f == "PK":
            parts.append(f"PK:{m.packs}/{res.total_packs}×{res.sheets_per_pack}")
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
            # «Линии маркировки»: 0..3 (0 — chiziqsiz); belgi/rang bo'sh bo'lsa — standart
            out[side] = {"symbol": (el.symbol if el else "") or "?", "color": (el.color if el else "#000") or "#000",
                         "lines": max(0, min(3, int(el.marker_lines))) if el else 1, "name": op.name}
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
def _hatch_pattern(pid: str, kind: str, s: float, sw: float) -> str:
    """To'ldirish shtrixlash shabloni (SVG <pattern>): s — qadam, sw — chiziq qalinligi (list mm birligida)."""
    if kind == "horizontal":
        d = f"M0 {fmt(s / 2)} H{fmt(s)}"
    elif kind == "vertical":
        d = f"M{fmt(s / 2)} 0 V{fmt(s)}"
    elif kind == "cross":
        d = f"M0 {fmt(s)} L{fmt(s)} 0 M0 0 L{fmt(s)} {fmt(s)}"
    else:                                          # diag
        d = f"M0 {fmt(s)} L{fmt(s)} 0"
    return (f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{fmt(s)}" height="{fmt(s)}">'
            f'<path d="{d}" stroke="#000" stroke-opacity=".38" stroke-width="{sw:.1f}" fill="none"/></pattern>')


def _allowance_insets(part: Part, ma: float, rotated: bool) -> tuple[float, float, float, float]:
    """Pripusk (detal tomonlari + umumiy «Припуск на обработку заготовки») — joylashgan detalning chap/yuqori/o'ng/past
    tomonidan ichkariga qancha (mm). Burilgan detalda tomonlar `rotate_edges` bilan bir xil almashadi."""
    t, b, l, r = part.allow_top + ma, part.allow_bottom + ma, part.allow_left + ma, part.allow_right + ma
    if rotated:
        return b, l, t, r              # (left, top, right, bottom) = (orig bottom, orig left, orig top, orig right)
    return l, t, r, b


def map_svg(m: CutMap, width_px: int = 900, part_names: Optional[dict[str, str]] = None,
            project: Optional[Project] = None, op: Optional[Operation] = None,
            label: str = "number_name", show_edges: bool = True, remnant_numbers: bool = True,
            mirror: bool = False, style: Optional[PrintSettings] = None, uid: str = "m",
            show_allowance: bool = True) -> str:
    """Karta: detallar — to'q sariq (raqam + o'lchamlar: pastda uzunlik, o'ngda en), chiqindi — kulrang,
    деловой qoldiq — ko'k (Д№ o'lcham bilan). Kromkali tomonlar — rangli qalin chiziq (1..3 ta, «Линии маркировки»;
    0 — chiziqsiz). mirror=True («Зеркально»): faqat geometriya gorizontal akslanadi (koordinatalar o'zgaradi),
    matn va raqamlar o'qiladigan holda qoladi.
    style (PrintSettings) berilsa: shrift o'lcham/qalinligi, detal/chiqindi rangi va shtrixlash, ishlov belgilari;
    show_allowance — pripusk (pripusk > 0 bo'lsa) detal ichida punktir to'rtburchak. uid — shtrix shablon id prefiksi."""
    L, W = m.sheet_length, m.sheet_width
    k = width_px / L
    h_px = W * k
    fs = max(16.0, min(L, W) / 42)
    parts_by_id = {p.id: p for p in op.parts} if op else {}
    st = style if style is not None else PrintSettings()
    pt_to_mm = (96.0 / 72.0) / k if k > 0 else 1.0       # pt (chop) → SVG birligi (list mm); k — px/mm
    fd = max(2.0, st.map_dim_font * pt_to_mm) if st.map_dim_font > 0 else fs     # o'lchamlar shrifti
    part_fill = safe_color(st.map_part_fill, PART_FILL)
    waste_fill = safe_color(st.map_waste_fill, WASTE_FILL)
    hatch_step, hatch_sw = max(12.0, fs * 0.9), max(1.0, fs / 12)
    ma = (op.cs_cut.machining_allowance if op is not None and op.cs_cut else 0) or 0

    def X(x: float) -> float:                 # nuqta (matn markazi, chiziq uchi)
        return L - x if mirror else x

    def RX(x: float, w: float) -> float:      # to'rtburchakning chap chegarasi
        return L - x - w if mirror else x

    def fl(v) -> float:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return f if f == f and abs(f) != float("inf") else 0.0

    end_anchor = ' text-anchor="end"' if mirror else ""     # ko'zguda pastki-chap matn o'ng chetga tiraladi
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(L)} {fmt(W)}" '
           f'width="{width_px}" height="{h_px:.0f}" font-family="Arial, Helvetica, sans-serif">',
           f'<rect x="0" y="0" width="{fmt(L)}" height="{fmt(W)}" fill="{TRIM_FILL}" stroke="#222" stroke-width="{fs / 5:.1f}"/>']
    hp_id, hw_id = f"{uid}-hp", f"{uid}-hw"        # shtrixlash shablonlari (faqat tanlangan bo'lsa)
    if st.map_part_hatch != "none" or st.map_waste_hatch != "none":
        out.insert(1, "<defs>" + (_hatch_pattern(hp_id, st.map_part_hatch, hatch_step, hatch_sw) if st.map_part_hatch != "none" else "")
                   + (_hatch_pattern(hw_id, st.map_waste_hatch, hatch_step, hatch_sw) if st.map_waste_hatch != "none" else "")
                   + "</defs>")
    # foydali zona (chiqindi fon) — daraxt ildizidan
    if m.strips:
        r = m.strips[0]
        wx, wy, wl, ww = num(RX(fl(r.get("x")), fl(r.get("l")))), num(r.get("y")), num(r.get("l")), num(r.get("w"))
        out.append(f'<rect x="{wx}" y="{wy}" width="{wl}" height="{ww}" fill="{waste_fill}"/>')
        if st.map_waste_hatch != "none":
            out.append(f'<rect x="{wx}" y="{wy}" width="{wl}" height="{ww}" fill="url(#{hw_id})"/>')
    for o in m.offcuts:
        if o.kind != "remnant":
            continue
        fill = REMNANT_FILL if o.business else REMNANT_SMALL
        out.append(f'<rect x="{fmt(RX(o.x, o.length))}" y="{fmt(o.y)}" width="{fmt(o.length)}" height="{fmt(o.width)}" '
                   f'fill="{fill}" stroke="#3b6ea5" stroke-width="{fs / 8:.1f}"/>')
        if remnant_numbers and o.length > fs * 4 and o.width > fs * 1.6:
            out.append(f'<text x="{fmt(X(o.x + o.length / 2))}" y="{fmt(o.y + o.width / 2)}" font-size="{fs * 1.1:.1f}" '
                       f'fill="#1f3f66" text-anchor="middle" dominant-baseline="middle">Д{int(o.number)} '
                       f'{fmt(o.length)}×{fmt(o.width)}</text>')
    for p in m.placements:
        out.append(f'<rect x="{fmt(RX(p.x, p.length))}" y="{fmt(p.y)}" width="{fmt(p.length)}" height="{fmt(p.width)}" '
                   f'fill="{part_fill}" stroke="{PART_STROKE}" stroke-width="{fs / 7:.1f}"/>')
        if st.map_part_hatch != "none":
            out.append(f'<rect x="{fmt(RX(p.x, p.length))}" y="{fmt(p.y)}" width="{fmt(p.length)}" height="{fmt(p.width)}" '
                       f'fill="url(#{hp_id})"/>')
        part = parts_by_id.get(p.part_id)
        if show_allowance and part is not None and (ma > 0 or part.allow_top or part.allow_bottom or part.allow_left
                                                    or part.allow_right):
            il, it, ir, ib = _allowance_insets(part, ma, p.rotated)            # pripusk: punktir to'rtburchak (DM-010)
            aw, ah = p.length - il - ir, p.width - it - ib
            if aw > 0 and ah > 0:
                out.append(f'<rect x="{fmt(RX(p.x + il, aw))}" y="{fmt(p.y + it)}" width="{fmt(aw)}" height="{fmt(ah)}" '
                           f'fill="none" stroke="{PART_STROKE}" stroke-width="{fs / 14:.1f}" '
                           f'stroke-dasharray="{fs * 0.6:.1f} {fs * 0.4:.1f}"/>')
        if show_edges and part is not None and project is not None:
            ed = rotate_edges(part_edges(part, project), p.rotated)
            sw = fs / 6                                   # ingichka kromka chizig'i (ekrandagi karta bilan bir xil uslub)
            ins = sw / 2 + fs / 12
            seg = {
                "top": (p.x + ins, p.y + ins, p.x + p.length - ins, p.y + ins),
                "bottom": (p.x + ins, p.y + p.width - ins, p.x + p.length - ins, p.y + p.width - ins),
                "left": (p.x + ins, p.y + ins, p.x + ins, p.y + p.width - ins),
                "right": (p.x + p.length - ins, p.y + ins, p.x + p.length - ins, p.y + p.width - ins),
            }
            for side, e in ed.items():
                if not e or e.get("lines", 1) <= 0:
                    continue
                x1, y1, x2, y2 = seg[side]
                n_lines = int(e.get("lines", 1))
                lw = sw / (2 * n_lines - 1)               # n ta chiziq va ular orasidagi bo'shliqlar — umumiy qalinlik sw
                for j in range(n_lines):
                    off = (j - (n_lines - 1) / 2) * 2 * lw
                    dxo, dyo = (off, 0.0) if side in ("left", "right") else (0.0, off)
                    out.append(f'<line x1="{fmt(X(x1 + dxo))}" y1="{fmt(y1 + dyo)}" x2="{fmt(X(x2 + dxo))}" '
                               f'y2="{fmt(y2 + dyo)}" stroke="{safe_color(e["color"])}" stroke-width="{lw:.1f}"/>')
        cx, cy = p.x + p.length / 2, p.y + p.width / 2
        name = (part_names or {}).get(p.part_id) or (part.name if part else "")
        uid_s = str(p.part_uid)
        big = min(fs * 2.0, p.width * 0.45, p.length / max(1, len(uid_s)) * 0.9)
        if st.map_num_font > 0:                       # detal raqami shrifti qo'lda (pt); detalga sig'maydigan bo'lsa kichraytiriladi
            big = min(max(2.0, st.map_num_font * pt_to_mm), p.width * 0.8, p.length / max(1, len(uid_s)) * 1.1)
        num_weight = ' font-weight="bold"' if st.map_num_bold else ""
        if label in ("number", "number_name"):
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(cy)}" font-size="{big:.1f}"{num_weight} fill="#241400" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(uid_s)}</text>')
        if label in ("name", "number_name") and name and p.width > fs * 3.2 and p.length > fs * 6:
            dy = big * 0.9 if label == "number_name" else 0
            max_chars = max(3, int(p.length / (fs * 0.62)))
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(cy + dy)}" font-size="{fs * 0.85:.1f}" fill="#3a2600" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(name[:max_chars])}</text>')
        # ishlov belgilari (= pazlash, * frezerlash, % teshik): detalning yuqori-chap burchagida (ixtiyoriy)
        if st.map_part_marks and part is not None and project is not None:
            mk = part_marks(part, project)
            if mk and p.length > fs * 2.5 and p.width > fs * 2.2:
                out.append(f'<text x="{fmt(X(p.x + fs * 0.35))}" y="{fmt(p.y + fs * 1.25)}" font-size="{fs * 1.1:.1f}" '
                           f'font-weight="bold" fill="#241400"{end_anchor}>{escape(mk)}</text>')
        # o'lchamlar: pastki-chap burchakda uzunlik, o'ng tomonda en (vertikal); ko'zguda — teskari burchaklarda
        dim_weight = ' font-weight="bold"' if st.map_dim_bold else ""
        if p.length > fd * 3 and p.width > fd * 1.4:
            out.append(f'<text x="{fmt(X(p.x + fd * 0.35))}" y="{fmt(p.y + p.width - fd * 0.35)}" font-size="{fd:.1f}"'
                       f'{dim_weight} fill="#241400"{end_anchor}>{fmt(p.length)}</text>')
        if st.map_dim_rotate:
            if p.width > fd * 3 and p.length > fd * 1.4:
                tx, ty = X(p.x + p.length - fd * 0.4), p.y + fd * 0.35
                out.append(f'<text x="{fmt(tx)}" y="{fmt(ty)}" font-size="{fd:.1f}"{dim_weight} fill="#241400" '
                           f'transform="rotate(90 {fmt(tx)} {fmt(ty)})">{fmt(p.width)}</text>')
        elif p.width > fd * 3 and p.length > fd * (len(fmt(p.width)) * 0.6 + 1.2):
            # «Разворачивать шрифты» o'chiq: en yozuvi aylantirilmaydi — yuqori-o'ng burchakda gorizontal
            w_anchor = "" if mirror else ' text-anchor="end"'          # ko'zguda yuqori-chapda, matn o'ngga o'sadi
            out.append(f'<text x="{fmt(X(p.x + p.length - fd * 0.35))}" y="{fmt(p.y + fd * 1.15)}" font-size="{fd:.1f}"'
                       f'{dim_weight} fill="#241400"{w_anchor}>{fmt(p.width)}</text>')
    out.append("</svg>")
    return "".join(out)


# ───────────────────────── Hisobot ─────────────────────────
def _cell(c) -> str:
    """Katak: Markup (ishonchli, o'zimiz yasagan HTML) — o'zicha; qolgan hamma narsa — escape."""
    if isinstance(c, Markup):
        return str(c)
    return str(escape("" if c is None else str(c)))


class Cell:
    """Sinf berilgan katak: `Cell(mazmun, "hl")` — <td class='hl'>; mazmun `_cell` qoidasi bo'yicha (Markup — o'zicha)."""
    def __init__(self, content, cls: str = ""):
        self.content, self.cls = content, cls


class GroupRow:
    """Jadvalda butun qatorga cho'zilgan guruh sarlavhasi (masalan, mahsulot nomi) — matn escape qilinadi."""
    def __init__(self, title):
        self.title = title


def _td(c) -> str:
    if isinstance(c, Cell):
        return f"<td class='{escape(c.cls)}'>{_cell(c.content)}</td>"
    return f"<td>{_cell(c)}</td>"


def _table(headers: list[str], rows: list[list], cls: str = "") -> str:
    """Jadval HTML (oddiy str — Markup emas, aks holda keyingi `+=` qo'shimchalarni qayta escape qiladi)."""
    h = "".join(f"<th>{_cell(x)}</th>" for x in headers)
    b = "".join(f"<tr class='grp'><td colspan='{len(headers)}'>{_cell(r.title)}</td></tr>" if isinstance(r, GroupRow)
                else "<tr>" + "".join(_td(c) for c in r) + "</tr>" for r in rows)
    return f"<table class='{escape(cls)}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def _qr_svg(data: str, scale: int = 2) -> str:
    try:
        import segno
        return segno.make(data, error="m").svg_inline(scale=scale, border=1)
    except Exception:  # noqa: BLE001 — segno o'rnatilmagan bo'lsa QR chiqmaydi
        return ""


def _page_css(ps: PrintSettings) -> str:
    """«Поля страницы»: chap/o'ng/yuqori/past chegaralar (mm)."""
    def mm(v) -> str:
        try:
            return f"{max(0.0, min(50.0, float(v))):g}mm"
        except (TypeError, ValueError):
            return "10mm"
    margin = f"{mm(ps.page_margin_top)} {mm(ps.page_margin_right)} {mm(ps.page_margin_bottom)} {mm(ps.page_margin_left)}"
    # `land` — nomlangan sahifa: «Альбомная» kartalar (`.land` bloki) gorizontal A4 ga chiqadi
    return f"@page {{ size: A4; margin: {margin}; }} @page land {{ size: A4 landscape; margin: {margin}; }}"


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
.land { page: land; }
.grp td { background: #e9ecef; font-weight: bold; }
td.hl { background: #fff1c2; font-weight: bold; }
.kv td { border: none; padding: 1px 12px 1px 0; }
.maphdr { font-weight: bold; text-align: center; margin: 8px 0 3px; font-size: 12px;
          page-break-after: avoid; break-after: avoid; }
.mapcard { page-break-inside: avoid; break-inside: avoid; }
.mapwrap { display: flex; gap: 8px; align-items: flex-start; page-break-inside: avoid; break-inside: avoid; }
.mapwrap svg { max-width: 100%; height: auto; }
.side { min-width: 170px; font-size: 10px; }
.side table { margin-top: 0; }
.legend { font-size: 10px; margin-top: 4px; }
.qr svg { width: 70px; height: 70px; }
.brand { color: #0f5c9a; font-weight: bold; letter-spacing: .5px; }
.muted { color: #666; }
"""


def project_report_html(project: Project, ps: Optional[PrintSettings] = None, lang: str = "ru") -> str:
    """Hisobot HTML. Ichidagi barcha tarjima qilinadigan matnlar (talabnoma va h.k.) — hisobot tilida."""
    from ..i18n import LANG
    lang = lang if lang in T else "ru"
    token = LANG.set(lang)
    try:
        return _project_report_html(project, ps, lang)
    finally:
        LANG.reset(token)


def _project_report_html(project: Project, ps: Optional[PrintSettings], lang: str) -> str:
    ps = ps or PrintSettings()
    t = T[lang]
    cur = project.currency
    s = [f"<!DOCTYPE html><html lang='{lang}'><head><meta charset='utf-8'>{CSP_META}<title>{escape(project.name)}</title>"
         f"<style>{CSS}{_page_css(ps)}</style></head><body>"]
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
            if r["type"] in ("CS", "CN") and ps.warehouse_cut_work and not r.get("remnant"):
                name += f" ({t['sheets_n']}: {r['qty']} {t['pcs']}  {t['cut_len']}: {r.get('cut_m', 0)} {t['m']})"
            elif r["type"] == "CL" and ps.warehouse_cut_work and not r.get("remnant"):     # (CL) polosalar va kesim uzunligi
                name += f" ({t['cl_strips_n']}: {fmt(r.get('strips', 0))} {t['pcs']}  {t['cut_len']}: {r.get('cut_m', 0)} {t['m']})"
            elif r["type"] == "EL" and ps.warehouse_edge_work:
                name += f" ({t['edge_work']}: {r.get('work_m', 0)} {t['m']})"
            rows.append([i, r["type"], r["code"], name, t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"])])
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"]], rows))
    if ps.materials_list:
        sec += 1
        s.append(f"<h2>{sec}. {t['materials']}</h2>")
        rows = []
        for i, r in enumerate(warehouse_request(project), 1):
            rows.append([i, r["type"], r["code"], r["name"], t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"]),
                         fmt(r.get("price", 0)),
                         fmt(r.get("sum", 0))])
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"], t["price"], t["sum"]], rows))
    if ps.products_list and project.products:
        sec += 1
        s.append(f"<h2>{sec}. {t['products']}</h2>")
        # narxlar 1 dona uchun; «Всего» = × soni
        rows = [[i, p.code, p.name, p.qty, fmt(p.cost_material), fmt(p.cost_operation),
                 fmt(round(p.cost_material + p.cost_operation, 2)),
                 fmt(round((p.cost_material + p.cost_operation) * p.qty, 2))] for i, p in enumerate(project.products, 1)]
        s.append(_table(["№", t["code_short"], t["name"], t["qty"], t["cost_mat_s"], t["cost_op_s"], t["cost_unit"],
                         t["cost_all"]], rows))
    if ps.xnc_stats:
        from .xnc import xnc_stats
        xs = [o for o in project.operations if o.type == OpType.XNC and o.xnc]
        if xs:
            sec += 1
            s.append(f"<h2>{sec}. {t['xnc']}</h2>")
            rows = []
            for i, o in enumerate(xs, 1):
                st = xnc_stats(o.xnc)
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
            elif op.type == OpType.CL:
                from .cl_render import cl_section        # (CL) Погонажный раскрой: parametrlar, detallar, polosalar, otxodlar, kartalar
                s.append(cl_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.CN:
                from .cn_render import cn_section        # (CN, W16) Нестинговый раскрой: parametrlar, shakllar, listlar, qoldiqlar, kontur kartalari
                s.append(cn_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.EL:
                s.append(_el_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.GR and (ps.gr_params or ps.gr_parts):
                s.append(_gr_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.XNC and ps.xnc_drawing:
                s.append(_xnc_section(project, op, t, sec, cls))
            elif op.type == OpType.SP and (ps.sp_params or ps.sp_parts):
                from .sp_render import sp_section        # (SP) Обработка поверхности: parametrlar + hisob + detallar jadvali
                s.append(sp_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.O and (ps.o_params or ps.o_materials):
                from .o_render import o_section        # (O) Комплектация: parametrlar bloki + materiallar jadvali
                s.append(o_section(project, op, ps, t, sec, cls))
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
    return Markup("<br>").join(Markup("({}) {}").format(n, k) for k, n in names.items())


T["ru"].update(no_product="Без изделия", u_m2="м²")
T["uz"].update(no_product="Mahsulotsiz", u_m2="m²")
from .cl_labels import CL_T                      # noqa: E402  (CL, W11) pogonaj kroy hisobot matnlari
T["ru"].update(CL_T["ru"])
T["uz"].update(CL_T["uz"])
from .cn_labels import CN_T                      # noqa: E402  (CN, W16) nesting hisobot matnlari
T["ru"].update(CN_T["ru"])
T["uz"].update(CN_T["uz"])


def _cs_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    # `cs_title` o'chiq bo'lsa sarlavha chiqmaydi, lekin «Н.Стр» (yangi sahifa) saqlanadi
    s = [f"<h2{cls}>{sec}. (CS) {t['cs']}: {escape(op.name)}</h2>" if ps.cs_title else f"<div{cls}></div>"]
    mode = ps.cs_size_mode or project.size_mode
    mode_title = {SizeMode.BLANK: t["size_blank"], SizeMode.DETAIL: t["size_detail"],
                  SizeMode.JOINTED: t["size_jointed"]}[SizeMode(mode)]
    edges = edge_map(project)
    cut = op.cs_cut
    n = 0
    if ps.cs_parts:
        n += 1
        rows = []

        def edge_cell(p: Part, sides: tuple[str, str]):
            v = _edge_names_len(p, project, sides)
            return Cell(v, "hl") if ps.cs_edge_highlight and v else v          # «Выделять в колонке кромкования»

        def part_row(p: Part) -> list:
            sz = compute_sizes(p, SizeMode(mode), edges, cut.machining_allowance if cut else 0)
            L, W = sz.blank if mode == SizeMode.BLANK else (sz.jointed if mode == SizeMode.JOINTED else sz.detail)
            marks = part_marks(p, project)
            return [p.uid, fmt(L), edge_cell(p, ("top", "bottom")), fmt(W), edge_cell(p, ("left", "right")),
                    total_qty(project, p), p.used_qty, p.left_qty, escape((marks + " " if marks else "") + p.name)]

        if ps.cs_group_by_product:                 # detallar mahsulotlar bo'yicha guruhlanadi (mahsulotlar tartibida)
            by_prod: dict[Optional[str], list[Part]] = {}
            known = {pr.id for pr in project.products}
            for p in op.parts:
                by_prod.setdefault(p.product_id if p.product_id in known else None, []).append(p)
            for pr in [*project.products, None]:
                grp = by_prod.get(pr.id if pr else None)
                if not grp:
                    continue
                title = (f"{t['product']}: {pr.name} × {pr.qty} {t['pcs']}" if pr else t["no_product"])
                rows.append(GroupRow(title))
                rows += [part_row(p) for p in grp]
        else:
            rows = [part_row(p) for p in op.parts]
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
        prices = material_prices(op)
        for i, sh in enumerate(op.sheets, 1):
            if not sh.used_qty:
                continue
            area = sh.length * sh.width / 1e6
            if sh.is_remnant or sh.source_remnant_id or not (mat and mat.cost_by_sheets):
                price = round(prices["m2"] * area, 2)       # ombor qoldig'i yoki m² narxi — maydoni bo'yicha
            else:
                price = mat.price if mat else 0
            summ = price * sh.used_qty
            tot_area += area * sh.used_qty; tot_sum += summ
            rows.append([i, fmt(sh.length), fmt(sh.width), fmt(round(area, 3)), sh.used_qty, fmt(price),
                         fmt(round(area * sh.used_qty, 3)), fmt(round(summ, 2))])
        rows.append(["", "", "", "", "", Markup("<b>{}:</b>").format(t["total"]),
                     Markup("<b>{}</b>").format(fmt(round(tot_area, 3))), Markup("<b>{}</b>").format(fmt(round(tot_sum, 2)))])
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
        legend = _edge_legend(project, op, t)
        landscape = ps.map_orientation == "landscape"          # «Альбомная»: kartalar gorizontal A4 sahifalarga chiqadi
        cards: list[str] = []
        for m in res.maps:
            # sarlavha va karta bitta blokda — sahifa chegarasida sarlavha kartasidan ajralib qolmaydi
            card_head = f"<div class='maphdr'>{escape(op.name)} &nbsp; {escape(map_header(m, res, ps.map_header_fields))}</div>"
            svg = map_svg(m, 840 if landscape else 620, names, project, op, ps.map_part_label, ps.map_edges,
                          ps.map_remnant_number, ps.map_mirror, style=ps, uid=f"s{sec}m{m.index}",
                          show_allowance=ps.map_allowance)
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
                side += _table(["№", t["s_len"], t["s_wid"], t["s_qty"], t["s_marks"]], rows)
                if legend:
                    side += f"<div class='legend'>{legend}</div>"
            if ps.cs_commands:
                side += _table([t["c_code"], t["c_size"], t["c_count"], t["c_ref"]], [[f"{c.code}{c.level}", fmt(c.size), c.count, c.ref]
                                                      for c in m.commands])
            if ps.map_qr:
                qr = _qr_svg(f"MXK:{project.number}:{op.id}:{m.index}")
                if qr:
                    side += f"<div class='qr'>{qr}</div>"
            cards.append(f"<div class='mapcard'>{card_head}<div class='mapwrap'><div>{svg}</div>"
                         f"<div class='side'>{side}</div></div></div>")
        s.append(f"<div class='land'>{''.join(cards)}</div>" if landscape and cards else "".join(cards))
    return "".join(s)


def _edge_legend(project: Project, op: Operation, t: dict) -> str:
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
            lines = max(0, min(3, int(o.el.marker_lines))) if o.el else 1
            out.append(f"<span style='color:{safe_color(o.el.color if o.el else None)}'>■</span> "
                       f"{escape(sym)}-{escape(str(lines))}: {escape(o.name)}")
    marks = {m for p in op.parts for m in part_marks(p, project)}
    if "*" in marks:
        out.append(f"[*] {t['lg_mill']}")
    if "%" in marks:
        out.append(f"[%] {t['lg_drill']}")
    if "=" in marks:
        out.append(f"[=] {t['lg_groove']}")
    return "<br>".join(out)


def _el_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    u = edge_usage(project, op)
    el = op.el
    cur = project.currency
    s = [f"<h2{cls}>{sec}. (EL) {t['el']}: {('(' + escape(op.code) + ') ') if op.code else ''}{escape(op.name)}</h2>"]
    if ps.el_params and el:
        mm, m = t["mm"], t["m"]
        left = [(t["el_width"], f"{fmt(el.width)} {mm}"), (t["el_thick"], f"{fmt(el.thickness)} {mm}"),
                (t["el_joint"], f"{fmt(el.jointing_width)} {mm}"), (t["el_waste"], f"{fmt(el.waste_percent)}%"),
                (t["el_overhang"], f"{fmt(el.overhang)} {mm}"), (t["el_min_glue"], f"{fmt(el.min_glue_length)} {mm}"),
                (t["el_symbol"], el.symbol), (t["el_lines"], el.marker_lines)]
        right = [(t["mat_len"], f"{u['material_m']} {m}"), (t["el_mat_price"], f"{fmt(el.price)} {cur}"),
                 (t["el_mat_cost"], f"{fmt(op.cost_material)} {cur}"), (t["el_op_price"], f"{fmt(el.op_price)} {cur}"),
                 (t["edge_work"], f"{u['work_m']} {m}"), (t["el_op_cost"], f"{fmt(op.cost_operation)} {cur}"),
                 (t["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        rows = "".join(f"<tr><td>{escape(str(a[0]))}</td><td>{escape(str(a[1]))}</td><td style='width:30px'></td>"
                       f"<td>{escape(str(b[0]))}</td><td>{escape(str(b[1]))}</td></tr>"
                       for a, b in zip(left + [("", "")] * (len(right) - len(left)), right + [("", "")] * (len(left) - len(right))))
        s.append(f"<table class='kv'>{rows}</table>")
    if ps.el_parts:
        extra = []
        if ps.el_header_work:
            extra.append(f"{t['edge_work']}: {u['work_m']} {t['m']}")
        if ps.el_header_material:
            extra.append(f"{t['mat_len']}: {u['material_m']} {t['m']}")
        s.append(f"<h3>1. {t['parts']}{(' — ' + escape('; '.join(extra))) if extra else ''}</h3>")
        s.append(_table(["№", t["el_goods"], t["length"], t["el_e_len"], t["width"], t["el_e_wid"], t["qty"],
                         t["el_edge_len"], t["name"]],
                        [[i, escape(r["material"]), fmt(r["length"]), r["edges_len"], fmt(r["width"]), r["edges_wid"],
                          r["qty"], fmt(r["edge_m"]), ("(!) " if r.get("narrow") else "") + r["name"]]
                         for i, r in enumerate(u["rows"], 1)]))
        if u.get("narrow") and el:
            s.append(f"<p class='muted'>(!) {t['el_narrow']}: {fmt(el.min_perp_side)} {t['mm']}</p>")
    return "".join(s)


def _xnc_section(project: Project, op: Operation, t: dict, sec: int, cls: str) -> str:
    from .xnc import xnc_drawing_svg, xnc_holes_table
    x = op.xnc
    if not x:
        return ""
    part = None                     # (detal, uning CS operatsiyasi): avval xnc_part_id bo'yicha, bo'lmasa havola qilgan detal
    for o in project.operations:
        for p in o.parts:
            if op.xnc_part_id and p.id == op.xnc_part_id:
                part = (p, o)
            elif op.id in p.xnc_op_ids and (part is None or part[0].id != op.xnc_part_id):
                part = (p, o)
    s = [f"<h2{cls}>{sec}. (XNC) {t['xnc']}: {escape(op.code)} {escape(op.name)}</h2>"]
    s.append("<div class='mapwrap'>" + xnc_drawing_svg(op, project, 560) + "<div class='side'>")
    rows = xnc_holes_table(op)
    if rows:
        s.append(_table(["№", "X", "Y", "Ø", "DP", "T"], rows))
    prod_name, blank_sz, detail_sz, qty_txt = "", f"{fmt(x.length)} × {fmt(x.width)} × {fmt(x.thickness)}", "", str(x.qty)
    if part:
        pt, cs = part
        prod = next((pr for pr in project.products if pr.id == pt.product_id), None)
        prod_name = prod.name if prod else ""
        sz = compute_sizes(pt, project.size_mode, edge_map(project))
        thick = fmt(x.thickness)
        blank_sz = f"{fmt(sz.blank[0])} × {fmt(sz.blank[1])} × {thick}"
        detail_sz = f"{fmt(sz.detail[0])} × {fmt(sz.detail[1])} × {thick}"
        # «1 × 3 = 3 шт»: detal soni × mahsulot soni = ОК (МК bo'lsa — kroy/ishlovga: ОК − МК)
        qty_txt = f"{pt.qty} × {product_qty(project, pt)} = {total_qty(project, pt)} {t['pcs']}"
        if pt.minus_qty:
            qty_txt += f" − {pt.minus_qty} = {effective_qty(project, pt)} {t['pcs']}"
    stamp = [(t["name"], op.name), (t["product"], prod_name), (t["detail"], part[0].name if part else ""),
             (t["material"], part[1].name if part else ""), (t["blank_size"], blank_sz)]
    if detail_sz:
        stamp.append((t["detail_size"], detail_sz))
    stamp += [(t["code"], op.code), (t["qty"], qty_txt), (t["by_part_size"], t["yes"] if x.by_part_size else t["no"])]
    s.append("<table>" + "".join(f"<tr><th>{escape(str(a))}</th><td>{escape(str(b))}</td></tr>" for a, b in stamp) + "</table>")
    s.append("</div></div>")
    return "".join(s)


def _gr_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    """(GR) bo'limi (K4): parametrlar + hisob (uzunlik, o'tishlar, narx) va pazli detallar jadvali."""
    u = groove_usage(project, op)
    g = op.gr
    cur = project.currency
    s = [f"<h2{cls}>{sec}. (GR) {t['gr']}: {('(' + escape(op.code) + ') ') if op.code else ''}{escape(op.name)}</h2>"]
    if ps.gr_params and g:
        mm, m = t["mm"], t["m"]
        left = [(t["gr_width"], f"{fmt(g.width)} {mm}"), (t["gr_depth"], f"{fmt(g.depth)} {mm}"),
                (t["gr_offset"], f"{fmt(g.offset)} {mm}" + (f" ({t['gr_incl']})" if g.offset_inclusive else "")),
                (t["gr_saw"], f"{fmt(g.saw_thickness)} {mm}")]
        right = [(t["gr_usage"], f"{fmt(u['usage'])} {m}"), (t["gr_passes"], u["passes"]),
                 (t["gr_cut"], f"{fmt(u['cut_length'])} {m}"), (t["gr_price"], f"{fmt(g.price)} {cur}"),
                 (t["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        n = max(len(left), len(right))
        left += [("", "")] * (n - len(left))
        right += [("", "")] * (n - len(right))
        rows = "".join(f"<tr><td>{escape(str(a[0]))}</td><td>{escape(str(a[1]))}</td><td style='width:30px'></td>"
                       f"<td>{escape(str(b[0]))}</td><td>{escape(str(b[1]))}</td></tr>" for a, b in zip(left, right))
        s.append(f"<table class='kv'>{rows}</table>")
    if ps.gr_parts:
        def mark(v: int) -> str:
            return "" if not v else ("+" if v == 1 else f"+ {t['gr_back']}")
        s.append(f"<h3>1. {t['parts']}</h3>")
        s.append(_table(["№", t["el_goods"], t["length"], t["gr_pv"], t["gr_pn"], t["width"], t["gr_pl"], t["gr_pp"],
                         t["qty"], t["gr_len"], t["name"]],
                        [[i, escape(r["material"]), fmt(r["length"]), mark(r["top"]), mark(r["bottom"]), fmt(r["width"]),
                          mark(r["left"]), mark(r["right"]), r["qty"], fmt(r["groove_len_m"]), r["name"]]
                         for i, r in enumerate(u["rows"], 1)]))
    return "".join(s)
