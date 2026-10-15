"""(CN) Нестинговый раскрой — hisob-kitoblar (W16): kroy elementlari, nesting natijasini yig'ish, qoldiqlar, etiketka o'rni, narx, ombor
talabnomasi, MES. Optimizator — `cn_nest.py`, tekshiruv — `cn_validate.py`, qoldiq / etiketka geometriyasi — `cn_free.py`.

Detal o'lchami CS dagi kabi: `compute_sizes(...).saw` (pilniy o'lcham = zagotovka + pripusk; kromka qalinligi ayiriladi). Shakl — bog'langan
XNC konturi yoki shu o'lchamdagi to'rtburchak (`cn_geometry.part_shape`). Natija — `CuttingResult(kind="nest")`: CS bilan bir xil tuzilma
(kartalar, joylashuvlar, qoldiqlar), shuning uchun ИК/Ост hisobi, ombor, MES, «Исп. кол-во» umumiy kod bilan ishlaydi. Qo'shimcha:
joylashuvda burchak va kontur (`angle / outline / holes / label`), qoldiqda `in_part` (detal ichki kesimi).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..i18n import _
from ..models import (CNParams, CutMap, CuttingResult, Offcut, OpCostBase, Operation, Part, Placement, Project,
                      SheetRounding, StockSheet)
from . import cn_free, cn_messages  # noqa: F401
from . import cn_geometry as G
from . import cn_nest as N
from .calc import _account, _frac_up, edge_map, effective_qty, is_remnant_map, remnant_sheets_used, sheets_per_pack, total_qty
from .cn_validate import Poly
from .sizes import compute_sizes

MAX_NEST_ITEMS = 5000
COORD_DEC = 4                 # ko'rsatish uchun kontur koordinatalari yaxlitlanishi (joylashuv x, y — yaxlitlanmaydi)


def max_items() -> int:
    try:
        return max(1, int(os.getenv("MEBELIX_MAX_NEST_ITEMS", str(MAX_NEST_ITEMS))))
    except ValueError:
        return MAX_NEST_ITEMS


def ensure_cn(op: Operation) -> CNParams:
    if op.cn is None:
        op.cn = CNParams()
    return op.cn


def spacing_of(cn: CNParams) -> float:
    """Nesting va tekshiruv uchun detallar orasidagi talab etilgan masofa: asbob + qo'shimcha masofa + yoy yaqinlashtirish zaxirasi."""
    return cn.spacing + cn.arc_tol


# ───────────────────────── Kroy elementlari ─────────────────────────
@dataclass
class CnItems:
    parts: list[N.NestPart] = field(default_factory=list)
    shapes: dict[str, G.Shape] = field(default_factory=dict)
    need: dict[str, int] = field(default_factory=dict)
    grains: dict[str, bool] = field(default_factory=dict)
    by_pid: dict[str, Part] = field(default_factory=dict)
    bad: list[str] = field(default_factory=list)
    small: list[str] = field(default_factory=list)
    sizes: dict[str, tuple[float, float]] = field(default_factory=dict)


def saw_size(project: Project, part: Part, edges=None) -> tuple[float, float]:
    edges = edges if edges is not None else edge_map(project)
    s = compute_sizes(part, project.size_mode, edges, 0)
    return float(s.saw[0]), float(s.saw[1])


def build_items(project: Project, op: Operation, with_shapes: bool = True) -> CnItems:
    """Kroyga kiradigan detallar (ОК − МК), shakllari va ruxsat etilgan burchaklari."""
    cn = ensure_cn(op)
    edges = edge_map(project)
    out = CnItems()
    for part in op.parts:
        n = effective_qty(project, part)
        if n <= 0:
            continue
        if part.length <= 0 and part.width <= 0:           # 0×0 — to'ldirilmagan qator: jim o'tkazib yuboriladi
            continue
        L, W = saw_size(project, part, edges)
        out.by_pid[part.id] = part
        if part.length <= 0 or part.width <= 0 or L <= 0 or W <= 0:
            out.bad += [part.id] * n
            continue
        if cn.min_part_size > 0 and min(L, W) < cn.min_part_size - 1e-9:
            out.small += [part.id] * n
            continue
        out.sizes[part.id] = (L, W)
        out.need[part.id] = n
        out.grains[part.id] = bool(part.grain)
        if with_shapes:
            shape = G.part_shape(project, op, part, (L, W), cn.use_xnc_contours, cn.arc_tol)
            out.shapes[part.id] = shape
            out.parts.append(N.NestPart(part.id, part.uid, shape, n, N.allowed_angles(part.grain, cn.rot90, cn.rot_step, cn.use_grain)))
    return out


