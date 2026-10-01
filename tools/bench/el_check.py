"""Kromka (EL): MebeliX hisobi ↔ .project ichida saqlangan qiymatlar (elLength — ish metri, material count —
material metri). Faqat saqlangan qiymati bor operatsiyalar solishtiriladi.    cd tools/bench && python3 el_check.py"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import calc  # noqa: E402

ok_w = ok_m = tot = 0
bad = []
for f in sorted(glob.glob(os.path.join(HERE, "projects", "**", "*.project"), recursive=True)):
    data = open(f, "rb").read()
    try:
        root = ET.fromstring(data)
        p, _w = import_project(data, f)
    except Exception:  # noqa: BLE001
        continue
    src = [oe for oe in root.findall("operation") if oe.get("typeId") == "EL"]
    els = [o for o in p.operations if o.type.value == "EL"]
    for oe, op in zip(src, els):
        gl_work = float(oe.get("elLength") or 0)
        me = oe.find("material")
        gl_mat = float(me.get("count") or 0) if me is not None else 0
        if gl_work == 0 and gl_mat == 0:
            continue                      # avvalgi dastur hisoblamagan
        u = calc.edge_usage(p, op)
        tot += 1
        okw = abs(u["work_m"] - gl_work) <= 0.011
        okm = abs(u["material_m"] - gl_mat) <= 0.011
        ok_w += okw
        ok_m += okm
        if not (okw and okm) and len(bad) < 12:
            bad.append((os.path.basename(f), op.name[:30], "ish", u["work_m"], gl_work, "material", u["material_m"], gl_mat))
print(f"EL: {tot} operatsiya | ish metri mos {ok_w} | material metri mos {ok_m}")
for b in bad:
    print("  ", b)
