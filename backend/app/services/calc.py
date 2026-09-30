"""Hisob-kitoblar: kroyni ishga tushirish, kromka, narx, ombor talabnomasi."""
from __future__ import annotations

import math

from ..models import (CSCutParams, CSMaterialParams, ELParams, OpCostBase, OpType,
                      Operation, Part, Project, SheetRounding)
from .optimizer import Item, optimize
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
def run_cutting(project: Project, op: Operation) -> Operation:
    assert op.type == OpType.CS
    cut = op.cs_cut or CSCutParams()
    mat = op.cs_material or CSMaterialParams()
    edges = edge_map(project)
    items: list[Item] = []
    for part in op.parts:
        s = compute_sizes(part, project.size_mode, edges, cut.machining_allowance)
        can_rotate = not (cut.use_grain and part.grain)
        for _ in range(total_qty(project, part)):
            items.append(Item(part.id, part.uid, s.saw[0], s.saw[1], can_rotate))
    res = optimize(items, op.sheets, cut, mat)
    op.result = res
    # ИК / Ост
    unplaced: dict[str, int] = {}
    for pid in res.unplaced:
        unplaced[pid] = unplaced.get(pid, 0) + 1
    for part in op.parts:
        tq = total_qty(project, part)
        part.left_qty = unplaced.get(part.id, 0)
        part.used_qty = tq - part.left_qty
    # Ishlatilgan listlar
    for sh in op.sheets:
        sh.used_qty = sum(m.copies for m in res.maps if m.sheet_id == sh.id)
    cs_cost(project, op)
    return op


def _rounded_sheet_count(op: Operation) -> float:
    """Listlar sonini 'Окруление Листы' qoidasiga ko'ra yaxlitlash.
    To'liq ishlatilmagan oxirgi list qismi (qoldiq) bo'yicha kasr hisoblanadi."""
    mat = op.cs_material
    res = op.result
    if not res or not res.maps:
        return 0
    full = res.total_sheets
    rule = mat.sheet_rounding
    if rule == SheetRounding.WHOLE:
        return full
    denom = int(rule.value[1])
    last = res.maps[-1]
    used_frac = min(1.0, last.parts_area_m2 / last.sheet_area_m2 * 1.0) if last.sheet_area_m2 else 1
    # oxirgi listning band qismi (polosalar bo'yicha taxminiy): maydon ulushi
    part = math.ceil(used_frac * denom - 1e-9) / denom
    return full - 1 + part


def cs_cost(project: Project, op: Operation) -> None:
    mat = op.cs_material or CSMaterialParams()
    res = op.result
    edges = edge_map(project)
    if res and res.maps:
        if mat.cost_by_sheets:
            qty = _rounded_sheet_count(op)
            if mat.price_per_m2:
                sheet_area = res.material_area_m2 / max(res.total_sheets, 1)
                op.cost_material = qty * sheet_area * mat.price
            else:
                op.cost_material = qty * mat.price
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
            rows.append(dict(part_id=part.id, material=op.name, length=part.length,
                             edges_len=n_len, width=part.width, edges_wid=n_wid,
                             qty=q, edge_m=round(m / 1000, 3), name=part.name))
    material *= (1 + p.waste_percent / 100)
    work_m = round_to(work / 1000, p.work_rounding)
    mat_m = round_to(material / 1000, p.material_rounding)
    el_op.cost_material = round(mat_m * p.price, 2) if p.count_material else 0
    el_op.cost_operation = round(work_m * p.op_price, 2)
    return dict(rows=rows, work_m=round(work_m, 3), material_m=round(mat_m, 3))


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
    return project


def warehouse_request(project: Project) -> list[dict]:
    """Требование на склад: material nomi, birlik, miqdor."""
    out = []
    for op in project.operations:
        if op.type == OpType.CS:
            res = op.result
            sheets = res.total_sheets if res else 0
            cut = res.total_cut_length_m if res else 0
            out.append(dict(type="CS", code=op.code, name=op.name, unit="list",
                            qty=sheets, note=f"Kesish uzunligi: {cut} m"))
        elif op.type == OpType.EL:
            u = edge_usage(project, op)
            out.append(dict(type="EL", code=op.code, name=op.name, unit="m",
                            qty=u["material_m"], note=f"Kromkalash (ish): {u['work_m']} m"))
    return out