def input_rev(project: Project, op: Operation) -> str:
    """Hisob kirishining izi: detallar (o'lcham, soni, tekstura, bog'langan XNC), listlar, nesting parametrlari. Fon vazifasi tugaganda
    loyiha shu orada o'zgargan-o'zgarmaganini aniqlash uchun."""
    cn = ensure_cn(op)
    edges = edge_map(project)
    xnc = {o.id: o.xnc.model_dump_json() for o in project.operations if o.xnc is not None}
    d = dict(
        cn=cn.model_dump(exclude={"usage_m2", "multiplicity", "price", "op_price", "cost_by_sheets", "sheet_rounding",
                                  "est_fill_percent", "op_cost_base"}),
        mode=str(project.size_mode.value),
        parts=[[p.id, p.uid, saw_size(project, p, edges), effective_qty(project, p), p.grain,
                [hashlib.md5(xnc.get(x, "").encode()).hexdigest()[:8] for x in p.xnc_op_ids]] for p in op.parts],
        sheets=[[s.id, s.length, s.width, s.qty] for s in op.sheets])
    return hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ───────────────────────── Xarita yig'ish ─────────────────────────
def point_on_placement(shape: G.Shape, angle: float, x: float, y: float, pt) -> tuple[float, float]:
    o = G.orient_shape(shape, angle)
    c, s = G.rot_cs(angle)
    return c * pt[0] - s * pt[1] + o.ox + x, s * pt[0] + c * pt[1] + o.oy + y


def _rd(ring) -> list[list[float]]:
    return [[round(px, COORD_DEC), round(py, COORD_DEC)] for px, py in ring]


_LABEL_CACHE: dict = {}
_LABEL_CACHE_MAX = 4000


def label_for(shape: G.Shape, cn: CNParams) -> Optional[dict]:
    """Etiketka o'rni (detal koordinatalarida): `cn_free.find_label_spot`; shakl va etiketka o'lchami bo'yicha keshlanadi."""
    if cn.label_w <= 0 or cn.label_h <= 0:
        return None
    key = (hash(tuple((round(x, 2), round(y, 2)) for x, y in shape.outer)),
           hash(tuple(tuple((round(x, 2), round(y, 2)) for x, y in h) for h in shape.holes)), hash(repr(shape.marks or {})),
           cn.label_w, cn.label_h)
    got = _LABEL_CACHE.get(key)
    if got is None:
        if len(_LABEL_CACHE) > _LABEL_CACHE_MAX:
            _LABEL_CACHE.clear()
        got = _LABEL_CACHE[key] = cn_free.find_label_spot(shape, cn.label_w, cn.label_h)
    return got


@dataclass
class Spec:
    """Bitta joylashuv: detal, shakl, burchak va aylantirilgan shakl o'rovchi to'rtburchagining list koordinatalaridagi chap-yuqori burchagi."""
    part: Part
    shape: G.Shape
    angle: float
    x: float
    y: float


def make_placement(sp: Spec, label_local: Optional[dict]) -> tuple[Placement, G.Ring, list[G.Ring]]:
    """Joylashuv + list koordinatalaridagi poligonlar (tashqi, ichki)."""
    outer, holes, bw, bh = G.place_shape(sp.shape, sp.angle, sp.x, sp.y)
    ang = sp.angle % 360.0
    pl = Placement(part_id=sp.part.id, part_uid=sp.part.uid, x=sp.x, y=sp.y, length=bw, width=bh,
                   rotated=abs((ang % 180.0) - 90.0) < 1e-6, angle=ang, outline=_rd(outer), holes=[_rd(h) for h in holes])
    if label_local and label_local.get("label"):
        cx, cy, lw, lh, la = label_local["label"]
        px, py = point_on_placement(sp.shape, sp.angle, sp.x, sp.y, (cx, cy))
        pl.label = [round(px, COORD_DEC), round(py, COORD_DEC), round(lw, 3), round(lh, 3), round((la + ang) % 360.0, 3)]
    return pl, outer, holes


