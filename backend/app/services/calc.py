"""Hisob-kitoblar: kroyni ishga tushirish, kromka, narx, ombor talabnomasi."""
from __future__ import annotations

import math
import time
from collections import Counter
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

from ..i18n import _
from ..models import (CSCutParams, CSMaterialParams, ELParams, FirstCutDir, GRParams, OpCostBase, OpType,
                      Operation, Part, Project, SheetRounding, SPParams)
from . import product_program                                                      # (W12) mahsulot «Программа»
from .o_ops import o_cost, o_warehouse_rows, prune_o_owners, product_shares as o_product_shares   # (O) Комплектация
from .optimizer import Item, _finish, optimize
from .sizes import compute_sizes
from .sp_ops import material_dims, part_sides, prune_surface_refs                  # (SP) Обработка поверхности


# ───────────────────────── Yordamchi ─────────────────────────
def edge_map(project: Project) -> dict[str, ELParams]:
    return {op.id: op.el for op in project.operations if op.type == OpType.EL and op.el}


def product_qty(project: Project, part: Part) -> int:
    if not part.product_id:
        return 1
    for pr in project.products:
        if pr.id == part.product_id:
            return pr.qty
    return 1


def total_qty(project: Project, part: Part) -> int:
    """ОК = (detal soni) × (mahsulot soni)."""
    return part.qty * product_qty(project, part)


def effective_qty(project: Project, part: Part) -> int:
    """Kroyga / ishlovga kiradigan soni: ОК − МК (МК — omborda tayyor detallar)."""
    return max(0, total_qty(project, part) - max(0, part.minus_qty or 0))


def op_part(op: Operation, part: Part) -> Part:
    """(CL) detalning eni — polosa eni (`op.cl.width`): CL da `Part.width` 0 saqlanadi, kromka / paz / maydon hisobida esa polosa eni
    olinadi (CL-038: aks holda ОЛ/ОП kromka metri 0 chiqadi). Boshqa operatsiyalarda — detalning o'zi."""
    if op.type == OpType.CL:
        from ..models import CL_DEFAULTS
        return part.model_copy(update={"width": op.cl.width if op.cl else CL_DEFAULTS["width"]})
    return part


def round_code(value: float, code: int) -> float:
    """Yaxlitlash kodi (GibLab bilan bir xil ma'no): o'nlik xonalar = code // 10, rejim = code % 10
    (0 — yaqiniga, 1 — kattaga ⌈⌉, 2 — kichikka ⌊⌋). Masalan 20 — [0.00] yaqiniga, 11 — ⌈0.0⌉."""
    try:
        decimals, mode = divmod(int(code), 10)
        decimals = max(0, min(6, decimals))
        q = Decimal(1).scaleb(-decimals)
        rnd = {0: ROUND_HALF_UP, 1: ROUND_CEILING, 2: ROUND_FLOOR}.get(mode, ROUND_HALF_UP)
        return float(Decimal(repr(float(value))).quantize(q, rounding=rnd))
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        return value


# ───────────────────────── CS: kroy ─────────────────────────
def _items_for(project: Project, op: Operation, cut: CSCutParams, only: Optional[dict[str, int]] = None,
               small: Optional[list[str]] = None, bad: Optional[list[str]] = None) -> list[Item]:
    """Kroy elementlari (pilniy o'lcham, ОК − МК nusxa). small berilsa — «Мин. размер детали» dan kichik
    detallar kroyga kiritilmaydi va ularning id lari shu ro'yxatga yoziladi (ogohlantirish uchun).
    bad berilsa — ishchi o'lchami 0 yoki manfiy bo'lib qolgan detallar (bir tomoni 0; kromka qalinligi detaldan katta
    va h.k.) ham shunday yoziladi; uzunligi VA eni 0 bo'lgan (to'ldirilmagan, qoralama) qator esa jim o'tkazib yuboriladi."""
    edges = edge_map(project)
    mat = op.cs_material or CSMaterialParams()
    min_side = mat.min_part_size or 0
    items: list[Item] = []
    for part in op.parts:
        n = effective_qty(project, part) if only is None else only.get(part.id, 0)
        if n <= 0:
            continue
        if part.length <= 0 and part.width <= 0:       # 0×0 — to'ldirilmagan (bo'sh) qator: kroyga kirmaydi (jim)
            continue
        s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
        # bir tomoni 0 yoki kromka/prifugovka ayirilgach ≤ 0: detal jimgina yo'qolmasin — «bad» ro'yxatida
        if part.length <= 0 or part.width <= 0 or s.saw[0] <= 0 or s.saw[1] <= 0:
            if bad is not None:
                bad += [part.id] * n
            continue
        if small is not None and min_side > 0 and min(s.saw) < min_side - 1e-9:
            small += [part.id] * n
            continue
        can_rotate = not (cut.use_grain and part.grain)
        items += [Item(part.id, part.uid, s.saw[0], s.saw[1], can_rotate) for _i in range(n)]
    return items


def groups_for(op: Operation) -> dict[str, tuple[int, int, str]]:
    """«Группировка в блок»: part_id → (min, max, 'l' | 'w'). 0 — cheklanmagan (min ≥ 2)."""
    out = {}
    for p in op.parts:
        if p.group_by in ("length", "width"):
            out[p.id] = (max(2, p.group_min or 0), max(0, p.group_max or 0), "l" if p.group_by == "length" else "w")
    return out


def _account(project: Project, op: Operation) -> None:
    """ИК / Ост va ishlatilgan listlar sonini natijadan qayta hisoblash."""
    res = op.result
    placed: dict[str, int] = {}
    if res:
        for m in res.maps:
            for pl in m.placements:
                placed[pl.part_id] = placed.get(pl.part_id, 0) + m.copies
    for part in op.parts:
        tq = effective_qty(project, part)            # ИК + Ост = ОК − МК
        part.used_qty = min(tq, placed.get(part.id, 0))
        part.left_qty = tq - part.used_qty
    for sh in op.sheets:
        sh.used_qty = sum(m.copies for m in res.maps if m.sheet_id == sh.id) if res else 0
    if res:
        _packets(op, res)


