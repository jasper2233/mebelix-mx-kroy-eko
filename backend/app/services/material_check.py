"""Material bazasi tekshiruvi va buyurtmalar navbati (foydalanuvchi talabi, 2026-10-15).

Har kroy operatsiyasi (CS / CL / CN) uchun: **kerakli** butun listlar (kroydan keyin — kartalardagi butun listlar, ombor qoldiqlari
hisobga olinmaydi; kroygacha — taxmin, `calc.cs_cost`) va **bazadagi** listlar (material katalogi `stock`: tovar `material_id`
bo'yicha, bo'lmasa kod / nom bo'yicha). Qoldiqlar ombori alohida ko'rsatiladi (`remnants` — dona). Navbat: loyihalar raqam
(kelish) tartibida — birinchi «material to'liq bor» loyiha **navbatdagi** deb belgilanadi, yetmaganlar uchun «bazani to'ldirish
kerak» ogohlantirishi beriladi. Hech narsa saqlanmaydi; zaxira (`stock`) MES / «Каталог товаров» orqali yuritiladi."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from ..db import CatalogItemRow, ProjectRow, RemnantRow, SessionLocal
from ..i18n import _
from ..models import OpType, Operation, Project
from . import calc
from . import catalog as cat
from . import warehouse

KIND_BY_TYPE = {OpType.CS: "sheet", OpType.CN: "sheet", OpType.CL: "linear"}
EPS = 1e-9


def _thickness(op: Operation) -> Optional[float]:
    if op.type == OpType.CS:
        return op.cs_material.thickness if op.cs_material else None
    if op.type == OpType.CL:
        return op.cl.thickness if op.cl else None
    if op.type == OpType.CN:
        return op.cn.thickness if op.cn else None
    return None


def find_catalog_item(op: Operation) -> Optional[CatalogItemRow]:
    """Operatsiya materiali katalogda: avval `material_id`, so'ng kod / nom bo'yicha aniq moslik."""
    if op.material_id:
        with SessionLocal() as s:
            row = s.get(CatalogItemRow, op.material_id)
        if row is not None:
            return row
    kind = KIND_BY_TYPE.get(op.type, "sheet")
    for text in (op.code, op.name):
        row = cat.find_item(kind, text)
        if row is not None:
            return row
    return None


def required_units(project: Project, op: Operation) -> tuple[float, bool]:
    """(kerakli butun listlar / polosalar, taxminiymi). Kroydan keyin — kartalardagi butun (qoldiq bo'lmagan) listlar;
    kroygacha CS da — `calc.cs_cost` taxmini; CL / CN da kroysiz taxmin yo'q (0, taxminiy)."""
    res = op.result
    if res and res.maps:
        return float(sum(m.copies for m in res.maps if not m.is_remnant)), False
    if op.type == OpType.CS:
        q = calc.cs_cost(project, op)
        return float(q.get("sheets_total") or 0), True
    return 0.0, True


def _fmt(v: Optional[float]) -> str:
    if v is None:
        return "?"
    return f"{v:g}"


def check_project(project: Project) -> dict:
    """Loyihaning kroy operatsiyalari bo'yicha material yetarliligi: items (har operatsiya), ok, known, warnings."""
    with SessionLocal() as s:
        remn = s.scalars(select(RemnantRow).where(RemnantRow.qty > 0)).all()
        remn = [(r.material_code or "", r.thickness, bool(getattr(r, "linear", False)), int(r.qty or 0)) for r in remn]
    items: list[dict] = []
    for op in project.operations:
        if op.type not in KIND_BY_TYPE or not op.parts:
            continue
        need, est = required_units(project, op)
        item = find_catalog_item(op)
        t = _thickness(op)
        key = warehouse.material_key(op)
        linear = op.type == OpType.CL
        rem_qty = sum(q for code, rt, lin, q in remn
                      if code.strip() == key and lin == linear and (t is None or rt is None or abs(float(rt) - float(t)) < 0.01))
        if item is None:
            have: Optional[float] = None
            short: Optional[float] = None
            status = "unknown"
        else:
            have = float(item.stock or 0)
            short = max(0.0, need - have)
            status = "ok" if short <= EPS else "short"
        items.append(dict(op_id=op.id, type=op.type.value if hasattr(op.type, "value") else str(op.type), code=op.code, name=op.name,
                          thickness=t, need=need, estimated=est, have=have, short=short, remnants=rem_qty, status=status,
                          catalog_id=item.id if item is not None else None, catalog_name=item.name if item is not None else None))
    warnings: list[str] = []
    for i in items:
        unit = _("unit_sheets")
        if i["status"] == "short":
            warnings.append(_("mat_short", name=i["name"], need=_fmt(i["need"]), have=_fmt(i["have"]), short=_fmt(i["short"]), unit=unit))
        elif i["status"] == "unknown":
            warnings.append(_("mat_unknown", name=i["name"]))
    return dict(project_id=project.id, number=project.number, name=project.name, status=int(project.status),
                ok=bool(items) and all(i["status"] == "ok" for i in items),
                known=all(i["status"] != "unknown" for i in items),
                estimated=any(i["estimated"] for i in items),
                items=items, warnings=warnings)


def queue(statuses: list[int], folder_id: Optional[str] = None, limit: int = 100, all_folders: bool = True) -> dict:
    """Buyurtmalar navbati: holati `statuses` da bo'lgan loyihalar raqam tartibida, har biri uchun material tekshiruvi.
    `next` — birinchi «material to'liq bor» loyiha; `warnings` — yetmagan / noma'lum materiallar (loyiha raqami bilan)."""
    from .. import store
    with SessionLocal() as s:
        st = select(ProjectRow.id).where(ProjectRow.status.in_(statuses)).order_by(ProjectRow.number)
        if not all_folders:
            st = st.where(ProjectRow.folder_id == folder_id)
        ids = list(s.scalars(st.limit(max(1, min(int(limit), 1000)))))
    rows: list[dict] = []
    for pid in ids:
        try:
            p = store.load(pid)
        except Exception:  # noqa: BLE001 — buzuq yozuv navbatni to'xtatmaydi
            continue
        rows.append(check_project(p))
    nxt = next((r for r in rows if r["ok"]), None)
    for i, r in enumerate(rows):
        r["position"] = i + 1
        r["next"] = nxt is not None and r["project_id"] == nxt["project_id"]
    warnings = [f"№{r['number']}: {w}" for r in rows if not r["ok"] for w in r["warnings"]]
    message = _("queue_next", n=nxt["number"], name=nxt["name"]) if nxt else _("queue_none")
    return dict(count=len(rows), statuses=statuses,
                next=dict(project_id=nxt["project_id"], number=nxt["number"], name=nxt["name"]) if nxt else None,
                rows=rows, warnings=warnings, message=message)