def map_signature(st: StockSheet, specs: list[Spec]) -> tuple:
    return (st.id, st.length, st.width, tuple((s.part.id, round(s.angle, 6), s.x, s.y) for s in specs))


def make_map(index: int, st: StockSheet, copies: int, specs: list[Spec], cn: CNParams, labels: dict,
             reuse_offcuts: Optional[list[Offcut]] = None, comment: str = "", done: int = 0) -> CutMap:
    """Karta: joylashuvlar (konturlar bilan), ko'rsatkichlar (LT, CT, F, AP, AM), qoldiqlar (`reuse_offcuts` berilsa — qayta hisoblanmaydi)."""
    pls: list[Placement] = []
    polys: list[Poly] = []
    area = per = 0.0
    cuts = 0
    for sp in specs:
        if sp.part.id not in labels:
            labels[sp.part.id] = label_for(sp.shape, cn)
        pl, outer, holes = make_placement(sp, labels[sp.part.id])
        pls.append(pl)
        polys.append(Poly(sp.part.uid, outer, holes))
        area += sp.shape.area
        per += sp.shape.perimeter
        cuts += 1 + len(sp.shape.holes)
    m = CutMap(index=index, sheet_id=st.id, sheet_length=st.length, sheet_width=st.width,
               is_remnant=bool(st.is_remnant or st.source_remnant_id), copies=max(1, int(copies)), placements=pls,
               parts_count=len(pls), cut_length_m=round(per / 1000, 4), cuts_count=cuts, parts_area_m2=round(area / 1e6, 4),
               sheet_area_m2=round(st.length * st.width / 1e6, 4), comment=comment, done_count=done)
    if reuse_offcuts is not None:
        m.offcuts = [o.model_copy() for o in reuse_offcuts]
    else:
        m.offcuts = remnants_of(polys, st, cn)
    return m


def remnants_of(polys: list[Poly], st: StockSheet, cn: CNParams) -> list[Offcut]:
    rects = cn_free.free_rectangles(polys, st.length, st.width, cn.margin, spacing_of(cn), cn.remnant_min_side1, cn.remnant_min_side2)
    out: list[Offcut] = []
    for fr in rects:
        x0, y0, x1, y1 = fr.raw
        out.append(Offcut(x=round(fr.x, 3), y=round(fr.y, 3), length=round(fr.w, 3), width=round(fr.h, 3), kind="remnant",
                          business=fr.w * fr.h / 1e6 >= cn.remnant_min_area - 1e-9,
                          raw_length=round(x1 - x0, 3), raw_width=round(y1 - y0, 3), in_part=fr.in_part))
    return out


def finish_result(res: CuttingResult) -> CuttingResult:
    """Jami ko'rsatkichlar (CS `_finish` kabi: F = detallar maydoni ÷ (list − деловой qoldiqlar)); qoldiqlar uzluksiz raqamlanadi."""
    n = 0
    for i, m in enumerate(res.maps, 1):
        m.index = i
        for o in m.offcuts:
            if o.kind == "remnant":
                n += 1
                o.number = n
        m.remnant_area_m2 = round(sum(o.length * o.width for o in m.offcuts if o.business) / 1e6, 4)
        denom = m.sheet_area_m2 - m.remnant_area_m2
        m.fill_percent = round(100 * m.parts_area_m2 / denom, 2) if denom > 0 else 0
    res.kind = "nest"
    res.total_sheets = sum(m.copies for m in res.maps)
    res.total_parts = sum(m.parts_count * m.copies for m in res.maps)
    res.total_cut_length_m = round(sum(m.cut_length_m * m.copies for m in res.maps), 3)
    res.total_cuts = sum(m.cuts_count * m.copies for m in res.maps)
    res.parts_area_m2 = round(sum(m.parts_area_m2 * m.copies for m in res.maps), 4)
    res.material_area_m2 = round(sum(m.sheet_area_m2 * m.copies for m in res.maps), 4)
    res.remnant_area_m2 = round(sum(m.remnant_area_m2 * m.copies for m in res.maps), 4)
    res.material_qty_m2 = round(res.material_area_m2 - res.remnant_area_m2, 4)
    denom = res.material_area_m2 - res.remnant_area_m2
    res.total_fill_percent = round(100 * res.parts_area_m2 / denom, 2) if denom > 0 else 0
    res.remnants = [o for m in res.maps for o in m.offcuts if o.kind == "remnant" for _c in range(m.copies)]
    return res


