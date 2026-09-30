"""Loyihalarni saqlash yordamchilari: yuklash, saqlash (tarix bilan), undo/redo, qulf, raqamlash."""
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import HTTPException
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
        return Project.model_validate(row.data)


def next_number() -> int:
    with SessionLocal() as s:
        return (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1


def save(p: Project, history: bool = True) -> Project:
    """Hisob-kitobni yangilab saqlaydi; history=True — yangi versiya (redo zanjiri kesiladi)."""
    calc.recalc_project(p)
    data = json.loads(p.model_dump_json())
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
        if history:
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


def step(pid: str, d: int) -> Project:
    with _lock(pid), SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        if not row:
            raise HTTPException(404, _("project_not_found"))
        cur = (row.history_cursor or 0) + d
        h = s.scalar(select(ProjectHistoryRow).where(ProjectHistoryRow.project_id == pid,
                                                     ProjectHistoryRow.version == cur))
        if not h:
            raise HTTPException(400, _("cannot_undo") if d < 0 else _("cannot_redo"))
        row.history_cursor = cur
        s.commit()
        p = Project.model_validate(h.data)
    return save(p, history=False)


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
        return Project.model_validate(row.data) if row else None


def find_by_mes_ref(ref: str) -> Optional[Project]:
    with SessionLocal() as s:
        row = s.scalar(select(ProjectRow).where(ProjectRow.mes_order_ref == ref))
        return Project.model_validate(row.data) if row else None
