"""CNC (XNC): MebeliX program_stats ↔ .project ichida saqlangan countBore / countMill / countCut
(faqat avvalgi dastur hisoblagan operatsiyalar).    cd tools/bench && python3 xnc_check.py"""
import collections
import glob
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.plugins.legacy_project import program_to_commands  # noqa: E402
from app.services.xnc import program_stats  # noqa: E402

tot = ok_b = ok_m = ok_c = skipped = 0
bad = collections.Counter()
ex = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(HERE, "projects", "**", "*.project"), recursive=True)):
    try:
        root = ET.parse(f).getroot()
    except ET.ParseError:
        continue
    for op in root.findall("operation"):
        if op.get("typeId") != "XNC":
            continue
        if op.get("countBore") is None:
            skipped += 1
            continue
        cmds, size = program_to_commands(op.get("program") or "")
        if not size:
            bad["nosize"] += 1
            continue
        st = program_stats(cmds, *size)
        gb, gm, gc = (float(op.get(k) or 0) for k in ("countBore", "countMill", "countCut"))
        tot += 1
        okb = int(gb) == st["drills"]
        okm = abs(gm - st["mill_m"]) <= 0.002 + 0.001 * gm
        okc = abs(gc - st["saw_m"]) <= 0.002 + 0.001 * gc
        ok_b += okb
        ok_m += okm
        ok_c += okc
        for nm, okx, g, o in (("teshik", okb, gb, st["drills"]), ("freza", okm, gm, st["mill_m"]), ("arra", okc, gc, st["saw_m"])):
            if not okx:
                bad[nm] += 1
                if len(ex[nm]) < 6:
                    ex[nm].append((os.path.relpath(f, HERE)[:60], op.get("id"), g, o))
print(f"XNC: {tot} dastur (hisoblanmaganlari {skipped}) | teshiklar mos {ok_b} | freza mos {ok_m} | arra mos {ok_c} | {dict(bad)}")
for k, v in ex.items():
    for e in v:
        print("  ", k, e)