def build_result(op: Operation, ci: CnItems, outcome: N.NestOutcome, cn: CNParams) -> CuttingResult:
    """`NestOutcome` → `CuttingResult(kind="nest")`."""
    stock = {s.id: s for s in op.sheets}
    labels: dict = {}
    maps: list[CutMap] = []
    for ly in outcome.layouts:
        sh = outcome_sheet(op, ly.sheet)
        st = stock[sh]
        specs = [Spec(ci.by_pid[ci.parts[it.part].key], ci.parts[it.part].shape, it.angle, it.x, it.y) for it in ly.items]
        maps.append(make_map(len(maps) + 1, st, ly.copies, specs, cn, labels))
    res = CuttingResult(maps=maps, kind="nest")
    res.unplaced = [ci.parts[pi].key for pi in outcome.unplaced]
    finish_result(res)
    return res


def outcome_sheet(op: Operation, idx: int) -> str:
    return op.sheets[idx].id


# ───────────────────────── Kroy ─────────────────────────
def run_nesting(project: Project, op: Operation, quality: Optional[str] = None,
                progress: Optional[Callable[[float, str], None]] = None, cancel: Optional[Callable[[], bool]] = None) -> Operation:
    """Раскроить (CN): shakllar → nesting → natija (qoldiqlar, etiketka o'rni, ИК/Ост, narx). Natija `validate_cn` dan o'tkaziladi
    (o'tmasa — ichki xato: nesting noto'g'ri joylagan bo'lardi)."""
    from .cn_validate import validate_cn
    t0 = time.monotonic()
    cn = ensure_cn(op)
    ci = build_items(project, op)
    sheets = [N.NestSheet(s.id, s.length, s.width, s.qty) for s in op.sheets]
    prm = N.NestParams(spacing=spacing_of(cn), margin=cn.margin, quality=quality or cn.quality, time_limit=cn.time_limit_s,
                       order=cn.sort_mode)
    outcome = N.nest(ci.parts, sheets, prm, progress, cancel)
    res = build_result(op, ci, outcome, cn)
    warns = _warnings(project, op, ci, outcome, res, prm)
    errs = validate_cn(res, ci.shapes, ci.need, ci.grains, op.sheets, cn)
    if errs:                                     # mustaqil tekshiruv: bunday natija foydalanuvchiga ko'rsatilmaydi
        raise RuntimeError("; ".join(errs[:3]))
    res.warnings = warns
    res.unplaced = list(res.unplaced) + ci.small + ci.bad
    res.nest = dict(outcome.info, input_rev=input_rev(project, op), spacing=round(spacing_of(cn), 4), margin=cn.margin)
    res.elapsed_s = round(time.monotonic() - t0, 2)
    op.result = res
    _account(project, op)
    cn_cost(project, op)
    return op


def _warnings(project: Project, op: Operation, ci: CnItems, outcome: N.NestOutcome, res: CuttingResult, prm: N.NestParams) -> list[str]:
    cn = ensure_cn(op)
    w: list[str] = []
    seen_shape_warns: set = set()
    for pid, sh in ci.shapes.items():
        for key, kw in sh.warns:
            k = (key, tuple(sorted(kw.items())))
            if k not in seen_shape_warns:
                seen_shape_warns.add(k)
                w.append(_(key, **kw))
    if ci.small:
        w.append(_("cn.w_small", n=len(ci.small), mm=f"{cn.min_part_size:g}"))
    by_id = {p.id: p for p in op.parts}
    for pid in dict.fromkeys(ci.bad):
        part = by_id.get(pid)
        if part is not None:
            L, W = saw_size(project, part)
            w.append(_("cn.w_bad", uid=part.uid, l=f"{L:g}", w=f"{W:g}"))
    if outcome.unplaced:
        big: list[int] = []
        stock_n = 0
        for pi in dict.fromkeys(outcome.unplaced):
            part = ci.parts[pi]
            fits = False
            for s in op.sheets:
                Lu, Wu = s.length - 2 * cn.margin, s.width - 2 * cn.margin
                for a in part.angles:
                    o = G.orient_shape(part.shape, a)
                    if o.bw <= Lu + 1e-9 and o.bh <= Wu + 1e-9:
                        fits = True
                        break
                if fits:
                    break
            n = sum(1 for x in outcome.unplaced if x == pi)
            if fits:
                stock_n += n
            else:
                bw, bh = part.shape.bbox_size
                w.append(_("cn.w_too_big", uid=part.uid, w=f"{bw:g}", h=f"{bh:g}", margin=f"{cn.margin:g}"))
        if stock_n:
            w.append(_("cn.w_stock", n=stock_n))
    if outcome.info.get("timed_out"):
        w.append(_("cn.w_time", s=f"{(cn.time_limit_s or N.QUALITY[prm.quality]['time']):g}"))
    return w


