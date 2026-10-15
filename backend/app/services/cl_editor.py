"""CLE — Редактирование погонажного раскроя (W11): kroy kartasini (polosa) qo'lda tahrirlash.

Frontend qoralama natijani (`CuttingResult`) va bitta amalni yuboradi → backend yangi qoralamani qaytaradi (loyiha saqlanmaydi).
Har amaldan keyin hamma karta qayta quriladi (koordinatalar, otxod tasnifi, T/P/W buyruqlari, LT / F / kesimlar soni) va
`validate_cl` dan o'tkaziladi: polosaga sig'maydigan, ortiqcha detal joylangan, polosa soni oshgan holat qaytarilmaydi — `EditError`.
Detal uzunligi, propil va torsovka serverda hisoblanadi (mijoz koordinatalari qabul qilinmaydi).

Amallar (`action.type`):
  add_map     {sheet_id?}                    yangi bo'sh karta (polosa)
  delete_map  {map}                          kartani o'chirish (detallar «Остаток» ga qaytadi)
  copies      {map, copies}                  «Количество листов» — shu sxemadagi polosalar soni (C)
  place       {map, uid, index?}             detalni polosaga qo'yish (index — pozitsiya; bo'lmasa oxiriga)
  place_auto  {uid, map?}                    detalni birinchi mos polosaga qo'yish (map dan boshlab)
  remove      {map, index | indices}         detalni polosadan olib tashlash
  move        {map, index, to}               to: start | end | left | right | son (pozitsiya) — Ctrl+← / Ctrl+→
  transfer    {map, index, to_map}           detalni boshqa polosaga ko'chirish (ikkala karta nusxalari soni teng bo'lsa)
  trims       {map, trim_start?, trim_end?}  «Торцовка листа»: shu polosaga alohida torsovka (None — parametrdagi qiymat)
  move_map    {map, to}                      kartani ko'chirish: up | down | first | last
  comment     {map, comment}                 karta izohi
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from ..i18n import _
from ..models import CutMap, CuttingResult, Operation, Project, StockSheet
from .cl_calc import ClItems, cl_items, ensure_cl, normalize_sheets
from .cl_optimizer import UNLIMITED, Geom, finish_cl, layout, make_map, mm, rules_of, trims_of, u, validate_cl
from .editor import EditError

MAX_COPIES = 100_000
MAX_TRIM = 500.0
COMMENT_MAX = 2000


@dataclass
class PInfo:
    part_id: str
    uid: int
    p: int          # pilniy uzunlik, birlik (0.01 mm)
    need: int       # ОК − МК


def part_info(ci: ClItems) -> tuple[dict[int, PInfo], dict[str, PInfo]]:
    """Kroyga kiradigan detallar (uzunlik > 0): uid → PInfo va part_id → PInfo."""
    need: Counter = Counter(it.part_id for it in ci.items)
    by_uid: dict[int, PInfo] = {}
    by_id: dict[str, PInfo] = {}
    for it in ci.items:
        if it.part_id not in by_id:
            pi = PInfo(it.part_id, it.uid, u(it.length), need[it.part_id])
            by_id[it.part_id] = pi
            by_uid[it.uid] = pi
    return by_uid, by_id


def result_rev(res: Optional[CuttingResult]) -> str:
    """Natijaning «izi» (parallel tahrirni aniqlash): kartalar, nusxalar, izohlar, torsovka, detallar tartibi, omborga yozilganligi."""
    if res is None:
        return "none"
    h = hashlib.sha1()
    for m in res.maps:
        h.update(json.dumps([m.sheet_id, m.copies, m.comment, m.trim_length, m.end_offset_right,
                             [p.part_uid for p in m.placements]], separators=(",", ":"), default=str).encode("utf-8"))
    h.update(f"|{len(res.maps)}|{len(res.unplaced)}|{int(bool(res.remnants_saved))}".encode())
    return h.hexdigest()[:16]


# ───────────────────────── Qoralama ↔ buyurtma ro'yxati ─────────────────────────
@dataclass
class Row:
    """Bitta karta: polosa turi, nusxalar, detallar tartibi (uid), alohida torsovkalar (None — parametr)."""
    sheet_id: str
    copies: int = 1
    comment: str = ""
    done: int = 0
    ts: Optional[float] = None
    te: Optional[float] = None
    pieces: Optional[list[int]] = None

    def __post_init__(self) -> None:
        if self.pieces is None:
            self.pieces = []


def _rows_of(res: CuttingResult) -> list[Row]:
    out = []
    for m in res.maps:
        pls = sorted(m.placements, key=lambda p: p.x)
        out.append(Row(m.sheet_id, max(1, int(m.copies)), m.comment, m.done_count, m.trim_length, m.end_offset_right,
                       [p.part_uid for p in pls]))
    return out


def _build(project: Project, op: Operation, ci: ClItems, rows: list[Row], base: CuttingResult, final: bool) -> CuttingResult:
    cl = ensure_cl(op)
    by_uid, by_id = part_info(ci)
    stock: dict[str, StockSheet] = {s.id: s for s in op.sheets}
    k = u(cl.kerf)
    rules = rules_of(cl)
    ts_def, te_def = trims_of(cl)
    width = float(cl.width)
    counter = [0]
    maps: list[CutMap] = []
    used_sheet: Counter = Counter()
    placed: Counter = Counter()
    for i, r in enumerate(rows, 1):
        st = stock.get(r.sheet_id)
        if st is None:
            raise EditError(_("edc.no_sheet"))
        ts = u(r.ts) if r.ts is not None else ts_def
        te = u(r.te) if r.te is not None else te_def
        g = Geom(u(st.length), k, ts, te)
        if g.U <= 0:
            raise EditError(_("edc.sheet_small"))
        pieces: list[tuple[int, str, int]] = []
        for uid in r.pieces:
            pi = by_uid.get(uid)
            if pi is None:
                raise EditError(_("part_uid_not_found", uid=uid))
            pieces.append((pi.p, pi.part_id, pi.uid))
            placed[pi.part_id] += r.copies
        is_rem = bool(st.is_remnant or st.source_remnant_id)
        if pieces:
            m = make_map(i, st, g, rules, pieces, width, counter, is_remnant=is_rem)
            if m is None:
                need = mm(sum(p for p, _a, _b in pieces) + (len(pieces) - 1) * k)
                raise EditError(_("edc.no_fit", map=i, need=need, have=mm(g.U)))
        else:
            if final:
                raise EditError(_("edc.map_empty", map=i))
            m = CutMap(index=i, sheet_id=st.id, sheet_length=mm(g.L), sheet_width=width, is_remnant=is_rem, copies=1)
            m.trim_length, m.end_offset_right = mm(ts), mm(te)
            m.sheet_area_m2 = round(g.L / 100 * width / 1e6, 4)
        m.copies = max(1, min(MAX_COPIES, int(r.copies)))
        m.comment = r.comment[:COMMENT_MAX]
        m.done_count = min(max(0, r.done), m.copies)
        used_sheet[st.id] += m.copies
        maps.append(m)
    for pid, n in placed.items():
        if n > by_id[pid].need:
            raise EditError(_("edc.too_many", uid=by_id[pid].uid, n=n, need=by_id[pid].need))
    for sid, n in used_sheet.items():
        st = stock[sid]
        if st.qty < UNLIMITED and n > st.qty:
            raise EditError(_("edc.sheets_exceeded", size=f"{st.length:g}", n=n, q=st.qty))
    out = CuttingResult(maps=maps, variant=base.variant, manual=True, elapsed_s=base.elapsed_s, warnings=list(base.warnings))
    in_cut = [pid for pid, pi in by_id.items() for _i in range(pi.need - placed.get(pid, 0))]
    out.unplaced = list(in_cut)
    finish_cl(out, width)
    errs = validate_cl(out, ci.items, op.sheets, cl, allow_empty=not final)
    if errs:
        raise EditError(errs[0], errs)
    out.unplaced = in_cut + ci.small + ci.bad + ci.uncomputed          # kroyga kirmaydigan detallar ham «sig'magan» ro'yxatda
    return out


def rebuild(project: Project, op: Operation, res: CuttingResult, final: bool = True) -> CuttingResult:
    """Qoralamani qayta qurish va tekshirish (`PUT …/result`: final=True — bo'sh karta bo'lmasligi shart)."""
    normalize_sheets(op)
    ci = cl_items(project, op)
    return _build(project, op, ci, _rows_of(res), res, final)


# ───────────────────────── Amallar ─────────────────────────
def apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    """Bitta tahrir amali. Xato bo'lsa EditError (qoralama o'zgarmaydi)."""
    if not isinstance(action, dict):
        raise EditError(_("edc.bad_action", a=type(action).__name__))
    try:
        return _apply(project, op, res, action)
    except EditError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        raise EditError(_("edc.bad_action", a=str(action.get("type"))[:40])) from None


def _int(v, lo: int, hi: int) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError
    return max(lo, min(hi, int(v)))


def _trim(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        raise ValueError
    if not (0 <= v <= MAX_TRIM):
        raise EditError(_("edc.trim_range", n=int(MAX_TRIM)))
    return float(v)


def _apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    normalize_sheets(op)
    ci = cl_items(project, op)
    by_uid, _by_id = part_info(ci)
    rows = _rows_of(res)
    kind = action.get("type")
    stock = {s.id: s for s in op.sheets}

    def remaining(uid: int) -> int:
        pi = by_uid[uid]
        return pi.need - sum(r.copies * r.pieces.count(uid) for r in rows)

    if kind == "add_map":
        sid = action.get("sheet_id")
        st = (stock.get(sid) if isinstance(sid, str) else None) or (op.sheets[0] if op.sheets else None)
        if st is None:
            raise EditError(_("edc.no_sheet"))
        rows.append(Row(st.id))
        return _build(project, op, ci, rows, res, False)

    mi = _int(action.get("map", 0), 0, 10 ** 9) - 1
    if not (0 <= mi < len(rows)):
        raise EditError(_("edc.no_map"))
    r = rows[mi]

    if kind == "delete_map":
        rows.pop(mi)
    elif kind == "copies":
        n = action.get("copies")
        if isinstance(n, bool) or not isinstance(n, (int, float)) or not (1 <= n <= MAX_COPIES):
            raise EditError(_("edc.copies_range", n=MAX_COPIES))
        r.copies = int(n)
    elif kind == "comment":
        c = action.get("comment", "")
        if not isinstance(c, str):
            raise ValueError
        r.comment = c[:COMMENT_MAX]
    elif kind == "trims":
        r.ts = _trim(action.get("trim_start"))
        r.te = _trim(action.get("trim_end"))
    elif kind == "move_map":
        to = action.get("to")
        j = {"up": mi - 1, "down": mi + 1, "first": 0, "last": len(rows) - 1}.get(to)
        if j is None:
            raise ValueError
        if not (0 <= j < len(rows)):
            raise EditError(_("ed.map_edge"))
        rows.insert(j, rows.pop(mi))
    elif kind in ("place", "place_auto"):
        uid = _int(action.get("uid", 0), 0, 10 ** 9)
        if uid not in by_uid:
            raise EditError(_("part_uid_not_found", uid=uid))
        if kind == "place":
            if remaining(uid) < r.copies:
                raise EditError(_("edc.none_left", uid=uid, c=r.copies))
            idx = action.get("index")
            idx = len(r.pieces) if idx is None else _int(idx, 0, len(r.pieces))
            r.pieces.insert(idx, uid)
        else:
            order = list(range(mi, len(rows))) + list(range(0, mi))
            last_err: Optional[EditError] = None
            for j in order:
                rj = rows[j]
                if remaining(uid) < rj.copies:
                    continue
                rj.pieces.append(uid)
                try:
                    return _build(project, op, ci, rows, res, False)
                except EditError as e:
                    rj.pieces.pop()
                    last_err = e
            raise last_err or EditError(_("edc.none_left", uid=uid, c=r.copies))
    elif kind == "remove":
        raw = action.get("indices")
        idxs = sorted({_int(i, 0, 10 ** 9) for i in raw}, reverse=True) if isinstance(raw, list) else \
            [_int(action.get("index", -1), -1, 10 ** 9)]
        for i in idxs:
            if not (0 <= i < len(r.pieces)):
                raise EditError(_("edc.no_piece", map=mi + 1, i=i + 1))
            r.pieces.pop(i)
    elif kind == "move":
        i = _int(action.get("index", -1), -1, 10 ** 9)
        if not (0 <= i < len(r.pieces)):
            raise EditError(_("edc.no_piece", map=mi + 1, i=i + 1))
        to = action.get("to", "end")
        n = len(r.pieces)
        j = {"start": 0, "end": n - 1, "left": max(0, i - 1), "right": min(n - 1, i + 1)}.get(to) if isinstance(to, str) else None
        if j is None:
            j = _int(to, 0, n - 1)
        r.pieces.insert(j, r.pieces.pop(i))
    elif kind == "transfer":
        i = _int(action.get("index", -1), -1, 10 ** 9)
        tj = _int(action.get("to_map", 0), 0, 10 ** 9) - 1
        if not (0 <= i < len(r.pieces)):
            raise EditError(_("edc.no_piece", map=mi + 1, i=i + 1))
        if not (0 <= tj < len(rows)):
            raise EditError(_("edc.no_map"))
        if rows[tj].copies != r.copies:
            raise EditError(_("edc.copies_differ", a=r.copies, b=rows[tj].copies))
        uid = r.pieces.pop(i)
        ti = action.get("to_index")
        rows[tj].pieces.insert(len(rows[tj].pieces) if ti is None else _int(ti, 0, len(rows[tj].pieces)), uid)
    else:
        raise EditError(_("edc.bad_action", a=str(kind)[:40]))
    return _build(project, op, ci, rows, res, False)
