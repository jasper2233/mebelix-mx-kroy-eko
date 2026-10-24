"""Loyihalarni saqlash yordamchilari: yuklash, saqlash (tarix bilan), undo/redo, qulf, raqamlash."""
from __future__ import annotations

import copy
import json
import threading
import time
import zlib
from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy import null as sa_null

from .db import ProjectHistoryRow, ProjectRow, SessionLocal
from .i18n import _
from .models import Operation, Part, Project
from .services import calc

HISTORY_LIMIT = 100          # har loyiha uchun saqlanadigan versiyalar soni

_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()
_held = threading.local()            # oqim → {pid: (chuqurlik, PostgreSQL ulanishi)}


class _ProjectLock:
    """Loyiha qulfi: jarayon ichida — RLock (qayta kirish mumkin); PostgreSQL da qo'shimcha ravishda jarayonlararo advisory lock
    (bir nechta ilova jarayoni bir loyihani bir vaqtda o'zgartirsa, yangilanish yo'qolmasin). Advisory lock faqat eng tashqi
    kirishda olinadi — ichki (qayta) kirish o'sha ulanishdan foydalanadi, o'z-o'zini kutib qolmaydi."""

    def __init__(self, pid: str, rlock: threading.RLock):
        self.pid, self.rlock = pid, rlock

    def __enter__(self):
        self.rlock.acquire()
        held = getattr(_held, "m", None)
        if held is None:
            held = _held.m = {}
        depth, conn = held.get(self.pid, (0, None))
        if depth == 0:
            from .db import IS_PG, engine
            if IS_PG:
                from sqlalchemy import text
                try:
                    conn = engine.connect()
                    conn.execute(text("SELECT pg_advisory_lock(hashtextextended(:k, 0))"), {"k": f"mx:proj:{self.pid}"})
                    conn.commit()        # sessiya qulfi tranzaksiyasiz turadi (ochiq tranzaksiya VACUUM ni to'sardi)
                except Exception:
                    if conn is not None:
                        conn.close()
                    self.rlock.release()
                    raise
        held[self.pid] = (depth + 1, conn)
        return self

    def __exit__(self, *_exc):
        held = _held.m
        depth, conn = held[self.pid]
        try:
            if depth == 1:
                held.pop(self.pid, None)
                if conn is not None:
                    from sqlalchemy import text
                    try:
                        conn.execute(text("SELECT pg_advisory_unlock(hashtextextended(:k, 0))"), {"k": f"mx:proj:{self.pid}"})
                        conn.commit()
                    finally:
                        conn.close()
            else:
                held[self.pid] = (depth - 1, conn)
        finally:
            self.rlock.release()
        return False


def _lock(pid: str) -> _ProjectLock:
    with _locks_guard:
        lk = _locks.get(pid)
        if lk is None:
            lk = _locks[pid] = threading.RLock()
    return _ProjectLock(pid, lk)


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


def _pack(data: dict) -> bytes:
    """Tarix versiyasi → zlib(JSON): xom JSON dan ~17 marta, PostgreSQL TOAST (pglz) dan ~3 marta kichik."""
    return zlib.compress(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 6)


def history_data(h: ProjectHistoryRow) -> dict:
    """Tarix versiyasi ma'lumoti: siqilgan (`zdata`) yoki eski siqilmagan (`data`)."""
    if h.zdata is not None:
        return json.loads(zlib.decompress(h.zdata))
    return h.data


def pack_history_backlog(batch: int = 100) -> int:
    """Eski siqilmagan tarix versiyalarini siqish (start-up da fon oqimida, barcha korxonalar). Qaytaradi: nechta siqildi."""
    from . import tenant
    n = 0
    with tenant.system():
        while True:
            with SessionLocal() as s:
                rows = s.scalars(select(ProjectHistoryRow).where(ProjectHistoryRow.zdata.is_(None),
                                                                 ProjectHistoryRow.data.is_not(None)).limit(batch)).all()
                if not rows:
                    return n
                for h in rows:
                    h.zdata, h.data = _pack(h.data), sa_null()          # SQL NULL (JSON «null» emas)
                s.commit()
                n += len(rows)


def next_number() -> int:
    with SessionLocal() as s:
        return (s.scalar(select(func.max(ProjectRow.number))) or 1000000) + 1