def sheets_per_pack(op: Operation) -> int:
    """Кратность (paketda birga kesiladigan listlar) = ⌊Высота пакета / material qalinligi⌋, kamida 1."""
    if op.type == OpType.CL:                       # (CL) paket balandligi va qalinlik — CLParams da
        pack, thick = (op.cl.pack_height, op.cl.thickness) if op.cl else (0, 0)
    else:
        cut = op.cs_cut or CSCutParams()
        pack, thick = cut.pack_height, (op.cs_material.thickness if op.cs_material else 0) or 0
    n = int((pack + 1e-9) // thick) if pack and thick > 0 else 1
    return max(1, n)


def _packets(op: Operation, res) -> None:
    spp = sheets_per_pack(op)
    res.sheets_per_pack = spp
    for m in res.maps:
        m.packs = math.ceil(m.copies / spp) if m.copies > 0 else 0
    res.total_packs = sum(m.packs for m in res.maps)


def _from_remnant_first(project: Project, op: Operation, cut: CSCutParams, mat: CSMaterialParams, quality, first_cut,
                        fill_free: bool) -> bool:
    """«Из остатка» belgili detallar (2026-10-24, foydalanuvchi talabi): avval FAQAT shu detallar ro'yxatdagi soni cheklangan
    listlarga (qoldiqlar — fayldan / ombordan) kesiladi, keyin qolgan hamma detal oddiy «До кроить» qoidasi bilan (qoldiqdagi
    bo'sh joy, so'ng yangi listlar). Qoldiqqa sig'magan belgili detallar — ogohlantirish, oddiy qoida bilan joylanadi.
    Belgili detal yoki cheklangan list bo'lmasa — False (oddiy kroy)."""
    flagged = {pt.id: effective_qty(project, pt) for pt in op.parts if pt.from_remnant and effective_qty(project, pt) > 0}
    lim = [sh for sh in op.sheets if sh.qty < 10000]
    if not flagged or not lim:
        return False
    small: list[str] = []
    bad: list[str] = []
    first = optimize(_items_for(project, op, cut, flagged, small, bad), lim, cut, mat, groups=groups_for(op))
    if not first.maps:
        return False
    miss = len(first.unplaced)
    first.unplaced = []
    op.result = _finish(first, mat)
    run_cutting(project, op, only_remaining=True, first_cut=first_cut, quality=quality, fill_free=fill_free)
    if op.result is not None:            # kartalar tartibi: butun listlar avval, qoldiqlar oxirida (umumiy qoida)
        lim_ids = {sh.id for sh in lim}
        op.result.maps.sort(key=lambda m: m.sheet_id in lim_ids)
        for i, m in enumerate(op.result.maps, 1):
            m.index = i
    if miss and op.result is not None:
        op.result.warnings = list(op.result.warnings) + [_("cut_from_remnant_miss", n=miss)]
    return True


def run_cutting(project: Project, op: Operation, only_remaining: bool = False,
                first_cut: Optional[FirstCutDir] = None, quality: Optional[str] = None, fill_free: bool = True) -> Operation:
    """Раскроить. only_remaining=True — «До кроить»: faqat kroyga kirmagan detallar, mavjud kartalarga qo'shiladi."""
    assert op.type == OpType.CS
    cut = (op.cs_cut or CSCutParams()).model_copy()
    if first_cut is not None:
        cut.first_cut = first_cut
    if quality:
        cut.quality = quality
    mat = op.cs_material or CSMaterialParams()
    t0 = time.monotonic()
    if only_remaining and op.result and op.result.maps:
        _account(project, op)
        left = {p.id: p.left_qty for p in op.parts if p.left_qty > 0}
        if not left:
            return op
        stock = []
        for sh in op.sheets:
            free = sh.qty - sh.used_qty if sh.qty < 10000 else sh.qty
            if free > 0:
                stock.append(sh.model_copy(update={"qty": free}))
        small: list[str] = []
        bad: list[str] = []
        # onlayn tizimdagidek: avval mavjud kartalarning bo'sh joylari (joylangan detallar o'z joyida), keyin yangi listlar
        from .cut_rest import fill_existing
        old, left = fill_existing(project, op, op.result, left, cut) if fill_free else (op.result, left)
        if not left:
            res = _finish(old, mat)
            res.elapsed_s = round(time.monotonic() - t0, 2)
            op.result = res
            _account(project, op)
            cs_cost(project, op)
            return op
        add = optimize(_items_for(project, op, cut, left, small, bad), stock, cut, mat, groups=groups_for(op))
        _small_warning(add, small, mat)
        _bad_warning(add, bad, project, op)
        start = len(old.maps)
        for i, m in enumerate(add.maps, 1):
            m.index = start + i
        old.maps += add.maps
        old.unplaced = add.unplaced
        old.warnings = add.warnings
        res = _finish(old, mat)
    elif _from_remnant_first(project, op, cut, mat, quality, first_cut, fill_free):
        return op
    else:
        small = []
        bad = []
        items = _items_for(project, op, cut, small=small, bad=bad)
        res = optimize(items, op.sheets, cut, mat, groups=groups_for(op))
        _oversize_warning(res, items, op.sheets, cut)
        _small_warning(res, small, mat)
        _bad_warning(res, bad, project, op)
    res.elapsed_s = round(time.monotonic() - t0, 2)
    op.result = res
    _account(project, op)
    cs_cost(project, op)
    return op


def _small_warning(res, small: list[str], mat: CSMaterialParams) -> None:
    if small:
        res.unplaced = list(res.unplaced) + small
        res.warnings = list(res.warnings) + [_("warn_small_parts", n=len(small), mm=f"{mat.min_part_size:g}")]


def _oversize_warning(res, items, sheets: list[StockSheet], cut: CSCutParams) -> None:
    """Listdan (foydali zonadan) katta detallar: kroyga kirmaydi — avval jimgina «sig'magan» bo'lib qolardi (korpus:
    3120 kuxniya — 2845×600 detal 2750 li listda; avvalgi tizim ham joylamagan, lekin xodim sababini ko'rishi kerak)."""
    if not res.unplaced:
        return
    from .optimizer import _zone
    zones = []
    for st in sheets:
        z = _zone(st, cut)
        if z.UL > 0 and z.UW > 0:
            zones.append((z.UL, z.UW))
    if not zones:
        return
    by: dict[str, object] = {}
    for it in items:
        by.setdefault(it.part_id, it)
    # soni — dona (nusxalar) bo'yicha, «Мин. размер детали» ogohlantirishidagi kabi; tekstura sababli (burilsa sig'adigan)
    # detallar alohida aytiladi — «listdan katta» deyilsa xodim adashadi (masalan 70×2500 tekstura bo'ylab, list 2750×1830)
    n = n_grain = 0
    pieces = Counter(res.unplaced)
    for pid, k in pieces.items():
        it = by.get(pid)
        if it is None:
            continue
        fits = any((it.l <= L + 1e-6 and it.w <= W + 1e-6) or (it.can_rotate and it.w <= L + 1e-6 and it.l <= W + 1e-6)
                   for L, W in zones)
        if fits:
            continue
        if not it.can_rotate and any(it.w <= L + 1e-6 and it.l <= W + 1e-6 for L, W in zones):
            n_grain += k
        else:
            n += k
    if n:
        res.warnings = list(res.warnings) + [_("parts_exceed_sheet", n=n)]
    if n_grain:
        res.warnings = list(res.warnings) + [_("parts_exceed_grain", n=n_grain)]


def _bad_warning(res, bad: list[str], project: Project, op: Operation) -> None:
    """O'lchami kromka/prifugovka ayirilgach ≤ 0 bo'lgan detallar: kroyga kirmaydi, «sig'magan» (unplaced) ro'yxatiga
    tushadi va ogohlantirishda detal № bilan ko'rsatiladi (jimgina yo'qolmaydi)."""
    if not bad:
        return
    cut = op.cs_cut or CSCutParams()
    edges = edge_map(project)
    by_id = {p.id: p for p in op.parts}
    msgs = []
    for pid in dict.fromkeys(bad):                      # tartib saqlanadi, takrorsiz
        part = by_id.get(pid)
        if part is None:
            continue
        s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
        msgs.append(_("warn_bad_size", uid=part.uid, l=f"{s.saw[0]:g}", w=f"{s.saw[1]:g}"))
    res.unplaced = list(res.unplaced) + bad
    res.warnings = list(res.warnings) + msgs


def cutting_variants(project: Project, op: Operation) -> list[dict]:
    """SketchCut g'oyasi: uch variant (optimal / 1-kesish uzunlik bo'yicha / eni bo'yicha) — xodim solishtirib tanlaydi."""
    from .optimizer import time_budget
    out = []
    base = (op.cs_cut or CSCutParams()).model_copy()
    mat = op.cs_material or CSMaterialParams()
    for key, fc in (("optimal", FirstCutDir.ANY), ("length", FirstCutDir.LENGTH), ("width", FirstCutDir.WIDTH)):
        cut = base.model_copy(update={"first_cut": fc})
        t0 = time.monotonic()
        small: list[str] = []
        bad: list[str] = []
        items = _items_for(project, op, cut, small=small, bad=bad)
        tl = time_budget(len(items), cut.quality) * (1.0 if key == "optimal" else 0.6)
        res = optimize(items, op.sheets, cut, mat, time_limit=tl, groups=groups_for(op))
        _small_warning(res, small, mat)
        _bad_warning(res, bad, project, op)
        res.variant = key
        res.elapsed_s = round(time.monotonic() - t0, 2)
        out.append(dict(variant=key, sheets=res.total_sheets, fill=res.total_fill_percent,
                        cut_m=res.total_cut_length_m, cuts=res.total_cuts, unplaced=len(res.unplaced),
                        remnant_m2=res.remnant_area_m2, result=res))
    return out


def is_remnant_map(op: Operation, m) -> bool:
    """Karta ombordagi qoldiqdan kesilganmi (yangi list emas)."""
    if m.is_remnant:
        return True
    sh = next((x for x in op.sheets if x.id == m.sheet_id), None)
    return bool(sh and (sh.is_remnant or sh.source_remnant_id))


def remnant_sheets_used(op: Operation) -> list[dict]:
    """Kroyda ishlatilgan ombor qoldiqlari (talabnoma uchun): qoldiq №, o'lcham, soni, maydon."""
    res = op.result
    if not res:
        return []
    sheets = {x.id: x for x in op.sheets}
    agg: dict[tuple, dict] = {}
    for m in res.maps:
        if not is_remnant_map(op, m):
            continue
        sh = sheets.get(m.sheet_id)
        rid = sh.source_remnant_id if sh else None
        k = (rid, m.sheet_length, m.sheet_width)
        r = agg.setdefault(k, dict(remnant_id=rid, length=m.sheet_length, width=m.sheet_width, qty=0, area_m2=0.0))
        r["qty"] += m.copies
        r["area_m2"] = round(r["area_m2"] + m.sheet_area_m2 * m.copies, 4)
    return list(agg.values())


def _new_maps(op: Operation) -> list:
    return [m for m in (op.result.maps if op.result else []) if not is_remnant_map(op, m)]


def _frac_up(x: float, k: int) -> float:
    return min(1.0, math.ceil(max(0.0, x) * k - 1e-9) / k)


def _rounded_sheet_count(op: Operation) -> float:
    """Yangi listlar soni «Округление - Листы» qoidasi bilan (ombor qoldiqlari alohida hisoblanadi).
    Oxirgi bitta nusxali kartaning band qismi: «по длине» — max(x + uzunlik) / L, «по ширине» —
    max(y + en) / W, «любое» — ikkisining kichigi; ulush 1/k ga yuqoriga yaxlitlanadi."""
    mat = op.cs_material or CSMaterialParams()
    maps = _new_maps(op)
    if not maps:
        return 0
    full = sum(m.copies for m in maps)
    rule = mat.sheet_rounding
    if rule == SheetRounding.WHOLE:
        return full
    last = maps[-1]
    if last.copies != 1 or not last.placements or not last.sheet_length or not last.sheet_width:
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


def _new_sheet_area(op: Operation) -> float:
    """Yangi list maydoni, m² (kroydagi yangi kartalar bo'yicha o'rtacha, bo'lmasa ro'yxatdagi birinchi list)."""
    maps = _new_maps(op)
    n = sum(m.copies for m in maps)
    if n:
        return sum(m.sheet_area_m2 * m.copies for m in maps) / n
    sh = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None)
    return sh.length * sh.width / 1e6 if sh else 0.0


