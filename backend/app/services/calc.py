"""Hisob-kitoblar: kroyni ishga tushirish, kromka, narx, ombor talabnomasi."""
from __future__ import annotations

import math
import time
from typing import Optional

from ..i18n import _
from ..models import (CSCutParams, CSMaterialParams, ELParams, FirstCutDir, OpCostBase, OpType,
                      Operation, Part, Project, SheetRounding)
from .optimizer import Item, _finish, optimize
from .sizes import compute_sizes


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


def round_to(value: float, step: float) -> float:
    """step=0 → o'zgarmaydi; aks holda yuqoriga yaxlitlash (masalan 0.5 m)."""
    return math.ceil(value / step - 1e-9) * step if step else value


# ───────────────────────── CS: kroy ─────────────────────────
def _items_for(project: Project, op: Operation, cut: CSCutParams, only: Optional[dict[str, int]] = None) -> list[Item]:
    edges = edge_map(project)
    items: list[Item] = []
    for part in op.parts:
        n = total_qty(project, part) if only is None else only.get(part.id, 0)
        if n <= 0:
            continue
        s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
        if s.saw[0] <= 0 or s.saw[1] <= 0:      # to'ldirilmagan (bo'sh) qator — kroyga kirmaydi
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
        tq = total_qty(project, part)
        part.used_qty = min(tq, placed.get(part.id, 0))
        part.left_qty = tq - part.used_qty
    for sh in op.sheets:
        sh.used_qty = sum(m.copies for m in res.maps if m.sheet_id == sh.id) if res else 0
    if res:
        _packets(op, res)


def sheets_per_pack(op: Operation) -> int:
    """Paketda birga kesiladigan listlar: min(Кратность, ⌊Высота пакета / qalinlik⌋), kamida 1."""
    cut = op.cs_cut or CSCutParams()
    thick = (op.cs_material.thickness if op.cs_material else 0) or 0
    by_h = int((cut.pack_height + 1e-9) // thick) if cut.pack_height and thick > 0 else 1
    n = min(by_h, cut.multiplicity) if cut.multiplicity and cut.multiplicity > 0 else by_h
    return max(1, n)


def _packets(op: Operation, res) -> None:
    spp = sheets_per_pack(op)
    res.sheets_per_pack = spp
    for m in res.maps:
        m.packs = math.ceil(m.copies / spp) if m.copies > 0 else 0
    res.total_packs = sum(m.packs for m in res.maps)


def run_cutting(project: Project, op: Operation, only_remaining: bool = False,
                first_cut: Optional[FirstCutDir] = None, quality: Optional[str] = None) -> Operation:
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
        add = optimize(_items_for(project, op, cut, left), stock, cut, mat, groups=groups_for(op))
        old = op.result
        start = len(old.maps)
        for i, m in enumerate(add.maps, 1):
            m.index = start + i
        old.maps += add.maps
        old.unplaced = add.unplaced
        res = _finish(old, mat)
    else:
        res = optimize(_items_for(project, op, cut), op.sheets, cut, mat, groups=groups_for(op))
    res.elapsed_s = round(time.monotonic() - t0, 2)
    op.result = res
    _account(project, op)
    cs_cost(project, op)
    return op


def cutting_variants(project: Project, op: Operation) -> list[dict]:
    """SketchCut g'oyasi: uch variant (optimal / 1-kesish uzunlik bo'yicha / eni bo'yicha) — xodim solishtirib tanlaydi."""
    from .optimizer import time_budget
    out = []
    base = (op.cs_cut or CSCutParams()).model_copy()
    mat = op.cs_material or CSMaterialParams()
    for key, fc in (("optimal", FirstCutDir.ANY), ("length", FirstCutDir.LENGTH), ("width", FirstCutDir.WIDTH)):
        cut = base.model_copy(update={"first_cut": fc})
        t0 = time.monotonic()
        items = _items_for(project, op, cut)
        tl = time_budget(len(items), cut.quality) * (1.0 if key == "optimal" else 0.6)
        res = optimize(items, op.sheets, cut, mat, time_limit=tl, groups=groups_for(op))
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


def _rounded_sheet_count(op: Operation) -> float:
    """Yangi listlar sonini (ombor qoldiqlari alohida) «Округление листы» qoidasiga ko'ra yaxlitlash.
    Oxirgi listning band qismi = 1 − деловой qoldiq ulushi (sarf = material − деловой qoldiq)."""
    mat = op.cs_material or CSMaterialParams()
    maps = _new_maps(op)
    if not maps:
        return 0
    full = sum(m.copies for m in maps)
    rule = mat.sheet_rounding
    if rule == SheetRounding.WHOLE:
        return full
    denom = int(rule.value[1])
    last = maps[-1]
    if last.sheet_area_m2:
        used_frac = min(1.0, max(0.0, 1 - last.remnant_area_m2 / last.sheet_area_m2))
    else:
        used_frac = 1.0
    part = math.ceil(used_frac * denom - 1e-9) / denom
    return full - 1 + part


def _new_sheet_area(op: Operation) -> float:
    """Yangi list maydoni, m² (kroydagi yangi kartalar bo'yicha o'rtacha, bo'lmasa ro'yxatdagi birinchi list)."""
    maps = _new_maps(op)
    n = sum(m.copies for m in maps)
    if n:
        return sum(m.sheet_area_m2 * m.copies for m in maps) / n
    sh = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None)
    return sh.length * sh.width / 1e6 if sh else 0.0


