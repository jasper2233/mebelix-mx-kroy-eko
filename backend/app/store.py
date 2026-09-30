"""Loyihalarni saqlash yordamchilari: yuklash, saqlash (tarix bilan), undo/redo, qulf, raqamlash."""
from __future__ import annotations

import copy
import json
import threading
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select

from .db import ProjectHistoryRow, ProjectRow, SessionLocal
from .i18n import _
from .models import Operation, Part, Project
from .services import calc

HISTORY_LIMIT = 100          # har loyiha uchun saqlanadigan versiyalar soni

_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


def _lock(pid: str) -> threading.RLock:
    with _locks_guard:
        lk = _locks.get(pid)
        if lk is None:
            lk = _locks[pid] = threading.RLock()
        return lk


def load(pid: str) -> Project:
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        if not row:
            raise HTTPException(404, _("project_not_found"))
        return validate_data(row.data)


def validate_data(data: dict) -> Project:
    """Bazadagi loyiha → model. Eski/buzilgan yozuvda son o'rnida null (masalan, avval cheksiz qiymat saqlangan)
    bo'lsa — 0 bilan tuzatib ochiladi (loyiha «ochilmaydigan» bo'lib qolmasin)."""
    try:
        return Project.model_validate(data)
    except ValidationError as e:
        data = copy.deepcopy(data)
        for _attempt in range(20):
            fixed = False
            for err in e.errors():
                if err.get("input", 0) is None and err.get("type") in _NUM_ERRORS:
                    fixed |= _set_path(data, err["loc"], 0)
            if not fixed:
                raise
            try:
                return Project.model_validate(data)
            except ValidationError as e2:
                e = e2
        raise


_NUM_ERRORS = {"float_type", "int_type", "float_parsing", "int_parsing", "finite_number"}


def _set_path(data, loc, value) -> bool:
    cur = data
    for k in loc[:-1]:
        try:
            cur = cur[k]
        except (KeyError, IndexError, TypeError):
            return False
    try:
        cur[loc[-1]] = value
        return True
    except (KeyError, IndexError, TypeError):
        return False


def _dump(p: Project) -> tuple[dict, bool]:
    """Model → JSON-ma'lumot. Hisoblashda paydo bo'lgan cheksiz/NaN qiymatlar 0 ga almashtiriladi."""
    bad = [False]

    def fix(_c: str) -> float:
        bad[0] = True
        return 0.0
    return json.loads(p.model_dump_json(), parse_constant=fix), bad[0]


def next_number() -> int:
    with SessionLocal() as s:
        return (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1


def save(p: Project, history: bool = True, cursor: Optional[int] = None) -> Project:
    """Hisob-kitobni yangilab saqlaydi; history=True — yangi versiya (redo zanjiri kesiladi);
    cursor — undo/redo: tarix ko'rsatkichi shu versiyaga o'rnatiladi (bitta tranzaksiyada)."""
    calc.recalc_project(p)
    data, bad = _dump(p)
    if bad:                                    # xotiradagi obyekt ham tozalanadi (javob JSON bo'lib chiqsin)
        clean = Project.model_validate(data)
        for k in Project.model_fields:
            setattr(p, k, getattr(clean, k))
    cost = sum(o.cost_material + o.cost_operation for o in p.operations)
    with _lock(p.id), SessionLocal() as s:
        row = s.get(ProjectRow, p.id)
        if not row:
            row = ProjectRow(id=p.id, history_cursor=0)
            s.add(row)
        row.number = p.number; row.folder_id = p.folder_id; row.name = p.name
        row.owner = p.owner; row.status = int(p.status); row.order_date = str(p.order_date)
        row.cost = round(cost, 2); row.mes_order_ref = p.mes_order_ref; row.customer = p.customer
        row.data = data
        s.flush()                      # loyiha qatori tarixdan oldin yozilsin (PostgreSQL FK tekshiruvi)
        if cursor is not None:
            row.history_cursor = cursor
        elif history:
            cur = row.history_cursor or 0
            s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == p.id,
                                              ProjectHistoryRow.version > cur).delete()
            v = cur + 1
            s.add(ProjectHistoryRow(project_id=p.id, version=v, data=data))
            row.history_cursor = v
            s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == p.id,
                                              ProjectHistoryRow.version <= v - HISTORY_LIMIT).delete()
        s.commit()
    return p


_new_lock = threading.Lock()


def save_new(p: Project, attempts: int = 20) -> Project:
    """Yangi loyiha: raqam (Заказ ID) ajratish jarayon ichida ketma-ket; boshqa jarayon (ikkinchi server)
    bilan to'qnashsa — keyingi raqam bilan qayta urinish."""
    from sqlalchemy.exc import IntegrityError
    with _new_lock:
        for i in range(attempts):
            if i or not p.number:
                p.number = next_number()
            try:
                return save(p)
            except IntegrityError:
                if i == attempts - 1:
                    raise
                time.sleep(0.005 * (i + 1))
    return p


