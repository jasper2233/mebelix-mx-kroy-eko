"""Kroy kartasini SVG ga chizish va chop etish uchun HTML hisobot (A4, brauzerda PDF).

Hisobot tuzilishi xodimlarga tanish tartibda (UI_SPEC §8): sarlavha → omborga talabnoma →
har operatsiya (CS: detallar, listlar, qoldiqlar, kartalar; EL: parametrlar + detallar; XNC: chizma).
Ranglar/shriftlar — MebeliX palitrasi.
"""
from __future__ import annotations

import re
from datetime import date, datetime
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
        "project": "Проект", "author": "Автор", "order_id": "ID Проекта", "order_date": "Дата заказа",
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
        "rem_keep": "На склад", "rem_client": "Клиенту", "rem_rule": "Остаток ≥ {p} % листа ({a} м²) — на склад, меньше — клиенту",
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
        "lg_texture": "Текстура",
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
        "rem_keep": "Omborga", "rem_client": "Mijozga", "rem_rule": "Qoldiq ≥ {p} % list ({a} m²) — omborga, kichigi — mijozga",
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
        "lg_texture": "Tekstura",
        "u_sheets": "List", "u_m": "m", "u_pcs": "dona",
        "el_narrow": "kromkaga perpendikulyar tomon chegaradan kichik",
        "gr": "Pazlash", "gr_width": "Paz eni", "gr_depth": "Paz chuqurligi", "gr_offset": "Chetdan masofa",
        "gr_incl": "qo'shilgan holda", "gr_saw": "Arra qalinligi", "gr_price": "1 m paz narxi",
        "gr_usage": "Pazlash uzunligi", "gr_passes": "Arra o'tishlari", "gr_cut": "Kesish uzunligi",
        "gr_pv": "Yu", "gr_pn": "Pa", "gr_pl": "Ch", "gr_pp": "O'", "gr_len": "Paz uz.", "gr_back": "orqa",
        "by_part_size": "Detal o'lchami bo'yicha", "yes": "Ha", "no": "Yo'q",
    },
}


def clip_text(s: str, n: int) -> str:
    """Matnni `n` belgigacha qisqartirish: sig'masa oxiri «…» (kesilgani ko'rinsin)."""
    s = str(s or "")
    return s if len(s) <= n else ("…" if n <= 1 else s[:n - 1].rstrip() + "…")


def fmt(v: float) -> str:
    if v is None:
        return ""
    r = round(float(v), 2)
    # `:g` 6 ta raqamdan keyin «1.13283e+06» beradi (pul/narxlar uchun yaramaydi) — qat'iy ≤ 2 xona
    return str(int(r)) if r == int(r) else f"{r:.2f}".rstrip("0").rstrip(".")


def fmt3(v) -> str:
    """Uzunlik (m) — onlayn hisobotdagidek ≤ 3 xona, ortiqcha nolsiz: 113.299, 50, 21.68."""
    try:
        r = round(float(v or 0), 3)
    except (TypeError, ValueError):
        return str(v)
    return str(int(r)) if r == int(r) else f"{r:.3f}".rstrip("0").rstrip(".")


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
        elif f == "R":              # chiqindi %: (list − detallar − деловой qoldiq) / list
            parts.append(f"R:{fmt(_waste_pct(m.sheet_area_m2, m.parts_area_m2, m.remnant_area_m2))}%/"
                         f"{fmt(_waste_pct(res.material_area_m2, res.parts_area_m2, res.remnant_area_m2))}%")
        elif f == "T":              # torsovka: uzunlik / en bo'yicha (buyruqlar jadvalidagi T1 / T2)
            tr = {c.level: c.size for c in m.commands if c.code == "T"}
            parts.append(f"T:{fmt(tr.get(1, 0))}/{fmt(tr.get(2, 0))}")
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


def part_mill_flag(part: Part, project: Project) -> bool:
    """Stanok fayllaridagi «фрезеровка» bayrog'i (etiketka o'zgaruvchisi `mill`, Felder PC7 / SCM MaestroCut va h.k.):
    detalda frezalash bor va ularning HECH BIRI teshib o'tuvchi kesim (`DP = throughCutDepth`) emas. Korxona namunalari
    (PC7, 3151/3153 …: 9 «true» — faqat oddiy freza, 15 «false» — teshib o'tuvchi + oddiy) bilan tekshirildi (2026-10-24).
    Avval har qanday Mill buyrug'i «true» berardi."""
    xnc = [o for o in project.operations if o.type == OpType.XNC and o.id in part.xnc_op_ids and o.xnc]
    has = through = False
    for o in xnc:
        for c in _flatten(o.xnc.program):
            if not getattr(c, "enabled", True):
                continue
            nm = str(getattr(c.cmd, "value", c.cmd))
            if not nm.startswith("Mill"):
                continue
            has = True
            if nm in ("MillStart", "MillRect", "MillEllipse") and                     str((getattr(c, "params", None) or {}).get("DP", "")).strip() == "throughCutDepth":
                through = True
    return has and not through


def table_marks(part: Part, project: Project) -> str:
    """Karta yonidagi jadval «Мт» ustuni va legenda belgilari: «T» — tekstura (Ткт), keyin ishlov belgilari (`part_marks`:
    % teshik, * frezerlash, = pazlash)."""
    return ("T" if part.grain else "") + part_marks(part, project)


def xnc_program_lines(project: Project, part: Part) -> list[str]:
    """Detallar jadvalida nom ostidagi dastur qatorlari «P<tomon>-<№>: <kod>» (onlayn tizim hisobotidagidek): tomon 1 — lits
    (face_side), 2 — orqa; № — shu tomondagi dastur tartib raqami (loyiha operatsiyalari tartibida); kod bo'sh — nomi.
    ❓ onlayn tizimda faqat «P1-1» (bitta lits dasturi) ko'rilgan; ikki dasturli detal uchun belgilash — taxmin."""
    out: list[str] = []
    n = {1: 0, 2: 0}
    for o in project.operations:
        if o.type == OpType.XNC and o.id in part.xnc_op_ids:
            side = 1 if o.xnc is None or o.xnc.face_side else 2
            n[side] += 1
            out.append(f"P{side}-{n[side]}: {o.code or o.name}")
    return out


def _dim_label(size: float, edges: dict, sides: tuple[str, str]) -> str:
    """Kartadagi o'lcham yozuvi: son + shu o'lcham bo'ylab tomonlarning kromka belgilari («1984 A», «2000 AA»);
    kromkasiz — faqat son."""
    syms = "".join((edges.get(s) or {}).get("symbol", "") for s in sides)
    return f"{fmt(size)} {syms}" if syms else fmt(size)


def _dmy(d) -> str:
    """Sarlavhadagi sana «дд.мм.гггг» (onlayn tizim hisobotidagidek); bo'sh — «—»."""
    if isinstance(d, (date, datetime)):
        return d.strftime("%d.%m.%Y")
    return str(d) if d else "—"


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


def cut_lines(strips, L: float, W: float, kerf2: float = 0.0) -> list[tuple[float, float, float, float]]:
    """Kesish daraxtidan gilyotina kesish chiziqlari (ekrandagi karta bilan bir xil): torsovka — butun list bo'ylab; har ichki
    tugunda har bolaning oxiridan keyin (propil o'rtasida, `kerf2` = propil/2) ota hududi bo'ylab; oxirgi bola ota oxirigacha
    yetmasa — undan keyin ham (chiqindini ajratadi)."""
    out: list[tuple[float, float, float, float]] = []
    if not strips:
        return out

    def g(n, k) -> float:
        try:
            return float(n.get(k) or 0)
        except (TypeError, ValueError, AttributeError):
            return 0.0
    eps = 0.01
    r = strips[0]
    rx, ry, rl, rw = g(r, "x"), g(r, "y"), g(r, "l"), g(r, "w")
    if rx > eps:
        out.append((rx, 0, rx, W))
    if rx + rl < L - eps:
        out.append((rx + rl, 0, rx + rl, W))
    if ry > eps:
        out.append((rx, ry, rx + rl, ry))
    if ry + rw < W - eps:
        out.append((rx, ry + rw, rx + rl, ry + rw))

    def walk(n, depth: int) -> None:
        if depth > 64 or not isinstance(n, dict) or n.get("k") != "C":
            return
        kids = [c for c in (n.get("c") or []) if isinstance(c, dict)]
        x, y, l, w = g(n, "x"), g(n, "y"), g(n, "l"), g(n, "w")
        for i, c in enumerate(kids):
            if n.get("a") == "x":
                end = g(c, "x") + g(c, "l")
                if i < len(kids) - 1 or end < x + l - eps:
                    e = min(end + kerf2, x + l)
                    out.append((e, y, e, y + w))
            else:
                end = g(c, "y") + g(c, "w")
                if i < len(kids) - 1 or end < y + w - eps:
                    e = min(end + kerf2, y + w)
                    out.append((x, e, x + l, e))
            walk(c, depth + 1)
    walk(r, 0)
    return out