def material_prices(op: Operation) -> dict:
    """Narx ma'nosi «Расчет стоимости по листам» ga bog'liq: ✓ — price 1 list narxi, ☐ — 1 m² narxi.
    Ikkalasi ham qaytadi (ombor qoldiqlari m² narxida hisoblanadi)."""
    mat = op.cs_material or CSMaterialParams()
    area = _new_sheet_area(op)
    if mat.cost_by_sheets:
        return dict(sheet=mat.price, m2=(mat.price / area) if area else 0.0)
    return dict(sheet=round(mat.price * area, 2), m2=mat.price)


def parts_area_m2(project: Project, op: Operation) -> float:
    """Detallar maydoni (pilniy = zagotovka + pripusk o'lchami bo'yicha, ОК − МК nusxa), m²."""
    cut = op.cs_cut or CSCutParams()
    edges = edge_map(project)
    area = 0.0
    for part in op.parts:
        s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
        if s.saw[0] > 0 and s.saw[1] > 0:
            area += s.saw[0] * s.saw[1] / 1e6 * effective_qty(project, part)
    return area


def estimate_consumption_m2(project: Project, op: Operation) -> float:
    """Kroygacha taxminiy sarf: detallar (pilniy) maydoni × (2 − Расчетный процент заполнения / 100)."""
    mat = op.cs_material or CSMaterialParams()
    return parts_area_m2(project, op) * (2 - mat.est_fill_percent / 100)