# ───────────────────────── Narx ─────────────────────────
def _new_maps(op: Operation) -> list:
    return [m for m in (op.result.maps if op.result else []) if not is_remnant_map(op, m)]


def _new_sheet_area(op: Operation) -> float:
    maps = _new_maps(op)
    n = sum(m.copies for m in maps)
    if n:
        return sum(m.sheet_area_m2 * m.copies for m in maps) / n
    sh = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None) or (op.sheets[0] if op.sheets else None)
    return sh.length * sh.width / 1e6 if sh else 0.0


def material_prices(op: Operation) -> dict:
    """«по листам» ✓ — price 1 list narxi, ☐ — 1 m² narxi; ikkalasi ham qaytadi (ombor qoldiqlari m² narxida)."""
    cn = ensure_cn(op)
    area = _new_sheet_area(op)
    if cn.cost_by_sheets:
        return dict(sheet=cn.price, m2=(cn.price / area) if area else 0.0)
    return dict(sheet=round(cn.price * area, 2), m2=cn.price)


def rounded_sheet_count(op: Operation) -> float:
    """Yangi listlar soni «Округление — Листы» qoidasi bilan (CS dagi kabi: oxirgi bitta nusxali karta band qismi bo'yicha)."""
    cn = ensure_cn(op)
    maps = _new_maps(op)
    if not maps:
        return 0
    full = sum(m.copies for m in maps)
    rule = cn.sheet_rounding
    last = maps[-1]
    if rule == SheetRounding.WHOLE or last.copies != 1 or not last.placements or not last.sheet_length or not last.sheet_width:
        return full
    k = int(rule.value[1])
    fl = max(p.x + p.length for p in last.placements) / last.sheet_length
    fw = max(p.y + p.width for p in last.placements) / last.sheet_width
    if rule.value[0] == "3":
        frac = _frac_up(fl, k)
    elif rule.value[0] == "2":
        frac = _frac_up(fw, k)
    else:
        frac = min(_frac_up(fl, k), _frac_up(fw, k))
    return full - 1 + frac


def parts_rect_stats(project: Project, op: Operation) -> tuple[float, float]:
    """Kroygacha taxmin uchun: Σ to'rtburchak maydoni (m²) va perimetri (m) — shakllar hisoblanmaydi (har saqlashda chaqiriladi)."""
    edges = edge_map(project)
    area = per = 0.0
    for p in op.parts:
        L, W = saw_size(project, p, edges)
        if L > 0 and W > 0:
            q = effective_qty(project, p)
            area += L * W / 1e6 * q
            per += 2 * (L + W) / 1000 * q
    return area, per


