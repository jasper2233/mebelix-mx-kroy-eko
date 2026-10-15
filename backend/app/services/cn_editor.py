"""CNE — Редактирование нестингового раскроя (W16, UPD-003): kartani qo'lda tahrirlash (minimal to'plam).

Frontend qoralama natijani (`CuttingResult`, kind="nest") va bitta amalni yuboradi → backend yangi qoralamani qaytaradi (loyiha saqlanmaydi).
Har amaldan keyin hamma karta QAYTA quriladi: joylashuv konturlari detal shakli va (burchak, x, y) dan serverda hisoblanadi (mijozdan kelgan
outline / holes ishonilmaydi), qoldiqlar / etiketka o'rni / ko'rsatkichlar yangilanadi va `validate_cn` (mustaqil aniq geometriya tekshiruvi)
dan o'tkaziladi: kesishish, detallar orasidagi masofa, list chetidan masofa, burilish qoidalari buzilgan bo'lsa amal RAD ETILADI (`EditError`).

Amallar (`action.type`):
  add_map     {sheet_id?}                              yangi bo'sh karta
  delete_map  {map}                                    kartani o'chirish (detallar «Остаток» ga qaytadi)
  copies      {map, copies}                            shu sxemadagi listlar soni (C)
  comment     {map, comment}                           karta izohi
  move_map    {map, to: up|down|first|last}            kartalar tartibi
  move        {map, indices | index, dx, dy}           tanlanganlarni (mm) siljitish
  slide       {map, indices | index, dir}              tanlanganlarni yo'nalish bo'yicha qo'shni detal / list chetigacha «yopishtirib» surish
                                                       (dir: left | right | up | down) — «chet bo'yicha» yopishtirish
  snap        {map, indices | index, from:[x,y], to:[x,y]}   «nuqta bo'yicha» yopishtirish: from nuqtasi to ga qarab suriladi, to'siq
                                                       (masofa qoidasi) uchragan joyda to'xtaydi
  rotate      {map, indices | index, delta | angle}    burish (90° qadam yoki erkin burchak): delta — nisbiy, angle — mutlaq (bitta detal)
  remove      {map, indices | index}                   detallarni kartadan olib tashlash
  place       {map, uid, x, y, angle?}                 joylanmagan nusxani berilgan joyga qo'yish (o'rovchi to'rtburchak chap-yuqori burchagi)
  auto_place  {uid, map?}                              joylanmagan nusxani eng chap-yuqori mumkin bo'lgan joyga (map dan boshlab)
  renest      {map}                                    kartadagi detallar + joylanmaganlarni shu listga qaytadan joylash
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from ..i18n import _
from ..models import CNParams, CuttingResult, Offcut, Operation, Project
from . import cn_geometry as G
from . import cn_nest as N
from .cn_calc import (CnItems, Spec, build_items, ensure_cn, finish_result, make_map, spacing_of)
from .cn_validate import Poly, angle_ok, group_ok, validate_cn
from .editor import EditError

MAX_COPIES = 100_000
COMMENT_MAX = 2000
STEP_MM = 2.0                      # sirpantirish qadami (mm); to'siq aniqligi ikkilik qidiruv bilan 0.01 mm gacha


# ───────────────────────── Natija izi (parallel tahrirni aniqlash) ─────────────────────────
def result_rev(res: Optional[CuttingResult]) -> str:
    """Natijaning «izi»: kartalar, nusxalar, izohlar, joylashuvlar (detal, burchak, x, y), omborga yozilganligi."""
    if res is None:
        return "none"
    h = hashlib.sha1()
    for m in res.maps:
        h.update(json.dumps([m.sheet_id, m.copies, m.comment, [[p.part_uid, round(p.angle, 4), round(p.x, 3), round(p.y, 3)]
                                                                for p in m.placements]], separators=(",", ":")).encode("utf-8"))
    h.update(f"|{len(res.maps)}|{len(res.unplaced)}|{int(bool(res.remnants_saved))}".encode())
    return h.hexdigest()[:16]


# ───────────────────────── Qoralama ↔ qatorlar ─────────────────────────
@dataclass
class Row:
    sheet_id: str
    copies: int = 1
    comment: str = ""
    done: int = 0
    specs: list[Spec] = field(default_factory=list)
    offcuts: Optional[list[Offcut]] = None          # o'zgarmagan kartada qoldiqlar qayta hisoblanmaydi
    sig: Optional[tuple] = None


class _Ctx:
    def __init__(self, project: Project, op: Operation, res: CuttingResult):
        self.project, self.op, self.res = project, op, res
        self.cn: CNParams = ensure_cn(op)
        self.ci: CnItems = build_items(project, op)
        self.parts_by_uid = {p.uid: p for p in self.ci.by_pid.values() if p.id in self.ci.shapes}
        self.stock = {s.id: s for s in op.sheets}
        self.spacing = spacing_of(self.cn)

    def shape(self, part) -> G.Shape:
        return self.ci.shapes[part.id]

    def rows_of(self) -> list[Row]:
        rows: list[Row] = []
        for m in self.res.maps:
            r = Row(m.sheet_id, max(1, int(m.copies)), m.comment, m.done_count)
            for pl in m.placements:
                part = self.parts_by_uid.get(pl.part_uid)
                if part is None:
                    raise EditError(_("cn.v_no_part", uid=pl.part_uid))
                r.specs.append(Spec(part, self.shape(part), float(pl.angle) % 360.0, float(pl.x), float(pl.y)))
            st = self.stock.get(m.sheet_id)
            if st is not None:
                r.sig = _sig(st, r.specs)
                r.offcuts = [o.model_copy() for o in m.offcuts]
            rows.append(r)
        return rows

    def polys(self, specs: list[Spec]) -> list[Poly]:
        out = []
        for sp in specs:
            outer, holes, _bw, _bh = G.place_shape(sp.shape, sp.angle, sp.x, sp.y)
            out.append(Poly(sp.part.uid, outer, holes))
        return out

    def remaining(self, rows: list[Row], uid: int) -> int:
        part = self.parts_by_uid[uid]
        return self.ci.need.get(part.id, 0) - sum(r.copies * sum(1 for sp in r.specs if sp.part.uid == uid) for r in rows)


def _sig(st, specs: list[Spec]) -> tuple:
    return (st.id, st.length, st.width, tuple((s.part.id, round(s.angle, 6), s.x, s.y) for s in specs))


def _build(ctx: _Ctx, rows: list[Row], base: CuttingResult, final: bool) -> CuttingResult:
    cn = ctx.cn
    labels: dict = {}
    maps = []
    for i, r in enumerate(rows, 1):
        st = ctx.stock.get(r.sheet_id)
        if st is None:
            raise EditError(_("cn.e_no_sheet"))
        sig = _sig(st, r.specs)
        reuse = r.offcuts if (r.sig is not None and r.sig == sig) else None
        m = make_map(i, st, max(1, min(MAX_COPIES, int(r.copies))), r.specs, cn, labels, reuse, r.comment[:COMMENT_MAX],
                     min(max(0, r.done), max(1, r.copies)))
        maps.append(m)
    out = CuttingResult(maps=maps, kind="nest", manual=True, variant=base.variant, elapsed_s=base.elapsed_s,
                        warnings=list(base.warnings), nest=dict(base.nest or {}))
    placed: Counter = Counter()
    for r in rows:
        for sp in r.specs:
            placed[sp.part.id] += r.copies
    out.unplaced = [pid for pid, n in ctx.ci.need.items() for _k in range(max(0, n - placed.get(pid, 0)))]
    errs = validate_cn(out, ctx.ci.shapes, ctx.ci.need, ctx.ci.grains, ctx.op.sheets, cn, allow_empty=not final)
    if errs:
        raise EditError(errs[0], errs)
    out.unplaced = out.unplaced + ctx.ci.small + ctx.ci.bad
    finish_result(out)
    return out


def rebuild(project: Project, op: Operation, res: CuttingResult, final: bool = True) -> CuttingResult:
    """Qoralamani qayta qurish va tekshirish (`PUT …/result`: final=True — bo'sh karta bo'lmasligi shart)."""
    ctx = _Ctx(project, op, res)
    return _build(ctx, ctx.rows_of(), res, final)


# ───────────────────────── Amallar ─────────────────────────
def apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    """Bitta tahrir amali. Xato bo'lsa EditError (qoralama o'zgarmaydi)."""
    if not isinstance(action, dict):
        raise EditError(_("cn.e_bad_action", a=type(action).__name__))
    try:
        return _apply(project, op, res, action)
    except EditError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        raise EditError(_("cn.e_bad_action", a=str(action.get("type"))[:40])) from None


def _int(v, lo: int, hi: int) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError
    return max(lo, min(hi, int(v)))


def _num(v, lo: float = -1e6, hi: float = 1e6) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v in (float("inf"), float("-inf")):
        raise ValueError
    if not (lo <= v <= hi):
        raise EditError(_("cn.e_range"))
    return float(v)


def _indices(action: dict, n: int, mi: int) -> list[int]:
    raw = action.get("indices")
    idxs = sorted({_int(i, -1, 10 ** 9) for i in raw}) if isinstance(raw, list) else [_int(action.get("index", -1), -1, 10 ** 9)]
    for i in idxs:
        if not (0 <= i < n):
            raise EditError(_("cn.e_no_piece", map=mi + 1, i=i + 1))
    return idxs


def _shift(sp: Spec, dx: float, dy: float) -> Spec:
    return Spec(sp.part, sp.shape, sp.angle, sp.x + dx, sp.y + dy)


def _advance(ctx: _Ctx, st, specs: list[Spec], idxs: list[int], vx: float, vy: float) -> float:
    """Tanlanganlarni (vx, vy) vektor bo'ylab to'siqqacha (t ∈ [0, 1]) siljitish: eng katta yaroqli t."""
    L = math.hypot(vx, vy)
    if L < 1e-9:
        return 0.0
    base = [specs[i] for i in idxs]
    sel = set(idxs)
    others = ctx.polys([sp for i, sp in enumerate(specs) if i not in sel])          # bir marta: ular qimirlamaydi

    def ok(t: float) -> bool:
        moved = ctx.polys([_shift(sp, vx * t, vy * t) for sp in base])
        return group_ok(moved, others, st.length, st.width, ctx.cn.margin, ctx.spacing)
    if not ok(0.0):
        raise EditError(_("cn.e_collision", uid=base[0].part.uid))
    step = min(1.0, STEP_MM / L)
    last, t = 0.0, 0.0
    while t < 1.0 - 1e-12:
        t = min(1.0, t + step)
        if ok(t):
            last = t
        else:
            lo, hi = last, t
            while (hi - lo) * L > 0.01:
                mid = (lo + hi) / 2
                if ok(mid):
                    lo = mid
                else:
                    hi = mid
            return lo
    return last


def _apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    ctx = _Ctx(project, op, res)
    rows = ctx.rows_of()
    kind = action.get("type")

    if kind == "add_map":
        sid = action.get("sheet_id")
        st = (ctx.stock.get(sid) if isinstance(sid, str) else None) or (op.sheets[0] if op.sheets else None)
        if st is None:
            raise EditError(_("cn.e_no_sheet"))
        rows.append(Row(st.id))
        return _build(ctx, rows, res, False)
    if kind == "auto_place":
        return _auto_place(ctx, rows, res, action)

    mi = _int(action.get("map", 0), 0, 10 ** 9) - 1
    if not (0 <= mi < len(rows)):
        raise EditError(_("cn.e_no_map"))
    r = rows[mi]
    st = ctx.stock.get(r.sheet_id)
    if st is None:
        raise EditError(_("cn.e_no_sheet"))

    if kind == "delete_map":
        rows.pop(mi)
    elif kind == "copies":
        n = action.get("copies")
        if isinstance(n, bool) or not isinstance(n, (int, float)) or not (1 <= n <= MAX_COPIES):
            raise EditError(_("cn.e_range"))
        r.copies = int(n)
    elif kind == "comment":
        c = action.get("comment", "")
        if not isinstance(c, str):
            raise ValueError
        r.comment = c[:COMMENT_MAX]
    elif kind == "move_map":
        to = action.get("to")
        j = {"up": mi - 1, "down": mi + 1, "first": 0, "last": len(rows) - 1}.get(to)
        if j is None:
            raise ValueError
        if not (0 <= j < len(rows)):
            raise EditError(_("cn.e_no_map"))
        rows.insert(j, rows.pop(mi))
    elif kind == "remove":
        for i in sorted(_indices(action, len(r.specs), mi), reverse=True):
            r.specs.pop(i)
    elif kind == "move":
        idxs = _indices(action, len(r.specs), mi)
        dx, dy = _num(action.get("dx", 0.0), -1e5, 1e5), _num(action.get("dy", 0.0), -1e5, 1e5)
        for i in idxs:
            r.specs[i] = _shift(r.specs[i], dx, dy)
    elif kind == "slide":
        idxs = _indices(action, len(r.specs), mi)
        d = action.get("dir")
        if d not in ("left", "right", "up", "down"):
            raise ValueError
        sel = ctx.polys([r.specs[i] for i in idxs])
        x0 = min(p.bb[0] for p in sel)
        y0 = min(p.bb[1] for p in sel)
        x1 = max(p.bb[2] for p in sel)
        y1 = max(p.bb[3] for p in sel)
        m = ctx.cn.margin
        vx, vy = {"left": (-(x0 - m), 0.0), "right": ((st.length - m) - x1, 0.0), "up": (0.0, -(y0 - m)),
                  "down": (0.0, (st.width - m) - y1)}[d]
        t = _advance(ctx, st, r.specs, idxs, vx, vy)
        if t * math.hypot(vx, vy) < 0.01:
            raise EditError(_("cn.e_no_move"))
        for i in idxs:
            r.specs[i] = _shift(r.specs[i], vx * t, vy * t)
    elif kind == "snap":
        idxs = _indices(action, len(r.specs), mi)
        f, to = action.get("from"), action.get("to")
        if not (isinstance(f, list) and isinstance(to, list) and len(f) == 2 and len(to) == 2):
            raise ValueError
        vx, vy = _num(to[0], -1e6, 1e6) - _num(f[0], -1e6, 1e6), _num(to[1], -1e6, 1e6) - _num(f[1], -1e6, 1e6)
        t = _advance(ctx, st, r.specs, idxs, vx, vy)
        if t * math.hypot(vx, vy) < 0.01:
            raise EditError(_("cn.e_no_move"))
        for i in idxs:
            r.specs[i] = _shift(r.specs[i], vx * t, vy * t)
    elif kind == "rotate":
        _rotate(ctx, r, _indices(action, len(r.specs), mi), action)
    elif kind == "place":
        uid = _int(action.get("uid", 0), 0, 10 ** 9)
        part = ctx.parts_by_uid.get(uid)
        if part is None:
            raise EditError(_("cn.e_not_found", uid=uid))
        if ctx.remaining(rows, uid) < r.copies:
            raise EditError(_("cn.e_none_left", uid=uid))
        ang = _num(action.get("angle", 0.0), -720, 720) % 360.0
        if not angle_ok(ang, part.grain, ctx.cn):
            raise EditError(_("cn.e_angle", uid=uid, a=f"{ang:g}"))
        r.specs.append(Spec(part, ctx.shape(part), ang, _num(action.get("x", 0.0), -1e5, 1e5), _num(action.get("y", 0.0), -1e5, 1e5)))
    elif kind == "renest":
        return _renest(ctx, rows, mi, res)
    else:
        raise EditError(_("cn.e_bad_action", a=str(kind)[:40]))
    return _build(ctx, rows, res, False)


def _rotate(ctx: _Ctx, r: Row, idxs: list[int], action: dict) -> None:
    sel = [r.specs[i] for i in idxs]
    if "angle" in action and len(sel) == 1:
        delta = (_num(action["angle"], -720, 720) - sel[0].angle) % 360.0
    else:
        delta = _num(action.get("delta", 90.0), -720, 720) % 360.0
    boxes = [G.place_shape(sp.shape, sp.angle, sp.x, sp.y) for sp in sel]
    gx0 = min(sp.x for sp in sel)
    gy0 = min(sp.y for sp in sel)
    gx1 = max(sp.x + b[2] for sp, b in zip(sel, boxes))
    gy1 = max(sp.y + b[3] for sp, b in zip(sel, boxes))
    cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
    c, s = G.rot_cs(delta)
    for i, sp, b in zip(idxs, sel, boxes):
        na = (sp.angle + delta) % 360.0
        if not angle_ok(na, sp.part.grain, ctx.cn):
            raise EditError(_("cn.e_angle", uid=sp.part.uid, a=f"{na:g}"))
        mx, my = sp.x + b[2] / 2, sp.y + b[3] / 2
        if len(sel) == 1:
            ncx, ncy = mx, my
        else:
            ncx, ncy = cx + c * (mx - cx) - s * (my - cy), cy + s * (mx - cx) + c * (my - cy)
        o = G.orient_shape(sp.shape, na)
        r.specs[i] = Spec(sp.part, sp.shape, na, ncx - o.bw / 2, ncy - o.bh / 2)


def _nest_params(ctx: _Ctx, quality: str = "normal") -> N.NestParams:
    return N.NestParams(spacing=ctx.spacing, margin=ctx.cn.margin, quality=quality, time_limit=min(10.0, ctx.cn.time_limit_s or 10.0))


def _auto_place(ctx: _Ctx, rows: list[Row], res: CuttingResult, action: dict) -> CuttingResult:
    uid = _int(action.get("uid", 0), 0, 10 ** 9)
    part = ctx.parts_by_uid.get(uid)
    if part is None:
        raise EditError(_("cn.e_not_found", uid=uid))
    start = _int(action.get("map", 1), 1, 10 ** 9) - 1 if action.get("map") is not None else 0
    order = list(range(start, len(rows))) + list(range(0, min(start, len(rows))))
    angles = N.allowed_angles(part.grain, ctx.cn.rot90, ctx.cn.rot_step, ctx.cn.use_grain)
    last: Optional[EditError] = None
    for j in order:
        r = rows[j]
        if ctx.remaining(rows, uid) < r.copies:
            continue
        st = ctx.stock.get(r.sheet_id)
        if st is None:
            continue
        existing = [(p.outer, p.holes) for p in ctx.polys(r.specs)]
        got = N.place_in_layout(ctx.shape(part), angles, st.length, st.width, existing, _nest_params(ctx, "max"))
        if got is None:
            last = EditError(_("cn.e_no_room", uid=uid, map=j + 1))
            continue
        ang, x, y = got
        r.specs.append(Spec(part, ctx.shape(part), ang, x, y))
        try:
            return _build(ctx, rows, res, False)
        except EditError as e:
            r.specs.pop()
            last = e
    raise last or EditError(_("cn.e_none_left", uid=uid))


def _renest(ctx: _Ctx, rows: list[Row], mi: int, res: CuttingResult) -> CuttingResult:
    """Kartadagi detallar + hamma joylanmagan nusxalar shu listga qaytadan joylanadi; hamma eski detallar joylashsa — qabul qilinadi."""
    r = rows[mi]
    st = ctx.stock[r.sheet_id]
    cnt: Counter = Counter(sp.part.id for sp in r.specs)
    free: Counter = Counter()
    for pid, need in ctx.ci.need.items():
        placed = sum(rr.copies * sum(1 for sp in rr.specs if sp.part.id == pid) for rr in rows)
        left = max(0, need - placed)
        if left and r.copies == 1:
            free[pid] = left
    want = Counter(cnt)
    for pid, n in free.items():
        want[pid] += n
    parts = []
    by_pid = {p.id: p for p in ctx.ci.by_pid.values()}
    for pid, n in want.items():
        part = by_pid[pid]
        parts.append(N.NestPart(pid, part.uid, ctx.shape(part), n, N.allowed_angles(part.grain, ctx.cn.rot90, ctx.cn.rot_step, ctx.cn.use_grain)))
    out = N.nest(parts, [N.NestSheet(st.id, st.length, st.width, 1)], _nest_params(ctx, "normal"))
    if not out.layouts:
        raise EditError(_("cn.e_renest_worse"))
    lay = out.layouts[0]
    got: Counter = Counter(parts[it.part].key for it in lay.items)
    if any(got[pid] < n for pid, n in cnt.items()):
        raise EditError(_("cn.e_renest_worse"))
    r.specs = [Spec(by_pid[parts[it.part].key], parts[it.part].shape, it.angle, it.x, it.y) for it in lay.items]
    return _build(ctx, rows, res, False)