def _stock_sheet_area(op: Operation) -> float:
    """Kroygacha taxmin uchun list maydoni, m²: ro'yxatdagi birinchi *yangi* list (ombor qoldig'i emas); faqat qoldiqlar
    bo'lsa — birinchisi."""
    sh = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None) or (op.sheets[0] if op.sheets else None)
    return sh.length * sh.width / 1e6 if sh else 0.0


def cs_cost(project: Project, op: Operation) -> dict:
    """Material va operatsiya narxi. Kroydan keyin: «по листам» ✓ — yaxlitlangan listlar × list narxi,
    ☐ — Количество материала (listlar − деловой qoldiqlar, m²) × m² narxi; ombor qoldiqlari m² narxida.
    Kroygacha — taxminiy sarf (estimate_consumption_m2)."""
    mat = op.cs_material or CSMaterialParams()
    cut = op.cs_cut or CSCutParams()
    res = op.result
    edges = edge_map(project)
    info: dict = {}
    if res and res.maps:
        pr = material_prices(op)
        rem = remnant_sheets_used(op)
        rem_area = sum(r["area_m2"] for r in rem)
        new_maps = _new_maps(op)
        new_area = sum(m.sheet_area_m2 * m.copies for m in new_maps)
        new_business = sum(m.remnant_area_m2 * m.copies for m in new_maps)
        qty_m2 = max(0.0, new_area - new_business)
        sheets = _rounded_sheet_count(op)
        if mat.cost_by_sheets:
            op.cost_material = sheets * pr["sheet"] + rem_area * pr["m2"]
        else:
            op.cost_material = qty_m2 * pr["m2"] + rem_area * pr["m2"]
        consumption = res.material_qty_m2 or round(res.material_area_m2 - res.remnant_area_m2, 4)
        info.update(estimated=False, sheets=sheets, material_qty_m2=round(consumption, 4),
                    sheets_total=res.total_sheets, sheet_area_m2=round(_new_sheet_area(op), 4))
    else:
        consumption = estimate_consumption_m2(project, op)
        sa = _stock_sheet_area(op)
        sheets = math.ceil(consumption / sa - 1e-9) if sa else 0
        op.cost_material = (sheets if mat.cost_by_sheets else consumption) * mat.price
        info.update(estimated=True, sheets=sheets, material_qty_m2=round(consumption, 4), sheets_total=sheets,
                    sheet_area_m2=round(sa, 4))
    info["parts_area_m2"] = round(parts_area_m2(project, op), 4)
    # Operatsiya narxi («Расчет стоимости операции по»)
    base = 0.0
    if mat.op_cost_base == OpCostBase.CUT_LENGTH:
        base = res.total_cut_length_m if res else 0
    elif mat.op_cost_base in (OpCostBase.PART_PERIMETER, OpCostBase.PART_AREA):
        for part in op.parts:
            s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
            L, W = s.saw
            q = effective_qty(project, part)
            if mat.op_cost_base == OpCostBase.PART_PERIMETER:
                base += 2 * (L + W) / 1000 * q
            else:
                base += L * W / 1e6 * q
    else:                                   # material maydoni — деловой qoldiqlarsiz
        base = consumption
    op.cost_operation = round(base * mat.op_price, 2)
    op.cost_material = round(op.cost_material, 2)
    info.update(op_base=round(base, 4), cost_material=op.cost_material, cost_operation=op.cost_operation)
    return info


