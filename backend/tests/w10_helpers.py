"""W10 testlari uchun umumiy yordamchilar: loyihaning «kanonik» ko'rinishi (id lar o'rniga tartib raqamlari), hisoblangan
ko'rsatkichlar (detallar soni/maydoni, kromka metri, XNC statistikasi) va farqlarni topish.
Mijoz ma'lumoti hech qayerga yozilmaydi: faqat sonlar va nomsiz tuzilma ko'rsatkichlari."""
from __future__ import annotations

from typing import Any

from app.models import OpType, Project
from app.services import calc, xnc


def _dump(model, drop: set[str] | None = None) -> dict:
    d = model.model_dump(mode="json")
    for k in drop or ():
        d.pop(k, None)
    return d


def canon(p: Project) -> dict:
    """Loyiha mazmuni (id lar va hisoblangan maydonlarsiz). Tartib raqamlari: mahsulot / operatsiya / detal."""
    pidx = {pr.id: i for i, pr in enumerate(p.products)}
    oidx = {o.id: i for i, o in enumerate(p.operations)}
    flat = [pt for o in p.operations for pt in o.parts]
    partidx: dict[str, int] = {}
    for i, pt in enumerate(flat):
        partidx.setdefault(pt.id, i)

    def part(pt) -> dict:
        d = _dump(pt, {"id", "uid", "used_qty", "left_qty", "xnc_op_ids", "product_id", "surface_face_op", "surface_back_op"})
        d["product"] = pidx.get(pt.product_id)
        for k in ("edge_top", "edge_bottom", "edge_left", "edge_right"):
            d[k] = oidx.get(getattr(pt, k).op_id) if getattr(pt, k).op_id else None
        for k in ("groove_top", "groove_bottom", "groove_left", "groove_right"):
            g = getattr(pt, k)
            d[k] = (oidx.get(g.op_id), g.back_side) if g.op_id else None
        d["xnc"] = sorted(oidx[x] for x in pt.xnc_op_ids if x in oidx)
        return d

    out: dict[str, Any] = dict(name=p.name, currency=p.currency, size_mode=p.size_mode.value, note=p.note,
                               order_date=str(p.order_date), ready_date=str(p.ready_date))
    out["products"] = [_dump(pr, {"id", "cost_material", "cost_operation", "messages"}) for pr in p.products]
    ops = []
    for o in p.operations:
        d: dict[str, Any] = dict(type=o.type.value, name=o.name, print=o.print, new_page=o.new_page,
                                 description=o.description)
        if o.type in (OpType.CS, OpType.EL, OpType.XNC):
            d["code"] = o.code                      # O / GR / LB operatsiya kodi faylda saqlanmaydi (format maydoni yo'q)
        if o.type == OpType.CS:
            d["mat"] = _dump(o.cs_material) if o.cs_material else None
            d["cut"] = _dump(o.cs_cut) if o.cs_cut else None
            d["sheets"] = [_dump(s, {"id", "used_qty", "source_remnant_id", "uid"}) for s in o.sheets]
            d["parts"] = [part(pt) for pt in o.parts]
        elif o.type == OpType.EL:
            d["el"] = _dump(o.el)
        elif o.type == OpType.GR:
            d["gr"] = _dump(o.gr, {"usage", "cut_length", "passes"})
        elif o.type == OpType.XNC:
            x = _dump(o.xnc, {"part_vars", "program"})
            x["program"] = [_dump(c) for c in o.xnc.program]
            d["xnc"] = x
            d["xnc_part"] = partidx.get(o.xnc_part_id) if o.xnc_part_id else None
        elif o.type == OpType.O:
            od = _dump(o.o, {"multiplier", "messages", "owner_product_id"})
            od["owner"] = pidx.get(o.o.owner_product_id) if o.o.owner_product_id else None
            od["materials"] = [{k: v for k, v in m.items() if k != "id"} for m in od["materials"]]      # id — tasodifiy
            d["o"] = od
        elif o.type == OpType.LB:
            d["lb"] = _dump(o.lb)
        ops.append(d)
    out["operations"] = ops
    return out


def metrics(p: Project) -> dict:
    """Hisoblangan ko'rsatkichlar: detallar soni va maydoni (CS bo'yicha), kromka metri (`calc.edge_usage`), XNC statistikasi
    (`xnc-stats` endpointi bilan bir xil `xnc_stats`)."""
    calc.recalc_project(p)
    out: dict[str, Any] = {"cs": [], "el": [], "xnc": []}
    for o in p.operations:
        if o.type == OpType.CS:
            out["cs"].append((len(o.parts), sum(calc.effective_qty(p, pt) for pt in o.parts),
                              round(calc.parts_area_m2(p, o), 4)))
        elif o.type == OpType.EL:
            u = calc.edge_usage(p, o)
            out["el"].append((round(u["work_m"], 3), round(u["material_m"], 3)))
        elif o.type == OpType.XNC and o.xnc is not None:
            s = xnc.xnc_stats(o.xnc)
            out["xnc"].append((s["drills"], s["mill_m"], s["saw_m"]))
    return out


def diff(a: Any, b: Any, path: str = "", limit: int = 12) -> list[str]:
    """Ikki kanonik tuzilma orasidagi farqlar (yo'l: qiymat1 != qiymat2)."""
    out: list[str] = []

    def walk(x, y, p):
        if len(out) >= limit:
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y), key=str):
                if k not in x or k not in y:
                    out.append(f"{p}.{k}: {'yo`q' if k not in x else 'bor'}")
                else:
                    walk(x[k], y[k], f"{p}.{k}")
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                out.append(f"{p}: uzunlik {len(x)} != {len(y)}")
            for i, (u, v) in enumerate(zip(x, y)):
                walk(u, v, f"{p}[{i}]")
        elif x != y:
            out.append(f"{p}: {str(x)[:60]} != {str(y)[:60]}")
    walk(a, b, path)
    return out