def cn_cost(project: Project, op: Operation) -> dict:
    """Material va operatsiya narxi (CS bilan bir xil qoidalar). Kroygacha — taxminiy (`estimated`): Σ maydon × (2 − p/100)."""
    cn = ensure_cn(op)
    res = op.result
    info: dict = {}
    area_est, per_est = parts_rect_stats(project, op)
    if res and res.maps:
        pr = material_prices(op)
        rem = remnant_sheets_used(op)
        rem_area = sum(r["area_m2"] for r in rem)
        new_maps = _new_maps(op)
        new_area = sum(m.sheet_area_m2 * m.copies for m in new_maps)
        new_business = sum(m.remnant_area_m2 * m.copies for m in new_maps)
        qty_m2 = max(0.0, new_area - new_business)
        sheets = rounded_sheet_count(op)
        op.cost_material = (sheets * pr["sheet"] if cn.cost_by_sheets else qty_m2 * pr["m2"]) + rem_area * pr["m2"]
        consumption = res.material_qty_m2 or round(res.material_area_m2 - res.remnant_area_m2, 4)
        info.update(estimated=False, sheets=sheets, material_qty_m2=round(consumption, 4), sheets_total=res.total_sheets,
                    sheet_area_m2=round(_new_sheet_area(op), 4))
        parts_area = res.parts_area_m2
        outer_per = sum(sum(_ring_len(pl.outline) for pl in m.placements) * m.copies for m in res.maps) / 1000
        cut = res.total_cut_length_m
    else:
        consumption = area_est * (2 - cn.est_fill_percent / 100)
        sh0 = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None) or (op.sheets[0] if op.sheets else None)
        sa = sh0.length * sh0.width / 1e6 if sh0 else 0.0
        sheets = math.ceil(consumption / sa - 1e-9) if sa else 0
        op.cost_material = (sheets if cn.cost_by_sheets else consumption) * cn.price
        info.update(estimated=True, sheets=sheets, material_qty_m2=round(consumption, 4), sheets_total=sheets, sheet_area_m2=round(sa, 4))
        parts_area, outer_per, cut = area_est, per_est, per_est
    info["parts_area_m2"] = round(parts_area, 4)
    base = {OpCostBase.CUT_LENGTH: cut, OpCostBase.PART_PERIMETER: outer_per, OpCostBase.PART_AREA: parts_area,
            OpCostBase.MATERIAL_AREA: consumption}[cn.op_cost_base]
    op.cost_operation = round(base * cn.op_price, 2)
    op.cost_material = round(op.cost_material, 2)
    cn.usage_m2 = round(consumption, 4)
    cn.multiplicity = sheets_per_pack(op)
    info.update(op_base=round(base, 4), cut_length_m=round(cut, 3), multiplicity=cn.multiplicity, cost_material=op.cost_material,
                cost_operation=op.cost_operation)
    return info


def _ring_len(ring) -> float:
    if not ring:
        return 0.0
    return sum(math.hypot(ring[(i + 1) % len(ring)][0] - ring[i][0], ring[(i + 1) % len(ring)][1] - ring[i][1]) for i in range(len(ring)))


# ───────────────────────── Ombor talabnomasi ─────────────────────────
def cn_warehouse_rows(project: Project, op: Operation) -> list[dict]:
    """«Требование на склад»: yangi listlar (yaxlitlangan) va ombordagi qoldiqlar alohida qatorlarda (CS bilan bir xil)."""
    res = op.result
    sheets = rounded_sheet_count(op) if res else 0
    cut = res.total_cut_length_m if res else 0
    pr = material_prices(op)
    rem = remnant_sheets_used(op)
    rem_sum = sum(r["area_m2"] for r in rem) * pr["m2"]
    out = [dict(op_id=op.id, type="CN", code=op.code, name=op.name, unit=_("unit_sheets"), unit_code="sheets", qty=round(sheets, 3),
                cut_m=round(cut, 2), note=_("note_cut", m=round(cut, 2)), price=pr["sheet"], sum=round(max(0.0, op.cost_material - rem_sum), 2))]
    for r in rem:
        rid = r["remnant_id"]
        nm = f"{op.name} — " + (_("remnant_sheet", id=rid) if rid else _("remnant_word")) + f" {r['length']:g}×{r['width']:g}"
        out.append(dict(op_id=op.id, type="CN", code=op.code, name=nm, unit=_("unit_pcs"), unit_code="pcs", qty=r["qty"], remnant=True,
                        remnant_id=rid, area_m2=r["area_m2"], price=round(pr["m2"], 2), sum=round(r["area_m2"] * pr["m2"], 2),
                        note=f"{r['area_m2']} m²"))
    return out


