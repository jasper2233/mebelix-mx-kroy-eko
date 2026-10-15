"""(O) Комплектация — hisobot bo'limi (render.py dan chaqiriladi): parametrlar bloki, materiallar jadvali, izoh.

Jadval ustunlari: № Код Наименование Ед.И Кол Цена Стоимость. Qator «Стоимость» = Кол × Цена (1 mahsulot / loyiha uchun,
ko'paytirgichsiz); egasi mahsulot bo'lsa pastda «× soni» bilan jami ko'rsatiladi (operatsiya narxi shunga teng).
"""
from __future__ import annotations

from markupsafe import escape

from ..i18n import LANG
from ..models import Operation, PrintSettings, Project
from .o_ops import material_sum, o_multiplier, owner_product

TO = {
    "ru": {"title": "Комплектация", "owner": "Владелец", "project": "Проект", "cost_mat": "Стоимость материала",
           "cost_op": "Стоимость операции", "cost": "Стоимость", "descr": "Описание", "pcs": "шт",
           "total": "Всего", "items": "позиций", "code": "Код", "name": "Наименование", "unit": "Ед.И", "qty": "Кол",
           "price": "Цена", "sum": "Стоимость"},
    "uz": {"title": "Komplektatsiya", "owner": "Egasi", "project": "Loyiha", "cost_mat": "Material narxi",
           "cost_op": "Ish narxi", "cost": "Jami narx", "descr": "Izoh", "pcs": "dona",
           "total": "Jami", "items": "pozitsiya", "code": "Kod", "name": "Nomi", "unit": "O'lch.", "qty": "Soni",
           "price": "Narx", "sum": "Summa"},
}


def o_section(project: Project, op: Operation, ps: PrintSettings, t: dict, sec: int, cls: str) -> str:
    """(O) bo'limi HTML. `t` — render.T[lang] (umumiy matnlar); O ga xos matnlar — TO."""
    from .render import _table, fmt                   # render ni aylanma import qilmaslik uchun — chaqiruv paytida
    L = TO["uz" if LANG.get() == "uz" else "ru"]
    cur = project.currency
    p = op.o
    code = f"({escape(op.code)}) " if op.code else ""
    s = [f"<h2{cls}>{sec}. (O) {L['title']}: {code}{escape(op.name)}</h2>"]
    if p is None:
        return "".join(s)
    mult = o_multiplier(project, p)
    base = material_sum(p)
    pr = owner_product(project, p)
    if ps.o_params:
        owner = L["project"] if pr is None else \
            f"№{project.products.index(pr) + 1} {pr.name} ({fmt(pr.qty)} {L['pcs']})"
        mat_txt = f"{fmt(op.cost_material)} {cur}" + (f" ({fmt(base)} × {fmt(mult)})" if pr is not None else "")
        op_txt = f"{fmt(op.cost_operation)} {cur}" + (f" ({fmt(p.work_cost)} × {fmt(mult)})" if pr is not None else "")
        rows = [(L["owner"], owner), (L["cost_mat"], mat_txt), (L["cost_op"], op_txt),
                (L["cost"], f"{fmt(op.cost_material + op.cost_operation)} {cur}")]
        s.append("<table class='kv'>" + "".join(f"<tr><td><b>{escape(a)}</b></td><td>{escape(b)}</td></tr>"
                                                for a, b in rows) + "</table>")
        if op.description.strip():
            s.append(f"<p style='white-space:pre-wrap'><b>{L['descr']}:</b> {escape(op.description)}</p>")
    if ps.o_materials:
        rows = [[i, m.code, m.name, m.unit, fmt(m.qty), fmt(m.price), fmt(round(m.qty * m.price, 2))]
                for i, m in enumerate(p.materials, 1)]
        rows.append(["", "", f"{L['total']}: {len(p.materials)} {L['items']}", "", "", "", fmt(round(base, 2))])
        s.append(_table(["№", L["code"], L["name"], L["unit"], L["qty"], L["price"], L["sum"]], rows))
    return "".join(s)
