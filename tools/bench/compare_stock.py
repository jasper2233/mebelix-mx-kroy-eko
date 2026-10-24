"""Ko'p-listli kroylar (qoldiq/qirqim listlar + «cheksiz» list) bo'yicha avvalgi dastur natijasi bilan solishtirish.

    cd tools/bench && python compare_stock.py [fast|normal|max]

`compare.py` har kroyda faqat birinchi list turini oladi; bu skript esa loyihani importer orqali (listlar
soni bo'yicha tartiblangan) o'qib, to'liq list ro'yxati bilan kroy qiladi va ishlatilgan material maydonini
(m²) fayl ichida saqlangan natija (cMaterialAmount) bilan solishtiradi. Qoldiq maydoni kamroq bo'lsa — yaxshi.
"""
import glob
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))


def job(args):
    path, quality = args
    import defusedxml.ElementTree as ET
    from app.models import OpType
    from app.plugins.legacy_project import import_project
    from app.services import calc
    from app.services.validate import validate

    raw = open(path, "rb").read()
    root = ET.fromstring(raw)
    gl = [o for o in root.findall("operation") if o.get("typeId") == "CS"]
    gl_by_name = {}
    goods = {g.get("id"): g for g in root.findall("good")}
    for o in gl:
        m = o.find("material")
        g = goods.get(m.get("id")) if m is not None else None
        if g is not None:
            gl_by_name.setdefault(g.get("name"), []).append(o)
    p, _w = import_project(raw, os.path.basename(path))
    out = []
    seen: dict[str, int] = {}
    for op in p.operations:
        if op.type != OpType.CS:
            continue
        k = seen.get(op.name, 0)
        seen[op.name] = k + 1
        src = (gl_by_name.get(op.name) or [None] * (k + 1))[k] if k < len(gl_by_name.get(op.name, [])) else None
        if len(op.sheets) < 2 or src is None or not op.parts:
            continue
        t0 = time.time()
        calc.run_cutting(p, op, quality=quality)
        res = op.result
        items = calc._items_for(p, op, op.cs_cut)
        errs = len(validate(res, items, op.sheets, op.cs_cut))
        out.append(dict(file=os.path.relpath(path, os.path.join(HERE, "projects")).replace(os.sep, "/"), op=op.name,
                        sheets=[(s.length, s.width, s.qty) for s in op.sheets],
                        me_sheets=res.total_sheets, me_area=round(res.material_area_m2, 3),
                        gl_sheets=int(float(src.find("material").get("count") or 0)),
                        gl_area=round(float(src.get("cMaterialAmount") or 0), 3),
                        unplaced=len(res.unplaced), errs=errs, t=round(time.time() - t0, 1)))
    return out


def main():
    quality = sys.argv[1] if len(sys.argv) > 1 else "normal"
    files = sorted(glob.glob(os.path.join(HERE, "projects", "**", "*.project"), recursive=True))
    t = time.time()
    with Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
        rows = [r for part in pool.map(job, [(f, quality) for f in files], chunksize=1) for r in part]
    me = sum(r["me_area"] for r in rows)
    gl = sum(r["gl_area"] for r in rows)
    less = [r for r in rows if r["me_area"] < r["gl_area"] - 0.01]
    more = [r for r in rows if r["me_area"] > r["gl_area"] + 0.01]
    print(f"{len(rows)} ko'p-listli kroy | ishlatilgan material: MebeliX {me:.2f} m², avvalgi {gl:.2f} m² "
          f"| kam {len(less)}, teng {len(rows) - len(less) - len(more)}, ko'p {len(more)} | "
          f"tekshiruv xatosi {sum(r['errs'] for r in rows)} | joylashmagan {sum(r['unplaced'] for r in rows)} | "
          f"{time.time() - t:.0f} s")
    for r in more:
        print(f"  ko'p: {r['file']} [{r['op']}] {r['me_area']} > {r['gl_area']} m²  (listlar {r['me_sheets']} vs {r['gl_sheets']}) {r['sheets']}")
    if os.environ.get("STOCK_OUT"):                 # har kroy natijasi (solishtirish uchun)
        import json
        json.dump(rows, open(os.environ["STOCK_OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
