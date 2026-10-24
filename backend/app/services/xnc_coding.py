"""«Кодирование» (XNC Параметры, onlayn tizimdagidek; 2026-10-23 jonli ko'rildi): loyihadagi XNC operatsiyalari kodi qayta
yaratiladi — `xnc_coding` ifodasi (standart: sana-vaqt + loyiha nomi CRC-16 + detal ID; `crc16` onlayn natija bilan bir xil),
so'ng ixtiyoriy XNC tartib raqami (1, 2, … — loyihadagi XNC operatsiyalari tartibida) va ishlov tomoni raqami (1 — lits, 2 — orqa).
Detalga bog'lanmagan XNC ning kodi o'zgarmaydi (detal ID siz kod ma'nosiz). Natija baribir noyob bo'ladi: takror — «-2», «-3».
Hisob faqat `services/expr.py` da (ikkinchi dvigatel yo'q).
"""
from __future__ import annotations

import datetime as _dt
from typing import Callable

from ..models import OpType, Project
from . import expr


def _part_of(project: Project, oid: str):
    for o in project.operations:
        for pt in o.parts:
            if oid in pt.xnc_op_ids:
                return o, pt
    return None, None


def codes(project: Project, cfg: dict, clock: Callable[[], _dt.datetime] | None = None) -> list[tuple[str, str | None, str]]:
    """[(op_id, yangi kod yoki None — o'zgarmaydi, xato matni)] — XNC operatsiyalari tartibida. Barcha kodlar bir lahzada
    (bitta `now`) hisoblanadi, shuning uchun bir loyihaning kodlari bir xil boshlanadi."""
    now = (clock or _dt.datetime.now)()
    out: list[tuple[str, str | None, str]] = []
    n = 0
    for op in project.operations:
        if op.type != OpType.XNC:
            continue
        n += 1
        cs, pt = _part_of(project, op.id)
        if pt is None:
            out.append((op.id, None, ""))
            continue
        env = {"project.name": project.name, "project.id": project.number, "part.id": pt.uid, "part.name": pt.name,
               "op.name": op.name, "op.code": op.code, "material.name": cs.name if cs else ""}
        try:
            v = expr.to_text(expr.evaluate(cfg["expr"], env, clock=lambda: now))
        except ValueError as e:
            out.append((op.id, None, str(e)))
            continue
        if cfg.get("add_op_number", True):
            v += str(n)
        if cfg.get("add_side_number", False):
            v += "1" if (op.xnc is None or op.xnc.face_side) else "2"
        out.append((op.id, v, ""))
    return out


def apply(project: Project, cfg: dict) -> dict:
    """Kodlarni loyihaga yozadi (joyida). Qaytaradi: {changed, skipped, errors}."""
    res = codes(project, cfg)
    by_id = {o.id: o for o in project.operations}
    used: set[str] = set()
    changed = skipped = 0
    errors: list[str] = []
    for oid, code, err in res:
        op = by_id[oid]
        if err:
            errors.append(f"{op.name or op.code}: {err}")
        if code is None:
            skipped += 1
            if op.code:
                used.add(op.code)
            continue
        c, k = code, 2
        while c in used:
            c, k = f"{code}-{k}", k + 1
        used.add(c)
        if op.code != c:
            op.code = c
            changed += 1
    return dict(changed=changed, skipped=skipped, errors=errors)