@contextmanager
def editing(pid: str, history: bool = True) -> Iterator[Project]:
    """Loyihani qulf ostida o'zgartirish: `with editing(pid) as p: ...` — chiqishda saqlanadi (xato bo'lsa yo'q)."""
    with _lock(pid):
        p = load(pid)
        yield p
        save(p, history)


def history_info(pid: str) -> dict:
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        if not row:
            raise HTTPException(404, _("project_not_found"))
        lo, hi = s.execute(select(func.min(ProjectHistoryRow.version), func.max(ProjectHistoryRow.version))
                           .where(ProjectHistoryRow.project_id == pid)).one()
        cur = row.history_cursor or 0
        return dict(version=cur, first=lo or 0, last=hi or 0, can_undo=bool(lo) and cur > lo,
                    can_redo=bool(hi) and cur < hi)


def _result_sig(res) -> Optional[str]:
    """Natija «imzosi» — ombor/sex maydonlarisiz (bir xil kroyni tanish uchun)."""
    if res is None:
        return None
    d = res.model_dump(mode="json", exclude={"remnants_saved", "saved_remnant_ids", "saved_remnant_qty",
                                             "consumed_remnants", "elapsed_s"})
    for m in d.get("maps", []):
        m.pop("done_count", None)
        m.pop("comment", None)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def _reconcile(current: Project, target: Project) -> None:
    """Undo/redo ombor va sexni orqaga qaytarmaydi: ular loyiha tarixidan tashqarida.
    - kroy o'sha-o'sha bo'lsa — joriy ombor bog'lanishi va «Раскроено» hisoblagichlari saqlanadi;
    - kroy boshqasiga almashsa — joriy natijaning omborga yozuvi bekor qilinadi (xuddi qayta kroy kabi),
      tarixdagi natija esa omborga yozilmagan deb olinadi (qayta «Записать на склад» mumkin)."""
    from .services import warehouse
    cur_ops = {o.id: o for o in current.operations}
    same: set[str] = set()
    for to in target.operations:
        co = cur_ops.get(to.id)
        if co is not None and co.result is not None and to.result is not None \
                and _result_sig(co.result) == _result_sig(to.result):
            same.add(to.id)
            for f in warehouse.WH_FIELDS:
                setattr(to.result, f, getattr(co.result, f))
            for cm, tm in zip(co.result.maps, to.result.maps):
                tm.done_count = cm.done_count
        else:
            warehouse.detach(to)
    for co in current.operations:
        if co.id not in same and co.result is not None and co.result.remnants_saved:
            warehouse.rollback(co)


def step(pid: str, d: int) -> Project:
    with _lock(pid):                   # qulf saqlashgacha ushlab turiladi (parallel tahrir bilan poyga yo'q)
        with SessionLocal() as s:
            row = s.get(ProjectRow, pid)
            if not row:
                raise HTTPException(404, _("project_not_found"))
            cur = (row.history_cursor or 0) + d
            h = s.scalar(select(ProjectHistoryRow).where(ProjectHistoryRow.project_id == pid,
                                                         ProjectHistoryRow.version == cur))
            if not h:
                raise HTTPException(400, _("cannot_undo") if d < 0 else _("cannot_redo"))
            target = validate_data(h.data)
            current = validate_data(row.data)
        _reconcile(current, target)
        return save(target, history=False, cursor=cur)


def delete(pid: str) -> None:
    with _lock(pid), SessionLocal() as s:
        s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid).delete()
        s.query(ProjectRow).filter(ProjectRow.id == pid).delete()
        s.commit()


def op_of(p: Project, op_id: str) -> Operation:
    for o in p.operations:
        if o.id == op_id:
            return o
    raise HTTPException(404, _("op_not_found"))


def part_of(op: Operation, part_id: str) -> Part:
    for pt in op.parts:
        if pt.id == part_id:
            return pt
    raise HTTPException(404, _("part_not_found"))


def next_uid(p: Project) -> int:
    return max((pt.uid for o in p.operations for pt in o.parts), default=0) + 1


def find_by_number(number: int) -> Optional[Project]:
    with SessionLocal() as s:
        row = s.scalar(select(ProjectRow).where(ProjectRow.number == number))
        return validate_data(row.data) if row else None


def find_by_mes_ref(ref: str) -> Optional[Project]:
    with SessionLocal() as s:
        row = s.scalar(select(ProjectRow).where(ProjectRow.mes_order_ref == ref))
        return validate_data(row.data) if row else None