MAP_FONT_PX = 10.0          # karta yozuvlari chopdagi balandligi (px, 96 dpi) — hamma kartada bir xil


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
    # yozuvlar har kartada bir xil chop o'lchamida (≈10 px) — kichik qoldiq listi kattalashtirilib chizilganda ham sonlar kattalashmaydi
    fs = MAP_FONT_PX / k if k > 0 else max(16.0, min(L, W) / 42)
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
    expr_cache: dict[str, str] = {}                 # «Печать значения выражения»: detal → qiymat (bir marta hisoblanadi)
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
        if remnant_numbers and o.width > fs * 1.6:
            # to'liq yozuv sig'sa — to'liq, aks holda faqat raqam (qoldiqdan tashqariga chiqmasin)
            full, short = f"Д{int(o.number)} {fmt(o.length)}×{fmt(o.width)}", f"Д{int(o.number)}"
            txt = next((t for t in (full, short) if len(t) * fs * 1.1 * 0.6 + fs * 0.5 <= o.length), "")
            if txt:
                out.append(f'<text x="{fmt(X(o.x + o.length / 2))}" y="{fmt(o.y + o.width / 2)}" font-size="{fs:.1f}" '
                           f'fill="#1f3f66" text-anchor="middle" dominant-baseline="middle">{escape(txt)}</text>')
    # arra kesish chiziqlari (gilyotina): har kesish ota hududining boshidan oxirigacha — chiqindi ustidan ham o'tadi
    kerf2 = max(0.0, fl(op.cs_cut.kerf if op is not None and op.cs_cut else 0) / 2)
    cut_sw = fs / 7
    for x1, y1, x2, y2 in cut_lines(m.strips, L, W, kerf2):
        out.append(f'<line x1="{fmt(X(x1))}" y1="{fmt(y1)}" x2="{fmt(X(x2))}" y2="{fmt(y2)}" stroke="{PART_STROKE}" '
                   f'stroke-width="{cut_sw:.1f}" class="cut"/>')
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
        # kromkalar (joylashgan holatda): chiziqlar va o'lcham yozuvidagi belgilar («2000 AA» — ikkala tomoni A kromkali)
        ed = rotate_edges(part_edges(part, project), p.rotated) if show_edges and part is not None and project is not None else {}
        if ed:
            sw = fs / 6                                   # ingichka kromka chizig'i (ekrandagi karta bilan bir xil uslub)
            ins = sw / 2 + fs / 12
            dash = _edge_dash(st.map_edge_line_style, sw)       # «Стиль линий маркера кромок»
            seg = {
                "top": (p.x + ins, p.y + ins, p.x + p.length - ins, p.y + ins),
                "bottom": (p.x + ins, p.y + p.width - ins, p.x + p.length - ins, p.y + p.width - ins),
                "left": (p.x + ins, p.y + ins, p.x + ins, p.y + p.width - ins),
                "right": (p.x + p.length - ins, p.y + ins, p.x + p.length - ins, p.y + p.width - ins),
            }
            for side, e in (ed.items() if st.map_edge_marker != "symbols" else ()):   # «Символы» — chiziqsiz
                if not e or e.get("lines", 1) <= 0:
                    continue
                x1, y1, x2, y2 = seg[side]
                n_lines = int(e.get("lines", 1))
                lw = sw / (2 * n_lines - 1)               # n ta chiziq va ular orasidagi bo'shliqlar — umumiy qalinlik sw
                for j in range(n_lines):
                    off = (j - (n_lines - 1) / 2) * 2 * lw
                    dxo, dyo = (off, 0.0) if side in ("left", "right") else (0.0, off)
                    out.append(f'<line x1="{fmt(X(x1 + dxo))}" y1="{fmt(y1 + dyo)}" x2="{fmt(X(x2 + dxo))}" '
                               f'y2="{fmt(y2 + dyo)}" stroke="{safe_color(e["color"])}" stroke-width="{lw:.1f}"{dash}/>')
            if st.map_edge_marker in ("symbols", "both"):       # «Печать маркера кромок»: belgi (harf) tomon o'rtasida
                out += _edge_symbol_texts(ed, p, X, fs)
        cx, cy = p.x + p.length / 2, p.y + p.width / 2
        name = (part_names or {}).get(p.part_id) or (part.name if part else "")
        uid_s = str(p.part_uid)
        # ingichka polosa (~1 qator): ekrandagidek bitta qatorda — chapda uzunlik, markazda raqam, o'ngda en (`MapView.tsx`)
        row_mode = fd * 0.7 <= p.width < fd * 1.4
        big = min(fs, p.width * 0.45, p.length / max(1, len(uid_s)) * 0.9)     # detal raqami — o'lchamlar bilan bir xil o'lcham
        if st.map_num_font > 0:                       # detal raqami shrifti qo'lda (pt); detalga sig'maydigan bo'lsa kichraytiriladi
            big = min(max(2.0, st.map_num_font * pt_to_mm), p.width * 0.8, p.length / max(1, len(uid_s)) * 1.1)
        num_weight = ' font-weight="bold"' if st.map_num_bold else ""
        if label in ("number", "number_name") and not row_mode:
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(cy)}" font-size="{big:.1f}"{num_weight} fill="#241400" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(uid_s)}</text>')
        if label in ("name", "number_name") and name and p.width > fs * 3.2 and p.length > fs * 6 and not row_mode:
            dy = big * 0.9 if label == "number_name" else 0
            max_chars = max(3, int(p.length / (fs * 0.62)))
            out.append(f'<text x="{fmt(X(cx))}" y="{fmt(cy + dy)}" font-size="{fs * 0.85:.1f}" fill="#3a2600" '
                       f'text-anchor="middle" dominant-baseline="middle">{escape(clip_text(name, max_chars))}</text>')
        # ishlov belgilari (= pazlash, * frezerlash, % teshik): detalning yuqori-chap burchagida (ixtiyoriy)
        if st.map_part_marks and part is not None and project is not None:
            mk = part_marks(part, project)
            if mk and p.length > fs * 2.5 and p.width > fs * 2.2:
                out.append(f'<text x="{fmt(X(p.x + fs * 0.35))}" y="{fmt(p.y + fs * 1.25)}" font-size="{fs * 1.1:.1f}" '
                           f'font-weight="bold" fill="#241400"{end_anchor}>{escape(mk)}</text>')
        if st.map_part_expr and part is not None and p.width > fs * 3.2 and p.length > fs * 4:
            # «Печать значения выражения»: ifoda (services/expr.py) qiymati detal raqami ostida (xato — bo'sh)
            txt = _part_expr_value(st.map_part_expr, part, project, op, p, expr_cache)
            if txt:
                max_chars = max(3, int(p.length / (fs * 0.55)))
                out.append(f'<text x="{fmt(X(cx))}" y="{fmt(cy + big * 0.9 + fs * 0.9)}" font-size="{fs * 0.8:.1f}" '
                           f'fill="#3a2600" text-anchor="middle" dominant-baseline="middle">{escape(clip_text(txt, max_chars))}</text>')
        if st.map_machining and part is not None and project is not None:
            out += _machining_marks(part, project, p, X, fs)    # «Печать обработки на деталях»
        # o'lchamlar: pastki-chap burchakda uzunlik, o'ng tomonda en (vertikal); ko'zguda — teskari burchaklarda.
        # Yozuv yonida shu o'lcham bo'ylab tomonlarning kromka belgilari (uzunlik — yuqori/past, en — chap/o'ng): «1984 A»
        dim_weight = ' font-weight="bold"' if st.map_dim_bold else ""
        len_lbl, wid_lbl = _dim_label(p.length, ed, ("top", "bottom")), _dim_label(p.width, ed, ("left", "right"))
        if row_mode:
            yy = fmt(p.y + p.width / 2)
            fits = (len(len_lbl) + len(wid_lbl) + len(uid_s)) * fd * 0.6 + fd * 2 <= p.length
            w_anchor = "" if mirror else ' text-anchor="end"'
            l_anchor = ' text-anchor="end"' if mirror else ""
            if fits:
                out.append(f'<text x="{fmt(X(p.x + fd * 0.3))}" y="{yy}" font-size="{fd:.1f}"{dim_weight} fill="#241400"{l_anchor} '
                           f'dominant-baseline="middle">{escape(len_lbl)}</text>')
                out.append(f'<text x="{fmt(X(p.x + p.length - fd * 0.3))}" y="{yy}" font-size="{fd:.1f}"{dim_weight} fill="#241400"'
                           f'{w_anchor} dominant-baseline="middle">{escape(wid_lbl)}</text>')
            if label in ("number", "number_name") and p.length > fd * 0.6 * len(uid_s):
                out.append(f'<text x="{fmt(X(cx))}" y="{yy}" font-size="{fd:.1f}"{num_weight} fill="#241400" text-anchor="middle" '
                           f'dominant-baseline="middle">{escape(uid_s)}</text>')
            continue
        if p.length > max(fd * 3, len(len_lbl) * fd * 0.6 + fd * 0.7) and p.width > fd * 1.4:      # yozuv detaldan chiqmasin
            out.append(f'<text x="{fmt(X(p.x + fd * 0.35))}" y="{fmt(p.y + p.width - fd * 0.35)}" font-size="{fd:.1f}"'
                       f'{dim_weight} fill="#241400"{end_anchor}>{escape(len_lbl)}</text>')
        thin_h = fd * 1.15 < p.width <= fd * 3 and \
            p.length > (len(wid_lbl) + len(len_lbl)) * fd * 0.6 + fd * 1.5
        if thin_h:
            # ingichka uzun detal (masalan 2325×140): en — yuqori-o'ng burchakda gorizontal (uzunlik pastki-chapda qoladi)
            w_anchor = "" if mirror else ' text-anchor="end"'
            out.append(f'<text x="{fmt(X(p.x + p.length - fd * 0.35))}" y="{fmt(p.y + fd * 0.95)}" font-size="{fd:.1f}"'
                       f'{dim_weight} fill="#241400"{w_anchor}>{escape(wid_lbl)}</text>')
        elif st.map_dim_rotate:
            if p.width > fd * 3 and p.length > fd * 1.4:
                tx, ty = X(p.x + p.length - fd * 0.4), p.y + fd * 0.35
                out.append(f'<text x="{fmt(tx)}" y="{fmt(ty)}" font-size="{fd:.1f}"{dim_weight} fill="#241400" '
                           f'transform="rotate(90 {fmt(tx)} {fmt(ty)})">{escape(wid_lbl)}</text>')
        elif p.width > fd * 3 and p.length > fd * (len(wid_lbl) * 0.6 + 1.2):
            # «Разворачивать шрифты» o'chiq: en yozuvi aylantirilmaydi — yuqori-o'ng burchakda gorizontal
            w_anchor = "" if mirror else ' text-anchor="end"'          # ko'zguda yuqori-chapda, matn o'ngga o'sadi
            out.append(f'<text x="{fmt(X(p.x + p.length - fd * 0.35))}" y="{fmt(p.y + fd * 1.15)}" font-size="{fd:.1f}"'
                       f'{dim_weight} fill="#241400"{w_anchor}>{escape(wid_lbl)}</text>')
    out.append("</svg>")
    return _mirror_v("".join(out), W) if st.map_mirror_v else "".join(out)


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