def save(p: Project, history: bool = True, cursor: Optional[int] = None, skip_unchanged: bool = False) -> Project:
    """Hisob-kitobni yangilab saqlaydi; history=True — yangi versiya (redo zanjiri kesiladi);
    cursor — undo/redo: tarix ko'rsatkichi shu versiyaga o'rnatiladi (bitta tranzaksiyada);
    skip_unchanged — ma'lumot avvalgisi bilan bir xil bo'lsa bo'sh tarix versiyasi yozilmaydi («Сохранить»)."""
    calc.recalc_project(p)
    data, bad = _dump(p)
    if bad:                                    # xotiradagi obyekt ham tozalanadi (javob JSON bo'lib chiqsin)
        clean = Project.model_validate(data)
        for k in Project.model_fields:
            setattr(p, k, getattr(clean, k))
    cost = sum(o.cost_material + o.cost_operation for o in p.operations)
    with _lock(p.id), SessionLocal() as s:
        row = s.get(ProjectRow, p.id)
        prev = row.data if row is not None else None
        if not row:
            row = ProjectRow(id=p.id, history_cursor=0)
            s.add(row)
        row.number = p.number; row.folder_id = p.folder_id; row.name = p.name
        row.owner = p.owner; row.status = int(p.status); row.order_date = str(p.order_date)
        row.cost = round(cost, 2); row.mes_order_ref = p.mes_order_ref; row.customer = p.customer
        # versiya: bazadagi oldingi yozuvdan +1 (mijozdan / tarixdan kelgan qiymat hisobga olinmaydi); o'zgarmagan bo'lsa — o'sha
        prev_rev = int((prev or {}).get("rev") or 0) if isinstance(prev, dict) else 0
        data["rev"] = prev_rev
        unchanged = prev is not None and prev == data
        data["rev"] = p.rev = prev_rev if unchanged else prev_rev + 1
        row.data = data
        s.flush()                      # loyiha qatori tarixdan oldin yozilsin (PostgreSQL FK tekshiruvi)
        if cursor is not None:
            row.history_cursor = cursor
        elif history and not (skip_unchanged and unchanged):
            cur = row.history_cursor or 0
            s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == p.id,
                                              ProjectHistoryRow.version > cur).delete()
            v = cur + 1
            s.add(ProjectHistoryRow(project_id=p.id, version=v, zdata=_pack(data)))
            row.history_cursor = v
            s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == p.id,
                                              ProjectHistoryRow.version <= v - HISTORY_LIMIT).delete()
        s.commit()
    try:        # qoldiq rezervi: loyiha listlaridan chiqqan qoldiqlar bo'shatiladi (saqlashga xalaqit bermasin)
        from .services import warehouse
        warehouse.sync_reservations(p)
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger("mebelix.store").exception("rezervni sinxronlab bo'lmadi")
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
def editing(pid: str, history: bool = True, skip_unchanged: bool = False) -> Iterator[Project]:
    """Loyihani qulf ostida o'zgartirish: `with editing(pid) as p: ...` — chiqishda saqlanadi (xato bo'lsa yo'q).
    skip_unchanged=True — o'zgarish bo'lmasa tarixga bo'sh versiya yozilmaydi."""
    with _lock(pid):
        p = load(pid)
        yield p
        save(p, history, skip_unchanged=skip_unchanged)


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
            target = validate_data(history_data(h))
            current = validate_data(row.data)
        _reconcile(current, target)
        return save(target, history=False, cursor=cur)


def delete(pid: str) -> None:
    with _lock(pid), SessionLocal() as s:
        s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid).delete()
        s.query(ProjectRow).filter(ProjectRow.id == pid).delete()
        s.commit()
    from .services import warehouse
    warehouse.release_project(pid)             # loyiha band qilgan qoldiqlar bo'shaydi


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


def require_folder(folder_id: Optional[str]) -> Optional[str]:
    """Papka mavjudligini tekshiradi (None / bo'sh — «ildiz», ruxsat). Yo'q bo'lsa — 400."""
    if not folder_id:
        return None
    from .db import FolderRow
    with SessionLocal() as s:
        if s.get(FolderRow, folder_id) is None:
            raise HTTPException(400, _("folder_not_found"))
    return folder_id