def material_prices(op: Operation) -> dict:
    """Material narxlari: yangi list narxi, m² narxi (qoldiqlar maydoni bo'yicha shu narxda hisoblanadi)."""
    mat = op.cs_material or CSMaterialParams()
    area = _new_sheet_area(op)
    if mat.price_per_m2:
        return dict(sheet=round(mat.price * area, 2), m2=mat.price)
    return dict(sheet=mat.price, m2=(mat.price / area) if area else 0.0)


def cs_cost(project: Project, op: Operation) -> None:
    mat = op.cs_material or CSMaterialParams()
    res = op.result
    edges = edge_map(project)
    if res and res.maps:
        if mat.cost_by_sheets:
            pr = material_prices(op)
            op.cost_material = _rounded_sheet_count(op) * pr["sheet"] + \
                sum(r["area_m2"] for r in remnant_sheets_used(op)) * pr["m2"]
        else:
            op.cost_material = res.parts_area_m2 * mat.price
    else:  # kroysiz taxminiy hisob: maydon / (list maydoni × to'ldirish %)
        area = 0.0
        for part in op.parts:
            s = compute_sizes(part, project.size_mode, edges)
            area += s.saw[0] * s.saw[1] / 1e6 * total_qty(project, part)
        if op.sheets:
            sa = op.sheets[0].length * op.sheets[0].width / 1e6
            sheets = math.ceil(area / (sa * mat.est_fill_percent / 100)) if sa else 0
            op.cost_material = sheets * (mat.price if not mat.price_per_m2 else sa * mat.price)
    # Operatsiya narxi
    base = 0.0
    if mat.op_cost_base == OpCostBase.CUT_LENGTH:
        base = res.total_cut_length_m if res else 0
    elif mat.op_cost_base == OpCostBase.PART_PERIMETER:
        for part in op.parts:
            base += 2 * (part.length + part.width) / 1000 * total_qty(project, part)
    elif mat.op_cost_base == OpCostBase.PART_AREA:
        for part in op.parts:
            base += part.length * part.width / 1e6 * total_qty(project, part)
    else:
        base = res.material_area_m2 if res else 0
    op.cost_operation = round(base * mat.op_price, 2)
    op.cost_material = round(op.cost_material, 2)