def _page_css(ps: PrintSettings, project: Optional[Project] = None, t: Optional[dict] = None) -> str:
    """«Поля страницы»: chap/o'ng/yuqori/past chegaralar (mm); «Зеркальные поля» — chap sahifada chap/o'ng almashadi;
    «Позиция колонтитула» — sahifa chegara bloki (chopda, Chrome 131+ / PDF): «Проект ID… nom — стр. N»."""
    def mm(v) -> str:
        try:
            return f"{max(0.0, min(50.0, float(v))):g}mm"
        except (TypeError, ValueError):
            return "10mm"
    top, right, bottom, left = mm(ps.page_margin_top), mm(ps.page_margin_right), mm(ps.page_margin_bottom), mm(ps.page_margin_left)
    margin = f"{top} {right} {bottom} {left}"
    # `land` — nomlangan sahifa: «Альбомная» kartalar (`.land` bloki) gorizontal A4 ga chiqadi
    css = f"@page {{ size: A4; margin: {margin}; }} @page land {{ size: A4 landscape; margin: {margin}; }}"
    if ps.page_mirror_margins:
        css += f" @page :left {{ margin: {top} {left} {bottom} {right}; }}"
    if ps.page_footer_pos in ("bottom", "top") and project is not None:
        # kolontitul (xodimlarga tanish ko'rinish): chapda «Проект: nom», o'ngda «Страница N»
        tt = t or T["ru"]
        pos = ps.page_footer_pos
        left_lbl = _css_str(f"{tt['project']}: {project.name}")
        right_lbl = _css_str(f"{tt['page_word']} ")
        font = "font: bold 9px Arial, Helvetica, sans-serif; color: #222;"
        css += (f" @page {{ @{pos}-left {{ content: {left_lbl}; {font} }} "
                f"@{pos}-right {{ content: {right_lbl} counter(page); {font} }} }}")
    return css