# ───────────────────────── CL: pogonaj kroy (W11; mantiq — services/cl_calc.py) ─────────────────────────
def run_linear(project: Project, op: Operation, quality: Optional[str] = None, only_remaining: bool = False) -> Operation:
    """Раскроить (CL): 1D optimizator (`cl_optimizer`), ИК/Ост, narx; `only_remaining` — «До кроить» (W18). Qarang `cl_calc.run_linear`."""
    from .cl_calc import run_linear as _run
    return _run(project, op, quality, only_remaining)


def cl_variants(project: Project, op: Operation) -> list[dict]:
    """CL kroy variantlari («Варианты», W18). Qarang `cl_calc.cl_variants`."""
    from .cl_calc import cl_variants as _vars
    return _vars(project, op)


def cl_cost(project: Project, op: Operation) -> dict:
    """CL material va operatsiya narxi, Количество материала / Кратность (CLParams da). Qarang `cl_calc.cl_cost`."""
    from .cl_calc import cl_cost as _cost
    return _cost(project, op)


# ───────────────────────── EL: kromka ─────────────────────────
def edge_usage(project: Project, el_op: Operation) -> dict:
    """Kromka hisobi (GibLab saqlagan natijalar bilan solishtirilgan):
      Длина оклейки (ish)          = Σ tomon uzunligi                                   × (ОК − МК)
      Количество материала         = Σ (max(tomon, Мин. оклеиваемая длина) + 2 × Длина остатка по краям)
                                     × (ОК − МК) × (1 + Процент отхода / 100)
    Har biri o'z yaxlitlash kodi bilan («Округление длины кромкования / материала»)."""
    p = el_op.el or ELParams()
    rows = []
    work = 0.0
    material = 0.0
    for op in project.operations:
        if op.type not in (OpType.CS, OpType.CL, OpType.CN):
            continue
        for part in op.parts:
            part = op_part(op, part)               # (CL) eni = polosa eni (ОЛ/ОП kromka metri 0 chiqmasin)
            n_len = sum(1 for s in ("top", "bottom") if getattr(part, f"edge_{s}").op_id == el_op.id)
            n_wid = sum(1 for s in ("left", "right") if getattr(part, f"edge_{s}").op_id == el_op.id)
            if not (n_len or n_wid):
                continue
            q = effective_qty(project, part)
            sides = [part.length] * n_len + [part.width] * n_wid
            w = sum(sides) * q
            m = sum(max(s, p.min_glue_length) + 2 * p.overhang for s in sides) * q
            work += w
            material += m
            # «мин. размер стороны, перпендикулярной кромке»: tor detalni kromkalash stanogi ushlay olmaydi
            narrow = bool(p.min_perp_side) and ((n_len > 0 and part.width < p.min_perp_side - 1e-9) or
                                                (n_wid > 0 and part.length < p.min_perp_side - 1e-9))
            rows.append(dict(part_id=part.id, uid=part.uid, material=op.name, op_type=op.type, length=part.length,
                             edges_len=n_len, width=part.width, edges_wid=n_wid,
                             qty=q, edge_m=round(m * (1 + p.waste_percent / 100) / 1000, 3), name=part.name,
                             narrow=narrow))
    material *= (1 + p.waste_percent / 100)
    work_m = round_code(work / 1000, p.work_round)
    mat_m = round_code(material / 1000, p.material_round)
    el_op.cost_material = round(mat_m * p.price, 2) if p.count_material else 0
    el_op.cost_operation = round(work_m * p.op_price, 2)
    return dict(rows=rows, work_m=work_m, material_m=mat_m,
                narrow=sum(1 for r in rows if r["narrow"]))


# ───────────────────────── GR: pazovanie ─────────────────────────
GROOVE_SIDES = (("top", "length"), ("bottom", "length"), ("left", "width"), ("right", "width"))


def groove_passes(width: float, saw: float) -> int:
    """Arra o'tishlari soni (B7/K4): ⌈paz eni / arra qalinligi⌉, kamida 1 (arra qalinligi berilmasa — bitta o'tish)."""
    if width <= 0 or saw <= 0:
        return 1
    return max(1, math.ceil(width / saw - 1e-9))