# ───────────────────────── EL: kromka ─────────────────────────
def edge_usage(project: Project, el_op: Operation) -> dict:
    """Har bir kromka operatsiyasi uchun detallar ro'yxati va uzunliklar.
    Hisob (GibLab hisobotidagi natijaga mos):
      ish uzunligi   = Σ max(tomon, min_glue_length)
      material       = Σ (tomon + 2×overhang) × (1 + chiqindi%)"""
    p = el_op.el or ELParams()
    rows = []
    work = 0.0
    material = 0.0
    for op in project.operations:
        if op.type != OpType.CS:
            continue
        for part in op.parts:
            n_len = sum(1 for s in ("top", "bottom") if getattr(part, f"edge_{s}").op_id == el_op.id)
            n_wid = sum(1 for s in ("left", "right") if getattr(part, f"edge_{s}").op_id == el_op.id)
            if not (n_len or n_wid):
                continue
            q = total_qty(project, part)
            sides = [part.length] * n_len + [part.width] * n_wid
            w = sum(max(s, p.min_glue_length) for s in sides) * q
            m = sum(s + 2 * p.overhang for s in sides) * q
            work += w; material += m
            # «мин. размер стороны, перпендикулярной кромке»: tor detalni kromkalash stanogi ushlay olmaydi
            narrow = bool(p.min_perp_side) and ((n_len > 0 and part.width < p.min_perp_side - 1e-9) or
                                                (n_wid > 0 and part.length < p.min_perp_side - 1e-9))
            rows.append(dict(part_id=part.id, uid=part.uid, material=op.name, length=part.length,
                             edges_len=n_len, width=part.width, edges_wid=n_wid,
                             qty=q, edge_m=round(m / 1000, 3), name=part.name, narrow=narrow))
    material *= (1 + p.waste_percent / 100)
    work_m = round_to(work / 1000, p.work_rounding)
    mat_m = round_to(material / 1000, p.material_rounding)
    el_op.cost_material = round(mat_m * p.price, 2) if p.count_material else 0
    el_op.cost_operation = round(work_m * p.op_price, 2)
    return dict(rows=rows, work_m=round(work_m, 3), material_m=round(mat_m, 3),
                narrow=sum(1 for r in rows if r["narrow"]))


# ───────────────────────── Loyiha bo'yicha ─────────────────────────
def recalc_project(project: Project) -> Project:
    for op in project.operations:
        if op.type == OpType.CS:
            cs_cost(project, op)
        elif op.type == OpType.EL:
            edge_usage(project, op)
        elif op.type == OpType.XNC and op.xnc:
            from .xnc import xnc_cost
            xnc_cost(op)
    product_costs(project)
    return project


def product_costs(project: Project) -> None:
    """Mahsulotlar narxi (Изделия: Ст. м-ла / Ст. оп-и): har operatsiya narxi mahsulotlarga ulush bo'yicha
    taqsimlanadi — CS: detallar maydoni, EL: kromka uzunligi, XNC: bog'langan detal mahsuloti."""
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
        if op.type == OpType.CS:
            sh: dict[Optional[str], float] = {}
            for pt in op.parts:
                sh[pt.product_id] = sh.get(pt.product_id, 0.0) + pt.length * pt.width * total_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.EL:
            sh = {}
            for o in project.operations:
                if o.type != OpType.CS:
                    continue
                for pt in o.parts:
                    n = sum(pt.length if s in ("top", "bottom") else pt.width
                            for s in ("top", "bottom", "left", "right") if getattr(pt, f"edge_{s}").op_id == op.id)
                    if n:
                        sh[pt.product_id] = sh.get(pt.product_id, 0.0) + n * total_qty(project, pt)
            spread(op, sh)
        elif op.type == OpType.XNC and op.xnc_part_id:
            spread(op, {part_prod.get(op.xnc_part_id): 1.0})
    for p in project.products:
        p.cost_material = round(mat.get(p.id, 0.0), 2)
        p.cost_operation = round(opc.get(p.id, 0.0), 2)


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
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            if not u["rows"]:
                continue
            out.append(dict(op_id=op.id, type="EL", code=op.code, name=op.name, unit=_("unit_m"), unit_code="m",
                            qty=u["material_m"], work_m=u["work_m"], note=_("note_edge", m=u["work_m"]),
                            price=(op.el.price if op.el else 0), sum=op.cost_material))
    return out