CSS = """
@page { size: A4; margin: 10mm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #1b1f24; margin: 0; }
h1 { font-size: 18px; margin: 0 0 6px; }
h2 { font-size: 15px; margin: 14px 0 6px; }
h3 { font-size: 13px; margin: 10px 0 4px; }
table { border-collapse: collapse; margin: 4px 0 10px; width: 100%; }
td, th { border: 1px solid #333; padding: 2px 5px; vertical-align: top; overflow-wrap: anywhere; }
.kv, .side table { width: auto; }
th { background: #e9ecef; font-weight: bold; }
td.num { text-align: right; }
.pb { page-break-before: always; }
.land { page: land; }
.grp td { background: #e9ecef; font-weight: bold; }
td.hl { background: #fff1c2; font-weight: bold; }
td.b { font-weight: bold; }
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
    from ..i18n import lang_tag, tr_table
    t = tr_table(T, lang)                             # uz-Cyrl — o'zbekcha jadvalning kirill nusxasi
    cur = project.currency
    s = [f"<!DOCTYPE html><html lang='{lang_tag()}'><head><meta charset='utf-8'>{CSP_META}<title>{escape(project.name)}</title>"
         f"<style>{CSS}{_page_css(ps, project, t)}</style></head><body>"]
    total_m = sum(o.cost_material for o in project.operations)
    total_o = sum(o.cost_operation for o in project.operations)
    sec = 0
    if ps.header:
        s.append(f"<div class='brand'>MebeliX Kroy</div><h1>{t['project']}: {escape(project.name)}</h1>")
        rows = [(t["author"], project.owner or "—"), (t["order_id"], project.number),
                (t["order_date"], _dmy(project.order_date)), (t["ready_date"], _dmy(project.ready_date)),
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
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"]], _warehouse_rows(project, ps, t)))
    if ps.materials_list:
        sec += 1
        s.append(f"<h2>{sec}. {t['materials']}</h2>")
        rows = []
        for i, r in enumerate(_materials_rows(project, ps), 1):
            rows.append([i, r["type"], r["code"], r["name"], t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"]),
                         fmt(r.get("price", 0)),
                         fmt(r.get("sum", 0))])
        s.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"], t["price"], t["sum"]], rows))
    if ps.products_list and project.products and (len(project.products) > 1 or ps.products_list_single):
        sec += 1
        s.append(f"<h2>{sec}. {t['products']}</h2>")
        # narxlar 1 dona uchun; «Всего» = × soni
        rows = [[i, p.code, p.name, p.qty, fmt(p.cost_material), fmt(p.cost_operation),
                 fmt(round(p.cost_material + p.cost_operation, 2)),
                 fmt(round((p.cost_material + p.cost_operation) * p.qty, 2))] for i, p in enumerate(project.products, 1)]
        s.append(_table(["№", t["code_short"], t["name"], t["qty"], t["cost_mat_s"], t["cost_op_s"], t["cost_unit"],
                         t["cost_all"]], rows))
        s.append(_products_block(project, ps, t))          # «Изделия» oynasi: har mahsulot bloki
    if ps.operations_list and project.operations and (len(project.operations) > 1 or ps.operations_list_single):
        sec += 1                                             # «Печать списка операций»
        s.append(f"<h2>{sec}. {t['operations']}</h2>")
        s.append(_operations_table(project, t))
    if ps.xnc_stats:
        xs_html = _xnc_stats_block(project, ps, t)          # «Печатать статистику по XNC операциям»: ustunlar + guruhlash
        if xs_html:
            sec += 1
            s.append(f"<h2>{sec}. {t['xnc']}</h2>{xs_html}")
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
                s.append(_xnc_section(project, op, t, sec, cls, ps))
            elif op.type == OpType.SP and (ps.sp_params or ps.sp_parts):
                from .sp_render import sp_section        # (SP) Обработка поверхности: parametrlar + hisob + detallar jadvali
                s.append(sp_section(project, op, ps, t, sec, cls))
            elif op.type == OpType.O and (ps.o_params or ps.o_materials):
                from .o_render import o_section        # (O) Комплектация: parametrlar bloki + materiallar jadvali
                s.append(o_section(project, op, ps, t, sec, cls))
    s.append("</body></html>")
    return "".join(s)


def _warehouse_rows(project: Project, ps: PrintSettings, t: dict) -> list[list]:
    """«Требование на склад» qatorlari (onlayn tizim hisobotidagidek): «№» — operatsiyaning operatsiyalar jadvalidagi raqami
    (XNC lar ham sanaladi: ikkinchi mahsulot operatsiyalari 29, 30 …), ketma-ket 1..n emas. O operatsiyasi — bitta qator
    (№ | O | egasi mahsulot | operatsiya nomi) va ostida N.1, N.2 … material qatorlari (Код, Наименование, Ед.И, Кол);
    CS/CL/CN ning ombor qoldig'i qatorlari (bizning qo'shimcha) ham N.k. `op_id` siz qatorlar (bo'lmasligi kerak) — oxirida."""
    from .o_ops import owner_product
    idx = {o.id: i for i, o in enumerate(project.operations, 1)}
    by_op: dict[Optional[str], list[dict]] = {}
    for r in warehouse_request(project):
        by_op.setdefault(r.get("op_id") if r.get("op_id") in idx else None, []).append(r)

    def title(r: dict) -> str:
        name = r["name"]
        if r["type"] in ("CS", "CN") and ps.warehouse_cut_work and not r.get("remnant"):
            name += f" ({t['sheets_n']}: {r['qty']} {t['pcs']}  {t['cut_len']}: {fmt3(r.get('cut_m', 0))} {t['m']})"
        elif r["type"] == "CL" and ps.warehouse_cut_work and not r.get("remnant"):     # (CL) polosalar va kesim uzunligi
            name += f" ({t['cl_strips_n']}: {fmt(r.get('strips', 0))} {t['pcs']}  {t['cut_len']}: {fmt3(r.get('cut_m', 0))} {t['m']})"
        elif r["type"] == "EL" and ps.warehouse_edge_work:
            name += f" ({t['edge_work']}: {fmt3(r.get('work_m', 0))} {t['m']})"
        return name

    rows: list[list] = []
    for op in project.operations:
        rs = by_op.get(op.id)
        if not rs:
            continue
        n = idx[op.id]
        if op.type == OpType.O:
            pr = owner_product(project, op.o) if op.o else None
            # O sarlavha qatori qalin (onlayn tizim hisobotidagidek), ostidagi material qatorlari — oddiy
            rows.append([Cell(x, "b") for x in (n, "O", pr.name if pr is not None else t["project"], op.name, "", "")])
            for k, r in enumerate(rs, 1):
                rows.append([f"{n}.{k}", "", r["code"], r.get("material", r["name"]), r["unit"], fmt(r["qty"])])
            continue
        sub = 0
        for r in rs:
            sub += 1 if r.get("remnant") else 0
            rows.append([f"{n}.{sub}" if r.get("remnant") else n, r["type"], r["code"], title(r),
                         t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"])])
    for k, r in enumerate(by_op.get(None, []), len(project.operations) + 1):
        rows.append([k, r["type"], r["code"], title(r), t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"])])
    return rows


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
    if ps.cs_warehouse:                            # «Печать требования на склад» (shu operatsiya qatorlari)
        n += 1
        s.append(f"<h3>{n}. {t['warehouse']}</h3>")
        s.append(_op_warehouse_table(project, op, ps, t))
    if ps.cs_stats and op.result:                  # «Печать статистики»
        n += 1
        s.append(f"<h3>{n}. {t['stats']}</h3>")
        s.append(_cut_stats_table(op.result, t))
    if ps.cs_parts:
        n += 1
        rows = []

        def edge_cell(p: Part, sides: tuple[str, ...]):
            # «Печать символов кромкования»: nom o'rniga EL belgisi; «Выделять в колонке кромкования»: rangli katak
            v = _edge_symbols(p, project, sides) if ps.cs_edge_symbols else _edge_names_len(p, project, sides)
            return Cell(v, "hl") if ps.cs_edge_highlight and v else v

        def part_row(p: Part) -> list:
            sz = compute_sizes(p, SizeMode(mode), edges, cut.machining_allowance if cut else 0)
            L, W = sz.blank if mode == SizeMode.BLANK else (sz.jointed if mode == SizeMode.JOINTED else sz.detail)
            # nom ostida bog'langan XNC dasturlari «P1-1: <kod>» (onlayn tizim hisobotidagidek); ishlov belgilari nomga yozilmaydi
            name = Markup("<br>").join([escape(p.name), *(escape(x) for x in xnc_program_lines(project, p))])
            return [p.uid, fmt(L), edge_cell(p, ("top", "bottom")), fmt(W), edge_cell(p, ("left", "right")),
                    total_qty(project, p), p.used_qty, p.left_qty, name]

        def row_for(p: Part) -> list:              # «Форма печати деталей»: har tomon alohida — ОВ ОН / ОЛ ОП ustunlari
            r = part_row(p)
            if ps.cs_parts_form == "sides":
                r = [r[0], r[1], edge_cell(p, ("top",)), edge_cell(p, ("bottom",)), r[3], edge_cell(p, ("left",)),
                     edge_cell(p, ("right",)), *r[5:]]
            return r

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
                rows += [row_for(p) for p in grp]
        else:
            rows = [row_for(p) for p in op.parts]
        # «№» — jadvaldagi tartib raqami 1, 2, 3 … (onlayn tizim hisobotidagidek; detal ID si kartada qoladi)
        k = 0
        for r in rows:
            if isinstance(r, list):
                k += 1
                r[0] = k
        s.append(f"<h3>{n}. {t['parts']} ({mode_title})</h3>")
        s.append(_table(_cs_part_heads(ps, t), rows))
        if ps.cs_edge_symbols:                     # «… и вывести легенду»
            s.append(_edge_symbol_legend(project, op, t))
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
        from . import remnant_rules
        cls = remnant_rules.classify(op)
        s.append(f"<h3>{n}. {t['remnants']}</h3>")
        if cls is not None:          # material foiz qoidasi: ≥ foiz — omborga (korxona olib qoladi), kichigi — mijozga
            cnt = Counter((pc["length"], pc["width"], pc["percent"], pc["keep"]) for pc in cls["pieces"]
                          for _k in range(pc["copies"]) if pc["keep"] or pc["kind"] == "remnant")
            rows = [[i, fmt(l), fmt(w), fmt(round(l * w / 1e6, 3)), c, fmt(pct), t["rem_keep"] if k else t["rem_client"]]
                    for i, ((l, w, pct, k), c) in enumerate(sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1]), 1)]
            s.append(f"<p>{t['rem_rule'].format(p=fmt(cls['percent']), a=fmt(cls['sheet_m2']))}</p>")
            s.append(_table(["№", t["length"], t["width"], t["area"], t["qty"], "%", ""], rows))
        else:
            cnt = Counter((o.length, o.width, o.business) for o in res.remnants)
            rows = [[i, fmt(l), fmt(w), fmt(round(l * w / 1e6, 3)), c, t["remnant"] if b else "—"]
                    for i, ((l, w, b), c) in enumerate(sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1]), 1)]
            s.append(_table(["№", t["length"], t["width"], t["area"], t["qty"], ""], rows))
    if res and ps.cs_maps:
        names = {p.id: p.name for p in op.parts}
        parts_by_id = {p.id: p for p in op.parts}
        legend = _edge_legend(project, op, t)
        landscape = ps.map_orientation == "landscape"          # «Альбомная»: kartalar gorizontal A4 sahifalarga chiqadi
        cards: list[str] = []
        for m in res.maps:
            # sarlavha va karta bitta blokda — sahifa chegarasida sarlavha kartasidan ajralib qolmaydi
            # sarlavha ikki qatorda: material nomi, ostida «№:3/5 S:2750/1830 C:1/5 Cp:8/47 LT:… F:…» (onlayn tizim hisobotidagidek)
            card_head = f"<div class='maphdr'>{escape(op.name)}<br>{escape(map_header(m, res, ps.map_header_fields))}</div>"
            svg = map_svg(m, 840 if landscape else 620, names, project, op, ps.map_part_label, ps.map_edges,
                          ps.map_remnant_number, _map_mirror(m, ps), style=ps, uid=f"s{sec}m{m.index}",
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
                    rows.append([p.uid, fmt(p.length), fmt(p.width), c, table_marks(p, project)])
                side += _table(["№", t["s_len"], t["s_wid"], t["s_qty"], t["s_marks"]], rows)
                if legend:
                    side += f"<div class='legend'>{legend}</div>"
            if ps.cs_commands:
                side += _table([t["c_code"], t["c_size"], t["c_count"], t["c_ref"]], [[f"{c.code}{c.level}", fmt(c.size), "" if c.code == "T" else c.count, c.ref]
                                                      for c in m.commands])          # T (torsovka) — «К» bo'sh
            if ps.map_qr:
                qr = _qr_svg(f"MXK:{project.number}:{op.id}:{m.index}")
                if qr:
                    side += f"<div class='qr'>{qr}</div>"
            cards.append(f"<div class='mapcard'>{card_head}<div class='mapwrap'><div>{svg}</div>"
                         f"<div class='side'>{side}</div></div></div>")
        s.append(f"<div class='land'>{''.join(cards)}</div>" if landscape and cards else "".join(cards))
    return "".join(s)


def _edge_legend(project: Project, op: Operation, t: dict) -> str:
    """Karta legendasi (onlayn tizim hisobotidagi tartib): avval kartada uchragan belgilar «[T] Текстура», «[%] Сверление»,
    «[*] Фрезерование», «[=] Пазование», keyin kromkalar «A: <kromka nomi>» (rang kvadrati bilan)."""
    out = []
    marks = {m for p in op.parts for m in table_marks(p, project)}
    for mk, key in (("T", "lg_texture"), ("%", "lg_drill"), ("*", "lg_mill"), ("=", "lg_groove")):
        if mk in marks:
            out.append(f"[{mk}] {t[key]}")
    used = set()
    for p in op.parts:
        for sd in ("top", "bottom", "left", "right"):
            ref = getattr(p, f"edge_{sd}")
            if ref.op_id:
                used.add(ref.op_id)
    for o in project.operations:
        if o.type == OpType.EL and o.id in used:
            sym = (o.el.symbol if o.el else "?") or "?"
            out.append(f"<span style='color:{safe_color(o.el.color if o.el else None)}'>■</span> "
                       f"{escape(sym)}: {escape(o.name)}")
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
                 (t["edge_work"], f"{fmt3(u['work_m'])} {m}"), (t["el_op_cost"], f"{fmt(op.cost_operation)} {cur}"),
                 (t["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        rows = "".join(f"<tr><td>{escape(str(a[0]))}</td><td>{escape(str(a[1]))}</td><td style='width:30px'></td>"
                       f"<td>{escape(str(b[0]))}</td><td>{escape(str(b[1]))}</td></tr>"
                       for a, b in zip(left + [("", "")] * (len(right) - len(left)), right + [("", "")] * (len(left) - len(right))))
        s.append(f"<table class='kv'>{rows}</table>")
    if ps.el_parts:
        extra = []
        if ps.el_header_work:
            extra.append(f"{t['edge_work']}: {fmt3(u['work_m'])} {t['m']}")
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


def _xnc_section(project: Project, op: Operation, t: dict, sec: int, cls: str,
                 ps: Optional[PrintSettings] = None, dims: bool = False, width_px: int = 560) -> str:
    from .xnc import xnc_drawing_svg, xnc_holes_table
    x = op.xnc
    if not x:
        return ""
    if ps is not None:
        op = _xnc_print_op(op, ps)          # (XNC) «Чертеж → Зеркало для обратной стороны» (faqat chop nusxasi)
        x = op.xnc
    part = None                     # (detal, uning CS operatsiyasi): avval xnc_part_id bo'yicha, bo'lmasa havola qilgan detal
    for o in project.operations:
        for p in o.parts:
            if op.xnc_part_id and p.id == op.xnc_part_id:
                part = (p, o)
            elif op.id in p.xnc_op_ids and (part is None or part[0].id != op.xnc_part_id):
                part = (p, o)
    s = [f"<h2{cls}>{sec}. (XNC) {t['xnc']}: {escape(op.code)} {escape(op.name)}</h2>"]
    s.append("<div class='mapwrap'>" + xnc_drawing_svg(op, project, width_px, dims=dims) + "<div class='side'>")
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


# ───────────────────────── §11 (2026-10-15): chop sozlamalari oynalari → hisobot ─────────────────────────
T["ru"].update(operations="Операции", stats="Статистика", st_sheets="Листов", st_parts="Деталей", st_fill="Заполнение",
               st_cut="Длина реза, м", st_cuts="Резов", st_area_m="Площадь листов, м²", st_area_p="Площадь деталей, м²",
               st_area_w="Деловые остатки, м²", st_qty="Количество материала, м²", e_top="ОВ", e_bottom="ОН", e_left="ОЛ",
               e_right="ОП", side="Ст", side_face="Лиц", side_back="Обр", x_drills="Кол. св-ний", x_drill_price="Цена св-ний",
               x_drill_cost="Ст-ть св-ний", x_mill_len="Длина фр-ния", x_mill_price="Цена фр-ния", x_mill_cost="Ст-ть фр-ния",
               x_saw_len="Длина п-ния", x_saw_price="Цена п-ния", x_saw_cost="Ст-ть п-ния", x_extra="Доп. ст-ть",
               x_op_cost="Ст-ть оп-и", len_s="Д-на", wid_s="Ш-на", op_col="Операция", page="стр.", page_word="Страница", legend="Обозначения кромок")
T["uz"].update(operations="Operatsiyalar", stats="Statistika", st_sheets="Listlar", st_parts="Detallar", st_fill="To'ldirish",
               st_cut="Kesish uzunligi, m", st_cuts="Kesimlar", st_area_m="Listlar maydoni, m²", st_area_p="Detallar maydoni, m²",
               st_area_w="Deloviy qoldiqlar, m²", st_qty="Material miqdori, m²", e_top="Yu", e_bottom="Pa", e_left="Ch",
               e_right="O'", side="Tm", side_face="Yuz", side_back="Orqa", x_drills="Teshiklar", x_drill_price="Teshik narxi",
               x_drill_cost="Teshiklar qiymati", x_mill_len="Freza uz.", x_mill_price="Freza narxi", x_mill_cost="Freza qiymati",
               x_saw_len="Arra uz.", x_saw_price="Arra narxi", x_saw_cost="Arra qiymati", x_extra="Qo'sh. qiymat",
               x_op_cost="Operatsiya qiymati", len_s="Uz.", wid_s="En", op_col="Operatsiya", page="sah.", page_word="Sahifa", legend="Kromka belgilari")


def _fl(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return f if f == f and abs(f) != float("inf") else 0.0


def _css_str(s: str) -> str:
    """CSS satr literali (`content: "…"`): `\\`, `"`, `<`, `>` qochiriladi — loyiha nomi <style> dan chiqib keta olmaydi."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("<", "\\3c ").replace(">", "\\3e ").replace("\n", " ")
    return f'"{s}"'


def _waste_pct(sheet: float, parts: float, bus: float) -> float:
    return (100.0 * (sheet - parts - bus) / sheet) if sheet > 0 else 0.0


def _op_type(o: Operation) -> str:
    return o.type.value if hasattr(o.type, "value") else str(o.type)


def _materials_rows(project: Project, ps: PrintSettings) -> list[dict]:
    """«Печать списка материалов» qatorlari; «Группировать материалы по коду» — bir xil kodli (kod bo'sh — nom bo'yicha)
    qatorlar bitta qatorga yig'iladi (miqdor va summa qo'shiladi; birlik — birinchisi)."""
    rows = warehouse_request(project)
    if not ps.materials_group_by_code:
        return rows
    out: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r.get("type", ""), (r.get("code") or r.get("name") or "").strip().lower())
        if key in out:
            g = out[key]
            g["qty"] = round(_fl(g.get("qty")) + _fl(r.get("qty")), 3)
            g["sum"] = round(_fl(g.get("sum")) + _fl(r.get("sum")), 2)
        else:
            out[key] = dict(r)
    return list(out.values())


def _operations_table(project: Project, t: dict) -> str:
    """«Печать списка операций»: № | Тип | Код/Изделие | Наименование | Ст. м-ла | Ст. оп-и | Стоимость."""
    rows = [[i, _op_type(o), o.code, o.name, fmt(o.cost_material), fmt(o.cost_operation),
             fmt(round(o.cost_material + o.cost_operation, 2))] for i, o in enumerate(project.operations, 1)]
    return _table(["№", t["type"], t["code"], t["name"], t["cost_mat_s"], t["cost_op_s"], t["cost"]], rows)


def _products_block(project: Project, ps: PrintSettings, t: dict) -> str:
    """«Изделия» oynasi: ro'yxat ostida har mahsulot uchun sarlavha / operatsiyalar / materiallar / detallar."""
    if not (ps.prod_header or ps.prod_operations or ps.prod_materials or ps.prod_parts):
        return ""
    cut_types = (OpType.CS, OpType.CL, OpType.CN)
    wh = warehouse_request(project) if ps.prod_materials else []
    out = []
    for pr in project.products:
        ops = [o for o in project.operations if any(p.product_id == pr.id for p in o.parts)]
        if ps.prod_header:
            code = f"{pr.code} " if pr.code else ""
            out.append(f"<h3>{t['product']}: {escape(code)}{escape(pr.name)} × {pr.qty} {t['pcs']}</h3>")
        if ps.prod_operations and ops:
            out.append(_table(["№", t["type"], t["code_short"], t["name"], t["cost_mat_s"], t["cost_op_s"]],
                              [[i, _op_type(o), o.code, o.name, fmt(o.cost_material), fmt(o.cost_operation)]
                               for i, o in enumerate(ops, 1)]))
        if ps.prod_materials:
            ids = {o.id for o in ops}
            rows = [[i, r["type"], r["code"], r["name"], t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"])]
                    for i, r in enumerate((r for r in wh if r.get("op_id") in ids), 1)]
            if rows:
                out.append(_table(["№", t["type"], t["code"], t["name"], t["unit"], t["qty"]], rows))
        if ps.prod_parts:
            rows: list[list] = []
            for o in ops:
                if o.type not in cut_types:
                    continue
                for p in o.parts:
                    if p.product_id == pr.id:
                        rows.append([len(rows) + 1, o.name, fmt(p.length), fmt(p.width), p.qty, p.name])
            if rows:
                out.append(_table(["№", t["op_col"], t["length"], t["width"], t["qty"], t["name"]], rows))
    return "".join(out)


def _xnc_owner(project: Project, op: Operation):
    """XNC dasturining detali va uning kroy operatsiyasi: avval `xnc_part_id`, bo'lmasa havola qilgan birinchi detal."""
    found = None
    for o in project.operations:
        for p in o.parts:
            if op.xnc_part_id and p.id == op.xnc_part_id:
                return p, o
            if op.id in p.xnc_op_ids and found is None:
                found = (p, o)
    return found


def _xnc_stats_block(project: Project, ps: PrintSettings, t: dict) -> str:
    """«Печатать статистику по XNC операциям»: XNC «Статистика» oynasidagi ustunlar (Вкл, tartib, Ш-на) va «Группировка»
    (material = detal kroy operatsiyasi / mahsulot). Qiymatlar: teshiklar, freza va arra uzunligi (m), narx va qiymat × soni."""
    from ..models import XNC_STAT_COLS, PrintCol
    from .xnc import xnc_stats
    xs = [o for o in project.operations if o.type == OpType.XNC and o.xnc]
    if not xs:
        return ""
    heads = {"n": "№", "side": t["side"], "code": t["code_short"], "name": t["name"], "length": t["len_s"],
             "width": t["wid_s"], "qty": t["qty"], "drills": t["x_drills"], "drill_price": t["x_drill_price"],
             "drill_cost": t["x_drill_cost"], "mill_len": t["x_mill_len"], "mill_price": t["x_mill_price"],
             "mill_cost": t["x_mill_cost"], "saw_len": t["x_saw_len"], "saw_price": t["x_saw_price"],
             "saw_cost": t["x_saw_cost"], "extra_cost": t["x_extra"], "op_cost": t["x_op_cost"]}
    cols = [c for c in ps.xnc_stat_cols if c.on and c.key in heads] or \
        [PrintCol(key=k, width=w) for k, on, w in XNC_STAT_COLS if on]
    groups: dict[str, list[list]] = {}
    for i, o in enumerate(xs, 1):
        x = o.xnc
        st = xnc_stats(x)
        q = x.qty
        v = {"n": i, "side": t["side_face"] if x.face_side else t["side_back"], "code": o.code, "name": o.name,
             "length": fmt(x.length), "width": fmt(x.width), "qty": q, "drills": st["drills"],
             "drill_price": fmt(x.drill_price), "drill_cost": fmt(round(st["drills"] * x.drill_price * q, 2)),
             "mill_len": fmt(st["mill_m"]), "mill_price": fmt(x.mill_price_m),
             "mill_cost": fmt(round(st["mill_m"] * x.mill_price_m * q, 2)), "saw_len": fmt(st["saw_m"]),
             "saw_price": fmt(x.saw_price_m), "saw_cost": fmt(round(st["saw_m"] * x.saw_price_m * q, 2)),
             "extra_cost": fmt(x.extra_cost), "op_cost": fmt(o.cost_operation)}
        key = ""
        if ps.xnc_stats_group != "none":
            own = _xnc_owner(project, o)
            if ps.xnc_stats_group == "material":
                key = f"{t['material']}: {own[1].name}" if own else "—"
            else:
                prod = next((pr for pr in project.products if own and pr.id == own[0].product_id), None)
                key = f"{t['product']}: {prod.name}" if prod else t["no_product"]
        groups.setdefault(key, []).append([v[c.key] for c in cols])
    rows: list = []
    for key, grp in groups.items():
        if key:
            rows.append(GroupRow(key))
        rows += grp
    head = [Markup("<span style='display:inline-block;min-width:{}em'>{}</span>").format(round(c.width * 0.55, 1), heads[c.key])
            for c in cols]
    return _table(head, rows)


def _op_warehouse_table(project: Project, op: Operation, ps: PrintSettings, t: dict) -> str:
    """(CS)/(CL) «Печать требования на склад»: faqat shu operatsiyaning talabnoma qatorlari."""
    rows: list[list] = []
    for r in warehouse_request(project):
        if r.get("op_id") != op.id:
            continue
        name = r["name"]
        if ps.warehouse_cut_work and not r.get("remnant") and r.get("cut_m") is not None:
            name += f" ({t['cut_len']}: {r.get('cut_m', 0)} {t['m']})"
        rows.append([len(rows) + 1, name, t.get("u_" + r.get("unit_code", ""), r["unit"]), fmt(r["qty"])])
    return _table(["№", t["name"], t["unit"], t["qty"]], rows)


def _cut_stats_table(res: CuttingResult, t: dict) -> str:
    """(CS) «Печать статистики»: kroy natijasining umumiy ko'rsatkichlari."""
    rows = [(t["st_sheets"], res.total_sheets), (t["st_parts"], res.total_parts),
            (t["st_fill"], f"{fmt(res.total_fill_percent)}%"), (t["st_cut"], fmt(res.total_cut_length_m)),
            (t["st_cuts"], res.total_cuts), (t["st_area_m"], fmt(round(res.material_area_m2, 3))),
            (t["st_area_p"], fmt(round(res.parts_area_m2, 3))), (t["st_area_w"], fmt(round(res.remnant_area_m2, 3))),
            (t["st_qty"], fmt(round(res.material_qty_m2, 3)))]
    return "<table class='kv'>" + "".join(f"<tr><td>{escape(str(a))}</td><td><b>{escape(str(b))}</b></td></tr>"
                                         for a, b in rows) + "</table>"


def _cs_part_heads(ps: PrintSettings, t: dict) -> list[str]:
    """Detallar jadvali sarlavhasi: «Форма печати деталей» — o'lcham bo'yicha birlashtirilgan kromka ustunlari yoki har tomon."""
    if ps.cs_parts_form == "sides":
        return ["№", t["length"], t["e_top"], t["e_bottom"], t["width"], t["e_left"], t["e_right"], t["qty"], t["used"],
                t["left"], t["name"]]
    return ["№", t["length"], t["edge_len"], t["width"], t["edge_wid"], t["qty"], t["used"], t["left"], t["name"]]


def _edge_symbols(part: Part, project: Project, sides: tuple[str, ...]) -> str:
    """Kromka katagi belgilar bilan («Печать символов кромкования»): har tomon uchun EL «Символ» (bo'sh — «?»)."""
    ops = {o.id: o for o in project.operations if o.type == OpType.EL}
    syms = []
    for sd in sides:
        ref = getattr(part, f"edge_{sd}")
        if ref.op_id and ref.op_id in ops:
            o = ops[ref.op_id]
            syms.append((o.el.symbol if o.el else "") or "?")
    return " ".join(syms)


def _edge_symbol_legend(project: Project, op: Operation, t: dict) -> str:
    """«… и вывести легенду»: detallar jadvali ostida belgi — kromka operatsiyasi (qalinligi)."""
    used = {getattr(p, f"edge_{sd}").op_id for p in op.parts for sd in ("top", "bottom", "left", "right")}
    items = []
    for o in project.operations:
        if o.type == OpType.EL and o.id in used:
            sym = (o.el.symbol if o.el else "") or "?"
            thick = f" ({fmt(o.el.thickness)} {t['mm']})" if o.el and o.el.thickness else ""
            items.append(f"<b>{escape(sym)}</b> — {escape(o.name)}{escape(thick)}")
    return f"<div class='legend'>{t['legend']}: " + "; ".join(items) + "</div>" if items else ""


def _map_mirror(m: CutMap, ps: PrintSettings) -> bool:
    """«Зеркало → Горизонтально»: Да / Нет, yoki faqat birinchi kesimlari tik («cuts_v»: daraxt ildizi uzunlik bo'ylab
    bo'lingan — kesim chiziqlari en bo'ylab) / yotiq («cuts_h») kartalar uchun."""
    if ps.map_mirror_h in ("yes", "no"):
        return bool(ps.map_mirror)
    root = m.strips[0] if m.strips else None
    axis = root.get("a") if isinstance(root, dict) else None
    if axis not in ("x", "y"):
        return False
    return (axis == "x") == (ps.map_mirror_h == "cuts_v")


_TEXT_RE = re.compile(r'<text x="([^"]+)" y="([^"]+)"([^>]*)>')
_ROT_RE = re.compile(r' transform="rotate\(90 ([^ ]+) ([^)]+)\)"')
_FS_RE = re.compile(r'font-size="([^"]+)"')


def _mirror_v(svg: str, W: float) -> str:
    """«Зеркало → Вертикально»: karta vertikal akslanadi (<g> transform), matnlar esa o'qiladigan qoladi — har <text> ga
    teskari aks: oddiy yozuv o'z o'rnining ko'zgusiga ko'chadi (bazaviy chiziqli matn balandligicha pastga), 90° burilgan
    en yozuvi −90° bo'lib pastdan yuqoriga o'qiladi."""
    def fix(mt):
        x, y, rest = mt.group(1), mt.group(2), mt.group(3)
        rot = _ROT_RE.search(rest)
        if rot:
            tx, ty = rot.group(1), _fl(rot.group(2))
            rest = _ROT_RE.sub("", rest)
            final = f"translate(0 {fmt(W - 2 * ty)}) rotate(-90 {tx} {fmt(ty)})"
        else:
            fs_m = _FS_RE.search(rest)
            h = 0.0 if "dominant-baseline" in rest else (_fl(fs_m.group(1)) * 0.72 if fs_m else 0.0)
            final = f"translate(0 {fmt(W - 2 * _fl(y) + h)})"
        return f'<text x="{x}" y="{y}"{rest} transform="translate(0 {fmt(W)}) scale(1 -1) {final}">'
    body = _TEXT_RE.sub(fix, svg)
    i = body.index(">") + 1
    tail = "</svg>"
    if not body.endswith(tail):
        return body
    return body[:i] + f'<g transform="translate(0 {fmt(W)}) scale(1 -1)">' + body[i:-len(tail)] + "</g></svg>"


def _edge_dash(style: str, sw: float) -> str:
    """«Стиль линий маркера кромок»: chiziq namunasi — yaxlit / shtrix / nuqta (dasharray)."""
    if style == "dashed":
        return f' stroke-dasharray="{sw * 3:.1f} {sw * 1.5:.1f}"'
    if style == "dotted":
        return f' stroke-dasharray="{sw * 0.8:.1f} {sw * 1.2:.1f}"'
    return ""


def _edge_symbol_texts(ed: dict, p, X, fs: float) -> list[str]:
    """«Печать маркера кромок: Символы»: EL belgisi (harf) tomon o'rtasida, detal ichida, kromka rangida."""
    size = fs * 0.9
    if p.length < size * 2.5 or p.width < size * 2.5:
        return []
    pos = {"top": (p.x + p.length / 2, p.y + size * 0.75), "bottom": (p.x + p.length / 2, p.y + p.width - size * 0.65),
           "left": (p.x + size * 0.7, p.y + p.width / 2), "right": (p.x + p.length - size * 0.7, p.y + p.width / 2)}
    out = []
    for side, e in ed.items():
        if not e:
            continue
        x, y = pos[side]
        out.append(f'<text x="{fmt(X(x))}" y="{fmt(y)}" font-size="{size:.1f}" font-weight="bold" '
                   f'fill="{safe_color(e["color"])}" text-anchor="middle" dominant-baseline="middle">'
                   f'{escape(str(e.get("symbol") or "?"))}</text>')
    return out


def _part_expr_value(expr: str, part: Part, project: Optional[Project], op: Optional[Operation], p, cache: dict) -> str:
    """«Печать значения выражения»: ifoda (services/expr.py) detal o'zgaruvchilari bilan; xato — bo'sh matn."""
    if part.id in cache:
        return cache[part.id]
    from . import expr as ex
    prod = next((pr for pr in (project.products if project else []) if pr.id == part.product_id), None)
    env = {"name": part.name, "code": part.code, "description": part.description, "uid": part.uid, "length": part.length,
           "width": part.width, "qty": part.qty, "total_qty": total_qty(project, part) if project else part.qty,
           "grain": bool(part.grain), "material": op.name if op else "", "material_code": op.code if op else "",
           "thickness": (op.cs_material.thickness if op is not None and op.cs_material else 0),
           "product_name": prod.name if prod else "", "product_code": prod.code if prod else "",
           "rotated": bool(p.rotated)}
    try:
        v = ex.evaluate(expr, env)
        txt = "" if v is None else ex.to_text(v)
    except Exception:  # noqa: BLE001 — ifoda xatosi kartani buzmaydi
        txt = ""
    cache[part.id] = txt
    return txt


def _machining_marks(part: Part, project: Project, p, X, fs: float) -> list[str]:
    """«Печать обработки на деталях»: detalga bog'langan XNC dasturlarining yuza teshiklari (aylana) va pazlari (punktir)
    karta detalida — dastur koordinatalari detalning chap-yuqori burchagiga keltirilib, joylashuv (burilish) bo'yicha."""
    from .xnc import evaluate as xnc_eval, program_vars
    out: list[str] = []
    for o in project.operations:
        if o.type != OpType.XNC or o.id not in part.xnc_op_ids or not o.xnc:
            continue
        x = o.xnc
        try:
            ops = xnc_eval(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values)
        except Exception:  # noqa: BLE001 — dastur xatosi kartani buzmaydi
            continue
        dx, dy = max(_fl(x.length), 1.0), max(_fl(x.width), 1.0)
        fx = (x.origin in ("RT", "RB")) != bool(x.mirror_x)
        fy = (x.origin in ("LB", "RB")) != bool(x.mirror_y)

        def to_sheet(px: float, py: float) -> tuple[float, float]:
            qx = dx - px if fx else px
            qy = dy - py if fy else py
            if p.rotated:                  # uzunlik o'qi list bo'ylab tik: chap tomon → yuqori, yuqori tomon → o'ng
                return p.x + p.length - qy * (p.length / dy), p.y + qx * (p.width / dx)
            return p.x + qx * (p.length / dx), p.y + qy * (p.width / dy)

        for o2 in ops:
            k = o2.get("kind", "")
            if k == "DrillFront" and o2.get("inside", True):
                sx, sy = to_sheet(_fl(o2.get("X")), _fl(o2.get("Y")))
                r = max(_fl(o2.get("D")) / 2, fs * 0.12)
                out.append(f'<circle cx="{fmt(X(sx))}" cy="{fmt(sy)}" r="{fmt(round(r, 2))}" fill="#fff" stroke="#333" '
                           f'stroke-width="{fs / 20:.1f}"/>')
            elif k == "Groove":
                (x1, y1), (x2, y2) = to_sheet(_fl(o2.get("X1")), _fl(o2.get("Y1"))), to_sheet(_fl(o2.get("X2")), _fl(o2.get("Y2")))
                out.append(f'<line x1="{fmt(X(x1))}" y1="{fmt(y1)}" x2="{fmt(X(x2))}" y2="{fmt(y2)}" stroke="#333" '
                           f'stroke-width="{fs / 10:.1f}" stroke-dasharray="{fs * 0.3:.1f} {fs * 0.2:.1f}"/>')
    return out


def _xnc_print_op(op: Operation, ps: PrintSettings) -> Operation:
    """(XNC) «Чертеж → Зеркало для обратной стороны»: orqa tomon (lits emas) dasturi chizmasi «Горизонтально» — X bo'yicha,
    «Вертикально» — Y bo'yicha akslanadi, «Нет» — dasturdagidek. Faqat chop nusxasi o'zgaradi, dastur emas."""
    x = op.xnc
    if x is None or x.face_side or ps.xnc_back_mirror == "none":
        return op
    upd = {"mirror_x": not x.mirror_x} if ps.xnc_back_mirror == "horizontal" else {"mirror_y": not x.mirror_y}
    return op.model_copy(update={"xnc": x.model_copy(update=upd)})



T["ru"].update(sh_face="Лицевая сторона", sh_back="Обратная сторона", sh_edging="Кромкооблицовка", sh_qty="Количество",
               sh_code="Код", sh_by_size="По размеру", sh_by_part="детали", sh_by_blank="заготовки")
T["uz"].update(sh_face="Yuz tomoni", sh_back="Orqa tomoni", sh_edging="Kromkalash", sh_qty="Soni",
               sh_code="Kod", sh_by_size="O'lcham bo'yicha", sh_by_part="detal", sh_by_blank="zagotovka")

SHEET_CSS = """
html, body { margin: 0; height: 100%; font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #000; background: #fff; }
.sh { position: absolute; inset: 3px; border: 1px solid #000; display: flex; flex-direction: column; }
.sh-draw { flex: 1; min-height: 0; position: relative; display: flex; align-items: center; justify-content: center; padding: 4px 8px; }
.sh-draw > svg { width: 100%; height: 100%; }
.sh-holes { position: absolute; top: 4px; right: 4px; border-collapse: collapse; font-size: 9px; background: #fff; }
.sh-holes th, .sh-holes td { border: 1px solid #000; padding: 0 5px; text-align: center; line-height: 12px; }
.sh-face { display: flex; align-items: flex-end; gap: 6px; padding: 0 0 2px 4px; font-size: 11px; }
.sh-bot { display: flex; align-items: stretch; border-top: 1px solid #000; }
.sh-edges { flex: 1; min-width: 0; padding: 1px 4px; font-size: 9.5px; line-height: 12px; }
.sh-edges b { display: block; }
.sh-stamp { border-collapse: collapse; font-size: 9.5px; flex: none; }
.sh-stamp th, .sh-stamp td { border: 1px solid #000; padding: 0 3px; text-align: left; line-height: 13px; white-space: nowrap; }
.sh-stamp th { font-weight: 700; }
.sh-stamp td.v { min-width: 150px; }
"""


def xnc_sheet_html(project: Project, op: Operation, lang: str = "ru") -> str:
    """Detal «XNC Редактор» oynasining «Чертеж» varag'i — onlayn tizim varag'i tartibida: ramkali oq varaq, o'rtada chizma
    (oq detal, yon polosalar, kromka harflari, raqamlangan teshiklar, umumiy va ordinata o'lchamlari — `xnc_drawing_svg(sheet=True)`),
    o'ng yuqorida teshiklar jadvali (diametr / chuqurlik guruhlari bo'yicha), pastda chapda «Лицевая сторона» belgisi va
    «Кромкооблицовка» ro'yxati, o'ng pastda shtamp (Наименование, Код, Изделие, Деталь, Материал, Рм. Заготовки, Количество,
    Рм. Детали, По размеру)."""
    from ..i18n import LANG
    from .xnc import evaluate, program_vars, xnc_drawing_svg
    lang = lang if lang in T else "ru"
    t = T[lang]
    x = op.xnc
    if not x:
        return "<!doctype html><html><body></body></html>"
    token = LANG.set(lang)
    try:
        svg = xnc_drawing_svg(op, project, 1100, height_px=520, sheet=True)
    finally:
        LANG.reset(token)
    # teshiklar jadvali: chizmadagi raqamlar tartibida, (Ø, DP) guruhlari — guruh sarlavhasi «Ø=35  DP=13»
    groups: dict[tuple[float, float], list[tuple[int, str, str]]] = {}
    n = 0
    side_mark = {"DrillLeft": " ←", "DrillRight": " →", "DrillTop": " ↑", "DrillBottom": " ↓"}
    for o in evaluate(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values):
        if o["kind"].startswith("Drill") and o.get("inside", True):
            n += 1
            kd = o["kind"]
            xv = x.length if kd == "DrillRight" else 0.0 if kd == "DrillLeft" else o["X"]
            yv = x.width if kd == "DrillBottom" else 0.0 if kd == "DrillTop" else o["Y"]
            groups.setdefault((round(o["D"], 3), round(o["DP"], 3)), []).append((n, f"{xv:g}{side_mark.get(kd, '')}", f"{yv:g}"))
    holes = ""
    if groups:
        rows = ["<tr><th>№</th><th>X</th><th>Y</th><th>T</th></tr>"]
        for (d, dp), items in groups.items():
            rows.append(f"<tr><th></th><th>Ø={d:g}</th><th>DP={dp:g}</th><th></th></tr>")
            rows += [f"<tr><td>{i}</td><td>{escape(a)}</td><td>{escape(b_)}</td><td></td></tr>" for i, a, b_ in items]
        holes = f"<table class='sh-holes' data-testid='sh-holes'>{''.join(rows)}</table>"
    # shtamp
    owner = _xnc_owner(project, op)
    thick = fmt(x.thickness)
    blank_sz, detail_sz, qty_txt = f"{fmt(x.length)} x {fmt(x.width)} x {thick}", "", f"{x.qty} {t['pcs']}"
    prod_txt, part_txt, mat_txt, name_txt = "", "", "", op.name     # «Наименование» — ishlov nomi (onlayn varaqdagidek)
    edges_txt: list[str] = []
    if owner:
        pt, cs = owner
        prods = {pr.id: (i, pr) for i, pr in enumerate(project.products, 1)}
        if pt.product_id in prods:
            i, pr = prods[pt.product_id]
            prod_txt = f"№{i} {pr.name} ({pr.qty}{t['pcs']})"
        # «Деталь №2(2) tom»: № в изделии (mahsulot detallari ID tartibida) va ID, so'ng detal nomi
        same = sorted((q for o in project.operations for q in o.parts if q.product_id == pt.product_id), key=lambda q: q.uid)
        idx = next((i for i, q in enumerate(same, 1) if q.id == pt.id), 0)
        part_txt = (f"№{idx}({pt.uid})" if idx else f"№{pt.uid}") + (f" {pt.name}" if pt.name else "")
        mat_txt = cs.name
        sz = compute_sizes(pt, project.size_mode, edge_map(project))
        blank_sz = f"{fmt(sz.blank[0])} x {fmt(sz.blank[1])} x {thick}"
        detail_sz = f"{fmt(sz.detail[0])} x {fmt(sz.detail[1])} x {thick}"
        qty_txt = f"{pt.qty} x {product_qty(project, pt)} = {total_qty(project, pt)} {t['pcs']}"
        seen = set()
        for e in part_edges(pt, project).values():
            key = (e["symbol"], e["name"])
            if key not in seen:
                seen.add(key)
                edges_txt.append(f"({escape(e['symbol'])}) {escape(e['name'])}")
    by = t["sh_by_part"] if x.by_part_size else t["sh_by_blank"]
    E = escape
    stamp = (f"<table class='sh-stamp' data-testid='sh-stamp'>"
             f"<tr><th>{t['name']}</th><td class='v'>{E(name_txt)}</td><th>{t['sh_code']}</th><td>{E(op.code)}</td></tr>"
             f"<tr><th>{t['product']}</th><td class='v' colspan='3'>{E(prod_txt)}</td></tr>"
             f"<tr><th>{t['detail']}</th><td class='v' colspan='3'>{E(part_txt)}</td></tr>"
             f"<tr><th>{t['material']}</th><td class='v' colspan='3'>{E(mat_txt)}</td></tr>"
             f"<tr><th>{t['blank_size']}</th><td class='v'>{E(blank_sz)}</td><th>{t['sh_qty']}</th><td>{E(qty_txt)}</td></tr>"
             f"<tr><th>{t['detail_size']}</th><td class='v'><b>{E(detail_sz or blank_sz)}</b></td><th>{t['sh_by_size']}</th>"
             f"<td>{E(by)}</td></tr></table>")
    face = t["sh_face"] if x.face_side else t["sh_back"]
    face_svg = ('<svg width="34" height="16" viewBox="0 0 34 16"><line x1="17" y1="1" x2="17" y2="11" stroke="#000"/>'
                '<path d="M 14 8 L 17 11 L 20 8" fill="none" stroke="#000"/><rect x="1" y="12" width="32" height="3" fill="#fff" stroke="#000"/></svg>')
    return ("<!doctype html><html><head><meta charset='utf-8'><style>" + SHEET_CSS + "</style></head><body>"
            f"<div class='sh' data-testid='xnc-sheet'><div class='sh-draw'>{svg}{holes}</div>"
            f"<div class='sh-face' data-testid='sh-face'>{face_svg}<span>{E(face)}</span></div>"
            f"<div class='sh-bot'><div class='sh-edges' data-testid='sh-edges'><b>{t['sh_edging']}</b>{'<br>'.join(edges_txt)}</div>"
            f"{stamp}</div></div></body></html>")