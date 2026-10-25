"""XNC ishi — ASBOB bo'yicha (2026-10-25, foydalanuvchi talabi): MES (ERP + moliya) har asbob ishiga alohida narx qo'yadi —
parma uchun TESHIK soni, freza / arra uchun METR. MX buyurtmadagi XNC detallar soni va har asbob qilgan ishni yuboradi.

Manba — `xnc.evaluate()` (ifodalar, sikllar, massivlar hisoblangan tekis amallar ro'yxati; `program_stats` bilan bir xil qoidalar):
* parma: `Drill*` amallari (`inside`), asbob = `T` (bo'sh bo'lsa «D{diametr}»), tomon (yuza / yon), teshib o'tadimi (yuza teshigi
  chuqurligi ≥ detal qalinligi); soni — `count` (massiv yoyilgan);
* freza: kontur asbobi — oldingi `MillStart` (`T`, `D`); uzunlik — chiziq + yoy (radius × burchak), to'rtburchak / ellips; cho'ntak
  (C=3) uzunlikka kirmaydi (`program_stats` kabi); chuqurlik qadami (SDP) bo'lsa — o'tishlar bilan metr ham (`mill_pass_m`);
  dasturda hisoblanmaydigan kontur bo'lsa — frezalash 0 (`program_stats` kabi, stanokda bajarilmaydi) va xato yoziladi;
* arra pazi (Groove): metr × o'tishlar (`groove_passes`).
Har XNC operatsiya natijasi uning `qty` siga (ОК − МК, mahsulot soni bilan — `calc.sync_xnc`) ko'paytiriladi.
"""
from __future__ import annotations

import math
from typing import Optional

from ..models import OpType, Project
from . import xnc as X

_SIDE = {"DrillFront": "face", "DrillLeft": "side", "DrillRight": "side", "DrillTop": "side", "DrillBottom": "side"}


def _name(t, d) -> str:
    t = str(t or "").strip()
    return t if t else f"D{d:g}"


def op_tool_usage(x) -> tuple[list[dict], list[str]]:
    """Bitta XNC dasturi (1 dona detal uchun): [{kind, name, d, side, through, depth, holes, mill_m, mill_pass_m, saw_m}], xatolar."""
    ops = X.evaluate(x.program, x.length, x.width, x.thickness, X.program_vars(x), x.par_values)
    use: dict[tuple, dict] = {}

    def slot(kind: str, name: str, d: float, side: str = "", through: bool = False) -> dict:
        k = (kind, name, round(d, 2), side, through)
        return use.setdefault(k, dict(kind=kind, name=name, d=round(d, 2), side=side, through=through, depths=set(),
                                      holes=0, mill_m=0.0, mill_pass_m=0.0, saw_m=0.0))

    dz = float(x.thickness or 0)
    cur: Optional[dict] = None          # joriy kontur asbobi (MillStart)
    passes = 1
    pos = None
    for o in ops:
        k = o["kind"]
        if k.startswith("Drill"):
            if not o.get("inside", True):
                continue
            d = float(o.get("D") or 0)
            dp = float(o.get("DP") or 0)
            through = k == "DrillFront" and dz > 0 and dp >= dz - 1e-6
            s = slot("drill", _name(o.get("T"), d), d, _SIDE.get(k, "face"), through)
            s["holes"] += int(o.get("count") or 1)
            s["depths"].add(round(dp, 2))
        elif k == "MillStart":
            pos = (o["X"], o["Y"])
            if not o.get("ok", True) or (o.get("C", 0) == 3 and not X.POCKET_COUNTS_IN_LENGTH):
                pos, cur = None, None
                continue
            d = float(o.get("D") or 0)
            cur = slot("mill", _name(o.get("T"), d), d)
            dp, sdp = float(o.get("DP") or 0), float(o.get("SDP") or 0)
            cur["depths"].add(round(dp, 2))
            passes = max(1, math.ceil(dp / sdp - 1e-9)) if sdp > 0 and dp > 0 else 1
        elif k in ("MillLine", "MillArc", "MillArcCenter", "MillArc3P") and pos is not None and cur is not None:
            nxt = (o["X"], o["Y"])
            if k == "MillLine":
                ln = math.dist(pos, nxt)
            else:
                g = X.mill_arc(k, pos, o)
                ln = g[0] * g[1] if g else math.dist(pos, nxt)
            if math.isfinite(ln):
                cur["mill_m"] += ln / 1000
                cur["mill_pass_m"] += ln * passes / 1000
            pos = nxt
        elif k in ("MillRect", "MillEllipse"):
            if o.get("C", 0) == 3 and not X.POCKET_COUNTS_IN_LENGTH:
                continue
            d = float(o.get("D") or 0)
            s = slot("mill", _name(o.get("T"), d), d)
            ln = X.rect_length(o) if k == "MillRect" else X.ellipse_length(o)
            s["mill_m"] += ln / 1000
            s["mill_pass_m"] += ln / 1000
            s["depths"].add(round(float(o.get("DP") or 0), 2))
        elif k == "Groove" and o.get("ok", True):
            d = float(o.get("D") or 4.0)
            s = slot("saw", _name(o.get("T"), d), d)
            s["saw_m"] += math.dist((o["X1"], o["Y1"]), (o["X2"], o["Y2"])) * X.groove_passes(o["W"], d) / 1000
            s["depths"].add(round(float(o.get("DP") or 0), 2))
    errors = [str(m) for m in ops.messages] if ops.problems else []      # problems — xatolar soni
    bad = any(o["kind"] in X._MILL + ("Groove", "MillRect", "MillEllipse") and not o.get("ok", True) for o in ops)
    if bad:                              # program_stats kabi: hisoblanmaydigan kontur — frezalash 0
        for s in use.values():
            if s["kind"] == "mill":
                s["mill_m"] = s["mill_pass_m"] = 0.0
        errors.append("mill_not_ok")
    out = []
    for s in use.values():
        s["depths"] = sorted(s["depths"])
        for f in ("mill_m", "mill_pass_m", "saw_m"):
            s[f] = round(s[f], 4)
        out.append(s)
    return out, errors


