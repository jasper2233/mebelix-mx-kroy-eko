"""(CL) Погонажный раскрой — hisob-kitoblar (W11): kroy elementlari, kroyni ishga tushirish, material va operatsiya narxi,
ombor talabnomasi. Optimizator — `cl_optimizer.py`; `calc.run_linear` / `calc.cl_cost` shu yerga yo'naltiradi.

Detal eni: CL da `Part.width` 0 saqlanadi, hisobda har doim `op.cl.width` (polosa eni) olinadi (`calc.op_part`). Polosa qatorlari
(`op.sheets`) eni ham `cl.width` ga tenglashtiriladi (jadvalda ko'rinadi, tahrirlanmaydi — hujjat Q15).

Narx (hujjat §3.3; ❓ joylar — T_W11_CL.md):
  material      — kroydan keyin: price × (ishlatilgan polosalar uzunligi − деловой otxodlar), m  (price_by_strip: price × yaxlitlangan polosalar);
                  kroygacha: price × Σ detal uzunligi × (2 − Расчетный процент / 100)
  operatsiya    — asos × op_price; asos (cCostType): 0 kesim uzunligi torsovka bilan (LT = kesimlar × polosa eni) · 1 torsovkasiz ·
                  2 material uzunligi (деловой otxodsiz) · 3 detallar uzunligi; kroygacha kesim — har detalga 2 kesim × polosa eni
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional

from ..i18n import _
from ..models import CL_DEFAULTS, CLCostBase, CLParams, CuttingResult, Operation, Project, SheetRounding
from .calc import (_account, _frac_up, edge_map, effective_qty, is_remnant_map, remnant_sheets_used, sheets_per_pack,
                   total_qty)
from .cl_optimizer import UNIT, UNLIMITED, LItem, build_types, optimize_linear, trims_of, u
from .sizes import compute_sizes


def ensure_cl(op: Operation) -> CLParams:
    """CL operatsiyasida `cl` bo'lishi shart (eski / qo'lda yaratilgan yozuv — standart qiymatlar)."""
    if op.cl is None:
        op.cl = CLParams()
    return op.cl


def normalize_sheets(op: Operation) -> None:
    """Polosa qatorlari eni = `cl.width` (hamma detal eni — polosa eni)."""
    cl = ensure_cl(op)
    for sh in op.sheets:
        sh.width = cl.width


# ───────────────────────── Kroy elementlari ─────────────────────────
@dataclass
class ClItems:
    items: list[LItem] = field(default_factory=list)
    bad: list[str] = field(default_factory=list)             # ishchi uzunlik ≤ 0 (kromka / prifugovka detaldan katta)
    small: list[str] = field(default_factory=list)           # «Мин. размер детали» dan kichik
    uncomputed: list[str] = field(default_factory=list)      # import: manfiy (hisoblanmagan) uzunlik → 0


def saw_length(project: Project, op: Operation, part, edges=None) -> float:
    """Detalning pilniy uzunligi (loyiha o'lcham rejimiga mos; ОЛ/ОП kromka qalinligi uzunlikni kamaytiradi;
    «Припуск на обработку заготовки» har uchidan qo'shiladi)."""
    cl = ensure_cl(op)
    edges = edges if edges is not None else edge_map(project)
    return compute_sizes(part.model_copy(update={"width": cl.width}), project.size_mode, edges,
                         cl.machining_allowance).saw[0]


def cl_items(project: Project, op: Operation) -> ClItems:
    """Detal nusxalari (ОК − МК): uzunlik > 0; 0 uzunlik — to'ldirilmagan qator (jim; importdagi «hisoblanmagan» — ogohlantirish bilan)."""
    cl = ensure_cl(op)
    edges = edge_map(project)
    out = ClItems()
    for part in op.parts:
        n = effective_qty(project, part)
        if n <= 0:
            continue
        if part.length <= 0:
            if part.src_length is not None:
                out.uncomputed += [part.id] * n
            continue
        p = saw_length(project, op, part, edges)
        if p <= 0:
            out.bad += [part.id] * n
            continue
        if cl.min_part_len > 0 and p < cl.min_part_len - 1e-9:
            out.small += [part.id] * n
            continue
        out.items += [LItem(part.id, part.uid, p) for _i in range(n)]
    return out


def parts_length_m(project: Project, op: Operation) -> float:
    """Σ detal pilniy uzunligi × (ОК − МК), m."""
    edges = edge_map(project)
    tot = 0.0
    for part in op.parts:
        if part.length > 0:
            p = saw_length(project, op, part, edges)
            if p > 0:
                tot += p * effective_qty(project, part)
    return tot / 1000


def _piece_count(project: Project, op: Operation) -> int:
    return sum(effective_qty(project, p) for p in op.parts if p.length > 0)


# ───────────────────────── Kroy ─────────────────────────
def _compute(project: Project, op: Operation, quality: Optional[str] = None, objective: Optional[str] = None,
             items: Optional[list[LItem]] = None, stock: Optional[list] = None) -> tuple[CuttingResult, ClItems]:
    """Optimizatorni ishga tushirish va ogohlantirishlarni yig'ish (`op` o'zgarmaydi). `items` / `stock` berilsa («До кроить») —
    shular bo'yicha (kroyga kirmaydigan detallar — `ci` dan)."""
    t0 = time.monotonic()
    cl = ensure_cl(op)
    normalize_sheets(op)
    ci = cl_items(project, op)
    stock = op.sheets if stock is None else stock
    res = optimize_linear(ci.items if items is None else items, stock, cl, quality=quality, objective=objective)
    warns: list[str] = []
    types = build_types(stock, cl)
    u_max = max((t.geom.U for t in types), default=0)
    if res.unplaced:
        by_id = {p.id: p for p in op.parts}
        edges = edge_map(project)
        long_ids: list[str] = []
        short_ids: list[str] = []
        for pid in res.unplaced:
            part = by_id.get(pid)
            p = saw_length(project, op, part, edges) if part is not None else 0
            (long_ids if u(p) > u_max else short_ids).append(pid)
        if long_ids:
            warns.append(_("cl_warn_long", n=len(long_ids), mm=f"{u_max / UNIT:g}"))
        if short_ids:
            warns.append(_("cl_warn_stock", n=len(short_ids)))
    if ci.small:
        warns.append(_("warn_small_parts", n=len(ci.small), mm=f"{cl.min_part_len:g}"))
    if ci.uncomputed:
        warns.append(_("cl_warn_uncomputed", n=len(ci.uncomputed)))
    for pid in dict.fromkeys(ci.bad):
        part = next((p for p in op.parts if p.id == pid), None)
        if part is not None:
            warns.append(_("cl_warn_bad", uid=part.uid, l=f"{saw_length(project, op, part):g}"))
    res.unplaced = list(res.unplaced) + ci.small + ci.bad + ci.uncomputed
    res.warnings = warns
    res.elapsed_s = round(time.monotonic() - t0, 2)
    return res, ci


def run_linear(project: Project, op: Operation, quality: Optional[str] = None, only_remaining: bool = False) -> Operation:
    """Раскроить (CL). `only_remaining=True` — «До кроить» (W18): mavjud kartalar o'zgarmaydi, faqat kroyga kirmagan detallar
    qolgan polosalarga (ro'yxatda hali ishlatilmagan / cheksiz) yangi kartalar bo'lib qo'shiladi."""
    if only_remaining and op.result and op.result.maps:
        return _run_remaining(project, op, quality)
    res, _ci = _compute(project, op, quality)
    op.result = res
    _account(project, op)
    cl_cost(project, op)
    return op


def _run_remaining(project: Project, op: Operation, quality: Optional[str]) -> Operation:
    """«До кроить» (CL): `left_qty > 0` detallar → qolgan polosalar bo'yicha 1D kroy; natija mavjud kartalar ro'yxatiga qo'shiladi.
    Karta raqamlari, qoldiq (Д№) raqamlari va jami ko'rsatkichlar `cl_editor.rebuild` bilan butun natija bo'yicha qayta quriladi
    (eski kartalarning izohi / bajarilganligi / torsovkasi saqlanadi); natija «qo'lda tahrirlangan» deb belgilanmaydi."""
    from . import cl_editor
    _account(project, op)
    left = {p.id: p.left_qty for p in op.parts if p.left_qty > 0}
    old = op.result
    if not left or old is None:
        return op
    normalize_sheets(op)
    ci = cl_items(project, op)
    take = dict(left)
    items: list[LItem] = []
    for it in ci.items:                                    # har detalning faqat qolgan (ИК dan keyingi) nusxalari
        if take.get(it.part_id, 0) > 0:
            take[it.part_id] -= 1
            items.append(it)
    stock = []
    for sh in op.sheets:                                   # ro'yxat tartibi (ustuvorlik) saqlanadi; ishlatilgani ayriladi
        free = sh.qty - sh.used_qty if sh.qty < UNLIMITED else sh.qty
        if free > 0:
            stock.append(sh.model_copy(update={"qty": free}))
    add, _ci = _compute(project, op, quality, items=items, stock=stock)
    combined = CuttingResult(maps=[m.model_copy(deep=True) for m in old.maps] + add.maps, variant=old.variant,
                             manual=old.manual, elapsed_s=add.elapsed_s, warnings=list(add.warnings))
    new = cl_editor.rebuild(project, op, combined, final=True)
    new.manual = old.manual
    new.variant = old.variant
    new.warnings = list(add.warnings)
    new.elapsed_s = add.elapsed_s
    new.unplaced = list(add.unplaced)                      # sig'magan / kroyga kirmagan detallar (rebuild — «yangi» ro'yxatdan)
    op.result = new
    _account(project, op)
    cl_cost(project, op)
    return op


# ───────────────────────── Variantlar («Варианты») ─────────────────────────
VARIANT_KEYS = ("material", "consumption", "cuts", "max")        # `max` — material maqsadi, lekin «Максимальное» sifat rejimi


def _signature(res: CuttingResult) -> tuple:
    return tuple((m.sheet_id, m.copies, tuple(p.part_uid for p in sorted(m.placements, key=lambda p: p.x))) for m in res.maps)


def cl_variants(project: Project, op: Operation) -> list[dict]:
    """Kroy variantlarini solishtirish (CL): maqsad funksiyasi bo'yicha — kam material / kam sarf (material − деловой otxod) /
    kam kesim — va («Максимальное» sifat tanlanmagan bo'lsa) maksimal sifatda kam material. `op` o'zgarmaydi; tanlangan variant
    `PUT .../result` bilan saqlanadi. Natijalari bir xil variantlarda `same_as` — birinchi bir xil variant kaliti."""
    cl = ensure_cl(op)
    out: list[dict] = []
    seen: dict[tuple, str] = {}
    for key in VARIANT_KEYS:
        if key == "max" and cl.quality == "max":
            continue
        t0 = time.monotonic()
        res, _ci = _compute(project, op, "max" if key == "max" else None, "material" if key == "max" else key)
        res.variant = key
        res.elapsed_s = round(time.monotonic() - t0, 2)
        sig = _signature(res)
        out.append(dict(variant=key, sheets=res.total_sheets, fill=res.total_fill_percent, cut_m=res.total_cut_length_m,
                        cuts=res.total_cuts, unplaced=len(res.unplaced), remnant_m2=res.remnant_area_m2,
                        material_len_m=res.material_len_m, business_len_m=res.business_len_m, maps=len(res.maps),
                        same_as=seen.get(sig), result=res))
        seen.setdefault(sig, key)
    return out


# ───────────────────────── Narx ─────────────────────────
def _first_new_strip_len(op: Operation) -> float:
    sh = next((x for x in op.sheets if not (x.is_remnant or x.source_remnant_id)), None) or (op.sheets[0] if op.sheets else None)
    return sh.length if sh else 0.0


def _new_maps(op: Operation) -> list:
    return [m for m in (op.result.maps if op.result else []) if not is_remnant_map(op, m)]


def rounded_strip_count(op: Operation) -> float:
    """Yangi polosalar soni «Округление — Полосы» qoidasi bilan (11 — butun; 32 / 33 / 34 — oxirgi polosa uzunligi bo'yicha 1/2, 1/3, 1/4)."""
    cl = ensure_cl(op)
    maps = _new_maps(op)
    if not maps:
        return 0
    full = sum(m.copies for m in maps)
    rule = cl.strip_rounding
    last = maps[-1]
    if rule == SheetRounding.WHOLE or rule.value[0] != "3" or last.copies != 1 or not last.placements or not last.sheet_length:
        return full
    fl = max(p.x + p.length for p in last.placements) / last.sheet_length
    return full - 1 + _frac_up(fl, int(rule.value[1]))


def cl_cost(project: Project, op: Operation) -> dict:
    """Material va operatsiya narxi; `CLParams.usage_m` (Количество материала, m) va `multiplicity` yangilanadi."""
    cl = ensure_cl(op)
    normalize_sheets(op)
    res = op.result
    parts_m = parts_length_m(project, op)
    spp = sheets_per_pack(op)
    ts, te = trims_of(cl)
    info: dict = {}
    if res and res.maps:
        mat_m = res.material_len_m or round(sum(m.sheet_length * m.copies for m in res.maps) / 1000, 4)
        bus_m = res.business_len_m
        qty_m = max(0.0, mat_m - bus_m)
        strips = rounded_strip_count(op)
        rem = remnant_sheets_used(op)
        rem_m = sum(r["length"] * r["qty"] for r in rem) / 1000
        if cl.price_by_strip:
            nominal = _first_new_strip_len(op) or 1.0
            op.cost_material = strips * cl.price + (rem_m * 1000 / nominal) * cl.price
        else:
            op.cost_material = qty_m * cl.price            # ombor qoldiq-polosalari ham 1 m narxida (qty_m ga kiritilgan)
        cut_with = res.total_cut_length_m
        cut_no = 0.0
        for m in res.maps:
            m_ts = u(m.trim_length) if m.trim_length is not None else ts
            m_te = u(m.end_offset_right) if m.end_offset_right is not None else te
            cut_no += max(0, m.cuts_count - (1 if m_ts > 0 else 0) - (1 if m_te > 0 else 0)) * cl.width / 1000 * m.copies
        parts_done = sum(sum(p.length for p in m.placements) * m.copies for m in res.maps) / 1000
        info.update(estimated=False, strips=strips, strips_total=res.total_sheets, material_len_m=round(mat_m, 4),
                    business_len_m=round(bus_m, 4), parts_len_m=round(parts_done, 4))
        parts_base = parts_done
    else:
        qty_m = parts_m * (2 - cl.est_fill_percent / 100)
        nominal = _first_new_strip_len(op)
        strips = math.ceil(qty_m * 1000 / nominal - 1e-9) if nominal else 0
        op.cost_material = (strips if cl.price_by_strip else qty_m) * cl.price
        cut_with = cut_no = 2 * _piece_count(project, op) * cl.width / 1000        # cTrimLengthP: 2 kesim × polosa eni
        info.update(estimated=True, strips=strips, strips_total=strips, material_len_m=round(qty_m, 4), business_len_m=0.0,
                    parts_len_m=round(parts_m, 4))
        parts_base = parts_m
    base = {CLCostBase.CUT_WITH_TRIM: cut_with, CLCostBase.CUT_NO_TRIM: cut_no, CLCostBase.MATERIAL_LEN: qty_m,
            CLCostBase.PARTS_LEN: parts_base}[cl.op_cost_base]
    op.cost_material = round(op.cost_material, 2)
    op.cost_operation = round(base * cl.op_price, 2)
    cl.usage_m = round(qty_m, 4)
    cl.multiplicity = spp
    info.update(material_qty_m=round(qty_m, 4), cut_with_trim_m=round(cut_with, 3), cut_no_trim_m=round(cut_no, 3),
                op_base=round(base, 4), multiplicity=spp, cost_material=op.cost_material, cost_operation=op.cost_operation)
    return info


# ───────────────────────── Ombor talabnomasi ─────────────────────────
def cl_warehouse_rows(project: Project, op: Operation) -> list[dict]:
    """«Требование на склад»: CL — material uzunligi (m; деловой otxodsiz) yoki polosalar (price_by_strip) + ombor qoldiq-polosalari
    alohida qatorlarda. Hisob `cl_cost` bilan bir xil."""
    cl = ensure_cl(op)
    info = cl_cost(project, op)
    out: list[dict] = []
    res = op.result
    cut = res.total_cut_length_m if res else 0
    by_strip = cl.price_by_strip
    out.append(dict(op_id=op.id, type="CL", code=op.code, name=op.name,
                    unit=_("unit_strips") if by_strip else _("unit_m"), unit_code="strips" if by_strip else "m",
                    qty=round(info["strips"] if by_strip else info["material_qty_m"], 3), cut_m=round(cut, 2),
                    strips=info["strips"], note=_("note_cut", m=round(cut, 2)), price=cl.price, sum=op.cost_material))
    for r in remnant_sheets_used(op):
        rid = r["remnant_id"]
        nm = f"{op.name} — " + (_("remnant_sheet", id=rid) if rid else _("remnant_word")) + f" {r['length']:g}"
        out.append(dict(op_id=op.id, type="CL", code=op.code, name=nm, unit=_("unit_pcs"), unit_code="pcs", qty=r["qty"],
                        remnant=True, remnant_id=rid, length_m=round(r["length"] * r["qty"] / 1000, 3),
                        price=cl.price, sum=round(r["length"] * r["qty"] / 1000 * cl.price, 2),
                        note=f"{round(r['length'] * r['qty'] / 1000, 3)} m"))
    return out


# ───────────────────────── MES ─────────────────────────
def mes_payload(project: Project, op: Operation) -> dict:
    """MES uchun CL natijasi: detallar, polosa eni, material uzunligi (m), деловой qoldiqlar, kartalar (qisqa)."""
    cl = ensure_cl(op)
    res = op.result
    d: dict = dict(kind="linear", strip_width=cl.width, thickness=cl.thickness,
                   parts=[dict(uid=pt.uid, code=pt.code, name=pt.name, length=pt.length, qty=total_qty(project, pt),
                               used=pt.used_qty, left=pt.left_qty) for pt in op.parts])
    if res:
        d.update(strips=res.total_sheets, material_len_m=res.material_len_m, business_len_m=res.business_len_m,
                 parts_m=round(sum(pl.length * m.copies for m in res.maps for pl in m.placements) / 1000, 4),
                 fill_percent=res.total_fill_percent, cut_length_m=res.total_cut_length_m, cuts=res.total_cuts,
                 remnants=[dict(length=o.raw_length or o.length, width=o.raw_width or o.width, business=o.business)
                           for o in res.remnants],
                 maps=[dict(index=m.index, copies=m.copies, done=m.done_count, strip=[m.sheet_length, m.sheet_width],
                            fill=m.fill_percent, parts=m.parts_count) for m in res.maps])
    return d


# ───────────────────────── Parametrlar o'zgarishi ─────────────────────────
# kroy natijasini eskirtirmaydigan CL parametrlari (narx / ko'rinish / keyingi «Раскроить» strategiyasi / hisoblangan)
CL_NON_CUT = frozenset({"quality", "fill_packet", "pack_height", "thickness", "price", "price_by_strip", "strip_rounding",
                        "est_fill_percent", "op_cost_base", "op_price", "usage_m", "multiplicity",
                        # W-parity: saqlanadigan, lekin 1D kroy natijasiga ta'sir qilmaydigan belgilar (CS dagi kabi)
                        "merge_parts", "group_parts", "save_drawings"})


def cl_params_stale(old: Operation, new: Operation) -> bool:
    """Parametr o'zgarishi mavjud kroy natijasini eskirtiradimi (propil, torsovka, otxod qoidalari, eni, min. detal …)."""
    a, b = old.cl, new.cl
    if (a is None) != (b is None):
        return True
    return bool(a and any(getattr(a, f) != getattr(b, f) for f in CLParams.model_fields if f not in CL_NON_CUT))


def new_cl_params(defaults: dict, item=None) -> CLParams:
    """Yangi CL operatsiyasi: `cl_defaults` + katalogdagi погонажный tovar (qalinlik, eni, narx)."""
    p = CLParams.model_validate({k: v for k, v in (defaults or {}).items() if k not in ("usage_m", "multiplicity")})
    if item is not None:
        p.thickness = item.thickness or p.thickness
        p.price = item.price or p.price
        if item.width:
            p.width = float(item.width)
    return p


def default_strip_length(item=None, app_cfg: Optional[dict] = None) -> float:
    """Yangi CL operatsiyasidagi birinchi polosa uzunligi: katalog tovari standart uzunligi, bo'lmasa 6000 mm."""
    return float((item.length if item is not None and item.length else None) or CL_DEFAULTS["strip_length"])