# ───────────────────────── MES ─────────────────────────
def mes_payload(project: Project, op: Operation) -> dict:
    """MES uchun CN natijasi: detallar, kartalar (qisqa: joylashuvlar burchak va o'rni bilan), qoldiqlar."""
    cn = ensure_cn(op)
    res = op.result
    d: dict = dict(kind="nest", thickness=cn.thickness, tool_diameter=cn.tool_diameter, spacing=round(spacing_of(cn), 4),
                   parts=[dict(uid=pt.uid, code=pt.code, name=pt.name, length=pt.length, width=pt.width, qty=total_qty(project, pt),
                               used=pt.used_qty, left=pt.left_qty) for pt in op.parts])
    if res:
        d.update(sheets=res.total_sheets, fill_percent=res.total_fill_percent, cut_length_m=res.total_cut_length_m,
                 material_area_m2=res.material_area_m2, parts_area_m2=res.parts_area_m2, material_qty_m2=res.material_qty_m2,
                 remnants=[dict(length=o.raw_length or o.length, width=o.raw_width or o.width, business=o.business, in_part=o.in_part)
                           for o in res.remnants],
                 maps=[dict(index=m.index, copies=m.copies, done=m.done_count, sheet=[m.sheet_length, m.sheet_width], fill=m.fill_percent,
                            parts=[dict(uid=pl.part_uid, x=pl.x, y=pl.y, angle=pl.angle) for pl in m.placements]) for m in res.maps])
    return d


# ───────────────────────── Parametrlar o'zgarishi ─────────────────────────
# kroy natijasini eskirtirmaydigan CN parametrlari (narx / keyingi kroy strategiyasi / hisoblangan). Qoldiq qoidalari va etiketka o'lchami
# natijadagi qoldiq / etiketka o'rnini o'zgartiradi — shuning uchun CS dagi kabi natijani eskirtiradi.
CN_NON_CUT = frozenset({"quality", "time_limit_s", "thickness", "price", "cost_by_sheets", "sheet_rounding", "est_fill_percent",
                        "op_cost_base", "op_price", "usage_m2", "multiplicity"})


def cn_params_stale(old: Operation, new: Operation) -> bool:
    """Parametr o'zgarishi mavjud nesting natijasini eskirtiradimi (asbob, masofalar, burilish, tekstura, shakl manbai, qoldiq qoidalari …)."""
    a, b = old.cn, new.cn
    if (a is None) != (b is None):
        return True
    return bool(a and any(getattr(a, f) != getattr(b, f) for f in CNParams.model_fields if f not in CN_NON_CUT))


def new_cn_params(defaults: dict, item=None) -> CNParams:
    """Yangi CN operatsiyasi: `cn_defaults` + katalog tovari (qalinlik, narx)."""
    p = CNParams.model_validate({k: v for k, v in (defaults or {}).items() if k not in ("usage_m2", "multiplicity")})
    if item is not None:
        p.thickness = item.thickness or p.thickness
        p.price = item.price or p.price
    return p


def default_sheet(item=None, app_cfg: Optional[dict] = None) -> tuple[float, float]:
    cfg = app_cfg or {}
    L, W = cfg.get("default_sheet_length", 2750), cfg.get("default_sheet_width", 1830)
    if item is not None:
        L, W = item.length or L, item.width or W
    return float(L), float(W)


# ───────────────────────── «Детали» ma'lumoti (shakllar) ─────────────────────────
def shapes_info(project: Project, op: Operation) -> dict:
    """UI «Детали» uchun: har detalning shakli (tur, maydon, perimetr, o'rovchi o'lcham, ichki kesimlar soni, kontur), ogohlantirishlar va
    etiketka o'rni; hech narsa saqlanmaydi."""
    cn = ensure_cn(op)
    ci = build_items(project, op)
    rows = []
    for part in op.parts:
        sh = ci.shapes.get(part.id)
        if sh is None:
            continue
        bw, bh = sh.bbox_size
        spot = label_for(sh, cn)
        rows.append(dict(id=part.id, uid=part.uid, kind="rect" if sh.is_rect else "contour", area_mm2=round(sh.area, 2),
                         perimeter_mm=round(sh.perimeter, 2), width=round(bw, 3), height=round(bh, 3), holes=len(sh.holes),
                         points=sh.n_points, outline=_rd(sh.outer), hole_rings=[_rd(h) for h in sh.holes],
                         label=(spot.get("label") if spot else None), label_free=(
                             [round(spot[k], 2) for k in ("x", "y", "w", "h")] if spot else None),
                         label_fits=bool(spot and spot.get("fits")),
                         warnings=[_(k, **kw) for k, kw in sh.warns]))
    return dict(parts=rows, spacing=round(spacing_of(cn), 4), margin=cn.margin, bad=len(ci.bad), small=len(ci.small))