def groove_usage(project: Project, gr_op: Operation) -> dict:
    """Paz hisobi (B7/K4). Pazli tomon uzunligi: Сверху/Снизу — detal uzunligi, Слева/Справа — eni (tayyor detal
    o'lchami, kromka bilan); soni — ОК − МК.
      Длина пазования (usage)   = Σ pazli tomonlar × (ОК − МК)                   [m]
      Длина пропила (cut)       = usage × o'tishlar, o'tishlar = ⌈en / arra⌉
      Стоимость                 = usage × Цена метра паза  (operatsiya narxi; material narxi yo'q)
    Natija GRParams.usage / cut_length / passes ga ham yoziladi (API javobida ko'rinadi)."""
    p = gr_op.gr or GRParams()
    if gr_op.gr is None:
        gr_op.gr = p
    edges = edge_map(project)
    passes = groove_passes(p.width, p.saw_thickness)
    rows = []
    total_mm = 0.0
    for op in project.operations:
        if op.type not in (OpType.CS, OpType.CL, OpType.CN):
            continue
        for part in op.parts:
            part = op_part(op, part)               # (CL) eni = polosa eni
            hit ={sd: getattr(part, f"groove_{sd}") for sd, _dim in GROOVE_SIDES
                   if getattr(part, f"groove_{sd}").op_id == gr_op.id}
            if not hit:
                continue
            q = effective_qty(project, part)
            L, W = compute_sizes(part, project.size_mode, edges).detail
            per_unit = sum((L if dim == "length" else W) for sd, dim in GROOVE_SIDES if sd in hit)
            total_mm += per_unit * q
            rows.append(dict(part_id=part.id, uid=part.uid, material=op.name, length=L, width=W, qty=q,
                             top=_groove_mark(hit.get("top")), bottom=_groove_mark(hit.get("bottom")),
                             left=_groove_mark(hit.get("left")), right=_groove_mark(hit.get("right")),
                             groove_len_m=round(per_unit * q / 1000, 3), name=part.name))
    usage = round(total_mm / 1000, 3)
    p.usage = usage
    p.passes = passes
    p.cut_length = round(usage * passes, 3)
    gr_op.cost_material = 0
    gr_op.cost_operation = round(usage * p.price, 2)
    return dict(rows=rows, usage=usage, cut_length=p.cut_length, passes=passes, cost=gr_op.cost_operation)


def _groove_mark(side) -> int:
    """Detal jadvali katagi: 0 — paz yo'q, 1 — lits tomonda, 2 — orqa tomonda."""
    if side is None:
        return 0
    return 2 if side.back_side else 1


# ───────────────────────── SP: sirt ishlovi ─────────────────────────
def surface_usage(project: Project, sp_op: Operation) -> dict:
    """Sirt ishlovi hisobi (W12; formulalar — services/sp_ops.py). Detalning ishlov o'lchami «Режим размеров»dan: -1 — pilniy
    o'lcham (zagotovka + pripusk), 0 — zagotovka; soni — ОК − МК; tomonlar soni — detalning shu SP ga bog'langan tomonlari (lits /
    orqa, 0..2). Natija `SPParams.area_m2 / material_m2` ga va operatsiya narxiga yoziladi:
      cost_operation = ishlov maydoni × spCost;  cost_material = material sarfi × material narxi (faqat «Учитывать материал»)."""
    p = sp_op.sp
    if p is None:
        p = sp_op.sp = SPParams()
    edges = edge_map(project)
    rows = []
    area = mat = 0.0
    for op in project.operations:
        if op.type not in (OpType.CS, OpType.CL, OpType.CN):
            continue
        ma = op.cs_cut.machining_allowance if op.cs_cut else 0
        for part in op.parts:
            part = op_part(op, part)               # (CL) eni = polosa eni
            sides = part_sides(part, sp_op.id)
            if not sides:
                continue
            q = effective_qty(project, part)
            s = compute_sizes(part, project.size_mode, edges, ma)
            L, W = s.saw if p.size_mode == -1 else s.blank
            ok = L > 0 and W > 0
            a = L * W / 1e6 * sides * q if ok else 0.0
            ml, mw = material_dims(L, W, p.rest_side)
            m = ml * mw / 1e6 * sides * q * (1 + p.waste_percent / 100) if ok else 0.0
            area += a
            mat += m
            rows.append(dict(part_id=part.id, uid=part.uid, material=op.name, length=part.length, width=part.width,
                             front=part.surface_face_op == sp_op.id, back=part.surface_back_op == sp_op.id, sides=sides,
                             qty=q, calc_length=round(L, 3), calc_width=round(W, 3), area_m2=round(a, 4), name=part.name))
    p.area_m2 = round(area, 4)
    p.material_m2 = round(mat, 4) if p.count_material else 0.0
    sp_op.cost_material = round(p.material_m2 * p.price, 2) if p.count_material else 0.0
    sp_op.cost_operation = round(p.area_m2 * p.op_price, 2)
    return dict(rows=rows, area_m2=p.area_m2, material_m2=p.material_m2, cost_material=sp_op.cost_material,
                cost_operation=sp_op.cost_operation, cost=round(sp_op.cost_material + sp_op.cost_operation, 2))


# ───────────────────────── XNC: detal bilan sinxron ─────────────────────────
def prune_xnc(project: Project) -> None:
    """Detal o'chirilgan (yoki detalli operatsiya o'chirilgan) bo'lsa — unga bog'langan XNC operatsiyasi yetim:
    boshqa detal ham unga havola qilsa — bog'lanish shu detalga o'tkaziladi, aks holda operatsiya olib tashlanadi
    (narxga va hisobotga kirmaydi). Bo'lmagan XNC ga havolalar detallardan tozalanadi."""
    part_ids = {pt.id for op in project.operations for pt in op.parts}
    xnc_ids = {o.id for o in project.operations if o.type == OpType.XNC}
    refs: dict[str, list[str]] = {}                  # xnc op id → unga havola qiluvchi detallar
    for op in project.operations:
        for pt in op.parts:
            for xid in pt.xnc_op_ids:
                refs.setdefault(xid, []).append(pt.id)
    drop: set[str] = set()
    for o in project.operations:
        if o.type != OpType.XNC or not o.xnc_part_id or o.xnc_part_id in part_ids:
            continue
        alive = [pid for pid in refs.get(o.id, []) if pid in part_ids]
        if alive:
            o.xnc_part_id = alive[0]
        else:
            drop.add(o.id)
    if drop:
        project.operations = [o for o in project.operations if o.id not in drop]
        xnc_ids -= drop
    for op in project.operations:
        for pt in op.parts:
            if any(x not in xnc_ids for x in pt.xnc_op_ids):
                pt.xnc_op_ids = [x for x in pt.xnc_op_ids if x in xnc_ids]


