"""W16 (CN) testlari uchun loyiha yig'uvchi: model darajasida (API / bazasiz) CN operatsiyasi, detallar, listlar, XNC konturlari."""
from __future__ import annotations

from typing import Optional

from app.models import (CNParams, Operation, OpType, Part, Project, StockSheet, XNCParams, XncCommand)
from app.services import cn_calc


def cmd(name: str, **params):
    return XncCommand(cmd=name, params=params)


def make_project(parts: list[dict], sheets: Optional[list[tuple]] = None, cn: Optional[dict] = None,
                 xnc: Optional[dict[int, list[XncCommand]]] = None) -> tuple[Project, Operation]:
    """parts: [{length, width, qty, grain?, name?}], sheets: [(L, W, qty?)], xnc: {detal indeksi (0 dan): XNC dasturi} — shu detalga
    bog'langan XNC operatsiyasi (detal o'lchamida)."""
    p = Project(name="cn-test")
    op = Operation(type=OpType.CN, name="CN", cn=CNParams(**(cn or {})))
    for i, d in enumerate(parts):
        pt = Part(uid=i + 1, name=d.get("name", f"P{i + 1}"), length=d["length"], width=d["width"], qty=d.get("qty", 1), grain=d.get("grain", False))
        op.parts.append(pt)
        if xnc and i in xnc:
            xo = Operation(type=OpType.XNC, name=f"x{i + 1}", xnc=XNCParams(length=d["length"], width=d["width"], thickness=op.cn.thickness,
                                                                           by_part_size=False, program=xnc[i]), xnc_part_id=pt.id)
            pt.xnc_op_ids.append(xo.id)
            p.operations.append(xo)
    for L, W, *q in (sheets or [(2750, 1830)]):
        op.sheets.append(StockSheet(length=L, width=W, qty=q[0] if q else 10000))
    p.operations.insert(0, op)
    return p, op


def run(project: Project, op: Operation, quality: str = "fast"):
    cn_calc.run_nesting(project, op, quality=quality)
    return op.result
