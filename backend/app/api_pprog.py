"""Mahsulot «Программа» (parametrik mahsulot, W12) API: Par parametrlari / o'zgaruvchilar / xabarlar holati va umumiy amal
«Пересчитать параметричность». Dasturni o'zgartirish — umumiy `PATCH /projects/{pid}/products/{prid}` (`{program, par_values}`);
natija (`prog_vars`, `prog_messages`) har saqlashda `calc.recalc_project` da yangilanadi."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import store
from .i18n import _
from .services import product_program

router = APIRouter(tags=["mahsulot dasturi"])


@router.get("/projects/{pid}/products/{prid}/program-state")
def program_state(pid: str, prid: str):
    """Dasturni hozirgi `par_values` bilan hisoblab beradi: params (Par: nom, yorliq, tur, standart / joriy qiymat, ko'rinish,
    faqat o'qish), vars (o'zgaruvchilar), messages ([{level: info | warning | error, text, path}]), errors (Err soni),
    warnings, problems (ifoda xatolari). Xabarlar so'rov tilida."""
    p = store.load(pid)
    pr = next((x for x in p.products if x.id == prid), None)
    if pr is None:
        raise HTTPException(404, _("product_not_found"))
    return product_program.state(p, pr)


@router.post("/projects/{pid}/actions/recalc-parametric")
def recalc_parametric(pid: str):
    """Общие действия → «Пересчитать параметричность» (ma'nosi hujjatda yo'q ❓ — taxmin): hamma mahsulot dasturlari va XNC
    operatsiyalari ifodalari qayta hisoblanadi, mahsulot o'zgaruvchilari (`product.<nom>`) XNC `part_vars` ga yangilanadi.
    Bitta tarix qadami (ma'lumot o'zgarmagan bo'lsa tarixga bo'sh versiya yozilmaydi). Javob: {project, report: {products, xnc, totals}}."""
    with store.editing(pid, skip_unchanged=True) as p:
        report = product_program.recalc_parametric(p)
    return {"project": p, "report": report}