def sync_xnc(project: Project) -> None:
    """XNC ↔ detal (J5). «По размеру детали» ✓ va detalga bog'langan bo'lsa: DX/DY — tayyor detal o'lchami
    (loyihaning kiritish rejimiga mos, services/sizes.py), DZ — material qalinligi, soni = ОК − МК.
    Ifoda o'zgaruvchilari (J3): allowanceT/B/L/R (pripusklar), etj…ert (kromka: j — prifugovka, t — qalinlik;
    t/b/l/r — tomon), xncIndex (loyihadagi XNC tartibi), xncIndexInPart (shu detaldagi tartibi)."""
    edges = edge_map(project)
    prods = {p.id: p for p in project.products}
    parts: dict[str, tuple[Part, Operation]] = {}
    for op in project.operations:
        for pt in op.parts:
            parts.setdefault(pt.id, (pt, op))
    in_part: dict[str, int] = {}
    idx = 0
    for xo in project.operations:
        if xo.type != OpType.XNC or not xo.xnc:
            continue
        idx += 1
        x = xo.xnc
        v = {"xncIndex": float(idx), "xncIndexInPart": 1.0}
        ent = parts.get(xo.xnc_part_id) if xo.xnc_part_id else None
        if xo.xnc_part_id:
            in_part[xo.xnc_part_id] = in_part.get(xo.xnc_part_id, 0) + 1
            v["xncIndexInPart"] = float(in_part[xo.xnc_part_id])
        if ent is not None:
            pt, cs = ent
            mat_t = cs.cs_material.thickness if cs.cs_material is not None and cs.cs_material.thickness > 0 else None
            if mat_t is None and cs.cn is not None and cs.cn.thickness > 0:      # (CN, W16) nesting: material qalinligi CNParams da
                mat_t = cs.cn.thickness
            if x.by_part_size:
                L, W = compute_sizes(pt, project.size_mode, edges).detail
                x.length, x.width = round(L, 3), round(W, 3)
                x.qty = min(effective_qty(project, pt), 100000)
                # DZ material qalinligiga ergashadi — faqat u hozirgacha material qalinligiga teng bo'lgan bo'lsa
                # (korxona loyihalarida dz ≠ material qalinligi bo'lgan, masalan 32 mm li, dasturlar bor: tegilmaydi)
                if mat_t is not None:
                    prev = (x.part_vars or {}).get("matThickness", mat_t)
                    if abs(x.thickness - prev) < 1e-9:
                        x.thickness = mat_t
            if mat_t is not None:
                v["matThickness"] = mat_t
            v.update(allowanceT=pt.allow_top, allowanceB=pt.allow_bottom, allowanceL=pt.allow_left,
                     allowanceR=pt.allow_right)
            for side, ch in (("top", "t"), ("bottom", "b"), ("left", "l"), ("right", "r")):
                ref = getattr(pt, f"edge_{side}")
                e = edges.get(ref.op_id) if ref and ref.op_id else None
                v[f"e{ch}j"] = e.jointing_width if e else 0.0
                v[f"e{ch}t"] = e.thickness if e else 0.0
            # mahsulot dasturi o'zgaruvchilari (W12): `product.<nom>` — detalning mahsuloti «Программа» sidan
            v.update(product_program.ctx_vars(prods.get(pt.product_id or "")))
        x.part_vars = {k: float(val) for k, val in v.items()}


# ───────────────────────── Loyiha bo'yicha ─────────────────────────
def recalc_project(project: Project) -> Project:
    prune_xnc(project)
    product_program.apply(project)           # (W12) mahsulot dasturlari → prog_vars / prog_messages (XNC va etiketka konteksti)
    sync_xnc(project)
    prune_o_owners(project)                  # o'chirilgan mahsulot egasi bo'lgan O → loyiha egasiga (+ xabar)
    prune_surface_refs(project)              # (SP) o'chirilgan operatsiyaga havolalar tozalanadi
    for op in project.operations:
        if op.type == OpType.CS:
            cs_cost(project, op)
            if op.result is not None:
                _packets(op, op.result)          # qalinlik / paket balandligi o'zgarsa ham yangilanadi
        elif op.type == OpType.CL:               # (CL) Погонажный раскрой (W11): polosa eni, narx, paket
            cl_cost(project, op)
        elif op.type == OpType.CN:               # (CN) Нестинговый раскрой (W16): material miqdori va narx (shakllar hisoblanmaydi)
            from .cn_calc import cn_cost
            cn_cost(project, op)
        elif op.type == OpType.EL:
            edge_usage(project, op)
        elif op.type == OpType.GR:
            groove_usage(project, op)
        elif op.type == OpType.SP:
            surface_usage(project, op)
        elif op.type == OpType.O:
            o_cost(project, op)
        elif op.type == OpType.XNC and op.xnc:
            from .xnc import xnc_cost
            xnc_cost(op)
    product_costs(project)
    return project


