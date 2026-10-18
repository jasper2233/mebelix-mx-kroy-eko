"""(SP) Обработка поверхности — hisobot bo'limi (render.py dan chaqiriladi): parametrlar + hisob bloki va sirt ishlovi bor
detallar jadvali. Hisob — `calc.surface_usage`."""
from __future__ import annotations

from markupsafe import escape

from ..i18n import tr_table
from ..models import Operation, PrintSettings, Project
from .calc import surface_usage

TS = {
    "ru": {"title": "Обработка поверхности", "calc_mat": "Учитывать материал", "waste": "Процент отхода материала",
           "rest": "Длина остатка по краям", "size_mode": "Режим размеров", "mode_saw": "пильный размер",
           "mode_blank": "заготовка", "price": "Цена материала (м²)", "op_price": "Цена операции (м²)",
           "area": "Площадь обработки", "mat": "Расход материала", "mat_cost": "Стоимость материала",
           "op_cost": "Стоимость операции", "cost": "Стоимость", "yes": "Да", "no": "Нет", "mm": "мм", "m2": "м²",
           "parts": "Детали", "material": "Материал", "length": "Длина", "width": "Ширина", "front": "Лиц.",
           "back": "Обр.", "qty": "Кол", "name": "Наименование", "total": "Всего"},
    "uz": {"title": "Sirt ishlovi", "calc_mat": "Materialni hisobga olish", "waste": "Material chiqindi foizi",
           "rest": "Chetlardagi qoldiq uzunligi", "size_mode": "O'lcham rejimi", "mode_saw": "pilniy o'lcham",
           "mode_blank": "zagotovka", "price": "Material narxi (m²)", "op_price": "Operatsiya narxi (m²)",
           "area": "Ishlov maydoni", "mat": "Material sarfi", "mat_cost": "Material narxi",
           "op_cost": "Operatsiya narxi", "cost": "Jami narx", "yes": "Ha", "no": "Yo'q", "mm": "mm", "m2": "m²",
           "parts": "Detallar", "material": "Material", "length": "Uzunlik", "width": "En", "front": "Old",
           "back": "Orqa", "qty": "Soni", "name": "Nomi", "total": "Jami"},
}


def fmt(v, nd: int = 2) -> str:
    """Son matni: butun bo'lsa nuqtasiz, aks holda ≤ nd xona (render.fmt `:g` — 6 ta raqamdan keyin «1.13283e+06» beradi, pul uchun yaramaydi)."""
    r = round(float(v or 0), nd)
    return str(int(r)) if r == int(r) else f"{r:.{nd}f}".rstrip("0").rstrip(".")


def sp_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    """(SP) bo'limi HTML. `t` — render.T[lang] (umumiy matnlar); SP ga xos matnlar — TS."""
    from .render import _table                        # render ni aylanma import qilmaslik uchun — chaqiruv paytida
    L = tr_table(TS)
    cur = project.currency
    u = surface_usage(project, op)
    p = op.sp
    code = f"({escape(op.code)}) " if op.code else ""
    s = [f"<h2{cls}>{sec}. (SP) {L['title']}: {code}{escape(op.name)}</h2>"]
    if ps.sp_params and p:
        left = [(L["calc_mat"], L["yes"] if p.count_material else L["no"]), (L["waste"], f"{fmt(p.waste_percent)}%"),
                (L["rest"], f"{fmt(p.rest_side)} {L['mm']}"),
                (L["size_mode"], L["mode_saw"] if p.size_mode == -1 else L["mode_blank"])]
        right = [(L["area"], f"{fmt(u['area_m2'])} {L['m2']}"), (L["mat"], f"{fmt(u['material_m2'])} {L['m2']}"),
                 (L["price"], f"{fmt(p.price)} {cur}"), (L["mat_cost"], f"{fmt(op.cost_material)} {cur}"),
                 (L["op_price"], f"{fmt(p.op_price)} {cur}"), (L["op_cost"], f"{fmt(op.cost_operation)} {cur}"),
                 (L["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        n = max(len(left), len(right))
        left += [("", "")] * (n - len(left))
        right += [("", "")] * (n - len(right))
        rows = "".join(f"<tr><td>{escape(a[0])}</td><td>{escape(a[1])}</td><td style='width:30px'></td>"
                       f"<td>{escape(b[0])}</td><td>{escape(b[1])}</td></tr>" for a, b in zip(left, right))
        s.append(f"<table class='kv'>{rows}</table>")
        if op.description.strip():
            s.append(f"<p style='white-space:pre-wrap'>{escape(op.description)}</p>")
    if ps.sp_parts:
        s.append(f"<h3>1. {L['parts']}</h3>")
        rows = [[i, escape(r["material"]), fmt(r["length"]), fmt(r["width"]), "+" if r["front"] else "", "+" if r["back"] else "",
                 r["qty"], fmt(r["area_m2"]), escape(r["name"])] for i, r in enumerate(u["rows"], 1)]
        rows.append(["", "", "", "", "", "", "", fmt(u["area_m2"]), f"{L['total']}: {L['m2']}"])
        s.append(_table(["№", L["material"], L["length"], L["width"], L["front"], L["back"], L["qty"], L["m2"], L["name"]], rows))
    return "".join(s)