def project_tool_summary(project: Project) -> dict:
    """Buyurtma bo'yicha: XNC operatsiyalar va detallar soni; har asbob — teshiklar / metr (nusxalar bilan), nechta detalda,
    qaysi operatsiyalarda. {xnc_ops, xnc_parts, tools: [...], errors: [{op_id, code, error}]}."""
    parts = {pt.id: pt for o in project.operations for pt in o.parts}
    agg: dict[tuple, dict] = {}
    xops = xparts = 0
    errors: list[dict] = []
    for o in project.operations:
        if o.type != OpType.XNC or o.xnc is None:
            continue
        qty = max(0, int(o.xnc.qty or 0))
        if qty <= 0:
            continue
        xops += 1
        xparts += qty
        try:
            uses, errs = op_tool_usage(o.xnc)
        except Exception as e:  # noqa: BLE001 — bitta buzuq dastur butun hisobotni to'xtatmasin
            errors.append(dict(op_id=o.id, code=o.code, error=str(e)[:300]))
            continue
        for e in errs:
            errors.append(dict(op_id=o.id, code=o.code, error=str(e)[:300]))
        pt = parts.get(o.xnc_part_id or "")
        for u in uses:
            k = (u["kind"], u["name"], u["d"], u["side"], u["through"])
            g = agg.setdefault(k, dict(kind=u["kind"], name=u["name"], d=u["d"], side=u["side"], through=u["through"],
                                       depths=set(), holes=0, mill_m=0.0, mill_pass_m=0.0, saw_m=0.0, parts=0, ops=0, uses=[]))
            g["depths"].update(u["depths"])
            g["holes"] += u["holes"] * qty
            g["mill_m"] += u["mill_m"] * qty
            g["mill_pass_m"] += u["mill_pass_m"] * qty
            g["saw_m"] += u["saw_m"] * qty
            g["parts"] += qty
            g["ops"] += 1
            g["uses"].append(dict(op_id=o.id, code=o.code or "", part_id=o.xnc_part_id,
                                  part_uid=pt.uid if pt is not None else None, part_name=pt.name if pt is not None else "",
                                  qty=qty, holes=u["holes"], mill_m=u["mill_m"], saw_m=u["saw_m"]))
    tools = []
    for g in sorted(agg.values(), key=lambda g: ({"drill": 0, "mill": 1, "saw": 2}[g["kind"]], g["name"], g["d"])):
        g["depths"] = sorted(g["depths"])
        for f in ("mill_m", "mill_pass_m", "saw_m"):
            g[f] = round(g[f], 3)
        tools.append(g)
    return dict(xnc_ops=xops, xnc_parts=xparts, tools=tools, errors=errors)