def product_costs(project: Project) -> None:
    """Mahsulotlar narxi (Изделия: Ст. м-ла / Ст. оп-и) — 1 dona uchun (Всего = × soni): har operatsiya narxi
    mahsulotlarga ulush bo'yicha taqsimlanadi — CS: detallar maydoni, EL: kromka uzunligi,
    XNC: bog'langan detal mahsuloti."""
    mat: dict[str, float] = {p.id: 0.0 for p in project.products}
    opc: dict[str, float] = {p.id: 0.0 for p in project.products}
    part_prod: dict[str, Optional[str]] = {}
    for op in project.operations:
        for pt in op.parts:
            part_prod[pt.id] = pt.product_id

    def spread(op: Operation, shares: dict[Optional[str], float]) -> None:
        tot = sum(v for k, v in shares.items() if k in mat)
        if tot <= 0:
            return
        for k, v in shares.items():
            if k in mat:
                mat[k] += op.cost_material * v / tot
                opc[k] += op.cost_operation * v / tot

    for op in project.operations:
        if op.type in (OpType.CS, OpType.CN):      # (CN, W16) nesting: detallar maydoni ulushi (CS kabi)
            sh: dict[Optional[str], float] = {}
            for pt in op.parts:
                sh[pt.product_id] = sh.get(pt.product_id, 0.0) + pt.length * pt.width * effective_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.CL:                 # pogonaj kroy: detallar uzunligi ulushi (CL-009)
            sh = {}
            for pt in op.parts:
                sh[pt.product_id] = sh.get(pt.product_id, 0.0) + pt.length * effective_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.EL:
            sh = {}
            for o in project.operations:
                if o.type not in (OpType.CS, OpType.CL, OpType.CN):
                    continue
                for pt in o.parts:
                    pt = op_part(o, pt)
                    n = sum(pt.length if s in ("top", "bottom") else pt.width
                            for s in ("top", "bottom", "left", "right") if getattr(pt, f"edge_{s}").op_id == op.id)
                    if n:
                        sh[pt.product_id] = sh.get(pt.product_id, 0.0) + n * effective_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.GR:                 # paz: pazli tomonlar uzunligi ulushi
            sh = {}
            for o in project.operations:
                if o.type not in (OpType.CS, OpType.CL, OpType.CN):
                    continue
                for pt in o.parts:
                    pt = op_part(o, pt)
                    n = sum(pt.length if s in ("top", "bottom") else pt.width
                            for s in ("top", "bottom", "left", "right") if getattr(pt, f"groove_{s}").op_id == op.id)
                    if n:
                        sh[pt.product_id] = sh.get(pt.product_id, 0.0) + n * effective_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.SP:                 # sirt ishlovi: ishlov maydoni ulushi (W12)
            sh = {}
            for o in project.operations:
                if o.type not in (OpType.CS, OpType.CL, OpType.CN):
                    continue
                for pt in o.parts:
                    pt = op_part(o, pt)
                    n = part_sides(pt, op.id)
                    if n:
                        sh[pt.product_id] = sh.get(pt.product_id, 0.0) + n * pt.length * pt.width * effective_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.XNC and op.xnc_part_id:
            spread(op, {part_prod.get(op.xnc_part_id): 1.0})
        elif op.type == OpType.O:                  # komplektatsiya: egasi mahsulot → butun narx shunga (B10)
            spread(op, o_product_shares(project, op))
    for p in project.products:
        q = max(1, p.qty or 0)
        p.cost_material = round(mat.get(p.id, 0.0) / q, 2)
        p.cost_operation = round(opc.get(p.id, 0.0) / q, 2)


def warehouse_request(project: Project) -> list[dict]:
    """Требование на склад: material nomi, birlik, miqdor (+ kesish/kromkalash ishi).
    CS: yangi listlar va ombordagi qoldiqlar (№ bilan) alohida qatorlarda; price/sum — narx va summa."""
    out = []
    for op in project.operations:
        if op.type == OpType.CS:
            res = op.result
            sheets = _rounded_sheet_count(op) if res else 0
            cut = res.total_cut_length_m if res else 0
            pr = material_prices(op)
            rem = remnant_sheets_used(op)
            rem_sum = sum(r["area_m2"] for r in rem) * pr["m2"]
            out.append(dict(op_id=op.id, type="CS", code=op.code, name=op.name, unit=_("unit_sheets"), unit_code="sheets",
                            qty=round(sheets, 3), cut_m=round(cut, 2), note=_("note_cut", m=round(cut, 2)),
                            price=pr["sheet"], sum=round(max(0.0, op.cost_material - rem_sum), 2)))
            for r in rem:
                rid = r["remnant_id"]
                nm = f"{op.name} — " + (_("remnant_sheet", id=rid) if rid else _("remnant_word")) + \
                    f" {r['length']:g}×{r['width']:g}"
                out.append(dict(op_id=op.id, type="CS", code=op.code, name=nm, unit=_("unit_pcs"), unit_code="pcs",
                                qty=r["qty"],
                                remnant=True, remnant_id=rid, area_m2=r["area_m2"],
                                price=round(pr["m2"], 2), sum=round(r["area_m2"] * pr["m2"], 2),
                                note=f"{r['area_m2']} m²"))
        elif op.type == OpType.CL:                 # (CL) pogonaj: material uzunligi (m) yoki polosalar (price_by_strip) + qoldiq polosalar
            from .cl_calc import cl_warehouse_rows
            out.extend(cl_warehouse_rows(project, op))
        elif op.type == OpType.CN:                 # (CN, W16) nesting: yangi listlar (yaxlitlangan) + ombor qoldiqlari
            from .cn_calc import cn_warehouse_rows
            out.extend(cn_warehouse_rows(project, op))
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            if not u["rows"]:
                continue
            out.append(dict(op_id=op.id, type="EL", code=op.code, name=op.name, unit=_("unit_m"), unit_code="m",
                            qty=u["material_m"], work_m=u["work_m"], note=_("note_edge", m=u["work_m"]),
                            price=(op.el.price if op.el else 0), sum=op.cost_material))
        elif op.type == OpType.SP:                 # sirt ishlovi: material sarfi, m² (faqat «Учитывать материал» ✓)
            u = surface_usage(project, op)
            if not u["rows"] or not (op.sp and op.sp.count_material):
                continue
            out.append(dict(op_id=op.id, type="SP", code=op.code, name=op.name, unit=_("unit_m2"), unit_code="m2",
                            qty=u["material_m2"], area_m2=u["area_m2"], note=_("note_surface", m=u["area_m2"]),
                            price=op.sp.price, sum=op.cost_material))
        elif op.type == OpType.O:                  # komplektatsiya: har material qatori o'z birligida, qty × mahsulot soni
            out.extend(o_warehouse_rows(project, op))
    return out
